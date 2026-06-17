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

    1. ``_resolve_tenant_context(input)`` async → ``TenantContext`` (com cache
       por ``(company_id, request_id|session_id)`` em
       ``input.metadata['_tenant_ctx_cache']``).
    2. ``_get_tenant_context_snippet(input)`` async → ``str`` não-vazio OU
       ``MissingTenantContextError`` quando ``LIA_AGENT_TENANT_STRICT=true``.
    3. Override async de ``_process_langgraph`` que PRE-RESOLVE o snippet via
       ``TenantContextService`` ANTES do ``LangGraphReActBase`` chamar o sync
       ``_get_system_prompt`` — fechando o gap "snippet só funciona quando
       caller pré-injeta".
    4. Override sync de ``_get_system_prompt`` como rede de proteção
       (defense-in-depth) — se algum caller pular ``_process_langgraph``,
       a flag estrita ainda decide.
    5. ``_compose_runtime_prompt(input, ...)`` → wrapper canônico de
       ``PromptComposer.for_domain_runtime`` que auto-injeta snippet, pra
       agentes que sobrescrevem ``_get_runtime_domain_instructions``.

Métricas (Prometheus + snapshot in-memory):
    - Counter ``lia_agent_tenant_context_resolved_total{agent,outcome}``
      registrado no canonical metrics registry quando ``prometheus_client``
      está disponível (fail-OPEN se não estiver).
    - Snapshot in-memory exposto via ``get_tenant_context_metrics()`` pro
      endpoint ``/health/compliance/bypass-status`` (continua ativo
      mesmo sem Prometheus).

Outcomes:
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
    from lia_agents_core.agent_interface import AgentInput, AgentOutput
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
# Métricas — Prometheus (canonical) + snapshot in-memory (health endpoint)
# ----------------------------------------------------------------------
_OUTCOMES = ("hit", "miss", "fail_open", "fail_closed")
_METRICS: dict[str, dict[str, int]] = {}

# ----------------------------------------------------------------------
# Rolling-window event log for canary alerting (Task #977)
# ----------------------------------------------------------------------
# `_METRICS` is a monotonic counter — fine pra detectar "alguma vez aconteceu",
# mas o canary precisa de RATE em janela curta (ex: fail_closed > 5/min). Esta
# deque guarda timestamps recentes dos outcomes que interessam (fail_open e
# fail_closed) pra o endpoint `/health/tenant-context-canary` derivar status.
# Eventos mais antigos que `_CANARY_RETENTION_SECONDS` são descartados em
# leitura — sem timer, sem custo de I/O.
import time as _time
from collections import deque as _deque

_CANARY_RETENTION_SECONDS = 600  # 10 min — cobre janela default 60s + folga
_CANARY_EVENTS: "_deque[tuple[float, str, str]]" = _deque(maxlen=10_000)


def _record_canary_event(agent: str, outcome: str) -> None:
    if outcome not in ("fail_open", "fail_closed"):
        return
    _CANARY_EVENTS.append((_time.time(), agent, outcome))


def get_tenant_context_canary_status(window_seconds: int = 60) -> dict[str, Any]:
    """Status canary derivado da janela rolling de outcomes ruins.

    Regras (espelham o spec da Task #977):
      - ``critical`` quando ``fail_closed_per_min > 5`` na janela
        (sinaliza JWT/tenant resolution quebrada — agentes recusando requests).
      - ``warning`` quando ``fail_open_count > 0`` na janela
        (em prod isso NUNCA deveria acontecer — degradação silenciosa).
      - ``ok`` caso contrário.

    Returns:
        dict com ``status``, contadores na janela, threshold e timestamp.
        Canary monitoring decide alerta pelo campo ``status``, não pelo HTTP
        status code (paridade com `/health/compliance/bypass-status`).
    """
    now = _time.time()
    cutoff = now - max(1, window_seconds)
    # Drena eventos antigos da ponta esquerda (deque é FIFO ordenado por t).
    while _CANARY_EVENTS and _CANARY_EVENTS[0][0] < now - _CANARY_RETENTION_SECONDS:
        _CANARY_EVENTS.popleft()

    fail_open = 0
    fail_closed = 0
    by_agent: dict[str, dict[str, int]] = {}
    for ts, agent, outcome in _CANARY_EVENTS:
        if ts < cutoff:
            continue
        bucket = by_agent.setdefault(agent, {"fail_open": 0, "fail_closed": 0})
        bucket[outcome] = bucket.get(outcome, 0) + 1
        if outcome == "fail_open":
            fail_open += 1
        elif outcome == "fail_closed":
            fail_closed += 1

    # Normaliza fail_closed pra rate por minuto (threshold é "5/min")
    fail_closed_per_min = fail_closed * (60.0 / max(1, window_seconds))

    if fail_closed_per_min > 5:
        status = "critical"
        reason = (
            f"fail_closed rate {fail_closed_per_min:.1f}/min > 5/min — "
            "tenant resolution quebrada (JWT inválido ou TenantContextService caindo)"
        )
    elif fail_open > 0:
        status = "warning"
        reason = (
            f"fail_open={fail_open} na janela de {window_seconds}s — "
            "em prod, agentes degradando para 'sua empresa'/'geral' "
            "(LIA_AGENT_TENANT_STRICT deveria estar true)"
        )
    else:
        status = "ok"
        reason = "Sem fail_open/fail_closed na janela"

    return {
        "status": status,
        "reason": reason,
        "window_seconds": window_seconds,
        "fail_open_count": fail_open,
        "fail_closed_count": fail_closed,
        "fail_closed_per_min": round(fail_closed_per_min, 2),
        "threshold_fail_closed_per_min": 5,
        "by_agent": by_agent,
        "strict_mode": is_tenant_strict_mode(),
    }


def reset_tenant_context_canary_events() -> None:
    """Reset usado por testes."""
    _CANARY_EVENTS.clear()

# Counter Prometheus opcional. ``prometheus_client`` é dep transitiva via
# FastAPI/observability stack; se ausente, só atualizamos in-memory.
try:  # pragma: no cover — exercitado via integração
    from prometheus_client import Counter as _PromCounter
    from prometheus_client import REGISTRY as _PROM_REGISTRY

    # Idempotente — se outro import já registrou, reutiliza
    _existing = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(
        "lia_agent_tenant_context_resolved_total"
    )
    if _existing is not None:
        _TENANT_CONTEXT_COUNTER = _existing
    else:
        _TENANT_CONTEXT_COUNTER = _PromCounter(
            "lia_agent_tenant_context_resolved_total",
            "Total de resoluções de tenant context por agente e outcome (T-A canonical).",
            labelnames=("agent", "outcome"),
        )
except Exception:  # pragma: no cover — fail-OPEN se prometheus indisponível
    _TENANT_CONTEXT_COUNTER = None


def _record_metric(agent: str, outcome: str) -> None:
    """Incrementa Prometheus counter (se disponível) + snapshot in-memory."""
    bucket = _METRICS.setdefault(agent, {k: 0 for k in _OUTCOMES})
    bucket[outcome] = bucket.get(outcome, 0) + 1
    if _TENANT_CONTEXT_COUNTER is not None:
        try:
            _TENANT_CONTEXT_COUNTER.labels(agent=agent, outcome=outcome).inc()
        except Exception:  # pragma: no cover — defensive
            pass
    # Task #977: rolling-window canary feed (apenas outcomes "ruins")
    _record_canary_event(agent, outcome)


def get_tenant_context_metrics() -> dict[str, dict[str, int]]:
    """Snapshot do contador in-memory (canary monitoring + /health)."""
    return {agent: dict(counts) for agent, counts in _METRICS.items()}


def reset_tenant_context_metrics() -> None:
    """Reset usado por testes."""
    _METRICS.clear()


# ----------------------------------------------------------------------
# Helper canônico para CALLSITES NON-REACT (Task T-F / R2+R3)
# ----------------------------------------------------------------------
# `FallbackReActService` (caminho de fallback do CascadedRouter) e
# `app/orchestrator/orchestrator.py` invocam `SystemPromptBuilder.build()`
# direto — sem passar pelo mixin acima. Sem este helper, esses dois
# caminhos:
#   - nao emitem `lia_agent_tenant_context_resolved_total`
#   - nao levantam `MissingTenantContextError` em strict-mode
#   - degradam silenciosamente para `tenant_context_snippet=""`
#     -> LIA pergunta company_id no chat (3a recorrencia do bug).
#
# Esta funcao e o equivalente sync canonico das hooks do mixin para
# codigo que NAO e um ReActAgent. Mesma telemetria, mesma decisao
# fail-open/fail-closed.
# ----------------------------------------------------------------------
def resolve_tenant_snippet_for_non_react(
    ctx: dict | None,
    *,
    agent_name: str,
    company_id_raw: Any = None,
) -> str:
    """Resolve `tenant_context_snippet` em callsites que nao usam o mixin.

    Reutiliza a mesma logica de telemetria + fail-open/closed do
    `TenantAwareAgentMixin._get_system_prompt`, expondo um contrato sync
    para servicos non-ReAct (FallbackReActService, Orchestrator V1).

    Estrategia:
      1. `ctx['tenant_context_snippet']` populado -> registra `hit`, retorna.
      2. `ctx['tenant_context']` (TenantContext sync) -> renderiza snippet,
         registra `miss`, retorna.
      3. Sem snippet -> strict-mode levanta `MissingTenantContextError`,
         senao registra `fail_open` e retorna `""`.

    Task #1145: quando ``company_id_raw`` chega ``None``/``""`` E o callsite
    esta executando dentro de uma Celery TenantAwareTask, herda o tenant do
    worker ContextVar — assim codigo legado invocado de dentro de uma task
    nao precisa propagar ``company_id`` explicito ate aqui.
    """
    ctx = ctx or {}

    if company_id_raw in (None, ""):
        try:
            from app.jobs.tenant_aware_task import get_celery_company_id

            _cid_ctx = get_celery_company_id()
        except Exception:  # pragma: no cover — defensive
            _cid_ctx = ""
        if _cid_ctx:
            company_id_raw = _cid_ctx

    snippet = ctx.get("tenant_context_snippet", "")
    if isinstance(snippet, str) and snippet.strip():
        _record_metric(agent_name, "hit")
        return snippet

    tenant_ctx = ctx.get("tenant_context")
    if tenant_ctx is not None and hasattr(tenant_ctx, "to_prompt_snippet"):
        try:
            rendered = tenant_ctx.to_prompt_snippet() or ""
        except Exception:  # pragma: no cover
            rendered = ""
        if rendered.strip():
            ctx["tenant_context_snippet"] = rendered
            _record_metric(agent_name, "miss")
            return rendered

    if is_tenant_strict_mode():
        _record_metric(agent_name, "fail_closed")
        logger.error(
            "agent_tenant_context_missing",
            extra={
                "agent": agent_name,
                "company_id_raw": repr(company_id_raw),
                "tenant_source": "non_react_helper",
            },
        )
        raise MissingTenantContextError(
            f"Callsite '{agent_name}' invocado sem tenant context resolvivel",
            details={
                "agent": agent_name,
                "company_id_raw": repr(company_id_raw),
                "tenant_source": "non_react_helper",
            },
        )

    _record_metric(agent_name, "fail_open")
    logger.warning(
        "agent_tenant_context_missing_fail_open",
        extra={
            "agent": agent_name,
            "company_id_raw": repr(company_id_raw),
            "tenant_source": "non_react_helper",
            "hint": "Set LIA_AGENT_TENANT_STRICT=true to enforce fail-closed.",
        },
    )
    return ""


# ----------------------------------------------------------------------
# Cache key helper
# ----------------------------------------------------------------------
def _cache_key(input: "AgentInput") -> tuple[str, str]:
    """Chave canônica do cache: ``(company_id, request_id|session_id)``.

    Preferimos ``metadata['request_id']`` (injetado pelo middleware HTTP);
    caímos em ``session_id`` quando ausente. Isso garante que duas requests
    diferentes na mesma sessão não compartilhem snippet stale.
    """
    company_raw = str(input.company_id or "")
    metadata = getattr(input, "metadata", None) or {}
    req_id = (
        metadata.get("request_id")
        or metadata.get("trace_id")
        or getattr(input, "session_id", None)
        or ""
    )
    return (company_raw, str(req_id))


# ----------------------------------------------------------------------
# Mixin
# ----------------------------------------------------------------------
class TenantAwareAgentMixin:
    """Injete em ReActAgents para garantir tenant context no system prompt.

    Ordem de herança recomendada::

        class MyAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
            ...

    O mixin opera em duas camadas:

    1. **Pre-resolução async** (caminho normal): ``_process_langgraph``
       é override pra resolver e injetar o snippet em ``input.context``
       ANTES do ``super()._process_langgraph`` chamar
       ``_get_system_prompt`` (sync). Assim o resolver async via DB
       (``TenantContextService``) funciona sem precisar de
       ``asyncio.run`` dentro de hook sync.

    2. **Defense-in-depth sync**: o override de ``_get_system_prompt``
       cobre callers que pularam ``_process_langgraph`` (testes, hooks
       custom). Ele só consegue resolver via cache ou
       ``input.context['tenant_context']`` síncrono — sem hit no DB.

    Subclasses que sobrescrevem ``_get_runtime_domain_instructions`` devem
    chamar ``self._compose_runtime_prompt(input, ...)`` em vez de
    ``PromptComposer.for_domain_runtime`` direto, pra herdar a injeção
    automática do snippet.
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
        """Resolve ``TenantContext`` para a request com cache por
        ``(company_id, request_id|session_id)``.

        Estratégia:
            1. Cache hit → retorna direto.
            2. ``input.context['tenant_context']`` populado pelo orquestrador
               → cacheia + retorna.
            3. Valida ``input.company_id`` via ``CompanyId.parse`` e consulta
               ``TenantContextService.get_context``.

        Retorna ``None`` quando ``CompanyId.parse`` falha ou quando não há
        ``db`` no contexto (caller decide fail-open/closed via
        ``_get_tenant_context_snippet``).
        """
        metadata = getattr(input, "metadata", None) or {}
        cache_store = metadata.get("_tenant_ctx_cache")
        key = _cache_key(input)

        # Cache hit por (company_id, request_id)
        if isinstance(cache_store, dict) and key in cache_store:
            return cache_store[key]

        # Caller já resolveu (rota feliz — MainOrchestrator)
        ctx_obj = (input.context or {}).get("tenant_context")
        if ctx_obj is not None and hasattr(ctx_obj, "to_prompt_snippet"):
            self._cache_put(input, key, ctx_obj)
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
            self._cache_put(input, key, tenant_ctx)
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

    @staticmethod
    def _cache_put(input: "AgentInput", key: tuple[str, str], value: Any) -> None:
        """Insere no cache ``input.metadata['_tenant_ctx_cache'][key] = value``."""
        metadata = getattr(input, "metadata", None)
        if metadata is None:
            return
        store = metadata.get("_tenant_ctx_cache")
        if not isinstance(store, dict):
            store = {}
            metadata["_tenant_ctx_cache"] = store
        store[key] = value

    @staticmethod
    def _is_snippet_degraded(snippet: str) -> bool:
        """True quando o snippet existe mas carrega o fallback genérico.

        Task #1043 / PR-C. Origem: ``TenantContextService`` retorna
        ``company_name="sua empresa"`` (e ``sector="geral"``) quando não
        encontra a row em ``companies`` — sintaticamente o snippet não é
        vazio, mas semanticamente é inútil. Em strict-mode esse é o gatilho
        clássico do T-E ("LIA pergunta company_id no chat") porque o LLM,
        sem nome real do tenant, regride a perguntar identidade ao
        recrutador. Para fail-LOUD ao invés de fail-OPEN silencioso, este
        helper detecta os marcadores conhecidos do fallback.
        """
        if not snippet:
            return True
        s = snippet.lower()
        # Marcadores literais do fallback canônico em
        # ``app/shared/services/tenant_context_service.py`` (linhas 176/193):
        # ``company_name="sua empresa"``.
        return "**sua empresa**" in s or "sua empresa," in s or "sua empresa." in s

    async def _get_tenant_context_snippet(self, input: "AgentInput") -> str:
        """Retorna o snippet pro prompt — fail-closed quando estrito.

        Ordem de busca:
            1. ``input.context['tenant_context_snippet']`` (já injetado pelo
               MainOrchestrator/SSE/WS handlers — caso normal).
            2. ``self._resolve_tenant_context(input).to_prompt_snippet()``.
            3. Em strict-mode → ``MissingTenantContextError``; senão, ``""``.

        T-1043 / PR-C: snippets *degradados* (com o fallback ``"sua
        empresa"``) também levantam em strict-mode — fail-LOUD em vez de
        injetar contexto semanticamente vazio.
        """
        agent = self._tenant_aware_agent_name()
        ctx = input.context or {}

        existing = ctx.get("tenant_context_snippet")
        if isinstance(existing, str) and existing.strip():
            if self._is_snippet_degraded(existing) and self._is_strict():
                _record_metric(agent, "fail_closed")
                logger.error(
                    "agent_tenant_context_degraded",
                    extra={
                        "agent": agent,
                        "company_id_raw": repr(input.company_id),
                        "tenant_source": "agent_input_degraded",
                    },
                )
                raise MissingTenantContextError(
                    f"Agente '{agent}' recebeu tenant_context_snippet degradado "
                    f"(fallback 'sua empresa') — fail-LOUD em strict-mode (T-1043 PR-C).",
                    details={
                        "agent": agent,
                        "company_id_raw": repr(input.company_id),
                        "tenant_source": "agent_input_degraded",
                    },
                )
            _record_metric(agent, "hit")
            return existing

        tenant_ctx = await self._resolve_tenant_context(input)
        if tenant_ctx is not None:
            try:
                snippet = tenant_ctx.to_prompt_snippet()
                if snippet and snippet.strip():
                    # T-1043 / PR-C: snippet recém-renderizado também passa pelo
                    # filtro de degradação. ``TenantContextService`` retorna
                    # ``company_name="sua empresa"`` quando a row de companies
                    # não resolve — em strict-mode isso é fail-LOUD.
                    if self._is_snippet_degraded(snippet) and self._is_strict():
                        _record_metric(agent, "fail_closed")
                        logger.error(
                            "agent_tenant_context_degraded",
                            extra={
                                "agent": agent,
                                "company_id_raw": repr(input.company_id),
                                "tenant_source": "freshly_rendered_degraded",
                            },
                        )
                        raise MissingTenantContextError(
                            f"Agente '{agent}' renderizou tenant snippet degradado "
                            f"(fallback 'sua empresa') a partir de tenant_ctx — "
                            f"fail-LOUD em strict-mode (T-1043 PR-C).",
                            details={
                                "agent": agent,
                                "company_id_raw": repr(input.company_id),
                                "tenant_source": "freshly_rendered_degraded",
                            },
                        )
                    # Persiste pro próximo turn dentro da mesma request
                    if input.context is not None:
                        input.context["tenant_context_snippet"] = snippet
                    _record_metric(agent, "miss")
                    return snippet
            except MissingTenantContextError:
                raise
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
    # Pre-resolução async — gancho canônico no fluxo do LangGraphReActBase
    # ------------------------------------------------------------------

    async def _process_langgraph(self, input: "AgentInput") -> "AgentOutput":
        """Pre-resolve tenant snippet antes do super() async rodar.

        ``LangGraphReActBase._process_langgraph`` chama ``_get_system_prompt``
        (sync) na linha 190. Como o resolver via DB é async, precisamos
        garantir que o snippet já esteja em ``input.context`` ANTES desse
        ponto. Esta override roda primeiro a resolução async (com cache)
        e depois delega pro super.

        Em strict-mode, falha aqui já levanta ``MissingTenantContextError``
        — request rejeitada antes de qualquer chamada LLM.
        """
        # Garante snippet via caminho async (cache + DB fallback)
        snippet = await self._get_tenant_context_snippet(input)
        if snippet and input.context is not None:
            input.context["tenant_context_snippet"] = snippet

        return await super()._process_langgraph(input)  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Override sync — defense-in-depth (callers que pularam pre-resolução)
    # ------------------------------------------------------------------

    def _get_system_prompt(self, input: "AgentInput") -> str:  # type: ignore[override]
        """Garante ``tenant_context_snippet`` em ``input.context`` antes do super.

        ``LangGraphReActBase._get_system_prompt`` lê
        ``ctx.get("tenant_context_snippet", "")`` e passa pro
        ``SystemPromptBuilder.build()``. Se vier vazio, todo o trabalho do
        ``MainOrchestrator`` se perde no agente.

        No fluxo normal, ``_process_langgraph`` (override acima) já populou
        o snippet via caminho async. Esta hook é defense-in-depth pra
        callers que invocam ``_get_system_prompt`` direto (testes, hooks
        custom): tenta resolver via cache ou ``tenant_context`` sync; se
        falhar, deixa a flag estrita decidir.
        """
        agent = self._tenant_aware_agent_name()
        ctx = input.context if input.context is not None else {}

        snippet = ctx.get("tenant_context_snippet", "")
        if not (isinstance(snippet, str) and snippet.strip()):
            # Tenta cache (populado por _resolve_tenant_context)
            cached = None
            metadata = getattr(input, "metadata", None) or {}
            store = metadata.get("_tenant_ctx_cache")
            if isinstance(store, dict):
                cached = store.get(_cache_key(input))

            tenant_ctx = cached if cached is not None else ctx.get("tenant_context")
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
    # Helper canônico pra agentes que sobrescrevem _get_runtime_domain_instructions
    # ------------------------------------------------------------------

    def _compose_runtime_prompt(
        self,
        input: "AgentInput",
        *,
        agent_type: str | None = None,
        domain_specific: str = "",
        few_shot_examples: str = "",
        reasoning_template: str = "",
        memory_summary: str = "",
        stage_context: str = "",
        memory_summary_fallback: str | None = None,
    ) -> Any:
        """Wrapper canônico de ``PromptComposer.for_domain_runtime`` que
        auto-injeta ``tenant_context_snippet`` lido de ``input.context``.

        Subclasses que sobrescrevem ``_get_runtime_domain_instructions``
        devem usar este helper (em vez de chamar
        ``PromptComposer.for_domain_runtime`` direto) pra garantir que o
        snippet já resolvido pelo mixin chega ao composer.

        Nota: a resolução real é feita em ``_process_langgraph``
        (async, com DB fallback). Este helper é puramente sync e lê o
        snippet já populado no contexto.
        """
        from app.shared.prompts.prompt_composer import PromptComposer

        ctx = input.context or {}
        snippet = ctx.get("tenant_context_snippet", "") or ""

        # T-D: agentes onde agent_type (chave YAML) ≠ domain_name (cv_screening_pipeline,
        # jobs_mgmt, etc.) precisam preservar a chave YAML original. Aceita override
        # explícito; default é domain_name.
        effective_agent_type = agent_type or self._tenant_aware_agent_name()
        kwargs: dict[str, Any] = dict(
            agent_type=effective_agent_type,
            domain_specific=domain_specific,
            few_shot_examples=few_shot_examples,
            reasoning_template=reasoning_template,
            memory_summary=memory_summary,
            stage_context=stage_context,
            tenant_context_snippet=snippet,
        )
        if memory_summary_fallback is not None:
            kwargs["memory_summary_fallback"] = memory_summary_fallback
        return PromptComposer.for_domain_runtime(**kwargs)

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
