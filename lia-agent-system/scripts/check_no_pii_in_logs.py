#!/usr/bin/env python3
"""
CI Guard: No PII fields in log calls (LGPD Art. 46 compliance).

Usage:
    python3 scripts/check_no_pii_in_logs.py

Exits 1 if real PII (email addresses, names, CPF, phone numbers) are passed
as keyword arguments to logger calls.
"""
import sys
import re
from pathlib import Path

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

MAX_LOG_SPAN = 10  # max lines a single logger call can span before we assume false positive

errors = []
checked = 0

for path in Path("app").rglob("*.py"):
    if "__pycache__" in str(path) or "test" in str(path).lower():
        continue
    if "scripts" in str(path):
        continue
    checked += 1
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

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

if errors:
    print(f"\n[FAIL] PII in log calls: {len(errors)} violations")
    print()
    for e in errors[:20]:
        print(f"  {e}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more")
    print()
    print("Fix: Remove PII fields from log calls. See ARCHITECTURE.md ADR-006.")
    sys.exit(1)

print(f"[PASS] No PII in log calls ({checked} files checked)")
sys.exit(0)
