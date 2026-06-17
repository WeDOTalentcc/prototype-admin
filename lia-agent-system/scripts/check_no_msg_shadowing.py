#!/usr/bin/env python3
"""SENSOR (harness-engineering — guide computacional + sensor): detecta
shadowing da funcao i18n.msg em escopo de funcao.

Bug historico (Fix A 2026-05-27):
  app/domains/job_creation/nodes/jd_gate.py:69 rebound a variavel local `msg`
  para str apos o import `from app.domains.job_creation.helpers.i18n import msg`.
  As linhas 280, 305, 335, 341 chamavam `msg("jd_gate.new_jd_short_clarify")`
  esperando a funcao i18n. Em runtime: TypeError: 'str' object is not callable
  -> silent fallback no wizard_session_service -> recrutador via
  [ATENCAO: estado inconsistente] em vez do clarify message canonical.

Bug latente em outros 3 gates (Fix A P2-NOVO-#1):
  nodes/competency_gate.py L60/73/88, nodes/wsi_questions_gate.py L84/95/110,
  nodes/review_gate.py L93/102/117 — mesmo padrao rebind, sem msg() calls
  subsequentes hoje. Primeira refactor que adicionar `or msg("...")` no branch
  fallback gatilhara o mesmo TypeError. Sensor previne preemptivamente.

Pattern detectado via AST:
  1. Modulo importa `from app.domains.job_creation.helpers.i18n import msg`
     (sem `as` rename) no top-level.
  2. Em qualquer FunctionDef do modulo, existe `msg = <expr>` (Assign onde
     target eh Name `msg`).
  -> VIOLATION (shadowing latente OU ativo).

Exclusao canonical: se import usa `as` rename (ex:
  `from ...helpers.i18n import msg as i18n_msg`), nao ha shadowing -- skipped.

Modo: BLOCKING (exit 1 se violations > baseline).
Baseline: 0 -- Fix A renomeou os 3 sites canonical em jd_gate.py;
expectativa eh manter zero violations indefinidamente.

Run modes:
  python scripts/check_no_msg_shadowing.py        # exit 1 if violations
  python scripts/check_no_msg_shadowing.py --warn # exit 0 always (warn-only)

Fix se sensor falhar:
  Em vez de fazer `msg = state.get("...")` em escopo de funcao, renomeie a
  variavel local para `resume_msg`, `user_msg`, `feedback_msg` (semantica
  do que ela contem). Mantenha o import canonical `msg` da i18n intacto
  para chamadas `msg("namespace.key")`.

Skill canonica: harness-engineering [sensor + guide computacional].
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]  # lia-agent-system/
SCAN_PATHS: list[Path] = [
    REPO_ROOT / "app" / "domains" / "job_creation",
]

I18N_MODULE_SUFFIX = ".helpers.i18n"
TARGET_NAME = "msg"


def _module_imports_msg_function(tree: ast.Module) -> bool:
    """True se modulo importa `msg` canonical da i18n sem rename."""
    for node in tree.body:  # top-level only
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.endswith(I18N_MODULE_SUFFIX):
                for alias in node.names:
                    if alias.name == TARGET_NAME and (
                        alias.asname is None or alias.asname == TARGET_NAME
                    ):
                        return True
    return False


def _find_local_msg_rebinds(tree: ast.Module) -> list[tuple[int, int, str]]:
    """Find msg = ... assignments inside any FunctionDef/AsyncFunctionDef.

    Returns list of (lineno, col_offset, func_name).
    """
    violations: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if (
                            isinstance(target, ast.Name)
                            and target.id == TARGET_NAME
                        ):
                            violations.append(
                                (child.lineno, child.col_offset, node.name)
                            )
                elif isinstance(child, ast.AugAssign):
                    if (
                        isinstance(child.target, ast.Name)
                        and child.target.id == TARGET_NAME
                    ):
                        violations.append(
                            (child.lineno, child.col_offset, node.name)
                        )
    return violations


def _iter_python_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            # Skip __pycache__ and test files (tests may shadow on purpose).
            if "__pycache__" in p.parts:
                continue
            if any(part.startswith("test_") for part in p.parts):
                continue
            if p.name.endswith(".py.bak"):
                continue
            yield p


def scan(roots: Iterable[Path]) -> list[str]:
    findings: list[str] = []
    for path in _iter_python_files(roots):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        if not _module_imports_msg_function(tree):
            continue
        for lineno, col, func_name in _find_local_msg_rebinds(tree):
            rel = path.relative_to(REPO_ROOT)
            findings.append(
                f"  {rel}:{lineno}:{col} in function {func_name!r} -- "
                f"`msg = <expr>` shadows i18n.msg function. Rename local "
                f"variable (ex: resume_msg, user_msg, feedback_msg)."
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn",
        action="store_true",
        help="Warn-only mode (exit 0 always). Default: BLOCKING.",
    )
    args = parser.parse_args()

    findings = scan(SCAN_PATHS)
    if not findings:
        print("[check_no_msg_shadowing] OK -- baseline 0 violations preserved.")
        return 0

    print("[check_no_msg_shadowing] VIOLATIONS:")
    for line in findings:
        print(line)
    print()
    print(f"Total: {len(findings)} violation(s) of i18n.msg shadowing rule.")
    print(
        "Fix: rename local `msg = ...` variable to a semantic alternative "
        "(`resume_msg`, `user_msg`, `feedback_msg`). Keep the canonical "
        "`from app.domains.job_creation.helpers.i18n import msg` import "
        "intact so `msg(\"namespace.key\")` calls keep working."
    )
    print()
    print(
        "Audit history: Fix A 2026-05-27 corrigiu jd_gate.py L69/97/121 "
        "(rename msg -> resume_msg). Bug nao pode regressar."
    )

    return 0 if args.warn else 1


if __name__ == "__main__":
    sys.exit(main())
