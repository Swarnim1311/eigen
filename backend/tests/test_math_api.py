"""API tests for /api/v1/math/*: schemas, results, error shapes."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_evaluate_basic():
    r = client.post("/api/v1/math/evaluate", json={"expression": "2*(3+4)^2"})
    assert r.status_code == 200
    body = r.json()
    assert body["result"] == "98"
    assert body["decimal"] == 98.0
    assert body["expression"] == "2*(3+4)^2"


def test_evaluate_fraction_exact_and_decimal():
    r = client.post("/api/v1/math/evaluate", json={"expression": "1/3"})
    assert r.status_code == 200
    assert r.json()["result"] == "1/3"
    assert abs(r.json()["decimal"] - 1 / 3) < 1e-12


def test_evaluate_with_variables():
    r = client.post("/api/v1/math/evaluate", json={"expression": "x^2+2*x", "variables": {"x": 3}})
    assert r.status_code == 200
    assert r.json()["result"] == "15"


def test_evaluate_latex_flag():
    r = client.post(
        "/api/v1/math/evaluate", json={"expression": r"\frac{1}{2}+\frac{1}{4}", "latex": True}
    )
    assert r.status_code == 200
    assert r.json()["result"] == "3/4"


def test_simplify():
    r = client.post("/api/v1/math/simplify", json={"expression": "(x+1)^2-x^2-2*x"})
    assert r.status_code == 200
    assert r.json()["result"] == "1"


def test_solve_linear_and_quadratic():
    r = client.post("/api/v1/math/solve", json={"equation": "2*x+3=7", "variable": "x"})
    assert r.status_code == 200
    assert r.json() == {"variable": "x", "solutions": ["2"], "count": 1}
    r = client.post("/api/v1/math/solve", json={"equation": "x^2=4", "variable": "x"})
    assert r.status_code == 200
    assert r.json()["count"] == 2
    assert sorted(r.json()["solutions"]) == ["-2", "2"]


def test_error_shape_and_codes():
    cases = [
        ({"expression": "1/0"}, 422, "division_by_zero"),
        ({"expression": "__import__('os')"}, 400, "bad_token"),
        ({"expression": "y+1"}, 422, "unbound_variable"),
        ({"expression": "2^101"}, 422, "too_complex"),
        ({"expression": ""}, 422, "validation_error"),  # pydantic min_length
        ({"expression": "   "}, 400, "empty_input"),
    ]
    for payload, status, code in cases:
        r = client.post("/api/v1/math/evaluate", json=payload)
        assert r.status_code == status, payload
        assert r.json() == {"error": {"code": code, "message": r.json()["error"]["message"]}}


def test_solve_errors():
    r = client.post("/api/v1/math/solve", json={"equation": "x+y=2", "variable": "x"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unsupported_syntax"
    r = client.post("/api/v1/math/solve", json={"equation": "x=x", "variable": "x"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "solve_failed"
