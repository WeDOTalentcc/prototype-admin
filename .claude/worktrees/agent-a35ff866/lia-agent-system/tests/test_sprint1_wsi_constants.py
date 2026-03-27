"""
Tests for Sprint 1 — WSI canonical constants.
"""
import pytest
from app.domains.cv_screening.constants.wsi_constants import (
    WSI_DIMENSION_LABELS,
    WSI_DIMENSION_WEIGHTS_DEFAULT,
    WSI_BLOCK_NAMES,
)


class TestWSIDimensionLabels:
    def test_four_canonical_dimensions_exist(self):
        assert set(WSI_DIMENSION_LABELS.keys()) == {"technical", "behavioral", "gap_analysis", "contextual"}

    def test_dimension_labels_are_portuguese(self):
        assert WSI_DIMENSION_LABELS["technical"] == "Competências Técnicas"
        assert WSI_DIMENSION_LABELS["behavioral"] == "Competências Comportamentais"
        assert WSI_DIMENSION_LABELS["gap_analysis"] == "Experiência Profissional"
        assert WSI_DIMENSION_LABELS["contextual"] == "Fit Cultural e Alinhamento"

    def test_weights_sum_to_one(self):
        total = sum(WSI_DIMENSION_WEIGHTS_DEFAULT.values())
        assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"

    def test_weights_match_guia_v3(self):
        assert WSI_DIMENSION_WEIGHTS_DEFAULT["technical"] == 0.50
        assert WSI_DIMENSION_WEIGHTS_DEFAULT["behavioral"] == 0.20
        assert WSI_DIMENSION_WEIGHTS_DEFAULT["gap_analysis"] == 0.15
        assert WSI_DIMENSION_WEIGHTS_DEFAULT["contextual"] == 0.15


class TestWSIBlockNames:
    def test_six_blocks_defined(self):
        assert len(WSI_BLOCK_NAMES) == 6

    def test_block_2_includes_company(self):
        name = WSI_BLOCK_NAMES[2]
        assert "Empresa" in name, (
            f"Block 2 name '{name}' should mention Empresa"
        )

    def test_block_3_aligns_with_technical(self):
        assert "Técnic" in WSI_BLOCK_NAMES[3], (
            f"Block 3 '{WSI_BLOCK_NAMES[3]}' should align with 'Competências Técnicas'"
        )

    def test_block_4_aligns_with_behavioral(self):
        name = WSI_BLOCK_NAMES[4]
        assert "Comportamental" in name or "Fit" in name, (
            f"Block 4 '{name}' should align with behavioral dimension"
        )

    def test_no_old_labels_remain(self):
        old_labels = {"Análise de Gaps", "Contexto e Motivação", "Perguntas Finais", "Elegibilidade e Formação"}
        all_names = set(WSI_BLOCK_NAMES.values())
        overlap = old_labels & all_names
        assert not overlap, f"Deprecated labels still present: {overlap}"
