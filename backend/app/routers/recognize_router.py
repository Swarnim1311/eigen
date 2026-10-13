"""Eigen recognition route: POST /api/v1/recognize + GET /api/v1/ready."""

import logging

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse

from app import math_parser as mp
from app.recognizer import (
    MODEL_ID,
    ImageValidationError,
    ModelInferenceError,
    ModelUnavailableError,
    validate_image,
)
from app.schemas import MathParseStatus, ModelInfo, RecognizeResponse

log = logging.getLogger("eigen.api")

router = APIRouter(prefix="/api/v1", tags=["recognition"])

_VALIDATION_HTTP = {
    "empty_image": 400,
    "invalid_image": 400,
    "unsupported_media": 415,
    "image_too_large": 413,
    "image_too_small": 400,
}


def _parse_status(latex: str) -> MathParseStatus:
    """Best-effort check: does the predicted LaTeX fall in our math grammar?"""
    if not latex or not latex.strip():
        return MathParseStatus(ok=False, error="Empty prediction.")
    try:
        ascii_expr = mp.latex_to_ascii(latex)
        mp.parse_expression(ascii_expr)
        return MathParseStatus(ok=True, ascii=ascii_expr)
    except mp.MathError as exc:
        return MathParseStatus(ok=False, error=exc.message)


@router.post("/recognize", response_model=None)
def recognize(request: Request, file: UploadFile = File(...)) -> RecognizeResponse | JSONResponse:
    data = file.file.read()
    try:
        info = validate_image(data)
    except ImageValidationError as exc:
        log.info("rejected upload: %s", exc.code)
        return JSONResponse(
            status_code=_VALIDATION_HTTP.get(exc.code, 400),
            content={"error": {"code": exc.code, "message": exc.message}},
        )
    service = request.app.state.recognizer
    try:
        result = service.recognize(info, data)
    except ModelUnavailableError as exc:
        return JSONResponse(
            status_code=503, content={"error": {"code": "model_unavailable", "message": str(exc)}}
        )
    except ModelInferenceError as exc:
        return JSONResponse(
            status_code=502, content={"error": {"code": "model_error", "message": str(exc)}}
        )
    return RecognizeResponse(
        latex=result.latex,
        beam_score=result.beam_score,
        model=ModelInfo(id=MODEL_ID),
        duration_s=result.duration_s,
        math_parse=_parse_status(result.latex),
    )


@router.get("/ready")
def ready(request: Request):
    state, detail = request.app.state.recognizer.status()
    reported = {"configured": "standby"}.get(state, state)
    return {"api": "ok", "model": {"status": reported, "detail": detail}}
