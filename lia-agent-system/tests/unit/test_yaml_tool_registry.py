"""
Unit tests — YAML Tool Registry (Sprint G5).

Cobre:
- load_tool_metadata: leitura do YAML, cache, ausência de arquivo
- export_registry_to_yaml: serialização correta
- validate_registry_against_yaml: missing tools, description mismatches
- ToolRegistry.export_to_yaml / validate_yaml integração
- Arquivo YAML de metadados existente e válido
"""
import pytest

pytestmark = pytest.mark.medium

from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tool(name: str, description: str = "desc", allowed_agents=None):
    tool = MagicMock()
    tool.name = name
    tool.description = description
    tool.allowed_agents = allowed_agents or ["orchestrator"]
    tool.parameters_schema = {"type": "object", "properties": {}}
    return tool


SAMPLE_YAML = """
tools:
  - name: tool_a
    description: Tool A description
    allowed_agents: [orchestrator]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      properties:
        param1: {type: string}

  - name: tool_b
    description: Tool B description
    allowed_agents: [job_wizard, orchestrator]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      properties: {}
"""


# ---------------------------------------------------------------------------
# load_tool_metadata
# ---------------------------------------------------------------------------

class TestLoadToolMetadata:

    def test_load_from_temp_file(self, tmp_path):
        from app.tools.tool_registry_loader import load_tool_metadata
        yaml_file = tmp_path / "tools.yaml"
        yaml_file.write_text(SAMPLE_YAML, encoding="utf-8")
        metadata = load_tool_metadata(yaml_file)
        assert "tool_a" in metadata
        assert "tool_b" in metadata

    def test_tool_a_fields(self, tmp_path):
        from app.tools.tool_registry_loader import load_tool_metadata
        yaml_file = tmp_path / "tools.yaml"
        yaml_file.write_text(SAMPLE_YAML, encoding="utf-8")
        metadata = load_tool_metadata(yaml_file)
        assert metadata["tool_a"]["description"] == "Tool A description"
        assert metadata["tool_a"]["scope"] == "GLOBAL"
        assert "orchestrator" in metadata["tool_a"]["allowed_agents"]

    def test_tool_b_allowed_agents(self, tmp_path):
        from app.tools.tool_registry_loader import load_tool_metadata
        yaml_file = tmp_path / "tools.yaml"
        yaml_file.write_text(SAMPLE_YAML, encoding="utf-8")
        metadata = load_tool_metadata(yaml_file)
        assert "job_wizard" in metadata["tool_b"]["allowed_agents"]

    def test_missing_file_returns_empty(self, tmp_path):
        from app.tools.tool_registry_loader import load_tool_metadata
        missing = tmp_path / "nonexistent.yaml"
        metadata = load_tool_metadata(missing)
        assert metadata == {}

    def test_empty_yaml_returns_empty(self, tmp_path):
        from app.tools.tool_registry_loader import load_tool_metadata
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("tools: []", encoding="utf-8")
        metadata = load_tool_metadata(yaml_file)
        assert metadata == {}

    def test_returns_dict_keyed_by_name(self, tmp_path):
        from app.tools.tool_registry_loader import load_tool_metadata
        yaml_file = tmp_path / "tools.yaml"
        yaml_file.write_text(SAMPLE_YAML, encoding="utf-8")
        metadata = load_tool_metadata(yaml_file)
        assert isinstance(metadata, dict)
        for key in metadata:
            assert isinstance(key, str)

    def test_default_yaml_file_exists(self):
        from app.tools.tool_registry_loader import _DEFAULT_YAML_PATH
        assert _DEFAULT_YAML_PATH.exists(), (
            f"Default YAML not found at {_DEFAULT_YAML_PATH}"
        )

    def test_default_yaml_has_tools(self):
        from app.tools.tool_registry_loader import load_tool_metadata
        metadata = load_tool_metadata()
        assert len(metadata) > 0


# ---------------------------------------------------------------------------
# export_registry_to_yaml
# ---------------------------------------------------------------------------

class TestExportRegistryToYaml:

    def test_exports_tool_names(self):
        from app.tools.tool_registry_loader import export_registry_to_yaml
        tools = [_make_tool("tool_x"), _make_tool("tool_y")]
        yaml_str = export_registry_to_yaml(tools)
        assert "tool_x" in yaml_str
        assert "tool_y" in yaml_str

    def test_exports_descriptions(self):
        from app.tools.tool_registry_loader import export_registry_to_yaml
        tools = [_make_tool("my_tool", description="My special description")]
        yaml_str = export_registry_to_yaml(tools)
        assert "My special description" in yaml_str

    def test_exports_allowed_agents(self):
        from app.tools.tool_registry_loader import export_registry_to_yaml
        tools = [_make_tool("t1", allowed_agents=["wizard", "sourcing"])]
        yaml_str = export_registry_to_yaml(tools)
        assert "wizard" in yaml_str
        assert "sourcing" in yaml_str

    def test_writes_to_file(self, tmp_path):
        from app.tools.tool_registry_loader import export_registry_to_yaml
        tools = [_make_tool("written_tool")]
        out_path = tmp_path / "output.yaml"
        export_registry_to_yaml(tools, path=out_path)
        assert out_path.exists()
        content = out_path.read_text(encoding="utf-8")
        assert "written_tool" in content

    def test_returns_string(self):
        from app.tools.tool_registry_loader import export_registry_to_yaml
        result = export_registry_to_yaml([_make_tool("t")])
        assert isinstance(result, str)

    def test_empty_list(self):
        from app.tools.tool_registry_loader import export_registry_to_yaml
        yaml_str = export_registry_to_yaml([])
        assert "tools:" in yaml_str

    def test_roundtrip_via_load(self, tmp_path):
        from app.tools.tool_registry_loader import export_registry_to_yaml, load_tool_metadata
        tools = [_make_tool("roundtrip_tool", description="Roundtrip desc")]
        out_path = tmp_path / "roundtrip.yaml"
        export_registry_to_yaml(tools, path=out_path)
        loaded = load_tool_metadata(out_path)
        assert "roundtrip_tool" in loaded
        assert loaded["roundtrip_tool"]["description"] == "Roundtrip desc"


# ---------------------------------------------------------------------------
# validate_registry_against_yaml
# ---------------------------------------------------------------------------

class TestValidateRegistryAgainstYaml:

    def test_perfect_match_is_ok(self, tmp_path):
        from app.tools.tool_registry_loader import validate_registry_against_yaml
        yaml_file = tmp_path / "tools.yaml"
        yaml_file.write_text(SAMPLE_YAML, encoding="utf-8")
        tools = [
            _make_tool("tool_a", description="Tool A description"),
            _make_tool("tool_b", description="Tool B description"),
        ]
        report = validate_registry_against_yaml(tools, path=yaml_file)
        assert report["ok"] is True

    def test_missing_in_yaml(self, tmp_path):
        from app.tools.tool_registry_loader import validate_registry_against_yaml
        yaml_file = tmp_path / "tools.yaml"
        yaml_file.write_text(SAMPLE_YAML, encoding="utf-8")
        tools = [
            _make_tool("tool_a", description="Tool A description"),
            _make_tool("tool_b", description="Tool B description"),
            _make_tool("extra_tool"),
        ]
        report = validate_registry_against_yaml(tools, path=yaml_file)
        assert report["ok"] is False
        assert "extra_tool" in report["missing_in_yaml"]

    def test_missing_in_registry(self, tmp_path):
        from app.tools.tool_registry_loader import validate_registry_against_yaml
        yaml_file = tmp_path / "tools.yaml"
        yaml_file.write_text(SAMPLE_YAML, encoding="utf-8")
        tools = [_make_tool("tool_a", description="Tool A description")]
        report = validate_registry_against_yaml(tools, path=yaml_file)
        assert report["ok"] is False
        assert "tool_b" in report["missing_in_registry"]

    def test_description_mismatch(self, tmp_path):
        from app.tools.tool_registry_loader import validate_registry_against_yaml
        yaml_file = tmp_path / "tools.yaml"
        yaml_file.write_text(SAMPLE_YAML, encoding="utf-8")
        tools = [
            _make_tool("tool_a", description="DIFFERENT description"),
            _make_tool("tool_b", description="Tool B description"),
        ]
        report = validate_registry_against_yaml(tools, path=yaml_file)
        assert report["ok"] is False
        assert any(m["tool"] == "tool_a" for m in report["description_mismatches"])

    def test_report_counts(self, tmp_path):
        from app.tools.tool_registry_loader import validate_registry_against_yaml
        yaml_file = tmp_path / "tools.yaml"
        yaml_file.write_text(SAMPLE_YAML, encoding="utf-8")
        tools = [
            _make_tool("tool_a", description="Tool A description"),
            _make_tool("tool_b", description="Tool B description"),
        ]
        report = validate_registry_against_yaml(tools, path=yaml_file)
        assert report["registered_count"] == 2
        assert report["yaml_count"] == 2


# ---------------------------------------------------------------------------
# ToolRegistry integration
# ---------------------------------------------------------------------------

class TestToolRegistryYamlIntegration:

    def test_export_to_yaml_method(self):
        from app.tools.registry import ToolRegistry
        reg = ToolRegistry()
        reg.register(_make_tool("reg_tool_1"))
        reg.register(_make_tool("reg_tool_2"))
        yaml_str = reg.export_to_yaml()
        assert "reg_tool_1" in yaml_str
        assert "reg_tool_2" in yaml_str

    def test_validate_yaml_method_ok(self, tmp_path):
        from app.tools.registry import ToolRegistry
        yaml_file = tmp_path / "reg.yaml"
        reg = ToolRegistry()
        tool = _make_tool("validated_tool", description="Validated desc")
        reg.register(tool)
        # Export then validate
        reg.export_to_yaml(path=yaml_file)
        report = reg.validate_yaml(path=yaml_file)
        assert report["ok"] is True

    def test_validate_yaml_detects_new_tool(self, tmp_path):
        from app.tools.registry import ToolRegistry
        yaml_file = tmp_path / "reg2.yaml"
        reg = ToolRegistry()
        reg.register(_make_tool("tool_orig"))
        reg.export_to_yaml(path=yaml_file)
        # Add new tool after export
        reg.register(_make_tool("tool_new"))
        report = reg.validate_yaml(path=yaml_file)
        assert report["ok"] is False
        assert "tool_new" in report["missing_in_yaml"]


# ---------------------------------------------------------------------------
# Default YAML metadata content
# ---------------------------------------------------------------------------

class TestDefaultYamlContent:

    def test_default_yaml_has_job_wizard_tools(self):
        from app.tools.tool_registry_loader import load_tool_metadata
        metadata = load_tool_metadata()
        assert "search_salary_benchmark" in metadata

    def test_default_yaml_has_candidate_tools(self):
        from app.tools.tool_registry_loader import load_tool_metadata
        metadata = load_tool_metadata()
        assert "update_candidate_stage" in metadata

    def test_default_yaml_has_communication_tools(self):
        from app.tools.tool_registry_loader import load_tool_metadata
        metadata = load_tool_metadata()
        assert "send_email" in metadata

    def test_default_yaml_has_export_tools(self):
        from app.tools.tool_registry_loader import load_tool_metadata
        metadata = load_tool_metadata()
        assert "export_candidates" in metadata

    def test_default_yaml_tool_count_gte_20(self):
        from app.tools.tool_registry_loader import load_tool_metadata
        metadata = load_tool_metadata()
        assert len(metadata) >= 20

    def test_all_tools_have_required_fields(self):
        from app.tools.tool_registry_loader import load_tool_metadata
        metadata = load_tool_metadata()
        for name, tool in metadata.items():
            assert "description" in tool, f"Tool {name} missing description"
            assert "allowed_agents" in tool, f"Tool {name} missing allowed_agents"
            assert "scope" in tool, f"Tool {name} missing scope"

    def test_scopes_are_valid(self):
        from app.tools.tool_registry_loader import load_tool_metadata
        valid_scopes = {"TALENT_FUNNEL", "JOB_TABLE", "IN_JOB", "GLOBAL"}
        metadata = load_tool_metadata()
        for name, tool in metadata.items():
            assert tool.get("scope") in valid_scopes, (
                f"Tool {name} has invalid scope: {tool.get('scope')}"
            )

    def test_all_tools_have_returns_field(self):
        """Every tool in tool_registry_metadata.yaml must declare returns: schema (R-029)."""
        from app.tools.tool_registry_loader import load_tool_metadata
        metadata = load_tool_metadata()
        missing = [name for name, meta in metadata.items() if "returns" not in meta]
        assert not missing, f"Tools missing returns: field: {missing}"

    def test_returns_field_has_required_properties(self):
        """returns: schema must have success and message as required properties (R-029)."""
        from app.tools.tool_registry_loader import load_tool_metadata
        metadata = load_tool_metadata()
        for name, tool in metadata.items():
            returns = tool.get("returns", {})
            required = returns.get("required", [])
            assert "success" in required, (
                f"Tool {name} returns: missing required 'success' field"
            )
            assert "message" in required, (
                f"Tool {name} returns: missing required 'message' field"
            )
