"""
Scheduling Repository - encapsulates all database access for the scheduling API.
"""
from sqlalchemy.ext.asyncio import AsyncSession


class SchedulingRepository:
    """Repository that provides access to a database session for the scheduling domain."""

    def __init__(self, db: AsyncSession):
        self.db = db
