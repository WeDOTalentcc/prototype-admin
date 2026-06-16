"""R-007 — decode_token valida exp/aud/iss explicitamente.

Sprint 1 Quick Wins — REMEDIATION_BRIEF Wave 0.
Cobre criterio de aceite F-318 / R-007.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import jwt as pyjwt
import pytest


@pytest.fixture
def reset_jwt_settings():
    """Reset JWT_AUDIENCE/ISSUER entre testes via patch em settings."""
    from app.auth import security as security_mod

    original_audience = getattr(security_mod.settings, "JWT_AUDIENCE", None)
    original_issuer = getattr(security_mod.settings, "JWT_ISSUER", None)

    yield security_mod

    # Restaura
    if hasattr(security_mod.settings, "JWT_AUDIENCE"):
        setattr(security_mod.settings, "JWT_AUDIENCE", original_audience)
    if hasattr(security_mod.settings, "JWT_ISSUER"):
        setattr(security_mod.settings, "JWT_ISSUER", original_issuer)


def test_jwt_audience_setting_exists() -> None:
    """R-007: AuthSettings expoe JWT_AUDIENCE (Optional[str])."""
    from app.auth.security import settings

    assert hasattr(
        settings, "JWT_AUDIENCE"
    ), "R-007: AuthSettings precisa expor JWT_AUDIENCE (Optional[str], default None)."


def test_jwt_issuer_setting_exists() -> None:
    """R-007: AuthSettings expoe JWT_ISSUER (Optional[str])."""
    from app.auth.security import settings

    assert hasattr(
        settings, "JWT_ISSUER"
    ), "R-007: AuthSettings precisa expor JWT_ISSUER (Optional[str], default None)."


def test_decode_token_rejects_expired_token() -> None:
    """R-007: token expirado raises ExpiredSignatureError (traduzido em 401)."""
    from app.auth.security import decode_token, settings

    # Token expirado ha 1h
    payload = {
        "sub": "user-123",
        "exp": datetime.utcnow() - timedelta(hours=1),
        "iat": datetime.utcnow() - timedelta(hours=2),
    }
    token = pyjwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_token(token)


def test_decode_token_validates_audience_when_configured(reset_jwt_settings) -> None:
    """R-007: settings.JWT_AUDIENCE='lia-app' + token com aud='evil' → InvalidAudienceError."""
    security_mod = reset_jwt_settings
    setattr(security_mod.settings, "JWT_AUDIENCE", "lia-app")
    setattr(security_mod.settings, "JWT_ISSUER", None)

    payload = {
        "sub": "user-123",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "aud": "evil-attacker",
    }
    token = pyjwt.encode(payload, security_mod.settings.SECRET_KEY, algorithm=security_mod.settings.ALGORITHM)

    with pytest.raises(pyjwt.InvalidAudienceError):
        security_mod.decode_token(token)


def test_decode_token_validates_issuer_when_configured(reset_jwt_settings) -> None:
    """R-007: settings.JWT_ISSUER='wedotalent' + token com iss='attacker' → InvalidIssuerError."""
    security_mod = reset_jwt_settings
    setattr(security_mod.settings, "JWT_AUDIENCE", None)
    setattr(security_mod.settings, "JWT_ISSUER", "wedotalent")

    payload = {
        "sub": "user-123",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iss": "attacker.example.com",
    }
    token = pyjwt.encode(payload, security_mod.settings.SECRET_KEY, algorithm=security_mod.settings.ALGORITHM)

    with pytest.raises(pyjwt.InvalidIssuerError):
        security_mod.decode_token(token)


def test_decode_token_accepts_correct_aud_iss(reset_jwt_settings) -> None:
    """R-007: settings.JWT_AUDIENCE='lia' + token com aud='lia' → OK."""
    security_mod = reset_jwt_settings
    setattr(security_mod.settings, "JWT_AUDIENCE", "lia-app")
    setattr(security_mod.settings, "JWT_ISSUER", "wedotalent")

    payload = {
        "sub": "user-123",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "aud": "lia-app",
        "iss": "wedotalent",
    }
    token = pyjwt.encode(payload, security_mod.settings.SECRET_KEY, algorithm=security_mod.settings.ALGORITHM)

    result = security_mod.decode_token(token)
    assert result["sub"] == "user-123"
    assert result["aud"] == "lia-app"
    assert result["iss"] == "wedotalent"


def test_decode_token_backward_compat_when_no_aud_iss_configured(reset_jwt_settings) -> None:
    """R-007: sem JWT_AUDIENCE/ISSUER setados, tokens legacy sem aud/iss continuam validos."""
    security_mod = reset_jwt_settings
    setattr(security_mod.settings, "JWT_AUDIENCE", None)
    setattr(security_mod.settings, "JWT_ISSUER", None)

    payload = {
        "sub": "user-legacy",
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    token = pyjwt.encode(payload, security_mod.settings.SECRET_KEY, algorithm=security_mod.settings.ALGORITHM)

    # Nao deve raise — backward compat preservada
    result = security_mod.decode_token(token)
    assert result["sub"] == "user-legacy"


def test_create_access_token_includes_aud_iss_when_configured(reset_jwt_settings) -> None:
    """R-007: tokens emitidos incluem aud/iss quando settings configurados."""
    security_mod = reset_jwt_settings
    setattr(security_mod.settings, "JWT_AUDIENCE", "lia-app")
    setattr(security_mod.settings, "JWT_ISSUER", "wedotalent")

    token = security_mod.create_access_token(subject="user-1", role="admin", company_id="company-1")
    decoded = pyjwt.decode(
        token,
        security_mod.settings.SECRET_KEY,
        algorithms=[security_mod.settings.ALGORITHM],
        audience="lia-app",
        issuer="wedotalent",
    )
    assert decoded["aud"] == "lia-app"
    assert decoded["iss"] == "wedotalent"
