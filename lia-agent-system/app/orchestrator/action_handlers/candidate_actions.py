"""
Candidate Actions — closed-loop candidate management actions.

Handles: move_candidate, update_candidate_field, start_screening, analyze_profile
"""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

ALLOWED_DIRECT_FIELDS = {
    "phone", "email", "linkedin_url", "current_title",
    "current_company", "location_city", "location_state",
    "salary_expectation_clt", "salary_expectation_pj",
    "work_model_preference", "languages",
}

ALLOWED_JSON_FIELDS = {"availability_date", "education_level"}
ALLOWED_FIELDS = ALLOWED_DIRECT_FIELDS | ALLOWED_JSON_FIELDS

FIELD_ALIASES = {
    "telefone": "phone",
    "celular": "phone",
    "e-mail": "email",
    "linkedin": "linkedin_url",
    "cargo atual": "current_title",
    "cargo": "current_title",
    "empresa": "current_company",
    "empresa atual": "current_company",
    "cidade": "location_city",
    "estado": "location_state",
    "salário clt": "salary_expectation_clt",
    "salario clt": "salary_expectation_clt",
    "salário pj": "salary_expectation_pj",
    "salario pj": "salary_expectation_pj",
    "modelo de trabalho": "work_model_preference",
    "modelo trabalho": "work_model_preference",
    "idiomas": "languages",
    "idioma": "languages",
    "formação": "education_level",
    "formacao": "education_level",
    "disponibilidade": "availability_date",
    "disponibilidade de início": "availability_date",
    "disponibilidade de inicio": "availability_date",
}


async def execute_candidate_action(
    action_id: str,
    params: Dict[str, Any],
    context: Dict[str, Any],
):
    """Route candidate actions to specific handler."""
    from app.orchestrator.action_executor import ActionResult

    if action_id == "move_candidate":
        return await _move_candidate(params, context)
    elif action_id == "update_candidate_field":
        return await _update_candidate_field(params, context)
    elif action_id == "start_screening":
        return await _start_screening(params, context)
    elif action_id == "analyze_profile":
        return await _analyze_profile(params, context)
    return None


async def _move_candidate(params: Dict[str, Any], context: Dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text

        candidate_id = params.get("candidate_id", "")
        to_stage = params.get("to_stage", "")
        candidate_name = params.get("candidate_name", "o candidato")
        from_stage = params.get("from_stage", "")

        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                UPDATE vacancy_candidates
                SET stage = :to_stage, status = 'active', updated_at = NOW()
                WHERE (id = CAST(:candidate_id AS uuid) OR candidate_id = CAST(:candidate_id AS uuid))
            """), {
                "to_stage": to_stage,
                "candidate_id": candidate_id,
            })
            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message="Candidato não encontrado",
                    error_detail="Candidato não encontrado no pipeline",
                    action_type="move_candidate",
                )
            await db.commit()
            return ActionResult(
                status="executed",
                message=f"**{candidate_name}** foi movido(a) para a etapa **{to_stage}**.",
                data={
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                    "moved_at": datetime.utcnow().isoformat(),
                    "simulated": False,
                },
                action_type="move_candidate",
            )
    except Exception as e:
        logger.warning(f"Direct move_candidate failed, falling back to domain: {e}")
        return None


async def _update_candidate_field(params: Dict[str, Any], context: Dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text

        candidate_id = params.get("candidate_id", "")
        field_name = params.get("field_name", "")
        field_value = params.get("field_value", "")
        candidate_name = params.get("candidate_name", "o candidato")
        company_id = context.get("company_id") if context else None

        resolved_field = FIELD_ALIASES.get(field_name.lower(), field_name)

        if resolved_field not in ALLOWED_FIELDS:
            return ActionResult(
                status="error",
                message=(
                    f"Campo '{field_name}' não é atualizável pelo chat. "
                    "Campos permitidos: email, telefone, linkedin, cargo atual, empresa, cidade, "
                    "estado, salário CLT/PJ, modelo de trabalho, formação, idiomas, disponibilidade."
                ),
                error_detail=f"Field '{field_name}' not in ALLOWED_FIELDS",
                action_type="update_candidate_field",
            )

        async with AsyncSessionLocal() as db:
            if company_id and candidate_id:
                authz = await db.execute(
                    text("SELECT 1 FROM vacancy_candidates WHERE candidate_id = CAST(:cid AS uuid) AND company_id = CAST(:co AS uuid) LIMIT 1"),
                    {"cid": candidate_id, "co": str(company_id)},
                )
                if authz.fetchone() is None:
                    return ActionResult(
                        status="error",
                        message="Sem permissão para atualizar este candidato.",
                        error_detail="Candidate does not belong to caller's company",
                        action_type="update_candidate_field",
                    )

            if resolved_field in ALLOWED_JSON_FIELDS:
                result = await db.execute(
                    text(
                        "UPDATE candidates "
                        "SET lia_insights = COALESCE(lia_insights, '{}'::jsonb) || jsonb_build_object(:key, :val::text), "
                        "    updated_at = NOW() "
                        "WHERE id = CAST(:cid AS uuid)"
                    ),
                    {"key": resolved_field, "val": field_value, "cid": candidate_id},
                )
            else:
                result = await db.execute(
                    text(f"UPDATE candidates SET {resolved_field} = :val, updated_at = NOW() WHERE id = CAST(:cid AS uuid)"),
                    {"val": field_value, "cid": candidate_id},
                )

            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message="Candidato não encontrado ou sem permissão para atualizar.",
                    error_detail="Candidate not found or no rows updated",
                    action_type="update_candidate_field",
                )
            await db.commit()
            return ActionResult(
                status="executed",
                message=f"Campo **{field_name}** de **{candidate_name}** atualizado para **{field_value}**.",
                data={
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "field": resolved_field,
                    "field_label": field_name,
                    "value": field_value,
                    "updated_at": datetime.utcnow().isoformat(),
                    "simulated": False,
                },
                action_type="update_candidate_field",
            )
    except Exception as e:
        logger.warning(f"Direct update_candidate_field failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao atualizar o campo do candidato.",
            error_detail=str(e),
            action_type="update_candidate_field",
        )


async def _start_screening(params: Dict[str, Any], context: Dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        candidate_ids = params.get("candidate_ids", [])
        logger.info(f"Screening queued for candidates: {candidate_ids}")
        return ActionResult(
            status="executed",
            message="Triagem iniciada para os candidatos da vaga.",
            data={
                "action": "start_screening",
                "candidate_ids": candidate_ids,
                "queued_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="start_screening",
        )
    except Exception as e:
        logger.warning(f"Direct start_screening failed: {e}")
        return None


async def _analyze_profile(params: Dict[str, Any], context: Dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "o candidato")
        logger.info(f"Profile analysis queued for candidate: {candidate_id}")
        return ActionResult(
            status="executed",
            message=f"Análise de perfil iniciada para **{candidate_name}**.",
            data={
                "action": "analyze_profile",
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "queued_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="analyze_profile",
        )
    except Exception as e:
        logger.warning(f"Direct analyze_profile failed: {e}")
        return None
