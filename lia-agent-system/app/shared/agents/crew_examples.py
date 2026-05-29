"""
Example crew definitions for common multi-agent workflows.

Provides factory functions that return pre-configured AgentCrew instances
with roles and plans ready for execution.

Production handlers delegate to real domain entry-points
(``JobWizardGraph``, ``SourcingReActAgent``).  Stub fallbacks are used
only when the domain modules cannot be imported (e.g. in unit-tests).
"""
from __future__ import annotations

import logging
from typing import Any

from app.shared.agents.crew_context import CrewContext
from app.shared.agents.crew_models import (
    AgentCrew,
    CrewPlan,
    CrewRole,
    CrewRoleType,
    CrewTask,
)

logger = logging.getLogger(__name__)


def build_job_opening_sourcing_crew(
    company_id: str,
    job_title: str,
    job_params: dict[str, Any] | None = None,
    sourcing_params: dict[str, Any] | None = None,
) -> AgentCrew:
    """Build a crew for "abrir vaga + sourcing automático".

    Flow:
        1. JobWizard (leader) creates/validates the job opening
        2. SourcingAgent (researcher) searches for matching candidates
        3. ReviewerAgent (reviewer) validates sourcing results
    """
    task_create_job = CrewTask(
        task_id="create_job",
        assigned_agent="job_wizard",
        action="create_job_opening",
        description=f"Create job opening: {job_title}",
        params={
            "job_title": job_title,
            **(job_params or {}),
        },
        timeout_seconds=30.0,
        is_critical=True,
    )

    task_source_candidates = CrewTask(
        task_id="source_candidates",
        assigned_agent="sourcing",
        action="auto_source_candidates",
        description=f"Find candidates matching: {job_title}",
        params={
            **(sourcing_params or {}),
        },
        depends_on=["create_job"],
        timeout_seconds=60.0,
        is_critical=False,
        context_mappings={
            "job_id": "create_job.job_id",
            "requirements": "create_job.requirements",
        },
    )

    task_review_results = CrewTask(
        task_id="review_sourcing",
        assigned_agent="pipeline",
        action="review_sourcing_results",
        description="Review and validate sourcing results",
        depends_on=["source_candidates"],
        timeout_seconds=30.0,
        is_critical=False,
        context_mappings={
            "job_id": "create_job.job_id",
            "candidates": "source_candidates.candidates",
        },
    )

    plan = CrewPlan(
        name="job_opening_sourcing",
        description=f"Open job '{job_title}' and automatically source candidates",
        tasks=[task_create_job, task_source_candidates, task_review_results],
    )

    crew = AgentCrew(
        name=f"Job Opening + Sourcing: {job_title}",
        description=f"Automated crew for opening job '{job_title}' and sourcing candidates",
        company_id=company_id,
        roles=[
            CrewRole(
                agent_name="job_wizard",
                role_type=CrewRoleType.LEADER,
                description="Creates and validates job openings",
                capabilities=["create_job", "validate_job", "publish_job"],
            ),
            CrewRole(
                agent_name="sourcing",
                role_type=CrewRoleType.RESEARCHER,
                description="Searches for matching candidates across sources",
                capabilities=["search_candidates", "enrich_profiles", "score_match"],
            ),
            CrewRole(
                agent_name="pipeline",
                role_type=CrewRoleType.REVIEWER,
                description="Reviews and validates sourcing results",
                capabilities=["review_candidates", "rank_candidates"],
            ),
        ],
        plan=plan,
    )

    return crew


def get_production_handlers() -> dict[str, Any]:
    """Return handler mapping that wires to real domain agents.

    Falls back to stub handlers for any domain that cannot be imported
    (e.g. missing database deps in unit-test environments).
    """
    handlers: dict[str, Any] = {}

    handlers["create_job_opening"] = handler_create_job_opening
    handlers["auto_source_candidates"] = handler_auto_source_candidates
    handlers["review_sourcing_results"] = handler_review_sourcing_results

    return handlers


# JobWizardGraph LEGACY removido (2026-05-29). A criação canônica de vaga é
# conversacional via WizardSessionService/JobCreationGraph (chat), não via
# crew/plan_executor. handler_create_job_opening é stub explícito abaixo.


_SOURCING_DOMAIN_AVAILABLE = False

try:
    from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
    from lia_agents_core.agent_interface import AgentInput as _AgentInput
    _SOURCING_DOMAIN_AVAILABLE = True
except ImportError as exc:
    logger.info("SourcingReActAgent not available (missing deps): %s", exc)
    SourcingReActAgent = None  # type: ignore[misc, assignment]
    _AgentInput = None  # type: ignore[misc, assignment]


async def handler_create_job_opening(
    params: dict[str, Any],
    crew_ctx: CrewContext,
) -> dict[str, Any]:
    """Stub EXPLÍCITO de criação de vaga via crew (não implementado).

    O JobWizardGraph LEGACY foi removido (2026-05-29). A criação canônica de
    vaga é conversacional via WizardSessionService/JobCreationGraph (chat), não
    via crew/plan_executor. Este handler está dormente — nenhum plano de crew
    dispara ``create_job_opening``. Retorna um resultado explícito de
    não-implementado: NUNCA finge sucesso (REGRA 4 anti-silent-fallback).
    """
    job_title = params.get("job_title", "Untitled")
    logger.warning(
        "[handler_create_job_opening] crew job-creation não implementado — "
        "use o wizard conversacional (WizardSessionService/JobCreationGraph)."
    )
    return {
        "job_id": None,
        "job_title": job_title,
        "status": "not_implemented",
        "created": False,
        "requirements": params.get("requirements", []),
        "message": (
            "Criação de vaga via crew não está implementada. "
            "Use o wizard conversacional da LIA."
        ),
        "source": "stub_not_implemented",
    }


async def handler_auto_source_candidates(
    params: dict[str, Any],
    crew_ctx: CrewContext,
) -> dict[str, Any]:
    """Source candidates via SourcingReActAgent.

    Delegates to the real ``SourcingReActAgent.process()`` when the domain
    is available.  Falls back to a minimal stub otherwise.
    """
    job_id = params.get("job_id", "unknown")
    company_id = params.get("company_id", "")

    if _SOURCING_DOMAIN_AVAILABLE and SourcingReActAgent is not None and _AgentInput is not None:
        agent = SourcingReActAgent()

        requirements = params.get("requirements", [])
        req_text = ", ".join(requirements) if isinstance(requirements, list) else str(requirements)
        message = f"Buscar candidatos para vaga {job_id}. Requisitos: {req_text}"

        agent_input = _AgentInput(
            message=message,
            user_id=params.get("user_id", "crew-system"),
            company_id=company_id,
            session_id=f"crew-sourcing:{job_id}",
            metadata={"job_id": job_id, "crew_mode": True},
        )

        output = await agent.process(agent_input)

        candidates = output.metadata.get("candidates", []) if output.metadata else []
        return {
            "job_id": job_id,
            "candidates": candidates,
            "sources_searched": output.metadata.get("sources", ["auto"]) if output.metadata else ["auto"],
            "total_found": len(candidates),
            "message": output.message or f"Sourcing completed for job {job_id}",
            "source": "sourcing_react_agent",
        }

    if not _SOURCING_DOMAIN_AVAILABLE:
        logger.warning("[handler_auto_source_candidates] SourcingReActAgent unavailable — using stub (test mode only)")

    return {
        "job_id": job_id,
        "candidates": [],
        "sources_searched": ["linkedin", "github", "internal_db"],
        "total_found": 0,
        "message": f"Sourcing completed for job {job_id}",
        "source": "stub",
    }


async def handler_review_sourcing_results(
    params: dict[str, Any],
    crew_ctx: CrewContext,
) -> dict[str, Any]:
    """Review sourcing results and rank candidates.

    Uses a lightweight review heuristic.  In a full production setup this
    could delegate to a dedicated PipelineAgent or scoring service.
    """
    candidates = params.get("candidates", [])
    job_id = params.get("job_id", "unknown")

    approved = []
    rejected = []
    for c in candidates:
        score = c.get("match_score", c.get("score", 0))
        if score >= 0.5:
            approved.append(c)
        else:
            rejected.append(c)

    return {
        "job_id": job_id,
        "reviewed": len(candidates),
        "approved": len(approved),
        "approved_candidates": approved,
        "rejected": len(rejected),
        "message": f"Reviewed {len(candidates)} candidates: {len(approved)} approved, {len(rejected)} rejected",
    }
