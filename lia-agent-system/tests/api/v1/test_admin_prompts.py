"""
Tests — Wave 2 Agent B / T-13 Fase 2 — admin_prompts tenant overrides.

Cobre:
- GET /tenant-overrides — list empty para tenant novo
- PUT /tenant-overrides/{path} — cria YAML + invalidate_cache called
- PUT — invalid YAML → 422
- PUT — missing metadata.version → 422
- DELETE /tenant-overrides/{path} — remove override
- Multi-tenancy fail-closed — cross-tenant retorna 404

Pattern canonical: TestClient + dependency_overrides (mesmo de admin_compliance_fairness).
"""
import shutil
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import admin_prompts as ap_module
from app.api.v1.admin_prompts import router
from app.auth.dependencies import require_admin
from app.auth.models import User, UserRole
from app.shared.prompts.loader import PROMPTS_DIR, PromptLoader
from app.shared.security.require_company_id import require_company_id


@pytest.fixture
def fake_admin() -> User:
    """Stub admin user."""
    u = User(
        id=uuid4(),
        email="admin@test.com",
        name="Admin Test",
        role=UserRole.admin,
        company_id=uuid4(),
    )
    return u


@pytest.fixture
def tenant_id() -> str:
    return f"test-tenant-{uuid4().hex[:8]}"


@pytest.fixture
def app_with_router(fake_admin, tenant_id):
    """Minimal FastAPI app com router + dep overrides."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[require_admin] = lambda: fake_admin
    app.dependency_overrides[require_company_id] = lambda: tenant_id
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app_with_router):
    return TestClient(app_with_router)


@pytest.fixture
def cleanup_tenant_dir(tenant_id):
    """Remove tenant override dir antes E depois do teste."""
    from app.shared.prompts.loader import TENANTS_DIR

    tenant_dir = TENANTS_DIR / tenant_id
    if tenant_dir.exists():
        shutil.rmtree(tenant_dir)
    PromptLoader.invalidate_cache(tenant_id=tenant_id)
    yield tenant_dir
    if tenant_dir.exists():
        shutil.rmtree(tenant_dir)
    PromptLoader.invalidate_cache(tenant_id=tenant_id)


VALID_YAML = """metadata:
  version: "1.0.0-tenant-custom"
  description: "Override custom for tenant"

system_prompt: |
  Você é a LIA customizada para a empresa Acme.
  Use linguagem ainda mais formal nas saudações.
"""


# ---------------------------------------------------------------------------
# GET /tenant-overrides — list
# ---------------------------------------------------------------------------


class TestListTenantOverrides:
    def test_list_returns_empty_for_new_tenant(
        self, client, tenant_id, cleanup_tenant_dir
    ):
        response = client.get("/api/v1/admin/prompts/tenant-overrides")
        assert response.status_code == 200
        data = response.json()
        assert data["company_id"] == tenant_id
        assert data["total"] == 0
        assert data["overrides"] == []


# ---------------------------------------------------------------------------
# PUT /tenant-overrides/{path}
# ---------------------------------------------------------------------------


class TestPutTenantOverride:
    def test_put_creates_yaml_and_invalidates_cache(
        self, client, tenant_id, cleanup_tenant_dir
    ):
        with patch.object(
            PromptLoader, "invalidate_cache", wraps=PromptLoader.invalidate_cache
        ) as mock_invalidate:
            response = client.put(
                "/api/v1/admin/prompts/tenant-overrides/shared/lia_persona",
                json={"content": VALID_YAML},
            )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert data["path"] == "shared/lia_persona"
        assert data["version"] == "1.0.0-tenant-custom"
        assert isinstance(data["validation_warnings"], list)

        # invalidate_cache foi chamado com path + tenant_id
        mock_invalidate.assert_called_once()
        call_kwargs = mock_invalidate.call_args.kwargs
        assert call_kwargs.get("path") == "shared/lia_persona"
        assert call_kwargs.get("tenant_id") == tenant_id

        # Arquivo realmente criado em disco
        from app.shared.prompts.loader import TENANTS_DIR

        expected_file = TENANTS_DIR / tenant_id / "shared" / "lia_persona.yaml"
        assert expected_file.exists()

    def test_put_invalid_yaml_returns_422(
        self, client, cleanup_tenant_dir
    ):
        response = client.put(
            "/api/v1/admin/prompts/tenant-overrides/shared/lia_persona",
            json={"content": "metadata:\n  version: 1.0\n  invalid: [\n"},
        )
        assert response.status_code == 422
        assert "YAML inválido" in response.json()["detail"]

    def test_put_missing_metadata_version_returns_422(
        self, client, cleanup_tenant_dir
    ):
        response = client.put(
            "/api/v1/admin/prompts/tenant-overrides/shared/lia_persona",
            json={"content": "metadata:\n  description: sem version\nsystem_prompt: oi\n"},
        )
        assert response.status_code == 422
        assert "metadata.version" in response.json()["detail"]

    def test_put_blocks_path_traversal(self, client, cleanup_tenant_dir):
        response = client.put(
            "/api/v1/admin/prompts/tenant-overrides/../etc/passwd",
            json={"content": VALID_YAML},
        )
        # FastAPI normaliza .. — esperamos 400 OU 404 OU 422 (path traversal blocked)
        assert response.status_code in {400, 404, 422}

    def test_put_nonexistent_canonical_path_returns_404(
        self, client, cleanup_tenant_dir
    ):
        response = client.put(
            "/api/v1/admin/prompts/tenant-overrides/domains/nonexistent_xyz_canonical",
            json={"content": VALID_YAML},
        )
        assert response.status_code == 404
        assert "canonical" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /tenant-overrides/{path}
# ---------------------------------------------------------------------------


class TestDeleteTenantOverride:
    def test_delete_removes_override(
        self, client, tenant_id, cleanup_tenant_dir
    ):
        # 1) Criar
        put_resp = client.put(
            "/api/v1/admin/prompts/tenant-overrides/shared/lia_persona",
            json={"content": VALID_YAML},
        )
        assert put_resp.status_code == 200

        # 2) Verificar GET retorna o conteúdo
        get_resp = client.get(
            "/api/v1/admin/prompts/tenant-overrides/shared/lia_persona"
        )
        assert get_resp.status_code == 200
        assert "metadata" in get_resp.json()["content"]

        # 3) Delete
        with patch.object(
            PromptLoader, "invalidate_cache", wraps=PromptLoader.invalidate_cache
        ) as mock_invalidate:
            del_resp = client.delete(
                "/api/v1/admin/prompts/tenant-overrides/shared/lia_persona"
            )
        assert del_resp.status_code == 200
        assert del_resp.json()["success"] is True

        mock_invalidate.assert_called_once()
        from app.shared.prompts.loader import TENANTS_DIR

        assert not (TENANTS_DIR / tenant_id / "shared" / "lia_persona.yaml").exists()

    def test_delete_nonexistent_returns_404(self, client, cleanup_tenant_dir):
        response = client.delete(
            "/api/v1/admin/prompts/tenant-overrides/shared/lia_persona"
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Multi-tenancy fail-closed — cross-tenant isolation
# ---------------------------------------------------------------------------


class TestMultiTenancyIsolation:
    def test_cross_tenant_cannot_read_other_tenant_override(
        self, fake_admin, cleanup_tenant_dir
    ):
        """Tenant A cria override; Tenant B tenta GET — espera 404 (isolated)."""
        tenant_a = f"tenant-a-{uuid4().hex[:8]}"
        tenant_b = f"tenant-b-{uuid4().hex[:8]}"

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        app.dependency_overrides[require_admin] = lambda: fake_admin
        app.dependency_overrides[require_company_id] = lambda: tenant_a

        client_a = TestClient(app)
        put_resp = client_a.put(
            "/api/v1/admin/prompts/tenant-overrides/shared/lia_persona",
            json={"content": VALID_YAML},
        )
        assert put_resp.status_code == 200

        # Switch tenant
        app.dependency_overrides[require_company_id] = lambda: tenant_b
        client_b = TestClient(app)
        get_resp = client_b.get(
            "/api/v1/admin/prompts/tenant-overrides/shared/lia_persona"
        )
        assert get_resp.status_code == 404, (
            f"Multi-tenancy break — tenant B leu override de tenant A: {get_resp.text}"
        )

        # Cleanup tenant A
        from app.shared.prompts.loader import TENANTS_DIR

        for t in (tenant_a, tenant_b):
            d = TENANTS_DIR / t
            if d.exists():
                shutil.rmtree(d)
            PromptLoader.invalidate_cache(tenant_id=t)
        app.dependency_overrides.clear()
