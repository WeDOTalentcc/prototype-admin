#!/usr/bin/env python3
"""Fix patch 6: gemini_voice_service.py tenant-aware."""
import os

path = "/home/runner/workspace/lia-agent-system/app/domains/voice/services/gemini_voice_service.py"
with open(path) as f:
    content = f.read()

old = """        # Check tenant config for custom Gemini key
        if company_id:
            try:
                from app.shared.tenant_llm_context import _tenant_configs
                config = _tenant_configs.get(company_id)
                if config and "gemini" in config.get("providers", {}):
                    tenant_key = config["providers"]["gemini"].get("api_key")
                    if tenant_key:
                        api_key = tenant_key
                        base_url = None  # Direct API with tenant key
            except ImportError:
                pass

        if not api_key or not base_url:
            raise ValueError(
                "Gemini AI Integrations not configured. "
                "AI_INTEGRATIONS_GEMINI_API_KEY and AI_INTEGRATIONS_GEMINI_BASE_URL must be set."
            )

        self.client = genai.Client(
            api_key=api_key,
            http_options={
                'api_version': '',
                'base_url': base_url
            }
        )"""

new = """        # === Tenant-aware Gemini client (LGPD compliance) ===
        from app.shared.tenant_llm_context import get_gemini_client_for_tenant
        self.client = get_gemini_client_for_tenant(company_id)"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(content)
    print("OK: gemini_voice_service.py patched")
else:
    print("ERROR: pattern not found")
    # Debug: show lines around the area
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "Check tenant config" in line or "company_id" in line and "tenant" in line:
            for j in range(max(0, i-1), min(len(lines), i+30)):
                print(f"  {j+1}: {repr(lines[j])}")
            break
