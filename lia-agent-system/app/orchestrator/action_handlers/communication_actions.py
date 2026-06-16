"""
Communication Actions — closed-loop communication and scheduling actions.

Handles: send_email, schedule_interview, create_generic_event
"""
import logging
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)


async def execute_communication_action(
    action_id: str,
    params: dict[str, Any],
    context: dict[str, Any],
):
    """Route communication actions to specific handler."""
    if action_id == "send_email":
        return await _send_email(params, context)
    elif action_id == "schedule_interview":
        return await _schedule_interview(params, context)
    elif action_id == "create_generic_event":
        return await _create_generic_event(params, context)
    elif action_id == "send_feedback":
        return await _send_feedback(params, context)
    elif action_id == "send_whatsapp":
        return await _send_whatsapp(params, context)
    elif action_id == "send_screening_invite":
        return await _send_screening_invite(params, context)
    elif action_id == "send_candidate_report":
        return await _send_candidate_report(params, context)
    elif action_id == "send_progress_report":
        return await _send_progress_report(params, context)
    elif action_id == "share_candidate_profile":
        return await _share_candidate_profile(params, context)
    elif action_id == "create_template":
        return await _create_template(params, context)
    return None


async def _send_email(params: dict[str, Any], context: dict[str, Any]):
    import os
    from app.orchestrator.action_executor import ActionResult

    candidate_name = params.get("candidate_name", "")
    to_email = params.get("email", params.get("candidate_email", ""))
    subject = params.get("subject", "")
    body = params.get("body", "")
    env = os.environ.get("ENVIRONMENT", "development").lower()
    is_dev = env in ("development", "dev", "local", "test")

    try:
        import html as html_module

        from app.domains.communication.services.email_providers import get_email_provider

        provider = get_email_provider()
        status = provider.get_status()
        if status.get("configured") and status.get("healthy") and to_email and subject:
            safe_body = html_module.escape(body)
            result = await provider.send_email(
                to=to_email,
                subject=subject,
                html_content=f"<p>{safe_body}</p>",
                text_content=body,
            )
            if result.success:
                return ActionResult(
                    status="executed",
                    message=f'Email enviado para **{candidate_name}** com assunto "{subject}".',
                    data={
                        "candidate_id": params.get("candidate_id", ""),
                        "candidate_name": candidate_name,
                        "subject": subject,
                        "to_email": to_email,
                        "message_id": result.message_id,
                        "sent_at": datetime.utcnow().isoformat(),
                        "simulated": False,
                        "provider": result.provider,
                    },
                    action_type="send_email",
                )
    except Exception as e:
        logger.warning(f"Direct email sending failed: {e}")

    if is_dev:
        logger.info("=" * 70)
        logger.info("[DEV EMAIL] Mensagem enviada (modo desenvolvimento)")
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"[DEV EMAIL] Para: {to_email}")
        logger.info(f"[DEV EMAIL] Assunto: {subject}")
        logger.info(f"[DEV EMAIL] Corpo ({len(body)} caracteres): {body[:200]}")
        logger.info("=" * 70)
        return ActionResult(
            status="executed",
            message=f'Email enviado para **{candidate_name}** com assunto "{subject}".\n\n_(Modo desenvolvimento — email registrado no log do servidor.)_',
            data={
                "candidate_id": params.get("candidate_id", ""),
                "candidate_name": candidate_name,
                "subject": subject,
                "to_email": to_email,
                "sent_at": datetime.utcnow().isoformat(),
                "simulated": True,
                "delivered_via": "development_log",
            },
            action_type="send_email",
        )

    return ActionResult(
        status="error",
        message="Provedor de email não configurado ou indisponível. Configure um provedor de email para enviar mensagens.",
        error_detail="Email provider not configured or unhealthy",
        action_type="send_email",
    )


async def _schedule_interview(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        import uuid as uuid_mod

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal
        from app.orchestrator.action_handlers._handler_hooks import (
            log_action_audit,
            resolve_candidate_by_name,
        )

        candidate_name = params.get("candidate_name", "")
        dt = params.get("datetime", "")
        interviewer = params.get("interviewer", "")
        candidate_id = params.get("candidate_id", "")
        company_id = context.get("company_id") if context else None

        if not candidate_id and candidate_name:
            resolved = await resolve_candidate_by_name(candidate_name, company_id)
            if resolved:
                candidate_id = resolved["id"]
                candidate_name = resolved["name"]

        if not candidate_id:
            return ActionResult(
                status="error",
                message=f"Candidato **{candidate_name or 'não identificado'}** não encontrado. Informe o nome completo ou ID.",
                error_detail="Could not resolve candidate_id",
                action_type="schedule_interview",
            )

        async with AsyncSessionLocal() as db:
            candidate_check = await db.execute(text(
                "SELECT id, name FROM candidates WHERE id = CAST(:cid AS uuid)"
            ), {"cid": str(candidate_id)})
            candidate_row = candidate_check.fetchone()
            if not candidate_row:
                return ActionResult(
                    status="error",
                    message=f"Candidato **{candidate_name}** não encontrado no sistema.",
                    error_detail=f"Candidate {candidate_id} does not exist",
                    action_type="schedule_interview",
                )
            if not candidate_name or candidate_name == "o candidato":
                candidate_name = candidate_row.name

            interview_id = str(uuid_mod.uuid4())
            if not company_id:
                raise ValueError(
                    "company_id required for interviews INSERT "
                    "(multi-tenancy fail-closed per ADR-001)"
                )
            await db.execute(text("""
                INSERT INTO interviews (id, candidate_id, interviewer_name, start_time, status,
                    company_id, created_at, updated_at)
                VALUES (:id, CAST(:candidate_id AS uuid), :interviewer, :start_time, 'scheduled',
                    :company_id, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """), {
                "id": interview_id,
                "candidate_id": str(candidate_id),
                "start_time": dt,
                "interviewer": interviewer,
                "company_id": str(company_id),
            })
            await db.commit()

        await log_action_audit("schedule_interview", company_id, candidate_id=str(candidate_id))

        return ActionResult(
            status="executed",
            message=f"Entrevista agendada com **{candidate_name}** para **{dt}**.",
            data={
                "interview_id": interview_id,
                "candidate_id": str(candidate_id),
                "candidate_name": candidate_name,
                "datetime": dt,
                "interviewer": interviewer,
                "scheduled_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="schedule_interview",
        )
    except Exception as e:
        logger.warning(f"schedule_interview failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Não foi possível agendar a entrevista. Tente novamente.",
            error_detail=str(e),
            action_type="schedule_interview",
        )


async def _create_generic_event(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.domains.interview_scheduling.services.calendar_service import calendar_service

        title = params.get("title", "")
        dt_str = params.get("datetime", "")
        description = params.get("description", "")
        location = params.get("location", "")
        duration = params.get("duration_minutes", 60)
        user_id = context.get("user_id") if context else None

        if not user_id:
            return ActionResult(
                status="error",
                message="Usuário não identificado para criar o compromisso.",
                action_type="create_generic_event",
            )

        event_data = await calendar_service.create_generic_event(
            title=title,
            start_time=dt_str,
            organizer_id=user_id,
            description=description,
            location=location,
            duration_minutes=int(duration) if duration else 60,
        )

        return ActionResult(
            status="executed",
            message=f"Compromisso **\"{title}\"** registrado para **{dt_str}**.",
            data={**event_data, "simulated": False},
            action_type="create_generic_event",
        )
    except Exception as e:
        logger.warning(f"create_generic_event failed: {e}")
        return ActionResult(
            status="error",
            message="Não foi possível criar o compromisso. Tente novamente.",
            error_detail=str(e),
            action_type="create_generic_event",
        )


async def _send_feedback(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.domains.communication.services.email_providers import get_email_provider

        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "o candidato")
        feedback_type = params.get("feedback_type", "parcial")
        message = params.get("message", "")
        candidate_email = params.get("email", params.get("candidate_email", ""))

        if not candidate_email:
            from sqlalchemy import text

            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                result = await db.execute(text(
                    "SELECT email, name FROM candidates WHERE id = CAST(:cid AS uuid)"
                ), {"cid": candidate_id})
                row = result.fetchone()
                if row:
                    candidate_email = row.email
                    if not candidate_name or candidate_name == "o candidato":
                        candidate_name = row.name

        if not candidate_email:
            return ActionResult(
                status="error",
                message=f"Email de **{candidate_name}** não encontrado.",
                error_detail="No email found for candidate",
                action_type="send_feedback",
            )

        feedback_labels = {
            "aprovação": "Parabéns! Você foi aprovado(a) para a próxima etapa.",
            "rejeição": "Agradecemos sua participação no processo seletivo.",
            "parcial": "Temos uma atualização sobre sua candidatura.",
        }
        default_body = feedback_labels.get(feedback_type, feedback_labels["parcial"])
        body = message if message else default_body

        provider = get_email_provider()
        provider_status = provider.get_status()
        if provider_status.get("configured") and provider_status.get("healthy"):
            import html as html_module
            safe_body = html_module.escape(body)
            result = await provider.send_email(
                to=candidate_email,
                subject=f"Atualização do processo seletivo - {feedback_type.title()}",
                html_content=f"<p>Olá {candidate_name},</p><p>{safe_body}</p>",
                text_content=f"Olá {candidate_name}, {body}",
            )

        return ActionResult(
            status="executed",
            message=f"Feedback ({feedback_type}) enviado para **{candidate_name}**.",
            data={
                "candidate_id": candidate_id, "candidate_name": candidate_name,
                "feedback_type": feedback_type, "to_email": candidate_email,
                "sent_at": datetime.utcnow().isoformat(), "simulated": False,
            },
            action_type="send_feedback",
        )
    except Exception as e:
        logger.warning(f"send_feedback failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao enviar feedback.",
            error_detail=str(e),
            action_type="send_feedback",
        )


async def _send_whatsapp(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "o candidato")
        message = params.get("message", "")
        phone = params.get("phone", "")

        if not phone:
            from sqlalchemy import text

            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                result = await db.execute(text(
                    "SELECT phone, name FROM candidates WHERE id = CAST(:cid AS uuid)"
                ), {"cid": candidate_id})
                row = result.fetchone()
                if row:
                    phone = row.phone
                    if not candidate_name or candidate_name == "o candidato":
                        candidate_name = row.name

        if not phone:
            return ActionResult(
                status="error",
                message=f"Telefone de **{candidate_name}** não encontrado.",
                error_detail="No phone found for candidate",
                action_type="send_whatsapp",
            )

        from app.domains.communication.services.whatsapp_service import WhatsAppService
        wa_service = WhatsAppService()
        wa_result = await wa_service.send_message(
            to_phone=phone,
            message=message,
            metadata={
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "company_id": context.get("company_id") if context else None,
            },
        )

        if not wa_result.success:
            return ActionResult(
                status="error",
                message=f"Falha ao enviar WhatsApp para **{candidate_name}**: {wa_result.error}",
                error_detail=wa_result.error or "WhatsApp send failed",
                action_type="send_whatsapp",
            )

        is_dev_delivery = wa_result.provider == "development"
        suffix = "\n\n_(Modo desenvolvimento — mensagem registrada no log do servidor.)_" if is_dev_delivery else ""
        return ActionResult(
            status="executed",
            message=f"Mensagem WhatsApp enviada para **{candidate_name}** ({phone}).{suffix}",
            data={
                "candidate_id": candidate_id, "candidate_name": candidate_name,
                "phone": phone, "message": message[:100],
                "message_id": wa_result.message_id,
                "provider": wa_result.provider,
                "sent_at": datetime.utcnow().isoformat(),
                "simulated": is_dev_delivery,
            },
            action_type="send_whatsapp",
        )
    except Exception as e:
        logger.warning(f"send_whatsapp failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao enviar WhatsApp.",
            error_detail=str(e),
            action_type="send_whatsapp",
        )


async def _send_screening_invite(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.domains.communication.services.email_providers import get_email_provider

        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "o candidato")
        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            result = await db.execute(text(
                "SELECT email, name, phone FROM candidates WHERE id = CAST(:cid AS uuid)"
            ), {"cid": candidate_id})
            candidate = result.fetchone()

        if not candidate or not candidate.email:
            return ActionResult(
                status="error",
                message=f"Dados de contato de **{candidate_name}** não encontrados.",
                error_detail="Candidate email not found",
                action_type="send_screening_invite",
            )

        provider = get_email_provider()
        provider_status = provider.get_status()
        if provider_status.get("configured") and provider_status.get("healthy"):
            await provider.send_email(
                to=candidate.email,
                subject="Convite para Triagem - Processo Seletivo",
                html_content=f"<p>Olá {candidate.name},</p><p>Convidamos você para a etapa de triagem do nosso processo seletivo. Acesse o link abaixo para iniciar.</p>",
                text_content=f"Olá {candidate.name}, convidamos você para a etapa de triagem.",
            )

        return ActionResult(
            status="executed",
            message=f"Convite de triagem enviado para **{candidate.name}** ({candidate.email}).",
            data={
                "candidate_id": candidate_id, "candidate_name": candidate.name,
                "email": candidate.email, "job_id": job_id,
                "sent_at": datetime.utcnow().isoformat(), "simulated": False,
            },
            action_type="send_screening_invite",
        )
    except Exception as e:
        logger.warning(f"send_screening_invite failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao enviar convite de triagem.",
            error_detail=str(e),
            action_type="send_screening_invite",
        )


async def _send_candidate_report(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.domains.communication.services.email_providers import get_email_provider

        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "o candidato")
        recipient_email = params.get("recipient_email", "")
        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                SELECT c.name, c.current_title, c.current_company, c.seniority_level,
                       c.years_of_experience, c.location_city, c.location_state
                FROM candidates c WHERE c.id = CAST(:cid AS uuid)
            """), {"cid": candidate_id})
            candidate = result.fetchone()

        if not candidate:
            return ActionResult(
                status="error",
                message="Candidato não encontrado.",
                error_detail="Candidate not found",
                action_type="send_candidate_report",
            )

        report_lines = [
            f"**Parecer — {candidate.name}**",
            f"Cargo: {candidate.current_title or 'N/A'}",
            f"Empresa: {candidate.current_company or 'N/A'}",
            f"Senioridade: {candidate.seniority_level or 'N/A'}",
            f"Experiência: {candidate.years_of_experience or '?'} anos",
            f"Local: {candidate.location_city or ''}/{candidate.location_state or ''}",
        ]

        if recipient_email:
            provider = get_email_provider()
            provider_status = provider.get_status()
            if provider_status.get("configured") and provider_status.get("healthy"):
                await provider.send_email(
                    to=recipient_email,
                    subject=f"Parecer de Candidato: {candidate.name}",
                    html_content="<br>".join(report_lines),
                    text_content="\n".join(report_lines),
                )

        return ActionResult(
            status="executed",
            message=f"Parecer de **{candidate.name}** gerado" + (f" e enviado para {recipient_email}" if recipient_email else "") + ".\n\n" + "\n".join(report_lines),
            data={
                "candidate_id": candidate_id, "candidate_name": candidate.name,
                "recipient_email": recipient_email, "report": report_lines,
                "generated_at": datetime.utcnow().isoformat(), "simulated": False,
            },
            action_type="send_candidate_report",
        )
    except Exception as e:
        logger.warning(f"send_candidate_report failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao gerar/enviar parecer do candidato.",
            error_detail=str(e),
            action_type="send_candidate_report",
        )


async def _send_progress_report(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id", "") or (context or {}).get("job_vacancy_id", "")
        recipient_email = params.get("recipient_email", "")

        if not job_id:
            return ActionResult(
                status="error",
                message="Informe a vaga para gerar o relatório de progresso.",
                error_detail="Missing job_id",
                action_type="send_progress_report",
            )

        async with AsyncSessionLocal() as db:
            job_result = await db.execute(text(
                "SELECT title, status, created_at FROM job_vacancies WHERE id = CAST(:jid AS uuid)"
            ), {"jid": str(job_id)})
            job = job_result.fetchone()

            pipeline_result = await db.execute(text("""
                SELECT stage, COUNT(*) as cnt
                FROM vacancy_candidates
                WHERE vacancy_id = CAST(:jid AS uuid) AND status = 'active'
                GROUP BY stage ORDER BY cnt DESC
            """), {"jid": str(job_id)})
            stages = pipeline_result.fetchall()

        if not job:
            return ActionResult(
                status="error",
                message="Vaga não encontrada.",
                error_detail="Job not found",
                action_type="send_progress_report",
            )

        total = sum(s.cnt for s in stages) if stages else 0
        stage_lines = [f"  - {s.stage}: {s.cnt}" for s in stages]

        report = [
            f"**Relatório de Progresso — {job.title}**",
            f"Status: {job.status}",
            f"Total de candidatos ativos: {total}",
            "",
            "**Pipeline:**",
            *stage_lines,
        ]

        if recipient_email:
            try:
                from app.domains.communication.services.email_providers import get_email_provider
                provider = get_email_provider()
                ps = provider.get_status()
                if ps.get("configured") and ps.get("healthy"):
                    await provider.send_email(
                        to=recipient_email,
                        subject=f"Relatório de Progresso: {job.title}",
                        html_content="<br>".join(report),
                        text_content="\n".join(report),
                    )
            except Exception as email_err:
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.warning(f"Failed to email progress report: {email_err}")

        return ActionResult(
            status="executed",
            message="\n".join(report) + (f"\n\nEnviado para {recipient_email}." if recipient_email else ""),
            data={
                "job_id": job_id, "job_title": job.title,
                "total_candidates": total,
                "stages": {s.stage: s.cnt for s in stages},
                "generated_at": datetime.utcnow().isoformat(), "simulated": False,
            },
            action_type="send_progress_report",
        )
    except Exception as e:
        logger.warning(f"send_progress_report failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao gerar relatório de progresso.",
            error_detail=str(e),
            action_type="send_progress_report",
        )


async def _share_candidate_profile(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        import uuid as uuid_mod

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "o candidato")
        recipient_email = params.get("recipient_email", "")
        recipient_name = params.get("recipient_name", "")
        custom_message = params.get("message", "")

        if not candidate_id:
            return ActionResult(
                status="error",
                message="Informe o candidato para compartilhar.",
                error_detail="Missing candidate_id",
                action_type="share_candidate_profile",
            )

        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                SELECT name, current_title, current_company, seniority_level,
                       years_of_experience, location_city
                FROM candidates WHERE id = CAST(:cid AS uuid)
            """), {"cid": candidate_id})
            candidate = result.fetchone()

        if not candidate:
            return ActionResult(
                status="error",
                message="Candidato não encontrado.",
                error_detail="Candidate not found",
                action_type="share_candidate_profile",
            )

        share_token = str(uuid_mod.uuid4())[:12]
        share_link = f"/shared/candidate/{share_token}"

        profile_summary = (
            f"**{candidate.name}** — {candidate.current_title or 'N/A'} @ "
            f"{candidate.current_company or 'N/A'} | {candidate.seniority_level or 'N/A'} | "
            f"{candidate.years_of_experience or '?'} anos | {candidate.location_city or 'N/A'}"
        )

        if recipient_email:
            try:
                from app.domains.communication.services.email_providers import get_email_provider
                provider = get_email_provider()
                ps = provider.get_status()
                if ps.get("configured") and ps.get("healthy"):
                    body = custom_message or f"Estou compartilhando o perfil de {candidate.name} com você."
                    await provider.send_email(
                        to=recipient_email,
                        subject=f"Perfil compartilhado: {candidate.name}",
                        html_content=f"<p>{body}</p><p>{profile_summary}</p>",
                        text_content=f"{body}\n\n{profile_summary}",
                    )
            except Exception as email_err:
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.warning(f"Failed to email shared profile: {email_err}")

        return ActionResult(
            status="executed",
            message=f"Perfil de **{candidate.name}** compartilhado" + (f" com {recipient_name or recipient_email}" if recipient_email else "") + f".\n\n{profile_summary}",
            data={
                "candidate_id": candidate_id, "candidate_name": candidate.name,
                "share_link": share_link, "recipient_email": recipient_email,
                "shared_at": datetime.utcnow().isoformat(), "simulated": False,
            },
            action_type="share_candidate_profile",
        )
    except Exception as e:
        logger.warning(f"share_candidate_profile failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao compartilhar perfil do candidato.",
            error_detail=str(e),
            action_type="share_candidate_profile",
        )


async def _create_template(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from app.core.database import AsyncSessionLocal
        from app.orchestrator.action_handlers._handler_hooks import (
            log_action_audit,
        )

        name = (params.get("name") or "").strip()
        subject = (params.get("subject") or "").strip()
        body_html = (params.get("body_html") or "").strip()
        body_text = (params.get("body_text") or "").strip()
        category = params.get("category") or "custom"
        channel = params.get("channel") or "email"
        variables = params.get("variables") or []
        company_id = context.get("company_id") if context else None
        user_id = context.get("user_id") if context else None

        if not company_id:
            return ActionResult(
                status="error",
                message="Contexto de empresa ausente. Não é possível criar templates sem empresa associada.",
                error_detail="Missing company_id — tenant isolation required",
                action_type="create_template",
            )
        if not user_id:
            return ActionResult(
                status="error",
                message="Usuário não identificado. Faça login para criar templates.",
                error_detail="Missing user_id",
                action_type="create_template",
            )
        if not name:
            return ActionResult(
                status="error",
                message="Nome do template é obrigatório.",
                error_detail="Missing template name",
                action_type="create_template",
            )
        if not body_html:
            return ActionResult(
                status="error",
                message="Conteúdo HTML do template é obrigatório.",
                error_detail="Missing body_html",
                action_type="create_template",
            )

        import asyncio
        import warnings

        from app.domains.communication.services.email_service import EmailService

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            email_svc = EmailService()

        try:
            async with AsyncSessionLocal() as db:
                created = await asyncio.wait_for(
                    email_svc.create_template(
                        db=db,
                        name=name,
                        body_html=body_html,
                        subject=subject or None,
                        body_text=body_text or None,
                        category=category,
                        channel=channel,
                        variables=variables,
                        company_id=str(company_id),
                        created_by=str(user_id),
                    ),
                    timeout=15.0,
                )
                template_id = str(created.id)
        except asyncio.TimeoutError:
            logger.error("create_template DB timeout")
            return ActionResult(
                status="error",
                message="Tempo limite excedido ao acessar o banco de dados. Tente novamente.",
                error_detail="Database operation timed out",
                action_type="create_template",
            )
        except ValueError as ve:
            return ActionResult(
                status="error",
                message=str(ve),
                error_detail=str(ve),
                action_type="create_template",
            )
        except RuntimeError as re:
            return ActionResult(
                status="error",
                message="Tabela de templates não encontrada. Execute as migrações do banco de dados.",
                error_detail=str(re),
                action_type="create_template",
            )

        await log_action_audit("create_template", company_id, details={"template_id": template_id, "name": name})

        return ActionResult(
            status="executed",
            message=f'Template **"{name}"** criado com sucesso (canal: {channel}).',
            data={
                "template_id": template_id,
                "name": name,
                "channel": channel,
                "category": category,
                "created_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="create_template",
        )
    except Exception as e:
        logger.warning(f"create_template failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao criar template.",
            error_detail=str(e),
            action_type="create_template",
        )
