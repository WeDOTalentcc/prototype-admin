"""Task #1107 — End-to-end integration coverage for
``PUT /api/v1/company/culture-profile/{company_id}`` against a real Postgres.

A Task #1101 fechou o GET ponta-a-ponta. O PUT (caminho que recrutadores
usam pra ajustar o perfil manualmente) ainda não tinha um teste indo até
o banco e voltando pelo Pydantic — uma regressão na
``CompanyCultureRepository.update_profile_fields`` ou no
``CompanyCultureProfileUpdate`` (ex.: campo novo aceito mas não persistido,
``source`` deixando de virar ``"manual"``) passaria batido.

Este teste:
  * Cria as rows pai (``companies`` + ``company_profiles``) e uma linha
    base de ``company_culture_profiles`` com ``source = "auto"``.
  * Hits a rota real via ``TestClient`` com JWT assinado.
  * Faz PUT autenticado com payload **parcial** (subset de campos:
    scalars, arrays e Big-Five scores) e valida HTTP 200 + payload
    devolvido com ``source = "manual"``.
  * Faz GET de volta pelo mesmo endpoint pra confirmar persistência
    real (não apenas o eco da resposta do PUT) e que campos NÃO
    enviados continuaram inalterados.
  * Reusa o padrão de fixture/cleanup de
    ``test_culture_profile_get_endpoint_db_t1101.py``.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text


def _has_postgres() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    return bool(url and "postgres" in url)


pytestmark = pytest.mark.skipif(
    not _has_postgres(),
    reason="Requer DATABASE_URL apontando pra Postgres real (mesma fixture do test_save_hiring_policy_db.py).",
)


from app.auth.dependencies import (  # noqa: E402
    get_current_active_user,
    get_current_user,
    get_current_user_or_demo,
    get_current_user_strict,
)
from app.auth.security import create_access_token  # noqa: E402
from app.core.database import get_db, get_tenant_db  # noqa: E402
from app.main import app  # noqa: E402


def _user(company_id: str):
    u = MagicMock()
    u.id = "user-1107"
    u.company_id = company_id
    u.role = "admin"
    u.is_active = True
    u.email = "admin@t1107.com"
    return u


@pytest.fixture
async def pg_session_factory():
    """AsyncSessionLocal canônico do projeto (mesmo padrão do T1101)."""
    try:
        from lia_config.database import AsyncSessionLocal
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Não consegui importar AsyncSessionLocal: {exc}")

    try:
        async with AsyncSessionLocal() as s:
            await s.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Postgres indisponível para integração: {exc}")

    yield AsyncSessionLocal


async def _insert_company_and_profile(SessionMaker, company_id: uuid.UUID) -> None:
    cid_str = str(company_id)
    async with SessionMaker() as session:
        await session.execute(
            text("SELECT set_config('app.company_id', :cid, true)"),
            {"cid": cid_str},
        )
        await session.execute(
            text(
                """
                INSERT INTO companies (id, name, is_active, is_demo)
                VALUES (:id, :name, TRUE, FALSE)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"id": cid_str, "name": f"T1107 Test {cid_str[:8]}"},
        )
        await session.execute(
            text(
                """
                INSERT INTO company_profiles (id, name)
                VALUES (:id, :name)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"id": cid_str, "name": f"T1107 Profile {cid_str[:8]}"},
        )
        await session.commit()


async def _insert_baseline_culture_row(SessionMaker, company_id: uuid.UUID) -> None:
    """Insere uma linha 'auto' com TODOS os campos preenchidos —
    serve de baseline para o PUT parcial sobrescrever apenas alguns."""
    cid_str = str(company_id)
    now = datetime.utcnow()
    async with SessionMaker() as session:
        await session.execute(
            text("SELECT set_config('app.company_id', :cid, true)"),
            {"cid": cid_str},
        )
        await session.execute(
            text(
                """
                INSERT INTO company_culture_profiles (
                    id, company_id, website_url, mission, vision,
                    values, evp_bullets, core_competencies, analyzed_pages,
                    locations, tech_stack, default_languages,
                    openness_score, conscientiousness_score, extraversion_score,
                    agreeableness_score, stability_score,
                    source, confidence_score,
                    last_analysis_at, created_at, updated_at
                ) VALUES (
                    :id, :cid, :website, :mission, :vision,
                    :values, :evp_bullets, :core_competencies, :analyzed_pages,
                    :locations, :tech_stack, :default_languages,
                    :openness, :conscientiousness, :extraversion,
                    :agreeableness, :stability,
                    'auto', 0.7,
                    :now, :now, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "cid": cid_str,
                "website": "https://baseline-t1107.example.com",
                "mission": "Original mission",
                "vision": "Original vision",
                "values": ["original_v1", "original_v2"],
                "evp_bullets": ["Original EVP"],
                "core_competencies": ["original_comp"],
                "analyzed_pages": ["https://baseline-t1107.example.com/about"],
                "locations": ["Belo Horizonte"],
                "tech_stack": ["go"],
                "default_languages": ["pt-BR"],
                "openness": 40,
                "conscientiousness": 40,
                "extraversion": 40,
                "agreeableness": 40,
                "stability": 40,
            "now": now,
            },
        )
        await session.commit()


async def _cleanup(SessionMaker, company_id: uuid.UUID) -> None:
    cid_str = str(company_id)
    async with SessionMaker() as session:
        await session.execute(
            text("SELECT set_config('app.company_id', :cid, true)"),
            {"cid": cid_str},
        )
        for stmt in (
            "DELETE FROM company_culture_profiles WHERE company_id = :cid",
            "DELETE FROM company_profiles WHERE id = :cid",
            "DELETE FROM companies WHERE id = :cid",
        ):
            try:
                await session.execute(text(stmt), {"cid": cid_str})
            except Exception:
                pass
        await session.commit()


def _make_client(company_id: uuid.UUID, SessionMaker):
    user = _user(str(company_id))

    def _user_dep():
        return user

    async def _tenant_db_dep():
        async with SessionMaker() as session:
            await session.execute(
                text("SELECT set_config('app.company_id', :cid, true)"),
                {"cid": str(company_id)},
            )
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def _db_dep():
        async with SessionMaker() as session:
            await session.execute(
                text("SELECT set_config('app.company_id', :cid, true)"),
                {"cid": str(company_id)},
            )
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _db_dep
    app.dependency_overrides[get_tenant_db] = _tenant_db_dep
    app.dependency_overrides[get_current_user] = _user_dep
    app.dependency_overrides[get_current_active_user] = _user_dep
    app.dependency_overrides[get_current_user_or_demo] = _user_dep
    app.dependency_overrides[get_current_user_strict] = _user_dep

    token = create_access_token(
        subject="user-1107",
        role="admin",
        company_id=str(company_id),
    )
    client = TestClient(app, raise_server_exceptions=False)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.mark.asyncio
async def test_put_culture_profile_persists_partial_payload_and_flips_source(
    pg_session_factory,
):
    """PUT parcial → grava no Postgres, vira ``source = "manual"`` e
    deixa campos não enviados intactos. Validação via GET subsequente."""
    SessionMaker = pg_session_factory
    company_id = uuid.uuid4()
    await _insert_company_and_profile(SessionMaker, company_id)
    await _insert_baseline_culture_row(SessionMaker, company_id)

    payload = {
        # scalars
        "mission": "Updated mission via PUT",
        "culture_description": "Cultura ajustada manualmente pelo recrutador",
        # arrays
        "values": ["transparency", "ownership", "growth"],
        "tech_stack": ["python", "react", "postgres"],
        # Big-Five scores (subset — só dois)
        "openness_score": 82,
        "conscientiousness_score": 77,
    }

    try:
        with patch("app.main.init_db", AsyncMock()):
            client = _make_client(company_id, SessionMaker)
            put_resp = client.put(
                f"/api/v1/company/culture-profile/{company_id}",
                json=payload,
            )
            assert put_resp.status_code == 200, put_resp.text
            put_body = put_resp.json()

            # Eco do PUT já deve refletir source manual + campos atualizados
            assert put_body["source"] == "manual"
            assert put_body["mission"] == "Updated mission via PUT"
            assert put_body["culture_description"] == (
                "Cultura ajustada manualmente pelo recrutador"
            )
            assert put_body["values"] == ["transparency", "ownership", "growth"]
            assert put_body["tech_stack"] == ["python", "react", "postgres"]
            assert put_body["openness_score"] == 82
            assert put_body["conscientiousness_score"] == 77

            # Campos NÃO enviados precisam permanecer com o valor de baseline
            assert put_body["vision"] == "Original vision"
            assert put_body["evp_bullets"] == ["Original EVP"]
            assert put_body["core_competencies"] == ["original_comp"]
            assert put_body["locations"] == ["Belo Horizonte"]
            assert put_body["default_languages"] == ["pt-BR"]
            assert put_body["extraversion_score"] == 40
            assert put_body["agreeableness_score"] == 40
            assert put_body["stability_score"] == 40

            # Persistência real: GET subsequente confirma que o PUT escreveu
            # no banco (e não apenas devolveu o objeto em memória).
            get_resp = client.get(f"/api/v1/company/culture-profile/{company_id}")
            assert get_resp.status_code == 200, get_resp.text
            get_body = get_resp.json()

            assert get_body["source"] == "manual"
            assert get_body["mission"] == "Updated mission via PUT"
            assert get_body["culture_description"] == (
                "Cultura ajustada manualmente pelo recrutador"
            )
            assert get_body["values"] == ["transparency", "ownership", "growth"]
            assert get_body["tech_stack"] == ["python", "react", "postgres"]
            assert get_body["openness_score"] == 82
            assert get_body["conscientiousness_score"] == 77
            # Pass-through dos campos não enviados
            assert get_body["vision"] == "Original vision"
            assert get_body["evp_bullets"] == ["Original EVP"]
            assert get_body["core_competencies"] == ["original_comp"]
            assert get_body["default_languages"] == ["pt-BR"]
            assert get_body["extraversion_score"] == 40
            assert get_body["agreeableness_score"] == 40
            assert get_body["stability_score"] == 40
            # IDs imutáveis
            assert str(uuid.UUID(get_body["company_id"])) == str(company_id)
    finally:
        app.dependency_overrides.clear()
        await _cleanup(SessionMaker, company_id)
