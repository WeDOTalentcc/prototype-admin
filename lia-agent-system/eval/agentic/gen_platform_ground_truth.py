"""Helper to refresh ``platform_ground_truth.yaml`` from canonical sources.

Today the YAML is hand-curated. This script does a best-effort merge:

  * walks the i18n catalog at ``plataforma-lia/messages/pt.json`` to
    suggest ``screens.*.menu_label``;
  * walks the agent registry under
    ``lia-agent-system/app/tools/`` to suggest ``agents.*.tools``;
  * walks the next.js app dir to suggest ``screens.*.route``.

It NEVER overwrites the existing file by default — it writes a sibling
``platform_ground_truth.suggested.yaml`` so a human can diff/merge.

This is a *stub* — a follow-up task (see #566) will turn this into a
proper sync that fails CI when the live platform drifts from the YAML.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml  # type: ignore

ROOT = Path(__file__).resolve().parents[3]
GT = ROOT / "lia-agent-system/eval/agentic/platform_ground_truth.yaml"
PT_MESSAGES = ROOT / "plataforma-lia/messages/pt.json"
APP_DIR = ROOT / "plataforma-lia/app/[locale]"
TOOL_REG = ROOT / "lia-agent-system/app/tools/tool_registry_metadata.yaml"


def _safe_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  warn: could not parse {path.name}: {exc}", file=sys.stderr)
        return {}


def _safe_read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"  warn: could not parse {path.name}: {exc}", file=sys.stderr)
        return {}


def discover_routes() -> dict[str, str]:
    """Map screen-id-ish slug → route, by scanning app/[locale]/<slug>/page.tsx."""
    out: dict[str, str] = {}
    if not APP_DIR.exists():
        return out
    for page in APP_DIR.rglob("page.tsx"):
        rel = page.relative_to(APP_DIR).parent.as_posix()
        if not rel or rel.startswith("_") or rel.startswith("api"):
            continue
        slug = rel.split("/")[0].replace("(", "").replace(")", "")
        out.setdefault(slug, f"/pt/{rel}")
    return out


def discover_tools() -> dict[str, list[str]]:
    """Map agent_id → list of tool names from the tool registry metadata."""
    reg = _safe_read_yaml(TOOL_REG)
    out: dict[str, list[str]] = {}
    if not reg:
        return out
    for entry in reg.get("tools") or []:
        name = entry.get("name")
        agent = entry.get("agent") or entry.get("owner_agent")
        if name and agent:
            out.setdefault(agent, []).append(name)
    return out


def main() -> None:
    existing = _safe_read_yaml(GT)
    suggested = json.loads(json.dumps(existing))  # deep copy
    suggested.setdefault("screens", {})
    suggested.setdefault("agents", {})

    routes = discover_routes()
    if routes:
        for slug, route in routes.items():
            scr = suggested["screens"].setdefault(slug, {})
            scr.setdefault("route", route)
        print(f"  discovered {len(routes)} routes")

    tools = discover_tools()
    if tools:
        for agent, names in tools.items():
            ag = suggested["agents"].setdefault(agent, {})
            ag["tools"] = sorted(set((ag.get("tools") or []) + names))
        print(f"  discovered tools for {len(tools)} agents")

    pt = _safe_read_json(PT_MESSAGES)
    if pt:
        print(f"  loaded {len(pt)} top-level i18n keys (manual mapping required)")

    out = GT.with_name("platform_ground_truth.suggested.yaml")
    out.write_text(yaml.safe_dump(suggested, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"\nWrote suggestion: {out}")
    print("Diff against the canonical file and merge by hand.\n")


if __name__ == "__main__":
    main()
