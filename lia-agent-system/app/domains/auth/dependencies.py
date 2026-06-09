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
