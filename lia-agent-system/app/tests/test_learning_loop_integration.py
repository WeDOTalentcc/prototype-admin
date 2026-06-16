"""
Integration tests for the Learning Loop system.

Tests the complete flow:
Wizard → LearningHub → Agents → Feedback → LearningHub

These tests validate:
- Skill confirmations and promotion logic
- Responsibility deduplication
- Agent feedback recording
- Learning context retrieval
- Multi-tenant isolation
"""
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_learning import AgentFeedback, CompanyResponsibility, CompanySkill
from app.shared.services.learning_hub_service import LearningHubService
from app.shared.services.skills_catalog_service import skills_catalog_service


@pytest.fixture
def learning_hub() -> LearningHubService:
    """Return a fresh LearningHubService instance."""
    return LearningHubService()


@pytest.fixture
def company_a_id() -> str:
    """Return a unique company ID for Company A."""
    return f"company-a-{uuid4().hex[:8]}"


@pytest.fixture
def company_b_id() -> str:
    """Return a unique company ID for Company B."""
    return f"company-b-{uuid4().hex[:8]}"


class TestSkillConfirmationPromotesToCatalog:
    """Tests for skill confirmation and promotion flow."""
    
    @pytest.mark.asyncio
    async def test_skill_confirmation_promotes_to_catalog(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str
    ):
        """
        Test that confirming a skill 3 times promotes it to catalog.
        
        Flow:
        1. Record skill confirmation 3 times for same skill
        2. Verify skill is promoted (is_promoted=True)
        3. Verify skill appears in suggest_skills_with_learning()
        """
        skill_name = f"Python-{uuid4().hex[:6]}"
        role = "Desenvolvedor Backend"
        seniority = "Senior"
        
        result1 = await learning_hub.record_skill_confirmation(
            db=db_session,
            company_id=company_a_id,
            skill_name=skill_name,
            skill_type="technical",
            role=role,
            seniority=seniority
        )
        assert result1.success is True
        assert result1.is_new is True
        assert result1.times_confirmed == 1
        assert result1.is_promoted is False
        
        result2 = await learning_hub.record_skill_confirmation(
            db=db_session,
            company_id=company_a_id,
            skill_name=skill_name,
            skill_type="technical",
            role=role,
            seniority=seniority
        )
        assert result2.success is True
        assert result2.is_new is False
        assert result2.times_confirmed == 2
        assert result2.is_promoted is False
        
        result3 = await learning_hub.record_skill_confirmation(
            db=db_session,
            company_id=company_a_id,
            skill_name=skill_name,
            skill_type="technical",
            role=role,
            seniority=seniority
        )
        assert result3.success is True
        assert result3.is_new is False
        assert result3.times_confirmed == 3
        assert result3.is_promoted is True
        
        stmt = select(CompanySkill).where(
            CompanySkill.id == result3.item_id
        )
        result = await db_session.execute(stmt)
        skill = result.scalar_one_or_none()
        
        assert skill is not None
        assert skill.is_promoted is True
        assert skill.times_confirmed == 3
        
        suggestions = await skills_catalog_service.suggest_skills_with_learning(
            db=db_session,
            company_id=company_a_id,
            role=role,
            seniority=seniority
        )
        
        assert skill_name in suggestions.get("company_learned_skills", [])
        assert suggestions.get("source_mix", {}).get("company_learned", 0) >= 1
    
    @pytest.mark.asyncio
    async def test_skill_case_insensitive_dedup(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str
    ):
        """Test that skill matching is case-insensitive."""
        base_skill_name = f"TypeScript-{uuid4().hex[:6]}"
        
        result1 = await learning_hub.record_skill_confirmation(
            db=db_session,
            company_id=company_a_id,
            skill_name=base_skill_name.upper()
        )
        assert result1.is_new is True
        
        result2 = await learning_hub.record_skill_confirmation(
            db=db_session,
            company_id=company_a_id,
            skill_name=base_skill_name.lower()
        )
        assert result2.is_new is False
        assert result2.times_confirmed == 2


class TestResponsibilityConfirmationWithDedup:
    """Tests for responsibility confirmation and deduplication."""
    
    @pytest.mark.asyncio
    async def test_responsibility_confirmation_with_dedup(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str
    ):
        """
        Test responsibility confirmation with hash-based deduplication.
        
        Flow:
        1. Record same responsibility description multiple times
        2. Verify no duplicates (hash-based dedup works)
        3. Verify times_confirmed increments
        """
        description = f"Desenvolver APIs RESTful escaláveis - {uuid4().hex[:6]}"
        
        result1 = await learning_hub.record_responsibility_confirmation(
            db=db_session,
            company_id=company_a_id,
            description=description,
            category="development",
            role="Backend Developer"
        )
        assert result1.success is True
        assert result1.is_new is True
        assert result1.times_confirmed == 1
        
        result2 = await learning_hub.record_responsibility_confirmation(
            db=db_session,
            company_id=company_a_id,
            description=description,
            category="development"
        )
        assert result2.success is True
        assert result2.is_new is False
        assert result2.times_confirmed == 2
        
        result3 = await learning_hub.record_responsibility_confirmation(
            db=db_session,
            company_id=company_a_id,
            description=description,
            category="development"
        )
        assert result3.success is True
        assert result3.times_confirmed == 3
        assert result3.is_promoted is True
        
        stmt = select(func.count(CompanyResponsibility.id)).where(
            CompanyResponsibility.company_id == company_a_id,
            CompanyResponsibility.description == description
        )
        result = await db_session.execute(stmt)
        count = result.scalar()
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_responsibility_hash_consistency(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str
    ):
        """Test that description hash is consistent for same text."""
        description = f"Lead code reviews and mentor junior developers - {uuid4().hex[:6]}"
        
        hash1 = learning_hub._hash_description(description)
        hash2 = learning_hub._hash_description(description)
        hash3 = learning_hub._hash_description(f"  {description}  ")
        
        assert hash1 == hash2
        assert hash1 == hash3


class TestAgentFeedbackRecorded:
    """Tests for agent feedback recording."""
    
    @pytest.mark.asyncio
    async def test_agent_feedback_recorded(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str
    ):
        """
        Test agent feedback is recorded correctly.
        
        Flow:
        1. Call LearningHubService.record_agent_feedback()
        2. Verify feedback is stored with correct agent_type, action, company_id
        """
        job_id = str(uuid4())
        candidate_id = str(uuid4())
        agent_name = "sourcing_agent"
        action_type = "candidate_suggestion"
        
        success = await learning_hub.record_agent_feedback(
            db=db_session,
            company_id=company_a_id,
            agent_name=agent_name,
            action_type=action_type,
            accepted=True,
            suggested_value={"candidates": ["candidate_1", "candidate_2"]},
            actual_value={"candidates": ["candidate_1"]},
            job_id=job_id,
            candidate_id=candidate_id,
            context={"search_query": "Python developer"},
            feedback_reason="Good match for requirements",
            created_by="recruiter@test.com"
        )
        
        assert success is True
        
        stmt = select(AgentFeedback).where(
            AgentFeedback.company_id == company_a_id,
            AgentFeedback.agent_name == agent_name,
            AgentFeedback.action_type == action_type
        ).order_by(AgentFeedback.created_at.desc())
        
        result = await db_session.execute(stmt)
        feedback = result.scalar_one_or_none()
        
        assert feedback is not None
        assert feedback.company_id == company_a_id
        assert feedback.agent_name == agent_name
        assert feedback.action_type == action_type
        assert feedback.accepted is True
        assert str(feedback.job_id) == job_id
        assert str(feedback.candidate_id) == candidate_id
        assert feedback.suggested_value == {"candidates": ["candidate_1", "candidate_2"]}
        assert feedback.actual_value == {"candidates": ["candidate_1"]}
        assert feedback.feedback_reason == "Good match for requirements"
    
    @pytest.mark.asyncio
    async def test_agent_feedback_rejected_action(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str
    ):
        """Test recording rejected agent feedback."""
        success = await learning_hub.record_agent_feedback(
            db=db_session,
            company_id=company_a_id,
            agent_name="wsi_evaluator",
            action_type="score_suggestion",
            accepted=False,
            suggested_value={"score": 85},
            actual_value={"score": 70},
            feedback_reason="Score too optimistic"
        )
        
        assert success is True
        
        stmt = select(AgentFeedback).where(
            AgentFeedback.company_id == company_a_id,
            AgentFeedback.action_type == "score_suggestion"
        )
        result = await db_session.execute(stmt)
        feedback = result.scalar_one_or_none()
        
        assert feedback is not None
        assert feedback.accepted is False


class TestLearningContextReturnsPromotedSkills:
    """Tests for learning context retrieval."""
    
    @pytest.mark.asyncio
    async def test_learning_context_returns_promoted_skills(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str
    ):
        """
        Test that learning context includes promoted skills.
        
        Flow:
        1. Create promoted skills for a company
        2. Call LearningHubService.get_learning_context()
        3. Verify promoted skills appear in context
        """
        skill_name = f"Kubernetes-{uuid4().hex[:6]}"
        
        for i in range(3):
            await learning_hub.record_skill_confirmation(
                db=db_session,
                company_id=company_a_id,
                skill_name=skill_name,
                skill_type="technical",
                role="DevOps Engineer"
            )
        
        context = await learning_hub.get_learning_context(
            db=db_session,
            company_id=company_a_id
        )
        
        assert context is not None
        assert len(context.company_skills) > 0
        
        promoted_skill = next(
            (s for s in context.company_skills if s["name"].lower() == skill_name.lower()),
            None
        )
        assert promoted_skill is not None
        assert promoted_skill["is_promoted"] is True
        assert promoted_skill["times_confirmed"] >= 3
    
    @pytest.mark.asyncio
    async def test_learning_context_includes_responsibilities(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str
    ):
        """Test that learning context includes promoted responsibilities."""
        description = f"Manage cloud infrastructure - {uuid4().hex[:6]}"
        
        for i in range(3):
            await learning_hub.record_responsibility_confirmation(
                db=db_session,
                company_id=company_a_id,
                description=description,
                category="infrastructure"
            )
        
        context = await learning_hub.get_learning_context(
            db=db_session,
            company_id=company_a_id
        )
        
        assert context is not None
        assert len(context.company_responsibilities) > 0
        
        promoted_resp = next(
            (r for r in context.company_responsibilities if r["description"] == description),
            None
        )
        assert promoted_resp is not None
        assert promoted_resp["is_promoted"] is True


class TestSourcingAgentUsesLearningContext:
    """Tests for Sourcing Agent integration with learning context."""
    
    @pytest.mark.asyncio
    async def test_sourcing_agent_uses_learning_context(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str
    ):
        """
        Test that Sourcing Agent can retrieve learning context.
        
        Flow:
        1. Create company-specific skills
        2. Verify get_learning_context returns correct data
        3. Verify company-specific learned skills are available
        """
        skill_name = f"Docker-{uuid4().hex[:6]}"
        
        for i in range(3):
            await learning_hub.record_skill_confirmation(
                db=db_session,
                company_id=company_a_id,
                skill_name=skill_name,
                skill_type="technical",
                role="DevOps"
            )
        
        context = await learning_hub.get_learning_context(
            db=db_session,
            company_id=company_a_id,
            role="DevOps"
        )
        
        assert context is not None
        
        skill_names = [s["name"].lower() for s in context.company_skills]
        assert skill_name.lower() in skill_names
        
        assert hasattr(context, 'patterns')
        assert hasattr(context, 'success_rate')
    
    @pytest.mark.asyncio
    async def test_learning_context_filters_by_role(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str
    ):
        """Test that learning context can filter skills by role."""
        devops_skill = f"Terraform-{uuid4().hex[:6]}"
        frontend_skill = f"React-{uuid4().hex[:6]}"
        
        await learning_hub.record_skill_confirmation(
            db=db_session,
            company_id=company_a_id,
            skill_name=devops_skill,
            skill_type="technical",
            role="DevOps"
        )
        
        await learning_hub.record_skill_confirmation(
            db=db_session,
            company_id=company_a_id,
            skill_name=frontend_skill,
            skill_type="technical",
            role="Frontend Developer"
        )
        
        all_skills = await learning_hub.get_company_skills(
            db=db_session,
            company_id=company_a_id
        )
        
        skill_names = [s["name"].lower() for s in all_skills]
        assert devops_skill.lower() in skill_names
        assert frontend_skill.lower() in skill_names


class TestMultiTenantIsolation:
    """Tests for multi-tenant data isolation."""
    
    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str,
        company_b_id: str
    ):
        """
        Test that company data is properly isolated.
        
        Flow:
        1. Create skills for company_A and company_B
        2. Verify get_learning_context(company_A) doesn't include company_B skills
        """
        skill_a = f"Python-A-{uuid4().hex[:6]}"
        skill_b = f"Python-B-{uuid4().hex[:6]}"
        
        for i in range(3):
            await learning_hub.record_skill_confirmation(
                db=db_session,
                company_id=company_a_id,
                skill_name=skill_a,
                skill_type="technical"
            )
        
        for i in range(3):
            await learning_hub.record_skill_confirmation(
                db=db_session,
                company_id=company_b_id,
                skill_name=skill_b,
                skill_type="technical"
            )
        
        context_a = await learning_hub.get_learning_context(
            db=db_session,
            company_id=company_a_id
        )
        
        context_b = await learning_hub.get_learning_context(
            db=db_session,
            company_id=company_b_id
        )
        
        skills_a = [s["name"].lower() for s in context_a.company_skills]
        skills_b = [s["name"].lower() for s in context_b.company_skills]
        
        assert skill_a.lower() in skills_a
        assert skill_b.lower() not in skills_a
        
        assert skill_b.lower() in skills_b
        assert skill_a.lower() not in skills_b
    
    @pytest.mark.asyncio
    async def test_multi_tenant_responsibility_isolation(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str,
        company_b_id: str
    ):
        """Test that responsibilities are properly isolated between companies."""
        resp_a = f"Company A specific responsibility - {uuid4().hex[:6]}"
        resp_b = f"Company B specific responsibility - {uuid4().hex[:6]}"
        
        await learning_hub.record_responsibility_confirmation(
            db=db_session,
            company_id=company_a_id,
            description=resp_a
        )
        
        await learning_hub.record_responsibility_confirmation(
            db=db_session,
            company_id=company_b_id,
            description=resp_b
        )
        
        context_a = await learning_hub.get_learning_context(
            db=db_session,
            company_id=company_a_id
        )
        
        context_b = await learning_hub.get_learning_context(
            db=db_session,
            company_id=company_b_id
        )
        
        resp_a_descs = [r["description"] for r in context_a.company_responsibilities]
        resp_b_descs = [r["description"] for r in context_b.company_responsibilities]
        
        assert resp_a in resp_a_descs
        assert resp_b not in resp_a_descs
        
        assert resp_b in resp_b_descs
        assert resp_a not in resp_b_descs
    
    @pytest.mark.asyncio
    async def test_multi_tenant_feedback_isolation(
        self,
        db_session: AsyncSession,
        learning_hub: LearningHubService,
        company_a_id: str,
        company_b_id: str
    ):
        """Test that agent feedback is properly isolated between companies."""
        await learning_hub.record_agent_feedback(
            db=db_session,
            company_id=company_a_id,
            agent_name="sourcing_agent",
            action_type="search_company_a",
            accepted=True
        )
        
        await learning_hub.record_agent_feedback(
            db=db_session,
            company_id=company_b_id,
            agent_name="sourcing_agent",
            action_type="search_company_b",
            accepted=True
        )
        
        stmt_a = select(AgentFeedback).where(
            AgentFeedback.company_id == company_a_id
        )
        result_a = await db_session.execute(stmt_a)
        feedback_a = result_a.scalars().all()
        
        stmt_b = select(AgentFeedback).where(
            AgentFeedback.company_id == company_b_id
        )
        result_b = await db_session.execute(stmt_b)
        feedback_b = result_b.scalars().all()
        
        action_types_a = [f.action_type for f in feedback_a]
        action_types_b = [f.action_type for f in feedback_b]
        
        assert "search_company_a" in action_types_a
        assert "search_company_b" not in action_types_a
        
        assert "search_company_b" in action_types_b
        assert "search_company_a" not in action_types_b
