"""UC-P0-14: Candidate must have legal_basis_id and consent_version_id columns.

Uses metadata.tables inspection to avoid SQLAlchemy double-registration errors
(models are already loaded by pytest session before these tests run).
"""
import pytest


def _candidate_col_names():
    """Return column names from the candidates table via already-loaded metadata."""
    from app.models.candidate import Candidate
    return [c.name for c in Candidate.__table__.columns]


def _lgpd_legal_bases_col_names():
    """Return column names for lgpd_legal_bases table."""
    from app.models.lgpd_references import LegalBasis
    return [c.name for c in LegalBasis.__table__.columns]


def _lgpd_consent_versions_col_names():
    """Return column names for lgpd_consent_versions table."""
    from app.models.lgpd_references import ConsentVersion
    return [c.name for c in ConsentVersion.__table__.columns]


def test_candidate_has_legal_basis_id():
    """Candidate model must have legal_basis_id column (LGPD Art.18)."""
    col_names = _candidate_col_names()
    assert 'legal_basis_id' in col_names, (
        "Candidate must have legal_basis_id FK (LGPD Art.18). "
        "Run migration 108_lgpd_legal_basis_candidate."
    )


def test_candidate_has_consent_version_id():
    """Candidate model must have consent_version_id column (LGPD Art.18)."""
    col_names = _candidate_col_names()
    assert 'consent_version_id' in col_names, (
        "Candidate must have consent_version_id FK (LGPD Art.18). "
        "Run migration 108_lgpd_legal_basis_candidate."
    )


def test_lgpd_legal_bases_table_exists():
    """LegalBasis model must have correct table name."""
    from app.models.lgpd_references import LegalBasis
    assert LegalBasis.__tablename__ == "lgpd_legal_bases"


def test_lgpd_consent_versions_table_exists():
    """ConsentVersion model must have correct table name."""
    from app.models.lgpd_references import ConsentVersion
    assert ConsentVersion.__tablename__ == "lgpd_consent_versions"


def test_legal_basis_columns():
    """LegalBasis model must have all required LGPD Art.7 columns."""
    col_names = _lgpd_legal_bases_col_names()
    assert 'code' in col_names, "LegalBasis must have code column"
    assert 'description_pt' in col_names, "LegalBasis must have description_pt column"
    assert 'lgpd_article' in col_names, "LegalBasis must have lgpd_article column"
    assert 'active' in col_names, "LegalBasis must have active column"


def test_consent_version_columns():
    """ConsentVersion model must have all required tracking columns."""
    col_names = _lgpd_consent_versions_col_names()
    assert 'version' in col_names, "ConsentVersion must have version column"
    assert 'effective_from' in col_names, "ConsentVersion must have effective_from column"
    assert 'content_hash' in col_names, "ConsentVersion must have content_hash column"
    assert 'active' in col_names, "ConsentVersion must have active column"


def test_legal_basis_id_is_nullable():
    """legal_basis_id must be nullable (backfill happens separately)."""
    from app.models.candidate import Candidate
    col = Candidate.__table__.columns.get("legal_basis_id")
    assert col is not None, "legal_basis_id column not found"
    assert col.nullable is True, "legal_basis_id must be nullable (LGPD backfill constraint)"


def test_consent_version_id_is_nullable():
    """consent_version_id must be nullable (not required when basis != consent)."""
    from app.models.candidate import Candidate
    col = Candidate.__table__.columns.get("consent_version_id")
    assert col is not None, "consent_version_id column not found"
    assert col.nullable is True, "consent_version_id must be nullable (only required when basis=consent)"
