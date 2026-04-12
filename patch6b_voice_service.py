#!/usr/bin/env python3
"""Fix patch 6: gemini_voice_service.py — line-based replacement."""
path = "/home/runner/workspace/lia-agent-system/app/domains/voice/services/gemini_voice_service.py"

with open(path) as f:
    lines = f.readlines()

# Find the start line "# Check tenant config for custom Gemini key"
start = None
end = None
for i, line in enumerate(lines):
    if "# Check tenant config for custom Gemini key" in line:
        start = i
    if start is not None and "logger.info" in line and "Gemini Voice Service initialized" in line:
        end = i + 1
        break

if start is None or end is None:
    print(f"ERROR: could not find block (start={start}, end={end})")
    raise SystemExit(1)

print(f"Replacing lines {start+1}-{end} ({end-start} lines)")

new_lines = [
    "        # === Tenant-aware Gemini client (LGPD compliance) ===\n",
    "        from app.shared.tenant_llm_context import get_gemini_client_for_tenant\n",
    "        self.client = get_gemini_client_for_tenant(company_id)\n",
    "\n",
    '        logger.info("[GeminiVoiceService] Initialized (tenant-aware)")\n',
]

lines[start:end] = new_lines

with open(path, "w") as f:
    f.writelines(lines)

print("OK: gemini_voice_service.py patched")
