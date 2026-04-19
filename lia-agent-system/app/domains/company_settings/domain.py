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


def _load_keyword_action_map() -> dict[str, str]:
    if not _capabilities_yaml_path.exists():
        return {}
    raw = _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get('intent_keywords', {})
    inverted: dict[str, str] = {}
    for action, keywords in raw.items():
        if isinstance(keywords, list):
            for kw in keywords:
                inverted[str(kw)] = action
        else:
            inverted[str(keywords)] = action
    return inverted


_KEYWORD_ACTION_MAP: dict[str, str] = _load_keyword_action_map()

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
    agent_aliases = ("settings_config", "company_profile", "company_config")

    def get_allowed_actions(self) -> list[DomainAction]:
        return COMPANY_SETTINGS_ACTIONS

    def get_system_prompt(self) -> str:
        return (
            "Especialista em configuracao de perfil de empresa. "
            "Ajude o recrutador a preencher dados institucionais, cultura, tech stack, "
            "beneficios e planejamento de contratacoes via conversa natural."
        )

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

        handler_map = {
            "configure_profile": self._handle_configure_profile,
            "configure_culture": self._handle_configure_culture,
            "configure_tech_stack": self._handle_configure_tech_stack,
            "configure_benefits": self._handle_configure_benefits,
            "configure_workforce": self._handle_configure_workforce,
            "analyze_website": self._handle_analyze_website,
            "process_document": self._handle_process_document,
        }
        handler = handler_map.get(action_id)
        if handler:
            return await handler(params, context)

        return DomainResponse.error_response(
            error=f"Acao '{action_id}' nao implementada.",
            domain_id=self.domain_id,
            action_id=action_id,
        )

    # Falha explicita: o servico backend ainda nao existe (#602).
    # Retornamos error_response em vez de mascarar com sucesso falso.
    _SERVICE_UNAVAILABLE = (
        "Configuracao de empresa por chat ainda nao esta disponivel: "
        "o servico backend (CompanyProfileService) nao foi implementado. "
        "Use o painel de Configuracoes da empresa por enquanto."
    )

    def _service_unavailable(self, action_id: str) -> DomainResponse:
        return DomainResponse.error_response(
            error=self._SERVICE_UNAVAILABLE,
            domain_id=self.domain_id,
            action_id=action_id,
        )

    async def _handle_configure_profile(self, params, context):
        return self._service_unavailable("configure_profile")

    async def _handle_configure_culture(self, params, context):
        return self._service_unavailable("configure_culture")

    async def _handle_configure_tech_stack(self, params, context):
        return self._service_unavailable("configure_tech_stack")

    async def _handle_configure_benefits(self, params, context):
        return self._service_unavailable("configure_benefits")

    async def _handle_configure_workforce(self, params, context):
        return self._service_unavailable("configure_workforce")

    async def _handle_analyze_website(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        return self._service_unavailable("analyze_website")

    async def _handle_process_document(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        return self._service_unavailable("process_document")
