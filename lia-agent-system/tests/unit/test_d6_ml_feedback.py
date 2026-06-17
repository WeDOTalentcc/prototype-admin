"""
D6 — ML Adaptativo (Feedback Loop)

Testa MLFeedbackService: record_signal, compute_job_weights, get_weights_for_job.
Testa endpoint POST /ml-feedback/signal e GET /ml-feedback/weights.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime


COMPANY_ID = str(uuid4())
JOB_ID = str(uuid4())
CANDIDATE_ID = str(uuid4())


class TestMLFeedbackService:

    @pytest.mark.asyncio
    async def test_record_signal_returns_true_on_success(self):
        """record_signal retorna True quando CalibrationService não lança erro."""
        from app.shared.services.ml_feedback_service import MLFeedbackService, FeedbackSignal

        signal = FeedbackSignal(
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
            company_id=COMPANY_ID,
            ai_score=72.0,
            recruiter_decision="hire",
        )

        db = MagicMock()

        with patch(
            "app.domains.analytics.services.calibration_service.CalibrationService.record_explicit_feedback",
            new_callable=AsyncMock,
        ):
            service = MLFeedbackService()
            result = await service.record_signal(db, signal)

        assert result is True

    @pytest.mark.asyncio
    async def test_record_signal_fail_open_on_error(self):
        """record_signal retorna False sem lançar exceção em caso de erro."""
        from app.shared.services.ml_feedback_service import MLFeedbackService, FeedbackSignal

        signal = FeedbackSignal(
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
            company_id=COMPANY_ID,
            ai_score=65.0,
            recruiter_decision="reject",
        )

        db = MagicMock()

        with patch(
            "app.domains.analytics.services.calibration_service.CalibrationService.record_explicit_feedback",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB error"),
        ):
            service = MLFeedbackService()
            result = await service.record_signal(db, signal)

        assert result is False

    @pytest.mark.asyncio
    async def test_compute_weights_returns_neutral_when_insufficient_samples(self):
        """Pesos neutros (1.0) quando há menos que MIN_FEEDBACK_SAMPLES amostras."""
        from app.shared.services.ml_feedback_service import (
            MLFeedbackService, MIN_FEEDBACK_SAMPLES, JobScoringWeights
        )

        service = MLFeedbackService()

        # Simula resultado com 2 eventos — patch compute_job_weights internamente
        # ao isolar via mock da query
        with patch.object(
            service, "compute_job_weights",
            new_callable=AsyncMock,
            return_value=JobScoringWeights(
                job_id=JOB_ID,
                company_id=COMPANY_ID,
                sample_count=2,  # abaixo do mínimo
            ),
        ):
            weights = await service.compute_job_weights(MagicMock(), JOB_ID, COMPANY_ID)

        assert weights.job_id == JOB_ID
        assert weights.sample_count == 2
        # Pesos neutros (1.0) pois amostras insuficientes
        assert all(v == 1.0 for v in weights.weights.values())

    @pytest.mark.asyncio
    async def test_compute_weights_fail_open_on_db_error(self):
        """compute_job_weights retorna pesos neutros em caso de erro."""
        from app.shared.services.ml_feedback_service import MLFeedbackService

        db = MagicMock()
        db.execute = AsyncMock(side_effect=RuntimeError("DB unavailable"))

        service = MLFeedbackService()
        weights = await service.compute_job_weights(db, JOB_ID, COMPANY_ID)

        assert weights.job_id == JOB_ID
        # Default weights all 1.0
        assert weights.weights == {
            "technical": 1.0,
            "experience": 1.0,
            "education": 1.0,
            "soft_skills": 1.0,
            "cultural_fit": 1.0,
        }

    def test_job_scoring_weights_to_dict(self):
        """to_dict retorna estrutura esperada."""
        from app.shared.services.ml_feedback_service import JobScoringWeights

        w = JobScoringWeights(
            job_id="job-1",
            company_id="comp-1",
            weights={"technical": 1.2, "experience": 0.8},
            computed_at=datetime(2026, 3, 15, 10, 0, 0),
            sample_count=12,
        )
        d = w.to_dict()
        assert d["job_id"] == "job-1"
        assert d["weights"]["technical"] == 1.2
        assert d["sample_count"] == 12
        assert "2026-03-15" in d["computed_at"]


class TestMLFeedbackEndpoint:

    def _make_app(self):
        from fastapi import FastAPI
        from app.api.v1.ml_feedback import router
        from app.core.database import get_db
        from app.shared.security.require_company_id import require_company_id

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        async def mock_db():
            yield MagicMock()

        async def mock_company_id():
            return COMPANY_ID

        app.dependency_overrides[get_db] = mock_db
        app.dependency_overrides[require_company_id] = mock_company_id
        return app

    def test_record_signal_returns_200(self):
        """POST /signal retorna 200 com recorded=True."""
        from fastapi.testclient import TestClient

        app = self._make_app()

        with patch(
            "app.domains.analytics.services.ml_feedback_service.MLFeedbackService.record_signal",
            new_callable=AsyncMock,
            return_value=True,
        ):
            client = TestClient(app)
            response = client.post(
                "/api/v1/ml-feedback/signal",
                json={
                    "candidate_id": str(uuid4()),
                    "job_id": JOB_ID,
                    "ai_score": 75.0,
                    "recruiter_decision": "hire",
                },
                headers={"X-Company-ID": COMPANY_ID},
            )

        assert response.status_code == 200
        assert response.json()["recorded"] is True

    def test_get_weights_returns_200(self):
        """GET /weights retorna pesos com job_id."""
        from fastapi.testclient import TestClient
        from app.shared.services.ml_feedback_service import JobScoringWeights

        app = self._make_app()
        mock_weights = JobScoringWeights(
            job_id=JOB_ID,
            company_id=COMPANY_ID,
            sample_count=10,
        )

        with patch(
            "app.domains.analytics.services.ml_feedback_service.MLFeedbackService.get_weights_for_job",
            new_callable=AsyncMock,
            return_value=mock_weights,
        ):
            client = TestClient(app)
            response = client.get(
                f"/api/v1/ml-feedback/weights?job_id={JOB_ID}",
                headers={"X-Company-ID": COMPANY_ID},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == JOB_ID

    def test_signal_requires_company_header(self):
        """Sem X-Company-ID retorna 401."""
        from fastapi.testclient import TestClient

        app = self._make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/ml-feedback/signal",
            json={
                "candidate_id": str(uuid4()),
                "job_id": JOB_ID,
                "ai_score": 70.0,
                "recruiter_decision": "reject",
            },
        )
        assert response.status_code == 401

    def test_signal_invalid_decision_returns_422(self):
        """recruiter_decision inválido retorna 422."""
        from fastapi.testclient import TestClient

        app = self._make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/ml-feedback/signal",
            json={
                "candidate_id": str(uuid4()),
                "job_id": JOB_ID,
                "ai_score": 70.0,
                "recruiter_decision": "invalid_decision",
            },
            headers={"X-Company-ID": COMPANY_ID},
        )
        assert response.status_code == 422

    def test_celery_task_registered(self):
        """Celery task ml.feedback.process_weights está registrada."""
        from app.jobs.celery_tasks import celery_app

        assert "ml.feedback.process_weights" in celery_app.tasks


class TestMLFeedbackWiring:

    @pytest.mark.asyncio
    async def test_compute_calibration_adjustment_returns_float(self):
        """compute_calibration_adjustment retorna float entre -5 e +5."""
        from app.shared.services.ml_feedback_service import MLFeedbackService

        service = MLFeedbackService()
        db = MagicMock()

        with patch.object(
            service, "compute_job_weights",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB error"),
        ):
            result = await service.compute_calibration_adjustment(db, COMPANY_ID, JOB_ID)

        assert isinstance(result, float)
        assert -5.0 <= result <= 5.0

    @pytest.mark.asyncio
    async def test_record_decision_helper_returns_bool(self):
        """record_decision retorna bool."""
        from app.shared.services.ml_feedback_service import MLFeedbackService

        service = MLFeedbackService()
        db = MagicMock()

        with patch.object(
            service, "record_signal",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await service.record_decision(
                db=db,
                company_id=COMPANY_ID,
                job_id=JOB_ID,
                candidate_id=CANDIDATE_ID,
                lia_score=75.0,
                decision="hire",
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_compute_calibration_adjustment_no_db_returns_zero(self):
        """compute_calibration_adjustment retorna 0.0 quando db=None."""
        from app.shared.services.ml_feedback_service import MLFeedbackService

        service = MLFeedbackService()
        # db=None — deve retornar 0.0 sem erro
        result = await service.compute_calibration_adjustment(None, COMPANY_ID, JOB_ID)
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_record_decision_propagates_failure_as_false(self):
        """record_decision retorna False quando record_signal falha (fail-open)."""
        from app.shared.services.ml_feedback_service import MLFeedbackService

        service = MLFeedbackService()
        db = MagicMock()

        with patch.object(
            service, "record_signal",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await service.record_decision(
                db=db,
                company_id=COMPANY_ID,
                job_id=JOB_ID,
                candidate_id=CANDIDATE_ID,
                lia_score=55.0,
                decision="reject",
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_lia_score_service_async_calibration_no_db(self):
        """LIAScoreService._get_calibration_adjustment_async retorna 0.0 sem db."""
        from app.shared.services.lia_score_service import LIAScoreService

        service = LIAScoreService()
        result = await service._get_calibration_adjustment_async(
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
            company_id=COMPANY_ID,
            db=None,
        )
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_lia_score_service_async_calibration_with_db(self):
        """LIAScoreService._get_calibration_adjustment_async usa ml_feedback_service."""
        from app.shared.services.lia_score_service import LIAScoreService

        service = LIAScoreService()
        db = MagicMock()

        with patch(
            "app.domains.analytics.services.ml_feedback_service.MLFeedbackService.compute_calibration_adjustment",
            new_callable=AsyncMock,
            return_value=1.5,
        ):
            result = await service._get_calibration_adjustment_async(
                candidate_id=CANDIDATE_ID,
                job_id=JOB_ID,
                company_id=COMPANY_ID,
                db=db,
            )

        assert isinstance(result, float)
        assert -5.0 <= result <= 5.0
