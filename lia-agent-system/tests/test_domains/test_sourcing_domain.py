"""Tests for SourcingDomain — canonical wiring, action↔tool map, executor signature.

Covers the 3 gaps fixed in task #579:
- Gap A: `_ACTION_TOOL_MAP` references real tool ids registered in SOURCING_TOOLS.
- Gap B: 4 pipeline tools are reachable via DomainAction + capabilities keywords.
- Gap C: `execute_sourcing_tool` signature is `tenant_id: str` (not DomainContext).
"""
from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import pytest


# --- Gap A: _ACTION_TOOL_MAP integrity --------------------------------------

class TestActionToolMap:
    def test_all_mapped_tools_exist_in_registry(self):
        from app.domains.sourcing.domain import _ACTION_TOOL_MAP
        from app.domains.sourcing.tools import SOURCING_TOOLS
        tool_ids = {t["tool_id"] for t in SOURCING_TOOLS}
        unknown = {a: t for a, t in _ACTION_TOOL_MAP.items() if t not in tool_ids}
        assert not unknown, f"Action→tool entries point to non-existent tools: {unknown}"

    def test_search_candidates_maps_to_sourcing_prefixed_tool(self):
        from app.domains.sourcing.domain import _ACTION_TOOL_MAP
        assert _ACTION_TOOL_MAP["search_candidates"] == "sourcing_search_candidates"

    def test_rank_candidates_maps_to_sourcing_prefixed_tool(self):
        from app.domains.sourcing.domain import _ACTION_TOOL_MAP
        assert _ACTION_TOOL_MAP["rank_candidates"] == "sourcing_rank_candidates"

    def test_no_legacy_unprefixed_targets(self):
        """Old map referenced 'pearch_search', 'boolean_search', 'search_analytics' etc."""
        from app.domains.sourcing.domain import _ACTION_TOOL_MAP
        for tool_id in _ACTION_TOOL_MAP.values():
            assert tool_id.startswith("sourcing_"), (
                f"Tool id '{tool_id}' is not prefixed with 'sourcing_' — legacy entry"
            )


# --- Gap B: 4 pipeline actions wired through DomainAction + map -------------

PIPELINE_ACTIONS = [
    "update_candidate_stage",
    "reject_candidate",
    "shortlist_candidate",
    "add_candidate_to_vacancy",
]


class TestPipelineActionsWiring:
    def test_all_pipeline_actions_present_in_actions_list(self):
        from app.domains.sourcing.actions import SOURCING_ACTIONS
        action_ids = {a.action_id for a in SOURCING_ACTIONS}
        for aid in PIPELINE_ACTIONS:
            assert aid in action_ids, f"Pipeline action '{aid}' missing in SOURCING_ACTIONS"

    def test_sourcing_actions_total_count(self):
        from app.domains.sourcing.actions import SOURCING_ACTIONS
        assert len(SOURCING_ACTIONS) == 34

    @pytest.mark.parametrize("action_id", PIPELINE_ACTIONS)
    def test_pipeline_action_mapped_to_real_tool(self, action_id):
        from app.domains.sourcing.domain import _ACTION_TOOL_MAP
        from app.domains.sourcing.tools import SOURCING_TOOLS
        tool_ids = {t["tool_id"] for t in SOURCING_TOOLS}
        assert action_id in _ACTION_TOOL_MAP
        assert _ACTION_TOOL_MAP[action_id] in tool_ids

    def test_capabilities_yaml_contains_pipeline_keywords(self):
        from pathlib import Path

        import yaml
        cfg_path = (
            Path(__file__).resolve().parents[2]
            / "app" / "domains" / "sourcing" / "config" / "capabilities.yaml"
        )
        data = yaml.safe_load(cfg_path.read_text())
        targets = set(data.get("intent_keywords", {}).values())
        for aid in PIPELINE_ACTIONS:
            assert aid in targets, f"No keyword in capabilities.yaml routes to '{aid}'"


# --- Gap C: execute_sourcing_tool signature & behavior ----------------------

class TestExecuteSourcingToolSignature:
    def test_signature_uses_tenant_id_str(self):
        from app.domains.sourcing.tools import execute_sourcing_tool
        sig = inspect.signature(execute_sourcing_tool)
        params = sig.parameters
        assert list(params.keys()) == ["tool_id", "parameters", "tenant_id", "user_id"]
        assert params["tenant_id"].annotation is str

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        from app.domains.sourcing.tools import execute_sourcing_tool
        result = await execute_sourcing_tool("nonexistent", {}, "tenant-1")
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_tenant_id_and_context_are_forwarded(self):
        """Handler must receive both `_tenant_id` (str) and a `_context` object
        whose `company_id` matches tenant_id — required by canonical handlers
        in cv_screening.tools.candidate_tools (`_extract_context`)."""
        from app.domains.sourcing.tools import execute_sourcing_tool

        seen: dict = {}

        async def fake_handler(**kwargs):
            seen.update(kwargs)
            return {"ok": True}

        with patch("importlib.import_module") as mock_import:
            mod = MagicMock()
            mod.search_candidates = fake_handler
            mock_import.return_value = mod
            result = await execute_sourcing_tool(
                "sourcing_search_candidates",
                {"limit": 5},
                "tenant-xyz",
                user_id="user-42",
            )

        assert result["status"] == "success"
        assert seen.get("_tenant_id") == "tenant-xyz"
        assert seen.get("limit") == 5
        ctx = seen.get("_context")
        assert ctx is not None, "Handler must receive _context for canonical scoping"
        assert ctx.company_id == "tenant-xyz"
        assert ctx.user_id == "user-42"

    @pytest.mark.asyncio
    async def test_context_defaults_user_id_to_system(self):
        from app.domains.sourcing.tools import execute_sourcing_tool

        seen: dict = {}

        async def fake_handler(**kwargs):
            seen.update(kwargs)
            return {"ok": True}

        with patch("importlib.import_module") as mock_import:
            mod = MagicMock()
            mod.search_candidates = fake_handler
            mock_import.return_value = mod
            await execute_sourcing_tool(
                "sourcing_search_candidates", {}, "tenant-z"
            )

        ctx = seen.get("_context")
        assert ctx is not None
        assert ctx.user_id == "system"
        assert ctx.company_id == "tenant-z"


# --- Smoke: 4 pipeline tools resolve & invoke without ImportError/TypeError -

PIPELINE_TOOL_IDS = [
    "sourcing_update_candidate_stage",
    "sourcing_reject_candidate",
    "sourcing_shortlist_candidate",
    "sourcing_add_candidate_to_vacancy",
]


class TestPipelineToolsSmoke:
    @pytest.mark.parametrize("tool_id", PIPELINE_TOOL_IDS)
    @pytest.mark.asyncio
    async def test_pipeline_tool_invokes_handler(self, tool_id):
        from app.domains.sourcing.tools import (
            _get_tool_by_id,
            execute_sourcing_tool,
        )

        tool = _get_tool_by_id(tool_id)
        assert tool is not None, f"Pipeline tool '{tool_id}' not registered"
        func_name = tool["handler"].rsplit(".", 1)[1]

        async def fake_handler(**kwargs):
            return {"success": True, "received": list(kwargs.keys())}

        with patch("importlib.import_module") as mock_import:
            mod = MagicMock()
            setattr(mod, func_name, fake_handler)
            mock_import.return_value = mod
            result = await execute_sourcing_tool(
                tool_id,
                {"candidate_id": "c-1", "job_id": "j-1", "target_stage": "Triagem", "reason": "x"},
                "tenant-1",
            )

        assert result["status"] == "success"
        assert result["result"]["success"] is True


# --- Routing: "mover candidato X" → update_candidate_stage ------------------

class TestIntentRouting:
    @pytest.mark.asyncio
    async def test_mover_candidato_routes_to_update_candidate_stage(self):
        from app.domains.base import DomainContext
        from app.domains.sourcing.domain import SourcingDomain

        domain = SourcingDomain()
        ctx = DomainContext(
            domain_id="sourcing",
            user_id="user-1",
            session_id="sess-1",
            tenant_id="tenant-1",
        )
        result = await domain.process_intent("mover candidato para Entrevista", ctx)
        assert result.action_id == "update_candidate_stage"
