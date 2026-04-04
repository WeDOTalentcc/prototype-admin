"""
Unit tests — GlobalToolRegistry scope filtering (Task #125).

Covers:
- list_tools_for_scope: only returns tools allowed by declarative YAML
- get_tool_in_scope: cross-domain + scope checks combined
- Tenant isolation: different tenants see different scoped tools
- Fallback when ToolPermissionsLoader fails

Note: Uses sys.modules stubs to avoid triggering app.core.config
import chain (pre-existing env issue with USE_LANGGRAPH_NATIVE).
"""
import sys
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

pytestmark = pytest.mark.easy


# ---------------------------------------------------------------------------
# Minimal stubs to prevent deep import chains
# ---------------------------------------------------------------------------

def _stub_heavy_modules():
    stubs = {
        "app.shared.providers.ats_factory": MagicMock(),
        "app.shared.providers.voice_provider": MagicMock(),
        "app.services": MagicMock(),
        "app.services.ats_clients": MagicMock(),
        "app.services.ats_clients.base": MagicMock(),
        "app.core": MagicMock(),
        "app.core.config": MagicMock(),
        "lia_config": MagicMock(),
        "lia_config.config": MagicMock(),
    }
    for mod, stub in stubs.items():
        if mod not in sys.modules:
            sys.modules[mod] = stub


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_base_tool(name: str) -> MagicMock:
    t = MagicMock()
    t.name = name
    t.description = f"{name} description"
    return t


SCOPE_YAML = """
version: "1.0"
global:
  scopes:
    talent_funnel:
      query: [search_candidates, get_candidate_details]
      action: [add_candidate_to_vacancy]
    job_table:
      query: [search_jobs]
      action: [create_job]
    global:
      query: []
      action: [generate_report]
  llm_provider: gemini
  llm_fallback_order: [gemini]

tenants:
  limited_tenant:
    overrides:
      talent_funnel:
        remove: [search_candidates]
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_all():
    _stub_heavy_modules()

    from app.shared.global_tool_registry import GlobalToolRegistry
    from app.tools.tool_permissions_loader import ToolPermissionsLoader

    GlobalToolRegistry._instance = None
    ToolPermissionsLoader.invalidate_cache()
    yield
    GlobalToolRegistry._instance = None
    ToolPermissionsLoader.invalidate_cache()


@pytest.fixture
def permissions_path():
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    f.write(SCOPE_YAML)
    f.flush()
    f.close()
    return Path(f.name)


@pytest.fixture
def registry(permissions_path):
    from app.shared.global_tool_registry import GlobalToolRegistry, ToolPermission
    from app.tools.tool_permissions_loader import ToolPermissionsLoader

    ToolPermissionsLoader.get_instance(permissions_path)

    reg = GlobalToolRegistry.get_instance()
    reg.register(_make_base_tool("search_candidates"), "candidates", ToolPermission.READ_ONLY)
    reg.register(_make_base_tool("get_candidate_details"), "candidates", ToolPermission.READ_ONLY)
    reg.register(
        _make_base_tool("add_candidate_to_vacancy"), "candidates", ToolPermission.READ_WRITE
    )
    reg.register(_make_base_tool("create_job"), "jobs", ToolPermission.READ_WRITE)
    reg.register(_make_base_tool("search_jobs"), "jobs", ToolPermission.READ_ONLY)
    reg.register(_make_base_tool("generate_report"), "reports", ToolPermission.READ_ONLY)
    return reg


# ---------------------------------------------------------------------------
# list_tools_for_scope
# ---------------------------------------------------------------------------

class TestListToolsForScope:

    def test_returns_only_scope_allowed_tools(self, registry):
        from app.shared.global_tool_registry import ToolPermission
        tools = registry.list_tools_for_scope(
            requesting_domain="candidates",
            scope="talent_funnel",
            tenant_id=None,
            max_permission=ToolPermission.READ_ONLY,
        )
        names = {t.name for t in tools}
        assert "search_candidates" in names
        assert "get_candidate_details" in names
        assert "create_job" not in names

    def test_out_of_scope_tool_excluded(self, registry):
        from app.shared.global_tool_registry import ToolPermission
        tools = registry.list_tools_for_scope(
            requesting_domain="jobs",
            scope="talent_funnel",
            tenant_id=None,
            max_permission=ToolPermission.ADMIN,
        )
        names = {t.name for t in tools}
        assert "create_job" not in names

    def test_tenant_override_removes_tool(self, registry):
        from app.shared.global_tool_registry import ToolPermission
        tools = registry.list_tools_for_scope(
            requesting_domain="candidates",
            scope="talent_funnel",
            tenant_id="limited_tenant",
            max_permission=ToolPermission.READ_ONLY,
        )
        names = {t.name for t in tools}
        assert "search_candidates" not in names
        assert "get_candidate_details" in names

    def test_global_tenant_sees_all_defaults(self, registry):
        from app.shared.global_tool_registry import ToolPermission
        tools = registry.list_tools_for_scope(
            requesting_domain="candidates",
            scope="talent_funnel",
            tenant_id=None,
            max_permission=ToolPermission.READ_ONLY,
        )
        names = {t.name for t in tools}
        assert "search_candidates" in names

    def test_cross_domain_read_only_permission_enforced(self, registry):
        """Requesting from 'jobs' domain with READ_ONLY blocks READ_WRITE 'candidates' tools."""
        from app.shared.global_tool_registry import ToolPermission
        tools = registry.list_tools_for_scope(
            requesting_domain="jobs",
            scope="talent_funnel",
            tenant_id=None,
            max_permission=ToolPermission.READ_ONLY,
        )
        names = {t.name for t in tools}
        # add_candidate_to_vacancy is READ_WRITE, cross-domain with READ_ONLY → blocked
        assert "add_candidate_to_vacancy" not in names
        # search_candidates is READ_ONLY so cross-domain access is allowed
        assert "search_candidates" in names

    def test_cross_domain_with_elevated_permission(self, registry):
        """Requesting from 'jobs' domain with READ_WRITE allows READ_WRITE 'candidates' tools."""
        from app.shared.global_tool_registry import ToolPermission
        tools = registry.list_tools_for_scope(
            requesting_domain="jobs",
            scope="talent_funnel",
            tenant_id=None,
            max_permission=ToolPermission.READ_WRITE,
        )
        names = {t.name for t in tools}
        assert "add_candidate_to_vacancy" in names


# ---------------------------------------------------------------------------
# get_tool_in_scope
# ---------------------------------------------------------------------------

class TestGetToolInScope:

    def test_allowed_tool_returns_tool(self, registry):
        tool = registry.get_tool_in_scope(
            tool_name="search_candidates",
            requesting_domain="candidates",
            scope="talent_funnel",
            tenant_id=None,
        )
        assert tool is not None
        assert tool.name == "search_candidates"

    def test_out_of_scope_returns_none(self, registry):
        tool = registry.get_tool_in_scope(
            tool_name="create_job",
            requesting_domain="jobs",
            scope="talent_funnel",
            tenant_id=None,
        )
        assert tool is None

    def test_tenant_restricted_tool_returns_none(self, registry):
        tool = registry.get_tool_in_scope(
            tool_name="search_candidates",
            requesting_domain="candidates",
            scope="talent_funnel",
            tenant_id="limited_tenant",
        )
        assert tool is None

    def test_cross_domain_read_only_allowed(self, registry):
        tool = registry.get_tool_in_scope(
            tool_name="search_candidates",
            requesting_domain="jobs",
            scope="talent_funnel",
            tenant_id=None,
        )
        assert tool is not None

    def test_unknown_tool_returns_none(self, registry):
        tool = registry.get_tool_in_scope(
            tool_name="totally_unknown_xyz",
            requesting_domain="candidates",
            scope="talent_funnel",
            tenant_id=None,
        )
        assert tool is None


# ---------------------------------------------------------------------------
# Fallback when permissions loader fails
# ---------------------------------------------------------------------------

class TestScopeFilterFallback:

    def test_fails_closed_on_loader_error_list_tools(self):
        """SECURITY: list_tools_for_scope returns empty list when permissions fail to load."""
        from app.shared.global_tool_registry import GlobalToolRegistry, ToolPermission
        from app.tools.tool_permissions_loader import ToolPermissionsLoader

        ToolPermissionsLoader.invalidate_cache()
        reg = GlobalToolRegistry.get_instance()
        reg.register(_make_base_tool("some_tool_fc"), "domain_a", ToolPermission.READ_ONLY)

        with patch(
            "app.tools.tool_permissions_loader.get_tools_for_scope",
            side_effect=RuntimeError("yaml unavailable"),
        ):
            tools = reg.list_tools_for_scope(
                requesting_domain="domain_a",
                scope="talent_funnel",
                tenant_id=None,
            )
        # Fail-closed: no tools should be accessible when policy cannot be evaluated
        assert tools == []

    def test_fails_closed_on_loader_error_get_tool_in_scope(self):
        """SECURITY: get_tool_in_scope returns None when permissions fail to load."""
        from app.shared.global_tool_registry import GlobalToolRegistry, ToolPermission
        from app.tools.tool_permissions_loader import ToolPermissionsLoader

        ToolPermissionsLoader.invalidate_cache()
        reg = GlobalToolRegistry.get_instance()
        reg.register(_make_base_tool("protected_tool_fc"), "domain_b", ToolPermission.READ_ONLY)

        with patch(
            "app.tools.tool_permissions_loader.is_tool_allowed",
            side_effect=RuntimeError("yaml unavailable"),
        ):
            result = reg.get_tool_in_scope(
                tool_name="protected_tool_fc",
                requesting_domain="domain_b",
                scope="talent_funnel",
                tenant_id=None,
            )
        assert result is None
