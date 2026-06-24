"""Consolidated dependency injection factories.
Migrated from 30 repository_stub domains (T14 migration, 2026-06-09).
"""

# --- from admin ---
"""
Dependency injection for admin domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.admin_repository import AdminRepository


def get_admin_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> AdminRepository:
    return AdminRepository(db)

# --- from admin_settings ---
"""
Dependency injection for admin_settings domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.admin_settings_repository import (
    AdminSettingsRepository,
)


def get_admin_settings_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> AdminSettingsRepository:
    return AdminSettingsRepository(db)

# --- from agent_memory ---
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.agent_memory_repository import AgentMemoryRepository


def get_agent_memory_repo(db: AsyncSession = Depends(get_tenant_db)) -> AgentMemoryRepository:
    return AgentMemoryRepository(db)

# --- from approvals ---
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_tenant_db
from app.repositories.approvals_repository import ApprovalsRepository


def get_approvals_repo(db: AsyncSession = Depends(get_tenant_db)) -> ApprovalsRepository:
    return ApprovalsRepository(db)

# --- from auth ---
"""Dependency injection functions for auth domain repositories.

Multi-tenancy / RLS: usa get_tenant_db canonical (app.core.database) que setea
Postgres GUC \`app.company_id\` per-request via request.state injetado pelo
AuthEnforcementMiddleware. Pre-auth flows (register/login/forgot-password/
public-register/invitation-info) NAO tem company_id ainda — get_tenant_db
degrada graciosamente para sessao sem RLS context nesse caso (nao quebra).
Post-auth flows (/me, /change-password, /update-profile) ganham RLS
enforcement automatico — defense-in-depth alinhado com canonical pattern
em app/domains/job_management/dependencies.py.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.auth_user_repository import UserRepository
from app.repositories.workos_repository import WorkOSRepository


def get_user_repo(db: AsyncSession = Depends(get_tenant_db)) -> UserRepository:
    return UserRepository(db)


def get_workos_repo(db: AsyncSession = Depends(get_tenant_db)) -> WorkOSRepository:
    return WorkOSRepository(db)

# --- from bulk_actions ---
"""
Dependency injection for bulk_actions domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.bulk_actions_repository import BulkActionsRepository


def get_bulk_actions_repo(db: AsyncSession = Depends(get_tenant_db)) -> BulkActionsRepository:
    return BulkActionsRepository(db)

# --- from candidate_lists ---
"""
FastAPI dependency providers for the candidate_lists domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.candidate_list_repository import (
    CandidateListRepository,
)


def get_candidate_list_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> CandidateListRepository:
    return CandidateListRepository(db)

# --- from chat ---
"""
Dependency injection functions for the chat domain repository.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.chat_repository import ChatRepository


def get_chat_repo(db: AsyncSession = Depends(get_tenant_db)) -> ChatRepository:
    return ChatRepository(db)

# --- from client_users ---
"""Dependency injection for the client_users domain."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.client_user_repository import ClientUserRepository


def get_client_user_repo(db: AsyncSession = Depends(get_tenant_db)) -> ClientUserRepository:
    return ClientUserRepository(db)

# --- from clients ---
"""
Dependency injection functions for the clients domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.client_account_repository import ClientAccountRepository


def get_client_repo(db: AsyncSession = Depends(get_tenant_db)) -> ClientAccountRepository:
    return ClientAccountRepository(db)

# --- from company_culture ---
"""
Dependency injection functions for the company_culture domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.company_culture_repository import (
    CompanyCultureRepository,
)


def get_company_culture_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> CompanyCultureRepository:
    return CompanyCultureRepository(db)

# --- from compliance ---
"""
FastAPI dependency factories for the Compliance domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.compliance_controls_repository import (
    ComplianceControlsRepository,
)


def get_compliance_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> ComplianceControlsRepository:
    return ComplianceControlsRepository(db)

# --- from consent ---
"""
FastAPI dependency factories for the Consent domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.consent_repository import ConsentRepository


def get_consent_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> ConsentRepository:
    return ConsentRepository(db)

# --- from data_subject ---
"""Dependency injection factories for the data_subject domain."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.data_subject_repository import DataSubjectRepository


def get_data_subject_repo(db: AsyncSession = Depends(get_tenant_db)) -> DataSubjectRepository:
    return DataSubjectRepository(db)

# --- from email_templates ---
"""
Dependency injection for email_templates domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.email_templates_repository import (
    EmailTemplatesRepository,
)


def get_email_templates_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> EmailTemplatesRepository:
    return EmailTemplatesRepository(db)

# --- from goals ---
"""
Dependency injection functions for goals domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db

from app.repositories.goals_repository import GoalsRepository


def get_goals_repo(db: AsyncSession = Depends(get_tenant_db)) -> GoalsRepository:
    return GoalsRepository(db)

# --- from health_check ---
"""
FastAPI dependency factories for the Health Check domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.health_check_repository import (
    HealthCheckRepository,
)


def get_health_check_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> HealthCheckRepository:
    return HealthCheckRepository(db)

# --- from job_vacancies_analytics ---
"""
Dependency injection for job_vacancies_analytics domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.job_vacancies_analytics_repository import (
    JobVacanciesAnalyticsRepository,
)


def get_job_vacancies_analytics_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> JobVacanciesAnalyticsRepository:
    return JobVacanciesAnalyticsRepository(db)

# --- from journey_mapping ---
"""Dependency injection functions for journey_mapping domain repositories."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.journey_mapping_repository import JourneyMappingRepository


def get_journey_mapping_repo(db: AsyncSession = Depends(get_tenant_db)) -> JourneyMappingRepository:
    return JourneyMappingRepository(db)

# --- from notifications ---
"""
Dependency injection for notifications domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.notifications_repository import NotificationsRepository


def get_notifications_repo(db: AsyncSession = Depends(get_tenant_db)) -> NotificationsRepository:
    return NotificationsRepository(db)

# --- from observability ---
"""Dependency injection functions for observability domain repositories."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.observability_repository import ObservabilityRepository


def get_observability_repo(db: AsyncSession = Depends(get_tenant_db)) -> ObservabilityRepository:
    return ObservabilityRepository(db)

# --- from opinions ---
"""
Dependency injection for opinions domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.opinions_repository import OpinionsRepository


def get_opinions_repo(db: AsyncSession = Depends(get_tenant_db)) -> OpinionsRepository:
    return OpinionsRepository(db)

# --- from recruitment_journey ---
"""
Dependency injection functions for the recruitment_journey domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.recruitment_journey_repository import (
    RecruitmentJourneyRepository,
)


def get_recruitment_journey_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> RecruitmentJourneyRepository:
    return RecruitmentJourneyRepository(db)

# --- from saas_metrics ---
"""Dependency injection for the saas_metrics domain."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.saas_metrics_repository import (
    SaasMetricsRepository,
)


def get_saas_metrics_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> SaasMetricsRepository:
    return SaasMetricsRepository(db)

# --- from shared_searches ---
"""
Dependency injection for shared_searches domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.shared_search_repository import (
    SharedSearchRepository,
)


def get_shared_search_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> SharedSearchRepository:
    return SharedSearchRepository(db)

# --- from tasks ---
"""
Dependency injection factories for the tasks domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.tasks_repository import TasksRepository


def get_tasks_repo(db: AsyncSession = Depends(get_tenant_db)) -> TasksRepository:
    return TasksRepository(db)

# --- from technical_tests ---
"""
Dependency injection for technical_tests domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.technical_tests_repository import (
    TechnicalTestsRepository,
)


def get_technical_tests_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> TechnicalTestsRepository:
    return TechnicalTestsRepository(db)

# --- from triagem ---
"""P2 D (2026-05-23): get_triagem_repo retorna canonical TriagemSessionRepository.

Antes: retornava stub vazio TriagemRepository com apenas self.db.
Agora: retorna canonical com 7 métodos reais. Endpoint usage de `repo.db`
continua funcional (mesma interface).
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.domains.recruitment.repositories.triagem_session_repository import (
    TriagemSessionRepository,
)


def get_triagem_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> TriagemSessionRepository:
    return TriagemSessionRepository(db)

# --- from trust_center ---
"""
FastAPI dependency factories for the Trust Center domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.trust_center_repository import (
    TrustCenterRepository,
)


def get_trust_center_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> TrustCenterRepository:
    return TrustCenterRepository(db)

# --- from workforce ---
"""
FastAPI dependency injection factories for the workforce domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.workforce_repository import WorkforceRepository


def get_workforce_repo(db: AsyncSession = Depends(get_tenant_db)) -> WorkforceRepository:
    return WorkforceRepository(db)

