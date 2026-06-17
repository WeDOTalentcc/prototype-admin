"""Tests for `lia_right_panel_form_received_total` counter (PR-13 / F-100).

Decisão Paulo Opção C (2026-05-26): adicionar telemetria 48h antes de
decidir entre Opção A (implementar UI) ou B (remover backend órfão).

Cenários cobertos:
  1. Counter está registrado em `prometheus_client.REGISTRY`.
  2. Chamada com `right_panel_form` populado incrementa label populated=true.
  3. Chamada com dict vazio / None incrementa label populated=false.
  4. Logger INFO emite linha canary com nome canonical "[right_panel_form]".

Os testes mockam `_get_llm` para evitar chamada real ao provider (segue
o padrão dos testes em `tests/unit/test_intake_extractor.py`).
"""

from __future__ import annotations

import logging

import pytest

from app.domains.job_creation.services.intake_extractor import (
    IntakeExtractor,
    lia_right_panel_form_received_total,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read_counter_value(populated: str, stage: str = "intake") -> float:
    """Read current value of the counter for a given label combo.

    Returns 0.0 when the label combination has not been observed yet.
    """
    assert lia_right_panel_form_received_total is not None, (
        "Counter must be importable — prometheus_client missing?"
    )
    # Each labels() call creates the child if absent; reading _value.get()
    # exposes the current sample without side effects on the counter logic.
    child = lia_right_panel_form_received_total.labels(
        populated=populated, stage=stage
    )
    return float(child._value.get())  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_counter_registered_in_prometheus_registry():
    """Counter `lia_right_panel_form_received_total` is registered."""
    from prometheus_client import REGISTRY

    metric_names = {c.name for c in REGISTRY.collect()}
    # prometheus_client strips the `_total` suffix from Counter.name in
    # collect() output (it's restored in /metrics export). Accept either.
    assert (
        "lia_right_panel_form_received_total" in metric_names
        or "lia_right_panel_form_received" in metric_names
    ), (
        "Counter must be registered for /metrics scraping. "
        "If absent, prometheus_client import path or REGISTRY race likely broken."
    )


def test_counter_increments_with_populated_panel(monkeypatch):
    """right_panel_form com fields → counter labels(populated=true) +1."""
    extractor = IntakeExtractor(llm_client=None)
    monkeypatch.setattr(extractor, "_get_llm", lambda: None)

    before = _read_counter_value("true")
    extractor.extract_from_sources(
        user_text="",
        right_panel_form={"title": "Eng. de Dados", "seniority": "senior"},
    )
    after = _read_counter_value("true")
    assert after == before + 1.0, (
        f"populated=true counter should increment by 1 "
        f"(before={before} after={after})"
    )


def test_counter_increments_with_empty_panel(monkeypatch):
    """right_panel_form vazio → counter labels(populated=false) +1."""
    extractor = IntakeExtractor(llm_client=None)
    monkeypatch.setattr(extractor, "_get_llm", lambda: None)

    before = _read_counter_value("false")
    extractor.extract_from_sources(
        user_text="",
        right_panel_form={},
    )
    after = _read_counter_value("false")
    assert after == before + 1.0


def test_counter_increments_with_none_panel(monkeypatch):
    """right_panel_form=None → counter labels(populated=false) +1."""
    extractor = IntakeExtractor(llm_client=None)
    monkeypatch.setattr(extractor, "_get_llm", lambda: None)

    before = _read_counter_value("false")
    extractor.extract_from_sources(
        user_text="Vaga de eng",
        right_panel_form=None,
    )
    after = _read_counter_value("false")
    assert after == before + 1.0


def test_counter_treats_dict_with_only_empty_values_as_unpopulated(monkeypatch):
    """{"title": "", "seniority": None} → populated=false (todos vazios)."""
    extractor = IntakeExtractor(llm_client=None)
    monkeypatch.setattr(extractor, "_get_llm", lambda: None)

    before = _read_counter_value("false")
    extractor.extract_from_sources(
        user_text="",
        right_panel_form={"title": "", "seniority": None, "skills": []},
    )
    after = _read_counter_value("false")
    assert after == before + 1.0, (
        "Dict with only empty-equivalent values must classify as populated=false"
    )


def test_canary_log_emitted_with_right_panel_marker(monkeypatch, caplog):
    """Logger INFO emite linha começando com '[right_panel_form]'."""
    extractor = IntakeExtractor(llm_client=None)
    monkeypatch.setattr(extractor, "_get_llm", lambda: None)

    with caplog.at_level(
        logging.INFO,
        logger="app.domains.job_creation.services.intake_extractor",
    ):
        extractor.extract_from_sources(
            user_text="",
            right_panel_form={"title": "QA"},
        )

    matching = [r for r in caplog.records if "[right_panel_form]" in r.getMessage()]
    assert matching, (
        "Canary log line '[right_panel_form] received populated=...' must be "
        "emitted on every call (canary during 48h telemetry window)."
    )
    msg = matching[-1].getMessage()
    assert "populated=True" in msg or "populated=true" in msg.lower(), (
        f"Canary log should expose populated boolean, got: {msg!r}"
    )
