"""Task #1012 — prova de persistência REAL dos 3 campos da seção
"Remuneração & Onboarding" (`additional_notes`, `responsible_name`,
`responsible_position`) que vivem em `company_profiles.additional_data`.

Antes do PR7 (A5) esses campos caíam silenciosamente no `else` de
`_save_company_field_impl` — o YAML aponta para `save_company_field`,
o frontend exibe os campos no hub Minha Empresa, mas o save morria
sem ninguém perceber. PR7 introduziu `_PROFILE_ADDITIONAL_DATA_FIELDS`
+ `_build_profile_additional_data_queries` (`jsonb_set` parametrizado)
e um fallback no impl. Os testes existentes em
`test_company_settings_no_regression.py` provam o wiring estrutural
(whitelist tem os 3 campos, queries indexam por nome, fallback existe)
mas NÃO exercem o caminho contra um Postgres real.

Esta suíte fecha o gap: dispara `_save_company_field_impl` (mesmo
caminho que o wrapper `save_company_field` chama após o audit ctx)
contra o Postgres do CI usando `DATABASE_URL`, e valida via
`SELECT additional_data` que:

  1. additional_data NULL → preenchido com a chave correta no primeiro save
     (cobre o branch UPDATE com COALESCE(additional_data, '{}'::jsonb)).
  2. Save subsequente em campo diferente preserva o anterior
     (merge incremental via `jsonb_set` — anti-regressão para alguém
     que troque por sobrescrita simples).
  3. Os 3 campos coexistem após saves sequenciais, com os valores
     exatos persistidos.

Skip se `DATABASE_URL` ausente — espelha o mesmo skip de
`test_rls_candidates.py` para não quebrar o CI quando rodar fora do
ambiente com Postgres provisionado.
"""
from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.domains.company_settings.agents.company_tool_registry import (
    _PROFILE_ADDITIONAL_DATA_FIELDS,
    _save_company_field_impl,
)


pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — Postgres-backed integration test",
)


def _async_database_url() -> str:
    """Force the asyncpg driver — DATABASE_URL ships with the sync prefix
    `postgresql://` (psycopg2 default), but `create_async_engine` needs
    `postgresql+asyncpg://`. Also strip libpq-only query params
    (`sslmode`, `channel_binding`) que o asyncpg rejeita com
    `TypeError: connect() got an unexpected keyword argument 'sslmode'`."""
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

    url = os.environ["DATABASE_URL"]
    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"
    elif scheme == "postgresql+asyncpg":
        pass
    else:  # ex: postgresql+psycopg2 — normaliza pra asyncpg
        scheme = "postgresql+asyncpg"
    libpq_only = {"sslmode", "channel_binding", "gssencmode", "target_session_attrs"}
    query = urlencode([
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k not in libpq_only
    ])
    return urlunsplit((scheme, parts.netloc, parts.path, query, parts.fragment))


@pytest.fixture
async def pg_session():
    """One session per test bound to a dedicated asyncpg engine.

    NullPool keeps connections from leaking across tests when pytest
    creates/destroys the loop between cases."""
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(
        _async_database_url(), future=True, poolclass=NullPool
    )
    Maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    session = Maker()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()


@pytest.fixture
async def tenant_company_id(pg_session: AsyncSession):
    """Inserts a fresh `company_profiles` row with `additional_data`
    deliberately NULL so the first save in each test exercises the
    `COALESCE(additional_data, '{}'::jsonb)` branch. Cleans up after."""
    cid = uuid.uuid4()
    await pg_session.execute(
        text(
            "INSERT INTO company_profiles (id, name, is_active, created_at, updated_at) "
            "VALUES (:id, :name, true, NOW(), NOW())"
        ),
        {"id": cid, "name": f"Test Co {cid.hex[:8]}"},
    )
    await pg_session.commit()
    try:
        yield str(cid)
    finally:
        await pg_session.execute(
            text("DELETE FROM company_profiles WHERE id = :id"), {"id": cid}
        )
        await pg_session.commit()


async def _read_additional_data(
    session: AsyncSession, company_id: str
) -> dict | None:
    row = (
        await session.execute(
            text(
                "SELECT additional_data FROM company_profiles "
                "WHERE id::text = :id"
            ),
            {"id": company_id},
        )
    ).first()
    assert row is not None, f"company_profiles row sumiu para {company_id}"
    return row[0]


# ─── Sentinela do contrato — whitelist permanece com os 3 campos ─────────


def test_whitelist_covers_remuneration_section_fields():
    """Sanity check: se alguém remover um campo do
    `_PROFILE_ADDITIONAL_DATA_FIELDS`, todos os asserts abaixo passariam
    a falhar com mensagens crípticas. Esta linha localiza a regressão
    no exato local."""
    assert _PROFILE_ADDITIONAL_DATA_FIELDS == frozenset({
        "additional_notes",
        "responsible_name",
        "responsible_position",
    }), (
        "Whitelist de additional_data divergiu do esperado. "
        "Atualizar este teste *e* o bloco YAML de Remuneração & Onboarding."
    )


# ─── Cenário 1: additional_data NULL → preenchido (cada um dos 3 campos) ──


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "additional_notes",
            "Equipe trabalha em formato hibrido com escritorio em SP.",
        ),
        ("responsible_name", "Maria Souza"),
        ("responsible_position", "Head de Recursos Humanos"),
    ],
)
async def test_save_fills_null_additional_data(
    pg_session: AsyncSession,
    tenant_company_id: str,
    field: str,
    value: str,
):
    """Cada um dos 3 campos: additional_data NULL → JSON com a chave
    correta. Antes do PR7 isso retornava
    `"Campo '<x>' nao e valido para perfil"` e o DB não mudava."""
    pre = await _read_additional_data(pg_session, tenant_company_id)
    assert pre is None, (
        "Fixture deveria deixar additional_data NULL — alguem mexeu na "
        "criacao da row e o teste perdeu o branch COALESCE."
    )

    result = await _save_company_field_impl(
        session=pg_session,
        company_id=tenant_company_id,
        section="profile",
        field=field,
        value=value,
    )
    assert result["success"] is True, (
        f"_save_company_field_impl falhou para {field!r}: {result!r}. "
        "Possivel regressao no fallback A5 ou no FairnessGuard recursivo."
    )
    await pg_session.commit()

    persisted = await _read_additional_data(pg_session, tenant_company_id)
    assert isinstance(persisted, dict), (
        f"additional_data continua nulo/invalido apos save: {persisted!r}"
    )
    assert persisted.get(field) == value, (
        f"Campo {field!r} nao foi persistido. Esperado={value!r}, "
        f"obtido additional_data={persisted!r}"
    )


# ─── Cenário 2: merge incremental preserva campos previamente salvos ─────


async def test_incremental_saves_merge_without_overwriting(
    pg_session: AsyncSession,
    tenant_company_id: str,
):
    """Salva os 3 campos em sequencia e valida que cada save preserva
    os anteriores — anti-regressao para qualquer mudanca futura que
    troque `jsonb_set` por sobrescrita direta da coluna inteira."""
    saves = [
        ("responsible_name", "Maria Souza"),
        ("responsible_position", "Head de Recursos Humanos"),
        (
            "additional_notes",
            "Onboarding remoto + buddy nas duas primeiras semanas.",
        ),
    ]

    accumulated: dict[str, str] = {}
    for field, value in saves:
        result = await _save_company_field_impl(
            session=pg_session,
            company_id=tenant_company_id,
            section="profile",
            field=field,
            value=value,
        )
        assert result["success"] is True, (
            f"Save incremental falhou em {field!r}: {result!r}"
        )
        await pg_session.commit()
        accumulated[field] = value

        persisted = await _read_additional_data(pg_session, tenant_company_id)
        assert isinstance(persisted, dict)
        for prev_field, prev_value in accumulated.items():
            assert persisted.get(prev_field) == prev_value, (
                f"Apos salvar {field!r}, campo anterior {prev_field!r} foi "
                f"sobrescrito ou perdido. additional_data={persisted!r}"
            )

    # Estado final: 3 chaves coexistem com seus valores exatos.
    final = await _read_additional_data(pg_session, tenant_company_id)
    assert final == accumulated, (
        f"Estado final do additional_data divergiu do esperado.\n"
        f"  esperado: {accumulated!r}\n"
        f"  obtido:   {final!r}"
    )
