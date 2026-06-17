#!/usr/bin/env python3
"""Onda 1 F9 (2026-05-27) — sensor canonical Studio DecisionTreeDrawer.

Garante que toda usage de `<DecisionTreeDrawer>` em src/components/ use
EXATAMENTE as props canonical:
  - executionId  (string | null)
  - onClose      (() => void)

Se uma Onda 2/3 quiser passar prop nova, ela TEM que:
  1. Atualizar `DecisionTreeDrawerProps` em `decision-tree/DecisionTreeDrawer.tsx`
  2. Atualizar este sensor (bumpar `ALLOWED_PROPS`)
  3. Rodar todos os tests do drawer pra garantir não-regressão

Modo: BLOCKING por default. Exit 1 quando viola.

Mensagem otimizada pra consumo de LLM:
  - aponta arquivo:linha
  - lista prop inválida + sugestão de fix
  - referência ao arquivo canonical de definição
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src"

# Props canonical em DecisionTreeDrawerProps. Mudar aqui exige mudar o type
# em src/components/pages-agent-studio/decision-tree/DecisionTreeDrawer.tsx.
ALLOWED_PROPS = {"executionId", "onClose"}

# Patterns que casam usage <DecisionTreeDrawer ... />.
# Suporta multi-linha; capturamos tudo entre o nome e o primeiro '>' não-prefixado.
DRAWER_BLOCK_RE = re.compile(
    r"<DecisionTreeDrawer\b([\s\S]*?)(/?>)",
    re.MULTILINE,
)
# Captura prop names: nome= ou nome (boolean shorthand).
PROP_NAME_RE = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=|$|\s)")

CANONICAL_DEF = (
    "src/components/pages-agent-studio/decision-tree/DecisionTreeDrawer.tsx"
)


def find_violations() -> list[tuple[Path, int, str, set[str]]]:
    """Retorna (file, line, snippet, unknown_props) por usage não-canonical."""
    violations: list[tuple[Path, int, str, set[str]]] = []
    for tsx in ROOT.rglob("*.tsx"):
        # Skip o próprio definidor + testes que mockam props extras.
        if "decision-tree/DecisionTreeDrawer" in str(tsx):
            continue
        text = tsx.read_text(encoding="utf-8")
        if "<DecisionTreeDrawer" not in text:
            continue
        for match in DRAWER_BLOCK_RE.finditer(text):
            block_inner = match.group(1)
            # Extrai prop names (top-level only — não validamos contents).
            props = set()
            # Heurística: cada token "nome=" ou "nome " no início de uma "linha"
            # é considerado prop. Filtramos depois.
            for prop_match in re.finditer(
                r"(?:^|\s)([a-zA-Z_][a-zA-Z0-9_]*)\s*=",
                block_inner,
            ):
                props.add(prop_match.group(1))
            unknown = props - ALLOWED_PROPS
            if unknown:
                line_no = text[: match.start()].count("\n") + 1
                snippet = block_inner.strip().splitlines()[0][:80]
                violations.append((tsx, line_no, snippet, unknown))
    return violations


def main() -> int:
    violations = find_violations()
    if not violations:
        print("✅ DecisionTreeDrawer usage canonical (0 violations).")
        return 0

    print("❌ DecisionTreeDrawer usage NÃO-canonical detectado.\n")
    print(f"   Props canonical permitidas: {sorted(ALLOWED_PROPS)}")
    print(f"   Definição canonical: {CANONICAL_DEF}\n")
    for path, line, snippet, unknown in violations:
        rel = path.relative_to(ROOT.parent)
        print(f"  [{rel}:{line}] props inválidas: {sorted(unknown)}")
        print(f"    snippet: {snippet}")
        print(
            "    → Fix: remova a prop inválida OU atualize DecisionTreeDrawerProps "
            "+ ALLOWED_PROPS neste sensor."
        )
        print()
    print(f"Total: {len(violations)} violação(ões).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
