#!/usr/bin/env python3
"""
Wave 3 sensor (2026-05-22): detect domain code that bypasses the universal
ai_credit_gate by calling the LLM SDK directly without ensuring a tenant
ContextVar is set.

This is the FEEDBACK sensor that complements the FEEDFORWARD guide
(`app/shared/llm_bootstrap.py` monkey-patches). The bootstrap is universal:
any call to `anthropic.Anthropic().messages.create`, `openai.OpenAI().chat.
completions.create`, or `genai.Client().models.generate_content` goes through
the gate. The sensor's job is to catch direct HTTP usage (raw httpx /
requests POSTing to api.anthropic.com / api.openai.com / generativelanguage.
googleapis.com) — those bypass the SDK and therefore bypass the bootstrap.

## Pattern detected

    httpx.AsyncClient().post("https://api.anthropic.com/v1/messages", ...)
    requests.post("https://api.openai.com/v1/chat/completions", ...)
    aiohttp.ClientSession.post("https://generativelanguage.googleapis.com/...", ...)

When this pattern is present, the file SHOULD also import either
`check_credit_budget` directly OR `with_runtime_context`/`_current_company_id`
so it's at least going through tenant gating.

## Allowlist

Files that legitimately do raw HTTP for non-LLM endpoints (e.g.
multimodal_service for audio uploads to Whisper transcription) live in
ALLOWLIST. Add entries with a citation.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = REPO_ROOT / "app"

# Domains+hostnames that indicate raw LLM call
LLM_HOSTS = (
    "api.anthropic.com",
    "api.openai.com",
    "generativelanguage.googleapis.com",
    "generativelanguage.google.com",
)

ALLOWLIST: set[str] = {
    # anthropic_client.py — canonical SDK seam wrapper. The string match is
    # inside the docstring ("https://api.anthropic.com"). The actual call
    # goes through anthropic.Anthropic which the llm_bootstrap monkey-patch
    # gates. False positive — reviewed 2026-05-22.
    "app/shared/providers/anthropic_client.py",
    # voice_openai_realtime.py — WebSocket connection to OpenAI Realtime API
    # (audio streaming). Not chat completions, token model is different.
    # TODO Wave 5: separate ai_credits_balance line for realtime audio.
    # Reviewed 2026-05-22.
    "app/shared/providers/voice_openai_realtime.py",
    # ---------------------------------------------------------------------
    # P1.AIC2 closure (2026-05-22): voice_service.py and multimodal_service.py
    # were removed from this allowlist. Both files now route through the
    # SDK (openai.AsyncOpenAI, anthropic.AsyncAnthropic, google.genai.Client)
    # so the llm_bootstrap monkey-patch fires transitively. Audio APIs are
    # additionally gated by _patch_openai_audio with per-minute (Whisper)
    # and per-char (TTS) token-equivalent estimators.
    # ---------------------------------------------------------------------
}


def _has_llm_host_string(tree: ast.AST) -> tuple[bool, str | None]:
    """Walk AST, return (found, sample_url)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for host in LLM_HOSTS:
                if host in node.value:
                    return True, node.value
    return False, None


def _imports_credit_gate(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", "") or ""
            if "ai_credit_gate" in mod:
                return True
            for n in getattr(node, "names", []):
                if "ai_credit_gate" in (n.name or ""):
                    return True
    return False


def _imports_runtime_context(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", "") or ""
            if "runtime_context" in mod or "auth_enforcement" in mod:
                return True
    return False


def main() -> int:
    offenders: list[tuple[str, str]] = []

    for py_file in APP_ROOT.rglob("*.py"):
        rel = py_file.relative_to(REPO_ROOT).as_posix()
        if rel in ALLOWLIST:
            continue
        try:
            src = py_file.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=rel)
        except (SyntaxError, UnicodeDecodeError):
            continue
        has_host, sample = _has_llm_host_string(tree)
        if not has_host:
            continue
        # If the file already gates via ai_credit_gate import OR uses
        # runtime context, treat it as wired (defense-in-depth).
        if _imports_credit_gate(tree) or _imports_runtime_context(tree):
            continue
        offenders.append((rel, sample or ""))

    if not offenders:
        print("OK — no raw-HTTP LLM callers bypassing ai_credit_gate")
        return 0

    print("FAIL — raw HTTP calls to LLM endpoints WITHOUT ai_credit_gate import:")
    for path, url in offenders:
        print(f"  {path}  → {url}")
        print(
            f"    Fix: import `check_credit_budget` from app.shared.services.ai_credit_gate\n"
            f"    OR switch to SDK client (anthropic.Anthropic / openai.OpenAI / genai.Client)\n"
            f"    so the llm_bootstrap monkey-patch enforces the gate automatically.\n"
            f"    OR add the file to ALLOWLIST with a citation if it's non-chat (e.g. TTS, Whisper)."
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
