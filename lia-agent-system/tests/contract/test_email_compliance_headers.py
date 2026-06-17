"""
GAP-07-002: Contract tests — DMARC + List-Unsubscribe headers
Every outgoing email MUST include CAN-SPAM / RFC 8058 compliance headers.
"""
import os
import unittest
from unittest.mock import patch

_MAILGUN_ENV = {
    "MAILGUN_API_KEY": "test-key",
    "MAILGUN_DOMAIN": "mg.wedotalent.cc",
    "MAILGUN_FROM_EMAIL": "noreply@wedotalent.com",
}


class TestDispatcherComplianceHeaders(unittest.TestCase):
    """CommunicationDispatcher.send_email injects compliance headers in every Mailgun call."""

    def _capture_mailgun_data(self, to="test@example.com", extra_env=None):
        """Call dispatcher.send_email and capture what was POSTed to Mailgun."""
        captured = {}
        env = {**_MAILGUN_ENV, **(extra_env or {})}

        class FakeResponse:
            status_code = 200
            def json(self): return {"id": "mg-test-123"}

        class FakeClient:
            def __init__(self, **_): pass
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def post(self, url, auth, data):
                captured.update(data)
                return FakeResponse()

        with patch.dict(os.environ, env):
            from app.domains.communication.services.communication_dispatcher import (
                CommunicationDispatcher,
            )
            d = CommunicationDispatcher()
            with patch("httpx.Client", FakeClient):
                d.send_email(
                    to_email=to,
                    subject="Test Subject",
                    body_html="<p>Hello</p>",
                )
        return captured

    def test_list_unsubscribe_header_present(self):
        data = self._capture_mailgun_data()
        self.assertIn("h:List-Unsubscribe", data, "List-Unsubscribe header must be injected")

    def test_list_unsubscribe_contains_mailto_fallback(self):
        data = self._capture_mailgun_data()
        self.assertIn("mailto:unsubscribe@wedotalent.cc", data["h:List-Unsubscribe"])

    def test_list_unsubscribe_post_rfc8058(self):
        data = self._capture_mailgun_data()
        self.assertEqual(
            data.get("h:List-Unsubscribe-Post"),
            "List-Unsubscribe=One-Click",
            "RFC 8058 one-click unsubscribe header required",
        )

    def test_dmarc_policy_header(self):
        data = self._capture_mailgun_data()
        dmarc = data.get("h:DMARC-Policy", "")
        self.assertIn("v=DMARC1", dmarc)
        self.assertIn("p=quarantine", dmarc)

    def test_x_mailer_header(self):
        data = self._capture_mailgun_data()
        self.assertIn("WeDOTalent", data.get("h:X-Mailer", ""))

    def test_app_base_url_env_used_in_unsubscribe(self):
        data = self._capture_mailgun_data(extra_env={"APP_BASE_URL": "https://custom.example.com"})
        self.assertIn("custom.example.com", data["h:List-Unsubscribe"])


class TestMailgunProviderComplianceHeaders(unittest.IsolatedAsyncioTestCase):
    """MailgunProvider.send_email injects compliance defaults; caller headers override."""

    async def _send_and_capture(self, extra_headers=None):
        captured = {}

        class FakeResp:
            status_code = 200
            def json(self): return {"id": "mg-async-test"}

        class FakeAsyncClient:
            def __init__(self, **_): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *a): pass
            async def post(self, url, auth, data):
                captured.update(data)
                return FakeResp()

        with patch.dict(os.environ, _MAILGUN_ENV):
            from app.domains.communication.services.email_providers.mailgun_provider import (
                MailgunProvider,
            )
            p = MailgunProvider()
            with patch("httpx.AsyncClient", FakeAsyncClient):
                await p.send_email(
                    to="test@example.com",
                    subject="Test",
                    html_content="<p>Hi</p>",
                    headers=extra_headers,
                )
        return captured

    async def test_default_compliance_headers_injected(self):
        data = await self._send_and_capture()
        self.assertIn("h:List-Unsubscribe", data)
        self.assertIn("h:List-Unsubscribe-Post", data)
        self.assertIn("h:DMARC-Policy", data)
        self.assertIn("h:X-Mailer", data)

    async def test_caller_headers_override_defaults(self):
        custom = {"X-Mailer": "CustomMailer/1.0", "X-Custom": "yes"}
        data = await self._send_and_capture(extra_headers=custom)
        self.assertEqual(data["h:X-Mailer"], "CustomMailer/1.0", "Caller header must override default")
        self.assertEqual(data["h:X-Custom"], "yes")

    async def test_list_unsubscribe_post_present(self):
        data = await self._send_and_capture()
        self.assertEqual(data["h:List-Unsubscribe-Post"], "List-Unsubscribe=One-Click")

    async def test_no_headers_arg_still_gets_compliance(self):
        """Passing headers=None still injects compliance headers."""
        data = await self._send_and_capture(extra_headers=None)
        self.assertIn("h:List-Unsubscribe", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
