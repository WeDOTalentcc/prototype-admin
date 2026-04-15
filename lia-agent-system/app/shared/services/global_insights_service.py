"""
Global Insights Service — anonymous cross-tenant intelligence (Camada 3).

Aggregates anonymized patterns from ALL tenants to provide market-level
intelligence that benefits every customer from day one (cold start resolution).

Architecture:
  Camada 1: Few-shot estáticos (YAML) — piso de qualidade
  Camada 2: Aprendizado por tenant (CalibrationWeight + Preferences) — personalização
  Camada 3: Inteligência global anônima (THIS SERVICE) — padrões de mercado

Privacy: AnonymizationPipeline removes all identifiable data before aggregation.
Minimum thresholds: 10 tenants + 100 samples per bucket.

Item: P36 Full — Communication agent first, reusable for all agents.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Minimum thresholds for statistical validity + privacy
MIN_TENANT_THRESHOLD = 10
MIN_SAMPLE_SIZE = 100


class AnonymizationPipeline:
    """Strips all identifiable data, keeps only statistical patterns."""

    @staticmethod
    def anonymize_communication_event(event: dict[str, Any]) -> dict[str, Any] | None:
        """Remove identifiable data, keep statistical pattern."""
        try:
            return {
                "channel": event.get("channel"),
                "seniority_bucket": event.get("seniority_level", "unknown"),
                "sector_bucket": event.get("sector", "unknown"),
                "template_category": event.get("template_type", "general"),
                "send_hour_bucket": _bucket_hour(event.get("sent_at")),
                "send_day_bucket": _bucket_day(event.get("sent_at")),
                "responded": bool(event.get("responded")),
                "response_time_bucket": _bucket_time(event.get("response_time_hours")),
                # REMOVED: company_id, candidate_id, recruiter_id, names, content
            }
        except Exception:
            return None


def _bucket_hour(sent_at: Any) -> str:
    """Bucket hours into ranges."""
    if not sent_at:
        return "unknown"
    try:
        hour = sent_at.hour if hasattr(sent_at, "hour") else int(sent_at)
        if 8 <= hour < 10:
            return "early_morning"
        if 10 <= hour < 12:
            return "late_morning"
        if 12 <= hour < 14:
            return "lunch"
        if 14 <= hour < 17:
            return "afternoon"
        return "evening"
    except Exception:
        return "unknown"


def _bucket_day(sent_at: Any) -> str:
    """Bucket day of week."""
    if not sent_at:
        return "unknown"
    try:
        weekday = sent_at.weekday() if hasattr(sent_at, "weekday") else 0
        days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        return days[weekday] if weekday < 7 else "unknown"
    except Exception:
        return "unknown"


def _bucket_time(hours: Any) -> str:
    """Bucket response time into ranges."""
    if hours is None:
        return "no_response"
    try:
        h = float(hours)
        if h < 1:
            return "under_1h"
        if h < 4:
            return "1_4h"
        if h < 24:
            return "4_24h"
        if h < 72:
            return "1_3d"
        return "over_3d"
    except Exception:
        return "unknown"


class GlobalInsightsService:
    """Provides anonymized cross-tenant intelligence.

    Returns hardcoded baseline insights initially (bootstrapped from market research).
    When aggregation Celery task runs with sufficient data, insights are
    updated from real anonymized patterns.

    Usage:
        service = get_global_insights()
        insights = await service.get_communication_insights()
        # inject into prompt context
    """

    # Bootstrapped from market research — replaced by real data when available
    _BASELINE_COMMUNICATION_INSIGHTS: dict[str, Any] = {
        "best_channels_by_seniority": {
            "estagiario": {"email": 0.55, "whatsapp": 0.90},
            "junior": {"email": 0.60, "whatsapp": 0.85},
            "pleno": {"email": 0.70, "whatsapp": 0.75},
            "senior": {"email": 0.78, "whatsapp": 0.52},
            "lead": {"email": 0.82, "whatsapp": 0.45},
            "diretor": {"email": 0.90, "whatsapp": 0.30},
        },
        "best_send_times": {
            "email": "09:00-10:00 terca a quinta",
            "whatsapp": "14:00-16:00 segunda a quarta",
        },
        "avg_response_rates": {
            "personalized": 0.72,
            "template_generic": 0.35,
            "follow_up_1": 0.45,
            "follow_up_2": 0.22,
            "follow_up_3": 0.08,
        },
        "avg_response_time_hours": {
            "email": 18.5,
            "whatsapp": 2.3,
        },
        "source": "market_research_baseline",
        "sample_size": 0,
        "last_updated": "2026-04-14",
    }

    async def get_communication_insights(self) -> dict[str, Any]:
        """Get communication patterns. Tries DB first, falls back to baseline."""
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    text("SELECT insights FROM global_insights WHERE domain = 'communication' LIMIT 1")
                )
                row = result.scalar_one_or_none()
                if row and isinstance(row, dict) and row.get("sample_size", 0) >= MIN_SAMPLE_SIZE:
                    return row
        except Exception as exc:
            logger.debug("[GlobalInsights] DB lookup failed (using baseline): %s", exc)

        return dict(self._BASELINE_COMMUNICATION_INSIGHTS)

    def format_for_prompt(self, insights: dict[str, Any]) -> str:
        """Format insights as a prompt snippet for agent injection."""
        lines = ["[DADOS DE MERCADO — inteligencia global anonimizada]"]

        # Best channels by seniority
        channels = insights.get("best_channels_by_seniority", {})
        if channels:
            lines.append("Canais com melhor taxa de resposta por senioridade:")
            for seniority, rates in channels.items():
                best = max(rates.items(), key=lambda x: x[1])
                lines.append(f"  - {seniority}: {best[0]} ({best[1]:.0%})")

        # Best times
        times = insights.get("best_send_times", {})
        if times:
            lines.append("Melhores horarios de envio:")
            for channel, time_range in times.items():
                lines.append(f"  - {channel}: {time_range}")

        # Response rates
        rates = insights.get("avg_response_rates", {})
        if rates:
            personalized = rates.get("personalized", 0)
            generic = rates.get("template_generic", 0)
            if personalized and generic:
                lift = ((personalized - generic) / max(generic, 0.01)) * 100
                lines.append(f"Mensagens personalizadas tem {lift:.0f}% mais resposta que templates genericos.")

        source = insights.get("source", "baseline")
        sample = insights.get("sample_size", 0)
        if sample > 0:
            lines.append(f"Base: {sample:,} comunicacoes anonimizadas.")
        else:
            lines.append("Base: pesquisa de mercado (dados reais serao agregados com uso).")

        return "\n".join(lines)


    # ── Integration ATS insights ──────────────────────────────────

    _BASELINE_INTEGRATION_INSIGHTS: dict[str, Any] = {
        "popular_ats_by_sector": {
            "tech": ["Gupy", "Greenhouse", "Lever"],
            "finance": ["Pandape", "Workday", "SAP SuccessFactors"],
            "retail": ["Pandape", "Kenoby", "Gupy"],
            "health": ["Pandape", "TOTVS", "Senior"],
            "logistics": ["Pandape", "Gupy"],
        },
        "common_mapping_issues": [
            "seniority_level: 60% das empresas precisam mapear manualmente",
            "salary_range: formato varia (anual vs mensal, USD vs BRL)",
            "skills/tags: taxonomias divergentes entre ATSs",
        ],
        "sync_best_practices": {
            "frequency": "diaria para vagas ativas, semanal para encerradas",
            "conflict_resolution": "72% preferem ATS como master para dados cadastrais",
            "batch_size": "max 100 registros por sync (evita timeout)",
        },
        "avg_setup_time_minutes": 25,
        "common_errors": {
            "401_expired_token": "35% dos erros — renovar credenciais",
            "429_rate_limit": "25% — reduzir frequencia ou batch size",
            "500_server_error": "20% — retry em 30min",
            "mapping_error": "15% — campo obrigatorio faltando",
        },
        "source": "market_research_baseline",
        "sample_size": 0,
        "last_updated": "2026-04-14",
    }

    async def get_integration_insights(self) -> dict[str, Any]:
        """Get ATS integration patterns. Tries DB first, falls back to baseline."""
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    text("SELECT insights FROM global_insights WHERE domain = 'integration' LIMIT 1")
                )
                row = result.scalar_one_or_none()
                if row and isinstance(row, dict) and row.get("sample_size", 0) >= MIN_SAMPLE_SIZE:
                    return row
        except Exception as exc:
            logger.debug("[GlobalInsights] integration DB lookup failed: %s", exc)

        return dict(self._BASELINE_INTEGRATION_INSIGHTS)

    def format_integration_for_prompt(self, insights: dict[str, Any]) -> str:
        """Format integration insights as prompt snippet."""
        lines = ["[DADOS DE MERCADO — inteligencia global de integracao ATS]"]

        ats_by_sector = insights.get("popular_ats_by_sector", {})
        if ats_by_sector:
            lines.append("ATSs mais populares por setor:")
            for sector, atss in ats_by_sector.items():
                lines.append(f"  - {sector}: {', '.join(atss)}")

        practices = insights.get("sync_best_practices", {})
        if practices:
            lines.append("Boas praticas de sync:")
            for key, val in practices.items():
                lines.append(f"  - {key}: {val}")

        errors = insights.get("common_errors", {})
        if errors:
            lines.append("Erros mais comuns e solucoes:")
            for code, desc in errors.items():
                lines.append(f"  - {code}: {desc}")

        return "\n".join(lines)


    # ── Interview Scheduling insights ──────────────────────────────

    _BASELINE_SCHEDULING_INSIGHTS: dict[str, Any] = {
        "best_times_by_seniority": {
            "junior": "10h-11h terca a quinta",
            "pleno": "14h-16h terca a quinta",
            "senior": "10h-11h segunda a quarta",
            "diretor": "09h-10h terca ou quarta",
        },
        "no_show_rate_by_invite_channel": {
            "email_only": 0.18,
            "email_plus_whatsapp": 0.08,
            "auto_scheduling_link": 0.05,
        },
        "ideal_advance_days": {
            "junior": 2,
            "pleno": 3,
            "senior": 5,
            "diretor": 7,
        },
        "reschedule_rate_by_day": {
            "segunda": 0.12,
            "terca": 0.08,
            "quarta": 0.07,
            "quinta": 0.09,
            "sexta": 0.22,
        },
        "avg_interview_duration_minutes": {
            "triagem": 20,
            "tecnica": 60,
            "comportamental": 45,
            "final": 30,
        },
        "source": "market_research_baseline",
        "sample_size": 0,
        "last_updated": "2026-04-14",
    }

    async def get_scheduling_insights(self) -> dict[str, Any]:
        """Get interview scheduling patterns."""
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    text("SELECT insights FROM global_insights WHERE domain = 'scheduling' LIMIT 1")
                )
                row = result.scalar_one_or_none()
                if row and isinstance(row, dict) and row.get("sample_size", 0) >= MIN_SAMPLE_SIZE:
                    return row
        except Exception as exc:
            logger.debug("[GlobalInsights] scheduling DB lookup failed: %s", exc)

        return dict(self._BASELINE_SCHEDULING_INSIGHTS)

    def format_scheduling_for_prompt(self, insights: dict[str, Any]) -> str:
        """Format scheduling insights as prompt snippet."""
        lines = ["[DADOS DE MERCADO — inteligencia global de agendamento]"]

        times = insights.get("best_times_by_seniority", {})
        if times:
            lines.append("Melhores horarios por senioridade:")
            for seniority, time_range in times.items():
                lines.append(f"  - {seniority}: {time_range}")

        no_show = insights.get("no_show_rate_by_invite_channel", {})
        if no_show:
            lines.append("Taxa de no-show por canal de convite:")
            for channel, rate in no_show.items():
                lines.append(f"  - {channel.replace('_', ' ')}: {rate:.0%}")

        reschedule = insights.get("reschedule_rate_by_day", {})
        if reschedule:
            worst_day = max(reschedule.items(), key=lambda x: x[1])
            best_day = min(reschedule.items(), key=lambda x: x[1])
            lines.append(f"Reagendamentos: {worst_day[0]} ({worst_day[1]:.0%}) e o pior dia; {best_day[0]} ({best_day[1]:.0%}) e o melhor.")

        return "\n".join(lines)


    # ── WSI Screening / Evaluation insights ────────────────────────

    _BASELINE_SCREENING_INSIGHTS: dict[str, Any] = {
        "score_distribution_by_seniority": {
            "junior": {"avg": 3.2, "p25": 2.5, "p75": 3.8},
            "pleno": {"avg": 3.6, "p25": 3.0, "p75": 4.2},
            "senior": {"avg": 4.0, "p25": 3.5, "p75": 4.5},
            "lead": {"avg": 4.2, "p25": 3.7, "p75": 4.6},
        },
        "recruiter_ia_agreement_rate": 0.78,
        "most_discriminating_criteria": {
            "tech": ["arquitetura de sistemas", "resolucao de problemas", "code review"],
            "behavioral": ["lideranca situacional", "comunicacao sob pressao", "colaboracao cross-team"],
            "general": ["experiencia pratica > certificacoes", "consistencia STAR > extensao"],
        },
        "common_red_flags": [
            "Respostas genericas sem exemplos concretos (62% dos candidatos reprovados)",
            "Inconsistencia entre CV e respostas verbais (28%)",
            "Evasividade em perguntas sobre falhas/erros (24%)",
            "Experiencia declarada sem evidencia de profundidade (18%)",
        ],
        "source": "market_research_baseline",
        "sample_size": 0,
        "last_updated": "2026-04-14",
    }

    async def get_screening_insights(self) -> dict[str, Any]:
        """Get WSI screening/evaluation patterns."""
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    text("SELECT insights FROM global_insights WHERE domain = 'screening' LIMIT 1")
                )
                row = result.scalar_one_or_none()
                if row and isinstance(row, dict) and row.get("sample_size", 0) >= MIN_SAMPLE_SIZE:
                    return row
        except Exception as exc:
            logger.debug("[GlobalInsights] screening DB lookup failed: %s", exc)

        return dict(self._BASELINE_SCREENING_INSIGHTS)

    def format_screening_for_prompt(self, insights: dict[str, Any]) -> str:
        """Format screening insights as prompt snippet."""
        lines = ["[DADOS DE MERCADO — inteligencia global de avaliacao WSI]"]

        scores = insights.get("score_distribution_by_seniority", {})
        if scores:
            lines.append("Score medio WSI por senioridade (escala 0-5):")
            for seniority, dist in scores.items():
                lines.append(f"  - {seniority}: media {dist['avg']}, P25={dist['p25']}, P75={dist['p75']}")

        agreement = insights.get("recruiter_ia_agreement_rate")
        if agreement:
            lines.append(f"Taxa de concordancia recrutador vs IA: {agreement:.0%}")

        flags = insights.get("common_red_flags", [])
        if flags:
            lines.append("Red flags mais comuns em candidatos reprovados:")
            for flag in flags[:4]:
                lines.append(f"  - {flag}")

        return "\n".join(lines)


    # ── Automation insights ────────────────────────────────────────

    _BASELINE_AUTOMATION_INSIGHTS: dict[str, Any] = {
        "most_used_automations": ["follow-up pos-triagem", "lembrete de entrevista", "feedback de rejeicao", "alerta pipeline parado"],
        "engagement_rate_by_type": {"follow_up": 0.45, "reminder": 0.72, "rejection_feedback": 0.30, "stage_alert": 0.85},
        "ideal_followup_frequency": {"first": "3 dias", "second": "7 dias", "max": "2 follow-ups por candidato"},
        "automations_often_disabled": ["rejeicao automatica (42% desativam)", "bulk move sem revisao (38%)"],
        "source": "market_research_baseline", "sample_size": 0, "last_updated": "2026-04-14",
    }

    async def get_automation_insights(self) -> dict[str, Any]:
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("SELECT insights FROM global_insights WHERE domain = 'automation' LIMIT 1"))
                row = result.scalar_one_or_none()
                if row and isinstance(row, dict) and row.get("sample_size", 0) >= MIN_SAMPLE_SIZE:
                    return row
        except Exception:
            pass
        return dict(self._BASELINE_AUTOMATION_INSIGHTS)

    def format_automation_for_prompt(self, insights: dict[str, Any]) -> str:
        lines = ["[DADOS DE MERCADO — inteligencia global de automacao]"]
        most_used = insights.get("most_used_automations", [])
        if most_used:
            lines.append(f"Automacoes mais usadas: {', '.join(most_used[:4])}")
        disabled = insights.get("automations_often_disabled", [])
        if disabled:
            lines.append("Automacoes que recrutadores desativam:")
            for d in disabled:
                lines.append(f"  - {d}")
        return "\n".join(lines)

    # ── Analytics insights ────────────────────────────────────────

    _BASELINE_ANALYTICS_INSIGHTS: dict[str, Any] = {
        "benchmarks_by_sector": {
            "tech": {"time_to_fill_days": 35, "candidates_per_hire": 28, "conversion_rate": 0.12, "cost_per_hire_brl": 4500},
            "finance": {"time_to_fill_days": 45, "candidates_per_hire": 35, "conversion_rate": 0.09, "cost_per_hire_brl": 6200},
            "retail": {"time_to_fill_days": 21, "candidates_per_hire": 18, "conversion_rate": 0.18, "cost_per_hire_brl": 2800},
            "health": {"time_to_fill_days": 40, "candidates_per_hire": 30, "conversion_rate": 0.10, "cost_per_hire_brl": 5000},
        },
        "conversion_rate_by_stage": {"triagem": 0.45, "entrevista_tecnica": 0.60, "entrevista_final": 0.75, "oferta": 0.85},
        "source": "market_research_baseline", "sample_size": 0, "last_updated": "2026-04-14",
    }

    async def get_analytics_insights(self) -> dict[str, Any]:
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("SELECT insights FROM global_insights WHERE domain = 'analytics' LIMIT 1"))
                row = result.scalar_one_or_none()
                if row and isinstance(row, dict) and row.get("sample_size", 0) >= MIN_SAMPLE_SIZE:
                    return row
        except Exception:
            pass
        return dict(self._BASELINE_ANALYTICS_INSIGHTS)

    def format_analytics_for_prompt(self, insights: dict[str, Any]) -> str:
        lines = ["[DADOS DE MERCADO — benchmarks de recrutamento por setor]"]
        benchmarks = insights.get("benchmarks_by_sector", {})
        for sector, metrics in benchmarks.items():
            lines.append(f"  {sector}: TTF={metrics['time_to_fill_days']}d, cand/vaga={metrics['candidates_per_hire']}, conversao={metrics['conversion_rate']:.0%}")
        return "\n".join(lines)

    # ── Company Settings insights ─────────────────────────────────

    _BASELINE_COMPANY_INSIGHTS: dict[str, Any] = {
        "most_filled_fields_by_sector": {"tech": ["tech_stack", "benefits", "work_model"], "finance": ["compliance_certifications", "salary_ranges"], "retail": ["locations", "shifts", "benefits"]},
        "most_common_benefits": ["vale-refeicao (92%)", "plano de saude (88%)", "vale-transporte (82%)", "home office (65%)", "gympass (48%)"],
        "avg_profile_completeness": 0.62,
        "sections_most_impacting_jd_quality": ["tech_stack (+35% match)", "behavioral_competencies (+28%)", "salary_ranges (+22%)"],
        "source": "market_research_baseline", "sample_size": 0, "last_updated": "2026-04-14",
    }

    async def get_company_settings_insights(self) -> dict[str, Any]:
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("SELECT insights FROM global_insights WHERE domain = 'company_settings' LIMIT 1"))
                row = result.scalar_one_or_none()
                if row and isinstance(row, dict) and row.get("sample_size", 0) >= MIN_SAMPLE_SIZE:
                    return row
        except Exception:
            pass
        return dict(self._BASELINE_COMPANY_INSIGHTS)

    def format_company_for_prompt(self, insights: dict[str, Any]) -> str:
        lines = ["[DADOS DE MERCADO — perfil empresarial]"]
        benefits = insights.get("most_common_benefits", [])
        if benefits:
            lines.append(f"Beneficios mais comuns: {', '.join(benefits[:5])}")
        completeness = insights.get("avg_profile_completeness")
        if completeness:
            lines.append(f"Completude media de perfil: {completeness:.0%}")
        sections = insights.get("sections_most_impacting_jd_quality", [])
        if sections:
            lines.append("Secoes que mais impactam qualidade de vagas:")
            for s in sections:
                lines.append(f"  - {s}")
        return "\n".join(lines)

    # ── Kanban / Pipeline insights ────────────────────────────────

    _BASELINE_KANBAN_INSIGHTS: dict[str, Any] = {
        "avg_days_per_stage": {"triagem": 3, "entrevista_tecnica": 5, "entrevista_final": 4, "oferta": 3, "contratacao": 2},
        "common_bottlenecks": ["entrevista_tecnica (42% das vagas)", "oferta (28% — aprovacao do gestor)"],
        "dropout_rate_by_stage": {"triagem": 0.55, "entrevista_tecnica": 0.25, "entrevista_final": 0.10, "oferta": 0.08},
        "stages_needing_recruiter_action": {"triagem": "revisao de CVs", "oferta": "aprovacao de proposta", "entrevista_final": "feedback pos-entrevista"},
        "source": "market_research_baseline", "sample_size": 0, "last_updated": "2026-04-14",
    }

    async def get_kanban_insights(self) -> dict[str, Any]:
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("SELECT insights FROM global_insights WHERE domain = 'kanban' LIMIT 1"))
                row = result.scalar_one_or_none()
                if row and isinstance(row, dict) and row.get("sample_size", 0) >= MIN_SAMPLE_SIZE:
                    return row
        except Exception:
            pass
        return dict(self._BASELINE_KANBAN_INSIGHTS)

    def format_kanban_for_prompt(self, insights: dict[str, Any]) -> str:
        lines = ["[DADOS DE MERCADO — inteligencia de pipeline]"]
        avg_days = insights.get("avg_days_per_stage", {})
        if avg_days:
            lines.append("Tempo medio por estagio:")
            for stage, days in avg_days.items():
                lines.append(f"  - {stage}: {days} dias")
        bottlenecks = insights.get("common_bottlenecks", [])
        if bottlenecks:
            lines.append("Gargalos mais comuns:")
            for b in bottlenecks:
                lines.append(f"  - {b}")
        return "\n".join(lines)


    # ── Autonomous cross-domain insights (aggregates all) ──────────

    async def get_autonomous_insights(self) -> dict[str, Any]:
        """Aggregate the most relevant insights from ALL domains for cross-domain agent."""
        combined: dict[str, Any] = {}
        try:
            comm = await self.get_communication_insights()
            combined["best_communication_channels"] = comm.get("best_channels_by_seniority", {})
        except Exception:
            pass
        try:
            sched = await self.get_scheduling_insights()
            combined["best_interview_times"] = sched.get("best_times_by_seniority", {})
            combined["no_show_rates"] = sched.get("no_show_rate_by_invite_channel", {})
        except Exception:
            pass
        try:
            screen = await self.get_screening_insights()
            combined["score_benchmarks"] = screen.get("score_distribution_by_seniority", {})
            combined["common_red_flags"] = screen.get("common_red_flags", [])[:3]
        except Exception:
            pass
        try:
            analytics = await self.get_analytics_insights()
            combined["sector_benchmarks"] = analytics.get("benchmarks_by_sector", {})
        except Exception:
            pass
        try:
            kanban = await self.get_kanban_insights()
            combined["pipeline_bottlenecks"] = kanban.get("common_bottlenecks", [])
            combined["avg_days_per_stage"] = kanban.get("avg_days_per_stage", {})
        except Exception:
            pass
        return combined

    def format_autonomous_for_prompt(self, insights: dict[str, Any]) -> str:
        """Format cross-domain insights as compact prompt snippet."""
        lines = ["[DADOS DE MERCADO — inteligencia cross-domain]"]

        benchmarks = insights.get("sector_benchmarks", {})
        if benchmarks:
            lines.append("Benchmarks por setor (TTF dias):")
            for sector, m in list(benchmarks.items())[:4]:
                ttf = m.get("time_to_fill_days", "?")
                lines.append(f"  - {sector}: {ttf}d")

        bottlenecks = insights.get("pipeline_bottlenecks", [])
        if bottlenecks:
            lines.append(f"Gargalos comuns: {'; '.join(bottlenecks[:2])}")

        flags = insights.get("common_red_flags", [])
        if flags:
            lines.append(f"Red flags frequentes: {'; '.join(str(f)[:60] for f in flags[:2])}")

        return "\n".join(lines)


_instance: GlobalInsightsService | None = None


def get_global_insights() -> GlobalInsightsService:
    """Get singleton GlobalInsightsService."""
    global _instance
    if _instance is None:
        _instance = GlobalInsightsService()
    return _instance
