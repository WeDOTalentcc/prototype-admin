"""
Wizard Tool Registry - Exposes wizard tools to the ReAct loop.

Wraps existing job_wizard_tools functions into ToolDefinition format
so the ReActLoop can autonomously decide which tools to call.
"""
import logging
import uuid
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput
from sqlalchemy import text as sql_text

from app.core.database import AsyncSessionLocal
from app.domains.job_management.tools.job_wizard_tools import (
    generate_enriched_jd as _generate_enriched_jd,
)
from app.domains.job_management.tools.job_wizard_tools import (
    get_company_config as _get_company_config,
)
from app.domains.job_management.tools.job_wizard_tools import (
    get_job_suggestions as _get_job_suggestions,
)
from app.domains.job_management.tools.job_wizard_tools import (
    save_job_draft as _save_job_draft,
)
from app.domains.job_management.tools.job_wizard_tools import (
    search_salary_benchmark as _search_salary_benchmark,
)
from app.domains.job_management.tools.job_wizard_tools import (
    validate_job_fields as _validate_job_fields,
)
from app.shared.compliance.fairness_guard import FairnessGuard

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_SALARY_FALLBACK = {
    "estagio": {"min": 1200, "max": 2500, "currency": "BRL"},
    "estagiario": {"min": 1200, "max": 2500, "currency": "BRL"},
    "junior": {"min": 3000, "max": 6000, "currency": "BRL"},
    "júnior": {"min": 3000, "max": 6000, "currency": "BRL"},
    "pleno": {"min": 6000, "max": 12000, "currency": "BRL"},
    "senior": {"min": 12000, "max": 22000, "currency": "BRL"},
    "sênior": {"min": 12000, "max": 22000, "currency": "BRL"},
    "especialista": {"min": 15000, "max": 28000, "currency": "BRL"},
    "gerente": {"min": 18000, "max": 35000, "currency": "BRL"},
    "diretor": {"min": 30000, "max": 60000, "currency": "BRL"},
    "c-level": {"min": 40000, "max": 80000, "currency": "BRL"},
}


async def _fetch_market_range(job_title: str, seniority: str, location: str | None = None) -> dict[str, Any]:
    """Fetch market salary range from MarketBenchmarkService, falling back to
    static estimates only when the external service is unavailable."""
    try:
        from app.domains.analytics.services.market_benchmark_service import MarketBenchmarkService
        service = MarketBenchmarkService()
        data = await service.search_salary_benchmark(
            role=job_title or seniority,
            seniority=seniority,
            location=location,
        )
        if data and data.get("min") and data.get("max"):
            return {
                "min": data["min"],
                "max": data["max"],
                "currency": data.get("currency", "BRL"),
                "sources": data.get("sources", []),
                "confidence": data.get("confidence", "medium"),
                "is_external": True,
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[wizard_tools] MarketBenchmarkService unavailable, using fallback: {e}")
    import unicodedata

    seniority_key = seniority.lower().strip() if seniority else "pleno"
    seniority_key = unicodedata.normalize("NFKD", seniority_key).encode("ascii", "ignore").decode("ascii")
    fallback = _SALARY_FALLBACK.get(seniority_key, _SALARY_FALLBACK.get("pleno"))
    return {
        "min": fallback["min"] if fallback else 6000,
        "max": fallback["max"] if fallback else 12000,
        "currency": "BRL",
        "sources": ["Estimativa interna (fallback)"],
        "confidence": "low",
        "is_external": False,
    }

_fairness_guard = FairnessGuard()


# ── Phase E — vacancy stage-action helpers ──────────────────────────────
async def _load_vacancy_or_error(
    vacancy_id: str | None,
    company_id: str | None,
):
    """Load a JobVacancy scoped to the agent's company.

    Returns the vacancy on success, or a {error, ...} dict on failure
    (cross-tenant / missing / no auth context). Tools call this first
    and short-circuit when the dict is returned.

    Multi-tenancy: company_id is the *agent context* value the wizard
    passes per session — never from LLM-generated args. The repo method
    enforces the WHERE company_id = :id clause on the SQL query.

    ADR-001 W1-004-C: migrated from inline select() to repo method.
    """
    if not vacancy_id:
        return {"error": "vacancy_id required", "is_error": True}
    if not company_id:
        return {"error": "company_id missing from agent context", "is_error": True}

    # ADR-001 W1-004-C MIGRATE 1: uses JobVacancyCrudRepository.get_by_id_strict_company
    # instead of inline select(JobVacancy). Fail-closed via _require_company_id.
    from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCrudRepository

    async with AsyncSessionLocal() as db:
        try:
            repo = JobVacancyCrudRepository(db)
            job = await repo.get_by_id_strict_company(vacancy_id, company_id)
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"[wizard_tools] vacancy load error: {e}", exc_info=True)
            return {"error": f"db error: {e}", "is_error": True}

    if not job:
        # Return the same opaque error for missing vs cross-tenant to avoid
        # leaking ID existence to the LLM.
        return {"error": "vacancy not found", "is_error": True}

    return job


@tool_handler("wizard")
async def _wrap_generate_screening_questions(**kwargs: Any) -> dict[str, Any]:
    """Phase E — generate WSI screening questions (compact 5 / complete 15)."""
    vacancy_id = kwargs.get("vacancy_id")
    mode = (kwargs.get("mode") or "compact").lower()
    company_id = kwargs.get("company_id")

    if mode not in ("compact", "complete"):
        return {"is_error": True, "error": f"mode must be 'compact' or 'complete' (got {mode!r})"}
    max_q = 5 if mode == "compact" else 15

    job = await _load_vacancy_or_error(vacancy_id, company_id)
    if isinstance(job, dict):
        return job

    # Allowed stages — fail fast with a structured error if invoked out of stage.
    # The wizard ReAct loop SHOULD only offer this tool in 'enriquecida', but a
    # belt-and-suspenders check keeps the contract honest if the loop drifts.
    if not getattr(job, "enriched_jd", None):
        return {
            "is_error": True,
            "error": "vacancy has no enriched_jd yet — enrich the JD first",
            "stage_check": "blocked_pre_enrichment",
        }

    try:
        # Reuse the same generate_questions service the HTTP endpoint uses.
        from app.api.v1.wsi.questions import GenerateQuestionsRequest, generate_questions
        from app.shared.fastapi_dependencies import get_db
        async with AsyncSessionLocal() as db:
            req = GenerateQuestionsRequest(
                skills=getattr(job, "required_skills", None) or [],
                technical_skills=getattr(job, "technical_requirements", None) or [],
                behavioral_competencies=getattr(job, "behavioral_competencies", None) or [],
                seniority_level=getattr(job, "seniority_level", None) or "pleno",
                job_title=job.title,
                max_questions=max_q,
                description=getattr(job, "description", None),
                requirements=getattr(job, "technical_requirements", None) or [],
            )
            result = await generate_questions(req, db=db)
            return {
                "is_error": False,
                "vacancy_id": str(vacancy_id),
                "mode": mode,
                "questions_count": len(getattr(result, "questions", []) or []),
                "questions": [q.model_dump() if hasattr(q, "model_dump") else q
                              for q in (getattr(result, "questions", []) or [])],
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[wizard_tools] generate_screening_questions error: {e}", exc_info=True)
        return {"is_error": True, "error": str(e)}


@tool_handler("wizard")
async def _wrap_dispatch_screening(**kwargs: Any) -> dict[str, Any]:
    """Phase E — dispatch WSI screening to candidates pending in a vacancy."""
    vacancy_id = kwargs.get("vacancy_id")
    company_id = kwargs.get("company_id")
    audience_policy = (kwargs.get("audience_policy") or "new_only").lower()

    job = await _load_vacancy_or_error(vacancy_id, company_id)
    if isinstance(job, dict):
        return job

    try:
        from app.domains.job_management.services.job_readiness_service import (
            JobReadinessService, AUDIENCE_POLICIES,
        )
        if audience_policy not in AUDIENCE_POLICIES:
            return {
                "is_error": True,
                "error": f"audience_policy must be one of {sorted(AUDIENCE_POLICIES)}",
            }
        async with AsyncSessionLocal() as db:
            svc = JobReadinessService(db=db)
            updated = await svc.dispatch_screening(
                job, actor=f"wizard:{company_id}", audience_policy=audience_policy,
            )
            await db.commit()
            return {
                "is_error": False,
                "vacancy_id": str(vacancy_id),
                "status": updated.status,
                "audience_policy": audience_policy,
                "message": "Triagem WSI ativada",
            }
    except ValueError as ve:
        # The service raises ValueError on stage / policy mismatch.
        return {"is_error": True, "error": str(ve), "stage_check": "blocked"}
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[wizard_tools] dispatch_screening error: {e}", exc_info=True)
        return {"is_error": True, "error": str(e)}


@tool_handler("wizard")
async def _wrap_request_approval(**kwargs: Any) -> dict[str, Any]:
    """Phase I.8 — request approval of WSI screening questions.

    Mirror of the UI's 'Solicitar aprovação' button (Phase I.1, commit
    2bb6dad3c). Sets approval_status='pendente' + approval_requested_at via
    JobReadinessService.approve_stage; the lifecycle classifier then moves
    the vacancy from wsi_config to aguardando_aprovacao.

    Stage allowlist: wsi_config (registered in STAGE_TOOLS below).
    Multi-tenancy: company_id REQUIRED in args; vacancy resolved via
    _load_vacancy_or_error (cross-tenant returns opaque 'not found').
    """
    vacancy_id = kwargs.get("vacancy_id")
    company_id = kwargs.get("company_id")

    job = await _load_vacancy_or_error(vacancy_id, company_id)
    if isinstance(job, dict):
        return job

    try:
        from app.domains.job_management.services.job_readiness_service import (
            JobReadinessService,
        )
        async with AsyncSessionLocal() as db:
            svc = JobReadinessService(db=db)
            updated = await svc.approve_stage(job, actor=f"wizard:{company_id}")
            await db.commit()
            return {
                "is_error": False,
                "vacancy_id": str(vacancy_id),
                "approval_status": getattr(updated, "approval_status", None),
                "message": "Aprovação solicitada — vaga aguarda revisão",
            }
    except ValueError as ve:
        # The service raises ValueError on stage / state mismatch
        # (e.g., trying to approve a vaga that has no screening_questions yet).
        return {"is_error": True, "error": str(ve), "stage_check": "blocked"}
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[wizard_tools] request_approval error: {e}", exc_info=True)
        return {"is_error": True, "error": str(e)}


@tool_handler("wizard")
async def _wrap_publish_vacancy(**kwargs: Any) -> dict[str, Any]:
    """Phase E — publish (status -> Ativa) or unpublish (clear flags) a vacancy."""
    vacancy_id = kwargs.get("vacancy_id")
    company_id = kwargs.get("company_id")
    action = (kwargs.get("action") or "publish").lower()

    if action not in ("publish", "unpublish"):
        return {"is_error": True, "error": "action must be 'publish' or 'unpublish'"}

    job = await _load_vacancy_or_error(vacancy_id, company_id)
    if isinstance(job, dict):
        return job

    try:
        from app.domains.job_management.repositories.job_vacancy_lifecycle_repository import (
            JobVacancyLifecycleRepository,
        )
        async with AsyncSessionLocal() as db:
            # Re-attach the loaded job to this session.
            db.add(job)
            repo = JobVacancyLifecycleRepository(db)
            if action == "publish":
                updated = await repo.publish_vacancy_v2(job)
                await db.commit()
                return {
                    "is_error": False,
                    "vacancy_id": str(vacancy_id),
                    "status": updated.status,
                    "message": "Vaga publicada",
                }
            else:
                updated, changed = await repo.unpublish_vacancy(job)
                await db.commit()
                return {
                    "is_error": False,
                    "vacancy_id": str(vacancy_id),
                    "status": updated.status,
                    "changed": changed,
                    "message": "Vaga despublicada" if changed else "Vaga já estava despublicada",
                }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[wizard_tools] publish_vacancy error: {e}", exc_info=True)
        return {"is_error": True, "error": str(e)}


@tool_handler("wizard")
async def _wrap_change_vacancy_status(**kwargs: Any) -> dict[str, Any]:
    """Phase E — change a vacancy's status (Pausada / Concluída / Cancelada / Arquivada / Ativa)."""
    vacancy_id = kwargs.get("vacancy_id")
    company_id = kwargs.get("company_id")
    new_status = kwargs.get("status")

    from app.api.v1.job_vacancies._shared import VALID_JOB_STATUSES
    if new_status not in VALID_JOB_STATUSES:
        return {
            "is_error": True,
            "error": f"status must be one of {VALID_JOB_STATUSES} (got {new_status!r})",
        }

    job = await _load_vacancy_or_error(vacancy_id, company_id)
    if isinstance(job, dict):
        return job

    try:
        from app.domains.job_management.repositories.job_vacancy_lifecycle_repository import (
            JobVacancyLifecycleRepository,
        )
        async with AsyncSessionLocal() as db:
            db.add(job)
            repo = JobVacancyLifecycleRepository(db)
            updated = await repo.update_vacancy_status(job, new_status)
            await db.commit()
            return {
                "is_error": False,
                "vacancy_id": str(vacancy_id),
                "old_status": job.status,
                "new_status": updated.status,
                "message": f"Status alterado para {updated.status}",
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[wizard_tools] change_vacancy_status error: {e}", exc_info=True)
        return {"is_error": True, "error": str(e)}


@tool_handler("wizard")
async def _wrap_validate_job_requirements(**kwargs: Any) -> dict[str, Any]:
    text = kwargs.get("text", "")
    field_name = kwargs.get("field_name", "requirements")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[wizard_tools] validate_job_requirements called for field={field_name}")
    try:
        explicit_result = _fairness_guard.check(text)
        implicit_warnings = _fairness_guard.check_implicit_bias(text)

        if explicit_result.is_blocked:
            return {
                "is_compliant": False,
                "educational_message": explicit_result.educational_message,
                "blocked_terms": explicit_result.blocked_terms,
                "category": explicit_result.category,
                "soft_warnings": implicit_warnings,
                "field_name": field_name,
            }

        semantic_warnings = []
        try:
            semantic_result = await _fairness_guard.check_semantic(text, context=f"job_{field_name}")
            if semantic_result.is_blocked:
                return {
                    "is_compliant": False,
                    "educational_message": semantic_result.educational_message,
                    "blocked_terms": semantic_result.blocked_terms,
                    "category": semantic_result.category,
                    "soft_warnings": implicit_warnings + (semantic_result.soft_warnings or []),
                    "field_name": field_name,
                }
            semantic_warnings = semantic_result.soft_warnings or []
        except Exception as sem_err:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.debug(f"[wizard_tools] semantic check skipped: {sem_err}")

        all_warnings = implicit_warnings + [w for w in semantic_warnings if w not in implicit_warnings]

        return {
            "is_compliant": True,
            "educational_message": None,
            "soft_warnings": all_warnings,
            "field_name": field_name,
        }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[wizard_tools] validate_job_requirements error: {e}", exc_info=True)
        return {"is_compliant": True, "soft_warnings": [], "error": str(e)}


@tool_handler("wizard")
async def _wrap_get_salary_benchmarks(**kwargs: Any) -> dict[str, Any]:
    job_title = kwargs.get("job_title", "")
    seniority = kwargs.get("seniority", "pleno")
    location = kwargs.get("location", "")
    department = kwargs.get("department", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[wizard_tools] get_salary_benchmarks called for title={job_title}, seniority={seniority}")

    internal_avg: dict[str, Any] | None = None
    # ADR-001-EXEMPT: salary benchmark aggregation (AVG/MIN/MAX by role+dept GROUP BY) —
    # analytics query, not abstractable to simple repo method without over-engineering.
    try:
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            query = sql_text("""
                SELECT
                    AVG((salary_range->>'min')::float) as avg_min,
                    AVG((salary_range->>'max')::float) as avg_max,
                    COUNT(*) as total_vagas
                FROM job_vacancies
                WHERE salary_range IS NOT NULL
                  AND (title ILIKE :title_pattern OR department = :dept)
            """)
            result = await db.execute(query, {
                "title_pattern": f"%{job_title}%",
                "dept": department or "",
            })
            row = result.fetchone()
            if row and row.total_vagas and row.total_vagas > 0:
                internal_avg = {
                    "avg_min": round(float(row.avg_min), 2) if row.avg_min else None,
                    "avg_max": round(float(row.avg_max), 2) if row.avg_max else None,
                    "sample_size": int(row.total_vagas),
                    "source": "Histórico interno da empresa",
                }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[wizard_tools] get_salary_benchmarks SQL error (non-fatal): {e}")

    market_range = await _fetch_market_range(job_title, seniority, location)

    recommendation = None
    if internal_avg and internal_avg.get("avg_min") and market_range:
        if internal_avg["avg_min"] < market_range["min"] * 0.8:
            recommendation = (
                f"O histórico interno (R$ {internal_avg['avg_min']:,.0f}-{internal_avg['avg_max']:,.0f}) "
                f"está abaixo do benchmark de mercado (R$ {market_range['min']:,.0f}-{market_range['max']:,.0f}) "
                f"para nível {seniority}. Considere ajustar para atrair melhores candidatos."
            )
        elif internal_avg["avg_max"] and internal_avg["avg_max"] > market_range["max"] * 1.2:
            recommendation = (
                f"O histórico interno (R$ {internal_avg['avg_min']:,.0f}-{internal_avg['avg_max']:,.0f}) "
                f"está acima do benchmark de mercado (R$ {market_range['min']:,.0f}-{market_range['max']:,.0f}) "
                f"para nível {seniority}. A empresa oferece remuneração competitiva."
            )
        else:
            recommendation = (
                f"O histórico interno está alinhado com o benchmark de mercado "
                f"(R$ {market_range['min']:,.0f}-{market_range['max']:,.0f}) para nível {seniority}."
            )
    elif market_range:
        recommendation = (
            f"Sem histórico interno disponível. Benchmark de mercado para {seniority}: "
            f"R$ {market_range['min']:,.0f}-{market_range['max']:,.0f}."
        )

    return {
        "internal_avg": internal_avg,
        "market_range": {
            "min": market_range["min"] if market_range else None,
            "max": market_range["max"] if market_range else None,
            "currency": market_range.get("currency", "BRL"),
            "seniority": seniority,
            "confidence": market_range.get("confidence", "low"),
        },
        "sources": market_range.get("sources", []),
        "recommendation": recommendation,
        "job_title": job_title,
        "location": location or "Brasil",
    }


@tool_handler("wizard")
async def _wrap_search_salary_benchmark(**kwargs: Any) -> dict[str, Any]:
    """Wrapper for search_salary_benchmark that handles errors gracefully."""
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[wizard_tools] search_salary_benchmark called with: {list(kwargs.keys())}")
    return await _search_salary_benchmark(**kwargs)
@tool_handler("wizard")
async def _wrap_validate_job_fields(**kwargs: Any) -> dict[str, Any]:
    """Wrapper for validate_job_fields that handles errors gracefully."""
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[wizard_tools] validate_job_fields called with: {list(kwargs.keys())}")
    return await _validate_job_fields(**kwargs)
@tool_handler("wizard")
async def _wrap_get_job_suggestions(**kwargs: Any) -> dict[str, Any]:
    """Wrapper for get_job_suggestions that handles errors gracefully."""
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[wizard_tools] get_job_suggestions called with: {list(kwargs.keys())}")
    return await _get_job_suggestions(**kwargs)
@tool_handler("wizard")
async def _wrap_save_job_draft(**kwargs: Any) -> dict[str, Any]:
    """Wrapper for save_job_draft that handles errors gracefully."""
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[wizard_tools] save_job_draft called with: {list(kwargs.keys())}")
    return await _save_job_draft(**kwargs)
@tool_handler("wizard")
async def _wrap_get_company_config(**kwargs: Any) -> dict[str, Any]:
    """Wrapper for get_company_config that handles errors gracefully."""
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[wizard_tools] get_company_config called with: {list(kwargs.keys())}")
    return await _get_company_config(**kwargs)
@tool_handler("wizard")
async def _wrap_generate_enriched_jd(**kwargs: Any) -> dict[str, Any]:
    """Wrapper for generate_enriched_jd that handles errors gracefully."""
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[wizard_tools] generate_enriched_jd called with: {list(kwargs.keys())}")
    return await _generate_enriched_jd(**kwargs)
@tool_handler("wizard")
async def _wrap_check_job_draft_health(**kwargs: Any) -> dict[str, Any]:
    title = kwargs.get("title", "")
    seniority = kwargs.get("seniority", "")
    kwargs.get("salary_min", 0)
    salary_max = kwargs.get("salary_max", 0)
    skills_count = kwargs.get("skills_count", 0)
    responsibilities_count = kwargs.get("responsibilities_count", 0)
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[wizard_tools] check_job_draft_health called: title={title}")

    risks = []

    if not title:
        risks.append({
            "level": "high",
            "type": "missing_title",
            "message": "Titulo da vaga nao definido. Campo obrigatorio.",
        })

    if not seniority:
        risks.append({
            "level": "medium",
            "type": "missing_seniority",
            "message": "Senioridade nao definida. Essencial para calibrar requisitos e remuneracao.",
        })

    if salary_max > 0 and seniority:
        bench = await _fetch_market_range(title or seniority, seniority)
        if bench and salary_max < bench["min"]:
            risks.append({
                "level": "high",
                "type": "salary_below_market",
                "message": f"Salario maximo (R${salary_max:,.0f}) abaixo do piso de mercado (R${bench['min']:,.0f}) para {seniority}. Risco de atracao insuficiente.",
            })

    if skills_count < 3:
        risks.append({
            "level": "medium",
            "type": "few_skills",
            "message": f"Apenas {skills_count} skills definidas. O recomendado e 5-10 para boa triagem WSI.",
        })

    if responsibilities_count < 2:
        risks.append({
            "level": "medium",
            "type": "few_responsibilities",
            "message": f"Apenas {responsibilities_count} responsabilidades. O recomendado e 4-8 para descricao completa.",
        })

    overall_health = "healthy"
    if any(r["level"] == "high" for r in risks):
        overall_health = "critical"
    elif any(r["level"] == "medium" for r in risks):
        overall_health = "attention"

    return {
        "success": True,
        "data": {
            "title": title or "(nao definido)",
            "risks": risks,
            "overall_health": overall_health,
            "completeness": max(0, 100 - len(risks) * 15),
        },
        "message": f"Saude do rascunho: {overall_health}. {len(risks)} riscos identificados.",
    }


TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="validate_job_requirements",
        description="Valida requisitos da vaga contra viés discriminatório usando FairnessGuard. Verifica viés explícito (bloqueia) e implícito (alertas educacionais). Use para validar requirements, description e screening_questions.",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Conteúdo a validar (requisitos, descrição ou perguntas de triagem)"},
                "field_name": {"type": "string", "description": "Campo sendo validado: requirements, description ou screening_questions"},
            },
            "required": ["text", "field_name"],
        },
        output_schema=ToolOutput,
        function=_wrap_validate_job_requirements,
    ),
    ToolDefinition(
        name="get_salary_benchmarks",
        description="Busca benchmarks salariais reais combinando histórico interno da empresa (SQL) com dados de mercado (Robert Half 2024, Gupy). Retorna internal_avg, market_range, sources citáveis e recommendation. Use no estágio salary para fornecer dados concretos.",
        parameters={
            "type": "object",
            "properties": {
                "job_title": {"type": "string", "description": "Titulo do cargo"},
                "seniority": {"type": "string", "description": "Nivel de senioridade (Estagio, Junior, Pleno, Senior, Especialista, Gerente, Diretor)"},
                "location": {"type": "string", "description": "Localizacao/cidade/regiao"},
                "department": {"type": "string", "description": "Departamento da vaga"},
            },
            "required": ["job_title", "seniority"],
        },
        output_schema=ToolOutput,
        function=_wrap_get_salary_benchmarks,
    ),
    ToolDefinition(
        name="search_salary_benchmark",
        description="Busca benchmarks salariais de mercado para um cargo. Retorna faixa salarial com min, max e mediana baseado em dados de mercado.",
        parameters={
            "type": "object",
            "properties": {
                "job_title": {"type": "string", "description": "Titulo do cargo"},
                "seniority": {"type": "string", "description": "Nivel de senioridade (Junior, Pleno, Senior, etc.)"},
                "location": {"type": "string", "description": "Localizacao/cidade"},
                "industry": {"type": "string", "description": "Setor da industria"},
            },
            "required": ["job_title"],
        },
        output_schema=ToolOutput,
        function=_wrap_search_salary_benchmark,
    ),
    ToolDefinition(
        name="validate_job_fields",
        description="Valida os campos preenchidos da vaga. Retorna score de completude, campos preenchidos e campos faltantes.",
        parameters={
            "type": "object",
            "properties": {
                "job_data": {"type": "object", "description": "Dados atuais da vaga"},
                "company_config": {"type": "object", "description": "Configuracao da empresa"},
            },
            "required": ["job_data"],
        },
        output_schema=ToolOutput,
        function=_wrap_validate_job_fields,
    ),
    ToolDefinition(
        name="get_job_suggestions",
        description="Obtem sugestoes de IA para um campo especifico da vaga (skills, beneficios, competencias, modelo de trabalho, etc.).",
        parameters={
            "type": "object",
            "properties": {
                "field_name": {"type": "string", "description": "Nome do campo (skills, behavioral_competencies, benefits, work_model, seniority, etc.)"},
                "job_context": {"type": "object", "description": "Contexto atual da vaga"},
            },
            "required": ["field_name", "job_context"],
        },
        output_schema=ToolOutput,
        function=_wrap_get_job_suggestions,
    ),
    ToolDefinition(
        name="save_job_draft",
        description="Salva o rascunho atual da vaga no banco de dados. Use quando o usuario confirmar dados ou quiser salvar progresso.",
        parameters={
            "type": "object",
            "properties": {
                "draft_id": {"type": "string", "description": "UUID do rascunho"},
                "updates": {"type": "object", "description": "Campos a atualizar"},
                "recruiter_id": {"type": "string", "description": "ID do recrutador"},
            },
            "required": ["draft_id", "updates", "recruiter_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_save_job_draft,
    ),
    ToolDefinition(
        name="get_company_config",
        description="Busca configuracoes da empresa: beneficios, politicas salariais, templates de pipeline, perguntas de triagem e cultura.",
        parameters={
            "type": "object",
            "properties": {
                "config_type": {"type": "string", "description": "Tipo de config: all, benefits, salary_levels, pipeline_templates, screening_questions, communication, culture, ai_context"},
                "seniority": {"type": "string", "description": "Nivel de senioridade para filtrar beneficios"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_get_company_config,
    ),
    ToolDefinition(
        name="generate_enriched_jd",
        description="Gera descricao de vaga enriquecida com sugestoes de responsabilidades, skills, competencias e remuneracao baseadas em benchmarks de mercado.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Titulo do cargo"},
                "seniority": {"type": "string", "description": "Nivel de senioridade"},
                "location": {"type": "string", "description": "Localizacao"},
                "detected_responsibilities": {"type": "array", "items": {"type": "string"}, "description": "Responsabilidades ja detectadas"},
                "detected_skills": {"type": "array", "items": {"type": "string"}, "description": "Skills ja detectadas"},
                "detected_behavioral": {"type": "array", "items": {"type": "string"}, "description": "Competencias comportamentais ja detectadas"},
                "salary_min": {"type": "number", "description": "Salario minimo"},
                "salary_max": {"type": "number", "description": "Salario maximo"},
            },
            "required": ["title"],
        },
        output_schema=ToolOutput,
        function=_wrap_generate_enriched_jd,
    ),
    ToolDefinition(
        name="check_job_draft_health",
        description="Avalia proativamente a saude do rascunho da vaga: identifica riscos como campos faltantes, salario abaixo do mercado, poucas skills ou responsabilidades. Use antes de publicar para garantir qualidade.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Titulo da vaga"},
                "seniority": {"type": "string", "description": "Nivel de senioridade"},
                "salary_min": {"type": "number", "description": "Salario minimo oferecido"},
                "salary_max": {"type": "number", "description": "Salario maximo oferecido"},
                "skills_count": {"type": "integer", "description": "Numero de skills definidas"},
                "responsibilities_count": {"type": "integer", "description": "Numero de responsabilidades definidas"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_check_job_draft_health,
    ),
]


@tool_handler("wizard")
async def _wrap_generate_report(**kwargs: Any) -> dict[str, Any]:
    report_type = kwargs.get("report_type", "summary")
    period = kwargs.get("period", "month")
    company_id = kwargs.get("company_id", "")
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[wizard_tools] generate_report called: type={report_type} period={period}")
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    summary: dict[str, Any] = {}
    try:
        # ADR-001-EXEMPT: report aggregation (COUNT/FILTER by status, MAKE_INTERVAL) —
        # analytics query, not abstractable to simple repo method without over-engineering.
        async with AsyncSessionLocal() as session:
            row = await session.execute(sql_text("""
                SELECT COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status = 'draft') AS drafts,
                    COUNT(*) FILTER (WHERE status = 'published') AS published
                FROM job_vacancies
                WHERE company_id = :cid
                  AND created_at > NOW() - MAKE_INTERVAL(days => :days)
            """), {"cid": company_id, "days": period_days})
            data = row.mappings().first() or {}
            summary = {
                "total_jobs": int(data.get("total") or 0),
                "drafts": int(data.get("drafts") or 0),
                "published": int(data.get("published") or 0),
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[wizard_tools] generate_report DB error: {e}")
    return {
        "success": True,
        "data": {
            "report_type": report_type,
            "period": period,
            "report_id": report_id,
            "generated": True,
            "summary": summary,
        },
        "message": f"Relatorio '{report_type}' de vagas gerado (id: {report_id}). {summary.get('total_jobs', 0)} vagas no periodo.",
    }


TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="generate_report",
        description="Gera relatorio de vagas criadas e publicadas no periodo selecionado.",
        parameters={
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "Tipo de relatorio: summary, detailed"},
                "period": {"type": "string", "description": "Periodo: week, month, quarter"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_generate_report,
    )
)

# ── Phase E — register 4 stage-action tools ──────────────────────────────
TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="generate_screening_questions",
        description="Gera perguntas de triagem WSI para uma vaga. Compacta (5) ou completa (15). Use APENAS quando a vaga já tem JD enriquecido. Retorna lista de questions.",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga (UUID)"},
                "mode": {"type": "string", "enum": ["compact", "complete"], "description": "compact = 5 perguntas; complete = 15 perguntas"},
            },
            "required": ["vacancy_id", "mode"],
        },
        output_schema=ToolOutput,
        function=_wrap_generate_screening_questions,
    )
)
TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="dispatch_screening",
        description="Ativa o disparo de triagem WSI para os candidatos da vaga. Use quando a vaga está em 'aguardando_aprovacao' e o recrutador confirmou. audience_policy: 'new_only' (default, só não-triados) | 'imported_untriaged' | 'manual_selection'.",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga"},
                "audience_policy": {"type": "string", "enum": ["new_only", "imported_untriaged", "manual_selection"], "description": "Política de audiência"},
            },
            "required": ["vacancy_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_dispatch_screening,
    )
)
TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="request_approval",
        description="Solicita aprovação das perguntas de triagem WSI da vaga. Use APENAS quando a vaga já tem perguntas geradas (estágio wsi_config) e o recrutador quer avançar para o estágio aguardando_aprovacao. Backend chama job_readiness/approve-stage e seta approval_status=pendente.",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga (UUID)"},
            },
            "required": ["vacancy_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_request_approval,
    )
)
TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="publish_vacancy",
        description="Publica (status=Ativa) ou despublica (limpa flags published_*) uma vaga. action='publish' (default) ou 'unpublish'.",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga"},
                "action": {"type": "string", "enum": ["publish", "unpublish"], "description": "publish ou unpublish"},
            },
            "required": ["vacancy_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_publish_vacancy,
    )
)
TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="change_vacancy_status",
        description="Altera o status da vaga. Status válidos: Rascunho, Ativa, Pausada, Concluída, Cancelada, Arquivada. Cancelada é terminal — não admite saída.",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga"},
                "status": {"type": "string", "enum": ["Rascunho", "Ativa", "Pausada", "Concluída", "Cancelada", "Arquivada"], "description": "Novo status"},
            },
            "required": ["vacancy_id", "status"],
        },
        output_schema=ToolOutput,
        function=_wrap_change_vacancy_status,
    )
)



# ─── Eligibility Question Templates wizard tools (audit 2026-05-20 Sprint 1 F5) ──
# 3 tools canonical pro wizard conversacional de criacao de vaga manusear o
# catalogo dinamico de eligibility-question-templates (substitui catalogo
# hardcoded `plataforma-lia/.../eligibility-questions-bank.ts`).

@tool_handler("wizard")
async def _wrap_suggest_eligibility_templates(**kwargs):
    """
    Sugere templates de elegibilidade canonical relevantes para a vaga em
    criacao baseado em job_industry, work_model, languages e categorias mais
    pertinentes.

    Multi-tenancy: company_id obrigatorio via ContextVar JWT (@tool_handler).
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.cv_screening.repositories.eligibility_question_template_repository import (
        EligibilityQuestionTemplateRepository,
    )

    company_id = kwargs.get("company_id")
    job_industry = (kwargs.get("industry") or "").lower()
    work_model = (kwargs.get("work_model") or "").lower()
    languages = kwargs.get("languages") or []

    PRIORITY_CATEGORIES = ["system_default", "eligibility", "availability", "compliance"]

    async with AsyncSessionLocal() as db:
        repo = EligibilityQuestionTemplateRepository(db)
        all_items = await repo.list_for_company(
            company_id=company_id, include_master=True
        )

    suggestions = []
    for item in all_items:
        data = item.data or {}
        category = data.get("category", "")
        # Score: priority category + linkedField match + languages match
        score = 0
        if category in PRIORITY_CATEGORIES:
            score += 3
        linked = data.get("linkedField")
        if linked == "workModel" and work_model:
            score += 5
        if linked == "languages" and languages:
            score += 5
        if linked == "location" and work_model in ("hibrido", "presencial"):
            score += 4
        if score > 0:
            suggestions.append({
                "id": str(item.id),
                "question": data.get("question", ""),
                "category": category,
                "is_master": item.is_master_template,
                "score": score,
            })

    suggestions.sort(key=lambda s: s["score"], reverse=True)
    top = suggestions[:10]

    return {
        "success": True,
        "data": {
            "suggestions": top,
            "total_in_catalog": len(all_items),
            "industry_used": job_industry or None,
            "work_model_used": work_model or None,
        },
        "message": (
            f"{len(top)} template(s) de elegibilidade sugerido(s) "
            f"(top 10 de {len(all_items)} no catalogo da empresa)."
        ),
    }


@tool_handler("wizard")
async def _wrap_apply_eligibility_template_to_vacancy(**kwargs):
    """
    Aplica template de elegibilidade canonical a uma vaga em criacao.

    Snapshot canonical (decisao Paulo B1): copia o data do template e adiciona
    a vaga.eligibility_questions JSONB (in-memory; persistencia final ocorre
    no save_job_draft).

    Multi-tenancy: company_id + vacancy_id required via ContextVar.
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.cv_screening.repositories.eligibility_question_template_repository import (
        EligibilityQuestionTemplateRepository,
    )
    import uuid

    company_id = kwargs.get("company_id")
    template_id_raw = kwargs.get("template_id")
    vacancy_id = kwargs.get("vacancy_id")

    if not template_id_raw:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "template_id obrigatorio",
        }

    try:
        template_uuid = uuid.UUID(template_id_raw) if isinstance(template_id_raw, str) else template_id_raw
    except (ValueError, TypeError):
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": f"template_id invalido: {template_id_raw}",
        }

    async with AsyncSessionLocal() as db:
        repo = EligibilityQuestionTemplateRepository(db)
        template = await repo.get_by_id(template_uuid, company_id)

    if not template:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "Template nao encontrado ou fora do escopo da empresa",
        }

    snapshot = dict(template.data or {})
    snapshot["_template_id"] = str(template.id)
    snapshot["_is_master_origin"] = template.is_master_template

    return {
        "success": True,
        "data": {
            "vacancy_id": vacancy_id,
            "template_id": str(template.id),
            "snapshot": snapshot,
            "is_master_origin": template.is_master_template,
        },
        "message": (
            f"Template '{snapshot.get('question', '')[:60]}...' aplicado à vaga "
            f"(snapshot canonical B1; persistencia ocorre no save_job_draft)."
        ),
    }


@tool_handler("wizard")
async def _wrap_create_custom_eligibility_template(**kwargs):
    """
    Cria template de elegibilidade custom canonical via wizard conversacional.

    Permissoes: qualquer user (recrutador + admin podem criar — decisao
    Paulo C 2026-05-20). Persistido per-company.
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.cv_screening.repositories.eligibility_question_template_repository import (
        EligibilityQuestionTemplateRepository,
    )

    company_id = kwargs.get("company_id")
    user_id = kwargs.get("user_id")
    question = (kwargs.get("question") or "").strip()
    question_type = kwargs.get("type") or "yes_no"
    category = kwargs.get("category") or "general"

    if not question or len(question) < 3:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "Pergunta obrigatoria (min 3 caracteres)",
        }

    data = {
        "question": question,
        "type": question_type,
        "category": category,
        "contextHint": kwargs.get("contextHint"),
        "eliminatory": kwargs.get("eliminatory", False),
        "eliminatoryAnswer": kwargs.get("eliminatoryAnswer"),
    }
    if kwargs.get("options"):
        data["options"] = kwargs["options"]

    async with AsyncSessionLocal() as db:
        repo = EligibilityQuestionTemplateRepository(db)
        try:
            template = await repo.create_custom(
                company_id=company_id,
                data=data,
                created_by=str(user_id) if user_id else None,
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "fallback_used": True,
                "needs_manual_review": True,
                "message": f"Falha ao criar template: {str(e)}",
            }

    return {
        "success": True,
        "data": {
            "id": str(template.id),
            "company_id": template.company_id,
            "is_master_template": False,
            "question": data["question"],
            "category": category,
        },
        "message": f"Template custom criado para a empresa (id={str(template.id)[:8]}...)",
    }


TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="suggest_eligibility_templates",
        description=(
            "Sugere templates de elegibilidade canonical relevantes para a vaga em "
            "criacao baseado em industry, work_model, languages. Retorna top 10 "
            "ranked por relevancia (priority categorias + linkedField match)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "industry": {"type": "string", "description": "Setor da empresa"},
                "work_model": {"type": "string", "description": "Modelo de trabalho da vaga"},
                "languages": {"type": "array", "items": {"type": "string"}, "description": "Idiomas requeridos"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_suggest_eligibility_templates,
    )
)

TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="apply_eligibility_template_to_vacancy",
        description=(
            "Aplica template canonical a uma vaga em criacao via snapshot "
            "canonical (B1). NAO sincroniza com master apos aplicacao."
        ),
        parameters={
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "UUID do template canonical"},
                "vacancy_id": {"type": "string", "description": "UUID da vaga (ou identifier)"},
            },
            "required": ["template_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_apply_eligibility_template_to_vacancy,
    )
)

TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="create_custom_eligibility_template",
        description=(
            "Cria template de elegibilidade custom canonical persistido per-company. "
            "Recrutador + admin podem criar (decisao Paulo C 2026-05-20)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Texto da pergunta (min 3 chars)"},
                "type": {"type": "string", "enum": ["text", "yes_no", "scale", "multiple"]},
                "category": {"type": "string", "description": "Categoria canonical"},
                "contextHint": {"type": "string"},
                "eliminatory": {"type": "boolean"},
                "eliminatoryAnswer": {"type": "string"},
                "options": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["question"],
        },
        output_schema=ToolOutput,
        function=_wrap_create_custom_eligibility_template,
    )
)



# ============================================================================
# Sprint 2 F5 — Pipeline Stage Templates wizard tools (canonical 2026-05-21)
# ============================================================================
# 3 tools canonical pro wizard conversacional manusear o catalogo dinamico
# per-tenant de pipeline_stage_templates (substitui hardcoded DEFAULT_STAGES
# em RecruitmentJourneyConfig.tsx + modais). Mesma estrutura das 3 tools
# Sprint 1 F5 (eligibility templates) — snapshot canonical B1.

@tool_handler("wizard")
async def _wrap_suggest_pipeline_stage_templates(**kwargs: Any) -> dict[str, Any]:
    """
    Sugere templates de pipeline stage canonical relevantes pra vaga em
    criacao. Ranking: is_default_in_pipeline (peso 5) + master scope (peso 3)
    + stage_category match (peso 2). Retorna top 15 (cobre o pipeline completo
    canonical de ~15 stages).

    Multi-tenancy: company_id obrigatorio via ContextVar JWT (@tool_handler).
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.pipeline.repositories.pipeline_stage_template_repository import (
        PipelineStageTemplateRepository,
    )

    company_id = kwargs.get("company_id")
    job_industry = (kwargs.get("job_industry") or kwargs.get("industry") or "").lower()
    job_type = (kwargs.get("job_type") or "").lower()

    async with AsyncSessionLocal() as db:
        repo = PipelineStageTemplateRepository(db)
        all_items = await repo.list_for_company(
            company_id=company_id, include_master=True
        )

    suggestions = []
    for item in all_items:
        data = item.data or {}
        # Score canonical: default_in_pipeline + master + category
        score = 0
        if data.get("is_default_in_pipeline"):
            score += 5
        if item.is_master_template:
            score += 3
        category = data.get("stage_category")
        if category in ("system", "catalog"):
            score += 2
        # Bonus: job_type/industry-aware (futuro — placeholder simbolico)
        if job_industry and category == "catalog":
            score += 1
        suggestions.append({
            "id": str(item.id),
            "label": data.get("label", ""),
            "key": data.get("key", ""),
            "order": data.get("order", 9999),
            "action_behavior": data.get("action_behavior"),
            "stage_category": category,
            "is_master": item.is_master_template,
            "is_default_in_pipeline": data.get("is_default_in_pipeline", False),
            "score": score,
        })

    # Sort por score desc + order asc (preserva ordem canonical do funil)
    suggestions.sort(key=lambda s: (-s["score"], s["order"]))
    top = suggestions[:15]

    return {
        "success": True,
        "data": {
            "suggestions": top,
            "total_in_catalog": len(all_items),
            "industry_used": job_industry or None,
            "job_type_used": job_type or None,
        },
        "message": (
            f"{len(top)} pipeline stage template(s) sugerido(s) "
            f"(top 15 de {len(all_items)} no catalogo da empresa)."
        ),
    }


@tool_handler("wizard")
async def _wrap_apply_pipeline_stage_template_to_vacancy(**kwargs: Any) -> dict[str, Any]:
    """
    Aplica template de pipeline stage canonical a uma vaga em criacao.

    Snapshot canonical (decisao Paulo B1): copia o data do template para
    vaga.pipeline_stages JSONB (in-memory; persistencia ocorre via
    save_job_draft canonical).

    Multi-tenancy: company_id required via ContextVar; vacancy_id opcional
    (pode ser snapshot pre-vaga durante o wizard).
    """
    import uuid as _uuid
    from app.core.database import AsyncSessionLocal
    from app.domains.pipeline.repositories.pipeline_stage_template_repository import (
        PipelineStageTemplateRepository,
    )

    company_id = kwargs.get("company_id")
    template_id_raw = kwargs.get("template_id")
    vacancy_id = kwargs.get("vacancy_id")

    if not template_id_raw:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "template_id obrigatorio",
        }

    try:
        template_uuid = (
            _uuid.UUID(template_id_raw)
            if isinstance(template_id_raw, str)
            else template_id_raw
        )
    except (ValueError, TypeError):
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": f"template_id invalido: {template_id_raw}",
        }

    async with AsyncSessionLocal() as db:
        repo = PipelineStageTemplateRepository(db)
        template = await repo.get_by_id(template_uuid, company_id)

    if not template:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "Template nao encontrado ou fora do escopo da empresa",
        }

    snapshot = dict(template.data or {})
    snapshot["_template_id"] = str(template.id)
    snapshot["_parent_template_id"] = (
        str(template.parent_template_id) if template.parent_template_id else None
    )
    snapshot["_is_master_origin"] = template.is_master_template

    return {
        "success": True,
        "data": {
            "vacancy_id": vacancy_id,
            "template_id": str(template.id),
            "snapshot": snapshot,
            "is_master_origin": template.is_master_template,
        },
        "message": (
            f"Pipeline stage '{snapshot.get('label', '')[:60]}' aplicado a vaga "
            f"(snapshot canonical B1; persistencia ocorre no save_job_draft)."
        ),
    }


@tool_handler("wizard")
async def _wrap_create_custom_pipeline_stage_template(**kwargs: Any) -> dict[str, Any]:
    """
    Cria pipeline stage template custom canonical via wizard conversacional.

    Permissoes: qualquer user (recrutador + admin podem criar — decisao Paulo C
    2026-05-20). Persistido per-company.

    Validacao: label min 2 chars; key inferido se omitido.
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.pipeline.repositories.pipeline_stage_template_repository import (
        PipelineStageTemplateRepository,
    )

    company_id = kwargs.get("company_id")
    user_id = kwargs.get("user_id")
    label = (kwargs.get("label") or "").strip()
    key_raw = (kwargs.get("key") or "").strip()
    color = kwargs.get("color")
    icon = kwargs.get("icon")
    order = kwargs.get("order", 0)
    is_default = kwargs.get("is_default_in_pipeline", False)

    if not label or len(label) < 2:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "label obrigatorio (min 2 caracteres)",
        }

    # Infere key canonical do label se nao fornecido (snake_case)
    if not key_raw:
        import re as _re
        key = _re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")[:64] or "custom_stage"
    else:
        key = key_raw[:64]

    try:
        order_int = int(order)
    except (ValueError, TypeError):
        order_int = 0

    data: dict[str, Any] = {
        "label": label,
        "key": key,
        "order": max(0, order_int),
        "is_default_in_pipeline": bool(is_default),
        "stage_category": kwargs.get("stage_category") or "custom",
        "type": kwargs.get("type") or "custom",
    }
    if color:
        data["color"] = color
    if icon:
        data["icon"] = icon
    if kwargs.get("action_behavior"):
        data["action_behavior"] = kwargs["action_behavior"]
    if kwargs.get("default_channel"):
        data["default_channel"] = kwargs["default_channel"]
    if kwargs.get("sla_hours") is not None:
        try:
            data["sla_hours"] = max(0, int(kwargs["sla_hours"]))
        except (ValueError, TypeError):
            pass

    async with AsyncSessionLocal() as db:
        repo = PipelineStageTemplateRepository(db)
        try:
            template = await repo.create_custom(
                company_id=company_id,
                data=data,
                created_by=str(user_id) if user_id else None,
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "fallback_used": True,
                "needs_manual_review": True,
                "message": f"Falha ao criar pipeline stage template: {str(e)}",
            }

    return {
        "success": True,
        "data": {
            "id": str(template.id),
            "company_id": template.company_id,
            "is_master_template": False,
            "label": data["label"],
            "key": data["key"],
            "order": data["order"],
            "is_default_in_pipeline": data["is_default_in_pipeline"],
        },
        "message": (
            f"Pipeline stage custom criado para a empresa "
            f"(id={str(template.id)[:8]}..., key={key})."
        ),
    }


TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="suggest_pipeline_stage_templates",
        description=(
            "Sugere templates canonical de etapas de pipeline (funil de recrutamento) "
            "relevantes para a vaga em criacao baseado em job_industry e job_type. "
            "Retorna top 15 ranked por is_default_in_pipeline + master scope + "
            "stage_category. Substitui o catalogo hardcoded DEFAULT_STAGES."
        ),
        parameters={
            "type": "object",
            "properties": {
                "job_industry": {"type": "string", "description": "Setor da empresa"},
                "job_type": {"type": "string", "description": "Tipo da vaga (CLT, PJ, etc.)"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_suggest_pipeline_stage_templates,
    )
)

TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="apply_pipeline_stage_template_to_vacancy",
        description=(
            "Aplica template canonical de pipeline stage a uma vaga em criacao via "
            "snapshot canonical (B1). Copia data + parent_template_id. NAO sincroniza "
            "com master apos aplicacao. Persistencia final ocorre em save_job_draft."
        ),
        parameters={
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "UUID do pipeline stage template"},
                "vacancy_id": {"type": "string", "description": "UUID da vaga (opcional durante wizard)"},
            },
            "required": ["template_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_apply_pipeline_stage_template_to_vacancy,
    )
)

TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="create_custom_pipeline_stage_template",
        description=(
            "Cria pipeline stage template custom canonical persistido per-company. "
            "Recrutador + admin podem criar (decisao Paulo C 2026-05-20). label min 2 "
            "chars; key inferido snake_case do label se omitido."
        ),
        parameters={
            "type": "object",
            "properties": {
                "label": {"type": "string", "description": "Nome canonical da etapa (min 2 chars)"},
                "key": {"type": "string", "description": "Slug canonical snake_case (inferido se omitido)"},
                "color": {"type": "string", "description": "CSS var ou hex (opcional)"},
                "icon": {"type": "string", "description": "Lucide icon name (opcional)"},
                "order": {"type": "integer", "description": "Ordem canonical 1..N (default 0)"},
                "is_default_in_pipeline": {"type": "boolean", "description": "Aparece em novos pipelines (default False)"},
                "action_behavior": {
                    "type": "string",
                    "enum": [
                        "intake", "screening", "passive", "scheduling", "evaluation",
                        "verification", "offer", "conclusion_hired",
                        "conclusion_declined", "conclusion_rejected",
                    ],
                },
                "default_channel": {"type": "string", "enum": ["email", "email_whatsapp", "whatsapp", "none"]},
                "stage_category": {"type": "string", "enum": ["system", "custom", "catalog"]},
                "type": {"type": "string", "enum": ["system", "custom", "default"]},
                "sla_hours": {"type": "integer", "description": "SLA em horas (default 0)"},
            },
            "required": ["label"],
        },
        output_schema=ToolOutput,
        function=_wrap_create_custom_pipeline_stage_template,
    )
)


_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in TOOL_DEFINITIONS}

# --- STAGE_TOOLS canonical allowlist ---------------------------------------
#
# CONVENCAO CANONICAL (PR-16 / 2026-05-26): TODAS as keys sao snake_case.
#
# Creation stages alinhados com WizardStage Literal canonical
# (app/domains/job_creation/state.py):
#   intake, jd_enrichment, pipeline_template, salary, competency,
#   wsi_questions, review, publish
#
# Lifecycle stages Phase E (DB column values em
# _classify_job_lifecycle_stage / app/api/v1/job_vacancies/analytics.py):
#   enriquecida, wsi_config, aguardando_aprovacao, publicada, ao_vivo
#
# Frontend ainda dispatch kebab (input-evaluation, jd-enrichment, etc.)
# via /api/v1/wizard/smart-orchestrate -- traducao kebab->snake fica em
# FRONTEND_TO_BACKEND_STAGE (app/api/v1/wizard_smart_orchestrator.py).
# STAGE_TOOLS aqui e canonical documentation (zero callers de
# get_stage_tools em producao).
#
# Sensor canonical (scripts/check_stage_tools_naming.py) valida que
# entries seguem snake_case e estao no conjunto canonical conhecido.
# --------------------------------------------------------------------------
STAGE_TOOLS: dict[str, list[str]] = {
    # Creation stages (alinhados com WizardStage Literal canonical):
    "intake": ["validate_job_requirements", "validate_job_fields", "get_job_suggestions", "get_company_config", "save_job_draft", "check_job_draft_health", "suggest_pipeline_stage_templates", "apply_pipeline_stage_template_to_vacancy", "create_custom_pipeline_stage_template"],
    "jd_enrichment": ["generate_enriched_jd", "get_job_suggestions", "get_company_config", "save_job_draft", "check_job_draft_health"],
    "pipeline_template": ["suggest_pipeline_stage_templates", "apply_pipeline_stage_template_to_vacancy", "create_custom_pipeline_stage_template"],
    "salary": ["get_salary_benchmarks", "search_salary_benchmark", "validate_job_fields", "save_job_draft", "check_job_draft_health"],
    "competency": ["validate_job_requirements", "get_job_suggestions", "validate_job_fields", "save_job_draft", "suggest_eligibility_templates", "apply_eligibility_template_to_vacancy", "create_custom_eligibility_template"],
    "wsi_questions": ["validate_job_requirements", "validate_job_fields", "save_job_draft", "generate_screening_questions", "suggest_eligibility_templates", "apply_eligibility_template_to_vacancy", "create_custom_eligibility_template"],
    "review": ["validate_job_requirements", "save_job_draft", "validate_job_fields", "check_job_draft_health", "generate_report", "publish_vacancy", "change_vacancy_status", "suggest_pipeline_stage_templates", "apply_pipeline_stage_template_to_vacancy", "create_custom_pipeline_stage_template"],
    "publish": ["validate_job_requirements", "save_job_draft", "validate_job_fields", "check_job_draft_health", "generate_report", "publish_vacancy", "change_vacancy_status", "suggest_pipeline_stage_templates", "apply_pipeline_stage_template_to_vacancy", "create_custom_pipeline_stage_template"],
    # Phase E -- vacancy lifecycle stages (Recrutar > Vagas rail).
    # Stage names match _classify_job_lifecycle_stage in
    # app/api/v1/job_vacancies/analytics.py.
    "enriquecida": ["generate_screening_questions", "validate_job_requirements"],
    "wsi_config": ["generate_screening_questions", "validate_job_requirements", "request_approval"],
    "aguardando_aprovacao": ["dispatch_screening"],
    "publicada": ["publish_vacancy", "change_vacancy_status"],
    "ao_vivo": ["change_vacancy_status", "publish_vacancy"],
}


def get_wizard_tools() -> list[ToolDefinition]:
    """Return all wizard tool definitions."""
    return list(TOOL_DEFINITIONS)


def get_stage_tools(stage: str) -> list[ToolDefinition]:
    """Return only tools relevant to the current wizard stage.

    Args:
        stage: Current wizard stage identifier.

    Returns:
        List of ToolDefinition instances available for the given stage.
    """
    tool_names = STAGE_TOOLS.get(stage, list(_TOOL_MAP.keys()))
    tools = [_TOOL_MAP[name] for name in tool_names if name in _TOOL_MAP]
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.debug(f"[wizard_tools] Stage '{stage}' tools: {[t.name for t in tools]}")
    return tools
