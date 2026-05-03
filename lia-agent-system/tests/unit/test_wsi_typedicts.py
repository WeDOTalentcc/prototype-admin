"""TDD tests for UC-P2-06: WSI TypedDicts.

Verifies that wsi_types.py TypedDicts exist, are importable,
and that wsi_repository methods have typed (non-Any) return annotations.
"""
import inspect


def test_wsi_types_importable():
    """All WSI TypedDicts must be importable from the canonical schema module."""
    from app.domains.voice.schemas.wsi_types import (  # noqa: F401
        ScreeningPolicyConfig,
        ScreeningPolicyResult,
        WsiCandidateRankRow,
        WsiFeedbackRow,
        WsiJobVacancyContextRow,
        WsiQuestionTextRow,
        WsiReportRow,
        WsiResultRow,
        WsiSessionRow,
        WsiVacancyAveragesRow,
    )
    assert True  # import check


def test_wsi_repository_get_session_return_type():
    """get_session must have a typed return annotation, not bare Any or missing."""
    from app.domains.voice.repositories.wsi_repository import WsiRepository

    sig = inspect.signature(WsiRepository.get_session)
    ret = sig.return_annotation
    assert ret is not inspect.Parameter.empty, "get_session has no return annotation"
    assert "Any" not in str(ret), f"get_session still returns Any: {ret}"


def test_wsi_repository_get_result_with_session_return_type():
    """get_result_with_session must have a typed annotation."""
    from app.domains.voice.repositories.wsi_repository import WsiRepository

    sig = inspect.signature(WsiRepository.get_result_with_session)
    ret = sig.return_annotation
    assert ret is not inspect.Parameter.empty
    assert "Any" not in str(ret), f"returns Any: {ret}"


def test_wsi_repository_get_vacancy_averages_return_type():
    """get_vacancy_averages must have a typed annotation."""
    from app.domains.voice.repositories.wsi_repository import WsiRepository

    sig = inspect.signature(WsiRepository.get_vacancy_averages)
    ret = sig.return_annotation
    assert ret is not inspect.Parameter.empty
    assert "Any" not in str(ret), f"returns Any: {ret}"


def test_wsi_session_row_has_required_keys():
    """WsiSessionRow TypedDict must declare all expected columns."""
    from app.domains.voice.schemas.wsi_types import WsiSessionRow

    hints = WsiSessionRow.__annotations__
    for key in ("id", "candidate_id", "job_vacancy_id", "screening_type", "mode", "status"):
        assert key in hints, f"Missing field '{key}' in WsiSessionRow"


def test_screening_policy_result_has_required_keys():
    """ScreeningPolicyResult must have 'questions' and 'policy_applied' fields."""
    from app.domains.voice.schemas.wsi_types import ScreeningPolicyResult

    hints = ScreeningPolicyResult.__annotations__
    assert "questions" in hints
    assert "policy_applied" in hints


def test_screening_policy_config_has_required_keys():
    """ScreeningPolicyConfig must mirror get_screening_policy() return dict."""
    from app.domains.voice.schemas.wsi_types import ScreeningPolicyConfig

    hints = ScreeningPolicyConfig.__annotations__
    for key in ("experience_policy", "default_screening_questions",
                "salary_expectation_filter", "salary_tolerance_percent"):
        assert key in hints, f"Missing field '{key}' in ScreeningPolicyConfig"


def test_wsi_screening_pipeline_apply_policy_typed():
    """apply_screening_policy return annotation must be ScreeningPolicyResult."""
    from app.domains.cv_screening.services.wsi_screening_pipeline import (
        WSIScreeningPipeline,
    )
    from app.domains.voice.schemas.wsi_types import ScreeningPolicyResult

    sig = inspect.signature(WSIScreeningPipeline.apply_screening_policy)
    ret = sig.return_annotation
    assert ret is not inspect.Parameter.empty
    # Accept string forward ref or direct type
    assert "ScreeningPolicyResult" in str(ret), f"Expected ScreeningPolicyResult, got: {ret}"


def test_wsi_screening_pipeline_get_policy_typed():
    """get_screening_policy return annotation must be ScreeningPolicyConfig."""
    from app.domains.cv_screening.services.wsi_screening_pipeline import (
        WSIScreeningPipeline,
    )

    sig = inspect.signature(WSIScreeningPipeline.get_screening_policy)
    ret = sig.return_annotation
    assert ret is not inspect.Parameter.empty
    assert "ScreeningPolicyConfig" in str(ret), f"Expected ScreeningPolicyConfig, got: {ret}"
