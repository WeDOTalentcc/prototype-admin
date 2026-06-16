"""
Smoke tests para api-onboarding.

Verifica que a sub-app carrega, expõe health endpoint e não tem
import circular com o monolito (via sys.path isolado).
"""
import sys
import importlib
import pytest
from pathlib import Path

# Garante que api-onboarding pode ser importado com path explícito
ONBOARDING_PATH = str(Path(__file__).parent.parent)
MONOLITH_PATH = str(Path(__file__).parent.parent.parent.parent)


class TestApiOnboardingSmoke:

    def test_app_boots(self):
        """api-onboarding deve importar sem exceção."""
        if ONBOARDING_PATH not in sys.path:
            sys.path.insert(0, ONBOARDING_PATH)
        if MONOLITH_PATH not in sys.path:
            sys.path.insert(0, MONOLITH_PATH)
        from main import app  # noqa: PLC0415
        assert app is not None
        assert app.title == "LIA api-onboarding"

    def test_app_has_routes(self):
        """Sub-app deve ter routers registrados (não vazia)."""
        if ONBOARDING_PATH not in sys.path:
            sys.path.insert(0, ONBOARDING_PATH)
        if MONOLITH_PATH not in sys.path:
            sys.path.insert(0, MONOLITH_PATH)
        from main import app  # noqa: PLC0415
        assert len(app.routes) > 10, (
            f"Esperado >10 routers, obtido {len(app.routes)}. "
            "Algum include_router falhou silenciosamente."
        )

    def test_health_route_present(self):
        """Deve haver rota de health check registrada."""
        if ONBOARDING_PATH not in sys.path:
            sys.path.insert(0, ONBOARDING_PATH)
        if MONOLITH_PATH not in sys.path:
            sys.path.insert(0, MONOLITH_PATH)
        from main import app  # noqa: PLC0415
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        health_routes = [p for p in paths if "health" in p or "status" in p]
        assert len(health_routes) > 0, (
            f"Nenhuma rota de health encontrada. Rotas disponíveis: {paths[:10]}"
        )

    def test_pyproject_has_lia_deps(self):
        """pyproject.toml deve declarar lia-models e lia-config."""
        pyproject = Path(ONBOARDING_PATH) / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml ausente"
        content = pyproject.read_text()
        assert "lia-models" in content, "lia-models não declarado"
        assert "lia-config" in content, "lia-config não declarado"
        assert "lia-events" in content, "lia-events não declarado"

    def test_exception_handlers_registered(self):
        """Exception handlers canônicos devem estar registrados (OWASP A09)."""
        if ONBOARDING_PATH not in sys.path:
            sys.path.insert(0, ONBOARDING_PATH)
        if MONOLITH_PATH not in sys.path:
            sys.path.insert(0, MONOLITH_PATH)
        from main import app  # noqa: PLC0415
        from starlette.exceptions import HTTPException as StarletteHTTPException
        handlers = app.exception_handlers
        assert Exception in handlers or StarletteHTTPException in handlers, (
            "Exception handlers globais não registrados — risco de stack trace leakage"
        )
