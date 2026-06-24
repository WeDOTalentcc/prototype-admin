"""DeepSeek LLM Provider implementation (W2-011 · OpenAI-compatible API).

DeepSeek API é OpenAI-compatible (https://api.deepseek.com/v1) — reusa o SDK
`openai` Python apontando para custom base_url. NÃO requer SDK dedicada.

Modelos canonical:
- `deepseek-chat` — general-purpose, padrão DeepSeek-V3 (default)
- `deepseek-reasoner` — DeepSeek-R1 reasoning model

Opt-in only: NÃO entra em FALLBACK_ORDER default. Tenant precisa setar
`primary_provider="deepseek"` ou incluir explicitamente em custom fallback_order
via `LLMConfigRequest`.

LGPD nota (W2-012): DeepSeek runs em data centers China (Hangzhou). Provider
NÃO expõe header data-residency. Cliente que opta por DeepSeek aceita que
LGPD Art 33 region pinning não se aplica.
"""
import logging
import os

from app.shared.providers.llm_provider import (
    LLMProviderABC,
    LLMResponse,
    LLMToolCall,
    LLMToolResponse,
)
from app.shared.providers.llm_retry import llm_transient_retry
from app.shared.resilience.circuit_breaker import (
    DEEPSEEK_CIRCUIT,
    circuit_breaker_decorator,
)

logger = logging.getLogger(__name__)

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


class DeepSeekLLMProvider(LLMProviderABC):
    """DeepSeek LLM provider (OpenAI-compatible API)."""

    _provider_name = "deepseek"
    _default_model = "deepseek-chat"

    def __init__(self, api_key: str | None = None, region: str | None = None):
        self._client = None
        self._custom_api_key = api_key
        # W2-012 (2026-05-22): region kwarg presente para uniformidade
        # de interface. DeepSeek não suporta region pinning — armazenado mas
        # não consumido (vide docstring deste módulo).
        self._region = region

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def default_model(self) -> str:
        return self._default_model

    def _get_client(self):
        if not self._client:
            from openai import OpenAI

            api_key = self._custom_api_key or os.environ.get("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("No DeepSeek API key configured")
            self._client = OpenAI(
                api_key=api_key,
                base_url=DEEPSEEK_BASE_URL,
            )
        return self._client

    @circuit_breaker_decorator(DEEPSEEK_CIRCUIT)
    @llm_transient_retry
    async def generate(self, prompt, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        client = self._get_client()
        response = client.chat.completions.create(
            model=model or self._default_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = response.choices[0].message.content or ""
        usage = (
            {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }
            if response.usage
            else {}
        )
        return LLMResponse(
            text=text,
            provider=self._provider_name,
            model=model or self._default_model,
            usage=usage,
            raw_response=response,
        )

    @circuit_breaker_decorator(DEEPSEEK_CIRCUIT)
    @llm_transient_retry
    async def generate_with_system(
        self, system_prompt, user_message, model=None, temperature=0.7, max_tokens=4096, **kwargs
    ):
        client = self._get_client()
        response = client.chat.completions.create(
            model=model or self._default_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = response.choices[0].message.content or ""
        usage = (
            {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }
            if response.usage
            else {}
        )
        return LLMResponse(
            text=text,
            provider=self._provider_name,
            model=model or self._default_model,
            usage=usage,
            raw_response=response,
        )

    @circuit_breaker_decorator(DEEPSEEK_CIRCUIT)
    @llm_transient_retry
    async def generate_with_tools(
        self, messages, tools, system_prompt=None, max_tokens=4096, **kwargs
    ):
        import json

        client = self._get_client()
        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})
        openai_messages.extend(messages)
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", t.get("input_schema", {})),
                },
            }
            for t in tools
        ]
        response = client.chat.completions.create(
            model=self._default_model,
            messages=openai_messages,
            tools=openai_tools if openai_tools else None,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        if choice.message.tool_calls:
            tool_calls = [
                LLMToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    parameters=json.loads(tc.function.arguments),
                )
                for tc in choice.message.tool_calls
            ]
            return LLMToolResponse(
                tool_calls=tool_calls,
                is_tool_call=True,
                provider=self._provider_name,
                model=self._default_model,
                raw_response=response,
            )
        return LLMToolResponse(
            text=choice.message.content,
            is_tool_call=False,
            provider=self._provider_name,
            model=self._default_model,
            raw_response=response,
        )

    @circuit_breaker_decorator(DEEPSEEK_CIRCUIT)
    @llm_transient_retry
    async def generate_structured(
        self, messages, output_schema, system_prompt=None, max_tokens=4096, **kwargs
    ):
        import json

        client = self._get_client()
        openai_messages = []
        if system_prompt:
            openai_messages.append(
                {"role": "system", "content": system_prompt + "\n\nRespond with valid JSON."}
            )
        openai_messages.extend(messages)
        response = client.chat.completions.create(
            model=self._default_model,
            messages=openai_messages,
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
        )
        return json.loads(response.choices[0].message.content or "{}")
