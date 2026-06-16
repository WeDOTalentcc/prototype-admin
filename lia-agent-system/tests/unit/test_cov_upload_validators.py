"""Coverage tests for upload_validators.py — magic-number file validation."""
import io
import zipfile
import pytest

from app.shared.upload_validators import (
    UnsupportedFileTypeError,
    ValidatedFile,
    _looks_like_text,
    _is_docx,
    _is_pdf,
    validate_upload,
)

# ─── _looks_like_text ────────────────────────────────────────────────────────

class TestLooksLikeText:
    def test_empty_returns_false(self):
        assert _looks_like_text(b"") is False

    def test_valid_utf8_returns_true(self):
        assert _looks_like_text(b"Hello World\n") is True

    def test_nul_byte_returns_false(self):
        assert _looks_like_text(b"Header\x00Rest") is False

    def test_pure_binary_returns_false(self):
        # Binary garbage with lots of control chars
        assert _looks_like_text(bytes(range(256)) * 10) is False

    def test_portuguese_utf8_returns_true(self):
        text = "Olá, este é um currículo em português!\n".encode("utf-8")
        assert _looks_like_text(text) is True

    def test_short_latin1_text_returns_true(self):
        # Latin-1 content without NUL bytes should be accepted
        content = b"Resumo profissional\nExperiencia: 5 anos\n"
        assert _looks_like_text(content) is True


# ─── _is_pdf ─────────────────────────────────────────────────────────────────

class TestIsPdf:
    def test_valid_pdf_magic(self):
        assert _is_pdf(b"%PDF-1.4 header content") is True

    def test_wrong_magic(self):
        assert _is_pdf(b"PK\x03\x04") is False

    def test_empty_bytes(self):
        assert _is_pdf(b"") is False

    def test_text_file(self):
        assert _is_pdf(b"Hello World") is False


# ─── _is_docx ────────────────────────────────────────────────────────────────

def _make_valid_docx() -> bytes:
    """Create a minimal valid DOCX (ZIP with Content_Types.xml)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        zf.writestr("word/document.xml", "<document/>")
    return buf.getvalue()


class TestIsDocx:
    def test_valid_docx_returns_true(self):
        assert _is_docx(_make_valid_docx()) is True

    def test_generic_zip_without_manifest_returns_false(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("data.json", "{}")
        assert _is_docx(buf.getvalue()) is False

    def test_pdf_bytes_returns_false(self):
        assert _is_docx(b"%PDF-1.4") is False

    def test_plain_text_returns_false(self):
        assert _is_docx(b"Hello World") is False


# ─── validate_upload ─────────────────────────────────────────────────────────

class TestValidateUpload:
    def test_unsupported_extension_raises(self):
        with pytest.raises(UnsupportedFileTypeError) as exc_info:
            validate_upload("malware.exe", b"\x4d\x5a")
        assert exc_info.value.declared_ext == ".exe"

    def test_empty_content_raises(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("doc.pdf", b"")

    def test_valid_pdf(self):
        result = validate_upload("resume.pdf", b"%PDF-1.4 content")
        assert isinstance(result, ValidatedFile)
        assert result.extension == ".pdf"
        assert "pdf" in result.mime

    def test_invalid_pdf_magic_raises(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("resume.pdf", b"Not a PDF!")

    def test_valid_docx(self):
        docx_bytes = _make_valid_docx()
        result = validate_upload("cv.docx", docx_bytes)
        assert result.extension == ".docx"

    def test_invalid_docx_raises(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("cv.docx", b"Not a DOCX")

    def test_valid_txt(self):
        result = validate_upload("notes.txt", b"Hello world text")
        assert result.extension == ".txt"

    def test_valid_md(self):
        result = validate_upload("README.md", b"# Title\nContent here")
        assert result.extension == ".md"

    def test_binary_as_txt_raises(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("file.txt", b"Binary\x00garbage\xff" * 100)

    def test_filename_without_extension_raises(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("noextension", b"content")

    def test_case_insensitive_extension(self):
        result = validate_upload("file.PDF", b"%PDF-1.4 content")
        assert result.extension == ".pdf"


# ─── UnsupportedFileTypeError ────────────────────────────────────────────────

class TestUnsupportedFileTypeError:
    def test_has_declared_ext(self):
        err = UnsupportedFileTypeError("bad file", declared_ext=".exe")
        assert err.declared_ext == ".exe"

    def test_str_message(self):
        err = UnsupportedFileTypeError("bad file")
        assert str(err) == "bad file"

    def test_declared_ext_none_by_default(self):
        err = UnsupportedFileTypeError("oops")
        assert err.declared_ext is None


# ─── ValidatedFile dataclass ─────────────────────────────────────────────────

class TestValidatedFile:
    def test_frozen_dataclass(self):
        vf = ValidatedFile(extension=".pdf", mime="application/pdf")
        assert vf.extension == ".pdf"
        with pytest.raises(Exception):
            vf.extension = ".docx"  # type: ignore — frozen
