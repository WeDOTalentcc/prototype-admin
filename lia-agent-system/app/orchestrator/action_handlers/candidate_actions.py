"""
Candidate Actions — closed-loop candidate management actions.

Handles: move_candidate, update_candidate_field, start_screening, analyze_profile
"""
import logging
import re
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

_SAFE_COLUMN_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


def _safe_identifier(name: str, allowed: set[str]) -> str:
    if name not in allowed:
        raise ValueError(f"Column '{name}' not in allow-list")
    if not _SAFE_COLUMN_RE.match(name):
        raise ValueError(f"Column '{name}' contains invalid characters")
    return name

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
    elif action_id == "bulk_move_by_stage":
        return await _bulk_move_by_stage(params, context)
    return None


async def _move_candidate(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal
        from app.orchestrator.action_handlers._handler_hooks import (
            log_action_audit,
            resolve_candidate_by_name,
            sync_to_rails,
        )

        candidate_id = params.get("candidate_id", "")
        to_stage = params.get("to_stage", "")
        candidate_name = params.get("candidate_name", "o candidato")
        from_stage = params.get("from_stage", "")
        company_id = context.get("company_id") if context else None

        if not candidate_id and candidate_name:
            resolved = await resolve_candidate_by_name(candidate_name, company_id)
            if resolved:
                candidate_id = resolved["id"]
                candidate_name = resolved["name"]

        if not candidate_id:
            return ActionResult(
                status="error",
                message=f"Candidato **{candidate_name}** não encontrado no pipeline.",
                error_detail="Could not resolve candidate_id",
                action_type="move_candidate",
            )

        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                UPDATE vacancy_candidates
                SET stage = :to_stage, status = 'active', updated_at = NOW()
                WHERE (id = CAST(:candidate_id AS uuid) OR candidate_id = CAST(:candidate_id AS uuid))
            """), {
                "to_stage": to_stage,
                "candidate_id": str(candidate_id),
            })
            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message=f"Candidato **{candidate_name}** não encontrado no pipeline.",
                    error_detail="Candidato não encontrado no pipeline",
                    action_type="move_candidate",
                )
            await db.commit()

        await log_action_audit("move_stage", company_id, candidate_id=str(candidate_id))
        await sync_to_rails("candidate_moved", "candidate", str(candidate_id), {"from_stage": from_stage, "to_stage": to_stage})

        return ActionResult(
            status="executed",
            message=f"**{candidate_name}** foi movido(a) para a etapa **{to_stage}**.",
            data={
                "candidate_id": str(candidate_id),
                "candidate_name": candidate_name,
                "from_stage": from_stage,
                "to_stage": to_stage,
                "moved_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="move_candidate",
        )
    except Exception as e:
        logger.warning(f"move_candidate failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao mover o candidato no pipeline.",
            error_detail=str(e),
            action_type="move_candidate",
        )


async def _update_candidate_field(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        from app.orchestrator.action_handlers._handler_hooks import (
            log_action_audit,
            resolve_candidate_by_name,
            sync_to_rails,
        )

        candidate_id = params.get("candidate_id", "")
        field_name = params.get("field_name", "")
        field_value = params.get("field_value", "")
        candidate_name = params.get("candidate_name", "o candidato")
        company_id = context.get("company_id") if context else None

        if not candidate_id and candidate_name:
            resolved = await resolve_candidate_by_name(candidate_name, company_id)
            if resolved:
                candidate_id = resolved["id"]
                candidate_name = resolved["name"]

        if not candidate_id:
            return ActionResult(
                status="error",
                message=f"Candidato **{candidate_name}** não encontrado.",
                error_detail="Could not resolve candidate_id",
                action_type="update_candidate_field",
            )

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
                safe_col = _safe_identifier(resolved_field, ALLOWED_DIRECT_FIELDS)
                result = await db.execute(
                    text(f"UPDATE candidates SET {safe_col} = :val, updated_at = NOW() WHERE id = CAST(:cid AS uuid)"),
                    {"val": field_value, "cid": candidate_id},
                )

            if result.rowcount == 0:
                return ActionResult(
                    status="error",
                    message=f"Candidato **{candidate_name}** não encontrado ou sem permissão para atualizar.",
                    error_detail="Candidate not found or no rows updated",
                    action_type="update_candidate_field",
                )
            await db.commit()

        await log_action_audit("update_candidate_field", company_id, candidate_id=str(candidate_id))
        await sync_to_rails("candidate_updated", "candidate", str(candidate_id), {"field": resolved_field, "value": field_value})

        return ActionResult(
            status="executed",
            message=f"Campo **{field_name}** de **{candidate_name}** atualizado para **{field_value}**.",
            data={
                "candidate_id": str(candidate_id),
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
        logger.warning(f"update_candidate_field failed: {e}")
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
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal
        from app.domains.recruitment.services.triagem_session_service.service import (
            TriagemSessionService,
        )
        from app.orchestrator.action_handlers._handler_hooks import (
            log_action_audit,
            resolve_candidate_by_name,
            sync_to_rails,
        )

        candidate_ids = params.get("candidate_ids", [])
        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "")
        job_vacancy_id = (
            params.get("job_vacancy_id")
            or params.get("vacancy_id")
            or params.get("job_id")
            or (context or {}).get("job_vacancy_id")
        )
        company_id = (context or {}).get("company_id")

        if candidate_id and not candidate_ids:
            candidate_ids = [candidate_id]

        if not candidate_ids and candidate_name:
            resolved = await resolve_candidate_by_name(candidate_name, company_id)
            if resolved:
                candidate_ids = [resolved["id"]]
                candidate_name = resolved["name"]

        if not candidate_ids:
            # SC-001 fix: when job_id is provided (from context), auto-fetch candidates
            # in "Novo" or "Triagem" (waiting) stage rather than asking for UUIDs
            _auto_fetched = False
            if job_vacancy_id and company_id:
                try:
                    from sqlalchemy import text as _text
                    from app.core.database import AsyncSessionLocal as _ASL
                    async with _ASL() as _db:
                        _rows = await _db.execute(_text("""
                            SELECT vc.candidate_id
                            FROM vacancy_candidates vc
                            WHERE vc.job_vacancy_id = CAST(:jid AS uuid)
                              AND vc.company_id = CAST(:co AS uuid)
                              AND vc.stage IN ('Novo', 'Triagem', 'Aguardando')
                              AND (vc.status IS NULL OR vc.status NOT IN ('screening', 'screened'))
                            LIMIT 50
                        """), {"jid": str(job_vacancy_id), "co": str(company_id)})
                        _found = [str(r[0]) for r in _rows.fetchall()]
                    if _found:
                        candidate_ids = _found
                        _auto_fetched = True
                        logger.info(
                            "start_screening: auto-fetched %d waiting candidates for job %s",
                            len(candidate_ids), job_vacancy_id,
                        )
                except Exception as _fe:
                    logger.warning("start_screening: auto-fetch failed: %s", _fe)

            if not candidate_ids:
                # If job_id is known but no candidates found, give useful message
                if job_vacancy_id:
                    return ActionResult(
                        status="executed",
                        message=(
                            "Não encontrei candidatos em espera (etapa Novo/Triagem) "
                            "para esta vaga no momento. "
                            "Verifique se há candidatos na etapa inicial do pipeline."
                        ),
                        data={"job_vacancy_id": str(job_vacancy_id), "candidates_found": 0},
                        action_type="start_screening",
                    )
                return ActionResult(
                    status="error",
                    message="Nenhum candidato identificado para iniciar a triagem.",
                    error_detail="No candidate_ids or candidate_name provided",
                    action_type="start_screening",
                )

        if not job_vacancy_id:
            return ActionResult(
                status="error",
                message="Vaga não identificada. Informe a vaga para iniciar a triagem.",
                error_detail="job_vacancy_id missing from params and context",
                action_type="start_screening",
            )

        triagem_service = TriagemSessionService()
        sessions_created = []
        candidates_updated = 0

        if not company_id:
            return ActionResult(
                status="error",
                message="Contexto de empresa não disponível para iniciar a triagem.",
                error_detail="company_id missing from context",
                action_type="start_screening",
            )

        async with AsyncSessionLocal() as db:
            job_row = await db.execute(
                text("""
                    SELECT title FROM job_vacancies
                    WHERE id = CAST(:jid AS uuid) AND company_id = CAST(:co AS uuid)
                    LIMIT 1
                """),
                {"jid": str(job_vacancy_id), "co": str(company_id)},
            )
            job_info = job_row.fetchone()
            if not job_info:
                return ActionResult(
                    status="error",
                    message="Vaga não encontrada ou não pertence à empresa.",
                    error_detail="job_vacancy_id not found for company",
                    action_type="start_screening",
                )
            job_title = job_info.title

            company_row = await db.execute(
                text("SELECT name FROM companies WHERE id = CAST(:cid AS uuid) LIMIT 1"),
                {"cid": str(company_id)},
            )
            company_name_db = company_row.fetchone()
            company_name_str = company_name_db.name if company_name_db else None

            for cid in candidate_ids:
                cid_str = str(cid)

                authz_result = await db.execute(
                    text("""
                        SELECT c.id, c.name, c.email
                        FROM candidates c
                        JOIN vacancy_candidates vc ON vc.candidate_id = c.id
                        WHERE c.id = CAST(:cid AS uuid)
                          AND vc.company_id = CAST(:co AS uuid)
                          AND vc.job_vacancy_id = CAST(:jid AS uuid)
                        LIMIT 1
                    """),
                    {"cid": cid_str, "co": str(company_id), "jid": str(job_vacancy_id)},
                )
                candidate_row = authz_result.fetchone()

                if not candidate_row:
                    logger.warning(f"start_screening: candidate {cid_str} not found in pipeline for company/job")
                    continue

                update_result = await db.execute(
                    text("""
                        UPDATE vacancy_candidates
                        SET stage = 'Triagem', status = 'screening', updated_at = NOW()
                        WHERE candidate_id = CAST(:cid AS uuid)
                          AND job_vacancy_id = CAST(:jid AS uuid)
                          AND company_id = CAST(:co AS uuid)
                    """),
                    {"cid": cid_str, "jid": str(job_vacancy_id), "co": str(company_id)},
                )
                if update_result.rowcount > 0:
                    candidates_updated += 1

                try:
                    session = await triagem_service.create_session(
                        db=db,
                        candidate_id=cid_str,
                        job_id=str(job_vacancy_id),
                        company_id=str(company_id) if company_id else "",
                        candidate_name=candidate_row.name,
                        candidate_email=candidate_row.email,
                        job_title=job_title,
                        company_name=company_name_str,
                        invite_channel="chat",
                        created_by=str((context or {}).get("user_id", "system")),
                    )
                    sessions_created.append({
                        "session_id": str(session.id),
                        "token": session.token,
                        "candidate_id": cid_str,
                        "candidate_name": candidate_row.name,
                    })
                except Exception as sess_err:
                    logger.warning(f"start_screening: failed to create TriagemSession for {cid_str}: {sess_err}")

            await db.commit()

        if not candidates_updated and not sessions_created:
            return ActionResult(
                status="error",
                message="Nenhum candidato válido encontrado para iniciar a triagem.",
                error_detail="No candidates matched in pipeline for this job",
                action_type="start_screening",
            )

        for s in sessions_created:
            await log_action_audit(
                "start_screening",
                company_id,
                candidate_id=s["candidate_id"],
                job_vacancy_id=str(job_vacancy_id),
                details={"session_id": s["session_id"]},
            )
            await sync_to_rails(
                "screening_started", "candidate", s["candidate_id"],
                {"job_id": str(job_vacancy_id), "session_token": s["token"]},
            )

        count = len(sessions_created)
        if count == 1:
            name = sessions_created[0]["candidate_name"]
            msg = f"Triagem iniciada para **{name}**. Uma sessão de triagem WSI foi criada."
        else:
            msg = f"Triagem iniciada para **{count} candidatos**. Sessões de triagem WSI foram criadas."

        return ActionResult(
            status="executed",
            message=msg,
            data={
                "action": "start_screening",
                "candidates_updated": candidates_updated,
                "sessions_created": [
                    {"session_id": s["session_id"], "candidate_id": s["candidate_id"]}
                    for s in sessions_created
                ],
                "job_vacancy_id": str(job_vacancy_id),
                "started_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="start_screening",
        )
    except Exception as e:
        logger.warning(f"start_screening failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao iniciar a triagem.",
            error_detail=str(e),
            action_type="start_screening",
        )


async def _analyze_profile(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from uuid import UUID

        from sqlalchemy import select
        from sqlalchemy import text as sql_text

        from app.core.database import AsyncSessionLocal
        from lia_models.candidate import Candidate
        from app.shared.services.analysis_service import analysis_service

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
        from app.orchestrator.action_handlers._handler_hooks import log_action_audit, sync_to_rails

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

        for cid in candidate_ids:
            await log_action_audit("move_stage", company_id, candidate_id=str(cid))
            await sync_to_rails("candidate_moved", "candidate", str(cid), {"to_stage": to_stage})

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
        logger.warning(f"batch_move_candidates failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao mover candidatos em lote.",
            error_detail=str(e),
            action_type="batch_move_candidates",
        )


async def _bulk_move_by_stage(params: dict, context: dict):
    """Move ALL candidates in a given stage to another stage for a specific job."""
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        from app.orchestrator.action_handlers._handler_hooks import log_action_audit

        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")
        from_stage = params.get("from_stage", "")
        to_stage = params.get("to_stage", "")
        company_id = (context or {}).get("company_id")

        if not from_stage or not to_stage:
            missing = []
            if not from_stage:
                missing.append("etapa de origem")
            if not to_stage:
                missing.append("etapa destino")
            return ActionResult(
                status="clarification_needed",
                message=f"Para mover em bloco, preciso saber: {' e '.join(missing)}. "
                        "Qual etapa de origem e qual etapa destino?",
                action_type="bulk_move_by_stage",
            )

        if not job_id:
            return ActionResult(
                status="clarification_needed",
                message="Para mover todos os candidatos de uma etapa, preciso saber qual é a vaga. "
                        "Qual vaga você quer usar?",
                action_type="bulk_move_by_stage",
            )

        async with AsyncSessionLocal() as db:
            moved = 0
            for attempt in range(2):
                try:
                    if attempt == 0:
                        sql = """
                            UPDATE vacancy_candidates
                            SET stage = :to_stage, updated_at = NOW()
                            WHERE vacancy_id = CAST(:jid AS uuid)
                              AND stage = :from_stage
                        """
                    else:
                        # Fallback: look up vacancy UUID from job_id short code
                        sql = """
                            UPDATE vacancy_candidates vc
                            SET stage = :to_stage, updated_at = NOW()
                            FROM job_vacancies jv
                            WHERE jv.id = vc.vacancy_id
                              AND jv.job_id = :jid
                              AND vc.stage = :from_stage
                        """
                    bind: dict = {
                        "to_stage": to_stage,
                        "from_stage": from_stage,
                        "jid": str(job_id),
                    }
                    if company_id and attempt == 0:
                        sql += " AND company_id = CAST(:co AS uuid)"
                        bind["co"] = str(company_id)
                    elif company_id and attempt == 1:
                        sql += " AND vc.company_id = :co"
                        bind["co"] = str(company_id)
                    result = await db.execute(text(sql), bind)
                    moved = result.rowcount
                    await db.commit()
                    break
                except Exception:
                    await db.rollback()
                    if attempt == 0:
                        continue
                    raise

        await log_action_audit(
            "bulk_move_by_stage", company_id,
            extra={"from_stage": from_stage, "to_stage": to_stage, "job_id": str(job_id)}
        )

        return ActionResult(
            status="executed",
            message=f"**{moved} candidato(s)** movido(s) de **{from_stage}** para **{to_stage}**.",
            data={
                "from_stage": from_stage,
                "to_stage": to_stage,
                "job_id": str(job_id),
                "moved_count": moved,
                "moved_at": datetime.utcnow().isoformat(),
            },
            action_type="bulk_move_by_stage",
        )
    except Exception as e:
        logger.warning(f"bulk_move_by_stage failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao mover candidatos por etapa.",
            error_detail=str(e),
            action_type="bulk_move_by_stage",
        )
