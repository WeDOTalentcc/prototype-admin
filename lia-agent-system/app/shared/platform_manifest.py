"""
Platform Manifest Loader — reads app/config/platform_manifest.yaml and exposes
typed accessors for pages, methodology, and capabilities.

Any code that previously had hardcoded page lists, keywords, or methodology
descriptions should migrate to these accessors. Adding a new page only requires
editing the YAML.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    """Load platform_manifest.yaml with 1-entry lru_cache (invalidate with clear)."""
    path = Path(__file__).resolve().parent.parent / "config" / "platform_manifest.yaml"
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data
    except Exception as exc:
        logger.error("[PlatformManifest] Failed to load manifest: %s", exc)
        return {}


def clear_cache() -> None:
    """Invalidate the cache (useful in tests and on hot-reload)."""
    load_manifest.cache_clear()


def get_pages() -> dict[str, dict[str, Any]]:
    """Return {page_id: page_data} dict."""
    return load_manifest().get("pages", {})


def get_page(page_id: str) -> dict[str, Any] | None:
    """Return data for a specific page, or None if not in manifest."""
    return get_pages().get(page_id)


def get_navigation_patterns() -> list[tuple[list[tuple[str, float]], str, str]]:
    """
    Return navigation patterns in the legacy format used by NavigationIntentDetector:
    [(keywords_with_weights, display_name, hint), ...]
    """
    patterns: list[tuple[list[tuple[str, float]], str, str]] = []
    for _pid, pdata in get_pages().items():
        kws = pdata.get("keywords", [])
        if not kws:
            continue
        # keywords are [[word, weight], ...] from YAML
        weighted = [(str(kw[0]), float(kw[1])) for kw in kws if isinstance(kw, (list, tuple)) and len(kw) >= 2]
        if not weighted:
            continue
        patterns.append((
            weighted,
            pdata.get("display_name", _pid),
            pdata.get("navigation_hint", f"Quer que eu abra {pdata.get('display_name', _pid)}?"),
        ))
    return patterns


def get_methodology() -> dict[str, Any]:
    """Return the methodology section (WSI, Bloom, Dreyfus, Big Five)."""
    return load_manifest().get("methodology", {})


def get_capabilities() -> dict[str, str]:
    """Return the capabilities dict (cv_processing, interviews, boolean_strings, etc.)."""
    return load_manifest().get("capabilities", {})


def render_platform_knowledge_snippet() -> str:
    """
    Generate the _PLATFORM_KNOWLEDGE text injected in every system prompt.
    Pulls from the manifest so adding a new page / capability is reflected
    automatically.
    """
    m = load_manifest()
    pages = m.get("pages", {})
    methodology = m.get("methodology", {})
    capabilities = m.get("capabilities", {})

    lines: list[str] = []
    lines.append("## Conhecimento da Plataforma WeDOTalent\n")
    lines.append("Voce conhece todas as paginas, funcionalidades e metodologias abaixo.\n")
    lines.append("**Paginas principais** (voce pode navegar o recrutador ate elas):")
    for _pid, pdata in pages.items():
        dn = pdata.get("display_name", "")
        desc = pdata.get("description", "")
        lines.append(f"- **{dn}**: {desc}")

    if methodology:
        lines.append("\n## Metodologia (conhecimento canonico)\n")
        wsi = methodology.get("wsi", {})
        if wsi:
            lines.append(f"- **{wsi.get('name', 'WSI')}**: {wsi.get('formula', '')}")
        bloom = methodology.get("bloom", {})
        if bloom and bloom.get("levels"):
            niveis = ", ".join(f"{lv['level']} {lv['name']}" for lv in bloom["levels"])
            lines.append(f"- **Bloom**: {niveis}")
        dreyfus = methodology.get("dreyfus", {})
        if dreyfus and dreyfus.get("levels"):
            niveis = ", ".join(f"{lv['level']} {lv['name']}" for lv in dreyfus["levels"])
            lines.append(f"- **Dreyfus**: {niveis}")
        big5 = methodology.get("big_five", {})
        if big5 and big5.get("dimensions"):
            dims = ", ".join(big5["dimensions"])
            lines.append(f"- **Big Five**: {dims}")

    if capabilities:
        lines.append("\n## Capacidades reais (seja precisa)\n")
        for _cid, text in capabilities.items():
            lines.append(f"- {text}")

    lines.append(
        "\n**Regra de Proatividade**: Se detectar pre-condicao faltando "
        "(empresa sem perfil, vaga sem perguntas de triagem, candidato sem contato), "
        "OFERECA ajuda imediatamente — nao espere o recrutador perceber."
    )
    return "\n".join(lines)
