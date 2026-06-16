"""UC-P2-14: secrets_provider.get_required() must NOT leak the env var name in the exception message."""
import pytest


def _make_env_provider():
    from app.core.secrets_provider import EnvProvider
    return EnvProvider()


def test_secrets_provider_does_not_leak_key_name(monkeypatch):
    """UC-P2-14: ValueError message must not contain the secret key name."""
    key = "ANTHROPIC_API_KEY_THAT_DOES_NOT_EXIST_XYZ"
    monkeypatch.delenv(key, raising=False)

    provider = _make_env_provider()
    with pytest.raises(ValueError) as exc_info:
        provider.get_required(key)

    assert key not in str(exc_info.value), (
        f"Secret key name leaked in exception message: {exc_info.value!r}"
    )


def test_secrets_provider_message_is_generic(monkeypatch):
    """UC-P2-14: ValueError message is a safe generic string."""
    key = "SOME_SECRET_VAR_ABC123"
    monkeypatch.delenv(key, raising=False)

    provider = _make_env_provider()
    with pytest.raises(ValueError) as exc_info:
        provider.get_required(key)

    msg = str(exc_info.value)
    assert "deployment" in msg.lower() or "environment" in msg.lower(), (
        f"Unexpected exception message: {msg!r}"
    )
