from __future__ import annotations

import logging
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP: dict[str, str] = {
    "criar vaga": "create_job",
    "nova vaga": "create_job",
    "create job": "create_job",
    "abrir vaga": "create_job",
    "wizard": "guided_wizard",
    "guiado": "guided_wizard",
    "passo a passo": "guided_wizard",
    "step": "guided_wizard",
    "extrair requisito": "extract_requirements",
    "extract": "extract_requirements",
    "requisitos": "extract_requirements",
    "rubrica": "generate_rubrics",
    "rubric": "generate_rubrics",
    "atualizar vaga": "update_job",
    "editar vaga": "update_job",
    "update": "update_job",
    "alterar vaga": "update_job",
    "saúde": "health_check",
    "health": "health_check",
    "diagnóstico": "health_check",
    "estratégia": "suggest_strategy",
    "strategy": "suggest_strategy",
    "duplicar": "duplicate_job",
    "duplicate": "duplicate_job",
    "template": "create_from_template",
    "modelo": "create_from_template",
    "clonar": "clone_job",
    "clone": "clone_job",
    "fechar vaga": "close_job",
    "close": "close_job",
    "arquivar": "close_job",
    "encerrar": "close_job",
    "pausar vaga": "pause_job",
    "pausar": "pause_job",
    "pause": "pause_job",
    "pausa": "pause_job",
    "suspender": "pause_job",
    "suspende": "pause_job",
    "benefício": "get_benefits",
    "benefit": "get_benefits",
    "melhorar jd": "suggest_jd_improvements",
    "improve": "suggest_jd_improvements",
    "sugerir melhoria": "suggest_jd_improvements",
    "detectar critério": "detect_criteria",
    "detect": "detect_criteria",
    "auto detect": "detect_criteria",
    "pergunta wsi": "generate_wsi_questions",
    "wsi question": "generate_wsi_questions",
    "triagem": "generate_wsi_questions",
    "avançar etapa": "advance_wizard_step",
    "avançar para próxima": "advance_wizard_step",
    "próxima etapa": "advance_wizard_step",
    "next step": "advance_wizard_step",
    "advance": "advance_wizard_step",
    "dados etapa": "get_wizard_step_data",
    "step data": "get_wizard_step_data",
    "etapa atual": "get_wizard_step_data",
    "enriquecer jd": "enrich_jd",
    "enriquecer a job": "enrich_jd",
    "enriquecer": "enrich_jd",
    "enrich": "enrich_jd",
    "enriquecimento": "enrich_jd",
    "importar jd": "import_jd",
    "import jd": "import_jd",
    "gerar jd": "generate_jd",
    "generate jd": "generate_jd",
    "gerar job description": "generate_jd",
    "analytics": "job_analytics",
    "métricas": "job_analytics",
    "relatório": "job_analytics",
    "qualificação": "qualify_job",
    "qualify": "qualify_job",
    "publicar": "publish_job",
    "publish": "publish_job",
    "job board": "publish_job",
    "webhook": "job_status_webhook",
    "status": "job_status_webhook",
    "buscar template": "search_templates",
    "pesquisar template": "search_templates",
    "search template": "search_templates",
    "aplicar template": "apply_template",
    "usar template": "apply_template",
    "apply template": "apply_template",
    "analisar jd": "analyze_jd",
    "avaliar jd": "analyze_jd",
    "qualidade jd": "analyze_jd",
    "analyze jd": "analyze_jd",
    "compensação": "suggest_compensation",
    "faixa salarial": "suggest_compensation",
    "salary range": "suggest_compensation",
    "sugerir salário": "suggest_compensation",
    "remuneração": "suggest_compensation",
}


@register_domain
class JobManagementDomain(ComplianceDomainPrompt):
    """Domínio de Job Management & Wizard da LIA."""

    _compliance_config = {'high_impact': False}

    domain_id = "job_management"
    domain_name = "Job Management & Wizard"
    description = "Criação, gestão e otimização de vagas de emprego"

    def get_allowed_actions(self) -> list[DomainAction]:
        from app.domains.job_management.actions import JOB_MANAGEMENT_ACTIONS
        return JOB_MANAGEMENT_ACTIONS

    def get_system_prompt(self) -> str:
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt(self.domain_id)

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        query_lower = query.lower()
        best_action = "create_job"
        best_confidence = 0.3

        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                confidence = min(0.95, 0.6 + len(keyword) * 0.02)
                if confidence > best_confidence:
                    best_action = action_id
                    best_confidence = confidence

        return IntentResult(
            intent_id=f"job_management.{best_action}",
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
                error=f"Ação '{action_id}' não encontrada no domínio de job management."
            )

        logger.info(f"Routing job management action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.job_management.tools import JOB_MANAGEMENT_TOOLS, execute_job_management_tool

        tool_ids = {t["tool_id"] for t in JOB_MANAGEMENT_TOOLS}

        _ACTION_TOOL_MAP: dict[str, str] = {
            "create_job": "create_job_vacancy",
            "update_job": "update_job_vacancy",
            "close_job": "close_job_vacancy",
            "pause_job": "pause_job_vacancy",
            "duplicate_job": "duplicate_job_vacancy",
            "clone_job": "duplicate_job_vacancy",
            "generate_jd": "generate_job_description",
            "enrich_jd": "enrich_job_description",
            "import_jd": "import_job_description",
            "search_templates": "search_job_templates",
            "create_from_template": "search_job_templates",
            "apply_template": "search_job_templates",
            "health_check": "get_job_health",
            "advance_wizard_step": "advance_wizard",
            "get_wizard_step_data": "get_wizard_step",
            "guided_wizard": "get_wizard_step",
            "job_analytics": "get_job_analytics",
        }

        mapped_tool = _ACTION_TOOL_MAP.get(action_id)
        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_job_management_tool(
                tool_id=mapped_tool,
                params=params,
                tenant_id=context.tenant_id,
            )
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        from app.shared.delegation_fallback import DelegationFallbackHandler
        fallback_data = DelegationFallbackHandler.handle(
            action_id=action_id,
            domain_id=self.domain_id,
            params=params,
            context={"user_id": context.user_id, "tenant_id": context.tenant_id},
        )
        return DomainResponse.success_response(
            message=fallback_data["message"],
            data=fallback_data,
            domain_id=self.domain_id,
            action_id=action_id,
        )
