"""
LIA-C03 + LIA-C04 — Testes unitários

LIA-C03: FairnessGuard intercepta args de tool calls discriminatórios no TimedToolNode.
LIA-C04: PII é automaticamente removido de HumanMessage/AIMessage antes do LLM
         no LangGraphReActBase (SystemMessage preservado).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tool_call(name: str, args: dict, call_id: str = "tc-001"):
    """Cria um mock de tool_call compatível com LangChain."""
    tc = MagicMock()
    tc.name = name
    tc.args = args
    tc.id = call_id
    return tc


# ---------------------------------------------------------------------------
# TestTimedToolNodeFairness — LIA-C03
# ---------------------------------------------------------------------------

class TestTimedToolNodeFairness:
    """Testa intercepção de tool calls discriminatórios pelo FairnessGuard."""

    def _make_node(self, fairness_enabled=True):
        """Cria TimedToolNode stub sem LangGraph real."""
        from lia_agents_core.timed_tool_node import TimedToolNode
        node = TimedToolNode.__new__(TimedToolNode)
        node.domain = "pipeline"
        node.default_timeout_seconds = 15
        node.tool_timeouts = {}
        node._tools_list = []
        node._fairness_tool_check_enabled = fairness_enabled
        return node

    @pytest.mark.asyncio
    async def test_tool_call_with_gender_filter_is_blocked(self):
        """Tool call com filtro de gênero deve ser bloqueada."""
        node = self._make_node()
        # "apenas homens" dispara regex de genero
        tool_args = {"filtros": "apenas homens", "vaga_id": "vaga-123"}
        result = await node._check_tool_args_fairness("search_candidates", tool_args)

        assert result is not None, "FairnessGuard deve bloquear filtro de gênero"
        # Mensagem educacional deve mencionar gênero ou legislação
        assert any(
            kw in result.lower()
            for kw in ["gênero", "genero", "clt", "discrimin", "legislação", "legislacao"]
        )

    @pytest.mark.asyncio
    async def test_tool_call_with_age_filter_string_is_blocked(self):
        """Tool call com string contendo filtro etário explícito deve ser bloqueada."""
        node = self._make_node()
        # "até 30 anos" e "apenas jovens" disparam regex de idade
        tool_args = {"query": "candidatos apenas jovens até 30 anos", "cargo": "dev"}
        result = await node._check_tool_args_fairness("search_candidates", tool_args)

        assert result is not None, "FairnessGuard deve bloquear filtro etário explícito"

    @pytest.mark.asyncio
    async def test_tool_call_without_bias_passes(self):
        """Tool call com args neutros não deve ser bloqueada."""
        node = self._make_node()
        tool_args = {"skills": ["Python", "SQL"], "experiencia_anos": 3, "cargo": "engenheiro"}
        result = await node._check_tool_args_fairness("search_candidates", tool_args)

        assert result is None, "Tool call sem viés não deve ser bloqueada"

    @pytest.mark.asyncio
    async def test_fairness_check_failure_does_not_break_execution(self):
        """Se FairnessGuard lançar exception internamente, tool call continua (fail-safe)."""
        node = self._make_node()

        # Patch no módulo onde FairnessGuard é importado localmente
        mock_guard = MagicMock()
        mock_guard.check.side_effect = RuntimeError("DB connection failed")

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard",
            return_value=mock_guard,
        ):
            result = await node._check_tool_args_fairness("search_candidates", {"query": "test"})

        assert result is None, "Falha no FairnessGuard deve ser silenciosa"

    @pytest.mark.asyncio
    async def test_fairness_check_disabled_by_flag(self):
        """_fairness_tool_check_enabled=False desativa a verificação por completo."""
        node = self._make_node(fairness_enabled=False)
        # Arg explicitamente discriminatório mas flag desativada
        tool_args = {"filtro": "apenas mulheres"}
        result = await node._check_tool_args_fairness("search_candidates", tool_args)

        assert result is None, "Com flag desativada, FairnessGuard não deve ser chamado"

    @pytest.mark.asyncio
    async def test_build_fairness_block_response_returns_tool_messages(self):
        """_build_fairness_block_response deve retornar ToolMessages com conteúdo correto."""
        from langchain_core.messages import ToolMessage

        node = self._make_node()
        tool_calls = [_make_tool_call("search_candidates", {"age": "<30"}, "tc-007")]
        state = {"messages": [MagicMock()]}

        result = node._build_fairness_block_response(
            state,
            tool_calls,
            "search_candidates",
            "Mensagem educacional de compliance.",
        )

        messages = result.get("messages", [])
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_messages) == 1
        assert "LIA-C03" in tool_messages[0].content
        assert "Mensagem educacional de compliance." in tool_messages[0].content
        assert tool_messages[0].tool_call_id == "tc-007"

    @pytest.mark.asyncio
    async def test_fairness_import_error_is_silenced(self):
        """ImportError ao importar FairnessGuard retorna None sem propagar exception."""
        node = self._make_node()

        with patch.dict("sys.modules", {"app.shared.compliance.fairness_guard": None}):
            result = await node._check_tool_args_fairness("tool", {"key": "value"})

        assert result is None, "ImportError deve ser tratado silenciosamente"

    @pytest.mark.asyncio
    async def test_race_filter_is_blocked(self):
        """Tool call com filtro de raça/etnia deve ser bloqueada."""
        node = self._make_node()
        tool_args = {"filtro": "apenas brancos", "departamento": "TI"}
        result = await node._check_tool_args_fairness("filter_candidates", tool_args)

        assert result is not None, "FairnessGuard deve bloquear filtro racial"


# ---------------------------------------------------------------------------
# TestLangGraphReActBasePII — LIA-C04
# ---------------------------------------------------------------------------

class TestLangGraphReActBasePII:
    """Testa remoção automática de PII de mensagens antes do LLM."""

    def _make_base(self, enable_pii_strip=True):
        """Cria instância mínima de LangGraphReActBase para testes."""
        from lia_agents_core.langgraph_react_base import LangGraphReActBase
        from lia_agents_core.agent_interface import AgentInput, AgentOutput

        class _TestAgent(LangGraphReActBase):
            domain_name = "test"
            available_tools = []

            def _build_graph(self):
                return MagicMock()

            async def process(self, input: AgentInput) -> AgentOutput:
                return AgentOutput(message="ok", confidence=1.0)

        agent = _TestAgent.__new__(_TestAgent)
        agent._enable_pii_strip = enable_pii_strip
        agent.domain_name = "test"
        return agent

    @pytest.mark.asyncio
    async def test_pii_stripped_from_human_messages(self):
        """CPF em HumanMessage deve ser removido antes do LLM."""
        from langchain_core.messages import HumanMessage

        agent = self._make_base()
        messages = [HumanMessage(content="Meu CPF é 123.456.789-00 e preciso de ajuda")]

        result = await agent._sanitize_messages_pii(messages)

        assert len(result) == 1
        assert "123.456.789-00" not in result[0].content
        assert "[CPF REMOVIDO]" in result[0].content

    @pytest.mark.asyncio
    async def test_email_stripped_from_human_messages(self):
        """Email em HumanMessage deve ser removido."""
        from langchain_core.messages import HumanMessage

        agent = self._make_base()
        messages = [HumanMessage(content="Contate-me em joao.silva@empresa.com.br")]

        result = await agent._sanitize_messages_pii(messages)

        assert "joao.silva@empresa.com.br" not in result[0].content
        assert "[EMAIL REMOVIDO]" in result[0].content

    @pytest.mark.asyncio
    async def test_system_message_not_stripped(self):
        """SystemMessage não deve ser modificado — pode ter placeholders."""
        from langchain_core.messages import SystemMessage

        agent = self._make_base()
        original_content = "Você é LIA. CPF do usuário: {cpf_placeholder} — use com cuidado."
        messages = [SystemMessage(content=original_content)]

        result = await agent._sanitize_messages_pii(messages)

        assert result[0].content == original_content, "SystemMessage não deve ser alterado"

    @pytest.mark.asyncio
    async def test_mixed_messages_only_human_stripped(self):
        """Apenas HumanMessage/AIMessage são sanitizados; SystemMessage preservado."""
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        agent = self._make_base()
        messages = [
            SystemMessage(content="System prompt com email: admin@sistema.com"),
            HumanMessage(content="Candidato: joao@email.com, CPF: 987.654.321-00"),
            AIMessage(content="Entendi. Vou processar o cadastro."),
        ]

        result = await agent._sanitize_messages_pii(messages)

        # SystemMessage intocado
        assert "admin@sistema.com" in result[0].content
        # HumanMessage sanitizado
        assert "joao@email.com" not in result[1].content
        assert "987.654.321-00" not in result[1].content
        # AIMessage sem PII — intacto
        assert result[2].content == "Entendi. Vou processar o cadastro."

    @pytest.mark.asyncio
    async def test_pii_strip_failure_does_not_break_pipeline(self):
        """Se strip_pii falhar, pipeline continua com mensagens originais (fail-safe)."""
        from langchain_core.messages import HumanMessage

        agent = self._make_base()
        original = "Mensagem com CPF 111.222.333-44"
        messages = [HumanMessage(content=original)]

        with patch(
            "app.shared.pii_masking.strip_pii_for_llm_prompt",
            side_effect=RuntimeError("PII module falhou"),
        ):
            result = await agent._sanitize_messages_pii(messages)

        # Deve retornar a lista original intacta
        assert len(result) == 1
        assert result[0].content == original

    @pytest.mark.asyncio
    async def test_disable_pii_strip_flag(self):
        """_enable_pii_strip = False desativa completamente o strip."""
        from langchain_core.messages import HumanMessage

        agent = self._make_base(enable_pii_strip=False)
        original = "CPF: 444.555.666-77, email: test@test.com"
        messages = [HumanMessage(content=original)]

        result = await agent._sanitize_messages_pii(messages)

        # Conteúdo não deve ter sido alterado
        assert result[0].content == original

    @pytest.mark.asyncio
    async def test_messages_without_string_content_not_affected(self):
        """Mensagens com content não-string (list) devem ser passadas sem modificação."""
        agent = self._make_base()
        # Simular mensagem com content = lista (multi-modal)
        msg = MagicMock()
        msg.__class__.__name__ = "HumanMessage"
        msg.content = [{"type": "text", "text": "CPF 555.666.777-88"}, {"type": "image"}]
        messages = [msg]

        result = await agent._sanitize_messages_pii(messages)

        # Content não-string não deve ser processado
        assert result[0].content == msg.content

    @pytest.mark.asyncio
    async def test_no_pii_message_unchanged(self):
        """Mensagem sem PII não deve ser alterada."""
        from langchain_core.messages import HumanMessage

        agent = self._make_base()
        original = "Preciso de candidatos com experiência em Python e AWS"
        messages = [HumanMessage(content=original)]

        result = await agent._sanitize_messages_pii(messages)

        assert result[0].content == original

    @pytest.mark.asyncio
    async def test_pii_strip_preserves_message_type(self):
        """Após strip, o tipo da mensagem deve ser preservado."""
        from langchain_core.messages import HumanMessage, AIMessage

        agent = self._make_base()
        messages = [
            HumanMessage(content="Email: user@test.com"),
            AIMessage(content="CPF detectado: 222.333.444-55"),
        ]

        result = await agent._sanitize_messages_pii(messages)

        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)
        assert "[EMAIL REMOVIDO]" in result[0].content
        assert "[CPF REMOVIDO]" in result[1].content
