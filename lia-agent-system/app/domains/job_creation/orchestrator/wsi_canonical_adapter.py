"""Anticorruption Layer — orquestrador conversacional → kernel WSI canônico.

Consolidação WSI (Paulo 2026-05-31, .planning/wsi-consolidation-plan.md): o fluxo
conversacional para de usar o fork `job_creation` (WSIQuestionGenerator,
CompetencyBenchmarkService) e passa a consumir o kernel canônico
`cv_screening.WSIService` — a MESMA metodologia usada por Configurações da vaga +
toda a automação de triagem/entrevista. Single source of truth (DDD Shared Kernel).

Este adapter mapeia os schemas canônicos (CompetencySuggestion, WSIQuestion) →
shapes que as tools do orquestrador/painel já esperam, e normaliza o vocabulário
(senioridade) na fronteira. A orquestração do wizard (HITL, painéis, confirmação)
permanece no orquestrador — só a METODOLOGIA é repontada.

Sync por contrato: o serviço canônico é async; chamamos via run_coro_in_threadpool
(tools do orquestrador são sync, rodam em to_thread).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_COMPETENCY_TIMEOUT_S = 20.0


def suggest_competencies_canonical(
    *,
    title: str,
    seniority: Optional[str],
    jd_text: str = "",
    company_id: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Fase 1: sugere competências via cv_screening.WSIService (kernel canônico).

    Retorna o shape que o wizard espera:
        {"technical": [{"skill": ...}], "behavioral": [{"competencia": ..., "trait_big_five": ...}]}
    ou None em falha (caller trata fail-loud).
    """
    from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool
    from app.domains.job_creation.helpers.vacancy_vocab import to_cv_screening_seniority

    cv_seniority = to_cv_screening_seniority(seniority)
    # O kernel canônico analisa um texto de JD; antes da JD existir, usamos
    # título + (raw) como contexto mínimo.
    job_description = (jd_text or "").strip() or (title or "").strip()
    if not job_description:
        return None

    async def _fetch():
        from app.domains.cv_screening.services.wsi_service.service import get_wsi_service
        svc = get_wsi_service()
        return await svc.analyze_jd_and_suggest_competencies(
            job_description=job_description,
            seniority=cv_seniority,  # type: ignore[arg-type]
        )

    try:
        suggestion = run_coro_in_threadpool(_fetch, timeout=_COMPETENCY_TIMEOUT_S)
    except Exception as exc:  # noqa: BLE001 — caller decide fail-loud
        logger.warning("[WSIAdapter] suggest_competencies canonical failed: %s", exc)
        return None
    if suggestion is None:
        return None

    technical = [
        {"skill": c.name}
        for c in (getattr(suggestion, "technical_competencies", None) or [])
        if getattr(c, "name", None)
    ]
    # comportamentais + culturais → bloco comportamental do wizard (com trait Big Five).
    behavioral = []
    for c in list(getattr(suggestion, "behavioral_competencies", None) or []) + list(
        getattr(suggestion, "cultural_competencies", None) or []
    ):
        name = getattr(c, "name", None)
        if name:
            behavioral.append({
                "competencia": name,
                "trait_big_five": getattr(c, "big_five_mapping", None) or "conscientiousness",
            })
    if not technical and not behavioral:
        return None
    return {"technical": technical, "behavioral": behavioral}
