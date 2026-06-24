"""Claude LLM Provider implementation."""
import logging
import os
import time


from app.shared.providers.llm_provider import LLMProviderABC, LLMResponse, LLMToolCall, LLMToolResponse
from app.shared.resilience.circuit_breaker import ANTHROPIC_CIRCUIT, circuit_breaker_decorator
from app.shared.providers.llm_retry import llm_transient_retry

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

# Prometheus metrics canonical pattern (vide wizard_session_service.py:42-62).
# Idempotente entre reimports + fail-open se prometheus indisponível.
try:  # pragma: no cover — exercitado via integração
    from prometheus_client import Counter as _PromCounter  # type: ignore
    from prometheus_client import Histogram as _PromHistogram  # type: ignore
    from prometheus_client import REGISTRY as _PROM_REGISTRY  # type: ignore

    _existing_req = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(
        "lia_llm_requests_total"
    )
    if _existing_req is not None:
        llm_requests_total = _existing_req
    else:
        llm_requests_total = _PromCounter(
            "lia_llm_requests_total",
            "Total de requests LLM segmentado por provider e status (success/error).",
            labelnames=("provider", "status"),
        )

    _existing_lat = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(
        "lia_llm_latency_seconds"
    )
    if _existing_lat is not None:
        llm_latency_seconds = _existing_lat
    else:
        llm_latency_seconds = _PromHistogram(
            "lia_llm_latency_seconds",
            "Latência LLM (segundos) por provider.",
            labelnames=("provider",),
        )
except Exception:  # pragma: no cover — fail-OPEN se prometheus indisponível
    llm_requests_total = None
    llm_latency_seconds = None


# W2-008 (2026-05-22): Anthropic prompt caching · 50-80% economia em
# sessions longas. Beta header GA desde Nov/2024 mas mantido por compat.
# Cache breakpoint mínimo Anthropic: 1024 tokens (Sonnet) / 2048 (Haiku).
# Abaixo do threshold, cache_control é ignorado silenciosamente (no-op).
ANTHROPIC_PROMPT_CACHE_BETA = "prompt-caching-2024-07-31"
ANTHROPIC_CACHE_HEADERS = {"anthropic-beta": ANTHROPIC_PROMPT_CACHE_BETA}


def _system_with_cache_control(system_prompt: str | None):
    """Convert system string → cacheable blocks list (W2-008).

    Anthropic API aceita system como str OU list de blocks. Para
    prompt caching, precisa ser list com `cache_control: ephemeral`.
    Strings curtas (<1024 tokens) são cacheadas como no-op (Anthropic
    ignora cache breakpoints abaixo do threshold).
    """
    if not system_prompt:
        return system_prompt
    return [
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }
    ]


def _build_usage_with_cache(response) -> dict:
    """Extract usage incluindo cache metrics (W2-008).

    Anthropic response.usage tem 4 campos relevantes pra cache:
      - input_tokens · prompt tokens não-cacheados
      - cache_creation_input_tokens · prompt tokens escritos no cache (1ª vez)
      - cache_read_input_tokens · prompt tokens lidos do cache (hits)
      - output_tokens · completion tokens
    """
    usage = response.usage
    return {
        "input_tokens": getattr(usage, "input_tokens", 0),
        "output_tokens": getattr(usage, "output_tokens", 0),
        "cache_creation_input_tokens": getattr(
            usage, "cache_creation_input_tokens", 0
        ),
        "cache_read_input_tokens": getattr(
            usage, "cache_read_input_tokens", 0
        ),
    }


def _log_cache_metrics(method_name: str, usage_dict: dict) -> None:
    """Log canary cache hit rate per-call (W2-008 observability)."""
    created = usage_dict.get("cache_creation_input_tokens", 0)
    read = usage_dict.get("cache_read_input_tokens", 0)
    total_cacheable = created + read
    if total_cacheable > 0:
        hit_rate = read / total_cacheable
        logger.info(
            "[anthropic_cache] method=%s created=%d read=%d hit_rate=%.2f",
            method_name, created, read, hit_rate,
        )


class ClaudeLLMProvider(LLMProviderABC):
    """Claude/Anthropic LLM provider implementation."""

    _provider_name = "claude"
    _default_model = "claude-sonnet-4-6"

    def __init__(self, api_key: str | None = None, region: str | None = None):
        self._client = None
        self._async_client = None
        self._custom_api_key = api_key
        # W2-012 (2026-05-22): LGPD Art 33 per-tenant region pinning.
        # None = sem region constraint (default global do provider).
        self._region = region

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
            # W2-012 (2026-05-22): LGPD Art 7 §II + Art 33 — opt-out de
            # treinamento + declaração de jurisdição. Header canonical do
            # Anthropic API. Aplicado a TODA construção do client.
            kwargs = {
                "api_key": api_key,
                "default_headers": {"anthropic-no-train": "true"},
            }
            if base_url:
                kwargs["base_url"] = base_url
            self._client = Anthropic(**kwargs)
        return self._client

    def _get_async_client(self):
        """Return AsyncAnthropic client for async methods.

        Bug C canonical fix (2026-05-24): async methods in this provider
        MUST use AsyncAnthropic + `await client.messages.create(...)`.
        Calling the sync Anthropic client from a running event loop
        triggers _enforce_credit_gate_sync's loud-fail RuntimeError
        ("called from running event loop") because is_local=true
        transaction-scoped gate cannot run inside an existing loop.

        LGPD Art 7 §II + Art 33 headers preserved (anthropic-no-train).
        """
        if not self._async_client:
            from anthropic import AsyncAnthropic
            api_key = (
                self._custom_api_key
                or os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
                or os.environ.get("ANTHROPIC_API_KEY")
            )
            base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
            if not api_key:
                raise ValueError("No Claude API key configured")
            kwargs = {
                "api_key": api_key,
                "default_headers": {"anthropic-no-train": "true"},
            }
            if base_url:
                kwargs["base_url"] = base_url
            self._async_client = AsyncAnthropic(**kwargs)
        return self._async_client

    @circuit_breaker_decorator(ANTHROPIC_CIRCUIT)
    @llm_transient_retry
    @_traceable(name="Claude Generate", run_type="llm")
    async def generate(self, prompt, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        client = self._get_async_client()
        t_start = time.time()
        status = "success"
        try:
            response = await client.messages.create(
                model=model or self._default_model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                extra_headers=ANTHROPIC_CACHE_HEADERS,
            )
            text = response.content[0].text if response.content else ""
            usage_dict = _build_usage_with_cache(response)
            _log_cache_metrics("generate", usage_dict)
            return LLMResponse(
                text=text,
                provider=self._provider_name,
                model=model or self._default_model,
                usage=usage_dict,
                raw_response=response,
            )
        except Exception:
            status = "error"
            raise
        finally:
            if llm_requests_total is not None:
                llm_requests_total.labels(provider="claude", status=status).inc()
            if llm_latency_seconds is not None:
                llm_latency_seconds.labels(provider="claude").observe(time.time() - t_start)

    @circuit_breaker_decorator(ANTHROPIC_CIRCUIT)
    @llm_transient_retry
    @_traceable(name="Claude GenerateWithSystem", run_type="llm")
    async def generate_with_system(self, system_prompt, user_message, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        client = self._get_async_client()
        t_start = time.time()
        status = "success"
        try:
            response = await client.messages.create(
                model=model or self._default_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=_system_with_cache_control(system_prompt),
                messages=[{"role": "user", "content": user_message}],
                extra_headers=ANTHROPIC_CACHE_HEADERS,
            )
            text = response.content[0].text if response.content else ""
            usage_dict = _build_usage_with_cache(response)
            _log_cache_metrics("generate_with_system", usage_dict)
            return LLMResponse(
                text=text,
                provider=self._provider_name,
                model=model or self._default_model,
                usage=usage_dict,
                raw_response=response,
            )
        except Exception:
            status = "error"
            raise
        finally:
            if llm_requests_total is not None:
                llm_requests_total.labels(provider="claude", status=status).inc()
            if llm_latency_seconds is not None:
                llm_latency_seconds.labels(provider="claude").observe(time.time() - t_start)

    @circuit_breaker_decorator(ANTHROPIC_CIRCUIT)
    @llm_transient_retry
    @_traceable(name="Claude GenerateWithTools", run_type="llm")
    async def generate_with_tools(self, messages, tools, system_prompt=None, max_tokens=4096, **kwargs):
        client = self._get_async_client()
        t_start = time.time()
        status = "success"
        try:
            request_kwargs = {
                "model": self._default_model,
                "max_tokens": max_tokens,
                "messages": messages,
                "extra_headers": ANTHROPIC_CACHE_HEADERS,  # W2-008
            }
            if tools:
                request_kwargs["tools"] = tools
            if system_prompt:
                request_kwargs["system"] = _system_with_cache_control(system_prompt)
            response = await client.messages.create(**request_kwargs)
            _log_cache_metrics("generate_with_tools", _build_usage_with_cache(response))
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
            if llm_requests_total is not None:
                llm_requests_total.labels(provider="claude", status=status).inc()
            if llm_latency_seconds is not None:
                llm_latency_seconds.labels(provider="claude").observe(time.time() - t_start)

    @circuit_breaker_decorator(ANTHROPIC_CIRCUIT)
    @llm_transient_retry
    @_traceable(name="Claude GenerateStructured", run_type="llm")
    async def generate_structured(self, messages, output_schema, system_prompt=None, max_tokens=4096, **kwargs):
        tool = {"name": "respond", "description": "Respond with structured output", "input_schema": output_schema}
        client = self._get_async_client()
        t_start = time.time()
        status = "success"
        try:
            enhanced_system = (system_prompt or "") + "\n\nYou MUST use the 'respond' tool to provide your response."
            response = await client.messages.create(
                model=self._default_model,
                max_tokens=max_tokens,
                messages=messages,
                tools=[tool],
                tool_choice={"type": "tool", "name": "respond"},
                system=_system_with_cache_control(enhanced_system.strip()),
                extra_headers=ANTHROPIC_CACHE_HEADERS,  # W2-008
            )
            _log_cache_metrics("generate_structured", _build_usage_with_cache(response))
            for block in response.content:
                if hasattr(block, "type") and block.type == "tool_use" and block.name == "respond":
                    return block.input if isinstance(block.input, dict) else {}
            return {}
        except Exception:
            status = "error"
            raise
        finally:
            if llm_requests_total is not None:
                llm_requests_total.labels(provider="claude", status=status).inc()
            if llm_latency_seconds is not None:
                llm_latency_seconds.labels(provider="claude").observe(time.time() - t_start)
