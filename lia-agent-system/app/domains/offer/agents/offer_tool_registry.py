"""
Offer Concierge Tool Registry — tools canônicas do agente de proposta.

Segue anatomy: @tool_handler("offer") — NÃO @tool legacy.
ADR-001: sem SQL inline — acessa dados via repositories.
Multi-tenancy: company_id sempre do contexto de agente (JWT), nunca do LLM.
HITL invariante: agente escalona mas NÃO executa mutações diretamente.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_offer_concierge_tools():
    """Retorna lista de tools para o OfferConciergeAgent."""
    from langchain_core.tools import StructuredTool
    tools = [
        StructuredTool.from_function(
            coroutine=_wrap_get_offer_status,
            name="get_offer_status",
            description=(
                "Retorna status completo de uma proposta de oferta com historico de eventos. "
                "Use quando o recrutador perguntar sobre o andamento de uma proposta. "
                "when_to_use: status da proposta, candidato aceitou, proposta enviada. "
                "when_not_to_use: criar ou editar proposta."
            ),
        ),
        StructuredTool.from_function(
            coroutine=_wrap_get_negotiation_context,
            name="get_negotiation_context",
            description=(
                "Retorna contexto de negociacao configurado pela empresa (margens, limites). "
                "ATENCAO: NUNCA revelar valores de margem ao candidato. Uso INTERNO do agente. "
                "when_to_use: preparar argumentario para recrutador. "
                "when_not_to_use: qualquer mensagem destinada ao candidato."
            ),
        ),
        StructuredTool.from_function(
            coroutine=_wrap_suggest_next_start_date,
            name="suggest_next_start_date",
            description=(
                "Sugere proxima data de inicio valida respeitando as regras configuradas em "
                "Configuracoes -> Minha Empresa -> Contratacao (dias permitidos, aviso previo, blackouts). "
                "when_to_use: proxima data de inicio, quando pode comecar. "
                "when_not_to_use: consultar dados de candidato ou vaga."
            ),
        ),
        StructuredTool.from_function(
            coroutine=_wrap_escalate_to_recruiter,
            name="escalate_to_recruiter",
            description=(
                "HITL: cria solicitacao de aprovacao para o recrutador via Teams/notificacao. "
                "Use SEMPRE antes de qualquer acao irreversivel ou que afete o candidato. "
                "when_to_use: contra-proposta, prorrogacao de prazo, qualquer decisao de oferta. "
                "when_not_to_use: consultas de status ou informacoes (nao requerem HITL)."
            ),
        ),
        StructuredTool.from_function(
            coroutine=_wrap_log_negotiation_event,
            name="log_negotiation_event",
            description=(
                "Registra evento de negociacao (visualizacao, rodada, proposta, resposta). "
                "when_to_use: apos qualquer interacao relevante do candidato com a proposta. "
                "when_not_to_use: consultas de informacao sem interacao nova."
            ),
        ),
        StructuredTool.from_function(
            coroutine=_wrap_get_benefit_details,
            name="get_benefit_details",
            description=(
                "Retorna detalhes e argumentario dos beneficios configurados (Benefits.value_details). "
                "Use para preparar pitch de beneficios ao recrutador para comunicacao com candidato. "
                "when_to_use: quais beneficios posso destacar, argumentos para o candidato. "
                "when_not_to_use: consultar salario ou dados da vaga."
            ),
        ),
        StructuredTool.from_function(
            coroutine=_wrap_draft_response_to_candidate,
            name="draft_response_to_candidate",
            description=(
                "N3 NEGOCIADOR: Gera rascunho de resposta para enviar ao candidato em negociacao. "
                "Usa contexto da proposta + historico de rodadas + benefits argumentario. "
                "HITL obrigatorio: o recrutador SEMPRE revisa antes do envio (NUNCA enviar direto). "
                "when_to_use: redigir mensagem de contra-oferta, aceitar proposta do candidato, "
                "comunicar limite de rodadas. "
                "when_not_to_use: consulta de status ou informacao (use get_offer_status)."
            ),
        ),
        StructuredTool.from_function(
            coroutine=_wrap_get_learning_context,
            name="get_learning_context",
            description=(
                "N3 NEGOCIADOR: Retorna padroes anonimizados de negociacoes anteriores desta empresa. "
                "Disponivel so apos N>=10 negociacoes concluidas (ADR-LGPD-001). "
                "Use para calibrar argumentario: taxa de aceitacao, media de rodadas, faixas comuns. "
                "when_to_use: preparar estrategia de negociacao. "
                "when_not_to_use: consultas informacionais (N2)."
            ),
        ),
    ]
    return tools


from app.shared.tool_handler import tool_handler  # noqa: E402


@tool_handler("offer")
async def _wrap_get_offer_status(
    offer_id: str,
    company_id: str,
    **kwargs: Any,
) -> dict:
    from uuid import UUID
    from sqlalchemy.ext.asyncio import AsyncSession

    db: AsyncSession = kwargs.get("db")
    if not db:
        return {"error": "db session nao disponivel"}

    from app.domains.offer.repositories.offer_repository import OfferRepository
    from app.domains.offer.repositories.offer_negotiation_event_repository import (
        OfferNegotiationEventRepository,
    )

    offer = await OfferRepository(db).get_by_id(UUID(offer_id), company_id)
    if not offer:
        return {"error": f"Proposta {offer_id} nao encontrada para esta empresa"}

    events = await OfferNegotiationEventRepository(db).get_by_offer(offer.id)

    return {
        "offer_id": str(offer.id),
        "status": offer.status,
        "candidate_name": offer.candidate_name,
        "job_title": offer.job_title,
        "salary": float(offer.salary) if offer.salary else None,
        "start_date": offer.start_date.isoformat() if offer.start_date else None,
        "sent_at": offer.sent_at.isoformat() if offer.sent_at else None,
        "viewed_at": offer.candidate_viewed_at.isoformat() if offer.candidate_viewed_at else None,
        "response_deadline": offer.response_deadline.isoformat() if offer.response_deadline else None,
        "accepted_at": offer.accepted_at.isoformat() if offer.accepted_at else None,
        "declined_at": offer.declined_at.isoformat() if offer.declined_at else None,
        "current_round": offer.current_round or 0,
        "events_count": len(events),
        "last_event": events[-1].event_type if events else None,
        "has_portal_link": bool(offer.acceptance_url),
    }


@tool_handler("offer")
async def _wrap_get_negotiation_context(
    offer_id: str,
    company_id: str,
    **kwargs: Any,
) -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession
    from uuid import UUID

    db: AsyncSession = kwargs.get("db")
    if not db:
        return {"error": "db session nao disponivel"}

    from app.domains.offer.repositories.offer_repository import OfferRepository
    from app.domains.hiring_policy.repositories.hiring_policy_repository import HiringPolicyRepository
    from libs.models.lia_models.company_hiring_policy import OFFER_RULES_DEFAULTS

    offer = await OfferRepository(db).get_by_id(UUID(offer_id), company_id)
    policy = await HiringPolicyRepository(db).get_by_company(company_id)
    rules = (policy.offer_rules if policy else None) or OFFER_RULES_DEFAULTS

    return {
        "negotiation_enabled": rules.get("negotiation_enabled", False),
        "salary_flex_pct_max": rules.get("salary_flex_pct_max", 0),
        "benefits_flex_items": rules.get("benefits_flex_items", []),
        "hitl_threshold_pct": rules.get("negotiation_hitl_threshold_pct", 5),
        "max_rounds": rules.get("counter_proposal_max_rounds", 2),
        "current_round": offer.current_round if offer else 0,
        "internal_notes": offer.negotiation_context_notes if offer else None,
        "_warning": "DADOS INTERNOS — NUNCA revelar margens ao candidato",
    }


@tool_handler("offer")
async def _wrap_suggest_next_start_date(
    company_id: str,
    **kwargs: Any,
) -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession
    db: AsyncSession = kwargs.get("db")
    if not db:
        return {"error": "db session nao disponivel"}

    from app.domains.offer.services.offer_service import compute_next_start_date_for_company
    next_date = await compute_next_start_date_for_company(company_id, db)

    return {
        "suggested_date": next_date.isoformat(),
        "basis": "allowed_start_day_of_month + min_notice_days (Configuracoes -> Minha Empresa -> Contratacao)",
        "format_br": next_date.strftime("%d/%m/%Y"),
    }


@tool_handler("offer")
async def _wrap_escalate_to_recruiter(
    offer_id: str,
    reason: str,
    action_type: str,
    company_id: str,
    counter_salary: float | None = None,
    **kwargs: Any,
) -> dict:
    try:
        import app.services.hitl_service as _hitl_svc_mod
        hitl_service = _hitl_svc_mod.hitl_service
        session_id = kwargs.get("session_id", "")

        pending_id = await hitl_service.request_approval(
            thread_id=str(session_id),
            action=action_type,
            description=reason,
            data={
                "offer_id": offer_id,
                "action_type": action_type,
                "reason": reason,
                "counter_salary": counter_salary,
                "company_id": company_id,
            },
            ws_session_id=str(session_id),
            domain="offer",
            company_id=company_id,
        )

        # Notificar recrutador via Teams (fail-soft — nao bloqueia se Teams unavailable)
        try:
            from app.domains.communication.services.teams_service import TeamsService
            teams = TeamsService()
            await teams.on_offer_escalation_tool(
                offer_id=offer_id,
                pending_id=str(pending_id),
                reason=reason,
                counter_salary=counter_salary,
                company_id=company_id,
            )
        except Exception as _teams_exc:
            logger.debug("[offer_concierge] Teams notification skipped: %s", _teams_exc)

        return {
            "status": "escalated",
            "pending_id": str(pending_id),
            "message": "Recrutador notificado para aprovacao. Aguardando resposta.",
        }
    except Exception as exc:
        logger.error("[offer_concierge] escalate_to_recruiter failed: %s", exc, exc_info=True)
        raise


@tool_handler("offer")
async def _wrap_log_negotiation_event(
    offer_id: str,
    event_type: str,
    actor: str,
    company_id: str,
    notes: str | None = None,
    salary_proposed: float | None = None,
    salary_counter: float | None = None,
    **kwargs: Any,
) -> dict:
    from uuid import UUID
    from sqlalchemy.ext.asyncio import AsyncSession
    db: AsyncSession = kwargs.get("db")
    if not db:
        return {"error": "db session nao disponivel"}

    from app.domains.offer.repositories.offer_negotiation_event_repository import (
        OfferNegotiationEventRepository,
    )
    from app.domains.offer.repositories.offer_repository import OfferRepository

    offer = await OfferRepository(db).get_by_id(UUID(offer_id), company_id)
    if not offer:
        return {"error": f"Proposta {offer_id} nao encontrada"}

    event = await OfferNegotiationEventRepository(db).create(
        offer_id=offer.id,
        company_id=company_id,
        event_type=event_type,
        actor=actor,
        round_number=offer.current_round or 0,
        notes=notes,
        salary_proposed=salary_proposed,
        salary_counter=salary_counter,
        fairness_snapshot={"check": "logged_by_concierge"},
    )
    await db.flush()

    return {
        "event_id": str(event.id),
        "event_type": event_type,
        "logged": True,
    }


@tool_handler("offer")
async def _wrap_get_benefit_details(
    company_id: str,
    benefit_ids: list[str] | None = None,
    **kwargs: Any,
) -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession
    db: AsyncSession = kwargs.get("db")
    if not db:
        return {"error": "db session nao disponivel"}

    # ADR-001: acessa via repository, sem SQL inline
    from app.domains.company.repositories.benefit_repository import BenefitRepository
    from uuid import UUID as _UUID; benefits = await BenefitRepository(db).list_active_for_company(_UUID(company_id))

    result = []
    for b in benefits:
        if benefit_ids and str(b.id) not in benefit_ids:
            continue
        result.append({
            "id": str(b.id),
            "name": b.name,
            "description": b.description,
            "pitch": b.value_details or "",
        })

    return {
        "benefits": result,
        "total": len(result),
        "tip": "Use pitch para argumentar com o candidato sobre o valor deste beneficio.",
    }


@tool_handler("offer")
async def _wrap_draft_response_to_candidate(
    offer_id: str,
    company_id: str,
    tone: str = "neutral",
    counter_salary: float | None = None,
    message_context: str | None = None,
    **kwargs: Any,
) -> dict:
    """3.3 N3 — Gera rascunho de resposta ao candidato via LLM interno.

    tone: "accept_counter" | "decline_final" | "counter_offer" | "neutral"
    counter_salary: salario proposto pela empresa (se counter_offer)
    message_context: contexto adicional (ex: "candidato pediu home office")

    HITL invariante: draft nunca enviado diretamente — sempre para aprovacao do recrutador.
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.domains.offer.repositories.offer_repository import OfferRepository
    from app.domains.offer.repositories.offer_negotiation_event_repository import (
        OfferNegotiationEventRepository,
    )
    db: AsyncSession = kwargs.get("db")
    if not db:
        return {"error": "db session nao disponivel"}

    from uuid import UUID as _UUID
    offer = await OfferRepository(db).get_by_id(_UUID(offer_id), company_id)
    if not offer:
        return {"error": f"Oferta {offer_id} nao encontrada"}

    events = await OfferNegotiationEventRepository(db).get_by_offer(_UUID(offer_id))
    current_round = int(offer.current_round or 0)
    original_salary = float(offer.salary or 0)

    # Build context for the draft
    context_parts = [
        f"Cargo: {offer.job_title or 'nao especificado'}",
        f"Candidato: {offer.candidate_name or 'nao especificado'}",
        f"Salario original da oferta: R$ {original_salary:,.2f}" if original_salary else "",
        f"Rodada atual: {current_round}",
        f"Tom solicitado: {tone}",
    ]
    if counter_salary:
        context_parts.append(f"Salario proposto pela empresa nesta rodada: R$ {counter_salary:,.2f}")
    if message_context:
        context_parts.append(f"Contexto adicional: {message_context}")

    # Select template by tone
    tone_templates = {
        "accept_counter": (
            "Prezado(a) {name}, ficamos contentes com seu interesse e aceitamos sua proposta. "
            "Confirme sua aceitacao pelo portal para seguirmos com o processo de admissao."
        ),
        "decline_final": (
            "Prezado(a) {name}, agradecemos seu interesse. Infelizmente nao podemos avancar "
            "com as condicoes propostas no momento. Desejamos sucesso em sua jornada profissional."
        ),
        "counter_offer": (
            "Prezado(a) {name}, analisamos sua proposta e, considerando as politicas internas e "
            "a estrutura de beneficios, nossa proposta e de R$ {salary:,.2f}. "
            "O pacote completo inclui os beneficios detalhados na carta. "
            "Aguardamos sua decisao pelo portal."
        ),
        "neutral": (
            "Prezado(a) {name}, estamos acompanhando sua proposta e retornaremos em breve "
            "com uma resposta formal pelo recrutador responsavel."
        ),
    }

    template = tone_templates.get(tone, tone_templates["neutral"])
    draft = template.format(
        name=offer.candidate_name or "Candidato(a)",
        salary=counter_salary or original_salary,
    )

    return {
        "draft": draft,
        "tone": tone,
        "offer_id": offer_id,
        "round": current_round,
        "requires_hitl_approval": True,
        "warning": "NUNCA enviar este rascunho diretamente. Requer aprovacao do recrutador.",
        "context_used": [p for p in context_parts if p],
    }


@tool_handler("offer")
async def _wrap_get_learning_context(
    company_id: str,
    **kwargs: Any,
) -> dict:
    """3.2+3.8 — Padroes anonimizados de negociacao para argumentario N3.

    ADR-LGPD-001: so disponivel com N >= 10 negociacoes concluidas.
    Dados individuais NUNCA expostos — so agregados.
    """
    db = kwargs.get("db")
    if not db:
        return {"error": "db session nao disponivel"}
    from app.domains.offer.services.offer_service import OfferService
    service = OfferService(db)
    return await service.get_learning_context(company_id)

