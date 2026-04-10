"""Agent Studio Domain - Sourcing agents, calibration, multi-strategy search."""
import logging
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP = {
    "criar agente": "create_sourcing_agent", "novo agente": "create_sourcing_agent",
    "ativar agente": "create_sourcing_agent", "agente sourcing": "create_sourcing_agent",
    "agent studio": "list_agents", "studio agentes": "list_agents",
    "calibrar": "calibrate_agent", "calibração": "calibrate_agent",
    "recalibrar": "recalibrate_agent",
    "status agente": "get_agent_status", "como está o agente": "get_agent_status",
    "pausar agente": "pause_agent", "parar agente": "pause_agent",
    "templates setor": "list_sector_templates", "templates disponíveis": "list_sector_templates",
    "busca inteligente": "run_multi_strategy", "multi estratégia": "run_multi_strategy",
    "busca multi": "run_multi_strategy", "4 estratégias": "run_multi_strategy",
}

@register_domain
class AgentStudioDomain(ComplianceDomainPrompt):
    domain_id = "agent_studio"
    domain_name = "Agent Studio"
    description = "Criação e gestão de agentes de sourcing, calibração, busca multi-estratégia"
    _compliance_config = {"high_impact": False, "fairness_action_type": "sourcing"}

    def get_allowed_actions(self):
        from app.domains.agent_studio.actions import AGENT_STUDIO_ACTIONS
        return AGENT_STUDIO_ACTIONS

    def get_system_prompt(self):
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt("agent_calibration")

    async def process_intent(self, query, context):
        q = query.lower()
        best_action, best_conf = "list_agents", 0.3
        for kw, action in _KEYWORD_ACTION_MAP.items():
            if kw in q:
                conf = 0.9 if len(kw) > 6 else 0.75
                if conf > best_conf:
                    best_action, best_conf = action, conf
        return IntentResult(intent_id=f"agent_studio.{best_action}", action_id=best_action, confidence=best_conf, extracted_params={"raw_query": query}, reasoning=f"Keyword matched {best_action}")

    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(error=f"Action {action_id} not found")

        # --- create_sourcing_agent: wire to real orchestrator ---
        if action_id == "create_sourcing_agent":
            return await self._handle_create_sourcing_agent(params, context)

        # Default passthrough for other actions
        return DomainResponse.success_response(
            message=f"Ação {action.name} encaminhada.",
            data={"action_id": action_id, "params": params},
            domain_id=self.domain_id,
            action_id=action_id,
        )

    async def _handle_create_sourcing_agent(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        """Create a sourcing agent via the real orchestrator."""
        from app.core.database import get_db
        from app.services.sourcing_agent_orchestrator import SourcingAgentOrchestrator

        agent_name = params.get("agent_name", "").strip()
        if not agent_name:
            return DomainResponse.clarification_response(
                question="Qual nome você quer dar ao agente de sourcing?",
                options=["Agente Tech SR", "Agente Vendas", "Agente Dados"],
                domain_id=self.domain_id,
                action_id="create_sourcing_agent",
            )

        company_id = context.tenant_id
        job_id = params.get("job_id")
        talent_pool_id = params.get("talent_pool_id")
        sector_template = params.get("sector_template")

        try:
            orchestrator = SourcingAgentOrchestrator()
            async for db in get_db():
                result = await orchestrator.create_agent(
                    company_id=company_id,
                    agent_name=agent_name,
                    job_id=job_id,
                    talent_pool_id=talent_pool_id,
                    agent_template_id=sector_template,
                    db=db,
                )
                break

            agent_id = result.get("agent_id", "")
            status = result.get("status", "active")

            return DomainResponse.success_response(
                message=f"Agente {agent_name} criado com sucesso! Status: {status}. Acesse o Agent Studio para calibrar e acompanhar.",
                data={
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "status": status,
                    "navigation_hint": {"page": "Agent Studio", "entity_id": agent_id},
                },
                metadata={
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "status": status,
                    "navigation_hint": {"page": "Agent Studio", "entity_id": agent_id},
                },
                domain_id=self.domain_id,
                action_id="create_sourcing_agent",
                suggestions=[
                    "Calibrar agente agora",
                    "Ver status do agente",
                    "Listar todos os agentes",
                ],
            )
        except Exception as exc:
            logger.exception("Failed to create sourcing agent: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao criar agente: {exc}",
                domain_id=self.domain_id,
                action_id="create_sourcing_agent",
            )
