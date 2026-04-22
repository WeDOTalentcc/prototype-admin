"""Onda 4.8 FIX 35 — G1 conversational polish tests."""
from __future__ import annotations

from pathlib import Path

import yaml


def _find_persona() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "app/prompts/shared/lia_persona.yaml"
        if cand.exists():
            return cand
    raise RuntimeError("lia_persona.yaml not found")


def test_fix35_marker_in_persona() -> None:
    """FIX 35: persona content contains FIX 35 marker."""
    data = yaml.safe_load(_find_persona().read_text(encoding="utf-8"))
    persona = data["prompts"]["lia_persona"]
    assert "FIX 35" in persona


def test_persona_has_respostas_ricas_section() -> None:
    """FIX 35: new ## Estrutura de Respostas Ricas section present."""
    data = yaml.safe_load(_find_persona().read_text(encoding="utf-8"))
    persona = data["prompts"]["lia_persona"]
    assert "Estrutura de Respostas Ricas" in persona


def test_persona_mentions_citations_footnotes_pattern() -> None:
    """FIX 35: citations footnote pattern documented."""
    data = yaml.safe_load(_find_persona().read_text(encoding="utf-8"))
    persona = data["prompts"]["lia_persona"]
    low = persona.lower()
    assert "footnote" in low or "[^1]" in persona or "superscript" in low
    assert "search_jobs" in persona, "FIX 35: should show concrete tool_name example"


def test_persona_mentions_numbered_options_pattern() -> None:
    """FIX 35: numbered options (action chips alt) documented."""
    data = yaml.safe_load(_find_persona().read_text(encoding="utf-8"))
    persona = data["prompts"]["lia_persona"]
    low = persona.lower()
    assert "numeradas" in low or "numbered" in low
    assert "1)" in persona or "1." in persona  # concrete numbering example


def test_persona_mentions_filtros_em_texto_pattern() -> None:
    """FIX 35: filtros em texto (filter chips alt) documented."""
    data = yaml.safe_load(_find_persona().read_text(encoding="utf-8"))
    persona = data["prompts"]["lia_persona"]
    assert "Filtros ativos" in persona or "filtros ativos" in persona
    assert "remover" in persona.lower()


def test_persona_mentions_progress_streaming_pattern() -> None:
    """FIX 35: progress streaming deltas documented."""
    data = yaml.safe_load(_find_persona().read_text(encoding="utf-8"))
    persona = data["prompts"]["lia_persona"]
    low = persona.lower()
    assert "progress" in low or "1/4" in persona or "2/4" in persona


def test_persona_mentions_error_recovery_offers() -> None:
    """FIX 35: error recovery ofertas em texto documented."""
    data = yaml.safe_load(_find_persona().read_text(encoding="utf-8"))
    persona = data["prompts"]["lia_persona"]
    low = persona.lower()
    assert "timeout" in low or "tentar de novo" in low or "rota de saída" in low
    assert "abrir ticket" in low or "ajustar filtros" in low


def test_persona_yaml_still_parses_after_fix35() -> None:
    """FIX 35 regression: YAML must still load cleanly."""
    data = yaml.safe_load(_find_persona().read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "prompts" in data
    assert "lia_persona" in data["prompts"]
    assert len(data["prompts"]["lia_persona"]) > 1000
