"""Tests for navigate marker extraction + residual strip (FIX-NAVIGATE-LEAK hardening)."""
import re
import pytest


# ---------------------------------------------------------------------------
# Helpers (mirror of what agent_chat_sse.py does inline)
# ---------------------------------------------------------------------------

def _apply_navigate_pipeline(text: str):
    """
    Mirror do pipeline FIX-NAVIGATE-LEAK em agent_chat_sse.py:
    1. Camada 1: _extract_navigate_marker (strip + ui_action)
    2. Camada 2: strip residual regex
    Retorna (clean_text, ui_action, ui_action_params).
    """
    from app.orchestrator.context.chat_adapter import _extract_navigate_marker

    nav_ui_action = None
    nav_ui_params = None
    clean = text
    try:
        result = _extract_navigate_marker(clean)
        if result is not None:
            clean, page, params = result
            if page != "general":
                nav_ui_action = "navigate_to"
                nav_ui_params = {"page": page, **params}
    except Exception:
        pass
    # Camada 2: strip residual
    clean = re.sub(r"\[NAVIGATE:[^\]]*\]", "", clean).strip()
    return clean, nav_ui_action, nav_ui_params


# ---------------------------------------------------------------------------
# Testes do pipeline de strip (Camada 1 + Camada 2)
# ---------------------------------------------------------------------------

class TestNavigatePipelineNoLeak:
    """O pipeline completo nunca deixa [NAVIGATE:] vazar no texto limpo."""

    def test_single_marker_stripped(self):
        """Marker único é removido e gera ui_action."""
        clean, action, params = _apply_navigate_pipeline(
            "Te levando para Configurações! [NAVIGATE:configuracoes]"
        )
        assert "[NAVIGATE:" not in clean
        assert action == "navigate_to"
        assert params["page"] == "configuracoes"

    def test_multiple_markers_all_stripped(self):
        """Dois markers: primeiro gera ui_action, segundo é stripped pela Camada 2."""
        text = "Aqui [NAVIGATE:configuracoes] e também [NAVIGATE:vagas]"
        clean, action, params = _apply_navigate_pipeline(text)
        assert "[NAVIGATE:" not in clean, f"Marker residual encontrado em: {clean!r}"
        # Primeiro marker (configuracoes) gerou ui_action
        assert action == "navigate_to"

    def test_no_marker_no_action(self):
        """Mensagem sem markup passa intacta."""
        text = "Aqui estão seus candidatos."
        clean, action, params = _apply_navigate_pipeline(text)
        assert clean == text
        assert action is None
        assert params is None

    def test_only_marker_text_becomes_empty_string(self):
        """Mensagem que É só o marker resulta em string vazia (não leak)."""
        text = "[NAVIGATE:configuracoes]"
        clean, action, params = _apply_navigate_pipeline(text)
        assert clean == ""
        assert "[NAVIGATE:" not in clean

    def test_marker_with_id_stripped_and_ui_action(self):
        """Marker com id de vaga: stripped do texto + ui_action_params com id."""
        text = "Abrindo vaga [NAVIGATE:vaga_detalhe:abc-123] agora."
        clean, action, params = _apply_navigate_pipeline(text)
        assert "[NAVIGATE:" not in clean
        assert action == "navigate_to"
        assert params["id"] == "abc-123"

    def test_marker_with_deeplink_stripped(self):
        """Marker com query de deep-link: stripped do texto + params corretos."""
        text = "Editando [NAVIGATE:vaga_detalhe:xyz?tab=edit&section=descricao]"
        clean, action, params = _apply_navigate_pipeline(text)
        assert "[NAVIGATE:" not in clean
        assert action == "navigate_to"
        assert params["id"] == "xyz"
        assert params.get("query", {}).get("tab") == "edit"

    def test_residual_strip_handles_unknown_page(self):
        """Page desconhecida (normalize_page retorna 'general') → Camada 1 nao gera
        ui_action MAS Camada 2 faz strip do marker do texto."""
        # 'unknown_page_xyz' será normalizado para 'general' pelo canonical_pages
        text = "Mensagem com [NAVIGATE:unknown_page_xyz_aaaaa] markup."
        clean, action, params = _apply_navigate_pipeline(text)
        assert "[NAVIGATE:" not in clean, f"Marker nao stripped: {clean!r}"
        # 'general' não gera ui_action
        assert action is None

    def test_fallback_regex_strip_simulated(self):
        """
        Simula falha da Camada 1 (como se import falhasse) e verifica que
        a Camada 2 (regex puro) ainda faz strip do markup.
        """
        # Aplica diretamente só a Camada 2 (regex strip), simulando fallback
        text = "Texto com [NAVIGATE:configuracoes] markup."
        clean = re.sub(r"\[NAVIGATE:[^\]]*\]", "", text).strip()
        assert "[NAVIGATE:" not in clean
        assert clean == "Texto com  markup."

    def test_pipeline_text_preserved_around_marker(self):
        """Texto antes e depois do marker é preservado."""
        text = "Antes do marker [NAVIGATE:vagas] depois do marker"
        clean, _, _ = _apply_navigate_pipeline(text)
        assert "Antes do marker" in clean
        assert "depois do marker" in clean
        assert "[NAVIGATE:" not in clean


# ---------------------------------------------------------------------------
# Teste do system_prompt_builder — instrução de gerar markup ainda está ativa
# ---------------------------------------------------------------------------

class TestSystemPromptBuilderNavigateInstruction:
    """Verifica que o system_prompt ainda instrui o modelo a gerar [NAVIGATE:]."""

    def test_navigate_instruction_present_in_prompt_builder(self):
        """system_prompt_builder.py contém instrução de NAVIGATE (confirma que
        o agente pode gerar o markup — exige que o pipeline de strip esteja ativo)."""
        import subprocess
        result = subprocess.run(
            ["grep", "-c", r"\[NAVIGATE:", 
             "/home/runner/workspace/lia-agent-system/app/shared/prompts/system_prompt_builder.py"],
            capture_output=True, text=True
        )
        count = int(result.stdout.strip() or "0")
        assert count >= 3, (
            "system_prompt_builder.py deve conter pelo menos 3 referências a [NAVIGATE:] "
            "(instrução ao LLM). Se for 0, o modelo não saberá gerar o marker e a "
            "navegação quebrará. Verifique se o instrução foi removida acidentalmente."
        )

    def test_strip_pipeline_is_wired_in_sse(self):
        """agent_chat_sse.py deve conter a Camada 2 (strip residual) do pipeline."""
        import subprocess
        result = subprocess.run(
            ["grep", "-c", "Camada 2",
             "/home/runner/workspace/lia-agent-system/app/api/v1/agent_chat_sse.py"],
            capture_output=True, text=True
        )
        count = int(result.stdout.strip() or "0")
        assert count >= 1, (
            "agent_chat_sse.py deve conter o comentário 'Camada 2' do FIX-NAVIGATE-LEAK. "
            "O strip residual foi removido — risco de leak de markup para o FE."
        )
