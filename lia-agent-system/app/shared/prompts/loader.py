"""
PromptLoader — centralized YAML-based prompt loading.

Moved from app/prompts/__init__.py (I3b cleanup).
YAML files remain in app/prompts/domains/ and app/prompts/shared/.
"""
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

_logger = logging.getLogger(__name__)

# Point back to app/prompts/ where YAML files live
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


class PromptLoader:
    """Loads and caches prompts from YAML files."""

    _cache: Dict[str, Any] = {}

    @classmethod
    def load(cls, path: str) -> Dict[str, Any]:
        """Load a YAML prompt file. Path relative to prompts/ dir.
        Example: PromptLoader.load("domains/sourcing")
        """
        if path in cls._cache:
            return cls._cache[path]

        file_path = PROMPTS_DIR / f"{path}.yaml"
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        cls._cache[path] = data
        _logger.info(f"Loaded prompt: {path}")
        return data

    @classmethod
    def get_domain_prompt(cls, domain_id: str) -> str:
        """Get system prompt for a specific domain."""
        data = cls.load(f"domains/{domain_id}")
        return data.get("system_prompt", "")

    @classmethod
    def get_shared_prompt(cls, name: str, key: Optional[str] = None) -> str:
        """Get a shared prompt by name, optionally a specific key."""
        data = cls.load(f"shared/{name}")
        if key:
            return data.get("prompts", {}).get(key, "")
        return data.get("system_prompt", "")

    @classmethod
    def clear_cache(cls):
        """Clear the prompt cache."""
        cls._cache.clear()
