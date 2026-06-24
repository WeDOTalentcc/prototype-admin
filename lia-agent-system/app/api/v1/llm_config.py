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
from app.shared.errors import LIAInternalError
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from lia_config.database import get_db
# F11 Phase 1 fix (2026-05-24): get_tenant_db for RLS-protected writes
from app.core.database import get_tenant_db
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.shared.tenant_llm_context import clear_tenant_config_cache, refresh_byok_active_flag
from app.domains.ai.repositories.llm_config_repository import LlmConfigRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

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

class LLMConfigRequest(WeDoBaseModel):
    primary_provider: str = "gemini"
    fallback_order: list[str] = Field(default=["gemini", "claude", "openai"])
    providers: dict[str, ProviderConfig] = Field(default={})
    routing: RoutingConfig = RoutingConfig()
    # W2-012-B (2026-05-23): LGPD Art 33 per-tenant region pinning.
    # None = usa default global do provider (us-central1 Gemini etc.).
    # Override: "us-east-1", "sa-east-1", "southamerica-east1".
    region: str | None = None

class LLMConfigResponse(BaseModel):
    company_id: str
    primary_provider: str
    fallback_order: list[str]
    providers: dict[str, Any]  # API keys masked
    routing: dict[str, str]
    is_active: bool
    # W2-012-B (2026-05-23): per-tenant region (None = global default)
    region: str | None = None

class TestProviderRequest(WeDoBaseModel):
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
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
                region=None,  # W2-012-B (2026-05-23): empty config = global default
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
            region=config.region,  # W2-012-B (2026-05-23): per-tenant region pinning
        )
    except HTTPException:
        raise
    except Exception as e:
        # REGRA 4 (CLAUDE.md): NEVER silently return fabricated config — fail-loud.
        # Previous version returned a fake "success" LLMConfigResponse with empty
        # providers, masking DB/RLS/tenant_llm_configs failures (P0.2 audit 2026-05-20).
        logger.exception(
            "[LLMConfig] Failed to fetch config for company_id=%s", company_id
        )
        raise HTTPException(
            status_code=503,
            detail={
                "error": "llm_config_unavailable",
                "message": (
                    "Não foi possível recuperar a configuração LLM. "
                    "Tente novamente em instantes ou contate o suporte se persistir."
                ),
                "fallback_used": False,
                "needs_manual_review": True,
                "internal_error_class": type(e).__name__,
            },
        ) from e


@router.put("", response_model=None)
async def update_llm_config(
    request: LLMConfigRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        await repo.upsert(
            company_id=company_id,
            primary_provider=request.primary_provider,
            fallback_order=request.fallback_order,
            providers_dict=providers_dict,
            routing=request.routing.dict(),
            created_by=str(current_user.id),
            region=request.region,  # W2-012-B (2026-05-23): LGPD Art 33 region pinning
        )

        # Audit log
        audit_repo = AuditLogRepository(db)
        _company_uuid = None
        try:
            from uuid import UUID as _UUID
            _company_uuid = _UUID(company_id) if company_id else None
        except ValueError:
            pass
        await audit_repo.create_log({
            "action": "llm_config_update",
            "action_category": "security",
            "company_id": _company_uuid,
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

        # ADR-WT-2027 Opcao C (2026-05-22): refresh denormalized byok_active
        # flag on ai_credits_balance so credit gate skip logic stays in sync.
        # Fail-safe: any error here is logged but does NOT roll back the
        # config update (gate also has live detect via byok_detector helper).
        try:
            await refresh_byok_active_flag(db, company_id, providers_dict)
        except Exception as _byok_refresh_err:
            logger.warning(
                "[LLMConfig] BYOK flag refresh failed for company=%s (non-blocking): %s",
                company_id, _byok_refresh_err,
            )

        changed_providers = list(request.providers.keys())
        logger.info(
            "[LLMConfig] Config updated by user=%s company=%s primary=%s providers=%s",
            current_user.id,
            company_id,
            request.primary_provider,
            changed_providers,
        )

        try:
            from app.repositories.audit_log_repository import AuditLogRepository
            audit_repo = AuditLogRepository(db)
            await audit_repo.create_log({
                "user_id": str(current_user.id),
                "user_email": getattr(current_user, "email", "unknown"),
                "company_id": _company_uuid,
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

        return {"status": "updated", "company_id": company_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[LLMConfig] Update error: %s", e)
        raise LIAInternalError(f"Failed to update config: {e}")


@router.post("/test", response_model=TestProviderResponse)
async def test_llm_provider(
    request: TestProviderRequest,
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
            from anthropic import AsyncAnthropic  # ADR-LLM-001-EXEMPT: BYOK validation endpoint — testa chave do usuario, nao pode usar factory  # W3-027-EXEMPT: BYOK validation endpoint — testa chave raw do usuario, nao pode usar factory
            client = AsyncAnthropic(api_key=request.api_key)
            model = request.model or "claude-sonnet-4-6"
            response = await client.messages.create(
                model=model, max_tokens=10,
                messages=[{"role": "user", "content": test_prompt}]
            )
            result = response.content[0].text

        elif request.provider == "openai":
            from openai import AsyncOpenAI  # ADR-LLM-001-EXEMPT: BYOK validation endpoint — testa chave do usuario, nao pode usar factory  # W3-027-EXEMPT: BYOK validation endpoint — testa chave raw do usuario, nao pode usar factory
            client = AsyncOpenAI(api_key=request.api_key)
            model = request.model or "gpt-4o"
            response = await client.chat.completions.create(
                model=model, max_tokens=10,
                messages=[{"role": "user", "content": test_prompt}]
            )
            result = response.choices[0].message.content

        elif request.provider == "deepseek":
            # W2-011 (2026-05-23): DeepSeek API é OpenAI-compatible — reusa SDK
            # com base_url=https://api.deepseek.com/v1
            from openai import AsyncOpenAI  # ADR-LLM-001-EXEMPT: BYOK validation endpoint — testa chave do usuario, nao pode usar factory  # W3-027-EXEMPT: BYOK validation endpoint — testa chave raw do usuario, nao pode usar factory
            client = AsyncOpenAI(
                api_key=request.api_key,
                base_url="https://api.deepseek.com/v1",
            )
            model = request.model or "deepseek-chat"
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
async def list_available_providers(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
            {
                "id": "deepseek",
                "name": "DeepSeek",
                "models": ["deepseek-chat", "deepseek-reasoner"],
                "capabilities": ["chat", "screening"],
                "default_model": "deepseek-chat",
                "opt_in_only": True,
                "data_residency": "China (no region pinning)",
            },
        ],
        "routing_types": ["chat", "embedding", "screening", "voice"],
    }
