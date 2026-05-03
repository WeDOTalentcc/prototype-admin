"""UC-P1-15: Candidate name/phone must be stored encrypted (EncryptedFieldMixin).

These tests run without a DB connection — they inspect model metadata only.
Import via app.models shim to avoid double-MetaData registration.
"""
import os
import pytest

# Ensure IS_DEVELOPMENT=true so EncryptedFieldMixin doesn't fail on missing key
os.environ.setdefault("IS_DEVELOPMENT", "true")


def test_candidate_name_encrypted_column_exists():
    """name_encrypted LargeBinary column must exist on candidates table."""
    from app.models.candidate import Candidate

    enc_col = Candidate.__table__.c.get("name_encrypted")
    assert enc_col is not None, (
        "Candidate must have a 'name_encrypted' LargeBinary column (added by migration 111). "
        "Apply EncryptedFieldMixin to name field."
    )

    from sqlalchemy import LargeBinary
    assert isinstance(enc_col.type, LargeBinary), (
        f"name_encrypted column type {type(enc_col.type).__name__} must be LargeBinary"
    )


def test_candidate_phone_encrypted_column_exists():
    """phone_encrypted LargeBinary column must exist on candidates table."""
    from app.models.candidate import Candidate

    enc_col = Candidate.__table__.c.get("phone_encrypted")
    assert enc_col is not None, (
        "Candidate must have a 'phone_encrypted' LargeBinary column (added by migration 111). "
        "Apply EncryptedFieldMixin to phone field."
    )

    from sqlalchemy import LargeBinary
    assert isinstance(enc_col.type, LargeBinary), (
        f"phone_encrypted column type {type(enc_col.type).__name__} must be LargeBinary"
    )


def test_candidate_name_pii_fields_spec():
    """_pii_encrypt_fields must include name and phone specs."""
    from app.models.candidate import Candidate

    field_names = [spec[0] for spec in Candidate._pii_encrypt_fields]
    assert "_name_raw" in field_names, (
        "Candidate._pii_encrypt_fields must include _name_raw entry. "
        "Add ('_name_raw', '_name_encrypted', None) to _pii_encrypt_fields."
    )
    assert "_phone_raw" in field_names, (
        "Candidate._pii_encrypt_fields must include _phone_raw entry. "
        "Add ('_phone_raw', '_phone_encrypted', None) to _pii_encrypt_fields."
    )


def test_candidate_name_is_hybrid_property():
    """Candidate.name must be a hybrid_property (not plain Column) for transparent encryption."""
    from app.models.candidate import Candidate

    name_attr = Candidate.__dict__.get("name")
    assert name_attr is not None, "Candidate.name must be defined on the class"
    assert hasattr(name_attr, "fget"), (
        f"Candidate.name must be a hybrid_property (has fget), got {type(name_attr).__name__}. "
        "Rename column to _name_raw and let EncryptedFieldMixin register 'name' as hybrid_property."
    )


def test_candidate_phone_is_hybrid_property():
    """Candidate.phone must be a hybrid_property for transparent encryption."""
    from app.models.candidate import Candidate

    phone_attr = Candidate.__dict__.get("phone")
    assert phone_attr is not None, "Candidate.phone must be defined on the class"
    assert hasattr(phone_attr, "fget"), (
        f"Candidate.phone must be a hybrid_property (has fget), got {type(phone_attr).__name__}. "
        "Rename column to _phone_raw and let EncryptedFieldMixin register 'phone' as hybrid_property."
    )
