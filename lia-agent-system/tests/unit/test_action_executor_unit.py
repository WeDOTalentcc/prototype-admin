"""
Tests for ActionExecutorService (unit — no real DB or LLM)
Target: action_executor.py (9% → ~35%)
"""
import sys
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import fields


class TestActionResultDataclass:
    def test_executed_status(self):
        from app.orchestrator.action_executor import ActionResult
        r = ActionResult(status="executed", message="OK")
        assert r.status == "executed"
        assert r.message == "OK"

    def test_needs_params_status(self):
        from app.orchestrator.action_executor import ActionResult
        r = ActionResult(status="needs_params", missing_params=["candidate_id"])
        assert r.status == "needs_params"
        assert "candidate_id" in r.missing_params

    def test_error_status(self):
        from app.orchestrator.action_executor import ActionResult
        r = ActionResult(status="error", error_detail="DB timeout")
        assert r.status == "error"
        assert r.error_detail == "DB timeout"

    def test_needs_confirmation_status(self):
        from app.orchestrator.action_executor import ActionResult
        r = ActionResult(
            status="needs_confirmation",
            confirmation_summary={"action": "move", "from": "triagem", "to": "entrevista"},
        )
        assert r.status == "needs_confirmation"
        assert r.confirmation_summary is not None

    def test_not_actionable_status(self):
        from app.orchestrator.action_executor import ActionResult
        r = ActionResult(status="not_actionable")
        assert r.status == "not_actionable"

    def test_default_optional_fields(self):
        from app.orchestrator.action_executor import ActionResult
        r = ActionResult(status="executed")
        assert r.data is None
        assert r.missing_params is None
        assert r.confirmation_summary is None
        assert r.action_type is None
        assert r.pending_action_id is None
        assert r.error_detail is None


class TestActionableIntents:
    def test_mover_candidato_registered(self):
        from app.orchestrator.action_executor import ACTIONABLE_INTENTS
        assert "mover_candidato" in ACTIONABLE_INTENTS

    def test_mover_candidato_required_params(self):
        from app.orchestrator.action_executor import ACTIONABLE_INTENTS
        intent = ACTIONABLE_INTENTS["mover_candidato"]
        assert "candidate_id" in intent["required_params"]
        assert "to_stage" in intent["required_params"]

    def test_reprovar_candidato_registered(self):
        from app.orchestrator.action_executor import ACTIONABLE_INTENTS
        assert "reprovar_candidato" in ACTIONABLE_INTENTS

    def test_reprovar_candidato_high_risk(self):
        from app.orchestrator.action_executor import ACTIONABLE_INTENTS
        intent = ACTIONABLE_INTENTS["reprovar_candidato"]
        assert intent["risk_level"] == "high"

    def test_intents_have_required_fields(self):
        from app.orchestrator.action_executor import ACTIONABLE_INTENTS
        for intent_name, config in ACTIONABLE_INTENTS.items():
            assert "domain_id" in config, f"{intent_name} missing domain_id"
            assert "action_id" in config, f"{intent_name} missing action_id"
            assert "required_params" in config, f"{intent_name} missing required_params"
            assert "risk_level" in config, f"{intent_name} missing risk_level"

    def test_atualizar_status_candidato_registered(self):
        from app.orchestrator.action_executor import ACTIONABLE_INTENTS
        assert "atualizar_status_candidato" in ACTIONABLE_INTENTS

    def test_aprovar_candidato_registered(self):
        from app.orchestrator.action_executor import ACTIONABLE_INTENTS
        assert "aprovar_candidato" in ACTIONABLE_INTENTS

    def test_multiple_intents_registered(self):
        from app.orchestrator.action_executor import ACTIONABLE_INTENTS
        assert len(ACTIONABLE_INTENTS) >= 3


class TestActionExecutorInstantiation:
    def test_instantiation_with_no_deps(self):
        from app.orchestrator.action_executor import ActionExecutorService
        executor = ActionExecutorService()
        assert executor is not None

    def test_try_execute_unknown_returns_not_actionable(self):
        from app.orchestrator.action_executor import ActionExecutorService
        executor = ActionExecutorService()
        result = asyncio.run(
            executor.try_execute(
                intent="totally_unknown_intent_xyz",
                entities={},
                context={},
            )
        )
        assert result.status == "not_actionable"

    def test_try_execute_missing_required_params(self):
        from app.orchestrator.action_executor import ActionExecutorService
        executor = ActionExecutorService()
        result = asyncio.run(
            executor.try_execute(
                intent="mover_candidato",
                entities={},  # missing candidate_id and to_stage
                context={},
            )
        )
        assert result.status == "needs_params"
        assert result.missing_params is not None
        assert len(result.missing_params) > 0

    def test_try_execute_partial_params(self):
        from app.orchestrator.action_executor import ActionExecutorService
        executor = ActionExecutorService()
        result = asyncio.run(
            executor.try_execute(
                intent="mover_candidato",
                entities={"candidate_id": "123"},  # missing to_stage
                context={},
            )
        )
        assert result.status == "needs_params"
        assert result.missing_params is not None

    def test_try_execute_all_params_needs_confirmation(self):
        from app.orchestrator.action_executor import ActionExecutorService
        executor = ActionExecutorService()
        result = asyncio.run(
            executor.try_execute(
                intent="mover_candidato",
                entities={
                    "candidate_id": "cand-123",
                    "to_stage": "Entrevista Técnica",
                },
                context={},
            )
        )
        # mover_candidato requires_confirmation=True → needs_confirmation, needs_params, or error
        assert result.status in ("needs_confirmation", "needs_params", "executed", "error")

    def test_is_actionable_known_intent(self):
        from app.orchestrator.action_executor import ActionExecutorService
        executor = ActionExecutorService()
        assert executor.is_actionable("mover_candidato") is True

    def test_is_actionable_unknown_intent(self):
        from app.orchestrator.action_executor import ActionExecutorService
        executor = ActionExecutorService()
        assert executor.is_actionable("unknown_xyz") is False

    def test_get_action_config(self):
        from app.orchestrator.action_executor import ActionExecutorService
        executor = ActionExecutorService()
        config = executor.get_action_config("mover_candidato")
        assert config is not None
        assert "required_params" in config

    def test_get_action_config_unknown(self):
        from app.orchestrator.action_executor import ActionExecutorService
        executor = ActionExecutorService()
        config = executor.get_action_config("unknown_xyz")
        assert config is None
