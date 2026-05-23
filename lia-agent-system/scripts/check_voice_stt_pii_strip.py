#!/usr/bin/env python3
"""
Sensor anti-regressão · W3-018 (2026-05-23)

Verifica que `transcript_segments.append({"text": <raw_text>, ...})` em
voice STT services SEMPRE usa `strip_pii_for_llm_prompt(<text>)`, nunca
o text raw.

Risco: transcript_segments é lido em conversation_history sent to LLM →
text raw vaza PII direto pro Gemini LLM (LGPD breach ATIVO).

Pattern violação:
- `"text": text,` em transcript_segments.append (raw)
- `"text": text` sem strip_pii (raw)

Pattern canonical:
- `"text": strip_pii_for_llm_prompt(text)` ✅

Modo: BLOCKING por default · --warn-only opt-out.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VOICE_FILES = [
    REPO_ROOT / "app/domains/voice/services/voice_screening_orchestrator.py",
    REPO_ROOT / "app/domains/voice/services/gemini_live_audio_service.py",
]

# Detecta `"text": <bare_variable>,` em transcript_segments.append() context
# Bare variable = sem strip_pii_for_llm_prompt() ou mask_pii() wrapper
TRANSCRIPT_RAW_RE = re.compile(
    r'transcript_segments\.append\(\{\s*[^}]*?'  # within append({...})
    r'"text":\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*,',  # "text": <bare>
    re.DOTALL,
)


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return errors

    src = path.read_text()
    if "strip_pii_for_llm_prompt" not in src and "transcript_segments.append" in src:
        errors.append(
            f"❌ {path.relative_to(REPO_ROOT)} usa transcript_segments mas\n"
            f"   NÃO importa strip_pii_for_llm_prompt\n"
            "   FIX: from app.shared.pii_masking import strip_pii_for_llm_prompt"
        )
        return errors

    # Find sites onde "text": <bare> aparece em transcript_segments context
    for match in TRANSCRIPT_RAW_RE.finditer(src):
        var_name = match.group(1)
        # Compute line number
        line_num = src[: match.start()].count("\n") + 1
        # Check se a linha CONTÉM strip_pii_for_llm_prompt (false positive guard)
        line_start = src.rfind("\n", 0, match.start()) + 1
        line_end = src.find("\n", match.end())
        line_content = src[line_start:line_end]
        if "strip_pii_for_llm_prompt" not in line_content:
            errors.append(
                f"❌ {path.relative_to(REPO_ROOT)}:{line_num} · transcript_segments\n"
                f"   armazena `\"text\": {var_name},` (raw, sem PII strip)\n"
                "   Risco: PII vaza para LLM via conversation_history\n"
                f"   FIX: trocar por `\"text\": strip_pii_for_llm_prompt({var_name}),`"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    for f in VOICE_FILES:
        errors.extend(check_file(f))

    if errors:
        print(
            f"W3-018 voice PII leak · {len(errors)} site(s) com raw text em "
            f"transcript_segments:",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print(file=sys.stderr)
        if args.warn_only:
            return 0
        return 1

    print(
        "✅ Voice STT PII strip wired (W3-018) · todos os transcript_segments "
        "usam strip_pii_for_llm_prompt antes de armazenar"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
