"""
lia-services — shared repositories and data access layer.

Re-exports the repository interface from app/shared/repositories/.
Usage:
    from lia_services import BaseRepository, CandidateRepository
"""
from app.shared.repositories.base import BaseRepository
from app.shared.repositories.sqlalchemy_base import SQLAlchemyRepository
from app.shared.repositories.candidate_repository import CandidateRepository
from app.shared.repositories.job_repository import JobRepository
from app.shared.repositories.company_repository import CompanyRepository
from app.shared.repositories.notification_repository import NotificationRepository

__all__ = [
    "BaseRepository",
    "SQLAlchemyRepository",
    "CandidateRepository",
    "JobRepository",
    "CompanyRepository",
    "NotificationRepository",
]
