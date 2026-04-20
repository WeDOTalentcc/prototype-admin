"""End-to-end isolation test for the tool registries.

Iterates over every ``ToolDefinition`` exported by the major LIA tool
registries (autonomous, sourcing, pipeline + cv_screening, kanban) and
asserts that invoking it without ``company_id`` returns the documented
"missing tenant context" failure response produced by
``app.shared.tool_handler.tool_handler``.

Tools intentionally exempt are skipped via an allow-list derived from the
``# require_company=False kept:`` comments in each registry's source.
This guards against regressions where someone re-adds
``require_company=False`` (or otherwise bypasses the tenant check) and
silently exposes cross-tenant data to the agent.
"""
from __future__ import annotations

import importlib
import inspect
import re
from typing import Any

import pytest

from app.shared.tool_handler import _TENANT_REQUIRED_RESPONSE


# Registries we want fully covered by this test. Each entry lists the
# attributes on the module that hold one or more ``ToolDefinition`` lists
# (or maps keyed by tool name).
REGISTRY_SOURCES: list[tuple[str, tuple[str, ...]]] = [
    (
        "app.domains.autonomous.agents.autonomous_tool_registry",
        ("AUTONOMOUS_TOOL_POOL",),
    ),
    (
        "app.domains.sourcing.agents.sourcing_tool_registry",
        ("TOOL_DEFINITIONS",),
    ),
    (
        "app.domains.pipeline.agents.pipeline_tool_registry",
        ("ALL_TOOLS", "_CV_SCREENING_TOOL_DEFINITIONS"),
    ),
    (
        "app.domains.recruiter_assistant.agents.kanban_tool_registry",
        ("TOOL_DEFINITIONS",),
    ),
]


_KEPT_RE = re.compile(r"#\s*require_company\s*=\s*False\s*kept\s*:", re.IGNORECASE)
_DEF_RE = re.compile(r"^\s*(?:async\s+def|def)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _exempt_function_names(module) -> set[str]:
    """Scan a registry's source and return the set of function names whose
    decorator carries ``require_company=False`` (i.e. the documented
    exemptions tagged with a ``# require_company=False kept:`` comment).
    """
    try:
        source = inspect.getsource(module)
    except OSError:  # pragma: no cover - source always available in repo
        return set()

    lines = source.splitlines()
    exempt: set[str] = set()
    for idx, line in enumerate(lines):
        if not _KEPT_RE.search(line):
            continue
        # Walk forward from the comment looking for the next def/async def.
        for forward in range(idx + 1, min(idx + 10, len(lines))):
            m = _DEF_RE.match(lines[forward])
            if m:
                exempt.add(m.group(1))
                break
    return exempt


def _collect_tools(module, attrs: tuple[str, ...]):
    """Yield unique (tool_name, function) pairs from a module's exports."""
    seen: set[int] = set()
    for attr in attrs:
        container = getattr(module, attr, None)
        if container is None:
            continue
        items = container.values() if isinstance(container, dict) else container
        for tool in items:
            fn = getattr(tool, "function", None)
            if fn is None or id(fn) in seen:
                continue
            seen.add(id(fn))
            yield getattr(tool, "name", getattr(fn, "__name__", "?")), fn


def _build_cases() -> list[tuple[str, str, str, Any]]:
    """Return [(module_path, tool_name, fn_name, fn), ...] for non-exempt tools.

    Import failures bubble up as real test errors instead of silent skips so
    a broken registry can never hide behind an empty parametrize set.
    """
    cases: list[tuple[str, str, str, Any]] = []
    for module_path, attrs in REGISTRY_SOURCES:
        module = importlib.import_module(module_path)
        exempt = _exempt_function_names(module)
        for tool_name, fn in _collect_tools(module, attrs):
            fn_name = getattr(fn, "__name__", "?")
            if fn_name in exempt:
                continue
            cases.append((module_path, tool_name, fn_name, fn))
    return cases


_CASES = _build_cases()


@pytest.fixture(autouse=True)
def _reset_tenant_contextvar():
    """Ensure no stray tenant context leaks into these tests.

    `tool_handler` falls back to `_current_company_id` when no kwargs are
    given. We reset it before each case so a previously-run test (or an
    import-time side effect) cannot mask a missing-tenant regression.
    """
    try:
        from app.middleware.auth_enforcement import _current_company_id
    except Exception:
        yield
        return
    token = _current_company_id.set("")
    try:
        yield
    finally:
        _current_company_id.reset(token)


def test_registries_yield_tools() -> None:
    """Sanity: at least one tool per registry must be covered."""
    assert _CASES, "No tools collected — registries imported empty?"
    covered_modules = {c[0] for c in _CASES}
    for module_path, _ in REGISTRY_SOURCES:
        assert module_path in covered_modules, (
            f"No non-exempt tools found in {module_path}; allow-list may be too broad."
        )


@pytest.mark.parametrize(
    ("module_path", "tool_name", "fn_name", "fn"),
    _CASES,
    ids=[f"{c[0].rsplit('.', 1)[-1]}::{c[1]}" for c in _CASES],
)
async def test_tool_rejects_missing_company_id(
    module_path: str, tool_name: str, fn_name: str, fn: Any
) -> None:
    """Each tool with require_company=True (the default) must fail-closed
    when invoked without a company_id and without any fallback context.
    """
    result = await fn()  # no kwargs → no company_id, no _context, no contextvar

    assert isinstance(result, dict), (
        f"{module_path}.{fn_name} returned {type(result).__name__}, expected dict"
    )
    assert result.get("success") is False, (
        f"{module_path}.{fn_name} (tool={tool_name!r}) did NOT fail-closed without "
        f"company_id; got: {result!r}"
    )
    assert result.get("message") == _TENANT_REQUIRED_RESPONSE["message"], (
        f"{module_path}.{fn_name} (tool={tool_name!r}) returned a non-tenant "
        f"failure message: {result.get('message')!r}. This usually means the "
        f"@tool_handler decorator was bypassed or replaced."
    )
    assert result.get("data") == {}, (
        f"{module_path}.{fn_name} (tool={tool_name!r}) leaked data in the "
        f"missing-tenant response: {result.get('data')!r}"
    )
