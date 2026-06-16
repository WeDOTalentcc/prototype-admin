"""Refactor 2026-06-06 (decisao Paulo): memoria-load + entity-resolve içados
pra ANTES do dispatch das trilhas no SSE -> agente E supervisor herdam
active_vacancy/active_candidate (create_task copia o context). Se isso voltar
pra DENTRO de _run_agent, o supervisor regride na dor "achar vaga/candidato por
nome". Sensor estrutural (sem subir o handler inteiro).
"""
from __future__ import annotations


def test_memory_entity_hoisted_before_dispatch():
    s = open("app/api/v1/agent_chat_sse.py", encoding="utf-8").read()
    i_dispatch = s.find("_run_via_supervisor() if _bubble_via_supervisor")
    assert i_dispatch > 0, "dispatch das trilhas nao encontrado"
    for marker in ("get_context_for_llm", "resolve_named_entities", "set_active_vacancy("):
        i = s.find(marker)
        assert 0 < i < i_dispatch, (
            f"'{marker}' precisa estar ANTES do dispatch (shared agente+supervisor); "
            "se voltou pra dentro de _run_agent, o supervisor nao herda."
        )


def test_run_agent_does_not_shadow_hoisted_hist():
    s = open("app/api/v1/agent_chat_sse.py", encoding="utf-8").read()
    # corpo real do _run_agent = def -> primeiro statement 8-espacos depois dele.
    defi = s.index("async def _run_agent():")
    i_dispatch = s.find("agent_task = asyncio.create_task")
    # o load içado fica ENTRE _run_agent e o dispatch; _run_agent em si nao pode
    # reassinar _hist (senao shadowa o load e zera a memoria do agente).
    # Heuristica robusta: '_hist: list = []' aparece exatamente 1x (no bloco içado).
    assert s.count("_hist: list = []") == 1, (
        "esperava 1 init de _hist (no bloco içado). >1 sugere shadow em _run_agent."
    )
