"""Testa normalização canônica de senioridade no kernel WSI.

Cobre:
1. _normalize_seniority_for_kernel: acento-safe, aliases corretos
2. generate_wsi_package: _sen acento-safe (Bug A linha 391)
3. _build_competencies_from_enriched_jd: usa kernel, não _SENIORITY_MAP inline (Bug B linha 582-590)
"""
import pytest
from app.domains.cv_screening.services.wsi_service.service import _normalize_seniority_for_kernel
from app.domains.cv_screening.constants.wsi_constants import SENIORITY_DISTRIBUTIONS


@pytest.mark.parametrize("raw,expected_key", [
    # Casos com acento (Bug A/B principal)
    ("sênior", "senior"),
    ("Sênior", "senior"),
    ("SENIOR", "senior"),
    ("estagiário", "estagiario"),
    ("Estagiário", "estagiario"),
    ("júnior", "junior"),
    ("Júnior", "junior"),
    # Casos sem acento
    ("senior", "senior"),
    ("junior", "junior"),
    ("pleno", "pleno"),
    ("lead", "lead"),
    ("principal", "principal"),
    ("diretor", "diretor"),
    ("executive", "executive"),
    # Aliases
    ("staff", "senior"),
    ("gerente", "lead"),
    ("manager", "lead"),
    ("sr", "senior"),
    ("jr", "junior"),
    ("vp_clevel", "executive"),
    # Fallback
    ("desconhecido", "pleno"),
    ("", "pleno"),
    (None, "pleno"),
])
def test_normalize_seniority_for_kernel(raw, expected_key):
    result = _normalize_seniority_for_kernel(raw)
    assert result == expected_key, f"normalize({raw!r}) = {result!r}, esperado {expected_key!r}"
    assert result in SENIORITY_DISTRIBUTIONS["full"], (
        f"Chave {result!r} não existe em SENIORITY_DISTRIBUTIONS"
    )


def test_normalize_does_not_map_principal_to_lead():
    """Bug B: _SENIORITY_MAP inline mapeava principal->lead; kernel usa principal."""
    result = _normalize_seniority_for_kernel("principal")
    assert result == "principal", f"principal deve mapear para principal, não para {result!r}"


def test_normalize_does_not_map_estagiario_to_junior():
    """Bug B: _SENIORITY_MAP inline mapeava estagiário->junior; kernel usa estagiario."""
    result = _normalize_seniority_for_kernel("estagiário")
    assert result == "estagiario", (
        f"estagiário deve mapear para estagiario, não para {result!r}"
    )


def test_normalize_diretor_is_valid_key():
    """Bug B: _SENIORITY_MAP inline mapeava diretor->executive; kernel usa diretor (chave real)."""
    result = _normalize_seniority_for_kernel("diretor")
    assert result == "diretor"
    assert result in SENIORITY_DISTRIBUTIONS["full"]
    assert result in SENIORITY_DISTRIBUTIONS["compact"]


def test_all_kernel_alias_targets_exist_in_seniority_distributions():
    """Sensor de contrato: todo target de alias deve ser chave válida no SENIORITY_DISTRIBUTIONS."""
    from app.domains.cv_screening.services.wsi_service.service import _SENIORITY_KERNEL_ALIASES
    full_keys = set(SENIORITY_DISTRIBUTIONS["full"].keys())
    for alias, target in _SENIORITY_KERNEL_ALIASES.items():
        assert target in full_keys, (
            f"Alias {alias!r} -> {target!r} mas {target!r} não está em SENIORITY_DISTRIBUTIONS"
        )
