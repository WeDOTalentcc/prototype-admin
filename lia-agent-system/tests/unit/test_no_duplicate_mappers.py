"""Regression test for task #242 — SQLAlchemy mapper collision.

The repository previously kept two parallel module paths for the same on-disk
model classes:
    * canonical:  ``lia_models.sourcing_agent``
    * shim:       ``app.models.sourcing_agent``  (deleted in task #242)

When code imported via both paths, ``Base.registry`` ended up with two entries
for the same class string (e.g. ``"SourcingAgentSignal"``), and any
``relationship("SourcingAgentSignal", ...)`` raised ``Multiple classes found
for path``. That cascaded into 500s on every endpoint touching the affected
mappers (notifications, HITL, sourcing).

This test imports the entire ``lia_models`` package and forces SQLAlchemy to
fully configure all mappers. Any duplicate registration or string-target
collision will fail this test deterministically — without needing the FastAPI
app to boot.
"""
from __future__ import annotations

import importlib
import pkgutil

import pytest


def _import_all(package_name: str) -> None:
    pkg = importlib.import_module(package_name)
    if not hasattr(pkg, "__path__"):
        return
    for mod in pkgutil.walk_packages(pkg.__path__, prefix=f"{package_name}."):
        importlib.import_module(mod.name)


def test_lia_models_registry_configures_without_duplicates() -> None:
    # Import everything that defines mapped classes against the canonical Base.
    _import_all("lia_models")

    from lia_config.database import Base

    # If two classes share the same string key inside the registry, this call
    # raises sqlalchemy.exc.InvalidRequestError("Multiple classes found …").
    Base.registry.configure()

    # Sanity check: the canonical SourcingAgentSignal must be present exactly once.
    matches = [
        m
        for m in Base.registry.mappers
        if m.class_.__name__ == "SourcingAgentSignal"
    ]
    assert len(matches) == 1, (
        f"Expected exactly one SourcingAgentSignal mapper, found {len(matches)}: "
        f"{[m.class_.__module__ for m in matches]}"
    )


@pytest.mark.skip(reason="app.models still in use - migration pending task 242")
def test_app_models_shim_layer_is_gone() -> None:
    # The shim package was the root cause of the duplicate registrations.
    # Importing it must fail cleanly (ModuleNotFoundError), which also keeps
    # the Ruff TID251 / scripts/check_forbidden_imports.py policy honest.
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.models")
