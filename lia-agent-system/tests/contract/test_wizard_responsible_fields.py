"""Contract tests — T9: wizard pergunta recrutador + gestor (4 campos responsáveis).

Valida que:
1. System prompt instrui o LLM a perguntar manager, manager_email, recruiter, recruiter_email.
2. _handle_set_job_fields aceita os 4 campos e grava no state.
3. Emails inválidos (recruiter_email e manager_email) são rejeitados.
4. PII mascarada em recruiter_email é ignorada (mesmo padrão de manager_email).
"""
from __future__ import annotations

import pytest

from app.domains.job_creation.orchestrator.wizard_tools import (
    ToolContext,
    _handle_set_job_fields,
    _SETTABLE_JOB_FIELDS,
    _FIELD_TO_STATE_KEY,
)


_CTX = ToolContext(company_id="test-company-001", user_id="user-001")


class TestSystemPromptMentionsResponsibleFields:
    """Sensor: system prompt deve instruir o LLM a perguntar responsáveis."""

    def test_prompt_mentions_all_four_fields(self):
        from app.domains.job_creation.orchestrator.wizard_orchestrator import (
            _SYSTEM_PROMPT_BASE,
        )
        for field_name in ("manager_name", "manager_email", "recruiter", "recruiter_email"):
            assert field_name in _SYSTEM_PROMPT_BASE, (
                f"System prompt não menciona '{field_name}'. "
                f"O LLM precisa ser instruído a perguntar esse campo."
            )

    def test_prompt_mentions_responsaveis_section(self):
        from app.domains.job_creation.orchestrator.wizard_orchestrator import (
            _SYSTEM_PROMPT_BASE,
        )
        assert "Responsáveis pela vaga" in _SYSTEM_PROMPT_BASE, (
            "System prompt deve ter seção 'Responsáveis pela vaga'."
        )


class TestSetJobFieldsAcceptsResponsibleFields:
    """handler aceita manager_name, manager_email, recruiter, recruiter_email."""

    def test_settable_fields_include_all_four(self):
        for f in ("manager_name", "manager_email", "recruiter", "recruiter_email"):
            assert f in _SETTABLE_JOB_FIELDS, f"'{f}' ausente em _SETTABLE_JOB_FIELDS"

    def test_field_to_state_key_maps_all_four(self):
        for f in ("manager_name", "manager_email", "recruiter", "recruiter_email"):
            assert f in _FIELD_TO_STATE_KEY, f"'{f}' ausente em _FIELD_TO_STATE_KEY"

    def test_set_manager_name_accepted(self):
        result = _handle_set_job_fields({}, {"manager_name": "Maria Silva"}, _CTX)
        assert not result.error, f"Erro inesperado: {result.llm_message}"
        assert result.state_updates.get("parsed_manager_name") == "Maria Silva"

    def test_set_recruiter_accepted(self):
        result = _handle_set_job_fields({}, {"recruiter": "João Souza"}, _CTX)
        assert not result.error, f"Erro inesperado: {result.llm_message}"
        assert result.state_updates.get("parsed_recruiter") == "João Souza"

    def test_set_recruiter_email_valid(self):
        result = _handle_set_job_fields(
            {}, {"recruiter_email": "joao@example.com"}, _CTX
        )
        assert not result.error, f"Erro inesperado: {result.llm_message}"
        assert result.state_updates.get("parsed_recruiter_email") == "joao@example.com"

    def test_set_all_four_at_once(self):
        result = _handle_set_job_fields(
            {},
            {
                "manager_name": "Maria Silva",
                "manager_email": "maria@corp.com",
                "recruiter": "João Souza",
                "recruiter_email": "joao@corp.com",
            },
            _CTX,
        )
        assert not result.error, f"Erro inesperado: {result.llm_message}"
        assert result.state_updates["parsed_manager_name"] == "Maria Silva"
        assert result.state_updates["parsed_manager_email"] == "maria@corp.com"
        assert result.state_updates["parsed_recruiter"] == "João Souza"
        assert result.state_updates["parsed_recruiter_email"] == "joao@corp.com"


class TestEmailValidationRejectsInvalid:
    """Emails inválidos são rejeitados com mensagem acionável."""

    def test_invalid_recruiter_email_rejected(self):
        result = _handle_set_job_fields(
            {}, {"recruiter_email": "not-an-email"}, _CTX
        )
        assert result.error
        assert "inválido" in result.llm_message.lower()

    def test_invalid_manager_email_rejected(self):
        result = _handle_set_job_fields(
            {}, {"manager_email": "bad-email"}, _CTX
        )
        assert result.error
        assert "inválido" in result.llm_message.lower()


class TestMaskedPiiIgnored:
    """PII mascarada (LGPD) em emails é ignorada silenciosamente."""

    def test_masked_recruiter_email_ignored(self):
        result = _handle_set_job_fields(
            {}, {"recruiter_email": "[EMAIL REMOVIDO]", "title": "Dev"}, _CTX
        )
        assert not result.error
        assert "parsed_recruiter_email" not in result.state_updates
        # title still applied
        assert result.state_updates.get("parsed_title") == "Dev"

    def test_masked_manager_email_ignored(self):
        result = _handle_set_job_fields(
            {}, {"manager_email": "[EMAIL REMOVIDO]", "title": "Dev"}, _CTX
        )
        assert not result.error
        assert "parsed_manager_email" not in result.state_updates
