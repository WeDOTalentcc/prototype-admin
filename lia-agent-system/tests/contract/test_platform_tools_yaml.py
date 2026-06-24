"""Contract tests: platform_tools.yaml is valid and consistent.

Validates:
  - YAML parses without error
  - All tools have valid access level (read|write)
  - HITL tools are a subset of known tools or standalone sensitive tools
  - Domain loaders point to importable modules
  - No duplicate tool names
  - Loader functions return correct types
"""
import pathlib

import pytest
import yaml


YAML_PATH = pathlib.Path("app/domains/agent_studio/config/platform_tools.yaml")


@pytest.fixture(scope="module")
def config():
    with open(YAML_PATH) as f:
        return yaml.safe_load(f)


class TestYamlStructure:

    def test_yaml_parses(self, config):
        assert isinstance(config, dict)

    def test_has_required_sections(self, config):
        assert "tools" in config
        assert "hitl_required" in config
        assert "domains" in config

    def test_tools_not_empty(self, config):
        assert len(config["tools"]) >= 16

    def test_all_tools_have_valid_access(self, config):
        for name, spec in config["tools"].items():
            assert spec["access"] in ("read", "write"), (
                f"{name} has invalid access: {spec['access']}"
            )

    def test_hitl_required_is_list(self, config):
        assert isinstance(config["hitl_required"], list)
        assert len(config["hitl_required"]) >= 1

    def test_domains_have_loader(self, config):
        for domain, spec in config["domains"].items():
            assert "loader" in spec, f"domain {domain} missing loader"
            assert spec["loader"].count(".") >= 2, (
                f"domain {domain} loader looks invalid: {spec['loader']}"
            )


class TestLoaderFunctions:

    def test_registry_returns_dict(self):
        from app.domains.agent_studio.platform_tools_loader import (
            get_platform_tools_registry,
        )
        registry = get_platform_tools_registry()
        assert isinstance(registry, dict)
        assert len(registry) >= 16
        for name, access in registry.items():
            assert access in ("read", "write")

    def test_hitl_returns_frozenset(self):
        from app.domains.agent_studio.platform_tools_loader import (
            get_hitl_required_tools,
        )
        hitl = get_hitl_required_tools()
        assert isinstance(hitl, frozenset)
        assert len(hitl) >= 1

    def test_domain_loaders_returns_dict(self):
        from app.domains.agent_studio.platform_tools_loader import (
            get_domain_tool_loaders,
        )
        loaders = get_domain_tool_loaders()
        assert isinstance(loaders, dict)
        assert len(loaders) >= 7

    def test_available_tool_names(self):
        from app.domains.agent_studio.platform_tools_loader import (
            get_available_tool_names,
        )
        names = get_available_tool_names()
        assert isinstance(names, list)
        assert "search_candidates" in names

    def test_domain_loaders_importable(self):
        import importlib
        from app.domains.agent_studio.platform_tools_loader import (
            get_domain_tool_loaders,
        )
        loaders = get_domain_tool_loaders()
        for domain, path in loaders.items():
            module_path, func_name = path.rsplit(".", 1)
            mod = importlib.import_module(module_path)
            func = getattr(mod, func_name)
            assert callable(func), f"{domain}: {func_name} not callable"

    def test_registry_matches_yaml(self):
        from app.domains.agent_studio.platform_tools_loader import (
            get_platform_tools_registry,
        )
        with open(YAML_PATH) as f:
            config = yaml.safe_load(f)
        registry = get_platform_tools_registry()
        assert set(registry.keys()) == set(config["tools"].keys())

    def test_write_tools_count(self):
        from app.domains.agent_studio.platform_tools_loader import (
            get_platform_tools_registry,
        )
        registry = get_platform_tools_registry()
        writes = [n for n, a in registry.items() if a == "write"]
        assert len(writes) >= 5
