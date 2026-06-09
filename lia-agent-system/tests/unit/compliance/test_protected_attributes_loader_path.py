"""
Mutation gap: mutmut mutant 763 — protected_attributes._load_config()

Mutant:  data = yaml.safe_load(f) or {}
→ kill: data = None

Sem o `or {}`, se o YAML estiver vazio (yaml.safe_load retorna None),
_load_config() retorna None. Downstream:
  - get_all_attributes() → None.get("attributes", []) → AttributeError
  - LEARNING_PROTECTED_FIELDS fica vazio (fallback hardcoded em fairness_guard)
  - validate_learning_batch() aceita campos protegidos → FAIL-OPEN na aprendizagem

Estes testes pintam o mutant e garantem fail-closed.
"""
from unittest.mock import mock_open, patch

import pytest


@pytest.fixture(autouse=True)
def _clear_loader_cache():
    """Limpa o lru_cache antes e depois de cada teste para forçar re-execução."""
    from app.shared.compliance import protected_attributes

    protected_attributes._load_config.cache_clear()
    yield
    protected_attributes._load_config.cache_clear()


class TestLoadConfigFallback:
    """Pinos direto no `or {}` do _load_config."""

    def test_yaml_none_returns_empty_dict(self):
        """
        Mutant 763: yaml.safe_load retorna None → sem `or {}` → _load_config
        retornaria None → fail-open downstream.
        """
        from app.shared.compliance import protected_attributes

        with patch("builtins.open", mock_open(read_data="")), \
             patch("yaml.safe_load", return_value=None):
            result = protected_attributes._load_config()

        assert isinstance(result, dict), (
            f"_load_config() deve retornar dict, retornou {type(result).__name__!r}. "
            "Mutant 763 ativo: `or {}` foi removido."
        )
        assert result == {}, (
            f"Fallback deve ser {{}} quando yaml.safe_load retorna None, got {result!r}"
        )

    def test_file_not_found_returns_empty_dict(self):
        """Caminho except: arquivo ausente → {} (nunca propaga exceção)."""
        from app.shared.compliance import protected_attributes

        with patch("builtins.open", side_effect=FileNotFoundError("yaml ausente")):
            result = protected_attributes._load_config()

        assert result == {}, "Deve retornar {} quando arquivo não existe"
        assert isinstance(result, dict)

    def test_yaml_parse_error_returns_empty_dict(self):
        """yaml.safe_load levantando exceção → fallback {}."""
        from app.shared.compliance import protected_attributes
        import yaml

        with patch("builtins.open", mock_open(read_data="invalid: ][")), \
             patch("yaml.safe_load", side_effect=yaml.YAMLError("parse fail")):
            result = protected_attributes._load_config()

        assert result == {}
        assert isinstance(result, dict)


class TestGetAllAttributesNeverNone:
    """Downstream safety: get_all_attributes() nunca retorna None."""

    def test_get_all_attributes_returns_list_on_empty_yaml(self):
        """
        Se _load_config() retornasse None (mutant ativo), get_all_attributes()
        lançaria AttributeError: 'NoneType'.get. Verifica que isso não ocorre.
        """
        from app.shared.compliance import protected_attributes

        with patch("builtins.open", mock_open(read_data="")), \
             patch("yaml.safe_load", return_value=None):
            protected_attributes._load_config()  # popula cache com fallback {}
            attrs = protected_attributes.get_all_attributes()

        assert isinstance(attrs, list), (
            "get_all_attributes() deve retornar list mesmo com YAML vazio. "
            "Mutant ativo causaria AttributeError aqui → LEARNING_PROTECTED_FIELDS "
            "ficaria sem campos YAML → fail-open em validate_learning_batch."
        )

    def test_learning_protected_fields_non_empty_with_real_yaml(self):
        """
        Com YAML real, LEARNING_PROTECTED_FIELDS deve conter pelo menos os campos
        canônicos de proteção. Falha se o loader ignorar o YAML silenciosamente.
        """
        from app.shared.compliance.protected_attributes import LEARNING_PROTECTED_FIELDS

        # Campos que DEVEM estar presentes independente da versão do YAML
        mandatory = {"gender", "genero", "race", "raca", "age", "idade"}
        missing = mandatory - {f.lower() for f in LEARNING_PROTECTED_FIELDS}
        assert not missing, (
            f"LEARNING_PROTECTED_FIELDS está faltando campos canônicos: {missing}. "
            "Loader pode estar retornando None/vazio silenciosamente."
        )
