"""Fase 1 (2026-06-10): CPF/phone hash columns + helpers para entity-resolution por
identificador no chat (resolve-then-strip, ADR-LGPD-002). Metadata + helper tests, no DB.
Espelha convenções de tests/unit/test_candidate_encryption.py."""
import os

os.environ.setdefault("IS_DEVELOPMENT", "true")


def test_cpf_hash_column_exists_indexed():
    from app.models.candidate import Candidate

    col = Candidate.__table__.c.get("cpf_hash")
    assert col is not None, (
        "Candidate must have indexed 'cpf_hash' column (migration 259). "
        "Add cpf_hash = Column(String(64), index=True) + triple ('_cpf_raw','_cpf_encrypted','cpf_hash')."
    )
    assert col.index is True, "cpf_hash must be indexed for lookup"


def test_phone_hash_column_exists_indexed():
    from app.models.candidate import Candidate

    col = Candidate.__table__.c.get("phone_hash")
    assert col is not None, (
        "Candidate must have indexed 'phone_hash' column (migration 259)."
    )
    assert col.index is True, "phone_hash must be indexed for lookup"


def test_pii_fields_spec_includes_cpf_phone_hash():
    from app.models.candidate import Candidate

    spec = {s[0]: s[2] for s in Candidate._pii_encrypt_fields}
    assert spec.get("_cpf_raw") == "cpf_hash", "_cpf_raw triple must point hash_attr to cpf_hash"
    assert spec.get("_phone_raw") == "phone_hash", "_phone_raw triple must point hash_attr to phone_hash"
    # email_hash must remain intact (no regression)
    assert spec.get("_email_raw") == "email_hash"


def test_cpf_hash_for_normalizes_digits_only():
    """Formatted CPF and raw digits must produce the SAME hash (resolve-then-strip needs this)."""
    from app.models.candidate import Candidate

    h1 = Candidate.cpf_hash_for("123.456.789-00")
    h2 = Candidate.cpf_hash_for("12345678900")
    assert h1 is not None
    assert h1 == h2, "CPF hash must be format-insensitive (digits-only canonical)"


def test_phone_hash_for_normalizes_format_and_country_code():
    """+55 (11) 99999-9999 and 11999999999 must match (BR normalization)."""
    from app.models.candidate import Candidate

    h1 = Candidate.phone_hash_for("+55 (11) 99999-9999")
    h2 = Candidate.phone_hash_for("11999999999")
    assert h1 is not None
    assert h1 == h2, "Phone hash must normalize BR country code + formatting"


def test_identity_hashes_differ_by_value():
    from app.models.candidate import Candidate

    assert Candidate.cpf_hash_for("12345678900") != Candidate.cpf_hash_for("00987654321")


def test_email_hash_for_unchanged():
    """Regression guard: email_hash_for must still be strip+lower (not digits-only)."""
    from app.models.candidate import Candidate

    assert Candidate.email_hash_for("  Joao@X.COM ") == Candidate.email_hash_for("joao@x.com")


def test_none_inputs_return_none():
    from app.models.candidate import Candidate

    assert Candidate.cpf_hash_for(None) is None
    assert Candidate.phone_hash_for(None) is None


def test_write_populates_cpf_and_phone_hash():
    """Write-path: setting cpf/phone on an instance populates the hash columns."""
    from app.models.candidate import Candidate

    c = Candidate()
    c.cpf = "123.456.789-00"
    c.phone = "+55 11 99999-9999"
    assert c.cpf_hash == Candidate.cpf_hash_for("12345678900")
    assert c.phone_hash == Candidate.phone_hash_for("11999999999")
