"""
Contract tests for the 4 architectural boundary Protocols defined in task-124.

Verifies:
1. OrchestratorProtocol — runtime_checkable structural typing
2. DomainProtocol       — runtime_checkable structural typing
3. AgentProtocol        — runtime_checkable structural typing
4. LLMProviderProtocol  — runtime_checkable structural typing

These tests act as a living specification: if a class satisfies the Protocol
structurally, isinstance() returns True; if it is missing a method, it returns False.
"""
from __future__ import annotations

import pytest

from lia_agents_core.contracts import (
    AgentProtocol,
    DomainProtocol,
    LLMProviderProtocol,
    OrchestratorProtocol,
)


# ---------------------------------------------------------------------------
# Minimal compliant implementations (for structural checking only)
# ---------------------------------------------------------------------------

class _MinimalOrchestrator:
    async def route(self, message, session_id, company_id, user_id, context, conversation_history, metadata=None):
        return {}

    async def get_status(self):
        return {"status": "ok"}


class _MinimalDomain:
    @property
    def domain_id(self):
        return "test_domain"

    @property
    def domain_name(self):
        return "Test Domain"

    def get_allowed_actions(self):
        return []

    def get_system_prompt(self):
        return "You are a test domain agent."

    async def process_intent(self, query, context):
        return {"intent_id": "noop", "action_id": "noop", "confidence": 1.0}

    async def execute_action(self, action_id, params, context):
        return {"success": True, "message": "ok"}


class _MinimalAgent:
    @property
    def domain_name(self):
        return "test"

    @property
    def available_tools(self):
        return []

    async def process(self, input):
        return {"message": "ok", "actions": []}

    async def get_status(self):
        return {"status": "ok"}


class _MinimalLLMProvider:
    @property
    def provider_name(self):
        return "mock"

    @property
    def default_model(self):
        return "mock-model-1"

    async def generate(self, prompt, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        return object()

    async def generate_with_system(self, system_prompt, user_message, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        return object()

    async def generate_with_tools(self, messages, tools, system_prompt=None, max_tokens=4096, **kwargs):
        return object()

    async def generate_structured(self, messages, output_schema, system_prompt=None, max_tokens=4096, **kwargs):
        return {}


# ---------------------------------------------------------------------------
# Non-compliant (missing required methods)
# ---------------------------------------------------------------------------

class _IncompleteOrchestrator:
    async def get_status(self):
        return {}


class _IncompleteDomain:
    @property
    def domain_id(self):
        return "bad"


class _IncompleteAgent:
    @property
    def domain_name(self):
        return "bad"


class _IncompleteLLMProvider:
    @property
    def provider_name(self):
        return "bad"


# ===========================================================================
# Tests
# ===========================================================================

class TestOrchestratorProtocol:
    def test_compliant_class_satisfies_protocol(self):
        obj = _MinimalOrchestrator()
        assert isinstance(obj, OrchestratorProtocol)

    def test_incomplete_class_fails_protocol(self):
        obj = _IncompleteOrchestrator()
        assert not isinstance(obj, OrchestratorProtocol)

    def test_plain_object_fails_protocol(self):
        assert not isinstance(object(), OrchestratorProtocol)

    def test_protocol_is_importable_from_contracts(self):
        from lia_agents_core.contracts import OrchestratorProtocol as OP
        assert OP is OrchestratorProtocol

    def test_protocol_is_importable_from_package(self):
        from lia_agents_core import OrchestratorProtocol as OP
        assert OP is OrchestratorProtocol


class TestDomainProtocol:
    def test_compliant_class_satisfies_protocol(self):
        obj = _MinimalDomain()
        assert isinstance(obj, DomainProtocol)

    def test_incomplete_class_fails_protocol(self):
        obj = _IncompleteDomain()
        assert not isinstance(obj, DomainProtocol)

    def test_plain_object_fails_protocol(self):
        assert not isinstance(object(), DomainProtocol)

    def test_protocol_is_importable_from_contracts(self):
        from lia_agents_core.contracts import DomainProtocol as DP
        assert DP is DomainProtocol

    def test_protocol_is_importable_from_package(self):
        from lia_agents_core import DomainProtocol as DP
        assert DP is DomainProtocol


class TestAgentProtocol:
    def test_compliant_class_satisfies_protocol(self):
        obj = _MinimalAgent()
        assert isinstance(obj, AgentProtocol)

    def test_incomplete_class_fails_protocol(self):
        obj = _IncompleteAgent()
        assert not isinstance(obj, AgentProtocol)

    def test_plain_object_fails_protocol(self):
        assert not isinstance(object(), AgentProtocol)

    def test_protocol_is_importable_from_contracts(self):
        from lia_agents_core.contracts import AgentProtocol as AP
        assert AP is AgentProtocol

    def test_protocol_is_importable_from_package(self):
        from lia_agents_core import AgentProtocol as AP
        assert AP is AgentProtocol


class TestLLMProviderProtocol:
    def test_compliant_class_satisfies_protocol(self):
        obj = _MinimalLLMProvider()
        assert isinstance(obj, LLMProviderProtocol)

    def test_incomplete_class_fails_protocol(self):
        obj = _IncompleteLLMProvider()
        assert not isinstance(obj, LLMProviderProtocol)

    def test_plain_object_fails_protocol(self):
        assert not isinstance(object(), LLMProviderProtocol)

    def test_protocol_is_importable_from_contracts(self):
        from lia_agents_core.contracts import LLMProviderProtocol as LP
        assert LP is LLMProviderProtocol

    def test_protocol_is_importable_from_package(self):
        from lia_agents_core import LLMProviderProtocol as LP
        assert LP is LLMProviderProtocol


class TestNoShimImports:
    """Regression guard: app.shared.agents.* must not appear anywhere in the codebase."""

    def test_no_remaining_shim_imports(self):
        import pathlib
        import re

        root = pathlib.Path(__file__).parent.parent.parent

        # Pattern: actual import statements, not docstrings or string literals
        import_pattern = re.compile(
            r"^\s*(from|import)\s+app\.shared\.agents",
            re.MULTILINE,
        )

        # Files allowed to mention the old path (docstrings, test guards, comments)
        allowlist = {
            pathlib.Path(__file__).resolve(),
            (root / "libs" / "agents-core" / "lia_agents_core" / "contracts.py").resolve(),
        }

        violations = []
        for py_file in root.rglob("*.py"):
            if py_file.resolve() in allowlist:
                continue
            try:
                source = py_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if import_pattern.search(source):
                relative = py_file.relative_to(root)
                violations.append(str(relative))

        assert violations == [], (
            f"Found {len(violations)} file(s) still importing from app.shared.agents:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_shim_files_do_not_exist(self):
        import pathlib

        agents_dir = pathlib.Path(__file__).parent.parent.parent / "app" / "shared" / "agents"
        allowed = {"__init__.py", "agent_bus.py", "agent_types.py"}
        if not agents_dir.exists():
            return

        existing = {p.name for p in agents_dir.iterdir() if p.is_file() and p.suffix == ".py"}
        unexpected = existing - allowed
        assert unexpected == set(), (
            f"Shim files still present in app/shared/agents/: {unexpected}"
        )
