"""
API-level integration tests for CompanyHiringPolicy endpoints.

Uses httpx AsyncClient + FastAPI TestClient pattern to test:
- GET /{company_id} → returns defaults when no policy exists
- PUT /{company_id} → creates/updates full policy (upsert)
- PATCH /{company_id}/block → updates a single block with merge
- GET /{company_id}/progress → returns progress and blocks_completed
- Invalid block returns 400
"""
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.company_hiring_policy import (
    AUTOMATION_RULES_DEFAULTS,
    COMMUNICATION_RULES_DEFAULTS,
    PIPELINE_RULES_DEFAULTS,
    SCHEDULING_RULES_DEFAULTS,
    SCREENING_RULES_DEFAULTS,
    CompanyHiringPolicy,
)


def _mock_policy(company_id: str, **overrides):
    defaults = {
        "id": uuid.uuid4(),
        "company_id": company_id,
        "pipeline_rules": PIPELINE_RULES_DEFAULTS.copy(),
        "scheduling_rules": SCHEDULING_RULES_DEFAULTS.copy(),
        "communication_rules": COMMUNICATION_RULES_DEFAULTS.copy(),
        "screening_rules": SCREENING_RULES_DEFAULTS.copy(),
        "automation_rules": AUTOMATION_RULES_DEFAULTS.copy(),
        "pipeline_templates": [],
        "learned_patterns": [],
        "answered_questions": [],
        "setup_progress": 0,
        "setup_completed_at": None,
        "created_by": None,
        "updated_by": None,
        "created_at": None,
        "updated_at": None,
    }
    defaults.update(overrides)
    policy = CompanyHiringPolicy(**defaults)
    return policy


class MockResult:
    def __init__(self, val):
        self._val = val
    def scalar_one_or_none(self):
        return self._val


class MockSession:
    def __init__(self, policy=None):
        self._policy = policy
        self.added = []

    async def execute(self, stmt):
        return MockResult(self._policy)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def close(self):
        pass


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
class TestGetPolicyAPI:
    """GET /api/v1/company-hiring-policy/{company_id}"""

    async def test_get_returns_defaults_when_no_policy(self):
        mock_db = MockSession(policy=None)

        async def override_get_db():
            yield mock_db

        from app.core.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/api/v1/company-hiring-policy/test-company")
            assert resp.status_code == 200
            data = resp.json()
            assert data["company_id"] == "test-company"
            assert data["pipeline_rules"] == PIPELINE_RULES_DEFAULTS
            assert data["scheduling_rules"] == SCHEDULING_RULES_DEFAULTS
            assert data["setup_progress"] == 0
        finally:
            app.dependency_overrides.clear()

    async def test_get_returns_existing_policy(self):
        policy = _mock_policy("acme", pipeline_rules={"min_interviews_before_offer": 5})
        mock_db = MockSession(policy=policy)

        async def override_get_db():
            yield mock_db

        from app.core.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/api/v1/company-hiring-policy/acme")
            assert resp.status_code == 200
            data = resp.json()
            assert data["pipeline_rules"]["min_interviews_before_offer"] == 5
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestUpsertPolicyAPI:
    """PUT /api/v1/company-hiring-policy/{company_id}"""

    async def test_put_creates_new_policy(self):
        mock_db = MockSession(policy=None)

        async def override_get_db():
            yield mock_db

        from app.core.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.put(
                    "/api/v1/company-hiring-policy/new-company",
                    json={
                        "pipeline_rules": {"min_interviews_before_offer": 4},
                    },
                )
            assert resp.status_code == 200
            data = resp.json()
            assert data["company_id"] == "new-company"
            assert data["pipeline_rules"]["min_interviews_before_offer"] == 4
            # sync_policy_to_models also adds FeatureFlag objects; verify exactly 1 policy was created
            assert sum(isinstance(o, CompanyHiringPolicy) for o in mock_db.added) == 1
        finally:
            app.dependency_overrides.clear()

    async def test_put_updates_existing_policy(self):
        policy = _mock_policy("existing")
        mock_db = MockSession(policy=policy)

        async def override_get_db():
            yield mock_db

        from app.core.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.put(
                    "/api/v1/company-hiring-policy/existing?user_id=admin",
                    json={
                        "pipeline_rules": {"min_interviews_before_offer": 3, "manager_approval_for_offer": False},
                    },
                )
            assert resp.status_code == 200
            data = resp.json()
            assert data["pipeline_rules"]["min_interviews_before_offer"] == 3
            assert data["pipeline_rules"]["manager_approval_for_offer"] is False
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestBlockUpdateAPI:
    """PATCH /api/v1/company-hiring-policy/{company_id}/block"""

    async def test_patch_block_merges_data(self):
        policy = _mock_policy(
            "merge-test",
            pipeline_rules={"min_interviews_before_offer": 2, "manager_approval_for_offer": True},
        )
        mock_db = MockSession(policy=policy)

        async def override_get_db():
            yield mock_db

        from app.core.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.patch(
                    "/api/v1/company-hiring-policy/merge-test/block",
                    json={
                        "block": "pipeline_rules",
                        "data": {"max_days_in_stage": 7},
                    },
                )
            assert resp.status_code == 200
            data = resp.json()
            assert data["pipeline_rules"]["min_interviews_before_offer"] == 2
            assert data["pipeline_rules"]["manager_approval_for_offer"] is True
            assert data["pipeline_rules"]["max_days_in_stage"] == 7
        finally:
            app.dependency_overrides.clear()

    async def test_patch_block_creates_policy_if_none(self):
        mock_db = MockSession(policy=None)

        async def override_get_db():
            yield mock_db

        from app.core.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.patch(
                    "/api/v1/company-hiring-policy/auto-create/block",
                    json={
                        "block": "scheduling_rules",
                        "data": {"default_duration_minutes": 30},
                    },
                )
            assert resp.status_code == 200
            data = resp.json()
            assert data["scheduling_rules"]["default_duration_minutes"] == 30
            # sync_policy_to_models also adds FeatureFlag objects; verify exactly 1 policy was created
            assert sum(isinstance(o, CompanyHiringPolicy) for o in mock_db.added) == 1
        finally:
            app.dependency_overrides.clear()

    async def test_patch_invalid_block_returns_400(self):
        mock_db = MockSession(policy=None)

        async def override_get_db():
            yield mock_db

        from app.core.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.patch(
                    "/api/v1/company-hiring-policy/test/block",
                    json={
                        "block": "invalid_block_name",
                        "data": {"key": "value"},
                    },
                )
            assert resp.status_code == 400
            assert "Invalid block" in resp.json()["message"]
        finally:
            app.dependency_overrides.clear()

    async def test_patch_all_5_rule_blocks(self):
        blocks_and_updates = [
            ("pipeline_rules", {"min_interviews_before_offer": 5}),
            ("scheduling_rules", {"default_duration_minutes": 90}),
            ("communication_rules", {"lia_tone": "casual"}),
            ("screening_rules", {"salary_tolerance_percent": 25}),
            ("automation_rules", {"auto_screening": True}),
        ]
        for block, update_data in blocks_and_updates:
            policy = _mock_policy("all-blocks-test")
            mock_db = MockSession(policy=policy)

            async def override_get_db():
                yield mock_db

            from app.core.database import get_db
            app.dependency_overrides[get_db] = override_get_db
            try:
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    resp = await client.patch(
                        "/api/v1/company-hiring-policy/all-blocks-test/block",
                        json={"block": block, "data": update_data},
                    )
                assert resp.status_code == 200, f"Failed for block {block}: {resp.text}"
                data = resp.json()
                for key, val in update_data.items():
                    assert data[block][key] == val, f"Mismatch for {block}.{key}"
            finally:
                app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestProgressAPI:
    """GET /api/v1/company-hiring-policy/{company_id}/progress"""

    async def test_progress_zero_for_new_policy(self):
        policy = _mock_policy("progress-test", answered_questions=[])
        mock_db = MockSession(policy=policy)

        async def override_get_db():
            yield mock_db

        from app.core.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/api/v1/company-hiring-policy/progress-test/progress")
            assert resp.status_code == 200
            data = resp.json()
            assert data["setup_progress"] == 0
            assert data["blocks_completed"]["pipeline_rules"] is False
        finally:
            app.dependency_overrides.clear()

    async def test_progress_with_some_answered(self):
        answered = [
            "min_interviews_before_offer",
            "manager_approval_for_offer",
            "max_days_in_stage",
            "pipeline_template",
        ]
        from app.api.v1.hiring_policy import TOTAL_QUESTIONS
        expected_progress = min(int((len(answered) / TOTAL_QUESTIONS) * 100), 100)
        policy = _mock_policy(
            "partial-progress",
            answered_questions=answered,
            setup_progress=expected_progress,
        )
        mock_db = MockSession(policy=policy)

        async def override_get_db():
            yield mock_db

        from app.core.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/api/v1/company-hiring-policy/partial-progress/progress")
            assert resp.status_code == 200
            data = resp.json()
            assert data["setup_progress"] == expected_progress
            assert data["setup_progress"] > 0
            assert data["blocks_completed"]["pipeline_rules"] is True
            assert data["blocks_completed"]["scheduling_rules"] is False
        finally:
            app.dependency_overrides.clear()
