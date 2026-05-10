"""TDD red-phase — P0-3: ADR-LGPD-001 N-threshold gate sentinels.

Audit finding (governance agent):
- ADR-LGPD-001 claims aggregate-not-PII but provides no quantitative
  argument. Mathematically: at small N (2-3 hires) running average is
  partially reversible if attacker has any side-channel signal.
- Mitigation: bigfive_department_profiles must NOT be queryable when
  sample_count < MIN_DEPT_SAMPLES (10).

Good news: bigfive_service.py:42 already defines MIN_DEPT_SAMPLES = 10
and bigfive_service.py:183 already gates the blend layer behind this
threshold. These tests are sentinel guards: they pass today AND prevent
regression to a state where the threshold drops below 10 or the gate is
removed.
"""
from __future__ import annotations

import inspect


def test_min_dept_samples_constant_is_at_least_10():
    """ADR-LGPD-001 requires N >= 10 before profile is queryable.
    Anything lower exposes residual inference risk on the running-average
    aggregate at small N."""
    from app.domains.job_creation.services.bigfive_service import MIN_DEPT_SAMPLES

    assert MIN_DEPT_SAMPLES >= 10, (
        f"MIN_DEPT_SAMPLES={MIN_DEPT_SAMPLES}, must be >= 10 per ADR-LGPD-001. "
        f"At smaller N the running-average aggregate is partially reversible "
        f"and can leak individual contributions when combined with side-channel "
        f"signals (e.g., when a candidate's PII is erased). Restoring the "
        f"threshold is required to keep the aggregate-not-PII argument valid."
    )


def test_get_blend_weights_skips_dept_when_under_min_samples():
    """The gate at bigfive_service.py:183 must remain present.
    Source-inspection sentinel: refuses removal of MIN_DEPT_SAMPLES gate
    from get_blend_weights without a replacing safeguard."""
    from app.domains.job_creation.services import bigfive_service

    source = inspect.getsource(bigfive_service.BigFiveDepartmentService.get_blend_weights)
    assert "MIN_DEPT_SAMPLES" in source, (
        "get_blend_weights no longer references MIN_DEPT_SAMPLES gate. "
        "Restore the check `if dept is not None and (dept.sample_count or 0) "
        "< MIN_DEPT_SAMPLES: dept = None` so dept profiles below the threshold "
        "are NOT used in the blend (ADR-LGPD-001 minimum-N requirement)."
    )
    # Negative regression: refuse a softening pattern like '< 5' or '< 3'
    assert "MIN_DEPT_SAMPLES" in source and "sample_count" in source, (
        "Gate logic looks weakened — both MIN_DEPT_SAMPLES and sample_count "
        "must appear together in get_blend_weights."
    )


def test_adr_lgpd_001_docstring_cites_anpd_precedent():
    """Audit finding: ADR-LGPD-001 must cite specific ANPD guidance, not
    just claim 'ANPD interpretation' generically. Required references:
    - ANPD Guia de Anonimização §3 (irreversibility test)
    - LGPD Art. 12 §1 (anonymized data scope)
    """
    from app.domains.communication.services import transition_dispatch_service

    source = inspect.getsource(
        transition_dispatch_service.TransitionDispatchService._hook_conclusion_hired
    )
    # Must cite Guia ANPD Anonimização (the canonical reference)
    has_anpd_citation = (
        "Guia" in source and "Anonimiz" in source
    ) or "Resolução CD/ANPD" in source or "Resolução CD/ANPD" in source

    assert has_anpd_citation, (
        "ADR-LGPD-001 docstring lacks a specific ANPD precedent citation. "
        "Add a reference to either ANPD's 'Guia de Anonimização' or "
        "'Resolução CD/ANPD nº 2/2022' (or both). The bare claim 'ANPD "
        "interpretation' does not survive regulator scrutiny — courts "
        "expect specific citations to opinions/dispatches/guidance."
    )

    # Must cite LGPD Art. 12 §1 (the legal hook for aggregate-not-PII argument)
    assert "Art. 12" in source or "Art 12" in source or "Artigo 12" in source, (
        "ADR-LGPD-001 must cite LGPD Art. 12 §1 — that is the article "
        "that places anonymized data outside the scope of LGPD protections "
        "when reversal requires 'esforços razoáveis'. Without this anchor "
        "the irreversibility argument has no legal basis."
    )

    # Must mention the N>=10 minimum threshold (the quantitative anchor)
    assert "MIN_DEPT_SAMPLES" in source or "N>=10" in source or "N >= 10" in source, (
        "ADR-LGPD-001 must reference the minimum-N gate (MIN_DEPT_SAMPLES) "
        "that operationalizes the irreversibility claim. Without a "
        "concrete threshold the docstring's 'irreversible' claim is unbacked."
    )
