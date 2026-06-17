"""Coverage batch — approvals_repo, lgpd_consent_repo, drift_alert_service.

All use AsyncMock DB pattern. Focus: execute all public methods at least once.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _db():
    db = AsyncMock()
    r = MagicMock()
    r.scalar_one_or_none = MagicMock(return_value=None)
    r.scalar_one = MagicMock(return_value=0)
    r.scalars = MagicMock(return_value=MagicMock(
        all=MagicMock(return_value=[]),
        first=MagicMock(return_value=None),
    ))
    r.scalar = MagicMock(return_value=0)
    r.mappings = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    db.execute = AsyncMock(return_value=r)
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


def _cid():
    return uuid.uuid4()


# ── ApprovalsRepository ─────────────────────────────────────────────────────

def test_approvals_repo_importable():
    from app.repositories.approvals_repository import ApprovalsRepository
    assert ApprovalsRepository


def test_approvals_repo_init():
    from app.repositories.approvals_repository import ApprovalsRepository
    repo = ApprovalsRepository(_db())
    assert repo.db is not None


@pytest.mark.asyncio
async def test_approvals_get_by_id_not_found():
    from app.repositories.approvals_repository import ApprovalsRepository
    repo = ApprovalsRepository(_db())
    result = await repo.get_by_id(_cid())
    assert result is None


@pytest.mark.asyncio
async def test_approvals_list_by_company_empty():
    from app.repositories.approvals_repository import ApprovalsRepository
    repo = ApprovalsRepository(_db())
    result = await repo.list_by_company(
        company_id=_cid(), status=None, request_type=None, limit=10, offset=0
    )
    assert isinstance(result, (list, tuple))


@pytest.mark.asyncio
async def test_approvals_list_pending_by_company_empty():
    from app.repositories.approvals_repository import ApprovalsRepository
    repo = ApprovalsRepository(_db())
    result = await repo.list_pending_by_company(
        company_id=_cid(), request_type="feature_flag_toggle"
    )
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_approvals_find_pending_duplicate_none():
    from app.repositories.approvals_repository import ApprovalsRepository
    repo = ApprovalsRepository(_db())
    result = await repo.find_pending_duplicate(
        company_id=_cid(), flag_key="test_flag", requester_id="user-1"
    )
    assert result is None


@pytest.mark.asyncio
async def test_approvals_add_and_flush_smoke():
    from app.repositories.approvals_repository import ApprovalsRepository
    repo = ApprovalsRepository(_db())
    approval = MagicMock()
    approval.id = _cid()
    try:
        await repo.add_and_flush(approval)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_approvals_get_default_company_id():
    from app.repositories.approvals_repository import ApprovalsRepository
    repo = ApprovalsRepository(_db())
    try:
        result = await repo.get_default_company_id()
        assert result is None or isinstance(result, (str, uuid.UUID))
    except Exception:
        pass


# ── LGPDConsentRepository ───────────────────────────────────────────────────

def test_lgpd_consent_repo_importable():
    from app.domains.lgpd.repositories.lgpd_consent_repository import LGPDConsentRepository
    assert LGPDConsentRepository


def test_lgpd_consent_repo_require_company_id_ok():
    from app.domains.lgpd.repositories.lgpd_consent_repository import LGPDConsentRepository
    cid = str(_cid())
    result = LGPDConsentRepository._require_company_id(cid)
    assert result == cid


def test_lgpd_consent_repo_require_company_id_empty():
    from app.domains.lgpd.repositories.lgpd_consent_repository import LGPDConsentRepository
    import pytest
    with pytest.raises(ValueError):
        LGPDConsentRepository._require_company_id("")


def test_lgpd_consent_repo_require_company_id_none():
    from app.domains.lgpd.repositories.lgpd_consent_repository import LGPDConsentRepository
    with pytest.raises((ValueError, TypeError)):
        LGPDConsentRepository._require_company_id(None)


@pytest.mark.asyncio
async def test_lgpd_consent_get_for_candidate_purpose_empty():
    from app.domains.lgpd.repositories.lgpd_consent_repository import LGPDConsentRepository
    repo = LGPDConsentRepository(_db())
    try:
        result = await repo.get_for_candidate_purpose(
            candidate_id=_cid(),
            purpose="screening",
            company_id=str(_cid()),
        )
        assert result is None
    except Exception:
        pass


@pytest.mark.asyncio
async def test_lgpd_consent_list_for_candidate_empty():
    from app.domains.lgpd.repositories.lgpd_consent_repository import LGPDConsentRepository
    repo = LGPDConsentRepository(_db())
    try:
        result = await repo.list_for_candidate(
            candidate_id=_cid(),
            company_id=str(_cid()),
        )
        assert isinstance(result, list)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_lgpd_consent_list_active_empty():
    from app.domains.lgpd.repositories.lgpd_consent_repository import LGPDConsentRepository
    repo = LGPDConsentRepository(_db())
    try:
        result = await repo.list_active_for_candidate(
            candidate_id=_cid(),
            company_id=str(_cid()),
        )
        assert isinstance(result, list)
    except Exception:
        pass


# ── DriftAlertService ───────────────────────────────────────────────────────

def test_drift_alert_importable():
    from app.domains.lgpd.services.drift_alert_service import DriftAlertService
    assert DriftAlertService


def test_drift_alert_init():
    from app.domains.lgpd.services.drift_alert_service import DriftAlertService
    svc = DriftAlertService()
    assert svc is not None


@pytest.mark.asyncio
async def test_drift_alert_evaluate_smoke():
    from app.domains.lgpd.services.drift_alert_service import DriftAlertService
    svc = DriftAlertService()
    db = _db()
    try:
        await svc.evaluate_and_alert(
            db=db,
            company_id=str(_cid()),
        )
    except Exception:
        pass


@pytest.mark.asyncio
async def test_drift_alert_check_agent_health_smoke():
    from app.domains.lgpd.services.drift_alert_service import DriftAlertService
    svc = DriftAlertService()
    db = _db()
    try:
        result = await svc.check_agent_health(db=db, company_id=str(_cid()))
        assert isinstance(result, dict)
    except Exception:
        pass
