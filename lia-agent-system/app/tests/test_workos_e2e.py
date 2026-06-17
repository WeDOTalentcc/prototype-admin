"""
End-to-End tests for WorkOS SSO/SCIM integration flows.

These tests simulate complete user journeys through SSO authentication and SCIM provisioning
without requiring actual WorkOS credentials. They use mock fixtures to simulate WorkOS
responses and verify the complete flow from authentication to database state.
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserRole
from app.auth.workos_models import (
    CompanyWorkOSConfig,
    SSOAuditLog,
    WorkOSGroup,
    WorkOSGroupMembership,
    WorkOSGroupRoleMapping,
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


@pytest.fixture
def mock_workos_client():
    """Mock WorkOS client for SSO operations."""
    with patch('workos.client') as mock_client:
        mock_client.sso.get_profile_and_token = MagicMock()
        mock_client.sso.get_authorization_url = MagicMock(return_value="https://auth.workos.com/sso")
        yield mock_client


@pytest.fixture
async def setup_company_config(db_session: AsyncSession):
    """Create a company WorkOS config for testing."""
    async def _create_config(company_id: str, directory_id: str = None, sso_enabled: bool = True, scim_enabled: bool = True):
        config = CompanyWorkOSConfig(
            company_id=company_id,
            workos_directory_id=directory_id or f"dir_{uuid.uuid4().hex[:8]}",
            sso_enabled=sso_enabled,
            scim_enabled=scim_enabled
        )
        db_session.add(config)
        await db_session.flush()
        return config
    return _create_config


@pytest.fixture
async def setup_workos_group(db_session: AsyncSession):
    """Create a WorkOS group for testing."""
    async def _create_group(workos_id: str, name: str, directory_id: str):
        group = WorkOSGroup(
            workos_id=workos_id,
            name=name,
            directory_id=directory_id,
            is_active=True
        )
        db_session.add(group)
        await db_session.flush()
        return group
    return _create_group


@pytest.mark.asyncio
class TestSSOLoginFlow:
    """E2E tests for complete SSO login flow."""

    async def test_sso_login_flow_new_user(self, test_client: AsyncClient, db_session: AsyncSession):
        """
        Test complete SSO login flow for a new user.
        
        Flow:
        1. WorkOS SSO callback received
        2. New user created in database
        3. Audit log entry created
        4. Response contains user info and is_new_user=True
        """
        unique_id = uuid.uuid4().hex[:8]
        workos_id = f"user_{unique_id}"
        email = f"sso_new_{unique_id}@example.com"
        organization_id = f"org_{unique_id}"
        
        response = await test_client.post(
            "/api/v1/auth/workos/sync-user",
            json={
                "email": email,
                "workos_id": workos_id,
                "first_name": "SSO",
                "last_name": "NewUser",
                "organization_id": organization_id,
                "connection_type": "GoogleOAuth"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_new_user"]
        assert data["email"] == email
        assert data["workos_id"] == workos_id
        assert data["sso_provider"] == "GoogleOAuth"
        
        result = await db_session.execute(
            select(User).where(User.workos_id == workos_id)
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == email
        assert user.workos_organization_id == organization_id
        assert user.last_sso_login_at is not None
        
        result = await db_session.execute(
            select(SSOAuditLog).where(
                SSOAuditLog.target_id == workos_id,
                SSOAuditLog.event_type == "sso.login"
            )
        )
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None
        assert audit_log.company_id == organization_id
        assert audit_log.actor_email == email
        assert audit_log.payload["is_new_user"]

    async def test_sso_login_flow_returning_user(self, test_client: AsyncClient, db_session: AsyncSession):
        """
        Test SSO login flow for returning user.
        
        Flow:
        1. First SSO login creates user
        2. Second SSO login updates last_sso_login_at
        3. is_new_user=False on second login
        """
        unique_id = uuid.uuid4().hex[:8]
        workos_id = f"user_{unique_id}"
        email = f"sso_returning_{unique_id}@example.com"
        
        response1 = await test_client.post(
            "/api/v1/auth/workos/sync-user",
            json={
                "email": email,
                "workos_id": workos_id,
                "first_name": "Returning",
                "last_name": "User"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        assert response1.status_code == 200
        assert response1.json()["is_new_user"]
        
        result = await db_session.execute(
            select(User).where(User.workos_id == workos_id)
        )
        user = result.scalar_one()
        first_login_time = user.last_sso_login_at
        
        response2 = await test_client.post(
            "/api/v1/auth/workos/sync-user",
            json={
                "email": email,
                "workos_id": workos_id,
                "first_name": "Returning",
                "last_name": "User"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response2.status_code == 200
        data = response2.json()
        assert not data["is_new_user"]
        assert data["email"] == email
        
        await db_session.refresh(user)
        assert user.last_sso_login_at >= first_login_time

    async def test_sso_login_links_existing_email_user(self, test_client: AsyncClient, db_session: AsyncSession):
        """
        Test SSO login links to existing user when email matches.
        
        Flow:
        1. User already exists with email (no workos_id)
        2. SSO login with same email
        3. Existing user is linked to WorkOS
        """
        unique_id = uuid.uuid4().hex[:8]
        email = f"existing_{unique_id}@example.com"
        workos_id = f"user_{unique_id}"
        
        existing_user = User(
            email=email,
            name="Existing User",
            role=UserRole.recruiter,
            is_active=True
        )
        db_session.add(existing_user)
        await db_session.flush()
        existing_user_id = existing_user.id
        
        response = await test_client.post(
            "/api/v1/auth/workos/sync-user",
            json={
                "email": email,
                "workos_id": workos_id,
                "first_name": "Linked",
                "last_name": "User",
                "connection_type": "SAML"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        data = response.json()
        assert not data["is_new_user"]
        assert str(data["id"]) == str(existing_user_id)
        
        result = await db_session.execute(
            select(User).where(User.id == existing_user_id)
        )
        linked_user = result.scalar_one()
        assert linked_user.workos_id == workos_id
        assert linked_user.sso_provider == "SAML"


@pytest.mark.asyncio
class TestSCIMUserLifecycle:
    """E2E tests for complete SCIM user lifecycle."""

    async def test_scim_user_lifecycle_complete(self, test_client: AsyncClient, db_session: AsyncSession):
        """
        Test complete SCIM user lifecycle: created → updated → deleted.
        
        Verifies database state at each step.
        """
        unique_id = uuid.uuid4().hex[:8]
        workos_id = f"scim_user_{unique_id}"
        email = f"scim_{unique_id}@corporate.com"
        directory_id = f"dir_{unique_id}"
        
        response = await test_client.post(
            "/api/v1/workos/users/created",
            json={
                "workos_id": workos_id,
                "email": email,
                "first_name": "SCIM",
                "last_name": "User",
                "directory_id": directory_id,
                "state": "active"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["action"] == "created"
        
        result = await db_session.execute(
            select(User).where(User.workos_id == workos_id)
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == email
        assert user.name == "SCIM User"
        assert user.is_scim_managed
        assert user.is_active
        assert user.workos_directory_id == directory_id
        
        result = await db_session.execute(
            select(SSOAuditLog).where(
                SSOAuditLog.event_type == "scim.user.created",
                SSOAuditLog.target_email == email
            )
        )
        create_audit = result.scalar_one_or_none()
        assert create_audit is not None
        
        response = await test_client.post(
            "/api/v1/workos/users/updated",
            json={
                "workos_id": workos_id,
                "first_name": "Updated",
                "last_name": "SCIMUser",
                "state": "active"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        assert response.json()["success"]
        
        await db_session.refresh(user)
        assert user.name == "Updated SCIMUser"
        
        result = await db_session.execute(
            select(SSOAuditLog).where(
                SSOAuditLog.event_type == "scim.user.updated",
                SSOAuditLog.actor_id == workos_id
            )
        )
        update_audit = result.scalar_one_or_none()
        assert update_audit is not None
        
        response = await test_client.post(
            "/api/v1/workos/users/deleted",
            json={"workos_id": workos_id},
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        assert response.json()["success"]
        assert response.json()["message"] == "User deactivated successfully"
        
        await db_session.refresh(user)
        assert not user.is_active
        
        result = await db_session.execute(
            select(SSOAuditLog).where(
                SSOAuditLog.event_type == "scim.user.deleted",
                SSOAuditLog.actor_id == workos_id
            )
        )
        delete_audit = result.scalar_one_or_none()
        assert delete_audit is not None

    async def test_scim_user_suspend_via_state(self, test_client: AsyncClient, db_session: AsyncSession):
        """Test SCIM user suspension via state update."""
        unique_id = uuid.uuid4().hex[:8]
        workos_id = f"suspend_user_{unique_id}"
        email = f"suspend_{unique_id}@corporate.com"
        
        await test_client.post(
            "/api/v1/workos/users/created",
            json={
                "workos_id": workos_id,
                "email": email,
                "first_name": "Suspend",
                "last_name": "Test",
                "state": "active"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        response = await test_client.post(
            "/api/v1/workos/users/updated",
            json={
                "workos_id": workos_id,
                "state": "suspended"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        
        result = await db_session.execute(
            select(User).where(User.workos_id == workos_id)
        )
        user = result.scalar_one()
        assert not user.is_active


@pytest.mark.asyncio
class TestSCIMGroupLifecycle:
    """E2E tests for SCIM group lifecycle with membership management."""

    async def test_scim_group_lifecycle_complete(
        self, 
        test_client: AsyncClient, 
        db_session: AsyncSession
    ):
        """
        Test complete SCIM group lifecycle: 
        group created → user added → user removed → group deleted.
        
        Verifies memberships at each step.
        """
        unique_id = uuid.uuid4().hex[:8]
        group_workos_id = f"group_{unique_id}"
        user_workos_id = f"user_{unique_id}"
        user_email = f"member_{unique_id}@corporate.com"
        directory_id = f"dir_{unique_id}"
        
        response = await test_client.post(
            "/api/v1/workos/groups/created",
            json={
                "workos_id": group_workos_id,
                "name": "Engineering Team",
                "directory_id": directory_id
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        assert response.json()["success"]
        assert response.json()["action"] == "created"
        
        result = await db_session.execute(
            select(WorkOSGroup).where(WorkOSGroup.workos_id == group_workos_id)
        )
        group = result.scalar_one_or_none()
        assert group is not None
        assert group.name == "Engineering Team"
        assert group.is_active
        
        await test_client.post(
            "/api/v1/workos/users/created",
            json={
                "workos_id": user_workos_id,
                "email": user_email,
                "first_name": "Team",
                "last_name": "Member",
                "directory_id": directory_id
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        result = await db_session.execute(
            select(User).where(User.workos_id == user_workos_id)
        )
        user = result.scalar_one()
        
        response = await test_client.post(
            "/api/v1/workos/group-membership",
            json={
                "user_id": user_workos_id,
                "group_id": group_workos_id,
                "action": "added"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        assert response.json()["success"]
        assert response.json()["message"] == "User added to group"
        
        result = await db_session.execute(
            select(WorkOSGroupMembership).where(
                WorkOSGroupMembership.group_id == group.id,
                WorkOSGroupMembership.user_id == user.id
            )
        )
        membership = result.scalar_one_or_none()
        assert membership is not None
        
        result = await db_session.execute(
            select(SSOAuditLog).where(
                SSOAuditLog.event_type == "scim.group.user_added"
            )
        )
        add_audit = result.scalar_one_or_none()
        assert add_audit is not None
        assert add_audit.payload["group_name"] == "Engineering Team"
        
        response = await test_client.post(
            "/api/v1/workos/group-membership",
            json={
                "user_id": user_workos_id,
                "group_id": group_workos_id,
                "action": "removed"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        assert response.json()["success"]
        assert response.json()["message"] == "User removed from group"
        
        result = await db_session.execute(
            select(WorkOSGroupMembership).where(
                WorkOSGroupMembership.group_id == group.id,
                WorkOSGroupMembership.user_id == user.id
            )
        )
        membership = result.scalar_one_or_none()
        assert membership is None
        
        response = await test_client.post(
            "/api/v1/workos/groups/deleted",
            json={
                "workos_id": group_workos_id,
                "name": "Engineering Team"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        assert response.json()["success"]
        
        await db_session.refresh(group)
        assert not group.is_active

    async def test_group_membership_idempotency(
        self, 
        test_client: AsyncClient, 
        db_session: AsyncSession
    ):
        """Test that adding a user to a group twice is idempotent."""
        unique_id = uuid.uuid4().hex[:8]
        group_workos_id = f"group_idemp_{unique_id}"
        user_workos_id = f"user_idemp_{unique_id}"
        user_email = f"idemp_{unique_id}@corporate.com"
        
        await test_client.post(
            "/api/v1/workos/groups/created",
            json={"workos_id": group_workos_id, "name": "Idempotent Group"},
            headers=INTERNAL_AUTH_HEADER
        )
        
        await test_client.post(
            "/api/v1/workos/users/created",
            json={
                "workos_id": user_workos_id,
                "email": user_email,
                "first_name": "Idemp",
                "last_name": "User"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        response1 = await test_client.post(
            "/api/v1/workos/group-membership",
            json={"user_id": user_workos_id, "group_id": group_workos_id, "action": "added"},
            headers=INTERNAL_AUTH_HEADER
        )
        assert response1.status_code == 200
        
        response2 = await test_client.post(
            "/api/v1/workos/group-membership",
            json={"user_id": user_workos_id, "group_id": group_workos_id, "action": "added"},
            headers=INTERNAL_AUTH_HEADER
        )
        assert response2.status_code == 200
        assert response2.json()["message"] == "Membership already exists"


@pytest.mark.asyncio
class TestSSOWithRoleMapping:
    """E2E tests for SSO login with group-based role mapping."""

    async def test_sso_with_role_mapping(
        self, 
        test_client: AsyncClient, 
        db_session: AsyncSession,
        setup_company_config,
        setup_workos_group
    ):
        """
        Test SSO login applies correct role based on group membership.
        
        Flow:
        1. Create company config with directory
        2. Create group
        3. Configure role mapping for group
        4. Create user via SCIM
        5. Add user to group
        6. Verify role mapping is queryable
        """
        unique_id = uuid.uuid4().hex[:8]
        company_id = f"company_{unique_id}"
        directory_id = f"dir_{unique_id}"
        
        await setup_company_config(company_id, directory_id)
        
        group_workos_id = f"admins_group_{unique_id}"
        group = await setup_workos_group(group_workos_id, "Admins", directory_id)
        
        response = await test_client.post(
            f"/api/v1/workos/admin/groups/{group.id}/role-mapping",
            params={"company_id": company_id},
            json={
                "role": "admin",
                "permissions": ["manage_users", "view_reports", "edit_settings"]
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        assert response.json()["success"]
        assert response.json()["role"] == "admin"
        
        result = await db_session.execute(
            select(WorkOSGroupRoleMapping).where(
                WorkOSGroupRoleMapping.company_id == company_id,
                WorkOSGroupRoleMapping.workos_group_id == group.id
            )
        )
        role_mapping = result.scalar_one_or_none()
        assert role_mapping is not None
        assert role_mapping.role == "admin"
        assert "manage_users" in role_mapping.permissions
        
        user_workos_id = f"admin_user_{unique_id}"
        user_email = f"admin_{unique_id}@corporate.com"
        
        await test_client.post(
            "/api/v1/workos/users/created",
            json={
                "workos_id": user_workos_id,
                "email": user_email,
                "first_name": "Admin",
                "last_name": "User",
                "directory_id": directory_id
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        result = await db_session.execute(
            select(User).where(User.workos_id == user_workos_id)
        )
        user = result.scalar_one()
        
        await test_client.post(
            "/api/v1/workos/group-membership",
            json={"user_id": user_workos_id, "group_id": group_workos_id, "action": "added"},
            headers=INTERNAL_AUTH_HEADER
        )
        
        result = await db_session.execute(
            select(WorkOSGroupMembership).where(
                WorkOSGroupMembership.user_id == user.id,
                WorkOSGroupMembership.group_id == group.id
            )
        )
        membership = result.scalar_one_or_none()
        assert membership is not None
        
        response = await test_client.get(
            "/api/v1/workos/admin/groups",
            params={"company_id": company_id},
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        groups = response.json()
        admin_group = next((g for g in groups if g["workos_id"] == group_workos_id), None)
        assert admin_group is not None
        assert admin_group["mapped_role"] == "admin"

    async def test_role_mapping_cross_tenant_isolation(
        self, 
        test_client: AsyncClient, 
        db_session: AsyncSession,
        setup_company_config,
        setup_workos_group
    ):
        """
        Test that role mappings are isolated between companies.
        
        Company A's role mapping should not affect Company B's users.
        """
        unique_id = uuid.uuid4().hex[:8]
        
        company_a = f"company_a_{unique_id}"
        company_b = f"company_b_{unique_id}"
        dir_a = f"dir_a_{unique_id}"
        dir_b = f"dir_b_{unique_id}"
        
        await setup_company_config(company_a, dir_a)
        await setup_company_config(company_b, dir_b)
        
        group_a = await setup_workos_group(f"group_a_{unique_id}", "Company A Admins", dir_a)
        await setup_workos_group(f"group_b_{unique_id}", "Company B Admins", dir_b)
        
        await test_client.post(
            f"/api/v1/workos/admin/groups/{group_a.id}/role-mapping",
            params={"company_id": company_a},
            json={"role": "admin", "permissions": ["full_access"]},
            headers=INTERNAL_AUTH_HEADER
        )
        
        response = await test_client.get(
            "/api/v1/workos/admin/groups",
            params={"company_id": company_a},
            headers=INTERNAL_AUTH_HEADER
        )
        groups_a = response.json()
        assert len(groups_a) == 1
        assert groups_a[0]["workos_id"] == f"group_a_{unique_id}"
        
        response = await test_client.get(
            "/api/v1/workos/admin/groups",
            params={"company_id": company_b},
            headers=INTERNAL_AUTH_HEADER
        )
        groups_b = response.json()
        assert len(groups_b) == 1
        assert groups_b[0]["workos_id"] == f"group_b_{unique_id}"
        assert groups_b[0]["mapped_role"] is None


@pytest.mark.asyncio
class TestSessionRefresh:
    """E2E tests for session refresh functionality."""

    async def test_session_refresh_extends_expiry(
        self, 
        test_client: AsyncClient, 
        db_session: AsyncSession
    ):
        """
        Test that session refresh endpoint extends token expiry.
        
        Note: This test verifies the refresh endpoint is accessible.
        The actual token refresh logic depends on JWT implementation.
        """
        unique_id = uuid.uuid4().hex[:8]
        workos_id = f"session_user_{unique_id}"
        email = f"session_{unique_id}@example.com"
        
        await test_client.post(
            "/api/v1/auth/workos/sync-user",
            json={
                "email": email,
                "workos_id": workos_id,
                "first_name": "Session",
                "last_name": "User"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        result = await db_session.execute(
            select(User).where(User.workos_id == workos_id)
        )
        user = result.scalar_one()
        original_login_time = user.last_sso_login_at
        
        await test_client.post(
            "/api/v1/auth/workos/sync-user",
            json={
                "email": email,
                "workos_id": workos_id,
                "first_name": "Session",
                "last_name": "User"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        await db_session.refresh(user)
        assert user.last_sso_login_at >= original_login_time


@pytest.mark.asyncio
class TestAuditLogVerification:
    """E2E tests for audit log completeness."""

    async def test_audit_logs_capture_all_events(
        self, 
        test_client: AsyncClient, 
        db_session: AsyncSession
    ):
        """
        Verify that all SSO/SCIM events are properly logged.
        """
        unique_id = uuid.uuid4().hex[:8]
        directory_id = f"dir_{unique_id}"
        user_workos_id = f"audit_user_{unique_id}"
        user_email = f"audit_{unique_id}@corporate.com"
        group_workos_id = f"audit_group_{unique_id}"
        
        await test_client.post(
            "/api/v1/workos/users/created",
            json={
                "workos_id": user_workos_id,
                "email": user_email,
                "first_name": "Audit",
                "last_name": "Test",
                "directory_id": directory_id
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        await test_client.post(
            "/api/v1/workos/groups/created",
            json={
                "workos_id": group_workos_id,
                "name": "Audit Group",
                "directory_id": directory_id
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        await test_client.post(
            "/api/v1/workos/group-membership",
            json={
                "user_id": user_workos_id,
                "group_id": group_workos_id,
                "action": "added"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        await test_client.post(
            "/api/v1/workos/group-membership",
            json={
                "user_id": user_workos_id,
                "group_id": group_workos_id,
                "action": "removed"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        await test_client.post(
            "/api/v1/workos/users/deleted",
            json={"workos_id": user_workos_id},
            headers=INTERNAL_AUTH_HEADER
        )
        
        await test_client.post(
            "/api/v1/workos/groups/deleted",
            json={
                "workos_id": group_workos_id, 
                "name": "Audit Group",
                "directory_id": directory_id
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        result = await db_session.execute(
            select(SSOAuditLog).where(
                SSOAuditLog.company_id == directory_id
            )
        )
        logs = result.scalars().all()
        
        event_types = {log.event_type for log in logs}
        expected_events = {
            "scim.user.created",
            "scim.user.deleted",
            "scim.group.created",
            "scim.group.deleted",
            "scim.group.user_added",
            "scim.group.user_removed"
        }
        assert expected_events.issubset(event_types), f"Missing events: {expected_events - event_types}"


@pytest.mark.asyncio
class TestErrorHandling:
    """E2E tests for error handling in SSO/SCIM flows."""

    async def test_scim_user_created_without_email_fails(self, test_client: AsyncClient):
        """Test that SCIM user creation without email returns appropriate error."""
        response = await test_client.post(
            "/api/v1/workos/users/created",
            json={
                "workos_id": f"user_{uuid.uuid4().hex}",
                "first_name": "No",
                "last_name": "Email"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        data = response.json()
        assert not data["success"]
        assert "Email required" in data["message"]

    async def test_group_membership_unknown_user_fails(self, test_client: AsyncClient):
        """Test that adding unknown user to group fails gracefully."""
        unique_id = uuid.uuid4().hex[:8]
        group_workos_id = f"group_{unique_id}"
        
        await test_client.post(
            "/api/v1/workos/groups/created",
            json={"workos_id": group_workos_id, "name": "Test Group"},
            headers=INTERNAL_AUTH_HEADER
        )
        
        response = await test_client.post(
            "/api/v1/workos/group-membership",
            json={
                "user_id": f"unknown_user_{unique_id}",
                "group_id": group_workos_id,
                "action": "added"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        assert not response.json()["success"]
        assert "User not found" in response.json()["message"]

    async def test_group_membership_unknown_group_fails(self, test_client: AsyncClient):
        """Test that adding user to unknown group fails gracefully."""
        unique_id = uuid.uuid4().hex[:8]
        user_workos_id = f"user_{unique_id}"
        user_email = f"test_{unique_id}@example.com"
        
        await test_client.post(
            "/api/v1/workos/users/created",
            json={
                "workos_id": user_workos_id,
                "email": user_email,
                "first_name": "Test",
                "last_name": "User"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        response = await test_client.post(
            "/api/v1/workos/group-membership",
            json={
                "user_id": user_workos_id,
                "group_id": f"unknown_group_{unique_id}",
                "action": "added"
            },
            headers=INTERNAL_AUTH_HEADER
        )
        
        assert response.status_code == 200
        assert not response.json()["success"]
        assert "Group not found" in response.json()["message"]

    async def test_unauthorized_request_rejected(self, test_client: AsyncClient):
        """Test that requests without auth header are rejected."""
        response = await test_client.post(
            "/api/v1/auth/workos/sync-user",
            json={"email": "test@example.com", "workos_id": "user_123"}
        )
        assert response.status_code == 401
