#!/usr/bin/env python3
"""
CI Guard: All @router endpoints must declare response_model.

Usage:
    python3 scripts/check_response_models.py

Exits 1 if any route decorators lack response_model.
This enforces Golden Rule G2.
"""
import sys
import re
from pathlib import Path

# Match @router.get/post/put/patch/delete/head/options without response_model
# Allow: websocket routes (no response_model needed)
# Allow: routes returning Response/StreamingResponse directly
ROUTER_PATTERN = re.compile(
    r"@router\.(get|post|put|patch|delete|head|options)\s*\(",
    re.IGNORECASE,
)
HAS_RESPONSE_MODEL = re.compile(r"response_model\s*=")
WEBSOCKET_PATTERN = re.compile(r"@router\.(websocket|on_event)")

SKIP_PATTERNS = [
    "response_model=None",  # explicitly opting out
    "# noqa: response_model",
]

errors = []
checked = 0
total_routes = 0

for path in Path("app/api").rglob("*.py"):
    if "__pycache__" in str(path):
        continue
    checked += 1
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]

        if ROUTER_PATTERN.search(line):
            total_routes += 1
            # Collect the full decorator (may span multiple lines)
            decorator_lines = [line]
            depth = line.count("(") - line.count(")")
            j = i + 1
            while depth > 0 and j < len(lines):
                decorator_lines.append(lines[j])
                depth += lines[j].count("(") - lines[j].count(")")
                j += 1

            decorator = "\n".join(decorator_lines)
            skip = any(p in decorator for p in SKIP_PATTERNS)

            if not skip and not HAS_RESPONSE_MODEL.search(decorator):
                errors.append(f"{path}:{i+1}: Missing response_model\n  > {line.strip()[:100]}")

        i += 1

if errors:
    print(f"\n[FAIL] {len(errors)}/{total_routes} routes missing response_model:")
    print()
    for e in errors[:30]:
        print(f"  {e}")
    if len(errors) > 30:
        print(f"  ... and {len(errors) - 30} more")
    print()
    print("Fix: Add response_model=YourSchema to each @router decorator.")
    print("See ARCHITECTURE.md ADR-005.")
    sys.exit(1)

print(f"[PASS] All {total_routes} routes have response_model ({checked} files checked)")
sys.exit(0)
