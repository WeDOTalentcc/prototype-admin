"""
Integration Tests — Webhook Merge.dev/ATS (Task #53, Item 10).

Testa o comportamento REAL do merge_webhooks module:
- verify_merge_signature: HMAC SHA256 correto aceito
- verify_merge_signature: assinatura incorreta rejeitada
- verify_merge_signature: sem secret configurado retorna False
- process_merge_event: loops sobre records e chama handlers corretos
- handle_candidate_created: chama activity_service.log
- handle_merge_webhook (FastAPI endpoint): invalid signature → 401
- handle_merge_webhook: valid flow → dispatches background task
"""
import hashlib
import hmac
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_payload(event_type: str = "Candidate.created") -> dict:
    return {
        "hook": {"event": event_type},
        "linked_account": {
            "end_user_origin_id": "company-001",
            "id": "token-abc",
            "integration": "Greenhouse",
        },
        "data": [
            {
                "id": "merge-cand-001",
                "first_name": "João",
                "last_name": "Silva",
                "email_addresses": [{"value": "joao@test.com"}],
            }
        ],
    }


def _sign_payload(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Seção 1 — Signature verification (real HMAC behavior)
# ---------------------------------------------------------------------------

class TestMergeSignatureVerification:

    def test_valid_signature_accepted(self):
        """HMAC correto deve ser aceito pelo verify_merge_signature."""
        from app.api.v1.merge_webhooks import verify_merge_signature
        payload = b'{"hook": {"event": "Candidate.created"}}'
        secret = "my-webhook-secret-abc"
        signature = _sign_payload(payload, secret)

        with patch.dict("os.environ", {"MERGE_WEBHOOK_SECRET": secret}):
            assert verify_merge_signature(payload, signature) is True

    def test_invalid_signature_rejected(self):
        """Assinatura incorreta deve ser rejeitada."""
        from app.api.v1.merge_webhooks import verify_merge_signature
        payload = b'{"hook": {"event": "Candidate.created"}}'
        secret = "my-webhook-secret-abc"
        wrong_signature = "cafebabe" * 8

        with patch.dict("os.environ", {"MERGE_WEBHOOK_SECRET": secret}):
            assert verify_merge_signature(payload, wrong_signature) is False

    def test_no_secret_configured_returns_false(self):
        """Sem MERGE_WEBHOOK_SECRET configurado, verify deve retornar False."""
        from app.api.v1.merge_webhooks import verify_merge_signature
        with patch.dict("os.environ", {}, clear=True):
            import os
            os.environ.pop("MERGE_WEBHOOK_SECRET", None)
            result = verify_merge_signature(b"payload", "any-signature")
        assert result is False

    def test_tampered_payload_fails_verification(self):
        """Payload alterado após assinar deve falhar a verificação."""
        from app.api.v1.merge_webhooks import verify_merge_signature
        original = b'{"hook": {"event": "Candidate.created"}}'
        secret = "tamper-test-secret"
        sig = _sign_payload(original, secret)

        tampered = b'{"hook": {"event": "Candidate.DELETED"}}'
        with patch.dict("os.environ", {"MERGE_WEBHOOK_SECRET": secret}):
            assert verify_merge_signature(tampered, sig) is False

    def test_empty_payload_wrong_signature_rejected(self):
        """Payload vazio com assinatura errada deve retornar False."""
        from app.api.v1.merge_webhooks import verify_merge_signature
        with patch.dict("os.environ", {"MERGE_WEBHOOK_SECRET": "secret123"}):
            assert verify_merge_signature(b"", "wrongsig") is False


# ---------------------------------------------------------------------------
# Seção 2 — process_merge_event: routing to correct handlers
# ---------------------------------------------------------------------------

class TestProcessMergeEventRouting:

    @pytest.mark.asyncio
    async def test_candidate_created_calls_handle_candidate_created(self):
        """Evento Candidate.created deve chamar handle_candidate_created."""
        from app.api.v1 import merge_webhooks
        data = _make_payload("Candidate.created")

        with patch.object(merge_webhooks, "handle_candidate_created",
                          new_callable=AsyncMock) as mock_handler:
            await merge_webhooks.process_merge_event(data)

        mock_handler.assert_awaited_once()
        call_args = mock_handler.call_args
        assert call_args[0][0]["id"] == "merge-cand-001"

    @pytest.mark.asyncio
    async def test_candidate_updated_calls_handle_candidate_updated(self):
        """Evento Candidate.updated deve chamar handle_candidate_updated."""
        from app.api.v1 import merge_webhooks
        data = _make_payload("Candidate.updated")

        with patch.object(merge_webhooks, "handle_candidate_updated",
                          new_callable=AsyncMock) as mock_handler:
            await merge_webhooks.process_merge_event(data)

        mock_handler.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unknown_event_type_does_not_raise(self):
        """Tipo de evento desconhecido não deve lançar exceção."""
        from app.api.v1 import merge_webhooks
        data = _make_payload("UNKNOWN.event_type_xyz")

        await merge_webhooks.process_merge_event(data)

    @pytest.mark.asyncio
    async def test_multiple_records_all_processed(self):
        """Todos os records no payload devem ser processados em loop."""
        from app.api.v1 import merge_webhooks

        data = {
            "hook": {"event": "Candidate.created"},
            "linked_account": {
                "end_user_origin_id": "company-001",
                "id": "token-abc",
                "integration": "Greenhouse",
            },
            "data": [
                {"id": f"cand-{i}", "first_name": f"Candidato {i}"}
                for i in range(3)
            ],
        }

        handler_calls = []

        async def _mock_handler(record, company_id, account_token):
            handler_calls.append(record["id"])

        with patch.object(merge_webhooks, "handle_candidate_created",
                          side_effect=_mock_handler):
            await merge_webhooks.process_merge_event(data)

        assert len(handler_calls) == 3
        assert "cand-0" in handler_calls
        assert "cand-2" in handler_calls


# ---------------------------------------------------------------------------
# Seção 3 — handle_candidate_created: logs activity
# ---------------------------------------------------------------------------

class TestHandleCandidateCreated:

    @pytest.mark.asyncio
    async def test_handle_candidate_created_calls_log_activity_with_correct_params(self):
        """handle_candidate_created deve chamar activity_service.log_activity
        com action='candidate_created_external' e entity_type='candidate'."""
        from app.api.v1 import merge_webhooks

        record = {
            "id": "merge-cand-log-test",
            "first_name": "Maria",
            "last_name": "Oliveira",
            "email_addresses": [{"value": "maria@test.com"}],
        }

        mock_activity_svc = MagicMock()
        mock_activity_svc.log_activity = AsyncMock()

        with patch(
            "app.services.activity_service.activity_service",
            mock_activity_svc,
        ):
            await merge_webhooks.handle_candidate_created(
                record=record,
                company_id="company-001",
                account_token="token-abc",
            )

        mock_activity_svc.log_activity.assert_awaited_once()
        call_kwargs = mock_activity_svc.log_activity.call_args[1]
        assert call_kwargs["action"] == "candidate_created_external"
        assert call_kwargs["entity_type"] == "candidate"
        assert call_kwargs["entity_id"] == "merge-cand-log-test"
        assert call_kwargs["details"]["company_id"] == "company-001"
        assert call_kwargs["details"]["first_name"] == "Maria"

    @pytest.mark.asyncio
    async def test_handle_candidate_created_is_async(self):
        """handle_candidate_created deve ser uma coroutine."""
        from app.api.v1.merge_webhooks import handle_candidate_created
        import asyncio
        assert asyncio.iscoroutinefunction(handle_candidate_created)


# ---------------------------------------------------------------------------
# Seção 4 — FastAPI endpoint: signature enforcement
# ---------------------------------------------------------------------------

class TestMergeWebhookEndpoint:

    def _make_test_app(self):
        from app.api.v1.merge_webhooks import router
        app = FastAPI()
        app.include_router(router)
        return app

    def test_endpoint_with_invalid_signature_returns_401(self):
        """Endpoint com assinatura inválida deve retornar 401."""
        app = self._make_test_app()
        client = TestClient(app, raise_server_exceptions=False)

        payload = json.dumps(_make_payload()).encode()

        with patch.dict("os.environ", {"MERGE_WEBHOOK_SECRET": "real-secret"}):
            resp = client.post(
                "/webhooks/merge/",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Merge-Signature": "wrong-signature",
                },
            )

        assert resp.status_code == 401

    def test_endpoint_without_signature_accepts_request(self):
        """Sem header de assinatura, endpoint deve aceitar (signature é opcional)."""
        app = self._make_test_app()
        client = TestClient(app, raise_server_exceptions=False)

        payload = _make_payload()

        with patch("app.api.v1.merge_webhooks.process_merge_event",
                   new_callable=AsyncMock):
            resp = client.post(
                "/webhooks/merge/",
                json=payload,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "received"
