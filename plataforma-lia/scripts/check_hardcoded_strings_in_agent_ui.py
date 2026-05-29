#!/usr/bin/env python3
"""Sensor harness (warn-only) — detecta strings PT-BR hardcoded em componentes
de Agent Studio que NÃO passam por useTranslations/t().

CONTEXTO (CLAUDE.md i18n contract + AUDIT 3/5 P2-8, C6.7 Fase 2.5):
  O sensor `check_i18n_keys.py` só valida que `t('key')` resolve no JSON —
  NÃO detecta o caso oposto: strings PT-BR escritas direto no JSX/props sem
  passar por `useTranslations`. Foi exatamente assim que os 4 componentes da
  Onda 2 (Agent Studio) atravessaram code review com texto hardcoded: como
  nunca chamavam t(), o sensor de keys ficava cego.

  Este sensor é o complemento: pega texto PT-BR que deveria ter virado chave
  i18n mas ficou literal.

ESCOPO (surfaces de Agent Studio — Fase 2/2.5):
  - src/components/pages-agent-studio/
  - src/components/pages/tasks/Agent*.tsx
  - src/components/jobs/JobAgent*.tsx
  - src/components/candidates/

HEURÍSTICA (2 padrões):
  1. JSX text node: `>Texto PT-BR<` com 2+ palavras (inicial maiúscula + minúsc)
  2. Prop de UI: `title=`, `label=`, `placeholder=`, `aria-label=` com string
     literal contendo 2+ palavras

  Filtros pra reduzir falso positivo:
  - Só conta se houver SINAL PT-BR (acento OU palavra-stopword PT-BR comum),
    pra não pegar texto inglês legítimo (ex: nomes de libs, ids).
  - Ignora se a string vem de `t(...)` na mesma linha.
  - Ignora arquivos de teste (__tests__, .test., .spec.).
  - Ignora linhas comentadas (// ou *).

MODO: warn-only (exit 0 sempre, salvo --blocking). Baseline pode ter
  violations residuais — ratchet. Promover a --blocking quando baseline = 0.

Uso:
  python3 scripts/check_hardcoded_strings_in_agent_ui.py            # warn-only
  python3 scripts/check_hardcoded_strings_in_agent_ui.py --blocking # exit 1 se > max
  python3 scripts/check_hardcoded_strings_in_agent_ui.py --max-violations N
  python3 scripts/check_hardcoded_strings_in_agent_ui.py --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent  # plataforma-lia/
SRC = ROOT / "src"

# Diretórios / globs de escopo (Agent Studio surfaces).
SCOPE_DIRS = [
    SRC / "components" / "pages-agent-studio",
    SRC / "components" / "candidates",
]
SCOPE_GLOBS = [
    (SRC / "components" / "pages" / "tasks", "Agent*.tsx"),
    (SRC / "components" / "jobs", "JobAgent*.tsx"),
]

EXCLUDE_FILE_PATTERNS = (".test.tsx", ".test.ts", ".spec.tsx", ".spec.ts", ".d.ts")
EXCLUDE_DIRS = {"__tests__", "node_modules", ".next", "dist", "build"}

# Sinal PT-BR: acento OU stopword frequente. Sem isso, não conta (evita inglês).
_PT_ACCENT = re.compile(r"[áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ]")
_PT_STOPWORDS = {
    "o", "a", "os", "as", "de", "da", "do", "das", "dos", "em", "no", "na",
    "nos", "nas", "um", "uma", "uns", "umas", "para", "por", "com", "sem",
    "que", "qual", "quais", "como", "quando", "onde", "seu", "sua", "seus",
    "suas", "este", "esta", "esse", "essa", "isso", "aqui", "ver", "criar",
    "editar", "salvar", "excluir", "voltar", "cancelar", "adicionar", "novo",
    "nova", "todos", "todas", "agente", "agentes", "vaga", "vagas",
    "candidato", "candidatos", "selecione", "buscar", "pesquisar", "filtro",
    "filtros", "nome", "configuração", "configuracao", "ações", "acoes",
}

# Palavras: inicial maiúscula seguida de minúsculas (com acentos) OU minúscula.
_WORD = r"[A-Za-zÀ-ÖØ-öø-ÿ][a-zà-öø-ÿ]+"
# JSX text node: >  Texto Com Palavras  <
_JSX_TEXT = re.compile(r">\s*(" + _WORD + r"(?:\s+" + _WORD + r")+)\s*<")
# Prop de UI com string literal.
_UI_PROP = re.compile(
    r"\b(title|label|placeholder|aria-label)\s*=\s*\"("
    + _WORD + r"(?:[\s\?\!\.,:]+" + _WORD + r")+)\""
)


def _has_pt_signal(text: str) -> bool:
    if _PT_ACCENT.search(text):
        return True
    tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", text.lower())
    return any(tok in _PT_STOPWORDS for tok in tokens)


def _is_comment_line(line: str) -> bool:
    s = line.strip()
    return s.startswith("//") or s.startswith("*") or s.startswith("/*")


def _scope_files() -> list[Path]:
    files: list[Path] = []
    for d in SCOPE_DIRS:
        if not d.exists():
            continue
        for f in d.rglob("*.tsx"):
            if any(part in EXCLUDE_DIRS for part in f.parts):
                continue
            if f.name.endswith(EXCLUDE_FILE_PATTERNS):
                continue
            files.append(f)
    for base, pat in SCOPE_GLOBS:
        if not base.exists():
            continue
        for f in base.glob(pat):
            if f.name.endswith(EXCLUDE_FILE_PATTERNS):
                continue
            files.append(f)
    return sorted(set(files))


def scan_file(path: Path) -> list[dict]:
    violations: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return violations
    rel = path.relative_to(ROOT)
    for lineno, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        # Ignora linha que claramente usa t(...) — assume já-i18n.
        line_uses_t = bool(re.search(r"\bt(?:[A-Z][A-Za-z]*)?\s*\(", line))

        for m in _JSX_TEXT.finditer(line):
            text = m.group(1).strip()
            if not _has_pt_signal(text):
                continue
            # Se o match está dentro de {t(...)}, a linha conteria t( antes do >.
            if line_uses_t and "{" in line[: m.start()]:
                continue
            violations.append({
                "file": str(rel), "line": lineno, "kind": "jsx_text", "text": text,
            })

        for m in _UI_PROP.finditer(line):
            prop, text = m.group(1), m.group(2).strip()
            if not _has_pt_signal(text):
                continue
            violations.append({
                "file": str(rel), "line": lineno, "kind": f"prop:{prop}", "text": text,
            })
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true")
    parser.add_argument("--max-violations", type=int, default=0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    all_violations: list[dict] = []
    files = _scope_files()
    for f in files:
        all_violations.extend(scan_file(f))

    if args.json:
        print(json.dumps({"count": len(all_violations), "violations": all_violations}, ensure_ascii=False, indent=2))
    else:
        print(f"[hardcoded-strings sensor] {len(files)} arquivos de Agent Studio escaneados.")
        if not all_violations:
            print("[hardcoded-strings sensor] OK — nenhuma string PT-BR hardcoded detectada.")
        else:
            print(f"[hardcoded-strings sensor] {len(all_violations)} string(s) PT-BR hardcoded (deveriam usar useTranslations):\n")
            for v in all_violations:
                print(f"  [{v['file']}:{v['line']}] {v['kind']}: \"{v['text']}\"")
            print(
                "\n  → Fix: migrar pra useTranslations('namespace') + t('chave') e adicionar"
                "\n    a chave em messages/pt-BR.json E messages/en.json. Ver CLAUDE.md"
                "\n    § i18n contract canonical."
            )

    over = len(all_violations) > args.max_violations
    if args.blocking and over:
        print(f"\n  Modo BLOCKING: {len(all_violations)} > max {args.max_violations} — exit 1.")
        return 1
    if all_violations and not args.blocking:
        print(f"\n  Modo warn-only (baseline {len(all_violations)}) — exit 0. Ratchet: zerar e promover a --blocking.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
