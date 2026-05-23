"""
Unit tests — Ciclo Fechado (closed-loop action execution).

Cobre os 4 caminhos de _build_response_from_action e a lógica
de multi-turno de handle_action_flow.
"""
import pytest
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# _build_response_from_action
# ---------------------------------------------------------------------------

from app.api.v1.chat import _build_response_from_action


class TestBuildResponseFromAction:
    """Testa geração de texto de override para cada estado de ação."""

    def test_none_when_no_metadata(self):
        assert _build_response_from_action({}) is None
        assert _build_response_from_action(None) is None  # type: ignore

    # --- action_result paths ---

    def test_executed_returns_success_message(self):
        meta = {
            "action_result": {
                "status": "executed",
                "message": "Candidato movido com sucesso.",
                "success": True,
            }
        }
        result = _build_response_from_action(meta)
        assert result == "Candidato movido com sucesso."

    def test_cancelled_returns_cancel_message(self):
        meta = {"action_result": {"status": "cancelled", "success": False}}
        assert _build_response_from_action(meta) == "Ação cancelada."

    def test_error_returns_error_message(self):
        meta = {
            "action_result": {
                "status": "error",
                "message": "Candidato não encontrado.",
                "success": False,
            }
        }
        result = _build_response_from_action(meta)
        assert "não foi possível" in result.lower()
        assert "Candidato não encontrado." in result

    # --- pending_action paths ---

    def test_awaiting_confirmation_with_candidate_and_stage(self):
        meta = {
            "pending_action": {
                "intent": "mover_candidato",
                "action_id": "move_candidate",
                "awaiting_confirmation": True,
                "collected_params": {
                    "candidate_name": "João Silva",
                    "to_stage": "Entrevista Técnica",
                },
            }
        }
        result = _build_response_from_action(meta)
        assert result is not None
        assert "João Silva" in result
        assert "Entrevista Técnica" in result
        assert "Confirma" in result

    def test_awaiting_confirmation_minimal(self):
        meta = {
            "pending_action": {
                "intent": "pausar_vaga",
                "action_id": "pause_job",
                "awaiting_confirmation": True,
                "collected_params": {},
            }
        }
        result = _build_response_from_action(meta)
        assert result is not None
        assert "Confirma" in result

    def test_missing_params_uses_clarification_prompt(self):
        meta = {
            "pending_action": {
                "intent": "mover_candidato",
                "action_id": "move_candidate",
                "awaiting_confirmation": False,
                "missing_params": ["candidate_id"],
                "collected_params": {},
            }
        }
        result = _build_response_from_action(meta)
        assert result is not None
        # Should use the clarification prompt from ACTIONABLE_INTENTS
        assert "candidato" in result.lower()

    def test_missing_params_stage_fallback(self):
        meta = {
            "pending_action": {
                "intent": "mover_candidato",
                "action_id": "move_candidate",
                "awaiting_confirmation": False,
                "missing_params": ["to_stage"],
                "collected_params": {"candidate_id": "abc", "candidate_name": "Maria"},
            }
        }
        result = _build_response_from_action(meta)
        assert result is not None
        assert "etapa" in result.lower() or "pipeline" in result.lower()

    def test_missing_params_unknown_param_uses_generic(self):
        meta = {
            "pending_action": {
                "intent": "some_intent",
                "action_id": "some_action",
                "awaiting_confirmation": False,
                "missing_params": ["custom_field"],
                "collected_params": {},
            }
        }
        result = _build_response_from_action(meta)
        assert result is not None
        assert "custom_field" in result


# ---------------------------------------------------------------------------
# handle_action_flow — multi-turno
# ---------------------------------------------------------------------------

from app.api.v1.chat import handle_action_flow
from app.orchestrator.execution.pending_action import PendingActionState, pending_action_store


def _make_user(company_id: str = "company-123"):
    user = MagicMock()
    user.id = "user-001"
    user.email = "recruiter@test.com"
    user.company_id = company_id
    return user


@pytest.mark.asyncio
class TestHandleActionFlowMultiTurn:
    """Testa coleta multi-turno de parâmetros."""

    def setup_method(self):
        # Limpar store entre testes
        pending_action_store._memory_store.clear()

    def _make_pending(
        self,
        conversation_id: str,
        missing_params: list,
        collected_params: dict = None,
    ) -> PendingActionState:
        import uuid as _uuid
        state = PendingActionState(
            pending_id=str(_uuid.uuid4()),
            intent="mover_candidato",
            action_id="move_candidate",
            domain_id="pipeline_transition",
            collected_params=collected_params or {},
            missing_params=missing_params,
            conversation_id=conversation_id,
            awaiting_confirmation=False,
        )
        pending_action_store.save(conversation_id, state)
        return state

    async def test_collects_simple_param_and_asks_next(self):
        """Quando faltam 2 params, preenche o primeiro e pede o segundo."""
        conv_id = "conv-multiturn-1"
        self._make_pending(conv_id, missing_params=["candidate_id", "to_stage"])

        db = AsyncMock()
        # resolve_candidate_by_name encontra o candidato
        with patch(
            "app.api.v1.chat.resolve_candidate_by_name",
            new=AsyncMock(return_value={"id": "cand-uuid", "stage": "Triagem", "status": "active"}),
        ):
            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="João Silva",
                intent="unknown",
                entities={},
                user_id="user-001",
                current_user=_make_user(),
                db=db,
            )

        assert result is not None
        assert "pending_action" in result
        pending = result["pending_action"]
        assert pending["awaiting_confirmation"] is False
        assert "to_stage" in pending["missing_params"]
        assert pending["collected_params"]["candidate_id"] == "cand-uuid"
        assert pending["collected_params"]["candidate_name"] == "João Silva"

    async def test_completes_params_and_requests_confirmation(self):
        """Quando último param é preenchido, move para confirmação."""
        conv_id = "conv-multiturn-2"
        self._make_pending(
            conv_id,
            missing_params=["to_stage"],
            collected_params={"candidate_id": "cand-uuid", "candidate_name": "Maria"},
        )

        db = AsyncMock()
        result = await handle_action_flow(
            conversation_id=conv_id,
            user_message_text="Entrevista Técnica",
            intent="unknown",
            entities={},
            user_id="user-001",
            current_user=_make_user(),
            db=db,
        )

        assert result is not None
        assert "pending_action" in result
        pending = result["pending_action"]
        assert pending["awaiting_confirmation"] is True
        assert pending["collected_params"]["to_stage"] == "Entrevista Técnica"

    async def test_stores_raw_name_when_candidate_not_found(self):
        """Quando candidato não é encontrado no DB, armazena nome raw."""
        conv_id = "conv-multiturn-3"
        self._make_pending(conv_id, missing_params=["candidate_id"])

        db = AsyncMock()
        with patch(
            "app.api.v1.chat.resolve_candidate_by_name",
            new=AsyncMock(return_value=None),
        ):
            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="Candidato Desconhecido",
                intent="unknown",
                entities={},
                user_id="user-001",
                current_user=_make_user(),
                db=db,
            )

        # Ainda tem pending (candidate_name armazenado mas candidate_id faltando)
        assert result is not None
        pending = result["pending_action"]
        assert pending["collected_params"].get("candidate_name") == "Candidato Desconhecido"

    async def test_no_pending_returns_none_for_unknown_intent(self):
        """Sem ação pendente e intent desconhecido → None."""
        conv_id = "conv-no-pending"
        db = AsyncMock()
        result = await handle_action_flow(
            conversation_id=conv_id,
            user_message_text="olá",
            intent="unknown",
            entities={},
            user_id="user-001",
            current_user=_make_user(),
            db=db,
        )
        assert result is None

    async def test_confirmation_yes_triggers_execution(self):
        """Quando pending awaiting_confirmation=True e user diz 'sim' → executa."""
        import uuid as _uuid
        conv_id = "conv-confirm-yes"
        state = PendingActionState(
            pending_id=str(_uuid.uuid4()),
            intent="mover_candidato",
            action_id="move_candidate",
            domain_id="pipeline_transition",
            collected_params={"candidate_id": "cand-abc", "to_stage": "Aprovado"},
            missing_params=[],
            conversation_id=conv_id,
            awaiting_confirmation=True,
        )
        pending_action_store.save(conv_id, state)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.status = "executed"
        mock_result.message = "Candidato movido."
        mock_result.data = {}
        mock_result.action_type = "move_candidate"

        with patch.object(
            __import__("app.orchestrator.action_executor", fromlist=["action_executor"]).action_executor,
            "_execute_action",
            new=AsyncMock(return_value=mock_result),
        ):
            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="sim",
                intent="unknown",
                entities={},
                user_id="user-001",
                current_user=_make_user(),
                db=db,
            )

        assert result is not None
        assert "action_result" in result
        assert result["action_result"]["status"] == "executed"

    async def test_confirmation_no_cancels_action(self):
        """Quando pending awaiting_confirmation=True e user diz 'não' → cancela."""
        import uuid as _uuid
        conv_id = "conv-confirm-no"
        state = PendingActionState(
            pending_id=str(_uuid.uuid4()),
            intent="mover_candidato",
            action_id="move_candidate",
            domain_id="pipeline_transition",
            collected_params={"candidate_id": "cand-abc", "to_stage": "Aprovado"},
            missing_params=[],
            conversation_id=conv_id,
            awaiting_confirmation=True,
        )
        pending_action_store.save(conv_id, state)

        db = AsyncMock()
        result = await handle_action_flow(
            conversation_id=conv_id,
            user_message_text="não",
            intent="unknown",
            entities={},
            user_id="user-001",
            current_user=_make_user(),
            db=db,
        )

        assert result is not None
        assert "action_result" in result
        assert result["action_result"]["status"] == "cancelled"
