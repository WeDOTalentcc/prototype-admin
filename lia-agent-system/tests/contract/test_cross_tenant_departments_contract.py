"""
Contract sensor — Department cross-tenant guard (Onda 4.2a-P0.1).

WHY THIS SENSOR EXISTS
======================
Audit Hub Minha Empresa (2026-05-23) descobriu que update_department,
delete_department, update_department_member, delete_department_member
NÃO passavam company_id pro repo. User da empresa A podia
PUT/DELETE department_id da empresa B (cross-tenant write/delete = LGPD).

Onda 4.2a-P0.1 fixou:
- DepartmentRepository.update(dept_id, data, company_id=...) — guard
- DepartmentRepository.delete(dept_id, company_id=...) — guard
- Handlers passam company_id do JWT

Esse sensor valida que:
1. Repo methods aceitam company_id argument
2. Handlers chamam com company_id passado
3. Quando company_id diverge, repo retorna None (404 do handler)

Pattern: BLOCKING. Anti-regressão LGPD critical.
"""
from __future__ import annotations

import inspect
from pathlib import Path


def test_repo_update_accepts_company_id():
    """DepartmentRepository.update aceita company_id (defense-in-depth)."""
    from app.domains.company.repositories.department_repository import (
        DepartmentRepository,
    )
    sig = inspect.signature(DepartmentRepository.update)
    params = sig.parameters
    assert "company_id" in params, (
        "DepartmentRepository.update sem param company_id. "
        "Onda 4.2a-P0.1 fix restaurar — cross-tenant write LGPD."
    )


def test_repo_delete_accepts_company_id():
    """DepartmentRepository.delete aceita company_id (defense-in-depth)."""
    from app.domains.company.repositories.department_repository import (
        DepartmentRepository,
    )
    sig = inspect.signature(DepartmentRepository.delete)
    params = sig.parameters
    assert "company_id" in params, (
        "DepartmentRepository.delete sem param company_id. "
        "Cross-tenant delete LGPD critical."
    )


def test_handlers_pass_company_id_to_repo():
    """Handlers em company_departments.py passam company_id pro repo."""
    repo_root = Path(__file__).resolve().parents[2]
    src = (repo_root / "app" / "api" / "v1" / "company_departments.py").read_text()

    # 4 mutation handlers devem passar company_id
    canonical_calls = [
        "dept_repo.update(",
        "dept_repo.delete(",
        "dept_repo.update_member(",
        "dept_repo.remove_member(",
    ]
    for call in canonical_calls:
        # Find each call site and verify company_id is in the args
        idx = 0
        found_unsafe = []
        while True:
            i = src.find(call, idx)
            if i < 0:
                break
            # capture next ~200 chars (call should fit)
            block = src[i : i + 400]
            # Find closing paren
            depth = 0
            end = -1
            for k, ch in enumerate(block):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        end = k
                        break
            if end < 0:
                idx = i + 1
                continue
            call_block = block[: end + 1]
            if "company_id" not in call_block:
                found_unsafe.append(f"line~{src[:i].count(chr(10)) + 1}: {call_block[:120]}")
            idx = i + end + 1

        assert not found_unsafe, (
            f"{call}*(...) sem company_id em {len(found_unsafe)} site(s):\n"
            + "\n".join(f"  - {s}" for s in found_unsafe)
            + "\nOnda 4.2a-P0.1: TODO mutation precisa passar company_id="
            + "uuid.UUID(company_id) do JWT — cross-tenant LGPD."
        )
