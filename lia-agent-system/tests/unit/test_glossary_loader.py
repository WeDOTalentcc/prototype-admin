"""Tests for runtime glossary integration into agent system prompts."""
from __future__ import annotations

import textwrap

import pytest

from app.shared.prompts import glossary_loader
from app.shared.prompts.glossary_loader import (
    CANONICAL_PROMPT_TERMS,
    detect_drift,
    get_glossary,
    get_term,
    render_canonical_terms_section,
)


@pytest.fixture(autouse=True)
def _reset_caches(monkeypatch):
    get_glossary.cache_clear()
    yield
    get_glossary.cache_clear()


def _write_glossary(tmp_path, body: str):
    path = tmp_path / "GLOSSARY.md"
    path.write_text(body, encoding="utf-8")
    return path


def test_loads_real_glossary_and_finds_canonical_terms():
    glossary = get_glossary()
    assert len(glossary) > 10, "Real glossary should parse many terms"
    wsi = get_term("WSI")
    assert wsi is not None
    assert "Work Suitability" in wsi.sigla or "Score" in wsi.definition
    assert "0" in wsi.definition  # mentions the 0-10 range


def test_render_section_includes_key_definitions():
    section = render_canonical_terms_section()
    assert "Definicoes canonicas" in section
    assert "WSI" in section
    assert "Bloom" in section
    assert "FairnessGuard" in section


def test_detect_drift_returns_empty_for_real_glossary():
    missing = detect_drift(CANONICAL_PROMPT_TERMS)
    assert missing == [], f"Glossary missing canonical terms: {missing}"


def test_detect_drift_flags_missing_terms(tmp_path, monkeypatch):
    body = textwrap.dedent(
        """
        # Glossary

        ### WSI
        | Campo | Valor |
        |---|---|
        | **Sigla** | WSI — Work Suitability Index |
        | **Definição** | Score 0-10 de adequacao. |
        | **Categoria** | Scoring |
        """
    ).strip()
    path = _write_glossary(tmp_path, body)
    monkeypatch.setenv("LIA_GLOSSARY_PATH", str(path))
    get_glossary.cache_clear()

    missing = detect_drift(["WSI", "Bloom", "FairnessGuard"])
    assert "WSI" not in missing
    assert "Bloom" in missing
    assert "FairnessGuard" in missing


def test_todo_entries_are_skipped(tmp_path, monkeypatch):
    body = textwrap.dedent(
        """
        ### Foo
        | Campo | Valor |
        |---|---|
        | **Sigla** | — |
        | **Definição** | TODO: needs definition |
        | **Categoria** | TODO |
        """
    ).strip()
    path = _write_glossary(tmp_path, body)
    monkeypatch.setenv("LIA_GLOSSARY_PATH", str(path))
    get_glossary.cache_clear()
    assert get_glossary() == {}


def test_missing_file_returns_empty_without_raising(tmp_path, monkeypatch):
    monkeypatch.setenv("LIA_GLOSSARY_PATH", str(tmp_path / "does_not_exist.md"))
    get_glossary.cache_clear()
    assert get_glossary() == {}
    assert render_canonical_terms_section() == ""


def test_system_prompt_builder_injects_canonical_glossary_block():
    """End-to-end: SystemPromptBuilder.build() must contain live glossary defs."""
    from app.shared.prompts import system_prompt_builder as spb

    # Force reload of the cached block so this test sees the real glossary.
    spb._get_canonical_glossary_block.cache_clear()
    spb._CANONICAL_GLOSSARY_BLOCK = spb._get_canonical_glossary_block()

    prompt = spb.SystemPromptBuilder.build(agent_type="orchestrator")
    assert "Definicoes canonicas" in prompt
    # WSI definition from the real glossary (not just the static fallback).
    assert "Work Suitability Index" in prompt
