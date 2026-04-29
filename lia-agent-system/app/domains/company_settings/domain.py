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

    # Falha explicita: ainda NAO existe um servico de WRITE conversacional para
    # cada bloco de configuracao da empresa (perfil/cultura/tech/beneficios/workforce).
    # As leituras vivem em `CompanyConfigurationService` e os repositorios
    # (`CompanyBenefitRepository` etc.) escrevem entidades isoladas, mas nao ha
    # um orquestrador que receba campos parciais do chat e faca merge seguro
    # com auditoria + invalidacao de cache.
    # Retornamos error_response (sem mascarar com mensagem de sucesso falsa).
    def _configure_unavailable(self, action_id: str, section: str) -> DomainResponse:
        return DomainResponse.error_response(
            error=(
                f"Configuracao de '{section}' por chat ainda nao esta disponivel: "
                "ainda nao existe um servico de escrita conversacional para esse bloco. "
                "Use o painel de Configuracoes da empresa por enquanto."
            ),
            domain_id=self.domain_id,
            action_id=action_id,
            metadata={"navigation_hint": {"page": "Company Settings", "section": section}},
        )

    async def _handle_configure_profile(self, params, context):
        return self._configure_unavailable("configure_profile", "perfil")

    async def _handle_configure_culture(self, params, context):
        return self._configure_unavailable("configure_culture", "cultura")

    async def _handle_configure_tech_stack(self, params, context):
        return self._configure_unavailable("configure_tech_stack", "tech_stack")

    async def _handle_configure_benefits(self, params, context):
        return self._configure_unavailable("configure_benefits", "beneficios")

    async def _handle_configure_workforce(self, params, context):
        return self._configure_unavailable("configure_workforce", "workforce")

    @staticmethod
    def _is_safe_public_url(url: str) -> tuple[bool, str]:
        """SSRF guard: only http/https + reject private/loopback/link-local hosts.

        Runs at handler level because `analyze_website` agora e alcancavel pelo
        chat e nao podemos delegar a validacao apenas para o scraper.
        """
        from urllib.parse import urlparse
        import ipaddress
        import socket

        try:
            parsed = urlparse(url if "://" in url else f"https://{url}")
        except Exception:
            return False, "URL invalida."
        if parsed.scheme not in ("http", "https"):
            return False, "URL precisa usar http ou https."
        host = (parsed.hostname or "").strip()
        if not host or host.lower() in ("localhost", "metadata", "metadata.google.internal"):
            return False, "Host nao permitido."
        try:
            infos = socket.getaddrinfo(host, None)
        except Exception:
            # Resolucao falhou; o scraper rodara seu proprio fetch e tratara.
            return True, ""
        for info in infos:
            sockaddr = info[4]
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                continue
            if (
                ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_multicast or ip.is_reserved or ip.is_unspecified
            ):
                return False, f"Host {host} resolve para endereco interno ({ip})."
        return True, ""

    async def _handle_analyze_website(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        url = (params.get("website") or params.get("url") or "").strip()
        if not url:
            return DomainResponse.clarification_response(
                question="Qual o endereco do site da empresa que devo analisar?",
                domain_id=self.domain_id,
                action_id="analyze_website",
            )

        ok, reason = self._is_safe_public_url(url)
        if not ok:
            return DomainResponse.error_response(
                error=f"URL recusada por politica de seguranca: {reason}",
                domain_id=self.domain_id,
                action_id="analyze_website",
            )

        linkedin_url = (params.get("linkedin_url") or "").strip() or None
        if linkedin_url:
            ok_li, reason_li = self._is_safe_public_url(linkedin_url)
            if not ok_li:
                return DomainResponse.error_response(
                    error=f"LinkedIn URL recusada por politica de seguranca: {reason_li}",
                    domain_id=self.domain_id,
                    action_id="analyze_website",
                )

        try:
            from app.domains.company.services.company_scraper_service import (
                CompanyScraperService,
            )
            scraper = CompanyScraperService()
            result = await scraper.scrape_website(
                url=url,
                linkedin_url=params.get("linkedin_url"),
                company_id=context.tenant_id,
                user_id=context.user_id,
            )
        except Exception as exc:
            logger.exception("[company_settings] analyze_website failed: %s", exc)
            return DomainResponse.error_response(
                error=f"Falha ao analisar o website: {exc}",
                domain_id=self.domain_id,
                action_id="analyze_website",
            )

        if not result or not result.get("success"):
            return DomainResponse.error_response(
                error=(
                    "Nao foi possivel extrair conteudo do site informado. "
                    "Verifique a URL ou tente novamente em instantes."
                ),
                data=result or {},
                domain_id=self.domain_id,
                action_id="analyze_website",
            )

        pages_scraped = result.get("pages_scraped") or len(result.get("pages") or [])
        content_preview = (result.get("content") or "")[:600]
        msg = (
            f"Analise concluida para {url}. "
            f"{pages_scraped} pagina(s) lida(s). "
            "Os dados extraidos podem ser revisados antes de salvar no perfil "
            "(a gravacao automatica no perfil ainda nao esta disponivel via chat)."
        )
        return DomainResponse.success_response(
            message=msg,
            data={
                "url": url,
                "pages_scraped": pages_scraped,
                "pages": result.get("pages", []),
                "linkedin_url": result.get("linkedin_url"),
                "linkedin_data": result.get("linkedin_data") or {},
                "content_preview": content_preview,
                "source": result.get("source"),
            },
            domain_id=self.domain_id,
            action_id="analyze_website",
            suggestions=["Revisar dados extraidos", "Atualizar perfil no painel"],
        )

    async def _handle_process_document(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        # Nao existe servico backend para extrair dados estruturados de
        # documentos institucionais (PDF/DOCX) e gravar no perfil. Falhamos
        # explicitamente em vez de fingir sucesso.
        return DomainResponse.error_response(
            error=(
                "Processamento de documentos institucionais por chat ainda nao "
                "esta disponivel: nao ha pipeline de extracao + gravacao no "
                "perfil da empresa. Anexe o documento no painel de Configuracoes."
            ),
            domain_id=self.domain_id,
            action_id="process_document",
            metadata={"navigation_hint": {"page": "Company Settings", "section": "documentos"}},
        )
