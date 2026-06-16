"""UC-P1-26: TTFPredictor — Time-to-Fill prediction with JobFeatures dataclass."""
import pytest


def test_job_features_to_dict():
    from app.shared.ml.ttf_predictor import JobFeatures

    f = JobFeatures(seniority_level="senior", location="São Paulo",
                    tech_stack=["Python", "FastAPI"], is_remote=False)
    d = f.to_dict()
    assert "seniority_level" in d
    assert "work_model" in d
    assert d["work_model"] == "presencial"


def test_job_features_remote_maps_to_work_model():
    from app.shared.ml.ttf_predictor import JobFeatures

    f = JobFeatures(seniority_level="mid", location="Remote", is_remote=True)
    d = f.to_dict()
    assert d["work_model"] == "remoto"


@pytest.mark.asyncio
async def test_predict_from_features_returns_dict():
    from app.shared.ml.ttf_predictor import JobFeatures, predict_from_features

    features = JobFeatures(seniority_level="senior", location="São Paulo",
                           tech_stack=["Python", "FastAPI"], is_remote=False)
    result = await predict_from_features(features)
    assert result["predicted_days"] > 0
    assert result["method"] in ("ml_model", "heuristic")
    assert "range" in result
    assert result["range"]["min"] < result["range"]["max"]


@pytest.mark.asyncio
async def test_remote_predicts_no_more_than_onsite():
    from app.shared.ml.ttf_predictor import JobFeatures, predict_from_features

    remote = JobFeatures("senior", "Remote", ["Python"], is_remote=True)
    onsite = JobFeatures("senior", "São Paulo", ["Python"], is_remote=False)
    r_remote = await predict_from_features(remote)
    r_onsite = await predict_from_features(onsite)
    assert r_remote["predicted_days"] <= r_onsite["predicted_days"]


@pytest.mark.asyncio
async def test_junior_faster_than_senior():
    from app.shared.ml.ttf_predictor import JobFeatures, predict_from_features

    junior = JobFeatures("junior", "SP", ["Python"])
    senior = JobFeatures("senior", "SP", ["Python"])
    r_j = await predict_from_features(junior)
    r_s = await predict_from_features(senior)
    assert r_j["predicted_days"] <= r_s["predicted_days"]


def test_heuristic_confidence_below_08():
    """Heuristic confidence should signal lower certainty than a trained model."""
    from app.shared.ml.ttf_predictor import TTFPredictor

    predictor = TTFPredictor()
    result = predictor._predict_heuristic({"seniority_level": "pleno"})
    assert result.confidence < 0.8
    assert result.source == "heuristic"


def test_job_features_defaults():
    from app.shared.ml.ttf_predictor import JobFeatures

    f = JobFeatures(seniority_level="mid")
    assert f.is_remote is False
    assert f.company_size == "medium"
    assert isinstance(f.tech_stack, list)


@pytest.mark.asyncio
async def test_predict_from_features_confidence_valid():
    from app.shared.ml.ttf_predictor import JobFeatures, predict_from_features

    features = JobFeatures(seniority_level="lead", is_remote=False)
    result = await predict_from_features(features)
    assert 0.0 < result["confidence"] <= 1.0
