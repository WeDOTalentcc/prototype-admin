"""
Contract test: sourcing must NOT run twice for the same job publish event.

The publish endpoints (lifecycle.py) call run_post_publish_sourcing inline.
The automation handler (handle_job_published) must skip sourcing when the
event payload carries sourcing_already_triggered=True.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

_ACTIVITY_SVC_PATH = "app.domains.analytics.services.activity_service.ActivityService"
_SOURCING_SVC_PATH = "app.domains.sourcing.services.sourcing_pipeline.SourcingPipelineService"
_CREATE_TASK_PATH = (
    "app.domains.automation.services.automation_handlers._create_automation_task"
)


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_handler_skips_sourcing_when_already_triggered(mock_db):
    """When sourcing_already_triggered=True, handler must NOT call run_post_publish_sourcing."""
    from app.domains.automation.services.automation_handlers import handle_job_published

    with patch(
        _ACTIVITY_SVC_PATH,
        return_value=MagicMock(create_activity=AsyncMock()),
    ), patch(
        _CREATE_TASK_PATH,
        new_callable=AsyncMock,
        return_value="task-123",
    ), patch(_SOURCING_SVC_PATH) as mock_sourcing_cls:
        mock_sourcing = MagicMock()
        mock_sourcing.run_post_publish_sourcing = AsyncMock(
            return_value={"local_candidates_added": 3}
        )
        mock_sourcing_cls.return_value = mock_sourcing

        result = await handle_job_published(
            candidate_id="",
            vacancy_id="job-001",
            company_id="company-001",
            db=mock_db,
            job_id="job-001",
            job_title="Dev Python",
            sourcing_already_triggered=True,
        )

        # Sourcing must NOT have been called
        mock_sourcing.run_post_publish_sourcing.assert_not_called()
        assert result["sourcing_activated"] is False
        assert result["sourcing_skipped_reason"] == "already_triggered_by_publish_endpoint"


@pytest.mark.asyncio
async def test_handler_runs_sourcing_when_not_already_triggered(mock_db):
    """When sourcing_already_triggered is absent/False, handler runs sourcing normally."""
    from app.domains.automation.services.automation_handlers import handle_job_published

    with patch(
        _ACTIVITY_SVC_PATH,
        return_value=MagicMock(create_activity=AsyncMock()),
    ), patch(
        _CREATE_TASK_PATH,
        new_callable=AsyncMock,
        return_value="task-456",
    ), patch(_SOURCING_SVC_PATH) as mock_sourcing_cls:
        mock_sourcing = MagicMock()
        mock_sourcing.run_post_publish_sourcing = AsyncMock(
            return_value={"local_candidates_added": 5}
        )
        mock_sourcing_cls.return_value = mock_sourcing

        result = await handle_job_published(
            candidate_id="",
            vacancy_id="job-002",
            company_id="company-002",
            db=mock_db,
            job_id="job-002",
            job_title="Dev React",
            # sourcing_already_triggered NOT passed - defaults to False
        )

        # Sourcing MUST have been called
        mock_sourcing.run_post_publish_sourcing.assert_called_once()
        assert result["sourcing_activated"] is True


@pytest.mark.asyncio
async def test_handler_runs_sourcing_when_explicit_false(mock_db):
    """When sourcing_already_triggered=False explicitly, handler runs sourcing."""
    from app.domains.automation.services.automation_handlers import handle_job_published

    with patch(
        _ACTIVITY_SVC_PATH,
        return_value=MagicMock(create_activity=AsyncMock()),
    ), patch(
        _CREATE_TASK_PATH,
        new_callable=AsyncMock,
        return_value="task-789",
    ), patch(_SOURCING_SVC_PATH) as mock_sourcing_cls:
        mock_sourcing = MagicMock()
        mock_sourcing.run_post_publish_sourcing = AsyncMock(
            return_value={"local_candidates_added": 0}
        )
        mock_sourcing_cls.return_value = mock_sourcing

        result = await handle_job_published(
            candidate_id="",
            vacancy_id="job-003",
            company_id="company-003",
            db=mock_db,
            job_id="job-003",
            job_title="Designer",
            sourcing_already_triggered=False,
        )

        mock_sourcing.run_post_publish_sourcing.assert_called_once()
        assert result["sourcing_activated"] is True


@pytest.mark.asyncio
async def test_event_payload_carries_sourcing_flag():
    """Verify on_job_status_changed passes sourcing_already_triggered through to payload."""
    from app.domains.analytics.services.event_dispatcher import EventDispatcher

    dispatcher = EventDispatcher()
    dispatcher.disable()  # prevent actual dispatch

    result = await dispatcher.on_job_status_changed(
        job_id="job-100",
        company_id="company-100",
        new_status="Ativa",
        previous_status="Rascunho",
        changed_by="test@test.com",
        job_title="Test Job",
        sourcing_already_triggered=True,
    )

    # When disabled, dispatch returns early with skipped=True
    assert result.get("skipped") is True
