"""TDD RED → GREEN tests for register_hire tool.

Camada 7 (Tool) — PR-HIRE audit fix.
Valida que register_hire faz write real no DB (não stub):
  - atualiza vacancy_candidates.status = "hired" + stage = "hired"
  - salva notes e registra hired_at
  - multi-tenant: rejeita quando company_id não confere
  - candidato not found → success: False
  - ausência de company_id → tenant isolation error (bloqueado pelo decorator)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, UTC
from uuid import uuid4


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_vacancy_candidate(company_id: str):
    """Mock VacancyCandidate instance with writable attributes."""
    vc = MagicMock()
    vc.company_id = company_id
    vc.status = "offer"
    vc.stage = "offer"
    vc.previous_status = "interview"
    vc.notes = None
    vc.stage_entered_at = None
    vc.updated_at = datetime.utcnow()
    return vc


def _make_db_session(vacancy_candidate=None, candidate=None):
    """Mock async DB session returning given objects from scalar_one_or_none."""
    db = AsyncMock()

    async def _execute_side_effect(query):
        # Return different mock results depending on what was queried
        result = MagicMock()
        if vacancy_candidate is not None:
            result.scalar_one_or_none.return_value = vacancy_candidate
        else:
            result.scalar_one_or_none.return_value = None
        return result

    db.execute = AsyncMock(side_effect=_execute_side_effect)
    db.commit = AsyncMock()
    db.__aenter__ = AsyncMock(return_value=db)
    db.__aexit__ = AsyncMock(return_value=False)
    return db


# ── Test 1: Happy path — writes hired status to DB ───────────────────────────

@pytest.mark.asyncio
async def test_register_hire_updates_vacancy_candidate_to_hired():
    """Core assertion: register_hire MUST write status='hired' to vacancy_candidates table."""
    company_id = "company-abc-123"
    candidate_id = str(uuid4())
    job_id = str(uuid4())

    vc = _make_vacancy_candidate(company_id)
    db = _make_db_session(vacancy_candidate=vc)

    with patch(
        "app.domains.pipeline.tools.pipeline_tools.AsyncSessionLocal",
        return_value=db,
    ):
        # Import the raw (unwrapped) function to call directly without decorator
        from app.domains.pipeline.tools import pipeline_tools as pt
        # The decorator wraps the function — we call the wrapper with company_id
        result = await pt.register_hire(
            candidate_id=candidate_id,
            job_id=job_id,
            notes="Candidato aprovado por unanimidade",
            company_id=company_id,
        )

    assert result["success"] is True, f"Expected success=True, got: {result}"
    # Core: DB commit was called (write happened)
    db.commit.assert_awaited_once()
    # Core: status and stage set to "hired" on the vacancy_candidate
    assert vc.status == "hired", f"Expected status='hired', got: {vc.status!r}"
    assert vc.stage == "hired", f"Expected stage='hired', got: {vc.stage!r}"
    # Notes preserved
    assert vc.notes == "Candidato aprovado por unanimidade"
    # hired_at returned in result
    assert "hired_at" in result
    assert result["candidate_id"] == candidate_id
    assert result["job_id"] == job_id


# ── Test 2: Cross-tenant isolation ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_hire_rejects_wrong_company_id():
    """Multi-tenant: vacancy_candidate.company_id != caller company_id → denied."""
    candidate_id = str(uuid4())
    job_id = str(uuid4())

    vc = _make_vacancy_candidate(company_id="other-company-999")
    db = _make_db_session(vacancy_candidate=vc)

    with patch(
        "app.domains.pipeline.tools.pipeline_tools.AsyncSessionLocal",
        return_value=db,
    ):
        from app.domains.pipeline.tools import pipeline_tools as pt
        result = await pt.register_hire(
            candidate_id=candidate_id,
            job_id=job_id,
            company_id="my-company-123",
        )

    assert result["success"] is False
    assert "tenant" in result.get("error", "").lower() or "acesso" in result.get("message", "").lower()
    # MUST NOT commit when cross-tenant
    db.commit.assert_not_awaited()


# ── Test 3: Candidate / VacancyCandidate not found ────────────────────────────

@pytest.mark.asyncio
async def test_register_hire_returns_error_when_vacancy_candidate_not_found():
    """If no VacancyCandidate row exists → success=False, no DB write."""
    db = _make_db_session(vacancy_candidate=None)

    with patch(
        "app.domains.pipeline.tools.pipeline_tools.AsyncSessionLocal",
        return_value=db,
    ):
        from app.domains.pipeline.tools import pipeline_tools as pt
        result = await pt.register_hire(
            candidate_id=str(uuid4()),
            job_id=str(uuid4()),
            company_id="company-xyz",
        )

    assert result["success"] is False
    db.commit.assert_not_awaited()


# ── Test 4: No company_id → tenant isolation blocks ──────────────────────────

@pytest.mark.asyncio
async def test_register_hire_blocked_without_company_id():
    """Decorator must block call when company_id is absent and no context set."""
    from app.domains.pipeline.tools import pipeline_tools as pt

    with patch("app.domains.pipeline.tools.pipeline_tools.AsyncSessionLocal") as mock_db:
        result = await pt.register_hire(
            candidate_id=str(uuid4()),
            job_id=str(uuid4()),
            # No company_id, no _context, no contextvar
        )

    assert result["success"] is False
    assert "company_id" in result.get("message", "").lower() or "tenant" in result.get("message", "").lower()
    mock_db.assert_not_called()


# ── Test 5: previous_status preserved ────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_hire_records_previous_status():
    """previous_status must be set to the stage before hiring (audit trail)."""
    company_id = "co-test"
    vc = _make_vacancy_candidate(company_id)
    vc.status = "offer"
    vc.stage = "offer"
    db = _make_db_session(vacancy_candidate=vc)

    with patch(
        "app.domains.pipeline.tools.pipeline_tools.AsyncSessionLocal",
        return_value=db,
    ):
        from app.domains.pipeline.tools import pipeline_tools as pt
        result = await pt.register_hire(
            candidate_id=str(uuid4()),
            job_id=str(uuid4()),
            company_id=company_id,
        )

    assert result["success"] is True
    # previous_status should reflect the prior stage
    assert vc.previous_status == "offer"
