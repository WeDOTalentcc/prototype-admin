"""UC-P1-27: A/B test auto-promotion when p<0.01 and n>=100."""
import pytest
from unittest.mock import AsyncMock, patch


def _make_service():
    from app.shared.learning.ab_testing_service import ABTestingService
    return ABTestingService()


def _results_with(p_value, n_control, n_variant, winner_variant="treatment"):
    """Build a fake get_test_results() return value."""
    return {
        "test_name": "test_abc",
        "winner": {
            "variant": winner_variant,
            "metric": "satisfaction_score",
            "improvement_pct": 12.5,
            "p_value": p_value,
        },
        "statistical_significance": {
            f"satisfaction_score:control_vs_{winner_variant}": {
                "control": "control",
                "variant": winner_variant,
                "n_control": n_control,
                "n_variant": n_variant,
                "p_value": p_value,
                "is_significant": True,
            }
        },
    }


@pytest.mark.asyncio
async def test_auto_promote_with_significant_winner():
    """p<0.01, n>=100 -> winner promoted, losers deactivated."""
    svc = _make_service()
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()

    fake_results = _results_with(p_value=0.005, n_control=150, n_variant=150)

    with patch.object(svc, 'get_test_results', new=AsyncMock(return_value=fake_results)):
        result = await svc.auto_promote_winner("test_abc", db)

    assert result["promoted"] is True
    assert result["winner"] == "treatment"
    assert result["reason"] == "auto_promoted"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_no_promote_insufficient_n():
    """n<100 -> no promotion even if p<0.01."""
    svc = _make_service()
    db = AsyncMock()

    fake_results = _results_with(p_value=0.005, n_control=50, n_variant=50)

    with patch.object(svc, 'get_test_results', new=AsyncMock(return_value=fake_results)):
        result = await svc.auto_promote_winner("test_abc", db)

    assert result["promoted"] is False
    assert "n=" in result["reason"]
    assert "< 100" in result["reason"]
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_no_promote_not_significant():
    """p>=0.01 -> no promotion."""
    svc = _make_service()
    db = AsyncMock()

    fake_results = _results_with(p_value=0.02, n_control=200, n_variant=200)

    with patch.object(svc, 'get_test_results', new=AsyncMock(return_value=fake_results)):
        result = await svc.auto_promote_winner("test_abc", db)

    assert result["promoted"] is False
    assert "p_value=" in result["reason"]
    assert ">= 0.01" in result["reason"]


@pytest.mark.asyncio
async def test_no_promote_no_winner():
    """No winner in results -> no promotion."""
    svc = _make_service()
    db = AsyncMock()

    empty_results = {
        "test_name": "test_abc",
        "winner": None,
        "statistical_significance": {},
    }

    with patch.object(svc, 'get_test_results', new=AsyncMock(return_value=empty_results)):
        result = await svc.auto_promote_winner("test_abc", db)

    assert result["promoted"] is False
    assert result["reason"] == "no_winner_yet"


def test_threshold_corrected():
    """Verify N_MIN_PER_VARIANT=100 and p threshold=0.01 in service source."""
    from app.shared.learning.ab_testing_service import ABTestingService
    svc = ABTestingService()
    assert svc.N_MIN_PER_VARIANT == 100, (
        f"Expected N_MIN_PER_VARIANT=100, got {svc.N_MIN_PER_VARIANT}"
    )

    import inspect
    source = inspect.getsource(svc.get_test_results)
    assert 'p_value < 0.01' in source, (
        "p_value threshold should be 0.01"
    )
    assert 'p_value < 0.05' not in source, (
        "Old p_value < 0.05 threshold still present"
    )
