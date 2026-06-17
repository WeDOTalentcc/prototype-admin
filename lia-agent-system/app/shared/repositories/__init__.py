"""
Repository Pattern - Database access abstraction layer.

Provides a clean interface between business logic and data access,
making it easier to swap ORM implementations (SQLAlchemy → ActiveRecord).
"""
from app.shared.repositories.base import BaseRepository
from app.shared.repositories.candidate_repository import CandidateRepository
from app.shared.repositories.company_repository import CompanyRepository
from app.shared.repositories.job_repository import JobRepository
from app.shared.repositories.notification_repository import NotificationRepository

__all__ = [
    "BaseRepository",
    "CandidateRepository",
    "JobRepository",
    "NotificationRepository",
    "CompanyRepository",
]
