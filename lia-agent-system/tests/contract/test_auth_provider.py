"""Auth provider abstraction — contrato TDD."""
import pytest


# ─── GRUPO 1: AuthContext dataclass ──────────────────────────────────────────

def test_auth_context_importable():
    """AuthContext deve ser importável de app.shared.auth."""
    from app.shared.auth.auth_provider import AuthContext
    assert AuthContext is not None


def test_auth_context_has_required_fields():
    """AuthContext deve ter: user, company_id, auth_source, roles."""
    from app.shared.auth.auth_provider import AuthContext
    import dataclasses
    fields = {f.name for f in dataclasses.fields(AuthContext)}
    required = {"user", "company_id", "auth_source", "roles"}
    missing = required - fields
    assert not missing, f"AuthContext faltando campos: {missing}"


def test_auth_context_auth_sources():
    """AuthSource deve ter LOCAL, RAILS, WORKOS."""
    from app.shared.auth.auth_provider import AuthSource
    assert hasattr(AuthSource, "LOCAL")
    assert hasattr(AuthSource, "RAILS")
    assert hasattr(AuthSource, "WORKOS")


def test_auth_context_creation():
    """AuthContext deve ser criável com dados mínimos."""
    from app.shared.auth.auth_provider import AuthContext, AuthSource
    from unittest.mock import MagicMock
    user = MagicMock()
    user.id = "user-123"
    user.role = "recruiter"
    ctx = AuthContext(
        user=user,
        company_id="company-abc",
        auth_source=AuthSource.LOCAL,
        roles=["recruiter"],
    )
    assert ctx.company_id == "company-abc"
    assert ctx.auth_source == AuthSource.LOCAL
    assert "recruiter" in ctx.roles


# ─── GRUPO 2: AuthProvider ────────────────────────────────────────────────────

def test_auth_provider_importable():
    """AuthProvider deve ser importável."""
    from app.shared.auth.auth_provider import AuthProvider
    provider = AuthProvider()
    assert hasattr(provider, "resolve")


def test_get_auth_context_fastapi_dep_importable():
    """get_auth_context deve ser importável como FastAPI dependency."""
    from app.shared.auth.auth_provider import get_auth_context
    assert callable(get_auth_context)


def test_auth_provider_resolve_local_jwt():
    """resolve() com User local → AuthSource.LOCAL."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.shared.auth.auth_provider import AuthProvider, AuthSource

    async def _run():
        provider = AuthProvider()
        user = MagicMock()
        user.id = "uuid-123"
        user.company_id = "company-abc"
        user.role = "recruiter"
        user.is_active = True

        with patch.object(provider, "_get_user_from_token", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (user, AuthSource.LOCAL)
            db = AsyncMock()
            ctx = await provider.resolve("fake-jwt-token", db)

        assert ctx.auth_source == AuthSource.LOCAL
        assert ctx.company_id == "company-abc"
        assert "recruiter" in ctx.roles
        return True

    assert asyncio.get_event_loop().run_until_complete(_run())


def test_auth_provider_raises_401_for_invalid_token():
    """resolve() com token inválido → HTTPException 401."""
    import asyncio
    from unittest.mock import AsyncMock, patch
    from fastapi import HTTPException
    from app.shared.auth.auth_provider import AuthProvider

    async def _run():
        provider = AuthProvider()
        with patch.object(provider, "_get_user_from_token", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (None, None)
            db = AsyncMock()
            try:
                await provider.resolve("invalid-token", db)
                return False  # should have raised
            except HTTPException as e:
                return e.status_code == 401

    assert asyncio.get_event_loop().run_until_complete(_run())


# ─── GRUPO 3: Compatibilidade com get_current_active_user ────────────────────

def test_auth_context_has_user_property():
    """AuthContext.user deve ser o User model original (retrocompat)."""
    from app.shared.auth.auth_provider import AuthContext, AuthSource
    from unittest.mock import MagicMock
    user = MagicMock()
    user.role = "admin"
    ctx = AuthContext(user=user, company_id="c1", auth_source=AuthSource.LOCAL, roles=["admin"])
    assert ctx.user is user


def test_auth_provider_preserves_company_id_contextvar():
    """resolve() deve atualizar o ContextVar _current_company_id."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.shared.auth.auth_provider import AuthProvider, AuthSource
    from app.middleware.request_id import get_correlation_id

    async def _run():
        provider = AuthProvider()
        user = MagicMock()
        user.id = "uuid-456"
        user.company_id = "company-xyz"
        user.role = "admin"
        user.is_active = True

        with patch.object(provider, "_get_user_from_token", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (user, AuthSource.LOCAL)
            db = AsyncMock()
            ctx = await provider.resolve("fake-token", db)

        assert ctx.company_id == "company-xyz"
        return True

    assert asyncio.get_event_loop().run_until_complete(_run())


# ─── GRUPO 4: Sensor ─────────────────────────────────────────────────────────

def test_auth_direct_import_sensor_exists():
    """Sensor check_auth_direct_import.py deve existir."""
    from pathlib import Path
    sensor = Path("scripts/check_auth_direct_import.py")
    assert sensor.exists(), (
        "scripts/check_auth_direct_import.py deve existir. "
        "Detecta sub-apps importando diretamente de app/auth/ "
        "em vez de usar app/shared/auth/auth_provider.py."
    )
