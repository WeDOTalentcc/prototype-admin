#!/usr/bin/env python3
"""
CI Guard: No PII fields in log calls (LGPD Art. 46 compliance).

Usage:
    python3 scripts/check_no_pii_in_logs.py

Exits 1 if real PII (email addresses, names, CPF, phone numbers) are passed
as keyword arguments to logger calls.

Marker support (added 2026-05-10 — P0-1 fix):
    Inline marker on the same line OR comment marker on line immediately above:
        # pii-logs ok: <reason — why this is not real PII per LGPD>

    Use cases for marker:
      - {company.name} — entidade jurídica, NÃO é PII per LGPD Art.5 V (titular = pessoa natural)
      - {department.name}, {automation.name}, {client.name}, {profile.name} — config/metadata
      - {template_name}, {trigger_name} — system identifiers, não-PII

    Mantém runtime defense via PIIMaskingFilter (app/shared/pii_masking.py:66) —
    marker apenas suprime sensor static. Filter continua mascarando email/CPF/phone
    em runtime via regex.
"""
import sys
import re
from pathlib import Path

# Optional: accept a single file argument to scan just that file (used by tests).
# Usage: python3 scripts/check_no_pii_in_logs.py [path/to/single_file.py]
_single_file_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else None

# Fields that are actual PII when used as log kwargs
PII_FIELD_PATTERNS = [
    r"\brecipient_email\s*=",
    r"\bcandidate_email\s*=",
    r"\buser_email\s*=",
    r"\bsender_email\s*=",
    r"\bto_email\s*=",
    r"\bemail\s*=\s*[a-zA-Z_][a-zA-Z_0-9.]*\.email",   # email=obj.email
    r"\bemail\s*=\s*request\.",                            # email=request.email
    r"\bcpf\s*=",
    r"\bcandidate_phone\s*=",
    r"\bphone_number\s*=",
    r"\bfull_name\s*=",
    r"\bcandidate_name\s*=\s*[a-zA-Z_]",   # candidate_name=something (not a bool)
    r"\buser_name\s*=\s*[a-zA-Z_]",
]

# NOT PII — exclude these from matching even if they contain "email" etc.
EXCLUSION_PATTERNS = [
    r"email_sent\s*=",
    r"email_count\s*=",
    r"email_error\s*=",
    r"email_status\s*=",
    r"email_result\s*=",
    r"email_created\s*=",
    r"whatsapp_sent\s*=",
    r"=\s*(True|False|None|\d+)",  # boolean/int value
    r"=\s*[0-9]",                    # numeric value
]

LOG_CALL_PATTERN = re.compile(
    r"(logger|logging|log)\.(info|warning|warn|error|debug|critical|exception)\s*\(",
    re.IGNORECASE,
)
PII_PATTERNS_COMPILED = [re.compile(p, re.IGNORECASE) for p in PII_FIELD_PATTERNS]
EXCLUSION_COMPILED = [re.compile(p, re.IGNORECASE) for p in EXCLUSION_PATTERNS]

# Marker to opt-out a specific log site (P0-1 fix 2026-05-10):
# Use on the same line OR on the comment line immediately above.
PII_LOGS_OK_MARKER = re.compile(r'#\s*pii-logs\s+ok\s*:\s*\S+', re.IGNORECASE)

MAX_LOG_SPAN = 10  # max lines a single logger call can span before we assume false positive


def has_pii_logs_ok_marker(lines: list, line_num: int) -> bool:
    """Check if line at line_num (1-indexed) or previous line has # pii-logs ok: <reason>.

    Returns True if marker is present in:
      - Same line (inline marker after the log call)
      - Line immediately above (block marker preceding the log call)
    """
    idx = line_num - 1  # convert to 0-indexed
    if 0 <= idx < len(lines) and PII_LOGS_OK_MARKER.search(lines[idx]):
        return True
    if idx > 0 and PII_LOGS_OK_MARKER.search(lines[idx - 1]):
        return True
    return False


# ---- F-string PII detection ----
# Variable-name patterns that indicate PII inside an f-string expression
PII_FSTRING_VAR_PATTERNS = [
    re.compile(r'\{[^}]*\bemail\b[^}]*\}', re.IGNORECASE),        # {email}, {manager_email}, etc.
    re.compile(r'\{[^}]*\bphone\b[^}]*\}', re.IGNORECASE),        # {phone}, {phone_number}
    re.compile(r'\{[^}]*\bcpf\b[^}]*\}', re.IGNORECASE),          # {cpf}
    re.compile(r'\{[^}]*\bname\b[^}]*\}', re.IGNORECASE),         # {manager_name}, {recruiter_name}
    re.compile(r'\{[^}]*_name[^}]*\}', re.IGNORECASE),              # {candidate_name}, {user_name}
    re.compile(r'\{[^}]*_email[^}]*\}', re.IGNORECASE),             # {recruiter_email}, {sender_email}
]

# Match any logger call that contains an f-string argument
FSTRING_LOG_PATTERN = re.compile(
    r'(logger|logging|log)\.(info|warning|warn|error|debug|critical|exception)\s*\(\s*f["\']',
    re.IGNORECASE,
)


def check_fstring_pii(filepath: "Path", lines: list) -> list:
    """Return violation strings for logger f-string calls containing PII variable names.

    Honors `# pii-logs ok: <reason>` marker (inline or on line above).
    """
    violations = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if not FSTRING_LOG_PATTERN.search(line):
            continue
        # P0-1 fix: skip if marker present
        if has_pii_logs_ok_marker(lines, i):
            continue
        for pat in PII_FSTRING_VAR_PATTERNS:
            if pat.search(line):
                violations.append(
                    f"{filepath}:{i}: f-string log with PII variable\n"
                    f"  > {stripped[:120]}"
                )
                break  # one violation per line is enough
    return violations


fstring_errors = []
errors = []
checked = 0

_scan_targets = [_single_file_arg] if _single_file_arg else [
    p for p in Path("app").rglob("*.py")
    if "__pycache__" not in str(p)
    and "test" not in str(p).lower()
    and "scripts" not in str(p)
]

for path in _scan_targets:
    checked += 1
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    fstring_errors.extend(check_fstring_pii(path, lines))

    in_log_call = False
    log_start_line = 0
    paren_depth = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        # Safety: if we have been in a log call for too many lines, reset (false positive)
        if in_log_call and (i - log_start_line) > MAX_LOG_SPAN:
            in_log_call = False

        if not in_log_call and LOG_CALL_PATTERN.search(line):
            in_log_call = True
            log_start_line = i
            paren_depth = line.count("(") - line.count(")")
            if paren_depth <= 0:
                in_log_call = False
            continue  # Don't double-count

        if in_log_call:
            # P0-1 fix: skip if marker present on log call start line OR current line
            if has_pii_logs_ok_marker(lines, log_start_line) or has_pii_logs_ok_marker(lines, i):
                paren_depth += line.count("(") - line.count(")")
                if paren_depth <= 0:
                    in_log_call = False
                continue

            # Check for PII patterns
            for pii_pat in PII_PATTERNS_COMPILED:
                if pii_pat.search(line):
                    # Make sure it's not an excluded pattern
                    excluded = any(exc.search(line) for exc in EXCLUSION_COMPILED)
                    if not excluded:
                        errors.append(
                            f"{path}:{i}: PII in log call (started at line {log_start_line})\n"
                            f"  > {stripped[:100]}"
                        )
                    break
            paren_depth += line.count("(") - line.count(")")
            if paren_depth <= 0:
                in_log_call = False

all_errors = errors + fstring_errors
if all_errors:
    print(f"\n[FAIL] PII in log calls: {len(all_errors)} violations ({len(errors)} kwargs, {len(fstring_errors)} f-string)")
    print()
    for e in all_errors[:25]:
        print(f"  {e}")
    if len(all_errors) > 25:
        print(f"  ... and {len(all_errors) - 25} more")
    print()
    print("Fix: Remove PII fields from log calls. Use %s format or structured extra={}.")
    print("If the log site is NOT real PII (e.g. company.name, automation.name — entidade jurídica/config metadata),")
    print("add `# pii-logs ok: <reason>` on the same line or the line above.")
    print("See ARCHITECTURE.md ADR-006.")
    sys.exit(1)

print(f"[PASS] No PII in log calls ({checked} files checked, 0 kwargs violations, 0 f-string violations)")
sys.exit(0)
