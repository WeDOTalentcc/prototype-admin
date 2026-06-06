"""Gemini LLM Provider implementation."""
import logging
import os

from tenacity import retry, retry_if_result, stop_after_attempt, wait_exponential

from app.shared.providers.llm_provider import LLMProviderABC, LLMResponse, LLMToolCall, LLMToolResponse
from app.shared.resilience.circuit_breaker import GEMINI_CIRCUIT, circuit_breaker_decorator
from app.shared.providers.llm_retry import llm_transient_retry

logger = logging.getLogger(__name__)


def _is_empty_response(result):
    if isinstance(result, LLMResponse):
        return not result.text
    return False


class GeminiLLMProvider(LLMProviderABC):
    """Google Gemini LLM provider implementation."""
    
    _provider_name = "gemini"
    _default_model = "gemini-2.5-flash"
    
    def __init__(self, api_key: str | None = None, region: str | None = None):
        self._client = None
        self._custom_api_key = api_key
        # W2-012 (2026-05-22): LGPD Art 33 per-tenant region pinning.
        # Default canonical us-central1 (audit recommendation).
        # Override via env LIA_GEMINI_DEFAULT_REGION.
        import os as _os_w2012
        self._region = region or _os_w2012.environ.get(
            "LIA_GEMINI_DEFAULT_REGION", "us-central1"
        )
    
    @property
    def provider_name(self) -> str:
        return self._provider_name
    
    @property
    def default_model(self) -> str:
        return self._default_model
    
    def _get_client(self):
        if not self._client:
            from google import genai
            api_key = self._custom_api_key or os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
            base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
            if not api_key:
                raise ValueError("Gemini API not configured")
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["http_options"] = {'api_version': '', 'base_url': base_url}
            self._client = genai.Client(**client_kwargs)
        return self._client
    
    @circuit_breaker_decorator(GEMINI_CIRCUIT)
    @llm_transient_retry
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, max=3), retry=retry_if_result(_is_empty_response))
    async def generate(self, prompt, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        client = self._get_client()
        response = client.models.generate_content(model=model or self._default_model, contents=prompt)
        text = response.text or ""
        if not text:
            logger.warning("Gemini returned empty response for generate(). Retrying...")
        return LLMResponse(text=text, provider=self._provider_name, model=model or self._default_model, raw_response=response)
    
    @circuit_breaker_decorator(GEMINI_CIRCUIT)
    @llm_transient_retry
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, max=3), retry=retry_if_result(_is_empty_response))
    async def generate_with_system(self, system_prompt, user_message, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        from google.genai import types
        client = self._get_client()
        config = types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=max_tokens, temperature=temperature)
        contents = [types.Content(role="user", parts=[types.Part(text=user_message)])]
        response = client.models.generate_content(model=model or self._default_model, contents=contents, config=config)
        text = response.text or ""
        if not text:
            logger.warning("Gemini returned empty response for generate_with_system(). Retrying...")
        return LLMResponse(text=text, provider=self._provider_name, model=model or self._default_model, raw_response=response)
    
    @circuit_breaker_decorator(GEMINI_CIRCUIT)
    @llm_transient_retry
    async def generate_with_tools(self, messages, tools, system_prompt=None, max_tokens=4096, **kwargs):
        from google.genai import types
        client = self._get_client()
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                contents.append(types.Content(role="user", parts=[types.Part(text=str(content))]))
            elif role in ("assistant", "model"):
                parts = []
                if content:
                    parts.append(types.Part(text=str(content)))
                if msg.get("function_call"):
                    fc = msg["function_call"]
                    parts.append(types.Part.from_function_call(name=fc.get("name", ""), args=fc.get("args", {})))
                if parts:
                    contents.append(types.Content(role="model", parts=parts))
            elif role == "function_response":
                fr = types.Part.from_function_response(name=msg.get("name", ""), response=msg.get("response", {}))
                contents.append(types.Content(role="user", parts=[fr]))
        
        function_declarations = [types.FunctionDeclaration(name=t.get("name",""), description=t.get("description",""), parameters=t.get("parameters", t.get("input_schema", {}))) for t in tools]
        gemini_tools = [types.Tool(function_declarations=function_declarations)] if function_declarations else None
        config = types.GenerateContentConfig(system_instruction=system_prompt, tools=gemini_tools, max_output_tokens=max_tokens)
        response = client.models.generate_content(model=self._default_model, contents=contents, config=config)
        
        tool_calls = []
        text_parts = []
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    tool_calls.append(LLMToolCall(id=f"gemini_{fc.name}_{len(tool_calls)}", name=fc.name, parameters=dict(fc.args) if fc.args else {}))
                elif hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
        
        return LLMToolResponse(text="".join(text_parts) if text_parts else None, tool_calls=tool_calls, is_tool_call=bool(tool_calls),
                              provider=self._provider_name, model=self._default_model, raw_response=response)
    
    @circuit_breaker_decorator(GEMINI_CIRCUIT)
    @llm_transient_retry
    async def generate_structured(self, messages, output_schema, system_prompt=None, max_tokens=4096, **kwargs):
        import json

        from google.genai import types
        client = self._get_client()
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                contents.append(types.Content(role="user", parts=[types.Part(text=str(content))]))
            elif role in ("assistant", "model") and content:
                contents.append(types.Content(role="model", parts=[types.Part(text=str(content))]))
        enhanced_system = (system_prompt or "") + "\n\nRespond with valid JSON matching the schema."
        config = types.GenerateContentConfig(system_instruction=enhanced_system.strip(), response_mime_type="application/json", response_schema=output_schema, max_output_tokens=max_tokens)
        response = client.models.generate_content(model=self._default_model, contents=contents, config=config)
        text = response.text or "{}"
        return json.loads(text)
