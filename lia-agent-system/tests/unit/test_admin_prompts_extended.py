"""
Extended unit tests for admin_prompts API endpoints and PromptVersionRegistry.

Covers: _to_response helper, endpoint behavior with empty/populated registry,
404 for unknown prompt name, response schema validation, list_all ordering,
multi-version scenarios, hash integrity.
"""
import hashlib
import pytest
from unittest.mock import MagicMock, patch

from app.api.v1.admin_prompts import (
    _to_response,
    PromptVersionResponse,
    PromptVersionListResponse,
)
from app.shared.services.prompt_version_registry import PromptVersionRegistry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def reg():
    """Fresh isolated registry per test."""
    return PromptVersionRegistry()


TEMPLATE_1 = "Você é um assistente de recrutamento da WeDOTalent."
TEMPLATE_2 = "Versão melhorada do prompt com suporte a múltiplos idiomas."
TEMPLATE_3 = "Prompt especializado para triagem técnica de candidatos."


# ---------------------------------------------------------------------------
# _to_response helper
# ---------------------------------------------------------------------------

class TestToResponse:
    def test_maps_all_fields_correctly(self):
        entry = {
            "name": "talent_react",
            "version": "2.0.0",
            "hash_prefix": "abc123def456",
            "hash_sha256": "a" * 64,
            "created_at": "2026-03-08T12:00:00+00:00",
        }
        resp = _to_response(entry)
        assert resp.name == "talent_react"
        assert resp.version == "2.0.0"
        assert resp.hash_prefix == "abc123def456"
        assert resp.hash_sha256 == "a" * 64
        assert resp.created_at == "2026-03-08T12:00:00+00:00"

    def test_returns_prompt_version_response_type(self):
        entry = {
            "name": "p", "version": "1.0.0",
            "hash_prefix": "x" * 12, "hash_sha256": "y" * 64,
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        resp = _to_response(entry)
        assert isinstance(resp, PromptVersionResponse)

    def test_hash_prefix_is_12_chars(self):
        entry = {
            "name": "p", "version": "1.0.0",
            "hash_prefix": "abcdef123456", "hash_sha256": "z" * 64,
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        resp = _to_response(entry)
        assert len(resp.hash_prefix) == 12


# ---------------------------------------------------------------------------
# PromptVersionResponse schema
# ---------------------------------------------------------------------------

class TestPromptVersionResponseSchema:
    def test_schema_requires_all_fields(self):
        resp = PromptVersionResponse(
            name="wizard_v1",
            version="1.0.0",
            hash_prefix="abc123def456",
            hash_sha256="a" * 64,
            created_at="2026-03-08T00:00:00",
        )
        assert resp.name == "wizard_v1"
        assert resp.version == "1.0.0"

    def test_schema_hash_sha256_is_string(self):
        resp = PromptVersionResponse(
            name="p", version="1.0.0",
            hash_prefix="a" * 12, hash_sha256="b" * 64,
            created_at="2026-01-01",
        )
        assert isinstance(resp.hash_sha256, str)


# ---------------------------------------------------------------------------
# PromptVersionListResponse schema
# ---------------------------------------------------------------------------

class TestPromptVersionListResponseSchema:
    def test_total_field(self):
        resp = PromptVersionListResponse(total=3, versions=[])
        assert resp.total == 3

    def test_empty_versions_list(self):
        resp = PromptVersionListResponse(total=0, versions=[])
        assert resp.versions == []

    def test_versions_list_with_items(self):
        v = PromptVersionResponse(
            name="p", version="1.0.0",
            hash_prefix="a" * 12, hash_sha256="b" * 64,
            created_at="2026-01-01",
        )
        resp = PromptVersionListResponse(total=1, versions=[v])
        assert len(resp.versions) == 1
        assert resp.versions[0].name == "p"


# ---------------------------------------------------------------------------
# Registry — list_all behavior
# ---------------------------------------------------------------------------

class TestRegistryListAll:
    def test_empty_registry_returns_empty_list(self, reg):
        assert reg.list_all() == []

    def test_list_all_returns_all_versions(self, reg):
        reg.register("p1", "1.0.0", TEMPLATE_1)
        reg.register("p1", "2.0.0", TEMPLATE_2)
        reg.register("p2", "1.0.0", TEMPLATE_3)
        all_entries = reg.list_all()
        assert len(all_entries) == 3

    def test_list_all_sorted_by_name_then_created_at(self, reg):
        reg.register("zoo", "1.0.0", TEMPLATE_1)
        reg.register("aaa", "1.0.0", TEMPLATE_2)
        all_entries = reg.list_all()
        names = [e["name"] for e in all_entries]
        assert names == sorted(names)

    def test_list_all_includes_template_field(self, reg):
        reg.register("p", "1.0.0", TEMPLATE_1)
        all_entries = reg.list_all()
        assert all_entries[0]["template"] == TEMPLATE_1


# ---------------------------------------------------------------------------
# Registry — __len__ and __contains__
# ---------------------------------------------------------------------------

class TestRegistryMagicMethods:
    def test_len_empty_registry(self, reg):
        assert len(reg) == 0

    def test_len_with_single_entry(self, reg):
        reg.register("p", "1.0.0", TEMPLATE_1)
        assert len(reg) == 1

    def test_len_with_multiple_entries(self, reg):
        reg.register("p1", "1.0.0", TEMPLATE_1)
        reg.register("p1", "2.0.0", TEMPLATE_2)
        reg.register("p2", "1.0.0", TEMPLATE_3)
        assert len(reg) == 3

    def test_contains_existing_name(self, reg):
        reg.register("talent_react", "1.0.0", TEMPLATE_1)
        assert "talent_react" in reg

    def test_not_contains_missing_name(self, reg):
        assert "nonexistent" not in reg

    def test_contains_only_checks_name_not_version(self, reg):
        reg.register("p", "1.0.0", TEMPLATE_1)
        assert "p" in reg
        # version "2.0.0" not registered, but name "p" is
        assert reg.get("p", "2.0.0") is None


# ---------------------------------------------------------------------------
# Registry — multi-version lifecycle
# ---------------------------------------------------------------------------

class TestMultiVersionLifecycle:
    def test_register_three_versions_and_get_latest(self, reg):
        reg.register("wizard", "1.0.0", TEMPLATE_1)
        reg.register("wizard", "1.1.0", TEMPLATE_2)
        h_latest = reg.register("wizard", "2.0.0", TEMPLATE_3)
        entry = reg.get("wizard", "latest")
        assert entry is not None
        assert entry["version"] == "2.0.0"
        assert reg.get_current_hash("wizard") == h_latest

    def test_update_existing_version_changes_hash(self, reg):
        h1 = reg.register("p", "1.0.0", TEMPLATE_1)
        h2 = reg.register("p", "1.0.0", TEMPLATE_2)
        assert h1 != h2
        # only new hash should be in index
        assert reg.get_by_hash(h1) is None
        assert reg.get_by_hash(h2) is not None

    def test_different_names_independent(self, reg):
        reg.register("a", "1.0.0", TEMPLATE_1)
        reg.register("b", "1.0.0", TEMPLATE_1)
        assert len(reg) == 2
        # both names have the same hash prefix (same template)
        ha = reg.get_current_hash("a")
        hb = reg.get_current_hash("b")
        # same hash since same template
        assert ha == hb

    def test_list_versions_count_after_updates(self, reg):
        reg.register("p", "1.0.0", TEMPLATE_1)
        reg.register("p", "1.0.0", TEMPLATE_2)  # update same version
        # same (name, version) → still 1 entry
        versions = reg.list_versions("p")
        assert len(versions) == 1

    def test_hash_consistency_across_registries(self):
        r1 = PromptVersionRegistry()
        r2 = PromptVersionRegistry()
        h1 = r1.register("p", "1.0.0", TEMPLATE_1)
        h2 = r2.register("p", "1.0.0", TEMPLATE_1)
        assert h1 == h2

    def test_sha256_full_hash_correct(self, reg):
        reg.register("p", "1.0.0", TEMPLATE_1)
        entry = reg.get("p", "1.0.0")
        expected = hashlib.sha256(TEMPLATE_1.encode("utf-8")).hexdigest()
        assert entry["hash_sha256"] == expected
        assert entry["hash_prefix"] == expected[:12]

    def test_created_at_is_iso_string(self, reg):
        reg.register("p", "1.0.0", TEMPLATE_1)
        entry = reg.get("p", "1.0.0")
        created_at = entry["created_at"]
        assert isinstance(created_at, str)
        assert "T" in created_at  # ISO format has T separator


# ---------------------------------------------------------------------------
# Admin endpoint - list_all_versions (unit — mocked registry)
# ---------------------------------------------------------------------------

class TestAdminPromptsListAllEndpoint:
    @pytest.mark.asyncio
    async def test_list_all_versions_returns_empty_when_no_prompts(self):
        from app.api.v1.admin_prompts import list_all_versions
        mock_user = MagicMock()
        with patch("app.api.v1.admin_prompts.prompt_version_registry") as mock_reg:
            mock_reg.list_all.return_value = []
            result = await list_all_versions(current_user=mock_user)
        assert result.total == 0
        assert result.versions == []

    @pytest.mark.asyncio
    async def test_list_all_versions_returns_correct_count(self):
        from app.api.v1.admin_prompts import list_all_versions
        mock_user = MagicMock()
        entries = [
            {"name": "p1", "version": "1.0.0", "hash_prefix": "a" * 12,
             "hash_sha256": "b" * 64, "created_at": "2026-01-01T00:00:00"},
            {"name": "p2", "version": "1.0.0", "hash_prefix": "c" * 12,
             "hash_sha256": "d" * 64, "created_at": "2026-01-02T00:00:00"},
        ]
        with patch("app.api.v1.admin_prompts.prompt_version_registry") as mock_reg:
            mock_reg.list_all.return_value = entries
            result = await list_all_versions(current_user=mock_user)
        assert result.total == 2
        assert len(result.versions) == 2

    @pytest.mark.asyncio
    async def test_list_versions_by_name_returns_404_when_not_found(self):
        from fastapi import HTTPException
        from app.api.v1.admin_prompts import list_versions_by_name
        mock_user = MagicMock()
        with patch("app.api.v1.admin_prompts.prompt_version_registry") as mock_reg:
            mock_reg.list_versions.return_value = []
            with pytest.raises(HTTPException) as exc_info:
                await list_versions_by_name("nonexistent", current_user=mock_user)
        assert exc_info.value.status_code == 404
        assert "nonexistent" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_versions_by_name_returns_versions(self):
        from app.api.v1.admin_prompts import list_versions_by_name
        mock_user = MagicMock()
        entries = [
            {"name": "wizard", "version": "1.0.0", "hash_prefix": "a" * 12,
             "hash_sha256": "b" * 64, "created_at": "2026-01-01T00:00:00"},
        ]
        with patch("app.api.v1.admin_prompts.prompt_version_registry") as mock_reg:
            mock_reg.list_versions.return_value = entries
            result = await list_versions_by_name("wizard", current_user=mock_user)
        assert result.total == 1
        assert result.versions[0].name == "wizard"
