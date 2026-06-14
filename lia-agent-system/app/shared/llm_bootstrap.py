"""
LLM Bootstrap — Monkey-patches SDK constructors to enforce tenant context,
PII stripping, and audit logging on ALL LLM calls system-wide.

This module patches:
  - anthropic.Anthropic / AsyncAnthropic: inject API key + audit
  - anthropic.Anthropic.messages.create/stream: PII strip + audit
  - google.genai.Client: inject API key + audit
  - openai.OpenAI / AsyncOpenAI: inject API key + audit

Call install_llm_guards() ONCE at app startup (in main.py) before any
other module instantiates an LLM client.

This is the "nuclear option" — it intercepts ALL SDK usage regardless
of whether the caller goes through LLMService or not.
"""
import functools
import inspect
import logging
import os
import time
import traceback

logger = logging.getLogger(__name__)

_installed = False


# ---------------------------------------------------------------------------
# Wave 3 (2026-05-22) — Universal ai_credit_gate enforcement
# ---------------------------------------------------------------------------
# Wraps SDK message creation primitives with a per-call credit gate that reads
# the tenant company_id from the same ContextVar used by tool_handler and the
# orchestrator. Closes the coverage gap identified by the AI credits audit
# (~/Documents/wedotalent_audit_2026-05-21/audit_ai_credits_templates.md):
# 7+ domain services (intake_extractor, voice_service, interview_scheduling,
# multimodal_service, agent_quality_evaluator, wsi_question_generator fallback
# paths, wizard_supervisor_classifier) bypass llm_factory and call the SDK
# directly. Monkey-patching the SDK constructors here is the single chokepoint
# that catches all of them universally.
#
# Defense-in-depth: gates in llm_factory / orchestrator / agentic_loop stay.
# This is the floor, not the ceiling.

def _estimate_tokens_anthropic(kwargs: dict) -> int:
    """Rough estimate of total tokens for an Anthropic messages.create call."""
    messages = kwargs.get("messages", []) or []
    prompt_chars = 0
    for m in messages:
        content = m.get("content", "") if isinstance(m, dict) else ""
        if isinstance(content, str):
            prompt_chars += len(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    prompt_chars += len(block.get("text", "") or "")
    system = kwargs.get("system", "")
    if isinstance(system, str):
        prompt_chars += len(system)
    prompt_tokens = prompt_chars // 4  # ~4 chars per token heuristic
    max_tokens = int(kwargs.get("max_tokens", 1024) or 0)
    return prompt_tokens + max_tokens


def _estimate_tokens_openai(kwargs: dict) -> int:
    """Rough estimate for openai chat.completions.create."""
    messages = kwargs.get("messages", []) or []
    chars = 0
    for m in messages:
        if isinstance(m, dict):
            c = m.get("content", "") or ""
            if isinstance(c, str):
                chars += len(c)
            elif isinstance(c, list):
                for block in c:
                    if isinstance(block, dict):
                        chars += len(block.get("text", "") or "")
    max_tokens = int(kwargs.get("max_tokens") or kwargs.get("max_completion_tokens") or 1024)
    return (chars // 4) + max_tokens


def _estimate_tokens_genai(kwargs: dict) -> int:
    """Rough estimate for google.genai generate_content."""
    contents = kwargs.get("contents") or kwargs.get("content") or ""
    chars = 0
    if isinstance(contents, str):
        chars = len(contents)
    elif isinstance(contents, list):
        for c in contents:
            if isinstance(c, str):
                chars += len(c)
            elif isinstance(c, dict):
                parts = c.get("parts", []) or []
                for p in parts:
                    if isinstance(p, dict):
                        chars += len(p.get("text", "") or "")
                    elif isinstance(p, str):
                        chars += len(p)
    cfg = kwargs.get("config") or kwargs.get("generation_config") or {}
    if hasattr(cfg, "max_output_tokens"):
        max_tokens = int(getattr(cfg, "max_output_tokens", 0) or 1024)
    elif isinstance(cfg, dict):
        max_tokens = int(cfg.get("max_output_tokens") or 1024)
    else:
        max_tokens = 1024
    return (chars // 4) + max_tokens


def _infer_service_from_caller() -> str:
    """Walk the stack from outer-most to inner-most to find the first
    application frame and return a coarse service identifier (filename
    without extension).

    Used as label for ai_credit_gate_calls_total + service param on
    AICreditExhausted. Keeps cardinality bounded (one label per file).

    Stack-walk order: outermost first. We want the OUTER application frame
    that initiated the call chain (e.g. wsi_question_generator.py) — not
    the inner-most non-system frame (which would still be the test runner
    when invoked under pytest). So we keep the first matching frame and
    return it.
    """
    SKIP_SUBSTRINGS = (
        "llm_bootstrap",
        "anthropic/",
        "openai/",
        "google/",
        "site-packages",
        "_bootstrap",
        "<frozen",
        "runpy",
        "_pytest",
        "pluggy",
        "/asyncio/",
        "unittest/",
        # Pytest entrypoint script (e.g. /path/.pythonlibs/bin/pytest).
        # The basename `pytest` would otherwise become the inferred service
        # under test runs — skipping it lets the next-newest application
        # frame (the actual test file or service module) win.
        "bin/pytest",
    )
    try:
        # extract_stack returns oldest -> newest; we want the OUTER-most
        # application frame (the one that initiated the LLM call).
        for frame_info in traceback.extract_stack():
            fname = frame_info.filename
            if any(s in fname for s in SKIP_SUBSTRINGS):
                continue
            base = fname.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            if base:
                return base[:48]
    except Exception:
        pass
    return "unknown"


def _emit_gate_call_metric(provider: str, service: str, outcome: str) -> None:
    """Best-effort emit of ai_credit_gate_calls_total. Non-blocking."""
    try:
        from app.shared.observability.canary_metrics import ai_credit_gate_calls_total
        if ai_credit_gate_calls_total is None:
            return
        ai_credit_gate_calls_total.labels(
            provider=provider, service=service, outcome=outcome
        ).inc()
    except Exception:
        pass


def _enforce_credit_gate_sync(provider: str, kwargs: dict, *, estimator) -> None:
    """Synchronous wrapper around async check_credit_budget. Used for sync SDK
    methods (anthropic.Anthropic.messages.create). Reads company_id from the
    ContextVar populated by auth_enforcement middleware.

    Fail-closed for AICreditExhausted (bubbles up). Fail-safe for everything
    else (logs + allows) — consistent with check_credit_budget default.

    Empty company_id: emits metric `outcome=no_context` and ALLOWS the call.
    Anti-pattern: hard-failing here would break every test fixture, internal
    cron, and background job that doesn't go through the HTTP middleware.
    Defense-in-depth is in llm_factory / orchestrator / agentic_loop.
    """
    company_id = _get_tenant_id()
    service = _infer_service_from_caller()
    if not company_id:
        _emit_gate_call_metric(provider, service, "no_context")
        logger.debug(
            "[LLM-CreditGate] no company_id in ContextVar (caller=%s, provider=%s) — skipping gate (fail-safe ALLOW)",
            service, provider,
        )
        return

    estimated = max(0, int(estimator(kwargs)))
    try:
        import asyncio
        from app.shared.services.ai_credit_gate import check_credit_budget, AICreditExhausted

        async def _gated():
            from lia_config.database import AsyncSessionLocal
            async with AsyncSessionLocal() as _credit_db:
                await check_credit_budget(
                    _credit_db,
                    company_id,
                    estimated_tokens=estimated,
                    service=service,
                )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # P0 fix (2026-05-22 — REGRA 4 fail-loud, no silent swallow):
            # caller is in a running event loop but reached the SYNC gate.
            # This means an async caller hit a sync-patched SDK method —
            # which after the _patch_messages_api refactor should NEVER
            # happen for AsyncAnthropic. If it does, the SDK detection in
            # the patcher regressed; raise loudly so the bug surfaces.
            raise RuntimeError(
                "_enforce_credit_gate_sync called from running event loop. "
                "This is a bug — async caller should hit "
                "_enforce_credit_gate_async via the async-patched SDK seam. "
                f"provider={provider} service={service}. "
                "If you intentionally need sync-in-async, run the sync SDK "
                "call inside asyncio.to_thread(...)."
            )
        else:
            asyncio.run(_gated())

        _emit_gate_call_metric(provider, service, "allowed")
    except Exception as exc:
        # AICreditExhausted is a subclass of Exception too — catch first
        try:
            from app.shared.services.ai_credit_gate import AICreditExhausted as _AICE
            if isinstance(exc, _AICE):
                _emit_gate_call_metric(provider, service, "exhausted")
                raise
        except ImportError:
            pass
        # REGRA 4 (2026-05-22): re-raise RuntimeError instead of swallowing.
        # The new fail-loud path in this function raises RuntimeError when
        # called from a running event loop — that signals a harness bug
        # (sync-in-async routing) and must surface, NOT be silently turned
        # into a fail-safe ALLOW (which previously caused the P0 audit
        # finding: silent bypass of credit gate for AsyncAnthropic).
        if isinstance(exc, RuntimeError):
            _emit_gate_call_metric(provider, service, "error")
            raise
        # Fail-safe ALLOW for other unexpected errors (DB outage, import failure)
        _emit_gate_call_metric(provider, service, "error")
        logger.warning(
            "[LLM-CreditGate] sync gate failed (fail-safe ALLOW) provider=%s service=%s: %s",
            provider, service, exc,
        )


async def _enforce_credit_gate_async(provider: str, kwargs: dict, *, estimator) -> None:
    """Async variant — used for AsyncAnthropic / AsyncOpenAI / genai.aio."""
    company_id = _get_tenant_id()
    service = _infer_service_from_caller()
    if not company_id:
        _emit_gate_call_metric(provider, service, "no_context")
        logger.debug(
            "[LLM-CreditGate] no company_id in ContextVar (caller=%s, provider=%s) — skipping gate (fail-safe ALLOW)",
            service, provider,
        )
        return

    estimated = max(0, int(estimator(kwargs)))
    try:
        from app.shared.services.ai_credit_gate import check_credit_budget, AICreditExhausted
        from lia_config.database import AsyncSessionLocal
        async with AsyncSessionLocal() as _credit_db:
            await check_credit_budget(
                _credit_db,
                company_id,
                estimated_tokens=estimated,
                service=service,
            )
        _emit_gate_call_metric(provider, service, "allowed")
    except Exception as exc:
        try:
            from app.shared.services.ai_credit_gate import AICreditExhausted as _AICE
            if isinstance(exc, _AICE):
                _emit_gate_call_metric(provider, service, "exhausted")
                raise
        except ImportError:
            pass
        _emit_gate_call_metric(provider, service, "error")
        logger.warning(
            "[LLM-CreditGate] async gate failed (fail-safe ALLOW) provider=%s service=%s: %s",
            provider, service, exc,
        )




def _get_tenant_id() -> str:
    """Get current tenant from contextvar (set by auth middleware)."""
    try:
        from app.middleware.auth_enforcement import _current_company_id
        return _current_company_id.get("")
    except (ImportError, LookupError):
        return ""


def _get_tenant_key_sync(provider: str) -> str | None:
    """Read BYOK tenant API key from in-memory cache (sync).

    The cache (_tenant_configs) is populated asynchronously on first
    get_tenant_llm_config() call. On cache miss (e.g. first request)
    we return None so the caller falls back to the env var — no blocking,
    no regression.

    provider: "anthropic" | "openai" | "gemini"
    """
    company_id = _get_tenant_id()
    if not company_id:
        return None
    try:
        from app.shared.tenant_llm_context import _tenant_configs
        config = _tenant_configs.get(company_id)
        if not config:
            return None
        key = config.get("providers", {}).get(provider, {}).get("api_key")
        if key and isinstance(key, str) and key.strip() and "..." not in key:
            return key.strip()
    except Exception:
        pass
    return None


def _get_caller() -> str:
    """Get the caller's file:line for audit trail."""
    for frame_info in traceback.extract_stack():
        fname = frame_info.filename
        if (
            "llm_bootstrap" not in fname
            and "anthropic/" not in fname
            and "openai/" not in fname
            and "google/" not in fname
            and "site-packages" not in fname
        ):
            last_app_frame = f"{fname}:{frame_info.lineno}"
    return last_app_frame if 'last_app_frame' in dir() else "unknown"


def _strip_pii(text: str) -> str:
    """PII stripping — delegates to existing module."""
    try:
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        return strip_pii_for_llm_prompt(text)
    except Exception:
        return text


def _strip_pii_from_messages(messages: list) -> list:
    """Strip PII from message content in-place (Anthropic/OpenAI format)."""
    if not messages:
        return messages
    stripped = []
    for msg in messages:
        if isinstance(msg, dict):
            new_msg = dict(msg)
            content = new_msg.get("content", "")
            if isinstance(content, str):
                new_msg["content"] = _strip_pii(content)
            elif isinstance(content, list):
                new_content = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        new_content.append({**block, "text": _strip_pii(block.get("text", ""))})
                    else:
                        new_content.append(block)
                new_msg["content"] = new_content
            stripped.append(new_msg)
        else:
            stripped.append(msg)
    return stripped


def _audit_log(provider: str, action: str, model: str = "", latency_ms: float = 0, **extra):
    """Lightweight audit log — no DB dependency, just structured logging."""
    tenant = _get_tenant_id()
    logger.info(
        "[LLM-AUDIT] provider=%s action=%s model=%s tenant=%s latency_ms=%.0f caller=%s %s",
        provider, action, model, tenant or "global",
        latency_ms, extra.get("caller", ""), 
        " ".join(f"{k}={v}" for k, v in extra.items() if k != "caller")
    )


# ---------------------------------------------------------------------------
# Anthropic patches
# ---------------------------------------------------------------------------

# Upstream defaults that LangChain ``ChatAnthropic`` and the raw Anthropic
# SDK auto-populate when no explicit ``base_url`` is provided. The bootstrap
# treats these as "no explicit override" so the proxy URL (configured via
# ``AI_INTEGRATIONS_ANTHROPIC_BASE_URL``) replaces them. Source: SDK
# ``DEFAULT_BASE_URL`` + ``ChatAnthropic.anthropic_api_url`` Field default.
_DEFAULT_ANTHROPIC_BASE_URLS: frozenset[str] = frozenset({
    "https://api.anthropic.com",
    "https://api.anthropic.com/",
})


def _is_default_anthropic_base_url(value: object) -> bool:
    """Return True when ``value`` is one of the upstream Anthropic defaults.

    Used by ``_inject_anthropic_env`` to decide whether the kwargs
    ``base_url`` represents an explicit caller override (leave alone) or
    the LangChain/SDK default that should be replaced by the modelfarm
    proxy URL.
    """
    if not isinstance(value, str):
        return False
    return value.rstrip("/") in {u.rstrip("/") for u in _DEFAULT_ANTHROPIC_BASE_URLS}


def _patch_anthropic() -> bool:
    """Patch anthropic.Anthropic and AsyncAnthropic constructors + messages."""
    try:
        import anthropic
    except ImportError:
        logger.debug("[LLM-Bootstrap] anthropic not installed, skipping patch")
        return False

    _orig_init = anthropic.Anthropic.__init__
    _orig_async_init = anthropic.AsyncAnthropic.__init__

    def _inject_anthropic_env(kwargs: dict) -> None:
        """Task #1164 — Bug D fix (extends Task #1161 Bug A): override the
        LangChain ``ChatAnthropic`` default ``base_url`` with the modelfarm
        proxy when configured.

        History:
          - #1161 Bug A: injected ``base_url`` only when caller passed
            nothing in kwargs. Fixed callsites that passed ``api_key=``
            explicitly via raw ``anthropic.Anthropic``.
          - #1164 Bug D: ``langchain_anthropic.ChatAnthropic._client_params``
            ALWAYS sets ``base_url=self.anthropic_api_url`` (default
            ``"https://api.anthropic.com"`` via ``from_env``). So kwargs
            arrives with ``base_url`` already populated → the previous
            guard ``"base_url" not in kwargs`` skipped injection → every
            ChatAnthropic instance (jd_enrichment, wsi_questions,
            bigfive via ``create_tracked_llm``) bypassed the proxy and
            hit ``api.anthropic.com`` directly with the wrapper key →
            401 invalid x-api-key. Diagnosed in Task #1164.

        Resolution:
          - ``api_key`` injection still gated on caller absence (don't
            override an explicit tenant key).
          - ``base_url`` injection now runs whenever the env var is set
            AND kwargs lacks an explicit non-default value. The set
            ``_DEFAULT_ANTHROPIC_BASE_URLS`` enumerates the upstream
            defaults the SDK / LangChain wrapper auto-populate; matching
            those is treated as "no explicit override" and we replace
            them with the proxy URL.

        In prod the env var is unset → no-op for both paths. In
        dev/staging it points at the local modelfarm proxy → every
        Anthropic client routes through it, including the LangChain
        wrapper.
        """
        if "api_key" not in kwargs:
            kwargs["api_key"] = (
                _get_tenant_key_sync("anthropic")
                or os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
                or os.environ.get("ANTHROPIC_API_KEY")
            )
        base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
        if base_url:
            current = kwargs.get("base_url")
            if current is None or _is_default_anthropic_base_url(current):
                kwargs["base_url"] = base_url

    @functools.wraps(_orig_init)
    def _patched_init(self, *args, **kwargs):
        if not args:
            _inject_anthropic_env(kwargs)
        _orig_init(self, *args, **kwargs)
        # Patch messages.create and messages.stream on this instance
        _patch_messages_api(self, "anthropic")

    @functools.wraps(_orig_async_init)
    def _patched_async_init(self, *args, **kwargs):
        if not args:
            _inject_anthropic_env(kwargs)
        _orig_async_init(self, *args, **kwargs)
        _patch_messages_api(self, "anthropic-async")

    anthropic.Anthropic.__init__ = _patched_init
    anthropic.AsyncAnthropic.__init__ = _patched_async_init
    logger.info("[LLM-Bootstrap] Anthropic SDK patched (API key injection + PII + audit)")
    return True


def _is_async_method(method) -> bool:
    """Robust detector: ``inspect.iscoroutinefunction`` returns False for
    SDK methods wrapped by decorators that don't preserve ``CO_COROUTINE``
    (e.g., Anthropic's ``_utils.required_args`` decorator wraps an
    ``async def`` and exposes the real one only via ``__wrapped__``).

    Detection cascade:
      1. ``inspect.iscoroutinefunction(method)`` — succeeds for unwrapped
         async functions and ``unittest.mock.AsyncMock``.
      2. ``inspect.iscoroutinefunction(method.__wrapped__)`` — handles
         ``functools.wraps``-style decorators on async defs.
      3. Method class name starts with ``Async`` — final fallback for SDKs
         that don't expose ``__wrapped__`` (Anthropic's ``AsyncMessages``
         vs ``Messages`` follows this convention reliably).
    """
    if inspect.iscoroutinefunction(method):
        return True
    wrapped = getattr(method, "__wrapped__", None)
    if wrapped is not None and inspect.iscoroutinefunction(wrapped):
        return True
    # Final fallback: introspect the owning class. ``self.__class__.__name__``
    # is the canonical seam (e.g., ``AsyncMessages`` for AsyncAnthropic).
    self_obj = getattr(method, "__self__", None)
    if self_obj is not None:
        cls_name = type(self_obj).__name__
        if cls_name.startswith("Async"):
            return True
    return False


def _patch_messages_api(client_instance, provider_label: str):
    """Patch messages.create() and messages.stream() on a client instance.

    P0 fix (2026-05-22 — async-from-sync): detects coroutine vs sync via
    ``inspect.iscoroutinefunction`` and routes each path through the
    matching gate helper (``_enforce_credit_gate_async`` vs
    ``_enforce_credit_gate_sync``). Before this fix, AsyncAnthropic's
    ``messages.create`` was patched with a sync wrapper that called
    ``_enforce_credit_gate_sync`` from inside the running event loop, which
    raised RuntimeError that was silently swallowed → fail-safe ALLOW →
    REGRA 4 violation. Now sync-from-sync and async-from-async only.
    """
    if not hasattr(client_instance, "messages"):
        return

    messages_obj = client_instance.messages

    # Only patch once per instance
    if getattr(messages_obj, "_lia_patched", False):
        return
    messages_obj._lia_patched = True

    _orig_create = messages_obj.create
    is_async = _is_async_method(_orig_create)

    if is_async:
        @functools.wraps(_orig_create)
        async def _patched_create_async(*args, **kwargs):
            caller = _get_caller()
            company_id = _get_tenant_id()
            estimated = max(0, int(_estimate_tokens_anthropic(kwargs)))
            await _enforce_credit_gate_async(
                provider_label, kwargs, estimator=_estimate_tokens_anthropic
            )
            if "messages" in kwargs:
                kwargs["messages"] = _strip_pii_from_messages(kwargs["messages"])
            if "system" in kwargs and isinstance(kwargs["system"], str):
                kwargs["system"] = _strip_pii(kwargs["system"])

            model = kwargs.get("model", "unknown")
            start = time.time()
            try:
                result = await _orig_create(*args, **kwargs)
                latency = (time.time() - start) * 1000
                _audit_log(provider_label, "messages.create", model=model,
                           latency_ms=latency, caller=caller)
                actual = _extract_response_usage_tokens(result)
                if company_id and actual > 0:
                    await reconcile_credits(
                        company_id, estimated, actual, service=provider_label
                    )
                return result
            except Exception as e:
                latency = (time.time() - start) * 1000
                _audit_log(provider_label, "messages.create.ERROR", model=model,
                           latency_ms=latency, caller=caller, error=str(e)[:100])
                raise

        messages_obj.create = _patched_create_async
    else:
        @functools.wraps(_orig_create)
        def _patched_create(*args, **kwargs):
            caller = _get_caller()
            company_id = _get_tenant_id()
            estimated = max(0, int(_estimate_tokens_anthropic(kwargs)))
            _enforce_credit_gate_sync(provider_label, kwargs, estimator=_estimate_tokens_anthropic)
            if "messages" in kwargs:
                kwargs["messages"] = _strip_pii_from_messages(kwargs["messages"])
            if "system" in kwargs and isinstance(kwargs["system"], str):
                kwargs["system"] = _strip_pii(kwargs["system"])

            model = kwargs.get("model", "unknown")
            start = time.time()
            try:
                result = _orig_create(*args, **kwargs)
                latency = (time.time() - start) * 1000
                _audit_log(provider_label, "messages.create", model=model,
                           latency_ms=latency, caller=caller)
                actual = _extract_response_usage_tokens(result)
                if company_id and actual > 0:
                    _reconcile_sync(company_id, estimated, actual, service=provider_label)
                return result
            except Exception as e:
                latency = (time.time() - start) * 1000
                _audit_log(provider_label, "messages.create.ERROR", model=model,
                           latency_ms=latency, caller=caller, error=str(e)[:100])
                raise

        messages_obj.create = _patched_create

    logger.info(
        "[LLM-Bootstrap] Patched %s messages.create (%s)",
        provider_label, "async" if is_async else "sync",
    )

    # Patch stream if it exists
    if hasattr(messages_obj, "stream"):
        _orig_stream = messages_obj.stream

        @functools.wraps(_orig_stream)
        def _patched_stream(*args, **kwargs):
            caller = _get_caller()
            company_id = _get_tenant_id()
            estimated = max(0, int(_estimate_tokens_anthropic(kwargs)))
            # Fix 2026-06-04: cliente SYNC -> gate sync aqui; cliente ASYNC ->
            # gate enforcado no __aenter__ async do reconciler (stream() e sync,
            # nao pode await; o gate sync no event loop levantava RuntimeError).
            _gate_kwargs = None
            if is_async:
                _gate_kwargs = dict(kwargs)
            else:
                _enforce_credit_gate_sync(provider_label, kwargs, estimator=_estimate_tokens_anthropic)
            if "messages" in kwargs:
                kwargs["messages"] = _strip_pii_from_messages(kwargs["messages"])
            if "system" in kwargs and isinstance(kwargs["system"], str):
                kwargs["system"] = _strip_pii(kwargs["system"])
            model = kwargs.get("model", "unknown")
            _audit_log(provider_label, "messages.stream", model=model, caller=caller)
            cm = _orig_stream(*args, **kwargs)
            return _AnthropicStreamReconciler(
                cm, company_id, estimated, provider_label, gate_kwargs=_gate_kwargs
            )

        messages_obj.stream = _patched_stream


# ---------------------------------------------------------------------------
# OpenAI patches
# ---------------------------------------------------------------------------

def _patch_openai() -> bool:
    """Patch openai.OpenAI and AsyncOpenAI constructors."""
    try:
        import openai
    except ImportError:
        logger.debug("[LLM-Bootstrap] openai not installed, skipping patch")
        return False

    _orig_init = openai.OpenAI.__init__
    _orig_async_init = openai.AsyncOpenAI.__init__

    @functools.wraps(_orig_init)
    def _patched_init(self, *args, **kwargs):
        if "api_key" not in kwargs and not args:
            # F3-2 fix (2026-05-10): fallback for Replit AI Integration prefix
            kwargs["api_key"] = (
                _get_tenant_key_sync("openai")
                or os.environ.get("OPENAI_API_KEY")
                or os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
            )
            base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
            if base_url and "base_url" not in kwargs:
                kwargs["base_url"] = base_url
        _orig_init(self, *args, **kwargs)
        logger.debug("[LLM-Bootstrap] OpenAI client created, caller=%s", _get_caller())

    @functools.wraps(_orig_async_init)
    def _patched_async_init(self, *args, **kwargs):
        if "api_key" not in kwargs and not args:
            # F3-2 fix (2026-05-10): fallback for Replit AI Integration prefix
            kwargs["api_key"] = (
                _get_tenant_key_sync("openai")
                or os.environ.get("OPENAI_API_KEY")
                or os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
            )
            base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
            if base_url and "base_url" not in kwargs:
                kwargs["base_url"] = base_url
        _orig_async_init(self, *args, **kwargs)
        _patch_openai_completions(self, "openai-async")
        _patch_openai_audio(self, "openai-async")
        logger.debug("[LLM-Bootstrap] AsyncOpenAI client created, caller=%s", _get_caller())

    # Patch sync init to also wrap chat completions + audio
    _orig_init_wrapped = openai.OpenAI.__init__
    @functools.wraps(_orig_init_wrapped)
    def _patched_init_with_completions(self, *args, **kwargs):
        _orig_init_wrapped(self, *args, **kwargs)
        _patch_openai_completions(self, "openai")
        _patch_openai_audio(self, "openai")

    openai.OpenAI.__init__ = _patched_init_with_completions
    openai.AsyncOpenAI.__init__ = _patched_async_init
    logger.info("[LLM-Bootstrap] OpenAI SDK patched (API key + audit + credit gate)")
    return True


def _patch_openai_completions(client_instance, provider_label: str):
    """Wave 3 — wrap chat.completions.create with credit gate."""
    chat = getattr(client_instance, "chat", None)
    if chat is None:
        return
    completions = getattr(chat, "completions", None)
    if completions is None or getattr(completions, "_lia_credit_patched", False):
        return
    completions._lia_credit_patched = True

    _orig = completions.create

    is_async = provider_label.endswith("-async")

    if is_async:
        @functools.wraps(_orig)
        async def _patched_async(*args, **kwargs):
            company_id = _get_tenant_id()
            estimated = max(0, int(_estimate_tokens_openai(kwargs)))
            await _enforce_credit_gate_async(
                provider_label, kwargs, estimator=_estimate_tokens_openai
            )
            response = await _orig(*args, **kwargs)
            # Wave 4 Gap 2 (2026-05-22) -- streaming returns AsyncStream;
            # non-streaming returns ChatCompletion with .usage populated.
            if kwargs.get("stream"):
                return _OpenAIStreamReconciler(response, company_id, estimated, provider_label, is_async=True)
            actual = _extract_response_usage_tokens(response)
            if company_id and actual > 0:
                await reconcile_credits(company_id, estimated, actual, service=provider_label)
            return response
        completions.create = _patched_async
    else:
        @functools.wraps(_orig)
        def _patched_sync(*args, **kwargs):
            company_id = _get_tenant_id()
            estimated = max(0, int(_estimate_tokens_openai(kwargs)))
            _enforce_credit_gate_sync(
                provider_label, kwargs, estimator=_estimate_tokens_openai
            )
            response = _orig(*args, **kwargs)
            if kwargs.get("stream"):
                return _OpenAIStreamReconciler(response, company_id, estimated, provider_label, is_async=False)
            actual = _extract_response_usage_tokens(response)
            if company_id and actual > 0:
                _reconcile_sync(company_id, estimated, actual, service=provider_label)
            return response
        completions.create = _patched_sync



# ---------------------------------------------------------------------------
# OpenAI Audio Gate (Whisper STT + TTS) — P1.AIC2 restored 2026-05-22
# ---------------------------------------------------------------------------
# Whisper and TTS are NOT chat-completions — they have distinct token models.
# Whisper STT is per-audio-minute ($0.006/min ≈ 2000 token-eq @ Claude $3/M).
# TTS is per-input-character ($0.015/1K chars ≈ 5 token-eq/char).
# These constants mirror the conversion logic in `ai_credit_gate.py` so the
# same ledger column is used regardless of price model.

_WHISPER_TOKEN_EQ_PER_MINUTE = 2000  # 60 sec audio → 2000 token-eq
_TTS_TOKEN_EQ_PER_CHAR = 5            # 1 char text → 5 token-eq

# 96 kbps MP3 / Opus is a sane default for compressed audio sent to Whisper.
# WAV (uncompressed 16kHz mono 16-bit) at ~256 kbps will under-estimate by ~3×,
# but the gate is meant to be a budget guardrail not a precise meter; the
# reconcile path can correct after the SDK returns `duration` in response.
_AUDIO_BYTES_PER_SECOND_HEURISTIC = 12000  # 96 kbps / 8


def _extract_audio_duration(file_arg) -> float | None:
    """Best-effort audio duration extraction from an openai SDK ``file=`` arg.

    Accepts:
      - tuples (filename, bytes, mime_type) — SDK file-tuple convention
      - tuples (filename, bytes) — also valid
      - raw bytes
      - file-like objects with ``len()``
      - objects exposing ``duration_seconds``

    Returns None when no signal is available (estimator returns 0 → gate
    fails-safe ALLOW). Caller should still set ``audio_duration_seconds``
    explicitly in kwargs when the value is known precisely.
    """
    if file_arg is None:
        return None
    if hasattr(file_arg, "duration_seconds"):
        try:
            return float(file_arg.duration_seconds)
        except Exception:
            pass
    # SDK file-tuple convention: (filename, bytes[, mime_type])
    if isinstance(file_arg, tuple) and len(file_arg) >= 2:
        payload = file_arg[1]
        if isinstance(payload, (bytes, bytearray, memoryview)):
            return float(len(payload)) / _AUDIO_BYTES_PER_SECOND_HEURISTIC
    if isinstance(file_arg, (bytes, bytearray, memoryview)):
        return float(len(file_arg)) / _AUDIO_BYTES_PER_SECOND_HEURISTIC
    if hasattr(file_arg, "__len__"):
        try:
            return float(len(file_arg)) / _AUDIO_BYTES_PER_SECOND_HEURISTIC
        except Exception:
            pass
    return None


def _estimate_tokens_openai_audio_transcription(kwargs: dict) -> int:
    """Whisper STT: token-eq derived from audio duration.

    Resolution order:
      1. explicit ``audio_duration_seconds`` kwarg (passed by callers that
         know the precise duration — e.g., after a probe).
      2. derived from ``file=`` arg via ``_extract_audio_duration``.
      3. fallback ``0`` (no signal → estimator yields 0; gate path will
         still fire but with no budget projection — defense in depth via
         reconciliation after the SDK returns).
    """
    duration_seconds = kwargs.get("audio_duration_seconds")
    if duration_seconds is None:
        duration_seconds = _extract_audio_duration(kwargs.get("file"))
    if duration_seconds is None or duration_seconds <= 0:
        return 0
    return int(round((float(duration_seconds) / 60.0) * _WHISPER_TOKEN_EQ_PER_MINUTE))


def _estimate_tokens_openai_audio_speech(kwargs: dict) -> int:
    """TTS: token-eq derived from input text length."""
    text = kwargs.get("input") or ""
    if not text:
        return 0
    return int(len(text) * _TTS_TOKEN_EQ_PER_CHAR)


def _patch_openai_audio(client_instance, provider_label: str):
    """Wrap audio.transcriptions.create + audio.speech.create with the gate.

    Mirrors ``_patch_openai_completions`` shape: detects sync vs async via
    ``provider_label.endswith("-async")`` (the constructor patch passes the
    label consistently). Both methods on the SDK are real attributes on the
    client (not @property), so ``getattr`` is safe.
    """
    audio = getattr(client_instance, "audio", None)
    if audio is None:
        logger.debug("[LLM-Bootstrap] %s has no audio API — skip", provider_label)
        return

    is_async = provider_label.endswith("-async")

    # ---- transcriptions ----
    transcriptions = getattr(audio, "transcriptions", None)
    if transcriptions is not None and not getattr(transcriptions, "_lia_credit_patched", False):
        transcriptions._lia_credit_patched = True
        _orig_create = transcriptions.create

        if is_async:
            @functools.wraps(_orig_create)
            async def _patched_transcription_async(*args, **kwargs):
                await _enforce_credit_gate_async(
                    provider_label + "/whisper",
                    kwargs,
                    estimator=_estimate_tokens_openai_audio_transcription,
                )
                return await _orig_create(*args, **kwargs)
            transcriptions.create = _patched_transcription_async
        else:
            @functools.wraps(_orig_create)
            def _patched_transcription_sync(*args, **kwargs):
                _enforce_credit_gate_sync(
                    provider_label + "/whisper",
                    kwargs,
                    estimator=_estimate_tokens_openai_audio_transcription,
                )
                return _orig_create(*args, **kwargs)
            transcriptions.create = _patched_transcription_sync

    # ---- speech (TTS) ----
    speech = getattr(audio, "speech", None)
    if speech is not None and not getattr(speech, "_lia_credit_patched", False):
        speech._lia_credit_patched = True
        _orig_create = speech.create

        if is_async:
            @functools.wraps(_orig_create)
            async def _patched_speech_async(*args, **kwargs):
                await _enforce_credit_gate_async(
                    provider_label + "/tts",
                    kwargs,
                    estimator=_estimate_tokens_openai_audio_speech,
                )
                return await _orig_create(*args, **kwargs)
            speech.create = _patched_speech_async
        else:
            @functools.wraps(_orig_create)
            def _patched_speech_sync(*args, **kwargs):
                _enforce_credit_gate_sync(
                    provider_label + "/tts",
                    kwargs,
                    estimator=_estimate_tokens_openai_audio_speech,
                )
                return _orig_create(*args, **kwargs)
            speech.create = _patched_speech_sync

    logger.info(
        "[LLM-Bootstrap] Patched %s audio (transcriptions + speech, %s)",
        provider_label, "async" if is_async else "sync",
    )


# ---------------------------------------------------------------------------
# Google GenAI patches
# ---------------------------------------------------------------------------

def _patch_genai() -> bool:
    """Patch google.genai.Client constructor."""
    try:
        from google import genai
    except ImportError:
        logger.debug("[LLM-Bootstrap] google.genai not installed, skipping patch")
        return False

    _orig_init = genai.Client.__init__

    @functools.wraps(_orig_init)
    def _patched_init(self, *args, **kwargs):
        if "api_key" not in kwargs and not args:
            kwargs["api_key"] = (
                _get_tenant_key_sync("gemini")
                or os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
            )
            base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
            if base_url and "http_options" not in kwargs:
                kwargs["http_options"] = {"api_version": "", "base_url": base_url}
        _orig_init(self, *args, **kwargs)
        _patch_genai_models(self, "gemini")
        logger.debug("[LLM-Bootstrap] genai.Client created, caller=%s", _get_caller())

    genai.Client.__init__ = _patched_init
    logger.info("[LLM-Bootstrap] Google GenAI SDK patched (API key + audit + credit gate)")
    return True


def _patch_genai_models(client_instance, provider_label: str):
    """Wave 3 — wrap models.generate_content + aio.models.generate_content."""
    models_obj = getattr(client_instance, "models", None)
    if models_obj is not None and not getattr(models_obj, "_lia_credit_patched", False):
        models_obj._lia_credit_patched = True
        _orig = getattr(models_obj, "generate_content", None)
        if _orig is not None:
            @functools.wraps(_orig)
            def _patched_sync(*args, **kwargs):
                _enforce_credit_gate_sync(
                    provider_label, kwargs, estimator=_estimate_tokens_genai
                )
                return _orig(*args, **kwargs)
            models_obj.generate_content = _patched_sync

    aio_obj = getattr(client_instance, "aio", None)
    aio_models = getattr(aio_obj, "models", None) if aio_obj else None
    if aio_models is not None and not getattr(aio_models, "_lia_credit_patched", False):
        aio_models._lia_credit_patched = True
        _orig_aio = getattr(aio_models, "generate_content", None)
        if _orig_aio is not None:
            @functools.wraps(_orig_aio)
            async def _patched_async(*args, **kwargs):
                await _enforce_credit_gate_async(
                    provider_label + "-async", kwargs, estimator=_estimate_tokens_genai
                )
                return await _orig_aio(*args, **kwargs)
            aio_models.generate_content = _patched_async




# ---------------------------------------------------------------------------
# Wave 4 Gap 2 (2026-05-22) -- streaming + tool-use reconciliation hooks
# ---------------------------------------------------------------------------
# Pre-call estimation uses ``max_tokens`` ceilings, so streaming and
# tool-use multi-turn underestimate or overestimate vs actual billing.
# After each successful SDK call we observe ``response.usage`` (or the
# final-chunk usage on streams) and adjust the credit ledger via
# ``reconcile_credits``. Per-turn tool-use is naturally handled because
# each turn is a separate ``create()`` call going through the same hook.


async def reconcile_credits(
    company_id: str,
    estimated: int,
    actual: int,
    *,
    service: str,
) -> None:
    """Adjust credit ledger after seeing real ``response.usage`` (or stream
    aggregate). Delta == 0 is a no-op.

    delta > 0 (actual > estimated): we under-charged -> top-up the ledger.
    delta < 0 (actual < estimated): we over-charged -> refund.

    Fail-safe: any error is logged + swallowed so a Redis/DB outage during
    reconciliation does NOT propagate into the user-facing LLM call which
    has already succeeded.
    """
    delta = int(actual) - int(estimated)
    if delta == 0:
        return

    sign = "positive" if delta > 0 else "negative"

    try:
        from app.shared.observability.canary_metrics import (
            llm_gate_reconciliation_delta_total,
        )
        if llm_gate_reconciliation_delta_total is not None:
            try:
                llm_gate_reconciliation_delta_total.labels(
                    provider=service, sign=sign
                ).inc(abs(delta))
            except Exception:
                pass
    except Exception:
        pass

    logger.info(
        "[LLM-Reconcile] company=%s service=%s estimated=%s actual=%s delta=%s",
        company_id, service, estimated, actual, delta,
    )

    if not company_id:
        return

    try:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import select
        from app.models.ai_consumption import AiCreditsBalance

        async with AsyncSessionLocal() as db:
            res = await db.execute(
                select(AiCreditsBalance).where(
                    AiCreditsBalance.company_id == company_id
                )
            )
            balance = res.scalar_one_or_none()
            if balance is None:
                return
            current_usage = int(getattr(balance, "current_usage", 0) or 0)
            balance.current_usage = max(0, current_usage + delta)
            await db.commit()
    except Exception as exc:
        logger.warning(
            "[LLM-Reconcile] ledger update failed (fail-safe): %s", exc
        )


def _extract_response_usage_tokens(response) -> int:
    """Best-effort extract input+output tokens from an SDK response object.

    Returns 0 when the shape is unknown (Anthropic/OpenAI/genai vary).
    """
    if response is None:
        return 0
    try:
        usage = getattr(response, "usage", None)
        if usage is None and isinstance(response, dict):
            usage = response.get("usage")
        if usage is None:
            return 0

        def _g(obj, name):
            if isinstance(obj, dict):
                return obj.get(name) or 0
            return getattr(obj, name, 0) or 0

        # Anthropic: input_tokens + output_tokens
        # OpenAI:    prompt_tokens + completion_tokens
        # genai:     prompt_token_count + candidates_token_count
        total = 0
        for k in ("input_tokens", "prompt_tokens", "prompt_token_count"):
            total += int(_g(usage, k))
        for k in ("output_tokens", "completion_tokens", "candidates_token_count"):
            total += int(_g(usage, k))
        if total > 0:
            return total
        return int(_g(usage, "total_tokens"))
    except Exception:
        return 0


def _reconcile_sync(company_id: str, estimated: int, actual: int, *, service: str) -> None:
    """Sync wrapper around reconcile_credits (sync SDK paths)."""
    if not company_id or actual <= 0:
        return
    try:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            new_loop = asyncio.new_event_loop()
            try:
                new_loop.run_until_complete(
                    reconcile_credits(company_id, estimated, actual, service=service)
                )
            finally:
                new_loop.close()
        else:
            asyncio.run(
                reconcile_credits(company_id, estimated, actual, service=service)
            )
    except Exception as exc:
        logger.warning("[LLM-Reconcile] sync wrapper failed (fail-safe): %s", exc)


class _AnthropicStreamReconciler:
    """Wave 4 Gap 2 (2026-05-22) -- proxy that forwards every attribute /
    iteration / context-manager call to the underlying Anthropic stream
    context-manager, and triggers reconcile_credits on close() using the
    stream's ``.usage`` snapshot if available.

    Anthropic ``messages.stream`` returns a ``MessageStreamManager`` used as
    ``with stream as s: ...``. After ``__exit__`` the stream exposes
    ``s.get_final_message().usage``. We snapshot at __exit__ and reconcile.
    """

    def __init__(self, wrapped, company_id: str, estimated: int, service: str,
                 gate_kwargs: dict | None = None):
        self._wrapped = wrapped
        self._company_id = company_id
        self._estimated = estimated
        self._service = service
        self._inner = None
        # Fix 2026-06-04: quando setado (caminho async), o gate de credito e
        # enforcado AQUI no __aenter__ async (stream() e sync, nao pode await).
        self._gate_kwargs = gate_kwargs

    def __getattr__(self, name):
        return getattr(self._wrapped, name)

    def __enter__(self):
        self._inner = self._wrapped.__enter__()
        return self._inner

    def __exit__(self, exc_type, exc, tb):
        try:
            return self._wrapped.__exit__(exc_type, exc, tb)
        finally:
            try:
                actual = 0
                if self._inner is not None and hasattr(self._inner, "get_final_message"):
                    final = self._inner.get_final_message()
                    actual = _extract_response_usage_tokens(final)
                if self._company_id and actual > 0:
                    _reconcile_sync(
                        self._company_id, self._estimated, actual,
                        service=self._service,
                    )
            except Exception as _exc:  # noqa: BLE001
                logger.debug("[LLM-Reconcile] anthropic stream reconcile failed: %s", _exc)

    async def __aenter__(self):
        # Async client: enforca o gate de credito async ANTES de abrir o stream.
        # No caminho sync, gate_kwargs e None (o gate sync ja rodou em _patched_stream).
        if self._gate_kwargs is not None:
            await _enforce_credit_gate_async(
                self._service, self._gate_kwargs, estimator=_estimate_tokens_anthropic
            )
        self._inner = await self._wrapped.__aenter__()
        return self._inner

    async def __aexit__(self, exc_type, exc, tb):
        try:
            return await self._wrapped.__aexit__(exc_type, exc, tb)
        finally:
            try:
                actual = 0
                if self._inner is not None and hasattr(self._inner, "get_final_message"):
                    final = self._inner.get_final_message()
                    if hasattr(final, "__await__"):
                        final = await final
                    actual = _extract_response_usage_tokens(final)
                if self._company_id and actual > 0:
                    await reconcile_credits(
                        self._company_id, self._estimated, actual,
                        service=self._service,
                    )
            except Exception as _exc:  # noqa: BLE001
                logger.debug("[LLM-Reconcile] anthropic async-stream reconcile failed: %s", _exc)


class _OpenAIStreamReconciler:
    """Wave 4 Gap 2 (2026-05-22) -- iterator/async-iterator proxy that
    accumulates token usage across stream chunks and reconciles on close.

    OpenAI streaming yields ChatCompletionChunk objects. With
    ``stream_options={'include_usage': True}`` the final chunk has
    ``chunk.usage`` populated. We track the max observed so the per-chunk
    .usage updates monotonically (some SDK versions repeat usage on
    intermediate chunks).
    """

    def __init__(self, wrapped, company_id: str, estimated: int, service: str, *, is_async: bool):
        self._wrapped = wrapped
        self._company_id = company_id
        self._estimated = estimated
        self._service = service
        self._is_async = is_async
        self._actual = 0
        self._closed = False

    def __getattr__(self, name):
        return getattr(self._wrapped, name)

    def __iter__(self):
        return self

    def __aiter__(self):
        return self

    def __next__(self):
        try:
            chunk = next(self._wrapped)
        except StopIteration:
            self._reconcile_now_sync()
            raise
        self._observe_chunk(chunk)
        return chunk

    async def __anext__(self):
        try:
            chunk = await self._wrapped.__anext__()
        except StopAsyncIteration:
            await self._reconcile_now_async()
            raise
        self._observe_chunk(chunk)
        return chunk

    def _observe_chunk(self, chunk):
        try:
            actual = _extract_response_usage_tokens(chunk)
            if actual > self._actual:
                self._actual = actual
        except Exception:
            pass

    def _reconcile_now_sync(self):
        if self._closed:
            return
        self._closed = True
        if self._company_id and self._actual > 0:
            _reconcile_sync(
                self._company_id, self._estimated, self._actual,
                service=self._service,
            )

    async def _reconcile_now_async(self):
        if self._closed:
            return
        self._closed = True
        if self._company_id and self._actual > 0:
            await reconcile_credits(
                self._company_id, self._estimated, self._actual,
                service=self._service,
            )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def install_llm_guards(entrypoint: str = "fastapi") -> dict:
    """
    Install monkey-patches on all LLM SDKs.

    Call this ONCE per process at startup, before any module creates an LLM
    client. Safe to call multiple times (idempotent).

    Wave 4 (Gap 1, 2026-05-22): accept entry-point label so the
    ``llm_guards_installed{provider,entrypoint}`` gauge fingerprints which
    processes have the guards active (FastAPI vs Celery vs RabbitMQ vs CLI).
    Grafana alarm: ``min by(entrypoint)(llm_guards_installed) == 0`` fires
    when any entrypoint never installed the guards (SDK bypass risk).

    Patches:
      - Anthropic/AsyncAnthropic: API key injection + PII strip + audit + credit gate
      - OpenAI/AsyncOpenAI: API key injection + audit + credit gate + audio gate
      - genai.Client: API key injection + audit + credit gate

    Returns:
      dict mapping provider -> bool. True = SDK present and patched.
      False = SDK absent in this venv (still safe -- no bypass possible).
    """
    global _installed
    if _installed:
        logger.debug(
            "[LLM-Bootstrap] Already installed (entrypoint=%s) -- re-emitting gauge",
            entrypoint,
        )
        _emit_guards_installed_gauge(_LAST_INSTALL_STATUS, entrypoint)
        return dict(_LAST_INSTALL_STATUS)

    logger.info(
        "[LLM-Bootstrap] Installing LLM guards (entrypoint=%s, PII + audit + credit gate + API key injection)...",
        entrypoint,
    )
    status = {
        "anthropic": _patch_anthropic(),
        "openai": _patch_openai(),
        "gemini": _patch_genai(),
    }
    _installed = True
    _LAST_INSTALL_STATUS.update(status)
    logger.info(
        "[LLM-Bootstrap] LLM guards installed: anthropic=%s openai=%s gemini=%s entrypoint=%s",
        "on" if status["anthropic"] else "sdk-absent",
        "on" if status["openai"] else "sdk-absent",
        "on" if status["gemini"] else "sdk-absent",
        entrypoint,
    )
    _emit_guards_installed_gauge(status, entrypoint)
    return status


# ---------------------------------------------------------------------------
# Wave 4 Gap 1 (2026-05-22) -- LLM guards installation telemetry
# ---------------------------------------------------------------------------

_LAST_INSTALL_STATUS: dict = {"anthropic": False, "openai": False, "gemini": False}


def _emit_guards_installed_gauge(status: dict, entrypoint: str) -> None:
    """Best-effort emit ``llm_guards_installed{provider, entrypoint}=1`` per
    successfully-patched provider. SDK absent -> gauge NOT set so Grafana
    treats the missing series as a separate signal from a present-but-zero.
    """
    try:
        from app.shared.observability.canary_metrics import llm_guards_installed
        if llm_guards_installed is None:
            return
        for provider, ok in status.items():
            if ok:
                try:
                    llm_guards_installed.labels(
                        provider=provider, entrypoint=entrypoint
                    ).set(1)
                except Exception:
                    pass
    except Exception:
        pass  # observability non-blocking
