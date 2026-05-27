"""Tests for trigger_types_canonical — Sprint Z.4 + Z.7 sensor smoke.

Covers:
- TriggerType enum well-formed (all str values, snake_case)
- TRIGGER_TYPE_CATALOG 1:1 with enum
- get_trigger_metadata: fail-CLOSED on unknown
- list_all_triggers immutable view
- to_api_response shape canonical
- Categories canonical (CANONICAL_CATEGORIES enforcement)
- Labels non-empty PT-BR + EN
- Param schemas well-formed for triggers that declare params
- Sensor passes (no drift beyond DEPRECATED_ALLOWLIST)
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from app.shared.automation.trigger_types_canonical import (
    CANONICAL_CATEGORIES,
    TRIGGER_TYPE_CATALOG,
    ParamDef,
    TriggerMetadata,
    TriggerType,
    get_trigger_metadata,
    list_all_triggers,
    to_api_response,
)


# ─────────────────────────────────────────────────────────────────────────────
# Enum sanity
# ─────────────────────────────────────────────────────────────────────────────


def test_trigger_type_is_string_enum() -> None:
    for tt in TriggerType:
        assert isinstance(tt.value, str), f"{tt.name} value must be str"


def test_trigger_type_values_snake_case() -> None:
    pattern = re.compile(r"^[a-z][a-z0-9_]*$")
    for tt in TriggerType:
        assert pattern.match(tt.value), f"{tt.name}={tt.value!r} must be snake_case"


def test_trigger_type_values_unique() -> None:
    values = [tt.value for tt in TriggerType]
    assert len(values) == len(set(values)), "TriggerType values must be unique"


def test_trigger_type_has_minimum_coverage() -> None:
    """Sanity: canonical deve cobrir os 4 enums pre-Z.4 (>= 17 values)."""
    assert len(list(TriggerType)) >= 17, (
        f"Expected >= 17 trigger types (union of 4 pre-Z.4 enums), got {len(list(TriggerType))}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Catalog 1:1 with enum
# ─────────────────────────────────────────────────────────────────────────────


def test_catalog_covers_every_enum_value() -> None:
    catalog_values = {meta.value for meta in TRIGGER_TYPE_CATALOG}
    enum_values = set(TriggerType)
    missing = enum_values - catalog_values
    assert not missing, f"Enum values missing from catalog: {missing}"


def test_catalog_has_no_duplicate_entries() -> None:
    values = [meta.value for meta in TRIGGER_TYPE_CATALOG]
    assert len(values) == len(set(values)), "Catalog entries must be unique"


def test_catalog_count_matches_enum_count() -> None:
    assert len(TRIGGER_TYPE_CATALOG) == len(list(TriggerType))


# ─────────────────────────────────────────────────────────────────────────────
# Labels & categories
# ─────────────────────────────────────────────────────────────────────────────


def test_every_trigger_has_non_empty_labels() -> None:
    for meta in TRIGGER_TYPE_CATALOG:
        assert meta.label_pt.strip(), f"{meta.value} missing label_pt"
        assert meta.label_en.strip(), f"{meta.value} missing label_en"


def test_every_trigger_has_description() -> None:
    for meta in TRIGGER_TYPE_CATALOG:
        assert meta.description.strip(), f"{meta.value} missing description"


def test_every_category_is_canonical() -> None:
    for meta in TRIGGER_TYPE_CATALOG:
        assert meta.category in CANONICAL_CATEGORIES, (
            f"{meta.value} has non-canonical category {meta.category!r}; "
            f"allowed: {sorted(CANONICAL_CATEGORIES)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def test_get_trigger_metadata_by_string() -> None:
    meta = get_trigger_metadata("candidate_applied")
    assert meta is not None
    assert meta.value == TriggerType.CANDIDATE_APPLIED


def test_get_trigger_metadata_by_enum() -> None:
    meta = get_trigger_metadata(TriggerType.OFFER_SENT)
    assert meta is not None
    assert meta.value == TriggerType.OFFER_SENT


def test_get_trigger_metadata_unknown_returns_none_fail_closed() -> None:
    assert get_trigger_metadata("does_not_exist") is None
    assert get_trigger_metadata("") is None


def test_list_all_triggers_returns_defensive_copy() -> None:
    triggers = list_all_triggers()
    assert isinstance(triggers, list)
    assert len(triggers) == len(TRIGGER_TYPE_CATALOG)
    # Mutating returned list must not affect canonical
    triggers.clear()
    assert len(list_all_triggers()) == len(TRIGGER_TYPE_CATALOG)


# ─────────────────────────────────────────────────────────────────────────────
# API response shape
# ─────────────────────────────────────────────────────────────────────────────


def test_to_api_response_shape() -> None:
    response = to_api_response()
    assert isinstance(response, list)
    assert len(response) == len(TRIGGER_TYPE_CATALOG)
    required_keys = {"value", "name", "label_pt", "label_en", "description", "category", "params"}
    for entry in response:
        assert required_keys.issubset(entry.keys()), (
            f"Missing keys in entry: {required_keys - entry.keys()}"
        )
        assert entry["name"] == entry["label_pt"], "name must mirror label_pt for backward compat"
        assert isinstance(entry["params"], list)


def test_to_api_response_preserves_backward_compat_values() -> None:
    """API response inclui values legacy: candidate_stage_changed, offer_sent etc."""
    values = {e["value"] for e in to_api_response()}
    legacy_required = {
        "candidate_applied",
        "candidate_stage_changed",
        "interview_scheduled",
        "offer_sent",
        "screening_completed",
        "no_response_48h",
        "candidate_rejected",
        "candidate_hired",
        "feedback_received",
        "deadline_approaching",
    }
    missing = legacy_required - values
    assert not missing, f"Backward-compat values missing from API: {missing}"


# ─────────────────────────────────────────────────────────────────────────────
# Param schemas
# ─────────────────────────────────────────────────────────────────────────────


def test_stage_changed_has_stage_id_param() -> None:
    meta = get_trigger_metadata(TriggerType.CANDIDATE_STAGE_CHANGED)
    assert meta is not None
    param_names = {p.name for p in meta.params}
    assert "stage_id" in param_names
    stage_param = next(p for p in meta.params if p.name == "stage_id")
    assert stage_param.type == "stage_id"


def test_params_have_canonical_types() -> None:
    allowed_types = {"string", "number", "select", "stage_id"}
    for meta in TRIGGER_TYPE_CATALOG:
        for p in meta.params:
            assert p.type in allowed_types, (
                f"{meta.value} param {p.name!r} has invalid type {p.type!r}"
            )


def test_select_params_have_options() -> None:
    for meta in TRIGGER_TYPE_CATALOG:
        for p in meta.params:
            if p.type == "select":
                assert p.options is not None, (
                    f"{meta.value} param {p.name} type=select must declare options"
                )


# ─────────────────────────────────────────────────────────────────────────────
# Sensor smoke test
# ─────────────────────────────────────────────────────────────────────────────


def test_sensor_script_runs() -> None:
    """Sensor scripts/check_trigger_types_canonical.py é executavel e retorna exit code 0 ou 1."""
    repo_root = Path(__file__).resolve().parents[3]
    sensor = repo_root / "scripts" / "check_trigger_types_canonical.py"
    assert sensor.exists(), f"Sensor not found at {sensor}"
    result = subprocess.run(
        [sys.executable, str(sensor)],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )
    assert result.returncode in (0, 1), (
        f"Sensor returned unexpected code {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_sensor_passes_with_deprecated_allowlist() -> None:
    """Default (sem --strict): sensor passa porque allowlist Z.5/Z.6 esta documentada."""
    repo_root = Path(__file__).resolve().parents[3]
    sensor = repo_root / "scripts" / "check_trigger_types_canonical.py"
    result = subprocess.run(
        [sys.executable, str(sensor)],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )
    assert result.returncode == 0, (
        f"Sensor should pass with allowlist. stdout: {result.stdout}\nstderr: {result.stderr}"
    )
