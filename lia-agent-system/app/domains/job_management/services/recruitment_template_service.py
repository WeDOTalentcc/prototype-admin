"""
RecruitmentTemplateService — Onda 5 (Frente C.2).

Mapeamento de tipo de vaga (título + job_type hint) para template canônico
de processo seletivo. Funções puras — sem DB, sem efeitos colaterais.

5 tipos suportados:
  technical    — tech / knowledge workers (engenheiro, dev, PM, QA, …)
  executive    — diretores, C-level, VPs, heads
  operational  — atendente, auxiliar, suporte ao cliente
  mass_hiring  — contratação em volume (sobrescrito por job_type)
  intern       — estágio, trainee, aprendiz

Skill canônica: harness-engineering [guide computacional] — regra
determinística substitui LLM para classificação de template.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_TEMPLATE_TYPES: frozenset[str] = frozenset({
    "technical",
    "executive",
    "operational",
    "mass_hiring",
    "intern",
})

_EXECUTIVE_KWS: frozenset[str] = frozenset({
    "ceo", "cto", "cfo", "coo", "cmo", "ciso",
    "diretor", "diretora",
    "vp",
    "head",
    "c-level", "clevel",
    "presidente", "presidenta",
    "vice-presidente",
})

_INTERN_KWS: frozenset[str] = frozenset({
    "estágio", "estagio",
    "estagiário", "estagiaria", "estagiaria",
    "trainee",
    "aprendiz",
})

# Longer phrases checked before single keywords (most-specific-first order)
_OPERATIONAL_PHRASES: tuple[str, ...] = (
    "suporte ao cliente",
    "suporte a cliente",
    "técnico de suporte",
    "tecnico de suporte",
    "operador de caixa",
    "auxiliar administrativo",
    "auxiliar de",
)

_OPERATIONAL_KWS: frozenset[str] = frozenset({
    "atendente",
    "auxiliar",
})

# ---------------------------------------------------------------------------
# Default templates
# ---------------------------------------------------------------------------

_DEFAULT_TEMPLATES: dict[str, dict[str, Any]] = {
    "technical": {
        "name": "Template Técnico",
        "type": "technical",
        "stages": [
            "Triagem",
            "Teste Técnico",
            "Entrevista Técnica",
            "Entrevista Cultural",
            "Oferta",
        ],
        "description": "Para vagas técnicas e de conhecimento (dev, PM, QA, design…)",
    },
    "executive": {
        "name": "Template Executivo",
        "type": "executive",
        "stages": [
            "Triagem",
            "Entrevista Sênior",
            "Reunião com Board",
            "Proposta",
            "Oferta",
        ],
        "description": "Para posições de liderança, C-level e diretoria",
    },
    "operational": {
        "name": "Template Operacional",
        "type": "operational",
        "stages": [
            "Triagem",
            "Entrevista Básica",
            "Avaliação Prática",
            "Oferta",
        ],
        "description": "Para vagas operacionais, atendimento e suporte",
    },
    "mass_hiring": {
        "name": "Template Contratação em Massa",
        "type": "mass_hiring",
        "stages": [
            "Triagem Automatizada",
            "Dinâmica em Grupo",
            "Oferta",
        ],
        "description": "Para processos de alto volume",
    },
    "intern": {
        "name": "Template Estágio / Trainee",
        "type": "intern",
        "stages": [
            "Triagem",
            "Teste de Perfil",
            "Entrevista",
            "Oferta",
        ],
        "description": "Para estágios, trainees e programas de aprendiz",
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def suggest_template_type(
    title: str | None,
    job_type: str | None = None,
) -> str:
    """Infer the canonical template type from vacancy title and optional job_type hint.

    Pure function — no DB, no external calls, idempotent for same inputs.

    Args:
        title: Job title string (may be None or empty).
        job_type: Optional hint from the wizard (e.g. "mass_hiring" overrides title).

    Returns:
        One of SUPPORTED_TEMPLATE_TYPES.
    """
    # job_type hint wins over title analysis
    if job_type and job_type in SUPPORTED_TEMPLATE_TYPES:
        return job_type

    if not title:
        return "technical"  # safe canonical default

    t = title.lower().strip()

    # Check executive keywords
    if any(kw in t for kw in _EXECUTIVE_KWS):
        return "executive"

    # Check intern keywords
    if any(kw in t for kw in _INTERN_KWS):
        return "intern"

    # Operational: phrases first (longer match = more specific)
    if any(phrase in t for phrase in _OPERATIONAL_PHRASES):
        return "operational"
    if any(kw in t for kw in _OPERATIONAL_KWS):
        return "operational"

    # Default: technical (broad knowledge/tech worker category)
    return "technical"


def get_default_template(template_type: str) -> dict[str, Any] | None:
    """Return the default template configuration for a given type.

    Args:
        template_type: One of SUPPORTED_TEMPLATE_TYPES.

    Returns:
        Template dict with at least "name", "type", "stages" keys, or None.
    """
    return _DEFAULT_TEMPLATES.get(template_type)
