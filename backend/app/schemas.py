"""Eigen backend — Pydantic request/response schemas (Phase 2)."""

from typing import Literal

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorBody(BaseModel):
    error: ErrorDetail


class EvaluateRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=2000)
    variables: dict[str, float] = Field(default_factory=dict)
    latex: bool = False


class EvaluateResponse(BaseModel):
    result: str
    decimal: float | None = None
    expression: str


class SimplifyRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=2000)
    latex: bool = False


class SimplifyResponse(BaseModel):
    result: str
    expression: str


class SolveRequest(BaseModel):
    equation: str = Field(min_length=1, max_length=2000)
    variable: str = Field(min_length=1, max_length=10)


class SolveResponse(BaseModel):
    variable: str
    solutions: list[str]
    count: int


class ModelInfo(BaseModel):
    id: str
    experimental: Literal[True] = True
    baseline_note: str = (
        "Phase-1 baseline: 0/30 exact, mean CER 0.912 on MathWriting renders; not production-ready."
    )


class MathParseStatus(BaseModel):
    ok: bool
    ascii: str | None = None
    error: str | None = None


class RecognizeResponse(BaseModel):
    latex: str
    beam_score: float
    model: ModelInfo
    duration_s: float
    math_parse: MathParseStatus


class ModelReadiness(BaseModel):
    status: Literal["ready", "loading", "standby", "unavailable", "unconfigured"]
    detail: str


class ReadyResponse(BaseModel):
    api: Literal["ok"] = "ok"
    model: ModelReadiness
