"""TDD — WizardOrchestrator empty-reply observability (anti-silent-degradation).

Harness sensor (2026-06-05). O caso em que o LLM produz ZERO texto em TODAS as
iterações do turno faz o reply cair no fallback genérico
("Certo! Como deseja seguir?"). Antes esse caminho era INVISÍVEL — o turno
respondia 200 OK com texto plausível enquanto o painel não abria e o recrutador
via uma resposta sem sentido. Estes testes pinam que a anomalia agora:

  1. emite um WARNING (caplog) — observável em logs de produção;
  2. NÃO emite WARNING quando o reply é genuíno (sem ruído / falso alarme);
  3. preserva o fallback string (UX intacta).

Cliente LLM é um fake scriptado (sem rede, sem API key).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pytest

from app.domains.job_creation.orchestrator.wizard_orchestrator import (
    WizardOrchestrator,
)
from app.domains.job_creation.orchestrator.wizard_tools import ToolContext


CTX = ToolContext(company_id="comp-123", user_id="user-1", workspace_id=1)
_GENERIC_FALLBACK = "Certo! Como deseja seguir?"
_WARN_MARKER = "empty-reply fallback"


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


# ── Testes ───────────────────────────────────────────────────────────────


@pytest.mark.medium
def test_warning_fires_on_genuinely_empty_reply(caplog):
    """Iteração única vazia (sem texto, sem tool) → WARNING + fallback string."""
    client = FakeLLMClient([_Response(content=[])])
    with caplog.at_level(logging.WARNING, logger="app.domains.job_creation.orchestrator.wizard_orchestrator"):
        res = _orch().process_turn(
            state={"current_stage": "intake", "thread_id": "thr-xyz"},
            user_message="oi",
            ctx=CTX,
            llm_client=client,
        )
    assert res.reply == _GENERIC_FALLBACK
    warnings = [r for r in caplog.records if _WARN_MARKER in r.getMessage()]
    assert warnings, "esperado WARNING de empty-reply fallback (anomalia observável)"
    # o thread aparece no log para correlação
    assert "thr-xyz" in warnings[0].getMessage()


@pytest.mark.medium
def test_warning_fires_when_tools_called_but_no_text(caplog):
    """Tool executou mas o LLM nunca emitiu texto → ainda é anomalia observável.

    iter1: tool_use sem texto; iter2: conteúdo vazio. accumulated_text fica
    vazio → fallback genérico → WARNING (com tools_called listado).
    """
    client = FakeLLMClient([
        _Response(content=[_ToolUseBlock(name="set_job_fields", input={"title": "PM"})]),
        _Response(content=[]),
    ])
    with caplog.at_level(logging.WARNING, logger="app.domains.job_creation.orchestrator.wizard_orchestrator"):
        res = _orch().process_turn(
            state={"current_stage": "intake"},
            user_message="vaga de PM",
            ctx=CTX,
            llm_client=client,
        )
    assert res.reply == _GENERIC_FALLBACK
    assert "set_job_fields" in res.tool_calls
    warnings = [r for r in caplog.records if _WARN_MARKER in r.getMessage()]
    assert warnings, "tool sem texto e iter vazio também é empty-reply fallback"
    assert "set_job_fields" in warnings[0].getMessage()


@pytest.mark.medium
def test_no_warning_when_reply_is_genuine(caplog):
    """Reply textual real → NENHUM warning de empty-reply (sem falso alarme)."""
    client = FakeLLMClient([
        _Response(content=[_TextBlock(text="Olá! Qual o título da vaga?")]),
    ])
    with caplog.at_level(logging.WARNING, logger="app.domains.job_creation.orchestrator.wizard_orchestrator"):
        res = _orch().process_turn(
            state={"current_stage": "intake"},
            user_message="oi",
            ctx=CTX,
            llm_client=client,
        )
    assert res.reply != _GENERIC_FALLBACK
    warnings = [r for r in caplog.records if _WARN_MARKER in r.getMessage()]
    assert warnings == [], "reply genuíno não deve disparar warning de empty-reply"


@pytest.mark.medium
def test_no_warning_when_text_plus_tool_accumulated(caplog):
    """Texto+tool no iter1, iter2 vazio → reply = texto acumulado, SEM warning.

    Pina que o sensor não cria falso positivo no caminho da regressão "wizard
    burro" já corrigida (commit 820a52573).
    """
    title_text = "Perfeito! Registrei o título Diretor de Compliance"
    client = FakeLLMClient([
        _Response(content=[
            _TextBlock(text=title_text),
            _ToolUseBlock(name="set_job_fields", input={"title": "Diretor de Compliance"}),
        ]),
        _Response(content=[]),
    ])
    with caplog.at_level(logging.WARNING, logger="app.domains.job_creation.orchestrator.wizard_orchestrator"):
        res = _orch().process_turn(
            state={"current_stage": "intake"},
            user_message="o título é Diretor de Compliance",
            ctx=CTX,
            llm_client=client,
        )
    assert res.reply == title_text
    warnings = [r for r in caplog.records if _WARN_MARKER in r.getMessage()]
    assert warnings == [], "texto acumulado é reply válido — sem warning"
