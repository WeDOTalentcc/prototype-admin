"""
P0-W2-01..05 regression sensors (2026-05-24):
Security fixes for IDOR + privilege escalation in company_users.py
and company_departments.py.

Strategy: AST-based source inspection — no DB required.
Each test reads the source file and verifies structural invariants
(presence of Depends, ownership checks, role-gate patterns).

Bugs prevented:
  P0-W2-01 — IDOR in PUT/DELETE /company/users/{user_id} (cross-tenant user mutation)
  P0-W2-02 — POST /company/users missing auth + company_id from payload
  P0-W2-03 — IDOR in PUT/DELETE /company/members/{member_id} (cross-tenant member mutation)
  P0-W2-04 — IDOR in PUT/DELETE /company/departments/{department_id}
  P0-W2-05 — Privilege escalation: recruiter self-promotion to admin
"""
from __future__ import annotations

import ast
import pathlib
import re

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
USERS_FILE = BASE / "app" / "api" / "v1" / "company_users.py"
DEPTS_FILE = BASE / "app" / "api" / "v1" / "company_departments.py"
SCHEMAS_FILE = BASE / "app" / "auth" / "schemas.py"


def _get_source(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _get_function_source(file_source: str, func_name: str) -> str:
    """Extract the source text of a top-level async def function."""
    tree = ast.parse(file_source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            if node.name == func_name:
                lines = file_source.splitlines()
                start = node.lineno - 1
                end = node.end_lineno
                return "\n".join(lines[start:end])
    raise AssertionError(f"Function {func_name!r} not found in source")


def _get_class_source(file_source: str, class_name: str) -> str:
    """Extract the source text of a top-level class definition."""
    tree = ast.parse(file_source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            lines = file_source.splitlines()
            start = node.lineno - 1
            end = node.end_lineno
            return "\n".join(lines[start:end])
    raise AssertionError(f"Class {class_name!r} not found in source")


class TestP0W201_IDORUserUpdateDelete:
    """P0-W2-01: PUT/DELETE /company/users/{user_id} must have auth + ownership."""

    def test_update_user_has_current_user_depends(self):
        """update_user must declare current_user via Depends (auth guard)."""
        src = _get_function_source(_get_source(USERS_FILE), "update_user")
        assert "get_current_user_or_demo" in src, (
            "update_user is missing current_user = Depends(get_current_user_or_demo). "
            "Any token can mutate users of other companies (IDOR P0-W2-01)."
        )

    def test_update_user_uses_company_scoped_get(self):
        """update_user must call get_by_id with company_id (ownership check)."""
        src = _get_function_source(_get_source(USERS_FILE), "update_user")
        assert "get_by_id" in src and "company_id" in src, (
            "update_user must call user_repo.get_by_id(..., company_id=company_id). "
            "Without this, users from other tenants can be fetched and mutated."
        )

    def test_delete_user_has_current_user_depends(self):
        """delete_user must declare current_user via Depends (auth guard)."""
        src = _get_function_source(_get_source(USERS_FILE), "delete_user")
        assert "get_current_user_or_demo" in src, (
            "delete_user is missing current_user = Depends(get_current_user_or_demo). "
            "Endpoint has no explicit auth gate (P0-W2-01)."
        )

    def test_delete_user_uses_company_scoped_get(self):
        """delete_user must call get_by_id with company_id (ownership check)."""
        src = _get_function_source(_get_source(USERS_FILE), "delete_user")
        assert "get_by_id" in src and "company_id" in src, (
            "delete_user must scope get_by_id by company_id to prevent cross-tenant deletion."
        )


class TestP0W202_CreateUserAuth:
    """P0-W2-02: POST /company/users must require auth and not use payload company_id."""

    def test_create_user_has_current_user_depends(self):
        """create_user must have authentication dependency."""
        src = _get_function_source(_get_source(USERS_FILE), "create_user")
        assert "get_current_user_or_demo" in src, (
            "create_user missing authentication Depends. Unauthenticated callers "
            "could create users for any tenant (P0-W2-02)."
        )

    def test_user_management_create_schema_has_no_company_id(self):
        """UserManagementCreate schema must NOT have company_id field (R2 canonical)."""
        src = _get_class_source(_get_source(SCHEMAS_FILE), "UserManagementCreate")
        field_lines = [
            line.strip() for line in src.splitlines()
            if re.match(r"\s*company_id\s*:", line) and "#" not in line
        ]
        assert not field_lines, (
            f"UserManagementCreate has company_id field: {field_lines}. "
            "Per CLAUDE.md Pydantic R2, company_id MUST come from JWT, never payload."
        )


class TestP0W203_IDORMember:
    """P0-W2-03: PUT/DELETE /company/members/{member_id} must have ownership check."""

    def test_update_department_member_uses_company_id(self):
        """update_department_member must pass company_id to repo (ownership check)."""
        src = _get_function_source(_get_source(DEPTS_FILE), "update_department_member")
        assert "company_id" in src, (
            "update_department_member must pass company_id to dept_repo.update_member. "
            "Without this, members from other tenants can be mutated (P0-W2-03)."
        )
        assert "require_company_id" in src, (
            "update_department_member must have require_company_id Depends."
        )

    def test_delete_department_member_uses_company_id(self):
        """delete_department_member must pass company_id to repo (ownership check)."""
        src = _get_function_source(_get_source(DEPTS_FILE), "delete_department_member")
        assert "company_id" in src, (
            "delete_department_member must pass company_id to dept_repo.remove_member. "
            "Without this, members from other tenants can be deleted (P0-W2-03)."
        )


class TestP0W204_IDORDepartment:
    """P0-W2-04: PUT/DELETE /company/departments/{department_id} must have ownership check."""

    def test_update_department_uses_company_id(self):
        """update_department must pass company_id to repo."""
        src = _get_function_source(_get_source(DEPTS_FILE), "update_department")
        assert "company_id" in src, (
            "update_department must scope repo.update by company_id (P0-W2-04 IDOR fix)."
        )
        assert "require_company_id" in src, (
            "update_department must have require_company_id Depends."
        )

    def test_delete_department_uses_company_id(self):
        """delete_department must pass company_id to repo."""
        src = _get_function_source(_get_source(DEPTS_FILE), "delete_department")
        assert "company_id" in src, (
            "delete_department must scope repo.delete by company_id (P0-W2-04 IDOR fix)."
        )


class TestP0W205_PrivilegeEscalation:
    """P0-W2-05: Recruiter self-promotion to admin must be blocked."""

    def test_update_user_has_role_escalation_gate(self):
        """update_user must gate role changes behind admin check."""
        src = _get_function_source(_get_source(USERS_FILE), "update_user")
        assert "data.role is not None" in src, (
            "update_user missing role-change gate (data.role is not None check). "
            "Any user can self-promote to admin (P0-W2-05 privilege escalation)."
        )

    def test_update_user_role_gate_checks_admin_roles(self):
        """update_user role gate must explicitly check for admin/wedotalent_admin."""
        src = _get_function_source(_get_source(USERS_FILE), "update_user")
        assert "UserRole.admin" in src, (
            "update_user role gate does not check UserRole.admin. "
            "Recruiter can self-promote to tenant admin (P0-W2-05)."
        )
        assert "current_role" in src, (
            "update_user must read current_user role into current_role for gate check."
        )

    def test_user_management_update_schema_has_no_company_id(self):
        """UserManagementUpdate schema must NOT have company_id field (R2 canonical)."""
        src = _get_class_source(_get_source(SCHEMAS_FILE), "UserManagementUpdate")
        field_lines = [
            line.strip() for line in src.splitlines()
            if re.match(r"\s*company_id\s*:", line) and "#" not in line
        ]
        assert not field_lines, (
            f"UserManagementUpdate has company_id field: {field_lines}. "
            "Per CLAUDE.md Pydantic R2, company_id MUST come from JWT."
        )
