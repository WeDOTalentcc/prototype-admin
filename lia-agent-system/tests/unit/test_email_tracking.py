"""
COMP-7: Email Tracking Service tests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestEmailTrackingService:
    """Tests para EmailTrackingService."""

    def test_generate_token_returns_string(self):
        """generate_tracking_token deve retornar string."""
        from app.domains.communication.services.email_tracking_service import EmailTrackingService
        svc = EmailTrackingService()
        token = svc.generate_tracking_token("notif-001", "co-001")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_generate_token_unique(self):
        """Tokens devem ser únicos."""
        from app.domains.communication.services.email_tracking_service import EmailTrackingService
        svc = EmailTrackingService()
        tokens = {svc.generate_tracking_token("notif-001", "co-001") for _ in range(50)}
        assert len(tokens) == 50  # todos únicos

    def test_sha256_ip_hash(self):
        """IP deve ser armazenado como SHA256."""
        from app.domains.communication.services.email_tracking_service import _hash_ip, _sha256
        ip = "192.168.1.100"
        hashed = _hash_ip(ip)
        assert hashed == _sha256(ip)
        assert len(hashed) == 64
        assert ip not in hashed  # IP não está em plaintext

    def test_sha256_email_hash(self):
        """Email deve ser armazenado como SHA256."""
        from app.domains.communication.services.email_tracking_service import _hash_email
        email = "joao@example.com"
        hashed = _hash_email(email)
        assert len(hashed) == 64
        assert "joao" not in hashed

    def test_hash_ip_none_returns_none(self):
        """_hash_ip(None) deve retornar None."""
        from app.domains.communication.services.email_tracking_service import _hash_ip
        assert _hash_ip(None) is None

    def test_hash_email_none_returns_none(self):
        """_hash_email(None) deve retornar None."""
        from app.domains.communication.services.email_tracking_service import _hash_email
        assert _hash_email(None) is None

    @pytest.mark.asyncio
    async def test_record_open_invalid_token_returns_false(self):
        """Token inválido deve retornar False sem crash."""
        from app.domains.communication.services.email_tracking_service import EmailTrackingService
        svc = EmailTrackingService()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await svc.record_open(mock_db, "invalid-token-xyz")
        assert result is False

    @pytest.mark.asyncio
    async def test_record_click_invalid_token_returns_none(self):
        """Token inválido deve retornar None."""
        from app.domains.communication.services.email_tracking_service import EmailTrackingService
        svc = EmailTrackingService()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await svc.record_click(mock_db, "invalid-token", "https://example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_stats_returns_dict(self):
        """get_stats deve retornar dict com opens, clicks, unique_opens."""
        from app.domains.communication.services.email_tracking_service import EmailTrackingService
        svc = EmailTrackingService()

        mock_db = AsyncMock()

        # Mock execução de queries
        class MockRow:
            def __init__(self, event_type, count):
                self.event_type = event_type
                self.count = count

        mock_result1 = MagicMock()
        mock_result1.__iter__ = MagicMock(return_value=iter([
            MockRow("open", 10),
            MockRow("click", 3),
        ]))

        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = 7

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        stats = await svc.get_stats(mock_db, "notif-001", "co-001")
        assert "opens" in stats
        assert "clicks" in stats
        assert "unique_opens" in stats
        assert stats["notification_id"] == "notif-001"


class TestEmailTrackingEndpoints:
    """Tests para endpoints de tracking."""

    def test_transparent_gif_bytes(self):
        """GIF transparente deve ter bytes corretos."""
        from app.api.v1.email_tracking import _TRANSPARENT_GIF
        assert isinstance(_TRANSPARENT_GIF, bytes)
        assert len(_TRANSPARENT_GIF) > 0
        # GIF89a header
        assert _TRANSPARENT_GIF[:6] == b"GIF89a"

    def test_router_has_pixel_route(self):
        """Router deve ter rota de pixel."""
        from app.api.v1.email_tracking import router
        paths = [r.path for r in router.routes]
        assert any("pixel" in p for p in paths)

    def test_router_has_click_route(self):
        """Router deve ter rota de click."""
        from app.api.v1.email_tracking import router
        paths = [r.path for r in router.routes]
        assert any("click" in p for p in paths)

    def test_router_has_stats_route(self):
        """Router deve ter rota de stats."""
        from app.api.v1.email_tracking import router
        paths = [r.path for r in router.routes]
        assert any("stats" in p for p in paths)

    def test_email_tracking_service_singleton(self):
        """Deve existir singleton email_tracking_service."""
        from app.domains.communication.services.email_tracking_service import email_tracking_service
        assert email_tracking_service is not None
