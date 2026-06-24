"""Unit tests for GAP-05-005: draft recovery pattern.

Tests cover:
- build_draft_snapshot produces correct shape with metadata
- is_draft_expired returns False for fresh snapshots
- is_draft_expired returns True after TTL passes
- merge_draft_with_existing prefers non-None draft values
- merge_draft_with_existing keeps existing when draft value is None/empty
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.shared.draft_recovery import (
    DRAFT_TTL_DAYS,
    build_draft_snapshot,
    is_draft_expired,
    merge_draft_with_existing,
)


class TestBuildDraftSnapshot:
    def test_build_draft_snapshot_has_metadata(self):
        form_data = {"title": "Engenheiro de Software", "department": "Tecnologia"}
        snapshot = build_draft_snapshot(form_data, step="descricao")

        assert snapshot["data"] == form_data
        assert snapshot["step"] == "descricao"
        assert snapshot["version"] == 1
        assert "saved_at" in snapshot
        # saved_at must be a valid ISO datetime
        dt = datetime.fromisoformat(snapshot["saved_at"])
        assert dt is not None

    def test_build_draft_snapshot_without_step(self):
        snapshot = build_draft_snapshot({"title": "Analista"})
        assert snapshot["step"] is None
        assert snapshot["data"]["title"] == "Analista"

    def test_build_draft_snapshot_saved_at_is_utc(self):
        snapshot = build_draft_snapshot({})
        saved_at = datetime.fromisoformat(snapshot["saved_at"])
        # Must be timezone-aware (UTC)
        assert saved_at.tzinfo is not None


class TestIsDraftExpired:
    def test_draft_not_expired_when_fresh(self):
        snapshot = build_draft_snapshot({"title": "Dev"}, step="requisitos")
        assert is_draft_expired(snapshot) is False

    def test_draft_expired_after_ttl(self):
        # Simulate a snapshot saved DRAFT_TTL_DAYS+1 days ago
        past_dt = datetime.now(timezone.utc) - timedelta(days=DRAFT_TTL_DAYS + 1)
        snapshot = {
            "data": {"title": "Old Dev"},
            "step": None,
            "saved_at": past_dt.isoformat(),
            "version": 1,
        }
        assert is_draft_expired(snapshot) is True

    def test_draft_not_expired_at_ttl_boundary(self):
        # Exactly TTL_DAYS ago — NOT expired (boundary is strictly >)
        boundary_dt = datetime.now(timezone.utc) - timedelta(days=DRAFT_TTL_DAYS)
        snapshot = {
            "data": {},
            "step": None,
            "saved_at": boundary_dt.isoformat(),
            "version": 1,
        }
        assert is_draft_expired(snapshot) is False

    def test_draft_expired_when_snapshot_malformed(self):
        assert is_draft_expired({}) is True
        assert is_draft_expired({"saved_at": "not-a-date"}) is True
        assert is_draft_expired({"saved_at": None}) is True

    def test_draft_expired_custom_ttl(self):
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=2)
        snapshot = {
            "data": {},
            "step": None,
            "saved_at": one_hour_ago.isoformat(),
            "version": 1,
        }
        # With ttl_days=0 (0 days), any snapshot from yesterday+ is expired.
        # 2 hours ago = 0 days age, not > 0 days, so NOT expired at ttl=0.
        assert is_draft_expired(snapshot, ttl_days=0) is False
        # With a very small custom ttl using a date from > 1 day ago
        old = datetime.now(timezone.utc) - timedelta(days=2)
        snapshot_old = {**snapshot, "saved_at": old.isoformat()}
        assert is_draft_expired(snapshot_old, ttl_days=1) is True


class TestMergeDraftWithExisting:
    def test_merge_draft_prefers_non_none_values(self):
        existing = {"title": "Dev Júnior", "department": "TI", "salary": None}
        draft = {"title": "Dev Pleno", "salary": "12000-16000"}
        merged = merge_draft_with_existing(existing, draft)

        assert merged["title"] == "Dev Pleno"
        assert merged["salary"] == "12000-16000"
        assert merged["department"] == "TI"  # kept from existing

    def test_merge_draft_keeps_existing_when_draft_null(self):
        existing = {"title": "Analista", "location": "São Paulo"}
        draft = {"title": None, "location": ""}  # None and "" both skip
        merged = merge_draft_with_existing(existing, draft)

        assert merged["title"] == "Analista"
        assert merged["location"] == "São Paulo"

    def test_merge_draft_adds_new_keys_from_draft(self):
        existing = {"title": "Dev"}
        draft = {"department": "Engenharia", "seniority_level": "Pleno"}
        merged = merge_draft_with_existing(existing, draft)

        assert merged["department"] == "Engenharia"
        assert merged["seniority_level"] == "Pleno"
        assert merged["title"] == "Dev"

    def test_merge_draft_does_not_mutate_existing(self):
        existing = {"title": "Dev"}
        draft = {"title": "Senior Dev"}
        original_existing = dict(existing)
        merge_draft_with_existing(existing, draft)
        # existing must be unchanged
        assert existing == original_existing

    def test_merge_draft_empty_draft_returns_copy_of_existing(self):
        existing = {"title": "Dev", "department": "TI"}
        merged = merge_draft_with_existing(existing, {})
        assert merged == existing
        assert merged is not existing  # must be a new dict
