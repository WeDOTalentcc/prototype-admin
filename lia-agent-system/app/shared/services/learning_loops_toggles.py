"""
Canonical helper for reading ``CompanyHiringPolicy.automation_rules.learning_loops``
toggles from anywhere in ``lia-agent-system``.

Registrado 2026-05-21 (audit follow-up). Substitui duas implementações
paralelas que estavam divergindo silenciosamente:

- ``app/domains/job_creation/services/bigfive_service.BigFiveService._get_toggles``
- ``app/domains/communication/services/transition_dispatch_service.TransitionDispatchService._load_learning_loops_toggles``

Ambas tinham a mesma intenção (carregar o dict ``learning_loops`` com
fallback para defaults canonical), mas implementações ligeiramente
diferentes — uma capturava ``SQLAlchemyError``, a outra ``Exception``;
uma usava ``logger.debug`` em fallback, a outra ``logger.warning``.
Drift de classe-de-falha entre dois callers para a MESMA pergunta é
exatamente o tipo de coisa que harness engineering quer eliminar.

## Pattern canonical

Qualquer service que precisa decidir se um learning loop está ativo
deve usar este helper:

    from app.shared.services.learning_loops_toggles import load_learning_loops_toggles

    toggles = await load_learning_loops_toggles(company_id, db)
    if not toggles.get("enabled", True):
        return  # master switch off
    if not toggles.get("wsi_question_effectiveness", False):
        return  # specific loop off

## Por que não ``LiaFieldConfigService``

``LiaFieldConfigService`` cuida do conjunto de 34 toggles PER-FIELD
(``mission``, ``vision``, ...), que vivem em ``CompanyCultureProfile``.
``learning_loops`` é um conjunto separado de toggles que vive em
``CompanyHiringPolicy.automation_rules.learning_loops`` e governam
write paths de aprendizado (BigFive dept, JD similar, WSI effectiveness).
São namespaces diferentes; misturar os dois confunde quem lê.

## Multi-tenancy

O ``company_id`` é argumento — o caller é responsável por garantir
que ele vem do JWT/contexto autenticado, NUNCA de payload externo
(ADR-LGPD-001 + REGRA ZERO multi-tenancy).
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def load_learning_loops_toggles(
    company_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """Return the ``learning_loops`` dict from the company's hiring policy.

    Args:
        company_id: UUID string of the calling tenant. Caller MUST already
            have validated this against the JWT/auth context.
        db: Async DB session bound to the caller's tenant.

    Returns:
        Dict shaped like the canonical defaults in
        ``AUTOMATION_RULES_DEFAULTS["learning_loops"]`` from
        ``lia_models.company_hiring_policy``. At minimum contains:

        - ``enabled`` (bool, default True) — master switch
        - ``bigfive_company_culture`` (bool, default True)
        - ``bigfive_department_history`` (bool, default False)
        - ``jd_similar_suggestion`` (bool, default True)
        - ``wsi_question_effectiveness`` (bool, default False) — Phase 3 opt-in

        On DB error or missing policy row, returns the canonical defaults
        (fail-safe: when in doubt, use the schema-defined behavior).

    Never raises. Designed to be called from hot paths (e.g. every hire
    event) without exception handling at the call site.
    """
    from lia_models.company_hiring_policy import AUTOMATION_RULES_DEFAULTS
    defaults = AUTOMATION_RULES_DEFAULTS["learning_loops"]
    if not company_id:
        return defaults
    try:
        # Local import: HiringPolicyRepository pulls a small dep graph and
        # most callers do not need it for anything else. Avoids widening
        # the import surface of this shared module.
        from app.domains.hiring_policy.repositories.hiring_policy_repository import (
            HiringPolicyRepository,
        )
        repo = HiringPolicyRepository(db)
        policy = await repo.get_by_company(company_id)
        if policy and policy.automation_rules:
            return policy.automation_rules.get("learning_loops", defaults)
    except Exception as exc:
        # Fail-soft: any DB error returns defaults. Callers can rely on
        # the helper to never raise — the conservative defaults
        # (wsi_question_effectiveness=False, etc.) act as a safety net
        # when the database is unreachable.
        logger.warning(
            "[learning_loops_toggles] policy load failed for company=%s; "
            "returning canonical defaults. Reason: %s",
            company_id, str(exc)[:120],
        )
    return defaults


__all__ = ["load_learning_loops_toggles"]
