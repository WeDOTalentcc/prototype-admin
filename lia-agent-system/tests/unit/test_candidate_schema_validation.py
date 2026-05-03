"""TDD: CandidateCreate email format validation. UC-P1-30"""
import pytest
from pydantic import ValidationError


def test_invalid_email_rejected():
    from app.schemas.candidate import CandidateCreate
    with pytest.raises(ValidationError, match="email"):
        CandidateCreate(name="Test", source="manual", email="not-an-email")


def test_valid_email_accepted():
    from app.schemas.candidate import CandidateCreate
    c = CandidateCreate(name="Test", source="manual", email="valid@example.com")
    assert c.email == "valid@example.com"


def test_none_email_allowed():
    from app.schemas.candidate import CandidateCreate
    c = CandidateCreate(name="Test", source="manual", email=None)
    assert c.email is None


def test_email_normalized_lowercase():
    from app.schemas.candidate import CandidateCreate
    c = CandidateCreate(name="Test", source="manual", email="USER@EXAMPLE.COM")
    assert c.email == "user@example.com"


def test_empty_string_email_rejected():
    from app.schemas.candidate import CandidateCreate
    with pytest.raises(ValidationError):
        CandidateCreate(name="Test", source="manual", email="")


def test_email_with_spaces_stripped_and_valid():
    from app.schemas.candidate import CandidateCreate
    c = CandidateCreate(name="Test", source="manual", email="  user@domain.com  ")
    assert c.email == "user@domain.com"


def test_email_missing_at_rejected():
    from app.schemas.candidate import CandidateCreate
    with pytest.raises(ValidationError):
        CandidateCreate(name="Test", source="manual", email="nodomain")


def test_email_missing_tld_rejected():
    from app.schemas.candidate import CandidateCreate
    with pytest.raises(ValidationError):
        CandidateCreate(name="Test", source="manual", email="user@nodot")
