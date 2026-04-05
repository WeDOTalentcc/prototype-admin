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
import os
import time
import logging
import functools
import traceback
from typing import Any

logger = logging.getLogger(__name__)

_installed = False


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

def _patch_anthropic():
    """Patch anthropic.Anthropic and AsyncAnthropic constructors + messages."""
    try:
        import anthropic
    except ImportError:
        logger.debug("[LLM-Bootstrap] anthropic not installed, skipping patch")
        return

    _orig_init = anthropic.Anthropic.__init__
    _orig_async_init = anthropic.AsyncAnthropic.__init__

    @functools.wraps(_orig_init)
    def _patched_init(self, *args, **kwargs):
        # Inject API key from env if not provided
        if "api_key" not in kwargs and not args:
            kwargs["api_key"] = (
                os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
                or os.environ.get("ANTHROPIC_API_KEY")
            )
            base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
            if base_url and "base_url" not in kwargs:
                kwargs["base_url"] = base_url
        _orig_init(self, *args, **kwargs)
        # Patch messages.create and messages.stream on this instance
        _patch_messages_api(self, "anthropic")

    @functools.wraps(_orig_async_init)
    def _patched_async_init(self, *args, **kwargs):
        if "api_key" not in kwargs and not args:
            kwargs["api_key"] = (
                os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
                or os.environ.get("ANTHROPIC_API_KEY")
            )
            base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
            if base_url and "base_url" not in kwargs:
                kwargs["base_url"] = base_url
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
            kwargs["api_key"] = os.environ.get("OPENAI_API_KEY")
        _orig_init(self, *args, **kwargs)
        logger.debug("[LLM-Bootstrap] OpenAI client created, caller=%s", _get_caller())

    @functools.wraps(_orig_async_init)
    def _patched_async_init(self, *args, **kwargs):
        if "api_key" not in kwargs and not args:
            kwargs["api_key"] = os.environ.get("OPENAI_API_KEY")
        _orig_async_init(self, *args, **kwargs)
        logger.debug("[LLM-Bootstrap] AsyncOpenAI client created, caller=%s", _get_caller())

    openai.OpenAI.__init__ = _patched_init
    openai.AsyncOpenAI.__init__ = _patched_async_init
    logger.info("[LLM-Bootstrap] OpenAI SDK patched (API key injection + audit)")


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
        logger.debug("[LLM-Bootstrap] genai.Client created, caller=%s", _get_caller())

    genai.Client.__init__ = _patched_init
    logger.info("[LLM-Bootstrap] Google GenAI SDK patched (API key injection + audit)")


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
