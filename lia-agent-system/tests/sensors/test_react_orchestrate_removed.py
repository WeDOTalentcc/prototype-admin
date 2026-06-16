"""Sensor: deprecated /wizard/react-orchestrate alias must stay removed.

Sprint S (2026-05-21): Paulo authorized removal of the deprecated
react_orchestrate alias in app/api/v1/wizard_smart_orchestrator.py
after a zero-caller audit. This sensor blocks accidental reintroduction.

What we guard:
  1. The Python source app/api/v1/wizard_smart_orchestrator.py MUST NOT
     contain the symbol react_orchestrate (function def, route literal,
     or comment that would suggest the alias is back).
  2. The FastAPI app MUST NOT expose /api/v1/wizard/react-orchestrate
     in its routes. Sibling routes /api/v1/pipeline/react-orchestrate
     and /api/v1/sourcing/react-orchestrate belong to other routers and
     are EXPECTED to keep existing - only the wizard alias is forbidden.

The canonical replacement is /api/v1/wizard/smart-orchestrate.
"""

from __future__ import annotations

from pathlib import Path


_WIZARD_ORCHESTRATOR = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "api"
    / "v1"
    / "wizard_smart_orchestrator.py"
)
_FORBIDDEN_WIZARD_ROUTE = "/api/v1/wizard/react-orchestrate"


def test_source_has_no_react_orchestrate_symbol() -> None:
    """Source file must not reference the removed alias."""
    assert _WIZARD_ORCHESTRATOR.exists(), (
        f"wizard_smart_orchestrator.py missing at {_WIZARD_ORCHESTRATOR}"
    )
    content = _WIZARD_ORCHESTRATOR.read_text(encoding="utf-8")
    # We forbid both the function name and the route literal.
    assert "react_orchestrate" not in content, (
        "Deprecated alias 'react_orchestrate' was reintroduced in "
        f"{_WIZARD_ORCHESTRATOR}. Sprint S (2026-05-21) removed it after "
        "zero-caller audit. Canonical route is '/wizard/smart-orchestrate'. "
        "If you genuinely need an alias, discuss with Paulo first."
    )
    assert "/react-orchestrate" not in content, (
        "Route literal '/react-orchestrate' was reintroduced in "
        f"{_WIZARD_ORCHESTRATOR}. Use '/smart-orchestrate' canonical."
    )


def test_fastapi_app_does_not_expose_wizard_react_orchestrate() -> None:
    """The running FastAPI app must not register the wizard alias route."""
    # Lazy import so a broken app surface still lets pytest collect this file.
    from app.main import app  # type: ignore[import-not-found]

    matching = [
        getattr(route, "path", None)
        for route in app.routes
        if getattr(route, "path", "") == _FORBIDDEN_WIZARD_ROUTE
    ]
    assert not matching, (
        f"Forbidden route {_FORBIDDEN_WIZARD_ROUTE} is registered on the "
        "FastAPI app. Sprint S removed this deprecated alias; reintroducing "
        "it requires explicit approval from Paulo. Sibling routes "
        "/api/v1/pipeline/react-orchestrate and /api/v1/sourcing/"
        "react-orchestrate belong to other routers and are NOT covered by "
        "this guard."
    )
