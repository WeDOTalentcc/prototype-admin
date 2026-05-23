"""
Testes de integração do Ciclo Fechado — handle_action_flow end-to-end.

Camada 3 da pirâmide de testes (testing-patterns §5).
Testa a função handle_action_flow diretamente com mocks de:
  - pending_action_store (in-memory, sem DB)
  - action_executor._execute_action
  - _try_extract_params_with_llm (LLM param extraction)
  - AsyncSession (DB queries)
  - User (current_user autenticado)

Cenários cobertos:
  1. Intent acionável + params completos nas entities → awaiting_confirmation=True
  2. Pending confirmando ("sim") → action_result.status=executed
  3. Pending recusando ("não") → action_result.status=cancelled
  4. Params faltantes + LLM extrai → awaiting_confirmation=True (single-shot)
  5. Params faltantes + LLM falha → missing_params multi-turno
"""
import sys
import os
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(company_id: str = "company-test-001") -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "recrutador@empresa.com"
    user.company_id = company_id
    return user


def _make_db() -> AsyncMock:
    """AsyncSession mock que retorna None em qualquer execute."""
    db = AsyncMock()
    result = MagicMock()
    result.fetchone.return_value = None
    db.execute = AsyncMock(return_value=result)
    return db


def _make_pending_state(
    conversation_id: str,
    awaiting_confirmation: bool = False,
    missing_params: list | None = None,
    collected_params: dict | None = None,
) -> "PendingActionState":
    from app.orchestrator.execution.pending_action import PendingActionState
    return PendingActionState(
        pending_id=str(uuid.uuid4()),
        intent="mover_candidato",
        action_id="move_candidate",
        domain_id="pipeline_transition",
        collected_params=collected_params or {
            "candidate_id": "cand-001",
            "candidate_name": "João Silva",
            "to_stage": "Entrevista",
        },
        missing_params=missing_params or [],
        conversation_id=conversation_id,
        company_id="company-test-001",
        awaiting_confirmation=awaiting_confirmation,
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )


# ---------------------------------------------------------------------------
# Cenário 1: Params completos nas entities → awaiting_confirmation=True
# ---------------------------------------------------------------------------

class TestScenario1AllParamsPresent:

    @pytest.mark.asyncio
    async def test_returns_pending_action_awaiting_confirmation(self):
        """Intent mover_candidato com candidato e etapa nas entities → confirmar antes de executar."""
        from app.api.v1.chat import handle_action_flow

        conv_id = str(uuid.uuid4())
        user = _make_user()
        db = _make_db()

        # Candidato resolvido por nome
        mock_cand = {"id": "cand-001", "candidate_id": "cand-001", "stage": "Triagem", "status": "active"}
        # Job queries retornam None (não há vaga no contexto)

        with patch("app.api.v1.chat.pending_action_store") as mock_store, \
             patch("app.api.v1.chat.resolve_candidate_by_name", return_value=mock_cand), \
             patch("app.api.v1.chat.resolve_job_id_by_title", return_value=None), \
             patch("app.api.v1.chat._try_extract_params_with_llm", return_value=None):

            mock_store.get.return_value = None  # sem pending existente
            mock_store.save = MagicMock()

            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="Mover João Silva para Entrevista",
                intent="mover_candidato",
                entities={"candidato": "João Silva", "etapa": "Entrevista"},
                user_id=str(user.id),
                current_user=user,
                db=db,
            )

        assert result is not None
        assert "pending_action" in result
        pending = result["pending_action"]
        assert pending["awaiting_confirmation"] is True
        assert pending["intent"] == "mover_candidato"
        mock_store.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_collected_params_contain_candidate_and_stage(self):
        """Os params coletados devem incluir candidate_id e to_stage."""
        from app.api.v1.chat import handle_action_flow

        conv_id = str(uuid.uuid4())
        user = _make_user()
        db = _make_db()

        mock_cand = {"id": "cand-abc", "candidate_id": "cand-abc", "stage": "Triagem", "status": "active"}

        with patch("app.api.v1.chat.pending_action_store") as mock_store, \
             patch("app.api.v1.chat.resolve_candidate_by_name", return_value=mock_cand), \
             patch("app.api.v1.chat.resolve_job_id_by_title", return_value=None), \
             patch("app.api.v1.chat._try_extract_params_with_llm", return_value=None):

            mock_store.get.return_value = None
            mock_store.save = MagicMock()

            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="Mover Ana para Proposta",
                intent="mover_candidato",
                entities={"candidato": "Ana", "etapa": "Proposta"},
                user_id=str(user.id),
                current_user=user,
                db=db,
            )

        assert result is not None
        collected = result["pending_action"]["collected_params"]
        assert collected.get("candidate_id") == "cand-abc"
        assert collected.get("to_stage") == "Proposta"


# ---------------------------------------------------------------------------
# Cenário 2: Pending existente + usuário confirma ("sim") → executed
# ---------------------------------------------------------------------------

class TestScenario2ConfirmExecution:

    @pytest.mark.asyncio
    async def test_returns_action_result_executed_on_confirmation(self):
        """Quando há pending awaiting_confirmation e usuário confirma → status=executed."""
        from app.api.v1.chat import handle_action_flow
        from app.orchestrator.action_executor import ActionResult

        conv_id = str(uuid.uuid4())
        user = _make_user()
        db = _make_db()
        pending = _make_pending_state(conv_id, awaiting_confirmation=True)

        mock_executed = ActionResult(
            status="executed",
            message="João Silva foi movido para Entrevista com sucesso.",
            action_type="move_candidate",
            data={"candidate_id": "cand-001", "to_stage": "Entrevista"},
        )

        with patch("app.api.v1.chat.pending_action_store") as mock_store, \
             patch("app.api.v1.chat.action_executor") as mock_executor:

            mock_store.get.return_value = pending
            mock_store.remove = MagicMock()
            mock_executor.get_action_config.return_value = {
                "action_id": "move_candidate",
                "domain_id": "pipeline_transition",
                "required_params": ["candidate_id", "to_stage"],
                "optional_params": [],
                "risk_level": "medium",
                "requires_confirmation": True,
            }
            mock_executor._execute_action = AsyncMock(return_value=mock_executed)

            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="sim",
                intent="",
                entities={},
                user_id=str(user.id),
                current_user=user,
                db=db,
            )

        assert result is not None
        assert "action_result" in result
        assert result["action_result"]["status"] == "executed"
        assert result["action_result"]["success"] is True
        mock_store.remove.assert_called_once_with(conv_id)

    @pytest.mark.asyncio
    async def test_multiple_confirmation_words_all_trigger_execution(self):
        """'pode', 'ok', 'confirmo' também devem confirmar."""
        from app.api.v1.chat import handle_action_flow
        from app.orchestrator.action_executor import ActionResult

        for word in ["pode", "ok", "confirmo", "claro", "bora"]:
            conv_id = str(uuid.uuid4())
            user = _make_user()
            db = _make_db()
            pending = _make_pending_state(conv_id, awaiting_confirmation=True)

            mock_executed = ActionResult(status="executed", message="ok", action_type="move_candidate")

            with patch("app.api.v1.chat.pending_action_store") as mock_store, \
                 patch("app.api.v1.chat.action_executor") as mock_executor:

                mock_store.get.return_value = pending
                mock_store.remove = MagicMock()
                mock_executor.get_action_config.return_value = {
                    "action_id": "move_candidate",
                    "domain_id": "pipeline_transition",
                    "required_params": ["candidate_id", "to_stage"],
                    "optional_params": [],
                    "risk_level": "medium",
                    "requires_confirmation": True,
                }
                mock_executor._execute_action = AsyncMock(return_value=mock_executed)

                result = await handle_action_flow(
                    conversation_id=conv_id,
                    user_message_text=word,
                    intent="",
                    entities={},
                    user_id=str(user.id),
                    current_user=user,
                    db=db,
                )

            assert result is not None, f"Word '{word}' should trigger execution"
            assert "action_result" in result, f"Word '{word}' should produce action_result"
            assert result["action_result"]["status"] == "executed"


# ---------------------------------------------------------------------------
# Cenário 3: Pending existente + usuário recusa ("não") → cancelled
# ---------------------------------------------------------------------------

class TestScenario3RejectCancellation:

    @pytest.mark.asyncio
    async def test_returns_action_result_cancelled_on_rejection(self):
        """Quando usuário digita 'não' → status=cancelled, pending removido."""
        from app.api.v1.chat import handle_action_flow

        conv_id = str(uuid.uuid4())
        user = _make_user()
        db = _make_db()
        pending = _make_pending_state(conv_id, awaiting_confirmation=True)

        with patch("app.api.v1.chat.pending_action_store") as mock_store:
            mock_store.get.return_value = pending
            mock_store.remove = MagicMock()

            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="não",
                intent="",
                entities={},
                user_id=str(user.id),
                current_user=user,
                db=db,
            )

        assert result is not None
        assert "action_result" in result
        assert result["action_result"]["status"] == "cancelled"
        assert result["action_result"]["success"] is False
        mock_store.remove.assert_called_once_with(conv_id)

    @pytest.mark.asyncio
    async def test_multiple_rejection_words_all_cancel(self):
        """'cancelar', 'para', 'abort' também devem cancelar."""
        from app.api.v1.chat import handle_action_flow

        for word in ["cancelar", "cancela", "para", "abortar", "não quero"]:
            conv_id = str(uuid.uuid4())
            user = _make_user()
            db = _make_db()
            pending = _make_pending_state(conv_id, awaiting_confirmation=True)

            with patch("app.api.v1.chat.pending_action_store") as mock_store:
                mock_store.get.return_value = pending
                mock_store.remove = MagicMock()

                result = await handle_action_flow(
                    conversation_id=conv_id,
                    user_message_text=word,
                    intent="",
                    entities={},
                    user_id=str(user.id),
                    current_user=user,
                    db=db,
                )

            assert result is not None, f"Word '{word}' should cancel"
            assert result["action_result"]["status"] == "cancelled", f"'{word}' should cancel"


# ---------------------------------------------------------------------------
# Cenário 4: Params faltantes + LLM extrai → awaiting_confirmation=True
# ---------------------------------------------------------------------------

class TestScenario4LLMExtractsParams:

    @pytest.mark.asyncio
    async def test_llm_extraction_fills_missing_leads_to_confirmation(self):
        """
        Entities vazias → missing_params = [candidate_id, to_stage].
        LLM extrai ambos → não entra em multi-turno → awaiting_confirmation=True.
        """
        from app.api.v1.chat import handle_action_flow

        conv_id = str(uuid.uuid4())
        user = _make_user()
        db = _make_db()

        # LLM extrai os dois params necessários
        llm_extracted = {"candidate_id": "cand-llm-001", "to_stage": "Entrevista Técnica"}

        with patch("app.api.v1.chat.pending_action_store") as mock_store, \
             patch("app.api.v1.chat.resolve_candidate_by_name", return_value=None), \
             patch("app.api.v1.chat.resolve_job_id_by_title", return_value=None), \
             patch("app.api.v1.chat._try_extract_params_with_llm", return_value=llm_extracted):

            mock_store.get.return_value = None
            mock_store.save = MagicMock()

            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="Mova o candidato para entrevista técnica",
                intent="mover_candidato",
                entities={},  # sem params nas entities
                user_id=str(user.id),
                current_user=user,
                db=db,
            )

        assert result is not None
        assert "pending_action" in result
        assert result["pending_action"]["awaiting_confirmation"] is True
        assert result["pending_action"]["collected_params"]["candidate_id"] == "cand-llm-001"
        assert result["pending_action"]["collected_params"]["to_stage"] == "Entrevista Técnica"

    @pytest.mark.asyncio
    async def test_llm_extraction_partial_still_awaits_missing(self):
        """LLM extrai apenas to_stage mas falta candidate_id → ainda vai para multi-turno."""
        from app.api.v1.chat import handle_action_flow

        conv_id = str(uuid.uuid4())
        user = _make_user()
        db = _make_db()

        # LLM só extrai to_stage, candidate_id ainda falta
        llm_extracted_partial = {"to_stage": "Entrevista"}

        with patch("app.api.v1.chat.pending_action_store") as mock_store, \
             patch("app.api.v1.chat.resolve_candidate_by_name", return_value=None), \
             patch("app.api.v1.chat.resolve_job_id_by_title", return_value=None), \
             patch("app.api.v1.chat._try_extract_params_with_llm", return_value=llm_extracted_partial):

            mock_store.get.return_value = None
            mock_store.save = MagicMock()

            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="mover para entrevista",
                intent="mover_candidato",
                entities={},
                user_id=str(user.id),
                current_user=user,
                db=db,
            )

        assert result is not None
        # partial extraction → LLM returns non-None but missing candidate_id → falls to multi-turn
        # _try_extract_params_with_llm returns None when required fields still missing
        # Here we mock it returning partial — the code checks missing after extraction
        # So result should be pending_action with missing_params still
        assert "pending_action" in result
        assert result["pending_action"]["awaiting_confirmation"] is False
        assert "candidate_id" in result["pending_action"]["missing_params"]


# ---------------------------------------------------------------------------
# Cenário 5: Params faltantes + LLM falha → missing_params multi-turno
# ---------------------------------------------------------------------------

class TestScenario5LLMFailsMultiTurn:

    @pytest.mark.asyncio
    async def test_llm_extraction_fails_returns_missing_params(self):
        """
        LLM retorna None → sistema salva pending com missing_params
        e retorna para multi-turno (LIA vai perguntar o próximo param).
        """
        from app.api.v1.chat import handle_action_flow

        conv_id = str(uuid.uuid4())
        user = _make_user()
        db = _make_db()

        with patch("app.api.v1.chat.pending_action_store") as mock_store, \
             patch("app.api.v1.chat.resolve_candidate_by_name", return_value=None), \
             patch("app.api.v1.chat.resolve_job_id_by_title", return_value=None), \
             patch("app.api.v1.chat._try_extract_params_with_llm", return_value=None):

            mock_store.get.return_value = None
            mock_store.save = MagicMock()

            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="mover candidato",
                intent="mover_candidato",
                entities={},
                user_id=str(user.id),
                current_user=user,
                db=db,
            )

        assert result is not None
        assert "pending_action" in result
        pending = result["pending_action"]
        assert pending["awaiting_confirmation"] is False
        assert len(pending["missing_params"]) > 0
        assert "candidate_id" in pending["missing_params"]
        mock_store.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_multi_turn_second_message_fills_param(self):
        """
        Segundo turno: pending com missing_params=["to_stage"].
        Usuário responde "Entrevista" → to_stage preenchido → awaiting_confirmation=True.
        """
        from app.api.v1.chat import handle_action_flow

        conv_id = str(uuid.uuid4())
        user = _make_user()
        db = _make_db()

        # Pending já existe com candidate_id preenchido, faltando to_stage
        pending = _make_pending_state(
            conv_id,
            awaiting_confirmation=False,
            missing_params=["to_stage"],
            collected_params={"candidate_id": "cand-001", "candidate_name": "João"},
        )

        with patch("app.api.v1.chat.pending_action_store") as mock_store, \
             patch("app.api.v1.chat.action_executor") as mock_executor:

            mock_store.get.return_value = pending
            mock_store.save = MagicMock()
            mock_executor.get_action_config.return_value = {
                "action_id": "move_candidate",
                "domain_id": "pipeline_transition",
                "required_params": ["candidate_id", "to_stage"],
                "optional_params": [],
                "risk_level": "medium",
                "requires_confirmation": True,
            }

            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="Entrevista",
                intent="",
                entities={},
                user_id=str(user.id),
                current_user=user,
                db=db,
            )

        assert result is not None
        assert "pending_action" in result
        assert result["pending_action"]["awaiting_confirmation"] is True
        assert result["pending_action"]["collected_params"].get("to_stage") == "Entrevista"


# ---------------------------------------------------------------------------
# Cenário extra: intent não acionável → retorna None
# ---------------------------------------------------------------------------

class TestNonActionableIntent:

    @pytest.mark.asyncio
    async def test_greeting_intent_returns_none(self):
        """Intents em SKIP_ACTION_INTENTS não devem disparar action flow."""
        from app.api.v1.chat import handle_action_flow

        conv_id = str(uuid.uuid4())
        user = _make_user()
        db = _make_db()

        with patch("app.api.v1.chat.pending_action_store") as mock_store:
            mock_store.get.return_value = None

            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="Olá LIA, tudo bem?",
                intent="greeting",
                entities={},
                user_id=str(user.id),
                current_user=user,
                db=db,
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_unknown_intent_returns_none(self):
        """Intent desconhecido retorna None."""
        from app.api.v1.chat import handle_action_flow

        conv_id = str(uuid.uuid4())
        user = _make_user()
        db = _make_db()

        with patch("app.api.v1.chat.pending_action_store") as mock_store:
            mock_store.get.return_value = None

            result = await handle_action_flow(
                conversation_id=conv_id,
                user_message_text="xpto qualquer coisa",
                intent="unknown",
                entities={},
                user_id=str(user.id),
                current_user=user,
                db=db,
            )

        assert result is None
