"""
PromptLoader — centralized YAML-based prompt loading.

Moved from app/prompts/__init__.py (I3b cleanup).
YAML files remain in app/prompts/domains/ and app/prompts/shared/.

T-13 PER-TENANT WIRE canonical (ADR-028-v3):
- load(path, tenant_id=...) — tenant override tries app/prompts/tenants/{id}/{path}.yaml first
- invalidate_cache(path=None, tenant_id=None) — hot-reload after admin override edit
- Fail-soft: tenant YAML não-existente cai pra canonical (default behavior)
"""
import logging
from pathlib import Path
from typing import Any

import yaml

_logger = logging.getLogger(__name__)

# Point back to app/prompts/ where YAML files live
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"
TENANTS_DIR = PROMPTS_DIR / "tenants"


class PromptLoader:
    """Loads and caches prompts from YAML files (with per-tenant override support)."""

    # Cache structure: {(path, tenant_id_or_None): yaml_data}
    _cache: dict[tuple[str, str | None], Any] = {}

    @classmethod
    def _resolve_path(cls, path: str, tenant_id: str | None) -> Path:
        """T-13: resolve path with tenant override priority.

        Order:
        1. If tenant_id provided, try tenants/{tenant_id}/{path}.yaml
        2. Fall back to canonical {path}.yaml
        """
        if tenant_id:
            tenant_path = TENANTS_DIR / tenant_id / f"{path}.yaml"
            if tenant_path.exists():
                _logger.info(
                    "[PromptLoader T-13] tenant override applied path=%s tenant=%s",
                    path, tenant_id,
                )
                return tenant_path
        return PROMPTS_DIR / f"{path}.yaml"

    @classmethod
    def load(cls, path: str, tenant_id: str | None = None) -> dict[str, Any]:
        """Load a YAML prompt file. Path relative to prompts/ dir.

        Example:
            PromptLoader.load("domains/sourcing")
            PromptLoader.load("domains/sourcing", tenant_id="acme-corp")

        T-13: tenant_id parameter is OPTIONAL — backward compat preserved.
        Cache key includes tenant_id to avoid cross-tenant pollution.
        """
        cache_key = (path, tenant_id)
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        file_path = cls._resolve_path(path, tenant_id)
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        cls._cache[cache_key] = data
        _logger.info(
            "Loaded prompt: %s%s",
            path,
            f" (tenant={tenant_id})" if tenant_id else "",
        )
        return data

    @classmethod
    def invalidate_cache(
        cls, path: str | None = None, tenant_id: str | None = None
    ) -> int:
        """T-13: hot-reload cache invalidation.

        Modes:
        - invalidate_cache() — clears entire cache
        - invalidate_cache(path="domains/sourcing") — clears all tenant variants
          of that path
        - invalidate_cache(tenant_id="acme-corp") — clears all paths for tenant
        - invalidate_cache(path="...", tenant_id="...") — clears specific entry

        Returns: number of entries invalidated.
        """
        if path is None and tenant_id is None:
            count = len(cls._cache)
            cls._cache.clear()
            _logger.info("[PromptLoader T-13] cache fully invalidated (%d entries)", count)
            return count

        to_remove = []
        for cache_key in cls._cache:
            p, t = cache_key
            if path is not None and p != path:
                continue
            if tenant_id is not None and t != tenant_id:
                continue
            to_remove.append(cache_key)

        for cache_key in to_remove:
            del cls._cache[cache_key]

        _logger.info(
            "[PromptLoader T-13] invalidated %d entries (path=%s tenant=%s)",
            len(to_remove), path, tenant_id,
        )
        return len(to_remove)

    @classmethod
    def get_domain_prompt(
        cls, domain_id: str, tenant_id: str | None = None
    ) -> str:
        """Get system prompt for a specific domain, composed with persona base.

        T-13: tenant_id parameter optional — backward compat preserved.
        """
        data = cls.load(f"domains/{domain_id}", tenant_id=tenant_id)
        domain_specific = data.get("system_prompt", "")
        try:
            from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

            return SystemPromptBuilder.build(
                agent_type=domain_id,
                extra_instructions=domain_specific,
            )
        except Exception:
            return domain_specific

    @classmethod
    def get_shared_prompt(
        cls, name: str, key: str | None = None, tenant_id: str | None = None
    ) -> str:
        """Get a shared prompt by name, optionally a specific key.

        T-13: tenant_id parameter optional — backward compat preserved.
        """
        data = cls.load(f"shared/{name}", tenant_id=tenant_id)
        if key:
            return data.get(key, "")
        return data.get("system_prompt", "") if isinstance(data, dict) else ""
