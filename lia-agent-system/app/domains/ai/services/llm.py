"""
LLM service for Claude, OpenAI, and Gemini.
Uses Replit AI Integrations for LLM access.
Supports function calling (tool use) for agent systems.
Supports structured outputs with Pydantic models.
"""
import hashlib
import json
import logging
import os
import time as _time
from dataclasses import dataclass, field
from typing import Any, Literal, TypeVar

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

from app.core.config import settings

# === E7: Audit logging on all LLM calls ===
from app.shared.compliance.audit_service import audit_service as _audit_svc

# === Choose Your AI: Tenant-aware LLM routing ===
# === E6: PII stripping on all LLM calls ===
from app.shared.pii_masking import strip_pii_for_llm_prompt
from app.shared.tenant_llm_context import get_current_llm_tenant

T = TypeVar("T", bound=BaseModel)

from app.shared.observability.tracing import trace_span

logger = logging.getLogger(__name__)

# === Audit 2026-05-24 P1: LLM token streaming opt-in via ContextVar ===
# Caller (SSE handler) seta callback antes de agent.process().
# _generate_with_tools_claude detecta callback presente → usa client.messages.stream()
# emitindo text deltas progressivos. Callback ausente → caminho blocking original.
# Backward compat: zero impacto em callers non-SSE (workers, jobs, tests).
from contextvars import ContextVar
from typing import Awaitable, Callable

_llm_streaming_callback: ContextVar = ContextVar(
    "_llm_streaming_callback", default=None
)
"""
Type: Optional[Callable[[dict], Awaitable[None]]]
When set, _generate_with_tools_claude streams text deltas via callback({"type": "token", "content": delta}).
"""

# === Audit 2026-05-24 (P1 fix): cache em chamadas LLM tool-calling idempotentes ===
# Reduz top-15 latencies de 5-13s para ~ms em cache hits. Safety: só cacheia
# responses text-only (sem tool_calls — esses têm side effects e devem rodar
# fresh). Multi-tenancy via company_id no key (LGPD isolation).
from app.domains.ai.services.response_cache_service import response_cache_service

_LLM_CACHE_TTL_SECONDS = 300  # 5 min — short o suficiente pra refletir mudanças


def _build_llm_tool_cache_key(
    provider: str,
    messages: list[dict],
    tools: list[dict],
    system_prompt: str | None,
    company_id: str,
) -> str:
    """Builds deterministic cache key for generate_with_tools.

    Includes:
      - provider (claude/gemini/...): different providers = different responses
      - canonical messages (content + role only): ignores raw_response noise
      - tool NAMES (sorted set): ignores tool schema ordering
      - system_prompt: changes => different response
      - company_id: multi-tenancy isolation

    Returns: lia:llm_tools:{provider}:{sha256[:32]}
    """
    canonical_messages = [
        {"role": m.get("role"), "content": m.get("content")}
        for m in messages or []
    ]
    tool_names = sorted({t.get("name", "") for t in (tools or []) if t.get("name")})
    payload = {
        "provider": provider,
        "system": system_prompt or "",
        "messages": canonical_messages,
        "tools": tool_names,
        "company_id": company_id or "",
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]
    return f"lia:llm_tools:{provider}:{digest}"


def _resolve_company_id_for_cache() -> str:
    """Get company_id via canonical RuntimeContext (fail-safe to empty)."""
    try:
        from app.shared.runtime_context import RuntimeContext
        ctx = RuntimeContext.from_contextvars()
        return ctx.company_id or ""
    except Exception:
        return ""


LLMProvider = Literal["claude", "openai", "gemini", "deepseek"]

MAX_TOOL_CALLS_PER_REQUEST = settings.REACT_MAX_TOOL_CALLS


@dataclass
class ToolCallRequest:
    """Represents a tool call requested by the LLM."""
    id: str
    name: str
    parameters: dict[str, Any]


@dataclass
class ToolCallResponse:
    """Response from generate_with_tools."""
    text_response: str | None = None
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    is_tool_call: bool = False
    raw_response: Any | None = None


class LLMService:
    """
    Service for managing multiple LLM providers.
    Uses Gemini as fallback when other providers are not configured.
    """
    
    def __init__(self):
        self._claude_client: ChatAnthropic | None = None
        self._openai_client: ChatOpenAI | None = None
        self._gemini_client = None
        # Multi-tenant LLM routing — set by MainOrchestrator per request
        self._tenant_container = None  # ProviderContainer | None
        self._current_tenant: str = ""
    
    @property
    def gemini_native(self):
        """Get Gemini client via Replit AI Integration using google.genai SDK."""
        if not self._gemini_client:
            from google import genai
            
            api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
            base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
            
            if not api_key or not base_url:
                raise ValueError("AI_INTEGRATIONS_GEMINI_API_KEY or AI_INTEGRATIONS_GEMINI_BASE_URL not configured")
            
            self._gemini_client = genai.Client(
                api_key=api_key,
                http_options={
                    'api_version': '',
                    'base_url': base_url
                }
            )
        
        return self._gemini_client
    
    @property
    def claude(self) -> BaseChatModel:
        """Get Claude client via Replit AI Integration or fallback to Gemini."""
        if settings.AI_INTEGRATIONS_ANTHROPIC_API_KEY:
            if not self._claude_client:
                self._claude_client = ChatAnthropic(
                    model_name=settings.LLM_PRIMARY_MODEL,
                    api_key=settings.AI_INTEGRATIONS_ANTHROPIC_API_KEY,
                    base_url=settings.AI_INTEGRATIONS_ANTHROPIC_BASE_URL,
                    temperature=settings.LLM_DEFAULT_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,  # type: ignore[union-attr]
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                    stop=None,
                )
            return self._claude_client
        
        if settings.ANTHROPIC_API_KEY:
            if not self._claude_client:
                self._claude_client = ChatAnthropic(
                    model_name=settings.LLM_PRIMARY_MODEL,
                    api_key=settings.ANTHROPIC_API_KEY,
                    temperature=settings.LLM_DEFAULT_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,  # type: ignore[union-attr]
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                    stop=None,
                )
            return self._claude_client
        
        raise ValueError("No Claude API key configured")
    

    def get_audited_model(self, company_id: str | None = None) -> "BaseChatModel":
        """Get a ChatModel wrapped with PII stripping and audit logging callbacks.

        Use this instead of ``llm_service.claude`` for chain patterns (prompt | llm).
        Ensures PII is stripped and all calls are audit-logged.

        Args:
            company_id: Optional company ID for tenant-specific model routing.
                        If set and tenant has custom keys, uses tenant model.
        """
        from app.shared.llm.callbacks import PIIStripCallback, AuditLogCallback
        import inspect

        frame = inspect.currentframe()
        caller = ""
        if frame and frame.f_back:
            caller = f"{os.path.basename(frame.f_back.f_code.co_filename)}:{frame.f_back.f_lineno}"

        tenant_id = company_id or self._current_tenant or ""

        # === Tenant-aware model selection (LGPD compliance) ===
        base_model = None
        if tenant_id:
            try:
                from app.shared.tenant_llm_context import get_claude_model_for_tenant
                base_model = get_claude_model_for_tenant(tenant_id)
            except Exception:
                pass
        if base_model is None:
            base_model = self.claude

        callbacks = [PIIStripCallback(), AuditLogCallback(tenant_id=tenant_id, caller=caller)]
        return base_model.with_config(callbacks=callbacks)

    @property
    def openai(self) -> BaseChatModel:
        """Get OpenAI client."""
        if settings.OPENAI_API_KEY:
            if not self._openai_client:
                self._openai_client = ChatOpenAI(
                    model="gpt-4o",
                    api_key=SecretStr(settings.OPENAI_API_KEY),
                    temperature=0.7,
                )
            return self._openai_client
        
        raise ValueError("No OpenAI API key configured")
    
    async def generate_with_gemini(self, prompt: str, model: str | None = None) -> str:
        """Generate text using Gemini via Replit AI Integration."""
        client = self.gemini_native
        model_id = model or settings.LLM_GEMINI_MODEL

        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        
        return response.text or ""
    

    async def generate_native_gemini(
        self,
        contents: "str | list",
        model: str = "gemini-2.5-flash",
        config: "Any | None" = None,
        system_instruction: str | None = None,
    ) -> "Any":
        """Wrapper around gemini_native.generate_content with PII strip + audit.

        For simple text prompts: returns response object (access .text).
        For multimodal (audio/image): pass contents as list with types.Part.
        Supports config dict or types.GenerateContentConfig.

        Args:
            contents: Prompt string or list of content parts.
            model: Gemini model name.
            config: Optional GenerateContentConfig or dict.
            system_instruction: Optional system instruction string.
        """
        import time as _time

        # PII strip on text content
        if isinstance(contents, str):
            contents = strip_pii_for_llm_prompt(contents)
        elif isinstance(contents, list):
            contents = [
                strip_pii_for_llm_prompt(c) if isinstance(c, str) else c
                for c in contents
            ]
        if system_instruction:
            system_instruction = strip_pii_for_llm_prompt(system_instruction)

        tenant_id = self._current_tenant or ""
        _t0 = _time.monotonic()

        try:
            # === Tenant-aware Gemini client (LGPD compliance) ===
            from app.shared.tenant_llm_context import get_gemini_client_for_tenant
            client = get_gemini_client_for_tenant(tenant_id) if tenant_id else self.gemini_native

            # Build kwargs
            kwargs: dict[str, Any] = {"model": model, "contents": contents}
            if config is not None:
                kwargs["config"] = config
            elif system_instruction:
                # If no config but system_instruction provided, build config
                try:
                    from google.genai import types
                    kwargs["config"] = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                    )
                except ImportError:
                    pass

            response = await client.aio.models.generate_content(**kwargs)

            _elapsed = round((_time.monotonic() - _t0) * 1000)
            logger.info(
                "[LLM-AUDIT] provider=gemini-native action=generate_content model=%s "
                "latency_ms=%d tenant=%s",
                model, _elapsed, tenant_id or "default",
            )
            return response

        except Exception as exc:
            _elapsed = round((_time.monotonic() - _t0) * 1000)
            logger.warning(
                "[LLM-AUDIT] provider=gemini-native action=generate_content.ERROR "
                "model=%s error=%s latency_ms=%d tenant=%s",
                model, type(exc).__name__, _elapsed, tenant_id or "default",
            )
            raise

    def generate_native_gemini_sync(
        self,
        contents: "str | list",
        model: str = "gemini-2.5-flash",
        config: "Any | None" = None,
        generation_config: "dict | None" = None,
    ) -> "Any":
        """Synchronous wrapper for direct Gemini SDK calls with PII strip + audit.

        For sync callers that use client.models.generate_content() directly.
        """
        import time as _time

        if isinstance(contents, str):
            contents = strip_pii_for_llm_prompt(contents)
        elif isinstance(contents, list):
            for i, c in enumerate(contents):
                if isinstance(c, str):
                    contents[i] = strip_pii_for_llm_prompt(c)
                elif isinstance(c, dict) and c.get("parts"):
                    for j, part in enumerate(c["parts"]):
                        if isinstance(part, dict) and "text" in part:
                            c["parts"][j]["text"] = strip_pii_for_llm_prompt(part["text"])

        tenant_id = self._current_tenant or ""
        _t0 = _time.monotonic()

        try:
            # === Tenant-aware Gemini client (LGPD compliance) ===
            from app.shared.tenant_llm_context import get_gemini_client_for_tenant
            client = get_gemini_client_for_tenant(tenant_id) if tenant_id else self.gemini_native
            kwargs: dict[str, Any] = {"model": model, "contents": contents}
            if config is not None:
                kwargs["config"] = config
            if generation_config is not None:
                kwargs["generation_config"] = generation_config

            response = client.models.generate_content(**kwargs)

            _elapsed = round((_time.monotonic() - _t0) * 1000)
            logger.info(
                "[LLM-AUDIT] provider=gemini-native-sync action=generate_content model=%s "
                "latency_ms=%d tenant=%s",
                model, _elapsed, tenant_id or "default",
            )
            return response
        except Exception as exc:
            _elapsed = round((_time.monotonic() - _t0) * 1000)
            logger.warning(
                "[LLM-AUDIT] provider=gemini-native-sync ERROR=%s latency_ms=%d tenant=%s",
                type(exc).__name__, _elapsed, tenant_id or "default",
            )
            raise

    async def generate(
        self,
        prompt: str,
        provider: LLMProvider = "gemini",
        model: str | None = None,
        **kwargs
    ) -> str:
        """
        # E6: PII stripping (auto-injected)
        if "prompt" in dir():
            prompt = strip_pii_for_llm_prompt(prompt)

        Generate text using specified LLM.
        
        Args:
            prompt: Input prompt
            provider: LLM provider to use
            model: Optional model name override (e.g. "gemini-2.5-flash", "claude-sonnet-4-6")
            **kwargs: Additional arguments (temperature, max_tokens, etc)
        
        Returns:
            Generated text
        """
        # === E6: PII stripping (LGPD Art. 12 / EU AI Act Art. 13) ===
        _original_len = len(prompt)
        prompt = strip_pii_for_llm_prompt(prompt)
        _stripped = _original_len != len(prompt)

        # === E7: Audit logging (every LLM call tracked) ===
        _cid = getattr(self, '_current_tenant', '') or get_current_llm_tenant()
        logger.info(
            "[LLMService] generate provider=%s model=%s prompt_len=%d pii_stripped=%s tenant=%s",
            provider, model or "default", len(prompt), _stripped, _cid or "global"
        )
        try:
            if _cid and _audit_svc:
                await _audit_svc.log_decision(  # AUDIT-NO-DEMO: LLM call telemetry (infrastructure layer; no candidate decision; LGPD Art.20 N/A)
                    company_id=_cid,
                    action="llm_call",
                    resource_type="llm_provider",
                    resource_id=f"{provider}:{model or 'default'}",
                    details={
                        "provider": provider,
                        "model": model or "default",
                        "prompt_length": len(prompt),
                        "pii_stripped": _stripped,
                    },
                    user_id="system",
                )
        except Exception:
            pass  # Audit is non-blocking

        # WT-2022 P0.AIC1: per-company ai_credits_balance gate (defense-in-depth).
        # llm_factory.ProviderContainer ja faz check no chokepoint principal,
        # mas tenant_container/global fallback abaixo NAO passa por ProviderContainer.
        # Wire aqui cobre 100% dos LLM calls do LLMService.generate.
        # fail-safe=True por default (helper) — outage de DB nao bloqueia LLM.
        if _cid:
            try:
                from app.shared.services.ai_credit_gate import (
                    AICreditExhausted,
                    check_credit_budget,
                )
                from lia_config.database import AsyncSessionLocal
                async with AsyncSessionLocal() as _credit_db:
                    await check_credit_budget(
                        _credit_db,
                        str(_cid),
                        estimated_tokens=int(kwargs.get("max_tokens", 0) or 0),
                    )
            except AICreditExhausted:
                raise  # bubble up — caller (route/agent) converte em 429
            except Exception as _credit_exc:
                logger.warning(
                    "[LLMService] ai_credit_gate failed (fail-safe ALLOW): %s",
                    _credit_exc,
                )

        # ── Multi-tenant provider routing ──
        # If a tenant ProviderContainer is active, delegate to it instead
        # of using the global provider clients. This enables per-tenant
        # API keys, models, and fallback chains.
        if self._tenant_container is not None:
            try:
                tenant_provider = self._tenant_container.get(provider)
                if system_prompt := kwargs.pop("system", None):
                    result = await tenant_provider.generate_with_system(system_prompt, prompt, **kwargs)
                else:
                    result = await tenant_provider.generate(prompt, **kwargs)
                return result.text
            except Exception as _tenant_exc:
                logger.warning(
                    "[LLMService] Tenant provider failed (tenant=%s, provider=%s): %s — falling back to global",
                    self._current_tenant, provider, _tenant_exc,
                )
                # Fall through to global provider

        if provider == "gemini":
            return await self.generate_with_gemini(prompt, model=model)
        elif provider == "claude":
            llm = self.claude
            if kwargs:
                llm = llm.bind(**kwargs)
            response = await llm.ainvoke(prompt)
            content = response.content
            if isinstance(content, list):
                text_parts: list[str] = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(str(block.get("text", "")))
                    elif isinstance(block, str):
                        text_parts.append(block)
                    elif hasattr(block, "text"):
                        text_parts.append(str(getattr(block, "text", "")))
                return "".join(text_parts)
            return str(content) if content else ""
        elif provider == "openai":
            llm = self.openai
            if kwargs:
                llm = llm.bind(**kwargs)
            response = await llm.ainvoke(prompt)
            content = response.content
            return str(content) if content else ""
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def generate_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        provider: LLMProvider = "gemini",
        system_prompt: str | None = None,
        max_tokens: int = 4096
    ) -> ToolCallResponse:
        """
        Generate response with tool/function calling support.
        
        Args:
            messages: List of message dicts with role and content
            tools: List of tool schemas in provider format
            provider: LLM provider to use
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            
        Returns:
            ToolCallResponse with either text or tool calls
        """
        # E6: PII stripping on message content
        for _msg in messages:
            if isinstance(_msg.get("content"), str):
                _msg["content"] = strip_pii_for_llm_prompt(_msg["content"])

        # === Audit 2026-05-24 P1: cache lookup (idempotent intents) ===
        # Lookup ANTES do dispatch — hit = ~ms vs ~5-13s miss.
        # Safety: cache only stores is_tool_call=False (text-only responses).
        # Multi-tenancy: key includes company_id from RuntimeContext (LGPD).
        _company_id = _resolve_company_id_for_cache()
        _cache_key = _build_llm_tool_cache_key(
            provider=provider,
            messages=messages,
            tools=tools,
            system_prompt=system_prompt,
            company_id=_company_id,
        )
        # Cache lookup is fail-soft: errors bypass cache and fall through
        # to real provider call (no silent fallback — cache miss is canonical
        # path, not a masked failure). See REGRA-4-EXEMPT marker on cache HIT
        # return below.
        try:
            _cached = await response_cache_service.get_cached_response(_cache_key)
        except Exception as _cache_err:
            logger.warning(f"[LLM-CACHE] lookup error (bypassing): {_cache_err}")
            _cached = None

        if _cached and _cached.get("_cache_safe") is True:
            # Reconstrói ToolCallResponse text-only (sem tool_calls/raw_response —
            # those são contextuais e não cacheable).
            logger.info(
                f"[LLM-CACHE] HIT provider={provider} key=...{_cache_key[-12:]} "
                f"text_len={len(_cached.get('text_response', '') or '')}"
            )
            # cache HIT return — _cached comes from successful cache lookup
            # (try branch). When lookup fails, _cached=None and falls through
            # to real provider call below; not silent fallback.
            # REGRA-4-EXEMPT (Wave D2.3): cache hit, not error fallback.
            return ToolCallResponse(
                text_response=_cached.get("text_response"),
                tool_calls=[],
                is_tool_call=False,
                raw_response=None,
            )

        # Cache miss → call provider real
        if provider == "claude":
            _result = await self._generate_with_tools_claude(
                messages, tools, system_prompt, max_tokens
            )
        elif provider == "gemini":
            _result = await self._generate_with_tools_gemini(
                messages, tools, system_prompt, max_tokens
            )
        else:
            raise ValueError(f"Provider {provider} does not support tool calling")

        # Cache só se text-only (tool_calls têm side effects, never cache)
        if not _result.is_tool_call and _result.text_response:
            try:
                await response_cache_service.cache_response(
                    _cache_key,
                    {
                        "text_response": _result.text_response,
                        "_cache_safe": True,  # marker — only present on text-only writes
                    },
                    ttl=_LLM_CACHE_TTL_SECONDS,
                    intent="llm_tools_text",
                )
            except Exception as _cache_err:
                logger.warning(f"[LLM-CACHE] store error (non-fatal): {_cache_err}")

        return _result
    
    async def _generate_with_tools_claude(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system_prompt: str | None = None,
        max_tokens: int = 4096
    ) -> ToolCallResponse:
        """Generate with Claude's tool_use via anthropic SDK."""
        from app.shared.providers.llm_factory import get_provider_for_tenant
        _claude_provider = get_provider_for_tenant().get("claude")
        # Bug C canonical fix (2026-05-24): use async client + await in
        # _generate_with_tools_claude (async def). Sync client from async
        # context → _enforce_credit_gate_sync RuntimeError.
        client = _claude_provider._get_async_client()

        try:
            request_kwargs = {
                "model": settings.LLM_PRIMARY_MODEL,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            
            if tools:
                request_kwargs["tools"] = tools
            
            if system_prompt:
                request_kwargs["system"] = system_prompt
            
            logger.info(f"Calling Claude with {len(tools)} tools, {len(messages)} messages")

            # === Audit 2026-05-24 P1: streaming opt-in ===
            _stream_cb = _llm_streaming_callback.get(None)
            if _stream_cb is not None:
                # Streaming path: emit text deltas via callback durante geracao
                logger.info(f"[LLM-STREAM] Streaming mode (callback presente)")
                async with client.messages.stream(**request_kwargs) as stream:
                    async for text_delta in stream.text_stream:
                        if text_delta:
                            try:
                                await _stream_cb({"type": "token", "content": text_delta})
                            except Exception as _cb_err:
                                logger.warning(f"[LLM-STREAM] callback error (continuing): {_cb_err}")
                    final_message = await stream.get_final_message()
                # Notifica fim
                try:
                    await _stream_cb({"type": "token_done"})
                except Exception:
                    pass
                response = final_message
            else:
                # Caminho original — blocking
                response = await client.messages.create(**request_kwargs)

            tool_calls = []
            text_parts = []

            for block in response.content:
                if hasattr(block, 'type'):
                    if block.type == "text":
                        text_parts.append(block.text)
                    elif block.type == "tool_use":
                        tool_calls.append(ToolCallRequest(
                            id=block.id,
                            name=block.name,
                            parameters=block.input if isinstance(block.input, dict) else {}
                        ))
            
            if tool_calls:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Claude requested {len(tool_calls)} tool calls: {[tc.name for tc in tool_calls]}")
                return ToolCallResponse(
                    is_tool_call=True,
                    tool_calls=tool_calls,
                    raw_response=response
                )
            
            text_response = "".join(text_parts)
            return ToolCallResponse(
                text_response=text_response,
                is_tool_call=False,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Claude tool call error: {e}", exc_info=True)
            raise
    
    async def _generate_with_tools_gemini(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system_prompt: str | None = None,
        max_tokens: int = 4096
    ) -> ToolCallResponse:
        """Generate with Gemini's function_calling via google.genai SDK."""
        from google.genai import types
        
        client = self.gemini_native
        
        try:
            contents = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "user":
                    contents.append(types.Content(
                        role="user",
                        parts=[types.Part(text=content if isinstance(content, str) else str(content))]
                    ))
                elif role == "assistant" or role == "model":
                    parts = []
                    if content:
                        parts.append(types.Part(text=content if isinstance(content, str) else str(content)))
                    if msg.get("function_call"):
                        fc = msg["function_call"]
                        parts.append(types.Part.from_function_call(
                            name=fc.get("name", ""),
                            args=fc.get("args", {})
                        ))
                    if parts:
                        contents.append(types.Content(role="model", parts=parts))
                elif role == "function_response":
                    function_response = types.Part.from_function_response(
                        name=msg.get("name", ""),
                        response=msg.get("response", {})
                    )
                    contents.append(types.Content(
                        role="user",
                        parts=[function_response]
                    ))
                elif role == "tool":
                    tool_result = msg.get("tool_result", content)
                    function_response = types.Part.from_function_response(
                        name=msg.get("name", "unknown"),
                        response=tool_result if isinstance(tool_result, dict) else {"result": tool_result}
                    )
                    contents.append(types.Content(
                        role="user",
                        parts=[function_response]
                    ))
            
            function_declarations = []
            for tool in tools:
                func_decl = types.FunctionDeclaration(
                    name=tool.get("name", ""),
                    description=tool.get("description", ""),
                    parameters=tool.get("parameters", tool.get("input_schema", {}))
                )
                function_declarations.append(func_decl)
            
            gemini_tools = [types.Tool(function_declarations=function_declarations)] if function_declarations else None
            
            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=gemini_tools,
                max_output_tokens=max_tokens
            )
            
            logger.info(f"Calling Gemini with {len(tools)} tools, {len(contents)} messages")
            
            response = client.models.generate_content(
                model=settings.LLM_GEMINI_MODEL,
                contents=contents,
                config=config
            )
            
            tool_calls = []
            text_parts = []
            
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        tool_calls.append(ToolCallRequest(
                            id=f"gemini_{fc.name}_{len(tool_calls)}",
                            name=fc.name,
                            parameters=dict(fc.args) if fc.args else {}
                        ))
                    elif hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
            
            if tool_calls:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Gemini requested {len(tool_calls)} tool calls: {[tc.name for tc in tool_calls]}")
                return ToolCallResponse(
                    is_tool_call=True,
                    tool_calls=tool_calls,
                    raw_response=response
                )
            
            text_response = "".join(text_parts) if text_parts else (response.text or "")
            return ToolCallResponse(
                text_response=text_response,
                is_tool_call=False,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Gemini tool call error: {e}", exc_info=True)
            raise
    
    
    async def generate_structured(
        self,
        messages: list[dict[str, Any]],
        output_model: type[T],
        provider: LLMProvider = "claude",
        system_prompt: str | None = None,
        max_tokens: int = 4096
    ) -> T:
        """
        Generate a response conforming to a Pydantic model schema.
        
        Uses provider-specific structured output mechanisms:
        - Claude: Tool calling with model schema as "respond" tool
        - Gemini: response_schema parameter with JSON schema
        
        Args:
            messages: List of message dicts with role and content
            output_model: Pydantic model class defining expected output structure
            provider: LLM provider to use ("claude" or "gemini")
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            
        Returns:
            Validated Pydantic model instance
            
        Raises:
            ValueError: If structured output parsing fails
        """
        # === E6: PII stripping (LGPD Art. 12 / EU AI Act Art. 13) ===
        # Strip PII from each user/assistant message content before sending to provider.
        for _msg in messages:
            _content = _msg.get("content", "")
            if isinstance(_content, str) and _content:
                _msg["content"] = strip_pii_for_llm_prompt(_content)
        if system_prompt:
            system_prompt = strip_pii_for_llm_prompt(system_prompt)

        # === E7: Audit logging ===
        _cid = getattr(self, "_current_tenant", "") or get_current_llm_tenant()
        logger.info(
            "[LLMService] generate_structured tenant=%s provider=%s output_model=%s msg_count=%d",
            _cid or "global", provider, output_model.__name__, len(messages),
        )
        try:
            if _cid and _audit_svc:
                await _audit_svc.log_decision(  # AUDIT-NO-DEMO: LLM structured call telemetry (infrastructure layer; no candidate decision; LGPD Art.20 N/A)
                    company_id=_cid,
                    action="llm_call",
                    resource_type="llm_provider",
                    resource_id=f"{provider}:structured:{output_model.__name__}",
                    details={
                        "provider": provider,
                        "method": "generate_structured",
                        "output_model": output_model.__name__,
                        "msg_count": len(messages),
                    },
                    user_id="system",
                )
        except Exception:
            pass  # Audit non-blocking

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Generating structured output: {output_model.__name__} via {provider}")
        
        if provider == "claude":
            return await self._generate_structured_claude(
                messages, output_model, system_prompt, max_tokens
            )
        elif provider == "gemini":
            return await self._generate_structured_gemini(
                messages, output_model, system_prompt, max_tokens
            )
        else:
            raise ValueError(f"Provider {provider} does not support structured outputs")
    
    async def _generate_structured_claude(
        self,
        messages: list[dict[str, Any]],
        output_model: type[T],
        system_prompt: str | None = None,
        max_tokens: int = 4096
    ) -> T:
        """Generate structured output using Claude's tool calling."""
        from app.domains.ai.services.structured_output import (
            parse_claude_tool_response,
            parse_json_from_text,
            structured_output_service,
        )
        from app.shared.providers.llm_factory import get_provider_for_tenant
        _claude_provider = get_provider_for_tenant().get("claude")
        client = _claude_provider._get_client()
        
        tool = structured_output_service.get_claude_tool(output_model, "respond")
        
        enhanced_system = system_prompt or ""
        enhanced_system += "\n\nYou MUST use the 'respond' tool to provide your response in the exact format specified. Do not respond with plain text."
        
        try:
            request_kwargs = {
                "model": settings.LLM_PRIMARY_MODEL,
                "max_tokens": max_tokens,
                "messages": messages,
                "tools": [tool],
                "tool_choice": {"type": "tool", "name": "respond"},
                "system": enhanced_system.strip()
            }
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.debug(f"Claude structured request: model={output_model.__name__}")
            
            response = client.messages.create(**request_kwargs)
            
            try:
                result = parse_claude_tool_response(response, output_model, "respond")
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Successfully parsed structured output: {output_model.__name__}")
                return result
            except ValueError as parse_error:
                logger.warning(f"Tool response parsing failed, trying text fallback: {parse_error}")
                text_parts = []
                for block in response.content:
                    if hasattr(block, 'type') and block.type == "text":
                        text_parts.append(block.text)
                if text_parts:
                    return parse_json_from_text("".join(text_parts), output_model)
                raise
                
        except Exception as e:
            logger.error(f"Claude structured output error: {e}", exc_info=True)
            raise ValueError(f"Failed to generate structured output: {e}")
    
    async def _generate_structured_gemini(
        self,
        messages: list[dict[str, Any]],
        output_model: type[T],
        system_prompt: str | None = None,
        max_tokens: int = 4096
    ) -> T:
        """Generate structured output using Gemini's response_schema."""
        from google.genai import types

        from app.domains.ai.services.structured_output import (
            parse_gemini_json_response,
            parse_json_from_text,
            structured_output_service,
        )
        
        client = self.gemini_native
        
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=content if isinstance(content, str) else str(content))]
                ))
            elif role == "assistant" or role == "model":
                if content:
                    contents.append(types.Content(
                        role="model",
                        parts=[types.Part(text=content if isinstance(content, str) else str(content))]
                    ))
        
        gemini_schema = structured_output_service.get_gemini_schema(output_model)
        
        enhanced_system = system_prompt or ""
        enhanced_system += "\n\nRespond with a valid JSON object matching this schema. Do not include any text outside the JSON."
        
        try:
            config = types.GenerateContentConfig(
                system_instruction=enhanced_system.strip() if enhanced_system.strip() else None,
                response_mime_type="application/json",
                response_schema=gemini_schema,
                max_output_tokens=max_tokens
            )
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.debug(f"Gemini structured request: model={output_model.__name__}")
            
            response = client.models.generate_content(
                model=settings.LLM_GEMINI_MODEL,
                contents=contents,
                config=config
            )
            
            try:
                result = parse_gemini_json_response(response, output_model)
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Successfully parsed structured output: {output_model.__name__}")
                return result
            except ValueError as parse_error:
                logger.warning(f"Gemini response parsing failed, trying text fallback: {parse_error}")
                if hasattr(response, 'text') and response.text:
                    return parse_json_from_text(response.text, output_model)
                raise
                
        except Exception as e:
            logger.error(f"Gemini structured output error: {e}", exc_info=True)
            raise ValueError(f"Failed to generate structured output: {e}")
    
    

    def _get_claude_for_model(self, model_name: str) -> "ChatAnthropic":
        """Create a ChatAnthropic instance for a specific model name."""
        api_key = (
            settings.AI_INTEGRATIONS_ANTHROPIC_API_KEY
            or settings.ANTHROPIC_API_KEY
        )
        if not api_key:
            raise ValueError("No Anthropic API key configured")

        kwargs: dict[str, Any] = {
            "model_name": model_name,
            "api_key": api_key,
            "temperature": settings.LLM_AGENT_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
            "timeout": settings.LLM_TIMEOUT_SECONDS,
        }
        if settings.AI_INTEGRATIONS_ANTHROPIC_BASE_URL:
            kwargs["base_url"] = settings.AI_INTEGRATIONS_ANTHROPIC_BASE_URL

        return ChatAnthropic(**kwargs)  # type: ignore[arg-type]

    async def safe_invoke(self, prompt: str, provider: str = "claude", **kwargs) -> str:
        """Wrapper for direct .claude.ainvoke() calls — adds PII stripping + audit.

        Use this instead of llm_service.claude.ainvoke(prompt) directly.
        Gradually migrate direct .ainvoke() calls to this method.
        """
        # E6: PII stripping
        prompt = strip_pii_for_llm_prompt(prompt)

        # E7: Audit
        _cid = get_current_llm_tenant()
        _start = _time.time()
        logger.info(
            "[LLMService] safe_invoke tenant=%s provider=%s prompt_len=%d",
            _cid or "global", provider, len(prompt)
        )

        if provider == "claude":
            response = await self.claude.ainvoke(prompt, **kwargs)
        elif provider == "openai":
            response = await self.openai.ainvoke(prompt, **kwargs)
        else:
            return await self.generate_with_gemini(prompt)

        _latency = (_time.time() - _start) * 1000
        content = response.content
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(str(block.get("text", "")))
                elif isinstance(block, str):
                    text_parts.append(block)
                elif hasattr(block, "text"):
                    text_parts.append(str(getattr(block, "text", "")))
            return "".join(text_parts)
        return str(content) if content else ""


llm_service = LLMService()

# FastAPI dependency injection factory
def get_llm_service() -> "LLMService":
    """Returns the shared LLMService singleton. Creates lazy HTTP clients on first call."""
    return llm_service


async def get_claude_response(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 2048
) -> str:
    """
    Helper function for simple Claude API calls.
    
    Args:
        system_prompt: System context for Claude
        user_message: User's message/prompt
        max_tokens: Maximum tokens in response
        
    Returns:
        Claude's text response
    """
    from app.shared.providers.llm_factory import get_provider_for_tenant

    container = get_provider_for_tenant()
    return await container.generate_with_fallback(user_message, system=system_prompt, agent_type="LLMServiceAgent")
