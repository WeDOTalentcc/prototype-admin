"""constants canonical — PR-17 extract (2026-05-26 ONDA 3 follow-up).

Movido de graph.py para reduzir LOC abaixo de 1500.
Source-of-truth: ver docstrings inline para histórico (Tasks #1055, #1062,
PR-8 ONDA 3 / F-3.3, PR-11 F-4.7).
"""

from pathlib import Path
from typing import Dict

# ── PR-11 F-4.7: magic numbers canonical ──
# Default question distribution para WSI quando state nao fornece (fallback
# defensivo). Source: WSI_METHODOLOGY_COMPLETE_v2.md "compact mode / pleno"
# — mesmo valor canonical retornado por _get_question_distribution() quando
# nao acha match na tabela. Centralizar evita drift (5 sites pre-PR-11).
WSI_DEFAULT_DISTRIBUTION_COMPACT_PLENO: Dict[str, int] = {
    "technical": 5,
    "behavioral": 2,
}

# Task #1055 — pipeline template suggestion (heurístico determinístico)
_PIPELINE_TEMPLATE_IDS: tuple[str, ...] = (
    "technical", "executive", "operational", "mass_hiring", "intern",
)
_EXECUTIVE_KEYWORDS = (
    "director", "diretor", "vp", "vice", "cto", "cfo", "ceo", "head",
    "gerente geral", "c-level", "chief",
)
_TECHNICAL_KEYWORDS = (
    "developer", "desenvolvedor", "engineer", "engenheiro", "programador",
    "software", "data", "devops", "sre", "backend", "frontend", "fullstack",
    "full-stack", "tech lead", "arquiteto",
)
_OPERATIONAL_KEYWORDS = (
    "operador", "auxiliar", "assistente", "atendente", "vendedor",
    "recepcionista", "caixa", "estoquista",
)
_INTERN_KEYWORDS = (
    # `estagi` cobre "estágio", "estagio", "estagiário", "estagiaria".
    "estagi", "trainee", "jovem aprendiz", "intern",
)

# Task #1068 — wizard fallback observability: nodes com fallback determinístico
_WIZARD_FALLBACK_NODES: tuple[str, ...] = (
    "jd_enrichment", "bigfive", "salary", "wsi_questions",
)

# T6 (Task #1088) — review gate destinations allowlist
# Allowlist canônica de canais ATS aceitos por ``configure_destinations``.
# Mantém-se sincronizada com ``Literal[...]`` no system_prompt YAML
# (gate_review.yaml).
_REVIEW_DESTINATIONS_ALLOWLIST: frozenset[str] = frozenset({
    "site_carreiras", "gupy", "pandape", "linkedin",
})

# Mapeia ``target_section`` (do request_changes) → nó destino do graph.
_REVIEW_TARGET_SECTION_TO_NODE: dict[str, str] = {
    "title": "jd_enrichment",
    "description": "jd_enrichment",
    "questions": "wsi_questions",
    "salary": "salary",
    "pipeline": "eligibility",
    # NOTE: "destinations" propositalmente AUSENTE — handled inline.
}

# T6: target_sections válidos para ``request_changes``
_REVIEW_VALID_TARGET_SECTIONS: frozenset[str] = frozenset({
    "title", "description", "questions", "salary", "pipeline", "destinations",
})

# WSI F5 deterministic distribution -- canonical config em YAML.
# PR-8 ONDA 3 / F-3.3: extraido de hardcoded dict para
# app/prompts/job_creation/wsi_question_distribution.yaml.
# Sensor: tests/contract/test_wsi_question_distribution_taxonomy.py
_WSI_QUESTION_DISTRIBUTION_FILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "prompts" / "job_creation" / "wsi_question_distribution.yaml"
)
