"""
Dependency injection functions for company domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.company.repositories.approver_repository import ApproverRepository
from app.domains.company.repositories.benefit_repository import BenefitRepository
from app.domains.company.repositories.company_profile_repository import CompanyProfileRepository
from app.domains.company.repositories.culture_profile_repository import CultureProfileRepository
from app.domains.company.repositories.culture_value_repository import CultureValueRepository
from app.domains.company.repositories.department_repository import DepartmentRepository
from app.domains.company.repositories.global_settings_repository import GlobalSettingsRepository
from app.domains.company.repositories.ideal_profile_repository import IdealProfileRepository
from app.domains.company.repositories.tenant_repository import TenantRepository
from app.domains.auth.repositories.user_repository import UserRepository


def get_company_profile_repo(db: AsyncSession = Depends(get_db)) -> CompanyProfileRepository:
    return CompanyProfileRepository(db)


def get_department_repo(db: AsyncSession = Depends(get_db)) -> DepartmentRepository:
    return DepartmentRepository(db)


def get_benefit_repo(db: AsyncSession = Depends(get_db)) -> BenefitRepository:
    return BenefitRepository(db)


def get_culture_value_repo(db: AsyncSession = Depends(get_db)) -> CultureValueRepository:
    return CultureValueRepository(db)


def get_ideal_profile_repo(db: AsyncSession = Depends(get_db)) -> IdealProfileRepository:
    return IdealProfileRepository(db)


def get_approver_repo(db: AsyncSession = Depends(get_db)) -> ApproverRepository:
    return ApproverRepository(db)


def get_global_settings_repo(db: AsyncSession = Depends(get_db)) -> GlobalSettingsRepository:
    return GlobalSettingsRepository(db)


def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_culture_profile_repo(db: AsyncSession = Depends(get_db)) -> CultureProfileRepository:
    return CultureProfileRepository(db)


def get_tenant_repo(db: AsyncSession = Depends(get_db)) -> TenantRepository:
    return TenantRepository(db)
