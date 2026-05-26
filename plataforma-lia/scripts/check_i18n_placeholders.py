#!/usr/bin/env python3
"""
check_i18n_placeholders.py — sensor canonical (harness-engineering).

Detecta strings i18n com placeholder dinamico (ex: {aiAssistant}) onde o
call site t() correspondente NAO passa o context object.

Bug recorrente (audit Paulo 2026-05-26 + Sprint 2 white-label drift):
  messages/pt-BR.json:
    "studio.chooseTemplateOrDescribe": "Escolha um template ou descreva para {aiAssistant}..."
  
  AgentStudioPage.tsx:641:
    {t("studio.chooseTemplateOrDescribe")}   <-- FORMATTING_ERROR runtime, sem fallback

Erro acontece em runtime (browser) como next-intl FORMATTING_ERROR. Bundlers e
linters NAO pegam — esse sensor pega ANTES do deploy.

Regra:
  1. Walk messages/pt-BR.json e messages/en.json. Para cada string value, extrair
     placeholders dinamicos via regex `\{([a-zA-Z_][a-zA-Z0-9_]*)\}` (next-intl ICU
     simples; ignora plurals/selects que tem `{var, plural,...}`).
  2. Coletar dotted key path completo (ex: "agents.studio.chooseTemplateOrDescribe").
  3. Walk src/**/*.{ts,tsx}. Encontrar todos t("ns") + bindings + chamadas t(key).
     Para cada call site cujo dotted key estah no set de placeholders, verificar
     se a chamada passa segundo arg `{ <placeholder>: ... }`.
  4. Se faltar, emitir violation.

Output otimizado pra consumo de LLM (instrucao de fix embutida).
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MESSAGES_DIR = ROOT / "messages"
SRC_DIR = ROOT / "src"

# Match {varName} but NOT {var, plural, ...} (ICU advanced syntax).
PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

# Catch: t('key.path')  OR  t("key.path")
T_CALL_RE = re.compile(r"""\bt\(\s*['"]([^'"]+)['"]\s*(,\s*\{[^)]*\})?\s*\)""", re.MULTILINE)
# Catch: const t = useTranslations('ns') OR ("ns")
USE_TRANSL_RE = re.compile(r"""const\s+(\w+)\s*=\s*useTranslations\(\s*['"]([^'"]+)['"]\s*\)""")
# Alt call sites where var name != 't' (e.g., tRich, tOnboarding)
VAR_CALL_RE = re.compile(r"""\b(\w+)\(\s*['"]([^'"]+)['"]\s*(,\s*\{[^)]*\})?\s*\)""", re.MULTILINE)

EXCLUDE_DIRS = {"node_modules", ".next", "__tests__", "test", "tests"}


def collect_keys_with_placeholders() -> dict[str, set[str]]:
    """Walk messages JSON; return {dotted.key: {placeholder_names}}."""
    keys: dict[str, set[str]] = {}
    for locale_file in ["pt-BR.json", "en.json"]:
        path = MESSAGES_DIR / locale_file
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        _walk(data, "", keys)
    return keys


def _walk(obj, prefix: str, out: dict[str, set[str]]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            _walk(v, f"{prefix}.{k}" if prefix else k, out)
    elif isinstance(obj, str):
        placeholders = set(PLACEHOLDER_RE.findall(obj))
        # Filter ICU advanced (e.g., obj contains "{count, plural,"); skip if ANY
        # placeholder appears followed by ", plural" or ", select".
        if placeholders:
            for ph in list(placeholders):
                if re.search(rf"\{{{re.escape(ph)}\s*,\s*(plural|select|selectordinal)", obj):
                    placeholders.discard(ph)
        if placeholders:
            out.setdefault(prefix, set()).update(placeholders)


def scan_file(path: Path, keys_needing_args: dict[str, set[str]]) -> list[str]:
    """Return list of violations in path."""
    try:
        text = path.read_text()
    except Exception:
        return []

    violations: list[str] = []

    # Find all useTranslations bindings (var name -> namespace prefix)
    bindings: dict[str, str] = {}
    for m in USE_TRANSL_RE.finditer(text):
        var_name, ns = m.group(1), m.group(2)
        bindings[var_name] = ns

    if not bindings:
        return []

    # Walk each call site `<var>('key')`
    for m in VAR_CALL_RE.finditer(text):
        var_name, raw_key, second_arg = m.group(1), m.group(2), m.group(3)
        if var_name not in bindings:
            continue
        ns = bindings[var_name]
        full_key = f"{ns}.{raw_key}"
        if full_key not in keys_needing_args:
            continue
        placeholders = keys_needing_args[full_key]
        # If no 2nd arg -> violation. If 2nd arg present, check that each placeholder appears.
        if second_arg is None:
            line_no = text[: m.start()].count("\n") + 1
            ph_list = ", ".join(sorted(placeholders))
            violations.append(
                f"[{path.relative_to(ROOT)}:{line_no}] {var_name}('{raw_key}') -> {full_key}\n"
                f"  Missing context for placeholders: {{{ph_list}}}\n"
                f"  -> Fix: pass {{ {', '.join(f'{p}: <value>' for p in sorted(placeholders))} }} as 2nd arg"
            )
        else:
            # Verify each placeholder is mentioned
            missing = [p for p in placeholders if not re.search(rf"\b{re.escape(p)}\s*:", second_arg)]
            if missing:
                line_no = text[: m.start()].count("\n") + 1
                violations.append(
                    f"[{path.relative_to(ROOT)}:{line_no}] {var_name}('{raw_key}') -> {full_key}\n"
                    f"  Missing in args: {', '.join(missing)}\n"
                    f"  -> Fix: add {', '.join(f'{p}: <value>' for p in missing)} to context object"
                )
    return violations


def main(argv: list[str]) -> int:
    blocking = "--blocking" in argv
    keys = collect_keys_with_placeholders()
    if not keys:
        print("No keys with dynamic placeholders found in messages/")
        return 0

    all_violations: list[str] = []
    for path in SRC_DIR.rglob("*.tsx"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        all_violations.extend(scan_file(path, keys))
    for path in SRC_DIR.rglob("*.ts"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        all_violations.extend(scan_file(path, keys))

    if all_violations:
        print(f"\nFound {len(all_violations)} i18n placeholder violations:\n")
        for v in all_violations:
            print(v)
            print()
        if blocking:
            return 1
        else:
            print(f"(warn-only mode — use --blocking to fail CI)")
    else:
        print("0 i18n placeholder violations (canonical baseline)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
