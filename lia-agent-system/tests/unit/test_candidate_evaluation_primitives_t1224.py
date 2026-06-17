"""
Task #1224 — Primitivos de avaliação de candidato.

Sentinelas red→green para os dois primitivos compartilhados pelos fluxos 1/2/5:

(a) CVScoringService.score_candidate_standalone — pontuação BARS standalone/dry-run
    que avalia dados de candidato contra os requisitos da vaga SEM exigir
    VacancyCandidate persistido, mantendo PARIDADE de schema com o modal de CV
    (screen_candidate) e os gates FairnessGuard + AuditService + tenant.

(b) candidate_tools.add_candidate_to_vacancy — endurecido com validação de
    e-mail (presença + formato), gate C1 de FairnessGuard antes da escrita e
    trilha de auditoria.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.shared.compliance import scoring_safeguards


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_eval_result():
    """Minimal RubricEvaluationResult-shaped object for the screening builder."""
    ev = SimpleNamespace(
        requirement="Python avançado",
        level=SimpleNamespace(value="strong"),
        points=75,
        weighted_points=150.0,
        evidence="5 anos de experiência com Python em produção",
    )
    return SimpleNamespace(
        score=82.0,
        recommendation="Recomendado",
        strengths=["Forte em backend Python"],
        concerns=["Sem experiência de liderança"],
        reasoning="Bom match técnico para a vaga",
        evaluations=[ev],
    )


def _patch_audit():
    """Patch the module-level audit_service.log_decision in scoring_safeguards."""
    return patch.object(
        scoring_safeguards.audit_service,
        "log_decision",
        new_callable=AsyncMock,
    )


def _assert_fairness_audit(audit_mock, expected_agent: str) -> None:
    assert audit_mock.await_count >= 1, (
        f"audit_service.log_decision must be called for {expected_agent} fairness block"
    )
    fairness_calls = [
        c for c in audit_mock.await_args_list
        if c.kwargs.get("action") == "cv_screening.fairness_block"
    ]
    assert fairness_calls, (
        f"Expected a 'cv_screening.fairness_block' audit entry for {expected_agent}, got "
        f"{[c.kwargs.get('action') for c in audit_mock.await_args_list]}"
    )


# ---------------------------------------------------------------------------
# (a) Standalone scoring — schema parity with the CV modal (screen_candidate)
# ---------------------------------------------------------------------------

class TestStandaloneScoringParity:
    @pytest.mark.asyncio
    async def test_standalone_matches_modal_schema_and_does_not_persist(self):
        from app.domains.cv_screening.services import cv_scoring_service as mod

        svc = mod.CVScoringService()
        eval_result = _make_eval_result()
        candidate_data = {
            "id": str(uuid4()),
            "name": "Ana",
            "resume_text": "Python sênior com 5 anos de experiência",
            "technical_skills": ["python"],
        }
        requirements = [MagicMock()]
        job_info = {"id": "v1", "title": "Dev Backend", "company_id": "co-1"}

        # --- screen_candidate (persisted) path ---
        screen_db = AsyncMock()
        with patch.object(svc, "_get_candidate_data", new_callable=AsyncMock, return_value=candidate_data), \
             patch.object(svc, "_get_job_requirements", new_callable=AsyncMock, return_value=requirements), \
             patch.object(svc, "_get_job_info", new_callable=AsyncMock, return_value=job_info), \
             patch.object(svc, "_update_candidate_score", new_callable=AsyncMock), \
             patch.object(mod.activity_service, "create_activity", new_callable=AsyncMock), \
             patch.object(mod.rubric_evaluation_service, "evaluate_candidate",
                          new_callable=AsyncMock, return_value=eval_result):
            screen = await svc.screen_candidate(
                candidate_id=candidate_data["id"], vacancy_id="v1",
                company_id="co-1", db=screen_db,
            )

        # --- standalone (dry-run) path ---
        standalone_db = AsyncMock()
        with patch.object(svc, "_get_job_requirements", new_callable=AsyncMock, return_value=requirements), \
             patch.object(svc, "_get_job_info", new_callable=AsyncMock, return_value=job_info), \
             patch.object(svc, "_update_candidate_score", new_callable=AsyncMock) as upd_standalone, \
             patch.object(mod.activity_service, "create_activity", new_callable=AsyncMock) as act_standalone, \
             patch.object(mod.rubric_evaluation_service, "evaluate_candidate",
                          new_callable=AsyncMock, return_value=eval_result):
            standalone = await svc.score_candidate_standalone(
                candidate_data=candidate_data, vacancy_id="v1",
                company_id="co-1", db=standalone_db,
            )

        assert screen["success"] is True
        assert standalone["success"] is True
        # Schema parity: identical key set ⇒ same data the CV modal renders.
        assert set(screen.keys()) == set(standalone.keys()), (
            f"schema drift: screen-only={set(screen)-set(standalone)} "
            f"standalone-only={set(standalone)-set(screen)}"
        )
        # Core rendered fields must match value-for-value.
        for k in ("rubric_score", "cv_fit", "recommendation", "sub_status",
                  "strengths", "concerns", "evaluations"):
            assert screen[k] == standalone[k], f"field '{k}' diverges"

        # Mode markers.
        assert screen["persisted"] is True
        assert standalone["persisted"] is False
        assert standalone["standalone"] is True

        # Standalone must NOT persist anything.
        upd_standalone.assert_not_called()
        act_standalone.assert_not_called()
        standalone_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_standalone_blocks_discriminatory_text(self):
        from app.domains.cv_screening.services import cv_scoring_service as mod

        svc = mod.CVScoringService()
        candidate_data = {
            "id": str(uuid4()),
            "name": "X",
            "resume_text": "Buscamos apenas jovens para essa vaga",
        }
        with _patch_audit() as audit_mock, \
             patch.object(mod.rubric_evaluation_service, "evaluate_candidate",
                          new_callable=AsyncMock) as rubric_mock:
            result = await svc.score_candidate_standalone(
                candidate_data=candidate_data, vacancy_id="v1",
                company_id="co-1", db=AsyncMock(),
            )

        assert result["success"] is False
        assert result["error"] == "fairness_block"
        rubric_mock.assert_not_called()
        _assert_fairness_audit(audit_mock, "cv_scoring_service")

    @pytest.mark.asyncio
    async def test_standalone_rejects_cross_tenant_vacancy(self):
        from app.domains.cv_screening.services import cv_scoring_service as mod

        svc = mod.CVScoringService()
        job_info = {"id": "v1", "title": "Dev", "company_id": "co-OTHER"}
        with patch.object(svc, "_get_job_requirements", new_callable=AsyncMock, return_value=[MagicMock()]), \
             patch.object(svc, "_get_job_info", new_callable=AsyncMock, return_value=job_info), \
             patch.object(mod.rubric_evaluation_service, "evaluate_candidate",
                          new_callable=AsyncMock) as rubric_mock:
            result = await svc.score_candidate_standalone(
                candidate_data={"id": str(uuid4()), "name": "X", "resume_text": "ok"},
                vacancy_id="v1", company_id="co-1", db=AsyncMock(),
            )

        assert result["success"] is False
        assert result["error"] == "cross_tenant_access_denied"
        rubric_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_standalone_fails_closed_on_null_job_company(self):
        """Fail-closed: a vacancy whose tenant cannot be verified is denied."""
        from app.domains.cv_screening.services import cv_scoring_service as mod

        svc = mod.CVScoringService()
        job_info = {"id": "v1", "title": "Dev", "company_id": None}
        with patch.object(svc, "_get_job_requirements", new_callable=AsyncMock, return_value=[MagicMock()]), \
             patch.object(svc, "_get_job_info", new_callable=AsyncMock, return_value=job_info), \
             patch.object(mod.rubric_evaluation_service, "evaluate_candidate",
                          new_callable=AsyncMock) as rubric_mock:
            result = await svc.score_candidate_standalone(
                candidate_data={"id": str(uuid4()), "name": "X", "resume_text": "ok"},
                vacancy_id="v1", company_id="co-1", db=AsyncMock(),
            )

        assert result["success"] is False
        assert result["error"] == "cross_tenant_access_denied"
        rubric_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_standalone_never_persists_even_on_scoring_error(self):
        """Even when rubric eval raises, standalone must not commit/rollback."""
        from app.domains.cv_screening.services import cv_scoring_service as mod

        svc = mod.CVScoringService()
        job_info = {"id": "v1", "title": "Dev", "company_id": "co-1"}
        standalone_db = AsyncMock()
        with patch.object(svc, "_get_job_requirements", new_callable=AsyncMock, return_value=[MagicMock()]), \
             patch.object(svc, "_get_job_info", new_callable=AsyncMock, return_value=job_info), \
             patch.object(svc, "_update_candidate_score", new_callable=AsyncMock) as upd_mock, \
             patch.object(mod.rubric_evaluation_service, "evaluate_candidate",
                          new_callable=AsyncMock, side_effect=RuntimeError("boom")):
            result = await svc.score_candidate_standalone(
                candidate_data={"id": str(uuid4()), "name": "X", "resume_text": "ok"},
                vacancy_id="v1", company_id="co-1", db=standalone_db,
            )

        assert result["success"] is False
        assert result["error"] == "screening_failed"
        upd_mock.assert_not_called()
        standalone_db.commit.assert_not_called()
        standalone_db.rollback.assert_not_called()


# ---------------------------------------------------------------------------
# (b) add_candidate_to_vacancy hardening
# ---------------------------------------------------------------------------

class _FakeResult:
    def __init__(self, obj):
        self._obj = obj

    def scalar_one_or_none(self):
        return self._obj


class _FakeSession:
    """Minimal async session whose .execute returns queued results in order."""
    def __init__(self, results):
        self._results = list(results)
        self.added = []
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def execute(self, *a, **k):
        return self._results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


def _ctx():
    return SimpleNamespace(company_id="co-1", user_id="user-1")


def _patch_session(session):
    return patch(
        "app.core.database.AsyncSessionLocal",
        return_value=session,
    )


class TestAddCandidateToVacancyHardening:
    @pytest.mark.asyncio
    async def test_missing_email_is_rejected(self):
        from app.domains.cv_screening.tools import candidate_tools as mod

        candidate = SimpleNamespace(id=uuid4(), name="Ana", email=None, company_id="co-1")
        job = SimpleNamespace(id=uuid4(), title="Dev", company_id="co-1")
        session = _FakeSession([_FakeResult(candidate), _FakeResult(job)])

        with _patch_session(session):
            result = await mod.add_candidate_to_vacancy(
                candidate_id=str(uuid4()), job_id=str(uuid4()), _context=_ctx(),
            )

        assert result["success"] is False
        assert result["error"] in ("missing_email", "invalid_email")
        assert session.committed is False
        assert session.added == []

    @pytest.mark.asyncio
    async def test_invalid_email_format_is_rejected(self):
        from app.domains.cv_screening.tools import candidate_tools as mod

        candidate = SimpleNamespace(id=uuid4(), name="Ana", email="not-an-email", company_id="co-1")
        job = SimpleNamespace(id=uuid4(), title="Dev", company_id="co-1")
        session = _FakeSession([_FakeResult(candidate), _FakeResult(job)])

        with _patch_session(session):
            result = await mod.add_candidate_to_vacancy(
                candidate_id=str(uuid4()), job_id=str(uuid4()), _context=_ctx(),
            )

        assert result["success"] is False
        assert result["error"] == "invalid_email"
        assert session.committed is False

    @pytest.mark.asyncio
    async def test_biased_notes_blocked_by_fairness(self):
        from app.domains.cv_screening.tools import candidate_tools as mod

        candidate = SimpleNamespace(id=uuid4(), name="Ana", email="ana@example.com", company_id="co-1")
        job = SimpleNamespace(id=uuid4(), title="Dev", company_id="co-1")
        session = _FakeSession([_FakeResult(candidate), _FakeResult(job)])

        with _patch_session(session), _patch_audit() as audit_mock:
            result = await mod.add_candidate_to_vacancy(
                candidate_id=str(uuid4()), job_id=str(uuid4()),
                notes="Buscamos apenas jovens para essa vaga",
                _context=_ctx(),
            )

        assert result["success"] is False
        assert result["error"] == "fairness_block"
        assert session.committed is False
        assert session.added == []
        _assert_fairness_audit(audit_mock, "add_candidate_to_vacancy")

    @pytest.mark.asyncio
    async def test_duplicate_candidate_is_rejected(self):
        from app.domains.cv_screening.tools import candidate_tools as mod

        candidate = SimpleNamespace(id=uuid4(), name="Ana", email="ana@example.com", company_id="co-1")
        job = SimpleNamespace(id=uuid4(), title="Dev", company_id="co-1")
        existing_vc = SimpleNamespace(id=uuid4())
        session = _FakeSession([
            _FakeResult(candidate), _FakeResult(job), _FakeResult(existing_vc),
        ])

        with _patch_session(session):
            result = await mod.add_candidate_to_vacancy(
                candidate_id=str(uuid4()), job_id=str(uuid4()), _context=_ctx(),
            )

        assert result["success"] is False
        assert result["error"] == "candidate_already_in_vacancy"
        assert session.committed is False

    @pytest.mark.asyncio
    async def test_happy_path_creates_vc_and_audits(self):
        from app.domains.cv_screening.tools import candidate_tools as mod

        candidate = SimpleNamespace(id=uuid4(), name="Ana", email="ana@example.com", company_id="co-1")
        job = SimpleNamespace(id=uuid4(), title="Dev", company_id="co-1")
        session = _FakeSession([
            _FakeResult(candidate), _FakeResult(job), _FakeResult(None),
        ])

        with _patch_session(session), _patch_audit() as audit_mock:
            result = await mod.add_candidate_to_vacancy(
                candidate_id=str(uuid4()), job_id=str(uuid4()),
                notes="Candidato forte tecnicamente", _context=_ctx(),
            )

        assert result["success"] is True
        assert session.committed is True
        assert len(session.added) == 1
        # Success must produce an audit entry for the add decision.
        assert audit_mock.await_count >= 1
        add_calls = [
            c for c in audit_mock.await_args_list
            if "add_candidate_to_vacancy" in str(c.kwargs.get("action", ""))
        ]
        assert add_calls, (
            f"expected an add_candidate_to_vacancy audit entry, got "
            f"{[c.kwargs.get('action') for c in audit_mock.await_args_list]}"
        )
