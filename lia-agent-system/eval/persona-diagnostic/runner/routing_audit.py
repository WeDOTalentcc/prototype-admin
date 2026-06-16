"""
Persona Diagnostic — Routing audit.

The runner only *hints* the CascadedRouter via context.scope/page; routing is
heuristic, so a probe targeted at WSI may very well end up answered by the
default LIA agent. The capture records `agent_observed` (extracted from the
chat response payload) — this module compares it against the probe's intended
target and flags mismatches so we can tell when probes aren't really exercising
the agent we think they are.

The output is consumed by `report.py` and by the unit test under `tests/`.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

# Canonical agent codes used in probes.yaml.
AGENT_CODES = ("LIA", "JOB", "SRC", "CVS", "INT", "WSI", "ORC")

# Substrings that appear in the agent identifier the backend returns. The
# CascadedRouter / specialist services use a variety of names (see e.g.
# `agent_name="wsi_question_generator"` or `"sourcing_pipeline_service"`),
# so we map by substring on the lowercased value rather than exact match.
_ALIASES: dict[str, tuple[str, ...]] = {
    "JOB": ("job", "vaga", "wizard"),
    "SRC": ("src", "sourcing", "candidate_search", "search_pipeline"),
    "CVS": ("cvs", "screening", "cv_screen", "resume"),
    "INT": ("int", "interview", "interviewer"),
    "WSI": ("wsi", "rubric_evaluation", "question_generator"),
    "ORC": ("orc", "orchestrat"),
    # LIA matches last and only as a fallback when nothing else hits.
    "LIA": ("lia", "default", "root", "general", "assistant"),
}

# Categories J.1 – J.6 are the agent-specific ones the task calls out.
AGENT_SPECIFIC_PREFIX = "J."


def normalise_observed(raw: Any) -> str | None:
    """Map whatever the backend returned to a canonical agent code, or None.

    Returns one of `AGENT_CODES` if a confident match is found, otherwise
    None (which is reported as 'unknown' in the audit).
    """
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip().lower()
    if not s:
        return None
    # Exact code first (case-insensitive).
    for code in AGENT_CODES:
        if s == code.lower():
            return code
    # Then substring aliases — order matters so the more specific specialists
    # win over the catch-all LIA aliases.
    for code in ("WSI", "INT", "CVS", "SRC", "JOB", "ORC", "LIA"):
        for needle in _ALIASES[code]:
            if needle in s:
                return code
    return None


def is_agent_specific(probe: dict) -> bool:
    """A probe counts as agent-specific when it targets a non-LIA specialist.

    Per the task we focus on the J.1–J.6 categories (Job Planner, Sourcing,
    CV Screening, Interviewer, WSI Evaluator, Orchestrator).
    """
    cat = (probe.get("category") or "")
    if cat.startswith(AGENT_SPECIFIC_PREFIX):
        return True
    # Belt-and-braces: any probe targeted at a specialist also counts.
    return (probe.get("agent") or "").upper() in {"JOB", "SRC", "CVS", "INT", "WSI", "ORC"}


def audit(results: Iterable[dict]) -> dict[str, Any]:
    """Build the routing-audit block.

    Shape:
      {
        "summary": {
          "agent_specific_total": int,
          "matched": int,
          "mismatched": int,
          "unknown": int,
          "match_rate": float,            # matched / (matched + mismatched)
          "match_rate_threshold": 0.9,
          "pass": bool,
        },
        "per_agent": [
          {"agent": "WSI", "n": 7, "matched": 6, "mismatched": 1,
           "unknown": 0, "match_rate": 0.86},
          …
        ],
        "mismatches": [
          {"id": "WSI-003", "agent": "WSI", "agent_observed": "lia_agent",
           "agent_observed_code": "LIA", "category": "J.5 …",
           "prompt": "…"},
          …
        ],
      }
    """
    items = list(results)
    specific = [r for r in items if is_agent_specific(r)]

    per_agent: dict[str, dict[str, int]] = defaultdict(
        lambda: {"n": 0, "matched": 0, "mismatched": 0, "unknown": 0}
    )
    mismatches: list[dict[str, Any]] = []

    for r in specific:
        target = (r.get("agent") or "").upper()
        observed_raw = r.get("agent_observed")
        observed_code = normalise_observed(observed_raw)
        bucket = per_agent[target]
        bucket["n"] += 1
        if observed_code is None:
            bucket["unknown"] += 1
            mismatches.append({
                "id": r.get("id"),
                "category": r.get("category"),
                "agent": target,
                "agent_observed": observed_raw,
                "agent_observed_code": None,
                "kind": "unknown",
                "prompt": r.get("prompt"),
            })
        elif observed_code == target:
            bucket["matched"] += 1
        else:
            bucket["mismatched"] += 1
            mismatches.append({
                "id": r.get("id"),
                "category": r.get("category"),
                "agent": target,
                "agent_observed": observed_raw,
                "agent_observed_code": observed_code,
                "kind": "mismatched",
                "prompt": r.get("prompt"),
            })

    matched = sum(b["matched"] for b in per_agent.values())
    mismatched = sum(b["mismatched"] for b in per_agent.values())
    unknown = sum(b["unknown"] for b in per_agent.values())
    total = matched + mismatched + unknown
    decided = matched + mismatched
    match_rate = round(matched / decided, 3) if decided else 0.0
    threshold = 0.9

    per_agent_list = []
    for code in AGENT_CODES:
        if code not in per_agent:
            continue
        b = per_agent[code]
        d = b["matched"] + b["mismatched"]
        per_agent_list.append({
            "agent": code,
            "n": b["n"],
            "matched": b["matched"],
            "mismatched": b["mismatched"],
            "unknown": b["unknown"],
            "match_rate": round(b["matched"] / d, 3) if d else 0.0,
        })

    return {
        "summary": {
            "agent_specific_total": total,
            "matched": matched,
            "mismatched": mismatched,
            "unknown": unknown,
            "match_rate": match_rate,
            "match_rate_threshold": threshold,
            # Pass only when we actually have observations to judge against.
            "pass": decided > 0 and match_rate >= threshold,
        },
        "per_agent": per_agent_list,
        "mismatches": mismatches,
    }
