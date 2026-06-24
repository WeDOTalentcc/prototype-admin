"""
Sprint C — role_scope_filters — contrato TDD.
Fase RED: estes testes definem o comportamento esperado.
Fase GREEN: criar migration + model + seed + middleware para fazê-los passar.
"""
import pytest


# ─── GRUPO 1: Schema da tabela ───────────────────────────────────────────────

def test_role_scope_filter_model_importable():
    """Model RoleScopeFilter deve ser importável."""
    from lia_models.role_scope_filter import RoleScopeFilter
    assert RoleScopeFilter.__tablename__ == "role_scope_filters"


def test_role_scope_filter_has_required_columns():
    """Tabela deve ter: role, resource, action, allowed, conditions, description."""
    from lia_models.role_scope_filter import RoleScopeFilter
    cols = {c.key for c in RoleScopeFilter.__table__.columns}
    required = {"id", "role", "resource", "action", "allowed", "conditions",
                "description", "created_at", "updated_at"}
    missing = required - cols
    assert not missing, f"Colunas faltando em role_scope_filters: {missing}"


def test_role_scope_filter_unique_constraint():
    """Deve haver unique constraint em (role, resource, action)."""
    from lia_models.role_scope_filter import RoleScopeFilter
    constraints = {str(c) for c in RoleScopeFilter.__table__.constraints}
    # verifica que existe ao menos uma UniqueConstraint
    from sqlalchemy import UniqueConstraint
    unique_cols = []
    for c in RoleScopeFilter.__table__.constraints:
        if isinstance(c, UniqueConstraint):
            unique_cols.extend([col.name for col in c.columns])
    assert "role" in unique_cols and "action" in unique_cols,         "Deve ter UniqueConstraint em (role, resource, action)"


# ─── GRUPO 2: Seed de permissões padrão ──────────────────────────────────────

def test_default_permissions_importable():
    """DEFAULT_ROLE_PERMISSIONS deve ser importável e não vazio."""
    from lia_models.role_scope_filter import DEFAULT_ROLE_PERMISSIONS
    assert isinstance(DEFAULT_ROLE_PERMISSIONS, list)
    assert len(DEFAULT_ROLE_PERMISSIONS) > 0


def test_all_five_roles_have_permissions():
    """Os 5 roles canônicos devem ter ao menos uma permissão cada."""
    from lia_models.role_scope_filter import DEFAULT_ROLE_PERMISSIONS
    roles_in_seed = {p["role"] for p in DEFAULT_ROLE_PERMISSIONS}
    required_roles = {"admin", "manager", "recruiter", "viewer", "wedotalent_admin"}
    missing = required_roles - roles_in_seed
    assert not missing, f"Roles sem permissões no seed: {missing}"


def test_recruiter_can_create_candidate():
    """recruiter deve ter candidate:create = allowed."""
    from lia_models.role_scope_filter import DEFAULT_ROLE_PERMISSIONS
    match = [p for p in DEFAULT_ROLE_PERMISSIONS
             if p["role"] == "recruiter"
             and p["resource"] == "candidate"
             and p["action"] == "create"]
    assert match and match[0]["allowed"] is True,         "recruiter deve ter candidate:create permitido no seed"


def test_viewer_cannot_create_job():
    """viewer NÃO deve ter job:create."""
    from lia_models.role_scope_filter import DEFAULT_ROLE_PERMISSIONS
    match = [p for p in DEFAULT_ROLE_PERMISSIONS
             if p["role"] == "viewer"
             and p["resource"] == "job"
             and p["action"] == "create"]
    # ou não existe no seed, ou existe com allowed=False
    if match:
        assert match[0]["allowed"] is False,             "viewer não deve ter job:create permitido"


def test_viewer_can_read_candidate():
    """viewer deve poder ler candidatos."""
    from lia_models.role_scope_filter import DEFAULT_ROLE_PERMISSIONS
    match = [p for p in DEFAULT_ROLE_PERMISSIONS
             if p["role"] == "viewer"
             and p["resource"] == "candidate"
             and p["action"] == "read"]
    assert match and match[0]["allowed"] is True,         "viewer deve ter candidate:read permitido"


def test_wedotalent_admin_has_all_resources():
    """wedotalent_admin deve ter acesso a todos os recursos principais."""
    from lia_models.role_scope_filter import DEFAULT_ROLE_PERMISSIONS
    admin_resources = {p["resource"] for p in DEFAULT_ROLE_PERMISSIONS
                       if p["role"] == "wedotalent_admin" and p["allowed"]}
    required = {"job", "candidate", "screening", "offer", "report", "policy", "admin"}
    missing = required - admin_resources
    assert not missing, f"wedotalent_admin faltando recursos: {missing}"


def test_admin_role_has_full_tenant_access():
    """admin (tenant_admin) deve ter todas as ações em recursos de tenant."""
    from lia_models.role_scope_filter import DEFAULT_ROLE_PERMISSIONS
    admin_perms = {(p["resource"], p["action"]): p["allowed"]
                   for p in DEFAULT_ROLE_PERMISSIONS if p["role"] == "admin"}
    # admin deve ter create+read+update+delete em job e candidate
    for resource in ("job", "candidate"):
        for action in ("create", "read", "update", "delete"):
            key = (resource, action)
            assert admin_perms.get(key) is True,                 f"admin deve ter {resource}:{action} — faltando no seed"


# ─── GRUPO 3: ScopeFilterService (lookup no seed / DB) ───────────────────────

def test_scope_filter_service_importable():
    """ScopeFilterService deve ser importável."""
    from app.shared.rbac.scope_filter_service import ScopeFilterService
    svc = ScopeFilterService()
    assert hasattr(svc, "is_allowed")


def test_scope_filter_service_denies_unknown_role():
    """Role desconhecida deve ser negada (fail-closed)."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock
    from app.shared.rbac.scope_filter_service import ScopeFilterService

    async def _run():
        svc = ScopeFilterService()
        db = AsyncMock()
        db.execute.return_value.scalars.return_value.first.return_value = None
        result = await svc.is_allowed("unknown_role", "job", "create", db)
        return result

    assert asyncio.get_event_loop().run_until_complete(_run()) is False


def test_scope_filter_service_allows_from_seed():
    """is_allowed deve retornar True para permissão presente no seed."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.shared.rbac.scope_filter_service import ScopeFilterService

    async def _run():
        svc = ScopeFilterService()
        # Mock DB retornando um record com allowed=True
        mock_record = MagicMock()
        mock_record.allowed = True
        db = AsyncMock()
        db.execute.return_value.scalars.return_value.first.return_value = mock_record
        result = await svc.is_allowed("recruiter", "candidate", "create", db)
        return result

    assert asyncio.get_event_loop().run_until_complete(_run()) is True


# ─── GRUPO 4: Sensor check_hardcoded_permissions.py ─────────────────────────

def test_hardcoded_permissions_sensor_importable():
    """Sensor AST deve existir e ser executável."""
    import importlib.util, sys
    from pathlib import Path
    sensor = Path("scripts/check_hardcoded_permissions.py")
    assert sensor.exists(), (
        "scripts/check_hardcoded_permissions.py deve existir. "
        "CORREÇÃO: criar sensor AST que detecta @requires_permission hardcoded "
        "em rotas sem entrada na role_scope_filters."
    )
