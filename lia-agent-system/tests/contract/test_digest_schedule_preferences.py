"""Sensor Fatia 2 (Decisão 3): digest_schedule_preferences — per-user frequency override.

Garante:
1. get_effective retorna override do usuário quando existe (user > company_default)
2. get_effective retorna company_default quando user sem override
3. get_effective retorna (None, 'none') quando nenhuma preferência existe
4. upsert_user_preference persiste e atualiza corretamente
5. upsert_company_default (user_id=None) persiste e atualiza
6. delete_user_preference soft-delete via is_active=False
7. Multi-tenancy: _require_company_id bloqueia company_id vazio
8. Router GET /notifications/digest-schedule retorna effective (user > company > fallback)
9. Router PUT /notifications/digest-schedule grava override pessoal
10. Router PUT /notifications/digest-schedule/company exige role admin
11. briefing_dispatch._resolve_user_briefing_frequency: user override ganha sobre company_freq
12. briefing_dispatch._resolve_user_briefing_frequency: fallback para company_freq quando sem pref
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pref(
    company_id: str = "comp-1",
    user_id: str | None = None,
    frequency: str = "daily",
    **kwargs,
):
    pref = MagicMock()
    pref.company_id = company_id
    pref.user_id = user_id
    pref.frequency = frequency
    pref.preferred_time_morning = kwargs.get("preferred_time_morning")
    pref.preferred_time_afternoon = kwargs.get("preferred_time_afternoon")
    pref.quiet_hours_start = kwargs.get("quiet_hours_start")
    pref.quiet_hours_end = kwargs.get("quiet_hours_end")
    pref.is_active = True
    return pref


def _make_repo(user_pref=None, company_default=None):
    """Cria um DigestScheduleRepository mock com comportamento configurável."""
    from app.domains.communication.repositories.digest_schedule_repository import (
        DigestScheduleRepository,
    )

    repo = MagicMock(spec=DigestScheduleRepository)
    repo.get_user_preference = AsyncMock(return_value=user_pref)
    repo.get_company_default = AsyncMock(return_value=company_default)

    async def _get_effective(db, *, company_id, user_id):
        if user_pref:
            return user_pref, "user"
        if company_default:
            return company_default, "company_default"
        return None, "none"

    repo.get_effective = _get_effective
    repo.upsert_user_preference = AsyncMock(return_value=_make_pref(user_id="usr-1", frequency="daily"))
    repo.upsert_company_default = AsyncMock(return_value=_make_pref(frequency="weekly"))
    repo.delete_user_preference = AsyncMock(return_value=True)
    return repo


# ---------------------------------------------------------------------------
# 1-3: Repository get_effective precedência
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_effective_returns_user_override_first():
    """get_effective deve preferir user override sobre company_default."""
    from app.domains.communication.repositories.digest_schedule_repository import (
        DigestScheduleRepository,
    )

    user_pref = _make_pref(user_id="usr-1", frequency="daily")
    company_default = _make_pref(frequency="weekly")

    repo = DigestScheduleRepository()
    mock_db = AsyncMock()

    with (
        patch.object(repo, "get_user_preference", AsyncMock(return_value=user_pref)),
        patch.object(repo, "get_company_default", AsyncMock(return_value=company_default)),
    ):
        pref, source = await repo.get_effective(mock_db, company_id="comp-1", user_id="usr-1")

    assert source == "user", f"source deveria ser 'user', recebeu {source!r}"
    assert pref.frequency == "daily"


@pytest.mark.asyncio
async def test_get_effective_falls_back_to_company_default():
    """get_effective usa company_default quando user sem override."""
    from app.domains.communication.repositories.digest_schedule_repository import (
        DigestScheduleRepository,
    )

    company_default = _make_pref(frequency="weekly")

    repo = DigestScheduleRepository()
    mock_db = AsyncMock()

    with (
        patch.object(repo, "get_user_preference", AsyncMock(return_value=None)),
        patch.object(repo, "get_company_default", AsyncMock(return_value=company_default)),
    ):
        pref, source = await repo.get_effective(mock_db, company_id="comp-1", user_id="usr-1")

    assert source == "company_default"
    assert pref.frequency == "weekly"


@pytest.mark.asyncio
async def test_get_effective_returns_none_when_no_preference():
    """get_effective retorna (None, 'none') quando nenhuma preferência existe."""
    from app.domains.communication.repositories.digest_schedule_repository import (
        DigestScheduleRepository,
    )

    repo = DigestScheduleRepository()
    mock_db = AsyncMock()

    with (
        patch.object(repo, "get_user_preference", AsyncMock(return_value=None)),
        patch.object(repo, "get_company_default", AsyncMock(return_value=None)),
    ):
        pref, source = await repo.get_effective(mock_db, company_id="comp-1", user_id="usr-1")

    assert pref is None
    assert source == "none"


# ---------------------------------------------------------------------------
# 4: upsert_user_preference
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upsert_user_preference_creates_new_row():
    """upsert_user_preference cria nova linha quando não existe."""
    from app.domains.communication.repositories.digest_schedule_repository import (
        DigestScheduleRepository,
    )

    repo = DigestScheduleRepository()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()

    with patch.object(repo, "get_user_preference", AsyncMock(return_value=None)):
        result = await repo.upsert_user_preference(
            mock_db,
            company_id="comp-1",
            user_id="usr-1",
            frequency="daily",
        )

    mock_db.add.assert_called_once()
    mock_db.flush.assert_awaited_once()
    assert result.frequency == "daily"
    assert result.user_id == "usr-1"


@pytest.mark.asyncio
async def test_upsert_user_preference_updates_existing_row():
    """upsert_user_preference atualiza linha existente sem criar nova."""
    from app.domains.communication.repositories.digest_schedule_repository import (
        DigestScheduleRepository,
    )

    existing = _make_pref(user_id="usr-1", frequency="weekly")
    repo = DigestScheduleRepository()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()

    with patch.object(repo, "get_user_preference", AsyncMock(return_value=existing)):
        result = await repo.upsert_user_preference(
            mock_db,
            company_id="comp-1",
            user_id="usr-1",
            frequency="monthly",
        )

    # Não deve chamar db.add (update in-place)
    mock_db.add.assert_not_called()
    assert result.frequency == "monthly"


# ---------------------------------------------------------------------------
# 5: upsert_company_default
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upsert_company_default_creates_row_with_null_user_id():
    """upsert_company_default cria linha com user_id=None."""
    from app.domains.communication.repositories.digest_schedule_repository import (
        DigestScheduleRepository,
    )

    repo = DigestScheduleRepository()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()

    with patch.object(repo, "get_company_default", AsyncMock(return_value=None)):
        result = await repo.upsert_company_default(
            mock_db,
            company_id="comp-1",
            frequency="weekly",
        )

    mock_db.add.assert_called_once()
    added_row = mock_db.add.call_args[0][0]
    assert added_row.user_id is None, "company default DEVE ter user_id=None"
    assert added_row.frequency == "weekly"


# ---------------------------------------------------------------------------
# 6: delete_user_preference soft-delete
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_user_preference_soft_deletes():
    """delete_user_preference seta is_active=False (soft delete)."""
    from app.domains.communication.repositories.digest_schedule_repository import (
        DigestScheduleRepository,
    )

    existing = _make_pref(user_id="usr-1", frequency="daily")
    existing.is_active = True
    repo = DigestScheduleRepository()
    mock_db = AsyncMock()
    mock_db.flush = AsyncMock()

    with patch.object(repo, "get_user_preference", AsyncMock(return_value=existing)):
        result = await repo.delete_user_preference(mock_db, company_id="comp-1", user_id="usr-1")

    assert result is True
    assert existing.is_active is False, "delete deve setar is_active=False (soft delete)"


# ---------------------------------------------------------------------------
# 7: Multi-tenancy — _require_company_id
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_require_company_id_blocks_empty():
    """_require_company_id deve levantar ValueError para company_id vazio."""
    from app.domains.communication.repositories.digest_schedule_repository import (
        DigestScheduleRepository,
    )

    repo = DigestScheduleRepository()
    mock_db = AsyncMock()

    with pytest.raises(ValueError, match="company_id é obrigatório"):
        await repo.get_effective(mock_db, company_id="", user_id="usr-1")


# ---------------------------------------------------------------------------
# 8-9: Router endpoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_digest_schedule_returns_user_override():
    """GET /notifications/digest-schedule retorna user override quando existe."""
    from app.api.v1.digest_schedule import get_digest_schedule

    user_pref = _make_pref(user_id="usr-1", frequency="twice_daily")
    mock_repo = _make_repo(user_pref=user_pref)

    mock_user = MagicMock()
    mock_user.id = "usr-1"
    mock_db = AsyncMock()

    with patch(
        "app.api.v1.digest_schedule.DigestScheduleRepository",
        return_value=mock_repo,
    ):
        result = await get_digest_schedule(
            current_user=mock_user,
            company_id="comp-1",
            db=mock_db,
        )

    assert result.frequency == "twice_daily"
    assert result.source == "user"


@pytest.mark.asyncio
async def test_put_digest_schedule_saves_user_pref():
    """PUT /notifications/digest-schedule chama upsert_user_preference e faz commit."""
    from app.api.v1.digest_schedule import update_digest_schedule
    from app.schemas.digest_schedule import DigestScheduleRequest

    saved_pref = _make_pref(user_id="usr-1", frequency="daily")
    mock_repo = _make_repo()
    mock_repo.upsert_user_preference = AsyncMock(return_value=saved_pref)

    mock_user = MagicMock()
    mock_user.id = "usr-1"
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    body = DigestScheduleRequest(frequency="daily")

    with patch(
        "app.api.v1.digest_schedule.DigestScheduleRepository",
        return_value=mock_repo,
    ):
        result = await update_digest_schedule(
            body=body,
            current_user=mock_user,
            company_id="comp-1",
            db=mock_db,
        )

    mock_repo.upsert_user_preference.assert_awaited_once()
    mock_db.commit.assert_awaited_once()
    assert result.source == "user"


# ---------------------------------------------------------------------------
# 10: Admin gate em PUT /company
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_put_company_schedule_blocks_non_admin():
    """PUT /notifications/digest-schedule/company deve retornar 403 para não-admin."""
    from fastapi import HTTPException

    from app.api.v1.digest_schedule import update_company_digest_schedule
    from app.auth.models import UserRole
    from app.schemas.digest_schedule import DigestScheduleRequest

    mock_user = MagicMock()
    mock_user.id = "usr-1"
    mock_user.role = UserRole.recruiter

    body = DigestScheduleRequest(frequency="weekly")
    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await update_company_digest_schedule(
            body=body,
            current_user=mock_user,
            company_id="comp-1",
            db=mock_db,
        )

    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# 11-12: briefing_dispatch._resolve_user_briefing_frequency
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resolve_user_freq_returns_user_override():
    """_resolve_user_briefing_frequency usa user override (digest_schedule_preferences)."""
    from app.jobs.tasks import briefing_dispatch

    user_pref = _make_pref(user_id="usr-1", frequency="twice_daily")
    mock_repo = MagicMock()

    async def _get_eff(db, *, company_id, user_id):
        return user_pref, "user"

    mock_repo.get_effective = _get_eff
    mock_db = AsyncMock()

    with patch(
        "app.domains.communication.repositories.digest_schedule_repository.DigestScheduleRepository",
        return_value=mock_repo,
    ):
        freq, source = await briefing_dispatch._resolve_user_briefing_frequency(
            mock_db,
            company_id="comp-1",
            user_id="usr-1",
            company_freq="weekly",
            company_source="hiring_policy",
        )

    assert freq == "twice_daily", f"Esperado 'twice_daily' (user override), got {freq!r}"
    assert "user" in source


@pytest.mark.asyncio
async def test_resolve_user_freq_falls_back_to_company_freq():
    """_resolve_user_briefing_frequency cai para company_freq quando sem pref pessoal."""
    from app.jobs.tasks import briefing_dispatch

    mock_repo = MagicMock()

    async def _get_eff(db, *, company_id, user_id):
        return None, "none"

    mock_repo.get_effective = _get_eff
    mock_db = AsyncMock()

    with patch(
        "app.domains.communication.repositories.digest_schedule_repository.DigestScheduleRepository",
        return_value=mock_repo,
    ):
        freq, source = await briefing_dispatch._resolve_user_briefing_frequency(
            mock_db,
            company_id="comp-1",
            user_id="usr-1",
            company_freq="monthly",
            company_source="hiring_policy",
        )

    assert freq == "monthly"
    assert source == "hiring_policy"
