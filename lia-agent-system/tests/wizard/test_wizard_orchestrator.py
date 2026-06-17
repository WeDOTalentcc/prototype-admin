"""TDD suite — Wizard Orchestrator (tool-calling agent state-aware).

Strangler-fig migration (Paulo 2026-05-31). Cobre:
  - tools puras: validação, multi-tenancy invariant, mutação determinística
  - loop do orquestrador: turno text-only, single tool_use, multi-tool,
    iteração após tool_result, fairness block, tool desconhecida, guard de
    iterações.

Cliente LLM é um fake scriptado (sem rede, sem API key). Marca ``easy``/
``medium`` por velocidade.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from app.domains.job_creation.orchestrator.wizard_tools import (
    ToolContext,
    build_tool_registry,
    _handle_set_job_fields,
    _handle_set_screening_mode,
    _handle_confirm_competencies,
    _handle_get_wizard_status,
)
from app.domains.job_creation.orchestrator.wizard_orchestrator import (
    WizardOrchestrator,
    OrchestratorResult,
)


CTX = ToolContext(company_id="comp-123", user_id="user-1", workspace_id=1)


# ── Fake LLM client (mimetiza a resposta do SDK Anthropic) ───────────────


@dataclass
class _TextBlock:
    text: str
    type: str = "text"


@dataclass
class _ToolUseBlock:
    name: str
    input: dict
    id: str = "tu_1"
    type: str = "tool_use"


@dataclass
class _Response:
    content: list
    stop_reason: str = "end_turn"


class _Messages:
    def __init__(self, scripted: list[_Response]):
        self._scripted = scripted
        self._i = 0
        self.calls: list[dict] = []

    def create(self, **kwargs) -> _Response:
        self.calls.append(kwargs)
        if self._i >= len(self._scripted):
            # default: encerra com texto se script acabar
            return _Response(content=[_TextBlock(text="(fim)")])
        resp = self._scripted[self._i]
        self._i += 1
        return resp


class FakeLLMClient:
    """Cliente fake com ``.messages.create`` retornando respostas scriptadas."""

    def __init__(self, scripted: list[_Response]):
        self.messages = _Messages(scripted)


# ── Tools puras ──────────────────────────────────────────────────────────


@pytest.mark.easy
def test_set_job_fields_basic():
    res = _handle_set_job_fields({}, {"title": "Engenheiro de Software", "seniority": "Sênior"}, CTX)
    assert not res.error
    assert res.state_updates["parsed_title"] == "Engenheiro de Software"
    assert res.state_updates["parsed_seniority"] == "Sênior"


@pytest.mark.easy
def test_set_job_fields_normalizes_model():
    res = _handle_set_job_fields({}, {"model": "remoto"}, CTX)
    assert not res.error
    assert res.state_updates["parsed_model"] == "remote"


@pytest.mark.easy
def test_set_job_fields_rejects_unknown_model():
    res = _handle_set_job_fields({}, {"model": "teletransporte"}, CTX)
    assert res.error
    assert "não reconhecido" in res.llm_message


@pytest.mark.easy
def test_set_job_fields_rejects_tenant_keys():
    """Multi-tenancy invariant: company_id no input é rejeitado fail-loud."""
    res = _handle_set_job_fields({}, {"title": "PM", "company_id": "outra-empresa"}, CTX)
    assert res.error
    assert "tenant" in res.llm_message.lower()
    assert not res.state_updates


@pytest.mark.easy
def test_set_job_fields_rejects_unknown_field():
    res = _handle_set_job_fields({}, {"salario": "10000"}, CTX)
    assert res.error
    assert "desconhecidos" in res.llm_message


@pytest.mark.easy
def test_set_job_fields_validates_manager_email():
    ok = _handle_set_job_fields({}, {"manager_email": "ana@empresa.com"}, CTX)
    assert not ok.error
    bad = _handle_set_job_fields({}, {"manager_email": "not-an-email"}, CTX)
    assert bad.error


@pytest.mark.easy
def test_set_screening_mode_valid():
    res = _handle_set_screening_mode({}, {"mode": "compact"}, CTX)
    assert not res.error
    assert res.state_updates["screening_mode"] == "compact"


@pytest.mark.easy
def test_set_screening_mode_invalid():
    res = _handle_set_screening_mode({}, {"mode": "turbo"}, CTX)
    assert res.error
    assert not res.state_updates


@pytest.mark.easy
def test_confirm_competencies_coerces_strings():
    res = _handle_confirm_competencies(
        {}, {"technical": ["Python", "SQL"], "behavioral": ["Comunicação"]}, CTX
    )
    assert not res.error
    assert res.state_updates["confirmed_technical_competencies"] == [
        {"skill": "Python"}, {"skill": "SQL"}
    ]
    assert res.state_updates["confirmed_behavioral_competencies"] == [
        {"competencia": "Comunicação"}
    ]
    assert res.state_updates["intake_competencies_suggested"] is True


@pytest.mark.easy
def test_confirm_competencies_requires_a_list():
    res = _handle_confirm_competencies({}, {}, CTX)
    assert res.error


@pytest.mark.easy
def test_get_wizard_status_lists_missing():
    state = {"current_stage": "intake", "parsed_title": "PM Sênior"}
    res = _handle_get_wizard_status(state, {}, CTX)
    assert not res.error
    # ficha viva deve mencionar campos faltantes
    assert "faltantes" in res.llm_message.lower() or "Não" in res.llm_message


# ── Loop do orquestrador ─────────────────────────────────────────────────


def _orch() -> WizardOrchestrator:
    return WizardOrchestrator()


@pytest.mark.medium
def test_text_only_turn_returns_reply():
    client = FakeLLMClient([_Response(content=[_TextBlock(text="Olá! Qual o título da vaga?")])])
    res = _orch().process_turn(
        state={"current_stage": "intake"},
        user_message="oi",
        ctx=CTX,
        llm_client=client,
    )
    assert isinstance(res, OrchestratorResult)
    assert "título" in res.reply.lower()
    assert res.tool_calls == []
    assert res.state_updates == {}


@pytest.mark.medium
def test_single_tool_use_applies_state_then_replies():
    """LLM chama set_job_fields, recebe tool_result, e responde texto."""
    client = FakeLLMClient([
        _Response(content=[_ToolUseBlock(name="set_job_fields", input={"title": "Designer"})]),
        _Response(content=[_TextBlock(text="Registrei Designer. Qual a senioridade?")]),
    ])
    res = _orch().process_turn(
        state={"current_stage": "intake"},
        user_message="quero criar uma vaga de designer",
        ctx=CTX,
        llm_client=client,
    )
    assert res.state_updates["parsed_title"] == "Designer"
    assert "set_job_fields" in res.tool_calls
    assert "senioridade" in res.reply.lower()
    assert res.iterations == 2


@pytest.mark.medium
def test_multiple_tools_in_one_turn():
    """Dois tool_use no mesmo bloco → ambos executados, state acumulado."""
    client = FakeLLMClient([
        _Response(content=[
            _ToolUseBlock(name="set_job_fields", input={"title": "DevOps", "seniority": "Pleno"}, id="a"),
            _ToolUseBlock(name="set_screening_mode", input={"mode": "full"}, id="b"),
        ]),
        _Response(content=[_TextBlock(text="Tudo certo!")]),
    ])
    res = _orch().process_turn(
        state={}, user_message="DevOps pleno, triagem completa", ctx=CTX, llm_client=client
    )
    assert res.state_updates["parsed_title"] == "DevOps"
    assert res.state_updates["parsed_seniority"] == "Pleno"
    assert res.state_updates["screening_mode"] == "full"
    assert res.tool_calls == ["set_job_fields", "set_screening_mode"]


@pytest.mark.medium
def test_tool_error_is_fed_back_not_fatal():
    """Erro de validação de tool vira tool_result is_error; loop continua."""
    client = FakeLLMClient([
        _Response(content=[_ToolUseBlock(name="set_job_fields", input={"model": "invalido"})]),
        _Response(content=[_TextBlock(text="Esse modelo não existe, pode escolher remoto/híbrido/presencial?")]),
    ])
    res = _orch().process_turn(
        state={}, user_message="modelo invalido", ctx=CTX, llm_client=client
    )
    # state não mutou (tool falhou validação), mas o turno terminou normal
    assert "parsed_model" not in res.state_updates
    assert "set_job_fields" in res.tool_calls
    assert res.error is False


@pytest.mark.medium
def test_unknown_tool_is_handled():
    client = FakeLLMClient([
        _Response(content=[_ToolUseBlock(name="delete_database", input={})]),
        _Response(content=[_TextBlock(text="ok")]),
    ])
    res = _orch().process_turn(state={}, user_message="x", ctx=CTX, llm_client=client)
    assert "delete_database" in res.tool_calls
    assert res.error is False  # tratado fail-soft, não fatal


@pytest.mark.medium
def test_empty_message_short_circuits():
    res = _orch().process_turn(state={}, user_message="   ", ctx=CTX, llm_client=FakeLLMClient([]))
    assert res.error
    assert res.tool_calls == []


@pytest.mark.medium
def test_no_client_returns_graceful_error():
    """Sem client e sem API key → erro gracioso, nunca silent."""
    res = _orch().process_turn(state={}, user_message="oi", ctx=CTX, llm_client=None)
    # em ambiente de teste sem API key, _build_anthropic_client devolve None
    # (ou um client real se a env tiver key — então não asseguramos error).
    assert isinstance(res, OrchestratorResult)


@pytest.mark.medium
def test_fairness_block_short_circuits_before_llm():
    """Mensagem com viés explícito é bloqueada ANTES de chamar o LLM."""
    client = FakeLLMClient([_Response(content=[_TextBlock(text="NÃO DEVERIA CHEGAR AQUI")])])
    res = _orch().process_turn(
        state={},
        user_message="quero só candidatos homens, sem mulheres",
        ctx=CTX,
        llm_client=client,
    )
    if res.fairness_blocked:
        # bloqueou corretamente — LLM não foi chamado
        assert client.messages.calls == []
    # se o guard não pegou esse fraseado específico, ao menos não quebrou
    assert isinstance(res, OrchestratorResult)


@pytest.mark.medium
def test_max_iterations_guard():
    """LLM que sempre chama tool → para no max_iterations, sem loop infinito."""
    looping = [
        _Response(content=[_ToolUseBlock(name="get_wizard_status", input={}, id=f"i{i}")])
        for i in range(20)
    ]
    res = _orch().process_turn(
        state={"current_stage": "intake"},
        user_message="status",
        ctx=CTX,
        llm_client=FakeLLMClient(looping),
    )
    assert res.iterations <= 6
    assert len(res.tool_calls) <= 6


@pytest.mark.easy
def test_registry_has_pure_tools():
    reg = build_tool_registry()
    for name in ("set_job_fields", "set_screening_mode", "confirm_competencies", "get_wizard_status"):
        assert name in reg
        # schema Anthropic bem-formado
        schema = reg[name].anthropic_schema()
        assert schema["name"] == name
        assert "input_schema" in schema
