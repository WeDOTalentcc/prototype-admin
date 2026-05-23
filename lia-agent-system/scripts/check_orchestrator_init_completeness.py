#!/usr/bin/env python3
"""
Anti-regression sensor (audit 2026-05-22, F-26 harness from
AUDIT_VOICE_SCREENING_ORCHESTRATOR.md): detect orchestrator classes where
__init__ does NOT assign a `self._XYZ` attribute that other methods read,
producing AttributeError at runtime.

## Background

F-01 (VoiceScreeningOrchestrator) e F-12 (GeminiVoiceService) eram a mesma
classe de bug: codigo lia self._llm_service.foo(...) mas __init__ nunca
fez self._llm_service = .... Em producao toda chamada lancava
AttributeError -> except generico -> fallback scripted. Sintoma silencioso,
feature degradada por dias.

## What this catches

Para cada modulo em app/domains/*/services/*orchestrator*.py:

  1. Parse AST
  2. Para cada `class X:`:
     a. Localiza __init__
     b. Coleta {assignments} = set de self.NAME = ... feitos em __init__
     c. Coleta {reads} = set de self.NAME usados em OUTROS metodos
     d. Diff: ghost = reads - assignments
     e. Reporta ghosts com lineno

## Allowlist marker

Linha contendo `# ORCHESTRATOR-GHOST-EXEMPT: <reason>` neutraliza o site.
Use SOMENTE em sites onde:
- Attribute is set externally by factory/DI container
- Attribute is set in a base class __init__ (we don't follow MRO)
- Attribute is conditionally assigned by another method (lazy init pattern)

## Exit

  0 = clean
  1 = >0 violations
"""
from __future__ import annotations

import ast
import pathlib
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAN_ROOTS = [
    REPO_ROOT / "app" / "domains",
]
# C.4 (Workstream C ticket 4, 2026-05-23): expanded scope to include
# `*service*.py` so we catch F-12 class of bugs (gemini_voice_service.py
# had self._llm_service ghost — same root cause as F-01 orchestrator,
# different filename). Keep `*orchestrator*.py` as a first-class glob too
# so legacy single-glob behaviour is preserved.
ORCHESTRATOR_GLOBS = [
    "*orchestrator*.py",
    "*service*.py",
]
# Backward-compat alias (some callers / tests may still reference the
# scalar constant). Points to the legacy glob so behavior matches old
# default when accessed by mistake.
ORCHESTRATOR_GLOB = ORCHESTRATOR_GLOBS[0]
EXEMPT_MARKER = "# ORCHESTRATOR-GHOST-EXEMPT"


class InitCollector(ast.NodeVisitor):
    """Walk __init__ body, collect self.XYZ assignments."""

    def __init__(self):
        self.assigned: set[str] = set()

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._collect_target(target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._collect_target(node.target)
        self.generic_visit(node)

    def _collect_target(self, target: ast.expr) -> None:
        # Match self.NAME = ...
        if (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
        ):
            self.assigned.add(target.attr)


class ReadCollector(ast.NodeVisitor):
    """Walk method bodies (not __init__), collect self.XYZ reads with lineno."""

    def __init__(self, skip_methods: set[str]):
        self.skip_methods = skip_methods
        self.reads: dict[str, list[int]] = {}
        self._current_method: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        prev = self._current_method
        self._current_method = node.name
        if node.name not in self.skip_methods:
            self.generic_visit(node)
        self._current_method = prev

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        prev = self._current_method
        self._current_method = node.name
        if node.name not in self.skip_methods:
            self.generic_visit(node)
        self._current_method = prev

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Match self.NAME being read (not assigned -- we don't visit Assign targets here)
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == "self"
            and self._current_method is not None
        ):
            self.reads.setdefault(node.attr, []).append(node.lineno)
        self.generic_visit(node)


def find_init(class_node: ast.ClassDef) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for item in class_node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "__init__":
            return item
    return None


def is_assignment_target(parent: ast.AST, attr_node: ast.Attribute) -> bool:
    """Check if attr_node is the target of an Assign/AugAssign (NOT a read)."""
    # We can't reliably detect parent without ast.parse(parent=True) helper,
    # so we use a different approach: ignore reads inside Assign targets at
    # the ReadCollector level. Currently we visit attributes in Store context
    # too. Filter via ast.Store ctx.
    return False


def collect_class_level_names(class_node: ast.ClassDef) -> set[str]:
    """Collect names defined at class body level: methods + class attrs.

    These are NOT instance attrs but are accessible via `self.NAME` (method lookup
    or class-level constant). Excluding them prevents false positives in the
    ghost-attr check.
    """
    names: set[str] = set()
    for item in class_node.body:
        # Methods (sync/async)
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(item.name)
        # Class-level assignments: SCREENING_QUESTIONS_PT = [...]
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            names.add(item.target.id)
    return names


def collect_violations(path: pathlib.Path) -> list[tuple[str, str, int]]:
    """Return list of (class_name, attr_name, lineno) ghost attributes."""
    source = path.read_text(encoding="utf-8")
    source_lines = source.splitlines()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    violations: list[tuple[str, str, int]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        init = find_init(node)
        if init is None:
            # Class without __init__ -- can't analyze, skip (inherits from base).
            continue

        init_collector = InitCollector()
        init_collector.visit(init)
        assigned = init_collector.assigned

        # Class-level names (methods + constants): these are accessible via self.NAME
        # without instance assignment. Exclude from ghost set.
        class_level = collect_class_level_names(node)

        # Reads in non-__init__ methods.
        reads: dict[str, list[int]] = {}
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if item.name == "__init__":
                continue
            for sub in ast.walk(item):
                if (
                    isinstance(sub, ast.Attribute)
                    and isinstance(sub.value, ast.Name)
                    and sub.value.id == "self"
                    and isinstance(sub.ctx, ast.Load)
                ):
                    reads.setdefault(sub.attr, []).append(sub.lineno)

        ghosts = set(reads.keys()) - assigned - class_level
        # Filter dunder + builtin-looking attrs we don't care about
        ghosts = {g for g in ghosts if not g.startswith("__")}

        for attr in sorted(ghosts):
            for lineno in reads[attr][:1]:  # report first occurrence per attr
                # Honor EXEMPT marker on the line, or on the line right above
                # (allows attaching a comment to the suspect line).
                exempt = False
                for probe_offset in (0, -1):
                    probe = lineno + probe_offset
                    if 0 < probe <= len(source_lines):
                        if EXEMPT_MARKER in source_lines[probe - 1]:
                            exempt = True
                            break
                if exempt:
                    continue
                violations.append((node.name, attr, lineno))

    return violations


def iter_orchestrator_files() -> list[pathlib.Path]:
    """C.4: walk SCAN_ROOTS once per glob pattern; dedupe in case a file
    matches both (e.g. `voice_screening_orchestrator_service.py`).
    """
    seen: set[pathlib.Path] = set()
    files: list[pathlib.Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for pattern in ORCHESTRATOR_GLOBS:
            for path in root.rglob(pattern):
                if not path.is_file() or path.suffix != ".py":
                    continue
                if path in seen:
                    continue
                seen.add(path)
                files.append(path)
    return files


def main() -> int:
    files = iter_orchestrator_files()
    if not files:
        print("[orchestrator-init-check] No orchestrator files found.", file=sys.stderr)
        return 0

    total_violations = 0
    for path in sorted(files):
        rel = path.relative_to(REPO_ROOT)
        violations = collect_violations(path)
        if not violations:
            continue
        for class_name, attr, lineno in violations:
            total_violations += 1
            print(
                f"[orchestrator-init-check] {rel}:{lineno}: "
                f"class {class_name} reads self.{attr} but __init__ "
                f"nao faz self.{attr} = .... AttributeError em runtime.\n"
                f"  Fix: adicionar self.{attr} = <canonical_value> em {class_name}.__init__\n"
                f"  Ou, se attr e' setado externamente (factory/DI): adicionar comment\n"
                f"     '{EXEMPT_MARKER}: <reason>' na linha {lineno} para suprimir."
            )

    if total_violations > 0:
        print(
            f"\n[orchestrator-init-check] {total_violations} ghost attribute(s) found. "
            f"Fix or mark {EXEMPT_MARKER}.",
            file=sys.stderr,
        )
        return 1

    print(f"[orchestrator-init-check] OK ({len(files)} files scanned, 0 violations).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
