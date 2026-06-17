"""
Contract sensor — ActionExecutor entity_id injection do contexto.

WHY THIS SENSOR EXISTS
======================
Recovery Tri-2 Body-Changes #1 (2026-05-23) descobriu que ``executor.py`` perdeu
bloco crítico no merge incident 02361f41c:

  ``ctx_entity_id = context.get("entity_id") or context.get("context_entity_id")``
  + injeção em ``entities["candidate_id"]`` / ``entities["job_id"]`` baseado
  em ``entity_type``.

Sem isso, quando user fala "esse candidato" / "essa vaga" em chat com
contexto persistente, handlers NÃO recebem ``candidate_id`` / ``job_id``
em params. Cai em fallback silent ou clarification loop.

Diff: -114 LOC perdidas pelo incident, body-changes-only (não removeu
funções top-level, mas removeu logic crítico dentro de ``execute_action``).

Pattern: BLOCKING. Context-aware actions são canonical pra chat.
"""
from __future__ import annotations

import inspect

from app.orchestrator.action_executor import executor as executor_mod


def test_executor_has_uuid_and_job_id_regex():
    """
    Regex constants ``_UUID_RE`` + ``_JOB_ID_RE`` devem existir no módulo —
    elas validam o formato do ``entity_id`` antes de injetar.
    """
    assert hasattr(executor_mod, "_UUID_RE"), (
        "_UUID_RE regex constant ausente. Sem ela, entity_id injection não "
        "valida formato UUID. Recovery Tri-2 Body-Changes #1 restaurou — "
        "ressuscitar."
    )
    assert hasattr(executor_mod, "_JOB_ID_RE"), (
        "_JOB_ID_RE regex constant ausente. Sem ela, job short-ID format "
        "(V0037, etc.) não valida. Recovery Tri-2 restaurou."
    )

    # Sanity: regexes devem ser compiláveis e matchar exemplos canonical
    assert executor_mod._UUID_RE.match("12345678-1234-1234-1234-123456789abc"), (
        "_UUID_RE não matcha exemplo UUID canonical"
    )
    assert executor_mod._JOB_ID_RE.match("V0037"), (
        "_JOB_ID_RE não matcha exemplo short-ID canonical"
    )


def test_execute_action_has_entity_id_injection_logic():
    """
    ``ActionExecutorService.try_execute`` deve conter logic de injeção
    de ``ctx_entity_id`` em ``entities``. Sem isso, conversação com contexto
    perde tracking do candidato/vaga ativo.
    """
    # Verificar src tanto de try_execute quanto _execute_action — bloco
    # entity_id injection pode estar em qualquer um dos dois.
    src = (
        inspect.getsource(executor_mod.ActionExecutorService.try_execute)  # type: ignore[attr-defined]
        + inspect.getsource(executor_mod.ActionExecutorService._execute_action)  # type: ignore[attr-defined]
    )

    # Indicadores canonical do bloco entity_id injection
    canonical_markers = [
        "ctx_entity_id",
        "context.get(\"entity_id\")",
        "context_entity_id",
        "entity_type",
    ]
    missing = [m for m in canonical_markers if m not in src]
    assert not missing, (
        f"execute_action NÃO tem entity_id injection logic. Markers missing: "
        f"{missing}\n"
        "Sem esse bloco, handlers não recebem candidate_id/job_id quando "
        "contexto da conversa indica entity ativa. Recovery Tri-2 Body-Changes #1 "
        "restaurou — ressuscitar."
    )

    # Validar específicos: ambos branches (job + candidate) devem estar lá
    assert "candidate_id" in src and "candidate" in src.lower(), (
        "Branch candidate de entity_id injection ausente"
    )
    assert "job_id" in src and "job" in src.lower(), (
        "Branch job de entity_id injection ausente"
    )
