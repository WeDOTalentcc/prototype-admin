"""
glossary_loader — carrega docs/GLOSSARY.md em runtime.

Permite que agentes acessem definicoes canonicas dos termos da plataforma
sem depender de blocos estaticos hardcoded no system prompt. O parser
le o markdown gerado/mantido por scripts/glossary_sync.py e expoe:

  - get_glossary(): dict normalized_name -> GlossaryEntry
  - get_term(name): lookup tolerante a acento/caixa
  - render_canonical_terms_section(keys): bloco markdown com definicoes
  - detect_drift(keys): lista de termos canonicos ausentes do glossario

O caminho do arquivo pode ser sobrescrito via env LIA_GLOSSARY_PATH
para testes. O carregamento e cacheado com lru_cache (limpe com
get_glossary.cache_clear() em tests).
"""
from __future__ import annotations

import logging
import os
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


_DEFAULT_GLOSSARY_PATH = (
    Path(__file__).resolve().parents[4] / "docs" / "GLOSSARY.md"
)


CANONICAL_PROMPT_TERMS: tuple[str, ...] = (
    "WSI",
    "WSI_tecnico",
    "WSI_comportamental",
    "WSI Final",
    "Bloom",
    "Dreyfus",
    "Big Five",
    "OCEAN",
    "CBI",
    "STAR",
    "BARS",
    "Gate",
    "JD Quality Score",
    "Smart Saturation",
    "Dynamic Cutoff",
    "FairnessGuard",
    "Bloco A",
    "Bloco B",
)


@dataclass(frozen=True)
class GlossaryEntry:
    name: str
    normalized: str
    sigla: str
    definition: str
    category: str


def _normalize(name: str) -> str:
    name = re.sub(r"\s*\(.*?\)", "", name)
    name = re.sub(r"[\s\-_*\\]", "", name)
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return name.lower()


def _glossary_path() -> Path:
    override = os.environ.get("LIA_GLOSSARY_PATH")
    if override:
        return Path(override)
    return _DEFAULT_GLOSSARY_PATH


_FIELD_PATTERNS = {
    "sigla": re.compile(r"\|\s*\*\*Sigla\*\*\s*\|\s*(.+?)\s*\|"),
    "definition": re.compile(r"\|\s*\*\*Defini[cç][aã]o\*\*\s*\|\s*(.+?)\s*\|"),
    "category": re.compile(r"\|\s*\*\*Categoria\*\*\s*\|\s*(.+?)\s*\|"),
}


def _parse(content: str) -> dict[str, GlossaryEntry]:
    entries: dict[str, GlossaryEntry] = {}
    h3 = re.compile(r"^### (.+)$", re.MULTILINE)
    any_heading = re.compile(r"^#{1,6} ", re.MULTILINE)

    for match in h3.finditer(content):
        raw_name = match.group(1).strip()
        if "pendentes" in raw_name.lower():
            continue
        clean = re.sub(r"\*+", "", raw_name).strip()
        norm = _normalize(clean)

        body_start = match.end()
        nxt = any_heading.search(content, body_start)
        body = content[body_start: nxt.start() if nxt else len(content)]

        sigla_m = _FIELD_PATTERNS["sigla"].search(body)
        def_m = _FIELD_PATTERNS["definition"].search(body)
        cat_m = _FIELD_PATTERNS["category"].search(body)

        definition = (def_m.group(1).strip() if def_m else "").strip()
        if not definition or definition.lower().startswith("todo"):
            continue

        sigla = (sigla_m.group(1).strip() if sigla_m else "").strip()
        if sigla in {"—", "-"}:
            sigla = ""
        category = (cat_m.group(1).strip() if cat_m else "").strip()

        existing = entries.get(norm)
        if existing is None or (not existing.definition and definition):
            entries[norm] = GlossaryEntry(
                name=clean,
                normalized=norm,
                sigla=sigla,
                definition=definition,
                category=category,
            )
    return entries


@lru_cache(maxsize=1)
def get_glossary() -> dict[str, GlossaryEntry]:
    """Carrega e cacheia o glossario. Retorna {} se o arquivo nao existir."""
    path = _glossary_path()
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("[glossary_loader] Could not read %s: %s", path, exc)
        return {}
    try:
        entries = _parse(content)
        logger.info(
            "[glossary_loader] Loaded %d terms from %s", len(entries), path
        )
        return entries
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("[glossary_loader] Parse failed for %s: %s", path, exc)
        return {}


def get_term(name: str) -> GlossaryEntry | None:
    """Lookup tolerante a acento/caixa/parenteses."""
    return get_glossary().get(_normalize(name))


def detect_drift(keys: tuple[str, ...] | list[str] = CANONICAL_PROMPT_TERMS) -> list[str]:
    """Retorna a lista de termos canonicos que NAO foram encontrados no glossario.

    Use para alertar quando o prompt depende de um termo que sumiu do
    docs/GLOSSARY.md (drift entre prompt e fonte da verdade).
    """
    glossary = get_glossary()
    missing: list[str] = []
    for key in keys:
        if _normalize(key) not in glossary:
            missing.append(key)
    return missing


def render_canonical_terms_section(
    keys: tuple[str, ...] | list[str] = CANONICAL_PROMPT_TERMS,
) -> str:
    """Renderiza um bloco markdown com as definicoes canonicas dos termos.

    Retorna string vazia se nenhum termo foi encontrado (ex: arquivo
    indisponivel) — o caller deve cair para o fallback estatico.
    """
    glossary = get_glossary()
    if not glossary:
        return ""

    lines: list[str] = [
        "## Definicoes canonicas (fonte: docs/GLOSSARY.md)",
        "",
        "Use SEMPRE estes termos exatamente como definidos. Nao invente sinonimos.",
        "",
    ]
    rendered_any = False
    for key in keys:
        entry = glossary.get(_normalize(key))
        if not entry:
            continue
        rendered_any = True
        header = f"**{entry.name}**"
        if entry.sigla:
            header += f" ({entry.sigla})"
        lines.append(f"- {header}: {entry.definition}")

    if not rendered_any:
        return ""
    return "\n".join(lines) + "\n"
