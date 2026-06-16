"""
Document Scanner — Detect and sanitize injection payloads in uploaded CV/PDF text.

Scans for invisible Unicode characters, base64-encoded instruction blocks,
oversized text sections, and prompt injection patterns embedded in document text.

Usage:
    from app.shared.robustness.document_scanner import scan_document
    result = scan_document(raw_cv_text)
    if not result.is_clean:
        logger.warning("Threats found: %s", result.threats)
    safe_text = result.sanitized_text
"""
import base64
import logging
import re
from dataclasses import dataclass, field

from app.shared.robustness.security_patterns import check_input_security

logger = logging.getLogger(__name__)

MAX_FIELD_LENGTH = 10_000

# Invisible / control Unicode characters that have no place in CV text
_INVISIBLE_CHARS = re.compile(
    "["
    "\u200b"     # zero-width space
    "\u200c"     # zero-width non-joiner
    "\u200d"     # zero-width joiner
    "\u200e"     # left-to-right mark
    "\u200f"     # right-to-left mark
    "\u2060"     # word joiner
    "\u2061"     # function application
    "\u2062"     # invisible times
    "\u2063"     # invisible separator
    "\u2064"     # invisible plus
    "\ufeff"     # BOM / zero-width no-break space
    "\u00ad"     # soft hyphen
    "\u034f"     # combining grapheme joiner
    "\u061c"     # Arabic letter mark
    "\u180e"     # Mongolian vowel separator
    "]+"
)

# Base64 blocks that look like encoded instructions (>=40 chars of base64)
_BASE64_BLOCK = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")

# Common instruction prefixes that might appear after decoding
_INSTRUCTION_KEYWORDS = [
    "ignore previous",
    "ignore all",
    "system prompt",
    "you are now",
    "new instructions",
    "override",
    "disregard",
]


@dataclass
class DocumentScanResult:
    """Result of a document injection scan."""
    is_clean: bool
    threats: list[str] = field(default_factory=list)
    sanitized_text: str = ""


def scan_document(text: str) -> DocumentScanResult:
    """Scan document text for injection payloads and return sanitized output.

    Checks performed:
      1. Invisible Unicode characters (zero-width spaces, RTL marks, etc.)
      2. Base64-encoded instruction blocks
      3. Oversized text sections (>10K chars)
      4. Prompt injection patterns via security_patterns.py

    Args:
        text: Raw extracted text from a CV or PDF.

    Returns:
        DocumentScanResult with is_clean flag, threat descriptions, and sanitized text.
    """
    if not text:
        return DocumentScanResult(is_clean=True, sanitized_text="")

    threats: list[str] = []
    sanitized = text

    # 1. Invisible Unicode characters
    invisible_matches = _INVISIBLE_CHARS.findall(sanitized)
    if invisible_matches:
        total_hidden = sum(len(m) for m in invisible_matches)
        threats.append(f"invisible_unicode: {total_hidden} hidden characters stripped")
        sanitized = _INVISIBLE_CHARS.sub("", sanitized)

    # 2. Base64-encoded instruction blocks
    for match in _BASE64_BLOCK.finditer(sanitized):
        raw_b64 = match.group()
        try:
            decoded = base64.b64decode(raw_b64, validate=True).decode("utf-8", errors="ignore").lower()
            if any(kw in decoded for kw in _INSTRUCTION_KEYWORDS):
                threats.append(f"base64_injection: encoded instruction block at pos {match.start()}")
                sanitized = sanitized.replace(raw_b64, "[REMOVED_ENCODED_BLOCK]")
        except Exception:
            pass  # Not valid base64 — benign (e.g. long skill description)

    # 3. Oversized text (single contiguous block without line breaks)
    lines = sanitized.split("\n")
    rebuilt_lines: list[str] = []
    for line in lines:
        if len(line) > MAX_FIELD_LENGTH:
            threats.append(f"oversized_section: line truncated from {len(line)} to {MAX_FIELD_LENGTH} chars")
            rebuilt_lines.append(line[:MAX_FIELD_LENGTH] + " [TRUNCATED]")
        else:
            rebuilt_lines.append(line)
    sanitized = "\n".join(rebuilt_lines)

    # 4. Prompt injection patterns (reuse existing security_patterns)
    security_result = check_input_security(sanitized)
    if security_result.is_blocked:
        sep = ", "
        pattern_names = sep.join(security_result.matched_pattern_names)
        threats.append(
            f"injection_pattern: {pattern_names} (risk={security_result.risk_level})"
        )
        # We do NOT strip the whole text — just flag it. The caller decides.

    is_clean = len(threats) == 0
    if not is_clean:
        logger.warning(
            "[DocumentScanner] %d threat(s) in document: %s",
            len(threats),
            "; ".join(threats),
        )

    return DocumentScanResult(
        is_clean=is_clean,
        threats=threats,
        sanitized_text=sanitized,
    )
