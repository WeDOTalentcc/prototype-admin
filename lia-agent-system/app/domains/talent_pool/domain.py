"""Talent Pool Domain - Live talent banks management."""
import logging
from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP = {
    "criar pool": "create_talent_pool", "criar banco": "create_talent_pool",
    "novo banco": "create_talent_pool", "novo pool": "create_talent_pool",
    "banco de talentos": "list_talent_pools", "listar pool": "list_talent_pools",
    "meus bancos": "list_talent_pools", "meus pools": "list_talent_pools",
    "adicionar ao pool": "add_to_pool", "adicionar no banco": "add_to_pool",
    "mover para vaga": "move_pool_to_job", "migrar para vaga": "move_pool_to_job",
    "candidatos do pool": "get_pool_candidates", "ver pool": "get_pool_candidates",
    "criar vaga do pool": "create_job_from_pool", "vaga a partir do pool": "create_job_from_pool",
}

@register_domain
class TalentPoolDomain(ComplianceDomainPrompt):
    domain_id = "talent_pool"
    domain_name = "Talent Pool Management"
    description = "Gestão de bancos de talentos vivos — criar, listar, adicionar candidatos, migrar para vagas"
    _compliance_config = {"high_impact": True, "fairness_action_type": "sourcing"}

    def get_allowed_actions(self):
        from app.domains.talent_pool.actions import TALENT_POOL_ACTIONS
        return TALENT_POOL_ACTIONS

    def get_system_prompt(self):
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt(self.domain_id)

    async def process_intent(self, query, context):
        q = query.lower()
        best_action, best_conf = "list_talent_pools", 0.3
        for kw, action in _KEYWORD_ACTION_MAP.items():
            if kw in q:
                conf = 0.9 if len(kw) > 6 else 0.75
                if conf > best_conf:
                    best_action, best_conf = action, conf
        return IntentResult(intent_id=f"talent_pool.{best_action}", action_id=best_action, confidence=best_conf, extracted_params={"raw_query": query}, reasoning=f"Keyword matched '{best_action}'")

    async def execute_action(self, action_id, params, context):
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(error=f"Action '{action_id}' not found")
        return DomainResponse.success_response(message=f"Ação '{action.name}' encaminhada.", data={"action_id": action_id, "params": params}, domain_id=self.domain_id, action_id=action_id)
