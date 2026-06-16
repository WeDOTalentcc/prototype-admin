"""Tests for ensure_demo_user gating and password-hash repair semantics."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException


@pytest.mark.asyncio
async def test_ensure_demo_user_refuses_outside_dev():
    """Defense-in-depth: helper itself must refuse to run in non-dev envs."""
    from app.auth import dependencies

    db = AsyncMock()
    with patch.object(dependencies, "_is_dev_environment", return_value=False):
        with pytest.raises(HTTPException) as exc:
            await dependencies.ensure_demo_user(db)
    assert exc.value.status_code == 403
    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_demo_user_repairs_broken_hash():
    """Existing demo user with placeholder hash must be re-hashed with bcrypt."""
    from app.auth import dependencies

    user = MagicMock()
    user.password_hash = "demo_not_for_login"

    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = user

    db = AsyncMock()
    db.execute = AsyncMock(return_value=scalar_result)

    with patch.object(dependencies, "_is_dev_environment", return_value=True):
        repaired = await dependencies.ensure_demo_user(db)

    assert repaired is user
    assert user.password_hash.startswith(("$2a$", "$2b$", "$2y$"))
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_ensure_demo_user_keeps_valid_bcrypt_hash():
    """Valid bcrypt hash must be left untouched (no spurious commits)."""
    from app.auth import dependencies
    from app.auth.security import get_password_hash

    user = MagicMock()
    user.password_hash = get_password_hash("demo123")
    original_hash = user.password_hash

    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = user

    db = AsyncMock()
    db.execute = AsyncMock(return_value=scalar_result)

    with patch.object(dependencies, "_is_dev_environment", return_value=True):
        result = await dependencies.ensure_demo_user(db)

    assert result is user
    assert user.password_hash == original_hash
    db.commit.assert_not_called()
