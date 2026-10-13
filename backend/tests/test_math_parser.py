"""Unit tests for the safe math engine: grammar, limits, security."""

import pytest

from app import math_parser as mp


def ev(src, variables=None):
    return mp.evaluate(mp.parse_expression(src), variables)


def test_arithmetic_precedence():
    assert ev("2+3*4") == 14
    assert ev("2*(3+4)^2") == 98
    assert ev("2**2**2") == 16  # right-associative: 2^(2^2)
    assert ev("-2^2") == -4  # -(2^2)
    assert ev("10-2-3") == 5
    assert ev("1/3") == mp.Rational(1, 3)


def test_implicit_multiplication():
    assert ev("2x", {"x": 3}) == 6
    assert ev("2(x+1)", {"x": 1}) == 4
    assert ev("(2+1)(3+4)") == 21
    assert ev("x(y+z)", {"x": 2, "y": 1, "z": 1}) == 4


def test_sqrt_and_decimals():
    assert ev("sqrt(16)") == 4
    assert ev("0.5+0.25") == mp.Rational(3, 4)  # exact, not float dust


def test_rejects_not_guesses():
    for bad in [
        "2+",
        "(2",
        "2++2",
        "+2",
        "2**",
        "sin(x)",
        "log(2)",
        "x_",
        ".5",
        "1e3",
        "2%3",
        "a=b",
        "2=2",
        "x^",
        "[1]",
        "{1}",
        "2;3",
        "x|y",
    ]:
        with pytest.raises(mp.MathError):
            mp.parse_expression(bad)
    # juxtaposition IS multiplication (documented): these are valid
    assert ev("2x3", {"x": 2}) == 12


def test_unknown_variables_rejected():
    for bad in ["q+1", "e+1", "X+1", "xy+1", "foo(2)"]:
        with pytest.raises(mp.MathError) as e:
            mp.parse_expression(bad)
        assert e.value.code == "unknown_variable"


def test_injection_attempts_rejected():
    payloads = [
        "__import__('os').system('x')",
        "open('/etc/passwd').read()",
        "eval('1+1')",
        "exec('x')",
        "x.__class__",
        "(lambda: 1)()",
        "().__class__.__bases__",
        "globals()",
        "().__class__",
        "import os",
    ]
    for p in payloads:
        with pytest.raises(mp.MathError):
            mp.parse_expression(p)


def test_division_by_zero():
    for bad in ["1/0", "0/0", "1/(2-2)"]:
        with pytest.raises(mp.MathError) as e:
            ev(bad)
        assert e.value.code == "division_by_zero"


def test_limits():
    with pytest.raises(mp.MathError) as e:
        mp.parse_expression("1+" * 300)
    assert e.value.code == "input_too_long"
    with pytest.raises(mp.MathError) as e:
        mp.parse_expression("9" * 16)
    assert e.value.code == "too_complex"  # >15 digits
    with pytest.raises(mp.MathError) as e:
        mp.parse_expression("2^101")
    assert e.value.code == "too_complex"
    # 7 parens fine:
    assert ev("(((((((1)))))))") == 1
    with pytest.raises(mp.MathError) as e:
        mp.parse_expression("(" * 150 + "1" + ")" * 150)
    assert e.value.code == "too_complex"  # depth guard, not RecursionError
    with pytest.raises(mp.MathError) as e:
        mp.parse_expression("")
    assert e.value.code == "empty_input"


def test_equations():
    lhs, rhs = mp.parse_equation("2*x+3=7")
    assert mp.solve_equation(lhs, rhs, "x") == [mp.Integer(2)]
    assert mp.solve_equation(*mp.parse_equation("x^2=4"), "x") is not None
    sols = mp.solve_equation(*mp.parse_equation("x^2=4"), "x")
    assert sorted(int(s) for s in sols) == [-2, 2]
    with pytest.raises(mp.MathError):
        mp.parse_equation("x==y")  # two '=' signs
    with pytest.raises(mp.MathError):
        mp.parse_equation("x+y")  # no '='
    with pytest.raises(mp.MathError) as e:
        mp.solve_equation(*mp.parse_equation("x+y=2"), "x")
    assert e.value.code == "unsupported_syntax"  # multi-variable
    with pytest.raises(mp.MathError) as e:
        mp.solve_equation(*mp.parse_equation("x=5"), "y")
    assert e.value.code == "solve_failed"


def test_latex_subset():
    assert mp.latex_to_ascii(r"\frac{1}{2}+\frac{1}{4}") is not None
    assert ev(mp.latex_to_ascii(r"\frac{1}{2}+\frac{1}{4}")) == mp.Rational(3, 4)
    assert ev(mp.latex_to_ascii(r"2\cdot x+3\times y"), {"x": 1, "y": 2}) == 8
    # translator rejects unknown commands outright:
    for bad in [r"\sqrt{4}", r"\sin x", r"\begin{matrix}"]:
        with pytest.raises(mp.MathError):
            mp.latex_to_ascii(bad)
    # braces/subscripts pass the translator but fail the safe grammar:
    with pytest.raises(mp.MathError):
        mp.parse_expression(mp.latex_to_ascii(r"x_{1}"))


def test_unbound_variable():
    with pytest.raises(mp.MathError) as e:
        ev("x+1")
    assert e.value.code == "unbound_variable"
