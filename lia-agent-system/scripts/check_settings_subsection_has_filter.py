#!/usr/bin/env python3
"""WT-2022: Sensor anti alias visual (false promise UI) em hubs de Settings.

Detecta quando um hub renderiza o MESMO componente para múltiplas subsections
SEM passar uma prop diferenciadora (filter / mode / scope / dataset).
Esse padrão cria "alias visual" — UI promete duas funcionalidades distintas
mas entrega exatamente a mesma coisa renderizada (false promise).

Bug histórico que motivou (audit Wave 1 hub #3 P1.B, 2026-05-21):

    // ❌ ANTI-PATTERN — FairnessComplianceHub.tsx
    {activeSubsection === "lgpd-candidatos" && <DSRInboxPanel />}
    {activeSubsection === "fairness"        && <DSRInboxPanel />}
    {activeSubsection === "audit"           && <DSRInboxPanel />}

Os 3 itens do menu lateral acabavam mostrando exatamente o mesmo painel
DSRInbox sem filtro. UX quebrava trust (recrutador clica em "Fairness"
esperando dashboards de bias, recebe inbox LGPD).

Padrão canonical (correto):

    // ✅ canonical
    {activeSubsection === "lgpd-candidatos" && <DSRInboxPanel scope="candidates" />}
    {activeSubsection === "fairness"        && <FairnessDashboard />}
    {activeSubsection === "audit"           && <AuditTrailPanel />}

OU se for legitimamente o mesmo componente com filtro diferente:

    // ✅ canonical (mesmo componente, propes diferenciadoras)
    {activeSubsection === "lgpd-candidatos" && <DSRInboxPanel scope="candidates" />}
    {activeSubsection === "lgpd-employees"  && <DSRInboxPanel scope="employees" />}

Estratégia de detecção (AST-based):
1. Procura por arquivos *Hub*.tsx ou *Settings*Panel*.tsx em plataforma-lia/src/.
2. Faz parse leve via regex (TSX não tem parser AST Python out-of-the-box;
   regex é suficiente porque padrão é estilizado e repetitivo).
3. Para cada arquivo, extrai todas as ocorrências de:
       activeSubsection === "X" && <Component prop1={...} ... />
4. Agrupa por Component name. Se >= 2 ocorrências do MESMO componente com:
   (a) MESMOS props (ou ausência de props), e
   (b) subsection strings DIFERENTES,
   reporta como violation.
5. Honra marker `{/* SUBSECTION-ALIAS-EXEMPT: <reason> */}` na linha anterior.

Modo: warn-only baseline inicial. Promove a BLOCKING quando baseline = 0.

Saída otimizada para LLM consumer (instruction-tuned messages em PT-BR).
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, NamedTuple

# Diretórios padrão de scan (relativos ao workspace root)
DEFAULT_SCAN_PATHS = (
    "plataforma-lia/src/components/settings",
    "plataforma-lia/src/components/hubs",
    "plataforma-lia/src/app",
)

# Pattern: `activeSubsection === "subsection-name" && <ComponentName ... />`
# Captura: (subsection_string, component_name, props_string)
SUBSECTION_PATTERN = re.compile(
    r'activeSubsection\s*===\s*["\']([^"\']+)["\']\s*&&\s*<([A-Z][A-Za-z0-9_]+)([^/>]*?)/?>',
    re.MULTILINE,
)

EXEMPT_MARKER = "SUBSECTION-ALIAS-EXEMPT"


class Match(NamedTuple):
    file: Path
    line_no: int
    subsection: str
    component: str
    props_raw: str
    exempt_reason: str | None


def normalize_props(props_raw: str) -> str:
    """Normaliza props pra comparação: remove whitespace + ordem alfabética.

    Não é parser TSX real — heurística. Se props complexas (closures inline,
    spreads), normalização vira no-op e o sensor pode dar falso positivo;
    nesse caso o dev marca com EXEMPT.
    """
    cleaned = re.sub(r"\s+", " ", props_raw).strip()
    # Quebra em tokens separados por espaço top-level (heurística — não trata
    # nesting de { } perfeitamente; bom o bastante pra detectar "mesma prop list").
    tokens = sorted(cleaned.split())
    return " ".join(tokens)


def has_exempt_marker(lines: list[str], target_line_no: int) -> str | None:
    """Procura `{/* SUBSECTION-ALIAS-EXEMPT: reason */}` nas 3 linhas anteriores."""
    start = max(0, target_line_no - 4)
    for line in lines[start:target_line_no]:
        if EXEMPT_MARKER in line:
            match = re.search(rf"{EXEMPT_MARKER}:\s*(.+?)\s*\*/", line)
            if match:
                return match.group(1).strip()
            return "unspecified"
    return None


def scan_file(path: Path) -> list[Match]:
    """Extrai todos os padrões `activeSubsection === X && <Y .../>` do arquivo."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    lines = text.splitlines()
    matches: list[Match] = []
    for m in SUBSECTION_PATTERN.finditer(text):
        # Calcula line_no baseado em offset
        line_no = text.count("\n", 0, m.start()) + 1
        exempt = has_exempt_marker(lines, line_no)
        matches.append(
            Match(
                file=path,
                line_no=line_no,
                subsection=m.group(1),
                component=m.group(2),
                props_raw=m.group(3),
                exempt_reason=exempt,
            )
        )
    return matches


def find_aliases(matches: Iterable[Match]) -> list[tuple[str, list[Match]]]:
    """Agrupa por (component_name, normalized_props). Retorna grupos com >= 2 subsections."""
    grouped: dict[tuple[str, str], list[Match]] = defaultdict(list)
    for m in matches:
        if m.exempt_reason is not None:
            continue
        key = (m.component, normalize_props(m.props_raw))
        grouped[key].append(m)

    violations: list[tuple[str, list[Match]]] = []
    for (component, props_norm), group in grouped.items():
        # Dedupe subsections do mesmo arquivo
        unique_subsections = {(g.file, g.subsection) for g in group}
        if len({sub for _, sub in unique_subsections}) >= 2:
            violations.append((component, group))
    return violations


def collect_tsx_files(scan_paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for base in scan_paths:
        if not base.exists():
            continue
        for ext in ("*.tsx", "*.jsx"):
            files.extend(base.rglob(ext))
    return sorted(set(files))


def format_violation(component: str, group: list[Match]) -> str:
    lines = [
        f"\n  Componente: <{component} ... />",
        f"  Renderizado em {len({m.subsection for m in group})} subsections distintas SEM prop diferenciadora:",
    ]
    for m in sorted(group, key=lambda x: (str(x.file), x.line_no)):
        lines.append(f"    - {m.file}:{m.line_no}  subsection=\"{m.subsection}\"")
    lines.append("")
    lines.append("  Por que isso é problema:")
    lines.append("    Múltiplos itens do menu lateral entregam exatamente a MESMA UI.")
    lines.append("    Usuário clica em opções diferentes esperando experiências diferentes,")
    lines.append("    e recebe a mesma tela — quebra de promise visual (false promise UI).")
    lines.append("")
    lines.append("  Como corrigir:")
    lines.append("    Opção A) Trocar pelo componente correto de cada subsection.")
    lines.append('       {activeSubsection === "fairness" && <FairnessDashboard />}')
    lines.append("")
    lines.append("    Opção B) Adicionar prop diferenciadora (scope/mode/filter):")
    lines.append(f'       {{activeSubsection === "X" && <{component} scope="A" />}}')
    lines.append(f'       {{activeSubsection === "Y" && <{component} scope="B" />}}')
    lines.append("")
    lines.append("    Opção C) Se for legítimo (mesma view duplicada conscientemente),")
    lines.append("       marcar com:")
    lines.append("       {/* SUBSECTION-ALIAS-EXEMPT: <motivo claro> */}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sensor anti alias visual em hubs de Settings (WT-2022).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root (default: cwd)",
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        default=list(DEFAULT_SCAN_PATHS),
        help="Subdirs a escanear (relativos a --root)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit code 1 quando violações encontradas (default: warn-only exit 0).",
    )
    args = parser.parse_args()

    scan_paths = [args.root / p for p in args.paths]
    files = collect_tsx_files(scan_paths)
    if not files:
        print(
            f"[check_settings_subsection_has_filter] nenhum arquivo .tsx/.jsx em {scan_paths}",
            file=sys.stderr,
        )
        return 0

    all_matches: list[Match] = []
    for f in files:
        all_matches.extend(scan_file(f))

    violations = find_aliases(all_matches)

    if not violations:
        print(
            f"[check_settings_subsection_has_filter] OK — 0 alias visual em "
            f"{len(files)} arquivos escaneados ({len(all_matches)} subsection patterns)."
        )
        return 0

    print(
        f"\n[check_settings_subsection_has_filter] ⚠ {len(violations)} alias visual potencial(is) "
        f"em {len(files)} arquivos escaneados:\n"
    )
    for component, group in violations:
        print(format_violation(component, group))

    print(
        f"\nResumo: {len(violations)} componentes com alias visual. "
        f"Modo: {'STRICT (exit 1)' if args.strict else 'warn-only (exit 0)'}.\n"
    )
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
