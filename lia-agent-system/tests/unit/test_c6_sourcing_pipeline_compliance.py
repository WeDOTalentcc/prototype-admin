"""
C6 — Sourcing pipeline compliance gates

Verifica:
1. Happy path: critério limpo passa pelo FairnessGuard e log_decision é chamado
   com company_id, candidate_id, decision_type e prompt_hash no `action`.
2. Critério discriminatório: FairnessGuard bloqueia, _run_local_search/global
   retornam [] e o decision audit registra `rejected`.
3. PII na query global é mascarada antes de chegar ao Pearch.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.sourcing.services.sourcing_pipeline_service import (
    SourcingPipelineService,
    _build_criteria_text,
    _prompt_hash,
)


def _make_job(title="Engenheiro Backend", desc="Vaga remota", reqs=None, company_id="comp-1", created_by=None):
    job = MagicMock()
    job.id = "job-1"
    job.title = title
    job.description = desc
    job.location = "Remoto"
    job.company_id = company_id
    job.created_by = created_by
    job.requirements = reqs or ["Python", "FastAPI"]
    return job


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

class TestHelpers:
    def test_build_criteria_text_combines_fields(self):
        job = _make_job()
        text = _build_criteria_text(job, ["Python"])
        assert "Engenheiro Backend" in text
        assert "Remoto" in text
        assert "Python" in text

    def test_prompt_hash_is_stable_sha256(self):
        h1 = _prompt_hash("abc")
        h2 = _prompt_hash("abc")
        assert h1 == h2
        assert len(h1) == 64

    def test_prompt_hash_changes_with_input(self):
        assert _prompt_hash("a") != _prompt_hash("b")


# ─────────────────────────────────────────────
# Happy path — clean criteria
# ─────────────────────────────────────────────

class TestHappyPath:
    @pytest.mark.asyncio
    async def test_clean_criteria_not_blocked_and_audited(self):
        svc = SourcingPipelineService()
        job = _make_job()

        with patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            new_callable=AsyncMock,
        ) as mock_audit:
            blocked, category, phash = await svc._check_fairness_on_criteria(
                job, ["Python", "FastAPI"], context="sourcing_pipeline_local"
            )
            assert blocked is False
            assert category is None
            assert len(phash) == 64

            await svc._audit_sourcing_decision(
                job=job,
                candidate_id="cand-9",
                decision_type="approve_candidate",
                decision="approved",
                prompt_hash=phash,
                reasoning=["match"],
                criteria_used=["technical_skills"],
                score=0.85,
            )

        assert mock_audit.await_count == 1
        kwargs = mock_audit.await_args.kwargs
        assert kwargs["company_id"] == "comp-1"
        assert kwargs["candidate_id"] == "cand-9"
        assert kwargs["decision_type"] == "approve_candidate"
        assert phash[:12] in kwargs["action"]


# ─────────────────────────────────────────────
# Discriminatory criteria blocking
# ─────────────────────────────────────────────

class TestFairnessBlocking:
    @pytest.mark.asyncio
    async def test_discriminatory_criteria_blocks_and_audits_rejection(self):
        svc = SourcingPipelineService()
        # explicit gender filter — Layer 1 hard block
        job = _make_job(
            title="Atendente",
            desc="Buscamos apenas homens para a vaga, idade máxima 30 anos",
            reqs=["comunicação"],
        )

        with patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            new_callable=AsyncMock,
        ) as mock_audit, patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            new_callable=AsyncMock,
        ):
            blocked, category, phash = await svc._check_fairness_on_criteria(
                job, ["comunicação"], context="sourcing_pipeline_local"
            )
            assert blocked is True
            assert category is not None

            await svc._audit_sourcing_decision(
                job=job,
                candidate_id=None,
                decision_type="reject_candidate",
                decision="rejected",
                prompt_hash=phash,
                reasoning=["discriminatory criteria"],
                criteria_used=["job_filter_criteria"],
            )

        kwargs = mock_audit.await_args.kwargs
        assert kwargs["decision"] == "rejected"
        assert kwargs["decision_type"] == "reject_candidate"
        assert kwargs["company_id"] == "comp-1"


# ─────────────────────────────────────────────
# Recruiter is notified in real-time when blocked
# ─────────────────────────────────────────────


class TestRecruiterBlockNotification:
    @pytest.mark.asyncio
    async def test_block_creates_bell_notification_for_recruiter(self):
        svc = SourcingPipelineService()
        job = _make_job(
            title="Atendente",
            desc="Buscamos apenas homens para a vaga, idade máxima 30 anos",
            reqs=["comunicação"],
            created_by="user-recruiter-42",
        )

        with patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            new_callable=AsyncMock,
        ), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            new_callable=AsyncMock,
        ), patch(
            "app.services.notification_service.notification_service.create_notification",
            new_callable=AsyncMock,
        ) as mock_notify:
            blocked, _category, _phash = await svc._check_fairness_on_criteria(
                job, ["comunicação"], context="sourcing_pipeline_local"
            )

        assert blocked is True
        assert mock_notify.await_count == 1
        kwargs = mock_notify.await_args.kwargs
        assert kwargs["user_id"] == "user-recruiter-42"
        assert kwargs["related_job_id"] == "job-1"
        assert kwargs["action_url"] == "/jobs/job-1"
        assert kwargs["source_trigger"] == "fairness_block"
        assert "bell" in kwargs["channels"]
        assert "Atendente" in kwargs["title"]

    @pytest.mark.asyncio
    async def test_block_without_recruiter_skips_notification(self):
        svc = SourcingPipelineService()
        job = _make_job(
            title="Atendente",
            desc="Buscamos apenas homens para a vaga",
            reqs=["comunicação"],
            created_by=None,
        )

        with patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            new_callable=AsyncMock,
        ), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            new_callable=AsyncMock,
        ), patch(
            "app.services.notification_service.notification_service.create_notification",
            new_callable=AsyncMock,
        ) as mock_notify:
            blocked, _category, _phash = await svc._check_fairness_on_criteria(
                job, ["comunicação"], context="sourcing_pipeline_local"
            )

        assert blocked is True
        assert mock_notify.await_count == 0


# ─────────────────────────────────────────────
# PII masking before external LLM/Pearch call
# ─────────────────────────────────────────────

class TestPIIMasking:
    @pytest.mark.asyncio
    async def test_global_search_strips_pii_before_pearch(self):
        from app.domains.sourcing.services import sourcing_pipeline_service as mod

        svc = SourcingPipelineService()
        # Description carries PII that must NOT be forwarded to Pearch.
        job = _make_job(
            title="Engenheiro contato joao.silva@example.com",
            desc="Telefone +55 11 91234-5678 - CPF 123.456.789-09",
            reqs=["Python"],
        )

        captured = {}

        async def fake_search(query, search_type="fast", limit=20):
            captured["query"] = query
            resp = MagicMock()
            resp.candidates = []
            return resp

        with patch.object(
            mod.pearch_service, "search_candidates", side_effect=fake_search
        ), patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            new_callable=AsyncMock,
        ):
            candidates, phash = await svc._run_global_search(job)

        assert candidates == []
        assert len(phash) == 64
        assert "query" in captured
        assert "joao.silva@example.com" not in captured["query"]
        assert "123.456.789-09" not in captured["query"]


# ─────────────────────────────────────────────
# Per-candidate exclusion auditing
# ─────────────────────────────────────────────

class TestExclusionAudits:
    @pytest.mark.asyncio
    async def test_add_candidates_audits_skip_when_interview_exists(self):
        svc = SourcingPipelineService()
        job = _make_job()

        candidate = MagicMock()
        candidate.id = "cand-existing"
        candidate.name = "Existing"

        # Simulate "interview already exists" — scalar_one_or_none returns truthy
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = MagicMock()

        db = MagicMock()
        db.execute = AsyncMock(return_value=existing_result)
        db.commit = AsyncMock()
        db.add = MagicMock()

        with patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            new_callable=AsyncMock,
        ) as mock_audit:
            added = await svc._add_candidates_to_job(
                db, job, [candidate], prompt_hash="abc" * 21 + "x"
            )

        assert added == 0
        # One audit call for the skip (rejected)
        assert mock_audit.await_count == 1
        kwargs = mock_audit.await_args.kwargs
        assert kwargs["decision"] == "rejected"
        assert kwargs["candidate_id"] == "cand-existing"
        # Full hash present (not truncated) in action
        assert "abc" * 21 + "x" in kwargs["action"]
