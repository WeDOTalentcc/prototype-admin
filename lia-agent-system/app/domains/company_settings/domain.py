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
    
        examples=('configura perfil da empresa', 'edita dados institucionais'),
    ),
    DomainAction(
        action_id="configure_culture",
        name="Configurar Cultura & EVP",
        description="Configura missao, visao, valores, cultura e proposta de valor",
        required_params=["company_id"],
        tags=["company", "culture"],
    
        examples=('configura cultura e valores', 'define missão e visão'),
    ),
    DomainAction(
        action_id="configure_tech_stack",
        name="Configurar Tech Stack",
        description="Configura stack tecnologico e cultura de engenharia",
        required_params=["company_id"],
        tags=["company", "tech"],
    
        examples=('configura tech stack', 'define as tecnologias usadas'),
    ),
    DomainAction(
        action_id="configure_benefits",
        name="Configurar Beneficios",
        description="Configura pacote de beneficios da empresa",
        required_params=["company_id"],
        tags=["company", "benefits"],
    
        examples=('configura benefícios', 'define pacote de benefícios'),
    ),
    DomainAction(
        action_id="configure_workforce",
        name="Configurar Planejamento de Contratacoes",
        description="Configura planejamento de contratacoes (workforce planning)",
        required_params=["company_id"],
        tags=["company", "workforce"],
    
        examples=('configura planejamento de contratações', 'define workforce planning'),
    ),
    DomainAction(
        action_id="analyze_website",
        name="Analisar Website",
        description="Analisa website da empresa para extrair dados automaticamente",
        required_params=["company_id"],
        tags=["company", "analysis"],
    
        examples=('analisa nosso site pra extrair dados', 'olha no website e extrai info'),
    ),
    DomainAction(
        action_id="process_document",
        name="Processar Documento",
        description="Processa documento enviado para extrair dados da empresa",
        required_params=["company_id"],
        tags=["company", "document"],
    
        examples=('processa este documento da empresa', 'extrai dados deste arquivo'),
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

    # WRITE conversacional — Task #712
    # As tools `_wrap_save_company_section`, `_wrap_save_company_field` e
    # `_wrap_import_workforce_plan` ja existem em
    # `app.domains.company_settings.agents.company_tool_registry` e ja aplicam
    # FairnessGuard + Audit + tier validation. Os 5 handlers abaixo apenas
    # delegam para essas tools, transformando a resposta em DomainResponse e
    # pedindo clarification quando faltam campos.

    _SECTION_FIELD_HINTS: dict[str, dict[str, list[str]]] = {
        "configure_profile": {
            "section": "profile",
            "fields": ["name", "trading_name", "cnpj", "website", "hr_email",
                       "hr_phone", "address", "industry", "company_size",
                       "employee_count", "founded_year", "linkedin_url", "logo_url"],
            "label": "perfil da empresa",
        },
        "configure_culture": {
            "section": "culture",
            "fields": ["mission", "vision", "values", "core_competencies",
                       "evp_bullets", "work_model", "employment_types",
                       "team_dynamics", "leadership_style", "dei_initiatives",
                       "sustainability", "social_impact"],
            "label": "cultura e EVP",
        },
        "configure_tech_stack": {
            "section": "culture",
            "fields": ["tech_stack", "engineering_culture", "default_languages"],
            "label": "tech stack",
        },
        # NOTA: configure_benefits NAO usa _delegate_section_write porque
        # 'benefits' nao existe em VALID_CULTURE_FIELDS (tabela dedicada
        # company_benefits). Tratado em _handle_configure_benefits abaixo.
    }

    def _extract_section_payload(self, action_id: str, params: dict[str, Any]) -> dict[str, Any]:
        hints = self._SECTION_FIELD_HINTS.get(action_id, {})
        allowed = set(hints.get("fields", []))
        payload: dict[str, Any] = {}
        if isinstance(params.get("data"), dict):
            for k, v in params["data"].items():
                if k in allowed and v not in (None, "", []):
                    payload[k] = v
        for k, v in params.items():
            if k in allowed and v not in (None, "", []):
                payload[k] = v
        return payload

    @staticmethod
    def _resolve_tenant(
        action_id: str,
        params: dict[str, Any],
        context: DomainContext,
    ) -> tuple[str | None, DomainResponse | None]:
        """Single source of truth: ALWAYS use context.tenant_id (the
        authenticated tenant) — params.company_id is treated as untrusted
        input from the LLM/tool args. If a different company_id is supplied,
        we refuse and audit the attempt (defense in depth — tools also
        re-scope by company_id, but the boundary check belongs here).
        """
        tenant = (context.tenant_id or "").strip()
        if not tenant:
            return None, DomainResponse.error_response(
                error="company_id ausente — nao foi possivel identificar a empresa.",
                domain_id="company_settings",
                action_id=action_id,
            )
        supplied = (params.get("company_id") or "").strip()
        if supplied and supplied != tenant:
            logger.warning(
                "[company_settings] tenant mismatch refused: action=%s "
                "context.tenant_id=%s params.company_id=%s user=%s",
                action_id, tenant, supplied, context.user_id,
            )
            return None, DomainResponse.error_response(
                error=(
                    "Operacao bloqueada: company_id informado nao corresponde "
                    "ao tenant autenticado. Tentativa registrada."
                ),
                data={"forbidden": True, "reason": "tenant_mismatch"},
                domain_id="company_settings",
                action_id=action_id,
            )
        return tenant, None

    async def _delegate_section_write(
        self,
        action_id: str,
        params: dict[str, Any],
        context: DomainContext,
    ) -> DomainResponse:
        hints = self._SECTION_FIELD_HINTS[action_id]
        section = hints["section"]
        label = hints["label"]
        company_id, err = self._resolve_tenant(action_id, params, context)
        if err is not None:
            return err

        payload = self._extract_section_payload(action_id, params)
        if not payload:
            return DomainResponse.clarification_response(
                question=(
                    f"Quais campos de {label} voce quer atualizar? "
                    f"Posso salvar: {', '.join(hints['fields'][:6])}."
                ),
                domain_id=self.domain_id,
                action_id=action_id,
            )

        try:
            from app.domains.company_settings.agents.company_tool_registry import (
                _wrap_save_company_section,
            )
            result = await _wrap_save_company_section(
                company_id=company_id,
                section=section,
                data=payload,
                user_id=context.user_id or "system",
            )
        except Exception as exc:
            logger.exception("[company_settings] %s delegate failed: %s", action_id, exc)
            return DomainResponse.error_response(
                error=f"Falha ao salvar {label}: {exc}",
                domain_id=self.domain_id,
                action_id=action_id,
            )

        if not result.get("success"):
            return DomainResponse.error_response(
                error=result.get("message") or f"Falha ao salvar {label}.",
                data=result.get("data") or {},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        return DomainResponse.success_response(
            message=result.get("message") or f"{label.capitalize()} atualizado(a).",
            data={
                **(result.get("data") or {}),
                "navigation_hint": {"page": "Company Settings", "section": "minha-empresa"},
            },
            domain_id=self.domain_id,
            action_id=action_id,
            suggestions=["Abrir tela de Configuracoes", "Continuar onboarding"],
        )

    async def _handle_configure_profile(self, params, context):
        return await self._delegate_section_write("configure_profile", params, context)

    async def _handle_configure_culture(self, params, context):
        return await self._delegate_section_write("configure_culture", params, context)

    async def _handle_configure_tech_stack(self, params, context):
        return await self._delegate_section_write("configure_tech_stack", params, context)

    async def _handle_configure_benefits(self, params, context):
        # Delega para tool dedicada da tabela company_benefits.
        # FairnessGuard L1 + Audit + tenant scoping rodam dentro da tool.
        company_id, err = self._resolve_tenant("configure_benefits", params, context)
        if err is not None:
            return err

        raw = params.get("benefits")
        if raw is None and isinstance(params.get("data"), dict):
            raw = params["data"].get("benefits")
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, list) or not raw:
            return DomainResponse.clarification_response(
                question=(
                    "Quais beneficios voce quer registrar? Me envie uma lista "
                    "(ex.: 'Vale Refeicao', 'Plano de Saude', 'Gympass') ou "
                    "objetos com {name, category, description}."
                ),
                domain_id=self.domain_id,
                action_id="configure_benefits",
                data={"navigation_hint": {
                    "page": "Company Settings",
                    "section": "minha-empresa",
                    "subsection": "beneficios",
                }},
            )

        # Aceita strings simples — converte em {name: ...}
        normalized: list[dict[str, Any]] = []
        for it in raw:
            if isinstance(it, str):
                normalized.append({"name": it.strip()})
            elif isinstance(it, dict):
                normalized.append(it)

        mode = (params.get("mode") or "append").lower()

        try:
            from app.domains.company_settings.agents.company_tool_registry import (
                _wrap_save_company_benefits,
            )
            result = await _wrap_save_company_benefits(
                company_id=company_id,
                benefits=normalized,
                mode=mode,
                user_id=context.user_id or "system",
            )
        except Exception as exc:
            logger.exception("[company_settings] configure_benefits delegate failed: %s", exc)
            return DomainResponse.error_response(
                error=f"Falha ao salvar beneficios: {exc}",
                domain_id=self.domain_id,
                action_id="configure_benefits",
            )

        if not result.get("success"):
            return DomainResponse.error_response(
                error=result.get("message") or "Falha ao salvar beneficios.",
                data=result.get("data") or {},
                domain_id=self.domain_id,
                action_id="configure_benefits",
            )

        return DomainResponse.success_response(
            message=result.get("message") or "Beneficios atualizados.",
            data={
                **(result.get("data") or {}),
                "navigation_hint": {
                    "page": "Company Settings",
                    "section": "minha-empresa",
                    "subsection": "beneficios",
                },
            },
            domain_id=self.domain_id,
            action_id="configure_benefits",
            suggestions=["Abrir Configuracoes > Beneficios", "Continuar onboarding"],
        )

    async def _handle_configure_workforce(self, params, context):
        company_id, err = self._resolve_tenant("configure_workforce", params, context)
        if err is not None:
            return err
        plan_data = params.get("plan_data") or params.get("plan") or []
        if isinstance(plan_data, dict):
            plan_data = [plan_data]
        if not plan_data:
            return DomainResponse.clarification_response(
                question=(
                    "Me envie o planejamento de contratacoes como uma lista de "
                    "{department, role, quantity, deadline, seniority}."
                ),
                domain_id=self.domain_id,
                action_id="configure_workforce",
            )
        try:
            from app.domains.company_settings.agents.company_tool_registry import (
                _wrap_import_workforce_plan,
            )
            result = await _wrap_import_workforce_plan(
                company_id=company_id,
                plan_data=plan_data,
                user_id=context.user_id or "system",
            )
        except Exception as exc:
            logger.exception("[company_settings] configure_workforce delegate failed: %s", exc)
            return DomainResponse.error_response(
                error=f"Falha ao importar planejamento: {exc}",
                domain_id=self.domain_id,
                action_id="configure_workforce",
            )
        if not result.get("success"):
            return DomainResponse.error_response(
                error=result.get("message") or "Falha ao importar planejamento.",
                data=result.get("data") or {},
                domain_id=self.domain_id,
                action_id="configure_workforce",
            )
        return DomainResponse.success_response(
            message=result.get("message") or "Planejamento importado.",
            data={
                **(result.get("data") or {}),
                "navigation_hint": {"page": "Company Settings", "section": "minha-empresa"},
            },
            domain_id=self.domain_id,
            action_id="configure_workforce",
            suggestions=["Revisar plano de contratacoes"],
        )

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
        """Pipeline de processamento de documento institucional — Task #712.

        Aceita texto pre-extraido (`document_text`) OU base64 de PDF/DOCX
        (`document_b64` + `document_format`). Faz extracao de texto se
        necessario, passa por FairnessGuard + PII via tool ja existente e
        retorna campos esperados para revisao humana antes de gravar.
        """
        company_id, err = self._resolve_tenant("process_document", params, context)
        if err is not None:
            return err

        # ------------------------------------------------------------------
        # PHASE 2 — persist after explicit human approval.
        # The chat layer calls back with `confirm=True` + `confirmed_fields`
        # (a dict in the same shape returned by phase 1). We map them to the
        # canonical sections (profile/culture) and write via the existing
        # _wrap_save_company_section tool. Audit trail differentiates this
        # operation as `persist_document_extraction`.
        # ------------------------------------------------------------------
        if params.get("confirm") is True or params.get("persist") is True:
            confirmed = params.get("confirmed_fields") or {}
            if not isinstance(confirmed, dict) or not confirmed:
                return DomainResponse.clarification_response(
                    question=(
                        "Para confirmar a gravacao, me envie `confirmed_fields` "
                        "como um objeto com os campos revisados pela pessoa "
                        "(ex.: {name, mission, values, tech_stack, ...})."
                    ),
                    domain_id=self.domain_id,
                    action_id="process_document",
                )
            # Particiona campos por seccao com base no _SECTION_FIELD_HINTS.
            # `benefits` tem caminho dedicado (tabela company_benefits) e e
            # roteado para _wrap_save_company_benefits — nunca via section.
            buckets: dict[str, dict[str, Any]] = {"profile": {}, "culture": {}}
            for action_key, hints in self._SECTION_FIELD_HINTS.items():
                section = hints["section"]
                for field in hints["fields"]:
                    if field in confirmed and confirmed[field] not in (None, "", []):
                        buckets[section][field] = confirmed[field]
            benefits_payload = confirmed.get("benefits")
            if isinstance(benefits_payload, list) and benefits_payload:
                # Aceita list[str] (nomes) ou list[dict] (entradas completas).
                normalized_benefits = [
                    {"name": b} if isinstance(b, str) else b
                    for b in benefits_payload
                    if (isinstance(b, str) and b.strip())
                    or (isinstance(b, dict) and (b.get("name") or "").strip())
                ]
            else:
                normalized_benefits = []
            try:
                from app.domains.company_settings.agents.company_tool_registry import (
                    _wrap_save_company_section,
                    _wrap_save_company_benefits,
                    _audit_log,
                )
                results = []
                for section, payload in buckets.items():
                    if not payload:
                        continue
                    res = await _wrap_save_company_section(
                        company_id=company_id,
                        section=section,
                        data=payload,
                        user_id=context.user_id or "system",
                    )
                    results.append({"section": section, "result": res})
                if normalized_benefits:
                    res_benefits = await _wrap_save_company_benefits(
                        company_id=company_id,
                        benefits=normalized_benefits,
                        mode="append",
                        user_id=context.user_id or "system",
                    )
                    results.append({"section": "benefits", "result": res_benefits})
                # Audit extra: distingue persistencia oriunda de aprovacao humana
                # de campos extraidos via process_document.
                try:
                    await _audit_log(
                        company_id,
                        "persist_document_extraction",
                        metadata={
                            "user_id": context.user_id or "system",
                            "sections": [r["section"] for r in results],
                            "fields_count": sum(
                                len((r["result"] or {}).get("data", {}).get("fields_saved", []))
                                for r in results
                            ),
                        },
                    )
                except Exception:
                    logger.warning(
                        "[company_settings] audit persist_document_extraction failed",
                        exc_info=True,
                    )
            except Exception as exc:
                logger.exception(
                    "[company_settings] process_document persist failed: %s", exc
                )
                return DomainResponse.error_response(
                    error=f"Falha ao gravar campos confirmados: {exc}",
                    domain_id=self.domain_id,
                    action_id="process_document",
                )
            saved_sections = [r["section"] for r in results
                              if (r["result"] or {}).get("success")]
            failed = [r for r in results if not (r["result"] or {}).get("success")]
            if failed and not saved_sections:
                return DomainResponse.error_response(
                    error="Nenhuma secao foi gravada.",
                    data={"failed": failed},
                    domain_id=self.domain_id,
                    action_id="process_document",
                )
            return DomainResponse.success_response(
                message=(
                    f"Campos confirmados gravados em: {', '.join(saved_sections)}. "
                    "Voce pode revisar em Configuracoes > Minha Empresa."
                ),
                data={
                    "persisted_sections": saved_sections,
                    "results": results,
                    "navigation_hint": {
                        "page": "Company Settings", "section": "minha-empresa",
                    },
                },
                domain_id=self.domain_id,
                action_id="process_document",
                suggestions=["Abrir Configuracoes > Minha Empresa", "Continuar onboarding"],
            )

        document_text = (params.get("document_text") or "").strip()
        document_type = params.get("document_type") or "general"
        if not document_text:
            b64 = params.get("document_b64")
            fmt = (params.get("document_format") or "").lower()
            if b64 and fmt in ("pdf", "docx", "txt"):
                try:
                    import base64
                    raw = base64.b64decode(b64)
                    if fmt == "txt":
                        document_text = raw.decode("utf-8", errors="ignore")
                    elif fmt == "pdf":
                        try:
                            from pypdf import PdfReader
                            from io import BytesIO
                            reader = PdfReader(BytesIO(raw))
                            document_text = "\n".join(
                                (p.extract_text() or "") for p in reader.pages
                            )
                        except Exception as exc:
                            return DomainResponse.error_response(
                                error=f"Falha ao extrair texto do PDF: {exc}",
                                domain_id=self.domain_id,
                                action_id="process_document",
                            )
                    elif fmt == "docx":
                        try:
                            from docx import Document  # type: ignore
                            from io import BytesIO
                            doc = Document(BytesIO(raw))
                            document_text = "\n".join(p.text for p in doc.paragraphs)
                        except Exception as exc:
                            return DomainResponse.error_response(
                                error=f"Falha ao extrair texto do DOCX: {exc}",
                                domain_id=self.domain_id,
                                action_id="process_document",
                            )
                except Exception as exc:
                    return DomainResponse.error_response(
                        error=f"Documento invalido: {exc}",
                        domain_id=self.domain_id,
                        action_id="process_document",
                    )
            else:
                return DomainResponse.clarification_response(
                    question=(
                        "Me envie o texto do documento (campo `document_text`) "
                        "ou um arquivo base64 com `document_b64` + "
                        "`document_format` (pdf, docx ou txt)."
                    ),
                    domain_id=self.domain_id,
                    action_id="process_document",
                )

        if not document_text.strip():
            return DomainResponse.error_response(
                error="O documento nao contem texto extraivel.",
                domain_id=self.domain_id,
                action_id="process_document",
            )

        try:
            from app.domains.company_settings.agents.company_tool_registry import (
                _wrap_process_uploaded_document,
            )
            result = await _wrap_process_uploaded_document(
                company_id=company_id,
                document_text=document_text,
                document_type=document_type,
                user_id=context.user_id or "system",
            )
        except Exception as exc:
            logger.exception("[company_settings] process_document delegate failed: %s", exc)
            return DomainResponse.error_response(
                error=f"Falha ao processar documento: {exc}",
                domain_id=self.domain_id,
                action_id="process_document",
            )

        if not result.get("success"):
            return DomainResponse.error_response(
                error=result.get("message") or "Falha ao processar documento.",
                data=result.get("data") or {},
                domain_id=self.domain_id,
                action_id="process_document",
            )

        data = result.get("data") or {}
        expected = data.get("expected_fields") or []
        msg = (
            f"{result.get('message') or 'Documento processado.'} "
            f"Quer que eu salve {', '.join(expected[:5]) or 'os campos extraidos'}? "
            "Confirme antes — gravacao requer aprovacao humana (LGPD Art. 8)."
        )
        return DomainResponse.success_response(
            message=msg,
            data={
                **data,
                "requires_human_approval": True,
                "navigation_hint": {"page": "Company Settings", "section": "minha-empresa"},
            },
            domain_id=self.domain_id,
            action_id="process_document",
            suggestions=["Revisar campos extraidos", "Confirmar gravacao"],
        )
