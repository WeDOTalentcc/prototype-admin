"""
D5 — Granular Consent LGPD

Testa GranularConsentService: mapeamento granular, bulk_update, get_summary,
check_purpose, e o endpoint FastAPI.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime


class TestGranularPurposeMap:

    def test_each_ai_purpose_has_distinct_type(self):
        """Cada finalidade de IA deve ter consent_type próprio (não todos SCREENING)."""
        from app.shared.services.granular_consent_service import GRANULAR_PURPOSE_MAP

        assert GRANULAR_PURPOSE_MAP["ai_screening"] == "SCREENING"
        assert GRANULAR_PURPOSE_MAP["ai_scoring"] == "AI_SCORING"
        assert GRANULAR_PURPOSE_MAP["ai_video_analysis"] == "AI_VIDEO_ANALYSIS"
        assert GRANULAR_PURPOSE_MAP["ai_comparison"] == "AI_COMPARISON"
        assert GRANULAR_PURPOSE_MAP["data_retention"] == "DATA_RETENTION"
        assert GRANULAR_PURPOSE_MAP["marketing"] == "MARKETING"
        assert GRANULAR_PURPOSE_MAP["analytics"] == "ANALYTICS"

    def test_blocking_purposes_are_ai_related(self):
        """BLOCKING_PURPOSES inclui todas as finalidades de IA críticas."""
        from app.shared.services.granular_consent_service import BLOCKING_PURPOSES

        assert "ai_screening" in BLOCKING_PURPOSES
        assert "ai_scoring" in BLOCKING_PURPOSES
        assert "ai_video_analysis" in BLOCKING_PURPOSES
        assert "ai_comparison" in BLOCKING_PURPOSES
        # marketing e analytics NÃO são bloqueantes
        assert "marketing" not in BLOCKING_PURPOSES
        assert "analytics" not in BLOCKING_PURPOSES


class TestGranularConsentService:

    def _make_service(self, db=None):
        from app.shared.services.granular_consent_service import GranularConsentService
        return GranularConsentService(db or MagicMock())

    @pytest.mark.asyncio
    async def test_get_summary_empty_db_returns_all_not_given(self):
        """Sem registros no BD, todos os consentimentos retornam given=False."""
        from app.shared.services.granular_consent_service import GranularConsentService, GRANULAR_PURPOSE_MAP

        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        service = GranularConsentService(db)
        with patch(
            "app.services.granular_consent_service.GranularConsentService.get_summary",
            wraps=service.get_summary,
        ):
            summary = await service.get_summary("cand-1", "company-1")

        assert summary.candidate_id == "cand-1"
        assert summary.company_id == "company-1"
        assert len(summary.consents) == len(GRANULAR_PURPOSE_MAP)
        assert all(not c.given for c in summary.consents)
        assert summary.all_blocking_given is False

    @pytest.mark.asyncio
    async def test_get_summary_with_given_consents(self):
        """Com registros, get_summary reflete o estado correto."""
        from app.shared.services.granular_consent_service import GranularConsentService, GRANULAR_PURPOSE_MAP

        now = datetime.utcnow()

        def _make_consent(ctype, given):
            c = MagicMock()
            c.consent_type = ctype
            c.consent_given = given
            c.revoked_at = None if given else now
            c.consent_date = now if given else None
            c.consent_source = "form"
            return c

        # Simula todos os blocking purposes como concedidos
        from app.shared.services.granular_consent_service import BLOCKING_PURPOSES
        consents = [
            _make_consent(GRANULAR_PURPOSE_MAP[p], True)
            for p in BLOCKING_PURPOSES
        ]

        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = consents
        db.execute = AsyncMock(return_value=mock_result)

        service = GranularConsentService(db)
        summary = await service.get_summary("cand-1", "company-1")

        assert summary.all_blocking_given is True

    @pytest.mark.asyncio
    async def test_bulk_update_inserts_new_records(self):
        """bulk_update cria registros para finalidades novas."""
        from app.shared.services.granular_consent_service import GranularConsentService

        added = []

        db = MagicMock()
        # select retorna None (sem registro existente)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        db.add = lambda obj: added.append(obj)
        db.flush = AsyncMock()

        service = GranularConsentService(db)
        updated = await service.bulk_update(
            candidate_id="cand-2",
            company_id="comp-1",
            updates={"ai_scoring": True, "marketing": False},
            source="portal",
        )

        assert len(updated) == 2
        assert any(u.purpose == "ai_scoring" and u.given for u in updated)
        assert any(u.purpose == "marketing" and not u.given for u in updated)
        # 2 novos objetos adicionados ao db
        assert len(added) == 2

    @pytest.mark.asyncio
    async def test_bulk_update_updates_existing_record(self):
        """bulk_update atualiza registro existente sem criar duplicata."""
        from app.shared.services.granular_consent_service import GranularConsentService

        existing = MagicMock()
        existing.consent_given = False
        existing.revoked_at = datetime.utcnow()

        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db.execute = AsyncMock(return_value=mock_result)
        db.flush = AsyncMock()

        service = GranularConsentService(db)
        updated = await service.bulk_update(
            candidate_id="cand-3",
            company_id="comp-1",
            updates={"ai_screening": True},
        )

        # Registro existente atualizado
        assert existing.consent_given is True
        assert existing.revoked_at is None
        assert len(updated) == 1
        assert updated[0].given is True

    @pytest.mark.asyncio
    async def test_check_purpose_returns_true_when_given(self):
        """check_purpose retorna True quando consent_given=True e não revogado."""
        from app.shared.services.granular_consent_service import GranularConsentService

        record = MagicMock()
        record.consent_given = True
        record.revoked_at = None

        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        db.execute = AsyncMock(return_value=mock_result)

        service = GranularConsentService(db)
        result = await service.check_purpose("cand-1", "comp-1", "ai_scoring")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_purpose_returns_false_when_absent(self):
        """check_purpose retorna False quando sem registro."""
        from app.shared.services.granular_consent_service import GranularConsentService

        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        service = GranularConsentService(db)
        result = await service.check_purpose("cand-1", "comp-1", "marketing")
        assert result is False

    @pytest.mark.asyncio
    async def test_check_purpose_fail_open_on_exception(self):
        """check_purpose retorna True (fail-open) em caso de erro."""
        from app.shared.services.granular_consent_service import GranularConsentService

        db = MagicMock()
        db.execute = AsyncMock(side_effect=RuntimeError("db error"))

        service = GranularConsentService(db)
        result = await service.check_purpose("cand-1", "comp-1", "ai_scoring")
        assert result is True  # fail-open


class TestGranularConsentEndpoint:

    def test_get_summary_returns_200(self):
        """GET /consent/granular/{candidate_id} retorna 200."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from app.api.v1.granular_consent import router
        from app.shared.services.granular_consent_service import (
            GranularConsentSummary, GranularConsentStatus, GRANULAR_PURPOSE_MAP
        )

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        statuses = [
            GranularConsentStatus(
                purpose=p, consent_type=ct, given=False, revoked=False
            )
            for p, ct in GRANULAR_PURPOSE_MAP.items()
        ]
        mock_summary = GranularConsentSummary(
            candidate_id="cand-1",
            company_id="comp-1",
            consents=statuses,
            all_blocking_given=False,
        )

        import uuid

        async def mock_get_db():
            yield MagicMock()

        from app.core.database import get_db
        app.dependency_overrides[get_db] = mock_get_db

        with patch(
            "app.services.granular_consent_service.GranularConsentService.get_summary",
            new_callable=AsyncMock,
            return_value=mock_summary,
        ):
            client = TestClient(app)
            response = client.get(
                f"/api/v1/consent/granular/cand-1",
                headers={"X-Company-ID": str(uuid.uuid4())},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["candidate_id"] == "cand-1"
        assert len(data["consents"]) == len(GRANULAR_PURPOSE_MAP)

    def test_post_update_no_valid_purpose_returns_422(self):
        """POST /update com finalidades inválidas retorna 422."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from app.api.v1.granular_consent import router
        import uuid

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        async def mock_get_db():
            yield MagicMock()

        from app.core.database import get_db
        app.dependency_overrides[get_db] = mock_get_db

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/consent/granular/cand-1/update",
            json={"updates": {"invalid_purpose": True}},
            headers={"X-Company-ID": str(uuid.uuid4())},
        )
        assert response.status_code == 422
