"""
Testes de Integração — POST /recruitment-stages/sync-canonical-sub-statuses
Camada 3 (Integração BE — pytest + httpx, sem mock de DB)

Cobre:
- Endpoint requer autenticação (401 sem token)
- Sync insere sub-statuses faltantes (inserted > 0 na primeira execução)
- Idempotência: segunda execução retorna inserted=0
- Isolamento por company_id: sync de empresa A não afeta empresa B
- Resposta contém campos 'success' e 'inserted'
"""
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import UserRole
from app.auth.security import create_access_token
from app.main import app
from app.models.recruitment_stages import (
    CANONICAL_SUB_STATUSES,
    RecruitmentStage,
    RecruitmentSubStatus,
)

pytestmark = pytest.mark.asyncio


def make_token(company_id: str, role: UserRole = UserRole.admin) -> str:
    user_id = str(uuid4())
    return create_access_token(subject=user_id, role=role.value)


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSyncCanonicalAuth:

    async def test_unauthenticated_returns_401(self):
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/recruitment-stages/sync-canonical-sub-statuses"
            )
        assert resp.status_code == 401

    async def test_viewer_role_returns_403(self):
        token = make_token("company-x", UserRole.viewer)
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/recruitment-stages/sync-canonical-sub-statuses",
                headers=auth_headers(token),
            )
        # viewer não tem permissão de admin_or_recruiter
        assert resp.status_code in (401, 403)


class TestSyncCanonicalBehavior:

    async def test_response_has_required_fields(self, db_session: AsyncSession, test_users: dict):
        """Resposta sempre contém 'success' e 'inserted'."""
        token = test_users["admin_a"]["token"]

        with patch(
            "app.api.v1.recruitment_stages.get_db",
            return_value=_mock_db_generator(db_session),
        ):
            async with httpx.AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post(
                    "/api/v1/recruitment-stages/sync-canonical-sub-statuses",
                    headers=auth_headers(token),
                )

        assert resp.status_code == 200
        body = resp.json()
        assert "success" in body
        assert "inserted" in body
        assert body["success"] is True
        assert isinstance(body["inserted"], int)

    async def test_inserts_missing_sub_statuses(self, db_session: AsyncSession, test_users: dict):
        """
        Para uma empresa com estágio 'rejected' sem sub-statuses,
        o sync deve inserir os sub-statuses canônicos.
        """
        company_id = test_users["admin_a"]["company_id"]
        token = test_users["admin_a"]["token"]

        # Criar estágio 'rejected' sem sub-statuses
        stage = RecruitmentStage(
            id=uuid4(),
            company_id=company_id,
            name="rejected",
            display_name="Reprovado",
            stage_order=99,
            is_active=True,
            is_system=True,
        )
        db_session.add(stage)
        await db_session.flush()

        with patch(
            "app.api.v1.recruitment_stages.get_db",
            return_value=_mock_db_generator(db_session),
        ):
            async with httpx.AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post(
                    "/api/v1/recruitment-stages/sync-canonical-sub-statuses",
                    headers=auth_headers(token),
                )

        assert resp.status_code == 200
        body = resp.json()
        canonical_count = len(CANONICAL_SUB_STATUSES["rejected"])
        assert body["inserted"] >= canonical_count

    async def test_idempotent_second_call_inserts_zero(
        self, db_session: AsyncSession, test_users: dict
    ):
        """
        Após o primeiro sync, o segundo não deve inserir nada.
        """
        company_id = test_users["admin_a"]["company_id"]
        token = test_users["admin_a"]["token"]

        # Criar estágio com todos os sub-statuses já presentes
        stage = RecruitmentStage(
            id=uuid4(),
            company_id=company_id,
            name="rejected",
            display_name="Reprovado",
            stage_order=99,
            is_active=True,
            is_system=True,
        )
        db_session.add(stage)
        await db_session.flush()

        # Inserir todos os canonical sub-statuses manualmente
        for i, sub_data in enumerate(CANONICAL_SUB_STATUSES["rejected"]):
            sub = RecruitmentSubStatus(
                id=uuid4(),
                stage_id=stage.id,
                company_id=company_id,
                sub_status_order=i,
                name=sub_data["name"],
                display_name=sub_data["display_name"],
                is_default=sub_data.get("is_default", False),
                is_waiting=sub_data.get("is_waiting", False),
            )
            db_session.add(sub)
        await db_session.flush()

        with patch(
            "app.api.v1.recruitment_stages.get_db",
            return_value=_mock_db_generator(db_session),
        ):
            async with httpx.AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post(
                    "/api/v1/recruitment-stages/sync-canonical-sub-statuses",
                    headers=auth_headers(token),
                )

        assert resp.status_code == 200
        assert resp.json()["inserted"] == 0

    async def test_company_isolation(self, db_session: AsyncSession, test_users: dict):
        """
        Sub-statuses de empresa A não são inseridos para empresa B.
        """
        company_b_id = test_users["recruiter_b"]["company_id"]
        token_a = test_users["admin_a"]["token"]

        # Criar estágio para empresa B
        stage_b = RecruitmentStage(
            id=uuid4(),
            company_id=company_b_id,
            name="rejected",
            display_name="Reprovado",
            stage_order=99,
            is_active=True,
            is_system=True,
        )
        db_session.add(stage_b)
        await db_session.flush()

        with patch(
            "app.api.v1.recruitment_stages.get_db",
            return_value=_mock_db_generator(db_session),
        ):
            async with httpx.AsyncClient(app=app, base_url="http://test") as client:
                # Sync executado como admin da empresa A
                await client.post(
                    "/api/v1/recruitment-stages/sync-canonical-sub-statuses",
                    headers=auth_headers(token_a),
                )

        # Verificar que empresa B não teve sub-statuses inseridos
        result = await db_session.execute(
            select(RecruitmentSubStatus).where(
                RecruitmentSubStatus.stage_id == stage_b.id
            )
        )
        subs_b = result.scalars().all()
        assert len(subs_b) == 0, (
            "Sync da empresa A não deve inserir sub-statuses para empresa B"
        )


async def _mock_db_generator(session: AsyncSession):
    """Helper para injetar a sessão de teste no endpoint via get_db."""
    yield session
