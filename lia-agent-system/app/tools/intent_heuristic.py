"""Onda 5.3.a — Intent heuristic for tool scoping.

Classifies user message + context_page into a list of candidate agent_types
WITHOUT an LLM call. Output feeds ToolRegistry.get_schemas_for_agents() to
reduce tool schema footprint (~40-95% token saving on scoped calls).

Design choice: `recruiter_assistant` and `orchestrator` are INTENTIONALLY
excluded from hint sets. Both have 84-98 tools in allowed_agents — including
them in the hint union destroys scoping (empirical measurement: from 40%
saving to 9% when recruiter_assistant is added).

Fail-safe contract:
  - Empty list return → "no confident signal" → caller falls back to full
    catalog (current behavior preserved).
  - Never raises; worst case = passthrough.

Author: Onda 5.3.a (2026-04-22). Canonical-fix producer-side.
"""
from __future__ import annotations

import re
from typing import Iterable

from app.orchestrator.context_adapter import PAGE_TO_CONTEXT_TYPE


# ---------------------------------------------------------------------------
# Context-type → SPECIFIC agents (no orchestrator, no recruiter_assistant)
# ---------------------------------------------------------------------------
_CONTEXT_TYPE_TO_AGENTS: dict[str, list[str]] = {
    "talent_funnel": ["sourcing", "analyst_feedback", "cv_screening"],
    "pipeline": ["screening", "analyst_feedback", "scheduling", "interviewer"],
    "job_management": ["job_planner", "job_intake", "job_wizard"],
    "analytics": ["analytics"],
    "company_settings": ["company_settings", "automation"],
    "general": [],  # no hint — regex decides or fall back to full catalog
}


# ---------------------------------------------------------------------------
# Keyword patterns → SPECIFIC agent hints (IGNORECASE, plural-aware)
# ---------------------------------------------------------------------------
# `recruiter_assistant` keywords are NOT listed — same rationale as above.
_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "sourcing": [
        r"sourc(ing|ear|iar)",
        r"busc(ar|a)\s+(candidatos?|profissionais?|perfi)",
        r"prospe[ck]t",
        r"linkedin",
        r"talent(\s+pool)?",
        r"headhunt",
        r"apollo",
        r"pearch",
    ],
    "job_planner": [
        r"(cri|abr)(ar|ir)\s+(uma\s+)?vagas?",
        r"novas?\s+vagas?",
        r"publicar\s+vagas?",
        r"duplicar\s+vagas?",
    ],
    "job_wizard": [
        r"wizard",
        r"fluxo.*cria\w+.*vagas?",
    ],
    "job_intake": [
        r"briefings?\s+(de\s+)?vagas?",
        r"requisitos?.*vagas?",
    ],
    "cv_screening": [
        r"\bcv\b",
        r"curr[ií]cul",
        r"anal(is|ys).*cv",
    ],
    "screening": [
        r"tria(g|r|ge)",
        r"screen",
        r"avali.*candidatos?",
        r"notas?\s+do\s+candidatos?",
    ],
    "scheduling": [
        r"entrevistas?",
        r"agend",
        r"hor[áa]rios?",
        r"marcar\s+reuni",
        r"calend[áa]rios?",
    ],
    "communication": [
        r"e-?mails?",
        r"whats?apps?",
        r"mensagens?",
        r"notific",
        r"templates?\s+(de\s+)?comunica",
    ],
    "analytics": [
        r"relat[óo]rios?",
        r"dashboards?",
        r"m[ée]tricas?",
        r"an[áa]lises?",
        r"funil",
        r"kpi",
        r"performance",
    ],
    "automation": [
        r"automat",
        r"triggers?",
        r"regras?",
        r"fluxo.*autom",
    ],
    "analyst_feedback": [
        r"feedbacks?",
        r"pareceres?",
        r"avalia(ção|cao)",
    ],
}

# Pre-compile for speed
_COMPILED_PATTERNS: dict[str, list[re.Pattern]] = {
    agent: [re.compile(p, re.IGNORECASE) for p in patterns]
    for agent, patterns in _DOMAIN_KEYWORDS.items()
}


def classify_intent(
    user_message: str | None,
    context_page: str | None = None,
) -> list[str]:
    """Return candidate agent_types for tool scoping (empty = no hint).

    Args:
        user_message: user input text
        context_page: UniversalContext.context_page (e.g., "Vagas", "pipeline")

    Returns:
        List of agent_type strings to union-filter tool schemas. Empty list
        means "no confident signal" — caller should fall back to full catalog.
    """
    hints: list[str] = []
    seen: set[str] = set()

    # 1. context_page signal (screen navigation)
    if context_page:
        context_type = PAGE_TO_CONTEXT_TYPE.get(context_page, "general")
        for agent in _CONTEXT_TYPE_TO_AGENTS.get(context_type, []):
            if agent not in seen:
                hints.append(agent)
                seen.add(agent)

    # 2. Regex signal (message keywords)
    if user_message:
        for agent, patterns in _COMPILED_PATTERNS.items():
            if any(p.search(user_message) for p in patterns):
                if agent not in seen:
                    hints.append(agent)
                    seen.add(agent)

    return hints


def describe_hints(hints: Iterable[str]) -> str:
    """Human-readable summary for logging."""
    lst = list(hints)
    if not lst:
        return "(no hints — full catalog)"
    return f"{len(lst)} agents: {', '.join(lst)}"
