from __future__ import annotations
from pathlib import Path

import logging
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
import yaml as _yaml_imp

logger = logging.getLogger(__name__)

_capabilities_yaml_path = Path(__file__).parent / 'config' / 'capabilities.yaml'
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get('intent_keywords', {})
    if _capabilities_yaml_path.exists()
    else {}
)

_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="company_settings")

COMPANY_SETTINGS_ACTIONS = [
    DomainAction(
        action_id="configure_profile",
        name="Configurar Perfil da Empresa",
        description="Configura dados institucionais da empresa (nome, CNPJ, website, etc.)",
        required_params=["company_id"],
        tags=["company", "profile"],
    ),
    DomainAction(
        action_id="configure_culture",
        name="Configurar Cultura & EVP",
        description="Configura missao, visao, valores, cultura e proposta de valor",
        required_params=["company_id"],
        tags=["company", "culture"],
    ),
    DomainAction(
        action_id="configure_tech_stack",
        name="Configurar Tech Stack",
        description="Configura stack tecnologico e cultura de engenharia",
        required_params=["company_id"],
        tags=["company", "tech"],
    ),
    DomainAction(
        action_id="configure_benefits",
        name="Configurar Beneficios",
        description="Configura pacote de beneficios da empresa",
        required_params=["company_id"],
        tags=["company", "benefits"],
    ),
    DomainAction(
        action_id="configure_workforce",
        name="Configurar Planejamento de Contratacoes",
        description="Configura planejamento de contratacoes (workforce planning)",
        required_params=["company_id"],
        tags=["company", "workforce"],
    ),
    DomainAction(
        action_id="analyze_website",
        name="Analisar Website",
        description="Analisa website da empresa para extrair dados automaticamente",
        required_params=["company_id"],
        tags=["company", "analysis"],
    ),
    DomainAction(
        action_id="process_document",
        name="Processar Documento",
        description="Processa documento enviado para extrair dados da empresa",
        required_params=["company_id"],
        tags=["company", "document"],
    ),
]


@register_domain
class CompanySettingsDomain(ComplianceDomainPrompt):
    _compliance_config = {'high_impact': False, 'fairness_action_type': 'data_check'}

    domain_id = "company_settings"
    domain_name = "Company Settings"
    description = "Configuracao conversacional de dados da empresa: perfil, cultura, tech stack, beneficios e planejamento"

    def get_allowed_actions(self) -> list[DomainAction]:
        return COMPANY_SETTINGS_ACTIONS

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        try:
            match = _matcher.match(query, default_action="configure_profile")
            return IntentResult(
                intent_id=f"company_settings.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}'",
            )
        except Exception as e:
            logger.debug("[company_settings] Matcher failed, using fallback: %s", e)
            return IntentResult(
                intent_id="company_settings.configure_profile",
                action_id="configure_profile",
                confidence=0.3,
                extracted_params={"raw_query": query},
                reasoning="Fallback to default action",
            )

    async def execute_action(
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(
                error=f"Acao '{action_id}' nao encontrada no dominio company_settings."
            )

        logger.info(f"Executing company_settings action '{action_id}' (tenant={context.tenant_id})")

        return DomainResponse.success_response(
            message=f"Acao '{action.name}' executada. Use o chat conversacional para configurar.",
            data={"action_id": action_id},
            domain_id=self.domain_id,
            action_id=action_id,
        )
