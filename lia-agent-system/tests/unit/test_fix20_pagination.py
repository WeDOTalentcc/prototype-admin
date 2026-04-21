"""FIX 20 (2026-04-21) — search_jobs pagination: offset + real total_count.

Red-Green TDD for pagination support in search_jobs. Closes the
"LIA says 20 vagas when user sees 50" bug from real chat audit.

Root cause (before FIX 20):
- query_tools.search_jobs had `limit: int = 20` and no offset parameter
- Return `data.total` was literally `len(jobs_list)` — same as page size
- Consequence: LIA announced "Encontrei 20 vagas" as if total == page

Canonical-fix (producer-side): search_jobs now runs a COUNT query before
LIMIT/OFFSET, returns true `total_count`, and exposes `pagination` block
so LLM can iterate pages and say "mostrando X de N".

This test is structural (signature + schema). Runtime behavior is
validated via smoke test on Replit post-restart.
"""
from __future__ import annotations

import inspect


def test_search_jobs_has_offset_parameter_default_zero() -> None:
    """FIX 20: search_jobs must accept `offset: int = 0` kwarg for pagination."""
    from app.domains.job_management.tools import query_tools

    sig = inspect.signature(query_tools.search_jobs)
    assert "offset" in sig.parameters, (
        "FIX 20: search_jobs signature must include `offset` for pagination. "
        "Without offset, LIA cannot request page 2+ and announces page count as total."
    )
    param = sig.parameters["offset"]
    assert param.default == 0, (
        f"FIX 20: offset default must be 0 (got {param.default!r})"
    )


def test_search_jobs_signature_preserves_existing_params() -> None:
    """FIX 20 regression guard: adding offset must not remove status/limit/filters."""
    from app.domains.job_management.tools import query_tools

    sig = inspect.signature(query_tools.search_jobs)
    required_existing = {
        "status", "department", "seniority", "work_model",
        "created_after", "created_before", "has_candidates",
        "min_candidates", "urgent", "recruiter_id", "limit",
    }
    missing = required_existing - set(sig.parameters)
    assert not missing, (
        f"FIX 20 must be additive; these existing params went missing: {missing}"
    )


def test_registered_schema_exposes_offset_and_total_count_hint() -> None:
    """FIX 20: tool schema advertised to LLM must expose `offset` property.

    Without offset in the schema, LLM has no way to paginate even if the
    handler supports it.
    """
    from app.domains.job_management.tools.query_tools import (
        register_job_management_query_tools,
    )
    from app.tools.registry import tool_registry

    register_job_management_query_tools()
    td = tool_registry.get_tool("search_jobs")
    assert td is not None, "search_jobs must be registered"
    schema = td.parameters_schema
    props = schema["properties"]
    assert "offset" in props, (
        "FIX 20: search_jobs schema must expose `offset` so LLM can paginate"
    )
    assert props["offset"]["type"] == "integer"
    assert props["offset"].get("default") == 0

    # Description must hint at pagination so LLM knows to use it
    assert "total_count" in td.description.lower() or "pagina" in td.description.lower(), (
        "FIX 20: tool description must mention pagination/total_count so LLM "
        "knows to iterate when has_more=True"
    )


def test_module_has_fix20_marker() -> None:
    """FIX 20 audit marker (traceability per canonical-fix protocol)."""
    from pathlib import Path

    import app.domains.job_management.tools.query_tools as qt

    source = Path(qt.__file__).read_text(encoding="utf-8")
    assert "FIX 20" in source, (
        "FIX 20: query_tools.py must contain `FIX 20` marker for traceability"
    )
    assert "total_count" in source, (
        "FIX 20: query_tools.py must compute and return total_count"
    )
