"""
Integration tests — W2.5: P1-7 /feedback persist (black hole fix).

Auditoria 2026-04-26 (P1-7): /feedback endpoint apenas logava
(`# TODO: persist to feedback table for LIA training`). Sem persistencia,
sem feedback loop de ML, sem dashboard de qualidade.

Fix W2.5:
1. Modelo TeamsFeedback em lia_models/teams.py.
2. Migration alembic 098 cria tabela teams_feedback.
3. Endpoint /feedback persiste via TeamsRepository.create_feedback().
4. Auth via Depends(get_current_user) — P1-4 cleanup.
"""
from __future__ import annotations
import inspect
import pytest


class TestTeamsFeedbackModel:
    def test_teams_feedback_model_exists(self):
        from lia_models.teams import TeamsFeedback  # noqa: F401

    def test_teams_feedback_has_required_columns(self):
        from lia_models.teams import TeamsFeedback
        cols = [c.key for c in TeamsFeedback.__table__.columns]
        for required in ("id", "feedback_type", "user_id", "company_id", "created_at"):
            assert required in cols, (
                f"TeamsFeedback must have column {required!r} (got {cols})"
            )


class TestFeedbackEndpoint:
    def test_endpoint_declares_get_current_user(self):
        import app.api.v1.teams as mod
        src = inspect.getsource(mod.receive_card_feedback)
        assert "get_current_user" in src or "current_user" in src, (
            "/feedback must require auth (P1-7 + P1-4)"
        )

    def test_endpoint_persists_to_db(self):
        """Endpoint must call repository to persist (not just logger.info)."""
        import app.api.v1.teams as mod
        src = inspect.getsource(mod.receive_card_feedback)
        # Must reference create_feedback OR direct add to db (persist signal)
        persists = (
            "create_feedback" in src
            or "TeamsFeedback(" in src
            or "db.add(" in src
        )
        assert persists, (
            "/feedback must persist via repository or db.add (P1-7 fix)"
        )


class TestRepositoryCreateFeedback:
    def test_create_feedback_method_exists(self):
        from app.domains.communication.repositories.teams_repository import TeamsRepository
        assert hasattr(TeamsRepository, "create_feedback"), (
            "TeamsRepository must expose create_feedback (P1-7)"
        )

    def test_create_feedback_signature(self):
        from app.domains.communication.repositories.teams_repository import TeamsRepository
        sig = inspect.signature(TeamsRepository.create_feedback)
        for required in ("feedback_type", "user_id", "company_id"):
            assert required in sig.parameters, (
                f"create_feedback signature must include {required!r}"
            )
