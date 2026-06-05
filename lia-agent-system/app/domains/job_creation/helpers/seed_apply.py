"""apply_seed_to_state - merge a JobCreationSeed into the flat JobCreationState.

Pure function (no IO). Used by the wizard entry (_start_wizard) when the
recruiter creates a vacancy from a source (template/vacancy). The state is
flat (parsed_title, parsed_seniority, salary_min, jd_raw, ...), so the seed is
mapped field-by-field.

Precedence: an existing truthy state value (user input / prior turn) wins over
the seed (user > seed). Provenance is recorded in state["seed_provenance"] so
the review surface can show "veio do template X" / "confira". ALWAYS_FRESH
fields (manager, headcount, deadline...) are never present in the seed, so they
are never touched here.
"""
from __future__ import annotations

from typing import Any

from app.domains.job_creation.schemas import JobCreationSeed

# JobCreationSeed field -> JobCreationState flat field.
_SEED_TO_STATE = {
    "title": "parsed_title",
    "seniority": "parsed_seniority",
    "work_model": "parsed_model",
    "department": "parsed_department",
    "location": "parsed_location",
    "employment_type": "parsed_employment_type",
    "salary_min": "salary_min",
    "salary_max": "salary_max",
}


def _compose_jd_raw(seed: JobCreationSeed) -> str:
    parts: list[str] = []
    if seed.description:
        parts.append(seed.description)
    if seed.responsibilities:
        parts.append(
            "Responsabilidades:\n" + "\n".join(f"- {r}" for r in seed.responsibilities)
        )
    if seed.requirements:
        parts.append("Requisitos:\n" + seed.requirements)
    if seed.skills:
        parts.append("Skills: " + ", ".join(seed.skills))
    if seed.nice_to_have:
        parts.append("Desejavel: " + seed.nice_to_have)
    return "\n\n".join(parts)


def apply_seed_to_state(
    state: dict[str, Any], seed: JobCreationSeed
) -> dict[str, Any]:
    """Merge seed into state in place and return it. Precedence: user > seed."""
    prov: dict[str, Any] = dict(state.get("seed_provenance") or {})

    for seed_field, state_field in _SEED_TO_STATE.items():
        val = getattr(seed, seed_field, None)
        if val in (None, "", [], {}):
            continue
        if state.get(state_field):  # user / prior value wins
            continue
        state[state_field] = val
        if seed_field in seed.provenance:
            prov[state_field] = seed.provenance[seed_field].model_dump()

    # Rich text fields feed the JD enrichment node via jd_raw (if recruiter
    # hasn't already provided their own JD text).
    if not state.get("jd_raw"):
        jd = _compose_jd_raw(seed)
        if jd:
            state["jd_raw"] = jd
            if seed.source is not None:
                prov["jd_raw"] = {
                    "source_type": seed.source.type,
                    "source_id": seed.source.id,
                    "source_name": seed.source.name,
                    "needs_review": False,
                }

    # Rich clone (PR-B2a): competencias + elegibilidade. competency_node
    # (_has_confirmed) e eligibility_node ja reusam quando presentes; os gates de
    # aprovacao continuam disparando (conservador). Precedencia user > seed.
    _RICH_MAP = {
        "technical_competencies": "confirmed_technical_competencies",
        "behavioral_competencies": "confirmed_behavioral_competencies",
        "eligibility_questions": "eligibility_questions",
        # WSI vai p/ chave de ESTACIONAMENTO (seed_wsi_questions), NAO
        # wsi_questions: o wsi_questions_node decide reaproveitar/gerar
        # perguntando ao recrutador (PR-B2b). Mapear direto pularia a escolha.
        "wsi_questions": "seed_wsi_questions",
        # JD enriquecida EXATA -> chave live; jd_enrichment_node tem reuse-guard
        # (usa se presente) e apresenta no HITL #1 p/ revisao (item 3).
        "jd_enriched": "jd_enriched",
    }
    for _seed_field, _state_field in _RICH_MAP.items():
        _val = getattr(seed, _seed_field, None)
        if not _val:
            continue
        if state.get(_state_field):  # user / prior value wins
            continue
        state[_state_field] = _val
        if _seed_field in seed.provenance:
            prov[_state_field] = seed.provenance[_seed_field].model_dump()

    if seed.source is not None:
        state["seed_source"] = seed.source.model_dump()
    if prov:
        state["seed_provenance"] = prov
    return state
