"""Tests for GAP-05-003: pipeline_rules canonical OFFER_STAGES + is_offer_stage.

Sensor: ensures OFFER_STAGES is the single source of truth and is_offer_stage
works correctly across all canonical variants.
"""
import pytest
from app.shared.pipeline_rules import OFFER_STAGES, is_offer_stage


class TestOfferStages:
    def test_offer_stages_is_frozenset(self):
        assert isinstance(OFFER_STAGES, frozenset)

    def test_canonical_variants_present(self):
        expected = {"proposta", "offer", "proposal", "contratação", "contratacao", "hiring"}
        assert expected.issubset(OFFER_STAGES)

    def test_is_offer_stage_proposta(self):
        assert is_offer_stage("proposta") is True

    def test_is_offer_stage_offer(self):
        assert is_offer_stage("offer") is True

    def test_is_offer_stage_proposal(self):
        assert is_offer_stage("proposal") is True

    def test_is_offer_stage_hiring(self):
        assert is_offer_stage("hiring") is True

    def test_is_offer_stage_contratacao_accent(self):
        assert is_offer_stage("contratação") is True

    def test_is_offer_stage_contratacao_no_accent(self):
        assert is_offer_stage("contratacao") is True

    def test_is_offer_stage_case_insensitive(self):
        assert is_offer_stage("PROPOSTA") is True
        assert is_offer_stage("Offer") is True
        assert is_offer_stage("HIRING") is True

    def test_is_offer_stage_whitespace_stripped(self):
        assert is_offer_stage("  proposta  ") is True

    def test_is_offer_stage_non_offer_stages(self):
        assert is_offer_stage("triagem") is False
        assert is_offer_stage("entrevista") is False
        assert is_offer_stage("rejected") is False
        assert is_offer_stage("hired") is False

    def test_is_offer_stage_none_returns_false(self):
        assert is_offer_stage(None) is False

    def test_is_offer_stage_empty_string_returns_false(self):
        assert is_offer_stage("") is False
        assert is_offer_stage("   ") is False
