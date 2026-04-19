"""Candidate Self-Service domain — read-only status portal for candidates."""
from __future__ import annotations

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

_matcher = KeywordIntentMatcher.from_keyword_map(
    _KEYWORD_ACTION_MAP, domain_id="candidate_self_service"
)

CANDIDATE_SELF_SERVICE_ACTIONS = [
    DomainAction(
        action_id="get_status",
        name="Consultar Status da Candidatura",
        description="Retorna etapa atual, data de entrada e próximos passos",
        required_params=["candidate_id", "vacancy_id"],
        tags=["status", "pipeline"],
    ),
    DomainAction(
        action_id="get_interview_info",
        name="Consultar Entrevista Agendada",
        description="Retorna data, horário e formato da entrevista agendada (se houver)",
        required_params=["candidate_id", "vacancy_id"],
        tags=["interview", "scheduling"],
    ),
    DomainAction(
        action_id="get_feedback",
        name="Consultar Feedback da Triagem",
        description="Retorna feedback estruturado WSI se disponibilizado pela empresa",
        required_params=["candidate_id", "vacancy_id"],
        tags=["feedback", "wsi"],
    ),
    DomainAction(
        action_id="get_lgpd_info",
        name="Solicitar Explicação LGPD",
        description="Informa sobre direito de explicação (LGPD Art. 20) e canal de contato",
        required_params=["candidate_id"],
        tags=["lgpd", "compliance"],
    ),
]


@register_domain
class CandidateSelfServiceDomain(ComplianceDomainPrompt):
    """Domínio read-only de autoatendimento do candidato."""

    _compliance_config = {"high_impact": True, "fairness_action_type": "candidate_response"}

    domain_id = "candidate_self_service"
    domain_name = "Candidate Self-Service"
    description = "Portal de autoatendimento: candidato consulta status do próprio processo seletivo"

    def get_allowed_actions(self) -> list[DomainAction]:
        return CANDIDATE_SELF_SERVICE_ACTIONS

    def get_system_prompt(self) -> str:
        return (
            "Assistente de autoatendimento para candidatos da WeDOTalent. "
            "Responda apenas sobre o processo seletivo do candidato autenticado, "
            "com empatia e clareza. Nunca revele scores internos ou dados de terceiros."
        )

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="get_status")
                return IntentResult(
                    intent_id=f"candidate_self_service.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[CSS] Info query → action='{match.action}'",
                )
            except Exception:
                pass

        try:
            match = _matcher.match(query, default_action="get_status")
            return IntentResult(
                intent_id=f"candidate_self_service.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"[CSS] KeywordIntentMatcher → action='{match.action}'",
            )
        except Exception as e:
            logger.debug("[CSS] Matcher failed, fallback: %s", e)
            return IntentResult(
                intent_id="candidate_self_service.get_status",
                action_id="get_status",
                confidence=0.5,
                extracted_params={"raw_query": query},
                reasoning="[CSS] Fallback default → get_status",
            )

    async def execute_action(
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio candidate_self_service."
            )
        logger.info("[CSS] action=%s candidate_id=%s", action_id, params.get("candidate_id"))
        return DomainResponse.success_response(
            message="Consultando informações...",
            data={"action_id": action_id},
            domain_id=self.domain_id,
            action_id=action_id,
        )
