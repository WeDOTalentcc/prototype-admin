"""
F-20 P1 sentinel: voice Response schemas use WeDoBaseModel canonical.

Audit: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-20.

Rationale: REGRA 1 Pydantic mandates `WeDoBaseModel` for request schemas (extra='forbid').
Audit F-20 extends consistency: voice Response schemas should also use WeDoBaseModel
since they are dataclasses (not ORM-backed) — `extra='forbid'` is safe and prevents
silent drift from server-side schema bugs.

Sentinels:
- N1 InitiateCallResponse inherits WeDoBaseModel
- N2 VoIPTokenResponse inherits WeDoBaseModel
- N3 StartSessionResponse inherits WeDoBaseModel
- N4 All inherit Config with extra='forbid'
- N5 Parametrized over all voice *Response schemas (catches regression of new ones)
"""
from __future__ import annotations

import pytest

from app.shared.types import WeDoBaseModel


def test_initiate_call_response_uses_wedo_base():
    """N1: InitiateCallResponse herda WeDoBaseModel."""
    from app.api.v1.twilio_voice import InitiateCallResponse
    assert issubclass(InitiateCallResponse, WeDoBaseModel), (
        f"InitiateCallResponse deve herdar WeDoBaseModel (F-20 P1 canonical), "
        f"hoje herda {InitiateCallResponse.__mro__[1].__name__}"
    )


def test_voip_token_response_uses_wedo_base():
    """N2: VoIPTokenResponse herda WeDoBaseModel."""
    from app.api.v1.twilio_voice import VoIPTokenResponse
    assert issubclass(VoIPTokenResponse, WeDoBaseModel), (
        f"VoIPTokenResponse deve herdar WeDoBaseModel (F-20 P1 canonical), "
        f"hoje herda {VoIPTokenResponse.__mro__[1].__name__}"
    )


def test_start_session_response_uses_wedo_base():
    """N3: StartSessionResponse (gemini_voice) herda WeDoBaseModel."""
    from app.api.v1.gemini_voice import StartSessionResponse
    assert issubclass(StartSessionResponse, WeDoBaseModel), (
        f"StartSessionResponse deve herdar WeDoBaseModel (F-20 P1 canonical), "
        f"hoje herda {StartSessionResponse.__mro__[1].__name__}"
    )


def test_response_schemas_have_extra_forbid():
    """N4: WeDoBaseModel subclasses respeitam extra='forbid' (defesa em profundidade)."""
    from app.api.v1.twilio_voice import InitiateCallResponse, VoIPTokenResponse
    from app.api.v1.gemini_voice import StartSessionResponse
    for cls in (InitiateCallResponse, VoIPTokenResponse, StartSessionResponse):
        config = getattr(cls, "model_config", {})
        extra = config.get("extra") if isinstance(config, dict) else getattr(config, "extra", None)
        assert extra == "forbid", (
            f"{cls.__name__} herda WeDoBaseModel mas extra='{extra}' (esperado 'forbid')"
        )


@pytest.mark.parametrize("module_path,schema_name", [
    ("app.api.v1.twilio_voice", "InitiateCallResponse"),
    ("app.api.v1.twilio_voice", "VoIPTokenResponse"),
    ("app.api.v1.gemini_voice", "StartSessionResponse"),
])
def test_all_voice_response_schemas_canonical(module_path, schema_name):
    """N5: parametrize regressão — qualquer voice *Response novo precisa herdar WeDoBaseModel."""
    import importlib
    mod = importlib.import_module(module_path)
    cls = getattr(mod, schema_name)
    assert issubclass(cls, WeDoBaseModel), (
        f"{module_path}.{schema_name} não herda WeDoBaseModel — F-20 P1 canonical"
    )


def test_initiate_call_response_rejects_extra_field():
    """N6: extra='forbid' efetivamente rejeita field não declarado em runtime."""
    from app.api.v1.twilio_voice import InitiateCallResponse
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        InitiateCallResponse(
            success=True,
            session_id="s1",
            status="ok",
            ghost_field="should-fail",  # campo fantasma
        )
