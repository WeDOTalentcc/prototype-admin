"""G2 canonical contract — search_jobs must fail-loud without tenant context.

The previous antipattern `company_id = context.company_id if context else None`
caused silent 0-rows when _context was missing from kwargs (orchestrator-level
gap). Per CLAUDE.md REGRA 4, the producer must fail-loud so the orchestrator
bug surfaces immediately, not as "0 vagas" puzzling the recruiter.

Red→Green:
- RED before fix: search_jobs(...) returns {"jobs": [], "count": 0} (silent).
- GREEN after fix: search_jobs(...) raises ToolContextMissingError.
"""
from __future__ import annotations

import pytest

from app.tools.context_helpers import (
    ToolContextMissingError,
    require_company_id_from_context,
)


def _ctx(company_id: str | None = "tenant-A", user_id: str = "u1"):
    """Construct a minimal ToolExecutionContext."""
    from app.tools.executor import ToolExecutionContext

    return ToolExecutionContext(
        user_id=user_id,
        company_id=company_id or "",
    )


class TestRequireCompanyIdFromContext:
    def test_raises_when_context_absent(self):
        kwargs: dict = {}
        with pytest.raises(ToolContextMissingError, match="without _context"):
            require_company_id_from_context(kwargs, "search_jobs")

    def test_raises_when_context_has_empty_company_id(self):
        ctx = _ctx(company_id="")
        kwargs = {"_context": ctx}
        with pytest.raises(ToolContextMissingError, match="empty company_id"):
            require_company_id_from_context(kwargs, "search_jobs")

    def test_returns_company_id_when_present(self):
        ctx = _ctx(company_id="tenant-X")
        kwargs = {"_context": ctx, "other": "kwarg"}
        result = require_company_id_from_context(kwargs, "search_jobs")
        assert result == "tenant-X"

    def test_removes_context_from_kwargs(self):
        ctx = _ctx(company_id="tenant-X")
        kwargs = {"_context": ctx, "other": "kwarg"}
        require_company_id_from_context(kwargs, "search_jobs")
        assert "_context" not in kwargs
        assert "other" in kwargs  # other kwargs preserved


@pytest.mark.asyncio
class TestSearchJobsFailLoud:
    async def test_search_jobs_raises_without_context(self):
        """RED→GREEN: search_jobs must raise (not return empty) when _context absent.

        This pins the canonical contract: silent 0-rows is forbidden by REGRA 4.
        """
        from app.domains.job_management.tools.query_tools import search_jobs

        with pytest.raises(ToolContextMissingError):
            await search_jobs()

    async def test_search_jobs_raises_with_empty_company_id(self):
        from app.domains.job_management.tools.query_tools import search_jobs

        ctx = _ctx(company_id="")
        with pytest.raises(ToolContextMissingError):
            await search_jobs(_context=ctx)
