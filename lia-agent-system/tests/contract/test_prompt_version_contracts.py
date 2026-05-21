"""
Testes de contrato para PromptVersionRegistry (Sprint B / André P3/R3).

Verifica:
- Endpoint /admin/prompts/versions existe no roteador admin_prompts
- PromptVersionRegistry tem os métodos obrigatórios (register, get, get_by_hash, list_versions)
- hash retornado é SHA-256 (64 chars hex) ou prefixo de 12 chars
- migration 030_add_prompt_version existe e tem upgrade/downgrade
"""
import hashlib
import inspect
import importlib
import pytest


# ---------------------------------------------------------------------------
# Contrato: endpoint /admin/prompts/versions
# ---------------------------------------------------------------------------


class TestAdminPromptsEndpoint:
    def test_admin_prompts_router_existe(self):
        """Módulo admin_prompts deve ser importável e ter `router`."""
        module = importlib.import_module("app.api.v1.admin_prompts")
        assert hasattr(module, "router"), "admin_prompts deve exportar `router`"

    def test_admin_prompts_router_tem_rotas_versions(self):
        """Router deve ter a rota /versions registrada."""
        from app.api.v1.admin_prompts import router
        route_paths = [r.path for r in router.routes]
        assert any("/versions" in p for p in route_paths), (
            f"Rota /versions não encontrada. Rotas disponíveis: {route_paths}"
        )

    def test_admin_prompts_router_tem_rota_versions_por_nome(self):
        """Router deve ter a rota /versions/{name} registrada."""
        from app.api.v1.admin_prompts import router
        route_paths = [r.path for r in router.routes]
        assert any("{name}" in p for p in route_paths), (
            f"Rota /versions/{{name}} não encontrada. Rotas disponíveis: {route_paths}"
        )

    def test_admin_prompts_prefix_correto(self):
        """Prefix do router deve ser /admin/prompts."""
        from app.api.v1.admin_prompts import router
        assert router.prefix == "/admin/prompts"

    def test_admin_prompts_tags_correto(self):
        """Tags do router devem incluir admin-prompts."""
        from app.api.v1.admin_prompts import router
        assert "admin-prompts" in router.tags


# ---------------------------------------------------------------------------
# Contrato: PromptVersionRegistry — métodos obrigatórios
# ---------------------------------------------------------------------------


class TestPromptVersionRegistryInterface:
    def test_classe_exportada(self):
        module = importlib.import_module("app.shared.services.prompt_version_registry")
        assert hasattr(module, "PromptVersionRegistry")

    def test_singleton_exportado(self):
        module = importlib.import_module("app.shared.services.prompt_version_registry")
        assert hasattr(module, "prompt_version_registry")

    def test_metodo_register_existe(self):
        from app.shared.services.prompt_version_registry import PromptVersionRegistry
        assert hasattr(PromptVersionRegistry, "register")
        assert callable(PromptVersionRegistry.register)

    def test_metodo_get_existe(self):
        from app.shared.services.prompt_version_registry import PromptVersionRegistry
        assert hasattr(PromptVersionRegistry, "get")
        assert callable(PromptVersionRegistry.get)

    def test_metodo_get_by_hash_existe(self):
        from app.shared.services.prompt_version_registry import PromptVersionRegistry
        assert hasattr(PromptVersionRegistry, "get_by_hash")
        assert callable(PromptVersionRegistry.get_by_hash)

    def test_metodo_list_versions_existe(self):
        from app.shared.services.prompt_version_registry import PromptVersionRegistry
        assert hasattr(PromptVersionRegistry, "list_versions")
        assert callable(PromptVersionRegistry.list_versions)

    def test_metodo_get_current_hash_existe(self):
        from app.shared.services.prompt_version_registry import PromptVersionRegistry
        assert hasattr(PromptVersionRegistry, "get_current_hash")
        assert callable(PromptVersionRegistry.get_current_hash)

    def test_register_retorna_string_12_chars(self):
        from app.shared.services.prompt_version_registry import PromptVersionRegistry
        r = PromptVersionRegistry()
        result = r.register("contract_test", "1.0.0", "template de contrato")
        assert isinstance(result, str)
        assert len(result) == 12

    def test_register_retorna_prefixo_sha256(self):
        """O prefixo retornado deve ser os primeiros 12 chars do SHA-256."""
        from app.shared.services.prompt_version_registry import PromptVersionRegistry
        r = PromptVersionRegistry()
        template = "template para validar sha256"
        prefix = r.register("sha256_test", "1.0.0", template)
        full_hash = hashlib.sha256(template.encode()).hexdigest()
        assert prefix == full_hash[:12]
        # O hash completo tem 64 chars hex
        assert len(full_hash) == 64
        assert all(c in "0123456789abcdef" for c in full_hash)

    def test_register_signature_tem_parametros_corretos(self):
        """register(self, name, version, template) -> str."""
        from app.shared.services.prompt_version_registry import PromptVersionRegistry
        sig = inspect.signature(PromptVersionRegistry.register)
        params = list(sig.parameters.keys())
        assert "name" in params
        assert "version" in params
        assert "template" in params

    def test_get_signature_tem_version_default_latest(self):
        """get(self, name, version="latest") deve ter default "latest"."""
        from app.shared.services.prompt_version_registry import PromptVersionRegistry
        sig = inspect.signature(PromptVersionRegistry.get)
        version_param = sig.parameters.get("version")
        assert version_param is not None
        assert version_param.default == "latest"


# ---------------------------------------------------------------------------
# Contrato: migration 030_add_prompt_version
# ---------------------------------------------------------------------------


class TestMigration030:
    def test_migration_arquivo_existe(self):
        """Arquivo de migration 030 deve existir."""
        import os
        migration_path = (
            "alembic/versions/030_add_prompt_version.py"
        )
        # Tenta importar o módulo
        try:
            module = importlib.import_module(
                "alembic.versions.030_add_prompt_version".replace("/", ".").replace("-", "_")
            )
        except ModuleNotFoundError:
            # Verificação alternativa via filesystem
            import pathlib
            base = pathlib.Path(__file__).parents[2]
            path = base / "alembic" / "versions" / "030_add_prompt_version.py"
            assert path.exists(), f"Migration não encontrada em {path}"

    def test_migration_tem_upgrade_function(self):
        """Migration deve ter função upgrade()."""
        import pathlib
        import importlib.util
        base = pathlib.Path(__file__).parents[2]
        path = base / "alembic" / "versions" / "030_add_prompt_version.py"
        if not path.exists():
            pytest.skip("Migration 030 não encontrada — skipping")
        spec = importlib.util.spec_from_file_location("migration_030", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, "upgrade"), "Migration deve ter função upgrade()"

    def test_migration_tem_downgrade_function(self):
        """Migration deve ter função downgrade()."""
        import pathlib
        import importlib.util
        base = pathlib.Path(__file__).parents[2]
        path = base / "alembic" / "versions" / "030_add_prompt_version.py"
        if not path.exists():
            pytest.skip("Migration 030 não encontrada — skipping")
        spec = importlib.util.spec_from_file_location("migration_030", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, "downgrade"), "Migration deve ter função downgrade()"

    def test_migration_tem_revision_id_correto(self):
        """Migration deve ter revision ID 030_add_prompt_version."""
        import pathlib
        import importlib.util
        base = pathlib.Path(__file__).parents[2]
        path = base / "alembic" / "versions" / "030_add_prompt_version.py"
        if not path.exists():
            pytest.skip("Migration 030 não encontrada — skipping")
        spec = importlib.util.spec_from_file_location("migration_030", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, "revision")
        assert "030" in module.revision

    def test_migration_menciona_prompt_version(self):
        """Arquivo de migration deve mencionar 'prompt_version'."""
        import pathlib
        base = pathlib.Path(__file__).parents[2]
        path = base / "alembic" / "versions" / "030_add_prompt_version.py"
        if not path.exists():
            pytest.skip("Migration 030 não encontrada — skipping")
        content = path.read_text()
        assert "prompt_version" in content
