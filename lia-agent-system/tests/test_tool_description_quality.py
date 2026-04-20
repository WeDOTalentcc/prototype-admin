"""
CI guard: validates that every tool in tool_registry_metadata.yaml follows the
rich description template introduced in Task #690. Also validates DomainAction
description quality across all domain action registries.

Run: pytest lia-agent-system/tests/test_tool_description_quality.py -v

Fails if ANY tool violates the template requirements:
  - description >= 80 characters
  - when_to_use field present and >= 40 characters
  - when_not_to_use field present and >= 40 characters
  - side_effects field present (list, may be ["none"])
  - governance_tags field present (list, includes multi_tenant)
  - related_tools field present (list, may be empty [])

Fails if ANY DomainAction violates:
  - description >= 80 characters (non-empty, active voice)
"""
from __future__ import annotations

import pathlib
import re
import sys
import os

import pytest
import yaml

YAML_PATH = (
    pathlib.Path(__file__).parent.parent
    / "app" / "tools" / "tool_registry_metadata.yaml"
)

MIN_DESCRIPTION_LEN = 80
MIN_WHEN_TO_USE_LEN = 40
MIN_WHEN_NOT_TO_USE_LEN = 40

ALLOWED_SIDE_EFFECTS = {
    "db_write", "db_delete", "email_sent", "whatsapp_sent",
    "webhook_fired", "quota_consumed", "credits_consumed",
    "external_api_call", "mock_only", "audit_trail",
    "write_destructive", "none",
}

ALLOWED_GOVERNANCE_TAGS = {
    "pii", "fairness_guard", "requires_hitl", "multi_tenant",
    "audit_trail", "credits_consumed", "write_destructive",
}

VALID_SCOPES = {"TALENT_FUNNEL", "JOB_TABLE", "IN_JOB", "GLOBAL"}


def _load_tools() -> list[dict]:
    with YAML_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("tools", [])


def _clean(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def _tool_ids(tools: list[dict]) -> list[str]:
    return [t.get("name", f"unnamed_{i}") for i, t in enumerate(tools)]


ALL_TOOLS = _load_tools()


class TestRegistryLevel:
    """Registry-wide integrity checks — run once."""

    def test_yaml_has_tools(self):
        assert len(ALL_TOOLS) >= 10, (
            f"Expected at least 10 tools, found {len(ALL_TOOLS)}."
        )

    def test_no_duplicate_tool_names(self):
        names = [t.get("name") for t in ALL_TOOLS]
        duplicates = sorted({n for n in names if names.count(n) > 1})
        assert not duplicates, f"Duplicate tool names found: {duplicates}"


@pytest.mark.parametrize("tool", ALL_TOOLS, ids=_tool_ids(ALL_TOOLS))
class TestEachTool:
    """Per-tool template compliance — one parametrized run per tool."""

    def test_has_name(self, tool):
        assert tool.get("name"), "Tool must have a 'name' field."

    def test_description_present_and_long_enough(self, tool):
        desc = _clean(tool.get("description", ""))
        assert desc, f"[{tool.get('name')}] 'description' is missing or empty."
        assert len(desc) >= MIN_DESCRIPTION_LEN, (
            f"[{tool.get('name')}] description is {len(desc)} chars "
            f"(min {MIN_DESCRIPTION_LEN}). Got: {desc[:120]!r}"
        )

    def test_when_to_use_present_and_long_enough(self, tool):
        val = _clean(tool.get("when_to_use", ""))
        assert val, (
            f"[{tool.get('name')}] 'when_to_use' is missing or empty."
        )
        assert len(val) >= MIN_WHEN_TO_USE_LEN, (
            f"[{tool.get('name')}] 'when_to_use' is {len(val)} chars "
            f"(min {MIN_WHEN_TO_USE_LEN}). Got: {val!r}"
        )

    def test_when_not_to_use_present_and_long_enough(self, tool):
        val = _clean(tool.get("when_not_to_use", ""))
        assert val, (
            f"[{tool.get('name')}] 'when_not_to_use' is missing or empty."
        )
        assert len(val) >= MIN_WHEN_NOT_TO_USE_LEN, (
            f"[{tool.get('name')}] 'when_not_to_use' is {len(val)} chars "
            f"(min {MIN_WHEN_NOT_TO_USE_LEN}). Got: {val!r}"
        )

    def test_side_effects_is_list(self, tool):
        se = tool.get("side_effects")
        assert se is not None, (
            f"[{tool.get('name')}] 'side_effects' is missing. Use ['none'] if none."
        )
        assert isinstance(se, list), (
            f"[{tool.get('name')}] 'side_effects' must be a list, got {type(se).__name__}."
        )

    def test_side_effects_values_are_known(self, tool):
        se = tool.get("side_effects", [])
        unknown = [v for v in se if v not in ALLOWED_SIDE_EFFECTS]
        assert not unknown, (
            f"[{tool.get('name')}] Unknown side_effect values: {unknown}. "
            f"Allowed: {sorted(ALLOWED_SIDE_EFFECTS)}"
        )

    def test_governance_tags_is_list(self, tool):
        gt = tool.get("governance_tags")
        assert gt is not None, (
            f"[{tool.get('name')}] 'governance_tags' is missing. "
            "Add at minimum ['multi_tenant']."
        )
        assert isinstance(gt, list), (
            f"[{tool.get('name')}] 'governance_tags' must be a list."
        )

    def test_governance_tags_values_are_known(self, tool):
        gt = tool.get("governance_tags", [])
        unknown = [v for v in gt if v not in ALLOWED_GOVERNANCE_TAGS]
        assert not unknown, (
            f"[{tool.get('name')}] Unknown governance_tag values: {unknown}. "
            f"Allowed: {sorted(ALLOWED_GOVERNANCE_TAGS)}"
        )

    def test_multi_tenant_tag_present(self, tool):
        gt = tool.get("governance_tags", [])
        assert "multi_tenant" in gt, (
            f"[{tool.get('name')}] 'multi_tenant' must be in governance_tags. "
            "All LIA tools enforce tenant isolation — make it explicit."
        )

    def test_related_tools_is_list(self, tool):
        rt = tool.get("related_tools")
        assert rt is not None, (
            f"[{tool.get('name')}] 'related_tools' is missing. Use [] if none."
        )
        assert isinstance(rt, list), (
            f"[{tool.get('name')}] 'related_tools' must be a list."
        )

    def test_related_tools_reference_known_tools(self, tool):
        all_names = {t.get("name") for t in ALL_TOOLS}
        related = tool.get("related_tools", [])
        unknown = [r for r in related if r not in all_names]
        assert not unknown, (
            f"[{tool.get('name')}] related_tools references unknown tools: {unknown}. "
            "Add those tools to the YAML or remove the reference."
        )

    def test_allowed_agents_present_and_nonempty(self, tool):
        aa = tool.get("allowed_agents")
        assert aa and isinstance(aa, list) and len(aa) > 0, (
            f"[{tool.get('name')}] 'allowed_agents' is missing or empty."
        )

    def test_scope_is_valid(self, tool):
        scope = tool.get("scope", "")
        assert scope in VALID_SCOPES, (
            f"[{tool.get('name')}] 'scope' must be one of {VALID_SCOPES}, got {scope!r}."
        )

    def test_version_present(self, tool):
        version = tool.get("version", "")
        assert version, f"[{tool.get('name')}] 'version' is missing."


# ---------------------------------------------------------------------------
# DomainAction description quality guard (Task #690)
# ---------------------------------------------------------------------------

DOMAINS_DIR = pathlib.Path(__file__).parent.parent / "app" / "domains"
_ACTION_DESC_PATTERN = re.compile(r'description="([^"]+)"')
_MIN_ACTION_DESC_LEN = 80


def _collect_domain_action_descriptions():
    """Scan all domain actions.py files for (domain, action_id, description)."""
    results = []
    if not DOMAINS_DIR.exists():
        return results
    for domain_dir in sorted(DOMAINS_DIR.iterdir()):
        actions_file = domain_dir / "actions.py"
        if not actions_file.exists():
            continue
        source = actions_file.read_text(encoding="utf-8")
        blocks = re.split(r"DomainAction\(", source)
        for block in blocks[1:]:
            action_id_m = re.search(r'action_id="([^"]+)"', block)
            desc_m = re.search(r'description="([^"]+)"', block)
            if action_id_m and desc_m:
                results.append({
                    "domain": domain_dir.name,
                    "action_id": action_id_m.group(1),
                    "description": desc_m.group(1),
                })
    return results


_ALL_DOMAIN_ACTIONS = _collect_domain_action_descriptions()


@pytest.mark.parametrize(
    "action",
    _ALL_DOMAIN_ACTIONS,
    ids=[f"{a['domain']}/{a['action_id']}" for a in _ALL_DOMAIN_ACTIONS],
)
class TestDomainActionDescriptionQuality:
    """Enforce minimum description quality on every DomainAction.description."""

    def test_description_min_length(self, action):
        desc = action["description"]
        assert len(desc) >= _MIN_ACTION_DESC_LEN, (
            f"[{action['domain']}/{action['action_id']}] description too short "
            f"({len(desc)} chars, min {_MIN_ACTION_DESC_LEN}): {desc!r}"
        )

    def test_description_not_placeholder(self, action):
        desc = action["description"].strip().lower()
        placeholders = {"todo", "placeholder", "fixme", "tbd", "n/a", ""}
        assert desc not in placeholders, (
            f"[{action['domain']}/{action['action_id']}] description is a placeholder: "
            f"{action['description']!r}"
        )
