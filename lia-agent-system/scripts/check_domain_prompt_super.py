#!/usr/bin/env python3
"""
check_domain_prompt_super.py — G-DOMAIN sensor
Verifica que todos os domain.py em app/domains/*/domain.py chamam
super().get_system_prompt() em seu método get_system_prompt().

GUARDA CONTRA: regressão de UC-P0-01 (compliance LGPD ausente em domínios).

COMO CORRIGIR:
  Seu domain.py tem get_system_prompt() que não chama super().
  Padrão correto:
    def get_system_prompt(self, ...) -> str:
        domain_specific = <seu prompt atual>
        return super().get_system_prompt(base_prompt=domain_specific)
  Ver compliance_base.py:180 para o contrato completo.
"""
import ast
import sys
from pathlib import Path


def check_domain_file(path: Path) -> list[str]:
    """Return list of violation messages for a domain.py file."""
    source = path.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"{path}: SyntaxError — {e}"]

    errors = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if not isinstance(item, ast.FunctionDef):
                continue
            if item.name != "get_system_prompt":
                continue
            # Found get_system_prompt — check for super().get_system_prompt() call
            has_super_call = False
            for subnode in ast.walk(item):
                if isinstance(subnode, ast.Call):
                    func = subnode.func
                    # Look for super().get_system_prompt(...)
                    if (isinstance(func, ast.Attribute) and
                            func.attr == "get_system_prompt" and
                            isinstance(func.value, ast.Call) and
                            isinstance(func.value.func, ast.Name) and
                            func.value.func.id == "super"):
                        has_super_call = True
                        break
            if not has_super_call:
                errors.append(
                    f"{path}:{item.lineno}: [G-DOMAIN] {node.name}.get_system_prompt() "
                    f"does not call super().get_system_prompt(). "
                    f"Fix: store domain prompt in local var, return super().get_system_prompt(base_prompt=<var>). "
                    f"See docs/UC-P0-01.md and compliance_base.py:180."
                )
    return errors


def main():
    domains_root = Path("app/domains")
    if not domains_root.exists():
        print("ERROR: app/domains not found. Run from lia-agent-system root.", file=sys.stderr)
        sys.exit(1)

    domain_files = list(domains_root.glob("*/domain.py"))
    if not domain_files:
        print("ERROR: No domain.py files found in app/domains/*/", file=sys.stderr)
        sys.exit(1)

    all_errors = []
    for domain_file in sorted(domain_files):
        all_errors.extend(check_domain_file(domain_file))

    if all_errors:
        print(f"\n❌ G-DOMAIN: {len(all_errors)} domain(s) missing compliance super() call:\n")
        for err in all_errors:
            print(f"  {err}")
        print(f"\nTotal violations: {len(all_errors)}")
        print("Fix guide: store existing prompt in local var, return super().get_system_prompt(base_prompt=<var>)")
        sys.exit(1)

    print(f"✅ G-DOMAIN: all {len(domain_files)} domains call super().get_system_prompt(). Compliance OK.")
    sys.exit(0)


if __name__ == "__main__":
    main()
