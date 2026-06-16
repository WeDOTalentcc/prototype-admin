"""
OfferConciergeAgent — agente canonical de proposta de oferta WeDOTalent.

Anatomy: LangGraphReActBase + EnhancedAgentMixin + @register_agent
Cross-cutting:
  FAR-2  — FairnessGuard bloqueia linguagem discriminatória antes do LLM
  PII    — strip_pii_for_llm_prompt antes de qualquer call
  AUD-4  — HITL gate para ações irreversíveis (_HITL_MESSAGE_TYPES)
  ACH-026 — audit_service.log_decision pós-processamento

HITL invariante: agente NUNCA muta status diretamente.
  Toda ação sensível → escalate_to_recruiter → HITLService.request_approval
  → recrutador aprova → executa.

N2 (default): concierge informacional — status, argumentário, datas.
N3 (gated em offer_rules.negotiation_enabled): agente negociador.
"""
from __future__ import annotations

import logging
from typing import Any

from lia_agents_core.agent_interface import AgentInput, AgentOutput
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin

logger = logging.getLogger(__name__)

_OFFER_YAML_PATH = "app/prompts/domains/offer.yaml"


@register_agent(
    "offer_concierge",
    aliases=["offer", "proposta", "carta_oferta", "negociacao_oferta"],
)
class OfferConciergeAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    """Agente de proposta de oferta — N2 informacional + N3 negociador (gated)."""

    domain_name = "offer"

    _HITL_MESSAGE_TYPES: frozenset[str] = frozenset({
        "send_counter_proposal",
        "accept_negotiation_round",
        "extend_deadline",
        "confirm_hire",
    })

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._system_prompt_path = _OFFER_YAML_PATH

    def _get_tools(self) -> list:
        from app.domains.offer.agents.offer_tool_registry import get_offer_concierge_tools
        return get_offer_concierge_tools()

    async def process(self, input: AgentInput) -> AgentOutput:
        # ── FAR-2: FairnessGuard ──────────────────────────────────────────────
        try:
            from app.shared.fairness.fairness_guard import FairnessGuard
            guard = FairnessGuard()
            fairness_result = await guard.check(
                text=input.message,
                context={"domain": self.domain_name, "company_id": input.company_id},
            )
            if fairness_result.blocked:
                logger.warning(
                    "[offer_concierge] FAR-2 block company=%s reason=%s",
                    input.company_id,
                    fairness_result.reason,
                )
                return AgentOutput(
                    message=fairness_result.safe_response
                    or "Não posso ajudar com isso. Por favor reformule sua pergunta.",
                    metadata={"fairness_blocked": True, "reason": fairness_result.reason},
                )
        except Exception as _far2_exc:
            logger.error("[offer_concierge] FAR-2 guard failed: %s", _far2_exc, exc_info=True)
            raise

        # ── PII Strip ────────────────────────────────────────────────────────
        try:
            from app.shared.pii_masking import strip_pii_for_llm_prompt
            safe_message = strip_pii_for_llm_prompt(input.message)
        except Exception as _pii_exc:
            logger.error("[offer_concierge] PII strip failed: %s", _pii_exc, exc_info=True)
            raise
        pii_stripped_input = input.model_copy(update={"message": safe_message})

        # ── AUD-4: HITL gate ─────────────────────────────────────────────────
        detected_hitl_type = self._detect_hitl_intent(input.message)
        if detected_hitl_type:
            logger.info(
                "[offer_concierge] AUD-4 HITL intent=%s company=%s",
                detected_hitl_type,
                input.company_id,
            )
            try:
                import app.services.hitl_service as _hitl_svc_mod
                hitl_service = _hitl_svc_mod.hitl_service
                pending_id = await hitl_service.request_approval(
                    thread_id=str(input.session_id or ""),
                    action=detected_hitl_type,
                    description=input.message,
                    data={
                        "original_message": input.message,
                        "hitl_type": detected_hitl_type,
                        "company_id": input.company_id,
                    },
                    ws_session_id=str(input.session_id or ""),
                    domain=self.domain_name,
                    company_id=input.company_id,
                )
                return AgentOutput(
                    message="Solicitei aprovação do recrutador para prosseguir. Aguardando confirmação.",
                    metadata={
                        "hitl_pending": True,
                        "pending_id": str(pending_id),
                        "hitl_type": detected_hitl_type,
                        "requires_approval": True,
                    },
                )
            except Exception as _hitl_exc:
                logger.error(
                    "[offer_concierge] AUD-4 gate failed: %s", _hitl_exc, exc_info=True
                )
                raise

        # ── Core processing ──────────────────────────────────────────────────
        try:
            output = await self._process_langgraph(pii_stripped_input)
        except Exception as exc:
            logger.error(
                "[offer_concierge] _process_langgraph error company=%s: %s",
                input.company_id,
                exc,
                exc_info=True,
            )
            raise

        # ── ACH-026: Audit log ───────────────────────────────────────────────
        try:
            from app.shared.services.audit_service import audit_service
            await audit_service.log_decision(
                company_id=input.company_id,
                agent="offer_concierge",
                action="process",
                input_summary=input.message[:200],
                output_summary=(output.message or "")[:200],
                metadata={
                    "session_id": str(input.session_id or ""),
                    "tools_used": getattr(output, "tools_used", []),
                    "hitl_triggered": False,
                },
                reasoning=["offer_concierge processed request via _process_langgraph"],
            )
        except Exception as _audit_exc:
            logger.warning("[offer_concierge] ACH-026 audit log failed: %s", _audit_exc)

        return output

    def _detect_hitl_intent(self, message: str) -> str | None:
        """Detecta intenção de HITL no texto livre do recrutador."""
        message_lower = message.lower()
        patterns: dict[str, list[str]] = {
            "send_counter_proposal": [
                "contra-proposta", "contraproposta", "nova proposta salarial",
                "ajustar salário", "ajustar salario", "propor novo valor",
            ],
            "accept_negotiation_round": [
                "aceitar proposta", "aprovar negociação", "aprovar negociacao",
                "confirmar acordo", "fechar negociação", "fechar negociacao",
            ],
            "extend_deadline": [
                "prorrogar prazo", "estender prazo", "mais tempo para responder",
                "adiar deadline", "ampliar prazo",
            ],
            "confirm_hire": [
                "confirmar contratação", "confirmar contratacao", "efetivar contratação",
                "efetivar contratacao", "contratar candidato", "finalizar admissão",
                "finalizar admissao",
            ],
        }
        for hitl_type, keywords in patterns.items():
            if any(kw in message_lower for kw in keywords):
                return hitl_type
        return None
