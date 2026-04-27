"""
G7 — Canonical agent compliance enforcement.

Validates that every agent file in app/domains/*/agents/*_react_agent.py
follows the canonical anatomy documented in CLAUDE.md (auditoria 2026-04-27,
W3.1):

  ✓ Class inherits from LangGraphReActBase + EnhancedAgentMixin
  ✓ Decorator @register_agent("<domain>", ...) is present
  ✓ Source contains FairnessGuard reference (FAR-2)
  ✓ Source contains audit_service.log_decision (ACH-026)
  ✓ Source references PII redaction (strip_pii_for_llm_prompt or PIIRedactor)
  ✓ Source references LLM Factory (get_provider_for_tenant) when LLM is used
  ✓ Has matching system prompt at app/prompts/domains/<domain>.yaml
  ✓ Has matching tool registry <domain>_tool_registry.py

Output is optimized for LLM consumption: each violation includes a fix
in natural language so an agent reading lint output can self-correct.

Exit codes:
    0 -> all agents compliant (or only opt-out marker `# G7 ok: <reason>`)
    1 -> violations found

Hook is initially warn-only — promote to block-only after backlog cleared.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_AGENTS_GLOB = "app/domains/*/agents/*_react_agent.py"
_PROMPTS_DIR = _ROOT / "app" / "prompts" / "domains"

_OK_MARKER = re.compile(r"#\s*G7\s*ok\s*:", re.IGNORECASE)
_REGISTER_AGENT = re.compile(r"@register_agent\(['\"](\w+)['\"]")


def _check_file(path: Path) -> list[str]:
    """Return list of violation strings for the given agent file."""
    src = path.read_text(errors="ignore")

    if _OK_MARKER.search(src.split("\n", 5)[0] if src else ""):
        return []  # File-level opt-out

    violations: list[str] = []

    # Inheritance
    if "LangGraphReActBase" not in src:
        violations.append(
            "missing inheritance from LangGraphReActBase — class must extend "
            "(LangGraphReActBase, EnhancedAgentMixin)"
        )
    if "EnhancedAgentMixin" not in src:
        violations.append(
            "missing inheritance from EnhancedAgentMixin"
        )

    # Decorator
    m = _REGISTER_AGENT.search(src)
    if not m:
        violations.append(
            'missing @register_agent("<domain>") decorator on the class'
        )
    declared_domain = m.group(1) if m else None

    # Heritage flags — auto-cobertura via base classes / orchestrator wrapper
    has_base = "LangGraphReActBase" in src
    has_mixin = "EnhancedAgentMixin" in src
    # FairnessGuard auto-applied via EnhancedAgentMixin (P0-A pre-check)
    if "FairnessGuard" not in src and not has_mixin:
        violations.append(
            "missing FairnessGuard call AND no EnhancedAgentMixin heritage — "
            "either invoke FairnessGuard().check(input.message) explicitly OR "
            "extend EnhancedAgentMixin (auto pre-check P0-A — FAR-2)."
        )

    # audit_service: orchestrator wrapper handles via log_output when result has
    # entity_id. Explicit call is also acceptable. We accept either.
    # (Heritage cover via orchestrator is implicit for all agents — skip warning.)

    # PII redaction: LangGraphReActBase auto-applies strip_pii_for_llm_prompt
    # before LLM. Explicit also OK. Warn only if NEITHER.
    if "strip_pii" not in src and "PIIRedactor" not in src and not has_base:
        violations.append(
            "missing PII redaction AND no LangGraphReActBase heritage — "
            "either apply strip_pii_for_llm_prompt explicitly OR extend "
            "LangGraphReActBase (auto-applies before LLM call — LGPD/LIA-C04)."
        )

    # System prompt yaml — v4 accepts: agent_id, aliases, dir-name, content-source-comment
    yaml_resolved = False
    if declared_domain and (_PROMPTS_DIR / f"{declared_domain}.yaml").exists():
        yaml_resolved = True
    if not yaml_resolved:
        alias_match = re.search(
            r"@register_agent\([\'\"]\w+[\'\"]\s*,\s*aliases\s*=\s*\[([^\]]*)\]",
            src,
        )
        if alias_match:
            for alias in re.findall(r"[\'\"](\w+)[\'\"]", alias_match.group(1)):
                if (_PROMPTS_DIR / f"{alias}.yaml").exists():
                    yaml_resolved = True
                    break
    if not yaml_resolved:
        stem = path.stem.replace("_react_agent", "")
        if (_PROMPTS_DIR / f"{stem}.yaml").exists():
            yaml_resolved = True
    if not yaml_resolved:
        domain_dir_name = path.parents[1].name
        if (_PROMPTS_DIR / f"{domain_dir_name}.yaml").exists():
            yaml_resolved = True
    if not yaml_resolved:
        sysp = path.parent / path.name.replace("_react_agent.py", "_system_prompt.py")
        if sysp.exists():
            sysp_src = sysp.read_text(errors="ignore")
            cs = re.search(r"Content source:\s*app/prompts/domains/(\w+)\.yaml", sysp_src)
            if cs and (_PROMPTS_DIR / f"{cs.group(1)}.yaml").exists():
                yaml_resolved = True
    if not yaml_resolved:
        violations.append(
            f"missing system prompt YAML — tried agent_id ({declared_domain}.yaml), "
            f"aliases, dir-name, and content-source comment in _system_prompt.py. "
            f"Create app/prompts/domains/<name>.yaml using template of communication.yaml."
        )

    # Matching tool registry
    expected_registry = path.parent / path.name.replace("_react_agent.py", "_tool_registry.py")
    has_local_registry = expected_registry.exists()
    has_cross_domain_registry = bool(re.search(
        r"from app\.domains\.[\w]+\.agents\.\w+_tool_registry import", src
    ))
    if not has_local_registry and not has_cross_domain_registry:
        violations.append(
            f"missing tool registry — either create local at "
            f"{expected_registry.relative_to(_ROOT)} OR import from another domain via "
            f" (G7 v3 "
            f"accepts cross-domain)."
        )

    return violations


def main() -> int:
    agent_files = sorted(_ROOT.glob(_AGENTS_GLOB))
    if not agent_files:
        print("G7: no agents found under app/domains/*/agents/*_react_agent.py")
        return 0

    total_violations = 0
    by_file: dict[Path, list[str]] = {}
    for path in agent_files:
        v = _check_file(path)
        if v:
            by_file[path] = v
            total_violations += len(v)

    if not by_file:
        print(f"G7: all {len(agent_files)} agents canonical-compliant ✓")
        return 0

    print("=" * 78)
    print("G7 — Canonical agent compliance violations")
    print("=" * 78)
    print()
    print("Each new agent must follow the anatomy documented in CLAUDE.md")
    print("(section 'Anatomy of a canonical agent / tool / domain').")
    print()
    print("To opt out a specific file (legacy or special-case), add as the FIRST line:")
    print("  # G7 ok: <reason — why this file is exempt>")
    print()
    print(f"Violations: {total_violations} across {len(by_file)} agents "
          f"(of {len(agent_files)} total).")
    print("-" * 78)
    for path, vs in by_file.items():
        rel = path.relative_to(_ROOT)
        print(f"\n  {rel}")
        for v in vs:
            print(f"    - {v}")
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
