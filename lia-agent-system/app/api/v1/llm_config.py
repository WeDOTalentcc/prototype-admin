"""
LLM Configuration API — Choose Your AI.

Allows tenant admins to:
- View current LLM configuration
- Add/update providers with API keys
- Configure routing (which LLM for which operation)
- Test provider connectivity
- List available providers
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from lia_config.database import get_db
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.shared.tenant_llm_context import clear_tenant_config_cache
from app.domains.ai.repositories.llm_config_repository import LlmConfigRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/llm-config", tags=["llm-config"])


# === Schemas ===

class ProviderConfig(BaseModel):
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None
    is_active: bool = True
    remove: bool = Field(False, alias="_remove")

    class Config:
        populate_by_name = True

class RoutingConfig(BaseModel):
    chat: str = "gemini"
    embedding: str = "gemini"
    screening: str = "gemini"
    voice: str = "gemini"
    fallback: str = "openai"

class LLMConfigRequest(BaseModel):
    primary_provider: str = "gemini"
    fallback_order: list[str] = Field(default=["gemini", "claude", "openai"])
    providers: dict[str, ProviderConfig] = Field(default={})
    routing: RoutingConfig = RoutingConfig()

class LLMConfigResponse(BaseModel):
    company_id: str
    primary_provider: str
    fallback_order: list[str]
    providers: dict[str, Any]  # API keys masked
    routing: dict[str, str]
    is_active: bool

class TestProviderRequest(BaseModel):
    provider: str
    api_key: str
    model: str | None = None

class TestProviderResponse(BaseModel):
    success: bool
    provider: str
    model: str
    latency_ms: float
    message: str


# === Endpoints ===

@router.get("", response_model=LLMConfigResponse)
# TODO(phase2): extract to repository — LLM config management
async def get_llm_config(
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
):
    """Get current LLM configuration for the tenant."""
    company_id = current_user.company_id

    try:
        repo = LlmConfigRepository(db)
        config = await repo.get_by_company_id(company_id)

        if not config:
            return LLMConfigResponse(
                company_id=company_id,
                primary_provider="gemini",
                fallback_order=["gemini", "claude", "openai"],
                providers={},
                routing={"chat": "gemini", "embedding": "gemini", "screening": "gemini", "voice": "gemini"},
                is_active=True,
            )

        masked_providers = {}
        for name, prov in (config.providers or {}).items():
            masked = dict(prov) if isinstance(prov, dict) else {}
            if "api_key" in masked and masked["api_key"]:
                raw = masked["api_key"]
                try:
                    decrypted = repo.decrypt_provider_key(raw)
                    if decrypted.startswith("gAAAAA"):
                        masked["api_key"] = "••••••••" + "..." + raw[-4:]
                    elif len(decrypted) > 12:
                        masked["api_key"] = decrypted[:8] + "..." + decrypted[-4:]
                    else:
                        masked["api_key"] = "••••••••"
                except Exception:
                    masked["api_key"] = "••••••••"
            masked_providers[name] = masked

        return LLMConfigResponse(
            company_id=company_id,
            primary_provider=config.primary_provider or "gemini",
            fallback_order=config.fallback_order or ["gemini", "claude", "openai"],
            providers=masked_providers,
            routing=config.routing or {},
            is_active=config.is_active,
        )
    except Exception as e:
        logger.error("[LLMConfig] Error: %s", e)
        return LLMConfigResponse(
            company_id=company_id,
            primary_provider="gemini",
            fallback_order=["gemini", "claude", "openai"],
            providers={},
            routing={},
            is_active=True,
        )


@router.put("", response_model=None)
async def update_llm_config(
    request: LLMConfigRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
):
    """Update LLM configuration for the tenant."""
    company_id = current_user.company_id

    try:
        providers_dict = {}
        for name, prov in request.providers.items():
            if prov.remove:
                providers_dict[name] = {"_remove": True}
            else:
                providers_dict[name] = {"api_key": prov.api_key, "model": prov.model, "is_active": prov.is_active}

        repo = LlmConfigRepository(db)
        await repo.upsert(
            company_id=company_id,
            primary_provider=request.primary_provider,
            fallback_order=request.fallback_order,
            providers_dict=providers_dict,
            routing=request.routing.dict(),
            created_by=str(current_user.id),
        )


        # Clear cache so next LLM call picks up new config
        clear_tenant_config_cache(company_id)

        return {"status": "updated", "company_id": company_id}
    except Exception as e:
        logger.error("[LLMConfig] Update error: %s", e)
        raise HTTPException(500, f"Failed to update config: {e}")


@router.post("/test", response_model=TestProviderResponse)
async def test_llm_provider(
    request: TestProviderRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    """Test if a provider + API key works by sending a simple prompt."""
    import time

    test_prompt = "Responda apenas: OK"
    start = time.time()

    try:
        if request.provider == "gemini":
            from google import genai
            client = genai.Client(api_key=request.api_key)
            model = request.model or "gemini-2.5-flash"
            response = client.models.generate_content(model=model, contents=test_prompt)
            result = response.text

        elif request.provider == "claude":
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=request.api_key)
            model = request.model or "claude-sonnet-4-6"
            response = await client.messages.create(
                model=model, max_tokens=10,
                messages=[{"role": "user", "content": test_prompt}]
            )
            result = response.content[0].text

        elif request.provider == "openai":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=request.api_key)
            model = request.model or "gpt-4o"
            response = await client.chat.completions.create(
                model=model, max_tokens=10,
                messages=[{"role": "user", "content": test_prompt}]
            )
            result = response.choices[0].message.content
        else:
            raise HTTPException(400, f"Unknown provider: {request.provider}")

        latency = (time.time() - start) * 1000

        return TestProviderResponse(
            success=True,
            provider=request.provider,
            model=request.model or "default",
            latency_ms=round(latency, 1),
            message=f"Provider working. Response: {result[:50]}"
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return TestProviderResponse(
            success=False,
            provider=request.provider,
            model=request.model or "default",
            latency_ms=round(latency, 1),
            message=f"Provider failed: {str(e)[:200]}"
        )


@router.get("/providers", response_model=None)
async def list_available_providers():
    """List all available LLM providers with their capabilities."""
    return {
        "providers": [
            {
                "id": "gemini",
                "name": "Google Gemini",
                "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
                "capabilities": ["chat", "embedding", "voice", "screening"],
                "default_model": "gemini-2.5-flash",
            },
            {
                "id": "claude",
                "name": "Anthropic Claude",
                "models": ["claude-sonnet-4-6", "claude-haiku-3-5"],
                "capabilities": ["chat", "screening"],
                "default_model": "claude-sonnet-4-6",
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                "capabilities": ["chat", "embedding", "screening"],
                "default_model": "gpt-4o",
            },
        ],
        "routing_types": ["chat", "embedding", "screening", "voice"],
    }
