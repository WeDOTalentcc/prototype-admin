"""
AST-based inventory of all Orchestrator V1 references in lia-agent-system.

Catches what grep misses:
- Dynamic imports via importlib.import_module()
- __import__() calls
- Re-exports through package __init__.py

Usage:
    python tools/migration/ast_orchestrator_inventory.py > docs/migrations/ast-v1-references-DATE.md

Created: 2026-04-26 (Sprint I — Tarefa A.2)
Lesson learned: grep had 33% false positive rate in Sprint A cleanup.
"""
from __future__ import annotations

import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path("/home/runner/workspace/lia-agent-system")

# Targets to detect (V1 = orchestrator.py, NOT main_orchestrator.py)
V1_MODULE_PATHS = {
    "app.orchestrator.legacy.orchestrator",
}
# Modules where importing "Orchestrator" name means V1
V1_AMBIGUOUS_PARENTS = {
    "app.orchestrator",  # if "from app.orchestrator import Orchestrator"
}
V1_CLASS_NAMES = {"Orchestrator"}
V1_FACTORY_NAMES = {"get_orchestrator"}  # NOT get_main_orchestrator
V1_METHOD_NAMES = {
    "process_request",
    "process_request_with_memory",
    "execute_plan",
    "process_analytics_request",
    "_handle_directly",
    "_handle_cv_screening_with_rubric",
}


class V1Visitor(ast.NodeVisitor):
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.findings: list[dict] = []

    def _add(self, lineno: int, kind: str, detail: str):
        self.findings.append({
            "file": str(self.file_path.relative_to(REPO_ROOT)),
            "line": lineno,
            "kind": kind,
            "detail": detail,
        })

    def visit_ImportFrom(self, node: ast.ImportFrom):
        # from X import Y
        module = node.module or ""
        if module in V1_MODULE_PATHS:
            for alias in node.names:
                self._add(node.lineno, "static_import_from_v1_module",
                          f"from {module} import {alias.name}")
        elif module in V1_AMBIGUOUS_PARENTS:
            for alias in node.names:
                if alias.name in V1_CLASS_NAMES or alias.name in V1_FACTORY_NAMES:
                    self._add(node.lineno, "static_import_v1_name_from_parent",
                              f"from {module} import {alias.name}")
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        # import X
        for alias in node.names:
            if alias.name in V1_MODULE_PATHS:
                self._add(node.lineno, "static_import_v1_module",
                          f"import {alias.name}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # importlib.import_module("...") and __import__("...")
        try:
            func = node.func
            # Detect importlib.import_module
            if (isinstance(func, ast.Attribute)
                    and func.attr == "import_module"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "importlib"):
                if node.args and isinstance(node.args[0], ast.Constant):
                    target = node.args[0].value
                    if isinstance(target, str) and target in V1_MODULE_PATHS:
                        self._add(node.lineno, "dynamic_import_importlib", target)
            # Detect __import__()
            if isinstance(func, ast.Name) and func.id == "__import__":
                if node.args and isinstance(node.args[0], ast.Constant):
                    target = node.args[0].value
                    if isinstance(target, str) and target in V1_MODULE_PATHS:
                        self._add(node.lineno, "dynamic_import___import__", target)
        except Exception:
            pass
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # x.process_request, x.execute_plan, etc.
        if node.attr in V1_METHOD_NAMES:
            self._add(node.lineno, "v1_method_access", f".{node.attr}")
        self.generic_visit(node)


def scan_file(path: Path) -> list[dict]:
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, IOError):
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return [{
            "file": str(path.relative_to(REPO_ROOT)),
            "line": 0,
            "kind": "parse_error",
            "detail": "SyntaxError - skipped",
        }]
    visitor = V1Visitor(path)
    visitor.visit(tree)
    return visitor.findings


def main():
    findings_by_kind: dict[str, list[dict]] = defaultdict(list)
    files_scanned = 0
    files_with_findings = set()

    for py_file in REPO_ROOT.rglob("*.py"):
        if "__pycache__" in py_file.parts or ".venv" in py_file.parts:
            continue
        files_scanned += 1
        for finding in scan_file(py_file):
            findings_by_kind[finding["kind"]].append(finding)
            files_with_findings.add(finding["file"])

    # Output as Markdown
    print("# AST V1 INVENTORY — Sprint I Tarefa A.2")
    print(f"# Date: 2026-04-26")
    print(f"# Files scanned: {files_scanned}")
    print(f"# Files with V1 references: {len(files_with_findings)}")
    print()
    
    for kind in sorted(findings_by_kind.keys()):
        items = findings_by_kind[kind]
        print(f"## {kind} ({len(items)} occurrences)")
        print()
        for item in sorted(items, key=lambda x: (x["file"], x["line"])):
            file_ = item["file"]
            line_ = item["line"]
            detail_ = item["detail"]
            print(f"- `{file_}:{line_}` — {detail_}")
        print()
    
    # JSON sidecar for diffing with grep
    with open("/tmp/ast-v1-2026-04-26.json", "w") as f:
        json.dump({k: v for k, v in findings_by_kind.items()}, f, indent=2)
    
    print("---")
    print(f"JSON saved to /tmp/ast-v1-2026-04-26.json for diff vs grep")


if __name__ == "__main__":
    main()
