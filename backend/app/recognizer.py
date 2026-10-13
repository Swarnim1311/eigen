"""Eigen recognition service (Phase 2, backend side).

Architecture: the backend env has NO torch. The PosFormer model lives in the
separate ml/.venv and is driven through ONE persistent stdio worker process
(ml/scripts/recognizer_worker.py), so the checkpoint loads once per server
lifetime — never per request. Everything behind RecognizerService is
replaceable: a future model only needs a new implementation of the protocol.

States: unconfigured (files missing) -> configured -> loading -> ready, or
unavailable (spawn failed twice / worker died twice). Failures surface as
structured errors; tracebacks are logged server-side only, never returned.
Uploaded image bytes are held in memory only, never written to disk or logged.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import subprocess
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from PIL import Image, UnidentifiedImageError

log = logging.getLogger("eigen.recognizer")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ML_PYTHON = REPO_ROOT / "ml" / ".venv" / "Scripts" / "python.exe"
DEFAULT_WORKER = REPO_ROOT / "ml" / "scripts" / "recognizer_worker.py"
DEFAULT_CKPT = REPO_ROOT / "ml" / "checkpoints" / "posformer-best.ckpt"

MODEL_ID = "posformer-crohme/best.ckpt-epoch206"

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MIN_DIMENSION = 16
MAX_DIMENSION = 4000
ALLOWED_FORMATS = {"PNG", "JPEG", "BMP", "WEBP"}

STARTUP_TIMEOUT_S = 300.0
REQUEST_TIMEOUT_S = 600.0
MAX_RESTARTS = 2


class ImageValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ModelUnavailableError(Exception):
    """Worker cannot serve (missing files, spawn failure, repeated death)."""


class ModelInferenceError(Exception):
    """Worker alive but this request failed inside the model."""


@dataclass
class RecognitionResult:
    latex: str
    beam_score: float
    duration_s: float


@dataclass
class ImageInfo:
    format: str
    width: int
    height: int
    num_bytes: int


def validate_image(data: bytes) -> ImageInfo:
    """Validate upload bytes WITHOUT retaining them. Raises ImageValidationError."""
    if not data:
        raise ImageValidationError("empty_image", "Uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ImageValidationError(
            "image_too_large", f"Image exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
        )
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()  # structural check; image unusable after verify()
        with Image.open(io.BytesIO(data)) as img:
            fmt = (img.format or "").upper()
            width, height = img.size
    except UnidentifiedImageError:
        raise ImageValidationError("invalid_image", "File is not a readable image.")
    except Exception:
        raise ImageValidationError("invalid_image", "Image is malformed or truncated.")
    if fmt not in ALLOWED_FORMATS:
        raise ImageValidationError(
            "unsupported_media", f"Format {fmt or '?'} not supported. Use PNG, JPEG, BMP or WEBP."
        )
    if width < MIN_DIMENSION or height < MIN_DIMENSION:
        raise ImageValidationError(
            "image_too_small", f"Image {width}x{height} below minimum {MIN_DIMENSION}px."
        )
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise ImageValidationError(
            "image_too_large", f"Image {width}x{height} exceeds maximum {MAX_DIMENSION}px per side."
        )
    return ImageInfo(format=fmt, width=width, height=height, num_bytes=len(data))


class RecognizerService(Protocol):
    def recognize(self, image: ImageInfo, data: bytes) -> RecognitionResult: ...
    def status(self) -> tuple[str, str]: ...  # (state, detail)
    def close(self) -> None: ...


class UnavailableRecognizer:
    """Honest stand-in: reports unavailability, never fake predictions."""

    def __init__(self, detail: str) -> None:
        self._detail = detail

    def recognize(self, image: ImageInfo, data: bytes) -> RecognitionResult:
        raise ModelUnavailableError(self._detail)

    def status(self) -> tuple[str, str]:
        return "unavailable", self._detail

    def close(self) -> None:
        pass


class PosFormerWorkerService:
    """RecognizerService backed by one persistent ml-env worker process."""

    def __init__(
        self, ml_python: Path, worker: Path, ckpt: Path, posformer_code: str | None = None
    ) -> None:
        self._ml_python = ml_python
        self._worker = worker
        self._ckpt = ckpt
        self._posformer_code = posformer_code
        self._lock = threading.Lock()
        self._reader = ThreadPoolExecutor(max_workers=1, thread_name_prefix="eigen-worker-io")
        self._proc: subprocess.Popen | None = None
        self._restarts = 0
        self._state = "configured"
        self._detail = "Worker not started yet."
        missing = [str(p) for p in (ml_python, worker, ckpt) if not p.exists()]
        if missing:
            self._state = "unconfigured"
            self._detail = f"Missing worker files: {', '.join(missing)}."

    # -- lifecycle --
    def _spawn(self) -> None:
        env = os.environ.copy()
        env["EIGEN_CKPT"] = str(self._ckpt)
        if self._posformer_code:
            env["POSFORMER_CODE"] = self._posformer_code
        self._state = "loading"
        self._detail = "Loading checkpoint into worker (one-time cost)."
        log.info("spawning recognizer worker")
        try:
            self._proc = subprocess.Popen(
                [str(self._ml_python), str(self._worker)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                env=env,
                cwd=str(REPO_ROOT / "ml"),
            )
        except Exception as exc:
            self._proc = None
            self._state = "unavailable"
            self._detail = "Worker process could not be started."
            log.error("worker spawn failed: %s", type(exc).__name__)
            raise ModelUnavailableError(self._detail)
        deadline = time.time() + STARTUP_TIMEOUT_S
        ready = False
        while time.time() < deadline:
            try:
                line = self._readline(max(1.0, deadline - time.time()))
            except TimeoutError:
                break
            if not line:  # EOF: worker died
                break
            # stdout may carry human-readable load logs; the protocol line
            # is the JSON {"ready": true, ...} handshake.
            if '"ready":true' in line.replace(" ", ""):
                ready = True
                break
        if not ready:
            self._kill()
            self._state = "unavailable"
            self._detail = "Worker failed during model load."
            log.error("worker failed readiness handshake")
            raise ModelUnavailableError(self._detail)
        self._state = "ready"
        self._detail = f"Model {MODEL_ID} loaded (experimental baseline)."

    def _readline(self, timeout_s: float) -> str:
        """Blocking readline with a timeout (Windows has no select on pipes)."""
        assert self._proc and self._proc.stdout
        future = self._reader.submit(self._proc.stdout.readline)
        try:
            return future.result(timeout=timeout_s)
        except Exception as exc:
            raise TimeoutError() from exc

    def _kill(self) -> None:
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass

    def _ensure_ready(self) -> None:
        if self._state == "unconfigured":
            raise ModelUnavailableError(self._detail)
        if self._proc is not None and self._proc.poll() is None:
            return
        # worker died (or never started): restart within budget
        self._proc = None
        if self._restarts >= MAX_RESTARTS:
            self._state = "unavailable"
            self._detail = "Worker died repeatedly; giving up."
            raise ModelUnavailableError(self._detail)
        self._restarts += 1
        self._spawn()

    # -- protocol --
    def recognize(self, image: ImageInfo, data: bytes) -> RecognitionResult:
        payload = json.dumps({"id": uuid.uuid4().hex, "image_b64": base64.b64encode(data).decode()})
        t0 = time.time()
        with self._lock:
            try:
                self._ensure_ready()
                assert self._proc and self._proc.stdin and self._proc.stdout
                self._proc.stdin.write(payload + "\n")
                self._proc.stdin.flush()
                resp = None
                try:
                    for _ in range(5):  # skip any stray non-protocol lines
                        line = self._readline(REQUEST_TIMEOUT_S)
                        if not line:
                            break
                        try:
                            resp = json.loads(line)
                            break
                        except Exception:
                            continue
                except TimeoutError:
                    log.error("worker request timed out")
                    self._kill()
                    raise ModelInferenceError("Recognition timed out; worker restarted.")
            except (ModelUnavailableError, ModelInferenceError):
                raise
            except Exception as exc:
                log.error("worker IPC failed: %s", type(exc).__name__)
                self._proc = None
                raise ModelInferenceError("Recognition worker failed.")
            if resp is None:
                self._proc = None
                raise ModelInferenceError("Recognition worker failed.")
        if "error" in resp:
            raise ModelInferenceError("Model could not read this image.")
        total = time.time() - t0
        log.info(
            "recognized %s image in %.1fs (model %.1fs)",
            image.format,
            total,
            resp.get("duration_s", -1),
        )
        return RecognitionResult(
            latex=resp.get("latex", ""),
            beam_score=float(resp.get("score", 0.0)),
            duration_s=round(total, 3),
        )

    def status(self) -> tuple[str, str]:
        if self._proc is not None and self._proc.poll() is not None:
            self._proc = None
            if self._state == "ready":
                self._state = "configured"
                self._detail = "Worker exited; will restart on next request."
        return self._state, self._detail

    def close(self) -> None:
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        try:
            self._reader.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass


def build_recognizer() -> RecognizerService:
    """Factory honoring EIGEN_* env overrides; honest fallback when unusable."""
    ml_python = Path(os.environ.get("EIGEN_ML_PYTHON", str(DEFAULT_ML_PYTHON)))
    worker = Path(os.environ.get("EIGEN_WORKER", str(DEFAULT_WORKER)))
    ckpt = Path(os.environ.get("EIGEN_CKPT", str(DEFAULT_CKPT)))
    svc = PosFormerWorkerService(ml_python, worker, ckpt, os.environ.get("POSFORMER_CODE"))
    if svc.status()[0] == "unconfigured":
        return UnavailableRecognizer(svc.status()[1])
    return svc
