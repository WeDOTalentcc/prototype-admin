"""
Testa que a normalizacao de senioridade no kernel WSI:
- Remove acentos corretamente
- Mapeia aliases canonicos
- Produz a distribuicao correta de perguntas por senioridade
"""
import pytest
from app.domains.cv_screening.services.wsi_service.service import _normalize_seniority_for_kernel
from app.domains.cv_screening.constants.wsi_constants import SENIORITY_DISTRIBUTIONS


@pytest.mark.parametrize("raw,expected_key", [
    # Acentos - o bug principal
    ("sênior", "senior"),
    ("Sênior", "senior"),
    ("SENIOR", "senior"),
    ("estagiário", "estagiario"),
    ("Estagiário", "estagiario"),
    ("júnior", "junior"),
    ("Júnior", "junior"),
    # Sem acento - devem funcionar direto
    ("senior", "senior"),
    ("junior", "junior"),
    ("pleno", "pleno"),
    ("lead", "lead"),
    ("principal", "principal"),
    ("diretor", "diretor"),
    ("executive", "executive"),
    # Mapeamentos de aliases
    ("staff", "senior"),
    ("director", "diretor"),
    ("vp_clevel", "executive"),
    ("vp", "executive"),
    ("gerente", "lead"),
    ("manager", "lead"),
    ("tech lead", "lead"),
    ("sr", "senior"),
    ("jr", "junior"),
    # Fallback
    ("desconhecido", "pleno"),
    ("", "pleno"),
])
def test_normalize_seniority_for_kernel(raw, expected_key):
    result = _normalize_seniority_for_kernel(raw)
    assert result == expected_key, (
        f"_normalize_seniority_for_kernel({raw!r}) retornou {result!r}, esperado {expected_key!r}"
    )
    # Garantir que o resultado e uma chave valida no dict de distribuicoes
    assert result in SENIORITY_DISTRIBUTIONS["full"], (
        f"Chave {result!r} nao existe em SENIORITY_DISTRIBUTIONS['full']"
    )


@pytest.mark.parametrize("raw,expected_key", [
    (None, "pleno"),
])
def test_normalize_seniority_handles_none(raw, expected_key):
    result = _normalize_seniority_for_kernel(raw)
    assert result == expected_key
