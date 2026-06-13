# FastAPI dependency injection factories for this service domain.
# Example:
#
# from fastapi import Depends
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.database import get_db
#
# async def get_{domain_name}_service(
#     db: AsyncSession = Depends(get_db),
# ) -> {DomainName}Service:
#     return {DomainName}Service(db)
