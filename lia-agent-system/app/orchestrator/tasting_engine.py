"""
TastingEngine — Contextual proactive insights for premium module tasting.

Detects context moments in the chat flow and generates real insights by calling
existing tools (analyze_skill_gaps, get_market_intelligence, match_internal_candidates)
in summary mode. Each insight is shown once per context key (candidate/job/company)
with a 24h TTL to avoid repetition.

Integration point: MainOrchestrator._inject_module_tasting_hints calls
TastingEngine.generate_insights() after Phase 2 response.

NOTE: Insights are appended to message content as markdown. The structured
tasting_insights metadata on ChatResponse is not yet forwarded through WS to
the frontend. The frontend TastingInsightCard component is ready for when the
metadata path is wired (future enhancement).
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_DISPLAY_TTL_SECONDS = 86400  # 24h
_INSIGHT_TIMEOUT_SECONDS = 5


@dataclass
class TastingInsight:
    module_name: str
    module_label: str
    insight_type: str
    summary: str
    cta: str
    context_key: str
    badge: str = "BETA"


@dataclass
class _DisplayRecord:
    context_key: str
    timestamp: float


class _FrequencyCache:
    def __init__(self, ttl: int = _DISPLAY_TTL_SECONDS) -> None:
        self._seen: dict[str, float] = {}
        self._ttl = ttl

    def was_shown(self, key: str) -> bool:
        ts = self._seen.get(key)
        if ts is None:
            return False
        if time.monotonic() - ts > self._ttl:
            del self._seen[key]
            return False
        return True

    def mark_shown(self, key: str) -> None:
        self._seen[key] = time.monotonic()
        if len(self._seen) > 5000:
            cutoff = time.monotonic() - self._ttl
            self._seen = {k: v for k, v in self._seen.items() if v > cutoff}


_CANDIDATE_ANALYSIS_PATTERNS = (
    r"analis[ea]r?\s+(o\s+)?candid",
    r"compatibilidade\s+d[eo]\s+candid",
    r"match\s+(d[eo]\s+)?candid",
    r"triag(em|ar)\s+(d[eo]\s+)?c[uv]",
    r"score\s+d[eo]\s+candid",
    r"avali[ea]r?\s+(o\s+)?c[uv]",
    r"gap\s+(de\s+)?skills?",
    r"skills?\s+gap",
    r"cv_screening",
    r"talent_analysis",
)

_JOB_SALARY_PATTERNS = (
    r"sal[aá]rio",
    r"faixa\s+salarial",
    r"remunera[cç][aã]o",
    r"benchmark\s+(salarial|de\s+mercado)",
    r"quanto\s+(pag|gan)",
    r"mercado\s+pag",
    r"salary_benchmark",
    r"market_intelligence",
    r"criar?\s+(uma\s+)?vaga",
    r"abr[ie]r?\s+(uma\s+)?vaga",
    r"nova\s+vaga",
    r"create_job",
)

_INTERNAL_MOBILITY_PATTERNS = (
    r"abr[ie]r?\s+(uma\s+)?vaga",
    r"nova\s+(posi[cç][aã]o|vaga)",
    r"vaga\s+(aberta|nova)",
    r"mobilidade\s+interna",
    r"candidato[s]?\s+interno[s]?",
    r"colaborador[es]*\s+(compatível|para|que)",
    r"create_job",
    r"internal_mobility",
)


class TastingEngine:
    def __init__(self) -> None:
        self._cache = _FrequencyCache()
        self._display_log: list[dict[str, Any]] = []

    async def generate_insights(
        self,
        ctx_company_id: str,
        ctx_message: str,
        ctx_intent: str,
        ctx_domain: str,
        ctx_entity_id: str | None,
        ctx_entity_type: str | None,
        ctx_candidates: list[dict[str, Any]] | None,
        ctx_job_context: dict[str, Any] | None,
        result: dict[str, Any],
    ) -> list[TastingInsight]:
        if not ctx_company_id:
            return []

        signals = f"{ctx_intent} {ctx_domain} {ctx_message}".lower()
        insights: list[TastingInsight] = []

        if self._matches(signals, _CANDIDATE_ANALYSIS_PATTERNS):
            insight = await self._safe_generate(
                self._generate_skill_gap_insight(
                    company_id=ctx_company_id,
                    candidates=ctx_candidates,
                    job_context=ctx_job_context,
                    entity_id=ctx_entity_id,
                    entity_type=ctx_entity_type,
                    result=result,
                ),
                "skill_gap",
            )
            if insight:
                insights.append(insight)

        if self._matches(signals, _JOB_SALARY_PATTERNS):
            insight = await self._safe_generate(
                self._generate_market_intel_insight(
                    company_id=ctx_company_id,
                    job_context=ctx_job_context,
                    result=result,
                ),
                "market_intel",
            )
            if insight:
                insights.append(insight)

        if self._matches(signals, _INTERNAL_MOBILITY_PATTERNS):
            insight = await self._safe_generate(
                self._generate_internal_mobility_insight(
                    company_id=ctx_company_id,
                    job_context=ctx_job_context,
                    entity_id=ctx_entity_id,
                    result=result,
                ),
                "internal_mobility",
            )
            if insight:
                insights.append(insight)

        shown = []
        for ins in insights[:2]:
            if not self._cache.was_shown(ins.context_key):
                self._cache.mark_shown(ins.context_key)
                self._log_display(ctx_company_id, ins)
                shown.append(ins)

        return shown

    async def _safe_generate(
        self,
        coro: Any,
        label: str,
    ) -> TastingInsight | None:
        try:
            return await asyncio.wait_for(coro, timeout=_INSIGHT_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            logger.warning("[TastingEngine] %s insight timed out after %ss", label, _INSIGHT_TIMEOUT_SECONDS)
            return None
        except Exception as exc:
            logger.debug("[TastingEngine] %s insight failed: %s", label, exc)
            return None

    def _matches(self, text: str, patterns: tuple[str, ...]) -> bool:
        return any(re.search(p, text) for p in patterns)

    async def _generate_skill_gap_insight(
        self,
        company_id: str,
        candidates: list[dict[str, Any]] | None,
        job_context: dict[str, Any] | None,
        entity_id: str | None,
        entity_type: str | None,
        result: dict[str, Any],
    ) -> TastingInsight | None:
        candidate_id = None
        candidate_skills: list[str] = []
        job_id = None
        required_skills: list[str] = []

        if entity_type == "candidate" and entity_id:
            candidate_id = entity_id
        elif candidates:
            first = candidates[0] if candidates else None
            if first:
                candidate_id = str(first.get("id", ""))
                candidate_skills = list(first.get("technical_skills") or first.get("skills") or [])

        if job_context:
            job_id = str(job_context.get("id", job_context.get("job_id", "")))
            required_skills = list(
                job_context.get("required_skills")
                or job_context.get("technical_requirements")
                or []
            )
            if required_skills and isinstance(required_skills[0], dict):
                required_skills = [r.get("technology", "") for r in required_skills if r.get("technology")]

        context_key = f"skill_gap:{company_id}:{candidate_id or 'none'}:{job_id or 'none'}"
        if self._cache.was_shown(context_key):
            return None

        summary_parts: list[str] = []
        try:
            from app.domains.talent_intelligence.tools.skills_ontology_tools import analyze_skill_gaps
            gap_result = await analyze_skill_gaps(
                candidate_skills=candidate_skills or None,
                required_skills=required_skills or None,
                candidate_id=candidate_id,
                job_id=job_id,
                company_id=company_id,
            )
            if gap_result.get("success"):
                data = gap_result.get("data", {})
                missing = data.get("missing_skills", [])
                adjacency = data.get("adjacency_matches", [])
                match_pct = data.get("effective_match_percentage", 0)
                if missing:
                    gap_text = ", ".join(missing[:3])
                    summary_parts.append(f"gap em **{gap_text}**")
                if adjacency:
                    adj_skills = [a.get("related_candidate_skill", "") for a in adjacency[:2] if a.get("related_candidate_skill")]
                    if adj_skills:
                        summary_parts.append(f"skills adjacentes transferíveis: **{', '.join(adj_skills)}**")
                if match_pct:
                    summary_parts.append(f"match efetivo de {match_pct}%")
        except Exception as exc:
            logger.debug("[TastingEngine] skill gap call failed: %s", exc)

        if not summary_parts:
            summary_parts.append("identificamos gaps e skills adjacentes transferíveis para este candidato")

        summary = "Este candidato tem " + "; ".join(summary_parts) + "."

        return TastingInsight(
            module_name="talent_intelligence_pro",
            module_label="Talent Intelligence Pro",
            insight_type="skill_gap",
            summary=summary,
            cta="Para análise completa de skills com ontologia de grafos, ative **Talent Intelligence Pro**.",
            context_key=context_key,
        )

    async def _generate_market_intel_insight(
        self,
        company_id: str,
        job_context: dict[str, Any] | None,
        result: dict[str, Any],
    ) -> TastingInsight | None:
        job_title = ""
        location = ""
        seniority = ""
        job_id = ""

        if job_context:
            job_title = str(job_context.get("title", job_context.get("job_title", "")))
            location = str(job_context.get("location", job_context.get("location_city", "")))
            seniority = str(job_context.get("seniority_level", job_context.get("seniority", "")))
            job_id = str(job_context.get("id", job_context.get("job_id", "")))

        context_key = f"market_intel:{company_id}:{job_id or job_title or 'none'}"
        if self._cache.was_shown(context_key):
            return None

        summary = ""
        try:
            if job_title:
                from app.domains.talent_intelligence.tools.market_intelligence_tools import get_market_intelligence
                mi_result = await get_market_intelligence(
                    job_title=job_title,
                    seniority=seniority or None,
                    location=location or None,
                    include_trends=False,
                )
                if mi_result.get("success"):
                    data = mi_result.get("data", {})
                    sal = data.get("salary_benchmark", {})
                    sal_min = sal.get("min")
                    sal_max = sal.get("max")
                    if sal_min and sal_max:
                        summary = (
                            f"Para **{job_title}**"
                            f"{' em ' + location if location else ''}, "
                            f"o mercado paga R$ {int(sal_min):,} – R$ {int(sal_max):,}."
                        )
        except Exception as exc:
            logger.debug("[TastingEngine] market intel call failed: %s", exc)

        if not summary:
            summary = "Temos dados de mercado em tempo real para esta posição, incluindo faixas salariais e tendências."

        return TastingInsight(
            module_name="talent_intelligence_pro",
            module_label="Talent Intelligence Pro",
            insight_type="market_intelligence",
            summary=summary,
            cta="Para benchmarks salariais completos e tendências de mercado, ative **Talent Intelligence Pro**.",
            context_key=context_key,
        )

    async def _generate_internal_mobility_insight(
        self,
        company_id: str,
        job_context: dict[str, Any] | None,
        entity_id: str | None,
        result: dict[str, Any],
    ) -> TastingInsight | None:
        job_id = ""
        job_title = ""
        required_skills: list[str] = []

        if job_context:
            job_id = str(job_context.get("id", job_context.get("job_id", "")))
            job_title = str(job_context.get("title", job_context.get("job_title", "")))
            required_skills = list(
                job_context.get("required_skills")
                or job_context.get("technical_requirements")
                or []
            )
            if required_skills and isinstance(required_skills[0], dict):
                required_skills = [r.get("technology", "") for r in required_skills if r.get("technology")]

        context_key = f"internal_mobility:{company_id}:{job_id or 'none'}"
        if self._cache.was_shown(context_key):
            return None

        summary = ""
        try:
            from app.domains.talent_intelligence.tools.internal_mobility_tools import match_internal_candidates
            im_result = await match_internal_candidates(
                job_id=job_id or None,
                required_skills=required_skills or None,
                job_title=job_title or None,
                limit=5,
                company_id=company_id,
            )
            if im_result.get("success"):
                data = im_result.get("data", {})
                total = data.get("total_matches", 0)
                ready_now = data.get("ready_now", 0)
                if total > 0:
                    summary = (
                        f"Encontrei **{total}** colaboradores internos com perfil compatível"
                        f"{' para ' + job_title if job_title else ''}."
                    )
                    if ready_now > 0:
                        summary += f" **{ready_now}** estão prontos agora."
        except Exception as exc:
            logger.debug("[TastingEngine] internal mobility call failed: %s", exc)

        if not summary:
            summary = "Podemos buscar colaboradores internos com perfil compatível para esta posição."

        return TastingInsight(
            module_name="internal_mobility",
            module_label="Internal Mobility Suite",
            insight_type="internal_mobility",
            summary=summary,
            cta="Para matching interno completo com readiness scoring, ative **Internal Mobility Suite**.",
            context_key=context_key,
        )

    def _log_display(self, company_id: str, insight: TastingInsight) -> None:
        record = {
            "company_id": company_id,
            "module_name": insight.module_name,
            "insight_type": insight.insight_type,
            "context_key": insight.context_key,
            "timestamp": time.time(),
        }
        self._display_log.append(record)
        if len(self._display_log) > 10000:
            self._display_log = self._display_log[-5000:]
        logger.info(
            "[TastingEngine] insight_displayed company=%s module=%s type=%s key=%s",
            company_id, insight.module_name, insight.insight_type, insight.context_key,
        )

    def get_display_stats(self, company_id: str | None = None) -> dict[str, Any]:
        records = self._display_log
        if company_id:
            records = [r for r in records if r["company_id"] == company_id]
        by_module: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for r in records:
            by_module[r["module_name"]] = by_module.get(r["module_name"], 0) + 1
            by_type[r["insight_type"]] = by_type.get(r["insight_type"], 0) + 1
        return {
            "total_displays": len(records),
            "by_module": by_module,
            "by_type": by_type,
        }


def format_tasting_block(insights: list[TastingInsight]) -> str:
    if not insights:
        return ""
    lines: list[str] = ["\n\n---"]
    for ins in insights:
        lines.append(
            f"🧪 **[{ins.badge}]** {ins.summary}\n"
            f"_{ins.cta}_"
        )
    return "\n".join(lines)


tasting_engine = TastingEngine()
