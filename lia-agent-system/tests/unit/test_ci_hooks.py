"""Tests for Phase 0-31: CI/CD Pre-commit Hook Automation (GAP-00-008)."""
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]  # workspace root
LIA_DIR = REPO_ROOT / "lia-agent-system"
SCRIPTS_DIR = LIA_DIR / "scripts"
GIT_HOOKS_DIR = REPO_ROOT / ".git" / "hooks"


class TestPreCommitHookScript:
    """pre-commit-hook.sh — versioned sensor runner."""

    def test_script_exists(self):
        assert (SCRIPTS_DIR / "pre-commit-hook.sh").is_file()

    def test_script_is_executable(self):
        hook = SCRIPTS_DIR / "pre-commit-hook.sh"
        assert os.access(hook, os.X_OK), "pre-commit-hook.sh must be executable"

    def test_script_has_shebang(self):
        first_line = (SCRIPTS_DIR / "pre-commit-hook.sh").read_text().splitlines()[0]
        assert first_line.startswith("#!/usr/bin/env bash"), f"Bad shebang: {first_line}"

    def test_skip_all_sensors_env_exits_zero(self):
        env = os.environ.copy()
        env["SKIP_ALL_SENSORS"] = "1"
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "pre-commit-hook.sh")],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(LIA_DIR),
        )
        assert result.returncode == 0, f"SKIP_ALL_SENSORS=1 should exit 0\nstderr: {result.stderr}"
        assert "SKIP_ALL_SENSORS" in result.stderr

    def test_skip_slow_sensors_skips_slow_but_allows_fast(self):
        env = os.environ.copy()
        env["SKIP_SLOW_SENSORS"] = "1"
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "pre-commit-hook.sh")],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(LIA_DIR),
        )
        # Should exit 0 (fast sensors likely pass) and mention slow sensors skipped
        combined = result.stdout + result.stderr
        assert "SKIP_SLOW_SENSORS" in combined or "pulados" in combined

    def test_migration_merge_safety_runs(self):
        """migration-merge-safety sensor name must appear in output."""
        env = os.environ.copy()
        env["SKIP_SLOW_SENSORS"] = "1"
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "pre-commit-hook.sh")],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(LIA_DIR),
        )
        combined = result.stdout + result.stderr
        assert "migration-merge-safety" in combined

    def test_script_is_git_tracked(self):
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "lia-agent-system/scripts/pre-commit-hook.sh"],
            capture_output=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, "pre-commit-hook.sh must be git-tracked"


class TestInstallHooksScript:
    """install_hooks.sh — idempotent hook bootstrapper."""

    def test_script_exists(self):
        assert (SCRIPTS_DIR / "install_hooks.sh").is_file()

    def test_script_is_executable(self):
        assert os.access(SCRIPTS_DIR / "install_hooks.sh", os.X_OK)

    def test_check_mode_detects_installed_hook(self):
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "install_hooks.sh"), "--check"],
            capture_output=True,
            text=True,
            cwd=str(LIA_DIR),
        )
        hook_path = GIT_HOOKS_DIR / "pre-commit"
        if hook_path.is_file() and os.access(hook_path, os.X_OK):
            assert result.returncode == 0
        else:
            assert result.returncode == 1

    def test_install_is_idempotent(self, tmp_path):
        """Installing twice produces same result without error."""
        fake_hooks = tmp_path / ".git" / "hooks"
        fake_hooks.mkdir(parents=True)
        env = os.environ.copy()
        # First install
        result1 = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "install_hooks.sh")],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(LIA_DIR),
        )
        # Second install (idempotent)
        result2 = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "install_hooks.sh")],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(LIA_DIR),
        )
        assert result2.returncode == 0, f"Second install failed: {result2.stderr}"

    def test_script_is_git_tracked(self):
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "lia-agent-system/scripts/install_hooks.sh"],
            capture_output=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, "install_hooks.sh must be git-tracked"


class TestGitHookInstalled:
    """.git/hooks/pre-commit wrapper — installed and callable."""

    def test_hook_file_exists(self):
        hook = GIT_HOOKS_DIR / "pre-commit"
        assert hook.is_file(), f".git/hooks/pre-commit missing — run: bash scripts/install_hooks.sh"

    def test_hook_is_executable(self):
        hook = GIT_HOOKS_DIR / "pre-commit"
        assert os.access(hook, os.X_OK), ".git/hooks/pre-commit must be executable"

    def test_hook_delegates_to_versioned_script(self):
        hook = GIT_HOOKS_DIR / "pre-commit"
        content = hook.read_text()
        assert "pre-commit-hook.sh" in content, "Hook should delegate to scripts/pre-commit-hook.sh"

    def test_hook_runs_skip_all(self):
        env = os.environ.copy()
        env["SKIP_ALL_SENSORS"] = "1"
        result = subprocess.run(
            [str(GIT_HOOKS_DIR / "pre-commit")],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(LIA_DIR),
        )
        assert result.returncode == 0


class TestMakefileTargets:
    """Makefile ci/ci-fast/hooks-install/hooks-check targets."""

    def test_makefile_has_ci_target(self):
        makefile = LIA_DIR / "Makefile"
        content = makefile.read_text()
        assert "ci:" in content or "ci :" in content

    def test_makefile_has_ci_fast_target(self):
        makefile = LIA_DIR / "Makefile"
        content = makefile.read_text()
        assert "ci-fast:" in content or "ci-fast :" in content

    def test_makefile_has_hooks_install_target(self):
        makefile = LIA_DIR / "Makefile"
        content = makefile.read_text()
        assert "hooks-install" in content

    def test_makefile_has_hooks_check_target(self):
        makefile = LIA_DIR / "Makefile"
        content = makefile.read_text()
        assert "hooks-check" in content

    def test_make_ci_fast_exits_zero(self):
        """ci-fast must complete without error (migration sensor passes)."""
        result = subprocess.run(
            ["make", "ci-fast"],
            capture_output=True,
            text=True,
            cwd=str(LIA_DIR),
            timeout=30,
        )
        assert result.returncode == 0, f"make ci-fast failed:\n{result.stdout}\n{result.stderr}"


class TestReplitWorkflow:
    """.replit ci-sensors workflow — declared but not executable in tests."""

    def test_ci_sensors_workflow_declared(self):
        replit_file = REPO_ROOT / ".replit"
        content = replit_file.read_text()
        assert 'name = "ci-sensors"' in content, "ci-sensors workflow missing from .replit"

    def test_ci_sensors_workflow_has_exec(self):
        replit_file = REPO_ROOT / ".replit"
        content = replit_file.read_text()
        # The ci-sensors block should reference install_hooks and make ci
        assert "install_hooks.sh" in content
        assert "make ci" in content
