"""
JobCreationGraph — LangGraph state machine for the Wizard WSI pipeline.

Maps WSI Bloco A (F1-F6) + publish + calibration + handoff into a
conversational wizard flow with 2 HITL approval points.

Pattern follows scheduling/graph.py: StateGraph, conditional edges,
checkpointer for session persistence, singleton access.

HITL points:
  - jd_enrichment (F1): recruiter approves enriched JD
  - wsi_questions (F6): recruiter approves generated questions
"""

import logging
import time
from typing import Any, Dict, Optional

from langgraph.graph import StateGraph, END

from app.domains.job_creation.state import (
    JobCreationState,
    calculate_completeness,
)
from app.domains.job_creation.services.jd_enrichment import JdEnrichmentService
from app.domains.job_creation.services.seniority_resolver import resolve_seniority
from app.domains.job_creation.services.wsi_question_generator import WSIQuestionGenerator
from app.domains.job_creation.api_client import JobCreationAPIClient

logger = logging.getLogger(__name__)

# Shared service instances (lazy-initialized in nodes)
_jd_service: Optional[JdEnrichmentService] = None
_wsi_generator: Optional[WSIQuestionGenerator] = None
_api_client: Optional[JobCreationAPIClient] = None


def _get_jd_service() -> JdEnrichmentService:
    global _jd_service
    if _jd_service is None:
        _jd_service = JdEnrichmentService()
    return _jd_service


def _get_wsi_generator() -> WSIQuestionGenerator:
    global _wsi_generator
    if _wsi_generator is None:
        _wsi_generator = WSIQuestionGenerator()
    return _wsi_generator


def _get_api_client(state: dict) -> JobCreationAPIClient:
    """Get API client with auth context from state."""
    global _api_client
    # Recreate if auth token changes
    token = state.get("auth_token", "")
    if _api_client is None or getattr(_api_client, "_last_token", "") != token:
        # Build minimal context for auth
        ctx = type("Ctx", (), {
            "auth_token": token,
            "track_api_call": lambda *a, **k: None,
        })()
        _api_client = JobCreationAPIClient(context=ctx)
        _api_client._last_token = token
    return _api_client


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------

def intake_node(state: JobCreationState) -> JobCreationState:
    """Pre-F1: Parse user input to extract job title, department, seniority, location."""
    t0 = time.time()
    query = state.get("user_query", "") or state.get("raw_input", "")
    logger.info("[JobCreation:intake] query=%s", query[:80])

    # LLM structured extraction will be implemented in B.1
    # For now, pass through to jd_enrichment with raw input
    updates: Dict[str, Any] = {
        "current_stage": "intake",
        "raw_input": query,
        "intake_confidence": 0.0,
        "stage_history": (state.get("stage_history") or []) + ["intake"],
        "completeness": calculate_completeness("intake"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "intake",
            "data": {"raw_input": query},
            "completeness": calculate_completeness("intake"),
            "requires_approval": False,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:intake] %0.fms", elapsed)
    return {**state, **updates}


def jd_enrichment_node(state: JobCreationState) -> JobCreationState:
    """F1: Call JdEnrichmentService to enrich JD + calculate quality score.

    This is HITL point 1 — recruiter must approve the enriched JD.
    """
    t0 = time.time()
    logger.info("[JobCreation:jd_enrichment] Starting F1")

    raw_input = state.get("raw_input", "")
    jd_raw = state.get("jd_raw") or raw_input

    # If already enriched and approved, skip re-enrichment (resume path)
    if state.get("jd_approved") is not None and state.get("jd_enriched"):
        jd_enriched_dict = state["jd_enriched"]
        jd_quality_score = state.get("jd_quality_score", 0.0)
        jd_quality_warnings = state.get("jd_quality_warnings", [])
    else:
        # Call JdEnrichmentService (F1.C LLM enrichment)
        service = _get_jd_service()
        enriched_obj, jd_quality_score, jd_quality_warnings = service.enrich(
            jd_raw=jd_raw,
            title=state.get("parsed_title", ""),
            seniority=state.get("parsed_seniority", ""),
            department=state.get("parsed_department", ""),
        )
        jd_enriched_dict = enriched_obj.model_dump()

    updates: Dict[str, Any] = {
        "current_stage": "jd_enrichment",
        "jd_raw": jd_raw,
        "jd_enriched": jd_enriched_dict,
        "jd_quality_score": jd_quality_score,
        "jd_quality_warnings": jd_quality_warnings,
        "stage_history": (state.get("stage_history") or []) + ["jd_enrichment"],
        "completeness": calculate_completeness("jd_enrichment"),
        "requires_approval": True,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "jd_enrichment",
            "data": {
                "jd_raw": jd_raw,
                "jd_enriched": jd_enriched_dict,
                "quality_score": jd_quality_score,
                "quality_warnings": jd_quality_warnings,
            },
            "completeness": calculate_completeness("jd_enrichment"),
            "requires_approval": True,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:jd_enrichment] score=%.1f | %0.fms", jd_quality_score, elapsed)
    return {**state, **updates}


def bigfive_node(state: JobCreationState) -> JobCreationState:
    """F2+F3: Extract Big Five profile from enriched JD + rank traits.

    F2: LLM extraction (temp=0.1)
    F3: Deterministic trait ranking formula
    """
    t0 = time.time()
    logger.info("[JobCreation:bigfive] Starting F2+F3")

    from app.domains.job_creation.schemas import EnrichedJobDescription

    jd_enriched_dict = state.get("jd_enriched", {})
    enriched = EnrichedJobDescription(**jd_enriched_dict) if jd_enriched_dict else None

    generator = _get_wsi_generator()

    if enriched:
        # F2: Extract Big Five via LLM
        bigfive_obj = generator.extract_bigfive(enriched)
        bigfive_profile = bigfive_obj.model_dump()

        # F3: Rank traits (deterministic)
        seniority = state.get("seniority_resolved") or state.get("parsed_seniority") or "pleno"
        trait_rankings = generator.rank_traits(bigfive_obj, seniority)
    else:
        bigfive_profile = state.get("bigfive_profile")
        trait_rankings = state.get("trait_rankings", [])

    updates: Dict[str, Any] = {
        "current_stage": "bigfive",
        "bigfive_profile": bigfive_profile,
        "trait_rankings": trait_rankings,
        "stage_history": (state.get("stage_history") or []) + ["bigfive"],
        "completeness": calculate_completeness("bigfive"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "bigfive",
            "data": {
                "bigfive_profile": bigfive_profile,
                "trait_rankings": trait_rankings,
            },
            "completeness": calculate_completeness("bigfive"),
            "requires_approval": False,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:bigfive] %0.fms", elapsed)
    return {**state, **updates}


def salary_node(state: JobCreationState) -> JobCreationState:
    """Validate salary range vs market benchmark."""
    t0 = time.time()
    logger.info("[JobCreation:salary] Starting salary validation")

    updates: Dict[str, Any] = {
        "current_stage": "salary",
        "stage_history": (state.get("stage_history") or []) + ["salary"],
        "completeness": calculate_completeness("salary"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "salary",
            "data": {
                "salary_min": state.get("salary_min"),
                "salary_max": state.get("salary_max"),
                "salary_currency": state.get("salary_currency", "BRL"),
                "benefits": state.get("benefits", []),
                "benchmark": state.get("salary_benchmark"),
            },
            "completeness": calculate_completeness("salary"),
            "requires_approval": False,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:salary] %0.fms", elapsed)
    return {**state, **updates}


def competency_node(state: JobCreationState) -> JobCreationState:
    """F4+F5: Resolve seniority + calculate question distribution.

    F4: Deterministic seniority resolution (5 signals)
    F5: Deterministic question distribution table
    Recruiter chooses screening mode (compact 7q / full 12q).
    """
    t0 = time.time()
    logger.info("[JobCreation:competency] Starting F4+F5")

    jd_enriched = state.get("jd_enriched", {})
    skills = [s.get("skill", "") for s in jd_enriched.get("skills_obrigatorias", [])]

    # F4: Resolve seniority using 5 signals
    seniority_result = resolve_seniority(
        explicit_seniority=state.get("parsed_seniority"),
        job_title=jd_enriched.get("titulo_padronizado") or state.get("parsed_title"),
        job_description=jd_enriched.get("about_role", ""),
        skills=skills,
        salary_min=state.get("salary_min"),
    )

    seniority = seniority_result.final_level
    screening_mode = state.get("screening_mode")

    # F5: Question distribution by mode (deterministic)
    distribution = None
    if screening_mode and seniority:
        distribution = _get_question_distribution(screening_mode, seniority)

    # Build competency tree from enriched JD
    competency_tree = []
    for s in jd_enriched.get("skills_obrigatorias", []):
        competency_tree.append({
            "skill": s.get("skill", ""),
            "contexto": s.get("contexto", ""),
            "block": "technical",
        })
    for c in jd_enriched.get("competencias_comportamentais", []):
        competency_tree.append({
            "skill": c.get("competencia", ""),
            "contexto": c.get("contexto", ""),
            "block": "behavioral",
            "trait": c.get("trait_big_five", ""),
        })

    updates: Dict[str, Any] = {
        "current_stage": "competency",
        "seniority_resolved": seniority,
        "seniority_signals": seniority_result.signals_used,
        "question_distribution": distribution,
        "competency_tree": competency_tree,
        "stage_history": (state.get("stage_history") or []) + ["competency"],
        "completeness": calculate_completeness("competency"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "competency",
            "data": {
                "seniority": seniority,
                "seniority_display": seniority_result.display_name,
                "seniority_confidence": seniority_result.confidence,
                "seniority_signals": seniority_result.signals_used,
                "screening_mode": screening_mode,
                "distribution": distribution,
                "competency_tree": competency_tree,
            },
            "completeness": calculate_completeness("competency"),
            "requires_approval": False,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:competency] seniority=%s mode=%s | %0.fms", seniority, screening_mode, elapsed)
    return {**state, **updates}


def wsi_questions_node(state: JobCreationState) -> JobCreationState:
    """F6: Generate WSI screening questions via LLM.

    This is HITL point 2 — recruiter must approve all questions.

    WSI absolute rules enforced:
    - CBI only (no hypothetical questions)
    - No cultural fit questions
    - Min questions per distribution table (F5)
    """
    t0 = time.time()
    logger.info("[JobCreation:wsi_questions] Starting F6")

    from app.domains.job_creation.schemas import EnrichedJobDescription

    # If already approved, skip re-generation (resume path)
    if state.get("questions_approved") is not None and state.get("wsi_questions"):
        questions_data = state["wsi_questions"]
    else:
        jd_enriched_dict = state.get("jd_enriched", {})
        enriched = EnrichedJobDescription(**jd_enriched_dict) if jd_enriched_dict else None
        distribution = state.get("question_distribution", {"technical": 5, "behavioral": 2})
        seniority = state.get("seniority_resolved", "pleno")
        trait_rankings = state.get("trait_rankings", [])

        if enriched:
            generator = _get_wsi_generator()
            question_objs = generator.generate_questions(
                enriched=enriched,
                seniority=seniority,
                distribution=distribution,
                trait_rankings=trait_rankings,
            )
            questions_data = [q.model_dump() for q in question_objs]
        else:
            questions_data = []

    updates: Dict[str, Any] = {
        "current_stage": "wsi_questions",
        "wsi_questions": questions_data,
        "stage_history": (state.get("stage_history") or []) + ["wsi_questions"],
        "completeness": calculate_completeness("wsi_questions"),
        "requires_approval": True,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "wsi_questions",
            "data": {
                "questions": questions_data,
                "screening_mode": state.get("screening_mode"),
                "distribution": state.get("question_distribution"),
            },
            "completeness": calculate_completeness("wsi_questions"),
            "requires_approval": True,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:wsi_questions] %d questions | %0.fms", len(questions_data), elapsed)
    return {**state, **updates}


def eligibility_node(state: JobCreationState) -> JobCreationState:
    """Pre-screening: yes/no eliminatory questions configured by recruiter."""
    t0 = time.time()
    logger.info("[JobCreation:eligibility] Starting eligibility questions")

    questions = state.get("eligibility_questions", [])

    updates: Dict[str, Any] = {
        "current_stage": "eligibility",
        "stage_history": (state.get("stage_history") or []) + ["eligibility"],
        "completeness": calculate_completeness("eligibility"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "eligibility",
            "data": {"questions": questions},
            "completeness": calculate_completeness("eligibility"),
            "requires_approval": False,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:eligibility] %d questions | %0.fms", len(questions), elapsed)
    return {**state, **updates}


def review_node(state: JobCreationState) -> JobCreationState:
    """Readiness check + apply company defaults from Settings.

    Calls api_client.get_company_defaults() to load recruitment policies,
    default eligibility questions, screening mode defaults, etc.
    """
    t0 = time.time()
    logger.info("[JobCreation:review] Starting readiness check")

    # Load company defaults if not already applied
    defaults_applied = list(state.get("company_defaults_applied", []))
    if not defaults_applied:
        try:
            api = _get_api_client(state)
            workspace_id = state.get("workspace_id", 0)
            if workspace_id:
                resp = api.get_company_defaults(workspace_id)
                if resp.success and resp.data:
                    defaults = resp.data
                    # Apply defaults that aren't already set
                    if not state.get("screening_mode") and defaults.get("default_screening_mode"):
                        defaults_applied.append("screening_mode")
                    if not state.get("publish_platforms") and defaults.get("default_platforms"):
                        defaults_applied.append("publish_platforms")
                    if not state.get("eligibility_questions") and defaults.get("default_eligibility"):
                        defaults_applied.append("eligibility_questions")
                    logger.info("[JobCreation:review] Loaded %d company defaults", len(defaults_applied))
        except Exception as e:
            logger.warning("[JobCreation:review] Failed to load company defaults: %s", e)

    readiness = _build_readiness_check(state)

    updates: Dict[str, Any] = {
        "current_stage": "review",
        "readiness_check": readiness,
        "company_defaults_applied": defaults_applied,
        "stage_history": (state.get("stage_history") or []) + ["review"],
        "completeness": calculate_completeness("review"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "review",
            "data": {
                "readiness": readiness,
                "defaults_applied": defaults_applied,
            },
            "completeness": calculate_completeness("review"),
            "requires_approval": False,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:review] ready=%s | %0.fms", readiness.get("ready"), elapsed)
    return {**state, **updates}


def publish_node(state: JobCreationState) -> JobCreationState:
    """Publish job via Rails API + save screening config + get share link.

    Steps:
    1. Create job in Rails (if no job_id yet)
    2. Save WSI screening questions + eligibility
    3. Publish to selected platforms
    4. Get share link
    5. Auto-dispatch screening if enabled

    Governance: circuit breaker wraps all API calls.
    """
    t0 = time.time()
    logger.info("[JobCreation:publish] Starting publish")

    api = _get_api_client(state)
    job_id = state.get("job_id")
    job_uid = state.get("job_uid")
    share_link = state.get("share_link")
    error = None

    try:
        from app.services.circuit_breaker import circuit_breaker_call, CircuitBreakerOpenError
        cb_wrap = lambda fn, *a, **kw: circuit_breaker_call(fn, *a, circuit_key="job_creation:publish", **kw)
    except ImportError:
        cb_wrap = lambda fn, *a, **kw: fn(*a, **kw)

    try:
        # Step 1: Create job if not yet created
        if not job_id:
            jd = state.get("jd_enriched", {})
            job_data = {
                "title": jd.get("titulo_padronizado", state.get("parsed_title", "")),
                "description": jd.get("about_role", ""),
                "seniority": state.get("seniority_resolved", ""),
                "department": state.get("parsed_department", ""),
                "location": state.get("parsed_location", ""),
                "work_model": state.get("parsed_model", ""),
                "salary_min": state.get("salary_min"),
                "salary_max": state.get("salary_max"),
                "salary_currency": state.get("salary_currency", "BRL"),
                "benefits": state.get("benefits", []),
                "technical_requirements": jd.get("skills_obrigatorias", []),
                "behavioral_competencies": jd.get("competencias_comportamentais", []),
                "responsibilities": jd.get("responsabilidades", []),
            }
            resp = cb_wrap(api.create_job, job_data)
            if resp.success and resp.data:
                data = resp.data.get("data", resp.data)
                attrs = data.get("attributes", data)
                job_id = attrs.get("id") or data.get("id")
                job_uid = attrs.get("uid") or data.get("uid")
                logger.info("[JobCreation:publish] Job created: id=%s", job_id)

        if job_id:
            # Step 2: Save screening config (WSI questions + eligibility)
            questions = state.get("wsi_questions", [])
            eligibility = state.get("eligibility_questions", [])
            mode = state.get("screening_mode", "compact")
            if questions:
                cb_wrap(api.save_screening_config, job_id, questions, mode, eligibility)

            # Step 3: Publish to platforms
            platforms = state.get("publish_platforms", ["website"])
            sourcing_mode = state.get("sourcing_mode", "local")
            cb_wrap(api.publish_job, job_id, platforms, sourcing_mode)

            # Step 4: Get share link
            link_resp = cb_wrap(api.get_share_link, job_id)
            if link_resp.success and link_resp.data:
                share_link = link_resp.data.get("share_link") or link_resp.data.get("public_url")

    except Exception as e:
        error = str(e)
        logger.error("[JobCreation:publish] Error: %s", e)

    updates: Dict[str, Any] = {
        "current_stage": "publish",
        "job_id": job_id,
        "job_uid": job_uid,
        "share_link": share_link,
        "error": error,
        "stage_history": (state.get("stage_history") or []) + ["publish"],
        "completeness": calculate_completeness("publish"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "publish",
            "data": {
                "job_id": job_id,
                "platforms": state.get("publish_platforms", []),
                "sourcing_mode": state.get("sourcing_mode"),
                "contact_channels": state.get("contact_channels", []),
                "share_link": share_link,
                "auto_screen": state.get("auto_screen_enabled", True),
                "error": error,
            },
            "completeness": calculate_completeness("publish"),
            "requires_approval": False,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:publish] job_id=%s share=%s | %0.fms", job_id, bool(share_link), elapsed)
    return {**state, **updates}


def calibration_node(state: JobCreationState) -> JobCreationState:
    """Present 3+ candidates for calibration (approve/reject).

    Fetches calibration candidates from Rails API if not already loaded.
    """
    t0 = time.time()
    logger.info("[JobCreation:calibration] Starting calibration")

    candidates = list(state.get("calibration_candidates", []))
    job_id = state.get("job_id")

    # Fetch candidates from API if we have a job_id but no candidates yet
    if job_id and not candidates:
        try:
            api = _get_api_client(state)
            resp = api.get_calibration_candidates(job_id, limit=5)
            if resp.success and resp.data:
                raw = resp.data.get("candidates", resp.data.get("data", []))
                for c in raw:
                    attrs = c.get("attributes", c)
                    candidates.append({
                        "id": str(attrs.get("id", "")),
                        "name": attrs.get("name", ""),
                        "current_title": attrs.get("current_title", ""),
                        "current_company": attrs.get("current_company", ""),
                        "match_score": float(attrs.get("match_score", 0)),
                        "match_criteria": attrs.get("match_criteria", []),
                    })
                logger.info("[JobCreation:calibration] Fetched %d candidates from API", len(candidates))
        except Exception as e:
            logger.warning("[JobCreation:calibration] Failed to fetch candidates: %s", e)

    threshold = state.get("calibration_threshold", 3)
    approved_count = sum(1 for c in candidates if c.get("decision") == "approved")
    complete = approved_count >= threshold

    updates: Dict[str, Any] = {
        "current_stage": "calibration",
        "calibration_complete": complete,
        "stage_history": (state.get("stage_history") or []) + ["calibration"],
        "completeness": calculate_completeness("calibration"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "calibration",
            "data": {
                "candidates": candidates,
                "threshold": threshold,
                "approved_count": approved_count,
                "complete": complete,
            },
            "completeness": calculate_completeness("calibration"),
            "requires_approval": False,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:calibration] %d/%d approved | %0.fms", approved_count, threshold, elapsed)
    return {**state, **updates}


def handoff_node(state: JobCreationState) -> JobCreationState:
    """Navigate recruiter to job page. Inform share link. Chat becomes job assistant."""
    t0 = time.time()
    logger.info("[JobCreation:handoff] Starting handoff")

    job_id = state.get("job_id")
    share_link = state.get("share_link")
    handoff_url = f"/jobs/{job_id}" if job_id else None

    updates: Dict[str, Any] = {
        "current_stage": "handoff",
        "handoff_url": handoff_url,
        "stage_history": (state.get("stage_history") or []) + ["handoff"],
        "completeness": 1.0,
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "handoff",
            "data": {
                "job_id": job_id,
                "handoff_url": handoff_url,
                "share_link": share_link,
            },
            "completeness": 1.0,
            "requires_approval": False,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:handoff] url=%s | %0.fms", handoff_url, elapsed)
    return {**state, **updates}


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

def route_after_jd(state: JobCreationState) -> str:
    """After JD enrichment: if HITL pending (not yet approved), END (wait for user).
    If approved and quality >= 50, proceed to bigfive.
    If quality < 30, loop back (recruiter must improve JD).
    """
    approved = state.get("jd_approved")
    quality = state.get("jd_quality_score", 0.0)

    if approved is None:
        # Waiting for recruiter approval — END to return control
        logger.info("[JobCreation:route] jd_enrichment -> END (awaiting approval)")
        return "end"

    if not approved:
        # Recruiter rejected — they'll provide new input, restart from intake
        logger.info("[JobCreation:route] jd_enrichment -> intake (rejected)")
        return "intake"

    if quality < 30:
        logger.info("[JobCreation:route] jd_enrichment -> END (quality %.1f < 30, blocked)", quality)
        return "end"

    logger.info("[JobCreation:route] jd_enrichment -> bigfive (approved, quality=%.1f)", quality)
    return "bigfive"


def route_after_competency(state: JobCreationState) -> str:
    """After competency: need screening_mode chosen to proceed."""
    if not state.get("screening_mode"):
        logger.info("[JobCreation:route] competency -> END (awaiting mode selection)")
        return "end"
    logger.info("[JobCreation:route] competency -> wsi_questions")
    return "wsi_questions"


def route_after_questions(state: JobCreationState) -> str:
    """After WSI questions: HITL point 2 — recruiter must approve all questions."""
    approved = state.get("questions_approved")

    if approved is None:
        logger.info("[JobCreation:route] wsi_questions -> END (awaiting approval)")
        return "end"

    if not approved:
        # Recruiter wants to regenerate — loop back to questions
        logger.info("[JobCreation:route] wsi_questions -> wsi_questions (regenerate)")
        return "wsi_questions"

    logger.info("[JobCreation:route] wsi_questions -> eligibility")
    return "eligibility"


def route_after_review(state: JobCreationState) -> str:
    """After review: check readiness."""
    readiness = state.get("readiness_check", {})
    if readiness.get("ready"):
        logger.info("[JobCreation:route] review -> publish")
        return "publish"
    logger.info("[JobCreation:route] review -> END (not ready)")
    return "end"


def route_after_publish(state: JobCreationState) -> str:
    """After publish: go to calibration if job was published."""
    if state.get("job_id"):
        logger.info("[JobCreation:route] publish -> calibration")
        return "calibration"
    logger.info("[JobCreation:route] publish -> END (publish failed)")
    return "end"


def route_after_calibration(state: JobCreationState) -> str:
    """After calibration: if threshold met, handoff."""
    if state.get("calibration_complete"):
        logger.info("[JobCreation:route] calibration -> handoff")
        return "handoff"
    logger.info("[JobCreation:route] calibration -> END (awaiting more calibration)")
    return "end"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _get_question_distribution(mode: str, seniority: str) -> Dict[str, int]:
    """WSI F5 deterministic distribution tables.

    Source: WSI_METHODOLOGY_COMPLETE_v2.md — canonical values.
    These MUST match the methodology exactly; do not change without updating the doc.
    """
    # Compact mode (7 questions total) — from methodology table
    compact_dist = {
        "estagiario": {"technical": 5, "behavioral": 2},
        "junior": {"technical": 5, "behavioral": 2},
        "pleno": {"technical": 5, "behavioral": 2},
        "senior": {"technical": 4, "behavioral": 3},
        "lead": {"technical": 3, "behavioral": 4},
        "principal": {"technical": 4, "behavioral": 3},
        "staff": {"technical": 4, "behavioral": 3},
        "diretor": {"technical": 3, "behavioral": 4},
    }
    # Full mode (12 questions total) — from methodology table
    full_dist = {
        "estagiario": {"technical": 9, "behavioral": 3},
        "junior": {"technical": 9, "behavioral": 3},
        "pleno": {"technical": 8, "behavioral": 4},
        "senior": {"technical": 7, "behavioral": 5},
        "lead": {"technical": 7, "behavioral": 5},
        "principal": {"technical": 7, "behavioral": 5},
        "staff": {"technical": 7, "behavioral": 5},
        "diretor": {"technical": 7, "behavioral": 5},
    }

    table = compact_dist if mode == "compact" else full_dist
    seniority_key = (
        seniority.lower()
        .replace("sênior", "senior")
        .replace("júnior", "junior")
        .replace("estágio", "estagiario")
        .replace("estagiário", "estagiario")
    )

    return table.get(seniority_key, table.get("pleno", {"technical": 5, "behavioral": 2}))


def _build_readiness_check(state: JobCreationState) -> Dict[str, Any]:
    """Check if all required fields are present for publishing."""
    checks = {
        "jd_approved": bool(state.get("jd_approved")),
        "questions_approved": bool(state.get("questions_approved")),
        "has_questions": len(state.get("wsi_questions", [])) > 0,
        "has_seniority": bool(state.get("seniority_resolved")),
        "quality_score_ok": (state.get("jd_quality_score", 0) >= 50),
    }

    ready = all(checks.values())
    missing = [k for k, v in checks.items() if not v]

    return {
        "ready": ready,
        "checks": checks,
        "missing": missing,
    }


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def _get_checkpointer():
    try:
        from app.services.checkpointer import get_checkpointer
        return get_checkpointer()
    except Exception as e:
        logger.warning("[JobCreationGraph] Checkpointer unavailable: %s", e)
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()


def create_job_creation_graph(checkpointer=None) -> StateGraph:
    """Build the job creation wizard graph.

    Flow: intake -> jd_enrichment --(HITL)--> bigfive -> salary -> competency
          -> wsi_questions --(HITL)--> eligibility -> review -> publish
          -> calibration -> handoff -> END
    """
    builder = StateGraph(JobCreationState)

    # Add all nodes
    builder.add_node("intake", intake_node)
    builder.add_node("jd_enrichment", jd_enrichment_node)
    builder.add_node("bigfive", bigfive_node)
    builder.add_node("salary", salary_node)
    builder.add_node("competency", competency_node)
    builder.add_node("wsi_questions", wsi_questions_node)
    builder.add_node("eligibility", eligibility_node)
    builder.add_node("review", review_node)
    builder.add_node("publish", publish_node)
    builder.add_node("calibration", calibration_node)
    builder.add_node("handoff", handoff_node)

    # Entry point
    builder.set_entry_point("intake")

    # Linear edges (no conditional routing needed)
    builder.add_edge("intake", "jd_enrichment")

    # HITL point 1: JD enrichment
    builder.add_conditional_edges(
        "jd_enrichment",
        route_after_jd,
        {
            "bigfive": "bigfive",
            "intake": "intake",
            "end": END,
        },
    )

    # F2+F3 -> salary -> F4+F5
    builder.add_edge("bigfive", "salary")
    builder.add_edge("salary", "competency")

    # F4+F5: needs screening mode
    builder.add_conditional_edges(
        "competency",
        route_after_competency,
        {
            "wsi_questions": "wsi_questions",
            "end": END,
        },
    )

    # HITL point 2: WSI questions
    builder.add_conditional_edges(
        "wsi_questions",
        route_after_questions,
        {
            "eligibility": "eligibility",
            "wsi_questions": "wsi_questions",
            "end": END,
        },
    )

    # Eligibility -> Review
    builder.add_edge("eligibility", "review")

    # Review: check readiness
    builder.add_conditional_edges(
        "review",
        route_after_review,
        {
            "publish": "publish",
            "end": END,
        },
    )

    # Publish -> Calibration
    builder.add_conditional_edges(
        "publish",
        route_after_publish,
        {
            "calibration": "calibration",
            "end": END,
        },
    )

    # Calibration -> Handoff
    builder.add_conditional_edges(
        "calibration",
        route_after_calibration,
        {
            "handoff": "handoff",
            "end": END,
        },
    )

    # Handoff -> Done
    builder.add_edge("handoff", END)

    # Compile with checkpointer
    if checkpointer is not None:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()


# ---------------------------------------------------------------------------
# Singleton access (same pattern as SchedulingGraph)
# ---------------------------------------------------------------------------

class JobCreationGraph:
    _instance = None
    _graph = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._graph = create_job_creation_graph(
                checkpointer=_get_checkpointer()
            )
        return cls._instance

    @property
    def graph(self):
        return self._graph

    def invoke(self, state: JobCreationState, thread_id: str) -> JobCreationState:
        """Invoke the graph for a wizard session.

        Args:
            state: Current wizard state (accumulated across invocations).
            thread_id: Unique session ID for checkpointer persistence.

        Returns:
            Updated state after graph execution (may END at HITL points).
        """
        config = {"configurable": {"thread_id": thread_id}}
        return self._graph.invoke(state, config=config)

    def resume(
        self,
        thread_id: str,
        prior_state: Dict[str, Any],
        updates: Dict[str, Any],
    ) -> JobCreationState:
        """Resume a wizard session after HITL approval.

        The caller (domain.py) is responsible for passing the prior_state
        from the last invocation. We merge the recruiter's updates and
        re-invoke the graph. The checkpointer handles thread continuity.

        This follows the same pattern as scheduling: caller accumulates
        state, graph is re-invoked with merged state.
        """
        merged = {**prior_state, **updates}
        config = {"configurable": {"thread_id": thread_id}}
        return self._graph.invoke(merged, config=config)


def get_job_creation_graph() -> JobCreationGraph:
    return JobCreationGraph()
