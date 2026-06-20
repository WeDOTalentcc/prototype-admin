"""
S05 — PII masking fail-soft (P-FAILLOUD + LGPD).

T-S05-a: when PII identity lookup throws, logger.error is emitted (not silently swallowed).
T-S05-b: when PII identity lookup throws, PII fields (name, email) are NOT exposed in
          the response — either masked with a safe fallback or the response raises.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_s05a_lookup_failure_logs_error():
    """PII identity lookup failure MUST log logger.error (P-FAILLOUD), not silently pass."""
    import inspect, ast
    import app.api.v1.agent_chat_sse as sse_module

    src = inspect.getsource(sse_module)
    tree = ast.parse(src)

    class SilentExceptFinder(ast.NodeVisitor):
        def __init__(self):
            self.silent_excepts = []

        def visit_ExceptHandler(self, node):
            body_calls = []
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Call):
                    func = stmt.func
                    if isinstance(func, ast.Attribute):
                        body_calls.append(func.attr)
            has_debug = "debug" in body_calls
            has_error = "error" in body_calls
            if has_debug and not has_error:
                self.silent_excepts.append((node.lineno, body_calls))
            self.generic_visit(node)

    finder = SilentExceptFinder()
    finder.visit(tree)
    pii_silent = [
        (ln, calls) for ln, calls in finder.silent_excepts
        if abs(ln - 530) < 30
    ]
    assert not pii_silent, (
        "PII masking except at line ~530 still silently debug-only. "
        "Found at lines: %s. "
        "Must use logger.error(..., exc_info=True) — P-FAILLOUD." % str(pii_silent)
    )


@pytest.mark.asyncio
async def test_s05b_lookup_failure_applies_safe_fallback():
    """When PII lookup raises, masked values must be safe defaults, not raw PII."""
    import app.api.v1.agent_chat_sse as sse_module
    import inspect

    src = inspect.getsource(sse_module)
    lines = src.splitlines()
    except_line = None
    for i, line in enumerate(lines, 1):
        if abs(i - 530) < 30 and "except" in line and "Exception" in line:
            except_line = i
            break

    if except_line is None:
        pytest.skip("Could not locate except block near line 530 — structure may have changed")

    block = "\n".join(lines[except_line - 1: except_line + 12])
    has_error_log = "logger.error" in block
    has_safe_fallback = (
        "_mask_b2 = True" in block
        or "_name_b2 = None" in block
        or "_safe_fallback" in block
        or "raise" in block
    )

    assert has_error_log, (
        "PII masking except block (line ~%d) missing logger.error. "
        "Block:\n%s" % (except_line, block)
    )
    assert has_safe_fallback, (
        "PII masking except block (line ~%d) missing safe fallback. "
        "After exception, PII fields must be explicitly set to safe defaults. "
        "Block:\n%s" % (except_line, block)
    )
