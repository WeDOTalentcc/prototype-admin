"""
Migration sensor — `candidate_actions.py` orchestrator handlers MIGRATED para
``cv_screening/tools/candidate_tools.py``. Garante que canonical tools existem
e que ninguém RE-ADICIONA handlers duplicados no orchestrator.

WHY THIS SENSOR EXISTS
======================
Audit Recovery #6 (2026-05-23) descobriu que ``_reject_candidate`` e
``_bulk_move_by_stage`` em ``app/orchestrator/action_handlers/candidate_actions.py``
foram MIGRATED legítimos pós-incident — não regressed:

- ``_reject_candidate`` → ``cv_screening/tools/candidate_tools.py:reject_candidate``
  com FairnessGuard + send_feedback (LGPD) + feedback_template canonical.
- ``_bulk_move_by_stage`` → ``cv_screening/tools/candidate_tools.py:bulk_update_candidates_stage``.

A IA agent invoca via tool registry (canonical), não via orchestrator dispatcher.

Esse sensor é DEFENSIVO em 2 direções:
1. Garante que canonical tools NÃO sumam (sem cv_screening/tools, feature
   silenciosamente quebra).
2. Garante que ninguém duplica handlers no orchestrator (regressão arquitetural
   — fragmentaria FairnessGuard logic em 2 paths).

Pattern: BLOCKING.
"""
from __future__ import annotations

import inspect
import re

from app.domains.cv_screening.tools import candidate_tools
from app.orchestrator.action_handlers import candidate_actions


# Actions que orchestrator candidate_actions.py NÃO DEVE despachar (canonical
# vive em cv_screening/tools/). Atualizar PR-explícito se algum dia decidir
# RE-CONSOLIDAR handlers (escolha arquitetural).
_MIGRATED_AWAY_FROM_ORCHESTRATOR = {
    "reject_candidate",
    "bulk_move_by_stage",
    "bulk_update_candidates_stage",  # synonym
}


def _extract_dispatched_action_ids() -> set[str]:
    src = inspect.getsource(candidate_actions.execute_candidate_action)
    return set(re.findall(r'action_id\s*==\s*"([^"]+)"', src))


def test_canonical_tools_exist_in_cv_screening():
    """
    ``reject_candidate`` e ``bulk_update_candidates_stage`` devem permanecer
    em ``cv_screening/tools/candidate_tools``. Se sumirem, feature quebra
    silenciosamente (LLM agent invoca via tool registry e cai em null).
    """
    assert hasattr(candidate_tools, "reject_candidate"), (
        "MIGRATED tool `reject_candidate` ausente em "
        "app/domains/cv_screening/tools/candidate_tools.py. "
        "Audit Recovery #6 (2026-05-23) confirmou esse é o caller canonical "
        "(FairnessGuard wired + send_feedback LGPD + feedback_template). "
        "Restaurar ou substituir antes de remover."
    )
    assert callable(candidate_tools.reject_candidate), (
        "candidate_tools.reject_candidate não é callable."
    )

    # bulk_update_candidates_stage também deve existir (substituiu
    # _bulk_move_by_stage do orchestrator).
    assert hasattr(candidate_tools, "bulk_update_candidates_stage"), (
        "MIGRATED tool `bulk_update_candidates_stage` ausente em "
        "app/domains/cv_screening/tools/candidate_tools.py. "
        "Substituiu o legacy `_bulk_move_by_stage` do orchestrator."
    )


def test_orchestrator_does_not_dispatch_migrated_actions():
    """
    ``execute_candidate_action`` NÃO DEVE despachar ``reject_candidate`` nem
    ``bulk_move_by_stage`` — features migraram pra tools layer.

    Se alguém adicionar branches dessas action_ids no orchestrator dispatcher,
    cria DUPLICAÇÃO arquitetural (2 paths pra mesma feature, fragmenta
    FairnessGuard logic).
    """
    dispatched = _extract_dispatched_action_ids()
    overlap = dispatched & _MIGRATED_AWAY_FROM_ORCHESTRATOR
    assert not overlap, (
        f"Orchestrator candidate_actions.py duplica actions MIGRATED: {overlap}\n"
        "Audit Recovery #6 (2026-05-23) confirmou que essas actions vivem em "
        "cv_screening/tools/candidate_tools.py com canonical FairnessGuard + "
        "send_feedback + feedback_template. Re-adicionar no orchestrator cria "
        "fragmentação. Remova as branches e use o canonical."
    )


def test_reject_candidate_has_fairness_guard():
    """
    ``cv_screening/tools/candidate_tools.reject_candidate`` deve invocar
    ``FairnessGuard`` antes de aplicar rejeição (compliance ANPD / EU AI Act —
    anti-bias check em decision de IA).
    """
    src = inspect.getsource(candidate_tools.reject_candidate)
    assert "FairnessGuard" in src, (
        "reject_candidate canonical NÃO importa FairnessGuard. "
        "Compliance EU AI Act / LGPD exige fairness check em decisões de "
        "rejection. Restaurar invocação."
    )


def test_reject_candidate_supports_send_feedback_flag():
    """
    ``reject_candidate`` deve aceitar parâmetro ``send_feedback`` (LGPD Art. 20
    transparência — direito de explicação de decisão automatizada).
    """
    sig = inspect.signature(candidate_tools.reject_candidate)
    assert "send_feedback" in sig.parameters, (
        "reject_candidate canonical SEM parâmetro send_feedback. "
        "LGPD Art. 20 exige envio de feedback ao candidato rejeitado."
    )
