"""Security regression tests: unsafe execution must stay impossible.

Two layers:
1. Static AST guard — backend/app must never gain eval()/exec()/compile()/
   sympify() call sites or __import__ usage (comments/docstrings are ignored
   because the check runs on the parsed AST, not text).
2. Behavioral — hostile payloads through the real HTTP endpoints are rejected
   with the structured {error:{code,message}} envelope and never executed.
"""

import ast
import pathlib

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"

BANNED_CALLS = {"eval", "exec", "compile", "sympify", "__import__"}


def _call_names(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id in BANNED_CALLS:
                yield f.id
            elif isinstance(f, ast.Attribute) and f.attr in BANNED_CALLS:
                # re.compile() is regex construction, not code execution.
                if isinstance(f.value, ast.Name) and f.value.id == "re":
                    continue
                yield f.attr


def test_no_unsafe_calls_in_backend_source():
    offenders = []
    for path in sorted(APP_DIR.rglob("*.py")):
        names = set(_call_names(ast.parse(path.read_text(encoding="utf-8"))))
        if names:
            offenders.append(f"{path.name}: {sorted(names)}")
    assert offenders == [], f"unsafe call sites introduced: {offenders}"


def test_injection_payloads_rejected_over_http():
    payloads = [
        "__import__('os').system('x')",
        "eval('1+1')",
        "exec('x')",
        "open('/etc/passwd').read()",
        "().__class__.__bases__",
        "[x for x in y]",
        "lambda: 1",
        "import os",
        "x; y",
    ]
    for p in payloads:
        r = client.post("/api/v1/math/evaluate", json={"expression": p})
        assert r.status_code in (400, 422), p
        body = r.json()
        assert set(body) == {"error"} and set(body["error"]) == {"code", "message"}, p


def test_oversize_and_malformed_rejected_over_http():
    r = client.post("/api/v1/math/evaluate", json={"expression": "1+" * 300})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "input_too_long"
    r = client.post("/api/v1/math/evaluate", json={"expression": "9" * 16})
    assert r.json()["error"]["code"] == "too_complex"
    r = client.post("/api/v1/math/evaluate", json={})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_solve_degenerate_equations():
    for eq in ["0=0", "x=x", "1=1"]:
        r = client.post("/api/v1/math/solve", json={"equation": eq, "variable": "x"})
        assert r.status_code == 422, eq
        assert r.json()["error"]["code"] == "solve_failed", eq
