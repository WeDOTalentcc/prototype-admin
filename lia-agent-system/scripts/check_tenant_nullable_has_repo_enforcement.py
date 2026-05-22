"""WT-2022 P0.TENANT: Sensor secundario pra models com TENANT-NULLABLE-DELIBERATE marker.

Se model declara que company_id pode ser NULL (cross-tenant analytics legitimo),
o repository correspondente DEVE explicitamente filter por company_id em queries
de leitura tenant-scoped (defesa em profundidade).

Sensor valida que existe ao menos 1 metodo no repository que usa
`.where(<Model>.company_id == ...)` ou marker `# CROSS-TENANT-INTENTIONAL`.

Modo: warn-only inicial.
"""
import ast
import pathlib
import re
import sys

MODELS_DIR = pathlib.Path("lia-agent-system/libs/models/lia_models")
REPOS_DIR = pathlib.Path("lia-agent-system/app/domains")


def find_models_with_deliberate_marker():
    """Yields (model_name, file_path) for models with TENANT-NULLABLE-DELIBERATE marker
    on or near the company_id column declaration.
    """
    for py_file in MODELS_DIR.rglob("*.py"):
        try:
            content = py_file.read_text()
        except Exception:
            continue
        if "TENANT-NULLABLE-DELIBERATE" not in content:
            continue
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue
        source_lines = content.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for child in node.body:
                if not isinstance(child, ast.Assign):
                    continue
                targets = [t.id for t in child.targets if isinstance(t, ast.Name)]
                if "company_id" not in targets:
                    continue
                # Check if the line immediately before this assignment
                # has the TENANT-NULLABLE-DELIBERATE marker (1-indexed lineno).
                lineno = child.lineno
                # Look at up to 3 lines above for a comment with the marker
                window = source_lines[max(0, lineno - 4):lineno - 1]
                if any("TENANT-NULLABLE-DELIBERATE" in line for line in window):
                    yield (node.name, str(py_file))
                break


def find_repo_files_for_model(model_name: str) -> list[pathlib.Path]:
    """Find repository files that import/use the model."""
    matches = []
    if not REPOS_DIR.exists():
        return matches
    pattern = re.compile(r"\b" + re.escape(model_name) + r"\b")
    for py_file in REPOS_DIR.rglob("*repository*.py"):
        try:
            content = py_file.read_text()
        except Exception:
            continue
        if pattern.search(content):
            matches.append(py_file)
    return matches


def check_repo_has_tenant_filter(repo_file: pathlib.Path, model_name: str) -> bool:
    """Returns True if repo has <Model>.company_id == ... OR CROSS-TENANT-INTENTIONAL marker."""
    try:
        content = repo_file.read_text()
    except Exception:
        return False
    pattern1 = re.compile(re.escape(model_name) + r"\.company_id\s*==")
    pattern2 = re.compile(r"#\s*CROSS-TENANT-INTENTIONAL")
    return bool(pattern1.search(content) or pattern2.search(content))


def main():
    issues = []
    models_checked = 0
    seen = set()
    for model_name, model_file in find_models_with_deliberate_marker():
        key = (model_name, model_file)
        if key in seen:
            continue
        seen.add(key)
        models_checked += 1
        repo_files = find_repo_files_for_model(model_name)
        if not repo_files:
            issues.append(
                "Model " + model_name + " (" + model_file + ") tem TENANT-NULLABLE-DELIBERATE mas nenhum repository encontrado. "
                "Adicione repository em app/domains/<dominio>/repositories/ com metodo que filter por company_id, "
                "OU adicione comentario '# CROSS-TENANT-INTENTIONAL' em metodo aggregate que le cross-tenant."
            )
            continue
        any_enforced = any(check_repo_has_tenant_filter(f, model_name) for f in repo_files)
        if not any_enforced:
            paths = [str(f) for f in repo_files]
            issues.append(
                "Model " + model_name + ": TENANT-NULLABLE-DELIBERATE declarado mas NENHUM filter por company_id no repo " + str(paths) + ". "
                "Adicione '.where(" + model_name + ".company_id == <id>)' em pelo menos 1 query "
                "OR adicione comentario '# CROSS-TENANT-INTENTIONAL' em metodo aggregate."
            )

    if issues:
        print("WT-2022 P0.TENANT [repo-enforcement]: " + str(len(issues)) + " issue(s) (warn-only):")
        for issue in issues:
            print("  " + issue)
        print("")
        print("TOTAL models with TENANT-NULLABLE-DELIBERATE: " + str(models_checked))
        return 0  # warn-only
    print("OK: " + str(models_checked) + " models com TENANT-NULLABLE-DELIBERATE all have repo enforcement (or CROSS-TENANT-INTENTIONAL marker)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
