"""
Tests for T1: hired_candidate_id is optional in /close endpoint when close_reason='not_filled'.

TDD: Red → Green → Refactor
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_request_mock(json_data: dict) -> AsyncMock:
    """Build a mock FastAPI Request that returns json_data from .json()."""
    req = AsyncMock()
    req.json = AsyncMock(return_value=json_data)
    return req


def _make_vacancy_mock(title: str = "Senior Dev") -> MagicMock:
    v = MagicMock()
    v.title = title
    return v


def _make_repo_mock(vacancy=None) -> AsyncMock:
    repo = AsyncMock()
    repo.get_vacancy_by_uuid_str = AsyncMock(return_value=vacancy or _make_vacancy_mock())
    repo.close_vacancy = AsyncMock()
    repo.rollback = AsyncMock()
    repo.db = MagicMock()
    return repo


def _make_activity_svc_mock() -> AsyncMock:
    svc = AsyncMock()
    svc.create_activity = AsyncMock()
    return svc


def _make_comm_svc_mock() -> AsyncMock:
    svc = AsyncMock()
    svc.send_message = AsyncMock(return_value={"success": True})
    return svc


def _make_user_and_company():
    user = MagicMock()
    user.id = "user-uuid-001"
    company_id = "company-uuid-001"
    return user, company_id


# event_dispatcher is a lazy local import inside close_vacancy — patch the source module
_ED_PATH = "app.shared.services.event_dispatcher.event_dispatcher"


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestCloseVacancyOptionalHired:
    """Unit tests for the /close endpoint's optional hired_candidate_id logic."""

    @pytest.mark.asyncio
    async def test_close_vacancy_with_hired_candidate(self):
        """T1-1: hired_candidate_id present + close_reason='filled' → success (HTTP 200)."""
        from app.api.v1.job_vacancies.lifecycle import close_vacancy

        user, company_id = _make_user_and_company()
        repo = _make_repo_mock()
        activity_svc = _make_activity_svc_mock()
        comm_svc = _make_comm_svc_mock()
        request = _make_request_mock({
            "hired_candidate_id": "cand-uuid-001",
            "close_reason": "filled",
            "hired_notification": {},
            "other_notifications": {"candidate_ids": []},
        })

        with (
            patch("app.api.v1.job_vacancies.lifecycle.get_user_company_id", return_value=company_id),
            patch(_ED_PATH) as mock_ed,
        ):
            mock_ed.on_job_status_changed = AsyncMock()
            result = await close_vacancy(
                vacancy_id="vacancy-uuid-001",
                request=request,
                repo=repo,
                current_user=user,
                activity_svc=activity_svc,
                comm_svc=comm_svc,
                company_id=company_id,
            )

        assert result["success"] is True
        assert result["hired_candidate_id"] == "cand-uuid-001"
        assert result["status"] == "Concluída"
        repo.close_vacancy.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_vacancy_not_filled_no_candidate(self):
        """T1-2: no hired_candidate_id + close_reason='not_filled' → success (HTTP 200)."""
        from app.api.v1.job_vacancies.lifecycle import close_vacancy

        user, company_id = _make_user_and_company()
        repo = _make_repo_mock()
        activity_svc = _make_activity_svc_mock()
        comm_svc = _make_comm_svc_mock()
        request = _make_request_mock({
            "hired_candidate_id": None,
            "close_reason": "not_filled",
            "hired_notification": {},
            "other_notifications": {"candidate_ids": ["cand-b", "cand-c"]},
        })

        with (
            patch("app.api.v1.job_vacancies.lifecycle.get_user_company_id", return_value=company_id),
            patch(_ED_PATH) as mock_ed,
        ):
            mock_ed.on_job_status_changed = AsyncMock()
            result = await close_vacancy(
                vacancy_id="vacancy-uuid-002",
                request=request,
                repo=repo,
                current_user=user,
                activity_svc=activity_svc,
                comm_svc=comm_svc,
                company_id=company_id,
            )

        assert result["success"] is True
        assert result["hired_candidate_id"] is None
        assert result["status"] == "Concluída"
        repo.close_vacancy.assert_awaited_once()

        # Verify the activity description reflects no-hire path
        call_kwargs = activity_svc.create_activity.call_args.kwargs
        assert "sem contratação" in call_kwargs["description"]

    @pytest.mark.asyncio
    async def test_close_vacancy_missing_hired_when_filled(self):
        """T1-3: no hired_candidate_id + close_reason='filled' → HTTP 400."""
        from app.api.v1.job_vacancies.lifecycle import close_vacancy

        user, company_id = _make_user_and_company()
        repo = _make_repo_mock()
        activity_svc = _make_activity_svc_mock()
        comm_svc = _make_comm_svc_mock()
        request = _make_request_mock({
            "hired_candidate_id": None,
            "close_reason": "filled",
            "hired_notification": {},
            "other_notifications": {},
        })

        with (
            patch("app.api.v1.job_vacancies.lifecycle.get_user_company_id", return_value=company_id),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await close_vacancy(
                    vacancy_id="vacancy-uuid-003",
                    request=request,
                    repo=repo,
                    current_user=user,
                    activity_svc=activity_svc,
                    comm_svc=comm_svc,
                    company_id=company_id,
                )

        assert exc_info.value.status_code == 400
        assert "hired_candidate_id" in exc_info.value.detail
        repo.close_vacancy.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_close_vacancy_default_close_reason_requires_hired(self):
        """T1-4: no hired_candidate_id + no close_reason (defaults to 'filled') → HTTP 400."""
        from app.api.v1.job_vacancies.lifecycle import close_vacancy

        user, company_id = _make_user_and_company()
        repo = _make_repo_mock()
        activity_svc = _make_activity_svc_mock()
        comm_svc = _make_comm_svc_mock()
        # close_reason absent — should default to "filled"
        request = _make_request_mock({
            "hired_notification": {},
            "other_notifications": {},
        })

        with (
            patch("app.api.v1.job_vacancies.lifecycle.get_user_company_id", return_value=company_id),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await close_vacancy(
                    vacancy_id="vacancy-uuid-004",
                    request=request,
                    repo=repo,
                    current_user=user,
                    activity_svc=activity_svc,
                    comm_svc=comm_svc,
                    company_id=company_id,
                )

        assert exc_info.value.status_code == 400
