"""
Regression test — Task #308 anti-revival (S7.2).

`GlobalToolRegistry` is intentionally NOT used to register domain tools at
boot time anymore. Domain tool routing goes through `ToolRegistry`
(`app.shared.tools.registry`) and the declarative `tool_permissions.yaml`.

This test fails the build if anything (a) imports
`app.shared.global_tool_registry` to populate it during module import, or
(b) re-introduces eager `GlobalToolRegistry.get_instance().register(...)`
side effects on app boot.

To avoid false passes from Python's module cache, the boot-import test
forcibly drops every cached `app.*` module and re-imports `app.main` from
scratch so any boot-time side effect runs again.
"""

from __future__ import annotations

import importlib
import sys

import pytest


def _reset_registry_module():
    """Drop the registry singleton so leftover state cannot leak between tests."""
    sys.modules.pop("app.shared.global_tool_registry", None)
    mod = importlib.import_module("app.shared.global_tool_registry")
    mod.GlobalToolRegistry._instance = None
    return mod


def _drop_app_modules():
    """Remove every cached `app.*` module so the next import re-runs side effects."""
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


def test_registry_is_empty_on_fresh_import():
    mod = _reset_registry_module()
    reg = mod.GlobalToolRegistry.get_instance()
    assert reg._registry == {}, (
        "GlobalToolRegistry._registry must be empty at boot. "
        "Task #308 retired eager registration; use ToolRegistry + "
        "tool_permissions.yaml for domain tools."
    )


def test_registry_stays_empty_after_app_module_import():
    _drop_app_modules()
    mod = _reset_registry_module()
    # Force a real import (not a cache hit) so any boot-time registration runs.
    sys.modules.pop("app.main", None)
    importlib.import_module("app.main")
    reg = mod.GlobalToolRegistry.get_instance()
    assert reg._registry == {}, (
        "Importing app.main caused something to populate "
        "GlobalToolRegistry. Task #308 forbids eager registration on boot. "
        f"Found entries: {sorted(reg._registry.keys())}"
    )
