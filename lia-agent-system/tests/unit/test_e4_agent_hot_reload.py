"""
Sprint Y5 — E4: Registro Dinâmico de Agentes YAML — Hot-Reload

8 test cases:
1. test_registry_yaml_exists           — file exists and has agents key
2. test_reload_from_yaml_loads_enabled_agents — mock yaml, check names returned
3. test_reload_from_yaml_skips_disabled — agent with enabled: false not loaded
4. test_reload_from_yaml_fail_open      — bad path returns empty list, no exception
5. test_agent_registry_watcher_detects_change — mock mtime change, reload called
6. test_agent_registry_watcher_no_change_no_reload — same mtime, no reload
7. test_is_registered_after_reload     — agent in registry after reload
8. test_admin_endpoint_returns_200     — FastAPI TestClient POST /admin/agents/reload
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# 1. YAML file exists and has the 'agents' key
# ---------------------------------------------------------------------------

def test_registry_yaml_exists():
    """agents_registry.yaml must exist and contain an 'agents' key."""
    import yaml

    yaml_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "app",
        "agents_registry.yaml",
    )
    assert os.path.exists(yaml_path), f"agents_registry.yaml not found at {yaml_path}"

    with open(yaml_path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    assert isinstance(data, dict), "YAML root must be a dict"
    assert "agents" in data, "YAML must have an 'agents' key"
    assert isinstance(data["agents"], list), "'agents' must be a list"
    assert len(data["agents"]) > 0, "'agents' list must not be empty"


# ---------------------------------------------------------------------------
# 2. reload_from_yaml loads enabled agents
# ---------------------------------------------------------------------------

def test_reload_from_yaml_loads_enabled_agents(tmp_path):
    """reload_from_yaml returns names of enabled agents from a valid YAML."""
    import yaml
    from lia_agents_core import react_agent_registry as reg_module

    yaml_content = {
        "agents": [
            {"name": "alpha", "domain": "alpha", "enabled": True, "model_id": "m1"},
            {"name": "beta", "domain": "beta", "enabled": True, "model_id": "m2"},
        ]
    }
    yaml_file = tmp_path / "test_agents.yaml"
    yaml_file.write_text(yaml.dump(yaml_content), encoding="utf-8")

    # Reset flat registry so test is isolated
    reg_module._flat_registry.clear()

    names = reg_module.reload_from_yaml(str(yaml_file))

    assert set(names) == {"alpha", "beta"}
    assert reg_module.is_registered("alpha")
    assert reg_module.is_registered("beta")


# ---------------------------------------------------------------------------
# 3. reload_from_yaml skips disabled agents
# ---------------------------------------------------------------------------

def test_reload_from_yaml_skips_disabled(tmp_path):
    """Agents with enabled: false must NOT be added to the registry."""
    import yaml
    from lia_agents_core import react_agent_registry as reg_module

    yaml_content = {
        "agents": [
            {"name": "enabled_agent", "domain": "x", "enabled": True},
            {"name": "disabled_agent", "domain": "y", "enabled": False},
        ]
    }
    yaml_file = tmp_path / "test_disabled.yaml"
    yaml_file.write_text(yaml.dump(yaml_content), encoding="utf-8")

    reg_module._flat_registry.clear()

    names = reg_module.reload_from_yaml(str(yaml_file))

    assert "enabled_agent" in names
    assert "disabled_agent" not in names
    assert reg_module.is_registered("enabled_agent")
    assert not reg_module.is_registered("disabled_agent")


# ---------------------------------------------------------------------------
# 4. reload_from_yaml fail-open — bad path returns empty list, no exception
# ---------------------------------------------------------------------------

def test_reload_from_yaml_fail_open():
    """reload_from_yaml with a non-existent path returns [] without raising."""
    from lia_agents_core import react_agent_registry as reg_module

    result = reg_module.reload_from_yaml("/non/existent/path/agents.yaml")

    assert result == [], f"Expected empty list, got {result}"


# ---------------------------------------------------------------------------
# 5. AgentRegistryWatcher detects mtime change and calls reload
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_agent_registry_watcher_detects_change():
    """When mtime changes, check_and_reload triggers reload_agents_registry."""
    from app.core.agent_registry_watcher import AgentRegistryWatcher

    watcher = AgentRegistryWatcher()
    # Pre-set a stale mtime so the file looks changed
    watcher._last_mtime = {}

    mock_reload = MagicMock(return_value=["pipeline", "sourcing"])

    with (
        patch("app.core.agent_registry_watcher.reload_agents_registry", mock_reload),
        patch("app.core.agent_registry_watcher.AgentRegistryWatcher._reload_tools_registry"),
        patch(
            "app.core.agent_registry_watcher.os.path.getmtime",
            side_effect=lambda p: 1000.0,
        ),
    ):
        # _last_mtime is empty → -1.0 sentinel → different from 1000.0 → change detected
        names = await watcher.check_and_reload()

    mock_reload.assert_called_once()
    assert "pipeline" in names
    assert "sourcing" in names


# ---------------------------------------------------------------------------
# 6. AgentRegistryWatcher — no change detected, reload NOT called
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_agent_registry_watcher_no_change_no_reload():
    """When mtime is unchanged, check_and_reload must NOT call reload."""
    from app.core.agent_registry_watcher import AgentRegistryWatcher, AGENTS_REGISTRY_YAML, TOOLS_REGISTRY_YAML

    watcher = AgentRegistryWatcher()
    # Pre-set mtimes to match what getmtime will return
    fixed_mtime = 9999.0
    watcher._last_mtime = {
        AGENTS_REGISTRY_YAML: fixed_mtime,
        TOOLS_REGISTRY_YAML: fixed_mtime,
    }

    mock_reload = MagicMock(return_value=["agent_x"])

    with (
        patch("app.core.agent_registry_watcher.reload_agents_registry", mock_reload),
        patch(
            "app.core.agent_registry_watcher.os.path.getmtime",
            side_effect=lambda p: fixed_mtime,
        ),
    ):
        names = await watcher.check_and_reload()

    # No change → reload should NOT have been called
    mock_reload.assert_not_called()
    assert names == []


# ---------------------------------------------------------------------------
# 7. is_registered returns True after reload_from_yaml
# ---------------------------------------------------------------------------

def test_is_registered_after_reload(tmp_path):
    """After reload_from_yaml, is_registered must return True for loaded agents."""
    import yaml
    from lia_agents_core import react_agent_registry as reg_module

    yaml_content = {
        "agents": [
            {"name": "gamma", "domain": "gamma", "enabled": True, "model_id": "m3"},
        ]
    }
    yaml_file = tmp_path / "gamma_agents.yaml"
    yaml_file.write_text(yaml.dump(yaml_content), encoding="utf-8")

    reg_module._flat_registry.clear()
    reg_module.reload_from_yaml(str(yaml_file))

    assert reg_module.is_registered("gamma") is True
    assert reg_module.is_registered("nonexistent") is False

    entry = reg_module.get("gamma")
    assert entry is not None
    assert entry["name"] == "gamma"


# ---------------------------------------------------------------------------
# 8. Admin endpoint POST /admin/agents/reload returns 200
# ---------------------------------------------------------------------------

def test_admin_endpoint_returns_200():
    """POST /api/v1/admin/agents/reload must return 200 with reloaded list."""
    from fastapi.testclient import TestClient
    from fastapi import FastAPI

    # Build a minimal isolated app — only the admin_agents router.
    # We patch require_admin BEFORE importing the router so the dependency
    # override is seamless.
    import app.api.v1.admin_agents as aa_mod
    from app.api.v1.admin_agents import require_admin as _req_admin
    from app.shared.security.require_company_id import require_company_id as _require_cid

    isolated_app = FastAPI()
    isolated_app.include_router(aa_mod.router, prefix="/api/v1")

    # Override auth dependencies so no real JWT is needed
    isolated_app.dependency_overrides[_req_admin] = lambda: {"sub": "admin"}
    isolated_app.dependency_overrides[_require_cid] = lambda: "test-company-id" 

    with (
        patch(
            "app.core.agent_registry_watcher.agent_registry_watcher.check_and_reload",
            new_callable=AsyncMock,
            return_value=["pipeline", "sourcing"],
        ),
        patch(
            "app.api.v1.admin_agents.reload_agents_registry",
            return_value=["pipeline", "sourcing", "wizard"],
        ),
    ):
        client = TestClient(isolated_app, raise_server_exceptions=True)
        response = client.post(
            "/api/v1/admin/agents/reload",
            headers={"X-Company-ID": "test-company-123"},
        )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert "reloaded" in body
    assert "total" in body
    assert isinstance(body["reloaded"], list)
    assert body["total"] == len(body["reloaded"])
    assert body["total"] > 0
