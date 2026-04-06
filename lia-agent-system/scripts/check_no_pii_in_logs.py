#!/usr/bin/env python3
"""
CI Guard: No PII fields in log calls (LGPD Art. 46 compliance).

Usage:
    python3 scripts/check_no_pii_in_logs.py

Exits 1 if any PII fields are found in logger calls.
"""
import sys
import re
from pathlib import Path

PII_FIELDS = [
    "email", "recipient_email", "candidate_email", "user_email", "sender_email",
    "cpf", "rg", "phone", "celular", "telefone", "mobile",
    "full_name", "nome", "nome_completo", "candidate_name", "user_name",
    "password", "senha", "token", "secret",
    "birth_date", "data_nascimento", "address", "endereco",
]

LOG_CALL_PATTERN = re.compile(
    r"(logger|logging|log)\.(info|warning|warn|error|debug|critical|exception)\s*\(",
    re.IGNORECASE,
)
PII_ARG_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(f) for f in PII_FIELDS) + r")\s*=",
    re.IGNORECASE,
)

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

        if not in_log_call and LOG_CALL_PATTERN.search(line):
            in_log_call = True
            log_start_line = i
            paren_depth = line.count("(") - line.count(")")

        if in_log_call:
            if PII_ARG_PATTERN.search(line):
                errors.append(
                    f"{path}:{i}: PII in log call (started at line {log_start_line})\n"
                    f"  > {stripped[:100]}"
                )
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
