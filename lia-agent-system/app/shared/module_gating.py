"""
Module gating infrastructure for premium tool access control.

Maps tools to monetizable modules and provides:
- `require_module` decorator for tool functions
- `check_tool_module_access()` for integration with tool_handler
- Degraded response templates with CTA for inactive modules
- BETA mode: all tools liberated with informational badge
"""
import logging
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

TOOL_MODULE_MAP: dict[str, str] = {
    "infer_related_skills": "talent_intelligence_pro",
    "get_skill_adjacencies": "talent_intelligence_pro",
    "analyze_skill_gaps": "talent_intelligence_pro",
    "map_candidate_skills_to_ontology": "talent_intelligence_pro",
    "get_market_intelligence": "talent_intelligence_pro",

    "match_internal_candidates": "internal_mobility",

    "analyze_interview_recording": "interview_intelligence",
    "detect_interview_bias": "interview_intelligence",
    "generate_interview_opinion": "interview_intelligence",
    "generate_candidate_feedback": "interview_intelligence",
    "compare_interview_performance": "interview_intelligence",

    "forecast_hiring_needs": "workforce_planning",

    "create_nurture_sequence": "candidate_nurture",
    "get_engagement_metrics": "candidate_nurture",
    "suggest_reengagement": "candidate_nurture",
}

PREMIUM_GATED_TOOLS: set[str] = {
    "analyze_interview_recording",
    "detect_interview_bias",
    "generate_interview_opinion",
    "generate_candidate_feedback",
    "compare_interview_performance",
    "forecast_hiring_needs",
    "create_nurture_sequence",
}

TASTING_TOOLS: set[str] = {
    "infer_related_skills",
    "get_skill_adjacencies",
    "analyze_skill_gaps",
    "get_market_intelligence",
    "match_internal_candidates",
    "get_engagement_metrics",
    "suggest_reengagement",
    "map_candidate_skills_to_ontology",
}

MODULE_LABELS: dict[str, str] = {
    "talent_intelligence_pro": "Talent Intelligence Pro",
    "internal_mobility": "Internal Mobility Suite",
    "interview_intelligence": "Interview Intelligence Pro",
    "workforce_planning": "Workforce Planning",
    "candidate_nurture": "Candidate Nurture / CRM",
}

_DEGRADED_TEMPLATES: dict[str, dict[str, str]] = {
    "talent_intelligence_pro": {
        "summary": "Identifiquei {count} skills relacionadas no grafo de ontologia. "
                   "A análise completa inclui adjacências ponderadas, gap analysis detalhado e intelligence de mercado.",
        "cta": "Para análise completa com ontologia de skills, gap analysis e market intelligence, "
               "ative o módulo **Talent Intelligence Pro**.",
    },
    "internal_mobility": {
        "summary": "Encontrei potenciais candidatos internos para esta posição. "
                   "A análise completa inclui matching baseado em ontologia de skills e readiness scoring.",
        "cta": "Para matching interno completo com readiness scoring, "
               "ative o módulo **Internal Mobility Suite**.",
    },
    "interview_intelligence": {
        "summary": "A análise de entrevistas requer processamento avançado de transcrições "
                   "com mapeamento de competências, detecção de viés e sentimento.",
        "cta": "Para análise completa de entrevistas com competency mapping e bias detection, "
               "ative o módulo **Interview Intelligence Pro**.",
    },
    "workforce_planning": {
        "summary": "A previsão de contratação requer análise avançada de dados de turnover, "
                   "pipeline e cenários de crescimento.",
        "cta": "Para previsão completa com cenários e dashboard de workforce, "
               "ative o módulo **Workforce Planning**.",
    },
    "candidate_nurture": {
        "summary": "Identifiquei candidatos que poderiam se beneficiar de reengajamento. "
                   "A gestão completa inclui sequências automatizadas e métricas de engajamento.",
        "cta": "Para sequências de nurture automatizadas e métricas de engajamento, "
               "ative o módulo **Candidate Nurture / CRM**.",
    },
}

_BETA_BADGE = " ℹ️ Este recurso está disponível gratuitamente durante o período BETA."


def build_degraded_response(
    tool_name: str,
    module_name: str,
    partial_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    template = _DEGRADED_TEMPLATES.get(module_name, {})
    label = MODULE_LABELS.get(module_name, module_name)
    summary = template.get("summary", f"Este recurso requer o módulo {label}.")
    cta = template.get("cta", f"Para acesso completo, ative o módulo **{label}**.")

    if partial_data and "count" in partial_data:
        summary = summary.format(count=partial_data["count"])
    else:
        summary = summary.replace("{count}", "algumas")

    return {
        "success": True,
        "data": partial_data or {},
        "message": f"{summary}\n\n{cta}",
        "module_required": module_name,
        "module_label": label,
        "module_active": False,
        "is_degraded": True,
    }


def build_beta_response(
    result: dict[str, Any],
    module_name: str,
) -> dict[str, Any]:
    label = MODULE_LABELS.get(module_name, module_name)
    if isinstance(result.get("message"), str):
        result["message"] = result["message"] + _BETA_BADGE
    result["module_status"] = "beta"
    result["module_name"] = module_name
    result["module_label"] = label
    return result


async def check_tool_module_access(
    tool_name: str,
    company_id: str,
    db: Any,
) -> dict[str, Any]:
    module_name = TOOL_MODULE_MAP.get(tool_name)
    if not module_name:
        return {"allowed": True, "module_name": None, "status": None}

    try:
        from app.domains.modules.services.module_service import module_service
        status = await module_service.get_module_status(db, company_id, module_name)

        if status == "beta":
            return {"allowed": True, "module_name": module_name, "status": "beta"}
        elif status in ("active", "trial"):
            return {"allowed": True, "module_name": module_name, "status": status}
        elif status in ("disabled", "expired", "coming_soon") or status is None:
            is_premium = tool_name in PREMIUM_GATED_TOOLS
            is_tasting = tool_name in TASTING_TOOLS
            return {
                "allowed": False,
                "module_name": module_name,
                "status": status or "not_provisioned",
                "is_premium_gated": is_premium,
                "is_tasting": is_tasting,
            }
        else:
            return {"allowed": True, "module_name": module_name, "status": status}
    except Exception as exc:
        logger.warning("Module access check failed for %s/%s: %s — fail-closed", tool_name, company_id, exc)
        is_premium = tool_name in PREMIUM_GATED_TOOLS
        is_tasting = tool_name in TASTING_TOOLS
        return {
            "allowed": False,
            "module_name": module_name,
            "status": "error_fallback",
            "is_premium_gated": is_premium,
            "is_tasting": is_tasting,
        }


def require_module(module_name: str):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(**kwargs: Any) -> dict[str, Any]:
            import asyncio

            company_id = kwargs.get("company_id")
            db = kwargs.get("db")
            tool_name = func.__name__

            if not company_id or not db:
                logger.warning(
                    "require_module fail-closed: missing context for %s (company_id=%s, db=%s)",
                    tool_name, bool(company_id), bool(db),
                )
                return build_degraded_response(tool_name, module_name)

            access = await check_tool_module_access(tool_name, company_id, db)

            if access["allowed"]:
                result = func(**kwargs)
                if asyncio.iscoroutine(result):
                    result = await result

                if access.get("status") == "beta":
                    if isinstance(result, dict):
                        return build_beta_response(result, module_name)

                return result

            if tool_name in PREMIUM_GATED_TOOLS:
                return build_degraded_response(tool_name, module_name)

            if tool_name in TASTING_TOOLS:
                try:
                    result = func(**kwargs)
                    if asyncio.iscoroutine(result):
                        result = await result
                    if isinstance(result, dict):
                        tasting_data = _extract_tasting_data(result)
                        return build_degraded_response(tool_name, module_name, partial_data=tasting_data)
                except Exception:
                    return build_degraded_response(tool_name, module_name)

            return build_degraded_response(tool_name, module_name)

        wrapper._module_gated = module_name
        return wrapper

    return decorator


def _extract_tasting_data(result: dict[str, Any]) -> dict[str, Any]:
    data = result.get("data", result)
    if not isinstance(data, dict):
        return {"preview": True}

    tasting: dict[str, Any] = {"preview": True}

    skills_key = None
    for k in ("skills", "related_skills", "canonical_skills", "mapped_skills"):
        if k in data and isinstance(data[k], list):
            skills_key = k
            break
    if skills_key:
        tasting["skills_preview"] = data[skills_key][:3]
        tasting["count"] = len(data[skills_key])
        tasting["total_available"] = len(data[skills_key])

    candidates_key = None
    for k in ("candidates", "matches", "internal_matches", "internal_candidates"):
        if k in data and isinstance(data[k], list):
            candidates_key = k
            break
    if candidates_key:
        tasting["candidates_preview"] = [
            {"name": c.get("name", ""), "match_score": c.get("match_score", c.get("score"))}
            for c in data[candidates_key][:2]
        ]
        tasting["count"] = len(data[candidates_key])

    gaps_key = None
    for k in ("gaps", "missing_skills", "skill_gaps"):
        if k in data and isinstance(data[k], list):
            gaps_key = k
            break
    if gaps_key:
        tasting["gaps_count"] = len(data[gaps_key])
        tasting["count"] = len(data[gaps_key])
        if data[gaps_key]:
            tasting["top_gap"] = data[gaps_key][0] if isinstance(data[gaps_key][0], str) else str(data[gaps_key][0])

    if "adjacencies" in data and isinstance(data["adjacencies"], (list, dict)):
        count = len(data["adjacencies"]) if isinstance(data["adjacencies"], list) else len(data["adjacencies"].keys())
        tasting["count"] = count

    if "metrics" in data and isinstance(data["metrics"], dict):
        tasting["metrics_preview"] = {k: data["metrics"][k] for k in list(data["metrics"].keys())[:2]}
        tasting["count"] = len(data["metrics"])

    if "market_snapshot" in data and isinstance(data["market_snapshot"], dict):
        snap = data["market_snapshot"]
        tasting["market_preview"] = {k: snap[k] for k in list(snap.keys())[:3]}
        tasting["count"] = tasting.get("count", len(snap))

    return tasting
