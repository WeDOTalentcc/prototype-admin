"""
Integration tests for Feature Flags API endpoints.

Uses httpx TestClient to test real API behavior.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from uuid import uuid4

from app.main import app


@pytest.mark.asyncio
class TestFeatureFlagsAPI:
    """Integration tests for feature flag endpoints."""
    
    async def test_get_all_flags_returns_defaults(self):
        """GET /feature-flags should return all default flags."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/lia/feature-flags")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "flags" in data
        assert len(data["flags"]) >= 8
        
        flag_keys = [f["flag_key"] for f in data["flags"]]
        assert "learning_hub_enabled" in flag_keys
        assert "outcome_learning_enabled" in flag_keys
        assert "skills_deduplication_enabled" in flag_keys
    
    async def test_check_flag_returns_default(self):
        """GET /feature-flags/check/{key} should return default value."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/lia/feature-flags/check/learning_hub_enabled")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["flag_key"] == "learning_hub_enabled"
        assert "is_enabled" in data
    
    async def test_check_unknown_flag_returns_false(self):
        """Unknown flags should return is_enabled=false."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/lia/feature-flags/check/unknown_flag_xyz")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["flag_key"] == "unknown_flag_xyz"
        assert data["is_enabled"] == False
    
    async def test_set_flag_creates_override(self):
        """POST /feature-flags/set should create a flag override."""
        company_id = str(uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/lia/feature-flags/set",
                json={
                    "flag_key": "test_integration_flag",
                    "is_enabled": True,
                    "company_id": company_id,
                    "rollout_percentage": 50,
                    "description": "Integration test flag"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["flag_key"] == "test_integration_flag"
        assert data["is_enabled"] == True
        assert data["rollout_percentage"] == 50
    
    async def test_set_flag_updates_existing(self):
        """Setting an existing flag should update it."""
        company_id = str(uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/api/v1/lia/feature-flags/set",
                json={
                    "flag_key": "update_test_flag",
                    "is_enabled": True,
                    "company_id": company_id
                }
            )
            
            response = await client.post(
                "/api/v1/lia/feature-flags/set",
                json={
                    "flag_key": "update_test_flag",
                    "is_enabled": False,
                    "company_id": company_id
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["is_enabled"] == False
    
    async def test_company_flag_check_with_company_id(self):
        """Checking flag with company_id should use company-specific override."""
        company_id = str(uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/api/v1/lia/feature-flags/set",
                json={
                    "flag_key": "company_specific_flag",
                    "is_enabled": False,
                    "company_id": company_id
                }
            )
            
            response = await client.get(
                f"/api/v1/lia/feature-flags/check/company_specific_flag",
                params={"company_id": company_id}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_enabled"] == False


@pytest.mark.asyncio
class TestLearningDashboardAPI:
    """Integration tests for learning dashboard endpoint."""
    
    async def test_dashboard_returns_structure(self):
        """POST /learning/dashboard should return expected structure."""
        company_id = str(uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/lia/learning/dashboard",
                json={"company_id": company_id}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "stage_analytics" in data
        assert "outcome_insights" in data
        assert "learning_health" in data
        
        assert "score" in data["learning_health"]
        assert "status" in data["learning_health"]


@pytest.mark.asyncio
class TestStillsDeduplicationAPI:
    """Integration tests for skills deduplication endpoint."""
    
    async def test_skills_deduplicated_returns_list(self):
        """POST /learning/skills-deduplicated should return skills list."""
        company_id = str(uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/lia/learning/skills-deduplicated",
                json={
                    "company_id": company_id,
                    "role": "Developer",
                    "exclude_already_selected": ["Python"]
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "skills" in data
        assert isinstance(data["skills"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
