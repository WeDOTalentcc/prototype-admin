"""Magic-number upload validation (Audit A-02 / Task #858).

Validates that `app.shared.upload_validators.validate_upload` rejects payloads
whose actual bytes do not match the declared extension and accepts legitimate
PDF / DOCX / TXT samples.

This is the unit-level gate that protects pypdf / python-docx from being
fed an `.exe` renamed as `.pdf` (the original A-02 threat).
"""
from __future__ import annotations

import io
import zipfile

import pytest

from app.shared.upload_validators import (
    UnsupportedFileTypeError,
    validate_upload,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


def _build_minimal_pdf() -> bytes:
    """A tiny but legitimate PDF that pypdf can open."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Count 0 /Kids [] >> endobj\n"
        b"xref\n0 3\n0000000000 65535 f \n"
        b"0000000009 00000 n \n0000000063 00000 n \n"
        b"trailer << /Size 3 /Root 1 0 R >> startxref 110\n%%EOF"
    )


def _build_minimal_docx() -> bytes:
    """A ZIP with the OOXML manifest entry — passes our docx detector."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
            "</Types>",
        )
        zf.writestr("word/document.xml", "<w:document/>")
    return buffer.getvalue()


def _build_plain_text() -> bytes:
    return "Vaga de Engenheiro de Software\nResponsabilidades:\n- Codar".encode("utf-8")


def _build_fake_pdf_actually_exe() -> bytes:
    """Windows PE header — the classic A-02 attack."""
    return b"MZ\x90\x00" + b"\x00" * 4096


def _build_fake_docx_random_zip() -> bytes:
    """A real ZIP but missing the OOXML manifest entry."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("readme.txt", "not a docx")
    return buffer.getvalue()


def _build_fake_text_with_nul() -> bytes:
    return b"abc\x00binary\x00garbage" + b"\x00" * 100


# --------------------------------------------------------------------------- #
# Happy path
# --------------------------------------------------------------------------- #


class TestValidUploads:
    def test_pdf_accepted(self):
        result = validate_upload("vaga.pdf", _build_minimal_pdf())
        assert result.extension == ".pdf"
        assert result.mime == "application/pdf"

    def test_docx_accepted(self):
        result = validate_upload("vaga.docx", _build_minimal_docx())
        assert result.extension == ".docx"

    def test_txt_accepted(self):
        result = validate_upload("vaga.txt", _build_plain_text())
        assert result.extension == ".txt"

    def test_md_accepted(self):
        result = validate_upload("vaga.md", b"# Vaga\nDescricao")
        assert result.extension == ".md"


# --------------------------------------------------------------------------- #
# Bypass attempts (the actual A-02 threat)
# --------------------------------------------------------------------------- #


class TestBypassAttempts:
    def test_exe_renamed_to_pdf_blocked(self):
        with pytest.raises(UnsupportedFileTypeError) as exc:
            validate_upload("payload.pdf", _build_fake_pdf_actually_exe())
        assert "PDF" in str(exc.value).upper() or "assinatura" in str(exc.value).lower()

    def test_random_zip_renamed_to_docx_blocked(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("vaga.docx", _build_fake_docx_random_zip())

    def test_binary_renamed_to_txt_blocked(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("notes.txt", _build_fake_text_with_nul())

    def test_unknown_extension_blocked(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("payload.exe", b"MZ\x90\x00")

    def test_empty_payload_blocked(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("vaga.pdf", b"")

    def test_pdf_with_wrong_extension_blocked(self):
        # PDF bytes uploaded as .docx — must be rejected because we trust the
        # declared extension as the routing key, not the magic alone.
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("vaga.docx", _build_minimal_pdf())


# --------------------------------------------------------------------------- #
# Zip bomb safeguard (the B-02 secondary risk surface)
# --------------------------------------------------------------------------- #


class TestZipBombSafeguard:
    def test_extreme_compression_ratio_rejected(self):
        """A ZIP with a massively compressible entry trips the ratio guard."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "[Content_Types].xml",
                "<?xml version=\"1.0\"?><Types/>",
            )
            # 5 MiB of 'A' compresses to a few hundred bytes — ratio > 200.
            zf.writestr("bomb.txt", "A" * (5 * 1024 * 1024))
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("vaga.docx", buffer.getvalue())
