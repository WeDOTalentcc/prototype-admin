"""
LIA Error Hierarchy — unified error types for the entire platform.

All errors inherit from LIAError which provides:
- code: machine-readable error code (ex: "TENANT_NOT_FOUND")
- message: human-readable description (PT-BR)
- details: structured metadata for debugging
- recoverable: whether the caller can retry/fallback

Usage:
    from app.shared.errors import LIAToolError, LIAComplianceError

    raise LIAToolError(
        message="Ferramenta de busca indisponível",
        code="TOOL_SEARCH_UNAVAILABLE",
        details={"tool": "pearch_search", "timeout": 30},
    )

    raise LIAComplianceError(
        message="Candidato revogou consentimento LGPD",
        code="CONSENT_REVOKED",
        details={"candidate_id": "123", "consent_type": "EMAIL_MARKETING"},
    )

Existing domain-specific exceptions (VoiceServiceError, GraphAPIError, etc.)
remain in their modules. This hierarchy is for CROSS-CUTTING errors that
any layer may raise. Domain exceptions can subclass from here over time.
"""
from __future__ import annotations

from typing import Any


class LIAError(Exception):
    """Base error for the entire LIA platform."""

    def __init__(
        self,
        message: str = "Erro interno da plataforma",
        code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
        recoverable: bool = True,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.recoverable = recoverable
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API error responses."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} code={self.code!r} message={self.message!r}>"


# ---------------------------------------------------------------------------
# Agent errors — during ReAct loop execution
# ---------------------------------------------------------------------------

class LIAAgentError(LIAError):
    """Error during agent execution (ReAct loop, graph, etc.)."""

    def __init__(self, message="Erro na execução do agente", code="AGENT_ERROR", **kwargs):
        super().__init__(message=message, code=code, **kwargs)


class LIAToolError(LIAAgentError):
    """Tool failed — agent can try alternative tool or fallback."""

    def __init__(self, message="Ferramenta indisponível", code="TOOL_ERROR", **kwargs):
        kwargs.setdefault("recoverable", True)
        super().__init__(message=message, code=code, **kwargs)


class LIALLMError(LIAAgentError):
    """LLM call failed (timeout, rate limit, invalid response)."""

    def __init__(self, message="Erro na chamada ao modelo de IA", code="LLM_ERROR", **kwargs):
        kwargs.setdefault("recoverable", True)
        super().__init__(message=message, code=code, **kwargs)


# ---------------------------------------------------------------------------
# Validation errors — invalid input
# ---------------------------------------------------------------------------

class LIAValidationError(LIAError):
    """Invalid input data."""

    def __init__(self, message="Dados de entrada inválidos", code="VALIDATION_ERROR", **kwargs):
        kwargs.setdefault("recoverable", True)
        super().__init__(message=message, code=code, **kwargs)


# ---------------------------------------------------------------------------
# Tenant errors — multi-tenancy issues
# ---------------------------------------------------------------------------

class LIATenantError(LIAError):
    """Tenant not found or isolation violated."""

    def __init__(self, message="Tenant não encontrado", code="TENANT_ERROR", **kwargs):
        kwargs.setdefault("recoverable", False)
        super().__init__(message=message, code=code, **kwargs)


# ---------------------------------------------------------------------------
# Compliance errors — LGPD, fairness, consent violations (NEVER silenced)
# ---------------------------------------------------------------------------

class LIAComplianceError(LIAError):
    """Compliance violation — consent, fairness, LGPD. NEVER fail-open."""

    def __init__(
        self,
        message="Violação de compliance detectada",
        code="COMPLIANCE_ERROR",
        **kwargs,
    ):
        kwargs["recoverable"] = False  # compliance errors are NEVER recoverable
        super().__init__(message=message, code=code, **kwargs)


class LIAConsentError(LIAComplianceError):
    """LGPD consent missing or revoked."""

    def __init__(self, message="Consentimento LGPD ausente ou revogado", code="CONSENT_ERROR", **kwargs):
        super().__init__(message=message, code=code, **kwargs)


class LIAFairnessError(LIAComplianceError):
    """Fairness violation — discriminatory criteria detected."""

    def __init__(self, message="Critério discriminatório detectado", code="FAIRNESS_BLOCKED", **kwargs):
        super().__init__(message=message, code=code, **kwargs)


# ---------------------------------------------------------------------------
# Integration errors — external services
# ---------------------------------------------------------------------------

class LIAIntegrationError(LIAError):
    """External service failed (email, WhatsApp, calendar, ATS)."""

    def __init__(self, message="Serviço externo indisponível", code="INTEGRATION_ERROR", **kwargs):
        kwargs.setdefault("recoverable", True)
        super().__init__(message=message, code=code, **kwargs)
