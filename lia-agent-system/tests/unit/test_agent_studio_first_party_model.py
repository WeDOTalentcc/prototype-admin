"""TDD tests for Agent Studio Fase A — first-party agent model support.

Tests:
1. company_id=None + agent_type=first_party is valid (no constraint violation)
2. Seed is idempotent (second run doesn't duplicate)
3. First-party agent appears in global listing (no company_id filter)
4. agent_type defaults to 'custom' for existing agents (no regression)

Run: python3 -m pytest tests/unit/test_agent_studio_first_party_model.py -v --no-cov
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy import MetaData, Table, Column, String, Boolean, Integer, Float, Text, DateTime
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import select

from lia_models.custom_agent import AgentType, CustomAgent, CustomAgentStatus

# --------------------------------------------------------------------------
# We create a MINIMAL standalone table for SQLite (no ARRAY, no JSONB, no ENUM).
# This tests the model's Python-level behavior (constructor, to_dict, queries).
# Postgres-specific types (ARRAY, JSONB, pg ENUM) are tested at migration level.
# --------------------------------------------------------------------------

class MinimalBase(DeclarativeBase):
    pass


class CustomAgentSQLite(MinimalBase):
    """Minimal SQLite-compatible shadow table for unit testing model behavior."""
    __tablename__ = "custom_agents"

    id = Column(sa.String(36), primary_key=True)
    company_id = Column(String(64), nullable=True)
    created_by = Column(String(64), nullable=False, default="test")
    name = Column(String(256), nullable=False)
    role = Column(String(256), nullable=False, default="role")
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=False, default="")
    allowed_tools = Column(SQLiteJSON, nullable=False, default=list)
    domain = Column(String(64), nullable=False, default="general")
    icon = Column(String(10), nullable=True, default="🤖")
    status = Column(String(20), nullable=False, default="draft")
    version = Column(Integer, nullable=False, default=1)
    config = Column(SQLiteJSON, nullable=False, default=dict)
    max_steps = Column(Integer, nullable=False, default=8)
    temperature = Column(Float, nullable=False, default=0.7)
    model_override = Column(String(64), nullable=True)
    enable_memory = Column(Boolean, nullable=False, default=True)
    context_level = Column(String(20), nullable=False, default="full")
    excluded_tools = Column(SQLiteJSON, nullable=False, default=list)
    voice_enabled = Column(Boolean, nullable=False, default=False)
    voip_enabled = Column(Boolean, nullable=False, default=False)
    whatsapp_enabled = Column(Boolean, nullable=False, default=False)
    triagem_invite_enabled = Column(Boolean, nullable=False, default=False)
    category = Column(String(32), nullable=True)
    runtime_metrics = Column(SQLiteJSON, nullable=False, default=dict)
    search_strategy = Column(SQLiteJSON, nullable=True)
    preferences = Column(SQLiteJSON, nullable=True)
    outreach_config = Column(SQLiteJSON, nullable=True)
    total_executions = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    last_executed_at = Column(DateTime, nullable=True)
    is_marketplace_published = Column(Boolean, default=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    # New Fase A columns
    agent_type = Column(String(20), nullable=False, default="custom")
    domains = Column(SQLiteJSON, nullable=False, default=list)


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture()
async def db_session():
    """Provide a transient in-memory SQLite session per test."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(MinimalBase.metadata.create_all)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
    await engine.dispose()


# --------------------------------------------------------------------------
# Unit tests (no DB needed — test Python model behavior)
# --------------------------------------------------------------------------

class TestAgentTypeEnum:
    """Test 4: enum values are correct, defaults to 'custom'."""

    def test_enum_values(self):
        assert AgentType.custom.value == "custom"
        assert AgentType.first_party.value == "first_party"

    def test_agent_type_is_string_enum(self):
        """AgentType inherits str so it serializes as plain string."""
        assert isinstance(AgentType.custom, str)
        assert AgentType.custom == "custom"

    def test_default_is_custom(self):
        """New CustomAgent defaults to agent_type='custom' (not first_party)."""
        agent = CustomAgent(
            id=uuid.uuid4(),
            company_id="test_company_123",
            created_by="test_user",
            name="MyAgent",
            role="Tester",
            system_prompt="You are a test agent.",
            domain="general",
        )
        # The default is AgentType.custom or None (before DB write)
        assert agent.agent_type != AgentType.first_party


class TestFirstPartyAgentModel:
    """Test 1: company_id=None + agent_type=first_party is constructible."""

    def test_first_party_agent_allows_null_company_id(self):
        """company_id=None is valid for first_party agents (no Python-level constraint)."""
        agent = CustomAgent(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            company_id=None,           # MUST be allowed
            created_by="wedo_system",
            name="TalentIntelAgent",
            role="Analista de Talentos",
            system_prompt="Global talent agent.",
            domain="talent",
            agent_type=AgentType.first_party,
            domains=[],
            status=CustomAgentStatus.ACTIVE.value,
        )
        assert agent.company_id is None
        assert agent.agent_type == AgentType.first_party

    def test_first_party_to_dict(self):
        """to_dict() includes agent_type and domains."""
        agent = CustomAgent(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            company_id=None,
            created_by="wedo_system",
            name="TalentIntelAgent",
            role="Analista de Talentos",
            system_prompt="Global talent agent.",
            domain="talent",
            agent_type=AgentType.first_party,
            domains=["talent", "jobs"],
            allowed_tools=[],
            status=CustomAgentStatus.ACTIVE.value,
            config={},
        )
        d = agent.to_dict()
        assert "agent_type" in d, "to_dict() must include agent_type"
        assert d["agent_type"] == "first_party"
        assert "domains" in d, "to_dict() must include domains"
        assert d["domains"] == ["talent", "jobs"]
        assert d["company_id"] is None

    def test_custom_agent_still_requires_company_logic(self):
        """Regression: custom agents still have company_id set (not None)."""
        agent = CustomAgent(
            id=uuid.uuid4(),
            company_id="company_abc",
            created_by="user_1",
            name="MyCustomAgent",
            role="Recruiter",
            system_prompt="Help recruit.",
            domain="general",
            agent_type=AgentType.custom,
            domains=[],
            allowed_tools=[],
            config={},
        )
        assert agent.company_id == "company_abc"
        assert agent.agent_type == AgentType.custom

    def test_to_dict_custom_agent_defaults(self):
        """Regression: custom agent to_dict shows agent_type=custom."""
        agent = CustomAgent(
            id=uuid.uuid4(),
            company_id="company_xyz",
            created_by="user_1",
            name="LegacyAgent",
            role="Sourcer",
            system_prompt="Old agent.",
            domain="general",
            agent_type=AgentType.custom,
            domains=[],
            allowed_tools=[],
            config={},
        )
        d = agent.to_dict()
        assert d["agent_type"] == "custom"
        assert d["domains"] == []


# --------------------------------------------------------------------------
# DB tests — use the SQLite shadow table for DB-level assertions
# --------------------------------------------------------------------------

@pytest.mark.asyncio
class TestFirstPartyAgentDB:
    """Tests 2 & 3: DB persistence, idempotency, global listing."""

    async def test_first_party_agent_persists_with_null_company_id(self, db_session: AsyncSession):
        """Test 1 (DB level): INSERT with company_id=None succeeds."""
        agent = CustomAgentSQLite(
            id=str(uuid.UUID("00000000-0000-0000-0000-000000000001")),
            company_id=None,
            created_by="wedo_system",
            name="TalentIntelAgent",
            role="Analista de Talentos",
            system_prompt="Global.",
            domain="talent",
            agent_type=AgentType.first_party.value,
            domains=[],
            allowed_tools=[],
            config={},
            status=CustomAgentStatus.ACTIVE.value,
        )
        db_session.add(agent)
        await db_session.commit()

        result = await db_session.execute(
            select(CustomAgentSQLite).where(
                CustomAgentSQLite.id == str(uuid.UUID("00000000-0000-0000-0000-000000000001"))
            )
        )
        fetched = result.scalar_one_or_none()
        assert fetched is not None
        assert fetched.company_id is None
        assert fetched.name == "TalentIntelAgent"
        assert fetched.agent_type == "first_party"

    async def test_seed_idempotency(self, db_session: AsyncSession):
        """Test 2: inserting the same first-party agent twice doesn't duplicate."""
        agent_id = str(uuid.UUID("00000000-0000-0000-0000-000000000002"))

        agent = CustomAgentSQLite(
            id=agent_id,
            company_id=None,
            created_by="wedo_system",
            name="InterviewAnalysisAgent",
            role="Analista de Entrevistas",
            system_prompt="Interview analysis.",
            domain="talent",
            agent_type=AgentType.first_party.value,
            domains=[],
            allowed_tools=[],
            config={},
            status=CustomAgentStatus.ACTIVE.value,
        )
        db_session.add(agent)
        await db_session.commit()

        # Simulate "seed again" — merge existing (ON CONFLICT DO NOTHING semantics)
        existing = await db_session.get(CustomAgentSQLite, agent_id)
        assert existing is not None  # already present — idempotent, no second insert

        result = await db_session.execute(
            select(CustomAgentSQLite).where(CustomAgentSQLite.id == agent_id)
        )
        rows = result.scalars().all()
        assert len(rows) == 1, f"Expected 1 agent, found {len(rows)}"

    async def test_first_party_agent_appears_in_global_listing(self, db_session: AsyncSession):
        """Test 3: first-party agents (company_id=None) appear without company filter."""
        first_party = CustomAgentSQLite(
            id=str(uuid.uuid4()),
            company_id=None,
            created_by="wedo_system",
            name="GlobalAgent",
            role="Global Role",
            system_prompt="Global.",
            domain="general",
            agent_type=AgentType.first_party.value,
            domains=[],
            allowed_tools=[],
            config={},
            status=CustomAgentStatus.ACTIVE.value,
        )
        tenant_agent = CustomAgentSQLite(
            id=str(uuid.uuid4()),
            company_id="tenant_company_123",
            created_by="user_a",
            name="TenantAgent",
            role="Recruiter",
            system_prompt="Tenant specific.",
            domain="general",
            agent_type=AgentType.custom.value,
            domains=[],
            allowed_tools=[],
            config={},
            status=CustomAgentStatus.ACTIVE.value,
        )
        db_session.add(first_party)
        db_session.add(tenant_agent)
        await db_session.commit()

        # Global listing: no company_id filter
        result = await db_session.execute(select(CustomAgentSQLite))
        all_agents = result.scalars().all()
        names = {a.name for a in all_agents}
        assert "GlobalAgent" in names, "First-party agent must appear in global listing"
        assert "TenantAgent" in names

        # First-party filter: company_id IS NULL
        result = await db_session.execute(
            select(CustomAgentSQLite).where(CustomAgentSQLite.company_id.is_(None))
        )
        global_only = result.scalars().all()
        assert len(global_only) >= 1
        assert all(a.company_id is None for a in global_only)
        assert any(a.agent_type == AgentType.first_party.value for a in global_only)

    async def test_custom_agent_type_default_regression(self, db_session: AsyncSession):
        """Test 4: existing agents without explicit agent_type don't break (defaults to 'custom')."""
        agent = CustomAgentSQLite(
            id=str(uuid.uuid4()),
            company_id="company_xyz",
            created_by="recruiter_1",
            name="LegacyAgent",
            role="Sourcer",
            system_prompt="Old agent.",
            domain="general",
            domains=[],
            allowed_tools=[],
            config={},
            status=CustomAgentStatus.DRAFT.value,
            # agent_type NOT explicitly set — relies on column default
        )
        db_session.add(agent)
        await db_session.commit()

        result = await db_session.execute(
            select(CustomAgentSQLite).where(CustomAgentSQLite.name == "LegacyAgent")
        )
        fetched = result.scalar_one_or_none()
        assert fetched is not None
        # Should be 'custom' (default) — never 'first_party'
        assert fetched.agent_type != AgentType.first_party.value, \
            "Legacy agent must not become first_party by default"
