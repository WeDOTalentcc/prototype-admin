"""
Canonical template type resolver for the wizard de criação de vagas.

This module is the single source of truth for the deterministic
mapping `(job_title, department) → template_type`. It is consumed by
the canonical `JobCreationGraph` (Task #850) via `intake_node` and by
the deprecated `WizardStepService` (Onda 38 will delete it).

Onda 37.3.1 — moved here from
`app/domains/job_management/services/wizard_step_service/stage_basic_info.py`
as part of the canonical migration. The function is pure and synchronous
(no I/O), so it lives in `services/` rather than as a graph node.

Harness classification: computational sensor (deterministic word-boundary match).
"""
from __future__ import annotations

import re
from typing import Literal

TemplateType = Literal[
    "technical",
    "executive",
    "operational",
    "mass_hiring",
    "intern",
]


# ─────────────────────────────────────────────────────────────────────
# Keyword mapping — deterministic, no LLM
# ─────────────────────────────────────────────────────────────────────

TEMPLATE_TYPE_KEYWORDS: dict[TemplateType, list[str]] = {
    "technical": [
        "desenvolvedor", "developer", "dev", "engenheiro", "engineer",
        "backend", "frontend", "fullstack", "full-stack", "full stack",
        "software", "dados", "data", "analytics", "bi", "machine learning",
        "ml", "ia", "ai", "devops", "sre", "platform", "infrastructure",
        "infra", "cloud", "qa", "quality", "tester", "product manager",
        "product owner", "pm", "po", "tech", "tecnologia", "sistemas",
        "arquiteto", "architect", "security", "segurança", "cybersecurity",
    ],
    "executive": [
        "diretor", "director", "cto", "ceo", "coo", "cfo", "cmo",
        "vp", "vice-presidente", "vice presidente", "head of",
        "head de", "c-level", "clevel", "presidente", "president",
        "gerente geral", "general manager",
    ],
    "mass_hiring": [
        "volume", "massa", "mass", "operador", "operator", "atendente",
        "attendant", "motorista", "driver", "entregador", "delivery",
        "caixa", "cashier", "repositor", "promotor", "promotora",
        "vendedor", "sales rep", "agente", "agent",
    ],
    "intern": [
        "estágio", "estagio", "estagiário", "estagiaria", "intern",
        "trainee", "aprendiz", "apprentice", "jovem aprendiz",
    ],
    "operational": [
        "analista", "analyst", "coordenador", "coordinator", "supervisor",
        "assistente", "assistant", "auxiliar", "auxiliary", "técnico", "tecnico",
        "technician", "especialista", "specialist", "consultor", "consultant",
        "gerente", "manager",
    ],
}


TEMPLATE_DISPLAY: dict[TemplateType, dict[str, str]] = {
    "technical": {
        "display_name": "Processo Técnico",
        "description": "Triagem → Entrevista Técnica → Entrevista Cultural → Proposta",
    },
    "executive": {
        "display_name": "Processo Executivo",
        "description": "Triagem → RH → Gestor → Diretoria → Proposta",
    },
    "operational": {
        "display_name": "Processo Operacional",
        "description": "Triagem → Entrevista RH → Proposta",
    },
    "mass_hiring": {
        "display_name": "Recrutamento em Massa",
        "description": "Triagem Automática → Proposta",
    },
    "intern": {
        "display_name": "Programa de Estágio",
        "description": "Triagem → Dinâmica de Grupo → Entrevista RH → Proposta",
    },
}


# ─────────────────────────────────────────────────────────────────────
# Internal: word-boundary matcher (avoids "Coordenador" matching "coo")
# ─────────────────────────────────────────────────────────────────────

_WORD_SPLIT_RE = re.compile(r"[\s\-_,./()|]+")


def _keyword_matches(combined: str, keyword: str) -> bool:
    """Return True if `keyword` appears in `combined` at a word boundary.

    For single-word keywords (no internal whitespace), use exact word match
    (set membership after splitting by whitespace/punctuation).

    For multi-word keywords (e.g. "head of", "general manager"), use
    bounded substring match (word boundaries on both sides).

    Both inputs are assumed lowercase already.
    """
    keyword = keyword.strip()
    if not keyword:
        return False

    if " " in keyword or "-" in keyword:
        # Multi-word keyword — bounded substring (regex word boundary).
        # \b doesn't work well with hyphens/accents, so we use explicit
        # whitespace/start/end markers.
        pattern = r"(?:^|[\s\-_,./()|])" + re.escape(keyword) + r"(?=$|[\s\-_,./()|])"
        return bool(re.search(pattern, combined))

    # Single-word keyword — exact word membership.
    words = set(_WORD_SPLIT_RE.split(combined))
    return keyword in words


# ─────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────

def suggest_template_type(
    job_title: str | None,
    department: str | None,
) -> TemplateType:
    """
    Deterministically map (job_title, department) → template_type.

    Returns one of: technical, executive, operational, mass_hiring, intern.
    Fail-safe default: 'technical' (engineering vagas são as mais comuns
    e tipicamente seguem o pipeline técnico).

    Priority order: intern > executive > mass_hiring > technical > operational.
    Higher-specificity templates win over lower ones (ex: "Diretor de
    Engenharia" matches both "executive" and "technical" — executive wins).

    Inputs are normalized to lowercase. None/empty inputs are treated as
    empty strings (still returns 'technical' fallback).

    Word boundaries: short keywords (e.g. "coo", "ml", "ai") are matched
    as exact words to avoid false positives like "Coordenador" matching
    "coo". Multi-word keywords (e.g. "head of") use regex with bounded
    delimiters.
    """
    combined = f"{job_title or ''} {department or ''}".lower()

    for ttype in ("intern", "executive", "mass_hiring", "technical", "operational"):
        keywords = TEMPLATE_TYPE_KEYWORDS.get(ttype, [])  # type: ignore[arg-type]
        for kw in keywords:
            if _keyword_matches(combined, kw):
                return ttype  # type: ignore[return-value]

    return "technical"


def get_template_metadata(template_type: TemplateType) -> dict[str, str]:
    """
    Return display metadata (display_name, description) for a template type.

    Used by frontend to render `WizardPipelineTemplateCard`. Caller is
    responsible for passing a valid `template_type` (Literal type-checked).
    """
    return TEMPLATE_DISPLAY.get(template_type, TEMPLATE_DISPLAY["technical"])


__all__ = [
    "TemplateType",
    "TEMPLATE_TYPE_KEYWORDS",
    "TEMPLATE_DISPLAY",
    "suggest_template_type",
    "get_template_metadata",
]
