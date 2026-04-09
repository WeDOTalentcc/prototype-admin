"""Recruitment Campaign Domain - End-to-end workflow management."""
import logging
from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP = {
    "criar campanha": "create_campaign", "nova campanha": "create_campaign",
    "iniciar campanha": "create_campaign", "campanha de recrutamento": "create_campaign",
    "progresso campanha": "get_campaign_progress", "status campanha": "get_campaign_progress",
    "como está a campanha": "get_campaign_progress",
    "avançar campanha": "advance_campaign", "próxima etapa": "advance_campaign",
    "listar campanhas": "list_campaigns", "minhas campanhas": "list_campaigns",
}

@register_domain
class RecruitmentCampaignDomain(ComplianceDomainPrompt):
    domain_id = "recruitment_campaign"
    domain_name = "Recruitment Campaigns"
    description = "Workflow ponta-a-ponta de recrutamento — definição a placement"
    _compliance_config = {"high_impact": False, "fairness_action_type": "general"}

    def get_allowed_actions(self):
        from app.domains.recruitment_campaign.actions import CAMPAIGN_ACTIONS
        return CAMPAIGN_ACTIONS

    def get_system_prompt(self):
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt("talent_pool")

    async def process_intent(self, query, context):
        q = query.lower()
        best_action, best_conf = "list_campaigns", 0.3
        for kw, action in _KEYWORD_ACTION_MAP.items():
            if kw in q:
                conf = 0.9 if len(kw) > 6 else 0.75
                if conf > best_conf:
                    best_action, best_conf = action, conf
        return IntentResult(intent_id=f"recruitment_campaign.{best_action}", action_id=best_action, confidence=best_conf, extracted_params={"raw_query": query}, reasoning=f"Keyword matched '{best_action}'")

    async def execute_action(self, action_id, params, context):
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(error=f"Action '{action_id}' not found")
        return DomainResponse.success_response(message=f"Ação '{action.name}' encaminhada.", data={"action_id": action_id, "params": params}, domain_id=self.domain_id, action_id=action_id)
