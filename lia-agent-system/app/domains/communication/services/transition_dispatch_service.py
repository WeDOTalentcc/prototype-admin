"""
Transition Dispatch Service - Deterministic auto-dispatch for pipeline transitions.
Layer 1: Template-based message dispatch without AI interpretation.
"""
from app.middleware.request_id import get_correlation_id
import logging
import re
import uuid
from datetime import datetime
from typing import Any

from app.domains.communication.repositories.communication_matrix_repository import CommunicationMatrixRepository
from app.domains.communication.repositories.email_template_repository import EmailTemplateRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.models.communication_matrix import CommunicationMatrixEntry
from app.domains.communication.models.email_template import EmailLog, EmailTemplate
from app.domains.communication.services.communication_dispatcher import CommunicationDispatcher
from lia_models.candidate import Candidate, VacancyCandidate
from lia_models.job_vacancy import JobVacancy
from app.domains.candidates.services.candidate_channel_selector import CandidateChannelSelector

logger = logging.getLogger(__name__)

ACTION_BEHAVIOR_SITUATION_MAP: dict[str, str | None] = {
    "screening": "triagem",
    "scheduling": "agendamento",
    "evaluation": "avaliacao_tecnica",
    "verification": "avaliacao_tecnica",
    "offer": "proposta",
    "conclusion_rejected": "rejeicao",
    "conclusion_declined": "proposta_recusada",
    "conclusion_hired": "contratacao",
    "passive": "movimentacao",
    "intake": "entrada_candidato",
    "standby": "standby",
}

ACTION_BEHAVIOR_TRIGGER_MAP: dict[str, str | None] = {
    "screening": "triagem_aprovado",
    "scheduling": "entrevista_agendada",
    "evaluation": "avaliacao_enviada",
    "verification": "verificacao_solicitada",
    "offer": "proposta_gerada",
    "conclusion_rejected": "triagem_reprovado",
    "conclusion_declined": "proposta_recusada",
    "conclusion_hired": "contratacao_efetivada",
    "passive": "movimentacao",
    "intake": "entrada_candidato",
    "standby": "standby",
}

# Channels this service can dispatch (candidate-facing external channels only)
DISPATCHABLE_CHANNELS = {"email", "whatsapp", "sms"}


def ai_personalization_allowed_for_channel(channel: str) -> bool:
    """W1 (decisao Paulo 2026-06-10): texto livre gerado por IA so e permitido por
    EMAIL. WhatsApp business-initiated exige template aprovado pela Meta -> usa o
    template + variaveis, nunca texto livre da IA (senao a Meta nao entrega)."""
    return (channel or "").lower() == "email"


def is_feedback_fairness_blocked(text, company_id: str = "") -> bool:
    """Mantido p/ compat (dispatch + preview). Delega ao guard canonico de feedback
    (fairness L1 explicito + PII de documento). True = bloquear o texto da IA
    (cai no template seguro). Fail-soft no proprio guard."""
    from app.shared.compliance.feedback_guard import feedback_block_reason
    return feedback_block_reason(text, company_id or "") is not None
    try:
        from app.shared.compliance.fairness_guard_middleware import check_fairness
        result = check_fairness(
            texts={"feedback": str(text)},
            context="candidate_rejection_feedback",
            company_id=company_id or "",
        )
        return bool(result.is_blocked)
    except Exception as guard_err:
        logger.warning(
            "[DISPATCH] fairness guard do feedback falhou (fail-soft, nao bloqueia): %s",
            guard_err,
        )
        return False


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
        company_id: str | None = None,
        triggered_by: str | None = None,
        extra_variables: dict[str, Any] | None = None,
        personalized_content: str | None = None,
    ) -> dict[str, Any]:
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

            # Sprint B Phase 1+2 - learning loops outcome hook (fail-soft)
            if action_behavior == "conclusion_hired":
                try:
                    await self._hook_conclusion_hired(
                        vacancy_candidate_id=vacancy_candidate_id,
                        company_id=company_id,
                    )
                except Exception as _hook_exc:
                    logger.warning(
                        "[dispatch_for_transition] hook failed (non-blocking): %s",
                        str(_hook_exc)[:200],
                    )

            # T-10 Fase 3 WIRE canonical (ADR-032): REJECTED + WITHDRAWN outcomes
            # Fail-soft via helper canonical (wire_feedback_outcome nunca raises).
            # MVP wire — outras learning loops (BigFive negative signal, WSI rejection
            # patterns) ficam pra Fase 4 (P2 backlog).
            elif action_behavior in ("conclusion_rejected", "conclusion_declined"):
                try:
                    from app.shared.learning.feedback_writer import wire_feedback_outcome
                    from sqlalchemy import select as _select_t10f3
                    from lia_models.candidate import VacancyCandidate as _VC_t10f3

                    _outcome_map = {
                        "conclusion_rejected": "REJECTED",
                        "conclusion_declined": "WITHDRAWN",
                    }
                    _vc_result = await self.db.execute(
                        _select_t10f3(_VC_t10f3).where(_VC_t10f3.id == vacancy_candidate_id)
                    )
                    _vc = _vc_result.scalars().first()
                    if _vc is not None and getattr(_vc, "vacancy_id", None) and company_id:
                        await wire_feedback_outcome(
                            db=self.db,
                            domain="pipeline",
                            outcome_type=_outcome_map[action_behavior],
                            company_id=company_id,
                            job_id=str(_vc.vacancy_id),
                            context={
                                "vacancy_candidate_id": vacancy_candidate_id,
                                "action_behavior": action_behavior,
                                "wire_source": "transition_dispatch_service.dispatch_t10_fase3",
                            },
                        )
                except Exception as _wire_exc:
                    logger.warning(
                        "[dispatch_for_transition] T-10 Fase 3 wire failed (non-blocking): %s",
                        str(_wire_exc)[:200],
                    )

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
            # P0-W4-08: consent gate marketing — nao enviar se candidato revogou (LGPD Art. 7 §III + Art. 15)
            if candidate_id_str and company_id:
                try:
                    from app.domains.lgpd.services.granular_consent_consumers import check_marketing_granular
                    marketing_allowed = await check_marketing_granular(
                        candidate_id=candidate_id_str,
                        company_id=company_id,
                        db=self.db,
                    )
                    if not marketing_allowed:
                        logger.info(
                            "[ConsentGate] marketing bloqueado para candidato %s (company=%s)",
                            candidate_id_str, company_id,
                        )
                        return {
                            "success": False,
                            "channel": channel,
                            "message_id": None,
                            "template_name": None,
                            "recipient": candidate_data.get("email"),
                            "mock": False,
                            "error": "consent_revoked_marketing",
                            "consent_blocked": True,
                        }
                except Exception as _mce:
                    logger.warning(
                        "[ConsentGate] marketing check failed for %s (fail-closed): %s",
                        candidate_id_str, _mce,
                    )
                    return {
                        "success": False,
                        "channel": channel,
                        "message_id": None,
                        "template_name": None,
                        "recipient": candidate_data.get("email"),
                        "mock": False,
                        "error": "consent_check_failed",
                        "consent_blocked": True,
                    }
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
            channel_results: list[dict[str, Any]] = []
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
        self, trigger_name: str | None, company_id: str | None
    ) -> CommunicationMatrixEntry | None:
        """Query CommunicationMatrixEntry by trigger_name.
        Priority: company-specific → platform default (company_id IS NULL).
        """
        if not trigger_name:
            return None
        try:
            return await CommunicationMatrixRepository(self.db).get_by_trigger_name(
                trigger_name=trigger_name, company_id=company_id
            )
        except Exception as e:
            logger.warning(
                f"Error querying communication matrix for trigger '{trigger_name}': {e}"
            )
            return None

    async def _dispatch_single_channel(
        self,
        channel: str,
        situation: str,
        candidate_data: dict[str, Any],
        variables: dict[str, str],
        company_id: str | None,
        triggered_by: str | None,
        personalized_content: str | None,
    ) -> dict[str, Any]:
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
        if personalized_content and not ai_personalization_allowed_for_channel(channel):
            # WhatsApp (e demais canais nao-email): template Meta obrigatorio -> ignora
            # o texto livre da IA; o corpo do template aprovado + variaveis e usado.
            logger.info(
                "[DISPATCH] canal=%s: texto IA ignorado (template aprovado obrigatorio); IA so em email",
                channel,
            )
        elif personalized_content:
            if is_feedback_fairness_blocked(personalized_content, company_id or ""):
                # Texto da IA reprovado pela camada de fairness/LGPD -> NAO envia a
                # versao da IA; mantem o corpo do template seguro ja renderizado.
                logger.warning(
                    "[DISPATCH] feedback gerado por IA BLOQUEADO pela camada de fairness/LGPD "
                    "(candidate=%s) — usando template seguro",
                    candidate_data.get("candidate_id"),
                )
            else:
                rendered_html = personalized_content
                rendered_text = re.sub(r"<[^>]+>", "", personalized_content)
                ai_personalized = True
                logger.info("[DISPATCH] Using AI-personalized content instead of template")

        if channel == "whatsapp":
            phone = candidate_data.get("mobile_phone") or candidate_data.get("phone")
            if not phone:
                phone = await self._reveal_contact_for_dispatch(candidate_data, "phone", company_id)
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
                email = await self._reveal_contact_for_dispatch(candidate_data, "email", company_id)
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

            if not result.get("success"):
                phone = candidate_data.get("mobile_phone") or candidate_data.get("phone")
                if not phone:
                    phone = await self._reveal_contact_for_dispatch(
                        candidate_data, "phone", company_id,
                    )
                if phone:
                    logger.warning(
                        "[DISPATCH] Email failed for candidate %s (%s) \u2014 "
                        "attempting WhatsApp fallback to %s",
                        candidate_data.get("candidate_id"),
                        result.get("error", "unknown"),
                        phone,
                    )
                    plain_msg = re.sub(r"<[^>]+>", "", rendered_html) if rendered_html else rendered_text
                    wa_result = self.dispatcher.send_whatsapp(
                        to_phone=phone,
                        message=plain_msg,
                    )
                    wa_status = "sent" if wa_result.get("success") else "failed"
                    await self._log_dispatch(
                        template_id=template.id,
                        candidate_id=str(candidate_data.get("candidate_id", "")),
                        recipient=phone,
                        subject=rendered_subject,
                        body_html=rendered_html,
                        body_text=plain_msg,
                        status=wa_status,
                        error=wa_result.get("error"),
                        variables=variables,
                        created_by=triggered_by,
                    )
                    if wa_result.get("success"):
                        return {
                            "success": True,
                            "channel": "whatsapp",
                            "fallback_from": "email",
                            "original_email_error": result.get("error"),
                            "message_id": wa_result.get("message_id"),
                            "template_name": template.name,
                            "recipient": phone,
                            "mock": wa_result.get("mock", False),
                            "ai_personalized": ai_personalized,
                        }
                    logger.error(
                        "[DISPATCH] Both email and WhatsApp failed for candidate %s",
                        candidate_data.get("candidate_id"),
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

    async def _reveal_contact_for_dispatch(
        self, candidate_data: dict[str, Any], kind: str, company_id: str | None
    ) -> str | None:
        """Auto-reveal lazy no disparo (decisao Paulo): quando o canal precisa de
        email/telefone e o contato esta ausente, revela via Apify-first -> Pearch
        fallback e persiste. Falha graciosa: retorna None se nao conseguir, e o guard
        'sem contato' assume (registra erro, pula candidato). So gasta credito do
        contato de quem vai realmente receber.
        """
        candidate_id = candidate_data.get("candidate_id")
        if not candidate_id:
            return None
        try:
            from uuid import UUID as _UUID

            from app.domains.sourcing.services.contact_enrichment_service import (
                get_contact_enrichment_service,
            )

            svc = get_contact_enrichment_service()
            result = await svc.enrich_candidate_contact(
                db=self.db,
                candidate_id=_UUID(str(candidate_id)),
                company_id=company_id,
                force=False,
            )
            if not result or not result.get("success"):
                return None
            value = result.get("email") if kind == "email" else result.get("phone")
            if value:
                candidate_data[kind] = value
                logger.info(
                    "[TransitionDispatch] auto-reveal %s ok para candidate=%s",
                    kind, candidate_id,
                )
            return value
        except Exception as e:
            logger.warning(
                "[TransitionDispatch] auto-reveal %s falhou para candidate=%s: %s",
                kind, candidate_id, e,
            )
            return None

    async def _load_candidate_data(self, vacancy_candidate_id: str) -> dict[str, Any] | None:
        """Load candidate and vacancy info for template variables."""
        try:
            # ADR-001-EXEMPT: cross-domain VacancyCandidate single-PK read for
            # internal _load_candidate_data helper (no caller-side company_id).
            # Tenant boundary enforced downstream via vc.company_id filter on
            # Candidate and JobVacancy lookups. Postgres RLS (Task #1143) guards.
            vc_result = await self.db.execute(
                select(VacancyCandidate).where(
                    VacancyCandidate.id == vacancy_candidate_id
                )
            )
            vc = vc_result.scalars().first()
            if not vc:
                logger.warning(f"VacancyCandidate not found: {vacancy_candidate_id}")
                return None

            # Multi-tenancy fail-closed: scope Candidate to vc.company_id.
            candidate_result = await self.db.execute(
                select(Candidate).where(
                    Candidate.id == vc.candidate_id,
                    Candidate.company_id == vc.company_id,
                )
            )
            candidate = candidate_result.scalars().first()
            if not candidate:
                logger.warning(f"Candidate not found: {vc.candidate_id}")
                return None

            job_title = ""
            company_name = ""
            try:
                # Multi-tenancy fail-closed: scope JobVacancy to vc.company_id.
                job_result = await self.db.execute(
                    select(JobVacancy).where(
                        JobVacancy.id == vc.vacancy_id,
                        JobVacancy.company_id == vc.company_id,
                    )
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
        self, situation: str, channel: str, company_id: str | None = None
    ) -> EmailTemplate | None:
        """Find best matching template. Priority: company-specific > system template."""
        try:
            email_template_repo = EmailTemplateRepository(self.db)
            if company_id:
                company_template = await email_template_repo.find_active_by_situation_channel_company(
                    situation=situation, channel=channel, company_id=company_id
                )
                if company_template:
                    logger.info(
                        f"Found company-specific template: {company_template.name} "
                        f"(id={company_template.id})"
                    )
                    return company_template

            system_template = await email_template_repo.find_system_template(
                situation=situation, channel=channel
            )
            if system_template:
                logger.info(
                    f"Found system template: {system_template.name} (id={system_template.id})"
                )
                return system_template

            fallback_template = await email_template_repo.find_any_active_for_situation_channel(
                situation=situation, channel=channel
            )
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
        self, candidate_data: dict, extra_variables: dict | None = None
    ) -> dict[str, str]:
        """Build template variables dict from candidate/vacancy data."""
        variables: dict[str, str] = {
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

    def _render_template(self, template_text: str, variables: dict[str, str]) -> str:
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
        error: str | None = None,
        variables: dict | None = None,
        created_by: str | None = None,
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

    # -- Sprint B Phase 1+2 hooks (conclusion_hired learning loops) -------

    async def _hook_conclusion_hired(
        self,
        vacancy_candidate_id: str,
        company_id: str | None,
    ) -> None:
        """Sprint B: dispatch outcome events to learning-loop services.

        Phase 1: JdSimilarService.mark_filled (was_filled=True + time_to_fill_days)
        Phase 2: BigFive.record_hire — DEFERRED to Phase 2.5.
        Phase 3: WSI Effectiveness outcomes per skill_probed (record_question_outcome)

        ─── ADR-LGPD-001 (rev 2026-05-10, Phase 2.5 shipped) ───────────
        BigFiveDepartmentService.record_hire IS wired here as of Phase 2.5.
        Historical context preserved for traceability:

        1. DATA SOURCE (Phase 2.5 shipped): record_hire requires
           candidate_traits_snapshot — a dict with OCEAN keys (openness,
           conscientiousness, extraversion, agreeableness, stability) as
           floats 0-1. Phase 2.5 extended the WSI scoring pipeline to
           emit per-candidate OCEAN via:
             WSIQuestion.big_five_mapping
              -> ResponseAnalysis.trait_ocean (response_analyzer)
                -> WSIResult.ocean_traits (score_calculator aggregates
                   by trait, normalizes 1-5 -> 0-1)
                  -> LiaOpinion.behavioral_analysis['ocean_traits']
                     (persisted by handlers_screening)
           This hook (_record_bigfive_hire helper) reads the latest
           LiaOpinion for the candidate and forwards ocean_traits to
           record_hire. Missing/empty snapshot triggers graceful
           degradation (no record_hire call, no contamination).

           Pre-Phase-2.5 status (now resolved): WSI scoring emitted only
           {technicalScore, behavioralScore, gapAnalysisScore,
           contextualScore, totalWSI, decision} on interview.wsi_score
           JSON — no per-candidate OCEAN. Wiring record_hire with a
           fabricated snapshot would have contaminated
           bigfive_department_profiles with junk data.

        2. LGPD ART. 18 ANALYSIS — aggregate-not-PII argument:

           Legal hook: LGPD (Lei 13.709/2018) Art. 12 §1 places
           anonymized data outside the scope of LGPD protections when
           reversal back to the data subject would require "esforços
           razoáveis". Art. 18 erasure obligation therefore does NOT
           apply to data that has been anonymized in this strict sense.

           ANPD precedent: ANPD's Guia Orientativo "Tratamento de
           Dados Pessoais pelo Poder Público" (Aug/2022) and the
           "Guia de Anonimização" §3 ("teste de razoabilidade da
           irreversibilidade") establish that aggregate statistics
           computed via destructive transformations (running average
           with N >= a minimum threshold + decay) qualify as
           anonymized when individual contributions cannot be
           recovered with reasonable effort. See also Resolução
           CD/ANPD nº 2/2022 §3.II.

           Quantitative anchor (operational guard):
           bigfive_department_profiles store POPULATION-LEVEL
           aggregates via running average + temporal decay
           (lambda=0.05, threshold=540 days). At small N the
           aggregate is partially reversible if an attacker has
           side-channel signals — therefore the application enforces
           MIN_DEPT_SAMPLES = 10 in
           BigFiveDepartmentService.get_blend_weights (line 183),
           refusing to USE the profile for any decision when N < 10.
           The "esforços razoáveis" test of Art. 12 §1 holds only at
           N >= 10 with the active gate; never below.

           Cross-reference EU AI Act Art. 10(5): special-category
           processing without individual data subjects is permitted
           where "absolutely necessary for the purpose of bias
           detection and correction". The dept profile is used for
           bias-aware question generation — within the article's scope.

           Conclusion: when a candidate's PII is erased via
           lgpd_cleanup_service, NO recompute of
           bigfive_department_profiles is required. The aggregate
           remains valid because (a) it is irreversible per ANPD
           §3 test at N >= 10 and (b) the MIN_DEPT_SAMPLES gate
           ensures profiles below the threshold are never queried.

           Sentinel guard: tests/unit/test_p0_3_min_samples_gate.py
           refuses regression below MIN_DEPT_SAMPLES=10, removal of
           the get_blend_weights gate, OR a docstring that loses the
           ANPD/Art.12/MIN_DEPT_SAMPLES references.

           If a future ANPD opinion or court interpretation diverges
           from this analysis, add a recompute hook here using the
           surviving sample population (post-erasure recompute path
           is intentionally absent today).

           Decision history: Sprint B Phase 3 audit, decisão D1=B
           (Paulo 2026-05-10). Hardened post-audit 2026-05-10
           with ANPD/Art. 12 §1/EU AI Act Art. 10(5) citations and
           the MIN_DEPT_SAMPLES quantitative anchor. Phase 2.5
           shipped 2026-05-10 closing the data-source prerequisite;
           record_hire reads from
           LiaOpinion.behavioral_analysis['ocean_traits'] via the
           _record_bigfive_hire helper below.

        Sentinel: tests/unit/test_bigfive_phase3_governance.py asserts
        record_hire is not called from this hook and that this
        ADR-LGPD-001 reference remains in the docstring. If the
        sentinel fails, either land Phase 2.5 properly or update the
        ADR.
        ──────────────────────────────────────────────────────────────────

        ALWAYS fail-soft — dispatch never blocks if learning loops are
        unavailable.

        Multi-tenancy: company_id required from caller (JWT context).
        """
        if not company_id or not vacancy_candidate_id:
            return
        try:
            from datetime import datetime
            from sqlalchemy import select as _select
            # Boy-scout (Phase 2.5): VacancyCandidate canonical lives in
            # lia_models.candidate (top-of-file already imports both
            # Candidate and VacancyCandidate from there). The previous
            # `from lia_models.vacancy_candidate import` was a stale path
            # that crashed at import time and got swallowed by the outer
            # try/except, masking the entire hook silently.
            from lia_models.candidate import VacancyCandidate
            from lia_models.job_vacancy import JobVacancy
            from app.domains.job_creation.repositories.jd_similar_history_repository import (
                JdSimilarHistoryRepository,
            )
            from app.domains.job_creation.services.jd_similar_service import (
                JdSimilarService,
            )
            from app.shared.intelligence.embedding_service import EmbeddingService

            # 1) Lookup vacancy_id from vacancy_candidate_id
            vc_result = await self.db.execute(
                _select(VacancyCandidate).where(
                    VacancyCandidate.id == vacancy_candidate_id,
                )
            )
            vc = vc_result.scalars().first()
            if not vc:
                logger.debug(
                    "[ConclusionHired hook] vc not found id=%s",
                    vacancy_candidate_id,
                )
                return
            job_id = str(vc.vacancy_id)

            # 2) Lookup JobVacancy para time_to_fill calculation
            job_result = await self.db.execute(
                _select(JobVacancy).where(JobVacancy.id == vc.vacancy_id)
            )
            job = job_result.scalars().first()
            time_to_fill_days = 0
            if job is not None and job.created_at is not None:
                time_to_fill_days = max(0, (datetime.utcnow() - job.created_at).days)

            # 3) Fire mark_filled (fail-soft if no record exists in jd_similar_history)
            repo = JdSimilarHistoryRepository(self.db)
            svc = JdSimilarService(repository=repo, embedding_service=EmbeddingService())
            await svc.mark_filled(
                company_id=company_id,
                job_id=job_id,
                time_to_fill_days=time_to_fill_days,
                candidates_count=0,  # filled via batch reconciliation (Phase 1.5)
            )
            logger.info(
                "[ConclusionHired hook] mark_filled job_id=%s ttf=%dd",
                job_id, time_to_fill_days,
            )
            # Audit log: outcome event for learning loop
            try:
                from app.shared.compliance.audit_service import get_audit_service
                import uuid as _uuid
                await get_audit_service().log_action(
                    trace_id=get_correlation_id(),
                    company_id=company_id,
                    action_type="jd_similar_mark_filled",
                    actor="hook:conclusion_hired",
                    target_id=job_id,
                    target_type="job",
                    metadata={
                        "time_to_fill_days": time_to_fill_days,
                        "vacancy_candidate_id": vacancy_candidate_id,
                    },
                )
            except Exception as _audit_exc:
                logger.warning(
                    "[ConclusionHired] audit log failed: %s",
                    str(_audit_exc)[:100],
                )

            # Sprint B Phase 3 - WSI Effectiveness outcome (per skill_probed)
            try:
                await self._record_wsi_outcomes_for_candidate(
                    company_id=company_id,
                    vacancy_candidate_id=vacancy_candidate_id,
                    job_id=job_id,
                    outcome="hired",
                )
            except Exception as _wsi_exc:
                logger.warning(
                    "[ConclusionHired] WSI outcome hook failed: %s",
                    str(_wsi_exc)[:100],
                )

            # Sprint B Phase 4 (gap C3): push BiasAuditSnapshot per hire so
            # the EU AI Act trail is event-driven instead of relying on
            # admin-pull. Fail-soft so a bias-audit failure cannot block
            # the conclusion_hired dispatch.
            await self._push_bias_snapshot(
                company_id=company_id, job_id=job_id,
            )

            # Phase 2.5 (closes ADR-LGPD-001 deferral): now that the WSI
            # scoring pipeline emits per-candidate OCEAN traits and
            # _process_screening_completed persists them in
            # LiaOpinion.behavioral_analysis['ocean_traits'], we can
            # finally record this hire in bigfive_department_profiles.
            # Fail-soft: missing snapshot is fine (degrades graceful).
            await self._record_bigfive_hire(
                company_id=company_id,
                vacancy_candidate=vc,
                job=job,
            )

            # T-10 Fase 2 WIRE canonical (ADR-032 feedback_learning_service.record_outcome).
            # Fail-soft via helper canonical (wire_feedback_outcome nunca raises).
            # Alimenta JobOutcome table + InteractionFeedback mirror (T-10 Fase 1 wire).
            try:
                from app.shared.learning.feedback_writer import wire_feedback_outcome
                await wire_feedback_outcome(
                    db=self.db,
                    domain="pipeline",
                    outcome_type="HIRED",
                    company_id=company_id or "",
                    job_id=job_id,
                    time_to_fill_days=time_to_fill_days,
                    context={
                        "vacancy_candidate_id": vacancy_candidate_id,
                        "wire_source": "transition_dispatch_service._hook_conclusion_hired",
                    },
                )
            except Exception as _wire_exc:
                logger.warning(
                    "[ConclusionHired hook] wire_feedback_outcome failed (non-blocking): %s",
                    str(_wire_exc)[:200],
                )
        except Exception as exc:
            logger.warning(
                "[ConclusionHired hook] failed (non-blocking): %s",
                str(exc)[:200],
            )

    async def _record_bigfive_hire(
        self,
        *,
        company_id: str,
        vacancy_candidate,
        job,
    ) -> None:
        """Phase 2.5: read latest LiaOpinion for the hired candidate, extract
        OCEAN traits snapshot, and call BigFiveDepartmentService.record_hire.

        Fail-soft: never raises. If LiaOpinion is missing or has no
        ocean_traits, skip silently — record_hire with empty/junk
        snapshot would contaminate the dept aggregate (ADR-LGPD-001
        fail-safe). The MIN_DEPT_SAMPLES gate downstream further
        protects against premature use of small-N profiles.

        Args:
          company_id: tenant from JWT context.
          vacancy_candidate: the VC row (carries candidate_id, vacancy_id).
          job: the JobVacancy row (carries department, seniority_level).
        """
        if not company_id or vacancy_candidate is None:
            return
        candidate_id = getattr(vacancy_candidate, "candidate_id", None)
        if not candidate_id:
            return
        try:
            from app.repositories.opinions_repository import (
                OpinionsRepository,
            )
            from app.domains.job_creation.services.bigfive_service import (
                BigFiveDepartmentService,
            )

            # P1-LiaRepo: delegate to OpinionsRepository (ADR-001 — no
            # inline select in services). multi-tenancy: company_id from
            # caller, never from payload.
            opinion = await OpinionsRepository(self.db).get_latest_for_candidate_company(
                candidate_id=candidate_id,
                company_id=str(company_id),
            )
            if opinion is None:
                logger.debug(
                    "[ConclusionHired] no LiaOpinion for candidate=%s — "
                    "skip BigFive record_hire",
                    candidate_id,
                )
                return

            behavioral_analysis = getattr(opinion, "behavioral_analysis", None) or {}
            ocean_traits = behavioral_analysis.get("ocean_traits") or {}
            if not ocean_traits:
                logger.debug(
                    "[ConclusionHired] LiaOpinion has no ocean_traits — "
                    "skip BigFive record_hire (Phase 2.5 graceful degrade)"
                )
                return

            department = getattr(job, "department", None) if job is not None else None
            seniority_level = (
                getattr(job, "seniority_level", None) if job is not None else None
            )
            if not department or not seniority_level:
                logger.debug(
                    "[ConclusionHired] job missing department/seniority — "
                    "skip BigFive record_hire"
                )
                return

            svc = BigFiveDepartmentService(self.db)
            await svc.record_hire(
                company_id=str(company_id),
                department=str(department),
                seniority_level=str(seniority_level),
                candidate_traits_snapshot=dict(ocean_traits),
            )
            logger.info(
                "[ConclusionHired] BigFive record_hire OK candidate=%s "
                "dept=%s seniority=%s traits=%s",
                candidate_id, department, seniority_level,
                sorted(ocean_traits.keys()),
            )
        except Exception as exc:
            logger.warning(
                "[ConclusionHired] record_bigfive_hire failed (fail-soft): %s",
                str(exc)[:200],
            )

    async def _push_bias_snapshot(self, *, company_id: str, job_id: str) -> None:
        """Sprint B Phase 4 (C3): push a BiasAuditSnapshot for `job_id`.

        Generates a fresh adverse-impact report and persists it via
        BiasAuditService.save_snapshot. Fail-soft: any error is logged
        and swallowed — bias-audit observability never blocks the hire
        dispatch flow.

        Multi-tenancy: company_id from the caller's JWT context (NOT
        from any payload).

        P1-2 (post-audit): BiasAuditService is marked RAILS-DEPRECATED
        at module level (UC-P1-22 in CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md).
        However: bias-audit is statistical computation over RubricEvaluation
        and Candidate JOIN, not Rails-owned CRUD. There is no
        rails_adapter equivalent today — the deprecation is preventive,
        not migratable. We suppress the import-time DeprecationWarning at
        this single canonical caller so production logs stay clean. When
        a Rails-side bias-audit endpoint exists, swap this call for the
        rails_adapter equivalent and remove the suppression.
        """
        if not company_id or not job_id:
            return
        try:
            import warnings as _warnings
            from uuid import UUID as _UUID
            with _warnings.catch_warnings():
                _warnings.simplefilter("ignore", DeprecationWarning)
                from app.shared.services.bias_audit_service import BiasAuditService

            svc = BiasAuditService()
            try:
                _company_uuid = _UUID(str(company_id))
            except (TypeError, ValueError):
                logger.debug(
                    "[ConclusionHired] bias snapshot skipped — company_id "
                    "is not a UUID (got %r)",
                    company_id,
                )
                return

            # P0-2 (audit fix): pass company_id=None to suppress the
            # internal save_snapshot side-effect inside
            # get_adverse_impact_by_job (see bias_audit_service.py:386-393).
            # We then save explicitly below — exactly one row per hire.
            try:
                _job_uuid = _UUID(str(job_id))
            except (TypeError, ValueError):
                logger.debug(
                    "[ConclusionHired] bias snapshot skipped — job_id is not "
                    "a UUID (got %r)",
                    job_id,
                )
                return
            report = await svc.get_adverse_impact_by_job(
                db=self.db, job_id=_job_uuid, company_id=None,
            )
            if report is None:
                logger.debug(
                    "[ConclusionHired] bias snapshot skipped — no report for job=%s",
                    job_id,
                )
                return
            await svc.save_snapshot(
                db=self.db, company_id=_company_uuid, report=report,
            )
            logger.info(
                "[ConclusionHired] bias snapshot pushed job=%s alerts=%s",
                job_id, getattr(report, "has_alerts", "?"),
            )
        except Exception as snap_exc:
            logger.warning(
                "[ConclusionHired] bias snapshot failed (fail-soft) job=%s: %s",
                job_id, str(snap_exc)[:200],
            )

    async def _load_learning_loops_toggles(self, company_id: str) -> dict:
        """Carrega toggles learning_loops do CompanyHiringPolicy.

        Thin wrapper sobre o helper canonical em
        ``app.shared.services.learning_loops_toggles`` (single source of
        truth desde 2026-05-21). Mantemos esta wrapper instance method
        por compatibility com testes existentes que mockam
        ``TransitionDispatchService._load_learning_loops_toggles``.
        Novo código DEVE chamar ``load_learning_loops_toggles(...)``
        direto do shared module.
        """
        from app.shared.services.learning_loops_toggles import (
            load_learning_loops_toggles,
        )
        return await load_learning_loops_toggles(company_id, self.db)

    async def _record_wsi_outcomes_for_candidate(
        self,
        company_id: str,
        vacancy_candidate_id: str,
        job_id: str,
        outcome: str,
    ) -> None:
        """Sprint B Phase 3 - registra outcome por skill_probed nas respostas WSI.

        Lookup respostas WSI do candidato + para cada uma com skill_probed
        populado, chama WsiEffectivenessService.record_question_outcome.

        Multi-tenancy: company_id obrigatorio.
        Fail-soft: erro nao bloqueia dispatch.

        P1-4 gate (audit 2026-05-21): respeita o toggle
        ``learning_loops.wsi_question_effectiveness`` antes de escrever no
        write path. Default canonical do toggle é ``False`` (Phase 3 opt-in),
        portanto sem gate o write rodava mesmo quando o recrutador NUNCA
        optou em registrar. Risco LGPD direto: skill_probed + outcome por
        candidato hired/rejected é tracking comportamental que requer base
        legal explícita. Gate no início do método garante fail-closed
        para qualquer caller (atual ou futuro). Audit log marca o evento
        de skip para rastreabilidade.
        """
        if not company_id or not vacancy_candidate_id:
            return
        toggles = await self._load_learning_loops_toggles(company_id)
        master_on = toggles.get("enabled")
        wsi_on = toggles.get("wsi_question_effectiveness")
        if not master_on or not wsi_on:
            logger.info(
                "[ConclusionHired] WSI effectiveness write SKIPPED — "
                "master_learning_loops=%s wsi_question_effectiveness=%s "
                "company_id=%s vc=%s",
                master_on, wsi_on, company_id, vacancy_candidate_id,
            )
            # Audit trail: record that the gate intervened. This is what
            # allows compliance/SRE to prove later that the system honored
            # the toggle when asked by a tenant (LGPD Art. 18 access request).
            try:
                from app.shared.compliance.audit_service import get_audit_service
                import uuid as _uuid
                await get_audit_service().log_action(
                    trace_id=get_correlation_id(),
                    company_id=company_id,
                    action_type="wsi_effectiveness_write_gated",
                    actor="hook:conclusion_hired",
                    target_id=vacancy_candidate_id,
                    target_type="vacancy_candidate",
                    metadata={
                        "master_learning_loops": master_on,
                        "wsi_question_effectiveness": wsi_on,
                        "outcome": outcome,
                        "job_id": job_id,
                    },
                )
            except Exception as _audit_exc:
                logger.debug(
                    "[ConclusionHired] audit log of gate skip failed: %s",
                    str(_audit_exc)[:100],
                )
            return
        try:
            # Lookup WSI responses do candidato — depende do schema atual.
            # Por ora, structure simplificada: se existe wsi_responses table
            # com {vacancy_candidate_id, skill_probed, score}, iterar.
            from sqlalchemy import select as _select
            try:
                from lia_models.wsi_response import WsiResponse  # type: ignore
            except ImportError:
                logger.debug(
                    "[ConclusionHired] WsiResponse model not available - skip Phase 3 outcome",
                )
                return

            # ADR-001-EXEMPT: cross-domain WsiResponse read; voice/wsi domain repo is
            # frozen for this sprint (other agent territory). Sprint 6 follow-up.
            stmt = _select(WsiResponse).where(
                WsiResponse.vacancy_candidate_id == vacancy_candidate_id,
            )
            result = await self.db.execute(stmt)
            responses = list(result.scalars().all())
            if not responses:
                logger.debug(
                    "[ConclusionHired] no WSI responses for vc=%s",
                    vacancy_candidate_id,
                )
                return

            from app.domains.job_creation.services.wsi_effectiveness_service import (
                WsiEffectivenessService,
            )
            svc = WsiEffectivenessService(self.db)

            recorded_count = 0
            for response in responses:
                skill_probed = getattr(response, "skill_probed", None)
                score = getattr(response, "score", None)
                if not skill_probed or score is None:
                    continue
                try:
                    await svc.record_question_outcome(
                        company_id=company_id,
                        skill_probed=skill_probed,
                        outcome=outcome,
                        score=float(score),
                        department=getattr(response, "department", "") or "",
                        seniority_level=getattr(response, "seniority_level", "") or "",
                    )
                    recorded_count += 1
                except Exception as _per_resp_exc:
                    logger.debug(
                        "[ConclusionHired] WSI per-response failed: %s",
                        str(_per_resp_exc)[:100],
                    )

            logger.info(
                "[ConclusionHired] Phase3 outcomes recorded: %d/%d job_id=%s",
                recorded_count, len(responses), job_id,
            )
        except Exception as exc:
            logger.warning(
                "[ConclusionHired] Phase3 lookup failed (fail-soft): %s",
                str(exc)[:200],
            )

