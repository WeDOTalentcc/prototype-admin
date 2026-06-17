"""
Recruiter Metrics Service — Sprint 2A (Recruiter Intelligence, Opção C).

Agrega métricas de produtividade do recrutador a partir de dados existentes:
- vacancy_candidates (stage_entered_at, stage, status)
- job_vacancies (created_by = recruiter link)
- communication_logs (sent_at = último contato com candidato)
- interviews (entrevistas agendadas)

Nenhuma migration necessária. Todos os dados já existem.
Linkage: vacancy_candidates.vacancy_id → job_vacancies.created_by = recruiter user_id
"""

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "recruiter_metrics_service is deprecated and will be removed once Rails adapter routes are complete. "
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

# Thresholds de urgência por etapa (dias sem ação = urgente)
_URGENCY_THRESHOLDS: dict[str, int] = {
    # Oferta — crítico mover rápido
    "offer": 2,
    "proposta": 2,
    # Entrevistas
    "interview_hr": 4,
    "entrevista_rh": 4,
    "interview_technical": 4,
    "entrevista_tecnica": 4,
    "interview_manager": 4,
    "interview_final": 4,
    # Triagem
    "screening": 5,
    "triagem": 5,
    # Candidaturas novas
    "applied": 3,
    "novo": 3,
    "initial": 3,
}

_DEFAULT_URGENCY_THRESHOLD = 5


def _urgency_threshold(stage: str) -> int:
    return _URGENCY_THRESHOLDS.get((stage or "").lower(), _DEFAULT_URGENCY_THRESHOLD)


def _urgency_weight(stage: str) -> float:
    """Peso para ordenação de urgência. Offer > entrevista > triagem > novo."""
    stage_lower = (stage or "").lower()
    if stage_lower in ("offer", "proposta"):
        return 4.0
    if "interview" in stage_lower or "entrevista" in stage_lower:
        return 3.0
    if stage_lower in ("screening", "triagem"):
        return 2.0
    return 1.0


class RecruiterMetricsService:
    """
    Serviço de métricas de produtividade do recrutador.
    Surfaça via: Daily Briefing, chat LIA (tool) e alertas ProactiveWorker.
    """

    async def get_action_backlog(
        self,
        recruiter_id: str,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retorna candidatos nas vagas do recrutador que precisam de ação,
        ordenados por urgência decrescente.

        Urgente = candidato na etapa atual há mais dias que o threshold da etapa.
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            result = await db.execute(
                text("""
                    SELECT
                        vc.id::text            AS vacancy_candidate_id,
                        vc.candidate_id::text  AS candidate_id,
                        c.name                 AS candidate_name,
                        vc.vacancy_id::text    AS vacancy_id,
                        jv.title               AS vacancy_title,
                        vc.stage,
                        vc.status,
                        vc.stage_entered_at,
                        EXTRACT(EPOCH FROM (NOW() - COALESCE(vc.stage_entered_at, vc.updated_at)))
                            / 86400.0          AS days_in_stage,
                        MAX(cl.sent_at)        AS last_contact_at
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv
                        ON vc.vacancy_id = jv.id
                        AND jv.company_id::text = :company_id
                        AND jv.status IN ('open', 'Ativa', 'Publicada')
                        AND (
                            jv.created_by = :recruiter_id
                            OR jv.recruiter_email = (
                                SELECT email FROM users
                                WHERE id::text = :recruiter_id
                                LIMIT 1
                            )
                        )
                    JOIN candidates c
                        ON vc.candidate_id = c.id
                    LEFT JOIN communication_logs cl
                        ON cl.candidate_id = vc.candidate_id::text
                        AND cl.company_id = :company_id
                        AND cl.status IN ('sent', 'delivered', 'read')
                    WHERE vc.status = 'active'
                    GROUP BY
                        vc.id, vc.candidate_id, c.name,
                        vc.vacancy_id, jv.title,
                        vc.stage, vc.status,
                        vc.stage_entered_at, vc.updated_at
                """),
                {"recruiter_id": recruiter_id, "company_id": company_id},
            )
            rows = result.fetchall()
        except Exception as e:
            logger.warning(f"get_action_backlog query failed: {e}")
            return []
        finally:
            if should_close:
                await db.close()

        backlog = []
        for row in rows:
            days_in_stage = float(row.days_in_stage or 0)
            threshold = _urgency_threshold(row.stage)
            if days_in_stage < threshold:
                continue  # ainda dentro do prazo

            weight = _urgency_weight(row.stage)
            backlog.append(
                {
                    "vacancy_candidate_id": row.vacancy_candidate_id,
                    "candidate_id": row.candidate_id,
                    "candidate_name": row.candidate_name,
                    "vacancy_id": row.vacancy_id,
                    "vacancy_title": row.vacancy_title,
                    "stage": row.stage,
                    "days_in_stage": round(days_in_stage, 1),
                    "threshold_days": threshold,
                    "overdue_days": round(days_in_stage - threshold, 1),
                    "last_contact_at": row.last_contact_at.isoformat() if row.last_contact_at else None,
                    "urgency_score": round(days_in_stage * weight, 2),
                    "is_critical": row.stage.lower() in ("offer", "proposta") and days_in_stage >= threshold,
                }
            )

        backlog.sort(key=lambda x: x["urgency_score"], reverse=True)
        return backlog

    async def get_response_time_avg(
        self,
        recruiter_id: str,
        company_id: str,
        period_days: int = 30,
        db: AsyncSession | None = None,
    ) -> float | None:
        """
        Tempo médio (em dias) entre um candidato entrar em uma etapa e o
        primeiro contato da empresa (via communication_logs).
        Retorna None se não houver dados suficientes.
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            result = await db.execute(
                text("""
                    SELECT AVG(
                        EXTRACT(EPOCH FROM (cl.sent_at - vc.stage_entered_at)) / 86400.0
                    ) AS avg_days
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv
                        ON vc.vacancy_id = jv.id
                        AND jv.company_id::text = :company_id
                        AND (
                            jv.created_by = :recruiter_id
                            OR jv.recruiter_email = (
                                SELECT email FROM users
                                WHERE id::text = :recruiter_id
                                LIMIT 1
                            )
                        )
                    JOIN (
                        SELECT candidate_id, MIN(sent_at) AS sent_at
                        FROM communication_logs
                        WHERE company_id = :company_id
                          AND status IN ('sent', 'delivered', 'read')
                        GROUP BY candidate_id
                    ) cl ON cl.candidate_id = vc.candidate_id::text
                    WHERE vc.stage_entered_at IS NOT NULL
                      AND cl.sent_at > vc.stage_entered_at
                      AND vc.stage_entered_at >= NOW() - INTERVAL '1 day' * :period_days
                """),
                {
                    "recruiter_id": recruiter_id,
                    "company_id": company_id,
                    "period_days": period_days,
                },
            )
            row = result.fetchone()
            return round(float(row.avg_days), 1) if row and row.avg_days is not None else None
        except Exception as e:
            logger.warning(f"get_response_time_avg query failed: {e}")
            return None
        finally:
            if should_close:
                await db.close()

    async def get_weekly_summary(
        self,
        recruiter_id: str,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Resumo semanal do recrutador para o Daily Briefing.
        Retorna estrutura segura — nunca lança exceção.
        """
        backlog = await self.get_action_backlog(recruiter_id, company_id, db)
        response_time = await self.get_response_time_avg(recruiter_id, company_id, 30, db)

        critical = [b for b in backlog if b["is_critical"]]
        most_urgent = backlog[0] if backlog else None

        # Candidatos avançados essa semana
        advanced_count = await self._get_advanced_this_week(recruiter_id, company_id, db)

        # Ofertas pendentes
        offers_pending = sum(
            1 for b in backlog
            if b["stage"].lower() in ("offer", "proposta")
        )

        return {
            "backlog_count": len(backlog),
            "critical_count": len(critical),
            "most_urgent": most_urgent,
            "avg_response_time_days": response_time,
            "candidates_advanced_this_week": advanced_count,
            "offers_pending": offers_pending,
        }

    async def _get_advanced_this_week(
        self,
        recruiter_id: str,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> int:
        """Candidatos que mudaram de etapa nos últimos 7 dias nas vagas do recrutador."""
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            result = await db.execute(
                text("""
                    SELECT COUNT(*) AS cnt
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv
                        ON vc.vacancy_id = jv.id
                        AND jv.company_id::text = :company_id
                        AND (
                            jv.created_by = :recruiter_id
                            OR jv.recruiter_email = (
                                SELECT email FROM users
                                WHERE id::text = :recruiter_id
                                LIMIT 1
                            )
                        )
                    WHERE vc.stage_entered_at >= NOW() - INTERVAL '7 days'
                      AND vc.status = 'active'
                """),
                {"recruiter_id": recruiter_id, "company_id": company_id},
            )
            row = result.fetchone()
            return int(row.cnt) if row else 0
        except Exception as e:
            logger.warning(f"_get_advanced_this_week query failed: {e}")
            return 0
        finally:
            if should_close:
                await db.close()

    async def get_company_recruiters_backlog(
        self,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retorna o backlog agregado por recrutador para toda a empresa.
        Usado pelo ProactiveAgentWorker — uma query, sem N+1.
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            result = await db.execute(
                text("""
                    SELECT
                        COALESCE(
                            u.id::text,
                            jv.created_by
                        )                                       AS recruiter_id,
                        vc.stage,
                        COUNT(*)                               AS candidate_count,
                        MAX(
                            EXTRACT(EPOCH FROM (NOW() - COALESCE(vc.stage_entered_at, vc.updated_at)))
                            / 86400.0
                        )                                       AS max_days_in_stage
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv
                        ON vc.vacancy_id = jv.id
                        AND jv.company_id::text = :company_id
                        AND jv.status IN ('open', 'Ativa', 'Publicada')
                    LEFT JOIN users u
                        ON u.email = jv.recruiter_email
                        AND u.company_id::text = :company_id
                    WHERE vc.status = 'active'
                      AND COALESCE(u.id::text, jv.created_by) IS NOT NULL
                    GROUP BY COALESCE(u.id::text, jv.created_by), vc.stage
                """),
                {"company_id": company_id},
            )
            rows = result.fetchall()
        except Exception as e:
            logger.warning(f"get_company_recruiters_backlog query failed: {e}")
            return []
        finally:
            if should_close:
                await db.close()

        # Agrupa por recruiter_id
        recruiters: dict[str, dict[str, Any]] = {}
        for row in rows:
            rid = row.recruiter_id
            if rid not in recruiters:
                recruiters[rid] = {
                    "recruiter_id": rid,
                    "company_id": company_id,
                    "total_active": 0,
                    "critical_stages": [],
                    "max_days_in_any_stage": 0.0,
                }
            threshold = _urgency_threshold(row.stage)
            max_days = float(row.max_days_in_stage or 0)
            recruiters[rid]["total_active"] += int(row.candidate_count)
            recruiters[rid]["max_days_in_any_stage"] = max(
                recruiters[rid]["max_days_in_any_stage"], max_days
            )
            if max_days >= threshold:
                recruiters[rid]["critical_stages"].append(
                    {
                        "stage": row.stage,
                        "candidate_count": int(row.candidate_count),
                        "max_days": round(max_days, 1),
                        "threshold_days": threshold,
                    }
                )

        return list(recruiters.values())


    async def get_company_benchmark(
        self,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Calcula a mediana anônima de métricas de todos os recrutadores ativos na empresa.
        Requer ≥ 2 recrutadores com dados para retornar benchmark válido (privacidade).

        Retorna:
          median_response_time_days, median_advanced_per_week,
          median_backlog_count, median_offers_pending, recruiter_count
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            # Busca todos os recrutadores com vagas ativas na empresa
            result = await db.execute(
                text("""
                    SELECT DISTINCT
                        COALESCE(u.id::text, jv.created_by) AS recruiter_id
                    FROM job_vacancies jv
                    LEFT JOIN users u
                        ON u.email = jv.recruiter_email
                        AND u.company_id::text = :company_id
                    WHERE jv.company_id::text = :company_id
                      AND jv.status IN ('open', 'Ativa', 'Publicada')
                      AND COALESCE(u.id::text, jv.created_by) IS NOT NULL
                """),
                {"company_id": company_id},
            )
            recruiter_ids = [r[0] for r in result.fetchall()]
        except Exception as e:
            logger.warning(f"get_company_benchmark recruiters query failed: {e}")
            return {"benchmark_available": False}
        finally:
            if should_close:
                await db.close()

        # Requer pelo menos 2 recrutadores para preservar privacidade
        if len(recruiter_ids) < 2:
            return {"benchmark_available": False, "recruiter_count": len(recruiter_ids)}

        # Coleta métricas de cada recrutador
        all_metrics: list[dict[str, Any]] = []
        for rid in recruiter_ids:
            try:
                summary = await self.get_weekly_summary(recruiter_id=rid, company_id=company_id)
                all_metrics.append(summary)
            except Exception:
                continue

        if len(all_metrics) < 2:
            return {"benchmark_available": False, "recruiter_count": len(recruiter_ids)}

        def _median(values: list[float]) -> float:
            sorted_vals = sorted(v for v in values if v is not None)
            n = len(sorted_vals)
            if n == 0:
                return 0.0
            mid = n // 2
            return round(
                (sorted_vals[mid - 1] + sorted_vals[mid]) / 2 if n % 2 == 0
                else sorted_vals[mid],
                1,
            )

        response_times = [m["avg_response_time_days"] for m in all_metrics if m["avg_response_time_days"] is not None]
        advanced_counts = [float(m["candidates_advanced_this_week"]) for m in all_metrics]
        backlog_counts = [float(m["backlog_count"]) for m in all_metrics]
        offers_counts = [float(m["offers_pending"]) for m in all_metrics]

        return {
            "benchmark_available": True,
            "recruiter_count": len(all_metrics),
            "median_response_time_days": _median(response_times) if response_times else None,
            "median_advanced_per_week": _median(advanced_counts),
            "median_backlog_count": _median(backlog_counts),
            "median_offers_pending": _median(offers_counts),
        }

    async def get_recruiter_benchmark_comparison(
        self,
        recruiter_id: str,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Retorna métricas pessoais do recrutador + benchmark da empresa + comparação.

        Para cada métrica calcula:
          - valor pessoal
          - mediana da empresa
          - delta (pessoal - mediana)
          - percentile_label: "above" | "at" | "below" (±15% de tolerância)
          - is_positive: True quando "above" é bom (ex: advanced_per_week)
                         True quando "below" é bom (ex: response_time, backlog)
        """
        personal, benchmark = await asyncio.gather(
            self.get_weekly_summary(recruiter_id, company_id, db),
            self.get_company_benchmark(company_id, db),
        )

        def _compare(
            personal_val: float | None,
            benchmark_val: float | None,
            lower_is_better: bool = False,
        ) -> dict[str, Any]:
            if personal_val is None or benchmark_val is None or benchmark_val == 0:
                return {
                    "personal": personal_val,
                    "benchmark": benchmark_val,
                    "delta": None,
                    "percentile_label": "unknown",
                    "performance": "unknown",
                }
            delta = round(personal_val - benchmark_val, 1)
            pct_diff = abs(delta) / benchmark_val if benchmark_val else 0
            tolerance = 0.15  # ±15% = "at par"

            # Determina se o valor pessoal é melhor ou pior que a mediana
            is_better = (personal_val < benchmark_val) if lower_is_better else (personal_val > benchmark_val)

            if pct_diff <= tolerance:
                label = "at_par"
                performance = "at_par"
            elif is_better:
                label = "above"   # acima da média (positivo)
                performance = "better"
            else:
                label = "below"   # abaixo da média (negativo)
                performance = "worse"

            return {
                "personal": personal_val,
                "benchmark": benchmark_val,
                "delta": delta,
                "percentile_label": label,
                "performance": performance,
            }

        response_time_cmp = _compare(
            personal.get("avg_response_time_days"),
            benchmark.get("median_response_time_days"),
            lower_is_better=True,
        )
        advanced_cmp = _compare(
            float(personal.get("candidates_advanced_this_week", 0)),
            benchmark.get("median_advanced_per_week"),
            lower_is_better=False,
        )
        backlog_cmp = _compare(
            float(personal.get("backlog_count", 0)),
            benchmark.get("median_backlog_count"),
            lower_is_better=True,
        )
        offers_cmp = _compare(
            float(personal.get("offers_pending", 0)),
            benchmark.get("median_offers_pending"),
            lower_is_better=True,
        )

        # Score geral de performance: contagem de métricas "better"
        comparisons = [response_time_cmp, advanced_cmp, backlog_cmp, offers_cmp]
        better_count = sum(1 for c in comparisons if c.get("performance") == "better")
        at_par_count = sum(1 for c in comparisons if c.get("performance") == "at_par")
        known_count = sum(1 for c in comparisons if c.get("performance") != "unknown")

        if known_count == 0:
            overall_performance = "unknown"
        elif better_count >= 3:
            overall_performance = "above_average"
        elif better_count + at_par_count >= 3:
            overall_performance = "average"
        else:
            overall_performance = "below_average"

        return {
            "recruiter_id": recruiter_id,
            "company_id": company_id,
            "benchmark_available": benchmark.get("benchmark_available", False),
            "recruiter_count_in_benchmark": benchmark.get("recruiter_count", 0),
            "overall_performance": overall_performance,
            "personal": personal,
            "comparison": {
                "response_time": response_time_cmp,
                "advanced_per_week": advanced_cmp,
                "backlog_count": backlog_cmp,
                "offers_pending": offers_cmp,
            },
        }


import asyncio

recruiter_metrics_service = RecruiterMetricsService()
