"""
Journey Intelligence Service — Sprint 2C.

Analisa o funil real de cada vaga: taxa de conversão por etapa, drop-off,
health score (0–100) e detecção de padrões preditivos de risco.

Sem migration — usa dados existentes:
  vacancy_candidates (stage, stage_entered_at, status)
  job_vacancies (status, created_at, deadline, created_by, recruiter_email)
  communication_logs (sent_at — último contato)
  users (id, email — para recruiter linkage)
"""

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "journey_intelligence_service is deprecated and will be removed once Rails adapter routes are complete. "
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
# Stage ordering (para cálculo de conversão sequencial)
# ---------------------------------------------------------------------------
_STAGE_ORDER: list[str] = [
    "applied", "novo", "initial",
    "screening", "triagem",
    "interview_hr", "entrevista_rh",
    "interview_technical", "entrevista_tecnica",
    "interview_manager",
    "interview_final",
    "offer", "proposta",
]


def _normalize_stage(stage: str) -> str:
    return (stage or "").lower().strip()


def _stage_rank(stage: str) -> int:
    norm = _normalize_stage(stage)
    for i, s in enumerate(_STAGE_ORDER):
        if norm == s:
            return i
    return len(_STAGE_ORDER)


# ---------------------------------------------------------------------------
# Health Score (0–100)
# ---------------------------------------------------------------------------
def compute_health_score(
    total_active: int,
    conversion_rate_overall: float,
    avg_drop_off_rate: float,
    candidates_in_advanced_stages: int,
    has_critical_ews: bool,
    days_since_last_movement: float,
) -> int:
    """
    Compõe o health score de uma vaga (0 = crítico, 100 = saudável).

    Componentes:
      - Pipeline volume    (20 pts): tem candidatos ativos?
      - Conversão         (25 pts): candidatos avançando entre etapas?
      - Candidatos avançados (25 pts): há candidatos em etapas finais?
      - Drop-off          (15 pts): taxa de saída está normal?
      - EWS / engajamento (15 pts): há candidatos em risco de ghosting?
    """
    score = 0

    # 1. Volume (20)
    if total_active >= 5:
        score += 20
    elif total_active >= 2:
        score += 12
    elif total_active == 1:
        score += 6

    # 2. Conversão geral (25)
    if conversion_rate_overall >= 0.20:
        score += 25
    elif conversion_rate_overall >= 0.10:
        score += 15
    elif conversion_rate_overall > 0:
        score += 8

    # 3. Candidatos em etapas avançadas (25)
    if candidates_in_advanced_stages >= 2:
        score += 25
    elif candidates_in_advanced_stages == 1:
        score += 15

    # 4. Drop-off (15) — penaliza alta evasão
    if avg_drop_off_rate <= 0.30:
        score += 15
    elif avg_drop_off_rate <= 0.50:
        score += 8
    elif avg_drop_off_rate <= 0.70:
        score += 3

    # 5. EWS / engajamento (15)
    if not has_critical_ews:
        if days_since_last_movement <= 3:
            score += 15
        elif days_since_last_movement <= 7:
            score += 10
        else:
            score += 5

    return min(100, max(0, score))


def health_label(score: int) -> str:
    if score >= 70:
        return "healthy"
    if score >= 45:
        return "warning"
    return "critical"


# ---------------------------------------------------------------------------
# Predictive Pattern Detection
# ---------------------------------------------------------------------------
def detect_risk_patterns(
    funnel: list[dict[str, Any]],
    total_active: int,
    candidates_in_advanced: int,
    drop_off_by_stage: dict[str, float],
    health_score: int,
) -> list[dict[str, str]]:
    """
    Detecta padrões preditivos de risco no funil.
    Retorna lista de padrões com severity e mensagem.
    """
    patterns = []

    # Funil zerado: nenhum candidato ativo em etapa avançada
    if total_active > 0 and candidates_in_advanced == 0:
        patterns.append({
            "pattern": "empty_advanced_funnel",
            "severity": "critical",
            "message": (
                f"Funil zerado em etapas avançadas: {total_active} candidato(s) ativo(s) "
                f"mas nenhum em entrevista ou oferta. Pipeline precisa de aceleração."
            ),
        })

    # Pipeline zerado: sem candidatos ativos
    if total_active == 0:
        patterns.append({
            "pattern": "zero_pipeline",
            "severity": "critical",
            "message": "Nenhum candidato ativo no pipeline. Vaga em risco de não fechar.",
        })

    # Drop-off anormal em offer stage (>40%)
    for stage_key in ("offer", "proposta"):
        rate = drop_off_by_stage.get(stage_key, 0.0)
        if rate > 0.40:
            patterns.append({
                "pattern": "high_offer_rejection",
                "severity": "critical",
                "message": (
                    f"Taxa de recusa na etapa '{stage_key}': {rate:.0%}. "
                    f"Acima de 40% — pode indicar problema com proposta ou processo."
                ),
            })

    # Top-heavy funnel: >70% dos candidatos ainda na triagem/aplicado
    top_stages = {"applied", "novo", "initial", "screening", "triagem"}
    top_count = sum(
        f["active_count"] for f in funnel
        if _normalize_stage(f["stage"]) in top_stages
    )
    if total_active > 3 and top_count / total_active > 0.70:
        patterns.append({
            "pattern": "top_heavy_funnel",
            "severity": "warning",
            "message": (
                f"{top_count} de {total_active} candidatos ({top_count / total_active:.0%}) "
                f"ainda nas etapas iniciais. Funil concentrado no topo."
            ),
        })

    # Health score crítico
    if health_score < 30:
        patterns.append({
            "pattern": "critical_health",
            "severity": "critical",
            "message": (
                f"Health score crítico: {health_score}/100. "
                f"Pipeline necessita de intervenção imediata."
            ),
        })

    return patterns


class JourneyIntelligenceService:
    """
    Serviço de inteligência de funil de candidatos por vaga e empresa.
    Calcula conversão, drop-off, health score e detecta padrões preditivos.
    """

    async def get_vacancy_metrics(
        self,
        vacancy_id: str,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Retorna métricas detalhadas do funil de uma vaga específica.
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            # Funil: count por stage (ativos)
            funnel_result = await db.execute(
                text("""
                    SELECT
                        vc.stage,
                        COUNT(*) FILTER (WHERE vc.status = 'active')     AS active_count,
                        COUNT(*) FILTER (WHERE vc.status IN ('rejected', 'withdrawn', 'desistiu', 'reprovado')) AS exited_count,
                        COUNT(*) FILTER (WHERE vc.status = 'hired')      AS hired_count,
                        COUNT(*)                                          AS total_count,
                        AVG(
                            EXTRACT(EPOCH FROM (
                                COALESCE(vc.updated_at, NOW()) - COALESCE(vc.stage_entered_at, vc.updated_at)
                            )) / 86400.0
                        )                                                 AS avg_days_in_stage,
                        MAX(vc.updated_at)                                AS last_movement
                    FROM vacancy_candidates vc
                    WHERE vc.vacancy_id::text = :vacancy_id
                    GROUP BY vc.stage
                """),
                {"vacancy_id": vacancy_id},
            )
            funnel_rows = funnel_result.fetchall()

            # Vaga metadata + recruiter
            vac_result = await db.execute(
                text("""
                    SELECT
                        jv.id::text AS vacancy_id,
                        jv.title,
                        jv.status,
                        jv.created_at,
                        jv.deadline,
                        COALESCE(u.id::text, jv.created_by) AS recruiter_id
                    FROM job_vacancies jv
                    LEFT JOIN users u
                        ON u.email = jv.recruiter_email
                        AND u.company_id::text = :company_id
                    WHERE jv.id::text = :vacancy_id
                      AND jv.company_id::text = :company_id
                """),
                {"vacancy_id": vacancy_id, "company_id": company_id},
            )
            vac_row = vac_result.fetchone()

            # EWS — tem candidatos critical/high?
            ews_result = await db.execute(
                text("""
                    SELECT COUNT(*) AS at_risk_count,
                           MAX(
                               EXTRACT(EPOCH FROM (
                                   NOW() - COALESCE(MAX(cl.sent_at), vc.stage_entered_at, vc.updated_at)
                               )) / 86400.0
                           ) AS max_days_no_contact
                    FROM vacancy_candidates vc
                    LEFT JOIN communication_logs cl
                        ON cl.candidate_id = vc.candidate_id::text
                        AND cl.company_id = :company_id
                        AND cl.status IN ('sent', 'delivered', 'read')
                    WHERE vc.vacancy_id::text = :vacancy_id
                      AND vc.status = 'active'
                    GROUP BY vc.id
                    HAVING EXTRACT(EPOCH FROM (
                               NOW() - COALESCE(MAX(cl.sent_at), vc.stage_entered_at, vc.updated_at)
                           )) / 86400.0 >= 3
                """),
                {"vacancy_id": vacancy_id, "company_id": company_id},
            )
            ews_rows = ews_result.fetchall()

        except Exception as e:
            logger.warning(f"get_vacancy_metrics query failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if should_close:
                await db.close()

        # Build funnel
        funnel: list[dict[str, Any]] = []
        total_active = 0
        total_exited = 0
        drop_off_by_stage: dict[str, float] = {}
        last_movement_ts = None
        advanced_stages = {
            "interview_hr", "entrevista_rh", "interview_technical",
            "entrevista_tecnica", "interview_manager", "interview_final",
            "offer", "proposta",
        }
        candidates_in_advanced = 0

        for row in funnel_rows:
            active = int(row.active_count or 0)
            exited = int(row.exited_count or 0)
            total = int(row.total_count or 0)
            drop_rate = exited / total if total > 0 else 0.0
            stage_norm = _normalize_stage(row.stage)

            entry: dict[str, Any] = {
                "stage": row.stage,
                "active_count": active,
                "exited_count": exited,
                "hired_count": int(row.hired_count or 0),
                "total_count": total,
                "drop_off_rate": round(drop_rate, 3),
                "avg_days_in_stage": round(float(row.avg_days_in_stage or 0), 1),
            }
            funnel.append(entry)
            total_active += active
            total_exited += exited
            drop_off_by_stage[stage_norm] = drop_rate

            if stage_norm in advanced_stages:
                candidates_in_advanced += active

            if row.last_movement and (
                last_movement_ts is None
                or row.last_movement > last_movement_ts
            ):
                last_movement_ts = row.last_movement

        # Sort by stage rank
        funnel.sort(key=lambda x: _stage_rank(x["stage"]))

        # Overall conversion: active in advanced / total ever entered
        total_ever = total_active + total_exited
        conversion_rate_overall = candidates_in_advanced / total_ever if total_ever > 0 else 0.0
        avg_drop_off = (
            sum(drop_off_by_stage.values()) / len(drop_off_by_stage)
            if drop_off_by_stage else 0.0
        )

        # Days since last movement
        import datetime
        now = datetime.datetime.now(datetime.UTC)
        if last_movement_ts:
            ts = last_movement_ts
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=datetime.UTC)
            days_since_last_movement = (now - ts).total_seconds() / 86400
        else:
            days_since_last_movement = 999.0

        has_critical_ews = len(ews_rows) > 0

        health_score = compute_health_score(
            total_active=total_active,
            conversion_rate_overall=conversion_rate_overall,
            avg_drop_off_rate=avg_drop_off,
            candidates_in_advanced_stages=candidates_in_advanced,
            has_critical_ews=has_critical_ews,
            days_since_last_movement=days_since_last_movement,
        )

        risk_patterns = detect_risk_patterns(
            funnel=funnel,
            total_active=total_active,
            candidates_in_advanced=candidates_in_advanced,
            drop_off_by_stage=drop_off_by_stage,
            health_score=health_score,
        )

        # Days to deadline
        days_to_deadline = None
        if vac_row and vac_row.deadline:
            dl = vac_row.deadline
            if dl.tzinfo is None:
                dl = dl.replace(tzinfo=datetime.UTC)
            days_to_deadline = max(0, (dl - now).days)

        return {
            "success": True,
            "vacancy_id": vacancy_id,
            "vacancy_title": vac_row.title if vac_row else None,
            "vacancy_status": vac_row.status if vac_row else None,
            "recruiter_id": vac_row.recruiter_id if vac_row else None,
            "days_to_deadline": days_to_deadline,
            "funnel": funnel,
            "summary": {
                "total_active": total_active,
                "total_exited": total_exited,
                "candidates_in_advanced_stages": candidates_in_advanced,
                "conversion_rate_overall": round(conversion_rate_overall, 3),
                "avg_drop_off_rate": round(avg_drop_off, 3),
                "days_since_last_movement": round(days_since_last_movement, 1),
                "at_risk_candidates": len(ews_rows),
            },
            "health_score": health_score,
            "health_label": health_label(health_score),
            "risk_patterns": risk_patterns,
        }

    async def get_company_overview(
        self,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Visão geral de saúde do pipeline por vaga ativa para toda a empresa.
        Retorna lista de vagas ordenada por health_score ASC (piores primeiro).
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            result = await db.execute(
                text("""
                    SELECT
                        jv.id::text AS vacancy_id,
                        jv.title    AS vacancy_title,
                        COALESCE(u.id::text, jv.created_by) AS recruiter_id,
                        COUNT(vc.id) FILTER (WHERE vc.status = 'active') AS total_active,
                        COUNT(vc.id) FILTER (
                            WHERE vc.status = 'active'
                            AND LOWER(vc.stage) IN (
                                'interview_hr','entrevista_rh',
                                'interview_technical','entrevista_tecnica',
                                'interview_manager','interview_final',
                                'offer','proposta'
                            )
                        ) AS candidates_in_advanced,
                        COUNT(vc.id) FILTER (
                            WHERE vc.status IN ('rejected','withdrawn','desistiu','reprovado')
                        ) AS total_exited,
                        MAX(vc.updated_at) AS last_movement
                    FROM job_vacancies jv
                    LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id
                    LEFT JOIN users u
                        ON u.email = jv.recruiter_email
                        AND u.company_id::text = :company_id
                    WHERE jv.company_id::text = :company_id
                      AND jv.status IN ('open', 'Ativa', 'Publicada')
                    GROUP BY jv.id, jv.title, COALESCE(u.id::text, jv.created_by)
                """),
                {"company_id": company_id},
            )
            rows = result.fetchall()
        except Exception as e:
            logger.warning(f"get_company_overview query failed: {e}")
            return {"success": False, "vacancies": [], "error": str(e)}
        finally:
            if should_close:
                await db.close()

        import datetime
        now = datetime.datetime.now(datetime.UTC)

        vacancies = []
        for row in rows:
            total_active = int(row.total_active or 0)
            total_exited = int(row.total_exited or 0)
            adv = int(row.candidates_in_advanced or 0)
            total_ever = total_active + total_exited
            conv = adv / total_ever if total_ever > 0 else 0.0

            if row.last_movement:
                lm = row.last_movement
                if lm.tzinfo is None:
                    lm = lm.replace(tzinfo=datetime.UTC)
                days_since = (now - lm).total_seconds() / 86400
            else:
                days_since = 999.0

            hs = compute_health_score(
                total_active=total_active,
                conversion_rate_overall=conv,
                avg_drop_off_rate=0.3,  # conservative estimate sem breakdown
                candidates_in_advanced_stages=adv,
                has_critical_ews=False,
                days_since_last_movement=days_since,
            )

            vacancies.append({
                "vacancy_id": row.vacancy_id,
                "vacancy_title": row.vacancy_title,
                "recruiter_id": row.recruiter_id,
                "total_active": total_active,
                "candidates_in_advanced_stages": adv,
                "conversion_rate": round(conv, 3),
                "days_since_last_movement": round(days_since, 1),
                "health_score": hs,
                "health_label": health_label(hs),
            })

        vacancies.sort(key=lambda x: x["health_score"])  # piores primeiro

        critical_count = sum(1 for v in vacancies if v["health_label"] == "critical")
        warning_count = sum(1 for v in vacancies if v["health_label"] == "warning")

        return {
            "success": True,
            "company_id": company_id,
            "total_open_vacancies": len(vacancies),
            "summary": {
                "critical": critical_count,
                "warning": warning_count,
                "healthy": len(vacancies) - critical_count - warning_count,
            },
            "vacancies": vacancies,
        }

    async def get_company_recruiters_journey(
        self,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """
        Agrega métricas de saúde por recrutador — para ProactiveWorker.
        Retorna apenas vagas com health_score < 50 (warning + critical).
        """
        overview = await self.get_company_overview(company_id=company_id, db=db)
        if not overview.get("success"):
            return []

        # Group by recruiter
        recruiter_map: dict[str, dict[str, Any]] = {}
        for vac in overview["vacancies"]:
            rid = vac.get("recruiter_id") or "unknown"
            if rid not in recruiter_map:
                recruiter_map[rid] = {
                    "recruiter_id": rid,
                    "at_risk_vacancies": [],
                    "critical_count": 0,
                    "warning_count": 0,
                }
            if vac["health_score"] < 50:
                recruiter_map[rid]["at_risk_vacancies"].append(vac)
                if vac["health_label"] == "critical":
                    recruiter_map[rid]["critical_count"] += 1
                else:
                    recruiter_map[rid]["warning_count"] += 1

        return [r for r in recruiter_map.values() if r["at_risk_vacancies"]]


journey_intelligence_service = JourneyIntelligenceService()
