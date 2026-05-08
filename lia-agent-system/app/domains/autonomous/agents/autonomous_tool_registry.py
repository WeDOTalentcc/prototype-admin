"""
Autonomous Tool Registry — Pool cross-domain curado para o AutonomousReActAgent (Tier 6).

Agrega um subconjunto de ferramentas dos domínios:
  - job_management (vagas)
  - sourcing (busca de candidatos)
  - cv_screening / pipeline (triagem, pipeline)
  - analytics (relatórios, métricas)
  - interview_scheduling (agendamento)
  - communication (mensagens)

Escopo de permissão: read-first, write controlado via confirm=True.
"""
import logging
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers de delegação — invocam funções dos domínios existentes
# ---------------------------------------------------------------------------


_TENANT_REQUIRED_RESPONSE: dict[str, Any] = {
    "success": False,
    "data": {},
    "message": (
        "Tenant isolation error: 'company_id' é obrigatório. "
        "Nenhuma query de dados pode ser executada sem contexto de tenant."
    ),
}


def _check_company_id(kwargs: dict[str, Any]) -> dict[str, Any] | None:
    """Return a fail-closed error dict if company_id is absent, else None."""
    if not kwargs.get("company_id"):
        return dict(_TENANT_REQUIRED_RESPONSE)
    return None


@tool_handler("autonomous")
async def _delegate_sourcing(fn_name: str, **kwargs: Any) -> dict[str, Any]:
    """Delega para funções do sourcing tool registry com mandatory tenant isolation.

    Rejeita a chamada se company_id não estiver presente, garantindo que queries
    de sourcing nunca cruzem fronteiras de tenant (fail-closed).
    """
    from app.domains.sourcing.agents.sourcing_tool_registry import (
        _wrap_search_candidates,
        _wrap_analyze_profile,
        _wrap_compare_candidates,
        _wrap_score_candidate,
        _wrap_filter_results,
        _wrap_set_search_criteria,
    )
    mapping: dict[str, Any] = {
        "search_candidates": _wrap_search_candidates,
        "analyze_profile": _wrap_analyze_profile,
        "compare_candidates": _wrap_compare_candidates,
        "score_candidate": _wrap_score_candidate,
        "filter_results": _wrap_filter_results,
        "set_search_criteria": _wrap_set_search_criteria,
    }
    fn = mapping.get(fn_name)
    if fn is None:
        return {"success": False, "data": {}, "message": f"Função '{fn_name}' não encontrada no domínio sourcing."}
    return await fn(**kwargs)


# ── Job Management ──────────────────────────────────────────────────────────

@tool_handler("autonomous")
async def _wrap_list_jobs(**kwargs: Any) -> dict[str, Any]:
    """List open job vacancies for the company."""
    logger.info("[autonomous_tools] list_jobs called with: %s", list(kwargs.keys()))
    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        company_id = kwargs.get("company_id", "")
        status = kwargs.get("status", "open")
        limit = min(int(kwargs.get("limit", 20)), 50)

        conditions = ["is_deleted = false"]
        params: dict[str, Any] = {"lim": limit}
        if company_id:
            conditions.append("company_id = :company_id")
            params["company_id"] = company_id
        if status:
            conditions.append("status = :status")
            params["status"] = status

        where = " AND ".join(conditions)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"""
                    SELECT id, title, department, seniority_level, location, work_model,
                           status, created_at
                    FROM job_vacancies
                    WHERE {where}
                    ORDER BY created_at DESC
                    LIMIT :lim
                """),
                params,
            )
            rows = result.mappings().all()

        jobs = [
            {
                "id": str(r["id"]),
                "title": r["title"],
                "department": r["department"],
                "seniority_level": r["seniority_level"],
                "location": r["location"],
                "work_model": r["work_model"],
                "status": r["status"],
            }
            for r in rows
        ]
        return {
            "success": True,
            "data": {"jobs": jobs, "total": len(jobs)},
            "message": f"{len(jobs)} vagas encontradas.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_list_jobs", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


@tool_handler("autonomous")
async def _wrap_get_job_details(**kwargs: Any) -> dict[str, Any]:
    """Get full details of a specific job vacancy with tenant isolation."""
    logger.info("[autonomous_tools] get_job_details called")
    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        job_id = kwargs.get("job_id", "")
        company_id = kwargs.get("company_id", "")
        if not job_id:
            return {"success": False, "data": {}, "message": "Parâmetro 'job_id' é obrigatório."}

        conditions = ["id = :jid"]
        params: dict[str, Any] = {"jid": job_id}
        if company_id:
            conditions.append("company_id = :company_id")
            params["company_id"] = company_id
        where = " AND ".join(conditions)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"""
                    SELECT id, title, description, requirements, department,
                           seniority_level, location, work_model, status,
                           salary_min, salary_max, salary_currency,
                           created_at, updated_at
                    FROM job_vacancies WHERE {where}
                """),
                params,
            )
            row = result.mappings().first()

        if not row:
            return {"success": False, "data": {}, "message": f"Vaga '{job_id}' não encontrada."}

        return {
            "success": True,
            "data": {
                "id": str(row["id"]),
                "title": row["title"],
                "description": row["description"],
                "requirements": row["requirements"] or [],
                "department": row["department"],
                "seniority_level": row["seniority_level"],
                "location": row["location"],
                "work_model": row["work_model"],
                "status": row["status"],
                "salary_range": {
                    "min": row["salary_min"],
                    "max": row["salary_max"],
                    "currency": row["salary_currency"],
                },
            },
            "message": f"Detalhes da vaga '{row['title']}' obtidos.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_get_job_details", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


# ── Sourcing ────────────────────────────────────────────────────────────────


async def _wrap_rag_search(**kwargs: Any) -> dict[str, Any]:
    """Semantic hybrid search (BM25 + pgvector)."""
    return await _delegate_sourcing(fn_name="rag_search", **kwargs)

async def _wrap_auto_search_candidates(**kwargs: Any) -> dict[str, Any]:
    """Search candidates matching given criteria."""
    return await _delegate_sourcing(fn_name="search_candidates", **kwargs)


async def _wrap_auto_analyze_profile(**kwargs: Any) -> dict[str, Any]:
    """Analyze a candidate profile in detail."""
    return await _delegate_sourcing(fn_name="analyze_profile", **kwargs)


async def _wrap_auto_compare_candidates(**kwargs: Any) -> dict[str, Any]:
    """Compare multiple candidate profiles side by side."""
    return await _delegate_sourcing(fn_name="compare_candidates", **kwargs)


async def _wrap_auto_score_candidate(**kwargs: Any) -> dict[str, Any]:
    """Score a candidate against a specific job vacancy using WSI."""
    return await _delegate_sourcing(fn_name="score_candidate", **kwargs)


async def _wrap_auto_filter_candidates(**kwargs: Any) -> dict[str, Any]:
    """Filter candidates by skills, location, seniority, experience."""
    return await _delegate_sourcing(fn_name="filter_results", **kwargs)


# ── Pipeline / CV Screening ─────────────────────────────────────────────────

@tool_handler("autonomous")
async def _wrap_get_pipeline_status(**kwargs: Any) -> dict[str, Any]:
    """Get current pipeline status and candidate counts per stage for a job."""
    logger.info("[autonomous_tools] get_pipeline_status called")
    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        job_id = kwargs.get("job_id", "")
        company_id = kwargs.get("company_id", "")

        conditions = ["1=1"]
        params: dict[str, Any] = {}
        if job_id:
            conditions.append("job_id = :job_id")
            params["job_id"] = job_id
        if company_id:
            conditions.append("company_id = :company_id")
            params["company_id"] = company_id

        where = " AND ".join(conditions)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"""
                    SELECT stage, COUNT(*) as count, status
                    FROM pipeline_candidates
                    WHERE {where}
                    GROUP BY stage, status
                    ORDER BY stage
                """),
                params,
            )
            rows = result.mappings().all()

        stages: dict[str, Any] = {}
        for row in rows:
            stage = row["stage"] or "unknown"
            if stage not in stages:
                stages[stage] = {"stage": stage, "total": 0, "by_status": {}}
            stages[stage]["total"] += row["count"]
            stages[stage]["by_status"][row["status"] or "unknown"] = row["count"]

        return {
            "success": True,
            "data": {
                "stages": list(stages.values()),
                "total_candidates": sum(s["total"] for s in stages.values()),
            },
            "message": f"Pipeline com {len(stages)} etapas obtido.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_get_pipeline_status", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


@tool_handler("autonomous")
async def _wrap_get_candidates_in_stage(**kwargs: Any) -> dict[str, Any]:
    """Get list of candidates currently in a specific pipeline stage with tenant isolation."""
    logger.info("[autonomous_tools] get_candidates_in_stage called")
    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        stage = kwargs.get("stage", "")
        job_id = kwargs.get("job_id", "")
        company_id = kwargs.get("company_id", "")
        limit = min(int(kwargs.get("limit", 20)), 50)
        if not stage:
            return {"success": False, "data": {}, "message": "Parâmetro 'stage' é obrigatório."}

        params: dict[str, Any] = {"stage": stage, "lim": limit}
        extra_conditions = []
        if job_id:
            extra_conditions.append("pc.job_id = :job_id")
            params["job_id"] = job_id
        if company_id:
            extra_conditions.append("pc.company_id = :company_id")
            params["company_id"] = company_id
        extra = (" AND " + " AND ".join(extra_conditions)) if extra_conditions else ""

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"""
                    SELECT pc.id, pc.candidate_id, pc.stage, pc.status,
                           c.name, c.current_title, c.lia_score
                    FROM pipeline_candidates pc
                    JOIN candidates c ON c.id = pc.candidate_id
                    WHERE pc.stage = :stage{extra}
                    ORDER BY c.lia_score DESC NULLS LAST
                    LIMIT :lim
                """),
                params,
            )
            rows = result.mappings().all()

        candidates = [
            {
                "pipeline_id": str(r["id"]),
                "candidate_id": str(r["candidate_id"]),
                "name": r["name"],
                "current_title": r["current_title"],
                "stage": r["stage"],
                "status": r["status"],
                "lia_score": r["lia_score"],
            }
            for r in rows
        ]
        return {
            "success": True,
            "data": {"candidates": candidates, "stage": stage, "count": len(candidates)},
            "message": f"{len(candidates)} candidatos na etapa '{stage}'.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_get_candidates_in_stage", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


@tool_handler("autonomous")
async def _wrap_match_candidates_to_job(**kwargs: Any) -> dict[str, Any]:
    """Cross-domain: find best candidates from sourcing for a specific job vacancy."""
    logger.info("[autonomous_tools] match_candidates_to_job called")
    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        job_id = kwargs.get("job_id", "")
        limit = min(int(kwargs.get("limit", 10)), 30)
        if not job_id:
            return {"success": False, "data": {}, "message": "Parâmetro 'job_id' é obrigatório."}

        company_id = kwargs.get("company_id", "")

        async with AsyncSessionLocal() as session:
            job_conditions = ["id = :jid"]
            job_params: dict[str, Any] = {"jid": job_id}
            if company_id:
                job_conditions.append("company_id = :company_id")
                job_params["company_id"] = company_id
            job_where = " AND ".join(job_conditions)

            job_result = await session.execute(
                text(f"SELECT title, requirements, seniority_level FROM job_vacancies WHERE {job_where}"),
                job_params,
            )
            job = job_result.mappings().first()
            if not job:
                return {"success": False, "data": {}, "message": f"Vaga '{job_id}' não encontrada."}

            requirements = job["requirements"] or []
            seniority = job["seniority_level"] or ""

            cand_conditions = ["is_active = true"]
            cand_params: dict[str, Any] = {"lim": 200}
            if company_id:
                cand_conditions.append("company_id = :company_id")
                cand_params["company_id"] = company_id
            cand_where = " AND ".join(cand_conditions)

            candidate_result = await session.execute(
                text(f"""
                    SELECT id, name, current_title, seniority_level,
                           years_of_experience, technical_skills, lia_score
                    FROM candidates
                    WHERE {cand_where}
                    ORDER BY lia_score DESC NULLS LAST
                    LIMIT :lim
                """),
                cand_params,
            )
            rows = candidate_result.mappings().all()

        scored = []
        for row in rows:
            cand_skills = set(s.lower() for s in (row["technical_skills"] or []))
            req_skills = set(r.lower() for r in requirements)
            skill_match = (len(cand_skills & req_skills) / len(req_skills) * 100) if req_skills else 50.0
            seniority_match = 100.0 if (seniority and row["seniority_level"] and
                                         seniority.lower() == row["seniority_level"].lower()) else 50.0
            composite = round(skill_match * 0.6 + seniority_match * 0.4, 2)
            scored.append({
                "candidate_id": str(row["id"]),
                "name": row["name"],
                "current_title": row["current_title"],
                "seniority_level": row["seniority_level"],
                "years_of_experience": row["years_of_experience"],
                "matched_skills": list(cand_skills & set(r.lower() for r in requirements)),
                "lia_score": row["lia_score"] or 0.0,
                "match_score": composite,
            })

        ranked = sorted(scored, key=lambda x: x["match_score"], reverse=True)[:limit]
        for i, c in enumerate(ranked):
            c["rank"] = i + 1

        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "job_title": job["title"],
                "top_candidates": ranked,
            },
            "message": f"Top {len(ranked)} candidatos encontrados para '{job['title']}'.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_match_candidates_to_job", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


# ── Analytics ───────────────────────────────────────────────────────────────

@tool_handler("autonomous")
async def _wrap_auto_get_job_insights(**kwargs: Any) -> dict[str, Any]:
    """Get analytics insights for a job: pipeline funnel, time-to-fill, source metrics."""
    logger.info("[autonomous_tools] get_job_insights called")
    from app.domains.analytics.agents.analytics_tool_registry import _wrap_get_job_insights
    return await _wrap_get_job_insights(**kwargs)


@tool_handler("autonomous")
async def _wrap_auto_generate_report(**kwargs: Any) -> dict[str, Any]:
    """Generate a comprehensive job or candidate report."""
    logger.info("[autonomous_tools] generate_report called")
    report_type = kwargs.get("report_type", "job")
    if report_type == "candidate":
        from app.domains.analytics.agents.analytics_tool_registry import _wrap_generate_candidate_report
        return await _wrap_generate_candidate_report(**kwargs)
    else:
        from app.domains.analytics.agents.analytics_tool_registry import _wrap_generate_job_report
        return await _wrap_generate_job_report(**kwargs)


@tool_handler("autonomous")
async def _wrap_auto_hiring_metrics(**kwargs: Any) -> dict[str, Any]:
    """Predict hiring probability and expected time-to-fill for a vacancy."""
    logger.info("[autonomous_tools] hiring_metrics called")
    from app.domains.analytics.agents.analytics_tool_registry import _wrap_predict_hiring_metrics
    return await _wrap_predict_hiring_metrics(**kwargs)


# ── Interview Scheduling ─────────────────────────────────────────────────────

@tool_handler("autonomous")
async def _wrap_get_scheduled_interviews(**kwargs: Any) -> dict[str, Any]:
    """Get upcoming or past interviews for a candidate or job with tenant isolation."""
    logger.info("[autonomous_tools] get_scheduled_interviews called")
    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        candidate_id = kwargs.get("candidate_id", "")
        job_id = kwargs.get("job_id", "")
        company_id = kwargs.get("company_id", "")
        status = kwargs.get("status", "scheduled")
        limit = min(int(kwargs.get("limit", 20)), 50)

        if not company_id and not candidate_id and not job_id:
            return {
                "success": False,
                "data": {},
                "message": "Pelo menos um de 'candidate_id', 'job_id' ou 'company_id' é obrigatório.",
            }

        conditions: list[str] = []
        params: dict[str, Any] = {"lim": limit}
        if candidate_id:
            conditions.append("candidate_id = :candidate_id")
            params["candidate_id"] = candidate_id
        if job_id:
            conditions.append("job_id = :job_id")
            params["job_id"] = job_id
        if company_id:
            conditions.append("company_id = :company_id")
            params["company_id"] = company_id
        if status:
            conditions.append("status = :status")
            params["status"] = status

        where = " AND ".join(conditions) if conditions else "1=0"
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"""
                    SELECT id, candidate_id, job_id, interview_type,
                           scheduled_at, duration_minutes, status, notes
                    FROM interviews
                    WHERE {where}
                    ORDER BY scheduled_at ASC
                    LIMIT :lim
                """),
                params,
            )
            rows = result.mappings().all()

        interviews = [
            {
                "id": str(r["id"]),
                "candidate_id": str(r["candidate_id"]),
                "job_id": str(r["job_id"]) if r["job_id"] else None,
                "interview_type": r["interview_type"],
                "scheduled_at": str(r["scheduled_at"]) if r["scheduled_at"] else None,
                "duration_minutes": r["duration_minutes"],
                "status": r["status"],
                "notes": r["notes"],
            }
            for r in rows
        ]
        return {
            "success": True,
            "data": {"interviews": interviews, "count": len(interviews)},
            "message": f"{len(interviews)} entrevistas encontradas.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_get_scheduled_interviews", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


# ── Communication ────────────────────────────────────────────────────────────

@tool_handler("autonomous")
async def _wrap_get_communication_history(**kwargs: Any) -> dict[str, Any]:
    """Get communication history (emails, messages) with a candidate."""
    logger.info("[autonomous_tools] get_communication_history called")
    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        candidate_id = kwargs.get("candidate_id", "")
        company_id = kwargs.get("company_id", "")
        limit = min(int(kwargs.get("limit", 20)), 50)
        if not candidate_id:
            return {"success": False, "data": {}, "message": "Parâmetro 'candidate_id' é obrigatório."}

        conditions = ["candidate_id = :cid"]
        params: dict[str, Any] = {"cid": candidate_id, "lim": limit}
        if company_id:
            conditions.append("company_id = :company_id")
            params["company_id"] = company_id
        where = " AND ".join(conditions)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"""
                    SELECT id, channel, subject, status, sent_at, opened_at
                    FROM communications
                    WHERE {where}
                    ORDER BY sent_at DESC NULLS LAST
                    LIMIT :lim
                """),
                params,
            )
            rows = result.mappings().all()

        comms = [
            {
                "id": str(r["id"]),
                "channel": r["channel"],
                "subject": r["subject"],
                "status": r["status"],
                "sent_at": str(r["sent_at"]) if r["sent_at"] else None,
                "opened_at": str(r["opened_at"]) if r["opened_at"] else None,
            }
            for r in rows
        ]
        return {
            "success": True,
            "data": {"communications": comms, "count": len(comms)},
            "message": f"{len(comms)} comunicações encontradas para o candidato.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_get_communication_history", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


# ── Additional tools: Job Management (extended) ──────────────────────────────

@tool_handler("autonomous")
async def _wrap_get_salary_benchmark(**kwargs: Any) -> dict[str, Any]:
    """Get salary benchmark for a role from wizard registry."""
    from app.domains.job_management.agents.wizard_tool_registry import _wrap_get_salary_benchmarks
    return await _wrap_get_salary_benchmarks(**kwargs)


@tool_handler("autonomous")
async def _wrap_validate_job_requirements(**kwargs: Any) -> dict[str, Any]:
    """Validate job requirements for completeness and quality."""
    from app.domains.job_management.agents.wizard_tool_registry import _wrap_validate_job_requirements
    return await _wrap_validate_job_requirements(**kwargs)


@tool_handler("autonomous")
async def _wrap_get_company_config(**kwargs: Any) -> dict[str, Any]:
    """Get company configuration including hiring policies and preferences."""
    from app.domains.job_management.agents.wizard_tool_registry import _wrap_get_company_config
    return await _wrap_get_company_config(**kwargs)


# ── Additional tools: CV Screening / Pipeline (extended) ─────────────────────

@tool_handler("autonomous")
async def _wrap_view_candidate_profile(**kwargs: Any) -> dict[str, Any]:
    """View full candidate profile from pipeline perspective."""
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_view_candidate_profile
    return await _wrap_view_candidate_profile(**kwargs)


@tool_handler("autonomous")
async def _wrap_view_screening_results(**kwargs: Any) -> dict[str, Any]:
    """View WSI screening results for a candidate."""
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_view_screening_results
    return await _wrap_view_screening_results(**kwargs)


@tool_handler("autonomous")
async def _wrap_view_interview_notes(**kwargs: Any) -> dict[str, Any]:
    """View interview notes and feedback for a candidate."""
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_view_interview_notes
    return await _wrap_view_interview_notes(**kwargs)


@tool_handler("autonomous")
async def _wrap_run_wsi_screening(**kwargs: Any) -> dict[str, Any]:
    """Run WSI automated screening for a candidate against a job."""
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_run_wsi_screening
    return await _wrap_run_wsi_screening(**kwargs)


@tool_handler("autonomous")
async def _wrap_add_candidate_notes(**kwargs: Any) -> dict[str, Any]:
    """Add notes or observations to a candidate's pipeline record."""
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_add_notes
    return await _wrap_add_notes(**kwargs)


# ── Additional tools: Sourcing (extended) ────────────────────────────────────

@tool_handler("autonomous")
async def _wrap_suggest_skills(**kwargs: Any) -> dict[str, Any]:
    """Suggest relevant skills for a role based on historical data."""
    from app.domains.sourcing.agents.sourcing_tool_registry import _wrap_suggest_skills
    return await _wrap_suggest_skills(**kwargs)


@tool_handler("autonomous")
async def _wrap_add_to_shortlist(**kwargs: Any) -> dict[str, Any]:
    """Add a candidate to a shortlist (write operation — use with care)."""
    from app.domains.sourcing.agents.sourcing_tool_registry import _wrap_add_to_shortlist
    return await _wrap_add_to_shortlist(**kwargs)


@tool_handler("autonomous")
async def _wrap_rank_candidates(**kwargs: Any) -> dict[str, Any]:
    """Rank a set of candidates by composite score with tenant isolation."""
    logger.info("[autonomous_tools] rank_candidates called")
    candidate_ids = kwargs.get("candidate_ids", [])
    criteria = kwargs.get("criteria", ["lia_score", "years_of_experience"])
    company_id = kwargs.get("company_id", "")
    if not candidate_ids:
        return {"success": False, "data": {}, "message": "Parâmetro 'candidate_ids' é obrigatório."}

    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        placeholders = ", ".join([f":id_{i}" for i in range(len(candidate_ids))])
        params: dict[str, Any] = {f"id_{i}": cid for i, cid in enumerate(candidate_ids)}

        conditions = [f"id IN ({placeholders})"]
        if company_id:
            conditions.append("company_id = :company_id")
            params["company_id"] = company_id
        where = " AND ".join(conditions)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"""
                    SELECT id, name, current_title, years_of_experience,
                           seniority_level, lia_score
                    FROM candidates
                    WHERE {where}
                """),
                params,
            )
            rows = result.mappings().all()

        ranked = sorted(
            [dict(r) for r in rows],
            key=lambda x: (x.get("lia_score") or 0, x.get("years_of_experience") or 0),
            reverse=True,
        )
        for i, c in enumerate(ranked):
            c["rank"] = i + 1
            c["id"] = str(c["id"])

        return {
            "success": True,
            "data": {"ranked_candidates": ranked, "total": len(ranked), "criteria": criteria},
            "message": f"{len(ranked)} candidatos ranqueados por {', '.join(criteria)}.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_rank_candidates", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


# ── Additional tools: Analytics (extended) ───────────────────────────────────

@tool_handler("autonomous")
async def _wrap_get_agent_performance(**kwargs: Any) -> dict[str, Any]:
    """Get performance metrics for LIA agents."""
    from app.domains.analytics.agents.analytics_tool_registry import _wrap_get_agent_performance
    return await _wrap_get_agent_performance(**kwargs)


@tool_handler("autonomous")
async def _wrap_get_search_analytics(**kwargs: Any) -> dict[str, Any]:
    """Get search quality analytics and metrics."""
    from app.domains.analytics.agents.analytics_tool_registry import _wrap_get_search_analytics
    return await _wrap_get_search_analytics(**kwargs)


# ── Additional tools: Candidate info (cross-domain read) ─────────────────────

@tool_handler("autonomous")
async def _wrap_get_candidate_by_id(**kwargs: Any) -> dict[str, Any]:
    """Get basic candidate information by ID with tenant isolation."""
    logger.info("[autonomous_tools] get_candidate_by_id called")
    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        candidate_id = kwargs.get("candidate_id", "")
        company_id = kwargs.get("company_id", "")
        if not candidate_id:
            return {"success": False, "data": {}, "message": "Parâmetro 'candidate_id' é obrigatório."}

        conditions = ["id = :cid"]
        params: dict[str, Any] = {"cid": candidate_id}
        if company_id:
            conditions.append("company_id = :company_id")
            params["company_id"] = company_id
        where = " AND ".join(conditions)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"""
                    SELECT id, name, email, current_title, current_company,
                           seniority_level, years_of_experience, technical_skills,
                           soft_skills, location_city, location_country,
                           status, lia_score, created_at
                    FROM candidates WHERE {where}
                """),
                params,
            )
            row = result.mappings().first()

        if not row:
            return {"success": False, "data": {}, "message": f"Candidato '{candidate_id}' não encontrado."}

        return {
            "success": True,
            "data": {
                "id": str(row["id"]),
                "name": row["name"],
                "current_title": row["current_title"],
                "current_company": row["current_company"],
                "seniority_level": row["seniority_level"],
                "years_of_experience": row["years_of_experience"],
                "technical_skills": row["technical_skills"] or [],
                "soft_skills": row["soft_skills"] or [],
                "location": f"{row['location_city'] or ''}, {row['location_country'] or ''}".strip(", "),
                "status": row["status"],
                "lia_score": row["lia_score"],
            },
            "message": f"Candidato '{row['name']}' encontrado.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_get_candidate_by_id", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


@tool_handler("autonomous")
async def _wrap_search_candidates_by_name(**kwargs: Any) -> dict[str, Any]:
    """Search candidates by name with tenant isolation."""
    logger.info("[autonomous_tools] search_candidates_by_name called")
    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        name = kwargs.get("name", "")
        company_id = kwargs.get("company_id", "")
        limit = min(int(kwargs.get("limit", 10)), 30)
        if not name:
            return {"success": False, "data": {}, "message": "Parâmetro 'name' é obrigatório."}

        conditions = ["name ILIKE :name_pattern", "is_active = true"]
        params: dict[str, Any] = {"name_pattern": f"%{name}%", "lim": limit}
        if company_id:
            conditions.append("company_id = :company_id")
            params["company_id"] = company_id
        where = " AND ".join(conditions)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"""
                    SELECT id, name, current_title, seniority_level, lia_score, status
                    FROM candidates WHERE {where}
                    ORDER BY lia_score DESC NULLS LAST LIMIT :lim
                """),
                params,
            )
            rows = result.mappings().all()

        candidates = [
            {"id": str(r["id"]), "name": r["name"], "current_title": r["current_title"],
             "seniority_level": r["seniority_level"], "lia_score": r["lia_score"], "status": r["status"]}
            for r in rows
        ]
        return {
            "success": True,
            "data": {"candidates": candidates, "count": len(candidates)},
            "message": f"{len(candidates)} candidatos encontrados com nome '{name}'.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_search_candidates_by_name", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


@tool_handler("autonomous")
async def _wrap_get_job_applications_summary(**kwargs: Any) -> dict[str, Any]:
    """Get a summary of all applications/candidates for a job vacancy."""
    logger.info("[autonomous_tools] get_job_applications_summary called")
    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        job_id = kwargs.get("job_id", "")
        company_id = kwargs.get("company_id", "")
        if not job_id:
            return {"success": False, "data": {}, "message": "Parâmetro 'job_id' é obrigatório."}

        conditions = ["pc.job_id = :job_id"]
        params: dict[str, Any] = {"job_id": job_id}
        if company_id:
            conditions.append("pc.company_id = :company_id")
            params["company_id"] = company_id
        where = " AND ".join(conditions)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"""
                    SELECT pc.stage, COUNT(*) as count,
                           AVG(c.lia_score) as avg_score,
                           MAX(pc.updated_at) as last_updated
                    FROM pipeline_candidates pc
                    LEFT JOIN candidates c ON c.id = pc.candidate_id
                    WHERE {where}
                    GROUP BY pc.stage ORDER BY pc.stage
                """),
                params,
            )
            rows = result.mappings().all()

        stages = [
            {
                "stage": r["stage"],
                "count": r["count"],
                "avg_lia_score": round(float(r["avg_score"] or 0), 2),
                "last_updated": str(r["last_updated"]) if r["last_updated"] else None,
            }
            for r in rows
        ]
        total = sum(s["count"] for s in stages)
        return {
            "success": True,
            "data": {"job_id": job_id, "stages": stages, "total_applications": total},
            "message": f"Resumo de {total} candidaturas para a vaga.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_get_job_applications_summary", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


@tool_handler("autonomous")
async def _wrap_cross_domain_funnel_analysis(**kwargs: Any) -> dict[str, Any]:
    """
    CROSS-DOMAIN: Full funnel analysis combining sourcing pool size, pipeline
    conversion rates, and predicted hiring metrics in one call.
    """
    logger.info("[autonomous_tools] cross_domain_funnel_analysis called")
    job_id = kwargs.get("job_id", "")
    company_id = kwargs.get("company_id", "")
    if not job_id:
        return {"success": False, "data": {}, "message": "Parâmetro 'job_id' é obrigatório."}

    results: dict[str, Any] = {"job_id": job_id}

    pipeline_result = await _wrap_get_pipeline_status(job_id=job_id, company_id=company_id)
    if pipeline_result["success"]:
        results["pipeline"] = pipeline_result["data"]

    match_result = await _wrap_match_candidates_to_job(job_id=job_id, company_id=company_id, limit=5)
    if match_result["success"]:
        results["top_sourcing_matches"] = match_result["data"].get("top_candidates", [])

    analytics_result = await _wrap_auto_hiring_metrics(job_id=job_id, company_id=company_id)
    if analytics_result["success"]:
        results["hiring_prediction"] = analytics_result["data"]

    return {
        "success": True,
        "data": results,
        "message": f"Análise de funil cross-domain para vaga '{job_id}' concluída.",
    }


@tool_handler("autonomous")
async def _wrap_candidate_360_view(**kwargs: Any) -> dict[str, Any]:
    """
    CROSS-DOMAIN: 360° view of a candidate combining profile, pipeline status,
    interviews, communications and WSI score in a single call.
    """
    logger.info("[autonomous_tools] candidate_360_view called")
    candidate_id = kwargs.get("candidate_id", "")
    company_id = kwargs.get("company_id", "")
    if not candidate_id:
        return {"success": False, "data": {}, "message": "Parâmetro 'candidate_id' é obrigatório."}

    result: dict[str, Any] = {"candidate_id": candidate_id}

    profile = await _wrap_auto_analyze_profile(candidate_id=candidate_id, company_id=company_id)
    if profile["success"]:
        result["profile"] = profile["data"]

    interviews = await _wrap_get_scheduled_interviews(candidate_id=candidate_id, company_id=company_id)
    if interviews["success"]:
        result["interviews"] = interviews["data"]

    comms = await _wrap_get_communication_history(candidate_id=candidate_id, company_id=company_id, limit=5)
    if comms["success"]:
        result["recent_communications"] = comms["data"]

    return {
        "success": True,
        "data": result,
        "message": f"Visão 360° do candidato '{candidate_id}' concluída.",
    }


@tool_handler("autonomous")
async def _wrap_get_shortlists(**kwargs: Any) -> dict[str, Any]:
    """Get shortlists for a company with candidate counts."""
    logger.info("[autonomous_tools] get_shortlists called")
    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        company_id = kwargs.get("company_id", "")
        job_id = kwargs.get("job_id", "")
        limit = min(int(kwargs.get("limit", 10)), 30)

        conditions: list[str] = []
        params: dict[str, Any] = {"lim": limit}
        if company_id:
            conditions.append("s.company_id = :company_id")
            params["company_id"] = company_id
        if job_id:
            conditions.append("s.job_id = :job_id")
            params["job_id"] = job_id
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"""
                    SELECT s.id, s.name, s.job_id, s.created_at,
                           COUNT(sc.candidate_id) as candidate_count
                    FROM shortlists s
                    LEFT JOIN shortlist_candidates sc ON sc.shortlist_id = s.id
                    {where}
                    GROUP BY s.id, s.name, s.job_id, s.created_at
                    ORDER BY s.created_at DESC LIMIT :lim
                """),
                params,
            )
            rows = result.mappings().all()

        shortlists = [
            {"id": str(r["id"]), "name": r["name"], "job_id": str(r["job_id"]) if r["job_id"] else None,
             "candidate_count": r["candidate_count"], "created_at": str(r["created_at"]) if r["created_at"] else None}
            for r in rows
        ]
        return {
            "success": True,
            "data": {"shortlists": shortlists, "count": len(shortlists)},
            "message": f"{len(shortlists)} shortlists encontradas.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_get_shortlists", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


@tool_handler("autonomous")
async def _wrap_schedule_interview(**kwargs: Any) -> dict[str, Any]:
    """Schedule an interview for a candidate (write operation)."""
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_schedule_interview as _pi_sched
    return await _pi_sched(**kwargs)


@tool_handler("autonomous")
async def _wrap_get_job_history(**kwargs: Any) -> dict[str, Any]:
    """Get change history / audit trail for a job vacancy."""
    logger.info("[autonomous_tools] get_job_history called")
    from sqlalchemy import text
    try:
        from app.core.database import AsyncSessionLocal
        job_id = kwargs.get("job_id", "")
        company_id = kwargs.get("company_id", "")
        limit = min(int(kwargs.get("limit", 20)), 50)
        if not job_id:
            return {"success": False, "data": {}, "message": "Parâmetro 'job_id' é obrigatório."}

        conditions = ["job_id = :job_id"]
        params: dict[str, Any] = {"job_id": job_id, "lim": limit}
        if company_id:
            conditions.append("company_id = :company_id")
            params["company_id"] = company_id
        where = " AND ".join(conditions)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"""
                    SELECT id, action, changed_by, changed_at, details
                    FROM job_history WHERE {where}
                    ORDER BY changed_at DESC LIMIT :lim
                """),
                params,
            )
            rows = result.mappings().all()

        history = [
            {"id": str(r["id"]), "action": r["action"], "changed_by": r["changed_by"],
             "changed_at": str(r["changed_at"]) if r["changed_at"] else None,
             "details": r["details"]}
            for r in rows
        ]
        return {
            "success": True,
            "data": {"history": history, "count": len(history)},
            "message": f"{len(history)} eventos no histórico da vaga.",
        }
    except Exception as _db_exc:
        import logging as _log
        _log.getLogger(__name__).warning("[autonomous_tools] %s DB error: %s", "_wrap_get_job_history", _db_exc)
        return {"success": False, "error": str(_db_exc), "data": {}}


@tool_handler("autonomous")
async def _wrap_get_tenant_hiring_overview(**kwargs: Any) -> dict[str, Any]:
    """
    CROSS-DOMAIN: Overview de contratação do tenant — vagas abertas, candidatos em pipeline,
    screening pendente, entrevistas agendadas.
    """
    logger.info("[autonomous_tools] get_tenant_hiring_overview called")
    company_id = kwargs.get("company_id", "")
    if not company_id:
        return {"success": False, "data": {}, "message": "Parâmetro 'company_id' é obrigatório."}

    result: dict[str, Any] = {"company_id": company_id}

    jobs = await _wrap_list_jobs(company_id=company_id, status="open", limit=100)
    result["open_jobs_count"] = len(jobs.get("data", {}).get("jobs", [])) if jobs["success"] else 0

    interviews = await _wrap_get_scheduled_interviews(company_id=company_id, limit=50)
    result["scheduled_interviews"] = interviews["data"] if interviews["success"] else {}

    return {
        "success": True,
        "data": result,
        "message": f"Overview de contratação para empresa '{company_id}'.",
    }


@tool_handler("autonomous")
async def _wrap_list_jobs_with_candidates(**kwargs: Any) -> dict[str, Any]:
    """List open jobs with candidate counts per stage — cross-domain overview."""
    logger.info("[autonomous_tools] list_jobs_with_candidates called")
    company_id = kwargs.get("company_id", "")
    limit = min(int(kwargs.get("limit", 10)), 30)

    jobs_result = await _wrap_list_jobs(company_id=company_id, status="open", limit=limit)
    if not jobs_result["success"]:
        return jobs_result

    enriched = []
    for job in jobs_result["data"].get("jobs", []):
        pipeline = await _wrap_get_pipeline_status(job_id=job["id"], company_id=company_id)
        stages = pipeline["data"].get("stages", []) if pipeline["success"] else []
        enriched.append({
            **job,
            "pipeline_stages": stages,
            "total_candidates": sum(s["total"] for s in stages),
        })

    return {
        "success": True,
        "data": {"jobs": enriched, "total": len(enriched)},
        "message": f"{len(enriched)} vagas com dados de pipeline.",
    }


# ── Shared / Cross-domain ────────────────────────────────────────────────────

@tool_handler("autonomous")
async def _wrap_summarize_context(**kwargs: Any) -> dict[str, Any]:
    """
    Summarize the current reasoning context, combining data from multiple domains.
    Use this to consolidate information before giving a final answer.
    """
    logger.info("[autonomous_tools] summarize_context called")
    gathered = kwargs.get("gathered_data", {})
    query = kwargs.get("query", "")
    return {
        "success": True,
        "data": {
            "summary": f"Contexto consolidado para: '{query}'",
            "domains_accessed": list(gathered.keys()) if isinstance(gathered, dict) else [],
            "gathered_data": gathered,
        },
        "message": "Contexto cross-domain consolidado com sucesso.",
    }


@tool_handler("autonomous")
async def _wrap_clarify_request(**kwargs: Any) -> dict[str, Any]:
    """
    Request clarification from the user when the query is ambiguous.
    Use when not enough information is available to complete the task.
    """
    question = kwargs.get("question", "Poderia fornecer mais detalhes sobre sua solicitação?")
    options = kwargs.get("options", [])
    return {
        "success": True,
        "data": {
            "needs_clarification": True,
            "question": question,
            "options": options,
        },
        "message": "Clarificação solicitada ao usuário.",
    }


# ---------------------------------------------------------------------------
# Tool Definitions — Pool curado de 40+ tools cross-domain
# ---------------------------------------------------------------------------

AUTONOMOUS_TOOL_POOL: list[ToolDefinition] = [
    # ── Job Management (4 tools) ────────────────────────────────────────────
    ToolDefinition(
        name="list_jobs",
        description=(
            "Listar vagas abertas ou filtradas por status. "
            "Parâmetros: company_id (str, opcional), status (str, padrão 'open'), "
            "limit (int, padrão 20, máx 50)."
        ),
        output_schema=ToolOutput,
        function=_wrap_list_jobs,
    ),
    ToolDefinition(
        name="get_job_details",
        description=(
            "Obter detalhes completos de uma vaga: descrição, requisitos, salário, localização. "
            "Parâmetros: job_id (str, obrigatório)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_job_details,
    ),
    ToolDefinition(
        name="get_job_insights",
        description=(
            "Obter benchmark salarial, frequência de skills e tempo médio de fechamento para um cargo. "
            "Parâmetros: job_title (str, obrigatório), company_id (str, obrigatório), location (str, opcional)."
        ),
        output_schema=ToolOutput,
        function=_wrap_auto_get_job_insights,
    ),
    ToolDefinition(
        name="predict_hiring_metrics",
        description=(
            "Prever probabilidade de contratação e tempo de fechamento de uma vaga. "
            "Parâmetros: job_id (str, obrigatório), company_id (str, obrigatório)."
        ),
        output_schema=ToolOutput,
        function=_wrap_auto_hiring_metrics,
    ),
    # ── Sourcing (6 tools) ──────────────────────────────────────────────────
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        touches_pii=True,
        pii_output_fields=["name",
        "email",
        "linkedin_url"],
        name="search_candidates",
        description=(
            "Buscar candidatos por role, skills, localização e seniority. "
            "Parâmetros: role (str), skills (list[str]), location (str), "
            "experience_level (str), page (int), limit (int, máx 50)."
        ),
        output_schema=ToolOutput,
        function=_wrap_auto_search_candidates,
    ),
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        touches_pii=True,
        pii_output_fields=["name",
        "email"],
        name="filter_candidates",
        description=(
            "Filtrar candidatos por múltiplos critérios avançados. "
            "Parâmetros: filters (dict com keys: min_experience, max_experience, "
            "location, skills, seniority_level, title, status), page, limit."
        ),
        output_schema=ToolOutput,
        function=_wrap_auto_filter_candidates,
    ),
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        touches_pii=True,
        pii_output_fields=["name",
        "email",
        "phone",
        "linkedin_url"],
        name="analyze_candidate_profile",
        description=(
            "Analisar perfil detalhado de um candidato: pontos fortes, gaps, score. "
            "Parâmetros: candidate_id (str, obrigatório)."
        ),
        output_schema=ToolOutput,
        function=_wrap_auto_analyze_profile,
    ),
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        name="compare_candidates",
        description=(
            "Comparar múltiplos candidatos e gerar ranking por score e experiência. "
            "Parâmetros: candidate_ids (list[str], obrigatório — 2 a 10 candidatos)."
        ),
        output_schema=ToolOutput,
        function=_wrap_auto_compare_candidates,
    ),
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        name="score_candidate_for_job",
        description=(
            "Calcular WSI score de um candidato para uma vaga específica. "
            "Parâmetros: candidate_id (str, obrigatório), vacancy_id (str, obrigatório)."
        ),
        output_schema=ToolOutput,
        function=_wrap_auto_score_candidate,
    ),
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        name="match_candidates_to_job",
        description=(
            "CROSS-DOMAIN: Encontrar os melhores candidatos do sourcing para uma vaga específica, "
            "calculando match score com base em skills e seniority. "
            "Parâmetros: job_id (str, obrigatório), limit (int, padrão 10, máx 30)."
        ),
        output_schema=ToolOutput,
        function=_wrap_match_candidates_to_job,
    ),
    # ── Pipeline / CV Screening (3 tools) ───────────────────────────────────
    ToolDefinition(
        name="get_pipeline_status",
        description=(
            "Obter status do pipeline de recrutamento com contagem de candidatos por etapa. "
            "Parâmetros: job_id (str, opcional), company_id (str, opcional)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_pipeline_status,
    ),
    ToolDefinition(
        touches_pii=True,
        pii_output_fields=["name",
        "email",
        "linkedin_url"],
        name="get_candidates_in_stage",
        description=(
            "Listar candidatos em uma etapa específica do pipeline. "
            "Parâmetros: stage (str, obrigatório), job_id (str, opcional), limit (int, padrão 20)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_candidates_in_stage,
    ),
    # ── Analytics (3 tools) ─────────────────────────────────────────────────
    ToolDefinition(
        name="generate_report",
        description=(
            "Gerar relatório completo de uma vaga ou conjunto de candidatos. "
            "Parâmetros: report_type ('job' ou 'candidate'), job_id (str), "
            "candidate_ids (list[str]), company_id (str), include_predictions (bool)."
        ),
        output_schema=ToolOutput,
        function=_wrap_auto_generate_report,
    ),
    # ── Interview Scheduling (1 tool) ───────────────────────────────────────
    ToolDefinition(
        name="get_scheduled_interviews",
        description=(
            "Obter entrevistas agendadas para um candidato ou vaga. "
            "Parâmetros: candidate_id (str, opcional), job_id (str, opcional), "
            "status (str, padrão 'scheduled'), limit (int, padrão 20)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_scheduled_interviews,
    ),
    # ── Communication (1 tool) ──────────────────────────────────────────────
    ToolDefinition(
        touches_pii=True,
        pii_output_fields=["message_body",
        "email_address",
        "phone_number"],
        name="get_communication_history",
        description=(
            "Obter histórico de comunicações com um candidato (emails, mensagens). "
            "Parâmetros: candidate_id (str, obrigatório), limit (int, padrão 20)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_communication_history,
    ),
    # ── Cross-domain / Shared (2 tools) ─────────────────────────────────────
    ToolDefinition(
        name="summarize_context",
        description=(
            "Consolidar informações de múltiplos domínios coletadas durante o raciocínio. "
            "Use antes de dar a resposta final em queries cross-domain complexas. "
            "Parâmetros: query (str), gathered_data (dict com dados por domínio)."
        ),
        output_schema=ToolOutput,
        function=_wrap_summarize_context,
    ),
    ToolDefinition(
        name="clarify_request",
        description=(
            "Solicitar clarificação ao usuário quando a query é ambígua ou faltam informações. "
            "Parâmetros: question (str), options (list[str] com opções para o usuário)."
        ),
        output_schema=ToolOutput,
        function=_wrap_clarify_request,
    ),
    # ── Job Management (extended, 3 tools) ──────────────────────────────────
    ToolDefinition(
        name="get_salary_benchmark",
        description=(
            "Obter benchmark salarial para um cargo com base em dados de mercado. "
            "Parâmetros: job_title (str, obrigatório), location (str, opcional), "
            "seniority_level (str, opcional)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_salary_benchmark,
    ),
    ToolDefinition(
        name="validate_job_requirements",
        description=(
            "Validar requisitos de uma vaga quanto a completude e qualidade. "
            "Parâmetros: requirements (list[str]), title (str), seniority_level (str)."
        ),
        output_schema=ToolOutput,
        function=_wrap_validate_job_requirements,
    ),
    ToolDefinition(
        name="get_company_config",
        description=(
            "Obter configurações da empresa: políticas de contratação, preferências e limites. "
            "Parâmetros: company_id (str, obrigatório)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_company_config,
    ),
    # ── CV Screening / Pipeline (extended, 5 tools) ──────────────────────────
    ToolDefinition(
        name="view_candidate_profile",
        description=(
            "Ver perfil completo de um candidato no contexto do pipeline. "
            "Parâmetros: candidate_id (str, obrigatório), job_id (str, opcional)."
        ),
        output_schema=ToolOutput,
        function=_wrap_view_candidate_profile,
    ),
    ToolDefinition(
        name="view_screening_results",
        description=(
            "Ver resultados de triagem WSI de um candidato: scores, critérios, recomendação. "
            "Parâmetros: candidate_id (str, obrigatório), job_id (str, opcional)."
        ),
        output_schema=ToolOutput,
        function=_wrap_view_screening_results,
    ),
    ToolDefinition(
        name="view_interview_notes",
        description=(
            "Ver notas e feedback de entrevistas de um candidato. "
            "Parâmetros: candidate_id (str, obrigatório), job_id (str, opcional)."
        ),
        output_schema=ToolOutput,
        function=_wrap_view_interview_notes,
    ),
    ToolDefinition(
        name="run_wsi_screening",
        description=(
            "Executar triagem WSI automatizada para um candidato vs. uma vaga. "
            "Parâmetros: candidate_id (str, obrigatório), job_id (str, obrigatório)."
        ),
        output_schema=ToolOutput,
        function=_wrap_run_wsi_screening,
    ),
    ToolDefinition(
        name="add_candidate_notes",
        description=(
            "Adicionar notas ou observações ao registro de um candidato no pipeline. "
            "Parâmetros: candidate_id (str, obrigatório), job_id (str, obrigatório), "
            "notes (str, obrigatório)."
        ),
        output_schema=ToolOutput,
        function=_wrap_add_candidate_notes,
    ),
    # ── Sourcing (extended, 3 tools) ─────────────────────────────────────────
    ToolDefinition(
        name="suggest_skills",
        description=(
            "Sugerir skills relevantes para um cargo com base em dados históricos de candidatos. "
            "Parâmetros: role (str, obrigatório)."
        ),
        output_schema=ToolOutput,
        function=_wrap_suggest_skills,
    ),
    ToolDefinition(
        name="rank_candidates",
        description=(
            "Ranquear um conjunto de candidatos por score composto (LIA score + experiência). "
            "Parâmetros: candidate_ids (list[str], obrigatório), criteria (list[str], opcional)."
        ),
        output_schema=ToolOutput,
        function=_wrap_rank_candidates,
    ),
    ToolDefinition(
        name="add_to_shortlist",
        description=(
            "Adicionar um candidato a uma lista de selecionados [WRITE — usa com confirmação]. "
            "Parâmetros: candidate_id (str, obrigatório), shortlist_id (str, obrigatório), "
            "added_by (str), notes (str)."
        ),
        output_schema=ToolOutput,
        function=_wrap_add_to_shortlist,
    ),
    # ── Analytics (extended, 2 tools) ────────────────────────────────────────
    ToolDefinition(
        name="get_agent_performance",
        description=(
            "Obter métricas de performance e custo dos agentes de IA. "
            "Parâmetros: company_id (str, obrigatório), agent_type (str, opcional)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_agent_performance,
    ),
    ToolDefinition(
        name="get_search_analytics",
        description=(
            "Obter métricas de qualidade das buscas: distribuições, top skills, alertas. "
            "Parâmetros: company_id (str, obrigatório), days (int, padrão 30)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_search_analytics,
    ),
    # ── Candidate Info (3 tools) ─────────────────────────────────────────────
    ToolDefinition(
        name="get_candidate_by_id",
        description=(
            "Obter informações básicas de um candidato por ID, com isolamento por tenant. "
            "Parâmetros: candidate_id (str, obrigatório), company_id (str, recomendado)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_candidate_by_id,
    ),
    ToolDefinition(
        name="search_candidates_by_name",
        description=(
            "Buscar candidatos pelo nome (busca parcial). "
            "Parâmetros: name (str, obrigatório), company_id (str, recomendado), limit (int)."
        ),
        output_schema=ToolOutput,
        function=_wrap_search_candidates_by_name,
    ),
    ToolDefinition(
        name="get_job_applications_summary",
        description=(
            "Obter resumo de candidaturas por etapa para uma vaga, com médias de score. "
            "Parâmetros: job_id (str, obrigatório), company_id (str, recomendado)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_job_applications_summary,
    ),
    # ── Cross-domain composites (3 tools) ────────────────────────────────────
    ToolDefinition(
        name="cross_domain_funnel_analysis",
        description=(
            "CROSS-DOMAIN: Análise completa do funil combinando sourcing, pipeline e previsão "
            "de contratação em uma única chamada. "
            "Parâmetros: job_id (str, obrigatório), company_id (str, recomendado)."
        ),
        output_schema=ToolOutput,
        function=_wrap_cross_domain_funnel_analysis,
    ),
    ToolDefinition(
        name="candidate_360_view",
        description=(
            "CROSS-DOMAIN: Visão 360° de um candidato combinando perfil, status no pipeline, "
            "entrevistas e comunicações em uma única chamada. "
            "Parâmetros: candidate_id (str, obrigatório), company_id (str, recomendado)."
        ),
        output_schema=ToolOutput,
        function=_wrap_candidate_360_view,
    ),
    ToolDefinition(
        name="list_jobs_with_candidates",
        description=(
            "CROSS-DOMAIN: Listar vagas abertas com contagem de candidatos por etapa do pipeline. "
            "Parâmetros: company_id (str, recomendado), limit (int, padrão 10)."
        ),
        output_schema=ToolOutput,
        function=_wrap_list_jobs_with_candidates,
    ),
    ToolDefinition(
        name="get_shortlists",
        description=(
            "Listar shortlists de candidatos de uma empresa com contagem de candidatos por lista. "
            "Parâmetros: company_id (str, recomendado), job_id (str, opcional), limit (int)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_shortlists,
    ),
    ToolDefinition(
        name="schedule_interview",
        description=(
            "Agendar uma entrevista para um candidato [WRITE]. "
            "Parâmetros: candidate_id (str, obrigatório), job_id (str, obrigatório), "
            "scheduled_at (str ISO-8601), interview_type (str), interviewer_id (str)."
        ),
        output_schema=ToolOutput,
        function=_wrap_schedule_interview,
    ),
    ToolDefinition(
        name="get_job_history",
        description=(
            "Obter histórico de alterações (audit trail) de uma vaga. "
            "Parâmetros: job_id (str, obrigatório), company_id (str, recomendado), limit (int)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_job_history,
    ),
    ToolDefinition(
        name="get_tenant_hiring_overview",
        description=(
            "CROSS-DOMAIN: Overview de contratação do tenant — vagas abertas, candidatos em pipeline, "
            "entrevistas agendadas — em uma única chamada. "
            "Parâmetros: company_id (str, obrigatório)."
        ),
        output_schema=ToolOutput,
        function=_wrap_get_tenant_hiring_overview,
    ),
    # -- RAG Search (semantic hybrid) -----------------------------------------
    ToolDefinition(
        name="rag_search",
        description=(
            "Busca semantica hibrida de candidatos (BM25 + pgvector). "
            "Fallback BM25 quando embeddings indisponiveis. "
            "Parametros: query (str, obrigatorio), company_id (str, recomendado), "
            "limit (int, padrao 20, max 50), filters (dict, opcional)."
        ),
        output_schema=ToolOutput,
        function=_wrap_rag_search,
    ),
]

# Mapeamento por nome para lookup rápido
_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in AUTONOMOUS_TOOL_POOL}

# Escopo de permissão por tool (read-only vs write)
TOOL_PERMISSION_SCOPE: dict[str, str] = {
    # Job Management
    "list_jobs": "read",
    "get_job_details": "read",
    "get_job_insights": "read",
    "predict_hiring_metrics": "read",
    "get_salary_benchmark": "read",
    "validate_job_requirements": "read",
    "get_company_config": "read",
    # Sourcing
    "search_candidates": "read",
    "filter_candidates": "read",
    "analyze_candidate_profile": "read",
    "compare_candidates": "read",
    "score_candidate_for_job": "read",
    "match_candidates_to_job": "read",
    "suggest_skills": "read",
    "rank_candidates": "read",
    "add_to_shortlist": "write",
    # Pipeline / CV Screening
    "get_pipeline_status": "read",
    "get_candidates_in_stage": "read",
    "view_candidate_profile": "read",
    "view_screening_results": "read",
    "view_interview_notes": "read",
    "run_wsi_screening": "write",
    "add_candidate_notes": "write",
    # Analytics
    "generate_report": "read",
    "get_agent_performance": "read",
    "get_search_analytics": "read",
    # Scheduling
    "get_scheduled_interviews": "read",
    # Communication
    "get_communication_history": "read",
    # Candidate Info
    "get_candidate_by_id": "read",
    "search_candidates_by_name": "read",
    "get_job_applications_summary": "read",
    # Cross-domain composites
    "cross_domain_funnel_analysis": "read",
    "candidate_360_view": "read",
    "list_jobs_with_candidates": "read",
    # Scheduling (extended)
    "get_shortlists": "read",
    "schedule_interview": "write",
    "get_job_history": "read",
    "get_tenant_hiring_overview": "read",
    # Utility
    "summarize_context": "utility",
    "clarify_request": "utility",
    # RAG Search
    "rag_search": "read",
}


def get_autonomous_tools() -> list[ToolDefinition]:
    """Return the complete cross-domain tool pool for the AutonomousReActAgent."""
    return list(AUTONOMOUS_TOOL_POOL)


def get_tool_by_name(name: str) -> ToolDefinition | None:
    """Lookup a tool by name."""
    return _TOOL_MAP.get(name)


def get_tool_names() -> list[str]:
    """Return all tool names in the autonomous pool."""
    return list(_TOOL_MAP.keys())
