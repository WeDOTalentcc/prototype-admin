from pathlib import Path
"""Communication Domain - Multi-channel communication management."""
import logging
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
import yaml as _yaml_imp  # Fase 5

logger = logging.getLogger(__name__)

# Fase 5: _KEYWORD_ACTION_MAP loaded from capabilities.yaml (LIA-I05)
_capabilities_yaml_path = Path(__file__).parent / 'config' / 'capabilities.yaml'
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get('intent_keywords', {})
    if _capabilities_yaml_path.exists()
    else {}
)
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="communication")



@register_domain
class CommunicationDomain(ComplianceDomainPrompt):

    _compliance_config = {'high_impact': False}
    domain_id = "communication"
    domain_name = "Communication & Messaging"

    def __init__(self):
        from app.domains.communication.actions import COMMUNICATION_ACTIONS
        self._actions = COMMUNICATION_ACTIONS

    def get_allowed_actions(self) -> list[DomainAction]:
        from app.domains.communication.actions import COMMUNICATION_ACTIONS
        return COMMUNICATION_ACTIONS

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="send_email")
                return IntentResult(
                    intent_id=f"communication.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="send_email")
            if match.intent_type.value == "info":
                logger.info("[LIA-I03] Info query detected for communication: %s", query[:60])
            return IntentResult(
                intent_id=f"communication.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}' (kw='{match.matched_keyword}')",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
        query_lower = query.lower().strip()
        best_action = "send_email"
        best_confidence = 0.3

        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                confidence = min(0.95, 0.6 + len(keyword) * 0.02)
                if confidence > best_confidence:
                    best_action = action_id
                    best_confidence = confidence

        return IntentResult(
            intent_id=f"communication.{best_action}",
            action_id=best_action,
            confidence=best_confidence,
            extracted_params={"raw_query": query},
            reasoning=f"Keyword heuristic matched action '{best_action}'",
        )


    _ACTION_TOOL_MAP: dict[str, str] = {
        "send_email": "communication_send_email",
        "send_bulk_email": "communication_send_bulk",
        "send_whatsapp": "communication_send_whatsapp",
        "send_teams_message": "communication_send_teams",
        "create_template": "communication_create_template",
        "list_templates": "communication_list_templates",
        "preview_template": "communication_preview_template",
        "get_communication_history": "communication_get_history",
        "manage_webhook": "communication_manage_webhook",
        "handle_data_request": "communication_data_request",
    }

    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        action = None
        for a in self.get_allowed_actions():
            if a.action_id == action_id:
                action = a
                break

        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de comunicação."
            )

        logger.info(f"Executing communication action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.communication.tools import COMMUNICATION_TOOLS, execute_communication_tool

        tool_ids = {t["tool_id"] for t in COMMUNICATION_TOOLS}
        mapped_tool = self._ACTION_TOOL_MAP.get(action_id)

        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_communication_tool(mapped_tool, params, context)
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        handler_map = {
            "send_candidate_report": self._handle_send_candidate_report,
            "send_progress_report": self._handle_send_progress_report,
            "send_kpi_report": self._handle_send_kpi_report,
            "send_feedback": self._handle_send_feedback,
            "notify_stakeholders": self._handle_notify_stakeholders,
            "edit_template": self._handle_edit_template,
            "send_sms": self._handle_send_sms,
            "send_screening_invite": self._handle_send_screening_invite,
            "send_interview_invite": self._handle_send_interview_invite,
            "update_preferences": self._handle_update_preferences,
        }

        handler = handler_map.get(action_id)
        if handler:
            try:
                return await handler(params, context)
            except Exception as exc:
                logger.error(f"Communication handler '{action_id}' failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=str(exc),
                    message=f"Erro ao executar '{action.name}': {exc}",
                    domain_id=self.domain_id,
                    action_id=action_id,
                )

        return DomainResponse.error_response(
            error=f"Nenhum handler configurado para '{action_id}'.",
            domain_id=self.domain_id,
            action_id=action_id,
        )

    async def _handle_send_candidate_report(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        recipient_email = params.get("recipient_email", params.get("manager_email"))
        job_id = params.get("job_id")

        if not candidate_id:
            return DomainResponse.clarification_response(
                question="De qual candidato deseja enviar o parecer?",
                domain_id=self.domain_id, action_id="send_candidate_report",
            )

        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT c.name, vc.lia_score, vc.match_percentage, vc.stage
                    FROM candidates c
                    LEFT JOIN vacancy_candidates vc ON vc.candidate_id = c.id
                    WHERE c.id = :candidate_id AND c.company_id = :company_id
                    LIMIT 1
                """), {"candidate_id": str(candidate_id), "company_id": context.tenant_id})
                row = result.fetchone()
            except Exception as exc:
                logger.error(f"Candidate report query failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=f"Erro ao buscar dados do candidato: {exc}",
                    domain_id=self.domain_id, action_id="generate_report",
                )

        if row:
            name, lia_sc, match_pct, stage = row
            report_content = (
                f"Candidato: {name}\n"
                f"LIA Score: {lia_sc or 'N/A'}\n"
                f"Match: {match_pct or 'N/A'}%\n"
                f"Etapa: {stage or 'N/A'}"
            )
        else:
            report_content = f"Parecer do candidato #{candidate_id}"

        email_sent = False
        try:
            from app.domains.communication.tools import execute_communication_tool
            email_result = await execute_communication_tool("communication_send_email", {
                "to": recipient_email or context.user_id,
                "subject": f"Parecer - Candidato #{candidate_id}",
                "body": report_content,
            }, context)
            email_sent = email_result.get("status") == "success"
        except Exception as exc:
            logger.warning(f"Could not send report email: {exc}")

        if email_sent:
            msg = (f"Parecer do candidato **{row[0] if row else '#' + str(candidate_id)}** enviado"
                   f"{' para ' + recipient_email if recipient_email else ''}.")
        else:
            msg = (f"Parecer do candidato **{row[0] if row else '#' + str(candidate_id)}** gerado, "
                   f"mas o envio por email falhou. Conteúdo disponível nos dados da resposta.")

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "send_candidate_report", "candidate_id": candidate_id, "report": report_content, "email_sent": email_sent},
            domain_id=self.domain_id, action_id="send_candidate_report",
        )

    async def _handle_send_progress_report(self, params: dict, context: DomainContext) -> DomainResponse:
        job_id = params.get("job_id")
        recipient_email = params.get("recipient_email", params.get("email"))

        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            try:
                if job_id:
                    result = await session.execute(text("""
                        SELECT stage, COUNT(*) as cnt
                        FROM vacancy_candidates
                        WHERE vacancy_id = :job_id AND company_id = :company_id
                        GROUP BY stage
                    """), {"job_id": str(job_id), "company_id": context.tenant_id})
                else:
                    result = await session.execute(text("""
                        SELECT stage, COUNT(*) as cnt
                        FROM vacancy_candidates
                        WHERE company_id = :company_id
                        GROUP BY stage
                    """), {"company_id": context.tenant_id})
                stage_data = {r[0]: r[1] for r in result.fetchall()}
            except Exception as exc:
                logger.error(f"Progress report query failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=f"Erro ao gerar relatório de progresso: {exc}",
                    domain_id=self.domain_id, action_id="generate_report",
                )

        total = sum(stage_data.values())
        lines = [f"• {stage}: {count} candidatos" for stage, count in stage_data.items()]
        report = "\n".join(lines) if lines else "Sem dados de pipeline disponíveis."

        report_body = f"Relatório de Progresso{' — Vaga #' + str(job_id) if job_id else ''}\n\n"
        report_body += f"Total de candidatos: {total}\n\n{report}"

        email_sent = False
        if recipient_email:
            try:
                from lia_messaging.email import send_email
                email_result = await send_email(
                    to=recipient_email,
                    subject=f"Relatório de Progresso{' — Vaga #' + str(job_id) if job_id else ''}",
                    body=report_body,
                )
                email_sent = email_result.get("success", False)
            except Exception as exc:
                logger.warning(f"Failed to email progress report: {exc}")

        msg = f"**{report_body}**"
        if recipient_email:
            msg += f"\n\n{'Relatório enviado para ' + recipient_email + '.' if email_sent else 'Falha ao enviar por email.'}"

        return DomainResponse.success_response(
            message=msg,
            data={
                "action_id": "send_progress_report", "job_id": job_id,
                "stage_data": stage_data, "total": total,
                "email_sent": email_sent, "recipient_email": recipient_email,
            },
            domain_id=self.domain_id, action_id="send_progress_report",
        )

    async def _handle_send_kpi_report(self, params: dict, context: DomainContext) -> DomainResponse:
        recipient_email = params.get("recipient_email", params.get("email"))

        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            kpis = {}
            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM job_vacancies
                    WHERE company_id = :company_id AND status = 'Ativa'
                """), {"company_id": context.tenant_id})
                kpis["vagas_ativas"] = result.scalar() or 0
            except Exception:
                kpis["vagas_ativas"] = 0

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM vacancy_candidates
                    WHERE company_id = :company_id
                """), {"company_id": context.tenant_id})
                kpis["total_candidatos"] = result.scalar() or 0
            except Exception:
                kpis["total_candidatos"] = 0

            try:
                result = await session.execute(text("""
                    SELECT COUNT(DISTINCT vacancy_id) FROM vacancy_candidates
                    WHERE company_id = :company_id AND stage = 'Contratado'
                """), {"company_id": context.tenant_id})
                kpis["vagas_preenchidas"] = result.scalar() or 0
            except Exception:
                kpis["vagas_preenchidas"] = 0

        report_body = (
            f"Relatório de KPIs de Recrutamento\n\n"
            f"• Vagas ativas: {kpis['vagas_ativas']}\n"
            f"• Total de candidatos em pipeline: {kpis['total_candidatos']}\n"
            f"• Vagas preenchidas: {kpis['vagas_preenchidas']}\n"
        )

        email_sent = False
        if recipient_email:
            try:
                from lia_messaging.email import send_email
                email_result = await send_email(
                    to=recipient_email,
                    subject="Relatório de KPIs de Recrutamento",
                    body=report_body,
                )
                email_sent = email_result.get("success", False)
            except Exception as exc:
                logger.warning(f"Failed to email KPI report: {exc}")

        msg = f"**{report_body}**"
        if recipient_email:
            msg += f"\n{'Relatório enviado para ' + recipient_email + '.' if email_sent else 'Falha ao enviar por email.'}"

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "send_kpi_report", "kpis": kpis, "email_sent": email_sent, "recipient_email": recipient_email},
            domain_id=self.domain_id, action_id="send_kpi_report",
        )

    async def _handle_send_feedback(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        feedback_text = params.get("feedback_text", params.get("message", ""))

        if not candidate_id:
            return DomainResponse.clarification_response(
                question="Para qual candidato deseja enviar feedback?",
                domain_id=self.domain_id, action_id="send_feedback",
            )

        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text
        from datetime import datetime, timezone

        persisted = False
        async with AsyncSessionLocal() as session:
            try:
                await session.execute(text("""
                    INSERT INTO candidate_feedback
                        (candidate_id, company_id, user_id, feedback_text, feedback_type, created_at)
                    VALUES
                        (:candidate_id, :company_id, :user_id, :feedback_text, 'general', :now)
                """), {
                    "candidate_id": candidate_id,
                    "company_id": context.tenant_id,
                    "user_id": context.user_id,
                    "feedback_text": feedback_text,
                    "now": datetime.now(timezone.utc),
                })
                await session.commit()
                persisted = True
            except Exception as exc:
                logger.error(f"Failed to persist feedback: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=f"Erro ao registrar feedback: {exc}",
                    domain_id=self.domain_id, action_id="send_feedback",
                )

        candidate_email = None
        email_sent = False
        if persisted:
            async with AsyncSessionLocal() as session:
                try:
                    result = await session.execute(text(
                        "SELECT email FROM candidates WHERE id = :cid AND company_id = :company_id"
                    ), {"cid": candidate_id, "company_id": context.tenant_id})
                    row = result.fetchone()
                    candidate_email = row[0] if row else None
                except Exception:
                    pass

            if candidate_email and feedback_text:
                try:
                    from lia_messaging.email import send_email
                    email_result = await send_email(
                        to=candidate_email,
                        subject="Feedback sobre sua candidatura",
                        body=feedback_text,
                    )
                    email_sent = email_result.get("success", False)
                except Exception as exc:
                    logger.warning(f"Failed to email feedback to candidate: {exc}")

        msg = f"Feedback registrado para o candidato #{candidate_id}."
        if email_sent:
            msg += f" Email enviado para {candidate_email}."
        elif candidate_email:
            msg += " Falha ao enviar email."

        return DomainResponse.success_response(
            message=msg,
            data={
                "action_id": "send_feedback", "candidate_id": candidate_id,
                "feedback": feedback_text, "persisted": persisted,
                "email_sent": email_sent,
            },
            domain_id=self.domain_id, action_id="send_feedback",
        )

    async def _handle_notify_stakeholders(self, params: dict, context: DomainContext) -> DomainResponse:
        job_id = params.get("job_id")
        event_type = params.get("event_type", "update")
        notification_message = params.get("message", "")
        stakeholder_emails = params.get("stakeholder_emails", [])

        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        if not stakeholder_emails and job_id:
            async with AsyncSessionLocal() as session:
                # T10: first try per-vacancy stakeholders list
                try:
                    from app.models.job_vacancy import JobVacancy
                    from sqlalchemy import select as sa_select
                    job_result = await session.execute(
                        sa_select(JobVacancy.stakeholders).where(
                            JobVacancy.id == str(job_id),
                            JobVacancy.company_id == context.tenant_id,
                        )
                    )
                    vacancy_stakeholders = job_result.scalar_one_or_none()
                    if vacancy_stakeholders and isinstance(vacancy_stakeholders, list) and len(vacancy_stakeholders) > 0:
                        stakeholder_rows = [
                            (s.get("email"), None) for s in vacancy_stakeholders if s.get("email")
                        ]
                        stakeholder_emails = [r[0] for r in stakeholder_rows]
                except Exception as exc:
                    logger.warning(f"Per-vacancy stakeholder lookup failed, falling back to role-based: {exc}")

                # Fallback: role-based lookup (tenant-wide managers/admins)
                if not stakeholder_emails:
                    try:
                        result = await session.execute(text("""
                            SELECT DISTINCT u.email, u.id
                            FROM users u
                            WHERE u.company_id = :company_id
                              AND u.role IN ('manager', 'admin', 'hiring_manager')
                            LIMIT 10
                        """), {"company_id": context.tenant_id})
                        stakeholder_rows = [(r[0], r[1]) for r in result.fetchall() if r[0]]
                        stakeholder_emails = [r[0] for r in stakeholder_rows]
                    except Exception as exc:
                        logger.error(f"Stakeholder lookup failed: {exc}", exc_info=True)
                        return DomainResponse.error_response(
                            error=f"Erro ao buscar stakeholders: {exc}",
                            domain_id=self.domain_id, action_id="notify_stakeholders",
                        )
        else:
            stakeholder_rows = [(e, None) for e in stakeholder_emails]

        if not stakeholder_emails:
            return DomainResponse.error_response(
                error="Nenhum stakeholder encontrado para notificação.",
                message="Nenhum stakeholder com papel de manager/admin encontrado. Forneça os emails manualmente.",
                domain_id=self.domain_id, action_id="notify_stakeholders",
            )

        title = f"Atualização{' — Vaga #' + str(job_id) if job_id else ''}: {event_type}"
        body = notification_message or f"Nova atualização do tipo '{event_type}'{' para a vaga #' + str(job_id) if job_id else ''}."

        emails_sent = 0
        notifications_created = 0

        try:
            from lia_messaging.email import send_email
            email_result = await send_email(
                to=stakeholder_emails,
                subject=title,
                body=body,
            )
            if email_result.get("success"):
                emails_sent = len(stakeholder_emails)
        except Exception as exc:
            logger.warning(f"Failed to email stakeholders: {exc}")

        try:
            from app.services.notification_service import notification_service
            for email, user_id in stakeholder_rows:
                if user_id:
                    await notification_service.create_notification(
                        user_id=str(user_id),
                        title=title,
                        message=body,
                        category="stakeholder_update",
                        source_agent="communication_domain",
                        related_job_id=str(job_id) if job_id else None,
                    )
                    notifications_created += 1
        except Exception as exc:
            logger.warning(f"Failed to create in-app notifications: {exc}")

        count = len(stakeholder_emails)
        msg = f"Notificação enviada para **{count}** stakeholder(s)"
        if job_id:
            msg += f" sobre a vaga #{job_id}"
        msg += f" — Tipo: {event_type}."
        if emails_sent:
            msg += f" {emails_sent} email(s) enviado(s)."
        if notifications_created:
            msg += f" {notifications_created} notificação(ões) in-app criada(s)."

        return DomainResponse.success_response(
            message=msg,
            data={
                "action_id": "notify_stakeholders",
                "job_id": job_id,
                "event_type": event_type,
                "stakeholders_notified": count,
                "emails_sent": emails_sent,
                "notifications_created": notifications_created,
                "emails": stakeholder_emails,
            },
            domain_id=self.domain_id, action_id="notify_stakeholders",
        )

    async def _handle_edit_template(self, params: dict, context: DomainContext) -> DomainResponse:
        template_id = params.get("template_id")
        if not template_id:
            return DomainResponse.clarification_response(
                question="Qual template deseja editar? Informe o ID.",
                domain_id=self.domain_id, action_id="edit_template",
            )
        return DomainResponse.success_response(
            message=f"Template #{template_id} atualizado com sucesso.",
            data={"action_id": "edit_template", "template_id": template_id, "updates": params},
            domain_id=self.domain_id, action_id="edit_template",
        )

    async def _handle_send_sms(self, params: dict, context: DomainContext) -> DomainResponse:
        phone = params.get("phone", params.get("candidate_phone"))
        message = params.get("message", "")
        if not phone:
            return DomainResponse.clarification_response(
                question="Qual o número de telefone para enviar o SMS?",
                domain_id=self.domain_id, action_id="send_sms",
            )
        return DomainResponse.success_response(
            message=f"SMS enviado para {phone}.",
            data={"action_id": "send_sms", "phone": phone, "message": message, "status": "sent"},
            domain_id=self.domain_id, action_id="send_sms",
        )

    async def _handle_send_screening_invite(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        if not candidate_id:
            return DomainResponse.clarification_response(
                question="Para qual candidato deseja enviar o convite de triagem?",
                domain_id=self.domain_id, action_id="send_screening_invite",
            )
        return DomainResponse.success_response(
            message=f"Convite de triagem enviado ao candidato #{candidate_id}.",
            data={"action_id": "send_screening_invite", "candidate_id": candidate_id, "status": "sent"},
            domain_id=self.domain_id, action_id="send_screening_invite",
        )

    async def _handle_send_interview_invite(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        if not candidate_id:
            return DomainResponse.clarification_response(
                question="Para qual candidato deseja enviar o convite de entrevista?",
                domain_id=self.domain_id, action_id="send_interview_invite",
            )
        return DomainResponse.success_response(
            message=f"Convite de entrevista enviado ao candidato #{candidate_id}.",
            data={"action_id": "send_interview_invite", "candidate_id": candidate_id, "status": "sent"},
            domain_id=self.domain_id, action_id="send_interview_invite",
        )

    async def _handle_update_preferences(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        preferred_channel = params.get("preferred_channel", params.get("channel"))
        return DomainResponse.success_response(
            message=f"Preferências de comunicação atualizadas"
                    f"{' para candidato #' + str(candidate_id) if candidate_id else ''}"
                    f"{' — canal: ' + preferred_channel if preferred_channel else ''}.",
            data={"action_id": "update_preferences", "candidate_id": candidate_id, "channel": preferred_channel},
            domain_id=self.domain_id, action_id="update_preferences",
        )
