"""
Sensor: rail_a_hint_override.try_hint_route — Tier -1 routing.

Cobre o fallback top-level (defesa em profundidade) introduzido após o audit
de wizard-domain-hint-leak (2026-04-29). Antes: try_hint_route só lia de
``context["metadata"]``; agora aceita também hint em top-level
``context.{source, domain_hint, intent_hint}``.

Guards:
  1. context.metadata canônico → hit (formato preservado).
  2. context top-level (fallback) → hit (defesa em profundidade).
  3. source != "rail_a" → None (anti-injection mantido em ambos os formatos).
  4. domain_hint não-registrado → None (allowlist mantida em ambos os formatos).
  5. metadata canônico tem precedência se ambos presentes.
  6. context vazio / None → None.
  7. confidence == HINT_CONFIDENCE (0.99) e source == OVERRIDE_SOURCE.

Fix se falhar:
  Verificar ``app/orchestrator/services/rail_a_hint_override.py::try_hint_route``
  — função deve tentar ``context["metadata"]`` primeiro, depois construir hint
  virtual a partir de ``context.{source, domain_hint, intent_hint}`` e validar
  via ``get_hint_domain``. Allowlist por ``DomainRegistry`` deve ser
  preservada em ambos os caminhos.

Skill canônica: harness-engineering [sensor computacional].
"""
from unittest.mock import MagicMock, patch

import pytest

from app.orchestrator.services.rail_a_hint_override import (
    HINT_CONFIDENCE,
    OVERRIDE_SOURCE,
    TRUSTED_SOURCE,
    try_hint_route,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patched_registry(registered_domains: list[str]):
    """Patch DomainRegistry.list_domains() to return a fixed allowlist."""
    mock_registry = MagicMock()
    mock_registry.list_domains.return_value = registered_domains
    return patch(
        "app.domains.registry.DomainRegistry",
        return_value=mock_registry,
    )


# ---------------------------------------------------------------------------
# Guard 1: context.metadata canônico
# ---------------------------------------------------------------------------


def test_metadata_canonical_hit():
    """context['metadata'] with valid source + domain_hint → RouteResult."""
    with _patched_registry(["wizard", "sourcing"]):
        result = try_hint_route(
            {
                "metadata": {
                    "source": TRUSTED_SOURCE,
                    "domain_hint": "wizard",
                    "intent_hint": "create_job",
                }
            }
        )
    assert result is not None
    assert result.domain_id == "wizard"
    assert result.confidence == HINT_CONFIDENCE
    assert result.source == OVERRIDE_SOURCE
    assert (result.intent_details or {}).get("raw_intent") == "create_job"


# ---------------------------------------------------------------------------
# Guard 2: context top-level fallback (defesa em profundidade)
# ---------------------------------------------------------------------------


def test_top_level_fallback_hit():
    """context.{source, domain_hint} top-level → RouteResult (fallback path)."""
    with _patched_registry(["wizard"]):
        result = try_hint_route(
            {
                "source": TRUSTED_SOURCE,
                "domain_hint": "wizard",
                "intent_hint": "create_job",
            }
        )
    assert result is not None
    assert result.domain_id == "wizard"
    assert result.confidence == HINT_CONFIDENCE
    assert result.source == OVERRIDE_SOURCE


def test_top_level_fallback_without_intent_hint():
    """Top-level without intent_hint still hits with raw_intent=domain_id."""
    with _patched_registry(["wizard"]):
        result = try_hint_route(
            {"source": TRUSTED_SOURCE, "domain_hint": "wizard"}
        )
    assert result is not None
    assert (result.intent_details or {}).get("raw_intent") == "wizard"


# ---------------------------------------------------------------------------
# Guard 3: anti-injection enforced in BOTH formats
# ---------------------------------------------------------------------------


def test_canonical_rejects_untrusted_source():
    """metadata.source != 'rail_a' → None (anti-injection canonical)."""
    with _patched_registry(["wizard"]):
        result = try_hint_route(
            {"metadata": {"source": "evil_actor", "domain_hint": "wizard"}}
        )
    assert result is None


def test_top_level_rejects_untrusted_source():
    """top-level source != 'rail_a' → None (anti-injection fallback)."""
    with _patched_registry(["wizard"]):
        result = try_hint_route(
            {"source": "evil_actor", "domain_hint": "wizard"}
        )
    assert result is None


def test_top_level_without_source_returns_none():
    """top-level without source → None (defense — only with explicit trusted source)."""
    with _patched_registry(["wizard"]):
        result = try_hint_route({"domain_hint": "wizard"})
    assert result is None


# ---------------------------------------------------------------------------
# Guard 4: allowlist enforced in BOTH formats
# ---------------------------------------------------------------------------


def test_canonical_rejects_unregistered_domain():
    """metadata.domain_hint not in DomainRegistry → None."""
    with _patched_registry(["wizard"]):
        result = try_hint_route(
            {"metadata": {"source": TRUSTED_SOURCE, "domain_hint": "ghost_domain"}}
        )
    assert result is None


def test_top_level_rejects_unregistered_domain():
    """top-level domain_hint not in DomainRegistry → None."""
    with _patched_registry(["wizard"]):
        result = try_hint_route(
            {"source": TRUSTED_SOURCE, "domain_hint": "ghost_domain"}
        )
    assert result is None


# ---------------------------------------------------------------------------
# Guard 5: canonical metadata wins when both present
# ---------------------------------------------------------------------------


def test_metadata_takes_precedence_over_top_level():
    """If both formats present, canonical metadata wins (deterministic)."""
    with _patched_registry(["wizard", "sourcing"]):
        result = try_hint_route(
            {
                "metadata": {"source": TRUSTED_SOURCE, "domain_hint": "wizard"},
                # Top-level points to a different domain — must be ignored.
                "source": TRUSTED_SOURCE,
                "domain_hint": "sourcing",
            }
        )
    assert result is not None
    assert result.domain_id == "wizard"  # canonical won


# ---------------------------------------------------------------------------
# Guard 6: empty / None inputs
# ---------------------------------------------------------------------------


def test_none_context_returns_none():
    assert try_hint_route(None) is None


def test_empty_context_returns_none():
    assert try_hint_route({}) is None


def test_context_with_only_unrelated_keys_returns_none():
    """Context without source/domain_hint/metadata → None (no signal, no work)."""
    with _patched_registry(["wizard"]):
        result = try_hint_route({"company_id": "c1", "user_id": "u1"})
    assert result is None
