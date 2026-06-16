#!/usr/bin/env python3
"""
Bug 5 sensor canonical: valida que cada literal de ChatContextType em
plataforma-lia/src/contexts/lia-float-context.tsx (exceto 'general') tem
entrada em CONTEXT_TYPE_TO_DOMAIN_HINT — OU comentário explícito 
declarando que mantém roteamento default.

Causa raiz Bug 5 (2026-05-24): settings_config era ChatContextType mas
NÃO tinha mapping para Rail A domain_hint → chat em /configuracoes ia
pro recruiter_assistant (sem analyze_company_website).

Run:
    python3 plataforma-lia/scripts/check_chat_context_hint.py
    python3 plataforma-lia/scripts/check_chat_context_hint.py --blocking
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "src" / "contexts" / "lia-float-context.tsx"

CHAT_CONTEXT_TYPE_RE = re.compile(
    r"export\s+type\s+ChatContextType\s*=\s*\|\s*((?:\"[a-z_]+\"\s*(?:\|\s*)?)+);?",
    re.MULTILINE,
)
MAPPING_RE = re.compile(
    r"CONTEXT_TYPE_TO_DOMAIN_HINT[^{]*\{([^}]*)\}",
    re.DOTALL,
)


def extract_literals(src: str) -> set[str]:
    m = CHAT_CONTEXT_TYPE_RE.search(src)
    if not m:
        return set()
    return set(re.findall(r'"([a-z_]+)"', m.group(1)))


def extract_mapped(src: str) -> tuple[set[str], set[str]]:
    """Returns (mapped_with_value, commented_skips)."""
    m = MAPPING_RE.search(src)
    if not m:
        return set(), set()
    body = m.group(1)
    mapped: set[str] = set()
    commented: set[str] = set()
    for line in body.splitlines():
        # active mapping: key: "value"
        match = re.match(r"\s*([a-z_]+):\s*['\"]([^'\"]+)['\"]", line)
        if match:
            mapped.add(match.group(1))
            continue
        # commented skip: // key: undefined  OR // key: "..."
        match_cmt = re.match(r"\s*//\s*([a-z_]+):", line)
        if match_cmt:
            commented.add(match_cmt.group(1))
    return mapped, commented


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocking", action="store_true")
    args = parser.parse_args()

    if not TARGET.exists():
        print(f"⚠️  {TARGET} not found")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    literals = extract_literals(src)
    mapped, commented = extract_mapped(src)

    # 'general' is implicit default routing
    literals.discard("general")

    unmapped = literals - mapped - commented
    if not unmapped:
        print(f"✅ check_chat_context_hint: {len(literals)} types, {len(mapped)} mapped, {len(commented)} skipped (clean)")
        return 0

    print(f"⚠️  check_chat_context_hint: {len(unmapped)} ChatContextType(s) sem mapping nem skip explícito")
    for lit in sorted(unmapped):
        print(f"  - {lit}")
    print(
        "  → Fix: Adicione em CONTEXT_TYPE_TO_DOMAIN_HINT (lia-float-context.tsx) "
        "`<type>: '<backend_domain>'` OU comentário explícito "
        "`// <type>: undefined  // default routing` declarando intenção. "
        "Reference: Bug 5 fix 2026-05-24 (settings_config → company_settings)."
    )
    if args.blocking:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
