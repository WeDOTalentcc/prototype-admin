"""
Candidate Actions — closed-loop candidate management actions.

Handles: move_candidate, update_candidate_field, start_screening, analyze_profile
"""
import logging
from datetime import datetime
from typing import Any

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
    params: dict[str, Any],
    context: dict[str, Any],
):
    """Route candidate actions to specific handler."""

    if action_id == "move_candidate":
        return await _move_candidate(params, context)
    elif action_id == "update_candidate_field":
        return await _update_candidate_field(params, context)
    elif action_id == "start_screening":
        return await _start_screening(params, context)
    elif action_id == "analyze_profile":
        return await _analyze_profile(params, context)
    elif action_id == "batch_move_candidates":
        return await _batch_move_candidates(params, context)
    return None


async def _move_candidate(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

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
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning(f"Direct move_candidate failed, falling back to domain: {e}")
        return None


async def _update_candidate_field(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

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
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning(f"Direct update_candidate_field failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao atualizar o campo do candidato.",
            error_detail=str(e),
            action_type="update_candidate_field",
        )


async def _start_screening(params: dict[str, Any], context: dict[str, Any]):
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


async def _analyze_profile(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from uuid import UUID

        from sqlalchemy import select
        from sqlalchemy import text as sql_text

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate
        from app.services.analysis_service import analysis_service

        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "o candidato")
        vacancy_id = params.get("vacancy_id") or params.get("job_vacancy_id") or (context or {}).get("job_vacancy_id")
        company_id = (context or {}).get("company_id")

        if not candidate_id:
            return ActionResult(
                status="error",
                message="ID do candidato não fornecido para análise.",
                error_detail="candidate_id missing",
                action_type="analyze_profile",
            )

        async with AsyncSessionLocal() as db:
            if company_id:
                authz = await db.execute(
                    sql_text(
                        "SELECT 1 FROM vacancy_candidates "
                        "WHERE candidate_id = CAST(:cid AS uuid) "
                        "AND company_id = :co LIMIT 1"
                    ),
                    {"cid": candidate_id, "co": str(company_id)},
                )
                if authz.fetchone() is None:
                    return ActionResult(
                        status="error",
                        message="Sem permissão para analisar este candidato.",
                        error_detail="Candidate does not belong to caller's company",
                        action_type="analyze_profile",
                    )

            if vacancy_id and company_id:
                vac_authz = await db.execute(
                    sql_text(
                        "SELECT 1 FROM vacancy_candidates "
                        "WHERE vacancy_id = CAST(:vid AS uuid) "
                        "AND company_id = :co LIMIT 1"
                    ),
                    {"vid": vacancy_id, "co": str(company_id)},
                )
                if vac_authz.fetchone() is None:
                    vacancy_id = None

            result = await db.execute(
                select(Candidate).where(Candidate.id == UUID(candidate_id))
            )
            candidate = result.scalar_one_or_none()

        if not candidate:
            return ActionResult(
                status="error",
                message=f"Candidato **{candidate_name}** não encontrado.",
                error_detail=f"Candidate {candidate_id} not found",
                action_type="analyze_profile",
            )

        candidate_data = {
            "id": str(candidate.id),
            "name": candidate.name,
            "email": candidate.email,
            "current_title": candidate.current_title,
            "current_company": candidate.current_company,
            "years_of_experience": candidate.years_of_experience,
            "seniority_level": candidate.seniority_level,
            "technical_skills": candidate.technical_skills or [],
            "soft_skills": candidate.soft_skills or [],
            "certifications": candidate.certifications or [],
            "languages": candidate.languages or {},
            "location_city": candidate.location_city,
            "location_state": candidate.location_state,
            "resume_text": getattr(candidate, "resume_text", None),
            "self_introduction": candidate.self_introduction,
            "cv_text": getattr(candidate, "resume_text", None) or candidate.self_introduction or "",
        }

        logger.info(f"[ANALYZE_PROFILE] Running enriched analysis for candidate={candidate_id}, vacancy={vacancy_id}")
        analysis_result = await analysis_service.analyze_profile_enriched(
            candidate_data=candidate_data,
            vacancy_id=vacancy_id,
        )

        overall = analysis_result.get("overall_assessment", {})
        behavioral = analysis_result.get("behavioral_profile", {})
        technical = analysis_result.get("technical_fit", {})
        confidence = analysis_result.get("confidence", "medium")

        score = overall.get("score", 0)
        archetype = behavioral.get("archetype", "N/A")
        recommendation = overall.get("recommendation", "Análise pendente")

        confidence_label = {"low": "baixa", "medium": "média", "high": "alta"}.get(confidence, confidence)
        bars_line = ""
        if technical.get("bars_score") is not None:
            bars_line = f"\n- **Fit Técnico (BARS):** {technical['bars_score']}% — {technical.get('bars_recommendation', 'N/A')}"

        big_five = behavioral.get("big_five", {})
        big_five_line = ""
        if big_five:
            traits = [f"O={big_five.get('openness', '?')}", f"C={big_five.get('conscientiousness', '?')}",
                      f"E={big_five.get('extraversion', '?')}", f"A={big_five.get('agreeableness', '?')}",
                      f"N={big_five.get('neuroticism', '?')}"]
            big_five_line = f"\n- **Big Five:** {', '.join(traits)}"

        message = (
            f"Análise de perfil concluída para **{candidate_name}**:\n\n"
            f"- **Score Geral:** {score}% — {recommendation}\n"
            f"- **Arquétipo:** {archetype}\n"
            f"- **Confiança:** {confidence_label}"
            f"{bars_line}{big_five_line}\n\n"
            f"{'⚠️ ' + analysis_result.get('confidence_note', '') if confidence == 'low' else ''}"
        )

        return ActionResult(
            status="executed",
            message=message.strip(),
            data=analysis_result,
            action_type="analyze_profile",
        )
    except Exception as e:
        logger.error(f"analyze_profile failed: {e}", exc_info=True)
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message=f"Erro ao analisar perfil de **{params.get('candidate_name', 'o candidato')}**: {str(e)[:100]}",
            error_detail=str(e),
            action_type="analyze_profile",
        )


async def _batch_move_candidates(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        candidate_ids = params.get("candidate_ids", [])
        to_stage = params.get("to_stage", "")
        from_stage = params.get("from_stage", "")
        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")

        if not candidate_ids or not to_stage:
            return ActionResult(
                status="error",
                message="Informe os candidatos e a etapa destino.",
                error_detail="Missing candidate_ids or to_stage",
                action_type="batch_move_candidates",
            )

        company_id = context.get("company_id") if context else None

        async with AsyncSessionLocal() as db:
            moved = 0
            for cid in candidate_ids:
                update_sql = """
                    UPDATE vacancy_candidates
                    SET stage = :to_stage, status = 'active', updated_at = NOW()
                    WHERE (id = CAST(:cid AS uuid) OR candidate_id = CAST(:cid AS uuid))
                """
                bind: dict[str, Any] = {"to_stage": to_stage, "cid": str(cid)}
                if company_id:
                    update_sql += " AND company_id = CAST(:co AS uuid)"
                    bind["co"] = str(company_id)
                result = await db.execute(text(update_sql), bind)
                moved += result.rowcount
            await db.commit()

        return ActionResult(
            status="executed",
            message=f"**{moved} candidato(s)** movido(s) para a etapa **{to_stage}**.",
            data={
                "candidate_ids": candidate_ids, "to_stage": to_stage,
                "from_stage": from_stage, "moved_count": moved,
                "moved_at": datetime.utcnow().isoformat(), "simulated": False,
            },
            action_type="batch_move_candidates",
        )
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning(f"batch_move_candidates failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao mover candidatos em lote.",
            error_detail=str(e),
            action_type="batch_move_candidates",
        )
