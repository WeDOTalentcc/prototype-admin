#!/usr/bin/env python3
"""
D0.7 — Verify Apify coverage: ensure every Apify HTTP call goes through
the gateway (apify_service.run_apify_actor with tracking) or is a test/config file.

Exit 0 = coverage OK. Exit non-zero = bypass detected.
"""
import os
import re
import sys
from pathlib import Path

BASE = Path("/home/runner/workspace/lia-agent-system")
BYPASSES = []

# Patterns that indicate direct Apify call bypassing the gateway
BYPASS_PATTERNS = [
    # direct httpx call to apify.com
    re.compile(r'(httpx|aiohttp|requests)\.(get|post|put|patch)\([^)]*apify\.com'),
    # Direct ApifyClient usage from SDK (not through our gateway)
    re.compile(r'from\s+apify_client\s+import'),
    re.compile(r'ApifyClient\s*\('),
]

# Files allowed to bypass (infrastructure)
ALLOWED_BYPASS_FILES = {
    "app/domains/sourcing/services/apify_service.py",       # THE gateway itself
    "app/domains/sourcing/services/apify_mcp_client.py",    # MCP client (different protocol)
    "app/services/__init__.py",                              # re-exports
    "libs/config/lia_config/config.py",                      # env var declaration
    "app/shared/health/providers_health.py",                 # health check — no actual call
}

for root, _, files in os.walk(BASE):
    if "__pycache__" in root or ".git" in root:
        continue
    # Skip test files
    if "test" in root.lower():
        continue
    for fname in files:
        if not fname.endswith(".py") or fname.startswith("test_"):
            continue
        path = Path(root) / fname
        try:
            content = path.read_text()
        except Exception:
            continue
        rel = str(path.relative_to(BASE))
        if rel in ALLOWED_BYPASS_FILES:
            continue
        for pattern in BYPASS_PATTERNS:
            for m in pattern.finditer(content):
                # Get line number
                line_num = content[:m.start()].count("\n") + 1
                snippet = content.splitlines()[line_num - 1].strip()[:120]
                BYPASSES.append((rel, line_num, snippet))

# Report
if BYPASSES:
    print(f"❌ FOUND {len(BYPASSES)} Apify bypasses (direct calls NOT via gateway):")
    for file, line, snippet in BYPASSES:
        print(f"  {file}:{line}: {snippet}")
    print("\nThese calls skip consumption tracking + budget check.")
    print("Refactor to use `from app.domains.sourcing.services.apify_service import apify_service`")
    print("and call `apify_service.run_apify_actor(actor_id, input_data, company_id=...)`")
    sys.exit(1)
else:
    print("✅ Apify coverage OK — all non-test code uses apify_service gateway")
    print(f"   Scanned {BASE}, allowed bypass files: {len(ALLOWED_BYPASS_FILES)}")
    sys.exit(0)
