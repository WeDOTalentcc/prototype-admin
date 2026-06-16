"""
Testes unitários para PromptVersionRegistry (Sprint B / André P3/R3).

Cobre: register, get, get_by_hash, list_versions, singleton,
hash SHA256 correto, versão "latest", registro duplicado, nome inexistente.
"""
import hashlib
import pytest

from app.shared.services.prompt_version_registry import (
    PromptVersionRegistry,
    prompt_version_registry,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def registry():
    """Registry isolado por teste (não afeta o singleton global)."""
    return PromptVersionRegistry()


TEMPLATE_A = "Você é um assistente de recrutamento da WeDOTalent."
TEMPLATE_B = "Você é um assistente especializado em triagem de candidatos."
TEMPLATE_C = "Versão atualizada do prompt de triagem com suporte a múltiplos idiomas."


# ---------------------------------------------------------------------------
# Testes de register
# ---------------------------------------------------------------------------


class TestRegister:
    def test_register_retorna_hash_prefix_12_chars(self, registry):
        hash_prefix = registry.register("talent_react", "1.0.0", TEMPLATE_A)
        assert isinstance(hash_prefix, str)
        assert len(hash_prefix) == 12

    def test_register_hash_e_sha256_correto(self, registry):
        """hash_prefix deve ser os primeiros 12 chars do SHA-256 do template."""
        hash_prefix = registry.register("talent_react", "1.0.0", TEMPLATE_A)
        expected_full = hashlib.sha256(TEMPLATE_A.encode("utf-8")).hexdigest()
        assert hash_prefix == expected_full[:12]

    def test_register_hash_e_determinístico(self, registry):
        """Mesmo template sempre gera o mesmo hash."""
        h1 = registry.register("prompt_x", "1.0.0", TEMPLATE_A)
        r2 = PromptVersionRegistry()
        h2 = r2.register("prompt_x", "1.0.0", TEMPLATE_A)
        assert h1 == h2

    def test_register_templates_diferentes_geram_hashes_diferentes(self, registry):
        h1 = registry.register("p", "1.0.0", TEMPLATE_A)
        h2 = registry.register("p", "2.0.0", TEMPLATE_B)
        assert h1 != h2

    def test_registro_duplicado_atualiza_entry(self, registry):
        """Registrar a mesma (name, version) com template diferente deve atualizar."""
        registry.register("p", "1.0.0", TEMPLATE_A)
        registry.register("p", "1.0.0", TEMPLATE_B)
        entry = registry.get("p", "1.0.0")
        assert entry is not None
        assert entry["template"] == TEMPLATE_B

    def test_registro_duplicado_atualiza_hash_index(self, registry):
        """Após atualização, o hash antigo não deve existir no índice."""
        h_old = registry.register("p", "1.0.0", TEMPLATE_A)
        h_new = registry.register("p", "1.0.0", TEMPLATE_B)
        assert registry.get_by_hash(h_old) is None
        assert registry.get_by_hash(h_new) is not None


# ---------------------------------------------------------------------------
# Testes de get
# ---------------------------------------------------------------------------


class TestGet:
    def test_get_por_nome_e_versao_retorna_entry(self, registry):
        registry.register("rec", "1.0.0", TEMPLATE_A)
        entry = registry.get("rec", "1.0.0")
        assert entry is not None
        assert entry["name"] == "rec"
        assert entry["version"] == "1.0.0"
        assert entry["template"] == TEMPLATE_A

    def test_get_nome_inexistente_retorna_none(self, registry):
        result = registry.get("nao_existe")
        assert result is None

    def test_get_versao_inexistente_retorna_none(self, registry):
        registry.register("rec", "1.0.0", TEMPLATE_A)
        result = registry.get("rec", "99.0.0")
        assert result is None

    def test_get_latest_retorna_versao_mais_recente(self, registry):
        """get(name, "latest") deve retornar a última versão registrada."""
        registry.register("rec", "1.0.0", TEMPLATE_A)
        registry.register("rec", "2.0.0", TEMPLATE_B)
        registry.register("rec", "3.0.0", TEMPLATE_C)
        entry = registry.get("rec", "latest")
        assert entry is not None
        assert entry["version"] == "3.0.0"

    def test_get_latest_com_uma_versao(self, registry):
        registry.register("only_one", "1.0.0", TEMPLATE_A)
        entry = registry.get("only_one", "latest")
        assert entry is not None
        assert entry["version"] == "1.0.0"

    def test_get_entry_contem_campos_obrigatorios(self, registry):
        registry.register("full_check", "1.0.0", TEMPLATE_A)
        entry = registry.get("full_check", "1.0.0")
        for campo in ("name", "version", "template", "hash_sha256", "hash_prefix", "created_at"):
            assert campo in entry, f"Campo ausente: {campo}"

    def test_get_hash_sha256_e_64_chars_hex(self, registry):
        registry.register("hash_check", "1.0.0", TEMPLATE_A)
        entry = registry.get("hash_check", "1.0.0")
        full_hash = entry["hash_sha256"]
        assert len(full_hash) == 64
        assert all(c in "0123456789abcdef" for c in full_hash)


# ---------------------------------------------------------------------------
# Testes de get_by_hash
# ---------------------------------------------------------------------------


class TestGetByHash:
    def test_get_by_hash_retorna_entry_correta(self, registry):
        h = registry.register("p", "1.0.0", TEMPLATE_A)
        entry = registry.get_by_hash(h)
        assert entry is not None
        assert entry["hash_prefix"] == h

    def test_get_by_hash_inexistente_retorna_none(self, registry):
        result = registry.get_by_hash("000000000000")
        assert result is None

    def test_get_by_hash_apos_multiplos_registros(self, registry):
        h1 = registry.register("p1", "1.0.0", TEMPLATE_A)
        h2 = registry.register("p2", "1.0.0", TEMPLATE_B)
        assert registry.get_by_hash(h1)["name"] == "p1"
        assert registry.get_by_hash(h2)["name"] == "p2"


# ---------------------------------------------------------------------------
# Testes de list_versions
# ---------------------------------------------------------------------------


class TestListVersions:
    def test_list_versions_retorna_todas_versoes(self, registry):
        registry.register("p", "1.0.0", TEMPLATE_A)
        registry.register("p", "2.0.0", TEMPLATE_B)
        versions = registry.list_versions("p")
        assert len(versions) == 2
        assert {v["version"] for v in versions} == {"1.0.0", "2.0.0"}

    def test_list_versions_nome_inexistente_retorna_lista_vazia(self, registry):
        result = registry.list_versions("nao_existe")
        assert result == []

    def test_list_versions_ordenado_por_created_at(self, registry):
        registry.register("p", "1.0.0", TEMPLATE_A)
        registry.register("p", "2.0.0", TEMPLATE_B)
        versions = registry.list_versions("p")
        # Deve estar ordenado (created_at é ISO string, ordenação lexicográfica funciona)
        assert versions[0]["version"] == "1.0.0"
        assert versions[1]["version"] == "2.0.0"


# ---------------------------------------------------------------------------
# Testes de get_current_hash
# ---------------------------------------------------------------------------


class TestGetCurrentHash:
    def test_get_current_hash_retorna_hash_da_versao_mais_recente(self, registry):
        registry.register("p", "1.0.0", TEMPLATE_A)
        h = registry.register("p", "2.0.0", TEMPLATE_B)
        assert registry.get_current_hash("p") == h

    def test_get_current_hash_nome_inexistente_retorna_none(self, registry):
        assert registry.get_current_hash("nao_existe") is None


# ---------------------------------------------------------------------------
# Testes de singleton global
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_singleton_e_instancia_de_prompt_version_registry(self):
        assert isinstance(prompt_version_registry, PromptVersionRegistry)

    def test_singleton_persiste_entre_imports(self):
        """O singleton global deve ser o mesmo objeto em importações diferentes."""
        from app.shared.services.prompt_version_registry import prompt_version_registry as r2
        assert prompt_version_registry is r2

    def test_singleton_registra_e_recupera(self):
        """Registrar no singleton e recuperar no mesmo teste."""
        template = "Prompt de teste singleton — Sprint B."
        h = prompt_version_registry.register(
            "__test_singleton__", "0.0.1", template
        )
        entry = prompt_version_registry.get("__test_singleton__", "0.0.1")
        assert entry is not None
        assert entry["hash_prefix"] == h
        # Limpeza para não poluir outros testes
        prompt_version_registry._store.pop("__test_singleton__", None)
        prompt_version_registry._hash_index.pop(h, None)
