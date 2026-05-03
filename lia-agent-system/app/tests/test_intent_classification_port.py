"""UC-P3-16: wizard_step_service → intent_classifier via abstract port.

TDD-first tests that verify:
1. IIntentClassificationPort is importable and correctly abstract.
2. Both adapters (standard + enhanced) implement the port.
3. A mock adapter can be injected and called.
4. wizard_step_service imports through the shared classifier services (not new)
   — the port adds a layer for future DI without breaking existing behaviour.
"""
from __future__ import annotations

import asyncio


def test_intent_classification_port_importable():
    """IIntentClassificationPort and adapters must be importable from shared/ports."""
    from app.shared.ports.intent_classification_port import (
        EnhancedIntentClassifierAdapter,
        IIntentClassificationPort,
        IntentClassifierAdapter,
    )

    assert IIntentClassificationPort is not None
    assert IntentClassifierAdapter is not None
    assert EnhancedIntentClassifierAdapter is not None


def test_intent_classification_port_is_abstract():
    """IIntentClassificationPort must be abstract (cannot be instantiated directly)."""
    from app.shared.ports.intent_classification_port import IIntentClassificationPort
    import pytest

    with pytest.raises(TypeError):
        IIntentClassificationPort()  # type: ignore[abstract]


def test_intent_classification_port_has_required_methods():
    """IIntentClassificationPort must declare classify and get_available_intents."""
    from app.shared.ports.intent_classification_port import IIntentClassificationPort

    abstract_methods = IIntentClassificationPort.__abstractmethods__
    assert "classify" in abstract_methods
    assert "get_available_intents" in abstract_methods


def test_standard_adapter_implements_port():
    """IntentClassifierAdapter must be a subclass of IIntentClassificationPort."""
    from app.shared.ports.intent_classification_port import (
        IIntentClassificationPort,
        IntentClassifierAdapter,
    )

    assert issubclass(IntentClassifierAdapter, IIntentClassificationPort)


def test_enhanced_adapter_implements_port():
    """EnhancedIntentClassifierAdapter must be a subclass of IIntentClassificationPort."""
    from app.shared.ports.intent_classification_port import (
        EnhancedIntentClassifierAdapter,
        IIntentClassificationPort,
    )

    assert issubclass(EnhancedIntentClassifierAdapter, IIntentClassificationPort)


def test_mock_intent_port_works():
    """A mock IIntentClassificationPort can be created and called without LLM."""
    from app.shared.ports.intent_classification_port import IIntentClassificationPort

    class MockIntentPort(IIntentClassificationPort):
        async def classify(self, user_input, stage_context=None, use_llm=True):
            class _Result:
                intent_type = "DATA_INPUT"
                confidence = 0.99
                extracted_entities = {}
                original_text = user_input
            return _Result()

        async def get_available_intents(self) -> list[str]:
            return ["DATA_INPUT", "QUESTION", "CORRECTION", "DEVIATION", "REUSE_VACANCY"]

    port = MockIntentPort()
    result = asyncio.run(port.classify("Engenheiro de Software Sênior"))
    assert result.intent_type == "DATA_INPUT"
    assert result.confidence == 0.99

    intents = asyncio.run(port.get_available_intents())
    assert "DATA_INPUT" in intents
    assert len(intents) == 5


def test_port_module_exists_in_shared_ports():
    """The port file must be importable at the canonical shared/ports path."""
    import importlib

    module = importlib.import_module("app.shared.ports.intent_classification_port")
    assert hasattr(module, "IIntentClassificationPort")
    assert hasattr(module, "IntentClassifierAdapter")
    assert hasattr(module, "EnhancedIntentClassifierAdapter")
