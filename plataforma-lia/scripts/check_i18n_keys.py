#!/usr/bin/env python3
"""
Sensor harness: valida que toda chamada `t('key')` ou `t(`key.${var}`)` em
componentes que usam `useTranslations('namespace')` resolve em
`messages/pt-BR.json` E `messages/en.json`.

REGRA canonical (CLAUDE.md i18n contract, registrada 2026-05-23):
  > Toda chave referenciada via useTranslations + t() DEVE existir em ambos
  > os messages files com tipo str. Defeito recorrente — commits 6eab583be
  > (Sprint D AlertPreferencesPanel) e ebcd18c38 (bulk-fix 81 keys) provam
  > que sem sensor automatizado MISSING_MESSAGE atravessa code review.

Uso:
  python3 scripts/check_i18n_keys.py                # warn-only (exit 0)
  python3 scripts/check_i18n_keys.py --blocking     # exit 1 se houver violation
  python3 scripts/check_i18n_keys.py --json         # output JSON pra CI

Heurística:
  - Por arquivo .tsx/.ts em src/ (excl __tests__/, node_modules)
  - Captura o PRIMEIRO useTranslations('ns') como namespace
  - Captura todas chamadas t('lit') e t(`prefix.${var}`)
  - Para template literal, valida que o PREFIXO ESTÁTICO existe como objeto
    (e.g., t(`alertPreferences.${unit}`) exige settings.communication.alertPreferences
    ser objeto não-vazio)
  - Resolve namespace.key contra os 2 messages files
  - Output otimizado pra consumo de LLM:
      [REL_PATH:LINE] namespace.key.path [absent | not string]
      → Fix: adicionar em messages/pt-BR.json e messages/en.json no caminho ...

Limitations conhecidas (v1):
  - Suporta apenas 1 useTranslations por arquivo (primeiro encontrado).
    Caso real raro; componentes com múltiplos namespaces precisam ser
    revisados manualmente. Futuro: AST parser real.
  - Template literal com prefix dinâmico (`${x}.title`) não é validável.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent  # plataforma-lia/
SRC = ROOT / "src"
MESSAGES = {
    "pt-BR": ROOT / "messages" / "pt-BR.json",
    "en": ROOT / "messages" / "en.json",
}

EXCLUDE_DIRS = {"node_modules", "__tests__", ".next", "dist", "build", ".turbo"}
EXCLUDE_FILE_PATTERNS = (".test.tsx", ".test.ts", ".spec.tsx", ".spec.ts", ".d.ts")

# Regex canonical SCOPE-AWARE (v2 — 2026-05-23).
#
# v1 capturava apenas o PRIMEIRO useTranslations por arquivo e atribuía
# todas as chamadas t() a ele. Falso-positivo massivo em arquivos com 2+
# namespaces (e.g. DigitalTwinComponents.tsx tem 5 useTranslations →
# 110 false positives quando o real é 0).
#
# v2 pareia `const VAR = useTranslations("NS")` → `VAR("key")` por nome
# da variável. Cobre o padrão canonical:
#   const t = useTranslations("agents.studio")
#   const tOnboarding = useTranslations("agents.studio.onboarding")
#   ...
#   t("title")              // → agents.studio.title
#   tOnboarding("step1")    // → agents.studio.onboarding.step1
#
# Limitations conhecidas v2:
#   - Single-file scope; variável shadowing em closure não detectada (raro
#     em React components, que tendem a flat-scope).
#   - useTranslations sem const binding (e.g. `useTranslations("ns")("key")`)
#     não suportado — rare pattern, ignorado.

# Captura: `const VAR = useTranslations("NS")` (também aceita let/var, sem const).
RE_USE_T_BINDING = re.compile(
    r"(?:const|let|var)?\s*(\w+)\s*=\s*useTranslations\(\s*['\"]([^'\"]+)['\"]\s*\)"
)

# Per-variable call detection. Built dynamically once we know the bindings.
def make_call_static_re(var: str) -> re.Pattern:
    return re.compile(rf"\b{re.escape(var)}\(\s*['\"]([^'\"]+)['\"]")

def make_call_template_re(var: str) -> re.Pattern:
    return re.compile(rf"\b{re.escape(var)}\(\s*`([^`${{]+?)(?:\.\$\{{|`)")


def load_messages() -> dict[str, dict[str, Any]]:
    out = {}
    for locale, path in MESSAGES.items():
        with path.open() as f:
            out[locale] = json.load(f)
    return out


def resolve(root: dict, dotted: str) -> tuple[Any, str | None]:
    """Returns (value, error). error is None on success."""
    node: Any = root
    parts = dotted.split(".")
    for i, part in enumerate(parts):
        if not isinstance(node, dict):
            return None, f"parent '{'.'.join(parts[:i])}' is {type(node).__name__}, expected dict"
        if part not in node:
            return None, f"key '{part}' not in '{'.'.join(parts[:i]) or '<root>'}'"
        node = node[part]
    return node, None


def line_of(content: str, match_start: int) -> int:
    return content.count("\n", 0, match_start) + 1


def collect_files() -> list[Path]:
    out = []
    for path in SRC.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in (".ts", ".tsx"):
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.name.endswith(EXCLUDE_FILE_PATTERNS):
            continue
        out.append(path)
    return out


def analyze_file(path: Path, messages: dict[str, dict]) -> list[dict]:
    """Returns list of violation dicts. Scope-aware v2.1 (function-block).

    v2 (2026-05-23 manhã): `dict[var, ns] = latest_wins` collapsed re-bindings
    of same variable across functions. Example bug:
        export function A() { const t = useTranslations("ns.A"); t("foo") }
        export function B() { const t = useTranslations("ns.B"); t("bar") }
    v2 mapped t→"ns.B" (latest) and checked A's t("foo") against ns.B.foo.

    v2.1 (this version): partition source by `export function X(){...}` blocks.
    Per-block bindings + per-block call scanning. Bindings outside any block
    (module-level) inherit to all blocks below.
    """
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return []

    if not RE_USE_T_BINDING.search(src):
        return []

    rel_path = str(path.relative_to(ROOT))
    violations: list[dict] = []

    def check_static(var: str, ns: str, m: re.Match) -> None:
        key = m.group(1)
        # Detecta concatenação dinâmica: `t('foo.' + variable)` captura `'foo.'`
        # com trailing dot. Trata como prefix-de-dict (igual template literal),
        # não como leaf string. Pattern canonical em React: t('categories.' + cat).
        if key.endswith("."):
            prefix = key.rstrip(".")
            if not prefix:
                return
            full = f"{ns}.{prefix}"
            for locale, root in messages.items():
                value, err = resolve(root, full)
                if err is not None:
                    violations.append({
                        "file": rel_path,
                        "line": line_of(src, m.start()),
                        "key": f"{full}.<dynamic>",
                        "var": var,
                        "locale": locale,
                        "kind": "concat",
                        "reason": err,
                    })
                elif not isinstance(value, dict):
                    violations.append({
                        "file": rel_path,
                        "line": line_of(src, m.start()),
                        "key": f"{full}.<dynamic>",
                        "var": var,
                        "locale": locale,
                        "kind": "concat",
                        "reason": f"parent is {type(value).__name__}, expected dict for concatenated key",
                    })
            return

        full = f"{ns}.{key}"
        for locale, root in messages.items():
            value, err = resolve(root, full)
            if err is not None:
                violations.append({
                    "file": rel_path,
                    "line": line_of(src, m.start()),
                    "key": full,
                    "var": var,
                    "locale": locale,
                    "kind": "static",
                    "reason": err,
                })
            elif isinstance(value, dict):
                violations.append({
                    "file": rel_path,
                    "line": line_of(src, m.start()),
                    "key": full,
                    "var": var,
                    "locale": locale,
                    "kind": "static",
                    "reason": f"resolves to object ({len(value)} children), expected leaf string",
                })
            elif not isinstance(value, str):
                violations.append({
                    "file": rel_path,
                    "line": line_of(src, m.start()),
                    "key": full,
                    "var": var,
                    "locale": locale,
                    "kind": "static",
                    "reason": f"value is {type(value).__name__}, expected str",
                })

    def check_template(var: str, ns: str, m: re.Match) -> None:
        prefix = m.group(1).rstrip(".")
        if not prefix:
            return
        full = f"{ns}.{prefix}"
        for locale, root in messages.items():
            value, err = resolve(root, full)
            if err is not None:
                violations.append({
                    "file": rel_path,
                    "line": line_of(src, m.start()),
                    "key": f"{full}.<dynamic>",
                    "var": var,
                    "locale": locale,
                    "kind": "template",
                    "reason": err,
                })
            elif not isinstance(value, dict):
                violations.append({
                    "file": rel_path,
                    "line": line_of(src, m.start()),
                    "key": f"{full}.<dynamic>",
                    "var": var,
                    "locale": locale,
                    "kind": "template",
                    "reason": f"parent is {type(value).__name__}, expected dict for dynamic interpolation",
                })

    # v2.1: partition source by `export function X(){...}` or
    # `function X(){...}` blocks. Track module-level bindings separately.
    # Block boundaries are start positions; the block ends at the start of
    # the next function or EOF.
    function_re = re.compile(
        r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(", re.MULTILINE
    )
    boundaries = [(m.group(1), m.start()) for m in function_re.finditer(src)]

    # Module-level region = src[0:first_function_start] (or whole file if no functions)
    module_end = boundaries[0][1] if boundaries else len(src)
    module_block = src[0:module_end]

    def extract_bindings(text: str) -> dict[str, str]:
        return {m.group(1): m.group(2) for m in RE_USE_T_BINDING.finditer(text)}

    def scan_block(block: str, block_offset: int, bindings: dict[str, str]) -> None:
        for var, ns in bindings.items():
            if var in {"e", "i", "x", "y", "k", "v", "fn"}:
                continue
            for m in make_call_static_re(var).finditer(block):
                # Need absolute position for line numbering
                abs_m = _FakeMatch(m, block_offset)
                check_static(var, ns, abs_m)
            for m in make_call_template_re(var).finditer(block):
                abs_m = _FakeMatch(m, block_offset)
                check_template(var, ns, abs_m)

    module_bindings = extract_bindings(module_block)

    # Module-level region scan (uses module bindings only)
    scan_block(module_block, 0, module_bindings)

    # Per-function block scan
    for i, (_name, start) in enumerate(boundaries):
        end = boundaries[i + 1][1] if i + 1 < len(boundaries) else len(src)
        block = src[start:end]
        local_bindings = extract_bindings(block)
        # Function inherits module bindings, but local rebinding wins (shadowing).
        effective = {**module_bindings, **local_bindings}
        scan_block(block, start, effective)

    return violations


class _FakeMatch:
    """Wraps a regex Match into something check_static/check_template can use,
    with an offset applied to .start() for absolute line numbers."""
    __slots__ = ("_m", "_offset")

    def __init__(self, m: re.Match, offset: int):
        self._m = m
        self._offset = offset

    def start(self) -> int:
        return self._m.start() + self._offset

    def group(self, n=0):
        return self._m.group(n)


def format_violation(v: dict) -> str:
    """Output otimizado pra LLM: file:line + key + reason + fix sugerido."""
    fix_hint = (
        f"\n    → Fix: adicionar '{v['key']}' em messages/{v['locale']}.json "
        f"(motivo: {v['reason']})"
    )
    return f"  [{v['file']}:{v['line']}] {v['key']} [missing in {v['locale']}]{fix_hint}"


def main():
    parser = argparse.ArgumentParser(
        description="Valida t('key') vs messages/*.json. Sensor harness canonical.",
    )
    parser.add_argument("--blocking", action="store_true",
                        help="Exit 1 se houver violation (default: warn-only, exit 0)")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON em vez de texto humano")
    parser.add_argument("--max-violations", type=int, default=0,
                        help="Ratchet: exit 1 se total > N (default: 0 = qualquer violation falha em modo blocking)")
    args = parser.parse_args()

    messages = load_messages()
    files = collect_files()

    all_violations = []
    for f in files:
        all_violations.extend(analyze_file(f, messages))

    if args.json:
        print(json.dumps({
            "total": len(all_violations),
            "violations": all_violations,
            "files_scanned": len(files),
        }, ensure_ascii=False, indent=2))
    else:
        if all_violations:
            # Group by file for readability
            by_file = {}
            for v in all_violations:
                by_file.setdefault(v["file"], []).append(v)
            print(f"\n⚠ i18n sensor: {len(all_violations)} violation(s) em {len(by_file)} arquivo(s) (scan: {len(files)} arquivos .ts/.tsx)\n")
            for fpath, vs in sorted(by_file.items()):
                print(f"\n{fpath}:")
                for v in vs:
                    print(format_violation(v))
            print(f"\nTotal: {len(all_violations)} violation(s).")
            print("Modo:", "BLOCKING (exit 1)" if args.blocking else "warn-only (exit 0)")
        else:
            print(f"✓ i18n sensor: 0 violations em {len(files)} arquivos .ts/.tsx")

    if args.blocking and len(all_violations) > args.max_violations:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
