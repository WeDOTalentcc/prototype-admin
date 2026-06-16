"""
Tests for WorkOS SSO/SCIM integration endpoints.
"""
import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.workos_models import (
    CompanyWorkOSConfig,
    WorkOSGroup,
)
from app.core.database import get_db
from app.main import app

INTERNAL_AUTH_HEADER = {"X-Internal-Auth": "test-secret"}


@pytest.fixture
def mock_internal_secret():
    """Mock the internal API secret for testing."""
    with patch('app.api.v1.workos.INTERNAL_API_SECRET', 'test-secret'):
        yield


@pytest.fixture
async def test_client(db_session: AsyncSession, mock_internal_secret):
    """Create test client with database dependency override."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestWorkOSSyncUser:
    """Tests for /api/v1/auth/workos/sync-user endpoint."""

    async def test_sync_new_user(self, test_client: AsyncClient):
        """Test creating a new user via SSO sync."""
        response = await test_client.post(
            "/api/v1/auth/workos/sync-user",
            json={
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                "workos_id": f"user_{uuid.uuid4().hex}",
                "first_name": "Test",
                "last_name": "User",
                "organization_id": "org_123",
                "connection_type": "GoogleOAuth"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_new_user"]
        assert "workos_id" in data

    async def test_sync_existing_user(self, test_client: AsyncClient):
        """Test syncing an existing user updates their last login."""
        workos_id = f"user_{uuid.uuid4().hex}"
        email = f"existing_{uuid.uuid4().hex[:8]}@example.com"
        
        response1 = await test_client.post(
            "/api/v1/auth/workos/sync-user",
            json={
                "email": email,
                "workos_id": workos_id,
                "first_name": "Existing",
                "last_name": "User"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        assert response1.status_code == 200
        assert response1.json()["is_new_user"]
        
        response2 = await test_client.post(
            "/api/v1/auth/workos/sync-user",
            json={
                "email": email,
                "workos_id": workos_id,
                "first_name": "Existing",
                "last_name": "User"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        assert response2.status_code == 200
        assert not response2.json()["is_new_user"]

    async def test_unauthorized_without_header(self, test_client: AsyncClient):
        """Test that requests without auth header are rejected."""
        response = await test_client.post(
            "/api/v1/auth/workos/sync-user",
            json={"email": "test@example.com", "workos_id": "user_123"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestSCIMUserEndpoints:
    """Tests for SCIM user lifecycle endpoints."""

    async def test_scim_user_created(self, test_client: AsyncClient):
        """Test SCIM user provisioning."""
        response = await test_client.post(
            "/api/v1/workos/users/created",
            json={
                "workos_id": f"user_{uuid.uuid4().hex}",
                "email": f"scim_{uuid.uuid4().hex[:8]}@example.com",
                "first_name": "SCIM",
                "last_name": "User",
                "directory_id": "dir_123",
                "state": "active"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["action"] == "created"

    async def test_scim_user_updated(self, test_client: AsyncClient):
        """Test SCIM user update."""
        workos_id = f"user_{uuid.uuid4().hex}"
        
        await test_client.post(
            "/api/v1/workos/users/created",
            json={
                "workos_id": workos_id,
                "email": f"update_{uuid.uuid4().hex[:8]}@example.com",
                "first_name": "Original",
                "last_name": "Name"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        response = await test_client.post(
            "/api/v1/workos/users/updated",
            json={
                "workos_id": workos_id,
                "first_name": "Updated",
                "last_name": "Name"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        assert response.status_code == 200
        assert response.json()["success"]

    async def test_scim_user_deleted(self, test_client: AsyncClient):
        """Test SCIM user deactivation (soft delete)."""
        workos_id = f"user_{uuid.uuid4().hex}"
        
        await test_client.post(
            "/api/v1/workos/users/created",
            json={
                "workos_id": workos_id,
                "email": f"delete_{uuid.uuid4().hex[:8]}@example.com"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        response = await test_client.post(
            "/api/v1/workos/users/deleted",
            json={"workos_id": workos_id},
            headers=INTERNAL_AUTH_HEADER
        )
        assert response.status_code == 200
        assert response.json()["success"]
        assert response.json()["message"] == "User deactivated successfully"


@pytest.mark.asyncio
class TestSCIMGroupEndpoints:
    """Tests for SCIM group endpoints."""

    async def test_scim_group_created(self, test_client: AsyncClient):
        """Test SCIM group creation."""
        response = await test_client.post(
            "/api/v1/workos/groups/created",
            json={
                "workos_id": f"group_{uuid.uuid4().hex}",
                "name": "Test Group",
                "directory_id": "dir_123"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["action"] == "created"

    async def test_scim_group_deleted(self, test_client: AsyncClient):
        """Test SCIM group soft deletion."""
        workos_id = f"group_{uuid.uuid4().hex}"
        
        await test_client.post(
            "/api/v1/workos/groups/created",
            json={"workos_id": workos_id, "name": "Delete Test Group"},
            headers=INTERNAL_AUTH_HEADER
        )
        
        response = await test_client.post(
            "/api/v1/workos/groups/deleted",
            json={"workos_id": workos_id, "name": "Delete Test Group"},
            headers=INTERNAL_AUTH_HEADER
        )
        assert response.status_code == 200
        assert response.json()["success"]


@pytest.mark.asyncio
class TestAdminEndpoints:
    """Tests for SSO Admin endpoints."""

    async def test_get_sso_status(self, test_client: AsyncClient):
        """Test getting SSO/SCIM status."""
        response = await test_client.get(
            "/api/v1/workos/admin/status?company_id=demo_company",
            headers=INTERNAL_AUTH_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        assert "sso_enabled" in data
        assert "scim_enabled" in data
        assert "sso_users_count" in data
        assert "groups_count" in data

    async def test_get_groups(self, test_client: AsyncClient):
        """Test getting WorkOS groups."""
        response = await test_client.get(
            "/api/v1/workos/admin/groups?company_id=demo_company",
            headers=INTERNAL_AUTH_HEADER
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_audit_logs(self, test_client: AsyncClient):
        """Test getting audit logs."""
        response = await test_client.get(
            "/api/v1/workos/admin/audit-logs?company_id=demo_company",
            headers=INTERNAL_AUTH_HEADER
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_sso_users(self, test_client: AsyncClient):
        """Test getting SSO/SCIM users."""
        response = await test_client.get(
            "/api/v1/workos/admin/users?company_id=demo_company",
            headers=INTERNAL_AUTH_HEADER
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
class TestCrossTenantIsolation:
    """Cross-tenant isolation regression tests.
    
    These tests verify that tenant isolation is properly enforced:
    - Company A cannot see Company B's groups
    - Company A cannot set role mappings for Company B's groups
    - Status endpoint only counts groups from the company's directory
    """

    async def _create_company_config(
        self, 
        db_session: AsyncSession, 
        company_id: str, 
        directory_id: str
    ) -> CompanyWorkOSConfig:
        """Helper to create a company WorkOS config."""
        config = CompanyWorkOSConfig(
            company_id=company_id,
            workos_directory_id=directory_id,
            sso_enabled=True,
            scim_enabled=True
        )
        db_session.add(config)
        await db_session.flush()
        return config

    async def _create_group(
        self, 
        db_session: AsyncSession, 
        workos_id: str, 
        name: str, 
        directory_id: str
    ) -> WorkOSGroup:
        """Helper to create a WorkOS group."""
        group = WorkOSGroup(
            workos_id=workos_id,
            name=name,
            directory_id=directory_id,
            is_active=True
        )
        db_session.add(group)
        await db_session.flush()
        return group

    async def test_cross_tenant_groups_isolation(
        self, 
        test_client: AsyncClient, 
        db_session: AsyncSession
    ):
        """Test that companies cannot access other company's groups.
        
        Creates two companies with different directories and verifies
        that each company only sees groups from their own directory.
        """
        company_a_id = f"company_a_{uuid.uuid4().hex[:8]}"
        company_b_id = f"company_b_{uuid.uuid4().hex[:8]}"
        dir_a_id = f"dir_a_{uuid.uuid4().hex[:8]}"
        dir_b_id = f"dir_b_{uuid.uuid4().hex[:8]}"
        
        await self._create_company_config(db_session, company_a_id, dir_a_id)
        await self._create_company_config(db_session, company_b_id, dir_b_id)
        
        await self._create_group(
            db_session, 
            f"group_a1_{uuid.uuid4().hex}", 
            "Company A Group 1", 
            dir_a_id
        )
        await self._create_group(
            db_session, 
            f"group_a2_{uuid.uuid4().hex}", 
            "Company A Group 2", 
            dir_a_id
        )
        await self._create_group(
            db_session, 
            f"group_b1_{uuid.uuid4().hex}", 
            "Company B Group 1", 
            dir_b_id
        )
        
        await db_session.flush()
        
        response_a = await test_client.get(
            f"/api/v1/workos/admin/groups?company_id={company_a_id}",
            headers=INTERNAL_AUTH_HEADER
        )
        assert response_a.status_code == 200
        groups_a = response_a.json()
        
        assert len(groups_a) == 2
        group_names_a = {g["name"] for g in groups_a}
        assert "Company A Group 1" in group_names_a
        assert "Company A Group 2" in group_names_a
        assert "Company B Group 1" not in group_names_a
        
        response_b = await test_client.get(
            f"/api/v1/workos/admin/groups?company_id={company_b_id}",
            headers=INTERNAL_AUTH_HEADER
        )
        assert response_b.status_code == 200
        groups_b = response_b.json()
        
        assert len(groups_b) == 1
        assert groups_b[0]["name"] == "Company B Group 1"

    async def test_cross_tenant_role_mapping_blocked(
        self, 
        test_client: AsyncClient, 
        db_session: AsyncSession
    ):
        """Test that companies cannot set role mappings for other company's groups.
        
        Creates Company A with directory A and a group in directory B.
        Verifies that Company A cannot set a role mapping for the group
        in directory B (receives 403 response).
        """
        company_a_id = f"company_a_{uuid.uuid4().hex[:8]}"
        dir_a_id = f"dir_a_{uuid.uuid4().hex[:8]}"
        dir_b_id = f"dir_b_{uuid.uuid4().hex[:8]}"
        
        await self._create_company_config(db_session, company_a_id, dir_a_id)
        
        group_b = await self._create_group(
            db_session, 
            f"group_b_{uuid.uuid4().hex}", 
            "Company B Group", 
            dir_b_id
        )
        
        await db_session.flush()
        
        response = await test_client.post(
            f"/api/v1/workos/admin/groups/{group_b.id}/role-mapping?company_id={company_a_id}",
            json={"role": "admin", "permissions": ["read", "write"]},
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 403
        assert "does not belong to your directory" in response.json()["message"]

    async def test_cross_tenant_status_counts_own_groups_only(
        self, 
        test_client: AsyncClient, 
        db_session: AsyncSession
    ):
        """Test that status endpoint only counts groups from company's directory.
        
        Creates two companies with different directories and groups.
        Verifies that each company's status endpoint only counts
        their own groups.
        """
        company_a_id = f"company_a_{uuid.uuid4().hex[:8]}"
        company_b_id = f"company_b_{uuid.uuid4().hex[:8]}"
        dir_a_id = f"dir_a_{uuid.uuid4().hex[:8]}"
        dir_b_id = f"dir_b_{uuid.uuid4().hex[:8]}"
        
        await self._create_company_config(db_session, company_a_id, dir_a_id)
        await self._create_company_config(db_session, company_b_id, dir_b_id)
        
        await self._create_group(db_session, f"group_a1_{uuid.uuid4().hex}", "Group A1", dir_a_id)
        await self._create_group(db_session, f"group_a2_{uuid.uuid4().hex}", "Group A2", dir_a_id)
        await self._create_group(db_session, f"group_a3_{uuid.uuid4().hex}", "Group A3", dir_a_id)
        await self._create_group(db_session, f"group_b1_{uuid.uuid4().hex}", "Group B1", dir_b_id)
        
        await db_session.flush()
        
        response_a = await test_client.get(
            f"/api/v1/workos/admin/status?company_id={company_a_id}",
            headers=INTERNAL_AUTH_HEADER
        )
        assert response_a.status_code == 200
        status_a = response_a.json()
        assert status_a["groups_count"] == 3
        
        response_b = await test_client.get(
            f"/api/v1/workos/admin/status?company_id={company_b_id}",
            headers=INTERNAL_AUTH_HEADER
        )
        assert response_b.status_code == 200
        status_b = response_b.json()
        assert status_b["groups_count"] == 1

    async def test_company_without_config_gets_empty_groups(
        self, 
        test_client: AsyncClient
    ):
        """Test that companies without WorkOS config get empty groups array.
        
        Verifies that a company without a configured directory ID
        receives an empty array when querying groups (not another 
        company's groups).
        """
        unconfigured_company_id = f"unconfigured_{uuid.uuid4().hex[:8]}"
        
        response = await test_client.get(
            f"/api/v1/workos/admin/groups?company_id={unconfigured_company_id}",
            headers=INTERNAL_AUTH_HEADER
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_company_without_config_cannot_set_role_mapping(
        self, 
        test_client: AsyncClient, 
        db_session: AsyncSession
    ):
        """Test that companies without config cannot set role mappings.
        
        Creates a group and attempts to set a role mapping from a
        company without a WorkOS config. Should receive 403.
        """
        unconfigured_company_id = f"unconfigured_{uuid.uuid4().hex[:8]}"
        dir_id = f"dir_{uuid.uuid4().hex[:8]}"
        
        group = await self._create_group(
            db_session, 
            f"group_{uuid.uuid4().hex}", 
            "Test Group", 
            dir_id
        )
        await db_session.flush()
        
        response = await test_client.post(
            f"/api/v1/workos/admin/groups/{group.id}/role-mapping?company_id={unconfigured_company_id}",
            json={"role": "admin", "permissions": []},
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 403
        assert "no configured WorkOS directory" in response.json()["message"]


@pytest.mark.asyncio
class TestWorkOSClientOnboardingRobustness:
    """Robustness tests for WorkOS client onboarding.
    
    These tests verify that the create_client endpoint handles edge cases
    gracefully, particularly around the WorkOS config creation using
    INSERT ON CONFLICT DO NOTHING.
    """

    async def test_idempotent_workos_config_creation(
        self,
        db_session: AsyncSession
    ):
        """Test that WorkOS config creation is idempotent.
        
        Verifies that the INSERT ON CONFLICT DO NOTHING pattern allows
        multiple insert attempts for the same company_id without failing.
        This tests the robustness of concurrent client creation attempts.
        """
        from sqlalchemy import select, text
        
        client_id = str(uuid.uuid4())
        config_id_1 = str(uuid.uuid4())
        config_id_2 = str(uuid.uuid4())
        now = datetime.utcnow()
        
        insert_statement = text("""
            INSERT INTO company_workos_config (id, company_id, sso_enabled, scim_enabled, created_at, updated_at)
            VALUES (:id, :company_id, false, false, :created_at, :updated_at)
            ON CONFLICT (company_id) DO NOTHING
        """)
        
        await db_session.execute(
            insert_statement,
            {
                "id": config_id_1,
                "company_id": client_id,
                "created_at": now,
                "updated_at": now
            }
        )
        await db_session.commit()
        
        config_check_1 = await db_session.execute(
            select(CompanyWorkOSConfig).where(
                CompanyWorkOSConfig.company_id == client_id
            )
        )
        config_1 = config_check_1.scalar_one_or_none()
        assert config_1 is not None, "First WorkOS config creation should succeed"
        assert str(config_1.id) == config_id_1
        
        await db_session.execute(
            insert_statement,
            {
                "id": config_id_2,
                "company_id": client_id,
                "created_at": now,
                "updated_at": now
            }
        )
        await db_session.commit()
        
        config_check_2 = await db_session.execute(
            select(CompanyWorkOSConfig).where(
                CompanyWorkOSConfig.company_id == client_id
            )
        )
        all_configs = config_check_2.scalars().all()
        assert len(all_configs) == 1, "Second insert should be a no-op due to ON CONFLICT DO NOTHING"
        assert str(all_configs[0].id) == config_id_1, "First config ID should be retained"

    async def test_create_client_insert_failure_handling(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch
    ):
        """Test that insert failures during client creation are handled gracefully.
        
        Uses monkeypatch to simulate an IntegrityError during WorkOS config insert.
        Verifies that:
        1. The API returns 500 status code
        2. No orphaned client remains in the database after rollback
        """
        from sqlalchemy import select
        from sqlalchemy.exc import IntegrityError

        from app.models.client_account import ClientAccount
        
        original_execute = db_session.execute
        call_count = {"count": 0}
        
        async def mock_execute(statement, *args, **kwargs):
            call_count["count"] += 1
            
            if hasattr(statement, "text") and "INSERT INTO company_workos_config" in str(statement):
                raise IntegrityError("Simulated integrity error", None, None)
            
            return await original_execute(statement, *args, **kwargs)
        
        monkeypatch.setattr(db_session, "execute", mock_execute)
        
        client_data = {
            "name": f"Fail Test Company {uuid.uuid4().hex[:8]}",
            "status": "pending_setup",
            "plan_id": "starter",
            "user_limit": 10,
            "job_limit": 50,
            "ai_credits_monthly": 1000
        }
        
        headers = {
            "X-Company-ID": "admin-company",
            "X-User-ID": "admin-user",
            "X-User-Role": "admin"
        }
        
        response = await test_client.post(
            "/api/v1/clients",
            json=client_data,
            headers=headers
        )
        
        assert response.status_code == 500, "API should return 500 on WorkOS config insert failure"
        assert "Failed to create client" in response.json()["message"]
        
        client_check = await db_session.execute(
            select(ClientAccount).where(
                ClientAccount.name == client_data["name"]
            )
        )
        orphaned_client = client_check.scalar_one_or_none()
        assert orphaned_client is None, "No orphaned client should remain after failed WorkOS config creation"
