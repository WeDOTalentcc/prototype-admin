"""
Agent x Tools x Prompts Mapper — Task #117 (T001).

Introspects ToolRegistry, GlobalToolRegistry, tool_permissions.yaml,
and agent prompt configuration to generate a complete map of:
  - Which tools each agent can access
  - Which tools are query vs. action
  - Which scope each tool belongs to
  - System prompt summary per agent

Outputs:
  - JSON: tests/quality_suite/output/agent_tool_map.json
  - Markdown: tests/quality_suite/output/agent_tool_map.md
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "output"

TOOL_PERMISSIONS_PATH = (
    Path(__file__).parent.parent.parent / "app" / "tools" / "tool_permissions.yaml"
)

PROMPTS_DIR = (
    Path(__file__).parent.parent.parent / "app" / "prompts"
)

AGENT_TYPES = [
    "orchestrator",
    "job_planner",
    "sourcing",
    "cv_screening",
    "interviewer",
    "wsi_evaluator",
    "scheduling",
    "analyst_feedback",
    "ats_integrator",
    "recruiter_assistant",
    "proactive_insights",
    "communication",
    "analytics",
    "pipeline_transition",
    "kanban",
    "talent",
    "jobs_management",
    "automation",
    "hiring_policy",
]

AGENT_DOMAIN_FILES = {
    "orchestrator": "app/orchestrator/orchestrator.py",
    "job_planner": "app/domains/job_management/agents/wizard_react_agent.py",
    "sourcing": "app/domains/sourcing/agents/sourcing_react_agent.py",
    "cv_screening": "app/domains/cv_screening/agents/pipeline_react_agent.py",
    "wsi_evaluator": "app/domains/cv_screening/agents/avaliador_wsi_agent.py",
    "communication": "app/domains/communication/agents/communication_react_agent.py",
    "analytics": "app/domains/analytics/agents/analytics_react_agent.py",
    "pipeline_transition": "app/domains/pipeline/agents/pipeline_transition_agent.py",
    "kanban": "app/domains/recruiter_assistant/agents/kanban_react_agent.py",
    "talent": "app/domains/recruiter_assistant/agents/talent_react_agent.py",
    "jobs_management": "app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py",
    "automation": "app/domains/automation/agents/automation_react_agent.py",
    "ats_integrator": "app/domains/ats_integration/agents/ats_integration_react_agent.py",
    "hiring_policy": "app/domains/hiring_policy/agents/policy_react_agent.py",
}


def load_tool_permissions() -> dict[str, Any]:
    if not TOOL_PERMISSIONS_PATH.exists():
        logger.warning("tool_permissions.yaml not found at %s", TOOL_PERMISSIONS_PATH)
        return {}
    with TOOL_PERMISSIONS_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def extract_scopes(permissions: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    scopes = permissions.get("global", {}).get("scopes", {})
    result: dict[str, dict[str, list[str]]] = {}
    for scope_name, scope_data in scopes.items():
        result[scope_name] = {
            "query": scope_data.get("query") or [],
            "action": scope_data.get("action") or [],
        }
    return result


def build_tool_catalog(scopes: dict[str, dict[str, list[str]]]) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for scope_name, tools_by_type in scopes.items():
        for tool_type, tools in tools_by_type.items():
            for tool_name in tools:
                if tool_name not in catalog:
                    catalog[tool_name] = {
                        "name": tool_name,
                        "type": tool_type,
                        "scopes": [],
                    }
                if scope_name not in catalog[tool_name]["scopes"]:
                    catalog[tool_name]["scopes"].append(scope_name)
                if tool_type == "action" and catalog[tool_name]["type"] == "query":
                    catalog[tool_name]["type"] = "mixed"
    return catalog


def load_prompt_summaries() -> dict[str, str]:
    summaries: dict[str, str] = {}
    domains_dir = PROMPTS_DIR / "domains"
    shared_dir = PROMPTS_DIR / "shared"

    for yaml_path in list(domains_dir.glob("*.yaml")) + list(shared_dir.glob("*.yaml")):
        try:
            with yaml_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            domain_id = yaml_path.stem
            if "system_prompt" in data:
                prompt = data["system_prompt"]
                summaries[domain_id] = prompt[:200] + "..." if len(prompt) > 200 else prompt
            elif "prompts" in data:
                for key, val in data["prompts"].items():
                    if isinstance(val, str):
                        summaries[key] = val[:200] + "..." if len(val) > 200 else val
        except Exception as exc:
            logger.warning("Error loading prompt %s: %s", yaml_path, exc)

    return summaries


def build_agent_tool_map() -> dict[str, Any]:
    permissions = load_tool_permissions()
    scopes = extract_scopes(permissions)
    tool_catalog = build_tool_catalog(scopes)
    prompt_summaries = load_prompt_summaries()

    agent_map: dict[str, Any] = {}
    for agent_type in AGENT_TYPES:
        agent_entry: dict[str, Any] = {
            "agent_type": agent_type,
            "implementation_file": AGENT_DOMAIN_FILES.get(agent_type, "unknown"),
            "prompt_summary": prompt_summaries.get(agent_type, "N/A"),
            "accessible_scopes": [],
            "tools": {"query": [], "action": []},
        }
        agent_map[agent_type] = agent_entry

    scope_agent_mapping = {
        "talent_funnel": ["talent", "sourcing", "recruiter_assistant"],
        "job_table": ["job_planner", "jobs_management", "analytics"],
        "in_job": ["cv_screening", "pipeline_transition", "kanban", "wsi_evaluator"],
        "global": ["orchestrator", "analytics", "communication"],
    }

    for scope_name, agent_types in scope_agent_mapping.items():
        scope_tools = scopes.get(scope_name, {})
        for agent_type in agent_types:
            if agent_type in agent_map:
                agent_map[agent_type]["accessible_scopes"].append(scope_name)
                for tool_name in scope_tools.get("query", []):
                    if tool_name not in agent_map[agent_type]["tools"]["query"]:
                        agent_map[agent_type]["tools"]["query"].append(tool_name)
                for tool_name in scope_tools.get("action", []):
                    if tool_name not in agent_map[agent_type]["tools"]["action"]:
                        agent_map[agent_type]["tools"]["action"].append(tool_name)

    all_tools_flat = set()
    for scope_data in scopes.values():
        all_tools_flat.update(scope_data.get("query", []))
        all_tools_flat.update(scope_data.get("action", []))

    covered_tools: set[str] = set()
    for entry in agent_map.values():
        covered_tools.update(entry["tools"]["query"])
        covered_tools.update(entry["tools"]["action"])

    uncovered = sorted(all_tools_flat - covered_tools)

    report = {
        "metadata": {
            "total_agents": len(agent_map),
            "total_tools": len(all_tools_flat),
            "total_scopes": len(scopes),
            "uncovered_tools": uncovered,
            "coverage_pct": round(
                (len(covered_tools) / len(all_tools_flat) * 100) if all_tools_flat else 100, 1
            ),
        },
        "scopes": scopes,
        "tool_catalog": tool_catalog,
        "agents": agent_map,
    }
    return report


def generate_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    meta = report["metadata"]
    lines.append("# LIA Agent x Tools x Prompts Map")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- **Total Agents:** {meta['total_agents']}")
    lines.append(f"- **Total Tools:** {meta['total_tools']}")
    lines.append(f"- **Total Scopes:** {meta['total_scopes']}")
    lines.append(f"- **Coverage:** {meta['coverage_pct']}%")
    if meta["uncovered_tools"]:
        lines.append(f"- **Uncovered Tools:** {', '.join(meta['uncovered_tools'])}")
    lines.append("")

    lines.append("## Scopes")
    lines.append("")
    for scope_name, scope_data in report["scopes"].items():
        query_count = len(scope_data.get("query", []))
        action_count = len(scope_data.get("action", []))
        lines.append(f"### {scope_name}")
        lines.append(f"- Query tools ({query_count}): {', '.join(scope_data.get('query', []))}")
        lines.append(f"- Action tools ({action_count}): {', '.join(scope_data.get('action', []))}")
        lines.append("")

    lines.append("## Agent Details")
    lines.append("")
    lines.append("| Agent | Scopes | Query Tools | Action Tools | Implementation |")
    lines.append("|-------|--------|-------------|--------------|----------------|")
    for agent_type, entry in report["agents"].items():
        scopes_str = ", ".join(entry["accessible_scopes"]) or "none"
        q_count = len(entry["tools"]["query"])
        a_count = len(entry["tools"]["action"])
        impl = entry["implementation_file"]
        lines.append(f"| {agent_type} | {scopes_str} | {q_count} | {a_count} | `{impl}` |")
    lines.append("")

    lines.append("## Agent x Tool Matrix")
    lines.append("")
    all_tools = sorted(report["tool_catalog"].keys())
    header = "| Tool | Type |"
    separator = "|------|------|"
    for agent_type in report["agents"]:
        header += f" {agent_type[:8]} |"
        separator += "----------|"
    lines.append(header)
    lines.append(separator)
    for tool_name in all_tools:
        tool_info = report["tool_catalog"][tool_name]
        row = f"| {tool_name} | {tool_info['type']} |"
        for agent_type, entry in report["agents"].items():
            has_tool = (
                tool_name in entry["tools"]["query"]
                or tool_name in entry["tools"]["action"]
            )
            row += " Y |" if has_tool else "   |"
        lines.append(row)
    lines.append("")

    lines.append("## Prompt Summaries")
    lines.append("")
    for agent_type, entry in report["agents"].items():
        lines.append(f"### {agent_type}")
        lines.append(f"```")
        lines.append(entry.get("prompt_summary", "N/A")[:300])
        lines.append(f"```")
        lines.append("")

    return "\n".join(lines)


def run_mapping() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = build_agent_tool_map()

    json_path = OUTPUT_DIR / "agent_tool_map.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info("JSON map written to %s", json_path)

    md_content = generate_markdown(report)
    md_path = OUTPUT_DIR / "agent_tool_map.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info("Markdown map written to %s", md_path)

    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    report = run_mapping()
    print(f"Generated agent-tool map: {report['metadata']['total_agents']} agents, "
          f"{report['metadata']['total_tools']} tools, "
          f"{report['metadata']['coverage_pct']}% coverage")
