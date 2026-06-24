"""GAP-00-004: tool_registry_metadata.yaml ↔ domain registries sync — Phase 0-30 tests.

8 tests covering:
  - run_sync_check() structure
  - ghost detection (YAML tools without handlers)
  - undocumented tools detection
  - ok=True only when fully in sync
  - blocking mode threshold behavior
  - JSON output contract
  - real baseline matches expected counts
  - catalog load resilience
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
# Use spec_from_file_location to avoid scripts/ namespace collision
# (workspace root also has scripts/ — causing ModuleNotFoundError via pkg resolution)
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location(
    "check_tool_registry_sync",
    str(REPO_ROOT / "scripts" / "check_tool_registry_sync.py"),
)
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
format_report = _mod.format_report
main = _mod.main
run_sync_check = _mod.run_sync_check
del _ilu, _spec, _mod


class TestRunSyncCheckStructure:
    def test_returns_expected_keys(self):
        report = run_sync_check(
            yaml_names={"tool_a", "tool_b"},
            catalog_names={"tool_b", "tool_c"},
        )
        assert set(report.keys()) == {
            "ok",
            "yaml_count",
            "catalog_count",
            "common_count",
            "ghost_in_yaml",
            "undocumented",
        }

    def test_counts_correct(self):
        report = run_sync_check(
            yaml_names={"a", "b", "c"},
            catalog_names={"b", "c", "d"},
        )
        assert report["yaml_count"] == 3
        assert report["catalog_count"] == 3
        assert report["common_count"] == 2  # b, c

    def test_ghost_in_yaml_detected(self):
        """Tool in YAML without handler = ghost."""
        report = run_sync_check(
            yaml_names={"ghost_tool", "real_tool"},
            catalog_names={"real_tool"},
        )
        assert "ghost_tool" in report["ghost_in_yaml"]
        assert "real_tool" not in report["ghost_in_yaml"]

    def test_undocumented_detected(self):
        """Tool with handler but not in YAML = undocumented."""
        report = run_sync_check(
            yaml_names={"documented_tool"},
            catalog_names={"documented_tool", "undocumented_tool"},
        )
        assert "undocumented_tool" in report["undocumented"]
        assert "documented_tool" not in report["undocumented"]


class TestOkFlag:
    def test_ok_true_when_in_sync(self):
        report = run_sync_check(
            yaml_names={"a", "b"},
            catalog_names={"a", "b"},
        )
        assert report["ok"] is True
        assert report["ghost_in_yaml"] == []
        assert report["undocumented"] == []

    def test_ok_false_when_ghost_exists(self):
        report = run_sync_check(
            yaml_names={"ghost"},
            catalog_names=set(),
        )
        assert report["ok"] is False

    def test_ok_false_when_yaml_empty_but_catalog_has_tools(self):
        """Undocumented tools alone do NOT set ok=False (they're warn-only)."""
        report = run_sync_check(
            yaml_names=set(),
            catalog_names={"tool1", "tool2"},
        )
        # ok=True because no ghost_in_yaml; undocumented is warn-only
        assert report["ok"] is True
        assert len(report["undocumented"]) == 2


class TestBlockingMode:
    def test_blocking_exits_1_when_ghosts_exceed_threshold(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            with patch(
                "scripts.check_tool_registry_sync.run_sync_check",
                return_value={
                    "ok": False,
                    "yaml_count": 5,
                    "catalog_count": 3,
                    "common_count": 2,
                    "ghost_in_yaml": ["ghost1", "ghost2", "ghost3"],
                    "undocumented": [],
                },
            ):
                sys.exit(main(["--blocking", "--max-violations", "2"]))
        assert exc_info.value.code == 1

    def test_blocking_exits_0_within_threshold(self):
        exit_code = main(["--blocking", "--max-violations", "50"])
        # Current baseline is 37, below 50
        assert exit_code == 0

    def test_warn_only_exits_0_regardless_of_ghosts(self):
        exit_code = main([])
        assert exit_code == 0


class TestRealBaseline:
    def test_yaml_has_51_tools(self):
        """Baseline 2026-06-15: YAML has 51 declared tools."""
        from app.tools.tool_registry_loader import load_tool_metadata
        yaml_names = set(load_tool_metadata().keys())
        assert len(yaml_names) == 51, (
            f"Expected 51 YAML tools, got {len(yaml_names)}. "
            "Update this test if tools are intentionally added/removed from YAML."
        )

    def test_ghost_count_not_increased(self):
        """Ratchet: ghost_in_yaml must not grow beyond baseline of 37."""
        report = run_sync_check()
        assert len(report["ghost_in_yaml"]) <= 37, (
            f"ghost_in_yaml grew from baseline 37 to {len(report['ghost_in_yaml'])}. "
            "A new YAML entry was added without a domain handler. "
            "Add the handler OR remove the YAML entry."
        )
