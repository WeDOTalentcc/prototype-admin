from __future__ import annotations
from pathlib import Path

import logging
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
import yaml as _yaml_imp  # Fase 5

logger = logging.getLogger(__name__)

# Fase 5: _KEYWORD_ACTION_MAP loaded from capabilities.yaml (LIA-I05)
_capabilities_yaml_path = Path(__file__).parent / 'config' / 'capabilities.yaml'
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get('intent_keywords', {})
    if _capabilities_yaml_path.exists()
    else {}
)

# LIA-I03: Shared KeywordIntentMatcher singleton
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="hiring_policy")

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

_ACTION_BLOCK_MAP: dict[str, str] = {
    "configure_policy": "pipeline_rules",
    "configure_pipeline": "pipeline_rules",
    "configure_scheduling": "scheduling_rules",
    "configure_communication": "communication_rules",
    "configure_screening": "screening_rules",
    "configure_automation": "automation_rules",
}

_VALID_BLOCKS = [
    "pipeline_rules", "scheduling_rules", "communication_rules",
    "screening_rules", "automation_rules", "pipeline_templates",
]

_TOTAL_SETUP_BLOCKS = 5


@register_domain
class HiringPolicyDomain(ComplianceDomainPrompt):
    """Domínio de Política de Contratação da LIA."""

    _compliance_config = {'high_impact': True, 'fairness_action_type': 'policy_check'}

    domain_id = "hiring_policy"
    domain_name = "Hiring Policy"
    description = "Configuração e gestão de políticas de contratação, pipeline, triagem e automação"

    def get_allowed_actions(self) -> list[DomainAction]:
        return HIRING_POLICY_ACTIONS

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="configure_policy")
                return IntentResult(
                    intent_id=f"hiring_policy.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="configure_policy")
            return IntentResult(
                intent_id=f"hiring_policy.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}'",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
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
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de hiring_policy."
            )

        logger.info(f"Executing hiring_policy action '{action_id}' (tenant={context.tenant_id})")

        handler_map = {
            "configure_policy": self._handle_configure,
            "configure_pipeline": self._handle_configure,
            "configure_scheduling": self._handle_configure,
            "configure_communication": self._handle_configure,
            "configure_screening": self._handle_configure,
            "configure_automation": self._handle_configure,
            "validate_compliance": self._handle_validate_compliance,
            "get_progress": self._handle_get_progress,
        }

        handler = handler_map.get(action_id)
        if not handler:
            return DomainResponse.error_response(error=f"No handler for '{action_id}'")

        try:
            return await handler(action_id, params, context)
        except Exception as exc:
            logger.error(f"Hiring policy action '{action_id}' failed: {exc}", exc_info=True)
            return DomainResponse.error_response(
                error=str(exc),
                message=f"Erro ao executar '{action.name}': {exc}",
                domain_id=self.domain_id,
                action_id=action_id,
            )

    async def _get_or_create_policy(self, session, company_id: str, user_id: str | None):
        from app.domains.hiring_policy.repositories.hiring_policy_repository import HiringPolicyRepository
        repo = HiringPolicyRepository(session)
        policy = await repo.get_by_company(company_id)
        if not policy:
            policy = await repo.create_if_missing(company_id, user_id)
            await repo.flush()
        return policy, repo

    async def _handle_configure(
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal

        block = _ACTION_BLOCK_MAP.get(action_id, "pipeline_rules")
        update_data = {}

        for key, value in params.items():
            if key in ("raw_query", "company_id"):
                continue
            if not update_data.get(block):
                update_data[block] = {}
            update_data[block][key] = value

        async with AsyncSessionLocal() as session:
            policy, repo = await self._get_or_create_policy(
                session, context.tenant_id, context.user_id
            )

            if update_data:
                policy = await repo.upsert(
                    company_id=context.tenant_id,
                    update_data=update_data,
                    valid_blocks=_VALID_BLOCKS,
                    user_id=context.user_id,
                )
                await repo.update_answered_questions(policy, block)

            answered = set(policy.answered_questions or [])
            progress = int(len(answered.intersection(set(_ACTION_BLOCK_MAP.values()))) / _TOTAL_SETUP_BLOCKS * 100)
            policy.setup_progress = progress

            await session.commit()
            policy_data = policy.to_dict()

        block_label = block.replace("_", " ").title()
        current_values = policy_data.get(block, {})

        if update_data:
            msg = f"Configuração de **{block_label}** atualizada com sucesso! Progresso: {progress}%."
        else:
            msg = f"Configuração atual de **{block_label}**:\n"
            for k, v in current_values.items():
                msg += f"• **{k}**: {v}\n"
            msg += f"\nProgresso geral: {progress}%. Envie os valores que deseja alterar."

        return DomainResponse.success_response(
            message=msg,
            data={
                "action_id": action_id,
                "block": block,
                "current_values": current_values,
                "progress": progress,
                "policy": policy_data,
            },
            domain_id=self.domain_id,
            action_id=action_id,
        )

    async def _handle_validate_compliance(
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            policy, repo = await self._get_or_create_policy(
                session, context.tenant_id, context.user_id
            )
            policy_data = policy.to_dict()

        issues: list[str] = []
        warnings: list[str] = []

        pipeline = policy_data.get("pipeline_rules", {})
        if pipeline.get("min_interviews_before_offer", 0) < 1:
            issues.append("Mínimo de entrevistas antes da oferta é 0 — recomendado pelo menos 1.")

        comm = policy_data.get("communication_rules", {})
        if not comm.get("auto_rejection_feedback", False):
            warnings.append("Feedback automático de rejeição desativado — considere ativar para melhor experiência do candidato.")

        automation = policy_data.get("automation_rules", {})
        if automation.get("autonomy_level") == "high" and not pipeline.get("manager_approval_for_offer", True):
            issues.append("Nível de autonomia 'high' sem aprovação do gestor para ofertas — risco de compliance.")

        screening = policy_data.get("screening_rules", {})
        if not screening.get("default_screening_questions"):
            warnings.append("Nenhuma pergunta de triagem padrão configurada.")

        if issues:
            status_msg = f"**{len(issues)} problema(s) de compliance encontrado(s):**\n"
            for i, issue in enumerate(issues, 1):
                status_msg += f"{i}. ⚠ {issue}\n"
        else:
            status_msg = "**Nenhum problema crítico de compliance encontrado.**\n"

        if warnings:
            status_msg += f"\n**{len(warnings)} recomendação(ões):**\n"
            for w in warnings:
                status_msg += f"• {w}\n"

        return DomainResponse.success_response(
            message=status_msg,
            data={
                "action_id": action_id,
                "issues": issues,
                "warnings": warnings,
                "compliant": len(issues) == 0,
                "policy": policy_data,
            },
            domain_id=self.domain_id,
            action_id=action_id,
        )

    async def _handle_get_progress(
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            policy, repo = await self._get_or_create_policy(
                session, context.tenant_id, context.user_id
            )
            policy_data = policy.to_dict()

        answered = set(policy_data.get("answered_questions", []))
        all_blocks = set(_ACTION_BLOCK_MAP.values())
        completed = answered.intersection(all_blocks)
        pending = all_blocks - completed
        progress = int(len(completed) / _TOTAL_SETUP_BLOCKS * 100)

        msg = f"**Progresso da configuração: {progress}%**\n\n"
        for blk in sorted(all_blocks):
            label = blk.replace("_", " ").title()
            status = "✅" if blk in completed else "⏳"
            msg += f"{status} {label}\n"

        if pending:
            msg += f"\nFaltam **{len(pending)}** bloco(s) para completar a configuração."

        return DomainResponse.success_response(
            message=msg,
            data={
                "action_id": action_id,
                "progress": progress,
                "completed_blocks": sorted(completed),
                "pending_blocks": sorted(pending),
                "policy": policy_data,
            },
            domain_id=self.domain_id,
            action_id=action_id,
        )
