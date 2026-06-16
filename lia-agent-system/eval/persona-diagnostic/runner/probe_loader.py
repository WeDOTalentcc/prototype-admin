"""Load the persona-diagnostic probe sheet from YAML."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROBES_YAML = Path(__file__).resolve().parent.parent / "probes.yaml"


def load_probes(
    only_ids: list[str] | None = None,
    only_categories: list[str] | None = None,
    only_agents: list[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return (meta, probes). All filters are intersected."""
    data = yaml.safe_load(PROBES_YAML.read_text(encoding="utf-8"))
    meta = data.get("meta", {})
    probes = data["probes"]

    if only_ids:
        wanted = {x.strip() for x in only_ids}
        probes = [p for p in probes if p["id"] in wanted]
    if only_categories:
        wanted = {x.strip().lower() for x in only_categories}
        probes = [
            p for p in probes
            if p["category"].lower() in wanted
            or p["category"].split(".")[0].strip().lower() in wanted
        ]
    if only_agents:
        wanted = {x.strip().upper() for x in only_agents}
        probes = [p for p in probes if p["agent"].upper() in wanted]

    return meta, probes
