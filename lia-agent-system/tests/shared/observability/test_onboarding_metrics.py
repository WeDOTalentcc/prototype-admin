"""Tests P2-2 Sprint C — onboarding metrics canonical."""
from __future__ import annotations

import pytest

from app.shared.observability.onboarding_metrics import (
    hash_company_id,
    onboarding_chat_abandoned_total,
    onboarding_chat_completed_total,
    onboarding_chat_started_total,
    onboarding_extraction_confidence,
    onboarding_extraction_duration_seconds,
    onboarding_field_extracted_total,
    onboarding_field_skipped_total,
    onboarding_field_validation_failed_total,
    progress_bucket,
    record_chat_abandoned,
    record_chat_completed,
    record_chat_started,
    record_extraction_duration,
    record_field_extracted,
    record_field_skipped,
    record_field_validation_failed,
)


# ---------- helpers ----------

def _counter_value(counter, **labels) -> float:
    """Read current counter value (sum across labels if no labels passed)."""
    try:
        total = 0.0
        for metric in counter.collect():
            for sample in metric.samples:
                if not sample.name.endswith("_total"):
                    continue
                if labels:
                    if all(sample.labels.get(k) == v for k, v in labels.items()):
                        total += sample.value
                else:
                    total += sample.value
        return total
    except Exception:
        return 0.0


def _histogram_count(histogram) -> float:
    try:
        for metric in histogram.collect():
            for sample in metric.samples:
                if sample.name.endswith("_count") and not sample.labels:
                    return sample.value
        return 0.0
    except Exception:
        return 0.0


# ---------- TestProgressBucket ----------

class TestProgressBucket:
    def test_low_progress(self):
        assert progress_bucket(10) == "0-25"

    def test_mid_progress(self):
        assert progress_bucket(30) == "25-50"

    def test_high_progress(self):
        assert progress_bucket(75) == "50-80"

    def test_exactly_25(self):
        assert progress_bucket(25) == "25-50"

    def test_exactly_80(self):
        # ate <80 ainda eh abandoned bucket; >=80 nao chama record_chat_abandoned
        assert progress_bucket(80) == "50-80"

    def test_zero(self):
        assert progress_bucket(0) == "0-25"


# ---------- TestHashCompanyId ----------

class TestHashCompanyId:
    def test_deterministic(self):
        assert hash_company_id("abc") == hash_company_id("abc")

    def test_different_inputs(self):
        assert hash_company_id("abc") != hash_company_id("xyz")

    def test_length_12(self):
        assert len(hash_company_id("anything")) == 12

    def test_unicode_safe(self):
        # nao deve estourar com unicode (LGPD: company name pode ter acento)
        out = hash_company_id("Empresa Ação")
        assert isinstance(out, str)
        assert len(out) == 12


# ---------- TestCounters ----------

class TestCounters:
    def test_chat_started_increments(self):
        before = _counter_value(onboarding_chat_started_total)
        record_chat_started()
        after = _counter_value(onboarding_chat_started_total)
        assert after == before + 1

    def test_chat_completed_increments(self):
        before = _counter_value(onboarding_chat_completed_total)
        record_chat_completed()
        after = _counter_value(onboarding_chat_completed_total)
        assert after == before + 1

    def test_chat_abandoned_low_bucket(self):
        before = _counter_value(
            onboarding_chat_abandoned_total, progress_bucket="0-25"
        )
        record_chat_abandoned(progress=15)
        after = _counter_value(
            onboarding_chat_abandoned_total, progress_bucket="0-25"
        )
        assert after == before + 1

    def test_chat_abandoned_mid_bucket(self):
        before = _counter_value(
            onboarding_chat_abandoned_total, progress_bucket="25-50"
        )
        record_chat_abandoned(progress=40)
        after = _counter_value(
            onboarding_chat_abandoned_total, progress_bucket="25-50"
        )
        assert after == before + 1

    def test_field_extracted_with_labels(self):
        before = _counter_value(
            onboarding_field_extracted_total, field_key="mission"
        )
        record_field_extracted(field_key="mission", confidence=0.85)
        after = _counter_value(
            onboarding_field_extracted_total, field_key="mission"
        )
        assert after == before + 1

    def test_field_extracted_observes_confidence(self):
        before = _histogram_count(onboarding_extraction_confidence)
        record_field_extracted(field_key="vision", confidence=0.92)
        after = _histogram_count(onboarding_extraction_confidence)
        assert after == before + 1

    def test_field_skipped_increments(self):
        before = _counter_value(
            onboarding_field_skipped_total, field_key="phone"
        )
        record_field_skipped("phone")
        after = _counter_value(
            onboarding_field_skipped_total, field_key="phone"
        )
        assert after == before + 1

    def test_field_validation_failed_with_rule(self):
        before = _counter_value(
            onboarding_field_validation_failed_total,
            field_key="cnpj",
            validation_rule="format",
        )
        record_field_validation_failed("cnpj", "format")
        after = _counter_value(
            onboarding_field_validation_failed_total,
            field_key="cnpj",
            validation_rule="format",
        )
        assert after == before + 1

    def test_field_validation_failed_default_rule(self):
        # rule vazia -> "unknown"
        before = _counter_value(
            onboarding_field_validation_failed_total,
            field_key="website",
            validation_rule="unknown",
        )
        record_field_validation_failed("website", "")
        after = _counter_value(
            onboarding_field_validation_failed_total,
            field_key="website",
            validation_rule="unknown",
        )
        assert after == before + 1

    def test_extraction_duration_observes(self):
        before = _histogram_count(onboarding_extraction_duration_seconds)
        record_extraction_duration(1.5)
        after = _histogram_count(onboarding_extraction_duration_seconds)
        assert after == before + 1
