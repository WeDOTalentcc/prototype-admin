"""
Contract tests for P0-W3-01, P0-W3-04, P0-W3-05 auth security fixes.

All tests are AST-based (source code inspection) — no DB or running server needed.

P0-W3-01: integrations_hub.py — all endpoints must have require_company_id or equivalent
P0-W3-05: billing.py — get_user_from_headers must NOT use X-User-Role header for is_admin
P0-W3-04: ai_consumption.py — /usage/{client_id} and /limits/{client_id} must have ownership/role checks
"""
import ast
import os
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent.parent  # lia-agent-system/
V1 = BASE / "app" / "api" / "v1"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse(path: Path) -> ast.Module:
    return ast.parse(_read(path))


# ---------------------------------------------------------------------------
# P0-W3-01 — integrations_hub.py: all route handlers must have auth guard
# ---------------------------------------------------------------------------

class TestIntegrationsHubAuth:
    """All endpoint handlers must have require_company_id or require_company_id_strict_match."""

    HUB_PATH = V1 / "integrations_hub.py"

    def _get_handler_names_missing_auth(self) -> list[str]:
        """Return names of async def functions decorated with @router.* that lack auth depend."""
        source = _read(self.HUB_PATH)
        tree = _parse(self.HUB_PATH)
        missing = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            # Only consider functions decorated with @router.get/post/put/delete/patch
            has_route_decorator = any(
                (isinstance(d, ast.Call)
                 and isinstance(d.func, ast.Attribute)
                 and d.func.attr in ("get", "post", "put", "delete", "patch"))
                or (isinstance(d, ast.Attribute) and d.attr in ("get", "post", "put", "delete", "patch"))
                for d in node.decorator_list
            )
            if not has_route_decorator:
                continue

            # Check that the function has at least one parameter using require_company_id
            # or require_company_id_strict_match as its dependency
            func_src = ast.get_source_segment(source, node) or ""
            has_auth = (
                "require_company_id" in func_src
                or "require_company_id_strict_match" in func_src
                or "get_verified_company_id" in func_src
            )
            if not has_auth:
                missing.append(node.name)

        return missing

    def test_all_handlers_have_auth_guard(self):
        """Every route handler in integrations_hub.py must use require_company_id (or equivalent)."""
        missing = self._get_handler_names_missing_auth()
        assert missing == [], (
            f"integrations_hub.py handlers missing auth guard (P0-W3-01): {missing}"
        )

    def test_connection_create_schema_has_no_company_id_field(self):
        """ConnectionCreate schema must NOT have a company_id field (multi-tenancy: from JWT only)."""
        source = _read(self.HUB_PATH)
        tree = _parse(self.HUB_PATH)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "ConnectionCreate":
                for item in node.body:
                    if isinstance(item, ast.AnnAssign):
                        if isinstance(item.target, ast.Name) and item.target.id == "company_id":
                            pytest.fail(
                                "ConnectionCreate has a 'company_id' field — violates multi-tenancy "
                                "canonical (company_id must come from JWT, never from payload). "
                                "Remove the field from ConnectionCreate."
                            )
                return  # class found, no company_id field — OK
        pytest.fail("ConnectionCreate class not found in integrations_hub.py — file may have changed")


# ---------------------------------------------------------------------------
# P0-W3-05 — billing.py: is_admin must come from JWT User, not X-User-Role header
# ---------------------------------------------------------------------------

class TestBillingAuthFix:
    """billing.py must NOT derive is_admin from the X-User-Role request header."""

    BILLING_PATH = V1 / "billing.py"

    def test_no_x_user_role_header_for_admin(self):
        """get_user_from_headers must not accept X-User-Role header (P0-W3-05)."""
        source = _read(self.BILLING_PATH)
        assert 'alias="X-User-Role"' not in source, (
            "billing.py still accepts X-User-Role header. "
            "P0-W3-05: is_admin must be derived from JWT-authenticated User.role, "
            "not from a request header the caller controls."
        )

    def test_no_header_based_admin_check(self):
        """is_admin must not be set to (x_user_role == 'admin')."""
        source = _read(self.BILLING_PATH)
        assert 'x_user_role == "admin"' not in source, (
            "billing.py still derives is_admin from x_user_role header value. "
            "P0-W3-05: use current_user.role from JWT instead."
        )

    def test_get_user_from_headers_uses_jwt_user(self):
        """get_user_from_headers must import and use get_current_active_user (JWT-based)."""
        source = _read(self.BILLING_PATH)
        assert "get_current_active_user" in source, (
            "billing.py does not import/use get_current_active_user. "
            "P0-W3-05 fix requires JWT-based user in get_user_from_headers."
        )

    def test_is_admin_uses_user_role_enum(self):
        """is_admin must reference UserRole enum (from JWT user.role)."""
        source = _read(self.BILLING_PATH)
        assert "UserRole.admin" in source, (
            "billing.py is_admin check does not reference UserRole.admin. "
            "P0-W3-05 fix must use current_user.role in (UserRole.admin, UserRole.wedotalent_admin)."
        )
        assert "UserRole.wedotalent_admin" in source, (
            "billing.py is_admin check does not include UserRole.wedotalent_admin. "
            "WeDOTalent staff must also be treated as admin."
        )


# ---------------------------------------------------------------------------
# P0-W3-04 — ai_consumption.py: /usage/{client_id} and /limits/{client_id} checks
# ---------------------------------------------------------------------------

class TestAiConsumptionAuthFix:
    """GET /usage/{client_id} needs ownership check; PUT /limits/{client_id} needs role check."""

    AI_PATH = V1 / "ai_consumption.py"

    def _get_func_source(self, func_name: str) -> str:
        """Extract source of an async def by name."""
        source = _read(self.AI_PATH)
        tree = _parse(self.AI_PATH)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == func_name:
                return ast.get_source_segment(source, node) or ""
        return ""

    def test_get_client_usage_imports_user(self):
        """ai_consumption.py must import User and get_current_active_user (P0-W3-04)."""
        source = _read(self.AI_PATH)
        assert "get_current_active_user" in source, (
            "ai_consumption.py does not import get_current_active_user. "
            "P0-W3-04: ownership check on /usage/{client_id} requires authenticated User."
        )
        assert "UserRole" in source, (
            "ai_consumption.py does not import UserRole. "
            "P0-W3-04: role check on /limits/{client_id} requires UserRole enum."
        )

    def test_get_client_usage_has_ownership_check(self):
        """GET /usage/{client_id} must verify caller is same company or admin."""
        func_src = self._get_func_source("get_client_usage")
        assert func_src, "get_client_usage function not found in ai_consumption.py"

        # Must reference current_user (from JWT)
        assert "current_user" in func_src, (
            "get_client_usage does not use current_user. "
            "P0-W3-04: must verify caller owns client_id or is admin."
        )

        # Must have a 403 raise for unauthorized access
        assert "403" in func_src or "status_code=403" in func_src or "HTTP_403_FORBIDDEN" in func_src, (
            "get_client_usage has no 403 guard. "
            "P0-W3-04: must raise 403 if caller company_id != client_id and not admin."
        )

    def test_get_client_usage_has_user_param(self):
        """GET /usage/{client_id} handler signature must include current_user dependency."""
        source = _read(self.AI_PATH)
        tree = _parse(self.AI_PATH)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_client_usage":
                param_names = [arg.arg for arg in node.args.args]
                assert "current_user" in param_names, (
                    f"get_client_usage does not have current_user param. Params: {param_names}. "
                    "P0-W3-04: add current_user: User = Depends(get_current_active_user)."
                )
                return
        pytest.fail("get_client_usage not found in ai_consumption.py")

    def test_update_limits_has_role_check(self):
        """PUT /limits/{client_id} must require admin or wedotalent_admin role."""
        func_src = self._get_func_source("update_limits")
        assert func_src, "update_limits function not found in ai_consumption.py"

        assert "current_user" in func_src, (
            "update_limits does not use current_user. "
            "P0-W3-04: must verify caller is admin."
        )
        assert "UserRole.admin" in func_src or "role not in" in func_src, (
            "update_limits has no role check. "
            "P0-W3-04: must require admin or wedotalent_admin role."
        )
        assert "403" in func_src or "HTTP_403_FORBIDDEN" in func_src, (
            "update_limits has no 403 guard. "
            "P0-W3-04: must raise 403 for non-admin callers."
        )

    def test_update_limits_has_user_param(self):
        """PUT /limits/{client_id} handler signature must include current_user dependency."""
        source = _read(self.AI_PATH)
        tree = _parse(self.AI_PATH)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "update_limits":
                param_names = [arg.arg for arg in node.args.args]
                assert "current_user" in param_names, (
                    f"update_limits does not have current_user param. Params: {param_names}. "
                    "P0-W3-04: add current_user: User = Depends(get_current_active_user)."
                )
                return
        pytest.fail("update_limits not found in ai_consumption.py")
