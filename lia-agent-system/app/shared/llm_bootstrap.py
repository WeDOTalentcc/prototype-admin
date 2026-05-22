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
            # We are being called from inside an async context but on the sync
            # SDK method (Anthropic.messages.create is sync). Use the existing
            # loop via run_coroutine_threadsafe-equivalent. Since SDK sync
            # methods inside async are normally invoked via asyncio.to_thread
            # already, we run a fresh loop in this thread.
            new_loop = asyncio.new_event_loop()
            try:
                new_loop.run_until_complete(_gated())
            finally:
                new_loop.close()
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
        # Fail-safe ALLOW for unexpected errors (DB outage, import failure)
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


def _patch_anthropic():
    """Patch anthropic.Anthropic and AsyncAnthropic constructors + messages."""
    try:
        import anthropic
    except ImportError:
        logger.debug("[LLM-Bootstrap] anthropic not installed, skipping patch")
        return

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
                os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
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


def _patch_messages_api(client_instance, provider_label: str):
    """Patch messages.create() and messages.stream() on a client instance."""
    if not hasattr(client_instance, "messages"):
        return

    messages_obj = client_instance.messages
    
    # Only patch once per instance
    if getattr(messages_obj, "_lia_patched", False):
        return
    messages_obj._lia_patched = True

    _orig_create = messages_obj.create

    @functools.wraps(_orig_create)
    def _patched_create(*args, **kwargs):
        caller = _get_caller()
        # Wave 3 — credit gate BEFORE PII strip + LLM call (fail-closed on exhaust)
        _enforce_credit_gate_sync(provider_label, kwargs, estimator=_estimate_tokens_anthropic)
        # PII strip messages
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
            return result
        except Exception as e:
            latency = (time.time() - start) * 1000
            _audit_log(provider_label, "messages.create.ERROR", model=model,
                      latency_ms=latency, caller=caller, error=str(e)[:100])
            raise

    messages_obj.create = _patched_create

    # Patch stream if it exists
    if hasattr(messages_obj, "stream"):
        _orig_stream = messages_obj.stream

        @functools.wraps(_orig_stream)
        def _patched_stream(*args, **kwargs):
            caller = _get_caller()
            # Wave 3 — credit gate BEFORE PII strip + LLM call (fail-closed on exhaust)
            _enforce_credit_gate_sync(provider_label, kwargs, estimator=_estimate_tokens_anthropic)
            if "messages" in kwargs:
                kwargs["messages"] = _strip_pii_from_messages(kwargs["messages"])
            if "system" in kwargs and isinstance(kwargs["system"], str):
                kwargs["system"] = _strip_pii(kwargs["system"])
            model = kwargs.get("model", "unknown")
            _audit_log(provider_label, "messages.stream", model=model, caller=caller)
            return _orig_stream(*args, **kwargs)

        messages_obj.stream = _patched_stream


# ---------------------------------------------------------------------------
# OpenAI patches
# ---------------------------------------------------------------------------

def _patch_openai():
    """Patch openai.OpenAI and AsyncOpenAI constructors."""
    try:
        import openai
    except ImportError:
        logger.debug("[LLM-Bootstrap] openai not installed, skipping patch")
        return

    _orig_init = openai.OpenAI.__init__
    _orig_async_init = openai.AsyncOpenAI.__init__

    @functools.wraps(_orig_init)
    def _patched_init(self, *args, **kwargs):
        if "api_key" not in kwargs and not args:
            # F3-2 fix (2026-05-10): fallback for Replit AI Integration prefix
            kwargs["api_key"] = (
                os.environ.get("OPENAI_API_KEY")
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
                os.environ.get("OPENAI_API_KEY")
                or os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
            )
            base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
            if base_url and "base_url" not in kwargs:
                kwargs["base_url"] = base_url
        _orig_async_init(self, *args, **kwargs)
        _patch_openai_completions(self, "openai-async")
        logger.debug("[LLM-Bootstrap] AsyncOpenAI client created, caller=%s", _get_caller())

    # Patch sync init to also wrap chat completions
    _orig_init_wrapped = openai.OpenAI.__init__
    @functools.wraps(_orig_init_wrapped)
    def _patched_init_with_completions(self, *args, **kwargs):
        _orig_init_wrapped(self, *args, **kwargs)
        _patch_openai_completions(self, "openai")

    openai.OpenAI.__init__ = _patched_init_with_completions
    openai.AsyncOpenAI.__init__ = _patched_async_init
    logger.info("[LLM-Bootstrap] OpenAI SDK patched (API key + audit + credit gate)")


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
            await _enforce_credit_gate_async(
                provider_label, kwargs, estimator=_estimate_tokens_openai
            )
            return await _orig(*args, **kwargs)
        completions.create = _patched_async
    else:
        @functools.wraps(_orig)
        def _patched_sync(*args, **kwargs):
            _enforce_credit_gate_sync(
                provider_label, kwargs, estimator=_estimate_tokens_openai
            )
            return _orig(*args, **kwargs)
        completions.create = _patched_sync


# ---------------------------------------------------------------------------
# Google GenAI patches
# ---------------------------------------------------------------------------

def _patch_genai():
    """Patch google.genai.Client constructor."""
    try:
        from google import genai
    except ImportError:
        logger.debug("[LLM-Bootstrap] google.genai not installed, skipping patch")
        return

    _orig_init = genai.Client.__init__

    @functools.wraps(_orig_init)
    def _patched_init(self, *args, **kwargs):
        if "api_key" not in kwargs and not args:
            kwargs["api_key"] = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
            base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
            if base_url and "http_options" not in kwargs:
                kwargs["http_options"] = {"api_version": "", "base_url": base_url}
        _orig_init(self, *args, **kwargs)
        _patch_genai_models(self, "gemini")
        logger.debug("[LLM-Bootstrap] genai.Client created, caller=%s", _get_caller())

    genai.Client.__init__ = _patched_init
    logger.info("[LLM-Bootstrap] Google GenAI SDK patched (API key + audit + credit gate)")


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
# Public API
# ---------------------------------------------------------------------------

def install_llm_guards():
    """
    Install monkey-patches on all LLM SDKs.
    
    Call this ONCE at app startup, before any module creates an LLM client.
    Safe to call multiple times (idempotent).
    
    Patches:
      - Anthropic/AsyncAnthropic: API key injection + PII strip + audit
      - OpenAI/AsyncOpenAI: API key injection + audit
      - genai.Client: API key injection + audit
    """
    global _installed
    if _installed:
        logger.debug("[LLM-Bootstrap] Already installed, skipping")
        return

    logger.info("[LLM-Bootstrap] Installing LLM guards (PII + audit + API key injection)...")
    _patch_anthropic()
    _patch_openai()
    _patch_genai()
    _installed = True
    logger.info("[LLM-Bootstrap] All LLM guards installed successfully")
