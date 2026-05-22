"""
Anti-regressão · W1-002 (2026-05-22) — BaseAgent legacy cleanup.

Garante que:
1. Símbolos canonical estão em `app/shared/agents/agent_types.py`
   (AgentType, TaskPriority, TaskStatus, AgentAction, AgentTask).
2. NÃO há imports de `from app.agents.base_agent import …` em código vivo
   (app/, libs/, tests/) — exceto o próprio shim em `app/agents/base_agent.py`.
3. `BaseAgent` legacy (com `process(intent, entities, context)`) NÃO é mais
   exportado pelo shim — shim só re-exporta enums + DeprecationWarning.
4. Canonical `BaseAgent` em `lia_agents_core.agent_interface` continua intacto.

Esse teste é o sensor TDD do W1-002. Roda antes (RED) e depois (GREEN).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestCanonicalAgentTypesLocation:
    """Símbolos vivos têm que estar em app/shared/agents/agent_types.py."""

    def test_agent_type_importable_from_canonical(self) -> None:
        from app.shared.agents.agent_types import AgentType  # noqa: F401

        # Sanity: enum tem os 9 ativos + 4 deprecated do diagnostic
        assert AgentType.ORCHESTRATOR.value == "orchestrator"
        assert AgentType.JOB_PLANNER.value == "job_planner"
        assert AgentType.CV_SCREENING.value == "cv_screening"
        assert AgentType.WSI_EVALUATOR.value == "wsi_evaluator"
        assert AgentType.ANALYST_FEEDBACK.value == "analyst_feedback"

    def test_task_priority_importable_from_canonical(self) -> None:
        from app.shared.agents.agent_types import TaskPriority

        assert TaskPriority.CRITICAL.value == "critical"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.LOW.value == "low"

    def test_task_status_importable_from_canonical(self) -> None:
        from app.shared.agents.agent_types import TaskStatus

        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.COMPLETED.value == "completed"

    def test_agent_task_importable_from_canonical(self) -> None:
        from app.shared.agents.agent_types import AgentTask, AgentType

        task = AgentTask(
            id="t-1",
            title="x",
            description="y",
            created_by_agent=AgentType.JOB_PLANNER,
        )
        assert task.id == "t-1"

    def test_agent_action_importable_from_canonical(self) -> None:
        from app.shared.agents.agent_types import AgentAction

        action = AgentAction(name="n", description="d", handler="h")
        assert action.name == "n"


class TestLegacyBaseAgentShimBehavior:
    """app/agents/base_agent.py NÃO pode mais ter BaseAgent ABC legacy."""

    def test_legacy_module_does_not_export_baseagent_abc(self) -> None:
        """
        Shim de retrocompat pode re-exportar enums (AgentType, TaskPriority etc.)
        com DeprecationWarning, mas NÃO o `BaseAgent(ABC)` legacy com
        process(intent, entities, context) — esse foi pra `lia_agents_core`.
        """
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from app.agents import base_agent as legacy_mod

        # Enums podem persistir via shim
        assert hasattr(legacy_mod, "AgentType"), "Shim deve re-exportar AgentType enum"

        # Legacy BaseAgent ABC com process(intent,entities,context) NÃO deve existir
        # nem como classe própria nem via re-export
        if hasattr(legacy_mod, "BaseAgent"):
            from lia_agents_core.agent_interface import BaseAgent as CanonicalBaseAgent

            # Se BaseAgent existe no shim, DEVE ser o canonical (não o legacy)
            assert legacy_mod.BaseAgent is CanonicalBaseAgent, (
                "BaseAgent exposto pelo shim deve ser o canonical do "
                "lia_agents_core.agent_interface, não o legacy ABC."
            )

    def test_legacy_module_emits_deprecation_warning(self) -> None:
        """Import direto do shim deve emitir DeprecationWarning."""
        import importlib
        import warnings

        # Force reload to capture warning
        import app.agents.base_agent
        importlib.reload(app.agents.base_agent)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            importlib.reload(app.agents.base_agent)
            deprecation_warns = [
                warn for warn in w if issubclass(warn.category, DeprecationWarning)
            ]
            assert len(deprecation_warns) >= 1, (
                "Shim deve emitir DeprecationWarning indicando que canonical é "
                "app.shared.agents.agent_types"
            )


class TestNoLegacyImportsInLiveCode:
    """
    AST scan: nenhum arquivo .py em app/, libs/, tests/ pode importar de
    `app.agents.base_agent` (exceto o próprio shim).
    """

    @staticmethod
    def _find_legacy_imports() -> list[tuple[str, int]]:
        offenders: list[tuple[str, int]] = []
        roots = [REPO_ROOT / "app", REPO_ROOT / "libs", REPO_ROOT / "tests"]
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob("*.py"):
                rel = path.relative_to(REPO_ROOT)
                # Skip o próprio shim + caches
                if str(rel) == "app/agents/base_agent.py":
                    continue
                if "__pycache__" in path.parts:
                    continue
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8"))
                except SyntaxError:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        mod = node.module or ""
                        if mod == "app.agents.base_agent" or mod.endswith(
                            ".agents.base_agent"
                        ):
                            offenders.append((str(rel), node.lineno))
        return offenders

    def test_no_imports_from_legacy_module(self) -> None:
        offenders = self._find_legacy_imports()
        assert offenders == [], (
            f"Imports legacy de `app.agents.base_agent` ainda presentes "
            f"({len(offenders)} sites). Use `app.shared.agents.agent_types`:\n"
            + "\n".join(f"  - {p}:{ln}" for p, ln in offenders)
        )


class TestCanonicalBaseAgentIntact:
    """Garante que lia_agents_core.BaseAgent (canonical) não foi tocado."""

    def test_canonical_base_agent_signature(self) -> None:
        from lia_agents_core.agent_interface import AgentInput, AgentOutput, BaseAgent

        # process(input: AgentInput) -> AgentOutput
        import inspect

        sig = inspect.signature(BaseAgent.process)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "input" in params
        # Output annotation deve ser AgentOutput (string ou class)
        ret = sig.return_annotation
        assert ret is AgentOutput or getattr(ret, "__name__", None) == "AgentOutput"
