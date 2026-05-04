#!/usr/bin/env python3
"""
glossary_sync.py — Sincronização automática do Glossário Central da LIA.

Uso:
    python3 scripts/glossary_sync.py          # modo padrão (atualiza GLOSSARY.md)
    python3 scripts/glossary_sync.py --check  # modo CI (falha se há termos obrigatórios sem definição; não modifica arquivos)
    python3 scripts/glossary_sync.py --dry-run # mostra diff sem escrever

Estratégia de detecção em dois níveis:
  Nível 1 — Termos obrigatórios (bloqueiam CI se sem definição):
    • Termos em CANONICAL_REQUIRED_TERMS que correspondam ao código/docs
    • Siglas canônicas do domínio (WSI, BARS, CBI, OCEAN, etc.)
    • Gates G1–G6

  Nível 2 — Componentes arquiteturais (stubs, não bloqueiam CI):
    • Classes com sufixo *Guard, *Engine, *Orchestrator, *Graph, *Pipeline, *Scorer
    • Tools registradas no tool_registry_metadata.yaml

Leia docs/GLOSSARY_MAINTENANCE.md para entender o fluxo completo.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# ── Configuração de caminhos ──────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_PATH = ROOT / "docs" / "GLOSSARY.md"
REPORT_PATH = ROOT / "docs" / "glossary_sync_report.md"
TOOL_REGISTRY_YAML = ROOT / "lia-agent-system" / "app" / "tools" / "tool_registry_metadata.yaml"

# ── Termos obrigatórios — ausência bloqueia CI ────────────────────────────────

# Siglas que DEVEM estar no glossário
CANONICAL_SIGLAS = {
    "WSI", "BARS", "CBI", "STAR", "JD", "OCEAN", "LGPD",
}

# Gates canônicos (G1-G6 cobertos pela entrada "Gate (G1–G6)" no glossário)
GATES: set[str] = set()

# Nomes canônicos — usados para verificar presença mas normalizados para match
# (o glossário pode usar a forma extensa com parênteses, ex: "Bloom (Taxonomia de Bloom)")
CANONICAL_REQUIRED_TERMS = {
    # Scoring
    "WSI", "WSI Final", "WSI_tecnico", "WSI_comportamental",
    "Bloom", "Dreyfus", "BARS", "CBI", "STAR",
    "JD Quality Score", "Gate", "Inflacao", "Red Flag",
    "Scoring Rubric", "SHA-256", "Dynamic Cutoff",
    "Dreyfus Comportamental",
    # Behavioral — nomes sem acento para normalização robusta
    "Big Five", "OCEAN", "Trait", "Arquetipo",
    "Abertura", "Conscienciosidade", "Extroversao",
    "Amabilidade", "Estabilidade Emocional", "Neuroticismo",
    # Sistema
    "Bloco A", "Bloco B", "Compact", "Full",
    "Smart Saturation", "Calibration Loop",
    "LLM Extrator", "SystemPromptBuilder",
    "WSIInterviewGraph", "WSIVoiceOrchestrator",
    # Compliance
    "FairnessGuard", "PromptInjectionGuard", "LGPD", "EU AI Act",
    "DEI", "HITL",
    # Geral
    "JD", "Elegibilidade",
}

# ── Componentes arquiteturais — detectados mas não bloqueiam CI ───────────────

ARCHITECTURAL_CLASS_SUFFIXES = (
    "Guard", "Engine", "Orchestrator", "Graph",
    "Pipeline", "Scorer", "Generator", "Extractor",
)

IGNORE_TERMS = {
    "Guard", "Engine", "Agent", "Domain", "Router", "Manager",
    "Base", "None", "True", "False", "Test", "Mock", "Stub",
    "Config", "Settings", "Utils", "Helper", "Type", "Model",
    "Request", "Response", "Schema", "Error", "Exception",
    "BaseAgent", "BaseHandler", "BaseService", "BaseDomain",
    "Extractor", "Generator", "Pipeline", "Orchestrator", "Scorer",
}

# ── Padrões de varredura ──────────────────────────────────────────────────────

CODE_GLOBS = [
    "lia-agent-system/app/**/*.py",
    "lia-agent-system/app/**/*.yaml",
    "lia-agent-system/app/**/*.yml",
]

DOC_GLOBS = [
    "WeDO/**/*.md",
    "lia-agent-system/docs/**/*.md",
]


# ── Estruturas de dados ───────────────────────────────────────────────────────

@dataclass
class GlossaryTerm:
    name: str
    normalized: str
    has_definition: bool
    is_required: bool = False


@dataclass
class SyncReport:
    new_required_terms: list[str] = field(default_factory=list)
    new_architectural_terms: list[str] = field(default_factory=list)
    orphan_terms: list[str] = field(default_factory=list)
    undefined_required_terms: list[str] = field(default_factory=list)
    undefined_architectural_terms: list[str] = field(default_factory=list)
    total_glossary_terms: int = 0
    scanned_files: int = 0


# ── Normalização ──────────────────────────────────────────────────────────────

def _normalize(name: str) -> str:
    """
    Normaliza para comparação case-insensitive e sem espaços/pontuação.
    Remove também conteúdo entre parênteses para que
    "Abertura (Openness)" e "Abertura" sejam considerados equivalentes.
    """
    # Remove parênteses e conteúdo dentro
    name = re.sub(r"\s*\(.*?\)", "", name)
    # Remove caracteres especiais e lowercase
    name = re.sub(r"[\s\-_*\\]", "", name).lower()
    # Acentos → equivalentes ASCII para comparação
    accent_map = str.maketrans("áàâãéêíóôõúüçñ", "aaaaeeiooouucn")
    return name.translate(accent_map)


def _is_required(name: str) -> bool:
    """Verifica se o nome normalizado é um termo obrigatório."""
    n = _normalize(name)
    for req in CANONICAL_REQUIRED_TERMS | GATES | CANONICAL_SIGLAS:
        if _normalize(req) == n:
            return True
    return False


# ── Leitura do glossário atual ────────────────────────────────────────────────

def _parse_glossary(path: Path) -> dict[str, GlossaryTerm]:
    """Lê GLOSSARY.md e retorna dicionário normalized_name → GlossaryTerm."""
    if not path.exists():
        return {}

    content = path.read_text(encoding="utf-8")
    terms: dict[str, GlossaryTerm] = {}

    h3_pattern = re.compile(r"^### (.+)$", re.MULTILINE)
    any_heading_pattern = re.compile(r"^#{1,6} ", re.MULTILINE)
    todo_pattern = re.compile(r"TODO:\s*needs definition", re.IGNORECASE)

    for match in h3_pattern.finditer(content):
        raw_name = match.group(1).strip()
        if "pendentes" in raw_name.lower():
            continue

        clean_name = re.sub(r"\*+", "", raw_name).strip()
        norm = _normalize(clean_name)

        section_start = match.end()
        # Stop at the next heading of ANY level (h1-h6), not just h3
        next_heading = any_heading_pattern.search(content, section_start)
        section_end = next_heading.start() if next_heading else len(content)
        section_body = content[section_start:section_end]

        has_def = not bool(todo_pattern.search(section_body))
        req = _is_required(clean_name)

        # Termos obrigatórios: a versão extensa (com definição) prevalece
        existing = terms.get(norm)
        if existing is None or (has_def and not existing.has_definition):
            terms[norm] = GlossaryTerm(
                name=clean_name,
                normalized=norm,
                has_definition=has_def,
                is_required=req,
            )

    return terms


# ── Varredura do codebase ─────────────────────────────────────────────────────

def _extract_architectural_classes(file_path: Path) -> set[str]:
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return set()

    found: set[str] = set()
    class_pattern = re.compile(r"^class\s+([A-Z][A-Za-z0-9]+)", re.MULTILINE)
    for m in class_pattern.finditer(content):
        name = m.group(1)
        if name in IGNORE_TERMS:
            continue
        if any(name.endswith(s) for s in ARCHITECTURAL_CLASS_SUFFIXES):
            found.add(name)
    return found


def _extract_siglas_from_content(file_path: Path) -> set[str]:
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return set()

    found: set[str] = set()
    for sigla in CANONICAL_SIGLAS:
        if re.search(rf"\b{re.escape(sigla)}\b", content):
            found.add(sigla)
    return found


def _extract_tool_names(yaml_path: Path) -> set[str]:
    if not yaml_path.exists():
        return set()
    try:
        content = yaml_path.read_text(encoding="utf-8")
    except OSError:
        return set()

    found: set[str] = set()
    name_pattern = re.compile(r"^\s*-?\s*name:\s*([a-z_]+)", re.MULTILINE)
    for m in name_pattern.finditer(content):
        found.add(m.group(1))
    return found


def _scan_codebase(root: Path) -> tuple[set[str], set[str], int]:
    """
    Retorna:
      required_candidates  — termos obrigatórios (sempre o set completo)
      architectural_detected — componentes arquiteturais encontrados no código
      scanned — número de arquivos varridos
    """
    # Obrigatórios = conjunto completo, sem depender do código
    required_candidates: set[str] = set(CANONICAL_REQUIRED_TERMS) | GATES | CANONICAL_SIGLAS
    architectural_detected: set[str] = set()
    scanned = 0

    for glob_pattern in CODE_GLOBS:
        for file_path in root.glob(glob_pattern):
            if "__pycache__" in str(file_path):
                continue
            architectural_detected |= _extract_architectural_classes(file_path)
            required_candidates |= _extract_siglas_from_content(file_path)
            scanned += 1

    for glob_pattern in DOC_GLOBS:
        for file_path in root.glob(glob_pattern):
            required_candidates |= _extract_siglas_from_content(file_path)
            scanned += 1

    # Tools registradas — apenas stubs
    architectural_detected |= _extract_tool_names(TOOL_REGISTRY_YAML)

    return required_candidates, architectural_detected, scanned


# ── Comparação e diff ─────────────────────────────────────────────────────────

def _compare(
    glossary: dict[str, GlossaryTerm],
    required_candidates: set[str],
    architectural_detected: set[str],
) -> tuple[list[str], list[str], list[str]]:
    """
    Retorna:
      new_required      — obrigatórios ausentes do glossário
      new_architectural — arquiteturais ausentes do glossário
      orphan_terms      — no glossário mas não detectados
    """
    new_required: list[str] = []
    for term in sorted(required_candidates):
        norm = _normalize(term)
        if norm not in glossary and term not in IGNORE_TERMS:
            new_required.append(term)

    new_architectural: list[str] = []
    for term in sorted(architectural_detected):
        norm = _normalize(term)
        if norm not in glossary and term not in IGNORE_TERMS and len(term) > 4:
            new_architectural.append(term)

    # Órfãos: no glossário mas não em nenhuma fonte conhecida
    all_required_norms = {_normalize(t) for t in required_candidates}
    all_arch_norms = {_normalize(t) for t in architectural_detected}
    orphan_terms: list[str] = []
    for norm, term_obj in sorted(glossary.items(), key=lambda x: x[1].name):
        if norm not in all_required_norms and norm not in all_arch_norms:
            if not term_obj.is_required:
                orphan_terms.append(term_obj.name)

    return new_required, new_architectural, orphan_terms


# ── Atualização do GLOSSARY.md ────────────────────────────────────────────────

def _stub_entry(term: str, is_required: bool = False) -> str:
    today = date.today().isoformat()
    note = " ⚠️ **OBRIGATÓRIO — bloqueia CI**" if is_required else ""
    return (
        f"\n### {term}\n"
        f"| Campo | Valor |\n"
        f"|---|---|\n"
        f"| **Sigla** | — |\n"
        f"| **Definição** | TODO: needs definition{note} |\n"
        f"| **Categoria** | TODO |\n"
        f"| **Fontes** | TODO |\n"
        f"| **Código relacionado** | TODO |\n"
        f"| **Owner** | TODO |\n"
        f"| **last_updated** | {today} |\n"
    )


def _update_glossary(
    path: Path,
    new_required: list[str],
    new_architectural: list[str],
) -> None:
    """Adiciona stubs ao GLOSSARY.md. Nunca chamado em --check ou --dry-run."""
    content = path.read_text(encoding="utf-8")
    new_terms = new_required + new_architectural
    if not new_terms:
        return

    req_stubs = "\n".join(_stub_entry(t, is_required=True) for t in sorted(new_required))
    arch_stubs = "\n".join(_stub_entry(t, is_required=False) for t in sorted(new_architectural))
    stubs = req_stubs + ("\n" if arch_stubs else "") + arch_stubs

    placeholder = "| Termo | Detectado em | Status |\n|---|---|---|\n| — | — | — |"
    if placeholder in content:
        content = content.replace(placeholder, stubs, 1)
    else:
        pending_marker = "## Termos pendentes (TODO: needs definition)"
        if pending_marker in content:
            idx = content.index(pending_marker) + len(pending_marker)
            content = content[:idx] + "\n\n" + stubs + content[idx:]
        else:
            content += f"\n\n## Termos pendentes (TODO: needs definition)\n\n{stubs}\n"

    path.write_text(content, encoding="utf-8")


# ── Geração do relatório ──────────────────────────────────────────────────────

def _format_report(report: SyncReport) -> str:
    today = date.today().isoformat()
    blocking = report.undefined_required_terms
    lines = [
        f"# Relatório de Sync do Glossário — {today}",
        "",
        f"**Arquivos varridos:** {report.scanned_files}",
        f"**Termos no glossário:** {report.total_glossary_terms}",
        f"**Novos obrigatórios detectados:** {len(report.new_required_terms)}",
        f"**Novos arquiteturais detectados:** {len(report.new_architectural_terms)}",
        f"**Termos órfãos:** {len(report.orphan_terms)}",
        f"**Obrigatórios sem definição (bloqueiam CI):** {len(blocking)}",
        f"**Arquiteturais sem definição (não bloqueiam CI):** {len(report.undefined_architectural_terms)}",
        "",
    ]

    if blocking:
        lines += ["## ❌ Obrigatórios sem definição — BLOQUEIAM CI", ""]
        for t in sorted(blocking):
            lines.append(f"- `{t}` — preencher em docs/GLOSSARY.md")
        lines.append("")

    if report.new_required_terms:
        lines += ["## Novos obrigatórios (stubs adicionados)", ""]
        for t in sorted(report.new_required_terms):
            lines.append(f"- `{t}`")
        lines.append("")

    if report.new_architectural_terms:
        lines += ["## Novos arquiteturais (stubs adicionados, não bloqueiam CI)", ""]
        for t in sorted(report.new_architectural_terms[:50]):
            lines.append(f"- `{t}`")
        if len(report.new_architectural_terms) > 50:
            lines.append(f"- ... e mais {len(report.new_architectural_terms) - 50} termos")
        lines.append("")

    if report.orphan_terms:
        lines += ["## Termos órfãos (warning, não bloqueiam CI)", ""]
        for t in sorted(report.orphan_terms):
            lines.append(f"- `{t}`")
        lines.append("")

    return "\n".join(lines)


def _write_report(report: SyncReport, path: Path) -> None:
    path.write_text(_format_report(report), encoding="utf-8")


def _print_dry_run_report(report: SyncReport) -> None:
    content = _format_report(report)
    print("\n--- RELATÓRIO (dry-run) ---")
    print(content[:4000])
    if len(content) > 4000:
        print(f"... [truncado — {len(content)} chars total]")
    print("--- FIM DO RELATÓRIO ---\n")


# ── Modo CI ───────────────────────────────────────────────────────────────────

def _ci_check(report: SyncReport) -> int:
    """Retorna exit code: 0=ok, 1=há termos obrigatórios sem definição."""
    blocking = report.undefined_required_terms

    if blocking:
        print("❌ [glossary-sync] CI BLOQUEADO — termos obrigatórios sem definição:")
        for t in sorted(blocking):
            print(f"   • {t}")
        print(
            "\nAção necessária: edite docs/GLOSSARY.md e preencha a definição "
            "de cada termo acima (substitua 'TODO: needs definition')."
        )
        print(f"Relatório: {REPORT_PATH}")
        return 1

    if report.new_required_terms:
        print("⚠️  [glossary-sync] Termos obrigatórios sem entrada no glossário:")
        for t in sorted(report.new_required_terms):
            print(f"   • {t}")
        print("   → Execute `python3 scripts/glossary_sync.py` para adicionar stubs,")
        print("     depois preencha as definições antes do próximo PR.")
        print(f"Relatório: {REPORT_PATH}")
        return 1

    if report.new_architectural_terms:
        n = len(report.new_architectural_terms)
        print(f"ℹ️  [glossary-sync] {n} componentes arquiteturais novos (execute sync para adicionar stubs).")

    if report.orphan_terms:
        print(f"⚠️  [glossary-sync] {len(report.orphan_terms)} termos órfãos no glossário.")

    print(f"\n✅ [glossary-sync] OK — {report.total_glossary_terms} termos definidos, "
          f"{report.scanned_files} arquivos varridos.")
    return 0


# ── Entry point ───────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sincroniza o Glossário Central da LIA com o codebase."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Modo CI: falha (exit 1) se houver termos obrigatórios sem/com definição pendente. Não modifica arquivos.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra diff sem modificar arquivos.",
    )
    args = parser.parse_args(argv)

    readonly = args.check or args.dry_run

    print(f"[glossary-sync] Lendo glossário: {GLOSSARY_PATH}")
    glossary = _parse_glossary(GLOSSARY_PATH)

    print(f"[glossary-sync] Varrendo codebase em: {ROOT}")
    required_candidates, architectural_detected, scanned = _scan_codebase(ROOT)

    new_required, new_architectural, orphan_terms = _compare(
        glossary, required_candidates, architectural_detected
    )

    # Termos no glossário mas sem definição preenchida
    undefined_required = [
        t.name for t in glossary.values()
        if not t.has_definition and t.is_required
    ]
    undefined_architectural = [
        t.name for t in glossary.values()
        if not t.has_definition and not t.is_required
    ]

    report = SyncReport(
        new_required_terms=new_required,
        new_architectural_terms=new_architectural,
        orphan_terms=orphan_terms,
        undefined_required_terms=undefined_required,
        undefined_architectural_terms=undefined_architectural,
        total_glossary_terms=len(glossary),
        scanned_files=scanned,
    )

    if not readonly:
        if new_required or new_architectural:
            n = len(new_required) + len(new_architectural)
            print(f"[glossary-sync] Adicionando {n} stubs ao GLOSSARY.md...")
            _update_glossary(GLOSSARY_PATH, new_required, new_architectural)
        _write_report(report, REPORT_PATH)
        print(f"[glossary-sync] Relatório: {REPORT_PATH}")
        print(
            f"[glossary-sync] Concluído — {len(new_required)} novos obrigatórios, "
            f"{len(new_architectural)} novos arquiteturais, "
            f"{len(orphan_terms)} órfãos, "
            f"{len(undefined_required)} obrigatórios sem definição."
        )
    elif args.dry_run:
        _print_dry_run_report(report)

    if args.check:
        return _ci_check(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
