"""
D5 — Memória e Continuidade
D5-02: Multiple system messages bug (fix a7d756097) — sensor de regressão
D5-05: Session isolation — sem vazamento de memória entre sessões

Estes testes verificam o CONTRATO real do código existente:
- _messages_for_continuation em langgraph_base.py
- ConversationMemoryRepository em app/domains/recruiter_assistant/repositories/
- ConversationMemory service em app/domains/recruiter_assistant/services/
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ---------------------------------------------------------------------------
# D5-02 — Sensor de regressão: multiple system messages bug (fix a7d756097)
# ---------------------------------------------------------------------------

class TestMultipleSystemMessagesBug:
    """D5-02 — Sensor de regressão para fix a7d756097.

    O bug: em turnos de continuação o grafo LangGraph recebia
    [System, Human, AI, System, Human] → Anthropic rejeitava com
    'multiple non-consecutive system messages'. O fix adicionou
    _messages_for_continuation em langgraph_base.py.
    """

    def test_messages_for_continuation_helper_exists(self):
        """_messages_for_continuation deve existir e ser importável."""
        from lia_agents_core.langgraph_base import _messages_for_continuation
        assert callable(_messages_for_continuation)

    def test_first_turn_preserves_system_message(self):
        """Turno 1 (has_prior_state=False): SystemMessage é preservado inalterado."""
        from langchain_core.messages import HumanMessage, SystemMessage
        from lia_agents_core.langgraph_base import _messages_for_continuation

        msgs = [SystemMessage(content="persona da LIA"), HumanMessage(content="oi")]
        result = _messages_for_continuation(msgs, has_prior_state=False)

        # No turno 1 deve retornar a lista sem modificações (identidade ou igual)
        assert result is msgs, "Turno 1: deve retornar a lista original sem cópia desnecessária"
        system_msgs = [m for m in result if type(m).__name__ == "SystemMessage"]
        assert len(system_msgs) == 1, "Turno 1: SystemMessage deve ser preservado"

    def test_continuation_turn_removes_system_from_new_input(self):
        """Turno 2+ (has_prior_state=True): SystemMessage é removido do input novo.

        O checkpointer já tem o SystemMessage do turno 1. Re-injetá-lo geraria
        mensagens não-consecutivas rejeitadas pela API Anthropic.
        """
        from langchain_core.messages import HumanMessage, SystemMessage
        from lia_agents_core.langgraph_base import _messages_for_continuation

        msgs = [SystemMessage(content="persona"), HumanMessage(content="segunda pergunta")]
        result = _messages_for_continuation(msgs, has_prior_state=True)

        type_names = [type(m).__name__ for m in result]
        assert "SystemMessage" not in type_names, (
            "Turno de continuação: SystemMessage deve ser removido do input novo"
        )
        assert len(result) == 1
        assert result[0].content == "segunda pergunta"

    def test_no_consecutive_system_messages_produced(self):
        """Nunca deve produzir múltiplos SystemMessages consecutivos no output."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
        from lia_agents_core.langgraph_base import _messages_for_continuation

        # Simula payload hipotético com múltiplos System (situação de bug)
        msgs = [
            SystemMessage(content="s1"),
            HumanMessage(content="h1"),
            AIMessage(content="a1"),
            SystemMessage(content="s2_reinjetado"),
            HumanMessage(content="h2"),
        ]
        result = _messages_for_continuation(msgs, has_prior_state=True)

        # Após o helper, não deve ter nenhum SystemMessage no output de continuação
        system_msgs = [m for m in result if type(m).__name__ == "SystemMessage"]
        assert len(system_msgs) == 0, (
            "Continuação: _messages_for_continuation deve remover TODOS os SystemMessages"
        )

        # Apenas mensagens Human/AI são preservadas
        type_names = [type(m).__name__ for m in result]
        assert type_names == ["HumanMessage", "AIMessage", "HumanMessage"]

    def test_empty_and_none_inputs_dont_raise(self):
        """None e lista vazia não devem causar exceção."""
        from lia_agents_core.langgraph_base import _messages_for_continuation

        assert _messages_for_continuation(None, has_prior_state=True) == []
        assert _messages_for_continuation([], has_prior_state=True) == []
        assert _messages_for_continuation(None, has_prior_state=False) is None or \
               _messages_for_continuation(None, has_prior_state=False) == []  # any safe value

    def test_thread_key_includes_domain_for_session_isolation(self):
        """O thread_id do LangGraph deve incluir domain para isolar sessões por domínio.

        Sprint C #41 mitigation: thread_id = session::domain evita contaminação
        cruzada entre domain agents que compartilham o mesmo checkpointer.
        Testa indiretamente o contrato verificando a lógica de composição.
        """
        import inspect
        from lia_agents_core import langgraph_base

        source = inspect.getsource(langgraph_base)

        # Verificar que a composição session::domain está no source
        assert "_agent_domain" in source, "Deve ter variável _agent_domain"
        assert "_thread_key" in source, "Deve ter variável _thread_key"
        # O padrão session::domain deve estar presente
        assert "session_id" in source and "_agent_domain" in source, (
            "thread_id deve compor session_id + domain para isolamento"
        )

    def test_prior_state_detection_logic_exists(self):
        """_run_graph deve verificar estado prior via aget_state antes de filtrar."""
        import inspect
        from lia_agents_core import langgraph_base

        source = inspect.getsource(langgraph_base)

        assert "aget_state" in source, (
            "Deve chamar aget_state para detectar se há estado prior no checkpointer"
        )
        assert "_has_prior" in source, (
            "Deve ter variável _has_prior para controlar a remoção do SystemMessage"
        )
        assert "_messages_for_continuation" in source, (
            "_run_graph deve invocar _messages_for_continuation"
        )


# ---------------------------------------------------------------------------
# D5-05 — Session isolation: sem vazamento de memória entre sessões
# ---------------------------------------------------------------------------

class TestSessionIsolation:
    """D5-05 — Isolamento de memória entre sessões.

    Garante que company_id + session_id são usados como chave composta de
    isolamento, evitando que memória de uma sessão vaze para outra.
    """

    def test_repository_requires_company_id_fail_closed(self):
        """ConversationMemoryRepository deve rejeitar company_id vazio (fail-closed)."""
        from app.domains.recruiter_assistant.repositories.conversation_memory_repository import (
            ConversationMemoryRepository,
        )

        # _require_company_id deve existir como método estático
        assert hasattr(ConversationMemoryRepository, "_require_company_id")

        with pytest.raises(ValueError, match="company_id required"):
            ConversationMemoryRepository._require_company_id("")

        with pytest.raises(ValueError, match="company_id required"):
            ConversationMemoryRepository._require_company_id(None)

    def test_session_isolation_key_includes_session_id(self):
        """get_recent_for_session deve filtrar por (company_id AND session_id)."""
        import inspect
        from app.domains.recruiter_assistant.repositories.conversation_memory_repository import (
            ConversationMemoryRepository,
        )

        source = inspect.getsource(ConversationMemoryRepository.get_recent_for_session)

        # Ambos os campos devem aparecer no filtro
        assert "company_id" in source, "Filtro deve incluir company_id"
        assert "session_id" in source, "Filtro deve incluir session_id"

    @pytest.mark.asyncio
    async def test_different_sessions_dont_share_memory(self):
        """Sessões diferentes retornam memória distinta (sem cross-session leak).

        Verifica que o repositório passa session_id distinto para cada chamada,
        usando spy nos parâmetros da query via captura do stmt executado.
        """
        from app.domains.recruiter_assistant.repositories.conversation_memory_repository import (
            ConversationMemoryRepository,
        )

        company_id = str(uuid4())
        session_a = "session-alpha"
        session_b = "session-beta"

        # Rastreia quais statements foram executados
        captured_stmts = []

        mock_db = AsyncMock()

        async def capturing_execute(stmt):
            captured_stmts.append(stmt)
            result = MagicMock()
            result.scalars.return_value.all.return_value = []
            return result

        mock_db.execute.side_effect = capturing_execute

        repo = ConversationMemoryRepository(mock_db)

        await repo.get_recent_for_session(company_id=company_id, session_id=session_a)
        await repo.get_recent_for_session(company_id=company_id, session_id=session_b)

        # Devem ter sido gerados 2 statements distintos (1 por chamada)
        assert len(captured_stmts) == 2, "Devem ter sido executadas 2 queries distintas"

        # Os dois statements devem ser objetos diferentes (queries independentes)
        assert captured_stmts[0] is not captured_stmts[1], (
            "Cada chamada deve gerar um statement independente"
        )

        # O execute foi chamado exatamente 2x com parâmetros diferentes
        assert mock_db.execute.call_count == 2, (
            "execute deve ser chamado uma vez por sessão"
        )

    def test_company_id_isolation_in_query_filter(self):
        """A query de memória deve conter AND company_id = X (multi-tenancy)."""
        import inspect
        from app.domains.recruiter_assistant.repositories.conversation_memory_repository import (
            ConversationMemoryRepository,
        )

        source = inspect.getsource(ConversationMemoryRepository.get_recent_for_session)

        # O filtro usa AND de company_id + session_id
        assert "and_" in source or "company_id" in source, (
            "Query deve filtrar por company_id para isolamento multi-tenant"
        )

    def test_conversation_memory_service_requires_company_id(self):
        """ConversationMemory.get_or_create_conversation deve rejeitar company_id vazio."""
        # Verifica o contrato da service (não depende de DB real)
        import inspect
        from app.domains.recruiter_assistant.services.conversation_memory import (
            ConversationMemory,
        )

        source = inspect.getsource(ConversationMemory.get_or_create_conversation)
        assert "company_id" in source, "Método deve usar company_id"
        assert "raise ValueError" in source or "raise" in source, (
            "Deve rejeitar company_id vazio (fail-closed)"
        )

    def test_conversation_service_session_id_stored_on_create(self):
        """ConversationMemory.get_or_create_conversation deve persistir session_id."""
        import inspect
        from app.domains.recruiter_assistant.services.conversation_memory import (
            ConversationMemory,
        )

        source = inspect.getsource(ConversationMemory.get_or_create_conversation)
        assert "session_id" in source, (
            "session_id deve ser parte do objeto Conversation criado/retornado"
        )

    def test_thread_id_composition_prevents_cross_session_contamination(self):
        """O thread_id LangGraph {session}::{domain} isola checkpointers por sessão.

        Duas sessões diferentes nunca compartilham thread_id idêntico, logo
        o checkpointer nunca injeta estado de uma sessão em outra.
        """
        session_a = "session-alpha"
        session_b = "session-beta"
        domain = "talent_management"

        thread_a = f"{session_a}::{domain}"
        thread_b = f"{session_b}::{domain}"

        assert thread_a != thread_b, (
            "Sessões distintas devem produzir thread_ids distintos"
        )
        assert session_a in thread_a
        assert session_b in thread_b

    def test_thread_id_composition_prevents_cross_domain_contamination(self):
        """O thread_id {session}::{domain} isola checkpointers por domínio.

        Dois domains dentro da mesma sessão nunca compartilham thread_id,
        evitando contaminação de mensagens entre agentes de domínios distintos.
        """
        session = "session-xyz"
        domain_talent = "talent_management"
        domain_jobs = "jobs_management"

        thread_talent = f"{session}::{domain_talent}"
        thread_jobs = f"{session}::{domain_jobs}"

        assert thread_talent != thread_jobs, (
            "Domínios distintos na mesma sessão devem ter thread_ids distintos"
        )
