"""TDD — Wizard Orchestrator text-accumulation regression ("wizard burro").

Bug confirmado em runtime (WIZDIAG): quando o modelo emite TEXTO + tool_use na
MESMA iteração (ex.: iter1 "Perfeito! Registrei o título Diretor de Compliance"
+ set_job_fields), o loop executava a tool e continuava — DESCARTANDO o texto
daquela iteração. A iteração seguinte vinha vazia (content=[]), e o branch
terminal devolvia o fallback genérico "Certo! Como deseja seguir?", perdendo o
reconhecimento do título. Fix canônico: acumular o texto de QUALQUER iteração e
usá-lo no reply terminal.

Cliente LLM é fake scriptado (sem rede / sem API key), mesmo harness do
test_wizard_orchestrator.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from app.domains.job_creation.orchestrator.wizard_tools import ToolContext
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
    input: dict = field(default_factory=dict)
    id: str = "tu_1"
    type: str = "tool_use"


@dataclass
class _Response:
    content: list
    stop_reason: str = "end_turn"


class _Messages:
    def __init__(self, scripted):
        self._scripted = scripted
        self._i = 0
        self.calls: list = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        resp = self._scripted[self._i]
        self._i += 1
        return resp


class FakeLLMClient:
    def __init__(self, scripted):
        self.messages = _Messages(scripted)


def _orch() -> WizardOrchestrator:
    return WizardOrchestrator()


_TITLE_TEXT = "Perfeito! Registrei o título Diretor de Compliance"


@pytest.mark.medium
def test_text_plus_tool_in_iter1_then_empty_iter2_keeps_text():
    """REGRESSÃO "wizard burro": texto+tool no iter1, iter2 vazio.

    O reply DEVE ser o texto do iter1 (não o fallback genérico). Sem o fix, o
    texto seria descartado e o usuário veria "Certo! Como deseja seguir?".
    """
    client = FakeLLMClient([
        # iter1: TEXTO + tool_use no MESMO turno
        _Response(content=[
            _TextBlock(text=_TITLE_TEXT),
            _ToolUseBlock(
                name="set_job_fields",
                input={"title": "Diretor de Compliance"},
            ),
        ]),
        # iter2: conteúdo VAZIO (o modelo não tem mais nada a dizer)
        _Response(content=[]),
    ])
    res = _orch().process_turn(
        state={"current_stage": "intake"},
        user_message="o título é Diretor de Compliance",
        ctx=CTX,
        llm_client=client,
    )
    assert isinstance(res, OrchestratorResult)
    assert "Registrei o título" in res.reply
    assert res.reply == _TITLE_TEXT
    assert res.reply != "Certo! Como deseja seguir?"
    # a tool ainda executou (estado registrado)
    assert "set_job_fields" in res.tool_calls
    assert res.state_updates.get("parsed_title") == "Diretor de Compliance"
    assert res.iterations == 2


@pytest.mark.medium
def test_tool_only_iter1_then_text_iter2_no_regression():
    """Caso que já funcionava: tool sem texto no iter1, texto no iter2."""
    reply_text = "Registrei Designer. Qual a senioridade?"
    client = FakeLLMClient([
        _Response(content=[
            _ToolUseBlock(name="set_job_fields", input={"title": "Designer"}),
        ]),
        _Response(content=[_TextBlock(text=reply_text)]),
    ])
    res = _orch().process_turn(
        state={"current_stage": "intake"},
        user_message="quero criar uma vaga de designer",
        ctx=CTX,
        llm_client=client,
    )
    assert res.reply == reply_text
    assert "set_job_fields" in res.tool_calls
    assert res.state_updates.get("parsed_title") == "Designer"
    assert res.iterations == 2


@pytest.mark.medium
def test_truly_empty_first_iter_uses_fallback():
    """Caso genuinamente vazio (sem texto em NENHUMA iteração) → fallback."""
    client = FakeLLMClient([
        _Response(content=[]),  # iter1: nada, nenhum tool
    ])
    res = _orch().process_turn(
        state={"current_stage": "intake"},
        user_message="oi",
        ctx=CTX,
        llm_client=client,
    )
    assert res.reply == "Certo! Como deseja seguir?"
    assert res.tool_calls == []
    assert res.iterations == 1
