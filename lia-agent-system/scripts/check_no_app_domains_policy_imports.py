"""WT-2022: AST sensor detecta imports de app.domains.policy (DEPRECATED).

Migration plan: usar app.domains.hiring_policy/ canonical em vez de app.domains.policy/.
ADR: ~/Documents/wedotalent_audit_2026-05-21/ADR-WT-2022-policy-domains-migration.md

Modo atual: WARN-ONLY (baseline 2026-05-21).
Quando baseline = 0, virar STRICT (exit 1).

Uso:
    python3 lia-agent-system/scripts/check_no_app_domains_policy_imports.py [--strict]

Exit codes:
    0 = OK (warn-only) ou zero violations (strict).
    1 = violations encontradas (apenas em --strict).
"""
from __future__ import annotations

import ast
import pathlib
import sys
from collections.abc import Iterator


# Baseline confirmado em 2026-05-21 via grep -rn "from app.domains.policy" lia-agent-system
# 39 distinct AST ImportFrom nodes em ~20 arquivos (production+tests, dedup self-imports excluidos). Refresh quando Phase 2+ rodar.
BASELINE_2026_05_21 = 39

# Self-imports DENTRO de policy/ não contam (são internal refactor, não cross-domain leak).
# Cross-import legitimate de hiring_policy DENTRO de policy/ é OK (bridge transitional).
EXCLUDE_PREFIXES = (
    "lia-agent-system/app/domains/policy/",  # internal self-imports
)


def find_violations(root: pathlib.Path) -> Iterator[tuple[str, int, str]]:
    """Walk root, yield (relpath, lineno, module) per import de app.domains.policy."""
    for py_file in root.rglob("*.py"):
        rel = str(py_file).replace(str(pathlib.Path.cwd()) + "/", "")
        # Skip self-imports inside policy/ domain
        if any(rel.startswith(p) or ("/" + p) in rel for p in EXCLUDE_PREFIXES):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == "app.domains.policy" or mod.startswith("app.domains.policy."):
                    yield (rel, node.lineno, mod)


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    root = pathlib.Path("lia-agent-system/app")
    if not root.exists():
        # Allow running from inside lia-agent-system/
        alt = pathlib.Path("app")
        if alt.exists():
            root = alt
        else:
            print(f"ERROR: nem 'lia-agent-system/app' nem 'app' encontrados em {pathlib.Path.cwd()}")
            return 2

    tests_root = root.parent / "tests"
    roots = [root]
    if tests_root.exists():
        roots.append(tests_root)

    violations: list[tuple[str, int, str]] = []
    for r in roots:
        violations.extend(find_violations(r))

    count = len(violations)
    if count == 0:
        print("OK: zero imports de app.domains.policy. Sensor pode virar STRICT.")
        return 0

    print(f"WT-2022: {count} imports de app.domains.policy detectados (baseline 2026-05-21 = {BASELINE_2026_05_21})")
    print(f"ADR: ~/Documents/wedotalent_audit_2026-05-21/ADR-WT-2022-policy-domains-migration.md")
    print(f"")
    print(f"Fix sugerido: substituir por equivalente em app.domains.hiring_policy/")
    print(f"  - PolicySetupAgent           -> hiring_policy.agents.policy_react_agent.PolicyReActAgent")
    print(f"  - stage_context              -> hiring_policy.agents.policy_stage_context")
    print(f"  - system_prompt              -> hiring_policy.agents.policy_system_prompt")
    print(f"  - tool_registry              -> hiring_policy.agents.policy_tool_registry")
    print(f"  - PolicyEngineService         -> aguarda decisao Phase 3 ADR (Anderson)")
    print(f"  - GlobalPolicyRepository      -> aguarda decisao Phase 3 ADR (Anderson)")
    print(f"  - ALPHA1_SECTOR_RULES         -> aguarda decisao Phase 3 ADR (Anderson)")
    print(f"")
    print(f"Primeiros 30 sites:")
    for path, line, mod in violations[:30]:
        print(f"  {path}:{line}: from {mod} import ...")
    if count > 30:
        print(f"  ... +{count - 30} more")

    if strict:
        return 1
    # warn-only durante migration phase
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
