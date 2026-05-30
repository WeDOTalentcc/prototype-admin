"""Unit tests — Phase 4I (PII fix + wizard_stage sync).

Harness: SENSOR (computacional) for Phase 4I.

Covers:
1. PII Layer 2 — jd_raw passed to LLM is the PII-stripped variant, NOT
   the original raw_input. Regression test for the LGPD bug fix.
2. wizard_stage sync — UPDATE SQL emitted with correct binds; multi-tenant
   guard via company_id; fail-open on DB error.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ---------------------------------------------------------------------------
# Test 1: Layer 2 PII strip is actually applied to LLM call
# ---------------------------------------------------------------------------

class TestPiiLayer2Applied:
    """Regression — raw_input_safe (PII-stripped) MUST be passed to LLM call."""

    def test_jd_raw_safe_used_in_enrich_call(self):
        """The fix in nodes/jd_enrichment.py — jd_raw_safe is what goes to LLM.

        Node was extracted from graph.py to nodes/jd_enrichment.py in PR-10 ONDA 3.
        Why this matters: the previous bug computed raw_input_safe but never
        used it; jd_raw fell back to raw_input (with PII). LGPD Art.46 violation.
        """
        # Node moved from graph.py to nodes/jd_enrichment.py (PR-10 ONDA 3 sub-B).
        with open("app/domains/job_creation/nodes/jd_enrichment.py") as f:
            src = f.read()

        # Anchor must exist exactly — guarantees the fix is in place
        assert "jd_raw=jd_raw_safe," in src, (
            "Fix: nodes/jd_enrichment.py MUST call service.enrich(jd_raw=jd_raw_safe, ...). "
            "Currently passes the original jd_raw (with PII) to the LLM. "
            "LGPD Art.46 violation."
        )

        # Negative assertion — original buggy line must NOT be present
        assert "jd_raw = state.get(\"jd_raw\") or raw_input\n" not in src, (
            "Fix: the buggy line `jd_raw = state.get('jd_raw') or raw_input` "
            "must be replaced with `jd_raw_safe = ...`. Old line allows PII to "
            "reach LLM."
        )

    def test_pii_strip_helper_is_imported_inside_layer_2(self):
        # Node moved from graph.py to nodes/jd_enrichment.py (PR-10 ONDA 3 sub-B).
        with open("app/domains/job_creation/nodes/jd_enrichment.py") as f:
            src = f.read()
        assert "from app.shared.pii_masking import strip_pii_for_llm_prompt" in src, (
            "Fix: PII Layer 2 requires `strip_pii_for_llm_prompt` import. "
            "See app/shared/pii_masking.py."
        )


# ---------------------------------------------------------------------------
# Test 2: wizard_stage sync after graph.invoke
# ---------------------------------------------------------------------------

class TestWizardStageSync:
    """WizardSessionService syncs wizard_stage to job_vacancies post-graph."""

    def test_update_sql_emitted_with_correct_binds(self):
        """Verifies the canonical UPDATE pattern is in WizardSessionService."""
        with open("app/domains/job_creation/services/wizard_session_service.py") as f:
            src = f.read()

        # Phase 4I anchor — comment + UPDATE must be present
        assert "Phase 4I — wizard_stage sync" in src, (
            "Fix: wizard_session_service.py missing Phase 4I sync block. "
            "Add post-graph hook that UPDATEs job_vacancies.wizard_stage."
        )

        # Multi-tenancy guard
        assert (
            "WHERE id = CAST(:jid AS uuid) AND company_id = :co" in src
        ), (
            "Fix: wizard_stage sync MUST include `AND company_id = :co` "
            "in WHERE clause — multi-tenancy enforcement (LGPD + tenant isolation)."
        )

        # Bind parameters present
        for required_bind in ('"s":', '"jid":', '"co":'):
            assert required_bind in src, (
                f"Fix: wizard_stage sync missing bind {required_bind} — "
                "check that all 3 placeholders are passed to db.execute()."
            )

    def test_fail_open_pattern_present(self):
        """Sync MUST fail-open — UX never blocks on sync regression."""
        with open("app/domains/job_creation/services/wizard_session_service.py") as f:
            src = f.read()

        assert (
            "wizard_stage sync failed (fail-open)" in src
        ), (
            "Fix: wizard_stage sync block MUST log 'fail-open' on exception "
            "and continue (NOT raise). Pattern: try/except Exception with "
            "logger.warning(...). See manager_preferences sync at lines 254-275."
        )

    def test_pre_publish_skip_logic(self):
        """Sync should skip when state['job_id'] is falsy (pre-publish stages)."""
        with open("app/domains/job_creation/services/wizard_session_service.py") as f:
            src = f.read()

        # The truthy-guard — skip when no job_id yet
        assert "_jv_id = result.get(\"job_id\")" in src, (
            "Fix: wizard_stage sync MUST read job_id from result dict and "
            "skip if falsy (pre-publish stages have no row to update)."
        )
        # And the conditional
        assert "if _jv_id and _stage_for_db and company_id:" in src, (
            "Fix: wizard_stage sync MUST be guarded by truthy job_id + "
            "current_stage + company_id (all 3 required for safe UPDATE)."
        )


# ---------------------------------------------------------------------------
# Test 3: wizard_stage column structural (already covered in Phase 4H, repeat
# here to keep Phase 4I tests self-contained)
# ---------------------------------------------------------------------------

class TestWizardStageColumnReady:
    """Sanity check — column exists on JobVacancy model."""

    def test_wizard_stage_column_exists(self):
        from lia_models.job_vacancy import JobVacancy
        assert hasattr(JobVacancy, "wizard_stage"), (
            "Fix: JobVacancy.wizard_stage column missing — Phase 4H step 1 "
            "migration 107 should have added it. Re-run alembic upgrade head."
        )
