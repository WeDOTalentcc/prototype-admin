#!/usr/bin/env python3
"""
Bug 6 sensor canonical: detecta hooks/components em src/components/settings/
ou src/hooks/settings/ que fazem mutations (POST/PUT/PATCH/DELETE) via fetch/apiFetch
sem subsequente window.dispatchEvent(new CustomEvent('lia:settings-updated', ...)).

Causa raiz Bug 6: chat lateral em /configuracoes só reage quando recebe
o evento lia:settings-updated. Save sem dispatch = LIA chat fica mudo.

Run:
    python3 plataforma-lia/scripts/check_settings_dispatch.py
    python3 plataforma-lia/scripts/check_settings_dispatch.py --blocking

Skill canonical: harness-engineering [sensor computacional].
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [
    ROOT / "src" / "components" / "settings",
    ROOT / "src" / "hooks" / "settings",
]

# Detect mutation: apiFetch/fetch/axios with method !== 'GET'
# Refined 2026-05-24: original regex had false negatives when body spans
# multiple lines (LogoUploadField, DSRInboxPanel, AITransparencyPanel,
# AIPerformancePanel escaped). New regex looks for the method literal
# directly, AND ensures the file uses apiFetch/fetch/axios at least once.
_HAS_FETCH_RE = re.compile(r"\b(apiFetch|fetch|axios)\b")
_METHOD_MUTATION_RE = re.compile(
    r"\bmethod\s*:\s*['\"](POST|PUT|PATCH|DELETE)['\"]"
)
_AXIOS_DIRECT_RE = re.compile(
    r"\baxios\.(post|put|patch|delete)\s*\("
)


def _find_mutations(src: str):
    """Return list of (lineno, method_literal) for each mutation site."""
    sites = []
    if _HAS_FETCH_RE.search(src):
        for m in _METHOD_MUTATION_RE.finditer(src):
            lineno = src.count("\n", 0, m.start()) + 1
            sites.append((lineno, m.group(1)))
    for m in _AXIOS_DIRECT_RE.finditer(src):
        lineno = src.count("\n", 0, m.start()) + 1
        sites.append((lineno, m.group(1).upper()))
    return sites


# Kept for backward compat in test imports — now wraps the new logic.
class _CompatRe:
    @staticmethod
    def finditer(text):
        for lineno, method in _find_mutations(text):
            # Yield a dummy match-like object via re module (we use a regex hit on file)
            yield from _METHOD_MUTATION_RE.finditer(text)
            break

MUTATION_RE = _CompatRe()
# Detect dispatch in the same file
# Accept either inline dispatch OR canonical helper notifyChatOfSettingsUpdate
DISPATCH_RE = re.compile(
    r"dispatchEvent\s*\(\s*new\s+CustomEvent\s*\(\s*['\"]lia:settings-updated['\"]"
    r"|notifyChatOfSettingsUpdate\s*\("
)
# Skip files that are pure types/constants
SKIP_SUFFIXES = ("-types.ts", "Constants.ts", "constants.ts", ".test.ts", ".test.tsx")


def scan() -> list[tuple[Path, int, str, str]]:
    violations: list[tuple[Path, int, str, str]] = []
    for target in TARGETS:
        if not target.exists():
            continue
        for ts in list(target.rglob("*.ts")) + list(target.rglob("*.tsx")):
            if any(ts.name.endswith(suf) for suf in SKIP_SUFFIXES):
                continue
            if "__tests__" in ts.parts:
                continue
            try:
                src = ts.read_text(encoding="utf-8")
            except Exception:
                continue
            mutations = _find_mutations(src)
            if not mutations:
                continue
            has_dispatch = bool(DISPATCH_RE.search(src))
            if has_dispatch:
                continue
            # Report each mutation site
            for lineno, method in mutations:
                violations.append((
                    ts, lineno,
                    f"Mutation {method} sem dispatch lia:settings-updated subsequente",
                    "Adicione após save bem-sucedido: "
                    "`window.dispatchEvent(new CustomEvent('lia:settings-updated', "
                    "{ detail: { actionId, section, field?, value?, source: 'ui', ts: Date.now() } }))`. "
                    "Pattern matches BenefitsListSection.tsx:93 / saveWorkforceData (Bug 6 fix 2026-05-24).",
                ))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocking", action="store_true")
    parser.add_argument("--max-violations", type=int, default=0)
    args = parser.parse_args()

    violations = scan()
    if not violations:
        print("✅ check_settings_dispatch: 0 violations")
        return 0

    print(f"⚠️  check_settings_dispatch: {len(violations)} violation(s)")
    for path, lineno, desc, fix in violations:
        rel = path.relative_to(ROOT)
        print(f"  [{rel}:{lineno}] {desc}")
        print(f"  → Fix: {fix}\n")

    if args.blocking and len(violations) > args.max_violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
