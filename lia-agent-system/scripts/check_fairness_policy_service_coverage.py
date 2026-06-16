#!/usr/bin/env python3
"""
Sensor AST: check_fairness_policy_service_coverage.py

Detects agent files in app/domains/*/agents/ that call allows_automated_decision
or auto_approve without importing/calling FairnessPolicyService.

Warn-only mode (exits 0 even with violations).

Usage:
    python3 scripts/check_fairness_policy_service_coverage.py [--root /path/to/project]
"""
import ast
import os
import sys
from pathlib import Path


SUSPICIOUS_CALLS = {"allows_automated_decision", "auto_approve", "automated_decision"}
SAFE_IMPORTS = {"FairnessPolicyService", "fairness_policy_service", "_get_fairness_service"}


def _has_fairness_service(tree: ast.AST) -> bool:
    """Returns True if the file imports or uses FairnessPolicyService."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            src = ast.dump(node)
            if any(safe in src for safe in SAFE_IMPORTS):
                return True
        if isinstance(node, ast.Name) and node.id in SAFE_IMPORTS:
            return True
        if isinstance(node, ast.Attribute) and node.attr in SAFE_IMPORTS:
            return True
    return False


def _has_suspicious_call(tree: ast.AST) -> list[tuple[int, str]]:
    """Returns list of (lineno, call_name) for suspicious calls found."""
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in SUSPICIOUS_CALLS:
                hits.append((node.lineno, node.func.attr))
            elif isinstance(node.func, ast.Name) and node.func.id in SUSPICIOUS_CALLS:
                hits.append((node.lineno, node.func.id))
    return hits


def scan_agents(root: Path) -> list[str]:
    violations = []
    agents_pattern = root / "app" / "domains"

    if not agents_pattern.exists():
        print(f"[fairness-coverage] No domains dir found at {agents_pattern}, skipping.")
        return violations

    for agent_file in agents_pattern.rglob("agents/*.py"):
        if agent_file.name.startswith("__"):
            continue
        try:
            source = agent_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(agent_file))
        except (SyntaxError, OSError) as exc:
            print(f"[fairness-coverage] SKIP {agent_file}: {exc}")
            continue

        suspicious = _has_suspicious_call(tree)
        if not suspicious:
            continue  # no suspicious calls at all

        has_guard = _has_fairness_service(tree)
        if not has_guard:
            for lineno, call_name in suspicious:
                rel_path = agent_file.relative_to(root)
                msg = (
                    f"[fairness-coverage] WARN {rel_path}:{lineno} "
                    f"calls '{call_name}' without FairnessPolicyService. "
                    f"→ Fix: import FairnessPolicyService and call allows_automated() before automated decisions."
                )
                violations.append(msg)

    return violations


def main() -> int:
    root = Path("/home/runner/workspace/lia-agent-system")
    if "--root" in sys.argv:
        idx = sys.argv.index("--root")
        if idx + 1 < len(sys.argv):
            root = Path(sys.argv[idx + 1])

    violations = scan_agents(root)

    if violations:
        print(f"\n[fairness-coverage] {len(violations)} violation(s) found (warn-only):\n")
        for v in violations:
            print(v)
        print(
            "\n[fairness-coverage] WARN: The above agents may bypass fairness policies. "
            "Import FairnessPolicyService and call allows_automated() before automated decisions.\n"
        )
    else:
        print("[fairness-coverage] OK — no uncovered automated decision calls found.")

    return 0  # warn-only: always exit 0


if __name__ == "__main__":
    sys.exit(main())
