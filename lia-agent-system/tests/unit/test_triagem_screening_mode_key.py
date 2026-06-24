"""Testa que a triagem respeita screening_mode (chave nova do wizard),
com fallback para format (chave legada) e default compact."""
import pytest


@pytest.mark.parametrize("config,expected_mode", [
    ({"screening_mode": "full"}, "full"),
    ({"screening_mode": "compact"}, "compact"),
    ({"format": "full"}, "full"),
    ({"format": "compact"}, "compact"),
    ({"screening_mode": "full", "format": "compact"}, "full"),  # nova tem precedência
    ({}, "compact"),
    ({"screening_mode": None, "format": "full"}, "full"),
])
def test_resolve_screening_mode_from_config(config, expected_mode):
    from app.domains.recruitment.services.triagem_session_service.wsi_blocks import (
        _resolve_screening_mode,
    )
    result = _resolve_screening_mode(config)
    assert result == expected_mode, (
        f"_resolve_screening_mode({config}) = {result!r}, esperado {expected_mode!r}"
    )
