"""
OTLP LGPD violation detector — pre-commit / CI hook.

Sprint III follow-up: enforça que spans OTLP NÃO incluem atributos
protegidos pela LGPD (race, religion, gender, ethnicity, etc.).

## Como funciona

1. Carrega FORBIDDEN_SPAN_ATTR_PATTERNS de _observability.py
2. Escaneia todos os arquivos `*.py` em `app/` por:
   - `span.set_attribute("FORBIDDEN_KEY", ...)` (OTel SDK pattern)
   - `attributes={"FORBIDDEN_KEY": ...}` (decorator pattern)
   - `span.update({"FORBIDDEN_KEY": ...})` (LightweightTracer pattern)
3. Reporta violations + exit code 1 (falha CI)

## Uso

### Via CLI:
    python tools/migration/otlp_lgpd_check.py

### Via pre-commit:
Add to .pre-commit-config.yaml:
    - id: otlp-lgpd-check
      entry: python tools/migration/otlp_lgpd_check.py
      language: system
      types: [python]
      pass_filenames: false

### Via CI:
    pytest tests/ci/test_otlp_lgpd.py  # wrapper que chama esse script

Reference: ADR-019 — Sprint III follow-up (audit recommendation)
"""
from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

# Path canônico do repo (assume execução do root)
REPO_ROOT = Path("/home/runner/workspace/lia-agent-system")
APP_DIR = REPO_ROOT / "app"

# Importar lista canônica de FORBIDDEN patterns
sys.path.insert(0, str(REPO_ROOT))
from app.orchestrator.observability._observability import FORBIDDEN_SPAN_ATTR_PATTERNS  # noqa: E402

# Lower-case lookup para case-insensitive match
FORBIDDEN_LOWER = {p.lower() for p in FORBIDDEN_SPAN_ATTR_PATTERNS}


class SpanAttributeVisitor(ast.NodeVisitor):
    """Visita nodes ast procurando span attribute settings com keys forbidden."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.violations: list[dict] = []

    def _check_string_for_forbidden(self, lineno: int, value: str, context: str):
        """Se string value matches forbidden pattern (token-based, case-insensitive).

        Tokenize value usando ._-/whitespace e checa match exato.
        Evita false positives: traceback (contem 'race'), trace_id, traces_enabled.
        """
        import re as _re
        v_lower = value.lower()
        tokens = set(_re.split(r"[._\-/\s]+", v_lower))
        tokens.discard("")
        for forbidden in FORBIDDEN_LOWER:
            if forbidden in tokens:
                self.violations.append({
                    "file": str(self.file_path.relative_to(REPO_ROOT)),
                    "line": lineno,
                    "context": context,
                    "value": value,
                    "matched": forbidden,
                })
                break

    def visit_Call(self, node: ast.Call):
        """Detect span.set_attribute("KEY", value) and similar patterns."""
        try:
            # Pattern 1: x.set_attribute("KEY", ...)
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "set_attribute"
                and len(node.args) >= 1
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                self._check_string_for_forbidden(
                    node.lineno, node.args[0].value, "span.set_attribute"
                )
        except Exception:
            pass
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict):
        """Detect dict literals com keys forbidden (e.g., attributes={"KEY": ...})."""
        try:
            for key_node in node.keys:
                if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                    # Apenas warn se contexto sugere span attributes
                    # (heurística simples: busca "span" ou "attribute" no source line)
                    self._check_string_for_forbidden(
                        key_node.lineno, key_node.value, "dict_key"
                    )
        except Exception:
            pass
        self.generic_visit(node)


def scan_file(path: Path) -> list[dict]:
    """Escaneia 1 arquivo Python por violations."""
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, IOError):
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    visitor = SpanAttributeVisitor(path)
    visitor.visit(tree)
    return visitor.violations


def filter_dict_violations(violations: list[dict], path: Path) -> list[dict]:
    """
    Heurística para reduzir false positives em dict_key context:
    Apenas considera violation se a linha contém "span" ou "trace" ou "attribute".
    """
    if not violations:
        return violations
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except IOError:
        return violations

    filtered = []
    for v in violations:
        if v["context"] != "dict_key":
            filtered.append(v)
            continue
        # dict_key: filter if line contains span-related keyword
        line_idx = v["line"] - 1
        if 0 <= line_idx < len(lines):
            line = lines[line_idx].lower()
            # Olhar linha + 3 anteriores para context
            context_lines = "\n".join(lines[max(0, line_idx - 3) : line_idx + 1]).lower()
            if any(
                kw in context_lines
                for kw in ("span", "trace", "attribute", "tracer", "otel")
            ):
                filtered.append(v)
    return filtered


def main() -> int:
    """Run scan + report. Exit code 1 if violations found."""
    print(f"OTLP LGPD violation check — scanning {APP_DIR}")
    print(f"Forbidden patterns: {len(FORBIDDEN_LOWER)}")
    print()

    all_violations: list[dict] = []
    files_scanned = 0

    for py_file in APP_DIR.rglob("*.py"):
        if "__pycache__" in py_file.parts or ".venv" in py_file.parts:
            continue
        files_scanned += 1
        violations = scan_file(py_file)
        violations = filter_dict_violations(violations, py_file)
        all_violations.extend(violations)

    print(f"Files scanned: {files_scanned}")
    print(f"Violations: {len(all_violations)}")
    print()

    if not all_violations:
        print("✅ OK — no LGPD-protected attribute names found in span attributes")
        return 0

    # Group by file for readable output
    by_file = defaultdict(list)
    for v in all_violations:
        by_file[v["file"]].append(v)

    print("❌ VIOLATIONS FOUND:")
    print()
    for file, items in sorted(by_file.items()):
        print(f"  {file}:")
        for v in items:
            print(
                f"    line {v['line']}: {v['context']} = {v['value']!r} "
                f"(matched: {v['matched']!r})"
            )
        print()

    print(f"Total: {len(all_violations)} violations in {len(by_file)} files")
    print()
    print("ACTION: Use audit_service.log_decision() for tenant data, NOT span attributes.")
    print("REFERENCE: app/orchestrator/_observability.py FORBIDDEN_SPAN_ATTR_PATTERNS")
    return 1


if __name__ == "__main__":
    sys.exit(main())
