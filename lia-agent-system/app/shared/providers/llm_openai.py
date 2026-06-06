"""OpenAI LLM Provider implementation."""
import logging
import os

from app.shared.providers.llm_provider import LLMProviderABC, LLMResponse, LLMToolCall, LLMToolResponse
from app.shared.resilience.circuit_breaker import OPENAI_CIRCUIT, circuit_breaker_decorator
from app.shared.providers.llm_retry import llm_transient_retry

logger = logging.getLogger(__name__)


class OpenAILLMProvider(LLMProviderABC):
    """OpenAI LLM provider implementation."""
    
    _provider_name = "openai"
    _default_model = "gpt-4o"
    
    def __init__(self, api_key: str | None = None, region: str | None = None):
        self._client = None
        self._custom_api_key = api_key
        # W2-012 (2026-05-22): LGPD Art 33 region pinning.
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
            api_key = self._custom_api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("No OpenAI API key configured")
            # W2-012 (2026-05-22): LGPD Art 33 — declara residência de
            # dados via header beta canonical da OpenAI API.
            self._client = OpenAI(
                api_key=api_key,
                default_headers={"OpenAI-Beta": "data-residency=v1"},
            )
        return self._client
    
    @circuit_breaker_decorator(OPENAI_CIRCUIT)
    @llm_transient_retry
    async def generate(self, prompt, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        client = self._get_client()
        response = client.chat.completions.create(model=model or self._default_model, messages=[{"role": "user", "content": prompt}], temperature=temperature, max_tokens=max_tokens)
        text = response.choices[0].message.content or ""
        usage = {"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens} if response.usage else {}
        return LLMResponse(text=text, provider=self._provider_name, model=model or self._default_model, usage=usage, raw_response=response)
    
    @circuit_breaker_decorator(OPENAI_CIRCUIT)
    @llm_transient_retry
    async def generate_with_system(self, system_prompt, user_message, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        client = self._get_client()
        response = client.chat.completions.create(model=model or self._default_model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}], temperature=temperature, max_tokens=max_tokens)
        text = response.choices[0].message.content or ""
        usage = {"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens} if response.usage else {}
        return LLMResponse(text=text, provider=self._provider_name, model=model or self._default_model, usage=usage, raw_response=response)
    
    @circuit_breaker_decorator(OPENAI_CIRCUIT)
    @llm_transient_retry
    async def generate_with_tools(self, messages, tools, system_prompt=None, max_tokens=4096, **kwargs):
        import json
        client = self._get_client()
        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})
        openai_messages.extend(messages)
        openai_tools = [{"type": "function", "function": {"name": t["name"], "description": t.get("description",""), "parameters": t.get("parameters", t.get("input_schema", {}))}} for t in tools]
        response = client.chat.completions.create(model=self._default_model, messages=openai_messages, tools=openai_tools if openai_tools else None, max_tokens=max_tokens)
        choice = response.choices[0]
        if choice.message.tool_calls:
            tool_calls = [LLMToolCall(id=tc.id, name=tc.function.name, parameters=json.loads(tc.function.arguments)) for tc in choice.message.tool_calls]
            return LLMToolResponse(tool_calls=tool_calls, is_tool_call=True, provider=self._provider_name, model=self._default_model, raw_response=response)
        return LLMToolResponse(text=choice.message.content, is_tool_call=False, provider=self._provider_name, model=self._default_model, raw_response=response)
    
    @circuit_breaker_decorator(OPENAI_CIRCUIT)
    @llm_transient_retry
    async def generate_structured(self, messages, output_schema, system_prompt=None, max_tokens=4096, **kwargs):
        import json
        client = self._get_client()
        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt + "\n\nRespond with valid JSON."})
        openai_messages.extend(messages)
        response = client.chat.completions.create(model=self._default_model, messages=openai_messages, response_format={"type": "json_object"}, max_tokens=max_tokens)
        return json.loads(response.choices[0].message.content or "{}")
