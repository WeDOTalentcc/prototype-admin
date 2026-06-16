"""WT-2022 P3.1: AST sensor anti V1 PolicyEngine reintroduction.

Detecta import direto de ``from app.orchestrator.policy_engine import PolicyEngine``
fora de paths whitelisted (legacy V1 itself + bridge V1↔V2 + V2 fallback).

V1 PolicyEngine (``app/orchestrator/policy_engine.py``) é a engine deprecated;
V2 vive em ``app/domains/policy/services/policy_engine_service.py``. Roadmap Q3 2026
prevê deleção de V1.

Modo: STRICT por default (promovido 2026-05-21 — baseline 0 sustentado fora
da allowlist EXEMPT_RELATIVE). Use --warn-only pra rollback emergencial.

Exit codes:
    0 = OK (zero violations fora exempt) ou --warn-only mode
    1 = STRICT default + violations detectadas fora exempt

Uso:
    python3 scripts/check_no_v1_policy_engine.py              # STRICT (default)
    python3 scripts/check_no_v1_policy_engine.py --warn-only  # legacy rollback
    python3 scripts/check_no_v1_policy_engine.py --block      # (deprecated, agora default)
    python3 scripts/check_no_v1_policy_engine.py --threshold N  # ratchet manual
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"

# Paths exempt: V1 itself + bridges legacy + V2 fallback path.
# Caminhos relativos a APP_DIR pra portabilidade (works from any cwd).
EXEMPT_RELATIVE: set[str] = {
    # W1-003 (2026-05-22): V1 PolicyEngine deletado. Allowlist esvaziada.
    # Mantemos apenas paths de bridge defensive (caso V1 reapareça por
    # algum revert acidental — sensor avisa antes de propagar). Após
    # 1 sprint estável (0 violations), remover esses 3 entries.
    "orchestrator/services/policy_gate_service.py",   # bridge V1↔V2 (histórico)
    "orchestrator/orchestrator.py",                    # legacy orchestrator (W3-024)
    "domains/job_creation/policy_gate.py",             # build_default_gate (legacy)
}


def _is_exempt(py_file: Path) -> bool:
    try:
        rel = py_file.relative_to(APP_DIR).as_posix()
    except ValueError:
        return False
    return rel in EXEMPT_RELATIVE


def find_v1_imports(root: Path):
    """Yield (path, lineno) tuples for each V1 PolicyEngine import found."""
    for py_file in root.rglob("*.py"):
        if _is_exempt(py_file):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "app.orchestrator.policy_engine":
                    for alias in node.names:
                        if alias.name == "PolicyEngine":
                            yield (str(py_file.relative_to(ROOT)), node.lineno)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    # WT-2022 P3.1 — promovido warn-only → STRICT em 2026-05-21
    # (baseline 0 fora dos paths exempt; allowlist cobre V1 itself + bridges).
    parser.add_argument(
        "--block",
        action="store_true",
        help="(deprecated, agora default) Exit 1 se houver violation fora allowlist.",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Legacy: nunca falhar mesmo com violations (rollback emergencial).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=None,
        help="Falhar (exit 1) se violations > threshold. Ratchet pattern manual.",
    )
    args = parser.parse_args()

    violations = list(find_v1_imports(APP_DIR))
    count = len(violations)

    if count == 0:
        print("OK: zero V1 PolicyEngine imports fora dos paths exempt.")
        return 0

    mode_label = "warn-only" if args.warn_only else "STRICT"
    print(
        f"WT-2022 P3.1: {count} V1 PolicyEngine imports detectados "
        f"(modo: {mode_label}):",
    )
    for path, line in violations[:50]:
        print(f"  {path}:{line}")
    if count > 50:
        print(f"  ... +{count - 50} more")

    print()
    print(
        "Fix sugerido: substituir por PolicyEngineService (V2) em "
        "``app/domains/policy/services/policy_engine_service.py``. "
        "V1 será deletado Q3 2026 — não adicione imports novos.",
    )

    if args.warn_only:
        print("(--warn-only flag — exit 0; promover para strict ASAP)")
        return 0
    if args.threshold is not None and count > args.threshold:
        print(f"FAIL: {count} > threshold {args.threshold}")
        return 1
    # STRICT default desde 2026-05-21 (WT-2022 ratchet promotion).
    return 1


if __name__ == "__main__":
    sys.exit(main())
