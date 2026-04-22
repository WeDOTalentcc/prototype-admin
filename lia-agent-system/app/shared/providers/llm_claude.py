"""Claude LLM Provider implementation."""
import logging
import os
import time


from app.shared.providers.llm_provider import LLMProviderABC, LLMResponse, LLMToolCall, LLMToolResponse
from app.shared.resilience.circuit_breaker import ANTHROPIC_CIRCUIT, circuit_breaker_decorator

logger = logging.getLogger(__name__)

try:
    from langsmith import traceable as _traceable
    _LANGSMITH_AVAILABLE = True
except ImportError:
    _LANGSMITH_AVAILABLE = False
    def _traceable(**kwargs):  # type: ignore[misc]
        def decorator(fn):
            return fn
        return decorator

_METRICS_AVAILABLE = False


class ClaudeLLMProvider(LLMProviderABC):
    """Claude/Anthropic LLM provider implementation."""

    _provider_name = "claude"
    _default_model = "claude-sonnet-4-6"

    def __init__(self, api_key: str | None = None):
        self._client = None
        self._custom_api_key = api_key

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def default_model(self) -> str:
        return self._default_model

    def _get_client(self):
        if not self._client:
            from anthropic import Anthropic
            api_key = self._custom_api_key or os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
            base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
            if not api_key:
                raise ValueError("No Claude API key configured")
            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            self._client = Anthropic(**kwargs)
        return self._client

    @circuit_breaker_decorator(ANTHROPIC_CIRCUIT)
    @_traceable(name="Claude Generate", run_type="llm")
    async def generate(self, prompt, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        client = self._get_client()
        t_start = time.time()
        status = "success"
        try:
            response = client.messages.create(
                model=model or self._default_model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text if response.content else ""
            return LLMResponse(
                text=text,
                provider=self._provider_name,
                model=model or self._default_model,
                usage={"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
                raw_response=response,
            )
        except Exception:
            status = "error"
            raise
        finally:
            if _METRICS_AVAILABLE:
                llm_requests_total.labels(provider="claude", status=status).inc()
                llm_latency_seconds.labels(provider="claude").observe(time.time() - t_start)

    @circuit_breaker_decorator(ANTHROPIC_CIRCUIT)
    @_traceable(name="Claude GenerateWithSystem", run_type="llm")
    async def generate_with_system(self, system_prompt, user_message, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        client = self._get_client()
        t_start = time.time()
        status = "success"
        try:
            response = client.messages.create(
                model=model or self._default_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            text = response.content[0].text if response.content else ""
            return LLMResponse(
                text=text,
                provider=self._provider_name,
                model=model or self._default_model,
                usage={"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
                raw_response=response,
            )
        except Exception:
            status = "error"
            raise
        finally:
            if _METRICS_AVAILABLE:
                llm_requests_total.labels(provider="claude", status=status).inc()
                llm_latency_seconds.labels(provider="claude").observe(time.time() - t_start)

    @circuit_breaker_decorator(ANTHROPIC_CIRCUIT)
    @_traceable(name="Claude GenerateWithTools", run_type="llm")
    async def generate_with_tools(self, messages, tools, system_prompt=None, max_tokens=4096, **kwargs):
        client = self._get_client()
        t_start = time.time()
        status = "success"
        try:
            request_kwargs = {"model": self._default_model, "max_tokens": max_tokens, "messages": messages}
            if tools:
                request_kwargs["tools"] = tools
            if system_prompt:
                request_kwargs["system"] = system_prompt
            response = client.messages.create(**request_kwargs)
            tool_calls = []
            text_parts = []
            for block in response.content:
                if hasattr(block, "type"):
                    if block.type == "text":
                        text_parts.append(block.text)
                    elif block.type == "tool_use":
                        tool_calls.append(
                            LLMToolCall(
                                id=block.id,
                                name=block.name,
                                parameters=block.input if isinstance(block.input, dict) else {},
                            )
                        )
            return LLMToolResponse(
                text="".join(text_parts) if text_parts else None,
                tool_calls=tool_calls,
                is_tool_call=bool(tool_calls),
                provider=self._provider_name,
                model=self._default_model,
                raw_response=response,
            )
        except Exception:
            status = "error"
            raise
        finally:
            if _METRICS_AVAILABLE:
                llm_requests_total.labels(provider="claude", status=status).inc()
                llm_latency_seconds.labels(provider="claude").observe(time.time() - t_start)

    @circuit_breaker_decorator(ANTHROPIC_CIRCUIT)
    @_traceable(name="Claude GenerateStructured", run_type="llm")
    async def generate_structured(self, messages, output_schema, system_prompt=None, max_tokens=4096, **kwargs):
        tool = {"name": "respond", "description": "Respond with structured output", "input_schema": output_schema}
        client = self._get_client()
        t_start = time.time()
        status = "success"
        try:
            enhanced_system = (system_prompt or "") + "\n\nYou MUST use the 'respond' tool to provide your response."
            response = client.messages.create(
                model=self._default_model,
                max_tokens=max_tokens,
                messages=messages,
                tools=[tool],
                tool_choice={"type": "tool", "name": "respond"},
                system=enhanced_system.strip(),
            )
            for block in response.content:
                if hasattr(block, "type") and block.type == "tool_use" and block.name == "respond":
                    return block.input if isinstance(block.input, dict) else {}
            return {}
        except Exception:
            status = "error"
            raise
        finally:
            if _METRICS_AVAILABLE:
                llm_requests_total.labels(provider="claude", status=status).inc()
                llm_latency_seconds.labels(provider="claude").observe(time.time() - t_start)
