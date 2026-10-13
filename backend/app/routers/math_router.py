"""Eigen math routes: /api/v1/math/{evaluate,simplify,solve}."""

from fastapi import APIRouter

from app import math_parser as mp
from app.schemas import (
    EvaluateRequest,
    EvaluateResponse,
    SimplifyRequest,
    SimplifyResponse,
    SolveRequest,
    SolveResponse,
)

router = APIRouter(prefix="/api/v1/math", tags=["math"])


def _ascii(body_latex: bool, src: str) -> str:
    if body_latex:
        return mp.latex_to_ascii(src)
    return src


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(body: EvaluateRequest) -> EvaluateResponse:
    expr = mp.parse_expression(_ascii(body.latex, body.expression))
    result = mp.evaluate(expr, body.variables or None)
    try:
        decimal: float | None = float(result)
    except Exception:
        decimal = None
    return EvaluateResponse(
        result=mp.render_result(result), decimal=decimal, expression=body.expression
    )


@router.post("/simplify", response_model=SimplifyResponse)
def simplify(body: SimplifyRequest) -> SimplifyResponse:
    expr = mp.parse_expression(_ascii(body.latex, body.expression))
    return SimplifyResponse(
        result=mp.render_result(mp.simplify_expr(expr)), expression=body.expression
    )


@router.post("/solve", response_model=SolveResponse)
def solve(body: SolveRequest) -> SolveResponse:
    lhs, rhs = mp.parse_equation(body.equation)
    solutions = mp.solve_equation(lhs, rhs, body.variable.strip())
    rendered = [mp.render_result(s) for s in solutions]
    return SolveResponse(variable=body.variable.strip(), solutions=rendered, count=len(rendered))
