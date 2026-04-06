from sqlalchemy.ext.asyncio import AsyncSession


class TriagemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
