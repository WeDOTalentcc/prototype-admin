"""Sensor test: AuthProvider nao usa Rails JWT fallback."""

def test_auth_provider_does_not_use_rails_fallback():
    """AuthProvider nao deve usar Rails JWT fallback — FastAPI JWT e fonte de verdade."""
    import asyncio
    from unittest.mock import AsyncMock, patch
    from fastapi import HTTPException
    from app.shared.auth.auth_provider import AuthProvider

    async def _run():
        provider = AuthProvider()
        # Mock: FastAPI JWT falha — deve retornar 401 sem cair em Rails
        with patch("app.auth.security.decode_token", side_effect=Exception("invalid jwt")):
            db = AsyncMock()
            # Simula DB retornando None para qualquer query
            db.execute.return_value.scalar_one_or_none = AsyncMock(return_value=None)
            try:
                await provider.resolve("invalid-fastapi-token", db)
                return False  # should have raised
            except HTTPException as e:
                return e.status_code == 401

    assert asyncio.get_event_loop().run_until_complete(_run()), \
        "AuthProvider deveria ter retornado 401 para token inválido (sem Rails fallback)"


def test_auth_source_rails_is_deprecated():
    """AuthSource.RAILS deve existir mas estar marcado como DEPRECATED no docstring."""
    from app.shared.auth.auth_provider import AuthSource
    assert hasattr(AuthSource, "RAILS"), "AuthSource.RAILS deve existir para retrocompat de logs"
    # Verify docstring mentions DEPRECATED
    import inspect
    doc = inspect.getdoc(AuthSource)
    assert doc and "DEPRECATED" in doc, \
        "AuthSource docstring deve mencionar DEPRECATED para AuthSource.RAILS"


def test_rails_jwt_sensor_exists():
    """Sensor check_rails_jwt_usage.py deve existir."""
    from pathlib import Path
    sensor = Path("scripts/check_rails_jwt_usage.py")
    assert sensor.exists(), (
        "scripts/check_rails_jwt_usage.py nao encontrado. "
        "Sensor detecta usos de Rails JWT fora dos pontos permitidos."
    )
