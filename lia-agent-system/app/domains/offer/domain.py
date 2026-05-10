"""
OfferDomain — exposes offer proposal lifecycle as agent-callable tools.
"""
import logging
from pathlib import Path
from typing import Any

import yaml as _yaml_imp

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain
from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher

logger = logging.getLogger(__name__)

_capabilities_yaml_path = Path(__file__).parent / "config" / "capabilities.yaml"
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get("intent_keywords", {})
    if _capabilities_yaml_path.exists()
    else {}
)
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="offer")


@register_domain
class OfferDomain(ComplianceDomainPrompt):
    """Domain for creating and sending structured offer letters."""

    _compliance_config = {"high_impact": True, "fairness_action_type": "offer"}
    domain_id = "offer"
    domain_name = "Offer"
    description = "Gerencia cartas-oferta estruturadas para candidatos aprovados"
    version = "1.0.0"
    agent_aliases = ("offer_agent", "send_offer", "proposal_agent")

    def get_allowed_actions(self) -> list[DomainAction]:
        return [
            DomainAction(
                action_id="create_offer_draft",
                name="Criar Rascunho de Proposta",
                description="Cria rascunho de carta-oferta com pre-fill da vaga e candidato",
                required_params=["candidate_id", "job_id"],
                optional_params=["template_id"],
                tags=["offer", "draft"],
                is_async=True,
            ),
            DomainAction(
                action_id="update_offer_draft",
                name="Atualizar Rascunho",
                description="Atualiza campos do rascunho de proposta",
                required_params=["offer_id"],
                optional_params=[
                    "offered_salary", "offered_bonus_admission",
                    "offered_benefits", "offered_start_date",
                    "validity_days", "recruiter_notes",
                ],
                tags=["offer", "draft"],
                is_async=True,
            ),
            DomainAction(
                action_id="get_offer_draft",
                name="Consultar Rascunho",
                description="Retorna estado atual do rascunho de proposta",
                required_params=["offer_id"],
                tags=["offer", "query"],
                is_async=True,
            ),
            DomainAction(
                action_id="send_offer",
                name="Enviar Proposta",
                description="Envia carta-oferta ao candidato (modo automatico via email)",
                required_params=["offer_id"],
                optional_params=["send_mode"],
                requires_confirmation=True,
                tags=["offer", "send", "high-impact"],
                is_async=True,
            ),
            DomainAction(
                action_id="prepare_offer_manual_send",
                name="Preparar Envio Manual",
                description="Prepara template pre-preenchido para envio manual pelo recrutador",
                required_params=["offer_id"],
                tags=["offer", "manual"],
                is_async=True,
            ),
            DomainAction(
                action_id="cancel_offer",
                name="Cancelar Proposta",
                description="Cancela rascunho de proposta",
                required_params=["offer_id"],
                optional_params=["reason"],
                tags=["offer", "cancel"],
                is_async=True,
            ),
        ]

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        try:
            match = _matcher.match(query, default_action="create_offer_draft")
            return IntentResult(
                intent_id=f"offer_{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={},
                reasoning=f"KeywordIntentMatcher: action='{match.action}' kw='{match.matched_keyword}'",
            )
        except Exception as exc:
            logger.debug("[OFFER-DOMAIN] Matcher failed: %s", exc)
            return IntentResult(
                intent_id="offer_create_offer_draft",
                action_id="create_offer_draft",
                confidence=0.4,
                extracted_params={},
                reasoning="Fallback to create_offer_draft",
            )

    async def execute_action(
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        try:
            result = await _dispatch_tool(action_id, params, context)
            if result.get("success"):
                return DomainResponse.success_response(
                    message=result.get("message", "Acao executada"),
                    data=result,
                    domain_id=self.domain_id,
                    action_id=action_id,
                )
            return DomainResponse.error_response(
                error=result.get("error", "Erro desconhecido"),
                domain_id=self.domain_id,
                action_id=action_id,
            )
        except Exception as exc:
            logger.error("[OFFER-DOMAIN] %s failed: %s", action_id, exc, exc_info=True)
            return DomainResponse.error_response(
                error=str(exc),
                domain_id=self.domain_id,
                action_id=action_id,
            )

    def get_suggestions(self, context: DomainContext) -> list[str]:
        return [
            "Preparar proposta salarial para candidato",
            "Enviar carta-oferta",
            "Ver rascunho de proposta",
        ]


async def _dispatch_tool(
    tool_name: str, params: dict[str, Any], context: DomainContext
) -> dict[str, Any]:
    from app.domains.offer.tools import (
        cancel_offer,
        create_offer_draft,
        get_offer_draft,
        prepare_offer_manual_send,
        send_offer,
        update_offer_draft,
    )

    handlers = {
        "create_offer_draft": create_offer_draft.run,
        "update_offer_draft": update_offer_draft.run,
        "get_offer_draft": get_offer_draft.run,
        "send_offer": send_offer.run,
        "prepare_offer_manual_send": prepare_offer_manual_send.run,
        "cancel_offer": cancel_offer.run,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    # P0-3 fix (2026-05-10): FairnessGuard pre-check em ações de envio
    # Inegociável #3 (FairnessGuard 100% high-impact) + Crença C02 (Justa).
    # offer.send é high_impact: True (domain.py:30). Bloqueia carta-oferta
    # com texto enviesado em recruiter_notes ANTES do envio ao candidato.
    if tool_name in ("send_offer", "update_offer_draft", "prepare_offer_manual_send"):
        from app.domains.offer.compliance import check_input_fairness, emit_offer_audit
        # Concatenar textos livres para fairness check
        free_text_fields = ["recruiter_notes", "send_mode", "offered_benefits"]
        offer_text = " ".join([
            str(params.get(f, "") or "") for f in free_text_fields
        ]).strip()
        if offer_text:
            check = check_input_fairness(offer_text)
            if check.is_blocked:
                # Audit blocked attempt
                emit_offer_audit(
                    company_id=str(getattr(context, "company_id", "") or ""),
                    offer_id=str(params.get("offer_id") or ""),
                    candidate_id=str(params.get("candidate_id") or ""),
                    job_id=str(params.get("job_id") or ""),
                    action=tool_name,
                    success=False,
                    fairness_blocked=check.blocked_terms,
                    payload_text=offer_text,
                )
                logger.warning(
                    "[OFFER-DOMAIN] FairnessGuard blocked %s: category=%s terms=%s",
                    tool_name, check.category, check.blocked_terms,
                )
                return {
                    "success": False,
                    "blocked_by_fairness": True,
                    "error": "Conteúdo bloqueado por FairnessGuard (LGPD/EU AI Act compliance)",
                    "category": check.category,
                    "blocked_terms": check.blocked_terms,
                    "educational_message": check.educational_message
                    or "Identifiquei termos discriminatórios ou enviesados na proposta. Reformule e envie novamente.",
                }

    result = await handler(params, context)

    # P0-3 fix (2026-05-10): emit audit on send_offer success
    if tool_name == "send_offer" and result.get("success"):
        from app.domains.offer.compliance import emit_offer_audit
        emit_offer_audit(
            company_id=str(getattr(context, "company_id", "") or ""),
            offer_id=str(params.get("offer_id") or ""),
            candidate_id=str(params.get("candidate_id") or result.get("candidate_id") or ""),
            job_id=str(params.get("job_id") or result.get("job_id") or ""),
            action="send_offer",
            success=True,
            payload_text=str(params.get("recruiter_notes") or ""),
        )

    return result
