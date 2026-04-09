"""Digital Twin Domain - RAG few-shot evaluation using SME reasoning."""
import logging
from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP = {
    "digital twin": "list_twins", "gêmeo digital": "list_twins",
    "criar twin": "create_twin", "novo twin": "create_twin",
    "avaliar com twin": "evaluate_with_twin", "avaliação twin": "evaluate_with_twin",
    "segunda opinião": "evaluate_with_twin", "opinião do especialista": "evaluate_with_twin",
    "treinar twin": "index_twin_audio", "indexar áudio": "index_twin_audio",
}

@register_domain
class DigitalTwinDomain(ComplianceDomainPrompt):
    domain_id = "digital_twin"
    domain_name = "Digital Twins"
    description = "Clone de raciocínio de especialistas via RAG few-shot para avaliação de candidatos"
    _compliance_config = {"high_impact": True, "fairness_action_type": "screening"}

    def get_allowed_actions(self):
        from app.domains.digital_twin.actions import DIGITAL_TWIN_ACTIONS
        return DIGITAL_TWIN_ACTIONS

    def get_system_prompt(self):
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt("digital_twin")

    async def process_intent(self, query, context):
        q = query.lower()
        best_action, best_conf = "list_twins", 0.3
        for kw, action in _KEYWORD_ACTION_MAP.items():
            if kw in q:
                conf = 0.9 if len(kw) > 6 else 0.75
                if conf > best_conf:
                    best_action, best_conf = action, conf
        return IntentResult(intent_id=f"digital_twin.{best_action}", action_id=best_action, confidence=best_conf, extracted_params={"raw_query": query}, reasoning=f"Keyword matched '{best_action}'")

    async def execute_action(self, action_id, params, context):
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(error=f"Action '{action_id}' not found")
        return DomainResponse.success_response(message=f"Ação '{action.name}' encaminhada.", data={"action_id": action_id, "params": params}, domain_id=self.domain_id, action_id=action_id)
