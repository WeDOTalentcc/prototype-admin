"""TDD: protected_attributes loader path bug (ADR-031 v2 P0).

Bug origin: 2026-05-06 audit. During Sprint 1D smoke test of
`CandidateSelfServiceAgent` we observed at startup:

    [ProtectedAttributes] Failed to load YAML: [Errno 2] No such file:
    '/home/runner/workspace/lia-agent-system/app/shared/config/protected_attributes.yaml'

Root cause: `app/shared/compliance/protected_attributes.py:24-30` assigned
`_CONFIG_PATH` twice. The second assignment overwrote the first with
`app/shared/config/...` (wrong). The YAML actually lives at
`app/config/protected_attributes.yaml`.

Result: `_load_config()` caught the FileNotFoundError and silently
returned `{}` (fail-OPEN). Downstream constants — `PROTECTED_ATTRIBUTE_IDS`,
`PROTECTED_DB_FIELDS`, `BIAS_AUDIT_DIMENSIONS`, `LEARNING_PROTECTED_FIELDS`
— became empty. FairnessGuard had nothing to enforce. LGPD compliance
effectively disabled in production since Mar 2026.

This test pins:
  1. `_CONFIG_PATH` resolves to the canonical location (`app/config/`)
  2. File actually exists at that location
  3. Loader returns non-empty config
  4. All four downstream constants are populated

Skill: tdd-workflow (red→green) + harness-engineering (computational sensor).
"""
from __future__ import annotations

import os

import pytest

from app.shared.compliance import protected_attributes as pa


def test_config_path_resolves_to_app_config_directory():
    """The YAML lives at `app/config/`, NOT `app/shared/config/`."""
    p = pa._CONFIG_PATH
    norm = os.path.normpath(p).replace("\\", "/")
    assert norm.endswith("/app/config/protected_attributes.yaml"), (
        f"_CONFIG_PATH must point to app/config/, got: {p}"
    )
    assert "/shared/config/" not in norm, (
        f"Bug regression: second _CONFIG_PATH assignment resurrected: {p}"
    )


def test_config_path_actually_exists():
    """File must exist at the resolved path."""
    assert os.path.isfile(pa._CONFIG_PATH), (
        f"YAML missing at canonical path: {pa._CONFIG_PATH}. "
        f"Either the path is wrong or the YAML was deleted/moved."
    )


def test_load_config_returns_non_empty():
    """Loader must return populated config — not silent fail-open empty {}.

    LGPD invariant: empty config = effectively disabled fairness checks.
    """
    pa._load_config.cache_clear()
    cfg = pa._load_config()
    assert cfg, (
        "loader returned empty — silent fail-open regression (LGPD compliance gap). "
        "Likely _CONFIG_PATH points to a non-existent location."
    )
    assert isinstance(cfg, dict)
    assert "attributes" in cfg, (
        f"expected 'attributes' key in YAML; got keys: {list(cfg.keys())}"
    )


def test_protected_attribute_ids_populated_at_startup():
    """Module-level constants must be populated (downstream pin)."""
    pa._load_config.cache_clear()
    ids = pa._compute_ids()
    assert ids, (
        "PROTECTED_ATTRIBUTE_IDS empty — FairnessGuard would have nothing to check. "
        "This is the LGPD compliance gap we're fixing."
    )
    assert len(ids) >= 7, (
        f"expected >=7 protected attributes (LGPD/EEOC essentials: gender, race, "
        f"age, religion, orientation, marital, disability); got {len(ids)}: {ids}"
    )


def test_protected_db_fields_populated():
    pa._load_config.cache_clear()
    fields = pa._compute_db_fields()
    assert fields, "PROTECTED_DB_FIELDS empty — ATS outbound LGPD filter has nothing to scrub"


def test_bias_audit_dimensions_populated():
    pa._load_config.cache_clear()
    dims = pa._compute_bias_audit_dimensions()
    assert dims, (
        "BIAS_AUDIT_DIMENSIONS empty — bias_audit_service.py 4/5 rule analysis "
        "has no dimensions to slice by"
    )


def test_learning_protected_fields_populated():
    """Learning patterns from candidate profiles must NEVER include sensitive fields."""
    pa._load_config.cache_clear()
    fields = pa._compute_learning_protected_fields()
    assert fields, (
        "LEARNING_PROTECTED_FIELDS empty — learning_outcomes service "
        "could leak sensitive data into trained patterns"
    )
