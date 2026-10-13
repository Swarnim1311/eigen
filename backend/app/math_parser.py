"""Eigen safe mathematical engine (Phase 2).

SECURITY MODEL — read before touching this file:
- User input is NEVER executed. No eval(), no exec(), no sympy.sympify() /
  sympy.parsing.* on untrusted strings. Expressions are built ONLY from
  individually validated tokens (digit strings, allowlisted variable names)
  using explicit SymPy constructors (Integer, Rational, Symbol, Add, Mul, Pow).
- Anything outside the documented grammar is rejected, never guessed.

DOCUMENTED GRAMMAR (v1):
  expr    := term (('+' | '-') term)*
  term    := unary (('*' | '/') unary | IMPLICIT unary)*
  unary   := '-' unary | power
  power   := primary (('^' | '**') unary)?        # right-associative; -2^2 = -(2^2)
  primary := number | variable | 'sqrt' '(' expr ')' | '(' expr ')'
  equation:= expr '=' expr                        # exactly one '=' (solve only)

  - number: integers and decimals, e.g. 12, 0.5, .5 is REJECTED (must lead digit).
    No scientific notation, no fractions syntax, no percent.
  - variable: exactly the set {x, y, z, t}. Anything else (including function
    names like sin/log, dunders, attributes) is rejected.
  - sqrt(): the single supported function, always with explicit parentheses.
  - IMPLICIT multiplication: 2x, 2(x+1), (a+b)(c+d), x( — a number, variable or
    ')' directly followed by a variable or '('.
  - LaTeX input is NOT parsed directly. latex_to_ascii() translates a tiny
    documented subset (\\frac{A}{B}, \\cdot, \\times, \\div, \\left/\\right,
    thin spaces) to the ASCII grammar; everything else (including \\sqrt,
    subscripts, matrices) is rejected as unsupported.

LIMITS (v1): input <= 500 chars; AST nodes <= 300; number literals <= 15 digits;
integer exponent literals |e| <= 100; result strings <= 2000 chars. solve() is
limited to univariate equations in one allowlisted variable; solutions are
verified by substitution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Union

import sympy
from sympy import Add, Integer, Mul, Pow, Rational, Symbol

VARIABLES = ("x", "y", "z", "t")

MAX_INPUT_LEN = 500
MAX_NODES = 300
MAX_DEPTH = 100
MAX_LITERAL_DIGITS = 15
MAX_INT_EXPONENT = 100
MAX_RESULT_CHARS = 2000

_TOKEN_RE = re.compile(
    r"""
    (?P<NUMBER>\d+(?:\.\d+)?)
  | (?P<IDENT>[A-Za-z]+)
  | (?P<POW2>\*\*)
  | (?P<OP>[+\-*/^()=])
  | (?P<SPACE>\s+)
  | (?P<BAD>.)
""",
    re.VERBOSE,
)


class MathError(Exception):
    """Structured engine error. `code` maps to API error codes."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class Token:
    kind: str
    value: str


def tokenize(src: str) -> list[Token]:
    if not src or not src.strip():
        raise MathError("empty_input", "Expression is empty.")
    if len(src) > MAX_INPUT_LEN:
        raise MathError("input_too_long", f"Expression exceeds {MAX_INPUT_LEN} characters.")
    tokens: list[Token] = []
    for m in _TOKEN_RE.finditer(src):
        kind = m.lastgroup or "BAD"
        if kind == "SPACE":
            continue
        if kind == "BAD":
            raise MathError("bad_token", f"Unsupported character {m.group(0)!r}.")
        tokens.append(Token(kind, m.group(0)))
    if not tokens:
        raise MathError("empty_input", "Expression is empty.")
    return tokens


class _Parser:
    """Recursive-descent parser building SymPy objects from validated tokens."""

    def __init__(self, tokens: list[Token]) -> None:
        self.toks = tokens
        self.pos = 0
        self.nodes = 0
        self.depth = 0

    def _count(self) -> None:
        self.nodes += 1
        if self.nodes > MAX_NODES:
            raise MathError("too_complex", f"Expression exceeds {MAX_NODES} operations.")

    def _nest(self):
        """Depth guard against stack exhaustion on degenerate nesting."""

        class _Guard:
            def __init__(guard_self, outer) -> None:
                guard_self.outer = outer

            def __enter__(guard_self) -> None:
                guard_self.outer.depth += 1
                if guard_self.outer.depth > MAX_DEPTH:
                    raise MathError("too_complex", f"Nesting exceeds depth {MAX_DEPTH}.")

            def __exit__(guard_self, *args) -> bool:
                guard_self.outer.depth -= 1
                return False

        return _Guard(self)

    def peek(self) -> Token | None:
        return self.toks[self.pos] if self.pos < len(self.toks) else None

    def next(self) -> Token:
        tok = self.peek()
        if tok is None:
            raise MathError("parse_error", "Unexpected end of expression.")
        self.pos += 1
        return tok

    def expect_op(self, op: str) -> None:
        tok = self.next()
        if tok.value != op:
            raise MathError("parse_error", f"Expected {op!r} but found {tok.value!r}.")

    # expr := term (('+'|'-') term)*
    def parse_expr(self):
        node = self.parse_term()
        while (t := self.peek()) is not None and t.value in ("+", "-"):
            self.next()
            rhs = self.parse_term()
            self._count()
            node = Add(node, rhs) if t.value == "+" else Add(node, -rhs)
        return node

    # term := unary (('*'|'/') unary | IMPLICIT unary)*
    def parse_term(self):
        node = self.parse_unary()
        while True:
            t = self.peek()
            if t is None:
                return node
            if t.value == "*":
                self.next()
                node = self._mul(node, self.parse_unary())
            elif t.value == "/":
                self.next()
                node = self._mul(node, Pow(self.parse_unary(), Integer(-1)))
            elif t.kind in ("NUMBER", "IDENT") or t.value == "(":
                # implicit multiplication: 2x, 2(x+1), )(, x(
                node = self._mul(node, self.parse_unary())
            else:
                return node

    def _mul(self, a, b):
        self._count()
        return Mul(a, b)

    # unary := '-' unary | power
    def parse_unary(self):
        t = self.peek()
        if t is not None and t.value == "-":
            self.next()
            self._count()
            with self._nest():
                return -self.parse_unary()
        if t is not None and t.value == "+":
            raise MathError("parse_error", "Unexpected '+'. Unary plus is not supported.")
        return self.parse_power()

    # power := primary (('^'|'**') unary)?
    def parse_power(self):
        base = self.parse_primary()
        t = self.peek()
        if t is not None and t.value in ("^", "**"):
            self.next()
            exp_tok = self.peek()
            with self._nest():
                exp = self.parse_unary()
            if (
                exp_tok is not None
                and exp_tok.kind == "NUMBER"
                and exp.is_Integer
                and abs(int(exp)) > MAX_INT_EXPONENT
            ):
                raise MathError("too_complex", f"Exponent magnitude capped at {MAX_INT_EXPONENT}.")
            self._count()
            return Pow(base, exp)
        return base

    # primary := number | variable | sqrt '(' expr ')' | '(' expr ')'
    def parse_primary(self):
        tok = self.next()
        if tok.kind == "NUMBER":
            digits = tok.value.replace(".", "")
            if len(digits) > MAX_LITERAL_DIGITS:
                raise MathError("too_complex", f"Number exceeds {MAX_LITERAL_DIGITS} digits.")
            if "." in tok.value:
                return Rational(tok.value)  # exact: Rational('0.1') == 1/10
            return Integer(tok.value)
        if tok.kind == "IDENT":
            if tok.value == "sqrt":
                self.expect_op("(")
                with self._nest():
                    inner = self.parse_expr()
                self.expect_op(")")
                self._count()
                return sympy.sqrt(inner)
            if tok.value in VARIABLES:
                return Symbol(tok.value)
            raise MathError(
                "unknown_variable",
                f"Unsupported name {tok.value!r}. Variables: "
                f"{', '.join(VARIABLES)}; sole function: sqrt().",
            )
        if tok.value == "(":
            with self._nest():
                node = self.parse_expr()
            self.expect_op(")")
            return node
        raise MathError("parse_error", f"Unexpected {tok.value!r}.")


def parse_expression(src: str):
    """Parse ASCII grammar -> SymPy expression. Raises MathError."""
    parser = _Parser(tokenize(src))
    node = parser.parse_expr()
    if parser.peek() is not None:
        raise MathError(
            "parse_error",
            f"Unexpected trailing {parser.peek().value!r}. "
            "An equation must contain exactly one '='; "
            "use /math/solve for equations.",
        )
    return node


def parse_equation(src: str):
    """Parse 'expr = expr' -> (lhs, rhs). Raises MathError."""
    if not src or not src.strip():
        raise MathError("empty_input", "Equation is empty.")
    if len(src) > MAX_INPUT_LEN:
        raise MathError("input_too_long", f"Equation exceeds {MAX_INPUT_LEN} characters.")
    if src.count("=") != 1:
        raise MathError("parse_error", "An equation must contain exactly one '='.")
    lhs_src, rhs_src = src.split("=", 1)
    return parse_expression(lhs_src), parse_expression(rhs_src)


# ---------------- LaTeX subset translator ----------------

_LATEX_SKIP = ("\\left", "\\right", "\\,", "\\;", "\\:", "\\!")
_LATEX_MUL = {"\\cdot": "*", "\\times": "*", "\\div": "/"}


def latex_to_ascii(src: str) -> str:
    """Translate a tiny documented LaTeX subset to the ASCII grammar.

    Supported: \\frac{A}{B} (nested), \\cdot \\times \\div, \\left \\right,
    thin spaces. Anything else starting with backslash is rejected.
    The result is re-parsed by the same safe grammar — never executed.
    """
    if not src or not src.strip():
        raise MathError("empty_input", "LaTeX input is empty.")
    out: list[str] = []
    i, n = 0, len(src)

    def read_group(j: int) -> tuple[str, int]:
        if j >= n or src[j] != "{":
            raise MathError("unsupported_syntax", "Expected '{...}' group in LaTeX input.")
        depth = 0
        k = j
        while k < n:
            if src[k] == "{":
                depth += 1
            elif src[k] == "}":
                depth -= 1
                if depth == 0:
                    return src[j + 1 : k], k + 1
            k += 1
        raise MathError("parse_error", "Unbalanced '{' in LaTeX input.")

    while i < n:
        if src[i] == "\\":
            matched = False
            for cmd in sorted(_LATEX_SKIP, key=len, reverse=True):
                if src.startswith(cmd, i):
                    i += len(cmd)
                    matched = True
                    break
            if matched:
                continue
            for cmd, rep in _LATEX_MUL.items():
                if src.startswith(cmd, i):
                    out.append(rep)
                    i += len(cmd)
                    matched = True
                    break
            if matched:
                continue
            if src.startswith("\\frac", i):
                i += len("\\frac")
                while i < n and src[i].isspace():
                    i += 1
                num, i = read_group(i)
                while i < n and src[i].isspace():
                    i += 1
                den, i = read_group(i)
                out.append(f"(({latex_to_ascii(num)})/({latex_to_ascii(den)}))")
                continue
            m = re.match(r"\\[A-Za-z]+", src[i:])
            raise MathError(
                "unsupported_syntax",
                f"Unsupported LaTeX command {(m.group(0) if m else chr(92))!r}. "
                "Supported: \\frac, \\cdot, \\times, \\div.",
            )
        else:
            out.append(src[i])
            i += 1
    return "".join(out)


# ---------------- operations ----------------


def _check_result(result) -> None:
    if result is sympy.zoo or result in (sympy.oo, -sympy.oo, sympy.nan):
        raise MathError("division_by_zero", "Operation involves division by zero.")
    if result.has(sympy.I):
        raise MathError("complex_result", "Complex-valued results are not supported in v1.")


def render_result(result) -> str:
    text = str(result)
    if len(text) > MAX_RESULT_CHARS:
        raise MathError("too_complex", "Result exceeds display limits.")
    return text


def evaluate(expr: sympy.Basic, variables: dict[str, float] | None = None):
    """Numerically evaluate a parsed expression with optional substitution."""
    subs = {}
    if variables:
        for name, value in variables.items():
            if name not in VARIABLES:
                raise MathError("unknown_variable", f"Unsupported variable {name!r}.")
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise MathError("parse_error", f"Variable {name!r} must be a number.")
            # JSON transports all numbers as float; restore exact integers so
            # results stay exact (3.0 -> 3) instead of Float artifacts.
            if isinstance(value, float) and value.is_integer():
                value = int(value)
            subs[Symbol(name)] = value
    result = expr.subs(subs) if subs else expr
    free = result.free_symbols
    if free:
        names = sorted(str(s) for s in free)
        raise MathError(
            "unbound_variable",
            f"Unbound variable(s): {', '.join(names)}. Provide values or use /math/simplify.",
        )
    result = sympy.simplify(result)
    _check_result(result)
    return result


def simplify_expr(expr: sympy.Basic):
    return sympy.simplify(expr)


def solve_equation(lhs, rhs, variable: str):
    """Solve lhs == rhs for one allowlisted variable. Verified by substitution."""
    if variable not in VARIABLES:
        raise MathError("unknown_variable", f"Can only solve for: {', '.join(VARIABLES)}.")
    var = Symbol(variable)
    eq = lhs - rhs
    if var not in eq.free_symbols:
        raise MathError("solve_failed", f"Variable {variable!r} does not occur in the equation.")
    others = {str(s) for s in eq.free_symbols} - {variable}
    if others:
        raise MathError(
            "unsupported_syntax",
            f"Multi-variable solving not supported (also found: {', '.join(sorted(others))}).",
        )
    try:
        solutions = sympy.solve(eq, var, dict=False)
    except Exception:
        raise MathError("solve_failed", "Equation could not be solved with the v1 solver.")
    if not solutions:
        raise MathError("solve_failed", "No solutions found.")
    if len(solutions) > 20:
        raise MathError("too_complex", "Too many solutions to report.")
    verified = []
    for s in solutions:
        try:
            if sympy.simplify(eq.subs(var, s)) == 0:
                _check_result(s)
                verified.append(s)
        except MathError:
            raise
        except Exception:
            continue
    if not verified:
        raise MathError("solve_failed", "No verifiable solutions found.")
    return verified


ExprNode = Union[sympy.Basic]
