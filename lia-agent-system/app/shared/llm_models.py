"""Canonical LLM model identifiers used across the platform.

EXTRACTED TO: libs/lia-llm/lia_llm/models.py
Este arquivo é shim de retrocompatibilidade — remover quando todos os consumers migrarem.

Task #1123 — single source of truth for canonical model names.
Sentinel: tests/integration/agents/test_no_hardcoded_haiku_model_t1123.py
"""
# ruff: noqa: F401, F403
from lia_llm.models import *  # noqa: F401, F403
from lia_llm.models import (  # noqa: F401 — re-export explícito para IDEs e type checkers
    CANONICAL_GEMINI_FLASH_MODEL,
    CANONICAL_HAIKU_MODEL,
    CANONICAL_SONNET_MODEL,
)
