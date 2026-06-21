"""
P0 regression sensor (audit 2026-06-21): wizard job creation MUST inherit
company-level screening_config_defaults when a new vacancy is created.

Ghost setting context: screening_config_defaults JSONB in
company_hiring_policies was saved via Settings UI but never read by any
wizard or screening pipeline. This module pins the wire so any future
refactor that drops the inheritance fails CI.

Contract under test:
  _enrich_state_with_hiring_policy(state, row) must:
  1. Store raw screening_config_defaults dict in state.
  2. Apply enabled channels to contact_channels (setdefault).
  3. Append applied field names to company_defaults_applied.

Strategy: pure-unit test with a mock DB row namedtuple. No real DB.
Lives in tests/contract/ — tests the contract between the wizard state
and the company policy data layer.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helpers to avoid importing the whole wizard service
# ---------------------------------------------------------------------------

def _make_row(pipeline_rules=None, screening_rules=None, automation_rules=None,
              screening_config_defaults=None):
    """Minimal stand-in for a SQLAlchemy Row with 4 positional columns."""
    from collections import namedtuple
    Row = namedtuple("Row", ["c0", "c1", "c2", "c3"])
    return Row(pipeline_rules, screening_rules, automation_rules, screening_config_defaults)


# ---------------------------------------------------------------------------
# RED: import the extracted helper — will fail until implementation exists
# ---------------------------------------------------------------------------

@pytest.fixture()
def _fn():
    """Import the canonical helper. Fails until extracted in wizard_session_service."""
    from app.domains.job_creation.services.wizard_session_service import (
        _enrich_state_with_hiring_policy,
    )
    return _enrich_state_with_hiring_policy


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestScreeningDefaultsInheritance:
    """wizard state MUST be populated with company screening defaults."""

    def test_stores_raw_screening_config_defaults_in_state(self, _fn):
        """Full JSONB is stored so downstream wizard nodes can read it."""
        scd = {
            "settings": {"min_score": 85, "auto_approval_limit": 5},
            "channels": {
                "chat_web": {"enabled": True, "label": "Chat Web"},
                "whatsapp": {"enabled": False, "label": "WhatsApp"},
            },
        }
        state = {}
        row = _make_row(screening_config_defaults=scd)
        _fn(state, row)
        assert state.get("screening_config_defaults") == scd

    def test_applies_enabled_channels_to_contact_channels(self, _fn):
        """contact_channels default = enabled channels from screening config."""
        scd = {
            "channels": {
                "chat_web": {"enabled": True, "label": "Chat Web"},
                "whatsapp": {"enabled": True, "label": "WhatsApp"},
                "phone_pstn": {"enabled": False, "label": "Ligacao"},
            },
        }
        state = {}
        row = _make_row(screening_config_defaults=scd)
        _fn(state, row)
        # Only enabled channels should be populated
        assert set(state.get("contact_channels", [])) == {"chat_web", "whatsapp"}
        assert "phone_pstn" not in state.get("contact_channels", [])

    def test_does_not_overwrite_recruiter_contact_channels(self, _fn):
        """If recruiter already set contact_channels, default must not overwrite."""
        scd = {
            "channels": {
                "chat_web": {"enabled": True, "label": "Chat Web"},
                "whatsapp": {"enabled": True, "label": "WhatsApp"},
            },
        }
        state = {"contact_channels": ["phone_pstn"]}  # recruiter explicitly chose phone
        row = _make_row(screening_config_defaults=scd)
        _fn(state, row)
        assert state["contact_channels"] == ["phone_pstn"]  # untouched

    def test_tracks_applied_defaults_in_company_defaults_applied(self, _fn):
        """Applied defaults are tracked for audit/transparency."""
        scd = {
            "settings": {"min_score": 80},
            "channels": {"chat_web": {"enabled": True, "label": "Chat Web"}},
        }
        state = {}
        row = _make_row(screening_config_defaults=scd)
        _fn(state, row)
        applied = state.get("company_defaults_applied", [])
        assert "contact_channels" in applied
        assert "screening_config_defaults" in applied

    def test_no_crash_when_screening_config_defaults_is_none(self, _fn):
        """Policy without screening_config_defaults must not raise."""
        state = {}
        row = _make_row(screening_config_defaults=None)
        _fn(state, row)  # must not raise
        assert state.get("screening_config_defaults") is None

    def test_no_crash_when_channels_key_missing(self, _fn):
        """Partial config without channels key must not raise."""
        scd = {"settings": {"min_score": 80}}  # no channels key
        state = {}
        row = _make_row(screening_config_defaults=scd)
        _fn(state, row)
        assert state.get("screening_config_defaults") == scd
        assert state.get("contact_channels") is None  # nothing to apply

    def test_does_not_overwrite_existing_screening_config_defaults(self, _fn):
        """Idempotent: re-run must not overwrite state already enriched."""
        scd_first = {"settings": {"min_score": 80}}
        state = {"screening_config_defaults": scd_first}
        scd_second = {"settings": {"min_score": 99}}
        row = _make_row(screening_config_defaults=scd_second)
        _fn(state, row)
        assert state["screening_config_defaults"] == scd_first  # untouched


class TestHiringPolicySummaryStillBuilt:
    """Extending the SQL must not break existing hiring_policy_summary injection."""

    def test_still_injects_manager_approval_flag(self, _fn):
        """pipeline_rules.manager_approval_for_offer => appears in summary."""
        pr = {"manager_approval_for_offer": True}
        row = _make_row(pipeline_rules=pr, screening_config_defaults=None)
        state = {}
        _fn(state, row)
        summary = state.get("hiring_policy_summary", "")
        assert "aprovação_gestor_oferta=True" in summary

    def test_still_injects_auto_approve_threshold(self, _fn):
        """automation_rules.auto_approve_threshold => appears in summary."""
        ar = {"auto_approve_threshold": 0.75}
        row = _make_row(automation_rules=ar, screening_config_defaults=None)
        state = {}
        _fn(state, row)
        summary = state.get("hiring_policy_summary", "")
        assert "auto_approve_threshold=0.75" in summary
