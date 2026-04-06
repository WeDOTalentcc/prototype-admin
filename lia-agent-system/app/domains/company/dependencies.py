"""
Dependency injection functions for company domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.company.repositories.approver_repository import ApproverRepository
from app.domains.company.repositories.benefit_repository import BenefitRepository
from app.domains.company.repositories.big_five_repository import BigFiveRepository
from app.domains.company.repositories.company_profile_repository import (
    CompanyProfileRepository,
)
from app.domains.company.repositories.culture_value_repository import (
    CultureValueRepository,
)
from app.domains.company.repositories.department_repository import DepartmentRepository
from app.domains.company.repositories.global_settings_repository import (
    GlobalSettingsRepository,
)
from app.domains.company.repositories.ideal_profile_repository import (
    IdealProfileRepository,
)
from app.domains.company.repositories.technical_test_repository import (
    TechnicalTestRepository,
)


def get_company_profile_repo(
    db: AsyncSession = Depends(get_db),
) -> CompanyProfileRepository:
    return CompanyProfileRepository(db)


def get_department_repo(
    db: AsyncSession = Depends(get_db),
) -> DepartmentRepository:
    return DepartmentRepository(db)


def get_benefit_repo(
    db: AsyncSession = Depends(get_db),
) -> BenefitRepository:
    return BenefitRepository(db)


def get_culture_value_repo(
    db: AsyncSession = Depends(get_db),
) -> CultureValueRepository:
    return CultureValueRepository(db)


def get_ideal_profile_repo(
    db: AsyncSession = Depends(get_db),
) -> IdealProfileRepository:
    return IdealProfileRepository(db)


def get_big_five_repo(
    db: AsyncSession = Depends(get_db),
) -> BigFiveRepository:
    return BigFiveRepository(db)


def get_technical_test_repo(
    db: AsyncSession = Depends(get_db),
) -> TechnicalTestRepository:
    return TechnicalTestRepository(db)


def get_approver_repo(
    db: AsyncSession = Depends(get_db),
) -> ApproverRepository:
    return ApproverRepository(db)


def get_global_settings_repo(
    db: AsyncSession = Depends(get_db),
) -> GlobalSettingsRepository:
    return GlobalSettingsRepository(db)
