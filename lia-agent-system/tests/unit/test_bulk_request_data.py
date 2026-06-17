"""
RED tests — G-RequestData: endpoint bulk request-data deve existir e chamar DataRequest service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestBulkRequestDataEndpoint:
    """G-RequestData: endpoint POST /candidates/bulk/request-data deve existir."""

    def test_bulk_request_data_schema_exists(self):
        """BulkRequestDataRequest schema deve existir em bulk_actions."""
        from app.api.v1.bulk_actions import BulkRequestDataRequest
        req = BulkRequestDataRequest(
            candidate_ids=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
            vacancy_id="vac-uuid-123",
        )
        assert req.candidate_ids == ["3fa85f64-5717-4562-b3fc-2c963f66afa6"]
        assert req.vacancy_id == "vac-uuid-123"

    def test_bulk_request_data_vacancy_optional(self):
        """vacancy_id deve ser opcional em BulkRequestDataRequest."""
        from app.api.v1.bulk_actions import BulkRequestDataRequest
        req = BulkRequestDataRequest(
            candidate_ids=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
        )
        assert req.vacancy_id is None

    def test_bulk_request_data_handler_exists(self):
        """Função bulk_request_data deve existir e ser chamável."""
        from app.api.v1.bulk_actions import bulk_request_data
        assert callable(bulk_request_data)

    @pytest.mark.asyncio
    async def test_bulk_request_data_calls_service(self):
        """
        bulk_request_data deve chamar data_request_service.create_data_request
        para cada candidate_id.
        """
        from app.api.v1.bulk_actions import bulk_request_data, BulkRequestDataRequest

        candidate_ids = [
            "3fa85f64-5717-4562-b3fc-2c963f66afa1",
            "3fa85f64-5717-4562-b3fc-2c963f66afa2",
        ]
        req = BulkRequestDataRequest(candidate_ids=candidate_ids)

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user-uuid-000"

        mock_data_request = MagicMock()
        mock_data_request.id = "dr-uuid-111"

        with patch("app.domains.communication.services.data_request_service.data_request_service") as mock_svc:
            mock_svc.create_data_request = AsyncMock(return_value=mock_data_request)
            mock_svc.send_notification = AsyncMock()

            result = await bulk_request_data(
                request=req,
                current_user=mock_user,
                company_id="company-uuid-123",
            )

        assert result.total == 2
        assert mock_svc.create_data_request.call_count == 2

    @pytest.mark.asyncio
    async def test_bulk_request_data_partial_failure(self):
        """
        Falha em um candidato não deve abortar os outros.
        """
        from app.api.v1.bulk_actions import bulk_request_data, BulkRequestDataRequest
        from uuid import UUID

        candidate_ids = [
            "3fa85f64-5717-4562-b3fc-2c963f66afa1",
            "3fa85f64-5717-4562-b3fc-2c963f66afa2",
        ]
        req = BulkRequestDataRequest(candidate_ids=candidate_ids)

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user-uuid-000"

        mock_data_request = MagicMock()
        mock_data_request.id = "dr-uuid-111"

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Candidate not found")
            return mock_data_request

        with patch("app.domains.communication.services.data_request_service.data_request_service") as mock_svc:
            mock_svc.create_data_request = AsyncMock(side_effect=side_effect)
            mock_svc.send_notification = AsyncMock()

            result = await bulk_request_data(
                request=req,
                current_user=mock_user,
                company_id="company-uuid-123",
            )

        assert result.total == 2
        assert result.successful == 1
        assert result.failed == 1
        assert len(result.errors) == 1
