"""Manus F1 — ``panel_pref`` one-shot no payload do ``wizard_stage``.

As tools ``open_panel``/``close_panel`` gravam ``state_updates={"panel_pref":
"expanded"|"docked"}``. Este contrato garante que o valor viaja UMA vez ao FE
dentro do dict ``data`` do payload do stage e depois sai do state — para não
re-forçar o modo nas etapas seguintes e quebrar a escolha manual do recrutador.

Mecanismo REAL (verificado em wizard_session_service._process_via_orchestrator):
``_persist_orchestrator_state`` roda ANTES do build do payload e usa
``update_state`` (merge no checkpoint — pop depois do persist não removeria a
key já persistida). Por isso o one-shot canônico é ``_consume_panel_pref``
(pop + validação) chamado ANTES do persist: a key nunca chega ao checkpoint.

Sensores de wiring (inspect.getsource) pinam a ordem consumo→persist e a
injeção em ``data["panel_pref"]`` — se o fio for removido, o teste quebra.
"""

import inspect

from app.domains.job_creation.services.wizard_session_service import (
    WizardSessionService,
    _consume_panel_pref,
)


def test_payload_inclui_panel_pref_quando_no_state():
    """State com panel_pref válido → valor consumido e injetado no data."""
    for pref in ("docked", "expanded"):
        state = {"panel_pref": pref, "parsed_title": "Dev"}
        assert _consume_panel_pref(state) == pref

    # Wiring sensor: o valor consumido é de fato injetado no dict `data`
    # do payload do wizard_stage (não basta o helper existir).
    src = inspect.getsource(WizardSessionService._process_via_orchestrator)
    assert "_consume_panel_pref(new_state)" in src, (
        "_process_via_orchestrator deve consumir panel_pref do new_state"
    )
    assert 'data["panel_pref"]' in src, (
        "payload `data` do wizard_stage deve receber panel_pref consumido"
    )


def test_payload_omite_panel_pref_quando_ausente():
    """State sem a key → nada a emitir; valor inválido → consumido e descartado."""
    state = {"parsed_title": "Dev"}
    assert _consume_panel_pref(state) is None
    assert "panel_pref" not in state

    # Valor fora do vocabulário ("expanded"|"docked") não vaza pro FE —
    # mas é consumido mesmo assim (não fica lixo no state).
    state = {"panel_pref": "fullscreen"}
    assert _consume_panel_pref(state) is None
    assert "panel_pref" not in state


def test_panel_pref_e_one_shot():
    """Após consumir, o state não carrega mais a key — 2º build não re-emite."""
    state = {"panel_pref": "docked", "other": 1}
    assert _consume_panel_pref(state) == "docked"
    assert "panel_pref" not in state
    assert state["other"] == 1  # só a key alvo é removida
    # Montar de novo (turno seguinte) → não re-emite.
    assert _consume_panel_pref(state) is None

    # Ordering sensor: o consumo PRECISA acontecer ANTES do persist —
    # _persist_orchestrator_state usa update_state (merge no checkpoint);
    # pop depois do persist deixaria a key no checkpoint e re-emitiria
    # em todos os turnos seguintes (quebra a escolha manual do recrutador).
    src = inspect.getsource(WizardSessionService._process_via_orchestrator)
    assert "_consume_panel_pref" in src and "_persist_orchestrator_state" in src
    assert src.index("_consume_panel_pref") < src.index(
        "_persist_orchestrator_state(thread_id, new_state)"
    ), "panel_pref deve ser consumido (pop) ANTES do persist do state"
