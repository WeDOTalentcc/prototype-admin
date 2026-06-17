"""
R-004 (2026-05-07): garante que cada class_path em agents_registry.yaml resolve.

Sensor canonical: drift de class_path era invisível em runtime antes desta
validação porque o loader (react_agent_registry.reload_from_yaml) nunca
chamava importlib.import_module — somente copiava metadata para um dict.
"""
import importlib
import sys
from pathlib import Path

import pytest
import yaml

# Garantir que `app.*` resolve quando o teste roda standalone (sem PYTHONPATH externo)
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_registry():
    registry_path = ROOT / "app" / "agents_registry.yaml"
    return yaml.safe_load(registry_path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("agent_cfg", _load_registry().get("agents", []))
def test_class_path_resolves(agent_cfg):
    """Cada class_path em registry deve resolver via importlib."""
    if not agent_cfg.get("enabled", True):
        pytest.skip(f"agent '{agent_cfg.get('name')}' disabled")
    class_path = agent_cfg["class_path"]
    module_path, class_name = class_path.rsplit(".", 1)
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    assert cls is not None, f"class {class_name} resolveu para None"


def test_wizard_entry_is_canonical_not_legacy():
    """Cleanup 2026-05-29: a entrada `wizard` do registry NAO pode apontar pro
    JobWizardGraph LEGACY. Canonical = WizardReActAgent (alinhado ao
    @register_agent('wizard') do decorator registry). O dominio wizard no chat
    roda via WizardSessionService/JobCreationGraph; este entry e o agente
    registrado pro registry yaml-based + background tasks."""
    reg = _load_registry()
    wizard = next(
        (a for a in reg.get("agents", []) if a.get("name") == "wizard"), None
    )
    assert wizard is not None, "entrada 'wizard' sumiu do agents_registry.yaml"
    cp = wizard["class_path"]
    assert "job_wizard_graph" not in cp, (
        f"wizard ainda aponta pro JobWizardGraph LEGACY: {cp}"
    )
    assert cp.endswith("WizardReActAgent"), (
        f"wizard class_path canonical = WizardReActAgent, got: {cp}"
    )
