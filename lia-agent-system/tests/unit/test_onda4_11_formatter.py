"""Onda 4.11 — lia_briefing_formatter reads actual briefing_service keys.

Runtime smoke revealed formatter returned "" because it read legacy keys
(pipeline_summary, active_alerts) that generate_daily_briefing() never
produces. Actual contract uses `pipeline`, `alerts`, `urgent_actions`,
`summary`.

Canonical-fix: formatter is consumer of briefing_service output — aligns
keys to producer contract. Not a silent fallback; formatter returns empty
string only when briefing genuinely has no signals.
"""
from __future__ import annotations


def test_formatter_produces_summary_with_active_jobs_and_candidates() -> None:
    """Onda 4.11: briefing with pipeline.active_jobs + total_candidates → non-empty."""
    from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
        format_briefing_for_greeting,
    )
    briefing = {
        "summary": {"urgent_count": 0, "tasks_today": 0, "alerts_active": 0},
        "urgent_actions": [],
        "pipeline": {"active_jobs": 30, "total_candidates": 320, "stages": {}},
        "alerts": [],
    }
    result = format_briefing_for_greeting(briefing)
    assert result, "formatter must produce non-empty summary when pipeline has jobs/candidates"
    assert "30" in result
    # Should mention pipeline context somehow (vagas / candidatos)
    assert "vaga" in result.lower() or "candidato" in result.lower()


def test_formatter_prefers_urgent_actions_when_present() -> None:
    """Onda 4.11: urgent_actions take priority over neutral pipeline counts."""
    from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
        format_briefing_for_greeting,
    )
    briefing = {
        "summary": {"urgent_count": 3},
        "urgent_actions": [{"type": "stale_offer", "id": "v1"}, {"type": "missing_feedback", "id": "c1"}, {"type": "stale_stage", "id": "c2"}],
        "pipeline": {"active_jobs": 30, "total_candidates": 320},
        "alerts": [],
    }
    result = format_briefing_for_greeting(briefing)
    assert result
    assert "3" in result
    assert "urgente" in result.lower() or "ação" in result.lower() or "ações" in result.lower()


def test_formatter_includes_alerts_when_present() -> None:
    """Onda 4.11: alerts list surfaces count."""
    from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
        format_briefing_for_greeting,
    )
    briefing = {
        "summary": {},
        "urgent_actions": [],
        "pipeline": {"active_jobs": 0, "total_candidates": 0},
        "alerts": [{"severity": "HIGH"}, {"severity": "MEDIUM"}],
    }
    result = format_briefing_for_greeting(briefing)
    assert result
    assert "2" in result
    assert "alerta" in result.lower()


def test_formatter_empty_on_all_zeros() -> None:
    """Onda 4.11: nothing to say → empty string (don't fabricate signals)."""
    from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
        format_briefing_for_greeting,
    )
    briefing = {
        "summary": {},
        "urgent_actions": [],
        "pipeline": {"active_jobs": 0, "total_candidates": 0, "stages": {}},
        "alerts": [],
    }
    result = format_briefing_for_greeting(briefing)
    assert result == ""


def test_formatter_none_briefing_returns_empty() -> None:
    """Onda 4.11 regression: None briefing still → empty."""
    from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
        format_briefing_for_greeting,
    )
    assert format_briefing_for_greeting(None) == ""


def test_formatter_backward_compat_with_legacy_keys() -> None:
    """Onda 4.11: if legacy pipeline_summary/active_alerts still present, still works."""
    from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
        format_briefing_for_greeting,
    )
    briefing = {
        "urgent_actions": [],
        "pipeline_summary": {"stale_candidates_count": 5, "missing_feedback_count": 2},
        "active_alerts": [{"severity": "HIGH"}],
    }
    result = format_briefing_for_greeting(briefing)
    assert result, "legacy key contract still works"
    assert "5" in result
