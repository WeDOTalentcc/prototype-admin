#!/usr/bin/env python3
"""
Lint check: ensure no direct LLM SDK imports outside allowed files.

Allowed locations:
  - app/shared/providers/   (provider implementations)
  - app/shared/llm_bootstrap.py  (SDK monkey-patching)
  - app/api/v1/llm_config.py     (admin test endpoint — tests user-supplied keys)
  - app/api/v1/chat.py           (SSE streaming — uses credentials from factory)

Run:  python scripts/check_llm_imports.py
Exit: 0 = clean, 1 = violations found
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

FORBIDDEN_PATTERNS = [
    r"from anthropic import",
    r"import anthropic\b",
    r"from google\.generativeai",
    r"import google\.generativeai",
    r"from openai import",
    r"import openai\b",
]

ALLOWED_PATHS = {
    "app/shared/providers",
    "app/shared/llm_bootstrap.py",
    "app/api/v1/llm_config.py",
    "app/api/v1/chat.py",
    # DEBT-014: tenant_llm_context IS the factory infrastructure — it creates
    # AsyncAnthropic clients with tenant BYOK keys. Legitimate infrastructure layer.
    "app/shared/tenant_llm_context.py",
}


def is_allowed(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    for allowed in ALLOWED_PATHS:
        if rel == allowed or rel.startswith(allowed + "/"):
            return True
    return False


def main() -> int:
    violations: list[str] = []
    combined = re.compile("|".join(FORBIDDEN_PATTERNS))

    for py_file in (ROOT / "app").rglob("*.py"):
        if is_allowed(py_file):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for lineno, line in enumerate(source.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if combined.search(line):
                rel = py_file.relative_to(ROOT)
                violations.append(f"  {rel}:{lineno}: {line.rstrip()}")

    if violations:
        print("FAIL — direct LLM SDK imports found outside allowed paths:")
        print("\n".join(violations))
        print(
            "\nMove these calls to providers/ or route through LLMProviderFactory."
        )
        return 1

    print("OK — no direct LLM SDK imports outside allowed paths.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
