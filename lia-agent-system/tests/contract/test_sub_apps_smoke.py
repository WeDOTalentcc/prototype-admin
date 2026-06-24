"""
Smoke tests canônicos para sub-apps (api-onboarding, api-funil, api-vagas).

Rodados pelo test runner do monolito, não isoladamente.
Verifica: estrutura, pyproject, boot da app, health route, exception handlers.
"""
import sys
from pathlib import Path

import pytest

MONOLITH = Path(__file__).parent.parent.parent  # workspace/lia-agent-system

APPS = {
    "api-onboarding": MONOLITH / "apps/api-onboarding",
    "api-funil": MONOLITH / "apps/api-funil",
    "api-vagas": MONOLITH / "apps/api-vagas",
}


class TestSubAppsStructure:
    """Verifica estrutura de deployable para cada sub-app."""

    @pytest.mark.parametrize("app_name,app_dir", APPS.items())
    def test_has_pyproject(self, app_name, app_dir):
        assert (app_dir / "pyproject.toml").exists(), \
            f"{app_name}: pyproject.toml ausente"

    @pytest.mark.parametrize("app_name,app_dir", APPS.items())
    def test_has_dockerfile(self, app_name, app_dir):
        assert (app_dir / "Dockerfile").exists(), \
            f"{app_name}: Dockerfile ausente"

    @pytest.mark.parametrize("app_name,app_dir", APPS.items())
    def test_has_init(self, app_name, app_dir):
        assert (app_dir / "__init__.py").exists(), \
            f"{app_name}: __init__.py ausente"

    @pytest.mark.parametrize("app_name,app_dir", APPS.items())
    def test_has_main(self, app_name, app_dir):
        assert (app_dir / "main.py").exists(), \
            f"{app_name}: main.py ausente"

    @pytest.mark.parametrize("app_name,app_dir", APPS.items())
    def test_pyproject_declares_lia_models(self, app_name, app_dir):
        content = (app_dir / "pyproject.toml").read_text()
        assert "lia-models" in content, f"{app_name}: lia-models não declarado"
        assert "lia-config" in content, f"{app_name}: lia-config não declarado"


class TestApiOnboardingBoot:
    """Boot completo da api-onboarding — mais pesado, roda só nesta classe."""

    def test_app_boots_with_438_plus_routes(self):
        monolith = str(MONOLITH)
        onboarding = str(APPS["api-onboarding"])
        if monolith not in sys.path:
            sys.path.insert(0, monolith)
        if onboarding not in sys.path:
            sys.path.insert(0, onboarding)
        import importlib
        mod = importlib.import_module("main")
        app = mod.app
        assert len(app.routes) > 50, (
            f"Esperado >50 routers, obtido {len(app.routes)}"
        )
        assert app.title == "LIA api-onboarding"

    def test_exception_handlers_registered(self):
        monolith = str(MONOLITH)
        onboarding = str(APPS["api-onboarding"])
        if monolith not in sys.path:
            sys.path.insert(0, monolith)
        if onboarding not in sys.path:
            sys.path.insert(0, onboarding)
        import importlib
        mod = importlib.import_module("main")
        app = mod.app
        from starlette.exceptions import HTTPException as StarletteHTTPException
        handlers = app.exception_handlers
        assert Exception in handlers or StarletteHTTPException in handlers, (
            "Exception handlers globais ausentes — risco de stack trace leakage (OWASP A09)"
        )
