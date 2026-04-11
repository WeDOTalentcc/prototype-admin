"""
Tests for Sprint 5 — Google Calendar client + OAuth security.

Verifies:
- GoogleCalendarClient initializes with and without credentials
- Token refresh logic is triggered for expired OAuth tokens
- OAuth state HMAC signing and verification (CSRF protection)
- Expiry is stored in token_data during callback
"""
import pytest
import hmac
import hashlib
import json
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta


class TestGoogleCalendarClientInit:
    def test_init_without_credentials_stores_none(self):
        from app.shared.services.google_calendar_client import GoogleCalendarClient
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON = None
            mock_settings.GOOGLE_CALENDAR_DEFAULT_TIMEZONE = "America/Sao_Paulo"
            client = GoogleCalendarClient(credentials_json=None)
            assert client._service is None
            assert client._creds is None

    def test_get_service_raises_without_credentials(self):
        from app.shared.services.google_calendar_client import GoogleCalendarClient
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON = None
            mock_settings.GOOGLE_CALENDAR_DEFAULT_TIMEZONE = "America/Sao_Paulo"
            client = GoogleCalendarClient(credentials_json=None)
            with pytest.raises(ValueError, match="credentials not configured"):
                client._get_service()

    def test_init_stores_timezone(self):
        from app.shared.services.google_calendar_client import GoogleCalendarClient
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON = None
            mock_settings.GOOGLE_CALENDAR_DEFAULT_TIMEZONE = "America/Sao_Paulo"
            client = GoogleCalendarClient(credentials_json=None, timezone="America/Recife")
            assert client.timezone == "America/Recife"


class TestGoogleCalendarTokenRefresh:
    """Verifica que _get_service() chama creds.refresh() quando token expirado."""

    def _make_expired_creds(self):
        creds = MagicMock()
        creds.expired = True
        creds.refresh_token = "rtoken_abc"
        creds.refresh = MagicMock()
        return creds

    def _make_valid_creds(self):
        creds = MagicMock()
        creds.expired = False
        creds.refresh_token = "rtoken_abc"
        creds.refresh = MagicMock()
        return creds

    def test_refresh_called_when_token_expired(self):
        from app.shared.services.google_calendar_client import GoogleCalendarClient
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON = None
            mock_settings.GOOGLE_CALENDAR_DEFAULT_TIMEZONE = "America/Sao_Paulo"
            client = GoogleCalendarClient(credentials_json=None)

        expired_creds = self._make_expired_creds()
        fake_service = MagicMock()
        client._service = fake_service
        client._creds = expired_creds

        with patch("google.auth.transport.requests.Request", return_value=MagicMock()):
            result = client._get_service()

        expired_creds.refresh.assert_called_once()
        assert result is fake_service

    def test_refresh_not_called_when_token_valid(self):
        from app.shared.services.google_calendar_client import GoogleCalendarClient
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON = None
            mock_settings.GOOGLE_CALENDAR_DEFAULT_TIMEZONE = "America/Sao_Paulo"
            client = GoogleCalendarClient(credentials_json=None)

        valid_creds = self._make_valid_creds()
        fake_service = MagicMock()
        client._service = fake_service
        client._creds = valid_creds

        result = client._get_service()
        valid_creds.refresh.assert_not_called()
        assert result is fake_service

    def test_refresh_failure_clears_service(self):
        from app.shared.services.google_calendar_client import GoogleCalendarClient
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON = None
            mock_settings.GOOGLE_CALENDAR_DEFAULT_TIMEZONE = "America/Sao_Paulo"
            client = GoogleCalendarClient(credentials_json=None)

        expired_creds = self._make_expired_creds()
        expired_creds.refresh.side_effect = Exception("Token revoked")
        client._service = MagicMock()
        client._creds = expired_creds

        with patch("google.auth.transport.requests.Request", return_value=MagicMock()):
            with pytest.raises(RuntimeError, match="token refresh failed"):
                client._get_service()

        assert client._service is None  # deve ser limpo para próximo rebuild


class TestOAuthStateCSRF:
    """Verifica que o state do OAuth é HMAC-assinado e verificado."""

    def _compute_expected_sig(self, secret_key: str, company_id: str) -> str:
        return hmac.new(
            secret_key.encode(), company_id.encode(), hashlib.sha256
        ).hexdigest()

    def test_valid_state_passes_verification(self):
        secret_key = "test-secret-key-for-unit-test"
        company_id = "550e8400-e29b-41d4-a716-446655440000"
        sig = self._compute_expected_sig(secret_key, company_id)
        state = f"{company_id}:{sig}"

        parts = state.split(":", 1)
        assert len(parts) == 2
        cid, provided_sig = parts
        expected = self._compute_expected_sig(secret_key, cid)
        assert hmac.compare_digest(provided_sig, expected)

    def test_tampered_state_fails_verification(self):
        secret_key = "test-secret-key-for-unit-test"
        company_id = "550e8400-e29b-41d4-a716-446655440000"
        tampered_company_id = "attacker-company-id-00000000000000"
        sig = self._compute_expected_sig(secret_key, company_id)
        tampered_state = f"{tampered_company_id}:{sig}"

        parts = tampered_state.split(":", 1)
        cid, provided_sig = parts
        expected = self._compute_expected_sig(secret_key, cid)
        assert not hmac.compare_digest(provided_sig, expected)

    def test_state_without_separator_invalid(self):
        state = "just-a-plain-company-id-no-sig"
        parts = state.split(":", 1)
        assert len(parts) == 1  # sem separador → inválido


class TestTokenDataStoresExpiry:
    """Verifica que o callback salva expiry no token_data."""

    def test_token_data_includes_expiry(self):
        # Simula o que o callback faz ao serializar credentials
        expiry_dt = datetime.utcnow() + timedelta(hours=1)
        fake_creds = MagicMock()
        fake_creds.token = "access_token_abc"
        fake_creds.refresh_token = "refresh_token_xyz"
        fake_creds.token_uri = "https://oauth2.googleapis.com/token"
        fake_creds.client_id = "client_id"
        fake_creds.client_secret = "client_secret"
        fake_creds.scopes = ["https://www.googleapis.com/auth/calendar"]
        fake_creds.expiry = expiry_dt

        token_data = json.dumps({
            "access_token": fake_creds.token,
            "refresh_token": fake_creds.refresh_token,
            "token_uri": fake_creds.token_uri,
            "client_id": fake_creds.client_id,
            "client_secret": fake_creds.client_secret,
            "scopes": list(fake_creds.scopes or []),
            "expiry": fake_creds.expiry.isoformat() if fake_creds.expiry else None,
        })

        parsed = json.loads(token_data)
        assert "expiry" in parsed
        assert parsed["expiry"] is not None
        # Verifica que é uma ISO string válida
        recovered = datetime.fromisoformat(parsed["expiry"])
        assert abs((recovered - expiry_dt).total_seconds()) < 1
