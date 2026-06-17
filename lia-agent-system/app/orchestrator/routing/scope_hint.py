"""ScopeHint — Fase C.2 (2026-06-09).

Emitted by Tier 7 in federated mode when a first-party Studio agent
covers the classified domain. The scope resolver uses this to augment
the federated agent's tool scope without instantiating a separate runtime.

Federated mode: Tier 7 returns ScopeHint → no runtime fork, just scope info.
Legacy mode:    Tier 7 returns RouteResult → CustomAgentRuntime executes directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScopeHint:
    """Lightweight signal emitted by Tier 7 in federated mode.

    The scope resolver (get_scoped_tool_definitions in tool_catalog.py, via
    studio_scope_extension) already augmented the federated agent's tool set.
    ScopeHint carries observability metadata only — it does NOT trigger any
    runtime instantiation.

    Fields:
        domain:  The classified domain that triggered the Studio match
                 (e.g. "talent_analysis", "interview_analysis").
        source:  "studio_first_party" if matched a global first-party agent;
                 "studio_deployment" if matched a tenant-scoped deployment.
        tools:   Snapshot of allowed_tools from the matched agent manifest
                 (informational only — actual tool injection happens in the
                 scope resolver, not here).
    """

    domain: str
    source: str  # "studio_first_party" | "studio_deployment"
    tools: list[str] = field(default_factory=list)
