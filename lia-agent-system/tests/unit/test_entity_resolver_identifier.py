"""TDD Fase 1 Step 4 (2026-06-10, ADR-LGPD-002 resolve-then-strip):
resolver casa candidato por IDENTIFICADOR (CPF/email/telefone) via hash indexado,
nunca ecoando o identificador cru. Produtor unico: entity_resolver."""
import os
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("IS_DEVELOPMENT", "true")


def test_extract_identifiers_finds_cpf_email_phone():
    from app.shared.entity_resolver import _extract_identifiers

    cpfs, emails, phones = _extract_identifiers(
        "mova o candidato cpf 123.456.789-00 email joao@x.com tel 11999998888"
    )
    assert any("123" in c for c in cpfs), f"CPF não extraído: {cpfs}"
    assert "joao@x.com" in emails, f"email não extraído: {emails}"
    assert phones, f"telefone não extraído: {phones}"


def test_extract_identifiers_empty_when_none():
    from app.shared.entity_resolver import _extract_identifiers

    cpfs, emails, phones = _extract_identifiers("liste os candidatos da vaga android")
    assert cpfs == []
    assert emails == []


def _mock_db_returning(rows):
    obj = MagicMock()
    obj.mappings.return_value = rows
    db = MagicMock()
    db.execute = AsyncMock(return_value=obj)
    return db


async def test_resolve_by_cpf_returns_uuid_and_name():
    from app.shared.entity_resolver import _resolve_candidates_by_identifier

    db = _mock_db_returning([{"id": "uuid-1", "name": "Joao Silva", "name_encrypted": None}])
    cands = await _resolve_candidates_by_identifier(
        "mova o candidato cpf 123.456.789-00 para entrevista", "co-1", db
    )
    assert cands == [("uuid-1", "Joao Silva")]


async def test_resolve_by_identifier_never_echoes_raw_identifier_in_sql():
    """O identificador cru NUNCA pode ir nos params da query — só o hash (minimização)."""
    from app.shared.entity_resolver import _resolve_candidates_by_identifier

    db = _mock_db_returning([{"id": "uuid-1", "name": "Joao", "name_encrypted": None}])
    await _resolve_candidates_by_identifier(
        "candidato cpf 123.456.789-00 email joao@x.com", "co-1", db
    )
    params_str = str(db.execute.call_args)
    assert "123.456.789-00" not in params_str, "CPF formatado vazou nos params"
    assert "12345678900" not in params_str, "CPF dígitos vazou nos params"
    assert "joao@x.com" not in params_str, "email vazou nos params"


async def test_resolve_by_identifier_company_scoped():
    """A query DEVE ser company-scoped (multi-tenancy não-negociável)."""
    from app.shared.entity_resolver import _resolve_candidates_by_identifier

    db = _mock_db_returning([])
    await _resolve_candidates_by_identifier("cpf 123.456.789-00", "co-XYZ", db)
    call_str = str(db.execute.call_args)
    assert "co-XYZ" in call_str, "company_id deve estar nos params (company-scoped)"


async def test_resolve_no_identifier_returns_empty_no_query():
    from app.shared.entity_resolver import _resolve_candidates_by_identifier

    db = _mock_db_returning([])
    cands = await _resolve_candidates_by_identifier("liste candidatos da vaga X", "co-1", db)
    assert cands == []
    db.execute.assert_not_called()  # sem identificador → não consulta o banco


async def test_resolve_decrypts_name_when_encrypted():
    """Quando name plaintext é NULL (linha pós-migração), decripta name_encrypted p/ o hint."""
    from app.shared.entity_resolver import _resolve_candidates_by_identifier
    from app.shared.encryption.encrypted_field_mixin import _encrypt

    enc = _encrypt("Maria Souza")
    db = _mock_db_returning([{"id": "uuid-2", "name": None, "name_encrypted": enc}])
    cands = await _resolve_candidates_by_identifier("cpf 111.222.333-44", "co-1", db)
    assert cands == [("uuid-2", "Maria Souza")]
