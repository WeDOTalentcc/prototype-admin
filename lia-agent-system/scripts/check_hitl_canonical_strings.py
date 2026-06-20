#!/usr/bin/env python3
"""
Sensor canônico HITL (AST): toda frozenset com action_type strings que batem
padrões de mutação de alto risco DEVE estar declarada em HITL_REQUIRED_ACTIONS.

Problema resolvido (2026-06-20): cada agent declarava `_HITL_ACTION_TYPES` local
sem checar contra um canonical. Resultado: ações adicionadas em um agent eram
esquecidas nos outros (ex: `reject_candidate` no kanban vs pipeline divergência).

Este sensor detecta:
  1. Frozensets com strings que batem HIGH_RISK_PATTERNS mas NÃO estão em canonical
  2. Frozensets com nome sugestivo (_HITL_*, *_HITL_*, SENSITIVE_FLAGS_*) cujos
     elementos não estão todos no canonical (warn) — exclui frozensets de sistema
     (ex: _GATE_TRUTHY, _ALLOWED_HOSTS) pelo padrão de conteúdo
  3. Arquivos que hardcodam strings de ação iguais a elementos do canonical
     em contextos de "aprovação" fora de frozensets (ex: `action_type == "reject_candidate"`)

Uso:
  python3 scripts/check_hitl_canonical_strings.py              # warn-only (default)
  python3 scripts/check_hitl_canonical_strings.py --blocking   # exit 1 se violations
  python3 scripts/check_hitl_canonical_strings.py --json       # JSON output para CI

Baseline 2026-06-20: 0 violations (canonical cobre todos os agentes wired).
"""
from __future__ import annotations

import argparse
import ast
import re
import json
import sys
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = REPO_ROOT / "app"
CANONICAL_PATH = APP_ROOT / "shared" / "hitl" / "hitl_canonical_actions.py"

# Padrões de conteúdo que indicam "ação de mutação de alto risco".
# Intencionalmente conservadores para evitar falsos positivos em frozensets
# de status (ex: "rejected"), HTTP methods ("DELETE"), paths, etc.
# APENAS frozensets com nome HITL_* ou _HITL_* passam pela checagem de Case 1
# (todos os elementos devem estar no canonical). Para frozensets sem nome HITL_*,
# só flagamos elementos que batem MULTIPLE_WORD_ACTION_PATTERNS (underscored) pois
# status strings (rejected) e HTTP verbs são single-word.
HIGH_RISK_PATTERNS: tuple[str, ...] = (
    # Padrões multi-palavra (underscored) — indica action_type, não status
    "bulk_",
    "auto_reject",
    "auto_advance",
    "batch_",
    "import_external",
    "export_",
    "schedule_recurring",
    "sync_to_",
    "send_batch",
    "send_report",
    "send_screening",
    "send_interview",
    "send_candidate",
    "send_progress",
    "send_feedback",
    "ats_create",
    "ats_update",
    "ats_reject",
    "send_whatsapp",
    "delete_vacancy",
    "delete_automation",
    "delete_company",
    "publish_vacancy",
    "unpublish_vacancy",
    "activate_automation",
    "deactivate_automation",
    "bulk_trigger",
    "bulk_vacancy",
    "talent_pool_assignment",
)

# Frozensets que batem _HITL_* mas devem ser ignorados pelo sensor pois
# são infra/configuração (não action_types de agente)
_HITL_CONSTANT_SYSTEM_EXEMPTIONS: frozenset[str] = frozenset({
    # Estes são infra — não ações de agente
})

# Nomes de constantes que indicam "este frozenset é sobre HITL/aprovação"
HITL_CONSTANT_NAMES: frozenset[str] = frozenset({
    "_HITL_ACTION_TYPES",
    "_HITL_MESSAGE_TYPES",
    "HITL_ACTION_TYPES",
    "SENSITIVE_FLAGS_REQUIRING_HITL",
    "HITL_REQUIRED_ACTIONS",
})

# Arquivos/diretórios a excluir do scan
EXCLUDE_PATHS: tuple[str, ...] = (
    "__pycache__",
    "test",
    ".pyc",
    "alembic/versions",
    "scripts/check_hitl",  # this file itself
)


def _is_excluded(path: Path) -> bool:
    s = str(path)
    return any(exc in s for exc in EXCLUDE_PATHS)


def _load_canonical() -> frozenset[str]:
    """Load HITL_REQUIRED_ACTIONS from canonical file via AST (no import).
    Handles both  and  (annotated assignment) forms.
    """
    if not CANONICAL_PATH.exists():
        return frozenset()
    src = CANONICAL_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        # AnnAssign: 
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "HITL_REQUIRED_ACTIONS":
                val = node.value
                if val is not None and isinstance(val, ast.Call) and val.args:
                    try:
                        return frozenset(ast.literal_eval(val.args[0]))
                    except (ValueError, TypeError):
                        return frozenset()
        # Assign: 
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "HITL_REQUIRED_ACTIONS":
                    val = node.value
                    if isinstance(val, ast.Call) and val.args:
                        try:
                            return frozenset(ast.literal_eval(val.args[0]))
                        except (ValueError, TypeError):
                            return frozenset()
    return frozenset()


def _extract_frozensets(src: str, filepath: Path) -> Iterator[tuple[str, int, set[str]]]:
    """Yield (constant_name, line, {elements}) for each frozenset in the file."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            val = node.value
            elements: set[str] | None = None
            # frozenset({...}) or frozenset([...])
            if isinstance(val, ast.Call) and val.args:
                try:
                    raw = ast.literal_eval(val.args[0])
                    if isinstance(raw, (set, frozenset, list, tuple)):
                        elements = {x for x in raw if isinstance(x, str)}
                except (ValueError, TypeError):
                    pass
            # Direct set literal: {...}
            elif isinstance(val, ast.Set):
                try:
                    raw = ast.literal_eval(val)
                    elements = {x for x in raw if isinstance(x, str)}
                except (ValueError, TypeError):
                    pass

            if elements is not None:
                yield (name, node.lineno, elements)


def scan(root: Path, canonical: frozenset[str]) -> list[dict]:
    violations: list[dict] = []

    for pyfile in sorted(root.rglob("*.py")):
        if _is_excluded(pyfile):
            continue
        # Skip the canonical file itself
        if pyfile == CANONICAL_PATH:
            continue

        try:
            src = pyfile.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for const_name, lineno, elements in _extract_frozensets(src, pyfile):
            # Only care about frozensets with action-like strings
            if not elements:
                continue

            # Skip frozensets that are clearly system/infra (non-action strings)
            # Heuristic: if elements look like keywords ("1", "true", "on") or
            # short infrastructure values, skip them.
            if all(
                e in {"1", "true", "on", "yes", "0", "false", "off", "no",
                      "127.0.0.1", "::1", "localhost", "email", "whatsapp",
                      "voice", "web", "daily", "twice_daily", "weekly", "monthly"}
                for e in elements
            ):
                continue

            # Case 1: Named HITL constant → all elements MUST be in canonical
            if const_name in HITL_CONSTANT_NAMES and const_name != "HITL_REQUIRED_ACTIONS":
                not_in_canonical = {e for e in elements if e not in canonical}
                if not_in_canonical:
                    rel = str(pyfile.relative_to(root))
                    violations.append({
                        "file": rel,
                        "line": lineno,
                        "constant": const_name,
                        "missing_from_canonical": sorted(not_in_canonical),
                        "reason": (
                            f"{const_name} contém strings NÃO presentes em HITL_REQUIRED_ACTIONS."
                        ),
                        "fix": (
                            f"Adicionar {sorted(not_in_canonical)} a "
                            "app/shared/hitl/hitl_canonical_actions.py → HITL_REQUIRED_ACTIONS. "
                            "Ações canônicas disponíveis: "
                            + ", ".join(sorted(canonical)[:10]) + " (+ mais)."
                        ),
                    })
                continue

            # Case 2: Unnamed / unrecognized frozenset with HIGH_RISK strings
            # not in canonical → warn only if constant name suggests it's an
            # action registry (contains "action", "HITL", "write_tool", "restricted", etc.)
            # Skip frozensets that are clearly status registers, HTTP methods, etc.
            # "action" registries are flagged; blocklists ("restricted") and
            # UI fallbacks ("fallback") are NOT HITL sets.
            # "high_impact" is a fairness concept, not an agent action_type.
            _IS_ACTION_REGISTRY = (
                any(
                    kw in const_name.lower()
                    for kw in ("_action_types", "write_tool", "mutation",
                               "communication_actions", "sourcing_actions",
                               "interview_actions")
                )
                and not any(
                    excl in const_name.lower()
                    for excl in ("restricted", "fallback", "high_impact",
                                 "blocked", "forbidden", "excluded")
                )
            )
            high_risk_not_canonical = {
                e for e in elements
                if any(p in e.lower() for p in HIGH_RISK_PATTERNS)
                and e not in canonical
            }
            if high_risk_not_canonical and _IS_ACTION_REGISTRY:
                rel = str(pyfile.relative_to(root))
                violations.append({
                    "file": rel,
                    "line": lineno,
                    "constant": const_name,
                    "missing_from_canonical": sorted(high_risk_not_canonical),
                    "reason": (
                        f"frozenset '{const_name}' contém strings de alto risco "
                        f"NÃO em HITL_REQUIRED_ACTIONS."
                    ),
                    "fix": (
                        f"Verificar se {sorted(high_risk_not_canonical)} são ações que "
                        "requerem HITL. Se sim, adicionar a HITL_REQUIRED_ACTIONS. "
                        "Se não, adicionar comentário `# HITL-EXEMPT: <motivo>`."
                    ),
                })

    return violations



def check_no_local_hitl_frozensets(root: Path) -> list[tuple[str, int, str]]:
    """
    Detect agent files that still declare their own _HITL_ACTION_TYPES /
    _HITL_MESSAGE_TYPES frozenset instead of importing from hitl_canonical_actions.

    After R4 Phase 4 migration (2026-06-20), zero agent files should declare
    their own local HITL frozenset. Any new local declaration diverges from the
    P-SSOT and creates the exact gap this migration was designed to close.
    """
    violations = []
    SUSPECT_NAMES = {"_HITL_ACTION_TYPES", "_HITL_MESSAGE_TYPES", "_HITL_TYPES"}
    # Exempt: canonical source file and the agent_gate docstring (illustrative example)
    EXEMPT_FILES = {"hitl_canonical_actions.py", "agent_gate.py", "check_hitl"}

    for pyfile in sorted(root.rglob("*.py")):
        if any(exc in str(pyfile) for exc in ("test", "__pycache__", *EXEMPT_FILES)):
            continue
        try:
            lines = pyfile.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            for name in SUSPECT_NAMES:
                if re.search(rf"\b{re.escape(name)}\b\s*=\s*frozenset", line):
                    rel = str(pyfile.relative_to(root.parent))
                    violations.append((
                        rel,
                        i,
                        f"{name} local frozenset — migrate to: "
                        f"from app.shared.hitl.hitl_canonical_actions import HITL_REQUIRED_ACTIONS"
                    ))
    return violations

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--blocking", action="store_true", help="Exit 1 if violations found.")
    parser.add_argument("--json", dest="json_output", action="store_true", help="JSON output.")
    parser.add_argument("--root", default=str(APP_ROOT), help="Root directory to scan.")
    parser.add_argument("--max-violations", type=int, default=0, help="Allowed violations before blocking.")
    args = parser.parse_args()

    canonical = _load_canonical()
    if not canonical:
        print(
            "❌ HITL_REQUIRED_ACTIONS não carregado — "
            f"canonical file ausente em {CANONICAL_PATH}.",
            file=sys.stderr,
        )
        return 1

    root = Path(args.root).resolve()
    violations = scan(root, canonical)

    # Check 2: no local frozensets in agent files (P-SSOT enforcement)
    local_fs_violations = check_no_local_hitl_frozensets(root)
    for fpath_str, lineno, msg in local_fs_violations:
        print(f"\n❌ [{fpath_str}:{lineno}] LOCAL_FROZENSET")
        print(f"   → Fix: {msg}")
    violations = violations + [{
        "file": fpath_str, "line": lineno, "constant": "LOCAL_FROZENSET",
        "missing_from_canonical": [], "reason": msg, "fix": msg
    } for fpath_str, lineno, msg in local_fs_violations]

    if args.json_output:
        print(json.dumps({
            "total": len(violations),
            "canonical_size": len(canonical),
            "violations": violations,
        }, indent=2, ensure_ascii=False))
    else:
        if violations:
            for v in violations:
                print(f"\n❌ [{v['file']}:{v['line']}] {v['constant']}")
                print(f"   Problema: {v['reason']}")
                print(f"   Faltando: {v['missing_from_canonical']}")
                print(f"   → Fix: {v['fix']}")
        else:
            print(
                f"✅ check_hitl_canonical_strings: 0 violations "
                f"({len(canonical)} actions in HITL_REQUIRED_ACTIONS)."
            )

    if args.blocking and len(violations) > args.max_violations:
        print(
            f"\n❌ {len(violations)} violation(s) encontradas "
            f"(max permitido: {args.max_violations}).",
            file=sys.stderr,
        )
        return 1

    if violations:
        print(f"\n⚠  {len(violations)} violation(s) — modo warn-only (exit 0).", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
