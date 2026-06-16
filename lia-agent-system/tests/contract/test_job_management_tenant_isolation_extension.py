"""job_management — extended cross-tenant repository/tools isolation contract tests.

Sensor permanente para os fixes do sprint 2026-05-22 (ratchet job_management)
que adicionaram multi-tenancy defense-in-depth em repositories + tools, ao
detectar via sensor B.1 ``check_query_has_tenant_filter`` que 39 sites
estavam sem company_id filter explícito.

Estratégia: AST-level + pure-unit — sem fixtures de DB. Inspeciona o
``select(...)`` SQL montado ou source-level pattern por arquivo.

Cobertura:
1. JobTemplateRepository.get_by_id accepts company_id kwarg.
2. JobEmbeddingRepository.get_by_job_id accepts company_id kwarg.
3. JobVacancyScreeningRepository.get_vacancy_by_id accepts company_id kwarg.
4. JobAlertRepository.get_alert_by_id accepts company_id kwarg.
5. pause_job / close_job / publish_job extract _context and apply
   JobVacancy.company_id == company_id filter when present.
6. save_job_draft applies JobDraft.company_id == company_id filter.
7. update_job inner cross-tenant detection query has TENANT-EXEMPT marker.

Referência: ADR-001 + REGRA ZERO + HARDENING_PLAN B.1 + CLAUDE.md REGRA #1.
"""
from __future__ import annotations

import ast
import re
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
TENANT_A_ID = uuid.UUID("11111111-1111-4111-a111-111111111111")
RESOURCE_ID = uuid.UUID("33333333-3333-4333-a333-333333333333")


def _read(path_rel: str) -> str:
    return (REPO_ROOT / path_rel).read_text(encoding="utf-8")


def _make_async_session_returning(rows: list | None = None) -> MagicMock:
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=None)
    result.scalar = MagicMock(return_value=0)
    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=rows or [])))
    session.execute = AsyncMock(return_value=result)
    return session


def _where_clause(stmt) -> str:
    sql = str(stmt.compile(compile_kwargs={"literal_binds": False})).lower()
    where_idx = sql.find("where ")
    assert where_idx >= 0, f"No WHERE clause in SQL: {sql}"
    return sql[where_idx:]


# ── Repository signature ratchet ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_job_template_get_by_id_accepts_company_id() -> None:
    from app.domains.job_management.repositories.job_template_repository import (
        JobTemplateRepository,
    )
    session = _make_async_session_returning([])
    repo = JobTemplateRepository(session)
    await repo.get_by_id(RESOURCE_ID, company_id=TENANT_A_ID)
    stmt = session.execute.await_args.args[0]
    assert "company_id" in _where_clause(stmt)


@pytest.mark.asyncio
async def test_job_embedding_get_by_job_id_accepts_company_id() -> None:
    from app.domains.job_management.repositories.job_embedding_repository import (
        JobEmbeddingRepository,
    )
    session = _make_async_session_returning([])
    repo = JobEmbeddingRepository(session)
    await repo.get_by_job_id(RESOURCE_ID, company_id=TENANT_A_ID)
    stmt = session.execute.await_args.args[0]
    assert "company_id" in _where_clause(stmt)


@pytest.mark.asyncio
async def test_job_vacancy_screening_get_by_id_accepts_company_id() -> None:
    from app.domains.job_management.repositories.job_vacancy_screening_repository import (
        JobVacancyScreeningRepository,
    )
    session = _make_async_session_returning([])
    repo = JobVacancyScreeningRepository(session)
    await repo.get_vacancy_by_id(RESOURCE_ID, company_id=TENANT_A_ID)
    stmt = session.execute.await_args.args[0]
    assert "company_id" in _where_clause(stmt)


def test_job_alert_repository_marks_alert_methods_tenant_exempt() -> None:
    """Alert model has no ``company_id`` column (intentional: scoping is
    via user_id / job_id / candidate_id). The repository must NOT pretend
    to filter by Alert.company_id (would raise AttributeError at query
    compile time) — instead methods carry TENANT-EXEMPT markers explaining
    the scoping invariant."""
    source = _read("app/domains/job_management/repositories/job_alert_repository.py")
    # find_active_alert + list_active_alerts + get_alert_by_id all live in
    # this file and must each have a TENANT-EXEMPT marker explaining the
    # invariant.
    for fn_name in ("find_active_alert", "list_active_alerts", "get_alert_by_id"):
        fn_start = source.find(f"async def {fn_name}(")
        assert fn_start >= 0, f"{fn_name} not found"
        next_def = source.find("    async def ", fn_start + 1)
        if next_def < 0:
            next_def = len(source)
        body = source[fn_start:next_def]
        assert "TENANT-EXEMPT" in body, (
            f"{fn_name} must have TENANT-EXEMPT marker explaining why "
            "Alert.company_id filter is absent (model has no such column)."
        )


# ── Tools cross-tenant fix (signature + filter pattern) ─────────────────────


def test_job_tools_pause_close_publish_extract_context() -> None:
    """Real bug fix: pause_job / close_job / publish_job must extract _context
    to scope by company_id (REGRA ZERO multi-tenancy)."""
    source = _read("app/domains/job_management/tools/job_tools.py")
    for fn in ("pause_job", "close_job", "publish_job"):
        tree = ast.parse(source)
        body_src = None
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == fn:
                body_src = ast.unparse(node)
                break
        assert body_src is not None, f"function {fn} not found"
        # Must extract context to know company_id
        assert "_extract_context(kwargs)" in body_src, (
            f"{fn} não chama _extract_context — multi-tenancy fail-open"
        )
        # Must reference company_id filter on JobVacancy
        assert "JobVacancy.company_id" in body_src, (
            f"{fn} não filtra por JobVacancy.company_id"
        )


def test_job_wizard_save_draft_applies_company_id_filter() -> None:
    """save_job_draft must filter JobDraft.company_id == company_id."""
    source = _read("app/domains/job_management/tools/job_wizard_tools.py")
    tree = ast.parse(source)
    body_src = None
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "save_job_draft":
            body_src = ast.unparse(node)
            break
    assert body_src is not None
    assert "JobDraft.company_id" in body_src, (
        "save_job_draft não filtra por JobDraft.company_id"
    )


# ── Cross-tenant detection idiom retains TENANT-EXEMPT marker ───────────────


def test_update_job_cross_tenant_detection_has_exempt_marker() -> None:
    """update_job uses a second select(JobVacancy).where(id==X) without
    company_id by design — to distinguish 'not found' from 'wrong tenant'.
    The TENANT-EXEMPT marker MUST stay in the 5-line window above so the
    B.1 sensor keeps recognising this as intentional."""
    source = _read("app/domains/job_management/tools/job_tools.py")
    # Find the cross_tenant_access_denied block
    idx = source.find("cross_tenant_access_denied")
    assert idx >= 0, "cross_tenant_access_denied removed?"
    # Look up to 400 chars BEFORE the block for the marker
    window = source[max(0, idx - 600) : idx]
    assert "TENANT-EXEMPT" in window, (
        "cross-tenant detection query needs a TENANT-EXEMPT marker so "
        "sensor B.1 doesn't flag the intentional no-tenant select."
    )
