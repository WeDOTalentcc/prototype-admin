"""
Deterministic builder: JD enriched dict + wizard state -> HybridSearchRequest search_spec.
No LLM. Missing field -> omitted. Called by wizard calibration (D1+D2 Fase D).
"""
from __future__ import annotations

from typing import Any

__all__ = ["build_search_spec_from_jd"]


def build_search_spec_from_jd(jd: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Build a search_spec dict from an enriched JD + wizard state.

    Deterministic, no LLM calls. Compatible with HybridSearchRequest.search_spec.
    Missing/empty fields are omitted — never fabricated.

    Fields covered (D1+D2):
        location / location_city / location_state  <- state parsed_location
        seniority                                  <- state seniority_resolved / parsed_seniority
        work_model                                 <- state parsed_work_model / parsed_model
        required_skills                            <- jd skills_obrigatorias
        preferred_skills                           <- jd skills_desejaveis
        languages                                  <- state parsed_languages (intake D1)

    Out of scope (V2):
        industries / years_experience_min  -- upstream extraction gap
        behavioral competencies            -- soft_skills orphaned in local search path
    """
    spec: dict[str, Any] = {}

    # location
    loc = state.get("parsed_location") or state.get("parsed_city")
    if isinstance(loc, dict):
        city    = (loc.get("city") or "").strip()
        st      = (loc.get("state") or "").strip()
        country = (loc.get("country") or "").strip()
        loc_str = ", ".join(x for x in [city, st] if x) or None
        if loc_str:
            spec["location"] = loc_str
        if city:
            spec["location_city"] = city
        if st:
            spec["location_state"] = st
        if country:
            spec["location_country"] = country
    elif isinstance(loc, str) and loc.strip():
        spec["location"] = loc.strip()

    # seniority
    seniority = (
        state.get("seniority_resolved") or state.get("parsed_seniority") or ""
    ).strip()
    if seniority:
        spec["seniority"] = seniority

    # work_model — PT accepted; to_pearch_custom_filters() maps to EN
    work_model = (
        state.get("parsed_work_model") or state.get("parsed_model") or ""
    ).strip()
    if work_model:
        spec["work_model"] = work_model

    # required_skills: tecnicas obrigatorias
    req = [
        (x.get("skill", "") if isinstance(x, dict) else str(x)).strip()
        for x in (jd.get("skills_obrigatorias") or [])
        if x
    ]
    req = [s for s in req if s]
    if req:
        spec["required_skills"] = req

    # preferred_skills: tecnicas desejaveis
    # NOT sent to Pearch (to_pearch_custom_filters ignores preferred_skills).
    # Retained for future local skills filter (V2).
    pref = [
        s.strip()
        for s in (jd.get("skills_desejaveis") or [])
        if isinstance(s, str) and s.strip()
    ]
    if pref:
        spec["preferred_skills"] = pref

    # languages — requires intake D1 fix to populate state["parsed_languages"]
    langs = [
        s.strip()
        for s in (state.get("parsed_languages") or [])
        if isinstance(s, str) and s.strip()
    ]
    if langs:
        spec["languages"] = langs

    return spec
