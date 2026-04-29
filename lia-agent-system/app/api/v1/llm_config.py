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
import re
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
from app.domains.admin.repositories.audit_log_repository import AuditLogRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/llm-config", tags=["llm-config"])


# === Schemas ===

class ProviderConfig(BaseModel):
    provider: str = ""
    api_key: str = ""
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
                key = masked["api_key"]
                if len(key) > 12:
                    masked["api_key"] = key[:8] + "..." + key[-4:]
                else:
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
    """Update LLM configuration for the tenant.
    Uses merge semantics: only keys with real (non-masked) values are updated.
    If a provider's api_key contains '...' it is treated as masked and the
    existing encrypted key is preserved."""
    company_id = current_user.company_id

    try:
        repo = LlmConfigRepository(db)

        existing = await repo.get_by_company_id(company_id)
        existing_providers = existing.providers if existing else {}

        providers_dict = dict(existing_providers)
        changed_providers = []

        for name, prov in request.providers.items():
            if prov.remove:
                providers_dict[name] = {"_remove": True}
                changed_providers.append(name)
                continue

            key_val = prov.api_key
            is_masked = "..." in key_val if key_val else True
            is_empty = not key_val

            if (is_masked or is_empty) and name in existing_providers:
                providers_dict[name] = {
                    **existing_providers[name],
                    "model": prov.model or existing_providers[name].get("model"),
                    "is_active": prov.is_active,
                }
            else:
                providers_dict[name] = {
                    "api_key": key_val,
                    "model": prov.model,
                    "is_active": prov.is_active,
                }
            changed_providers.append(name)

        # B7: Quality Tier Guard — warn if tenant selects Tier 2 for critical tasks
        _QUALITY_TIERS = {
            "claude-sonnet-4-6": "tier1", "claude-opus-4-7": "tier1",
            "gemini-2.5-pro": "tier1", "gemini-2.5-flash": "tier1",
            "gpt-4o": "tier1", "gpt-4-turbo": "tier1",
            "claude-haiku-3-5": "tier2", "gemini-2.0-flash": "tier2",
            "gpt-4o-mini": "tier2",
        }
        _CRITICAL_ROUTING_KEYS = {"screening", "wsi"}
        quality_warnings: list[str] = []
        routing_dict = request.routing.dict()
        for route_key in _CRITICAL_ROUTING_KEYS:
            route_provider = routing_dict.get(route_key, "")
            if route_provider and route_provider in request.providers:
                prov_model = request.providers[route_provider].model or ""
                if _QUALITY_TIERS.get(prov_model) == "tier2":
                    quality_warnings.append(
                        f"Modelo '{prov_model}' (Tier 2) configurado para '{route_key}' — "
                        f"qualidade da triagem WSI pode ser reduzida. "
                        f"Recomendamos Tier 1 (ex: claude-sonnet-4-6, gpt-4o, gemini-2.5-flash)."
                    )

        await repo.upsert(
            company_id=company_id,
            primary_provider=request.primary_provider,
            fallback_order=request.fallback_order,
            providers_dict=providers_dict,
            routing=request.routing.dict(),
            created_by=str(current_user.id),
        )

        # Audit log
        audit_repo = AuditLogRepository(db)
        await audit_repo.create_log({
            "action": "llm_config_update",
            "action_category": "security",
            "client_id": company_id,
            "user_id": str(current_user.id),
            "user_email": current_user.email,
            "resource_type": "llm_config",
            "resource_id": company_id,
            "status": "success",
            "evidence": {
                "primary": request.primary_provider,
                "changed_providers": changed_providers
            }
        })

        clear_tenant_config_cache(company_id)

        changed_providers = list(request.providers.keys())
        logger.info(
            "[LLMConfig] Config updated by user=%s company=%s primary=%s providers=%s",
            current_user.id,
            company_id,
            request.primary_provider,
            changed_providers,
        )

        try:
            audit_repo = AuditLogRepository(db)
            await audit_repo.create_log({
                "user_id": str(current_user.id),
                "user_email": getattr(current_user, "email", "unknown"),
                "client_id": company_id,
                "client_name": getattr(current_user, "company_name", company_id),
                "action": "llm_config.update",
                "action_category": "configuration",
                "resource_type": "tenant_llm_config",
                "resource_id": company_id,
                "status": "success",
                "details": {
                    "primary_provider": request.primary_provider,
                    "changed_providers": changed_providers,
                    "fallback_order": request.fallback_order,
                },
            })
        except Exception as audit_err:
            logger.warning("[LLMConfig] Audit log write failed (non-blocking): %s", audit_err)

        response_body: dict = {"status": "updated", "company_id": company_id}
        if quality_warnings:
            response_body["warnings"] = quality_warnings
            logger.warning(
                "[LIA-QUALITY] tenant=%s quality warnings on config save: %s",
                company_id, quality_warnings,
            )
        return response_body
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
            message="Provider failed: " + re.sub(
                r"(sk-|AIza|sk-ant-)[A-Za-z0-9_\-]{8,}",
                "***REDACTED***",
                str(e)[:200],
            )
        )


@router.get("/providers", response_model=None)
async def list_available_providers():
    """List all available LLM providers with their capabilities."""
    # B8: dependency map — tells the frontend which providers need companions
    # and which model tiers are available.
    return {
        "providers": [
            {
                "id": "gemini",
                "name": "Google Gemini",
                "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
                "model_tiers": {
                    "gemini-2.5-flash": "tier1",
                    "gemini-2.5-pro":   "tier1",
                    "gemini-2.0-flash": "tier2",
                },
                "capabilities": ["chat", "embedding", "voice", "screening"],
                "requires_companion_for": [],
                "default_model": "gemini-2.5-flash",
            },
            {
                "id": "claude",
                "name": "Anthropic Claude",
                "models": ["claude-sonnet-4-6", "claude-opus-4-7", "claude-haiku-3-5"],
                "model_tiers": {
                    "claude-sonnet-4-6": "tier1",
                    "claude-opus-4-7":   "tier1",
                    "claude-haiku-3-5":  "tier2",
                },
                "capabilities": ["chat", "screening"],
                "requires_companion_for": ["embedding", "voice"],
                "companion_recommendation": (
                    "Claude não suporta embedding nem voz nativas. "
                    "Configure Gemini ou OpenAI como provider secundário para essas funcionalidades."
                ),
                "default_model": "claude-sonnet-4-6",
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                "model_tiers": {
                    "gpt-4o":      "tier1",
                    "gpt-4-turbo": "tier1",
                    "gpt-4o-mini": "tier2",
                },
                "capabilities": ["chat", "embedding", "screening"],
                "requires_companion_for": ["voice"],
                "companion_recommendation": (
                    "OpenAI Realtime API suporta voz, mas requer configuração separada. "
                    "Para voz nativa, considere Gemini como provider de voz."
                ),
                "default_model": "gpt-4o",
            },
        ],
        "routing_types": ["chat", "embedding", "screening", "voice"],
        "tier_definitions": {
            "tier1": "Raciocínio complexo — adequado para WSI/Bloom/Dreyfus e triagem avançada.",
            "tier2": "Optimizado para velocidade/custo — não recomendado para tarefas críticas de triagem.",
        },
    }
