"""
WT-2022 P4.1: Helpers de check granular consent expostos por purpose.

Decisao Paulo 2026-05-21: wire todos 6 granular purposes (eram ghost antes).
Este arquivo expoe check functions canonical pra cada purpose; consumers
em domains diferentes devem importar e usar antes de processar PII.

Status por purpose (2026-05-21):
    ✅ ai_screening — wired em wsi_interview_graph.py:306
    ✅ ai_scoring — wired em rubric_evaluation_service.py:1174
    ✅ data_retention — wired em lgpd_cleanup_service (P4.1 fix)
    ⚠ ai_video_analysis — helper aqui, consumer TODO em voice/video pipeline
    ⚠ ai_comparison — helper aqui, consumer TODO em candidate compare feature
    ⚠ analytics — helper aqui, consumer TODO em analytics queries
    ⚠ marketing (granular) — helper aqui, namespace separado em consent_gate.py
    ⚠ training_data (granular) — helper aqui, company-level wired em feedback_repository

Pattern de uso (qualquer caller):

    from app.domains.lgpd.services.granular_consent_consumers import (
        check_data_retention,
    )

    if not await check_data_retention(candidate_id, company_id, db):
        # candidato opt-out de data_retention — comportamento per purpose
        return ...
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def _check_purpose(
    candidate_id: str,
    company_id: str,
    db: "AsyncSession",
    purpose: str,
) -> bool:
    """Helper interno: retorna True se candidato deu consent para purpose."""
    try:
        from app.domains.lgpd.services.granular_consent_service import (
            GranularConsentService,
        )
        svc = GranularConsentService(db)
        return await svc.check_purpose(
            candidate_id=candidate_id,
            company_id=company_id,
            purpose=purpose,
        )
    except Exception as exc:
        logger.warning(
            "Granular consent check failed for %s/%s: %s — defaulting to FALSE (fail-closed)",
            purpose, candidate_id, exc,
        )
        return False


async def check_ai_video_analysis(
    candidate_id: str, company_id: str, db: "AsyncSession"
) -> bool:
    """
    WT-2022 P4.1 purpose ai_video_analysis: bloqueia analise de video de entrevista
    quando candidato revogou consent.

    TODO consumer: wire em voice_screening_orchestrator.py:visual_pipeline ou
    interview video processing path. Hoje nao ha chamada real ainda.
    """
    return await _check_purpose(candidate_id, company_id, db, "ai_video_analysis")


async def check_ai_comparison(
    candidate_id: str, company_id: str, db: "AsyncSession"
) -> bool:
    """
    WT-2022 P4.1 purpose ai_comparison: bloqueia comparacao de candidato em
    compare-candidates feature.

    TODO consumer: wire em app/domains/candidate/services/candidate_compare_service.py
    antes de incluir candidato em set de comparacao IA.
    """
    return await _check_purpose(candidate_id, company_id, db, "ai_comparison")


async def check_data_retention(
    candidate_id: str, company_id: str, db: "AsyncSession"
) -> bool:
    """
    WT-2022 P4.1 purpose data_retention: candidato pode revogar consent de
    retencao prolongada. Se revogado, lgpd_cleanup_service deve ACELERAR
    deletion (nao esperar TTL canonical 90/180/365d).

    Wired em lgpd_cleanup_service.schedule_deletion_for_candidate (P4.1 fix).
    Comportamento: se candidato opt-out de data_retention, schedule_deletion
    usa retention_days=0 (deletar IMEDIATAMENTE) em vez do default 90d.
    """
    return await _check_purpose(candidate_id, company_id, db, "data_retention")


async def check_analytics(
    candidate_id: str, company_id: str, db: "AsyncSession"
) -> bool:
    """
    WT-2022 P4.1 purpose analytics: bloqueia inclusao do candidato em
    agregados analytics quando consent revogado.

    TODO consumer: wire em app/domains/analytics/services/weekly_digest_service.py
    antes de incluir candidate em metricas + em outras analytics queries que
    iteram candidatos.
    """
    return await _check_purpose(candidate_id, company_id, db, "analytics")


async def check_marketing_granular(
    candidate_id: str, company_id: str, db: "AsyncSession"
) -> bool:
    """
    WT-2022 P4.1 purpose marketing (granular per-candidate): bloqueia
    mensagens marketing outbound quando revogado.

    Namespace SEPARADO de consent_gate.py (EMAIL_MARKETING/WHATSAPP/SMS).
    TODO consumer: wire em communication_dispatcher.send pra checar granular
    ANTES do namespace antigo (granular OVERRIDE namespace cl candidato).
    """
    return await _check_purpose(candidate_id, company_id, db, "marketing")


async def check_training_data_granular(
    candidate_id: str, company_id: str, db: "AsyncSession"
) -> bool:
    """
    WT-2022 P4.1 purpose training_data (granular per-candidate): bloqueia
    incluir dados do candidato em fine-tune export.

    Company-level ja wired em feedback_repository.py:99-114 (CompanyTrainingConsent).
    TODO consumer: wire per-candidate em training_data_service.export_* pra
    aplicar AND (company-level=true AND per-candidate=true).
    """
    return await _check_purpose(candidate_id, company_id, db, "training_data")
