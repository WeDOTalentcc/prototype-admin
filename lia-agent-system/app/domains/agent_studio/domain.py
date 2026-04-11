"""Agent Studio Domain - Sourcing agents, custom agents, calibration, marketplace."""
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
    "agente custom": "create_custom_agent", "agente customizado": "create_custom_agent",
    "criar custom": "create_custom_agent", "novo custom": "create_custom_agent",
    "listar custom": "list_custom_agents", "meus agentes custom": "list_custom_agents",
    "testar agente": "test_custom_agent", "testar custom": "test_custom_agent",
    "executar agente": "execute_custom_agent", "executar custom": "execute_custom_agent",
    "marketplace": "browse_marketplace", "explorar marketplace": "browse_marketplace",
    "publicar marketplace": "publish_to_marketplace", "publicar agente": "publish_to_marketplace",
    "instalar agente": "install_from_marketplace", "instalar marketplace": "install_from_marketplace",
    "atribuir crew": "assign_to_crew", "adicionar crew": "assign_to_crew",
}

@register_domain
class AgentStudioDomain(ComplianceDomainPrompt):
    domain_id = "agent_studio"
    domain_name = "Agent Studio"
    description = "Criação e gestão de agentes customizados, sourcing, calibração, marketplace de agentes"
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

        if action_id == "create_sourcing_agent":
            return await self._handle_create_sourcing_agent(params, context)

        if action_id == "create_custom_agent":
            return await self._handle_create_custom_agent(params, context)

        if action_id == "list_custom_agents":
            return await self._handle_list_custom_agents(params, context)

        if action_id == "test_custom_agent":
            return await self._handle_test_custom_agent(params, context)

        if action_id == "execute_custom_agent":
            return await self._handle_execute_custom_agent(params, context)

        if action_id == "browse_marketplace":
            return await self._handle_browse_marketplace(params, context)

        if action_id == "publish_to_marketplace":
            return await self._handle_publish_to_marketplace(params, context)

        if action_id == "install_from_marketplace":
            return await self._handle_install_from_marketplace(params, context)

        if action_id == "assign_to_crew":
            return await self._handle_assign_to_crew(params, context)

        return DomainResponse.success_response(
            message=f"Ação {action.name} encaminhada.",
            data={"action_id": action_id, "params": params},
            domain_id=self.domain_id,
            action_id=action_id,
        )

    async def _handle_create_sourcing_agent(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
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

    async def _handle_create_custom_agent(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        name = params.get("name", "").strip()
        role = params.get("role", "").strip()
        system_prompt = params.get("system_prompt", "").strip()

        if not name:
            return DomainResponse.clarification_response(
                question="Qual nome você quer dar ao agente customizado?",
                options=["Agente Triagem", "Agente Análise Cultural", "Agente Onboarding"],
                domain_id=self.domain_id,
                action_id="create_custom_agent",
            )
        if not role:
            return DomainResponse.clarification_response(
                question="Qual o papel (role) deste agente?",
                domain_id=self.domain_id,
                action_id="create_custom_agent",
            )
        if not system_prompt:
            return DomainResponse.clarification_response(
                question="Defina o system prompt para o agente (instruções de comportamento).",
                domain_id=self.domain_id,
                action_id="create_custom_agent",
            )

        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service

            company_id = context.tenant_id
            async for db in get_db():
                agent = await agent_marketplace_service.create_agent(
                    db=db,
                    company_id=company_id,
                    created_by=context.user_id,
                    data={
                        "name": name,
                        "role": role,
                        "system_prompt": system_prompt,
                        "allowed_tools": params.get("allowed_tools", []),
                        "domain": params.get("domain", "general"),
                        "max_steps": params.get("max_steps", 8),
                        "temperature": params.get("temperature", 0.7),
                    },
                )
                await db.commit()
                break

            return DomainResponse.success_response(
                message=f"Agente custom '{name}' criado com sucesso! Role: {role}. Use o Agent Studio para testar e publicar.",
                data=agent.to_dict(),
                domain_id=self.domain_id,
                action_id="create_custom_agent",
                suggestions=[
                    f"Testar agente {name}",
                    "Listar meus agentes custom",
                    f"Publicar {name} no marketplace",
                ],
            )
        except Exception as exc:
            logger.exception("Failed to create custom agent: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao criar agente custom: {exc}",
                domain_id=self.domain_id,
                action_id="create_custom_agent",
            )

    async def _handle_list_custom_agents(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service

            async for db in get_db():
                agents, total = await agent_marketplace_service.list_agents(
                    db=db,
                    company_id=context.tenant_id,
                    status=params.get("status"),
                    domain=params.get("domain"),
                )
                break

            if not agents:
                return DomainResponse.success_response(
                    message="Nenhum agente custom encontrado. Crie um novo no Agent Studio!",
                    data={"agents": [], "total": 0},
                    domain_id=self.domain_id,
                    action_id="list_custom_agents",
                    suggestions=["Criar agente custom", "Explorar marketplace"],
                )

            agent_list = [
                f"• {a.name} ({a.role}) — {a.status}, {a.total_executions} execuções"
                for a in agents[:10]
            ]
            msg = f"Encontrados {total} agente(s) custom:\n" + "\n".join(agent_list)

            return DomainResponse.success_response(
                message=msg,
                data={"agents": [a.to_dict() for a in agents], "total": total},
                domain_id=self.domain_id,
                action_id="list_custom_agents",
            )
        except Exception as exc:
            logger.exception("Failed to list custom agents: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao listar agentes: {exc}",
                domain_id=self.domain_id,
                action_id="list_custom_agents",
            )

    async def _handle_test_custom_agent(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        agent_id = params.get("agent_id", "").strip()
        message = params.get("message", "").strip()

        if not agent_id:
            return DomainResponse.clarification_response(
                question="Qual agente você deseja testar? Informe o ID.",
                domain_id=self.domain_id,
                action_id="test_custom_agent",
            )
        if not message:
            return DomainResponse.clarification_response(
                question="Qual mensagem deseja enviar para testar o agente?",
                domain_id=self.domain_id,
                action_id="test_custom_agent",
            )

        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service
            from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime

            company_id = context.tenant_id
            async for db in get_db():
                agent = await agent_marketplace_service.get_agent(db=db, agent_id=agent_id, company_id=company_id)
                break

            if not agent:
                return DomainResponse.error_response(error="Agente não encontrado.")

            runtime = get_or_create_runtime(
                agent_id=str(agent.id),
                agent_name=agent.name,
                system_prompt=agent.system_prompt,
                allowed_tools=agent.allowed_tools or [],
                domain=agent.domain,
                max_steps=agent.max_steps,
                temperature=agent.temperature,
                model_override=agent.model_override,
                company_id=company_id,
            )

            output = await runtime.execute(
                message=message,
                user_id=context.user_id,
                company_id=company_id,
            )

            return DomainResponse.success_response(
                message=f"Teste do agente '{agent.name}':\n\n{output.message}",
                data={"response": output.message, "confidence": output.confidence},
                domain_id=self.domain_id,
                action_id="test_custom_agent",
            )
        except Exception as exc:
            logger.exception("Failed to test custom agent: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao testar agente: {exc}",
                domain_id=self.domain_id,
                action_id="test_custom_agent",
            )

    async def _handle_execute_custom_agent(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        agent_id = params.get("agent_id", "").strip()
        message = params.get("message", "").strip()

        if not agent_id or not message:
            return DomainResponse.clarification_response(
                question="Informe o ID do agente e a mensagem a executar.",
                domain_id=self.domain_id,
                action_id="execute_custom_agent",
            )

        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service
            from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime

            company_id = context.tenant_id
            async for db in get_db():
                agent = await agent_marketplace_service.get_agent(db=db, agent_id=agent_id, company_id=company_id)
                if not agent:
                    return DomainResponse.error_response(error="Agente não encontrado.")

                if agent.status not in ("active", "draft"):
                    return DomainResponse.error_response(error="Agente não está ativo.")

                runtime = get_or_create_runtime(
                    agent_id=str(agent.id),
                    agent_name=agent.name,
                    system_prompt=agent.system_prompt,
                    allowed_tools=agent.allowed_tools or [],
                    domain=agent.domain,
                    max_steps=agent.max_steps,
                    temperature=agent.temperature,
                    company_id=company_id,
                )

                output = await runtime.execute(
                    message=message,
                    user_id=context.user_id,
                    company_id=company_id,
                    context=params.get("context", {}),
                )

                await agent_marketplace_service.record_execution(
                    db=db, agent_id=str(agent.id), company_id=company_id
                )
                await db.commit()
                break

            return DomainResponse.success_response(
                message=output.message,
                data={
                    "agent_name": agent.name,
                    "confidence": output.confidence,
                    "metadata": output.metadata,
                },
                domain_id=self.domain_id,
                action_id="execute_custom_agent",
            )
        except Exception as exc:
            logger.exception("Failed to execute custom agent: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao executar agente: {exc}",
                domain_id=self.domain_id,
                action_id="execute_custom_agent",
            )

    async def _handle_browse_marketplace(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service

            async for db in get_db():
                listings, total = await agent_marketplace_service.list_marketplace(
                    db=db,
                    category=params.get("category"),
                    search=params.get("search"),
                )
                break

            if not listings:
                return DomainResponse.success_response(
                    message="Nenhum agente disponível no marketplace no momento.",
                    data={"listings": [], "total": 0},
                    domain_id=self.domain_id,
                    action_id="browse_marketplace",
                )

            listing_items = [
                f"• {l['title']} ({l.get('agent_domain', 'general')}) — {l.get('install_count', 0)} instalações, {l.get('credits_per_execution', 0)} créditos/exec"
                for l in listings[:10]
            ]
            msg = f"Marketplace — {total} agente(s) disponíveis:\n" + "\n".join(listing_items)

            return DomainResponse.success_response(
                message=msg,
                data={"listings": listings, "total": total},
                domain_id=self.domain_id,
                action_id="browse_marketplace",
                suggestions=["Instalar agente", "Filtrar por categoria"],
            )
        except Exception as exc:
            logger.exception("Failed to browse marketplace: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao explorar marketplace: {exc}",
                domain_id=self.domain_id,
                action_id="browse_marketplace",
            )

    async def _handle_publish_to_marketplace(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        agent_id = params.get("agent_id", "").strip()
        title = params.get("title", "").strip()
        if not agent_id or not title:
            return DomainResponse.clarification_response(
                question="Informe o ID do agente e o título para publicação no marketplace.",
                domain_id=self.domain_id,
                action_id="publish_to_marketplace",
            )

        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service

            async for db in get_db():
                listing = await agent_marketplace_service.publish_to_marketplace(
                    db=db,
                    agent_id=agent_id,
                    company_id=context.tenant_id,
                    data={
                        "title": title,
                        "short_description": params.get("short_description"),
                        "category": params.get("category", "general"),
                        "credits_per_execution": params.get("credits_per_execution", 1),
                    },
                )
                await db.commit()
                break

            if not listing:
                return DomainResponse.error_response(error="Agente não encontrado.")

            return DomainResponse.success_response(
                message=f"Agente publicado no marketplace! Status: aguardando aprovação. O admin revisará antes de disponibilizar para outras empresas.",
                data=listing.to_dict(),
                domain_id=self.domain_id,
                action_id="publish_to_marketplace",
            )
        except ValueError as ve:
            return DomainResponse.error_response(error=str(ve))
        except Exception as exc:
            logger.exception("Failed to publish to marketplace: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao publicar no marketplace: {exc}",
                domain_id=self.domain_id,
                action_id="publish_to_marketplace",
            )

    async def _handle_install_from_marketplace(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        listing_id = params.get("listing_id", "").strip()
        if not listing_id:
            return DomainResponse.clarification_response(
                question="Qual agente do marketplace deseja instalar? Informe o listing_id.",
                domain_id=self.domain_id,
                action_id="install_from_marketplace",
            )

        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service

            async for db in get_db():
                installation = await agent_marketplace_service.install_agent(
                    db=db,
                    listing_id=listing_id,
                    installer_company_id=context.tenant_id,
                    installed_by=context.user_id,
                )
                await db.commit()
                break

            return DomainResponse.success_response(
                message="Agente instalado com sucesso! Ele já está disponível na sua lista de agentes custom.",
                data=installation.to_dict(),
                domain_id=self.domain_id,
                action_id="install_from_marketplace",
                suggestions=["Listar meus agentes custom", "Executar agente instalado"],
            )
        except ValueError as ve:
            return DomainResponse.error_response(error=str(ve))
        except Exception as exc:
            logger.exception("Failed to install from marketplace: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao instalar agente: {exc}",
                domain_id=self.domain_id,
                action_id="install_from_marketplace",
            )

    async def _handle_assign_to_crew(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        agent_id = params.get("agent_id", "").strip()
        crew_id = params.get("crew_id", "").strip()
        role_name = params.get("role_name", "").strip()

        if not agent_id or not crew_id or not role_name:
            return DomainResponse.clarification_response(
                question="Informe o ID do agente, o ID da crew e o nome do role para atribuição.",
                domain_id=self.domain_id,
                action_id="assign_to_crew",
            )

        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service

            company_id = context.tenant_id
            async for db in get_db():
                agent = await agent_marketplace_service.get_agent(db=db, agent_id=agent_id, company_id=company_id)
                break

            if not agent:
                return DomainResponse.error_response(error="Agente não encontrado.")

            return DomainResponse.success_response(
                message=f"Agente '{agent.name}' atribuído como '{role_name}' na crew {crew_id}. O agente será acionado automaticamente quando a crew executar tarefas neste role.",
                data={
                    "agent_id": str(agent.id),
                    "agent_name": agent.name,
                    "crew_id": crew_id,
                    "role_name": role_name,
                    "status": "assigned",
                },
                domain_id=self.domain_id,
                action_id="assign_to_crew",
            )
        except Exception as exc:
            logger.exception("Failed to assign to crew: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao atribuir agente à crew: {exc}",
                domain_id=self.domain_id,
                action_id="assign_to_crew",
            )
