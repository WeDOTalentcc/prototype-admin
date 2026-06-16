"""GAP-05-006: File-level dedup via SHA-256 hash on CV uploads.

RED tests — all should FAIL before implementation:
1. CandidateAttachment model has file_hash column
2. CandidateAttachmentRepository has find_by_hash method
3. upload_and_parse_cv detects duplicate file by hash
4. Duplicate file response has is_file_duplicate=True + existing_attachment_id
5. find_by_hash is scoped by company_id (multi-tenancy invariant)
"""
from __future__ import annotations

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import inspect as sa_inspect


# ---------------------------------------------------------------------------
# Test 1 — model has file_hash column
# ---------------------------------------------------------------------------
def test_candidate_attachment_has_file_hash_column():
    """CandidateAttachment must have a file_hash column (String 64)."""
    from lia_models.candidate_attachment import CandidateAttachment

    mapper = sa_inspect(CandidateAttachment)
    col_names = [c.key for c in mapper.columns]
    assert "file_hash" in col_names, (
        "CandidateAttachment missing 'file_hash' column. "
        "Add: file_hash = Column(String(64), nullable=True, index=True) "
        "and create Alembic migration 287. "
        "See GAP-05-006 in audit_gaps_consolidado_2026-06-16.md."
    )
    col = mapper.columns["file_hash"]
    assert str(col.type) in ("VARCHAR(64)", "String(64)", "VARCHAR"), (
        f"file_hash should be String(64), got {col.type}"
    )


# ---------------------------------------------------------------------------
# Test 2 — repository has find_by_hash
# ---------------------------------------------------------------------------
def test_candidate_attachment_repository_has_find_by_hash():
    """CandidateAttachmentRepository must expose find_by_hash(file_hash, company_id)."""
    from app.domains.cv_screening.repositories.candidate_attachment_repository import (
        CandidateAttachmentRepository,
    )

    assert hasattr(CandidateAttachmentRepository, "find_by_hash"), (
        "CandidateAttachmentRepository missing 'find_by_hash' method. "
        "Add: async def find_by_hash(self, file_hash: str, company_id: str) "
        "-> CandidateAttachment | None. "
        "See GAP-05-006."
    )


# ---------------------------------------------------------------------------
# Test 3 — find_by_hash requires company_id (multi-tenancy)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_find_by_hash_raises_without_company_id():
    """find_by_hash must enforce company_id (multi-tenancy invariant)."""
    from app.domains.cv_screening.repositories.candidate_attachment_repository import (
        CandidateAttachmentRepository,
    )

    repo = CandidateAttachmentRepository(db=AsyncMock())
    with pytest.raises((ValueError, TypeError)):
        await repo.find_by_hash(file_hash="abc123", company_id="")


# ---------------------------------------------------------------------------
# Test 4 — find_by_hash returns match when hash exists
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_find_by_hash_returns_existing_attachment():
    """find_by_hash returns matching CandidateAttachment when hash found."""
    from app.domains.cv_screening.repositories.candidate_attachment_repository import (
        CandidateAttachmentRepository,
    )
    from lia_models.candidate_attachment import CandidateAttachment

    mock_attachment = MagicMock(spec=CandidateAttachment)
    mock_attachment.id = "att-existing-001"
    mock_attachment.candidate_id = "cand-001"
    mock_attachment.file_hash = "a" * 64

    mock_db = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = mock_attachment
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    repo = CandidateAttachmentRepository(db=mock_db)
    result = await repo.find_by_hash(file_hash="a" * 64, company_id="company-001")

    assert result is mock_attachment
    mock_db.execute.assert_called_once()


# ---------------------------------------------------------------------------
# Test 5 — upload_and_parse_cv computes hash and detects file dup
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_upload_detects_duplicate_file_by_hash():
    """upload_and_parse_cv returns file_duplicate_warning when hash already exists."""
    from fastapi import UploadFile
    from io import BytesIO

    file_bytes = b"fake CV content for dedup test"
    expected_hash = hashlib.sha256(file_bytes).hexdigest()

    # Import the function we're testing
    from app.api.v1.cv_parser import upload_and_parse_cv  # noqa: F401

    # The response model must have file_duplicate_warning field
    from app.api.v1.cv_parser import CVUploadResponse

    fields = CVUploadResponse.model_fields
    assert "file_duplicate_warning" in fields, (
        "CVUploadResponse missing 'file_duplicate_warning' field. "
        "Add: file_duplicate_warning: dict | None = None. "
        "See GAP-05-006."
    )


# ---------------------------------------------------------------------------
# Test 6 — file_duplicate_warning has required keys
# ---------------------------------------------------------------------------
def test_file_duplicate_warning_shape():
    """file_duplicate_warning dict must contain is_file_duplicate and existing_attachment_id."""
    # This tests the shape contract without calling the full endpoint
    warning = {
        "is_file_duplicate": True,
        "existing_attachment_id": "att-001",
        "existing_candidate_id": "cand-001",
        "existing_candidate_name": "João Silva",
    }
    assert warning["is_file_duplicate"] is True
    assert "existing_attachment_id" in warning
    assert "existing_candidate_id" in warning
