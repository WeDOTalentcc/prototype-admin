"""Coverage tests for wizard_suggestion_priority.py — WizardSuggestion + pick_canonical."""
import pytest
from app.shared.wizard_suggestion_priority import WizardSuggestion, pick_canonical


def _high(source="history", min_=5000.0, max_=8000.0, sample=20):
    return WizardSuggestion(
        source=source,
        recommended_min=min_,
        recommended_max=max_,
        confidence="high",
        sample_size=sample,
    )


def _low(source="market", min_=4000.0, max_=7000.0, sample=5):
    return WizardSuggestion(
        source=source,
        recommended_min=min_,
        recommended_max=max_,
        confidence="low",
        sample_size=sample,
    )


class TestWizardSuggestionDataclass:
    def test_has_data_with_min(self):
        s = WizardSuggestion(source="h", recommended_min=5000.0, recommended_max=None)
        assert s.has_data is True

    def test_has_data_false_when_min_none(self):
        s = WizardSuggestion(source="h", recommended_min=None, recommended_max=8000.0)
        assert s.has_data is False

    def test_has_data_false_when_min_zero(self):
        s = WizardSuggestion(source="h", recommended_min=0.0, recommended_max=8000.0)
        assert s.has_data is False

    def test_default_confidence_is_low(self):
        s = WizardSuggestion(source="h", recommended_min=5000.0, recommended_max=8000.0)
        assert s.confidence == "low"

    def test_default_sample_size_is_zero(self):
        s = WizardSuggestion(source="h", recommended_min=5000.0, recommended_max=8000.0)
        assert s.sample_size == 0

    def test_metadata_defaults_to_empty_dict(self):
        s = WizardSuggestion(source="h", recommended_min=5000.0, recommended_max=8000.0)
        assert s.metadata == {}


class TestPickCanonical:
    def test_both_none_returns_none(self):
        assert pick_canonical(None, None) is None

    def test_only_history_no_data_returns_none(self):
        s = WizardSuggestion(source="h", recommended_min=None, recommended_max=None)
        assert pick_canonical(history=s, market=None) is None

    def test_only_history_returns_history(self):
        h = _high()
        result = pick_canonical(history=h)
        assert result is h

    def test_only_market_returns_market(self):
        m = _low(source="market")
        result = pick_canonical(market=m)
        assert result is m

    def test_high_history_wins_over_low_market(self):
        h = _high("history")
        m = _low("market")
        result = pick_canonical(history=h, market=m)
        assert result is h

    def test_high_market_beats_low_history(self):
        h = WizardSuggestion(source="history", recommended_min=5000.0, recommended_max=8000.0, confidence="low")
        m = WizardSuggestion(source="market", recommended_min=4000.0, recommended_max=7000.0, confidence="high")
        result = pick_canonical(history=h, market=m)
        assert result is m

    def test_equal_confidence_history_wins(self):
        h = WizardSuggestion(source="history", recommended_min=5000.0, recommended_max=8000.0, confidence="medium", sample_size=10)
        m = WizardSuggestion(source="market", recommended_min=4000.0, recommended_max=7000.0, confidence="medium", sample_size=10)
        result = pick_canonical(history=h, market=m)
        assert result is h

    def test_equal_confidence_larger_market_sample_wins(self):
        h = WizardSuggestion(source="history", recommended_min=5000.0, recommended_max=8000.0, confidence="medium", sample_size=5)
        m = WizardSuggestion(source="market", recommended_min=4000.0, recommended_max=7000.0, confidence="medium", sample_size=20)
        result = pick_canonical(history=h, market=m)
        assert result is m

    def test_history_no_data_only_market_returned(self):
        h = WizardSuggestion(source="history", recommended_min=None, recommended_max=None)
        m = _low("market")
        result = pick_canonical(history=h, market=m)
        assert result is m

    def test_market_no_data_only_history_returned(self):
        h = _high("history")
        m = WizardSuggestion(source="market", recommended_min=None, recommended_max=None)
        result = pick_canonical(history=h, market=m)
        assert result is h
