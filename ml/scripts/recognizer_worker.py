"""Persistent PosFormer inference worker (Phase 2, runs in ml/.venv).

The backend API server (backend/.venv, no torch) spawns exactly ONE of these and
talks JSON-lines over stdio, so the 78 MB checkpoint is loaded ONCE, not per
request. Third-party PosFormer code is used UNMODIFIED via run_posformer helpers.

Protocol (all UTF-8, one JSON object per line, flush after every line):
  backend -> worker : {"id": "<req id>", "image_b64": "<png/jpg bytes, base64>"}
  worker  -> backend : {"id": same, "latex": "...", "score": float,
                        "duration_s": float}
                    or {"id": same, "error": "<short reason>"}
  worker announces on startup (after model load):
                       {"ready": true, "model_id": "<id>"}

Image handling: bytes -> PIL grayscale. Uploads (phone photos) are usually dark
ink on LIGHT background, but the CROHME checkpoint expects white ink on BLACK
(mean-calibrated in Phase 1), so light-background images are inverted. Documented
preprocessing, applied identically to every request; polarity flag included in
error-free responses is not needed because downstream only sees LaTeX.

Any request-level exception -> {"id","error"} (never a traceback on stdout;
tracebacks go to stderr = worker log). Fatal startup failure -> non-zero exit.
"""
import base64
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import run_posformer as rp  # noqa: E402  (installs pl_compat, imports torch/PIL)
import torch  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

MODEL_ID = "posformer-crohme/best.ckpt-epoch206 (experimental)"


def ensure_polarity(img: Image.Image) -> Image.Image:
    """CROHME checkpoint expects white ink on black background (Phase-1
    calibration). Phone-photo uploads are normally the opposite, so invert
    images whose mean brightness is above mid-grey."""
    import numpy as np

    if float(np.asarray(img).mean()) > 127.0:
        return ImageOps.invert(img)
    return img


def image_to_tensors(data: bytes):
    img = Image.open(io.BytesIO(data)).convert("L")
    img = ensure_polarity(img)
    import numpy as np

    arr = rp._scaler(np.asarray(img))
    t = rp._to_tensor(arr)
    _, h, w = t.shape
    mask = torch.zeros(1, h, w, dtype=torch.bool)
    return t.unsqueeze(0), mask


def main() -> int:
    ckpt = os.environ.get(
        "EIGEN_CKPT",
        os.path.join(HERE, "..", "checkpoints", "posformer-best.ckpt"),
    )
    try:
        model = rp.load_model(ckpt)
    except Exception as exc:  # startup failure: backend will see EOF -> 503
        print(f"WORKER FATAL: cannot load checkpoint: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"ready": True, "model_id": MODEL_ID}), flush=True)
    with torch.no_grad():
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                rid = req.get("id", "?")
                data = base64.b64decode(req["image_b64"])
                img_t, mask = image_to_tensors(data)
                t0 = time.time()
                hyps = model.beam_search(img_t, mask, **rp.BEAM)
                dt = time.time() - t0
                best = hyps[0]
                out = {"id": rid,
                       "latex": rp.vocab.indices2label(best.seq),
                       "score": float(best.score),
                       "duration_s": round(dt, 3)}
            except Exception as exc:  # never leak tracebacks to the backend
                print(f"WORKER request failed: {type(exc).__name__}: {exc}",
                      file=sys.stderr)
                try:
                    rid = json.loads(line).get("id", "?")
                except Exception:
                    rid = "?"
                out = {"id": rid, "error": f"{type(exc).__name__}"}
            print(json.dumps(out), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
