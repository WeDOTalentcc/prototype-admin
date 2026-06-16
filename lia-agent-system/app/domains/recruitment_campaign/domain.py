from pathlib import Path
"""Recruitment Campaign Domain - End-to-end workflow management.

ARCHITECTURAL DECISION (P2-3, 2026-05-10):
========================================
recruitment_campaign é ORCHESTRATION WRAPPER — sem agent ReAct próprio
por design (não over-engineering).

Delega execução para domains downstream:
  - create_campaign      → job_management.create_job + sourcing.start_pipeline
  - advance_campaign     → cv_screening.process + interview_scheduling.schedule
  - get_campaign_progress → analytics.report
  - list_campaigns       → leitura via repositories já existentes

Padrão canonical: KeywordIntentMatcher resolve intent (capabilities.yaml),
execute_action chama tools de outros domains via DomainRegistry. Audit
herda do ComplianceDomainPrompt base.

NÃO criar agent próprio: campaigns são workflows multi-domain, não tools
isoladas. Cada step é responsabilidade do domain especializado correspondente.
"""
import logging
import yaml as _yaml_imp  # Fase 5
from datetime import datetime
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher

logger = logging.getLogger(__name__)

# Fase 5: _KEYWORD_ACTION_MAP loaded from capabilities.yaml (LIA-I05)
_capabilities_yaml_path = Path(__file__).parent / 'config' / 'capabilities.yaml'
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get('intent_keywords', {})
    if _capabilities_yaml_path.exists()
    else {}
)

# LIA-I03: Shared KeywordIntentMatcher singleton
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="recruitment_campaign")

@register_domain
class RecruitmentCampaignDomain(ComplianceDomainPrompt):
    domain_id = "recruitment_campaign"
    domain_name = "Recruitment Campaigns"
    description = "Workflow ponta-a-ponta de recrutamento — definição a placement"
    _compliance_config = {"high_impact": False, "fairness_action_type": "general"}

    def get_allowed_actions(self):
        from app.domains.recruitment_campaign.actions import CAMPAIGN_ACTIONS
        return CAMPAIGN_ACTIONS

    async def process_intent(self, query, context):
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="list_campaigns")
                return IntentResult(
                    intent_id=f"recruitment_campaign.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="list_campaigns")
            return IntentResult(intent_id=f"recruitment_campaign.{match.action}", action_id=match.action, confidence=match.confidence, extracted_params={"raw_query": query}, reasoning=f"KeywordIntentMatcher matched '{match.action}'")
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
            q = query.lower()
            best_action, best_conf = "list_campaigns", 0.3
            for kw, action in _KEYWORD_ACTION_MAP.items():
                if kw in q:
                    conf = 0.9 if len(kw) > 6 else 0.75
                    if conf > best_conf:
                        best_action, best_conf = action, conf
            return IntentResult(intent_id=f"recruitment_campaign.{best_action}", action_id=best_action, confidence=best_conf, extracted_params={"raw_query": query}, reasoning=f"Keyword matched '{best_action}'")

    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(error=f"Action '{action_id}' not found")

        handler_map = {
            "create_campaign": self._handle_create_campaign,
            "get_campaign_progress": self._handle_get_campaign_progress,
            "advance_campaign": self._handle_advance_campaign,
            "list_campaigns": self._handle_list_campaigns,
        }

        handler = handler_map.get(action_id)
        if handler:
            return await handler(params, context)

        return DomainResponse.error_response(error=f"Action '{action_id}' not implemented")

    async def _handle_create_campaign(self, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        name = params.get("name", "").strip()
        if not name:
            return DomainResponse.clarification_response(
                question="Qual nome você quer dar à campanha de recrutamento?",
                options=["Campanha Tech Q1", "Campanha Vendas Regional", "Campanha Estágio 2026"],
                domain_id=self.domain_id,
                action_id="create_campaign",
            )

        try:
            from app.core.database import get_db
            from app.services.studio_metering_service import studio_metering_service
            from lia_models.recruitment_campaign import (
                RecruitmentCampaign, DEFAULT_CAMPAIGN_STAGES,
            )
            import uuid

            company_id = context.tenant_id

            async for db in get_db():
                allowed, msg = await studio_metering_service.check_and_increment_quota(db, company_id, "recruitment_campaign")
                if not allowed:
                    return DomainResponse.error_response(error=msg, domain_id=self.domain_id, action_id="create_campaign")

                automation_level = params.get("automation_level", "semi")
                custom_stages = params.get("stages")
                if custom_stages and isinstance(custom_stages, list):
                    validated_stages = []
                    for i, s in enumerate(custom_stages):
                        if not isinstance(s, dict) or "name" not in s:
                            continue
                        validated_stages.append({
                            "name": s["name"],
                            "order": s.get("order", i + 1),
                            "auto_actions": s.get("auto_actions", []),
                        })
                    stages = validated_stages if validated_stages else list(DEFAULT_CAMPAIGN_STAGES)
                else:
                    stages = list(DEFAULT_CAMPAIGN_STAGES)

                campaign = RecruitmentCampaign(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    created_by=context.user_id,
                    name=name,
                    description=params.get("description", f"Campanha: {name}"),
                    job_id=params.get("job_id"),
                    talent_pool_id=params.get("talent_pool_id"),
                    status="active",
                    stages=stages,
                    current_stage_index=0,
                    automation_level=automation_level,
                    stage_history=[{
                        "stage": stages[0]["name"],
                        "action": "campaign_created",
                        "timestamp": datetime.utcnow().isoformat(),
                        "by": context.user_id,
                    }],
                )
                db.add(campaign)
                await db.flush()
                await db.refresh(campaign)

                await studio_metering_service.record_studio_usage(
                    db=db, company_id=company_id, agent_type="recruitment_campaign",
                    operation="create_campaign", studio_agent_id=str(campaign.id),
                    user_id=context.user_id,
                )
                await db.commit()
                break

            stage_names = [s["name"] for s in stages]
            return DomainResponse.success_response(
                message=(
                    f"Campanha '{name}' criada com sucesso!\n\n"
                    f"**Estágios configurados:** {' → '.join(stage_names)}\n"
                    f"**Estágio atual:** {stages[0]['name']}\n"
                    f"**Automação:** {automation_level}\n\n"
                    f"A campanha está ativa e pronta para iniciar o sourcing."
                ),
                data=campaign.to_dict(),
                domain_id=self.domain_id,
                action_id="create_campaign",
                suggestions=[
                    "Ver progresso da campanha",
                    "Avançar campanha",
                    "Listar campanhas",
                ],
            )
        except Exception as exc:
            logger.exception("Failed to create campaign: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao criar campanha: {exc}", domain_id=self.domain_id, action_id="create_campaign")

    async def _handle_get_campaign_progress(self, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        campaign_id = params.get("campaign_id", "").strip()
        if not campaign_id:
            return DomainResponse.clarification_response(
                question="Qual campanha deseja consultar? Informe o campaign_id.",
                domain_id=self.domain_id,
                action_id="get_campaign_progress",
            )

        try:
            from app.core.database import get_db
            from lia_models.recruitment_campaign import RecruitmentCampaign
            from sqlalchemy import select

            company_id = context.tenant_id

            async for db in get_db():
                result = await db.execute(
                    select(RecruitmentCampaign).where(
                        RecruitmentCampaign.id == campaign_id,
                        RecruitmentCampaign.company_id == company_id,
                    )
                )
                campaign = result.scalar_one_or_none()
                break

            if not campaign:
                return DomainResponse.error_response(error="Campanha não encontrada.", domain_id=self.domain_id, action_id="get_campaign_progress")

            current = campaign.current_stage
            stages = campaign.stages or []
            stage_display = []
            for i, s in enumerate(stages):
                marker = "→ " if i == campaign.current_stage_index else "  "
                check = "✅" if i < campaign.current_stage_index else ("🔄" if i == campaign.current_stage_index else "⬜")
                stage_display.append(f"{marker}{check} {s['name']}")

            msg = (
                f"📊 Campanha '{campaign.name}':\n\n"
                f"**Status:** {campaign.status}\n"
                f"**Progresso:** {campaign.progress_pct}%\n"
                f"**Estágio atual:** {current['name'] if current else 'N/A'}\n\n"
                f"**Pipeline:**\n" + "\n".join(stage_display) + "\n\n"
                f"**Métricas:**\n"
                f"  • Candidatos totais: {campaign.total_candidates}\n"
                f"  • Triados: {campaign.candidates_screened}\n"
                f"  • Contatados: {campaign.candidates_contacted}\n"
                f"  • Entrevistados: {campaign.candidates_interviewed}\n"
                f"  • Ofertas: {campaign.candidates_offered}\n"
                f"  • Contratados: {campaign.candidates_hired}"
            )

            return DomainResponse.success_response(
                message=msg,
                data=campaign.to_dict(),
                domain_id=self.domain_id,
                action_id="get_campaign_progress",
                suggestions=["Avançar campanha", "Listar campanhas"],
            )
        except Exception as exc:
            logger.exception("Failed to get campaign progress: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao consultar progresso: {exc}", domain_id=self.domain_id, action_id="get_campaign_progress")

    async def _handle_advance_campaign(self, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        campaign_id = params.get("campaign_id", "").strip()
        if not campaign_id:
            return DomainResponse.clarification_response(
                question="Qual campanha deseja avançar? Informe o campaign_id.",
                domain_id=self.domain_id,
                action_id="advance_campaign",
            )

        try:
            from app.core.database import get_db
            from lia_models.recruitment_campaign import RecruitmentCampaign
            from app.services.studio_metering_service import studio_metering_service
            from sqlalchemy import select

            company_id = context.tenant_id

            async for db in get_db():
                result = await db.execute(
                    select(RecruitmentCampaign).where(
                        RecruitmentCampaign.id == campaign_id,
                        RecruitmentCampaign.company_id == company_id,
                    )
                )
                campaign = result.scalar_one_or_none()

                if not campaign:
                    return DomainResponse.error_response(error="Campanha não encontrada.")

                if campaign.status != "active":
                    return DomainResponse.error_response(error=f"Campanha não está ativa (status: {campaign.status}).")

                stages = campaign.stages or []
                current_idx = campaign.current_stage_index
                if current_idx >= len(stages) - 1:
                    campaign.status = "completed"
                    campaign.stage_history = list(campaign.stage_history or []) + [{
                        "stage": "completed",
                        "action": "campaign_completed",
                        "timestamp": datetime.utcnow().isoformat(),
                        "by": context.user_id,
                    }]
                    await studio_metering_service.decrement_active_count(db, company_id, "recruitment_campaign")
                    await studio_metering_service.record_studio_usage(
                        db=db, company_id=company_id, agent_type="recruitment_campaign",
                        operation="complete_campaign", studio_agent_id=str(campaign.id),
                        user_id=context.user_id,
                    )
                    await db.commit()

                    return DomainResponse.success_response(
                        message=f"🎉 Campanha '{campaign.name}' concluída! Todos os estágios foram completados.",
                        data=campaign.to_dict(),
                        domain_id=self.domain_id, action_id="advance_campaign",
                    )

                old_stage = stages[current_idx]["name"]
                new_idx = current_idx + 1
                new_stage = stages[new_idx]
                campaign.current_stage_index = new_idx

                history = list(campaign.stage_history or [])
                history.append({
                    "stage": new_stage["name"],
                    "action": "stage_advanced",
                    "from_stage": old_stage,
                    "timestamp": datetime.utcnow().isoformat(),
                    "by": context.user_id,
                    "auto_actions": new_stage.get("auto_actions", []),
                })
                campaign.stage_history = history

                auto_actions = new_stage.get("auto_actions", [])
                actions_triggered = []
                for auto_action in auto_actions:
                    dispatched = await self._dispatch_auto_action(
                        db=db, campaign=campaign,
                        stage_name=new_stage["name"],
                        action_name=auto_action,
                        company_id=company_id,
                        user_id=context.user_id,
                    )
                    actions_triggered.append(auto_action)
                    logger.info(
                        "[Campaign] Auto-action %s: campaign=%s stage=%s action=%s",
                        "dispatched" if dispatched else "skipped",
                        campaign_id, new_stage["name"], auto_action,
                    )

                await studio_metering_service.record_studio_usage(
                    db=db, company_id=company_id, agent_type="recruitment_campaign",
                    operation="advance_campaign", studio_agent_id=str(campaign.id),
                    user_id=context.user_id,
                    extra_data={"from_stage": old_stage, "to_stage": new_stage["name"]},
                )
                await db.commit()
                break

            msg = (
                f"Campanha '{campaign.name}' avançada!\n\n"
                f"**De:** {old_stage}\n"
                f"**Para:** {new_stage['name']}\n"
                f"**Progresso:** {campaign.progress_pct}%\n"
            )
            if actions_triggered:
                msg += f"\n**Ações automáticas disparadas:** {', '.join(actions_triggered)}"

            return DomainResponse.success_response(
                message=msg,
                data=campaign.to_dict(),
                domain_id=self.domain_id,
                action_id="advance_campaign",
                suggestions=["Ver progresso da campanha", "Avançar campanha novamente"],
            )
        except Exception as exc:
            logger.exception("Failed to advance campaign: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao avançar campanha: {exc}", domain_id=self.domain_id, action_id="advance_campaign")

    async def _handle_list_campaigns(self, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        try:
            from app.core.database import get_db
            from lia_models.recruitment_campaign import RecruitmentCampaign
            from sqlalchemy import select

            company_id = context.tenant_id
            status_filter = params.get("status")

            async for db in get_db():
                query = select(RecruitmentCampaign).where(
                    RecruitmentCampaign.company_id == company_id,
                )
                if status_filter:
                    query = query.where(RecruitmentCampaign.status == status_filter)
                query = query.order_by(RecruitmentCampaign.created_at.desc()).limit(20)

                result = await db.execute(query)
                campaigns = result.scalars().all()
                break

            if not campaigns:
                return DomainResponse.success_response(
                    message="Nenhuma campanha encontrada. Crie uma nova campanha de recrutamento!",
                    data={"campaigns": [], "total": 0},
                    domain_id=self.domain_id,
                    action_id="list_campaigns",
                    suggestions=["Criar campanha"],
                )

            campaign_list = [
                f"• {c.name} — {c.status}, estágio: {c.current_stage['name'] if c.current_stage else 'N/A'}, progresso: {c.progress_pct}%"
                for c in campaigns
            ]
            msg = f"Encontradas {len(campaigns)} campanha(s):\n" + "\n".join(campaign_list)

            return DomainResponse.success_response(
                message=msg,
                data={"campaigns": [c.to_dict() for c in campaigns], "total": len(campaigns)},
                domain_id=self.domain_id,
                action_id="list_campaigns",
                suggestions=["Criar nova campanha", "Ver progresso de campanha"],
            )
        except Exception as exc:
            logger.exception("Failed to list campaigns: %s", exc)
            return DomainResponse.error_response(error=f"Erro ao listar campanhas: {exc}", domain_id=self.domain_id, action_id="list_campaigns")

    async def _dispatch_auto_action(
        self,
        db,
        campaign,
        stage_name: str,
        action_name: str,
        company_id: str,
        user_id: str,
    ) -> bool:
        try:
            from app.shared.agents.agent_bus import AgentBus

            action_dispatch_map = {
                "search_candidates": {
                    "domain": "sourcing",
                    "action": "search_candidates",
                    "params": {
                        "campaign_id": str(campaign.id),
                        "job_id": str(campaign.job_id) if campaign.job_id else None,
                        "company_id": company_id,
                    },
                },
                "apply_screening": {
                    "domain": "cv_screening",
                    "action": "bulk_screen",
                    "params": {
                        "campaign_id": str(campaign.id),
                        "company_id": company_id,
                    },
                },
                "send_outreach_email": {
                    "domain": "email",
                    "action": "send_campaign_email",
                    "params": {
                        "campaign_id": str(campaign.id),
                        "stage": stage_name,
                        "company_id": company_id,
                    },
                },
                "schedule_interview": {
                    "domain": "interview_scheduling",
                    "action": "bulk_schedule",
                    "params": {
                        "campaign_id": str(campaign.id),
                        "stage": stage_name,
                        "company_id": company_id,
                    },
                },
                "generate_evaluation": {
                    "domain": "evaluation",
                    "action": "generate_campaign_evaluation",
                    "params": {
                        "campaign_id": str(campaign.id),
                        "company_id": company_id,
                    },
                },
                "prepare_offer": {
                    "domain": "offer",
                    "action": "prepare_campaign_offer",
                    "params": {
                        "campaign_id": str(campaign.id),
                        "company_id": company_id,
                    },
                },
                "notify_recruiters": {
                    "domain": "notifications",
                    "action": "send_notification",
                    "params": {
                        "type": "campaign_stage_advance",
                        "title": f"Campanha '{campaign.name}' avançou para '{stage_name}'",
                        "target": "recruiters",
                        "company_id": company_id,
                        "campaign_id": str(campaign.id),
                    },
                },
            }

            dispatch_config = action_dispatch_map.get(action_name)
            if not dispatch_config:
                logger.warning(
                    "[Campaign] Unknown auto-action '%s', skipping dispatch",
                    action_name,
                )
                return False

            bus = AgentBus()
            # AgentBus roteia ponto-a-ponto por (company_id, to_agent); nao ha
            # kwarg channel/message. Subscriber downstream = Fase 2 (ausente).
            await bus.publish(
                from_agent="recruitment_campaign",
                to_agent=dispatch_config["domain"],
                event_type=dispatch_config["action"],
                payload={
                    **dispatch_config["params"],
                    "triggered_by": user_id,
                    "source": "recruitment_campaign",
                },
                company_id=company_id,
            )

            logger.info(
                "[Campaign] Dispatched auto-action '%s' via AgentBus to domain '%s'",
                action_name, dispatch_config["domain"],
            )
            return True

        except Exception as e:
            logger.error(
                "[Campaign] Failed to dispatch auto-action %s: %s",
                action_name, e, exc_info=True,
            )
            return False
