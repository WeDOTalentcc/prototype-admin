"""
Unit tests — LLMProviderFactory DI (Task #125).

Covers:
- ProviderContainer: lazy instantiation, get_primary, clear
- ProviderContainer: generate_with_fallback with circuit breaker and exceptions
- TenantProviderRegistry: singleton, get_container, register_container, clear
- TenantProviderRegistry: loads provider config from ToolPermissionsLoader YAML
- Backward compat: LLMProviderFactory class API unchanged
- Multi-tenant isolation: separate container instances per tenant
"""
import sys
import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.easy

# ---------------------------------------------------------------------------
# Minimal stubs to prevent deep import chains triggered by
# app.shared.providers.__init__ → ats_factory → app.core.config → lia_config
# ---------------------------------------------------------------------------

_HEAVY_STUBS = {
    "app.shared.providers.ats_factory": MagicMock(),
    "app.shared.providers.voice_provider": MagicMock(),
}
for _mod, _stub in _HEAVY_STUBS.items():
    if _mod not in sys.modules:
        sys.modules[_mod] = _stub

from app.shared.providers.llm_factory import (  # noqa: E402
    LLMProviderFactory,
    ProviderContainer,
    TenantProviderRegistry,
    get_provider_for_tenant,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_state():
    TenantProviderRegistry.reset()
    LLMProviderFactory.clear()
    # Clear provider registrations between tests to avoid cross-test pollution
    LLMProviderFactory._providers.clear()
    yield
    TenantProviderRegistry.reset()
    LLMProviderFactory.clear()
    LLMProviderFactory._providers.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_provider_class(name: str, text: str = "ok"):
    """Dynamically create a minimal provider class."""
    _name = name
    _text = text

    def _init(self, api_key=None, region=None, **kwargs):
        pass

    cls = type(f"MockProvider_{_name}", (), {
        "_provider_name": _name,
        "__init__": _init,
    })

    async def generate(self, prompt, **kwargs):
        r = MagicMock()
        r.text = _text
        return r

    async def generate_with_system(self, system, prompt, **kwargs):
        r = MagicMock()
        r.text = _text
        return r

    cls.generate = generate
    cls.generate_with_system = generate_with_system
    cls.provider_name = property(lambda self: _name)
    return cls


def _register(name: str, text: str = "ok"):
    cls = _make_provider_class(name, text)
    LLMProviderFactory.register(cls)
    return cls


# ---------------------------------------------------------------------------
# ProviderContainer
# ---------------------------------------------------------------------------

class TestProviderContainer:

    def test_get_creates_instance_lazily(self):
        _register("gpc1")
        c = ProviderContainer(tenant_id="t1", primary_provider="gpc1")
        p = c.get("gpc1")
        assert p is not None

    def test_get_caches_instance(self):
        _register("gpc_cache")
        c = ProviderContainer(tenant_id="t1", primary_provider="gpc_cache")
        p1 = c.get("gpc_cache")
        p2 = c.get("gpc_cache")
        assert p1 is p2

    def test_get_primary_returns_configured_provider(self):
        _register("claude_pc")
        c = ProviderContainer(tenant_id="t1", primary_provider="claude_pc")
        p = c.get_primary()
        assert p.provider_name == "claude_pc"

    def test_get_unknown_provider_raises(self):
        c = ProviderContainer(tenant_id="t1", primary_provider="unknown_xyz")
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            c.get("unknown_xyz")

    def test_clear_releases_instances(self):
        _register("gpc_clr")
        c = ProviderContainer(tenant_id="t1", primary_provider="gpc_clr")
        c.get("gpc_clr")
        c.clear()
        assert c._instances == {}

    def test_tenant_id_property(self):
        c = ProviderContainer(tenant_id="my_tenant")
        assert c.tenant_id == "my_tenant"

    def test_fallback_order_property_returns_copy(self):
        c = ProviderContainer(primary_provider="a", fallback_order=["a", "b"])
        fo = c.fallback_order
        fo.append("c")
        assert "c" not in c.fallback_order

    def test_primary_always_first_in_fallback_order(self):
        """Primary provider must always be the first element in fallback order."""
        c = ProviderContainer(
            primary_provider="gemini",
            fallback_order=["claude", "gemini", "openai"],
        )
        assert c.fallback_order[0] == "gemini"
        assert c.fallback_order == ["gemini", "claude", "openai"]

    def test_primary_not_duplicated_when_already_first(self):
        """Primary already first: no duplicates introduced."""
        c = ProviderContainer(
            primary_provider="gemini",
            fallback_order=["gemini", "claude", "openai"],
        )
        assert c.fallback_order.count("gemini") == 1
        assert c.fallback_order[0] == "gemini"

    def test_primary_not_in_fallback_list_is_prepended(self):
        """Primary not in fallback list at all: it is prepended."""
        c = ProviderContainer(
            primary_provider="claude",
            fallback_order=["gemini", "openai"],
        )
        assert c.fallback_order[0] == "claude"
        assert "claude" in c.fallback_order

    @pytest.mark.asyncio
    async def test_primary_first_order_used_in_generate(self):
        """When primary != fallback_order[0] in config, primary is still called first."""
        call_order = []

        for pname in ["primary_pf", "secondary_pf"]:
            cls = _make_provider_class(pname)

            async def _gen(self, prompt, _name=pname, **kwargs):
                call_order.append(_name)
                r = MagicMock()
                r.text = _name
                return r

            cls.generate = _gen
            LLMProviderFactory.register(cls)

        c = ProviderContainer(
            primary_provider="primary_pf",
            fallback_order=["secondary_pf", "primary_pf"],  # primary listed second
        )
        result = await c.generate_with_fallback("test")
        assert call_order[0] == "primary_pf"
        assert result == "primary_pf"

    def test_repr_contains_tenant_and_provider(self):
        c = ProviderContainer(tenant_id="xyz", primary_provider="claude")
        r = repr(c)
        assert "xyz" in r
        assert "claude" in r

    @pytest.mark.asyncio
    async def test_generate_with_fallback_uses_primary(self):
        _register("gen_prim", text="primary_result")
        _register("gen_fb", text="fallback_result")
        c = ProviderContainer(
            tenant_id="t1",
            primary_provider="gen_prim",
            fallback_order=["gen_prim", "gen_fb"],
        )
        result = await c.generate_with_fallback("Hello")
        assert result == "primary_result"

    @pytest.mark.asyncio
    async def test_generate_with_fallback_falls_through_on_error(self):
        fail_cls = _make_provider_class("fail_pt")

        async def _fail_generate(self, prompt, **kwargs):
            raise RuntimeError("down")

        async def _fail_generate_ws(self, s, p, **kwargs):
            raise RuntimeError("down")

        fail_cls.generate = _fail_generate
        fail_cls.generate_with_system = _fail_generate_ws
        LLMProviderFactory.register(fail_cls)

        _register("ok_pt", text="ok_fallback")

        c = ProviderContainer(
            tenant_id="t1",
            primary_provider="fail_pt",
            fallback_order=["fail_pt", "ok_pt"],
        )
        result = await c.generate_with_fallback("test")
        assert result == "ok_fallback"

    @pytest.mark.asyncio
    async def test_generate_with_fallback_all_fail_raises(self):
        fail_cls = _make_provider_class("always_fails_af")

        async def _fail(self, p, **kw):
            raise RuntimeError("dead")

        fail_cls.generate = _fail
        fail_cls.generate_with_system = _fail
        LLMProviderFactory.register(fail_cls)

        c = ProviderContainer(
            tenant_id="t1",
            primary_provider="always_fails_af",
            fallback_order=["always_fails_af"],
        )
        with pytest.raises(Exception, match="Todos os provedores|All LLM providers failed"):
            await c.generate_with_fallback("hi")

    @pytest.mark.asyncio
    async def test_generate_with_system_passes_system_prompt(self):
        received = {}
        sys_cls = _make_provider_class("sys_cap")

        async def _gen_ws(self, system, prompt, **kwargs):
            received["system"] = system
            r = MagicMock()
            r.text = "with_system"
            return r

        sys_cls.generate_with_system = _gen_ws
        LLMProviderFactory.register(sys_cls)

        c = ProviderContainer(
            tenant_id="t1",
            primary_provider="sys_cap",
            fallback_order=["sys_cap"],
        )
        result = await c.generate_with_fallback("q", system="SYS")
        assert result == "with_system"
        assert received["system"] == "SYS"


# ---------------------------------------------------------------------------
# TenantProviderRegistry
# ---------------------------------------------------------------------------

class TestTenantProviderRegistry:

    def test_singleton(self):
        a = TenantProviderRegistry.get_instance()
        b = TenantProviderRegistry.get_instance()
        assert a is b

    def test_get_container_creates_container(self):
        _register("gemini_reg")
        registry = TenantProviderRegistry.get_instance()
        c = registry.get_container("tenant_x", primary_provider="gemini_reg")
        assert c.tenant_id == "tenant_x"
        assert c.primary_provider == "gemini_reg"

    def test_get_container_caches_per_tenant(self):
        _register("gemini_cache2")
        registry = TenantProviderRegistry.get_instance()
        c1 = registry.get_container("cached_tenant", primary_provider="gemini_cache2")
        c2 = registry.get_container("cached_tenant", primary_provider="gemini_cache2")
        assert c1 is c2

    def test_get_container_different_tenants_isolated(self):
        _register("claude_iso")
        _register("gemini_iso")
        registry = TenantProviderRegistry.get_instance()
        c_a = registry.get_container("tenant_a_reg", primary_provider="claude_iso")
        c_b = registry.get_container("tenant_b_reg", primary_provider="gemini_iso")
        assert c_a is not c_b
        assert c_a.primary_provider == "claude_iso"
        assert c_b.primary_provider == "gemini_iso"

    def test_register_container_explicitly(self):
        registry = TenantProviderRegistry.get_instance()
        custom = ProviderContainer(tenant_id="custom_reg", primary_provider="gemini")
        registry.register_container("custom_reg", custom)
        retrieved = registry.get_container("custom_reg")
        assert retrieved is custom

    def test_remove_container(self):
        _register("gemini_rm")
        registry = TenantProviderRegistry.get_instance()
        registry.get_container("tenant_rm", primary_provider="gemini_rm")
        removed = registry.remove_container("tenant_rm")
        assert removed is True
        assert "tenant_rm" not in registry.list_tenants()

    def test_remove_nonexistent_returns_false(self):
        registry = TenantProviderRegistry.get_instance()
        assert registry.remove_container("does_not_exist") is False

    def test_list_tenants(self):
        _register("gemini_lt")
        registry = TenantProviderRegistry.get_instance()
        registry.get_container("ta_lt", primary_provider="gemini_lt")
        registry.get_container("tb_lt", primary_provider="gemini_lt")
        tenants = registry.list_tenants()
        assert "ta_lt" in tenants
        assert "tb_lt" in tenants

    def test_clear_removes_all_containers(self):
        _register("gemini_cl")
        registry = TenantProviderRegistry.get_instance()
        registry.get_container("t1_cl", primary_provider="gemini_cl")
        registry.clear()
        assert registry.list_tenants() == []

    def test_global_container_none_tenant(self):
        _register("gemini_gbl")
        registry = TenantProviderRegistry.get_instance()
        c = registry.get_container(None, primary_provider="gemini_gbl")
        assert c.tenant_id is None

    def test_repr_contains_tenants(self):
        _register("gemini_rpr")
        registry = TenantProviderRegistry.get_instance()
        registry.get_container("repr_tenant", primary_provider="gemini_rpr")
        r = repr(registry)
        assert "repr_tenant" in r

    def test_loads_provider_from_permissions_yaml(self):
        """TenantProviderRegistry picks up per-tenant llm_provider from YAML."""
        import tempfile
        from pathlib import Path
        from app.tools.tool_permissions_loader import ToolPermissionsLoader

        yaml_content = """
version: "1.0"
global:
  scopes: {}
  llm_provider: gemini
  llm_fallback_order: [gemini]
tenants:
  yaml_tenant_t125:
    llm_provider: claude
    llm_fallback_order: [claude, gemini]
"""
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        )
        f.write(yaml_content)
        f.flush()
        f.close()
        path = Path(f.name)

        ToolPermissionsLoader.invalidate_cache()
        ToolPermissionsLoader.get_instance(path)

        registry = TenantProviderRegistry.get_instance()
        c = registry.get_container("yaml_tenant_t125")
        assert c.primary_provider == "claude"
        assert c.fallback_order == ["claude", "gemini"]

        ToolPermissionsLoader.invalidate_cache()


# ---------------------------------------------------------------------------
# Multi-tenant isolation contract tests
# ---------------------------------------------------------------------------

class TestMultiTenantProviderIsolation:

    def test_provider_instances_are_separate_per_tenant(self):
        _register("gemini_mti")
        registry = TenantProviderRegistry.get_instance()
        c1 = registry.get_container("iso_t1", primary_provider="gemini_mti")
        c2 = registry.get_container("iso_t2", primary_provider="gemini_mti")
        p1 = c1.get("gemini_mti")
        p2 = c2.get("gemini_mti")
        assert p1 is not p2

    def test_clear_one_does_not_affect_other(self):
        _register("gemini_mti2")
        registry = TenantProviderRegistry.get_instance()
        c1 = registry.get_container("tenant_x1_mti", primary_provider="gemini_mti2")
        c2 = registry.get_container("tenant_x2_mti", primary_provider="gemini_mti2")
        c1.get("gemini_mti2")
        c2.get("gemini_mti2")
        c1.clear()
        assert c2._instances != {}

    def test_fallback_order_not_shared_between_tenants(self):
        registry = TenantProviderRegistry.get_instance()
        c_a = registry.get_container(
            "fa_tenant_mti", primary_provider="gemini",
            fallback_order=["gemini", "claude"]
        )
        c_b = registry.get_container(
            "fb_tenant_mti", primary_provider="claude",
            fallback_order=["claude", "openai"]
        )
        assert c_a.fallback_order == ["gemini", "claude"]
        assert c_b.fallback_order == ["claude", "openai"]


# ---------------------------------------------------------------------------
# LLMProviderFactory backward compatibility
# ---------------------------------------------------------------------------

class TestLLMProviderFactoryBackwardCompat:

    def test_register_and_get(self):
        cls = _make_provider_class("test_prov_bc")
        LLMProviderFactory.register(cls)
        p = LLMProviderFactory.get("test_prov_bc")
        assert p is not None

    def test_available_providers(self):
        cls = _make_provider_class("prov_avail_bc")
        LLMProviderFactory.register(cls)
        assert "prov_avail_bc" in LLMProviderFactory.available_providers()

    def test_get_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            LLMProviderFactory.get("nonexistent_xyz_bc")

    def test_clear_removes_instances(self):
        cls = _make_provider_class("cl_prov_bc")
        LLMProviderFactory.register(cls)
        LLMProviderFactory.get("cl_prov_bc")
        LLMProviderFactory.clear()
        assert LLMProviderFactory._instances == {}

    def test_get_provider_for_tenant_shortcut(self):
        cls = _make_provider_class("gemini_sc")
        LLMProviderFactory.register(cls)
        container = get_provider_for_tenant("shortcut_tenant_bc", primary_provider="gemini_sc")
        assert container.tenant_id == "shortcut_tenant_bc"
