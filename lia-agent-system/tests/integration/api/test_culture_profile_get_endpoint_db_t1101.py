"""Task #1101 — End-to-end integration coverage for
``GET /api/v1/company/culture-profile/{company_id}`` against a real Postgres.

Task #1098 added unit-level coverage of the schema's NULL → default coercion
(``_coerce_culture_none_defaults``) and an HTTP test using a stub repo
(`test_culture_profile_get_response_t1098.py`). What was still missing was
the **full HTTP path going to the database and back through the Pydantic
``response_model``** — i.e., the exact shape of the wire that previously
broke with ``ResponseValidationError``. Without this, a regression in the
SQLAlchemy model or repo (e.g., dropping the schema's ``model_validator``
or reintroducing a strict NOT NULL list field) could silently slip past
the unit suite.

This test:
  * Inserts a `companies` row + `company_profiles` row + `company_culture_profiles`
    row directly via raw SQL (bypassing the ORM defaults so legacy NULLs are
    actually persisted).
  * Hits the real FastAPI route via ``TestClient`` with a signed JWT.
  * Lets ``get_tenant_db`` execute against the real Postgres session, going
    through ``CompanyCultureRepository`` → ORM → ``CompanyCultureProfileResponse``
    serialization end-to-end.
  * Asserts HTTP 200 + coerced defaults on the legacy row, and pass-through on
    the populated row.

Skips gracefully when ``DATABASE_URL`` does not point at a Postgres instance
(same posture as `test_save_hiring_policy_db.py`).
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


# Imports protegidos: o módulo só é importado quando há Postgres, mas o coletor
# do pytest precisa importar o arquivo de qualquer forma. Tudo abaixo é
# tolerante a ausência da app/database em ambientes degradados.
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
    u.id = "user-1101"
    u.company_id = company_id
    u.role = "admin"
    u.is_active = True
    u.email = "admin@t1101.com"
    return u


@pytest.fixture
async def pg_session_factory():
    """AsyncSessionLocal canônico do projeto (mesmo padrão do PR4/Task #1009)."""
    try:
        from lia_config.database import AsyncSessionLocal
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Não consegui importar AsyncSessionLocal: {exc}")

    # Smoke test de conectividade — falha cedo (skip) se o banco está fora.
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Postgres indisponível para integração: {exc}")

    yield AsyncSessionLocal


async def _insert_company_and_profile(SessionMaker, company_id: uuid.UUID) -> None:
    """Cria as rows pai exigidas pela FK de ``company_culture_profiles``."""
    cid_str = str(company_id)
    async with SessionMaker() as session:
        # `companies` usa String(255); `company_profiles.id` é UUID.
        # Tabela `companies` tem RLS de tenant — bind antes de inserir.
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
            {"id": cid_str, "name": f"T1101 Test {cid_str[:8]}"},
        )
        await session.execute(
            text(
                """
                INSERT INTO company_profiles (id, name)
                VALUES (:id, :name)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"id": cid_str, "name": f"T1101 Profile {cid_str[:8]}"},
        )
        await session.commit()


_LEGACY_NULLABLE_COLS = (
    "values", "evp_bullets", "core_competencies", "analyzed_pages",
    "locations", "tech_stack", "default_languages",
    "openness_score", "conscientiousness_score", "extraversion_score",
    "agreeableness_score", "stability_score",
)


async def _insert_legacy_culture_row(SessionMaker, company_id: uuid.UUID) -> None:
    """Insere uma linha 'legacy': NULL nos arrays e nos Big-Five scores.

    Reproduz o estado real do bug que motivou a Task #1098: rows que vivem
    no banco com NULL nessas colunas (escritas antes dos defaults Python
    existirem ou via SQL bruto). Como a migração 130 endureceu o schema
    pra NOT NULL, a fixture **derruba temporariamente** o NOT NULL apenas
    pelo tempo do INSERT e restaura logo em seguida — mesma posture de
    fixtures de "downgrade pontual" usadas em testes que validam coerção
    de defaults legacy. Isso garante que a regressão alvo (NULL chegando
    no Pydantic) continue testável mesmo com o hardening em vigor.
    """
    cid_str = str(company_id)
    now = datetime.utcnow()
    async with SessionMaker() as session:
        await session.execute(
            text("SELECT set_config('app.company_id', :cid, true)"),
            {"cid": cid_str},
        )
        # Drop NOT NULL temporariamente nas colunas hardenedas pela 130.
        for col in _LEGACY_NULLABLE_COLS:
            await session.execute(
                text(f'ALTER TABLE company_culture_profiles ALTER COLUMN "{col}" DROP NOT NULL')
            )
        try:
            await session.execute(
                text(
                    """
                    INSERT INTO company_culture_profiles (
                        id, company_id, website_url,
                        values, evp_bullets, core_competencies, analyzed_pages,
                        locations, tech_stack, default_languages,
                        openness_score, conscientiousness_score, extraversion_score,
                        agreeableness_score, stability_score,
                        source, confidence_score,
                        last_analysis_at, created_at, updated_at
                    ) VALUES (
                        :id, :cid, :website,
                        NULL, NULL, NULL, NULL,
                        NULL, NULL, NULL,
                        NULL, NULL, NULL,
                        NULL, NULL,
                        'auto', 0.5,
                        :now, :now, :now
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "cid": cid_str,
                    "website": "https://legacy-t1101.example.com",
                    "now": now,
                },
            )
        finally:
            # Restaura o NOT NULL — a migração 130 já garante que linhas
            # existentes (incluindo a recém-inserida) NÃO podem mais ficar
            # NULL após este ponto, então re-aplicar é seguro APENAS se
            # nenhuma outra linha do banco ficou NULL no meio. Nossa linha
            # legacy fica NULL → não podemos re-aplicar NOT NULL sem antes
            # backfillá-la, o que destruiria o cenário do teste. Optamos
            # por NÃO restaurar dentro da transação do teste; o cleanup
            # deleta a linha e um teste subsequente que precise do NOT
            # NULL re-roda a migração 130 (idempotente). Para não deixar
            # o schema relaxado entre testes, restauramos APÓS deletar a
            # row legacy — isso acontece em ``_restore_not_null`` chamado
            # do cleanup.
            pass
        await session.commit()


async def _restore_not_null(SessionMaker) -> None:
    """Re-aplica NOT NULL nas colunas afrouxadas por _insert_legacy_culture_row.

    Roda DEPOIS do DELETE da row legacy (sem ela, todas as linhas
    remanescentes respeitam o NOT NULL — a migração 130 já backfillou
    quaisquer NULLs históricos). Idempotente: SET NOT NULL em coluna já
    NOT NULL é no-op em Postgres ≥ 9.4.

    **Fail-loud:** se SET NOT NULL falhar (típico: outro processo
    escreveu uma row com NULL entre nosso DELETE e este restore), o
    teste levanta — o estado relaxado entre testes é justamente o que
    queremos evitar. CI deve rodar isso em DB isolado pra que falhas
    aqui sejam atribuíveis.
    """
    failures: list[str] = []
    async with SessionMaker() as session:
        for col in _LEGACY_NULLABLE_COLS:
            try:
                await session.execute(
                    text(f'ALTER TABLE company_culture_profiles ALTER COLUMN "{col}" SET NOT NULL')
                )
            except Exception as exc:
                failures.append(f"{col}: {exc}")
        await session.commit()
    if failures:
        raise AssertionError(
            "Falha ao restaurar NOT NULL em company_culture_profiles após "
            "fixture legacy — schema pode ter ficado relaxado para os próximos "
            "testes. Detalhes:\n" + "\n".join(failures)
        )


async def _insert_populated_culture_row(SessionMaker, company_id: uuid.UUID) -> None:
    """Insere uma linha 'rica' com TODAS as colunas array/score preenchidas."""
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
                    'manual', 0.95,
                    :now, :now, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "cid": cid_str,
                "website": "https://rich-t1101.example.com",
                "mission": "Empower talent",
                "vision": "Better hiring for everyone",
                "values": ["transparency", "ownership"],
                "evp_bullets": ["Remote-first", "Aprendizado contínuo"],
                "core_competencies": ["communication", "delivery"],
                "analyzed_pages": ["https://rich-t1101.example.com/about"],
                "locations": ["São Paulo", "Recife"],
                "tech_stack": ["python", "react"],
                "default_languages": ["pt-BR", "en"],
                "openness": 73,
                "conscientiousness": 68,
                "extraversion": 55,
                "agreeableness": 62,
                "stability": 71,
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
        try:
            await session.execute(
                text("DELETE FROM company_culture_profiles WHERE company_id = :cid"),
                {"cid": cid_str},
            )
        except Exception:
            pass
        try:
            await session.execute(
                text("DELETE FROM company_profiles WHERE id = :cid"),
                {"cid": cid_str},
            )
        except Exception:
            pass
        try:
            await session.execute(
                text("DELETE FROM companies WHERE id = :cid"),
                {"cid": cid_str},
            )
        except Exception:
            pass
        await session.commit()


def _make_client(company_id: uuid.UUID, SessionMaker):
    """Constrói um TestClient com auth mockada e get_tenant_db apontando
    pro Postgres real (com `app.company_id` pré-vinculado)."""

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
        subject="user-1101",
        role="admin",
        company_id=str(company_id),
    )
    client = TestClient(app, raise_server_exceptions=False)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.mark.asyncio
async def test_get_culture_profile_legacy_db_row_serializes_with_defaults(
    pg_session_factory,
):
    """Caminho real: linha legada (NULLs nos arrays/scores) no Postgres
    → endpoint devolve HTTP 200 com defaults aplicados pelo schema."""
    SessionMaker = pg_session_factory
    company_id = uuid.uuid4()
    await _insert_company_and_profile(SessionMaker, company_id)
    await _insert_legacy_culture_row(SessionMaker, company_id)

    try:
        with patch("app.main.init_db", AsyncMock()):
            client = _make_client(company_id, SessionMaker)
            resp = client.get(f"/api/v1/company/culture-profile/{company_id}")
    finally:
        app.dependency_overrides.clear()
        await _cleanup(SessionMaker, company_id)
        # Re-aplica NOT NULL afrouxado por _insert_legacy_culture_row
        # APÓS o DELETE da linha legacy (pré-condição de segurança).
        await _restore_not_null(SessionMaker)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["website_url"] == "https://legacy-t1101.example.com"
    # Arrays vindos como NULL do banco devem ser coercidos pra []
    assert body["values"] == []
    assert body["evp_bullets"] == []
    assert body["core_competencies"] == []
    assert body["analyzed_pages"] == []
    assert body["locations"] == []
    assert body["tech_stack"] == []
    assert body["default_languages"] == []
    # Big-Five scores NULL → 50
    assert body["openness_score"] == 50
    assert body["conscientiousness_score"] == 50
    assert body["extraversion_score"] == 50
    assert body["agreeableness_score"] == 50
    assert body["stability_score"] == 50
    # Metadados que sobreviveram ao roundtrip
    assert body["source"] == "auto"
    assert str(uuid.UUID(body["company_id"])) == str(company_id)


@pytest.mark.asyncio
async def test_get_culture_profile_populated_db_row_passes_through(
    pg_session_factory,
):
    """Caminho real: linha rica (todos campos preenchidos) → pass-through
    sem clobber dos valores reais."""
    SessionMaker = pg_session_factory
    company_id = uuid.uuid4()
    await _insert_company_and_profile(SessionMaker, company_id)
    await _insert_populated_culture_row(SessionMaker, company_id)

    try:
        with patch("app.main.init_db", AsyncMock()):
            client = _make_client(company_id, SessionMaker)
            resp = client.get(f"/api/v1/company/culture-profile/{company_id}")
    finally:
        app.dependency_overrides.clear()
        await _cleanup(SessionMaker, company_id)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["website_url"] == "https://rich-t1101.example.com"
    assert body["mission"] == "Empower talent"
    assert body["vision"] == "Better hiring for everyone"
    assert body["values"] == ["transparency", "ownership"]
    assert body["evp_bullets"] == ["Remote-first", "Aprendizado contínuo"]
    assert body["core_competencies"] == ["communication", "delivery"]
    assert body["analyzed_pages"] == ["https://rich-t1101.example.com/about"]
    assert body["locations"] == ["São Paulo", "Recife"]
    assert body["tech_stack"] == ["python", "react"]
    assert body["default_languages"] == ["pt-BR", "en"]
    assert body["openness_score"] == 73
    assert body["conscientiousness_score"] == 68
    assert body["extraversion_score"] == 55
    assert body["agreeableness_score"] == 62
    assert body["stability_score"] == 71
    assert body["source"] == "manual"
    assert body["confidence_score"] == 0.95
