"""API tests for /api/v1/recognize + /api/v1/ready.

The recognizer behind the API is a replaceable service: all behavior tests run
against a fake (fast, deterministic). ONE integration test exercises the real
PosFormer stdio worker; it is slow (~1-3 min: model load + CPU inference) and
runs only with EIGEN_TEST_WORKER=1.
"""

import io
import os

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.recognizer import (
    ModelInferenceError,
    ModelUnavailableError,
    RecognitionResult,
    UnavailableRecognizer,
)

client = TestClient(app)
_REAL_WORKER = os.environ.get("EIGEN_TEST_WORKER") == "1"


def make_png(size=(64, 64), color="white"):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


class FakeService:
    def __init__(self, latex=r"\frac{1}{2}", score=-1.5, fail=None, state=("ready", "fake ready")):
        self.latex = latex
        self.score = score
        self.fail = fail
        self._state = state

    def recognize(self, image, data):
        if self.fail == "unavailable":
            raise ModelUnavailableError("fake down")
        if self.fail == "inference":
            raise ModelInferenceError("fake bad image")
        return RecognitionResult(latex=self.latex, beam_score=self.score, duration_s=0.5)

    def status(self):
        return self._state

    def close(self):
        pass


@pytest.fixture()
def fake():
    real = app.state.recognizer
    svc = FakeService()
    app.state.recognizer = svc
    yield svc
    app.state.recognizer = real


def test_recognize_ok(fake):
    r = client.post("/api/v1/recognize", files={"file": ("eq.png", make_png(), "image/png")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["latex"] == r"\frac{1}{2}"
    assert body["beam_score"] == -1.5
    assert body["model"]["id"].startswith("posformer-crohme/")
    assert body["model"]["experimental"] is True
    assert body["duration_s"] == 0.5
    assert body["math_parse"]["ok"] is True


def test_recognize_math_parse_status(fake):
    fake.latex = "x + 2*y"
    r = client.post("/api/v1/recognize", files={"file": ("eq.png", make_png(), "image/png")})
    assert r.json()["math_parse"] == {"ok": True, "ascii": "x + 2*y", "error": None}
    fake.latex = r"\sqrt{4}"
    r = client.post("/api/v1/recognize", files={"file": ("eq.png", make_png(), "image/png")})
    parsed = r.json()["math_parse"]
    assert parsed["ok"] is False and parsed["ascii"] is None


def test_recognize_rejects_bad_uploads(fake):
    assert (
        client.post(
            "/api/v1/recognize", files={"file": ("x.png", b"not-an-image", "image/png")}
        ).status_code
        == 400
    )
    r = client.post("/api/v1/recognize", files={"file": ("x.png", b"not-an-image", "image/png")})
    assert r.json()["error"]["code"] == "invalid_image"
    r = client.post("/api/v1/recognize", files={"file": ("empty.png", b"", "image/png")})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "empty_image"
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), "white").save(buf, format="GIF")
    r = client.post("/api/v1/recognize", files={"file": ("x.gif", buf.getvalue(), "image/gif")})
    assert r.status_code == 415
    assert r.json()["error"]["code"] == "unsupported_media"
    r = client.post(
        "/api/v1/recognize", files={"file": ("tiny.png", make_png((8, 8)), "image/png")}
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "image_too_small"


def test_recognize_size_limit(fake, monkeypatch):
    import app.recognizer as rec

    monkeypatch.setattr(rec, "MAX_UPLOAD_BYTES", 10)
    monkeypatch.setattr(rec, "MAX_DIMENSION", 100000)
    r = client.post("/api/v1/recognize", files={"file": ("eq.png", make_png(), "image/png")})
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "image_too_large"


def test_recognize_dimension_limit(fake, monkeypatch):
    import app.recognizer as rec

    monkeypatch.setattr(rec, "MAX_DIMENSION", 32)
    r = client.post("/api/v1/recognize", files={"file": ("eq.png", make_png(), "image/png")})
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "image_too_large"


def test_recognize_service_errors():
    app.state.recognizer = FakeService(fail="unavailable")
    try:
        r = client.post("/api/v1/recognize", files={"file": ("eq.png", make_png(), "image/png")})
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "model_unavailable"
    finally:
        app.state.recognizer = FakeService()
    app.state.recognizer = FakeService(fail="inference")
    try:
        r = client.post("/api/v1/recognize", files={"file": ("eq.png", make_png(), "image/png")})
        assert r.status_code == 502
        assert r.json()["error"]["code"] == "model_error"
    finally:
        app.state.recognizer = FakeService()


def test_ready_states():
    app.state.recognizer = FakeService(state=("ready", "fake ready"))
    assert client.get("/api/v1/ready").json() == {
        "api": "ok",
        "model": {"status": "ready", "detail": "fake ready"},
    }
    app.state.recognizer = UnavailableRecognizer("no ckpt here")
    body = client.get("/api/v1/ready").json()
    assert body["model"]["status"] == "unavailable"
    app.state.recognizer = FakeService()


@pytest.mark.skipif(not _REAL_WORKER, reason="needs EIGEN_TEST_WORKER=1 (slow: loads 78MB ckpt)")
def test_real_worker_end_to_end():
    """Genuine integration: real PosFormer worker, real Phase-1 render."""
    from app.recognizer import PosFormerWorkerService, build_recognizer

    png = (
        r"C:\Users\Swarnim\Desktop\ML projects\eigen\ml\data\renders"
        r"\test\002ae6d5dd4173e4_b.png"
    )  # GT: x_{1}-x_{2}+x_{0}=0
    assert os.path.exists(png), "Phase-1 renders missing"
    svc = build_recognizer()
    assert isinstance(svc, PosFormerWorkerService)
    try:
        with open(png, "rb") as f:
            data = f.read()
        from app.recognizer import validate_image

        res = svc.recognize(validate_image(data), data)
        assert isinstance(res.latex, str) and res.latex.strip()
        assert res.duration_s > 0
        assert svc.status()[0] == "ready"
    finally:
        svc.close()
