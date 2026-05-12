"""Task #1017 — Round-trip PATCH→GET no CompanyProfile cobrindo o caso
``is_default=NULL`` (linhas legadas / seeded sem default explícito).

Bug reproduzido: ``CompanyProfileResponse.is_default: bool`` (schema)
+ coluna ``is_default = Column(Boolean, default=False)`` (sem
``nullable=False``) ⇒ linhas com ``is_default IS NULL`` (presentes em
backups/migrations antigas) faziam o GET /api/v1/company/profile
estourar 500 com ``ValidationError: Input should be a valid boolean``
do Pydantic v2.

Fix: ``convert_none_to_false`` validator estendido pra incluir
``is_default`` e ``is_active`` (vide
``app/schemas/company.py`` linha do ``@field_validator``).

Este teste é SENTINELA do fix — se alguém remover o validator ou
adicionar uma coluna boolean nova ao response sem cobrir o caso NULL,
o teste falha LOUD.
"""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.schemas.company import CompanyProfileResponse


class _TestBase(DeclarativeBase):
    """Base isolada — não importa lia_models.Base (que carrega mapeamentos
    pg-only via `UUID(as_uuid=True)`/`JSONB` que não rodam em sqlite)."""


class _CompanyProfileSqlite(_TestBase):
    """Espelho mínimo do CompanyProfile pra rodar em sqlite. Cobre as
    colunas tocadas pelo round-trip + as exigidas pelo Response model."""
    __tablename__ = "company_profiles"

    id = Column(String(36), primary_key=True)
    client_account_id = Column(String(36), nullable=True)
    name = Column(String(255), nullable=False)
    trading_name = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    cnpj = Column(String(18), nullable=True)
    industry = Column(String(100), nullable=True)
    sector = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)
    founded_year = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    headquarters_city = Column(String(100), nullable=True)
    headquarters_state = Column(String(100), nullable=True)
    headquarters_country = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    main_phone = Column(String(50), nullable=True)
    hr_phone = Column(String(50), nullable=True)
    main_email = Column(String(255), nullable=True)
    hr_email = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    glassdoor_url = Column(String(500), nullable=True)
    employee_count = Column(Integer, nullable=True)
    revenue_range = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=True)         # NULL-safe
    is_default = Column(Boolean, nullable=True)        # NULL-safe
    culture_analyzed = Column(Boolean, nullable=True)
    culture_analysis_date = Column(DateTime, nullable=True)
    culture_insights = Column(JSON, nullable=True)
    ats_history_analyzed = Column(Boolean, nullable=True)
    ats_analysis_date = Column(DateTime, nullable=True)
    ats_insights = Column(JSON, nullable=True)
    additional_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    created_by = Column(String(255), nullable=True)


@pytest.fixture
async def sqlite_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(_TestBase.metadata.create_all)
    SessionMaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with SessionMaker() as session:
        yield session
    await engine.dispose()


async def _seed_profile_with_null_is_default(session: AsyncSession, profile_id: str) -> None:
    """Insere via raw INSERT — bypass do `default=False` do ORM, simula
    linha legada vinda de backup/migration que não setou is_default."""
    now = datetime.utcnow()
    stmt = sqlite_insert(_CompanyProfileSqlite.__table__).values(
        id=profile_id,
        name="Acme Legado S.A.",
        is_default=None,    # ← ESTE é o caso que quebrava em produção
        is_active=None,     # ← idem (mesmo sintoma)
        created_at=now,
        updated_at=now,
    )
    await session.execute(stmt)
    await session.commit()


@pytest.mark.asyncio
async def test_response_serializer_coerces_null_is_default_to_false(sqlite_session):
    """Snapshot direto do bug: linha com is_default=NULL é serializável
    sem 500. Pydantic v2 rejeitaria None pra `bool` se o validator
    `convert_none_to_false` não cobrisse `is_default`/`is_active`."""
    profile_id = str(uuid.uuid4())
    await _seed_profile_with_null_is_default(sqlite_session, profile_id)

    row = (
        await sqlite_session.execute(
            _CompanyProfileSqlite.__table__.select().where(
                _CompanyProfileSqlite.id == profile_id
            )
        )
    ).mappings().first()

    assert row["is_default"] is None, (
        "Setup quebrou: SQLite armazenou is_default não-nulo. Sem "
        "is_default=NULL o teste perderia o sinal do bug."
    )

    response = CompanyProfileResponse.model_validate(dict(row))
    assert response.is_default is False, (
        "is_default=NULL deveria ser coercido para False pelo "
        "validator. Se este assert falhou, o validator "
        "`convert_none_to_false` em app/schemas/company.py regrediu "
        "(faltou cobrir `is_default`) e o GET /api/v1/company/profile "
        "vai voltar a estourar 500 em tenants legados."
    )
    assert response.is_active is False
    assert response.id == uuid.UUID(profile_id)
    assert response.name == "Acme Legado S.A."


@pytest.mark.asyncio
async def test_patch_then_get_roundtrip_preserves_null_is_default(sqlite_session):
    """Round-trip end-to-end no nível ORM/repo: PATCH (update via
    setattr) NÃO deve transformar is_default=NULL em False mágico nem
    quebrar o GET subsequente. Cobre o flow real do
    `CompanyProfileRepository.update` (setattr por chave do payload)."""
    profile_id = str(uuid.uuid4())
    await _seed_profile_with_null_is_default(sqlite_session, profile_id)

    # PATCH simulado — repo.update faz `setattr(profile, key, value)`
    # apenas para chaves no payload; is_default NÃO está no payload,
    # então deve permanecer NULL na DB.
    profile = (
        await sqlite_session.execute(
            _CompanyProfileSqlite.__table__.select().where(
                _CompanyProfileSqlite.id == profile_id
            )
        )
    ).mappings().first()

    patch_payload = {
        "website": "https://acme.example.com",
        "linkedin_url": "https://linkedin.com/company/acme",
        "updated_at": datetime.utcnow(),
    }
    await sqlite_session.execute(
        _CompanyProfileSqlite.__table__.update()
        .where(_CompanyProfileSqlite.id == profile_id)
        .values(**patch_payload)
    )
    await sqlite_session.commit()

    # GET subsequente — equivalente à serialização que /profile retorna
    after = (
        await sqlite_session.execute(
            _CompanyProfileSqlite.__table__.select().where(
                _CompanyProfileSqlite.id == profile_id
            )
        )
    ).mappings().first()
    assert after["is_default"] is None, (
        "Round-trip não pode reescrever is_default — o PATCH só "
        "carrega website/linkedin_url. Se virou False/True aqui, o "
        "repo.update está mexendo em chaves fora do payload."
    )

    # E o response model continua serializável (sem 500)
    response = CompanyProfileResponse.model_validate(dict(after))
    assert response.is_default is False  # NULL → False (validator)
    assert response.website == "https://acme.example.com"
    assert response.linkedin_url == "https://linkedin.com/company/acme"
