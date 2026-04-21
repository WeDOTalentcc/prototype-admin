"""Onda 2.3 Init IV — Proactive Agenda tests.

Covers:
- Formatter handles empty / None briefing gracefully
- Formatter produces PT greeting summary for non-empty briefing
- Top-3 cap maintained
- Never exposes candidate names (LGPD defense)
- Feature flag off → empty string
- TTL cache hit/miss behavior
"""
from __future__ import annotations


def test_format_none_returns_empty() -> None:
    """Init IV: None briefing → empty string (greeting omits agenda)."""
    from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
        format_briefing_for_greeting,
    )

    assert format_briefing_for_greeting(None) == ""


def test_format_empty_dict_returns_empty() -> None:
    """Init IV: empty briefing → empty string."""
    from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
        format_briefing_for_greeting,
    )

    assert format_briefing_for_greeting({}) == ""


def test_format_urgent_actions_counted() -> None:
    """Init IV: urgent_actions list produces count-based sentence."""
    from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
        format_briefing_for_greeting,
    )

    briefing = {"urgent_actions": [{"id": "a1"}, {"id": "a2"}, {"id": "a3"}]}
    out = format_briefing_for_greeting(briefing)
    assert "3" in out
    assert "urgente" in out.lower()


def test_format_pipeline_stale_and_feedback() -> None:
    """Init IV: pipeline_summary counts render."""
    from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
        format_briefing_for_greeting,
    )

    briefing = {
        "pipeline_summary": {
            "stale_candidates_count": 5,
            "missing_feedback_count": 2,
        }
    }
    out = format_briefing_for_greeting(briefing)
    assert "5" in out and "parado" in out.lower()
    assert "2" in out and "feedback" in out.lower()


def test_format_top_3_cap() -> None:
    """Init IV: never more than 3 items (keeps greeting concise)."""
    from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
        format_briefing_for_greeting,
    )

    briefing = {
        "urgent_actions": [{"id": i} for i in range(10)],
        "pipeline_summary": {
            "stale_candidates_count": 7,
            "missing_feedback_count": 4,
        },
        "active_alerts": [{"id": i} for i in range(6)],
    }
    out = format_briefing_for_greeting(briefing)
    # 3 comma-separated parts max → string has 1 "e" + 1 "," at most
    assert out.count(",") <= 1
    # 4th item (alerts) should NOT appear given first 3 fill up
    # urgent(10) + stale(7) + missing(4) = 3 items, alerts skipped
    assert "alerta" not in out.lower() or out.count(",") >= 2


def test_format_never_exposes_candidate_names() -> None:
    """Init IV LGPD: even if briefing has names, formatter uses counts only."""
    from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
        format_briefing_for_greeting,
    )

    briefing = {
        "urgent_actions": [
            {"id": "a1", "candidate_name": "João Silva", "description": "Candidato João parado"},
            {"id": "a2", "candidate_name": "Maria Santos"},
        ],
        "pipeline_summary": {
            "stale_candidates_count": 1,
        },
    }
    out = format_briefing_for_greeting(briefing)
    assert "João" not in out
    assert "Silva" not in out
    assert "Maria" not in out
    assert "Santos" not in out


def test_feature_flag_off_returns_empty() -> None:
    """Init IV: env LIA_PROACTIVE_AGENDA_ENABLED=false → passthrough empty."""
    import app.domains.recruiter_assistant.services.lia_briefing_formatter as mod

    original = mod._PROACTIVE_AGENDA_ENABLED
    try:
        mod._PROACTIVE_AGENDA_ENABLED = False
        briefing = {"urgent_actions": [{"id": "a1"}]}
        assert mod.format_briefing_for_greeting(briefing) == ""
    finally:
        mod._PROACTIVE_AGENDA_ENABLED = original


def test_cache_invalidate_all() -> None:
    """Init IV: invalidate_cache() clears in-memory store."""
    from app.domains.recruiter_assistant.services import lia_briefing_formatter as mod

    mod._CACHE[("u1", "c1")] = ({"test": 1}, 99999999999.0)
    assert len(mod._CACHE) >= 1
    mod.invalidate_cache()
    assert len(mod._CACHE) == 0


def test_initIV_marker_present() -> None:
    """Init IV audit marker for traceability."""
    from pathlib import Path

    import app.domains.recruiter_assistant.services.lia_briefing_formatter as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "Init IV" in source, "Init IV: formatter module must contain Init IV marker"
    assert "format_briefing_for_greeting" in source
    assert "get_cached_briefing" in source
