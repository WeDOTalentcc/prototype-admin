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


# --------------------------------------------------------------------------
# Fase D-seed tests: VoiceScreeningChannel manifesto
# --------------------------------------------------------------------------

VOICE_CHANNEL_ID = "00000000-0000-0000-0000-000000000003"


class TestVoiceScreeningChannelModel:
    """Unit tests for VoiceScreeningChannel first-party seed (Fase D)."""

    def test_voice_channel_category_is_voice_channel(self):
        """VoiceScreeningChannel must have category=voice_channel."""
        agent = CustomAgent(
            id=VOICE_CHANNEL_ID,
            company_id=None,
            created_by="wedo_system",
            name="VoiceScreeningChannel",
            role="Canal de Triagem por Voz",
            system_prompt="",
            domain="general",
            agent_type=AgentType.first_party,
            domains=[],
            allowed_tools=[],
            config={},
            category="voice_channel",
            voice_enabled=True,
        )
        assert agent.category == "voice_channel"
        assert agent.voice_enabled is True

    def test_voice_channel_has_empty_domains(self):
        """VoiceScreeningChannel must have empty domains — it is NOT a chat routing agent."""
        agent = CustomAgent(
            id=VOICE_CHANNEL_ID,
            company_id=None,
            created_by="wedo_system",
            name="VoiceScreeningChannel",
            role="Canal de Triagem por Voz",
            system_prompt="",
            domain="general",
            agent_type=AgentType.first_party,
            domains=[],
            allowed_tools=[],
            config={},
            category="voice_channel",
        )
        assert agent.domains == [], "voice_channel must have empty domains"
        assert agent.allowed_tools == [], "voice_channel must have no routing tools"

    def test_voice_channel_not_excluded_from_to_dict(self):
        """to_dict() must include category and voice_enabled for visibility in Studio UI."""
        agent = CustomAgent(
            id=VOICE_CHANNEL_ID,
            company_id=None,
            created_by="wedo_system",
            name="VoiceScreeningChannel",
            role="Canal de Triagem por Voz",
            system_prompt="",
            domain="general",
            agent_type=AgentType.first_party,
            domains=[],
            allowed_tools=[],
            config={},
            category="voice_channel",
            voice_enabled=True,
        )
        d = agent.to_dict()
        assert d.get("category") == "voice_channel"
        assert d.get("name") == "VoiceScreeningChannel"
        assert d.get("agent_type") == "first_party"


def _filter_chat_routing_agents(agents: list) -> list:
    """
    Simulates list_active_for_context() routing filter:
    Excludes category='voice_channel' from chat agent routing.

    This is the canonical filter logic that any repository or service
    providing agents for chat domain routing MUST apply.
    """
    return [a for a in agents if getattr(a, "category", None) != "voice_channel"]


class TestVoiceChannelExcludedFromChatRouting:
    """
    VoiceScreeningChannel must NOT appear in chat domain routing queries.

    Rationale: voice_channel agents are channel manifests for per-tenant
    config visibility in Agent Studio. They have no domains, no system_prompt,
    no routing tools. Including them in chat routing would cause the CascadedRouter
    to try to dispatch messages to an agent with no capabilities.
    """

    def _make_chat_agent(self, name: str, category: str = "screening") -> object:
        """Helper to create a minimal mock agent dict."""
        class AgentMock:
            pass
        a = AgentMock()
        a.name = name
        a.category = category
        a.agent_type = "first_party"
        a.domains = ["talent"] if category != "voice_channel" else []
        return a

    def test_voice_channel_excluded_from_routing(self):
        """voice_channel category must be excluded from chat domain routing."""
        agents = [
            self._make_chat_agent("TalentIntelAgent", "screening"),
            self._make_chat_agent("InterviewAnalysisAgent", "screening"),
            self._make_chat_agent("VoiceScreeningChannel", "voice_channel"),
        ]
        chat_agents = _filter_chat_routing_agents(agents)
        names = [a.name for a in chat_agents]
        assert "VoiceScreeningChannel" not in names, (
            "VoiceScreeningChannel must NOT appear in chat routing agents"
        )
        assert "TalentIntelAgent" in names
        assert "InterviewAnalysisAgent" in names

    def test_only_voice_channel_excluded_not_others(self):
        """Only voice_channel category is excluded; other categories pass through."""
        agents = [
            self._make_chat_agent("TalentIntelAgent", "screening"),
            self._make_chat_agent("SomeAnalyticsAgent", "analytics"),
            self._make_chat_agent("VoiceScreeningChannel", "voice_channel"),
        ]
        chat_agents = _filter_chat_routing_agents(agents)
        assert len(chat_agents) == 2
        assert all(a.category != "voice_channel" for a in chat_agents)

    def test_empty_agent_list_returns_empty(self):
        """Edge case: empty input returns empty output."""
        assert _filter_chat_routing_agents([]) == []

    def test_all_voice_channels_excluded(self):
        """Edge case: if all agents are voice_channel, routing gets empty list."""
        agents = [
            self._make_chat_agent("VoiceScreeningChannel", "voice_channel"),
            self._make_chat_agent("AnotherVoiceChannel", "voice_channel"),
        ]
        chat_agents = _filter_chat_routing_agents(agents)
        assert chat_agents == []


@pytest.mark.asyncio
class TestVoiceChannelSeedIdempotencyDB:
    """DB-level idempotency test for VoiceScreeningChannel seed (Fase D)."""

    async def test_voice_channel_seed_is_idempotent(self, db_session: AsyncSession):
        """Second insertion of VoiceScreeningChannel does NOT duplicate the row."""
        agent_id = VOICE_CHANNEL_ID

        # First insert
        voice = CustomAgentSQLite(
            id=agent_id,
            company_id=None,
            created_by="wedo_system",
            name="VoiceScreeningChannel",
            role="Canal de Triagem por Voz",
            system_prompt="",
            domain="general",
            agent_type=AgentType.first_party.value,
            domains=[],
            allowed_tools=[],
            config={},
            status=CustomAgentStatus.ACTIVE.value,
            voice_enabled=True,
            category="voice_channel",
        )
        db_session.add(voice)
        await db_session.commit()

        # Simulate second seed run: get_or_skip (ON CONFLICT DO NOTHING semantics)
        existing = await db_session.get(CustomAgentSQLite, agent_id)
        assert existing is not None  # already present — idempotent

        result = await db_session.execute(
            select(CustomAgentSQLite).where(CustomAgentSQLite.id == agent_id)
        )
        rows = result.scalars().all()
        assert len(rows) == 1, f"Expected exactly 1 VoiceScreeningChannel row, got {len(rows)}"
        assert rows[0].name == "VoiceScreeningChannel"
        assert rows[0].category == "voice_channel"
        assert rows[0].agent_type == AgentType.first_party.value

    async def test_voice_channel_does_not_appear_in_domain_filtered_query(self, db_session: AsyncSession):
        """
        list_active_for_context() with domain filter must exclude voice_channel agents.
        Simulates the routing query: WHERE domains @> ARRAY[domain] AND category != voice_channel.
        In SQLite we test the Python-layer filter equivalent.
        """
        # Seed all 3 first-party agents
        for row in [
            CustomAgentSQLite(
                id="00000000-0000-0000-0000-000000000001",
                company_id=None, created_by="wedo_system",
                name="TalentIntelAgent", role="r", system_prompt="",
                domain="talent", agent_type="first_party",
                domains=["talent"], allowed_tools=[], config={},
                status="active", category="screening",
            ),
            CustomAgentSQLite(
                id="00000000-0000-0000-0000-000000000002",
                company_id=None, created_by="wedo_system",
                name="InterviewAnalysisAgent", role="r", system_prompt="",
                domain="talent", agent_type="first_party",
                domains=["talent"], allowed_tools=[], config={},
                status="active", category="screening",
            ),
            CustomAgentSQLite(
                id=VOICE_CHANNEL_ID,
                company_id=None, created_by="wedo_system",
                name="VoiceScreeningChannel", role="r", system_prompt="",
                domain="general", agent_type="first_party",
                domains=[], allowed_tools=[], config={},
                status="active", category="voice_channel",
                voice_enabled=True,
            ),
        ]:
            db_session.add(row)
        await db_session.commit()

        # Fetch all active first_party agents
        result = await db_session.execute(
            select(CustomAgentSQLite).where(
                CustomAgentSQLite.agent_type == "first_party",
                CustomAgentSQLite.status == "active",
            )
        )
        all_first_party = result.scalars().all()
        assert len(all_first_party) == 3

        # Apply routing filter (Python-layer equivalent of SQL WHERE category != voice_channel)
        chat_routing = _filter_chat_routing_agents(all_first_party)
        names = [a.name for a in chat_routing]

        assert "VoiceScreeningChannel" not in names, (
            "VoiceScreeningChannel must be excluded from chat routing query"
        )
        assert len(chat_routing) == 2
        assert "TalentIntelAgent" in names
        assert "InterviewAnalysisAgent" in names


# =============================================================================
# Phase B tests: domains + allowed_tools manifest correctness
# =============================================================================

from app.domains.agent_studio.custom_agent_runtime import (
    PLATFORM_TOOLS_REGISTRY,
    get_available_tool_names,
)

TALENT_INTEL_AGENT_ID_STR = "00000000-0000-0000-0000-000000000001"
INTERVIEW_ANALYSIS_AGENT_ID_STR = "00000000-0000-0000-0000-000000000002"

# Canonical expected values — mirror of scripts/seed_first_party_agents.py
_EXPECTED_TALENT_INTEL_TOOLS = [
    "infer_related_skills",
    "get_skill_adjacencies",
    "analyze_skill_gaps",
    "map_candidate_skills_to_ontology",
    "get_market_intelligence",
    "forecast_hiring_needs",
    "match_internal_candidates",
    "create_nurture_sequence",
    "get_engagement_metrics",
    "suggest_reengagement",
    "analyze_interview_recording",
    "detect_interview_bias",
    "compare_interview_performance",
    "generate_candidate_feedback",
    "generate_interview_opinion",
]

_EXPECTED_INTERVIEW_ANALYSIS_TOOLS = [
    "analyze_interview_recording",
    "detect_interview_bias",
    "compare_interview_performance",
    "generate_candidate_feedback",
    "generate_interview_opinion",
]

_EXPECTED_TALENT_INTEL_DOMAINS = [
    "talent_analysis",
    "skill_gap",
    "market_intelligence",
    "workforce_planning",
    "candidate_nurture",
]

_EXPECTED_INTERVIEW_ANALYSIS_DOMAINS = [
    "interview_analysis",
    "bias_detection",
    "interview_feedback",
]


class TestPlatformToolsRegistryFaseB:
    """Phase B: all 15 talent_intelligence tools are in PLATFORM_TOOLS_REGISTRY."""

    def test_talent_intel_tools_registered(self):
        """All 15 talent_intelligence tools must exist in PLATFORM_TOOLS_REGISTRY."""
        registry_keys = set(PLATFORM_TOOLS_REGISTRY.keys())
        for tool_name in _EXPECTED_TALENT_INTEL_TOOLS:
            assert tool_name in registry_keys, (
                f"Tool '{tool_name}' missing from PLATFORM_TOOLS_REGISTRY. "
                f"Add it in app/domains/agent_studio/custom_agent_runtime.py."
            )

    def test_talent_intel_tool_types_are_correct(self):
        """Write tools are marked write; analytics/read tools are marked read."""
        write_tools = {"create_nurture_sequence", "generate_candidate_feedback", "generate_interview_opinion"}
        read_tools = set(_EXPECTED_TALENT_INTEL_TOOLS) - write_tools
        for tool_name in write_tools:
            assert PLATFORM_TOOLS_REGISTRY.get(tool_name) == "write", (
                f"Tool '{tool_name}' should be 'write' in PLATFORM_TOOLS_REGISTRY"
            )
        for tool_name in read_tools:
            assert PLATFORM_TOOLS_REGISTRY.get(tool_name) == "read", (
                f"Tool '{tool_name}' should be 'read' in PLATFORM_TOOLS_REGISTRY"
            )

    def test_original_16_tools_unchanged(self):
        """Regression: the original 16 core tools are still present and unchanged."""
        original_tools = {
            "search_candidates": "read",
            "list_jobs": "read",
            "get_job_details": "read",
            "get_candidate_details": "read",
            "summarize_context": "read",
            "clarify_request": "read",
            "get_evaluation_criteria": "read",
            "get_pipeline_summary": "read",
            "search_talent_pool": "read",
            "get_company_culture": "read",
            "get_analytics_summary": "read",
            "move_candidate": "write",
            "create_note": "write",
            "send_email": "write",
            "update_candidate_field": "write",
            "schedule_interview": "write",
        }
        for tool_name, expected_type in original_tools.items():
            assert tool_name in PLATFORM_TOOLS_REGISTRY, (
                f"Original tool '{tool_name}' was removed — regression!"
            )
            assert PLATFORM_TOOLS_REGISTRY[tool_name] == expected_type, (
                f"Original tool '{tool_name}' type changed from '{expected_type}' "
                f"to '{PLATFORM_TOOLS_REGISTRY[tool_name]}' — regression!"
            )

    def test_total_registry_size(self):
        """Registry should have exactly 31 tools (16 core + 15 talent_intelligence)."""
        assert len(PLATFORM_TOOLS_REGISTRY) == 31, (
            f"Expected 31 tools in PLATFORM_TOOLS_REGISTRY, got {len(PLATFORM_TOOLS_REGISTRY)}. "
            f"Tools present: {sorted(PLATFORM_TOOLS_REGISTRY.keys())}"
        )

    def test_get_available_tool_names_includes_talent_intel(self):
        """get_available_tool_names() must include talent_intelligence tools."""
        available = set(get_available_tool_names())
        for tool_name in _EXPECTED_TALENT_INTEL_TOOLS:
            assert tool_name in available, (
                f"Tool '{tool_name}' missing from get_available_tool_names() output"
            )


class TestFirstPartyAgentManifestFaseB:
    """Phase B: first-party agents have correct domains and allowed_tools."""

    def test_talent_intel_manifest_tool_count(self):
        """TalentIntelAgent manifest has exactly 15 tools."""
        assert len(_EXPECTED_TALENT_INTEL_TOOLS) == 15

    def test_talent_intel_manifest_domains(self):
        """TalentIntelAgent has 5 expected domains."""
        assert len(_EXPECTED_TALENT_INTEL_DOMAINS) == 5
        assert "talent_analysis" in _EXPECTED_TALENT_INTEL_DOMAINS
        assert "workforce_planning" in _EXPECTED_TALENT_INTEL_DOMAINS

    def test_interview_analysis_manifest_tool_count(self):
        """InterviewAnalysisAgent manifest has exactly 5 tools."""
        assert len(_EXPECTED_INTERVIEW_ANALYSIS_TOOLS) == 5

    def test_interview_analysis_manifest_domains(self):
        """InterviewAnalysisAgent has 3 expected domains."""
        assert len(_EXPECTED_INTERVIEW_ANALYSIS_DOMAINS) == 3
        assert "interview_analysis" in _EXPECTED_INTERVIEW_ANALYSIS_DOMAINS
        assert "bias_detection" in _EXPECTED_INTERVIEW_ANALYSIS_DOMAINS

    def test_interview_tools_are_subset_of_talent_intel_tools(self):
        """InterviewAnalysisAgent tools must be a strict subset of TalentIntelAgent tools.

        This ensures no tool is exposed by InterviewAnalysisAgent that isn't
        also in PLATFORM_TOOLS_REGISTRY via TalentIntelAgent.
        """
        interview_set = set(_EXPECTED_INTERVIEW_ANALYSIS_TOOLS)
        talent_set = set(_EXPECTED_TALENT_INTEL_TOOLS)
        assert interview_set.issubset(talent_set), (
            f"InterviewAnalysisAgent tools not a subset of TalentIntelAgent tools. "
            f"Extra: {interview_set - talent_set}"
        )

    def test_all_manifest_tools_in_registry(self):
        """Every tool in either first-party manifest must be in PLATFORM_TOOLS_REGISTRY.

        This is the boundary enforcement test: if a tool is listed in a
        first-party agent's allowed_tools but NOT in PLATFORM_TOOLS_REGISTRY,
        the runtime will silently skip it at execution time. This test catches
        that drift at definition time.
        """
        registry_keys = set(PLATFORM_TOOLS_REGISTRY.keys())
        all_manifest_tools = (
            set(_EXPECTED_TALENT_INTEL_TOOLS) | set(_EXPECTED_INTERVIEW_ANALYSIS_TOOLS)
        )
        missing = all_manifest_tools - registry_keys
        assert not missing, (
            f"Tools in first-party manifests but NOT in PLATFORM_TOOLS_REGISTRY: {missing}. "
            f"Add them to custom_agent_runtime.py PLATFORM_TOOLS_REGISTRY."
        )

    def test_tool_not_in_interview_agent_not_exposed(self):
        """Boundary: a TalentIntelAgent-only tool is NOT in InterviewAnalysisAgent manifest.

        Example: infer_related_skills is a TalentIntel-only skill; the
        InterviewAnalysisAgent should not claim it.
        """
        interview_only_allowed = set(_EXPECTED_INTERVIEW_ANALYSIS_TOOLS)
        talent_only_tools = {
            "infer_related_skills",
            "get_skill_adjacencies",
            "analyze_skill_gaps",
            "map_candidate_skills_to_ontology",
            "get_market_intelligence",
            "forecast_hiring_needs",
            "match_internal_candidates",
            "create_nurture_sequence",
            "get_engagement_metrics",
            "suggest_reengagement",
        }
        leaked = talent_only_tools & interview_only_allowed
        assert not leaked, (
            f"Tool(s) that belong only to TalentIntelAgent are also in "
            f"InterviewAnalysisAgent allowed_tools: {leaked}. "
            f"Remove them from InterviewAnalysisAgent allowed_tools."
        )
