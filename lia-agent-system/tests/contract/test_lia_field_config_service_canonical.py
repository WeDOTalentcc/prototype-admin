"""
P1-8 regression sensor (audit 2026-05-21): the shim at
``app/shared/services/lia_field_config_service.py`` MUST stay a thin re-export
of the canonical implementation at
``app/domains/cv_screening/services/lia_field_config_service.py``.

Bug-class context: the audit observed that several previously-singleton
services had drifted into copy-paste duplicates over time (the same defect
hit ``context_aggregator_service`` until 2026-05-21). Without a sensor, the
shim can be 'edited helpfully' into a divergent copy and any consumer that
imports from the shim path will silently see a different implementation.

Strategy: identity check on the public class symbols. If the shim ever
becomes a real implementation, ``Service`` from both paths will no longer be
``is`` the same Python object and this test will fail loudly.
"""
from __future__ import annotations


def test_shim_re_exports_canonical_service_class():
    from app.shared.services.lia_field_config_service import (
        LiaFieldConfigService as ShimSvc,
    )
    from app.domains.cv_screening.services.lia_field_config_service import (
        LiaFieldConfigService as CanonicalSvc,
    )
    # Identity, not equality: the shim must re-bind the SAME class object,
    # not create a subclass / wrapper / clone.
    assert ShimSvc is CanonicalSvc, (
        "lia_field_config_service shim has drifted from canonical. "
        "The file at app/shared/services/lia_field_config_service.py must "
        "remain a 2-line `from ... import *` re-export. If new behavior is "
        "needed in app/shared/, refactor the canonical implementation under "
        "app/domains/cv_screening/services/ — never copy it."
    )


def test_shim_re_exports_canonical_dataclasses():
    """Same pin on the data structures exported alongside the service.
    These are imported widely by consumers — divergence is invisible at
    import time but corrupts at runtime."""
    from app.shared.services.lia_field_config_service import (
        FieldConfig as ShimFieldConfig,
        FieldContext as ShimFieldContext,
        LiaFieldConfigResult as ShimResult,
    )
    from app.domains.cv_screening.services.lia_field_config_service import (
        FieldConfig as CanonicalFieldConfig,
        FieldContext as CanonicalFieldContext,
        LiaFieldConfigResult as CanonicalResult,
    )
    assert ShimFieldConfig is CanonicalFieldConfig
    assert ShimFieldContext is CanonicalFieldContext
    assert ShimResult is CanonicalResult


def test_shim_file_is_minimal():
    """Hard physical pin: the shim file should be no more than ~5 lines.
    If a future contributor adds logic here, this fails before any other
    test even has a chance to discriminate behavior."""
    import pathlib
    import app.shared.services.lia_field_config_service as shim_mod
    shim_path = pathlib.Path(shim_mod.__file__)
    text = shim_path.read_text()
    # Strip blank lines for fairness; we want to catch real code drift, not
    # cosmetic newlines.
    non_blank = [ln for ln in text.splitlines() if ln.strip()]
    assert len(non_blank) <= 5, (
        f"Shim grew to {len(non_blank)} non-blank lines (cap is 5). "
        f"Any logic in {shim_path} is a drift signal — move it into the "
        f"canonical module under app/domains/cv_screening/services/."
    )
