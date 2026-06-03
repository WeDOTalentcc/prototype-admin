"""
Testes unitários para WizardOrchestratorService (G.1).

Cobrem:
- _detect_intent: keyword matching para todos os intents
- process_wizard_message: dict com campos obrigatórios, tool_call, confirmation
- get_available_intents: 8 intents (sem UNKNOWN)
- build_context_for_prompt: truncation
"""
import pytest

from app.domains.job_management.services.wizard_orchestrator_service import (
    WizardOrchestratorService,
    WizardIntent,
    IntentDetectionResult,
    SuggestedToolCall,
    MAX_CONTEXT_CHARS,
)


class TestWizardOrchestratorService:
    def setup_method(self):
        self.svc = WizardOrchestratorService()

    # ------------------------------------------------------------------
    # _detect_intent — keyword matching
    # ------------------------------------------------------------------

    def test_detect_intent_publicar(self):
        """'publicar' → PUBLISH_JOB com requires_confirmation=True."""
        result = self.svc._detect_intent("quero publicar a vaga")
        assert result.intent == WizardIntent.PUBLISH_JOB
        assert result.confidence == 0.85
        assert result.suggested_tool_call is not None
        assert result.suggested_tool_call.requires_confirmation is True

    def test_detect_intent_pausar(self):
        """'pausar' → PAUSE_JOB."""
        result = self.svc._detect_intent("preciso pausar esta vaga")
        assert result.intent == WizardIntent.PAUSE_JOB

    def test_detect_intent_encerrar(self):
        """'encerrar' → CLOSE_JOB."""
        result = self.svc._detect_intent("vou encerrar a vaga hoje")
        assert result.intent == WizardIntent.CLOSE_JOB

    def test_detect_intent_salvar(self):
        """'salvar' → SAVE_DRAFT, requires_confirmation=False."""
        result = self.svc._detect_intent("salvar rascunho da vaga")
        assert result.intent == WizardIntent.SAVE_DRAFT
        assert result.suggested_tool_call is not None
        assert result.suggested_tool_call.requires_confirmation is False
        assert result.suggested_tool_call.confirmation_message is None

    def test_detect_intent_salario(self):
        """'salário' → SEARCH_SALARY."""
        result = self.svc._detect_intent("qual é o salário de mercado?")
        assert result.intent == WizardIntent.SEARCH_SALARY

    def test_detect_intent_unknown(self):
        """Mensagem sem keywords → UNKNOWN com confidence=0.5."""
        result = self.svc._detect_intent("olá, bom dia")
        assert result.intent == WizardIntent.UNKNOWN
        assert result.confidence == 0.5

    def test_detect_intent_returns_keyword_entity(self):
        """Intenção detectada deve ter entities['keyword'] presente."""
        result = self.svc._detect_intent("publicar vaga agora")
        assert "keyword" in result.entities
        assert result.entities["keyword"] != ""

    # ------------------------------------------------------------------
    # process_wizard_message — dict com campos obrigatórios
    # ------------------------------------------------------------------

    def test_process_wizard_message_returns_required_keys(self):
        """Resultado deve ter intent, confidence, entities."""
        result = self.svc.process_wizard_message("salvar agora")
        assert "intent" in result
        assert "confidence" in result
        assert "entities" in result

    def test_process_wizard_message_includes_tool_call_for_known_intent(self):
        """Intent reconhecida deve gerar suggested_tool_call não-None."""
        result = self.svc.process_wizard_message("publicar a vaga")
        assert "suggested_tool_call" in result
        assert result["suggested_tool_call"] is not None

    def test_process_wizard_message_confirmation_message_set_for_publish(self):
        """Publicar tem requires_confirmation=True → confirmation_message presente."""
        result = self.svc.process_wizard_message("publicar a vaga")
        tool = result.get("suggested_tool_call")
        assert tool is not None
        assert tool["requires_confirmation"] is True
        assert tool["confirmation_message"] is not None

    def test_process_wizard_message_no_confirmation_for_save(self):
        """Salvar tem requires_confirmation=False → confirmation_message é None."""
        result = self.svc.process_wizard_message("salvar rascunho")
        tool = result.get("suggested_tool_call")
        assert tool is not None
        assert tool["requires_confirmation"] is False
        assert tool["confirmation_message"] is None

    def test_process_wizard_message_unknown_has_no_tool_call(self):
        """Intent UNKNOWN não gera suggested_tool_call."""
        result = self.svc.process_wizard_message("olá")
        assert result["intent"] == WizardIntent.UNKNOWN.value
        assert "suggested_tool_call" not in result

    def test_process_wizard_message_include_response_false(self):
        """include_response=False omite conversational_response."""
        result = self.svc.process_wizard_message("publicar vaga", include_response=False)
        assert "conversational_response" not in result

    # ------------------------------------------------------------------
    # get_available_intents
    # ------------------------------------------------------------------

    def test_get_available_intents_count(self):
        """Deve retornar exatamente 8 intents (UNKNOWN não incluso)."""
        intents = self.svc.get_available_intents()
        assert len(intents) == 8

    def test_get_available_intents_close_job_required_params(self):
        """CLOSE_JOB deve ter required_params=['job_id', 'reason']."""
        intents = self.svc.get_available_intents()
        close_job = next(i for i in intents if i["intent"] == WizardIntent.CLOSE_JOB.value)
        assert close_job["required_params"] == ["job_id", "reason"]

    def test_get_available_intents_no_unknown(self):
        """UNKNOWN não deve aparecer na lista de intents disponíveis."""
        intents = self.svc.get_available_intents()
        intent_values = [i["intent"] for i in intents]
        assert WizardIntent.UNKNOWN.value not in intent_values

    def test_get_available_intents_all_have_tool_name(self):
        """Todos os intents disponíveis devem ter tool_name."""
        for item in self.svc.get_available_intents():
            assert "tool_name" in item
            assert item["tool_name"] != ""

    # ------------------------------------------------------------------
    # build_context_for_prompt — truncation
    # ------------------------------------------------------------------

    def test_build_context_truncates_at_max_chars(self):
        """Contexto muito longo deve ser truncado com nota de truncation."""
        long_summary = "x" * (MAX_CONTEXT_CHARS + 5000)
        context_data = {"summary": long_summary, "messages": []}
        result = self.svc.build_context_for_prompt(context_data)
        assert len(result) <= MAX_CONTEXT_CHARS
        assert "truncado" in result.lower()

    def test_build_context_includes_summary(self):
        """Contexto com summary deve incluir o resumo no output."""
        context_data = {"summary": "conversa sobre vaga de dev", "messages": []}
        result = self.svc.build_context_for_prompt(context_data)
        assert "conversa sobre vaga de dev" in result

    def test_build_context_includes_messages(self):
        """Contexto com messages deve incluir as mensagens."""
        context_data = {
            "summary": None,
            "messages": [
                {"role": "user", "content": "quero criar uma vaga"},
                {"role": "assistant", "content": "claro, qual o cargo?"},
            ],
        }
        result = self.svc.build_context_for_prompt(context_data)
        assert "quero criar uma vaga" in result

