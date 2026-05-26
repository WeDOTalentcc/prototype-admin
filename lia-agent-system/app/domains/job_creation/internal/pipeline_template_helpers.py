"""pipeline_template_helpers canonical — PR-17 step 5 extract (2026-05-26).

Pipeline template helpers movidos de graph.py:
- _suggest_pipeline_template (Task #1055 heurístico keyword-based determinístico)
- _build_pipeline_template_db_suggestion (Sprint Pipeline Templates 2026-05-26 — DB-based)
- _apply_pipeline_template_to_state (sync wrapper para pipeline_template_node)
"""

import logging
from typing import Any, Dict, Optional

from app.domains.job_creation.internal.constants import (
    _PIPELINE_TEMPLATE_IDS,
    _EXECUTIVE_KEYWORDS,
    _TECHNICAL_KEYWORDS,
    _OPERATIONAL_KEYWORDS,
    _INTERN_KEYWORDS,
)

logger = logging.getLogger(__name__)


def _suggest_pipeline_template(
    parsed_title: Optional[str],
    parsed_seniority: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Sugestão determinística de template de pipeline a partir do título.

    Retorna `None` quando ainda não há sinal suficiente (sem título), para o
    frontend pular a injeção do card. Nunca levanta — fail-open."""
    try:
        title = (parsed_title or "").strip().lower()
        if not title:
            return None
        seniority = (parsed_seniority or "").strip().lower()

        if any(kw in title for kw in _INTERN_KEYWORDS) or seniority in {"estagiário", "estagiario", "trainee"}:
            suggested = "intern"
        elif any(kw in title for kw in _EXECUTIVE_KEYWORDS) or seniority in {"diretor", "vp", "c-level", "executive"}:
            suggested = "executive"
        elif any(kw in title for kw in _TECHNICAL_KEYWORDS):
            suggested = "technical"
        elif any(kw in title for kw in _OPERATIONAL_KEYWORDS):
            suggested = "operational"
        else:
            suggested = "technical"  # default seguro — frontend ainda mostra todos
        return {
            "suggested_type": suggested,
            "templates": list(_PIPELINE_TEMPLATE_IDS),
        }
    except Exception:  # noqa: BLE001 — fail-open por design
        return None


def _build_pipeline_template_db_suggestion(state: dict) -> Optional[Dict[str, Any]]:
    """Sync wrapper canonical para uso dentro dos nodes do graph.

    Returns {"templates": [...], "top_score": float, "should_suggest": bool} ou None.

    Complementa o heurístico determinístico _suggest_pipeline_template (Task #1055)
    consultando o repositório real (PipelineTemplateRepository.list_for_suggestion)
    com scoring baseado em department_hint / seniority_hint / job_family_hint.

    Fail-open: qualquer erro retorna None. O caller (intake_node / jd_enrichment_node)
    continua emitindo o heurístico legacy.
    """
    try:
        from app.domains.pipeline.tools.pipeline_template_wizard_tools import (
            suggest_pipeline_template_sync_for_graph,
        )
    except Exception:  # noqa: BLE001 — fail-open por design
        return None
    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id:
        return None
    return suggest_pipeline_template_sync_for_graph(
        company_id,
        department=state.get("parsed_department") or state.get("department"),
        seniority=state.get("parsed_seniority"),
        job_family=state.get("parsed_job_family"),
    )


def _apply_pipeline_template_to_state(state: dict, template_id: str) -> Optional[Dict[str, Any]]:
    """Translate template.stages → vacancy.interview_stages, fail-open.

    Sync wrapper para uso dentro de pipeline_template_node. Usa
    AsyncSessionLocal + run_coro_in_threadpool (canonical async helper).

    PR-4 (2026-05-26): substituído _asyncio.run() por run_coro_in_threadpool()
    do app.domains.job_creation.helpers.async_audit. Python 3.12+ raise
    RuntimeError quando há event loop ativo + asyncio.run — sync nodes do
    LangGraph SEMPRE rodam num event loop, então asyncio.run aqui era
    silent-failure (template nunca aplicado em runtime). Helper canonical
    delega para ThreadPoolExecutor + asyncio.run em thread separada.
    """
    try:
        import uuid as _uuid
        from app.core.database import AsyncSessionLocal
        from app.domains.job_creation.helpers.async_audit import (
            run_coro_in_threadpool,
        )
        from app.domains.pipeline.repositories.pipeline_template_repository import (
            PipelineTemplateRepository,
        )
        from app.domains.pipeline.services.pipeline_template_service import (
            translate_template_stages_to_interview_stages,
        )

        company_id = str(state.get("workspace_id") or state.get("company_id") or "")
        if not company_id:
            return None

        async def _run():
            async with AsyncSessionLocal() as session:
                repo = PipelineTemplateRepository(session)
                template = await repo.get_by_id(_uuid.UUID(template_id), company_id)
                if not template:
                    return None
                stages_translated = translate_template_stages_to_interview_stages(template.stages or [])
                await repo.increment_usage(template)
                return {"interview_stages": stages_translated, "template_name": template.name}

        return run_coro_in_threadpool(lambda: _run())
    except Exception as exc:  # noqa: BLE001 — fail-open por design
        logger.warning(
            "_apply_pipeline_template_to_state fail-open (graph continua com default): %s",
            exc,
            exc_info=True,
        )
        return None
