"""
TenantAwareAgentMixin — injeção canônica de tenant context em ReActAgents.

Causa raiz endereçada (.local/tasks/canonical-tenant-aware-agent-infra.md):
    O ``MainOrchestrator`` resolve ``TenantContext`` corretamente e empurra
    ``ctx.tenant_context_snippet`` no ``UniversalContext``. O
    ``WizardSessionService`` propaga via ``_CONTEXT_CARRY_KEYS``. O
    ``SystemPromptBuilder.build()`` e o ``PromptComposer.for_domain_runtime()``
    aceitam ``tenant_context_snippet``. **Mas nenhum dos 17 ReActAgents
    propaga adiante** quando override ``_get_runtime_domain_instructions``.
    Resultado: a LIA "esquece" qual empresa está atendendo e pergunta o
    ``company_id`` no chat — apesar do JWT estar correto.

Esta mixin é o ponto canônico de injeção. Agentes herdam de
``TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin`` e ganham:

    1. ``_resolve_tenant_context(input)`` → ``TenantContext`` (com cache de
       request via ``input.metadata['_tenant_ctx_cache']``).
    2. ``_get_tenant_context_snippet(input)`` → ``str`` não-vazio OU
       ``MissingTenantContextError`` quando ``LIA_AGENT_TENANT_STRICT=true``.
    3. Override de ``_get_system_prompt`` que GARANTE que o snippet vai pro
       ``ctx.tenant_context_snippet`` antes do ``LangGraphReActBase`` montar
       o prompt — mesmo se o caller esqueceu de injetar.

Não substitui ``LangGraphReActBase`` nem ``EnhancedAgentMixin`` — soma.

Métricas (in-memory, expostas via ``get_tenant_context_metrics``):
    - ``hit``: snippet veio populado e foi usado
    - ``miss``: snippet veio vazio mas conseguimos resolver via DB
    - ``fail_open``: tenant não resolvível e flag estrita OFF (warning + segue)
    - ``fail_closed``: tenant não resolvível e flag estrita ON (raise)
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from app.shared.exceptions.tenant_errors import (
    InvalidCompanyIdError,
    MissingTenantContextError,
)
from app.shared.value_objects.company_id import CompanyId

if TYPE_CHECKING:
    from lia_agents_core.agent_interface import AgentInput
    from app.shared.services.tenant_context_service import TenantContext

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Feature flag — LIA_AGENT_TENANT_STRICT
# ----------------------------------------------------------------------
# Quando ``True``: ausência/invalidez de tenant levanta
# ``MissingTenantContextError`` (fail-closed canônico).
# Quando ``False``: log warning + degrada para snippet vazio (compat dev).
#
# Default por ambiente (espelha o padrão das 4 flags de bypass — main.py):
#   - production / prod / staging → ``True`` (fail-closed)
#   - development                  → ``False`` (warning-only)
#
# Override via env var ``LIA_AGENT_TENANT_STRICT=true|false|1|0``.
_STRICT_TRUTHY = frozenset({"1", "true", "yes", "on"})
_STRICT_FALSY = frozenset({"0", "false", "no", "off"})
_PROD_LIKE = frozenset({"production", "prod", "staging"})


def is_tenant_strict_mode() -> bool:
    """Resolve a flag em runtime (não cache — testes podem mexer no env)."""
    raw = os.getenv("LIA_AGENT_TENANT_STRICT", "").strip().lower()
    if raw in _STRICT_TRUTHY:
        return True
    if raw in _STRICT_FALSY:
        return False
    # Não setado → default por ambiente
    env = os.getenv("APP_ENV", "development").strip().lower()
    return env in _PROD_LIKE


# ----------------------------------------------------------------------
# Métricas in-memory (mesmo padrão de app/shared/observability/llm_metrics.py)
# ----------------------------------------------------------------------
_METRICS: dict[str, dict[str, int]] = {}


def _record_metric(agent: str, outcome: str) -> None:
    bucket = _METRICS.setdefault(agent, {"hit": 0, "miss": 0, "fail_open": 0, "fail_closed": 0})
    bucket[outcome] = bucket.get(outcome, 0) + 1


def get_tenant_context_metrics() -> dict[str, dict[str, int]]:
    """Snapshot do contador in-memory (canary monitoring + /health)."""
    return {agent: dict(counts) for agent, counts in _METRICS.items()}


def reset_tenant_context_metrics() -> None:
    """Reset usado por testes."""
    _METRICS.clear()


# ----------------------------------------------------------------------
# Mixin
# ----------------------------------------------------------------------
class TenantAwareAgentMixin:
    """Injete em ReActAgents para garantir tenant context no system prompt.

    Ordem de herança recomendada::

        class MyAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
            ...

    O mixin NÃO requer mudanças no ``LangGraphReActBase``: o override de
    ``_get_system_prompt`` injeta o snippet em ``input.context`` antes de
    delegar pro ``super()``.

    Subclasses que QUEREM controle fino podem chamar
    ``self._get_tenant_context_snippet(input)`` diretamente dentro do seu
    ``_get_runtime_domain_instructions(input)`` e passar o resultado pro
    ``PromptComposer.for_domain_runtime(tenant_context_snippet=...)``.
    """

    # Permite a subclasse FORÇAR strict-mode mesmo em dev (agentes que NUNCA
    # podem operar sem tenant — wizard, pipeline, screening). Aceita apenas
    # ``True`` ou ``None``. Bloqueamos ``False`` deliberadamente: enfraquecer
    # fail-closed deve passar SEMPRE pela env ``LIA_AGENT_TENANT_STRICT`` (que
    # é auditável via /health/compliance/bypass-status), nunca por código de
    # agente — senão um override silencioso vira bypass invisível em prod.
    tenant_strict_override: bool | None = None

    # ------------------------------------------------------------------
    # Resolução
    # ------------------------------------------------------------------

    async def _resolve_tenant_context(self, input: "AgentInput") -> "TenantContext | None":
        """Resolve ``TenantContext`` para a request.

        Estratégia:
            1. Se ``input.context['tenant_context']`` já vier populado pelo
               orquestrador → usa direto (cache hit do MainOrchestrator).
            2. Senão, valida ``input.company_id`` via ``CompanyId.parse`` e
               consulta ``TenantContextService.get_context``.
            3. Cacheia o resultado em ``input.metadata['_tenant_ctx_cache']``
               pra evitar rebusca dentro da mesma request.

        Retorna ``None`` quando ``CompanyId.parse`` falha (caller decide
        fail-open/closed via ``_get_tenant_context_snippet``).
        """
        cache = input.metadata.get("_tenant_ctx_cache") if input.metadata else None
        if cache is not None:
            return cache

        # Caller já resolveu (rota feliz — MainOrchestrator)
        ctx_obj = (input.context or {}).get("tenant_context")
        if ctx_obj is not None and hasattr(ctx_obj, "to_prompt_snippet"):
            input.metadata.setdefault("_tenant_ctx_cache", ctx_obj)
            return ctx_obj

        # Fallback: resolver via DB
        try:
            company_id = CompanyId.parse(input.company_id)
        except InvalidCompanyIdError as exc:
            logger.warning(
                "agent_tenant_context_invalid_company_id",
                extra={
                    "agent": self._tenant_aware_agent_name(),
                    "company_id_raw": repr(input.company_id),
                    "reason": exc.details.get("reason"),
                },
            )
            return None

        db = (input.context or {}).get("db")
        if db is None:
            logger.debug(
                "agent_tenant_context_no_db",
                extra={"agent": self._tenant_aware_agent_name(), "company_id": company_id.as_str()},
            )
            return None

        try:
            from app.shared.services.tenant_context_service import TenantContextService
            svc = TenantContextService()
            job_id = (input.context or {}).get("job_id")
            tenant_ctx = await svc.get_context(
                company_id=company_id.as_str(),
                db=db,
                job_id=job_id,
            )
            if input.metadata is not None:
                input.metadata["_tenant_ctx_cache"] = tenant_ctx
            return tenant_ctx
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning(
                "agent_tenant_context_resolve_failed",
                extra={
                    "agent": self._tenant_aware_agent_name(),
                    "company_id": company_id.as_str(),
                    "error": str(exc)[:200],
                },
            )
            return None

    async def _get_tenant_context_snippet(self, input: "AgentInput") -> str:
        """Retorna o snippet pro prompt — fail-closed quando estrito.

        Ordem de busca:
            1. ``input.context['tenant_context_snippet']`` (já injetado pelo
               MainOrchestrator/SSE/WS handlers — caso normal).
            2. ``self._resolve_tenant_context(input).to_prompt_snippet()``.
            3. Em strict-mode → ``MissingTenantContextError``; senão, ``""``.
        """
        agent = self._tenant_aware_agent_name()
        ctx = input.context or {}

        existing = ctx.get("tenant_context_snippet")
        if isinstance(existing, str) and existing.strip():
            _record_metric(agent, "hit")
            return existing

        tenant_ctx = await self._resolve_tenant_context(input)
        if tenant_ctx is not None:
            try:
                snippet = tenant_ctx.to_prompt_snippet()
                if snippet and snippet.strip():
                    # Persiste pro próximo turn dentro da mesma request
                    if input.context is not None:
                        input.context["tenant_context_snippet"] = snippet
                    _record_metric(agent, "miss")
                    return snippet
            except Exception as exc:  # pragma: no cover — defensive
                logger.warning(
                    "agent_tenant_context_snippet_render_failed",
                    extra={"agent": agent, "error": str(exc)[:200]},
                )

        # Sem tenant resolvido — decide fail-open vs fail-closed
        strict = self._is_strict()
        if strict:
            _record_metric(agent, "fail_closed")
            logger.error(
                "agent_tenant_context_missing",
                extra={
                    "agent": agent,
                    "company_id_raw": repr(input.company_id),
                    "tenant_source": "agent_input",
                },
            )
            raise MissingTenantContextError(
                f"Agente '{agent}' invocado sem tenant context resolvível",
                details={
                    "agent": agent,
                    "company_id_raw": repr(input.company_id),
                    "tenant_source": "agent_input",
                },
            )

        _record_metric(agent, "fail_open")
        logger.warning(
            "agent_tenant_context_missing_fail_open",
            extra={
                "agent": agent,
                "company_id_raw": repr(input.company_id),
                "tenant_source": "agent_input",
                "hint": "Set LIA_AGENT_TENANT_STRICT=true to enforce fail-closed.",
            },
        )
        return ""

    # ------------------------------------------------------------------
    # Override que LangGraphReActBase consome automaticamente
    # ------------------------------------------------------------------

    def _get_system_prompt(self, input: "AgentInput") -> str:  # type: ignore[override]
        """Garante ``tenant_context_snippet`` em ``input.context`` antes do super.

        ``LangGraphReActBase._get_system_prompt`` lê
        ``ctx.get("tenant_context_snippet", "")`` e passa pro
        ``SystemPromptBuilder.build()``. Se vier vazio, todo o trabalho do
        ``MainOrchestrator`` se perde no agente.

        Aqui resolvemos sincronamente via ``input.context`` (caso já
        injetado) ou caímos no caminho async-aware via
        ``_resolve_tenant_context_sync_fallback``. Quando o snippet é
        verdadeiramente irrecuperável, deixamos a flag estrita decidir.
        """
        agent = self._tenant_aware_agent_name()
        ctx = input.context if input.context is not None else {}

        snippet = ctx.get("tenant_context_snippet", "")
        if not (isinstance(snippet, str) and snippet.strip()):
            # Tenta TenantContext já resolvido (sem await — síncrono)
            tenant_ctx = ctx.get("tenant_context")
            if tenant_ctx is not None and hasattr(tenant_ctx, "to_prompt_snippet"):
                try:
                    snippet = tenant_ctx.to_prompt_snippet() or ""
                except Exception:  # pragma: no cover
                    snippet = ""

            if snippet and snippet.strip():
                ctx["tenant_context_snippet"] = snippet
                input.context = ctx
                _record_metric(agent, "miss")
            else:
                # Sem snippet e sem TenantContext sync — decide fail-open/closed
                strict = self._is_strict()
                if strict:
                    _record_metric(agent, "fail_closed")
                    logger.error(
                        "agent_tenant_context_missing",
                        extra={
                            "agent": agent,
                            "company_id_raw": repr(input.company_id),
                            "tenant_source": "system_prompt_hook",
                        },
                    )
                    raise MissingTenantContextError(
                        f"Agente '{agent}' invocado sem tenant context resolvível",
                        details={
                            "agent": agent,
                            "company_id_raw": repr(input.company_id),
                            "tenant_source": "system_prompt_hook",
                        },
                    )
                _record_metric(agent, "fail_open")
                logger.warning(
                    "agent_tenant_context_missing_fail_open",
                    extra={
                        "agent": agent,
                        "company_id_raw": repr(input.company_id),
                        "tenant_source": "system_prompt_hook",
                    },
                )
        else:
            _record_metric(agent, "hit")

        # Delega ao LangGraphReActBase (ou outra base) para montar o prompt.
        # ``super()`` é seguro porque a MRO inclui ``LangGraphReActBase`` quando
        # o agente herda na ordem recomendada.
        return super()._get_system_prompt(input)  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _is_strict(self) -> bool:
        """Resolve strict-mode efetivo do agente.

        ``tenant_strict_override`` só pode FORÇAR strict (``True``). Valores
        diferentes de ``True``/``None`` levantam — bloqueamos enfraquecer
        fail-closed via subclasse, exigindo que o opt-out sempre passe pela
        env ``LIA_AGENT_TENANT_STRICT`` (auditável via health endpoint).
        """
        override = self.tenant_strict_override
        if override is True:
            return True
        if override is None:
            return is_tenant_strict_mode()
        # override falsy explícito — proíbe (defesa contra bypass silencioso)
        raise RuntimeError(
            f"{type(self).__name__}.tenant_strict_override deve ser True ou None; "
            "use a env LIA_AGENT_TENANT_STRICT=false para enfraquecer fail-closed "
            "(auditável via /health/compliance/bypass-status)."
        )

    def _tenant_aware_agent_name(self) -> str:
        """Best-effort: usa ``domain_name`` quando exposto, senão class name."""
        name = getattr(self, "domain_name", None)
        if isinstance(name, str) and name:
            return name
        return type(self).__name__
