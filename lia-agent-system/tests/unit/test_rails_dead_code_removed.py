"""GAP-00-029: Rails dead code removed — Phase 0-29 tests.

Verifies:
  1. rails_migration module is gone
  2. rails_health.py is gone and not registered in routes
  3. sync_to_rails is a permanent noop (no RAILS_ENABLED guard)
  4. crud.py / candidates_crud.py no longer import deprecation guards
  5. No stale 'Direct DB calls will be replaced by RailsAdapter' comments
"""
import ast
import importlib
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent


class TestRailsMigrationModuleGone:
    def test_rails_migration_directory_deleted(self):
        assert not (REPO_ROOT / "app/shared/rails_migration").exists(), (
            "app/shared/rails_migration/ still exists — must be deleted (Rails eliminated)"
        )

    def test_rails_migration_not_importable(self):
        with pytest.raises(ModuleNotFoundError):
            import app.shared.rails_migration.deprecation  # noqa: F401


class TestRailsHealthEndpointGone:
    def test_rails_health_file_deleted(self):
        assert not (REPO_ROOT / "app/api/v1/rails_health.py").exists(), (
            "app/api/v1/rails_health.py still exists — must be deleted"
        )

    def test_rails_health_not_in_routes(self):
        routes_path = REPO_ROOT / "app/api/routes.py"
        content = routes_path.read_text()
        assert "rails_health" not in content, (
            "routes.py still references rails_health_router — remove the import and include_router"
        )


class TestSyncToRailsNoop:
    def test_rails_enabled_flag_removed(self):
        hooks_path = REPO_ROOT / "app/orchestrator/action_handlers/_handler_hooks.py"
        content = hooks_path.read_text()
        assert "RAILS_ENABLED" not in content, (
            "_handler_hooks.py still has RAILS_ENABLED flag — remove it (Rails is eliminated)"
        )

    def test_sync_to_rails_is_noop(self):
        hooks_path = REPO_ROOT / "app/orchestrator/action_handlers/_handler_hooks.py"
        content = hooks_path.read_text()
        assert "permanent noop" in content, (
            "sync_to_rails should be marked as permanent noop"
        )

    @pytest.mark.asyncio
    async def test_sync_to_rails_returns_immediately(self):
        """sync_to_rails must return None without any I/O when called."""
        from app.orchestrator.action_handlers._handler_hooks import sync_to_rails

        # Should complete instantly with no external calls
        result = await sync_to_rails(
            event_type="candidate_moved",
            entity_type="candidate",
            entity_id="test-id",
            data={"candidate_id": "test-id"},
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_sync_to_rails_no_ats_sync_called(self):
        """Confirm ATSSyncService is never called in the noop."""
        with patch(
            "app.domains.ats_integration.services.ats_sync_service.ATSSyncService"
        ) as mock_svc_class:
            from app.orchestrator.action_handlers._handler_hooks import sync_to_rails
            await sync_to_rails("job_created", "job", "job-123")
            mock_svc_class.assert_not_called()


class TestCrudDeprecationGuardsRemoved:
    def test_job_vacancies_crud_no_rails_migration_import(self):
        crud_path = REPO_ROOT / "app/api/v1/job_vacancies/crud.py"
        content = crud_path.read_text()
        assert "rails_migration" not in content, (
            "job_vacancies/crud.py still imports from rails_migration — remove it"
        )
        assert "enforce_job_vacancies_deprecation" not in content, (
            "enforce_job_vacancies_deprecation still referenced in crud.py"
        )

    def test_candidates_crud_no_rails_migration_import(self):
        crud_path = REPO_ROOT / "app/api/v1/candidates/candidates_crud.py"
        content = crud_path.read_text()
        assert "rails_migration" not in content, (
            "candidates_crud.py still imports from rails_migration — remove it"
        )
        assert "enforce_candidates_deprecation" not in content, (
            "enforce_candidates_deprecation still referenced in candidates_crud.py"
        )


class TestStaleRailsCommentsRemoved:
    def test_no_stale_ats_handoff_comments(self):
        result = subprocess.run(
            [
                "grep", "-rn",
                "Direct DB calls will be replaced by RailsAdapter after ats-api-rails handoff",
                str(REPO_ROOT / "app"),
                "--include=*.py",
            ],
            capture_output=True,
            text=True,
        )
        found = [l for l in result.stdout.splitlines() if "__pycache__" not in l]
        assert not found, (
            f"Stale RailsAdapter handoff comments found in {len(found)} location(s):\n"
            + "\n".join(found[:5])
        )
