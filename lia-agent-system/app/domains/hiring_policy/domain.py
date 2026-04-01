from __future__ import annotations

from typing import Dict, Any, List

import logging

from app.domains.base import DomainPrompt, DomainContext, DomainAction, IntentResult, DomainResponse
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP: Dict[str, str] = {
    "política": "configure_policy",
    "politica": "configure_policy",
    "policy": "configure_policy",
    "regra": "configure_policy",
    "configurar": "configure_policy",
    "setup": "configure_policy",
    "pipeline": "configure_pipeline",
    "etapa": "configure_pipeline",
    "stage": "configure_pipeline",
    "agendamento": "configure_scheduling",
    "scheduling": "configure_scheduling",
    "agendar": "configure_scheduling",
    "comunicação": "configure_communication",
    "comunicacao": "configure_communication",
    "communication": "configure_communication",
    "email": "configure_communication",
    "whatsapp": "configure_communication",
    "triagem": "configure_screening",
    "screening": "configure_screening",
    "automação": "configure_automation",
    "automacao": "configure_automation",
    "automation": "configure_automation",
    "autonomia": "configure_automation",
    "compliance": "validate_compliance",
    "conformidade": "validate_compliance",
    "validar": "validate_compliance",
    "progresso": "get_progress",
    "progress": "get_progress",
}

HIRING_POLICY_ACTIONS = [
    DomainAction(
        action_id="configure_policy",
        name="Configurar Política de Contratação",
        description="Configura regras gerais da política de contratação da empresa",
        required_params=["company_id"],
        tags=["policy", "setup"],
    ),
    DomainAction(
        action_id="configure_pipeline",
        name="Configurar Pipeline",
        description="Define regras de pipeline e etapas do processo seletivo",
        required_params=["company_id"],
        tags=["policy", "pipeline"],
    ),
    DomainAction(
        action_id="configure_scheduling",
        name="Configurar Agendamento",
        description="Define regras de agendamento de entrevistas",
        required_params=["company_id"],
        tags=["policy", "scheduling"],
    ),
    DomainAction(
        action_id="configure_communication",
        name="Configurar Comunicação",
        description="Define regras de comunicação com candidatos",
        required_params=["company_id"],
        tags=["policy", "communication"],
    ),
    DomainAction(
        action_id="configure_screening",
        name="Configurar Triagem",
        description="Define regras de triagem e avaliação de candidatos",
        required_params=["company_id"],
        tags=["policy", "screening"],
    ),
    DomainAction(
        action_id="configure_automation",
        name="Configurar Automação",
        description="Define nível de autonomia da LIA e regras de automação",
        required_params=["company_id"],
        tags=["policy", "automation"],
    ),
    DomainAction(
        action_id="validate_compliance",
        name="Validar Compliance",
        description="Valida se a política atual está em conformidade com regras de fairness e LGPD",
        required_params=["company_id"],
        tags=["policy", "compliance"],
    ),
    DomainAction(
        action_id="get_progress",
        name="Ver Progresso",
        description="Retorna o progresso atual da configuração da política",
        required_params=["company_id"],
        tags=["policy", "progress"],
    ),
]


@register_domain
class HiringPolicyDomain(ComplianceDomainPrompt):
    """Domínio de Política de Contratação da LIA."""

    _compliance_config = {'high_impact': True, 'fairness_action_type': 'policy_check'}

    domain_id = "hiring_policy"
    domain_name = "Hiring Policy"
    description = "Configuração e gestão de políticas de contratação, pipeline, triagem e automação"

    def get_allowed_actions(self) -> List[DomainAction]:
        return HIRING_POLICY_ACTIONS

    def get_system_prompt(self) -> str:
        return (
            "Você é a LIA, assistente especializada em configuração de políticas de contratação. "
            "Ajude o recrutador a definir regras de pipeline, agendamento, comunicação, triagem e automação "
            "de forma consultiva, explicando trade-offs e validando compliance."
        )

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        query_lower = query.lower()
        best_action = "configure_policy"
        best_confidence = 0.3

        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                confidence = 0.85 if len(keyword) > 4 else 0.7
                if confidence > best_confidence:
                    best_action = action_id
                    best_confidence = confidence

        return IntentResult(
            intent_id=f"hiring_policy.{best_action}",
            action_id=best_action,
            confidence=best_confidence,
            extracted_params={"raw_query": query},
            reasoning=f"Keyword heuristic matched action '{best_action}'",
        )

    async def execute_action(
        self, action_id: str, params: Dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de hiring_policy."
            )

        logger.info(f"Routing hiring_policy action '{action_id}' (tenant={context.tenant_id})")

        return DomainResponse.success_response(
            message=f"Ação '{action.name}' encaminhada para o agente de política de contratação.",
            data={"action_id": action_id, "params": params},
            domain_id=self.domain_id,
            action_id=action_id,
        )
