"""
Early Warning Service — Sprint 2B.

Detecta candidatos em risco de ghostar ANTES de o dano acontecer,
usando thresholds calibrados por etapa (warning + critical) e
ponderação pelo LIA score do candidato.

Substitui o threshold fixo de 10 dias do check_engagement_gaps por
lógica inteligente por etapa com EWS score de 0.0 a 1.0.

Sem migration — usa dados existentes:
  vacancy_candidates (stage, stage_entered_at, lia_score)
  communication_logs (sent_at — último contato)
  job_vacancies (created_by, recruiter_email, company_id)
  candidates (name)
  users (id, email — para recruiter_email → recruiter_id)
"""

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "early_warning_service is deprecated and will be removed once Rails adapter routes are complete. "
    "Migrate callers to rails_adapter equivalents. "
    "See UC-P1-22 in the remediation plan (CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md).",
    DeprecationWarning,
    stacklevel=2,
)

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thresholds por etapa — (warning_days, critical_days)
# ---------------------------------------------------------------------------
_EWS_THRESHOLDS: dict[str, tuple[int, int]] = {
    "offer": (2, 4),
    "proposta": (2, 4),
    "interview_hr": (3, 5),
    "entrevista_rh": (3, 5),
    "interview_technical": (3, 5),
    "entrevista_tecnica": (3, 5),
    "interview_manager": (3, 5),
    "interview_final": (3, 5),
    "screening": (5, 8),
    "triagem": (5, 8),
    "applied": (7, 12),
    "novo": (7, 12),
    "initial": (7, 12),
}

_DEFAULT_THRESHOLDS: tuple[int, int] = (5, 10)


def _thresholds_for_stage(stage: str) -> tuple[int, int]:
    return _EWS_THRESHOLDS.get((stage or "").lower(), _DEFAULT_THRESHOLDS)


def compute_ews_score(
    days_since_contact: float,
    stage: str,
    lia_score: float | None = None,
) -> float:
    """
    Calcula o EWS score de 0.0 a 1.0.

    Fórmula:
      base_score = days_since_contact / critical_threshold  (cap 1.0)
      lia_weight = 1.0 + (lia_score or 0.5) * 0.5
        → candidato com score 1.0 tem peso 1.5 (50% mais urgente)
        → candidato sem score usa 0.5 (peso neutro 1.25)
      ews_score = min(1.0, base_score * lia_weight)
    """
    _, critical = _thresholds_for_stage(stage)
    base_score = min(1.0, days_since_contact / critical) if critical > 0 else 1.0
    weight = 1.0 + (lia_score if lia_score is not None else 0.5) * 0.5
    return round(min(1.0, base_score * weight), 3)


def risk_level_for_score(ews_score: float) -> str:
    if ews_score >= 1.0:
        return "critical"
    if ews_score >= 0.6:
        return "high"
    if ews_score >= 0.3:
        return "medium"
    return "low"


class EarlyWarningService:
    """
    Serviço de alerta precoce de desengajamento de candidatos.

    Candidato "em risco" = sem contato por tempo >= warning_threshold da etapa.
    EWS score pondera urgência considerando LIA score e proximidade do critical threshold.
    """

    async def get_at_risk_candidates(
        self,
        company_id: str,
        min_risk_level: str = "medium",
        db: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retorna candidatos ativos em risco de desengajamento, ordenados por ews_score DESC.

        min_risk_level filtra o retorno:
          "medium"   → medium + high + critical
          "high"     → high + critical
          "critical" → apenas critical
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            result = await db.execute(
                text("""
                    SELECT
                        vc.id::text                AS vacancy_candidate_id,
                        vc.candidate_id::text      AS candidate_id,
                        c.name                     AS candidate_name,
                        vc.vacancy_id::text        AS vacancy_id,
                        jv.title                   AS vacancy_title,
                        vc.stage,
                        vc.lia_score,
                        COALESCE(u.id::text, jv.created_by) AS recruiter_id,
                        MAX(cl.sent_at)            AS last_contact_at,
                        EXTRACT(EPOCH FROM (
                            NOW() - COALESCE(MAX(cl.sent_at), vc.stage_entered_at, vc.updated_at)
                        )) / 86400.0               AS days_since_contact
                    FROM vacancy_candidates vc
                    JOIN candidates c
                        ON vc.candidate_id = c.id
                    JOIN job_vacancies jv
                        ON vc.vacancy_id = jv.id
                        AND jv.company_id::text = :company_id
                        AND jv.status IN ('open', 'Ativa', 'Publicada')
                    LEFT JOIN communication_logs cl
                        ON cl.candidate_id = vc.candidate_id::text
                        AND cl.company_id = :company_id
                        AND cl.status IN ('sent', 'delivered', 'read')
                    LEFT JOIN users u
                        ON u.email = jv.recruiter_email
                        AND u.company_id::text = :company_id
                    WHERE vc.status = 'active'
                    GROUP BY
                        vc.id, vc.candidate_id, c.name,
                        vc.vacancy_id, jv.title,
                        vc.stage, vc.lia_score,
                        vc.stage_entered_at, vc.updated_at,
                        COALESCE(u.id::text, jv.created_by)
                """),
                {"company_id": company_id},
            )
            rows = result.fetchall()
        except Exception as e:
            logger.warning(f"get_at_risk_candidates query failed: {e}")
            return []
        finally:
            if should_close:
                await db.close()

        # Score mínimo para filtrar
        min_score_map = {"low": 0.0, "medium": 0.3, "high": 0.6, "critical": 1.0}
        min_score = min_score_map.get(min_risk_level, 0.3)

        at_risk = []
        for row in rows:
            days = float(row.days_since_contact or 0)
            warning_threshold, critical_threshold = _thresholds_for_stage(row.stage)

            # Só entra se passou do warning threshold
            if days < warning_threshold:
                continue

            lia_score = float(row.lia_score) if row.lia_score is not None else None
            score = compute_ews_score(days, row.stage, lia_score)

            if score < min_score:
                continue

            level = risk_level_for_score(score)
            at_risk.append(
                {
                    "vacancy_candidate_id": row.vacancy_candidate_id,
                    "candidate_id": row.candidate_id,
                    "candidate_name": row.candidate_name,
                    "vacancy_id": row.vacancy_id,
                    "vacancy_title": row.vacancy_title,
                    "stage": row.stage,
                    "lia_score": lia_score,
                    "recruiter_id": row.recruiter_id,
                    "last_contact_at": row.last_contact_at.isoformat() if row.last_contact_at else None,
                    "days_since_contact": round(days, 1),
                    "warning_threshold": warning_threshold,
                    "critical_threshold": critical_threshold,
                    "ews_score": score,
                    "risk_level": level,
                }
            )

        at_risk.sort(key=lambda x: x["ews_score"], reverse=True)
        return at_risk

    async def get_summary_by_risk_level(
        self,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Resumo por nível de risco para o endpoint REST.
        Retorna contagens e top candidatos por nível.
        """
        candidates = await self.get_at_risk_candidates(
            company_id, min_risk_level="medium", db=db
        )

        summary: dict[str, Any] = {
            "total": len(candidates),
            "by_risk_level": {"critical": 0, "high": 0, "medium": 0},
            "top_critical": [],
            "top_high": [],
        }

        for c in candidates:
            level = c["risk_level"]
            if level in summary["by_risk_level"]:
                summary["by_risk_level"][level] += 1

        summary["top_critical"] = [c for c in candidates if c["risk_level"] == "critical"][:5]
        summary["top_high"] = [c for c in candidates if c["risk_level"] == "high"][:5]

        return summary


early_warning_service = EarlyWarningService()
