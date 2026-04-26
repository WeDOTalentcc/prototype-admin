"""Magic-number validation for uploaded files (Audit A-02).

Validating only by filename extension lets an attacker rename ``payload.exe``
to ``vaga.pdf`` and slip past the whitelist. This module sniffs the first
bytes of the payload to confirm the declared extension matches the actual
content type before any heavy parsing (pypdf / python-docx) runs.

Detection strategy:
* PDF — sniff ``%PDF-`` magic header.
* DOCX — sniff ZIP magic (``PK\x03\x04``) and verify the ``[Content_Types].xml``
  entry exists in the central directory (rules out generic ZIPs and
  protects parsers from random ZIP payloads).
* TXT/MD — reject if the bytes contain NUL or non-printable control
  characters that indicate a binary blob renamed as text.

The optional `filetype` library is used as a sanity check when present.
The validator never mutates the bytes; it returns the canonical extension
or raises ``UnsupportedFileTypeError`` so the endpoint can return ``415``.
"""
from __future__ import annotations

import io
import logging
import zipfile
from dataclasses import dataclass
from typing import Final

logger = logging.getLogger(__name__)


class UnsupportedFileTypeError(Exception):
    """Raised when the bytes do not match the declared/allowed extension."""

    def __init__(self, message: str, *, declared_ext: str | None = None) -> None:
        super().__init__(message)
        self.declared_ext = declared_ext


@dataclass(frozen=True)
class ValidatedFile:
    """Result of a successful magic-number check."""

    extension: str  # canonical, includes leading dot (e.g. ".pdf")
    mime: str


_PDF_MAGIC: Final[bytes] = b"%PDF-"
_ZIP_MAGIC: Final[bytes] = b"PK\x03\x04"
_OOXML_MARKER: Final[str] = "[Content_Types].xml"

_ALLOWED_EXTENSIONS: Final[frozenset[str]] = frozenset({".txt", ".md", ".pdf", ".docx"})


def _looks_like_text(content: bytes, sample_size: int = 4096) -> bool:
    """Heuristic for plain-text payloads.

    A renamed binary will almost always carry NUL bytes or a high
    proportion of non-printable bytes in the first few KiB. We allow
    standard whitespace (\\n, \\r, \\t) and any UTF-8 sequence.
    """
    if not content:
        return False
    sample = content[:sample_size]
    if b"\x00" in sample:
        return False
    try:
        sample.decode("utf-8")
        return True
    except UnicodeDecodeError:
        # Allow latin-1 / cp1252 fallback if no NUL bytes were seen.
        printable = sum(1 for b in sample if b == 9 or b == 10 or b == 13 or 32 <= b < 127 or b >= 128)
        return printable / max(1, len(sample)) >= 0.85


def _is_docx(content: bytes) -> bool:
    """A real DOCX is a ZIP that contains the OOXML manifest entry."""
    if not content.startswith(_ZIP_MAGIC):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = archive.namelist()
            if _OOXML_MARKER not in names:
                return False
            # Refuse archives that look like zip bombs (compression ratio).
            for info in archive.infolist():
                if info.compress_size and info.file_size:
                    ratio = info.file_size / info.compress_size
                    if ratio > 200:  # pragma: no cover — defensive
                        return False
            return True
    except (zipfile.BadZipFile, RuntimeError, OSError):
        return False


def _is_pdf(content: bytes) -> bool:
    return content.startswith(_PDF_MAGIC)


def _filetype_kind(content: bytes) -> str | None:
    """Use the optional `filetype` library when available as a sanity check."""
    try:  # pragma: no cover — exercised in environments with `filetype`
        import filetype  # type: ignore[import]

        kind = filetype.guess(content[:4096])
        if kind is not None:
            return kind.extension
        return None
    except Exception:
        return None


def validate_upload(
    filename: str,
    content: bytes,
    *,
    allowed_extensions: frozenset[str] = _ALLOWED_EXTENSIONS,
) -> ValidatedFile:
    """Validate the upload by magic number, returning the canonical extension.

    Raises ``UnsupportedFileTypeError`` if the bytes do not match the
    declared extension or if the extension is not whitelisted. Callers
    should map the exception to a 415 response.
    """
    declared_ext = ""
    if "." in (filename or ""):
        declared_ext = "." + filename.rsplit(".", 1)[-1].lower()

    if declared_ext not in allowed_extensions:
        raise UnsupportedFileTypeError(
            f"Tipo de arquivo não suportado: '{declared_ext}'. "
            f"Use: {', '.join(sorted(allowed_extensions))}",
            declared_ext=declared_ext,
        )

    if not content:
        raise UnsupportedFileTypeError(
            "Arquivo vazio.", declared_ext=declared_ext,
        )

    if declared_ext == ".pdf":
        if not _is_pdf(content):
            raise UnsupportedFileTypeError(
                "Conteúdo do arquivo não bate com PDF (assinatura ausente).",
                declared_ext=declared_ext,
            )
        return ValidatedFile(extension=".pdf", mime="application/pdf")

    if declared_ext == ".docx":
        if not _is_docx(content):
            raise UnsupportedFileTypeError(
                "Conteúdo do arquivo não bate com DOCX (ZIP/OOXML inválido).",
                declared_ext=declared_ext,
            )
        return ValidatedFile(
            extension=".docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    # txt / md
    if not _looks_like_text(content):
        raise UnsupportedFileTypeError(
            "Conteúdo binário enviado como texto — arquivo recusado.",
            declared_ext=declared_ext,
        )
    # Cross-check with filetype: a binary like an executable will return
    # an extension different from text/markdown — reject when it does.
    sniff = _filetype_kind(content)
    if sniff and sniff not in {"txt", "md"}:
        # filetype detected a binary signature inside what claims to be text.
        raise UnsupportedFileTypeError(
            f"Conteúdo detectado como '{sniff}', mas declarado como '{declared_ext}'.",
            declared_ext=declared_ext,
        )
    return ValidatedFile(
        extension=declared_ext,
        mime="text/markdown" if declared_ext == ".md" else "text/plain",
    )
