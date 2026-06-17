"""Communication ReAct Agent — Tool Registry.

Wraps CommunicationService, EmailService, TeamsService, WhatsAppService and
CommunicationHistoryService into ToolDefinition format so the ReActLoop can
autonomously decide which tools to call.
"""

import logging
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool wrappers
# ---------------------------------------------------------------------------


@tool_handler("communication")
async def _wrap_send_email(**kwargs: Any) -> dict[str, Any]:
    """Send an email to a candidate using EmailService / CommunicationService."""
    from app.core.database import AsyncSessionLocal
    from app.domains.communication.services.communication_service import (
        CommunicationService,
        MessageChannel,
        MessageType,
    )

    candidate_id = kwargs.get("candidate_id")
    company_id = kwargs.get("company_id")
    subject = kwargs.get("subject")
    body = kwargs.get("body")
    template_type = kwargs.get("template_type")

    if not candidate_id:
        return {"success": False, "message": "candidate_id é obrigatório"}
    if not subject:
        return {"success": False, "message": "subject é obrigatório"}
    if not body:
        return {"success": False, "message": "body é obrigatório"}

    svc = CommunicationService()

    # Derive message_type from template_type when supplied
    try:
        msg_type = MessageType(template_type) if template_type else MessageType.GENERAL
    except ValueError:
        msg_type = MessageType.GENERAL

    try:
        async with AsyncSessionLocal() as db:
            result = await svc.send_message(
                company_id=str(company_id),
                candidate_id=str(candidate_id),
                candidate_email=None,  # resolved by service from candidate record
                candidate_phone=None,
                message_type=msg_type,
                channel=MessageChannel.EMAIL,
                subject=subject,
                body=body,
                db=db,
            )

        return {
            "success": result.get("success", True),
            "message_id": result.get("message_id"),
            "channel": "email",
            "candidate_id": candidate_id,
            "company_id": company_id,
            "details": result,
        }
    except Exception as exc:
        logger.error("[communication_tools] send_email failed: %s", exc, exc_info=True)
        # Self-correction: check if candidate has phone for WhatsApp fallback
        alternative_channel = None
        try:
            async with AsyncSessionLocal() as _db:
                from sqlalchemy import text as _txt

                _row = await _db.execute(
                    _txt("SELECT phone FROM candidates WHERE id = :cid LIMIT 1"),
                    {"cid": str(candidate_id)},
                )
                if _row.scalar_one_or_none():
                    alternative_channel = "whatsapp"
        except Exception:
            pass

        alt_msg = " O candidato tem telefone — posso tentar por WhatsApp." if alternative_channel else ""
        return {
            "success": False,
            "message": f"Falha ao enviar email (servico indisponivel ou endereco invalido).{alt_msg}",
            "error_type": "integration_error",
            "candidate_id": candidate_id,
            "alternative_channel": alternative_channel,
        }


@tool_handler("communication")
async def _wrap_send_whatsapp(**kwargs: Any) -> dict[str, Any]:
    """Send a WhatsApp message to a candidate using WhatsAppService."""
    from app.domains.communication.services.whatsapp_service import WhatsAppService

    candidate_phone = kwargs.get("candidate_phone")
    message = kwargs.get("message")
    company_id = kwargs.get("company_id")
    candidate_id = kwargs.get("candidate_id")

    if not candidate_phone:
        return {"success": False, "message": "candidate_phone é obrigatório"}
    if not message:
        return {"success": False, "message": "message é obrigatório"}
    try:
        svc = WhatsAppService()
        result = await svc.send_message(
            to_phone=candidate_phone,
            message=message,
            metadata={
                "company_id": str(company_id),
                "candidate_id": str(candidate_id) if candidate_id else None,
            },
        )
        return {
            "success": result.success,
            "message_id": result.message_id,
            "status": result.status.value if result.status else None,
            "channel": "whatsapp",
            "candidate_phone": candidate_phone,
            "company_id": company_id,
        }
    except Exception as exc:
        logger.error("[communication_tools] send_whatsapp failed: %s", exc, exc_info=True)
        return {
            "success": False,
            "message": "Falha ao enviar WhatsApp: servico indisponivel. Verifique configuracao Twilio.",
            "error_type": "integration_error",
            "candidate_phone": candidate_phone,
        }


@tool_handler("communication")
async def _wrap_get_communication_history(**kwargs: Any) -> dict[str, Any]:
    """Retrieve communication history for a candidate using CommunicationHistoryService."""
    from app.domains.communication.services.communication_history_service import (
        CommunicationHistoryService,
    )

    candidate_id = kwargs.get("candidate_id")
    company_id = kwargs.get("company_id")
    limit = int(kwargs.get("limit", 10))

    if not candidate_id:
        return {"success": False, "message": "candidate_id é obrigatório"}
    svc = CommunicationHistoryService()
    result = await svc.list_communications(
        company_id=str(company_id),
        candidate_id=str(candidate_id),
        limit=limit,
    )
    return {
        "success": True,
        "candidate_id": candidate_id,
        "company_id": company_id,
        "total": result.get("total", 0),
        "communications": result.get("communications", []),
    }


@tool_handler("communication")
async def _wrap_schedule_message(**kwargs: Any) -> dict[str, Any]:
    """Schedule a future message for a candidate using CommunicationService.

    For email and whatsapp channels the message is routed through CommunicationService.
    Teams notifications are dispatched via TeamsService (webhook-based; scheduling is
    recorded locally since Teams does not support native delayed delivery).
    """
    from datetime import datetime

    from app.core.database import AsyncSessionLocal
    from app.domains.communication.services.communication_service import (
        CommunicationService,
        MessageChannel,
        MessageType,
    )

    candidate_id = kwargs.get("candidate_id")
    company_id = kwargs.get("company_id")
    channel_str = kwargs.get("channel", "email")
    message = kwargs.get("message")
    scheduled_at_str = kwargs.get("scheduled_at")

    if not candidate_id:
        return {"success": False, "message": "candidate_id é obrigatório"}
    if not message:
        return {"success": False, "message": "message é obrigatório"}
    if not scheduled_at_str:
        return {"success": False, "message": "scheduled_at é obrigatório (ISO datetime)"}

    # Validate channel
    channel_normalized = channel_str.lower()
    if channel_normalized not in ("email", "whatsapp", "teams"):
        return {
            "success": False,
            "message": f"Canal inválido '{channel_str}'. Use: email, whatsapp, teams",
        }

    try:
        datetime.fromisoformat(scheduled_at_str)
    except ValueError as e:
        return {"success": False, "message": f"scheduled_at inválido: {e}"}

    if channel_normalized == "teams":
        # Teams is webhook-based; record intent and notify via TeamsService.
        # Resolve per-tenant webhook URL so DB-configured URL drives delivery.
        from app.domains.communication.services.teams_service import (
            TeamsService,
            resolve_tenant_teams_webhook_url,
        )

        _teams_url: str | None = None
        if company_id:
            try:
                from app.core.database import AsyncSessionLocal as _ASL
                async with _ASL() as _db:
                    _teams_url, _ = await resolve_tenant_teams_webhook_url(str(company_id), _db)
            except Exception as _url_err:
                import logging as _log
                _log.getLogger(__name__).debug(
                    "schedule_message: could not resolve per-tenant Teams URL: %s", _url_err
                )

        svc_teams = TeamsService(webhook_url=_teams_url)
        await svc_teams.send_message(
            text=(f"[Agendado para {scheduled_at_str}] " f"Mensagem para candidato {candidate_id}: {message}"),
            webhook_url=_teams_url,
        )
        return {
            "success": True,
            "scheduled": True,
            "channel": "teams",
            "scheduled_at": scheduled_at_str,
            "candidate_id": candidate_id,
            "company_id": company_id,
            "note": "Teams não suporta envio nativo agendado; notificação imediata registrada.",
        }

    # MessageChannel only defines EMAIL; WhatsApp uses its own service
    channel_map = {
        "email": MessageChannel.EMAIL,
    }
    channel = channel_map.get(channel_normalized, MessageChannel.EMAIL)

    svc = CommunicationService()
    async with AsyncSessionLocal() as db:
        result = await svc.send_message(
            company_id=str(company_id),
            candidate_id=str(candidate_id),
            candidate_email=None,
            candidate_phone=None,
            message_type=MessageType.GENERAL,
            channel=channel,
            subject=None,
            body=message,
            db=db,
        )

    return {
        "success": True,
        "scheduled": True,
        "channel": channel_str,
        "scheduled_at": scheduled_at_str,
        "candidate_id": candidate_id,
        "company_id": company_id,
        "details": result,
    }


@tool_handler("communication")
async def _wrap_check_rate_limit(**kwargs: Any) -> dict[str, Any]:
    """Check the current rate limit status for a candidate/channel combination."""
    from app.core.database import AsyncSessionLocal
    from app.domains.communication.services.communication_service import (
        CommunicationService,
        MessageChannel,
        MessageType,
    )

    candidate_id = kwargs.get("candidate_id")
    company_id = kwargs.get("company_id")
    channel_str = kwargs.get("channel", "email")

    if not candidate_id:
        return {"success": False, "message": "candidate_id é obrigatório"}
    # Teams channel is not tracked in CommunicationService; validate via email proxy
    # MessageChannel only defines EMAIL; WhatsApp/Teams use email policy as proxy for rate-limit checks
    channel_map = {
        "email": MessageChannel.EMAIL,
        "whatsapp": MessageChannel.EMAIL,
        "teams": MessageChannel.EMAIL,
    }
    channel = channel_map.get(channel_str.lower())
    if not channel:
        return {
            "success": False,
            "message": f"Canal inválido '{channel_str}'. Use: email, whatsapp, teams",
        }

    try:
        svc = CommunicationService()
        async with AsyncSessionLocal() as db:
            validation = await svc.validate_can_send(
                candidate_id=str(candidate_id),
                company_id=str(company_id),
                channel=channel,
                message_type=MessageType.GENERAL,
                db=db,
            )

        return {
            "success": True,
            "can_send": validation.get("can_send", False),
            "requires_approval": validation.get("requires_approval", False),
            "warnings": validation.get("warnings", []),
            "blocks": validation.get("blocks", []),
            "candidate_id": candidate_id,
            "company_id": company_id,
            "channel": channel_str,
        }
    except Exception as exc:
        logger.error("[communication_tools] check_rate_limit failed: %s", exc, exc_info=True)
        return {
            "success": False,
            "can_send": False,
            "message": "Falha ao verificar rate limit. Por seguranca, envio bloqueado ate verificacao.",
            "error_type": "integration_error",
            "candidate_id": candidate_id,
        }


# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------


@tool_handler("communication")
async def _wrap_suggest_communication_policy(**kwargs):
    """
    Sugere politica canonical de comunicacao (horarios + canais) baseado no
    publico (recrutador|candidato) e evento.

    Audit 2026-05-20 Sessao I / Tema B: Settings > Comunicacao&Alertas hoje
    tem DEFAULT_ALERTS hardcoded (5 alertas) sem CRUD. Esta tool retorna
    sugestao canonical pra LIA propor ao admin via chat.

    Multi-tenancy: company_id obrigatorio via ContextVar JWT.
    """
    company_id = kwargs.get("company_id")
    audience = (kwargs.get("audience") or "candidato").strip().lower()
    event_type = (kwargs.get("event_type") or "geral").strip().lower()

    LGPD_BUSINESS_HOURS = {"start": "09:00", "end": "18:00", "tz": "America/Sao_Paulo", "days": ["mon","tue","wed","thu","fri"]}

    POLICIES = {
        ("candidato", "geral"): {
            "channels": ["email", "whatsapp"],
            "schedule": LGPD_BUSINESS_HOURS,
            "alert_rules": [
                {"trigger": "stage_change", "channel": "email", "delay_minutes": 0},
                {"trigger": "interview_24h_before", "channel": "whatsapp", "delay_minutes": 0},
            ],
        },
        ("candidato", "rejeicao"): {
            "channels": ["email"],
            "schedule": LGPD_BUSINESS_HOURS,
            "alert_rules": [
                {"trigger": "rejection", "channel": "email", "delay_minutes": 60, "rationale": "Delay 60min canonical pra revisao humana opcional."},
            ],
        },
        ("recrutador", "geral"): {
            "channels": ["email", "in_app"],
            "schedule": None,
            "alert_rules": [
                {"trigger": "new_candidate_match", "channel": "in_app"},
                {"trigger": "sla_breach", "channel": "email"},
            ],
        },
    }
    key = (audience, event_type)
    policy = POLICIES.get(key) or POLICIES.get((audience, "geral")) or POLICIES[("candidato", "geral")]

    return {
        "success": True,
        "data": {
            "policy": policy,
            "audience": audience,
            "event_type": event_type,
            "lgpd_compliant": audience == "candidato",
        },
        "message": f"Politica de comunicacao sugerida para {audience}/{event_type} (LGPD-compliant).",
    }



@tool_handler("communication")
async def _wrap_suggest_alert_rule_templates(**kwargs):
    """
    Sugere alert rule templates canonical ranked por relevancia.

    Audit 2026-05-20 Sprint 3 F5: substitui DEFAULT_ALERTS hardcoded
    (5 items) por catalogo dinamico per-tenant (AlertRuleTemplate).

    kwargs:
        company_id (str, obrigatorio via ContextVar JWT)
        audience (str, opcional): recruiter | admin | candidate
        event_type (str, opcional): chave canonical do evento (filtro)

    Returns: top 10 ranked por relevancia (audience match + event_type
    match + master priority).
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.communication.repositories.alert_rule_template_repository import (
        AlertRuleTemplateRepository,
    )

    company_id = kwargs.get("company_id")
    audience_filter = (kwargs.get("audience") or "").strip().lower() or None
    event_type_filter = (kwargs.get("event_type") or "").strip().lower() or None

    async with AsyncSessionLocal() as db:
        repo = AlertRuleTemplateRepository(db)
        all_items = await repo.list_for_company(
            company_id=company_id, include_master=True
        )

    suggestions = []
    for item in all_items:
        data = item.data or {}
        score = 0
        item_audience = (data.get("audience") or "").lower()
        item_event_type = (data.get("event_type") or "").lower()

        # Audience match: +5
        if audience_filter and item_audience == audience_filter:
            score += 5
        elif not audience_filter:
            # Sem filtro: dar peso default por audience canonical (recruiter mais comum)
            if item_audience == "recruiter":
                score += 2
            elif item_audience == "candidate":
                score += 1

        # Event type match: +6 (mais especifico que audience)
        if event_type_filter and item_event_type == event_type_filter:
            score += 6

        # Master template: +1 (curated by WeDOTalent)
        if item.is_master_template:
            score += 1

        # Schedule LGPD compliant: +1 (preferimos canonical compliant)
        if data.get("schedule_lgpd_compliant", False):
            score += 1

        # Enabled by default: +1
        if data.get("enabled_default", True):
            score += 1

        if score > 0:
            suggestions.append({
                "id": str(item.id),
                "event_type": data.get("event_type", ""),
                "label": data.get("label", ""),
                "audience": item_audience,
                "channels": data.get("channels", []),
                "delay_minutes": data.get("delay_minutes", 0),
                "schedule_lgpd_compliant": data.get("schedule_lgpd_compliant", False),
                "is_master": item.is_master_template,
                "rationale": data.get("rationale"),
                "score": score,
            })

    suggestions.sort(key=lambda s: s["score"], reverse=True)
    top = suggestions[:10]

    return {
        "success": True,
        "data": {
            "suggestions": top,
            "total_in_catalog": len(all_items),
            "audience_filter": audience_filter,
            "event_type_filter": event_type_filter,
        },
        "message": (
            f"{len(top)} alert rule template(s) sugerido(s) "
            f"(top 10 de {len(all_items)} no catalogo da empresa)."
        ),
    }


@tool_handler("communication")
async def _wrap_apply_alert_rule_template(**kwargs):
    """
    Aplica alert rule template canonical via snapshot canonical (B1).

    Decisao Paulo 2026-05-20: snapshot canonical (NAO sincroniza com master
    apos aplicacao). Quando admin escolhe customizar, criamos copia total
    via customize_master() do repo.

    kwargs:
        company_id (str, obrigatorio via ContextVar JWT)
        template_id (str, obrigatorio): UUID do template canonical
        target (str, opcional): "vacancy" ou "global" (default: global)
        vacancy_id (str, opcional se target=vacancy)
    """
    import uuid

    from app.core.database import AsyncSessionLocal
    from app.domains.communication.repositories.alert_rule_template_repository import (
        AlertRuleTemplateRepository,
    )

    company_id = kwargs.get("company_id")
    template_id_raw = kwargs.get("template_id")
    target = (kwargs.get("target") or "global").strip().lower()
    vacancy_id = kwargs.get("vacancy_id")
    user_id = kwargs.get("user_id")

    if not template_id_raw:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "template_id obrigatorio",
        }

    try:
        template_uuid = (
            uuid.UUID(template_id_raw)
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

    if target not in ("vacancy", "global"):
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": f"target invalido '{target}'. Use: vacancy | global",
        }

    if target == "vacancy" and not vacancy_id:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "vacancy_id obrigatorio quando target=vacancy",
        }

    async with AsyncSessionLocal() as db:
        repo = AlertRuleTemplateRepository(db)
        template = await repo.get_by_id(template_uuid, company_id)

        if not template:
            return {
                "success": False,
                "fallback_used": True,
                "needs_manual_review": True,
                "message": "Template nao encontrado ou fora do escopo da empresa",
            }

        # Snapshot canonical B1: copia total do data
        snapshot = dict(template.data or {})
        snapshot["_template_id"] = str(template.id)
        snapshot["_is_master_origin"] = template.is_master_template
        snapshot["_target"] = target
        if vacancy_id:
            snapshot["_vacancy_id"] = str(vacancy_id)

        # Se master, criar copia per-company (decisao A1+B1 canonical)
        cloned_id = None
        if template.is_master_template:
            try:
                cloned = await repo.customize_master(
                    master_id=template.id,
                    company_id=company_id,
                    created_by=str(user_id) if user_id else None,
                    overrides=None,
                )
                if cloned:
                    cloned_id = str(cloned.id)
                    await db.commit()
            except Exception:
                await db.rollback()
                # Snapshot retornado mesmo sem clone; persistencia final
                # ocorre em camada externa (settings save)
                pass

    return {
        "success": True,
        "data": {
            "template_id": str(template.id),
            "cloned_template_id": cloned_id,
            "target": target,
            "vacancy_id": str(vacancy_id) if vacancy_id else None,
            "snapshot": snapshot,
            "is_master_origin": template.is_master_template,
        },
        "message": (
            f"Alert rule '{snapshot.get('label', '')[:60]}' aplicado "
            f"(target={target}; snapshot canonical B1)."
        ),
    }


@tool_handler("communication")
async def _wrap_create_custom_alert_rule_template(**kwargs):
    """
    Cria alert rule template custom canonical via wizard conversacional.

    Permissoes (decisao Paulo C 2026-05-20): recrutador + admin podem criar
    novos templates; persistido per-company.

    kwargs:
        company_id (str, obrigatorio via ContextVar JWT)
        user_id (str, opcional): created_by audit
        event_type (str, obrigatorio): chave canonical do evento (min 2 chars)
        label (str, obrigatorio): nome humano (min 2 chars)
        audience (str, obrigatorio): recruiter | admin | candidate
        channels (list[str], obrigatorio): pelo menos 1 de email/in_app/teams/whatsapp
        delay_minutes (int, opcional): 0-43200 (default 0)
        rationale (str, opcional): explicacao do canal/delay canonical
        description (str, opcional)
        schedule_lgpd_compliant (bool, opcional, default True)
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.communication.repositories.alert_rule_template_repository import (
        AlertRuleTemplateRepository,
    )

    company_id = kwargs.get("company_id")
    user_id = kwargs.get("user_id")
    event_type = (kwargs.get("event_type") or "").strip()
    label = (kwargs.get("label") or "").strip()
    audience = (kwargs.get("audience") or "").strip().lower()
    channels = kwargs.get("channels") or []
    delay_minutes_raw = kwargs.get("delay_minutes", 0)
    rationale = kwargs.get("rationale")
    description = kwargs.get("description")
    schedule_lgpd_compliant = kwargs.get("schedule_lgpd_compliant", True)
    enabled_default = kwargs.get("enabled_default", True)

    # Validacoes canonical (mesmas regras do AlertRuleData schema)
    if not event_type or len(event_type) < 2:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "event_type obrigatorio (min 2 caracteres)",
        }
    if len(event_type) > 128:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "event_type max 128 caracteres",
        }
    if not label or len(label) < 2:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "label obrigatorio (min 2 caracteres)",
        }
    if len(label) > 255:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "label max 255 caracteres",
        }

    VALID_AUDIENCES = {"recruiter", "admin", "candidate"}
    if audience not in VALID_AUDIENCES:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": (
                f"audience invalido '{audience}'. "
                f"Use: {', '.join(sorted(VALID_AUDIENCES))}"
            ),
        }

    if not isinstance(channels, list) or len(channels) < 1:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "channels obrigatorio (lista com pelo menos 1 canal)",
        }

    VALID_CHANNELS = {"email", "in_app", "teams", "whatsapp"}
    invalid = [c for c in channels if c not in VALID_CHANNELS]
    if invalid:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": (
                f"channels invalidos: {invalid}. "
                f"Use: {', '.join(sorted(VALID_CHANNELS))}"
            ),
        }

    try:
        delay_minutes = int(delay_minutes_raw)
    except (ValueError, TypeError):
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": f"delay_minutes invalido: {delay_minutes_raw}",
        }
    if delay_minutes < 0 or delay_minutes > 43200:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "delay_minutes deve estar entre 0 e 43200 (30 dias)",
        }

    data = {
        "event_type": event_type,
        "label": label,
        "description": description,
        "audience": audience,
        "channels": channels,
        "delay_minutes": delay_minutes,
        "schedule_lgpd_compliant": bool(schedule_lgpd_compliant),
        "rationale": rationale,
        "enabled_default": bool(enabled_default),
    }

    async with AsyncSessionLocal() as db:
        repo = AlertRuleTemplateRepository(db)
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
                "message": f"Falha ao criar alert rule template: {str(e)}",
            }

    return {
        "success": True,
        "data": {
            "id": str(template.id),
            "company_id": template.company_id,
            "is_master_template": False,
            "event_type": event_type,
            "label": label,
            "audience": audience,
            "channels": channels,
            "delay_minutes": delay_minutes,
        },
        "message": (
            f"Alert rule template custom criado para a empresa "
            f"(id={str(template.id)[:8]}..., event_type={event_type})."
        ),
    }


def get_communication_tools() -> list[ToolDefinition]:
    # R-004 (Sprint 1 Quick Wins): primeiro tool deste registry adota
    # output_schema=ToolOutput como pattern canonical. Demais tools seguem
    # como debito Sprint 2 (mesmo template, copy-paste).
    from lia_agents_core.tool_adapter import ToolOutput

    return [
        ToolDefinition(
            side_effects=["send"],
            touches_pii=True,
            pii_output_fields=["body",
            "email_address"],
            name="send_email",
            description=(
                "Enviar e-mail para um candidato. "
                "Parâmetros: candidate_id (int, obrigatório), company_id (str, obrigatório), "
                "subject (str, obrigatório), body (str, obrigatório), "
                "template_type (str, opcional — ex: screening_invitation, rejection_feedback)."
            ),
            output_schema=ToolOutput,
            function=_wrap_send_email,
            
        ),
        ToolDefinition(
            side_effects=["send"],
            touches_pii=True,
            pii_output_fields=["message",
            "candidate_phone"],
            name="send_whatsapp",
            description=(
                "Enviar mensagem WhatsApp para um candidato via Twilio. "
                "Parâmetros: candidate_phone (str, obrigatório — com código do país), "
                "message (str, obrigatório), company_id (str, obrigatório), "
                "candidate_id (int, opcional)."
            ),
            output_schema=ToolOutput,
            function=_wrap_send_whatsapp,
        ),
        ToolDefinition(
            touches_pii=True,
            pii_output_fields=["message_body",
            "email_address",
            "phone_number"],
            name="get_communication_history",
            description="Recuperar histórico de comunicações de um candidato.",
            parameters={
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "string", "description": "ID do candidato"},
                    "limit": {
                        "type": "integer",
                        "description": "Numero maximo de mensagens (padrao: 10, max: 50)",
                    },
                    "channel": {
                        "type": "string",
                        "description": "Filtro por canal: email, whatsapp, all (padrao: all)",
                    },
                },
                "required": ["candidate_id"],
            },
            output_schema=ToolOutput,
            function=_wrap_get_communication_history,
        ),
        ToolDefinition(
            side_effects=["write",
            "send"],
            name="schedule_message",
            description=(
                "Agendar o envio de uma mensagem futura para um candidato. "
                "Parâmetros: candidate_id (int, obrigatório), company_id (str, obrigatório), "
                "channel (str, obrigatório — email/whatsapp/teams), message (str, obrigatório), "
                "scheduled_at (str ISO datetime, obrigatório — ex: 2026-03-10T14:00:00)."
            ),
            output_schema=ToolOutput,
            function=_wrap_schedule_message,
        ),
        ToolDefinition(
            name="check_rate_limit",
            description=(
                "Verificar se um candidato ainda pode receber mensagens (rate limit LGPD, "
                "opt-out, quarentena). "
                "Parâmetros: candidate_id (int, obrigatório), company_id (str, obrigatório), "
                "channel (str, obrigatório — email/whatsapp/teams)."
            ),
            output_schema=ToolOutput,
            function=_wrap_check_rate_limit,
        ),
        ToolDefinition(
            name="suggest_communication_policy",
            description=(
                "Sugere politica canonical de comunicacao (canais + horarios + "
                "alert rules) por publico (recrutador|candidato) e evento "
                "(geral|rejeicao|sla|...). Util quando admin abre Settings > "
                "Comunicacao&Alertas. Horarios LGPD-compliant para candidato."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "audience": {"type": "string", "description": "candidato | recrutador"},
                    "event_type": {"type": "string", "description": "geral | rejeicao | sla | ..."},
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_suggest_communication_policy,
        ),
        ToolDefinition(
            name="suggest_alert_rule_templates",
            description=(
                "Sugere alert rule templates canonical ranked por relevancia "
                "(audience match + event_type match + master priority). Top 10. "
                "Util quando admin abre Settings > Comunicacao&Alertas e quer "
                "ver opcoes recomendadas para a empresa."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "audience": {
                        "type": "string",
                        "enum": ["recruiter", "admin", "candidate"],
                        "description": "Filtrar por publico (opcional)",
                    },
                    "event_type": {
                        "type": "string",
                        "description": "Filtrar por chave canonical do evento (opcional)",
                    },
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_suggest_alert_rule_templates,
        ),
        ToolDefinition(
            name="apply_alert_rule_template",
            description=(
                "Aplica alert rule template canonical via snapshot canonical "
                "(B1). Se origem master, cria copia per-company automaticamente. "
                "NAO sincroniza com master apos aplicacao."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "UUID do template canonical",
                    },
                    "target": {
                        "type": "string",
                        "enum": ["vacancy", "global"],
                        "description": "Escopo da aplicacao (default global)",
                    },
                    "vacancy_id": {
                        "type": "string",
                        "description": "UUID da vaga (obrigatorio se target=vacancy)",
                    },
                },
                "required": ["template_id"],
            },
            output_schema=ToolOutput,
            function=_wrap_apply_alert_rule_template,
        ),
        ToolDefinition(
            name="create_custom_alert_rule_template",
            description=(
                "Cria alert rule template custom canonical persistido per-company. "
                "Recrutador + admin podem criar (decisao Paulo C 2026-05-20). "
                "Schema valida event_type/label/audience/channels canonical."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "description": "Chave canonical do evento (min 2 chars, max 128)",
                    },
                    "label": {
                        "type": "string",
                        "description": "Nome humano (min 2 chars, max 255)",
                    },
                    "description": {"type": "string"},
                    "audience": {
                        "type": "string",
                        "enum": ["recruiter", "admin", "candidate"],
                    },
                    "channels": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["email", "in_app", "teams", "whatsapp"],
                        },
                        "description": "Pelo menos 1 canal canonical",
                    },
                    "delay_minutes": {
                        "type": "integer",
                        "description": "0-43200 (30 dias). Default 0.",
                    },
                    "rationale": {
                        "type": "string",
                        "description": "Explicacao opcional do canal/delay canonical",
                    },
                    "schedule_lgpd_compliant": {
                        "type": "boolean",
                        "description": "Respeitar horario comercial (default True)",
                    },
                },
                "required": ["event_type", "label", "audience", "channels"],
            },
            output_schema=ToolOutput,
            function=_wrap_create_custom_alert_rule_template,
        ),
    ]


def get_stage_tools(stage: str) -> list[ToolDefinition]:
    """Return tools available for a given communication stage."""
    from app.domains.communication.agents.communication_stage_context import (
        get_stage_tools as _stage_tools,
    )

    stage_tool_names = set(_stage_tools(stage))
    return [t for t in get_communication_tools() if t.name in stage_tool_names]
