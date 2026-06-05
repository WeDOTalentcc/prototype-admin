"""Integration sensor — Wizard turn pipeline E2E (the missing guard).

Harness "never again" (2026-06-05). Unit tests cobriam o loop do orquestrador
em isolamento (``WizardOrchestrator.process_turn``) e as tools puras, mas
NENHUM teste exercitava o pipeline de turno REAL ponta-a-ponta — o caminho que
o caller de produção (``WizardSessionService._process_via_orchestrator``)
percorre: carrega state → roda o loop → deriva o stage → constrói o
``ws_stage_payload`` (o sinal que abre o painel lateral) → persiste.

Essa lacuna deixou passar uma classe inteira de bugs invisíveis a unit test:
  - reply perdido (texto+tool no mesmo iter → fallback genérico "wizard burro");
  - ws_stage_payload vazio (painel não abre mesmo com a conversa avançando);
  - campos não acumulados entre turnos.

## Nível de injeção

Dirigimos ``WizardSessionService._process_via_orchestrator`` (a ENTRADA real
do orquestrador — exercita state-carry, derivação de stage E build do payload).
``process_message`` em si depende do checkpointer DB (``_get_prior_state``) e
do supervisor pré-graph; o valor do sensor está no segmento do turno que
constrói reply + payload, que vive em ``_process_via_orchestrator``. Seams de
I/O (LLM real, persist no checkpointer, fetch de company_context) são
substituídos por fakes determinísticos:
  - LLM: ``WizardOrchestrator._build_anthropic_client`` → cliente scriptado;
  - persist: ``_persist_orchestrator_state`` → no-op async;
  - company_context: pré-semeado no state (curto-circuita o fetch async de DB).

Conversa multi-turno com state carregado manualmente entre turnos (espelha o
que o checkpointer faria). Cobre os padrões REAIS observados em produção.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from app.domains.job_creation.orchestrator.wizard_orchestrator import (
    WizardOrchestrator,
    get_wizard_orchestrator,
)
from app.domains.job_creation.services.wizard_session_service import (
    WizardSessionService,
)


_GENERIC_FALLBACK = "Certo! Como deseja seguir?"
_COMPANY_ID = "comp-e2e-1"
_THREAD_ID = "thr-e2e-1"


# ── Fake LLM (mimetiza o SDK Anthropic: .content lista de blocks) ─────────


@dataclass
class _TextBlock:
    text: str
    type: str = "text"


@dataclass
class _ToolUseBlock:
    name: str
    input: dict = field(default_factory=dict)
    id: str = "tu_e2e"
    type: str = "tool_use"


@dataclass
class _Response:
    content: list
    stop_reason: str = "end_turn"


class _ScriptedMessages:
    """``.messages`` do cliente: cada turno consome uma sub-lista de respostas.

    O orquestrador chama ``create`` 1x por iteração do ReAct loop. Damos uma
    FILA de respostas; o teste injeta, por turno, o número de respostas que
    aquele turno consome (1 ou 2 iterações).
    """

    def __init__(self) -> None:
        self.queue: list[_Response] = []
        self.calls: list[dict] = []

    def load(self, responses: list[_Response]) -> None:
        self.queue = list(responses)

    def create(self, **kwargs: Any) -> _Response:
        self.calls.append(kwargs)
        if not self.queue:
            return _Response(content=[_TextBlock(text="(fim)")])
        return self.queue.pop(0)


class _ScriptedClient:
    def __init__(self, messages: _ScriptedMessages) -> None:
        self.messages = messages


@pytest.fixture
def scripted_pipeline(monkeypatch):
    """Monta o pipeline com LLM scriptado + seams de I/O neutralizados.

    Retorna ``(run_turn, messages)`` onde:
      - ``messages`` é o ``_ScriptedMessages`` (carregar respostas por turno);
      - ``run_turn(state, user_message)`` roda um turno e devolve
        ``(reply, ws_stage_payload, state_out)``.
    """
    messages = _ScriptedMessages()
    client = _ScriptedClient(messages)

    # Singleton de produção, mas com o builder de cliente trocado pelo fake.
    orch = get_wizard_orchestrator()
    monkeypatch.setattr(orch, "_build_anthropic_client", lambda *a, **k: client)

    persisted: dict[str, dict] = {}

    # Persist no checkpointer → captura em memória (teste hermético, sem DB).
    # Espelha o que o checkpointer faria: guarda o state mutado para encadear
    # turnos (o caller real recarregaria via _get_prior_state no turno seguinte).
    async def _capture_persist(cls, thread_id, values):  # noqa: ANN001
        persisted["state"] = dict(values)
        return True

    monkeypatch.setattr(
        WizardSessionService,
        "_persist_orchestrator_state",
        classmethod(_capture_persist),
    )

    async def run_turn(state: dict, user_message: str):
        # company_context pré-semeado → curto-circuita o fetch async de DB.
        seeded = dict(state)
        seeded.setdefault("company_context", "")
        reply, payload, _tokens = await WizardSessionService._process_via_orchestrator(
            thread_id=_THREAD_ID,
            user_message=user_message,
            user_id="user-e2e",
            company_id=_COMPANY_ID,
            prior_state=seeded,
            context=None,
        )
        return reply, payload, persisted.get("state", {})

    return run_turn, messages


def _stage_of(payload: dict) -> str | None:
    if not isinstance(payload, dict):
        return None
    return payload.get("stage")


# ── E2E multi-turno ───────────────────────────────────────────────────────


@pytest.mark.medium
async def test_turn_pipeline_multi_turn_conversation(scripted_pipeline):
    """Conversa multi-turno completa pelo pipeline real, LLM mockado.

    Cada turno assere: reply não-vazio e ≠ fallback (exceto onde intencional),
    ws_stage_payload populado com o stage esperado (sinal do painel), e o
    state acumulando (título, senioridade, modelo após seus turnos).
    """
    run_turn, messages = scripted_pipeline
    state: dict = {"current_stage": "intake"}

    # ── Turn A — greeting: text-only, sem tool → pergunta o título ──────
    messages.load([
        _Response(content=[_TextBlock(text="Olá! Sobre qual cargo é a vaga?")]),
    ])
    reply, payload, state = await run_turn(state, "oi, quero criar uma vaga")
    assert reply, "Turn A: reply vazio"
    assert reply != _GENERIC_FALLBACK, "Turn A: caiu no fallback genérico"
    assert "cargo" in reply.lower() or "título" in reply.lower()
    assert _stage_of(payload) == "intake", "Turn A: painel deve sinalizar intake"
    assert isinstance(payload.get("data"), dict) and payload["data"].get("message")

    # ── Turn B — título nu: text + tool_use(set_job_fields) no MESMO iter,
    #    depois iter2 vazio. REGRESSÃO "wizard burro" em nível de pipeline:
    #    o reply DEVE conter o ack do título capturado, não o fallback. ──
    ack_b = "Perfeito! Registrei o título Diretor de Compliance. Qual a senioridade?"
    messages.load([
        _Response(content=[
            _TextBlock(text=ack_b),
            _ToolUseBlock(
                name="set_job_fields",
                input={"title": "Diretor de Compliance"},
                id="b1",
            ),
        ]),
        _Response(content=[]),  # iter2 vazio
    ])
    reply, payload, state = await run_turn(state, "diretor de compliance")
    assert reply == ack_b, "Turn B (wizard-burro): reply perdeu o texto do iter1"
    assert reply != _GENERIC_FALLBACK
    assert state.get("parsed_title") == "Diretor de Compliance", \
        "Turn B: título não acumulou no state"
    assert _stage_of(payload) == "intake"
    # o painel deve refletir o título capturado (ficha viva)
    assert payload["data"].get("message") == ack_b

    # ── Turn C — tool-only no iter1, texto no iter2 → reply == iter2 ────
    reply_c = "Anotei: Sênior. Modelo de trabalho?"
    messages.load([
        _Response(content=[
            _ToolUseBlock(
                name="set_job_fields", input={"seniority": "Sênior"}, id="c1"
            ),
        ]),
        _Response(content=[_TextBlock(text=reply_c)]),
    ])
    reply, payload, state = await run_turn(state, "sênior")
    assert reply == reply_c, "Turn C: reply deve ser o texto do iter2"
    assert reply != _GENERIC_FALLBACK
    assert state.get("parsed_seniority") == "Sênior"
    assert state.get("parsed_title") == "Diretor de Compliance", \
        "Turn C: título de turnos anteriores deve persistir"
    assert _stage_of(payload) == "intake"

    # ── Turn D — multi-field "senior, hibrido": set_job_fields com 2 campos
    #    em um único tool_use → ambos capturados + reply não-fallback. ──
    reply_d = "Registrei: híbrido. Vamos às competências?"
    messages.load([
        _Response(content=[
            _ToolUseBlock(
                name="set_job_fields",
                input={"seniority": "Sênior", "model": "hibrido"},
                id="d1",
            ),
        ]),
        _Response(content=[_TextBlock(text=reply_d)]),
    ])
    reply, payload, state = await run_turn(state, "senior, hibrido")
    assert reply == reply_d
    assert reply != _GENERIC_FALLBACK
    assert state.get("parsed_seniority") == "Sênior"
    assert state.get("parsed_model") == "hybrid", \
        "Turn D: modelo (normalizado) não acumulou"
    assert _stage_of(payload) == "intake"
    assert isinstance(payload.get("data"), dict) and payload["data"].get("message")


@pytest.mark.medium
async def test_turn_pipeline_advances_to_competency_stage(scripted_pipeline):
    """Drive a conversa até confirmar competências → stage avança p/ competency.

    Surfacing: confirma que, quando o orquestrador chama confirm_competencies,
    o pipeline deriva stage="competency" E o ws_stage_payload carrega o
    competency_tree (o sinal que abre o CompetencyPanel). Se isso quebrar, o
    painel de competências nunca aparece (bug B3 histórico).
    """
    run_turn, messages = scripted_pipeline
    state: dict = {
        "current_stage": "intake",
        "parsed_title": "Engenheiro de Dados",
        "parsed_seniority": "Pleno",
    }

    reply_text = "Confirmei as competências. Quer revisar?"
    messages.load([
        _Response(content=[
            _ToolUseBlock(
                name="confirm_competencies",
                input={
                    "technical": ["Python", "SQL", "Airflow"],
                    "behavioral": ["Comunicação"],
                },
                id="cc1",
            ),
        ]),
        _Response(content=[_TextBlock(text=reply_text)]),
    ])
    reply, payload, state = await run_turn(state, "as competências são python, sql, airflow")

    assert reply == reply_text
    assert reply != _GENERIC_FALLBACK
    assert state.get("confirmed_technical_competencies"), \
        "competências técnicas não acumularam"
    assert _stage_of(payload) == "competency", \
        "stage deveria avançar p/ competency (sinal do CompetencyPanel)"
    # o painel precisa do competency_tree para renderizar add/remove
    assert payload.get("data", {}).get("competency_tree"), \
        "ws_stage_payload sem competency_tree — painel de competências não abre"
