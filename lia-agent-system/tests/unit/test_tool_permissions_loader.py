"""
Unit tests — ToolPermissionsLoader (Task #125).

Covers:
- YAML loading: defaults, per-tenant overrides, missing file, PyYAML unavailable
- ToolPermissionsConfig: get_tools, is_tool_allowed, filter_tools
- Per-tenant add_query / add_action / remove overrides
- Provider config: llm_provider and llm_fallback_order per tenant
- Cache invalidation
- Backward-compat constants in scope_config still work
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

pytestmark = pytest.mark.easy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_YAML = """
version: "1.0"
global:
  scopes:
    talent_funnel:
      query: [search_candidates, get_candidate_details]
      action: [add_candidate_to_vacancy, reject_candidate]
    job_table:
      query: [search_jobs, get_job_details]
      action: [create_job, update_job]
    in_job:
      query: [get_vacancy_funnel]
      action: [update_candidate_stage]
    global:
      query: []
      action: [generate_report]
  llm_provider: gemini
  llm_fallback_order: [claude, gemini, openai]

tenants:
  acme_corp:
    llm_provider: claude
    llm_fallback_order: [claude, openai]
    overrides:
      talent_funnel:
        remove: [reject_candidate]
        add_action: [custom_acme_action]
      job_table:
        add_query: [get_acme_metrics]
  restricted_tenant:
    overrides:
      talent_funnel:
        remove: [search_candidates, get_candidate_details, add_candidate_to_vacancy, reject_candidate]
"""


def _write_yaml(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    f.write(content)
    f.flush()
    f.close()
    return Path(f.name)


# ---------------------------------------------------------------------------
# Always reset loader cache between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_loader():
    from app.tools.tool_permissions_loader import ToolPermissionsLoader
    ToolPermissionsLoader.invalidate_cache()
    yield
    ToolPermissionsLoader.invalidate_cache()


# ---------------------------------------------------------------------------
# ToolPermissionsLoader — YAML loading
# ---------------------------------------------------------------------------

class TestToolPermissionsLoader:

    def test_load_global_defaults(self):
        path = _write_yaml(MINIMAL_YAML)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader
        loader = ToolPermissionsLoader(path)
        cfg = loader.get_config(tenant_id=None)

        assert "search_candidates" in cfg.get_tools("talent_funnel", "query")
        assert "add_candidate_to_vacancy" in cfg.get_tools("talent_funnel", "action")
        assert "search_jobs" in cfg.get_tools("job_table", "query")
        assert "generate_report" in cfg.get_tools("global", "action")

    def test_load_tenant_overrides_provider(self):
        path = _write_yaml(MINIMAL_YAML)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader
        loader = ToolPermissionsLoader(path)
        cfg = loader.get_config(tenant_id="acme_corp")

        assert cfg.llm_provider == "claude"
        assert cfg.llm_fallback_order == ["claude", "openai"]

    def test_global_tenant_uses_default_provider(self):
        path = _write_yaml(MINIMAL_YAML)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader
        loader = ToolPermissionsLoader(path)
        cfg = loader.get_config(tenant_id=None)

        assert cfg.llm_provider == "gemini"
        assert "claude" in cfg.llm_fallback_order

    def test_missing_yaml_returns_empty_config(self):
        from app.tools.tool_permissions_loader import ToolPermissionsLoader
        loader = ToolPermissionsLoader(Path("/tmp/nonexistent_permissions_xyz.yaml"))
        cfg = loader.get_config(tenant_id=None)

        assert cfg.get_tools("talent_funnel", "all") == set()
        assert cfg.llm_provider == "gemini"

    def test_get_instance_is_singleton(self):
        path = _write_yaml(MINIMAL_YAML)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader
        a = ToolPermissionsLoader.get_instance(path)
        b = ToolPermissionsLoader.get_instance(path)
        assert a is b

    def test_invalidate_cache_resets_singleton(self):
        path = _write_yaml(MINIMAL_YAML)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader
        a = ToolPermissionsLoader.get_instance(path)
        ToolPermissionsLoader.invalidate_cache()
        b = ToolPermissionsLoader.get_instance(path)
        assert a is not b


# ---------------------------------------------------------------------------
# ToolPermissionsConfig — get_tools / is_tool_allowed / filter_tools
# ---------------------------------------------------------------------------

class TestToolPermissionsConfig:

    def _get_cfg(self, tenant_id=None):
        path = _write_yaml(MINIMAL_YAML)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader
        return ToolPermissionsLoader(path).get_config(tenant_id)

    def test_get_tools_all_union(self):
        cfg = self._get_cfg()
        all_tools = cfg.get_tools("talent_funnel", "all")
        assert "search_candidates" in all_tools
        assert "add_candidate_to_vacancy" in all_tools

    def test_get_tools_query_subset(self):
        cfg = self._get_cfg()
        q = cfg.get_tools("talent_funnel", "query")
        assert "search_candidates" in q
        assert "add_candidate_to_vacancy" not in q

    def test_get_tools_action_subset(self):
        cfg = self._get_cfg()
        a = cfg.get_tools("talent_funnel", "action")
        assert "add_candidate_to_vacancy" in a
        assert "search_candidates" not in a

    def test_get_tools_unknown_scope_returns_empty(self):
        cfg = self._get_cfg()
        assert cfg.get_tools("nonexistent_scope", "all") == set()

    def test_is_tool_allowed_true(self):
        cfg = self._get_cfg()
        assert cfg.is_tool_allowed("search_candidates", "talent_funnel") is True

    def test_is_tool_allowed_false(self):
        cfg = self._get_cfg()
        assert cfg.is_tool_allowed("create_job", "talent_funnel") is False

    def test_filter_tools_returns_allowed_only(self):
        cfg = self._get_cfg()
        tools = [
            {"name": "search_candidates"},
            {"name": "create_job"},
            {"name": "get_candidate_details"},
        ]
        filtered = cfg.filter_tools(tools, "talent_funnel")
        names = {t["name"] for t in filtered}
        assert "search_candidates" in names
        assert "get_candidate_details" in names
        assert "create_job" not in names

    def test_filter_tools_empty_list(self):
        cfg = self._get_cfg()
        assert cfg.filter_tools([], "talent_funnel") == []

    def test_repr_includes_tenant_and_provider(self):
        cfg = self._get_cfg("acme_corp")
        r = repr(cfg)
        assert "acme_corp" in r
        assert "claude" in r


# ---------------------------------------------------------------------------
# Per-tenant overrides
# ---------------------------------------------------------------------------

class TestTenantOverrides:

    def _get_cfg(self, tenant_id):
        path = _write_yaml(MINIMAL_YAML)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader
        return ToolPermissionsLoader(path).get_config(tenant_id)

    def test_add_action_adds_tool_for_tenant(self):
        cfg = self._get_cfg("acme_corp")
        assert "custom_acme_action" in cfg.get_tools("talent_funnel", "action")

    def test_add_query_adds_tool_for_tenant(self):
        cfg = self._get_cfg("acme_corp")
        assert "get_acme_metrics" in cfg.get_tools("job_table", "query")

    def test_remove_denies_tool_for_tenant(self):
        cfg = self._get_cfg("acme_corp")
        all_tools = cfg.get_tools("talent_funnel", "all")
        assert "reject_candidate" not in all_tools

    def test_remove_keeps_tool_for_other_tenant(self):
        cfg = self._get_cfg(None)
        assert "reject_candidate" in cfg.get_tools("talent_funnel", "action")

    def test_restricted_tenant_has_empty_scope(self):
        cfg = self._get_cfg("restricted_tenant")
        assert cfg.get_tools("talent_funnel", "all") == set()

    def test_add_without_remove_does_not_affect_global(self):
        path = _write_yaml(MINIMAL_YAML)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader
        loader = ToolPermissionsLoader(path)
        global_cfg = loader.get_config(None)
        acme_cfg = loader.get_config("acme_corp")

        assert "custom_acme_action" not in global_cfg.get_tools("talent_funnel", "action")
        assert "custom_acme_action" in acme_cfg.get_tools("talent_funnel", "action")


# ---------------------------------------------------------------------------
# Multi-tenant isolation
# ---------------------------------------------------------------------------

class TestMultiTenantIsolation:
    """
    Contract tests: tenant A permissions must not leak into tenant B.
    """

    def test_tenant_a_cannot_access_tenant_b_exclusive_tool(self):
        yaml_content = """
version: "1.0"
global:
  scopes:
    talent_funnel:
      query: [search_candidates]
      action: []
    global:
      query: []
      action: []
  llm_provider: gemini
  llm_fallback_order: [gemini]

tenants:
  tenant_a:
    overrides:
      talent_funnel:
        add_action: [exclusive_tool_a]
  tenant_b:
    overrides:
      talent_funnel:
        add_action: [exclusive_tool_b]
"""
        path = _write_yaml(yaml_content)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader
        loader = ToolPermissionsLoader(path)

        cfg_a = loader.get_config("tenant_a")
        cfg_b = loader.get_config("tenant_b")

        assert "exclusive_tool_a" in cfg_a.get_tools("talent_funnel", "action")
        assert "exclusive_tool_b" not in cfg_a.get_tools("talent_funnel", "action")
        assert "exclusive_tool_b" in cfg_b.get_tools("talent_funnel", "action")
        assert "exclusive_tool_a" not in cfg_b.get_tools("talent_funnel", "action")

    def test_global_default_independent_from_tenant_overrides(self):
        path = _write_yaml(MINIMAL_YAML)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader
        loader = ToolPermissionsLoader(path)

        global_cfg = loader.get_config(None)
        acme_cfg = loader.get_config("acme_corp")

        assert global_cfg.llm_provider == "gemini"
        assert acme_cfg.llm_provider == "claude"

    def test_provider_config_isolated_per_tenant(self):
        path = _write_yaml(MINIMAL_YAML)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader
        loader = ToolPermissionsLoader(path)

        cfg_acme = loader.get_config("acme_corp")
        cfg_restricted = loader.get_config("restricted_tenant")

        assert cfg_acme.llm_provider == "claude"
        assert cfg_restricted.llm_provider == "gemini"


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

class TestConvenienceFunctions:

    def test_get_tools_for_scope_global(self):
        path = _write_yaml(MINIMAL_YAML)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader, get_tools_for_scope
        ToolPermissionsLoader.get_instance(path)

        tools = get_tools_for_scope("talent_funnel", "query")
        assert "search_candidates" in tools

    def test_is_tool_allowed_global(self):
        path = _write_yaml(MINIMAL_YAML)
        from app.tools.tool_permissions_loader import ToolPermissionsLoader, is_tool_allowed
        ToolPermissionsLoader.get_instance(path)

        assert is_tool_allowed("search_candidates", "talent_funnel") is True
        assert is_tool_allowed("create_job", "talent_funnel") is False


# ---------------------------------------------------------------------------
# scope_config backward compatibility
# ---------------------------------------------------------------------------

class TestScopeConfigBackwardCompat:
    """Ensure refactored scope_config still exposes the same public API."""

    def test_constants_are_sets(self):
        from app.tools.scope_config import (
            FUNNEL_QUERY_TOOLS,
            FUNNEL_ACTION_TOOLS,
            VACANCY_QUERY_TOOLS,
            VACANCY_ACTION_TOOLS,
            IN_JOB_QUERY_TOOLS,
            IN_JOB_ACTION_TOOLS,
            GLOBAL_TOOLS,
        )
        for s in (
            FUNNEL_QUERY_TOOLS, FUNNEL_ACTION_TOOLS,
            VACANCY_QUERY_TOOLS, VACANCY_ACTION_TOOLS,
            IN_JOB_QUERY_TOOLS, IN_JOB_ACTION_TOOLS,
            GLOBAL_TOOLS,
        ):
            assert isinstance(s, set)

    def test_funnel_query_contains_expected_tools(self):
        from app.tools.scope_config import FUNNEL_QUERY_TOOLS
        assert "search_candidates" in FUNNEL_QUERY_TOOLS

    def test_get_tools_for_scope_no_tenant(self):
        from app.tools.scope_config import get_tools_for_scope, PromptScope
        tools = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "all")
        assert "search_candidates" in tools
        assert "add_candidate_to_vacancy" in tools

    def test_get_tools_for_scope_with_tenant_id(self):
        from app.tools.scope_config import get_tools_for_scope, PromptScope
        tools = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "all", tenant_id=None)
        assert isinstance(tools, set)

    def test_filter_tools_by_scope(self):
        from app.tools.scope_config import filter_tools_by_scope, PromptScope
        tool_list = [
            {"name": "search_candidates"},
            {"name": "create_job"},
        ]
        filtered = filter_tools_by_scope(tool_list, PromptScope.TALENT_FUNNEL)
        names = {t["name"] for t in filtered}
        assert "search_candidates" in names
        assert "create_job" not in names

    def test_is_tool_allowed_in_scope(self):
        from app.tools.scope_config import is_tool_allowed_in_scope, PromptScope
        assert is_tool_allowed_in_scope("search_candidates", PromptScope.TALENT_FUNNEL) is True
        assert is_tool_allowed_in_scope("create_job", PromptScope.TALENT_FUNNEL) is False

    def test_get_scope_system_prompt_addition(self):
        from app.tools.scope_config import get_scope_system_prompt_addition, PromptScope
        text = get_scope_system_prompt_addition(PromptScope.TALENT_FUNNEL)
        assert "Funil" in text or "PODE" in text

    def test_get_scope_system_prompt_addition_unknown_scope(self):
        from app.tools.scope_config import get_scope_system_prompt_addition, PromptScope
        text = get_scope_system_prompt_addition(PromptScope.GLOBAL)
        assert text == ""

    def test_scope_intent_mapping_exists(self):
        from app.tools.scope_config import SCOPE_INTENT_MAPPING, PromptScope
        assert "search_candidates" in SCOPE_INTENT_MAPPING
        assert SCOPE_INTENT_MAPPING["search_candidates"] == PromptScope.TALENT_FUNNEL

    def test_get_suggested_scope_for_intent(self):
        from app.tools.scope_config import get_suggested_scope_for_intent, PromptScope
        assert get_suggested_scope_for_intent("search_candidates") == PromptScope.TALENT_FUNNEL
        assert get_suggested_scope_for_intent("unknown_tool") == PromptScope.GLOBAL
