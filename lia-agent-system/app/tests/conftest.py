"""
Test fixtures for multi-tenancy and integration tests.

Provides async database sessions with proper transaction isolation,
test users, job vacancies, and candidates. All test data is automatically
rolled back after each test - no explicit cleanup needed.
"""
import os
from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.models import User, UserRole
from app.auth.security import create_access_token, get_password_hash
from app.core.config import settings
from app.models.candidate import Candidate, VacancyCandidate
from app.models.job_vacancy import JobVacancy


def get_test_database_url():
    """Get properly formatted database URL for tests."""
    database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
    
    if database_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    if database_url and "sslmode=" in database_url:
        parsed = urlparse(database_url)
        query_params = parse_qs(parsed.query)
        query_params.pop('sslmode', None)
        new_query = urlencode(query_params, doseq=True)
        database_url = urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, new_query, parsed.fragment
        ))
    
    return database_url


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create an async database session for testing with proper transaction isolation.
    
    This fixture:
    1. Creates a fresh engine for the test event loop
    2. Begins a transaction on the connection
    3. Creates a nested transaction (savepoint) for rollback capability
    4. Binds the session to the connection
    5. Automatically rolls back ALL changes when the test completes
    
    This ensures complete isolation between tests - no data leaks across tests.
    """
    database_url = get_test_database_url()
    
    test_engine = create_async_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
    )
    
    try:
        async with test_engine.connect() as conn:
            trans = await conn.begin()
            
            try:
                nested = await conn.begin_nested()
                
                async_session_factory = async_sessionmaker(
                    bind=conn,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autocommit=False,
                    autoflush=False,
                )
                
                async with async_session_factory() as session:
                    @event.listens_for(session.sync_session, "after_transaction_end")
                    def reopen_nested_transaction(session_sync, transaction):
                        """Re-open a nested transaction if the current one was committed/rolled back."""
                        nonlocal nested
                        if conn.closed:
                            return
                        if not conn.in_nested_transaction():
                            try:
                                nested = conn.sync_connection.begin_nested()
                            except Exception:
                                pass
                    
                    try:
                        yield session
                    finally:
                        await session.close()
            finally:
                await trans.rollback()
    finally:
        await test_engine.dispose()


class TestUserFactory:
    """Factory for creating test users with different roles and companies."""
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        name: str,
        role: UserRole,
        company_id: str,
        is_active: bool = True
    ) -> User:
        """Create a user in the database and return the model."""
        user = User(
            id=uuid4(),
            email=email,
            name=name,
            password_hash=get_password_hash("test_password_123"),
            role=role,
            company_id=company_id,
            is_active=is_active
        )
        db.add(user)
        await db.flush()
        return user
    
    @staticmethod
    def create_token(user: User) -> str:
        """Create a valid JWT token for the user."""
        return create_access_token(
            company_id="test_company",
            subject=str(user.id),
            role=user.role.value
        )


class TestJobVacancyFactory:
    """Factory for creating test job vacancies."""
    
    @staticmethod
    async def create_vacancy(
        db: AsyncSession,
        title: str,
        company_id: str,
        status: str = "Ativa",
        created_by: str = None
    ) -> JobVacancy:
        """Create a job vacancy in the database."""
        vacancy = JobVacancy(
            id=uuid4(),
            title=title,
            company_id=company_id,
            status=status,
            created_by=created_by,
            description=f"Test vacancy for {title}",
            department="Engineering",
            location="Remote"
        )
        db.add(vacancy)
        await db.flush()
        return vacancy


class TestCandidateFactory:
    """Factory for creating test candidates and vacancy-candidate associations."""
    
    @staticmethod
    async def create_candidate(
        db: AsyncSession,
        name: str,
        email: str,
        source: str = "manual"
    ) -> Candidate:
        """Create a candidate in the database."""
        candidate = Candidate(
            id=uuid4(),
            name=name,
            email=email,
            source=source,
            status="new",
            is_active=True
        )
        db.add(candidate)
        await db.flush()
        return candidate
    
    @staticmethod
    async def create_vacancy_candidate(
        db: AsyncSession,
        vacancy_id,
        candidate_id,
        company_id: str,
        status: str = "sourced",
        source: str = "local"
    ) -> VacancyCandidate:
        """Create a vacancy-candidate association."""
        vc = VacancyCandidate(
            id=uuid4(),
            vacancy_id=vacancy_id,
            candidate_id=candidate_id,
            company_id=company_id,
            status=status,
            source=source,
            lia_score=0.85,
            match_percentage=78.5
        )
        db.add(vc)
        await db.flush()
        return vc


@pytest.fixture(scope="function")
async def user_factory():
    """Provide the TestUserFactory for creating test users."""
    return TestUserFactory()


@pytest.fixture(scope="function")
async def vacancy_factory():
    """Provide the TestJobVacancyFactory for creating test vacancies."""
    return TestJobVacancyFactory()


@pytest.fixture(scope="function")
async def candidate_factory():
    """Provide the TestCandidateFactory for creating test candidates."""
    return TestCandidateFactory()


@pytest.fixture(scope="function")
async def test_users(db_session: AsyncSession, user_factory: TestUserFactory) -> dict:
    """
    Create a set of test users from different companies.
    Returns dict with user objects and their tokens.
    
    Note: Uses flush instead of commit - transaction is rolled back after test.
    """
    users = {}
    
    recruiter_a = await user_factory.create_user(
        db=db_session,
        email=f"recruiter_a_{uuid4().hex[:8]}@company-a.com",
        name="Recruiter A",
        role=UserRole.recruiter,
        company_id="test-company-a"
    )
    users["recruiter_a"] = {
        "user": recruiter_a,
        "token": user_factory.create_token(recruiter_a),
        "company_id": "test-company-a"
    }
    
    recruiter_b = await user_factory.create_user(
        db=db_session,
        email=f"recruiter_b_{uuid4().hex[:8]}@company-b.com",
        name="Recruiter B",
        role=UserRole.recruiter,
        company_id="test-company-b"
    )
    users["recruiter_b"] = {
        "user": recruiter_b,
        "token": user_factory.create_token(recruiter_b),
        "company_id": "test-company-b"
    }
    
    admin_a = await user_factory.create_user(
        db=db_session,
        email=f"admin_a_{uuid4().hex[:8]}@company-a.com",
        name="Admin A",
        role=UserRole.admin,
        company_id="test-company-a"
    )
    users["admin_a"] = {
        "user": admin_a,
        "token": user_factory.create_token(admin_a),
        "company_id": "test-company-a"
    }
    
    viewer_a = await user_factory.create_user(
        db=db_session,
        email=f"viewer_a_{uuid4().hex[:8]}@company-a.com",
        name="Viewer A",
        role=UserRole.viewer,
        company_id="test-company-a"
    )
    users["viewer_a"] = {
        "user": viewer_a,
        "token": user_factory.create_token(viewer_a),
        "company_id": "test-company-a"
    }
    
    await db_session.flush()
    
    return users


@pytest.fixture(scope="function")
async def test_vacancies(
    db_session: AsyncSession,
    vacancy_factory: TestJobVacancyFactory,
    test_users: dict
) -> dict:
    """
    Create test job vacancies for different companies.
    
    Note: Uses flush instead of commit - transaction is rolled back after test.
    """
    vacancies = {}
    
    vacancy_a1 = await vacancy_factory.create_vacancy(
        db=db_session,
        title="Senior Developer - Company A",
        company_id="test-company-a",
        created_by=str(test_users["recruiter_a"]["user"].id)
    )
    vacancies["vacancy_a1"] = vacancy_a1
    
    vacancy_a2 = await vacancy_factory.create_vacancy(
        db=db_session,
        title="Product Manager - Company A",
        company_id="test-company-a"
    )
    vacancies["vacancy_a2"] = vacancy_a2
    
    vacancy_b1 = await vacancy_factory.create_vacancy(
        db=db_session,
        title="Data Scientist - Company B",
        company_id="test-company-b",
        created_by=str(test_users["recruiter_b"]["user"].id)
    )
    vacancies["vacancy_b1"] = vacancy_b1
    
    await db_session.flush()
    
    return vacancies


@pytest.fixture(scope="function")
async def test_vacancy_candidates(
    db_session: AsyncSession,
    candidate_factory: TestCandidateFactory,
    test_vacancies: dict
) -> dict:
    """
    Create test candidates and associate them with vacancies.
    
    Note: Uses flush instead of commit - transaction is rolled back after test.
    """
    data = {"candidates": {}, "vacancy_candidates": {}}
    
    candidate_1 = await candidate_factory.create_candidate(
        db=db_session,
        name="John Doe",
        email=f"john_{uuid4().hex[:8]}@test.com"
    )
    data["candidates"]["candidate_1"] = candidate_1
    
    candidate_2 = await candidate_factory.create_candidate(
        db=db_session,
        name="Jane Smith",
        email=f"jane_{uuid4().hex[:8]}@test.com"
    )
    data["candidates"]["candidate_2"] = candidate_2
    
    candidate_3 = await candidate_factory.create_candidate(
        db=db_session,
        name="Bob Johnson",
        email=f"bob_{uuid4().hex[:8]}@test.com"
    )
    data["candidates"]["candidate_3"] = candidate_3
    
    vc_a1_c1 = await candidate_factory.create_vacancy_candidate(
        db=db_session,
        vacancy_id=test_vacancies["vacancy_a1"].id,
        candidate_id=candidate_1.id,
        company_id="test-company-a"
    )
    data["vacancy_candidates"]["vc_a1_c1"] = vc_a1_c1
    
    vc_a1_c2 = await candidate_factory.create_vacancy_candidate(
        db=db_session,
        vacancy_id=test_vacancies["vacancy_a1"].id,
        candidate_id=candidate_2.id,
        company_id="test-company-a"
    )
    data["vacancy_candidates"]["vc_a1_c2"] = vc_a1_c2
    
    vc_b1_c3 = await candidate_factory.create_vacancy_candidate(
        db=db_session,
        vacancy_id=test_vacancies["vacancy_b1"].id,
        candidate_id=candidate_3.id,
        company_id="test-company-b"
    )
    data["vacancy_candidates"]["vc_b1_c3"] = vc_b1_c3
    
    await db_session.flush()
    
    return data
