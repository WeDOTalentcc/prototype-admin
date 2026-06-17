"""
Anti-regressão · W1-001 (2026-05-22) — Agent registry coherence.

Garante:
1. YAML × decorator coherence (todo agent YAML enabled tem @register_agent).
2. Decorator coverage suficiente (>= 26 agents canonical no _AGENT_REGISTRY).
3. Sourcing sub-agents especializados decorados (W1-001 fix do drift).
4. Sensor coherence rodando STRICT (não --warn-only).

Pre-audit: sprint_logs/sprint_1.2/W1-001_AUDIT.md.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_YAML = REPO_ROOT / "app" / "agents_registry.yaml"
COHERENCE_SENSOR = REPO_ROOT / "scripts" / "check_yaml_decorator_coherence.py"
PATHS_SENSOR = REPO_ROOT / "scripts" / "check_agents_registry_paths.py"


def _yaml_agent_names() -> set[str]:
    data = yaml.safe_load(REGISTRY_YAML.read_text()) or {}
    agents = data.get("agents", []) if isinstance(data, dict) else []
    return {a["name"] for a in agents if a.get("enabled", True) and a.get("name")}


def _load_agent_registry_module():
    """Force imports + return canonical _AGENT_REGISTRY dict."""
    # Trigger imports via _ensure_agents_loaded equivalent
    from app.api.v1 import chat_shared as agent_chat_ws  # noqa

    if hasattr(agent_chat_ws, "_ensure_agents_loaded"):
        agent_chat_ws._ensure_agents_loaded()
    # 6 sourcing sub-agents — força import se ainda não foram (W1-001 cleanup target)
    try:
        from app.domains.sourcing.agents import (  # noqa: F401
            diversity_sourcing_agent,
            github_sourcing_agent,
            nurture_sequence_agent,
            passive_pipeline_agent,
            referral_agent,
            stackoverflow_sourcing_agent,
        )
    except ImportError:
        pass

    from app.shared.agents.agent_registry import _AGENT_ALIASES, _AGENT_REGISTRY

    return _AGENT_REGISTRY, _AGENT_ALIASES


class TestYamlDecoratorCoherence:
    """Todo agent YAML enabled tem @register_agent (ou alias)."""

    def test_every_yaml_agent_is_decorated(self) -> None:
        registry, aliases = _load_agent_registry_module()
        yaml_names = _yaml_agent_names()
        registered = set(registry.keys()) | set(aliases.keys())

        missing = yaml_names - registered
        assert not missing, (
            f"Agents em YAML SEM @register_agent: {sorted(missing)}\n"
            f"YAML names: {sorted(yaml_names)}\n"
            f"Registered: {sorted(registered)}"
        )


class TestDecoratorCoverage:
    """Decorator deve cobrir >= 26 agents canonical (estado pós-W1-001)."""

    def test_minimum_decorated_agents_count(self) -> None:
        registry, _ = _load_agent_registry_module()
        # 26 baseline + 6 sourcing sub-agents (W1-001 cleanup) = 32
        assert len(registry) >= 26, (
            f"Esperado >=26 decorated agents, encontrei {len(registry)}: "
            f"{sorted(registry.keys())}"
        )

    def test_sourcing_sub_agents_decorated_W1_001(self) -> None:
        """W1-001: os 6 sourcing sub-agents devem ter @register_agent."""
        registry, _ = _load_agent_registry_module()
        expected = {
            "sourcing_github",
            "sourcing_stackoverflow",
            "sourcing_diversity",
            "sourcing_passive_pipeline",
            "sourcing_referral",
            "sourcing_nurture_sequence",
        }
        missing = expected - set(registry.keys())
        assert not missing, (
            f"Sourcing sub-agents NÃO decorados (W1-001 fix): {sorted(missing)}\n"
            f"FIX: adicionar @register_agent(\"<name>\") no topo de cada class."
        )


class TestSensorBlocking:
    """Sensor coherence runs STRICT em CI/pre-commit (não --warn-only)."""

    def test_coherence_sensor_exists(self) -> None:
        assert COHERENCE_SENSOR.exists(), f"Sensor missing: {COHERENCE_SENSOR}"

    def test_coherence_sensor_passes_strict(self) -> None:
        result = subprocess.run(
            [sys.executable, str(COHERENCE_SENSOR)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"Coherence sensor FAILED (exit={result.returncode}):\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

    def test_paths_sensor_passes_strict(self) -> None:
        """R-004 class_path validation — sensor existente, agora BLOCKING."""
        assert PATHS_SENSOR.exists()
        result = subprocess.run(
            [sys.executable, str(PATHS_SENSOR)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"Class_paths sensor FAILED (exit={result.returncode}):\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )


class TestRegistryConsistencyInvariants:
    """Invariantes runtime do canonical AgentRegistry."""

    def test_pipeline_has_cv_screening_alias(self) -> None:
        """pipeline DEVE ter alias cv_screening (documentação canonical
        em app/shared/agents/agent_registry.py:18)."""
        _, aliases = _load_agent_registry_module()
        assert aliases.get("cv_screening") == "pipeline", (
            f"Alias cv_screening deve apontar pra 'pipeline'. "
            f"Aliases atuais: {aliases}"
        )

    def test_no_overlapping_canonical_and_alias(self) -> None:
        """Mesmo id NÃO pode ser canonical E alias simultaneamente."""
        registry, aliases = _load_agent_registry_module()
        overlap = set(registry.keys()) & set(aliases.keys())
        assert not overlap, (
            f"IDs duplicados como canonical + alias: {sorted(overlap)}"
        )
