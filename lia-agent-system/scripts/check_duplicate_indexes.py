#!/usr/bin/env python3
"""
CI Guard: Detect duplicate SQLAlchemy index names that cause DuplicateTableError.

Usage:
    python3 scripts/check_duplicate_indexes.py

Exits 1 if any model has a column-level `index=True` whose auto-generated name
(ix_{tablename}_{column}) collides with an explicit Index(...) name in
__table_args__, or if two explicit Index(...) entries share the same name.

Background: FeedbackEvent previously had `outcome = Column(..., index=True)`
which auto-creates `ix_feedback_events_outcome`, plus a composite
Index('ix_feedback_events_outcome', ...) in __table_args__. This caused
sqlalchemy.exc.DuplicateTableError on every startup.

Uses Python AST parsing to handle nested parentheses in type declarations
like Column(String(20), index=True) and Column(UUID(as_uuid=True), index=True),
as well as annotated assignments like `col: Mapped[str] = mapped_column(index=True)`.
"""
import ast
import sys
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "libs" / "models" / "lia_models"

EXIT_CODE = 0


def _is_column_call_with_index(call: ast.Call) -> bool:
    if not isinstance(call, ast.Call):
        return False
    func = call.func
    if isinstance(func, ast.Name):
        func_name = func.id
    elif isinstance(func, ast.Attribute):
        func_name = func.attr
    else:
        return False
    if func_name not in ("Column", "mapped_column"):
        return False
    for kw in call.keywords:
        if kw.arg == "index" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            return True
    return False


def find_indexed_columns(class_body: list) -> dict[str, str]:
    results: dict[str, str] = {}
    for node in class_body:
        attr_name = None
        call = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                attr_name = target.id
                call = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            attr_name = node.target.id
            call = node.value
        if attr_name and isinstance(call, ast.Call) and _is_column_call_with_index(call):
            results[attr_name] = attr_name
    return results


def find_tablename(class_body: list) -> str | None:
    for node in class_body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__tablename__":
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        return node.value.value
    return None


def find_explicit_index_names(class_body: list) -> list[str]:
    names: list[str] = []
    for node in ast.walk(ast.Module(body=class_body, type_ignores=[])):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr
        else:
            continue
        if func_name == "Index" and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                names.append(first_arg.value)
    return names


def check_file(filepath: Path):
    global EXIT_CODE
    content = filepath.read_text()

    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        print(f"FAIL  {filepath.name}: SyntaxError during parsing — {exc}")
        EXIT_CODE = 1
        return

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        tablename = find_tablename(node.body)
        if not tablename:
            continue

        indexed_cols = find_indexed_columns(node.body)
        auto_indexes: dict[str, str] = {}
        for col_name in indexed_cols:
            auto_indexes[f"ix_{tablename}_{col_name}"] = col_name

        explicit_names = find_explicit_index_names(node.body)

        seen: set[str] = set()
        for name in explicit_names:
            if name in seen:
                print(
                    f"FAIL  {filepath.name}:{node.name} "
                    f"duplicate explicit Index name '{name}'"
                )
                EXIT_CODE = 1
            seen.add(name)

        for auto_name, col_name in auto_indexes.items():
            if auto_name in seen:
                print(
                    f"FAIL  {filepath.name}:{node.name} "
                    f"column '{col_name}' has index=True (auto-name '{auto_name}') "
                    f"which collides with an explicit Index in __table_args__"
                )
                EXIT_CODE = 1


def main():
    global EXIT_CODE
    if not MODELS_DIR.is_dir():
        print(f"ERROR: models directory not found: {MODELS_DIR}")
        sys.exit(2)

    files = sorted(MODELS_DIR.glob("*.py"))
    files = [f for f in files if f.name != "__init__.py"]
    print(f"Scanning {len(files)} model files in {MODELS_DIR.name}/...")

    for f in files:
        check_file(f)

    if EXIT_CODE == 0:
        print(f"OK  All {len(files)} model files are clean — no duplicate index names.")
    else:
        print("\nFix the above collisions to prevent DuplicateTableError on startup.")

    sys.exit(EXIT_CODE)


if __name__ == "__main__":
    main()
