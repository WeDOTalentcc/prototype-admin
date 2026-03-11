"""
Transition Dispatch Service - Deterministic auto-dispatch for pipeline transitions.
Layer 1: Template-based message dispatch without AI interpretation.
"""
import logging
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import VacancyCandidate, Candidate
from app.models.job_vacancy import JobVacancy
from app.domains.communication.models.email_template import EmailTemplate, EmailLog
from app.domains.communication.models.communication_matrix import CommunicationMatrixEntry
from app.domains.communication.services.communication_dispatcher import CommunicationDispatcher
from app.services.candidate_channel_selector import CandidateChannelSelector

logger = logging.getLogger(__name__)

ACTION_BEHAVIOR_SITUATION_MAP: Dict[str, Optional[str]] = {
    "screening": "triagem",
    "scheduling": "agendamento",
    "evaluation": "avaliacao_tecnica",
    "verification": "avaliacao_tecnica",
    "offer": "proposta",
    "conclusion_rejected": "rejeicao",
    "conclusion_declined": "rejeicao",
    "conclusion_hired": None,
    "passive": None,
    "intake": None,
}

# Maps action_behavior → CommunicationMatrixEntry.trigger_name
ACTION_BEHAVIOR_TRIGGER_MAP: Dict[str, Optional[str]] = {
    "screening": "triagem_aprovado",
    "scheduling": "entrevista_agendada",
    "evaluation": None,
    "verification": None,
    "offer": "proposta_gerada",
    "conclusion_rejected": "triagem_reprovado",
    "conclusion_declined": "triagem_reprovado",
    "conclusion_hired": "contratacao_efetivada",
    "passive": None,
    "intake": None,
}

# Channels this service can dispatch (candidate-facing external channels only)
DISPATCHABLE_CHANNELS = {"email", "whatsapp", "sms"}


class TransitionDispatchService:
    """Handles automatic message dispatch when candidates move between pipeline stages."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dispatcher = CommunicationDispatcher()

    async def dispatch_for_transition(
        self,
        vacancy_candidate_id: str,
        to_stage: str,
        action_behavior: str,
        channel: str = "email",
        company_id: Optional[str] = None,
        triggered_by: Optional[str] = None,
        extra_variables: Optional[Dict[str, Any]] = None,
        personalized_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Main entry point for dispatching messages on transition."""
        try:
            if action_behavior not in ACTION_BEHAVIOR_SITUATION_MAP:
                logger.warning(
                    f"Unknown action_behavior '{action_behavior}' — skipping dispatch"
                )
                return {
                    "success": False,
                    "channel": channel,
                    "message_id": None,
                    "template_name": None,
                    "recipient": None,
                    "mock": False,
                    "error": f"Unknown action_behavior: {action_behavior}",
                }

            situation = ACTION_BEHAVIOR_SITUATION_MAP[action_behavior]
            if situation is None:
                logger.info(
                    f"action_behavior '{action_behavior}' has no auto-dispatch configured — skipping"
                )
                return {
                    "success": True,
                    "channel": channel,
                    "message_id": None,
                    "template_name": None,
                    "recipient": None,
                    "mock": False,
                    "error": None,
                }

            # --- Communication Matrix lookup ---
            trigger_name = ACTION_BEHAVIOR_TRIGGER_MAP.get(action_behavior)
            matrix_entry = await self._get_matrix_entry(trigger_name, company_id)

            if matrix_entry:
                if not matrix_entry.is_active:
                    logger.info(
                        f"Matrix entry '{trigger_name}' is inactive for company={company_id} — skipping dispatch"
                    )
                    return {
                        "success": True,
                        "channel": channel,
                        "message_id": None,
                        "template_name": None,
                        "recipient": None,
                        "mock": False,
                        "skipped": True,
                        "skip_reason": "matrix_inactive",
                        "matrix_trigger": trigger_name,
                        "error": None,
                    }

                if matrix_entry.requires_approval:
                    # Log for observability; blocking enforcement is L3 (Human Review Gate)
                    logger.info(
                        f"Matrix entry '{trigger_name}' requires_approval=True — "
                        f"dispatching (L3 enforcement pending)"
                    )

                raw_channels = matrix_entry.channels or []
                effective_channels = [ch for ch in raw_channels if ch in DISPATCHABLE_CHANNELS]
                if not effective_channels:
                    effective_channels = [channel]
            else:
                effective_channels = [channel]
                trigger_name = None

            # Load candidate data once
            candidate_data = await self._load_candidate_data(vacancy_candidate_id)
            if not candidate_data:
                logger.error(
                    f"Could not load candidate data for vacancy_candidate_id={vacancy_candidate_id}"
                )
                return {
                    "success": False,
                    "channel": channel,
                    "message_id": None,
                    "template_name": None,
                    "recipient": None,
                    "mock": False,
                    "matrix_trigger": trigger_name,
                    "error": "Candidate data not found",
                }

            # N3 — Filtrar canais pelas preferências do candidato
            candidate_id_str = candidate_data.get("candidate_id")
            if candidate_id_str and effective_channels:
                try:
                    channel_selector = CandidateChannelSelector(self.db)
                    effective_channels = await channel_selector.select_channels(
                        candidate_id=candidate_id_str,
                        company_id=company_id,
                        requested_channels=effective_channels,
                        message_type="transactional",
                    )
                    logger.info(
                        f"[CHANNEL_SELECTOR] Canais efetivos para candidate={candidate_id_str}: "
                        f"{effective_channels}"
                    )
                except Exception as sel_err:
                    logger.warning(f"[CHANNEL_SELECTOR] Erro ao filtrar canais: {sel_err} — usando canais originais")

            variables = self._build_variables(candidate_data, extra_variables)

            # Dispatch per channel; collect all results
            channel_results: List[Dict[str, Any]] = []
            for ch in effective_channels:
                result = await self._dispatch_single_channel(
                    channel=ch,
                    situation=situation,
                    candidate_data=candidate_data,
                    variables=variables,
                    company_id=company_id,
                    triggered_by=triggered_by,
                    personalized_content=personalized_content,
                )
                channel_results.append(result)
                logger.info(
                    f"[DISPATCH] channel={ch} trigger={trigger_name} "
                    f"success={result.get('success')} mock={result.get('mock')}"
                )

            # Return primary result (first success, else last)
            primary = next((r for r in channel_results if r.get("success")), channel_results[-1])
            primary["dispatched_channels"] = [r.get("channel") for r in channel_results]
            primary["matrix_trigger"] = trigger_name
            return primary

        except Exception as e:
            logger.error(f"Unexpected error in dispatch_for_transition: {e}", exc_info=True)
            return {
                "success": False,
                "channel": channel,
                "message_id": None,
                "template_name": None,
                "recipient": None,
                "mock": False,
                "ai_personalized": False,
                "error": str(e),
            }

    async def _get_matrix_entry(
        self, trigger_name: Optional[str], company_id: Optional[str]
    ) -> Optional[CommunicationMatrixEntry]:
        """Query CommunicationMatrixEntry by trigger_name.
        Priority: company-specific → platform default (company_id IS NULL).
        """
        if not trigger_name:
            return None
        try:
            if company_id:
                result = await self.db.execute(
                    select(CommunicationMatrixEntry).where(
                        CommunicationMatrixEntry.trigger_name == trigger_name,
                        CommunicationMatrixEntry.company_id == company_id,
                    )
                )
                entry = result.scalars().first()
                if entry:
                    return entry

            # Platform default
            result = await self.db.execute(
                select(CommunicationMatrixEntry).where(
                    CommunicationMatrixEntry.trigger_name == trigger_name,
                    CommunicationMatrixEntry.company_id == None,  # noqa: E711
                )
            )
            return result.scalars().first()
        except Exception as e:
            logger.warning(
                f"Error querying communication matrix for trigger '{trigger_name}': {e}"
            )
            return None

    async def _dispatch_single_channel(
        self,
        channel: str,
        situation: str,
        candidate_data: Dict[str, Any],
        variables: Dict[str, str],
        company_id: Optional[str],
        triggered_by: Optional[str],
        personalized_content: Optional[str],
    ) -> Dict[str, Any]:
        """Dispatch a message through a single channel. Returns a result dict."""
        template = await self._find_template(situation, channel, company_id)
        if not template:
            logger.warning(
                f"No active template found for situation='{situation}', channel='{channel}', "
                f"company_id='{company_id}'"
            )
            return {
                "success": False,
                "channel": channel,
                "message_id": None,
                "template_name": None,
                "recipient": candidate_data.get("email"),
                "mock": False,
                "ai_personalized": False,
                "error": f"No template found for situation '{situation}' and channel '{channel}'",
            }

        rendered_subject = self._render_template(template.subject or "", variables)
        rendered_html = self._render_template(template.body_html or "", variables)
        rendered_text = self._render_template(template.body_text or "", variables)

        ai_personalized = False
        if personalized_content:
            rendered_html = personalized_content
            rendered_text = re.sub(r"<[^>]+>", "", personalized_content)
            ai_personalized = True
            logger.info(f"[DISPATCH] Using AI-personalized content instead of template")

        if channel == "whatsapp":
            phone = candidate_data.get("mobile_phone") or candidate_data.get("phone")
            if not phone:
                logger.error(
                    f"No phone number available for candidate {candidate_data.get('candidate_id')}"
                )
                await self._log_dispatch(
                    template_id=template.id,
                    candidate_id=str(candidate_data.get("candidate_id", "")),
                    recipient="",
                    subject=rendered_subject,
                    body_html=rendered_html,
                    body_text=rendered_text,
                    status="failed",
                    error="No phone number available",
                    variables=variables,
                    created_by=triggered_by,
                )
                return {
                    "success": False,
                    "channel": "whatsapp",
                    "message_id": None,
                    "template_name": template.name,
                    "recipient": None,
                    "mock": False,
                    "ai_personalized": ai_personalized,
                    "error": "No phone number available for candidate",
                }

            plain_message = re.sub(r"<[^>]+>", "", rendered_html) if rendered_html else rendered_text
            result = self.dispatcher.send_whatsapp(to_phone=phone, message=plain_message)

            status = "sent" if result.get("success") else "failed"
            await self._log_dispatch(
                template_id=template.id,
                candidate_id=str(candidate_data.get("candidate_id", "")),
                recipient=phone,
                subject=rendered_subject,
                body_html=rendered_html,
                body_text=plain_message,
                status=status,
                error=result.get("error"),
                variables=variables,
                created_by=triggered_by,
            )

            return {
                "success": result.get("success", False),
                "channel": "whatsapp",
                "message_id": result.get("message_id"),
                "template_name": template.name,
                "recipient": phone,
                "mock": result.get("mock", False),
                "ai_personalized": ai_personalized,
                "error": result.get("error"),
            }

        else:
            email = candidate_data.get("email")
            if not email:
                logger.error(
                    f"No email available for candidate {candidate_data.get('candidate_id')}"
                )
                await self._log_dispatch(
                    template_id=template.id,
                    candidate_id=str(candidate_data.get("candidate_id", "")),
                    recipient="",
                    subject=rendered_subject,
                    body_html=rendered_html,
                    body_text=rendered_text,
                    status="failed",
                    error="No email available",
                    variables=variables,
                    created_by=triggered_by,
                )
                return {
                    "success": False,
                    "channel": "email",
                    "message_id": None,
                    "template_name": template.name,
                    "recipient": None,
                    "mock": False,
                    "ai_personalized": ai_personalized,
                    "error": "No email available for candidate",
                }

            result = self.dispatcher.send_email(
                to_email=email,
                subject=rendered_subject,
                body_html=rendered_html,
                body_text=rendered_text or None,
            )

            status = "sent" if result.get("success") else "failed"
            await self._log_dispatch(
                template_id=template.id,
                candidate_id=str(candidate_data.get("candidate_id", "")),
                recipient=email,
                subject=rendered_subject,
                body_html=rendered_html,
                body_text=rendered_text,
                status=status,
                error=result.get("error"),
                variables=variables,
                created_by=triggered_by,
            )

            return {
                "success": result.get("success", False),
                "channel": "email",
                "message_id": result.get("message_id"),
                "template_name": template.name,
                "recipient": email,
                "mock": result.get("mock", False),
                "ai_personalized": ai_personalized,
                "error": result.get("error"),
            }

    async def _load_candidate_data(self, vacancy_candidate_id: str) -> Optional[Dict[str, Any]]:
        """Load candidate and vacancy info for template variables."""
        try:
            vc_result = await self.db.execute(
                select(VacancyCandidate).where(
                    VacancyCandidate.id == vacancy_candidate_id
                )
            )
            vc = vc_result.scalars().first()
            if not vc:
                logger.warning(f"VacancyCandidate not found: {vacancy_candidate_id}")
                return None

            candidate_result = await self.db.execute(
                select(Candidate).where(Candidate.id == vc.candidate_id)
            )
            candidate = candidate_result.scalars().first()
            if not candidate:
                logger.warning(f"Candidate not found: {vc.candidate_id}")
                return None

            job_title = ""
            company_name = ""
            try:
                job_result = await self.db.execute(
                    select(JobVacancy).where(JobVacancy.id == vc.vacancy_id)
                )
                job = job_result.scalars().first()
                if job:
                    job_title = job.title or ""
                    company_name = job.company_id or ""
            except Exception as e:
                logger.warning(f"Could not load job vacancy data: {e}")

            email = (
                candidate.email
                or candidate.best_personal_email
                or candidate.best_business_email
            )

            return {
                "vacancy_candidate_id": str(vc.id),
                "vacancy_id": str(vc.vacancy_id),
                "candidate_id": str(candidate.id),
                "candidate_name": candidate.name or "",
                "email": email or "",
                "phone": candidate.phone or "",
                "mobile_phone": candidate.mobile_phone or "",
                "current_title": candidate.current_title or "",
                "current_company": candidate.current_company or "",
                "job_title": job_title,
                "company_name": company_name,
                "stage": vc.stage or "",
                "status": vc.status or "",
            }

        except Exception as e:
            logger.error(f"Error loading candidate data: {e}", exc_info=True)
            return None

    async def _find_template(
        self, situation: str, channel: str, company_id: Optional[str] = None
    ) -> Optional[EmailTemplate]:
        """Find best matching template. Priority: company-specific > system template."""
        try:
            if company_id:
                company_result = await self.db.execute(
                    select(EmailTemplate).where(
                        EmailTemplate.situation == situation,
                        EmailTemplate.channel == channel,
                        EmailTemplate.is_active == True,
                        EmailTemplate.company_id == company_id,
                    )
                )
                company_template = company_result.scalars().first()
                if company_template:
                    logger.info(
                        f"Found company-specific template: {company_template.name} "
                        f"(id={company_template.id})"
                    )
                    return company_template

            system_result = await self.db.execute(
                select(EmailTemplate).where(
                    EmailTemplate.situation == situation,
                    EmailTemplate.channel == channel,
                    EmailTemplate.is_active == True,
                    EmailTemplate.is_system_template == True,
                )
            )
            system_template = system_result.scalars().first()
            if system_template:
                logger.info(
                    f"Found system template: {system_template.name} (id={system_template.id})"
                )
                return system_template

            fallback_result = await self.db.execute(
                select(EmailTemplate).where(
                    EmailTemplate.situation == situation,
                    EmailTemplate.channel == channel,
                    EmailTemplate.is_active == True,
                )
            )
            fallback_template = fallback_result.scalars().first()
            if fallback_template:
                logger.info(
                    f"Found fallback template: {fallback_template.name} (id={fallback_template.id})"
                )
                return fallback_template

            logger.warning(
                f"No template found for situation='{situation}', channel='{channel}'"
            )
            return None

        except Exception as e:
            logger.error(f"Error finding template: {e}", exc_info=True)
            return None

    def _build_variables(
        self, candidate_data: Dict, extra_variables: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Build template variables dict from candidate/vacancy data."""
        variables: Dict[str, str] = {
            "candidate_name": candidate_data.get("candidate_name", ""),
            "job_title": candidate_data.get("job_title", ""),
            "company_name": candidate_data.get("company_name", ""),
            "candidate_email": candidate_data.get("email", ""),
            "candidate_phone": candidate_data.get("phone", ""),
            "current_title": candidate_data.get("current_title", ""),
            "current_company": candidate_data.get("current_company", ""),
            "stage": candidate_data.get("stage", ""),
            "date": datetime.utcnow().strftime("%d/%m/%Y"),
        }

        if extra_variables:
            for key, value in extra_variables.items():
                variables[str(key)] = str(value) if value is not None else ""

        return variables

    def _render_template(self, template_text: str, variables: Dict[str, str]) -> str:
        """Simple {{variable}} substitution."""
        if not template_text:
            return ""

        def replace_var(match):
            var_name = match.group(1).strip()
            return variables.get(var_name, match.group(0))

        return re.sub(r"\{\{(\s*\w+\s*)\}\}", replace_var, template_text)

    async def _log_dispatch(
        self,
        template_id,
        candidate_id: str,
        recipient: str,
        subject: str,
        body_html: str,
        body_text: str,
        status: str,
        error: Optional[str] = None,
        variables: Optional[Dict] = None,
        created_by: Optional[str] = None,
    ):
        """Create EmailLog record."""
        try:
            log_entry = EmailLog(
                id=uuid.uuid4(),
                template_id=template_id,
                candidate_id=candidate_id,
                recipient_email=recipient or "",
                subject=subject or "",
                body_html=body_html,
                body_text=body_text,
                status=status,
                sent_at=datetime.utcnow() if status == "sent" else None,
                error_message=error,
                variables_used=variables or {},
                created_by=created_by,
            )
            self.db.add(log_entry)
            await self.db.commit()
            logger.info(
                f"EmailLog created: id={log_entry.id}, status={status}, recipient={recipient}"
            )
        except Exception as e:
            logger.error(f"Failed to log dispatch: {e}", exc_info=True)
            try:
                await self.db.rollback()
            except Exception:
                pass
