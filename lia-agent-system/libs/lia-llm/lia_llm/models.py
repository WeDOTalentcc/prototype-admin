"""Canonical LLM model identifiers — single source of truth.

Extraído de app/shared/llm_models.py para libs/lia-llm.
O módulo original é mantido como shim de retrocompatibilidade.

Task #1123 — elimina literal duplicado "claude-3-5-haiku-20241022" (deprecated).
O nome canônico é CANONICAL_HAIKU_MODEL; importar SEMPRE via este módulo.
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
"""Google Gemini Flash — used by voice (Twilio + Gemini Live) and
other low-latency multimodal paths."""
