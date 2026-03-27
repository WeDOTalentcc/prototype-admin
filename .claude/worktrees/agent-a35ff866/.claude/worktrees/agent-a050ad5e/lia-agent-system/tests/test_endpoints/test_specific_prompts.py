"""Tests for Bloco A-F — Wizard, Pipeline Transition e Policy prompts.

Validates:
- company_id obrigatório e nunca "demo" hardcoded
- session_id nunca "default" compartilhado em policy chat
- conversation_id presente no schema de request e response (transição)
- Fallback legacy removido (policy + transição)
- generate_enriched_jd não chamado diretamente no endpoint wizard
- Auto-save draft incremental no wizard
- Hook useInterpretContext gerencia conversationId
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
FE_ROOT = PROJECT_ROOT.parent / "plataforma-lia" / "src"


def _read_be(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text()


def _read_fe(relative_path: str) -> str:
    return (FE_ROOT / relative_path).read_text()


# ── Bloco A: company_id obrigatório ─────────────────────────────────────────

def test_transition_company_id_uses_helper():
    """Transição: company_id usa get_user_company_id, não fallback manual."""
    content = _read_be("app/api/v1/recruitment_stages.py")
    # Deve usar o helper
    assert "company_id = request.company_id or get_user_company_id(current_user)" in content
    # Não deve mais ter o fallback manual de getattr
    assert 'getattr(current_user, "company_id", "") or ""' not in content


def test_policy_session_id_never_default():
    """Policy chat: session_id nunca usa string literal 'default'."""
    content = _read_be("app/api/v1/hiring_policy.py")
    assert 'session_id = payload.session_id or "default"' not in content
    assert "uuid.uuid4()" in content


def test_wizard_company_id_uses_helper():
    """Wizard: company_id usa get_user_company_id."""
    content = _read_be("app/api/v1/wizard_smart_orchestrator.py")
    assert "get_user_company_id(current_user)" in content


# ── Bloco B: conversation_id persistido na transição ────────────────────────

def test_transition_request_has_conversation_id():
    """InterpretContextRequest deve ter campo conversation_id."""
    content = _read_be("app/api/v1/recruitment_stages.py")
    assert "conversation_id: Optional[str]" in content


def test_transition_response_has_conversation_id():
    """InterpretContextResponse deve ter campo conversation_id."""
    content = _read_be("app/api/v1/recruitment_stages.py")
    assert "class InterpretContextResponse" in content
    # conversation_id deve aparecer na response model
    response_section = content.split("class InterpretContextResponse")[1].split("\n\n")[0]
    assert "conversation_id" in response_section


def test_transition_endpoint_generates_conv_id():
    """Endpoint de transição deve gerar conv_id via uuid4, não string fixa."""
    content = _read_be("app/api/v1/recruitment_stages.py")
    assert "conv_id = request.conversation_id or str(uuid.uuid4())" in content
    # Session ID fixo deve estar removido
    assert 'session_id=f"transition_{request.candidate_id}_{request.to_stage}"' not in content


def test_transition_response_returns_conv_id():
    """Response do Layer 3 deve incluir conversation_id=conv_id."""
    content = _read_be("app/api/v1/recruitment_stages.py")
    assert "conversation_id=conv_id," in content


def test_frontend_hook_has_conversation_id_state():
    """useInterpretContext deve ter estado conversationId e persistir entre turns."""
    content = _read_fe("hooks/use-interpret-context.ts")
    assert "conversationId" in content
    assert "setConversationId" in content
    # Envia conversation_id na request
    assert "conversation_id: conversationId" in content
    # Salva da response
    assert "data.conversation_id" in content


def test_frontend_hook_resets_conversation_id():
    """reset() do hook deve limpar conversationId."""
    content = _read_fe("hooks/use-interpret-context.ts")
    assert "setConversationId(undefined)" in content


# ── Bloco C: 3-layer fallback removido da transição ─────────────────────────

def test_transition_no_layer2_llm_fallback():
    """Layer 2 (LLM single-shot) deve estar removido como caminho de resposta."""
    content = _read_be("app/api/v1/recruitment_stages.py")
    assert "interpret_with_llm" not in content or "# Layer 2" not in content
    # Não deve mais chamar interpret_with_llm
    assert "llm_result = await interpret_with_llm" not in content


def test_transition_graceful_fallback_not_500():
    """Quando ReAct falha, deve retornar mensagem amigável (não HTTP 500)."""
    content = _read_be("app/api/v1/recruitment_stages.py")
    assert "Estou com dificuldade em processar agora" in content or \
           "Nao consegui processar" in content or \
           "não consegui processar" in content.lower()


# ── Bloco D: fallback legacy removido de policy ──────────────────────────────

def test_policy_no_legacy_setup_agent_fallback():
    """policy_setup_agent não deve ser usado como fallback do ReAct."""
    content = _read_be("app/api/v1/hiring_policy.py")
    # Pode ainda ser importado, mas não deve ser chamado no except do ReAct
    assert "policy_setup_agent.process_message" not in content


def test_policy_graceful_fallback_message():
    """Quando PolicyReActAgent falha, deve retornar mensagem amigável."""
    content = _read_be("app/api/v1/hiring_policy.py")
    assert "Estou com dificuldade" in content or "tente novamente" in content.lower()


# ── Bloco E: generate_enriched_jd autônomo ───────────────────────────────────

def test_wizard_no_auto_call_enriched_jd_in_endpoint():
    """Endpoint wizard não deve chamar generate_enriched_jd diretamente."""
    content = _read_be("app/api/v1/wizard_smart_orchestrator.py")
    # Não deve ter o bloco de auto-call
    assert "Auto-calling generate_enriched_jd" not in content
    assert "enrichment_result = await generate_enriched_jd" not in content


def test_wizard_system_prompt_instructs_agent_to_call_enriched_jd():
    """System prompt do wizard deve instruir o agente a chamar generate_enriched_jd autonomamente."""
    content = _read_be("app/domains/job_management/agents/wizard_system_prompt.py")
    assert "generate_enriched_jd" in content
    assert "jd-enrichment" in content
    assert "autonomo" in content.lower() or "AUTONOMA" in content or "autonomamente" in content.lower()


# ── Bloco F: auto-save draft ─────────────────────────────────────────────────

def test_wizard_auto_save_draft_incremental():
    """Wizard deve salvar draft incremental no Redis após cada turno bem-sucedido."""
    content = _read_be("app/api/v1/wizard_smart_orchestrator.py")
    assert "wizard_draft:" in content
    assert "setex" in content
    assert "Draft auto-saved" in content or "draft" in content.lower()


# ── Bloco G: conversation_id retornado nas responses ─────────────────────────

def test_wizard_response_returns_conversation_id():
    """SmartOrchestrateResponse deve ter campo conversation_id."""
    content = _read_be("app/api/v1/wizard_smart_orchestrator.py")
    assert "conversation_id: Optional[str]" in content
    # O campo deve ser retornado na response (não apenas no request)
    response_section = content.split("class SmartOrchestrateResponse")[1].split("\n\n")[0]
    assert "conversation_id" in response_section


def test_wizard_endpoint_returns_session_id_in_conversation_id():
    """Endpoint smart_orchestrate deve preencher conversation_id=session_id na response."""
    content = _read_be("app/api/v1/wizard_smart_orchestrator.py")
    assert "conversation_id=session_id," in content


def test_policy_response_schema_has_session_id():
    """PolicyChatResponse deve ter campo session_id."""
    content = _read_be("app/schemas/company_hiring_policy.py")
    # session_id deve aparecer na classe response
    response_section = content.split("class PolicyChatResponse")[1]
    assert "session_id" in response_section


def test_policy_endpoint_returns_session_id():
    """Endpoint policy_chat deve retornar session_id na response."""
    content = _read_be("app/api/v1/hiring_policy.py")
    assert "session_id=session_id," in content
