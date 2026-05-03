"""Unit tests for WsiSkillClassifier - Sprint B Phase 3."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def test_classifier_with_no_llm_uses_heuristic():
    from app.domains.job_creation.services.wsi_skill_classifier import (
        WsiSkillClassifier,
    )
    clf = WsiSkillClassifier(llm=None)

    result = clf.classify("Conte sobre uma vez que voce precisou cumprir um prazo apertado")
    assert result["source"] == "heuristic"
    # Pattern bate em "prazo|deadline|urgente"
    assert result["skill_id"] == "delivery_under_deadline_pressure"


def test_classifier_empty_text_returns_default():
    from app.domains.job_creation.services.wsi_skill_classifier import (
        DEFAULT_FALLBACK_SKILL,
        WsiSkillClassifier,
    )
    clf = WsiSkillClassifier(llm=None)

    result = clf.classify("")
    assert result["skill_id"] == DEFAULT_FALLBACK_SKILL
    assert result["source"] == "default"


def test_classifier_heuristic_priorization():
    from app.domains.job_creation.services.wsi_skill_classifier import (
        WsiSkillClassifier,
    )
    clf = WsiSkillClassifier(llm=None)

    result = clf.classify("Voce teve que escolher entre 3 demandas urgentes")
    # "escolher entre" e "priorizar" estao na lista
    assert result["skill_id"] == "prioritization_with_competing_demands"


def test_classifier_keyword_no_match_uses_default():
    from app.domains.job_creation.services.wsi_skill_classifier import (
        DEFAULT_FALLBACK_SKILL,
        WsiSkillClassifier,
    )
    clf = WsiSkillClassifier(llm=None)

    result = clf.classify("Some random text without any keywords matching")
    assert result["skill_id"] == DEFAULT_FALLBACK_SKILL
    assert result["source"] == "heuristic"


def test_classifier_with_llm_returns_llm_source():
    """LLM retorna skill_id valido - source=llm."""
    from app.domains.job_creation.services.wsi_skill_classifier import (
        WsiSkillClassifier,
    )
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(return_value=MagicMock(content="active_listening"))

    clf = WsiSkillClassifier(llm=mock_llm)
    result = clf.classify("How well do you listen?")
    assert result["skill_id"] == "active_listening"
    assert result["source"] == "llm"


def test_classifier_with_llm_invalid_response_falls_back_to_heuristic():
    """LLM retorna texto invalido - fallback heuristic."""
    from app.domains.job_creation.services.wsi_skill_classifier import (
        WsiSkillClassifier,
    )
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(return_value=MagicMock(content="garbage_not_a_skill"))

    clf = WsiSkillClassifier(llm=mock_llm)
    result = clf.classify("Conte sobre uma vez com prazo")
    # LLM invalida -> heuristic captura "prazo"
    assert result["source"] == "heuristic"
    assert result["skill_id"] == "delivery_under_deadline_pressure"


def test_classifier_with_llm_exception_falls_back_to_heuristic():
    """LLM raise - fallback heuristic, NEVER raises."""
    from app.domains.job_creation.services.wsi_skill_classifier import (
        WsiSkillClassifier,
    )
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(side_effect=RuntimeError("LLM down"))

    clf = WsiSkillClassifier(llm=mock_llm)
    result = clf.classify("uma decisao com dados")
    # Nao raise - heuristic captura "dado"
    assert result["source"] == "heuristic"


def test_classifier_normalize_strips_quotes():
    """LLM response com quotes/whitespace - normaliza pra skill_id."""
    from app.domains.job_creation.services.wsi_skill_classifier import (
        WsiSkillClassifier,
    )
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(return_value=MagicMock(
        content='  "active_listening"  ',
    ))

    clf = WsiSkillClassifier(llm=mock_llm)
    result = clf.classify("test")
    assert result["skill_id"] == "active_listening"
