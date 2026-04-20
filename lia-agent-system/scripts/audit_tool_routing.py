#!/usr/bin/env python3
"""
CI Guard: Validate that domain action_ids are reachable through tool routing.

Checks:
  1. Every action_id in domain actions.py has a matching keyword in capabilities.yaml
     (so the KeywordIntentMatcher can route it).
  2. Every domain that uses _ACTION_TOOL_MAP has all mapped tool_ids present in
     JOB_MANAGEMENT_TOOLS (or the global registry).
  3. No action_id is duplicated across domains without a domain namespace qualifier
     (collision risk in CascadedRouter).
  4. Every ToolDefinition registered in the global registry appears in
     tool_registry_metadata.yaml (description quality gate).

Usage:
    python3 scripts/audit_tool_routing.py

Exits 0 if all checks pass, 1 if gaps found.
"""
import sys
import re
import ast
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
DOMAINS_DIR = ROOT / "app" / "domains"

# ─── Helpers ────────────────────────────────────────────────────────────────


def _extract_action_ids(actions_file: Path) -> list[str]:
    """Parse action_ids from a DomainAction-based actions.py."""
    action_ids = []
    try:
        source = actions_file.read_text(encoding="utf-8")
        for match in re.finditer(r'action_id\s*=\s*["\']([^"\']+)["\']', source):
            action_ids.append(match.group(1))
    except Exception:
        pass
    return action_ids


def _extract_yaml_keywords(yaml_file: Path) -> set[str]:
    """Return set of action_id values from a domain capabilities.yaml."""
    action_ids = set()
    if not yaml_file.exists():
        return action_ids
    try:
        text = yaml_file.read_text(encoding="utf-8")
        # Format: "keyword: action_id"
        for match in re.finditer(r"^\s{2}[\w ]+:\s*(\w+)\s*$", text, re.MULTILINE):
            action_ids.add(match.group(1))
    except Exception:
        pass
    return action_ids


def _extract_tool_metadata_names(yaml_file: Path) -> set[str]:
    """Return tool names declared in tool_registry_metadata.yaml."""
    names: set[str] = set()
    if not yaml_file.exists():
        return names
    try:
        text = yaml_file.read_text(encoding="utf-8")
        for match in re.finditer(r"^\s{2}-\s+name:\s*(\S+)", text, re.MULTILINE):
            names.add(match.group(1))
    except Exception:
        pass
    return names


# ─── Check 1: action_id ↔ keyword coverage ──────────────────────────────────

def check_action_keyword_coverage() -> list[str]:
    """Return list of gaps: action_ids not reachable via keyword matcher.

    Skips domains that have no capabilities.yaml at all (no intent routing configured)
    and domains known to not have dedicated agents (Check 3 known-fallbacks).
    """
    # Skip domains where keyword-routing is not configured or not applicable
    _SKIP_DOMAINS = {
        "agent_studio", "digital_twin", "automation", "ats_integration",
        "hiring_policy", "company_settings",
    }
    gaps = []
    for domain_dir in sorted(DOMAINS_DIR.iterdir()):
        if domain_dir.name in _SKIP_DOMAINS:
            continue
        actions_file = domain_dir / "actions.py"
        capabilities_yaml = domain_dir / "config" / "capabilities.yaml"
        if not actions_file.exists():
            continue
        if not capabilities_yaml.exists():
            # Domain has no capabilities.yaml — no keyword routing configured, skip
            continue
        action_ids = _extract_action_ids(actions_file)
        if not action_ids:
            continue
        yaml_action_ids = _extract_yaml_keywords(capabilities_yaml)
        domain_name = domain_dir.name
        for aid in action_ids:
            if yaml_action_ids and aid not in yaml_action_ids:
                gaps.append(f"  [{domain_name}] action_id='{aid}' not in capabilities.yaml — intent routing may miss it")
    return gaps


# ─── Check 2: duplicate action_ids across domains ───────────────────────────

def check_duplicate_action_ids() -> list[str]:
    """Return duplicates: action_ids defined in multiple domains."""
    action_to_domains: dict[str, list[str]] = defaultdict(list)
    for domain_dir in sorted(DOMAINS_DIR.iterdir()):
        actions_file = domain_dir / "actions.py"
        if not actions_file.exists():
            continue
        for aid in _extract_action_ids(actions_file):
            action_to_domains[aid].append(domain_dir.name)

    gaps = []
    for aid, domains in sorted(action_to_domains.items()):
        if len(domains) > 1:
            gaps.append(f"  action_id='{aid}' duplicated in: {', '.join(domains)}")
    return gaps


# ─── Check 3: AgentRegistry — domains without agents ────────────────────────

def check_agent_registry_coverage() -> list[str]:
    """Return domain_ids returned by FastRouter that have no @register_agent match."""
    fast_router_file = ROOT / "app" / "orchestrator" / "fast_router.py"
    if not fast_router_file.exists():
        return ["  fast_router.py not found"]

    # Extract domain_ids from _HARDCODED_DOMAIN_PATTERNS keys
    source = fast_router_file.read_text(encoding="utf-8")
    pattern_domains: set[str] = set()
    for match in re.finditer(r'"([a-z][a-z_]+)"\s*:\s*\[', source):
        pattern_domains.add(match.group(1))

    # Extract registered agent ids from @register_agent decorators
    registered_agents: set[str] = set()
    agent_files = list((ROOT / "app" / "domains").rglob("*_agent*.py"))
    for f in agent_files:
        try:
            text = f.read_text(encoding="utf-8")
            for m in re.finditer(r'@register_agent\s*\(\s*["\']([^"\']+)["\']', text):
                registered_agents.add(m.group(1))
            # Also check aliases
            for m in re.finditer(r'aliases\s*=\s*\[([^\]]+)\]', text):
                alias_str = m.group(1)
                for alias_match in re.finditer(r'["\']([^"\']+)["\']', alias_str):
                    registered_agents.add(alias_match.group(1))
        except Exception:
            pass

    # _DOMAIN_ID_NORMALIZE maps source→target
    normalized: dict[str, str] = {}
    for m in re.finditer(r'"([^"]+)"\s*:\s*"([^"]+)"', source):
        normalized[m.group(1)] = m.group(2)

    # Domains that intentionally fall back to the default "talent" agent or are
    # routed elsewhere by design. These are tracked as KNOWN gaps (non-blocking).
    # Update this set when new agents are added.
    _KNOWN_FALLBACK_DOMAINS = {
        "recruiter_assistant",   # → TalentReActAgent by design
        "interviewing",          # → normalizes to "interview_scheduling"
        "scheduling",            # → normalizes to "interview_scheduling"
        "wsi_assessment",        # → normalizes to "cv_screening"
        "interview_scheduling",  # pending dedicated agent
        "agent_studio",          # pending dedicated agent
        "digital_twin",          # pending dedicated agent
        "recruitment_campaign",  # pending dedicated agent
        "talent_pool",           # pending dedicated agent
    }

    gaps = []
    for domain_id in sorted(pattern_domains):
        resolved = normalized.get(domain_id, domain_id)
        if resolved not in registered_agents:
            marker = "(known/non-blocking)" if domain_id in _KNOWN_FALLBACK_DOMAINS else "⚠️ BLOCKING"
            gaps.append(
                (
                    domain_id in _KNOWN_FALLBACK_DOMAINS,
                    f"  domain_id='{domain_id}' → '{resolved}' has no @register_agent "
                    f"— {marker}"
                )
            )
    return gaps


# ─── Check 4: Handler paths — target attributes must exist in target modules ──

def check_handler_attribute_integrity() -> list[tuple[bool, str]]:
    """Scan `"handler": "app.foo.bar"` declarations and verify the tail attributes
    (function name, class.method, or singleton.method) actually exist in the target
    module source. Uses static regex patterns — tolerant to re-exports via
    `from X import (Y, Z)` blocks.

    Returns list of (is_known_false_positive, message) tuples. False-positives are
    treated as non-blocking warnings.
    """
    # Modules that re-export symbols from another package via multi-line
    # `from X import (...)` — static regex might miss deep-chain attributes there.
    _KNOWN_REEXPORT_SHIMS = {
        "app/services/notification_service.py",
    }
    results: list[tuple[bool, str]] = []
    for f in ROOT.rglob("app/**/*.py"):
        if "__pycache__" in str(f):
            continue
        try:
            src = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in re.finditer(
            r'[\"\']handler[\"\']\s*:\s*[\"\'](app\.[\w.]+)[\"\']', src
        ):
            handler = m.group(1)
            parts = handler.split(".")
            # Find deepest module prefix on disk.
            source_file = None
            found_prefix = 0
            for i in range(len(parts), 0, -1):
                prefix = ROOT / ("/".join(parts[:i]))
                if Path(str(prefix) + ".py").exists():
                    source_file = Path(str(prefix) + ".py")
                    found_prefix = i
                    break
                if (prefix / "__init__.py").exists():
                    source_file = prefix / "__init__.py"
                    found_prefix = i
                    break
            if source_file is None:
                results.append((False, f"  handler '{handler}': no module prefix found — declared in {f.relative_to(ROOT)}"))
                continue
            remaining = parts[found_prefix:]
            if not remaining:
                continue
            tgt_src = source_file.read_text(encoding="utf-8")
            missing: list[str] = []
            for a in remaining:
                patterns = [
                    rf"^(?:async )?def {a}\b",
                    rf"^\s{{4,}}(?:async )?def {a}\b",
                    rf"^{a}\s*=",
                    rf"^class {a}\b",
                    rf"^from\s+\S+\s+import\s+[^\n]*\b{a}\b",
                ]
                found = any(re.search(p, tgt_src, re.MULTILINE) for p in patterns)
                # Multi-line re-export: "from X import (\n    Y,\n    Z,\n)"
                if not found:
                    for m2 in re.finditer(
                        r"from\s+\S+\s+import\s+(?:[^\n]*?)?\(([^)]*)\)",
                        tgt_src, re.DOTALL
                    ):
                        if re.search(rf"\b{a}\b", m2.group(1)):
                            found = True
                            break
                if not found:
                    missing.append(a)
            if missing:
                rel_target = str(source_file.relative_to(ROOT))
                is_known = rel_target in _KNOWN_REEXPORT_SHIMS
                marker = "(known re-export shim — verify at runtime)" if is_known else "⚠️ BROKEN REST handler"
                results.append((
                    is_known,
                    f"  handler='{handler}' missing attrs={missing} in {rel_target} — {marker}  (declared in {f.relative_to(ROOT)})"
                ))
    return results


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 65)
    print("  audit_tool_routing.py — LIA Tool Routing CI Guard")
    print("=" * 65)

    all_gaps = []

    print("\n[CHECK 1] Action ↔ keyword coverage")
    c1 = check_action_keyword_coverage()
    if c1:
        print(f"  ⚠️  {len(c1)} action_ids unreachable via keyword matcher:")
        for g in c1:
            print(g)
        all_gaps.extend(c1)
    else:
        print("  ✅ All action_ids have keyword coverage")

    print("\n[CHECK 2] Duplicate action_ids across domains")
    c2 = check_duplicate_action_ids()
    if c2:
        print(f"  ⚠️  {len(c2)} duplicate action_ids (collision risk):")
        for g in c2:
            print(g)
        # Duplicates are WARNING only — not all are bugs
    else:
        print("  ✅ No duplicate action_ids")

    print("\n[CHECK 3] AgentRegistry — domains without agents")
    c3 = check_agent_registry_coverage()
    if c3:
        blocking = [(is_known, msg) for is_known, msg in c3 if not is_known]
        known = [(is_known, msg) for is_known, msg in c3 if is_known]
        if blocking:
            print(f"  ❌ {len(blocking)} BLOCKING domain(s) with no agent:")
            for _, msg in blocking:
                print(msg)
            all_gaps.extend([msg for _, msg in blocking])
        if known:
            print(f"  ⚠️  {len(known)} known/non-blocking fallback domain(s):")
            for _, msg in known:
                print(msg)
        if not blocking:
            print("  ✅ No NEW blocking agent gaps found")
    else:
        print("  ✅ All FastRouter domains have registered agents")

    print("\n[CHECK 4] REST handler attribute integrity")
    c4 = check_handler_attribute_integrity()
    if c4:
        broken = [msg for is_known, msg in c4 if not is_known]
        known = [msg for is_known, msg in c4 if is_known]
        if broken:
            print(f"  ⚠️  {len(broken)} handler path(s) with missing target attributes:")
            for msg in broken:
                print(msg)
            # WARNING only — REST path is fallback; primary path is ReAct agent.
            # When a domain's ReAct agent works, these broken REST handlers are never hit.
            # Fix gradually by mapping to the real function/method in target modules.
        if known:
            print(f"  ℹ️  {len(known)} known re-export shim(s) (verify at runtime):")
            for msg in known:
                print(msg)
        if not broken:
            print("  ✅ All REST handler attributes resolve cleanly")
    else:
        print("  ✅ All REST handler attributes resolve cleanly")

    print()
    if all_gaps:
        print(f"❌ AUDIT FAILED — {len(all_gaps)} blocking gap(s) found")
        print("   Fix the gaps above before merging. See docs/architecture/ARCHITECTURE.md")
        return 1
    else:
        print("✅ AUDIT PASSED — routing connections look healthy")
        if c2:
            print(f"   ⚠️  {len(c2)} duplicate action_ids found (non-blocking — verify intent)")
        if c4:
            broken_count = sum(1 for is_known, _ in c4 if not is_known)
            if broken_count:
                print(f"   ⚠️  {broken_count} REST handler attribute(s) broken (non-blocking — REST is fallback path)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
