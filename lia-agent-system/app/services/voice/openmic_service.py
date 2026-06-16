"""
OpenMic.ai Automated Voice Screening Service.

Manages automated voice interview calls via OpenMic.ai API.
Integrates with circuit breaker pattern for production resilience.

Flow:
  1. Recruiter triggers a voice screening via LIA dashboard.
  2. openmic_service.initiate_call() dispatches outbound call to candidate.
  3. OpenMic conducts the scripted interview (questions defined per vaga).
  4. On call completion, OpenMic POSTs to /api/v1/openmic/webhook.
  5. Webhook handler extracts transcript → Deepgram re-processes (if needed)
     → enqueues Celery task for WSI pipeline → notifies recruiter.
"""
import hashlib
import hmac
import logging
import os
from typing import Any

import httpx

from app.shared.resilience.circuit_breaker import OPENMIC_CIRCUIT, CircuitBreakerError

logger = logging.getLogger(__name__)


class OpenMicError(Exception):
    """Raised when OpenMic API call fails."""


class OpenMicUnconfiguredError(OpenMicError):
    """Raised when OPENMIC_API_KEY is not set."""


class OpenMicSignatureError(OpenMicError):
    """Raised when webhook HMAC signature validation fails."""


class OpenMicService:
    """
    OpenMic.ai service with circuit breaker protection.

    Handles:
    - Initiating automated voice screening calls.
    - Validating incoming webhook signatures.
    - Parsing call completion events.
    """

    OPENMIC_BASE_URL = "https://api.openmic.ai/v1"

    def __init__(self) -> None:
        self._api_key: str | None = None
        self._webhook_secret: str | None = None

    def _get_api_key(self) -> str:
        if self._api_key:
            return self._api_key
        key = os.getenv("OPENMIC_API_KEY")
        if not key:
            raise OpenMicUnconfiguredError(
                "OPENMIC_API_KEY env var is not set. "
                "Configure it to enable OpenMic.ai voice screening."
            )
        self._api_key = key
        return key

    def _get_webhook_secret(self) -> str:
        if self._webhook_secret:
            return self._webhook_secret
        secret = os.getenv("OPENMIC_WEBHOOK_SECRET", "")
        self._webhook_secret = secret
        return secret

    def is_configured(self) -> bool:
        """Return True if OPENMIC_API_KEY is present."""
        return bool(os.getenv("OPENMIC_API_KEY"))

    def validate_webhook_signature(
        self,
        payload: bytes,
        signature_header: str,
    ) -> bool:
        """
        Validate HMAC-SHA256 signature from OpenMic webhook.

        OpenMic sends: X-OpenMic-Signature: sha256=<hex_digest>

        Args:
            payload: Raw request body bytes.
            signature_header: Value of X-OpenMic-Signature header.

        Returns:
            True if signature is valid.

        Raises:
            OpenMicSignatureError: If signature does not match or secret is unset.

        Note:
            Callers that need dev-mode bypass should check OPENMIC_WEBHOOK_SECRET
            and OPENMIC_ALLOW_UNSIGNED_WEBHOOK BEFORE calling this method.
            This method always requires a secret to be set (fail-closed).
        """
        secret = self._get_webhook_secret()
        if not secret:
            raise OpenMicSignatureError(
                "OPENMIC_WEBHOOK_SECRET is not configured. "
                "Signature validation cannot proceed."
            )

        if not signature_header or not signature_header.startswith("sha256="):
            raise OpenMicSignatureError("Missing or malformed X-OpenMic-Signature header.")

        expected = hmac.new(
            secret.encode(),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()

        provided = signature_header.removeprefix("sha256=")

        if not hmac.compare_digest(expected, provided):
            raise OpenMicSignatureError("Webhook signature mismatch — request rejected.")

        return True

    async def initiate_call(
        self,
        candidate_phone: str,
        candidate_name: str,
        candidate_id: str,
        job_id: str,
        company_id: str,
        language: str = "pt-BR",
        script_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Trigger an automated outbound voice screening call via OpenMic.

        Args:
            candidate_phone: E.164 phone number (e.g., +5511999999999).
            candidate_name: Candidate's full name (for greeting).
            candidate_id: Internal candidate ID.
            job_id: Internal vacancy ID.
            company_id: Tenant company ID.
            language: BCP-47 language code.
            script_id: OpenMic script/template ID (optional — uses default if omitted).
            metadata: Additional metadata passed through and returned in webhook.

        Returns:
            Dict with call_id, status, estimated_duration_minutes.

        Raises:
            OpenMicUnconfiguredError: API key not configured.
            OpenMicError: API call failed.
            CircuitBreakerError: Circuit is open.
        """
        async def _call() -> dict[str, Any]:
            api_key = self._get_api_key()

            payload: dict[str, Any] = {
                "phone": candidate_phone,
                "candidate_name": candidate_name,
                "language": language,
                "metadata": {
                    "candidate_id": candidate_id,
                    "job_id": job_id,
                    "company_id": company_id,
                    **(metadata or {}),
                },
            }
            if script_id:
                payload["script_id"] = script_id

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.OPENMIC_BASE_URL}/calls",
                    json=payload,
                    headers=headers,
                )

            if response.status_code not in (200, 201, 202):
                raise OpenMicError(
                    f"OpenMic API returned {response.status_code}: {response.text[:200]}"
                )

            data = response.json()
            call_id = data.get("call_id") or data.get("id", "unknown")

            logger.info(
                "[OpenMic] Call initiated — call_id=%s candidate_id=%s job_id=%s",
                call_id,
                candidate_id,
                job_id,
            )

            return {
                "call_id": call_id,
                "status": data.get("status", "initiated"),
                "estimated_duration_minutes": data.get("estimated_duration_minutes", 10),
                "provider": "openmic",
            }

        return await OPENMIC_CIRCUIT.call(_call)

    async def get_call_status(self, call_id: str) -> dict[str, Any]:
        """
        Retrieve the status of an ongoing or completed call.

        Args:
            call_id: OpenMic call identifier.

        Returns:
            Dict with call status details.
        """
        async def _call() -> dict[str, Any]:
            api_key = self._get_api_key()

            headers = {"Authorization": f"Bearer {api_key}"}

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.OPENMIC_BASE_URL}/calls/{call_id}",
                    headers=headers,
                )

            if response.status_code == 404:
                raise OpenMicError(f"Call '{call_id}' not found.")

            if response.status_code != 200:
                raise OpenMicError(
                    f"OpenMic API returned {response.status_code}: {response.text[:200]}"
                )

            return response.json()

        return await OPENMIC_CIRCUIT.call(_call)

    async def health_check(self) -> dict[str, Any]:
        """
        Validate OpenMic configuration (key presence only — no API call).

        Returns:
            Dict with status, configured, circuit_state.
        """
        configured = self.is_configured()
        circuit_state = OPENMIC_CIRCUIT.state.value
        webhook_secret_set = bool(os.getenv("OPENMIC_WEBHOOK_SECRET"))

        return {
            "service": "openmic",
            "provider": "OpenMic.ai",
            "configured": configured,
            "webhook_secret_configured": webhook_secret_set,
            "circuit_state": circuit_state,
            "status": "healthy" if (configured and circuit_state != "open") else "degraded",
            "languages_supported": ["pt-BR", "en-US"],
            "webhook_endpoint": "/api/v1/openmic/webhook",
        }


openmic_service = OpenMicService()
