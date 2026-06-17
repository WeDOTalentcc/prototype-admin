"""
C7 — Candidate feedback FairnessGuard

Verifica:
1. Happy path: mensagem limpa não é regenerada e não levanta erro.
2. Mensagem discriminatória bloqueada → regenera com tips padrão.
3. Mesmo após regenerar continua bloqueada → levanta LIAFairnessError.
4. PII no nome do candidato não vaza no `composed` enviado ao FairnessGuard
   (mask aplicada via _enforce_fairness_on_message indireto: garantimos que o
   candidate_id é passado como parâmetro de log).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.candidates.services.candidate_feedback_service import (
    CandidateFeedbackService,
)


def _msg(body="Olá, segue feedback construtivo da nossa equipe."):
    return {
        "subject": "Feedback sobre sua candidatura",
        "short_message": "Obrigado por se candidatar.",
        "body_text": body,
        "html_body": f"<p>{body}</p>",
        "whatsapp_message": "Obrigado por se candidatar.",
    }


# ─────────────────────────────────────────────
# Happy path
# ─────────────────────────────────────────────

class TestHappyPath:
    @pytest.mark.asyncio
    async def test_clean_message_returns_original_no_regeneration(self):
        svc = CandidateFeedbackService()
        message = _msg()

        out_msg, out_tips, meta = await svc._enforce_fairness_on_message(
            message=message,
            candidate_name="Maria",
            vacancy_title="Engenheira",
            company_name="Acme",
            adherence_score=55.0,
            improvement_tips=["Pratique algoritmos", "Aprofunde Python"],
            missing_skills=["Python"],
            resubmit_url="/apply/x",
            candidate_id="cand-1",
            vacancy_id="vac-1",
        )
        assert out_msg is message
        assert meta["fairness_blocked"] is False
        assert meta["regenerated"] is False


# ─────────────────────────────────────────────
# Discriminatory text — regeneration succeeds
# ─────────────────────────────────────────────

class TestDiscriminatoryRegenerated:
    @pytest.mark.asyncio
    async def test_discriminatory_message_is_regenerated(self):
        svc = CandidateFeedbackService()
        bad_message = _msg(body="Buscamos apenas homens para a vaga.")

        clean_message = _msg(body="Obrigado pela participação.")

        with patch.object(
            svc, "_generate_feedback_message", new=AsyncMock(return_value=clean_message)
        ), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            new_callable=AsyncMock,
        ):
            out_msg, out_tips, meta = await svc._enforce_fairness_on_message(
                message=bad_message,
                candidate_name="João",
                vacancy_title="Atendente",
                company_name="Acme",
                adherence_score=40.0,
                improvement_tips=["Boa aparência é essencial"],
                missing_skills=["comunicação"],
                resubmit_url="/apply/x",
                candidate_id="cand-7",
                vacancy_id="vac-7",
            )

        assert meta["regenerated"] is True
        assert out_msg == clean_message
        # safe_tips must come from the default generator (não conter o tip ruim)
        assert "Boa aparência é essencial" not in out_tips


# ─────────────────────────────────────────────
# Still blocked after regeneration → raises
# ─────────────────────────────────────────────

class TestStillBlockedRaises:
    @pytest.mark.asyncio
    async def test_blocked_after_regeneration_raises_fairness_error(self):
        from app.shared.errors import LIAFairnessError

        svc = CandidateFeedbackService()
        bad_message = _msg(body="Buscamos apenas mulheres para a vaga.")
        # Regenerated message is also bad
        still_bad = _msg(body="Apenas homens são considerados para a vaga.")

        with patch.object(
            svc, "_generate_feedback_message", new=AsyncMock(return_value=still_bad)
        ), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            new_callable=AsyncMock,
        ):
            with pytest.raises(LIAFairnessError):
                await svc._enforce_fairness_on_message(
                    message=bad_message,
                    candidate_name="X",
                    vacancy_title="Y",
                    company_name="Z",
                    adherence_score=20.0,
                    improvement_tips=[],
                    missing_skills=[],
                    resubmit_url="/x",
                    candidate_id="cand-9",
                    vacancy_id="vac-9",
                )


# ─────────────────────────────────────────────
# PII masking sanity — _generate_improvement_tips is deterministic
# (the regenerated path drops user-supplied missing_skills, ensuring no
# free-text PII from upstream calls leaks into the new message).
# ─────────────────────────────────────────────

class TestPIIInTipsDropped:
    @pytest.mark.asyncio
    async def test_regeneration_drops_user_missing_skills_carrying_pii(self):
        svc = CandidateFeedbackService()
        bad_message = _msg(body="Procuramos apenas homens.")
        regenerated = _msg(body="Mensagem segura padrão.")

        captured = {}

        async def fake_generate(**kwargs):
            captured.update(kwargs)
            return regenerated

        with patch.object(
            svc, "_generate_feedback_message", new=fake_generate
        ), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            new_callable=AsyncMock,
        ):
            await svc._enforce_fairness_on_message(
                message=bad_message,
                candidate_name="Maria",
                vacancy_title="Eng",
                company_name="Acme",
                adherence_score=30.0,
                improvement_tips=[],
                missing_skills=["maria@example.com - revisar projetos"],
                resubmit_url="/x",
                candidate_id="cand-2",
                vacancy_id="vac-2",
            )

        # On regeneration, missing_skills must be empty (not propagated)
        assert captured.get("missing_skills") == []
