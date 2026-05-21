#!/usr/bin/env python3
"""
SENSOR (harness-engineering): detect duplicate Pydantic BaseModel classes.

Mesma classe declarada em 2+ arquivos vira fonte silenciosa de bugs:
- divergem (BUG real: contrato A vs B → 422 inesperado)
- ou são idênticas (cleanup necessário; dead code; refactor incompleto)

Quaisquer dos 2 casos é violação ADR-SCHEMAS-001:
"Cada feature tem UM módulo canonical de schemas. Duplicar nome de classe
entre arquivos é proibido."

Sprint Q.2: suporte ao marcador `# DUPLICATE_OF_INTENT: <canonical_path>`.
Quando uma declaração duplicada carrega esse marcador (na linha imediatamente
acima do `class X(BaseModel):` OU em até 5 linhas acima), ela é considerada
intentional re-export e NÃO conta como violação. Pattern análogo ao
`# ADR-001-EXEMPT` de outros sensores.

Output otimizado para LLM: a mensagem inclui o nome da classe, os 2 paths,
se os fields divergem (com diff), e a ação corretiva.

Uso:
  python3 scripts/check_duplicate_pydantic_schemas.py [--root <dir>]

Exit codes:
  0 — nenhuma duplicação encontrada (✅ harness OK)
  1 — duplicação detectada (output mostra cada caso com fix sugerido)
"""
from __future__ import annotations

import argparse
import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple


# Sprint Q.2: número máximo de linhas acima da `class X(...)` para procurar marker.
INTENT_MARKER_LOOKBACK_LINES = 5
INTENT_MARKER_PREFIX = "# DUPLICATE_OF_INTENT:"


class SchemaDecl(NamedTuple):
    """A Pydantic BaseModel class declaration found via AST."""
    name: str
    path: Path
    lineno: int
    fields: tuple[tuple[str, str], ...]  # ((field_name, annotation_str), …)
    has_intent_marker: bool  # Sprint Q.2: true se há marker # DUPLICATE_OF_INTENT acima


def _is_pydantic_base(class_node: ast.ClassDef) -> bool:
    """True when the class inherits (directly) from BaseModel or a known alias."""
    bases = {
        ast.unparse(b).split(".")[-1].strip()
        for b in class_node.bases
    }
    return bool(bases & {"BaseModel", "WeDoBaseModel"})


def _extract_fields(class_node: ast.ClassDef) -> tuple[tuple[str, str], ...]:
    """Best-effort: list (field_name, annotation_str) pairs."""
    fields: list[tuple[str, str]] = []
    for stmt in class_node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            try:
                ann = ast.unparse(stmt.annotation)
            except Exception:
                ann = "<unparseable>"
            fields.append((stmt.target.id, ann))
    return tuple(fields)


def _is_intent_marker(line: str) -> bool:
    """Sprint Q.2: # DUPLICATE_OF_INTENT marker excludes intentional duplicates."""
    return line.strip().startswith(INTENT_MARKER_PREFIX)


def _has_intent_marker_above(
    source_lines: list[str], class_lineno: int
) -> bool:
    """Look up to INTENT_MARKER_LOOKBACK_LINES above the class declaration for
    a `# DUPLICATE_OF_INTENT: <canonical>` comment. Returns True if found.

    `class_lineno` is 1-indexed (ast.lineno convention).
    Lines scanned: [class_lineno - INTENT_MARKER_LOOKBACK_LINES, class_lineno - 1].
    """
    # Convert 1-indexed lineno to 0-indexed list index
    class_idx = class_lineno - 1
    start = max(0, class_idx - INTENT_MARKER_LOOKBACK_LINES)
    for i in range(start, class_idx):
        if i < len(source_lines) and _is_intent_marker(source_lines[i]):
            return True
    return False


def collect_schemas(root: Path) -> list[SchemaDecl]:
    """Walk every *.py under root, collect BaseModel-derived class declarations."""
    out: list[SchemaDecl] = []
    skip_segments = {"__pycache__", ".venv", "node_modules", ".git", "dist", "build"}
    for py_file in root.rglob("*.py"):
        if any(seg in py_file.parts for seg in skip_segments):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue
        source_lines = source.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and _is_pydantic_base(node):
                has_marker = _has_intent_marker_above(source_lines, node.lineno)
                out.append(
                    SchemaDecl(
                        name=node.name,
                        path=py_file.relative_to(root),
                        lineno=node.lineno,
                        fields=_extract_fields(node),
                        has_intent_marker=has_marker,
                    )
                )
    return out


def find_duplicates(schemas: list[SchemaDecl]) -> dict[str, list[SchemaDecl]]:
    """Group by class name, return only names with ≥2 declarations
    AFTER excluding declarations carrying `# DUPLICATE_OF_INTENT` marker.

    Sprint Q.2: if a group has N declarations and K of them carry the
    intent marker, the effective count drops to N - K. The group is only
    reported when the effective count is ≥ 2 (still a real violation),
    OR when N - K == 1 AND original N ≥ 2 (canonical alone, no violation).
    """
    by_name: dict[str, list[SchemaDecl]] = defaultdict(list)
    for s in schemas:
        by_name[s.name].append(s)

    out: dict[str, list[SchemaDecl]] = {}
    for n, decls in by_name.items():
        if len(decls) < 2:
            continue
        # Exclude intent-marked declarations from the violation count.
        # A class is only a violation if there are still 2+ unmarked declarations.
        unmarked = [d for d in decls if not d.has_intent_marker]
        if len(unmarked) >= 2:
            out[n] = decls  # report all decls (marked + unmarked) for context
    return out


def render_report(duplicates: dict[str, list[SchemaDecl]]) -> str:
    if not duplicates:
        return "✅ 0 duplicate Pydantic BaseModel class names — ADR-SCHEMAS-001 holds.\n"
    lines: list[str] = [
        f"❌ {len(duplicates)} duplicate Pydantic class name(s) detected.",
        "",
        "ADR-SCHEMAS-001 (CLAUDE.md): Pydantic schemas live in ONE canonical",
        "module per feature. Duplicate names between files are a violation —",
        "either drift silently (= bug), or are dead code (= cleanup).",
        "",
        "Sprint Q.2: declarações com `# DUPLICATE_OF_INTENT: <canonical>` acima",
        "são consideradas intentional re-export e NÃO contam como violação.",
        "",
    ]
    for name, decls in sorted(duplicates.items()):
        lines.append(f"── class `{name}` declared in {len(decls)} files ──")
        for d in decls:
            marker_tag = " [# DUPLICATE_OF_INTENT]" if d.has_intent_marker else ""
            lines.append(f"  • {d.path}:{d.lineno}  ({len(d.fields)} fields){marker_tag}")
            for fname, fann in d.fields[:5]:
                lines.append(f"      - {fname}: {fann}")
            if len(d.fields) > 5:
                lines.append(f"      ... +{len(d.fields)-5} more")
        # Drift check
        field_sets = [tuple(sorted(d.fields)) for d in decls]
        identical = all(fs == field_sets[0] for fs in field_sets)
        if identical:
            lines.append(
                "  HOW TO FIX (identical fields = dead code):"
            )
            keep = decls[0]
            for dup in decls[1:]:
                lines.append(
                    f"    rm class `{name}` from {dup.path}:{dup.lineno} "
                    f"(canonical kept at {keep.path}:{keep.lineno})"
                )
        else:
            lines.append(
                "  HOW TO FIX (divergent fields = silent contract bug):"
            )
            lines.append(
                f"    Pick ONE canonical declaration, delete the others, OR"
            )
            lines.append(
                f"    rename the second occurrence (e.g. `{name}V2`) and"
            )
            lines.append(
                "    document the divergence in CLAUDE.md."
            )
            lines.append(
                "    OR (intentional re-export): add line above the duplicate:"
            )
            lines.append(
                "      # DUPLICATE_OF_INTENT: <canonical_path> — <reason>"
            )
        lines.append("")
    lines.append(
        "After fixing, re-run: python3 scripts/check_duplicate_pydantic_schemas.py"
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect duplicate Pydantic BaseModel class names (ADR-SCHEMAS-001)."
    )
    parser.add_argument(
        "--root",
        default="app",
        help="Directory to scan (default: app)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"❌ {root} is not a directory", file=sys.stderr)
        return 2

    schemas = collect_schemas(root)
    duplicates = find_duplicates(schemas)
    print(render_report(duplicates))
    return 0 if not duplicates else 1


if __name__ == "__main__":
    sys.exit(main())
