"""
Sprint 1A.8 — review_node deve aplicar company defaults efetivamente.

ONDE APLICAR: app/domains/job_creation/nodes/review_node.py
AÇÃO: Substituir a lógica que só registra defaults por uma que aplica os valores.
"""

import logging

logger = logging.getLogger(__name__)


async def review_node(state: dict, config: dict) -> dict:
    """
    Review node — checks readiness and APPLIES company defaults.

    Instead of just logging "defaults_applied" as strings,
    actually applies the values to state fields.
    """
    # Get company defaults from API
    api = state.get("api_client")
    defaults = {}

    if api:
        try:
            defaults = await api.get_company_defaults()
        except Exception as e:
            logger.warning(f"Failed to get company defaults: {e}")

    # APPLY defaults to state (not just register)
    defaults_applied = []

    if defaults.get("screening_mode") and not state.get("screening_mode"):
        state["screening_mode"] = defaults["screening_mode"]
        defaults_applied.append("screening_mode")

    if defaults.get("eligibility_questions") and not state.get("eligibility_questions"):
        state["eligibility_questions"] = defaults["eligibility_questions"]
        defaults_applied.append("eligibility_questions")

    if defaults.get("publish_platforms") and not state.get("platforms"):
        state["platforms"] = defaults["publish_platforms"]
        defaults_applied.append("publish_platforms")

    if defaults.get("auto_screen") is not None and state.get("auto_screen") is None:
        state["auto_screen"] = defaults["auto_screen"]
        defaults_applied.append("auto_screen")

    if defaults.get("contact_channels") and not state.get("contact_channels"):
        state["contact_channels"] = defaults["contact_channels"]
        defaults_applied.append("contact_channels")

    # Readiness checks
    checks = {
        "jd_approved": state.get("jd_approved", False),
        "questions_approved": state.get("questions_approved", False),
        "has_questions": len(state.get("approved_questions", [])) > 0,
        "has_seniority": bool(state.get("seniority")),
        "quality_score_ok": (state.get("quality_score", 0) >= 50),
        "has_eligibility": len(state.get("eligibility_questions", [])) > 0,
        "has_salary": state.get("salary_min") is not None,
    }

    missing = [k for k, v in checks.items() if not v]
    ready = len(missing) == 0

    state["readiness"] = {
        "ready": ready,
        "checks": checks,
        "missing": missing,
    }
    state["defaults_applied"] = defaults_applied

    # WS stage payload
    state["ws_stage_payload"] = {
        "type": "wizard_stage",
        "stage": "review",
        "data": {
            "readiness": state["readiness"],
            "defaults_applied": defaults_applied,
        },
        "completeness": 0.80,
        "requires_approval": False,
    }

    return state
