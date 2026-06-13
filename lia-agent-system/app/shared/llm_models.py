"""Canonical LLM model identifiers used across the platform.

Task #1123 — single source of truth for the cheap Claude Haiku model used by
the wizard classifiers, fallback paths, fairness guards and other cheap-path
LLM call sites that historically duplicated the legacy/deprecated literal
``"claude-3-5-haiku-20241022"`` (anterior, mantido aqui só como referência
histórica — Task #1123).

That older legacy literal returns ``UNSUPPORTED_MODEL`` from the modelfarm proxy
at ``localhost:1106/modelfarm/anthropic`` (the canonical dev/staging
gateway). Every call that hardcoded it silently fail-OPEN'd in dev,
turning LLM-based classifiers into permanent no-ops and making the
wizard fall back to brittle keyword heuristics forever.

The canonical name is exposed here so every call site shares the same
default. Override via env var is preserved at each call site (so SRE can
pin a different version per service without changing code), but new code
MUST import ``CANONICAL_HAIKU_MODEL`` and use it as the default.

An architectural sentinel
(``tests/integration/agents/test_no_hardcoded_haiku_model_t1123.py``)
fails the build if any new file under ``app/`` hardcodes the literal
again outside this module.
"""
from __future__ import annotations

CANONICAL_HAIKU_MODEL: str = "claude-haiku-4-5-20251001"
"""Cheap path Claude Haiku model name accepted by the modelfarm proxy
(dev / staging / prod). All wizard classifiers + fallback paths default
to this constant. Override per call site via the env var documented in
the consumer module."""

CANONICAL_SONNET_MODEL: str = "claude-sonnet-4-5-20250929"
"""Mid-tier Claude Sonnet model used by handlers that need a richer
generation step than Haiku (e.g. wizard meta-question conversational
replies). Cheap path stays Haiku; Sonnet is reserved for handlers that
must produce a multi-sentence, tenant-aware reply."""
CANONICAL_GEMINI_FLASH_MODEL: str = "gemini-2.5-flash"
