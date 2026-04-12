"""
LLM service for Claude, OpenAI, and Gemini.
Uses Replit AI Integrations for LLM access.
Supports function calling (tool use) for agent systems.
Supports structured outputs with Pydantic models.
"""
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

logger = logging.getLogger(__name__)

LLMProvider = Literal["claude", "openai", "gemini"]

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


@dataclass

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
                    max_tokens=settings.LLM_MAX_TOKENS,  # type: ignore
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
                    max_tokens=settings.LLM_MAX_TOKENS,  # type: ignore
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
            client = self.gemini_native

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
            client = self.gemini_native
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
                await _audit_svc.log_decision(
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
        # E6: PII stripping
        strip_pii_for_llm_prompt(prompt)

        if provider == "claude":
            return await self._generate_with_tools_claude(
                messages, tools, system_prompt, max_tokens
            )
        elif provider == "gemini":
            return await self._generate_with_tools_gemini(
                messages, tools, system_prompt, max_tokens
            )
        else:
            raise ValueError(f"Provider {provider} does not support tool calling")
    
    async def _generate_with_tools_claude(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system_prompt: str | None = None,
        max_tokens: int = 4096
    ) -> ToolCallResponse:
        """Generate with Claude's tool_use via anthropic SDK."""
        from app.shared.providers.llm_factory import LLMProviderFactory
        _claude_provider = LLMProviderFactory.get("claude")
        client = _claude_provider._get_client()

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
            
            response = client.messages.create(**request_kwargs)
            
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
    
    async def generate_with_tool_loop(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_executor,
        provider: LLMProvider = "claude",
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        agent_type: str | None = None,
        conversation_id: str | None = None
    ) -> str:
        """
        Generate response with automatic tool execution loop.
        
        Handles the full cycle: call LLM -> if tool_call, execute, 
        send result back -> repeat until text response.
        
        Args:
            messages: Initial message list
            tools: Tool schemas
            tool_executor: ToolExecutor instance to execute tools
            provider: LLM provider
            system_prompt: Optional system prompt
            max_tokens: Max tokens
            agent_type: Agent type for authorization
            conversation_id: Conversation ID for logging
            
        Returns:
            Final text response after tool execution
        """
        # E6: PII stripping
        if isinstance(prompt, str): strip_pii_for_llm_prompt(prompt)

        current_messages = list(messages)
        loop_count = 0
        
        while loop_count < MAX_TOOL_CALLS_PER_REQUEST:
            loop_count += 1
            
            response = await self.generate_with_tools(
                messages=current_messages,
                tools=tools,
                provider=provider,
                system_prompt=system_prompt,
                max_tokens=max_tokens
            )
            
            if not response.is_tool_call:
                return response.text_response or ""
            
            for tool_call in response.tool_calls:
                logger.info(f"Executing tool: {tool_call.name}")
                
                result = await tool_executor.execute(
                    tool_name=tool_call.name,
                    parameters=tool_call.parameters,
                    agent_type=agent_type,
                    conversation_id=conversation_id
                )
                
                if provider == "claude":
                    current_messages.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": tool_call.id,
                                "name": tool_call.name,
                                "input": tool_call.parameters
                            }
                        ]
                    })
                    current_messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_call.id,
                                "content": result.to_llm_content()
                            }
                        ]
                    })
                elif provider == "gemini":
                    current_messages.append({
                        "role": "assistant",
                        "content": f"Called tool: {tool_call.name}",
                        "function_call": {
                            "name": tool_call.name,
                            "args": tool_call.parameters
                        }
                    })
                    current_messages.append({
                        "role": "function_response",
                        "name": tool_call.name,
                        "response": result.to_dict()
                    })
                else:
                    current_messages.append({
                        "role": "assistant",
                        "content": f"Called tool: {tool_call.name}"
                    })
                    current_messages.append({
                        "role": "tool",
                        "tool_result": result.to_dict()
                    })
        
        logger.warning(f"Tool loop reached max iterations ({MAX_TOOL_CALLS_PER_REQUEST})")
        
        final_response = await self.generate_with_tools(
            messages=current_messages,
            tools=[],
            provider=provider,
            system_prompt=system_prompt,
            max_tokens=max_tokens
        )
        
        return final_response.text_response or "Unable to complete the request."
    
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
        # E6: PII stripping
        strip_pii_for_llm_prompt(prompt)

        
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
        from app.shared.providers.llm_factory import LLMProviderFactory
        _claude_provider = LLMProviderFactory.get("claude")
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
            
            logger.debug(f"Claude structured request: model={output_model.__name__}")
            
            response = client.messages.create(**request_kwargs)
            
            try:
                result = parse_claude_tool_response(response, output_model, "respond")
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
            
            logger.debug(f"Gemini structured request: model={output_model.__name__}")
            
            response = client.models.generate_content(
                model=settings.LLM_GEMINI_MODEL,
                contents=contents,
                config=config
            )
            
            try:
                result = parse_gemini_json_response(response, output_model)
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
    
    async def generate_with_prompt_template(
        self,
        template_name: str,
        context: dict[str, Any],
        user_message: str | None = None,
        provider: LLMProvider = "gemini",
        **kwargs
    ) -> str:
        """
        Generate response using a registered prompt template.
        
        This method integrates with the prompt engineering system to provide:
        - Automatic few-shot example injection
        - Chain-of-Thought reasoning when enabled
        - Context variable interpolation
        
        Args:
            template_name: Name of the registered template (e.g., "job_field_extraction")
            context: Dictionary of variables to interpolate in the template
            user_message: Optional user message to include
            provider: LLM provider to use
            **kwargs: Additional arguments passed to generate()
            
        Returns:
            Generated text response
            
        Raises:
            KeyError: If template not found in PromptLibrary
        """
        # E6: PII stripping
        if isinstance(prompt, str): strip_pii_for_llm_prompt(prompt)

        from app.prompts.templates import PromptLibrary
        
        template = PromptLibrary.get(template_name)
        
        rendered_prompt = template.render(context)
        
        if user_message:
            full_prompt = f"{rendered_prompt}\n\nMensagem do usuário: {user_message}"
        else:
            full_prompt = rendered_prompt
        
        logger.info(f"Generating with template '{template_name}' via {provider}")
        logger.debug(f"Template has {len(template.few_shot_examples)} examples, CoT={template.cot_enabled}")
        
        return await self.generate(full_prompt, provider=provider, **kwargs)
    
    async def generate_with_template_structured(
        self,
        template_name: str,
        context: dict[str, Any],
        output_model: type[T],
        user_message: str | None = None,
        provider: LLMProvider = "gemini",
        **kwargs
    ) -> T:
        """
        Generate structured response using a registered prompt template.
        
        Combines prompt templates with structured output parsing.
        
        Args:
            template_name: Name of the registered template
            context: Dictionary of variables to interpolate
            output_model: Pydantic model for structured output
            user_message: Optional user message to include
            provider: LLM provider to use
            **kwargs: Additional arguments
            
        Returns:
            Validated Pydantic model instance
        """
        # E6: PII stripping
        if isinstance(prompt, str): strip_pii_for_llm_prompt(prompt)

        from app.prompts.templates import PromptLibrary
        
        template = PromptLibrary.get(template_name)
        
        system_prompt = template.render_system_prompt(context)
        
        if user_message:
            user_content = template.render_user_message(user_message, context)
        else:
            user_content = template.render(context)
        
        messages = [{"role": "user", "content": user_content}]
        
        logger.info(f"Generating structured output with template '{template_name}' via {provider}")
        
        return await self.generate_structured(
            messages=messages,
            output_model=output_model,
            provider=provider,
            system_prompt=system_prompt,
            **kwargs
        )

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
    return await container.generate_with_fallback(user_message, system=system_prompt)
