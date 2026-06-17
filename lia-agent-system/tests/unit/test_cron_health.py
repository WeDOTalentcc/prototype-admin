"""R-036 — Cron health sentinel tests."""
import time
import pytest
from unittest.mock import patch, MagicMock


def test_record_cron_run_writes_to_redis():
    mock_rc = MagicMock()
    from app.shared.resilience.cron_health import record_cron_run
    record_cron_run("lgpd.run_cleanup_daily", redis_client=mock_rc)
    mock_rc.setex.assert_called_once()
    args = mock_rc.setex.call_args[0]
    assert args[0] == "cron:last_run:lgpd.run_cleanup_daily"
    assert args[1] == 90 * 24 * 3600  # TTL 90 days


def test_record_cron_run_is_nonfatal_on_redis_error():
    """Sentinel write failure must NOT propagate — cron task still succeeds."""
    mock_rc = MagicMock()
    mock_rc.setex.side_effect = ConnectionError("Redis down")
    from app.shared.resilience.cron_health import record_cron_run
    # Should not raise
    record_cron_run("lgpd.run_cleanup_daily", redis_client=mock_rc)


def test_get_cron_health_never_run():
    mock_rc = MagicMock()
    mock_rc.get.return_value = None
    from app.shared.resilience.cron_health import get_cron_health
    result = get_cron_health(redis_client=mock_rc)
    assert result["status"] == "degraded"
    assert "lgpd.run_cleanup_daily" in result["unhealthy_crons"]
    assert result["crons"]["lgpd.run_cleanup_daily"]["status"] == "never_run"


def test_get_cron_health_recently_run():
    mock_rc = MagicMock()
    # Set last run to 1 hour ago (well within 2h threshold for dlq health)
    mock_rc.get.return_value = str(int(time.time()) - 3600)
    from app.shared.resilience.cron_health import get_cron_health
    result = get_cron_health(redis_client=mock_rc)
    # dlq health runs hourly, threshold is 2h — should be healthy
    cron = result["crons"].get("health.check_dlq_health", {})
    assert cron.get("status") == "healthy"


def test_get_cron_health_overdue():
    mock_rc = MagicMock()
    # Set last run to 30 hours ago (exceeds 26h daily threshold)
    mock_rc.get.return_value = str(int(time.time()) - 30 * 3600)
    from app.shared.resilience.cron_health import get_cron_health
    result = get_cron_health(redis_client=mock_rc)
    assert result["status"] == "degraded"
    lgpd_cron = result["crons"]["lgpd.run_cleanup_daily"]
    assert lgpd_cron["status"] == "overdue"
    assert "lgpd.run_cleanup_daily" in result["unhealthy_crons"]


def test_get_cron_health_redis_error():
    """If Redis is completely unreachable, return error status gracefully."""
    from app.shared.resilience.cron_health import get_cron_health
    with patch(
        "app.shared.resilience.cron_health._get_sync_redis",
        side_effect=ConnectionError("Redis down"),
    ):
        result = get_cron_health()
    assert result["status"] == "error"
    assert "error" in result


def test_get_cron_health_all_healthy():
    """All crons recently run → overall status = healthy."""
    mock_rc = MagicMock()
    # 1 minute ago — healthy for all cadences
    mock_rc.get.return_value = str(int(time.time()) - 60)
    from app.shared.resilience.cron_health import get_cron_health, CRON_EXPECTED_MAX_SECONDS
    result = get_cron_health(redis_client=mock_rc)
    assert result["status"] == "healthy"
    assert result["unhealthy_crons"] == []
    assert len(result["crons"]) == len(CRON_EXPECTED_MAX_SECONDS)
