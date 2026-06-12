from pathlib import Path
"""Agent Studio Domain - Sourcing agents, custom agents, calibration, marketplace."""
import logging
import yaml as _yaml_imp  # Fase 5
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

def _normalize_calibration_candidate(c: dict) -> dict:
    """P2.6-BE: Normaliza shape de candidato para CalibrationResultCard.

    Suporta multiplos shapes (sourcing, db-fallback, custom agents).
    score=0.0 padrao: candidatos de calibracao ainda nao foram pontuados;
    o recrutador avalia via aprovacao/rejeicao.
    """
    return {
        "id": str(c.get("id") or c.get("candidate_id") or ""),
        "name": c.get("name") or c.get("full_name") or "Candidato",
        "score": float(
            c.get("score")
            or c.get("calibration_score")
            or c.get("match_score")
            or c.get("ai_score")
            or 0.0
        ),
        "stage": c.get("stage") or c.get("current_stage") or c.get("current_title"),
    }



# Fase 5: _KEYWORD_ACTION_MAP loaded from capabilities.yaml (LIA-I05)
_capabilities_yaml_path = Path(__file__).parent / 'config' / 'capabilities.yaml'
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get('intent_keywords', {})
    if _capabilities_yaml_path.exists()
    else {}
)

@register_domain
class AgentStudioDomain(ComplianceDomainPrompt):
    domain_id = "agent_studio"
    domain_name = "Agent Studio"
    description = "Criação e gestão de agentes customizados, sourcing, calibração, marketplace de agentes"
    _compliance_config = {"high_impact": False, "fairness_action_type": "sourcing"}

    def get_allowed_actions(self):
        from app.domains.agent_studio.actions import AGENT_STUDIO_ACTIONS
        return AGENT_STUDIO_ACTIONS

    async def process_intent(self, query, context):
        q = query.lower()

        # LIA-I01: Use KeywordIntentMatcher for info/action disambiguation
        try:
            from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
            _matcher = KeywordIntentMatcher()
            if _matcher.is_info_query(query) and any(kw in q for kw in ("agent studio", "agente", "studio")):
                return IntentResult(
                    intent_id="agent_studio.explain_agent_studio",
                    action_id="explain_agent_studio",
                    confidence=0.9,
                    extracted_params={"raw_query": query},
                    reasoning="Info query about Agent Studio detected via LIA-I01",
                )
        except Exception:
            pass

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

        handler_map = {
            "create_sourcing_agent": self._handle_create_sourcing_agent,
            "calibrate_agent": self._handle_calibrate_agent,
            "get_agent_status": self._handle_get_agent_status,
            "run_multi_strategy": self._handle_run_multi_strategy,
            "create_custom_agent": self._handle_create_custom_agent,
            "list_custom_agents": self._handle_list_custom_agents,
            "test_custom_agent": self._handle_test_custom_agent,
            "execute_custom_agent": self._handle_execute_custom_agent,
            "browse_marketplace": self._handle_browse_marketplace,
            "publish_to_marketplace": self._handle_publish_to_marketplace,
            "install_from_marketplace": self._handle_install_from_marketplace,
            "assign_to_crew": self._handle_assign_to_crew,
            "get_studio_consumption": self._handle_get_studio_consumption,
            "deactivate_agent": self._handle_deactivate_agent,
            "uninstall_agent": self._handle_uninstall_agent,
            "explain_agent_studio": self._handle_explain_agent_studio,
            "list_agents": self._handle_list_agents,
        }

        # Canonical truth (Sprint 7B-3b Part 3a):
        # Reads de status + deactivate (branch sourcing) usam CustomAgent + category='sourcing'.
        # custom_agent branch: select(CustomAgent).where(CustomAgent.id, CustomAgent.company_id).
        # sourcing branch: select(CustomAgent).where(CustomAgent.id, CustomAgent.category, CustomAgent.company_id).
        # Aplica a: _handle_get_agent_status, _handle_deactivate_agent (sourcing branch).
        # Frontend Part 2 v2 (cc622d4c9) ja passa custom_agent.id direto — OR shim removido.

        handler = handler_map.get(action_id)
        if handler:
            return await handler(params, context)

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
        from app.services.studio_metering_service import studio_metering_service

        agent_name = params.get("agent_name", "").strip()
        if not agent_name:
            return DomainResponse.clarification_response(
                question="Qual nome você quer dar ao agente de sourcing?",
                options=["Agente Tech SR", "Agente Vendas", "Agente Dados"],
                domain_id=self.domain_id,
                action_id="create_sourcing_agent",
            )

        company_id = context.tenant_id

        try:
            async for db in get_db():
                allowed, msg = await studio_metering_service.check_and_increment_quota(db, company_id, "sourcing_agent")
                if not allowed:
                    return DomainResponse.error_response(error=msg, domain_id=self.domain_id, action_id="create_sourcing_agent")

                orchestrator = SourcingAgentOrchestrator()
                result = await orchestrator.create_agent(
                    company_id=company_id,
                    agent_name=agent_name,
                    job_id=params.get("job_id"),
                    talent_pool_id=params.get("talent_pool_id"),
                    agent_template_id=params.get("sector_template"),
                    db=db,
                )
                await studio_metering_service.record_studio_usage(
                    db=db, company_id=company_id, agent_type="sourcing_agent",
                    operation="create_sourcing_agent", studio_agent_id=result.get("agent_id"),
                    user_id=context.user_id,
                )
                await db.commit()
                break

            agent_id = result.get("agent_id", "")
            return DomainResponse.success_response(
                message=f"Agente {agent_name} criado com sucesso! Status: active. Acesse o Agent Studio para calibrar e acompanhar.",
                data={
                    "agent_id": agent_id, "agent_name": agent_name,
                    "status": "active",
                    "navigation_hint": {"page": "Agent Studio", "entity_id": agent_id},
                },
                metadata={"agent_id": agent_id, "agent_name": agent_name, "status": "active",
                           "navigation_hint": {"page": "Agent Studio", "entity_id": agent_id}},
                domain_id=self.domain_id,
                action_id="create_sourcing_agent",
                suggestions=["Calibrar agente agora", "Ver status do agente", "Listar todos os agentes"],
            )
        except Exception as exc:
            logger.exception("Failed to create sourcing agent: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao criar agente: {exc}", domain_id=self.domain_id, action_id="create_sourcing_agent")

    async def _handle_calibrate_agent(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        agent_id = params.get("agent_id", "").strip()
        if not agent_id:
            return DomainResponse.clarification_response(
                question="Qual agente deseja calibrar? Informe o agent_id.",
                domain_id=self.domain_id,
                action_id="calibrate_agent",
            )

        try:
            from app.core.database import get_db
            from app.services.sourcing_agent_orchestrator import SourcingAgentOrchestrator
            from app.services.studio_metering_service import studio_metering_service

            company_id = context.tenant_id
            orchestrator = SourcingAgentOrchestrator()

            async for db in get_db():
                candidates = await orchestrator.get_calibration_candidates(
                    agent_id=agent_id, limit=10, db=db,
                )

                await studio_metering_service.record_studio_usage(
                    db=db, company_id=company_id, agent_type="sourcing_agent",
                    operation="calibrate_agent", studio_agent_id=agent_id,
                    user_id=context.user_id,
                    profiles_processed=len(candidates) if candidates else 0,
                )
                await db.commit()
                break

            if not candidates:
                return DomainResponse.success_response(
                    message="Nenhum candidato encontrado para calibração. Verifique a estratégia de busca do agente.",
                    data={"candidates": [], "total": 0},
                    domain_id=self.domain_id,
                    action_id="calibrate_agent",
                )

            candidate_list = [
                f"• {c.get('name', 'N/A')} — {c.get('role_name', 'N/A')}"
                for c in candidates[:5]
            ]
            msg = (
                f"Calibração iniciada! {len(candidates)} candidatos selecionados para avaliação.\n\n"
                f"Primeiros perfis:\n" + "\n".join(candidate_list) +
                "\n\nAvalie cada perfil com 👍 (aprovar) ou 👎 (rejeitar) para calibrar o agente."
            )

            # P2.6-BE: emitir response_blocks calibration_result p/ CalibrationResultCard
            _candidates_normalized = [
                _normalize_calibration_candidate(c) for c in candidates[:20]
            ]
            _scores = [c["score"] for c in _candidates_normalized if c["score"] > 0]
            _average_score = round(sum(_scores) / len(_scores), 1) if _scores else 0.0

            return DomainResponse.success_response(
                message=msg,
                data={
                    "candidates": candidates,
                    "total": len(candidates),
                    "agent_id": agent_id,
                    "response_blocks": [
                        {
                            "type": "calibration_result",
                            "data": {
                                "candidates": _candidates_normalized,
                                "average_score": _average_score,
                            },
                        }
                    ],
                },
                domain_id=self.domain_id,
                action_id="calibrate_agent",
                suggestions=["Aprovar candidato", "Rejeitar candidato", "Ver estratégia do agente"],
            )
        except Exception as exc:
            logger.exception("Failed to calibrate agent: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao calibrar agente: {exc}", domain_id=self.domain_id, action_id="calibrate_agent")

    async def _handle_get_agent_status(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        agent_id = params.get("agent_id", "").strip()
        if not agent_id:
            return DomainResponse.clarification_response(
                question="Qual agente deseja consultar? Informe o agent_id.",
                domain_id=self.domain_id,
                action_id="get_agent_status",
            )

        try:
            from app.core.database import get_db
            from lia_models.custom_agent import CustomAgent
            from sqlalchemy import select

            company_id = context.tenant_id

            # Sprint 7B-3b Part 3a: OR shim removed — frontend Part 2 v2 swap completou.
            async for db in get_db():
                result = await db.execute(
                    select(CustomAgent).where(
                        CustomAgent.id == agent_id,
                        CustomAgent.category == "sourcing",
                        CustomAgent.company_id == company_id,
                    )
                )
                agent = result.scalar_one_or_none()
                break

            if not agent:
                return DomainResponse.error_response(
                    error="Agente não encontrado.",
                    domain_id=self.domain_id,
                    action_id="get_agent_status",
                )

            strategy = agent.search_strategy or {}
            skills = ", ".join(strategy.get("required_skills", [])) or "não definidas"
            exclusions = ", ".join(strategy.get("exclusions", [])) or "nenhuma"

            metrics = agent.runtime_metrics or {}
            msg = (
                f"📊 Status do Agente '{agent.name}':\n\n"
                f"**Status:** {agent.status}\n"
                f"**Versão de calibração:** v{int(metrics.get('calibration_v', 0))}\n"
                f"**Perfis visualizados:** {int(metrics.get('profiles_viewed', 0))}\n"
                f"**Aprovados:** {int(metrics.get('profiles_approved', 0))}\n"
                f"**Rejeitados:** {int(metrics.get('profiles_rejected', 0))}\n"
                f"**Emails enviados:** {int(metrics.get('emails_sent', 0))}\n\n"
                f"**Skills buscadas:** {skills}\n"
                f"**Exclusões:** {exclusions}"
            )

            return DomainResponse.success_response(
                message=msg,
                data={
                    "agent_id": str(agent.id),
                    "agent_name": agent.agent_name,
                    "status": agent.status,
                    "calibration_v": agent.calibration_v,
                    "profiles_viewed": agent.profiles_viewed or 0,
                    "profiles_approved": agent.profiles_approved or 0,
                    "profiles_rejected": agent.profiles_rejected or 0,
                    "emails_sent": agent.emails_sent or 0,
                    "search_strategy": strategy,
                },
                domain_id=self.domain_id,
                action_id="get_agent_status",
                suggestions=["Calibrar agente", "Pausar agente", "Busca multi-estratégia"],
            )
        except Exception as exc:
            logger.exception("Failed to get agent status: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao consultar status: {exc}", domain_id=self.domain_id, action_id="get_agent_status")

    async def _handle_run_multi_strategy(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        job_title = params.get("job_title", "").strip()
        skills = params.get("skills", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",")]

        if not job_title:
            return DomainResponse.clarification_response(
                question="Qual cargo deseja buscar com multi-estratégia?",
                domain_id=self.domain_id,
                action_id="run_multi_strategy",
            )

        try:
            import asyncio
            from app.core.database import get_db
            from app.services.studio_metering_service import studio_metering_service

            company_id = context.tenant_id
            location = params.get("location", "")
            seniority = params.get("seniority", "")

            strategies = [
                {"name": "skills_match", "query": f"Candidatos com {', '.join(skills)} para {job_title}", "weight": 0.3},
                {"name": "semantic_search", "query": f"Profissional ideal para {job_title} {seniority} {location}".strip(), "weight": 0.3},
                {"name": "similar_profiles", "query": f"Perfis similares a {job_title} com experiência em {', '.join(skills[:3])}", "weight": 0.2},
                {"name": "passive_candidates", "query": f"Talentos passivos para {job_title} disponíveis em {location or 'qualquer local'}", "weight": 0.2},
            ]

            all_results = {}
            try:
                from app.domains.sourcing.agents.sourcing_search_agent import SourcingSearchAgent
                from lia_agents_core.agent_interface import AgentInput

                search_agent = SourcingSearchAgent()

                async def _run_strategy(strategy: dict) -> tuple[str, list]:
                    try:
                        output = await search_agent.process(AgentInput(
                            message=strategy["query"],
                            context={"company_id": company_id, "limit": 10},
                        ))
                        return strategy["name"], output.data.get("candidates", [])[:10]
                    except Exception as e:
                        logger.warning("[MultiStrategy] Strategy %s failed: %s", strategy["name"], e)
                        return strategy["name"], []

                tasks = [_run_strategy(s) for s in strategies]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for r in results:
                    if isinstance(r, tuple):
                        all_results[r[0]] = r[1]
            except Exception as e:
                logger.warning("[MultiStrategy] Search agent unavailable: %s", e)

            total_found = sum(len(v) for v in all_results.values())

            async for db in get_db():
                await studio_metering_service.record_studio_usage(
                    db=db, company_id=company_id, agent_type="sourcing_agent",
                    operation="run_multi_strategy", user_id=context.user_id,
                    extra_data={"strategies": len(strategies), "total_found": total_found},
                    profiles_processed=total_found,
                )
                await db.commit()
                break

            strategy_summary = []
            for s in strategies:
                count = len(all_results.get(s["name"], []))
                strategy_summary.append(f"• {s['name']}: {count} candidatos encontrados")

            msg = (
                f"🔍 Busca multi-estratégia para '{job_title}' concluída!\n\n"
                f"**4 estratégias executadas em paralelo:**\n" +
                "\n".join(strategy_summary) +
                f"\n\n**Total de candidatos encontrados:** {total_found}"
            )

            return DomainResponse.success_response(
                message=msg,
                data={
                    "job_title": job_title,
                    "strategies_executed": len(strategies),
                    "total_candidates": total_found,
                    "results_by_strategy": {k: len(v) for k, v in all_results.items()},
                    "candidates": all_results,
                },
                domain_id=self.domain_id,
                action_id="run_multi_strategy",
                suggestions=["Criar agente de sourcing", "Ver detalhes dos candidatos"],
            )
        except Exception as exc:
            logger.exception("Failed to run multi-strategy: %s", exc)
            return DomainResponse.error_response(error=f"Erro na busca multi-estratégia: {exc}", domain_id=self.domain_id, action_id="run_multi_strategy")

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
                domain_id=self.domain_id, action_id="create_custom_agent",
            )
        if not role:
            return DomainResponse.clarification_response(
                question="Qual o papel (role) deste agente?",
                domain_id=self.domain_id, action_id="create_custom_agent",
            )
        if not system_prompt:
            return DomainResponse.clarification_response(
                question="Defina o system prompt para o agente (instruções de comportamento).",
                domain_id=self.domain_id, action_id="create_custom_agent",
            )

        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service
            from app.services.studio_metering_service import studio_metering_service

            company_id = context.tenant_id
            async for db in get_db():
                allowed, msg = await studio_metering_service.check_and_increment_quota(db, company_id, "custom_agent")
                if not allowed:
                    return DomainResponse.error_response(error=msg, domain_id=self.domain_id, action_id="create_custom_agent")

                agent = await agent_marketplace_service.create_agent(
                    db=db, company_id=company_id, created_by=context.user_id,
                    data={
                        "name": name, "role": role, "system_prompt": system_prompt,
                        "allowed_tools": params.get("allowed_tools", []),
                        "domain": params.get("domain", "general"),
                        "max_steps": params.get("max_steps", 8),
                        "temperature": params.get("temperature", 0.7),
                    },
                )
                await studio_metering_service.record_studio_usage(
                    db=db, company_id=company_id, agent_type="custom_agent",
                    operation="create_custom_agent", studio_agent_id=str(agent.id),
                    user_id=context.user_id,
                )
                await db.commit()
                break

            return DomainResponse.success_response(
                message=f"Agente custom '{name}' criado com sucesso! Role: {role}. Use o Agent Studio para testar e publicar.",
                data=agent.to_dict(),
                domain_id=self.domain_id, action_id="create_custom_agent",
                suggestions=[f"Testar agente {name}", "Listar meus agentes custom", f"Publicar {name} no marketplace"],
            )
        except Exception as exc:
            logger.exception("Failed to create custom agent: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao criar agente custom: {exc}", domain_id=self.domain_id, action_id="create_custom_agent")

    async def _handle_list_custom_agents(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service

            async for db in get_db():
                agents, total = await agent_marketplace_service.list_agents(
                    db=db, company_id=context.tenant_id,
                    status=params.get("status"), domain=params.get("domain"),
                )
                break

            if not agents:
                return DomainResponse.success_response(
                    message="Nenhum agente custom encontrado. Crie um novo no Agent Studio!",
                    data={"agents": [], "total": 0},
                    domain_id=self.domain_id, action_id="list_custom_agents",
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
                domain_id=self.domain_id, action_id="list_custom_agents",
            )
        except Exception as exc:
            logger.exception("Failed to list custom agents: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao listar agentes: {exc}", domain_id=self.domain_id, action_id="list_custom_agents")

    async def _handle_test_custom_agent(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        agent_id = params.get("agent_id", "").strip()
        message = params.get("message", "").strip()

        if not agent_id:
            return DomainResponse.clarification_response(
                question="Qual agente você deseja testar? Informe o ID.",
                domain_id=self.domain_id, action_id="test_custom_agent",
            )
        if not message:
            return DomainResponse.clarification_response(
                question="Qual mensagem deseja enviar para testar o agente?",
                domain_id=self.domain_id, action_id="test_custom_agent",
            )

        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service
            from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime
            from app.services.studio_metering_service import studio_metering_service

            company_id = context.tenant_id
            async for db in get_db():
                agent = await agent_marketplace_service.get_agent(db=db, agent_id=agent_id, company_id=company_id)
                break

            if not agent:
                return DomainResponse.error_response(error="Agente não encontrado.")

            runtime = get_or_create_runtime(
                agent_id=str(agent.id), agent_name=agent.name,
                system_prompt=agent.system_prompt,
                allowed_tools=agent.allowed_tools or [],
                domain=agent.domain, max_steps=agent.max_steps,
                temperature=agent.temperature, model_override=agent.model_override,
                company_id=company_id,
            )

            output = await runtime.execute(message=message, user_id=context.user_id, company_id=company_id)

            async for db in get_db():
                await studio_metering_service.record_studio_usage(
                    db=db, company_id=company_id, agent_type="custom_agent",
                    operation="test_custom_agent", studio_agent_id=agent_id,
                    user_id=context.user_id,
                )
                await db.commit()
                break

            return DomainResponse.success_response(
                message=f"Teste do agente '{agent.name}':\n\n{output.message}",
                data={"response": output.message, "confidence": output.confidence},
                domain_id=self.domain_id, action_id="test_custom_agent",
            )
        except Exception as exc:
            logger.exception("Failed to test custom agent: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao testar agente: {exc}", domain_id=self.domain_id, action_id="test_custom_agent")

    async def _handle_execute_custom_agent(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        agent_id = params.get("agent_id", "").strip()
        message = params.get("message", "").strip()

        if not agent_id or not message:
            return DomainResponse.clarification_response(
                question="Informe o ID do agente e a mensagem a executar.",
                domain_id=self.domain_id, action_id="execute_custom_agent",
            )

        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service
            from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime
            from app.services.studio_metering_service import studio_metering_service

            company_id = context.tenant_id
            async for db in get_db():
                agent = await agent_marketplace_service.get_agent(db=db, agent_id=agent_id, company_id=company_id)
                if not agent:
                    return DomainResponse.error_response(error="Agente não encontrado.")
                if agent.status not in ("active", "draft"):
                    return DomainResponse.error_response(error="Agente não está ativo.")

                runtime = get_or_create_runtime(
                    agent_id=str(agent.id), agent_name=agent.name,
                    system_prompt=agent.system_prompt,
                    allowed_tools=agent.allowed_tools or [],
                    domain=agent.domain, max_steps=agent.max_steps,
                    temperature=agent.temperature, company_id=company_id,
                )

                output = await runtime.execute(
                    message=message, user_id=context.user_id,
                    company_id=company_id, context=params.get("context", {}),
                )

                await agent_marketplace_service.record_execution(db=db, agent_id=str(agent.id), company_id=company_id)
                await studio_metering_service.record_studio_usage(
                    db=db, company_id=company_id, agent_type="custom_agent",
                    operation="execute_custom_agent", studio_agent_id=str(agent.id),
                    user_id=context.user_id,
                )
                await db.commit()
                break

            return DomainResponse.success_response(
                message=output.message,
                data={"agent_name": agent.name, "confidence": output.confidence, "metadata": output.metadata},
                domain_id=self.domain_id, action_id="execute_custom_agent",
            )
        except Exception as exc:
            logger.exception("Failed to execute custom agent: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao executar agente: {exc}", domain_id=self.domain_id, action_id="execute_custom_agent")

    async def _handle_browse_marketplace(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service

            async for db in get_db():
                listings, total = await agent_marketplace_service.list_marketplace(
                    db=db, category=params.get("category"), search=params.get("search"),
                )
                break

            if not listings:
                return DomainResponse.success_response(
                    message="Nenhum agente disponível no marketplace no momento.",
                    data={"listings": [], "total": 0},
                    domain_id=self.domain_id, action_id="browse_marketplace",
                )

            listing_items = [
                f"• {l['title']} ({l.get('agent_domain', 'general')}) — {l.get('install_count', 0)} instalações, {l.get('credits_per_execution', 0)} créditos/exec"
                for l in listings[:10]
            ]
            msg = f"Marketplace — {total} agente(s) disponíveis:\n" + "\n".join(listing_items)

            return DomainResponse.success_response(
                message=msg,
                data={"listings": listings, "total": total},
                domain_id=self.domain_id, action_id="browse_marketplace",
                suggestions=["Instalar agente", "Filtrar por categoria"],
            )
        except Exception as exc:
            logger.exception("Failed to browse marketplace: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao explorar marketplace: {exc}", domain_id=self.domain_id, action_id="browse_marketplace")

    async def _handle_publish_to_marketplace(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        agent_id = params.get("agent_id", "").strip()
        title = params.get("title", "").strip()
        if not agent_id or not title:
            return DomainResponse.clarification_response(
                question="Informe o ID do agente e o título para publicação no marketplace.",
                domain_id=self.domain_id, action_id="publish_to_marketplace",
            )

        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service

            async for db in get_db():
                listing = await agent_marketplace_service.publish_to_marketplace(
                    db=db, agent_id=agent_id, company_id=context.tenant_id,
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
                message="Agente publicado no marketplace! Status: aguardando aprovação. O admin revisará antes de disponibilizar para outras empresas.",
                data=listing.to_dict(),
                domain_id=self.domain_id, action_id="publish_to_marketplace",
            )
        except ValueError as ve:
            return DomainResponse.error_response(error=str(ve))
        except Exception as exc:
            logger.exception("Failed to publish to marketplace: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao publicar no marketplace: {exc}", domain_id=self.domain_id, action_id="publish_to_marketplace")

    async def _handle_install_from_marketplace(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        listing_id = params.get("listing_id", "").strip()
        if not listing_id:
            return DomainResponse.clarification_response(
                question="Qual agente do marketplace deseja instalar? Informe o listing_id.",
                domain_id=self.domain_id, action_id="install_from_marketplace",
            )

        try:
            from app.core.database import get_db
            from app.services.agent_marketplace_service import agent_marketplace_service
            from app.services.studio_metering_service import studio_metering_service

            company_id = context.tenant_id
            async for db in get_db():
                allowed, msg = await studio_metering_service.check_and_increment_quota(db, company_id, "custom_agent")
                if not allowed:
                    return DomainResponse.error_response(error=msg, domain_id=self.domain_id, action_id="install_from_marketplace")

                installation = await agent_marketplace_service.install_agent(
                    db=db, listing_id=listing_id,
                    installer_company_id=company_id, installed_by=context.user_id,
                )
                await studio_metering_service.record_studio_usage(
                    db=db, company_id=company_id, agent_type="marketplace_agent",
                    operation="install_from_marketplace",
                    studio_agent_id=str(installation.source_agent_id),
                    user_id=context.user_id,
                    extra_data={"listing_id": listing_id, "installation_id": str(installation.id)},
                )
                await db.commit()
                break

            return DomainResponse.success_response(
                message="Agente instalado com sucesso! Ele já está disponível na sua lista de agentes custom.",
                data=installation.to_dict(),
                domain_id=self.domain_id, action_id="install_from_marketplace",
                suggestions=["Listar meus agentes custom", "Executar agente instalado"],
            )
        except ValueError as ve:
            return DomainResponse.error_response(error=str(ve))
        except Exception as exc:
            logger.exception("Failed to install from marketplace: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao instalar agente: {exc}", domain_id=self.domain_id, action_id="install_from_marketplace")

    async def _handle_assign_to_crew(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        agent_id = params.get("agent_id", "").strip()
        crew_id = params.get("crew_id", "").strip()
        role_name = params.get("role_name", "").strip()

        if not agent_id or not crew_id or not role_name:
            return DomainResponse.clarification_response(
                question="Informe o ID do agente, o ID da crew e o nome do role para atribuição.",
                domain_id=self.domain_id, action_id="assign_to_crew",
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
                data={"agent_id": str(agent.id), "agent_name": agent.name, "crew_id": crew_id, "role_name": role_name, "status": "assigned"},
                domain_id=self.domain_id, action_id="assign_to_crew",
            )
        except Exception as exc:
            logger.exception("Failed to assign to crew: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao atribuir agente à crew: {exc}", domain_id=self.domain_id, action_id="assign_to_crew")

    async def _handle_get_studio_consumption(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        try:
            from app.core.database import get_db
            from app.services.studio_metering_service import studio_metering_service

            company_id = context.tenant_id
            days = params.get("days", 30)

            async for db in get_db():
                consumption = await studio_metering_service.get_studio_consumption(
                    db=db, company_id=company_id, days=days,
                )
                break

            breakdown = consumption.get("breakdown_by_type", {})
            breakdown_lines = []
            for agent_type, metrics in breakdown.items():
                breakdown_lines.append(
                    f"  • {agent_type}: {metrics['executions']} execuções, "
                    f"{metrics['tokens']:,} tokens, {metrics.get('credits', 0):.2f} créditos"
                )

            msg = (
                f"📊 Consumo do Agent Studio (últimos {days} dias):\n\n"
                f"**Total de execuções:** {consumption['total_executions']}\n"
                f"**Total de tokens:** {consumption['total_tokens']:,}\n"
                f"**Total de créditos:** {consumption.get('total_credits', 0):.2f}\n"
                f"**Perfis processados:** {consumption.get('total_profiles_processed', 0)}\n"
                f"**Custo total:** R${consumption['total_cost_cents']/100:.2f}\n\n"
                f"**Breakdown por tipo:**\n" + ("\n".join(breakdown_lines) if breakdown_lines else "  Nenhum uso registrado")
            )

            return DomainResponse.success_response(
                message=msg,
                data=consumption,
                domain_id=self.domain_id,
                action_id="get_studio_consumption",
            )
        except Exception as exc:
            logger.exception("Failed to get studio consumption: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao consultar consumo: {exc}", domain_id=self.domain_id, action_id="get_studio_consumption")

    async def _handle_deactivate_agent(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        try:
            from app.core.database import get_db
            from app.services.studio_metering_service import studio_metering_service

            agent_id = params.get("agent_id")
            agent_type = params.get("agent_type", "sourcing_agent")
            company_id = context.tenant_id

            if agent_type == "custom_agent":
                from app.services.agent_marketplace_service import agent_marketplace_service
                async for db in get_db():
                    from lia_models.custom_agent import CustomAgent
                    from sqlalchemy import select
                    result = await db.execute(
                        select(CustomAgent).where(
                            CustomAgent.id == agent_id,
                            CustomAgent.company_id == company_id,
                        )
                    )
                    agent = result.scalar_one_or_none()
                    if not agent:
                        return DomainResponse.error_response(
                            error="Agente não encontrado ou não pertence a esta empresa.",
                            domain_id=self.domain_id, action_id="deactivate_agent",
                        )
                    agent.status = "archived"
                    await studio_metering_service.decrement_active_count(db, company_id, "custom_agent")
                    await studio_metering_service.record_studio_usage(
                        db=db, company_id=company_id, agent_type="custom_agent",
                        operation="deactivate_agent", studio_agent_id=agent_id,
                        user_id=context.user_id,
                    )
                    await db.commit()
                    break
            else:
                async for db in get_db():
                    # Sprint 7B-3b Part 3a: OR shim removed — frontend Part 2 v2 swap completou.
                    from lia_models.custom_agent import CustomAgent
                    from sqlalchemy import select
                    result = await db.execute(
                        select(CustomAgent).where(
                            CustomAgent.id == agent_id,
                            CustomAgent.category == "sourcing",
                            CustomAgent.company_id == company_id,
                        )
                    )
                    agent = result.scalar_one_or_none()
                    if not agent:
                        return DomainResponse.error_response(
                            error="Agente não encontrado ou não pertence a esta empresa.",
                            domain_id=self.domain_id, action_id="deactivate_agent",
                        )
                    agent.status = "paused"
                    await studio_metering_service.decrement_active_count(db, company_id, "sourcing_agent")
                    await studio_metering_service.record_studio_usage(
                        db=db, company_id=company_id, agent_type="sourcing_agent",
                        operation="deactivate_agent", studio_agent_id=agent_id,
                        user_id=context.user_id,
                    )
                    await db.commit()
                    break

            return DomainResponse.success_response(
                message=f"Agente '{agent_id}' desativado com sucesso. Quota liberada.",
                data={"agent_id": agent_id, "agent_type": agent_type, "status": "archived" if agent_type == "custom_agent" else "paused"},
                domain_id=self.domain_id,
                action_id="deactivate_agent",
            )
        except Exception as exc:
            logger.exception("Failed to deactivate agent: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao desativar agente: {exc}", domain_id=self.domain_id, action_id="deactivate_agent")

    async def _handle_uninstall_agent(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        try:
            from app.core.database import get_db
            from app.services.studio_metering_service import studio_metering_service
            from app.services.agent_marketplace_service import agent_marketplace_service

            installation_id = params.get("installation_id")
            company_id = context.tenant_id

            async for db in get_db():
                success = await agent_marketplace_service.uninstall_agent(
                    db=db,
                    installation_id=installation_id,
                    company_id=company_id,
                )
                if not success:
                    return DomainResponse.error_response(
                        error="Instalação não encontrada, não pertence a esta empresa, ou já desinstalada.",
                        domain_id=self.domain_id, action_id="uninstall_agent",
                    )
                await studio_metering_service.decrement_active_count(db, company_id, "custom_agent")
                await studio_metering_service.record_studio_usage(
                    db=db, company_id=company_id, agent_type="marketplace_agent",
                    operation="uninstall_agent",
                    studio_agent_id=installation_id,
                    user_id=context.user_id,
                )
                await db.commit()
                break

            return DomainResponse.success_response(
                message="Agente desinstalado com sucesso. Quota liberada.",
                data={"installation_id": installation_id, "status": "uninstalled"},
                domain_id=self.domain_id,
                action_id="uninstall_agent",
            )
        except Exception as exc:
            logger.exception("Failed to uninstall agent: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao desinstalar agente: {exc}", domain_id=self.domain_id, action_id="uninstall_agent")

    async def _handle_explain_agent_studio(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        """LIA-I01: Handle 'como funciona o Agent Studio?' queries."""
        return DomainResponse.success_response(
            message=(
                "O Agent Studio permite criar e configurar agentes de IA personalizados "
                "para o seu processo seletivo. Voce pode:\n\n"
                "1. **Criar agentes especializados** \u2014 por exemplo, um agente de sourcing "
                "que busca candidatos com criterios especificos\n"
                "2. **Personalizar o comportamento** \u2014 definir prompts, ferramentas e "
                "regras de negocio para cada agente\n"
                "3. **Ativar/desativar agentes** \u2014 controlar quais agentes estao ativos\n"
                "4. **Monitorar resultados** \u2014 acompanhar o desempenho de cada agente\n\n"
                "Quer criar seu primeiro agente ou ver os que ja estao configurados?"
            ),
            data={"suggestions": ["Criar novo agente", "Listar meus agentes", "Como configurar um agente"]},
            domain_id=self.domain_id,
            action_id="explain_agent_studio",
        )

    async def _handle_list_agents(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        """List all agents for the current tenant."""
        try:
            from app.core.database import get_db
            async with get_db() as db:
                result = await db.execute(
                    "SELECT id, name, type, status FROM sourcing_agents WHERE company_id = :cid ORDER BY created_at DESC LIMIT 20",
                    {"cid": context.tenant_id},
                )
                agents = [dict(r) for r in result.fetchall()] if result else []

            if not agents:
                return DomainResponse.success_response(
                    message="Voce ainda nao tem agentes configurados. Quer criar o primeiro?",
                    data={"agents": [], "suggestions": ["Criar novo agente", "Ver templates disponiveis"]},
                    domain_id=self.domain_id,
                    action_id="list_agents",
                )

            lines = ["Seus agentes configurados:\n"]
            for a in agents:
                status_icon = "\u2705" if a.get("status") == "active" else "\u23f8\ufe0f"
                lines.append(f"- {status_icon} **{a.get('name', 'Sem nome')}** ({a.get('type', 'custom')}) - {a.get('status', 'unknown')}")

            return DomainResponse.success_response(
                message="\n".join(lines),
                data={"agents": agents, "count": len(agents)},
                domain_id=self.domain_id,
                action_id="list_agents",
            )
        except Exception as exc:
            logger.warning("[AgentStudio] list_agents failed: %s", exc)
            return DomainResponse.success_response(
                message="Voce tem agentes configurados no Agent Studio. Use o painel para gerencia-los.",
                data={"suggestions": ["Criar novo agente", "Ver status dos agentes"]},
                domain_id=self.domain_id,
                action_id="list_agents",
            )

