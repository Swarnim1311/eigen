"""Eigen backend — Phase 2 FastAPI application.

Routes: legacy /health + / (unchanged), /api/v1/math/*, /api/v1/recognize,
/api/v1/ready. Errors always take the structured {error: {code, message}} shape;
tracebacks are logged server-side only and never returned to clients.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import math_parser as mp
from app.recognizer import build_recognizer
from app.routers import math_router, recognize_router

log = logging.getLogger("eigen.api")

MATH_HTTP = {
    "empty_input": 400,
    "input_too_long": 400,
    "bad_token": 400,
    "parse_error": 400,
    "unknown_variable": 400,
    "unsupported_syntax": 422,
    "unbound_variable": 422,
    "too_complex": 422,
    "division_by_zero": 422,
    "solve_failed": 422,
    "complex_result": 422,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.recognizer = build_recognizer()
    log.info("recognizer: %s", app.state.recognizer.status())
    yield
    try:
        app.state.recognizer.close()
    except Exception:
        pass


app = FastAPI(title="Eigen API", version="0.2.0", lifespan=lifespan)
# TestClient without lifespan context still needs a recognizer:
app.state.recognizer = build_recognizer()


@app.exception_handler(mp.MathError)
async def math_error_handler(request: Request, exc: mp.MathError):
    _ = request
    return JSONResponse(
        status_code=MATH_HTTP.get(exc.code, 422),
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    _ = request
    return JSONResponse(
        status_code=422,
        content={
            "error": {"code": "validation_error", "message": "Request failed schema validation."}
        },
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    log.error(
        "unhandled %s %s: %s", request.method, request.url.path, type(exc).__name__, exc_info=True
    )
    return JSONResponse(
        status_code=500, content={"error": {"code": "internal", "message": "Internal error."}}
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by Phase 0 acceptance checks."""
    return {"status": "ok", "service": "eigen-backend"}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "eigen-backend", "health": "/health"}


app.include_router(math_router.router)
app.include_router(recognize_router.router)
