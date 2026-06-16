"""
D7 — RRP Blocks (Rich Response Protocol) — proveniência e exhaustividade
D7-04: Sem score_explainer sem opinion_id (proveniência honesta)
D7-05: Tipos de bloco exaustivos (assertNever pattern no BE)

Testes E2E de caixa-preta: exercitam o BUILDER completo
(build_candidate_ranking_blocks / build_candidate_card_block) e a camada
de tipos (rrp_blocks._KIND_MAP / ResponseBlock) de ponta-a-ponta, SEM
banco real.

Relação com testes existentes:
  - tests/contract/test_rrp_provenance_gate.py — testa verify_block_provenance
    (o validator da primitiva), valores unitários.
  - tests/contract/test_rrp_moat_provenance.py — testa a shape do moat montado
    manualmente com dados de parecer.
  Este arquivo (e2e) cobre o BUILDER end-to-end: row dict → blocos emitidos,
  garantindo que a lógica de opinion_id condicional funcione no caminho real.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Helpers locais — construir rows de teste
# ---------------------------------------------------------------------------

def _row_without_opinion(cid: str = "cand-1", score: float = 78.0) -> dict:
    """Candidato SEM parecer — não deve gerar score_explainer."""
    return {
        "id": cid,
        "name": "Candidato Sem Parecer",
        "score": score,
        "stage": "triagem",
        # opinion_id ausente (key nem existe)
    }


def _row_with_opinion(cid: str = "cand-2", score: float = 88.0) -> dict:
    """Candidato COM parecer — deve gerar score_explainer + evidence_stack."""
    return {
        "id": cid,
        "name": "Candidato Com Parecer",
        "score": score,
        "stage": "entrevista",
        "opinion_id": "op-abc-001",
        "wsi_id": "wsi-xyz-002",
        "recommendation": "Altamente Recomendado",
        "summary": "Forte fit técnico com a vaga.",
        "strengths": ["Python sênior", "Arquitetura distribuída"],
        "concerns": ["Sem experiência em K8s"],
    }


# ---------------------------------------------------------------------------
# D7-04 — Sem score_explainer sem opinion_id
# ---------------------------------------------------------------------------

class TestRRPProvenance:
    """D7-04 — score_explainer só com parecer real (opinion_id)."""

    def test_no_score_explainer_without_opinion_id(self):
        """Candidato sem opinion_id não gera bloco score_explainer."""
        from app.shared.rrp_ranking_builder import build_candidate_ranking_blocks

        rows = [_row_without_opinion()]
        blocks = build_candidate_ranking_blocks(job_id="job-test-1", rows=rows)

        assert blocks, "builder deve retornar pelo menos a comparison_table"
        kinds = [b.get("kind") for b in blocks]
        assert "score_explainer" not in kinds, (
            f"sem opinion_id não deve emitir score_explainer; kinds={kinds}"
        )

    def test_score_explainer_emitted_with_opinion_id(self):
        """Candidato com opinion_id gera score_explainer + evidence_stack."""
        from app.shared.rrp_ranking_builder import build_candidate_ranking_blocks

        rows = [_row_with_opinion()]
        blocks = build_candidate_ranking_blocks(job_id="job-test-2", rows=rows)

        kinds = [b.get("kind") for b in blocks]
        assert "score_explainer" in kinds, (
            f"com opinion_id deve emitir score_explainer; kinds={kinds}"
        )
        assert "evidence_stack" in kinds, (
            f"com opinion_id deve emitir evidence_stack; kinds={kinds}"
        )

    def test_score_explainer_provenance_fields_present(self):
        """score_explainer emitido tem campos de proveniência preenchidos."""
        from app.shared.rrp_ranking_builder import build_candidate_ranking_blocks

        row = _row_with_opinion(cid="cand-3", score=91.0)
        blocks = build_candidate_ranking_blocks(job_id="job-test-3", rows=[row])

        explainers = [b for b in blocks if b.get("kind") == "score_explainer"]
        assert explainers, "deve haver pelo menos um score_explainer"
        exp = explainers[0]

        # proveniência real: subject vinculado ao candidato correto
        assert exp["subject_id"] == "cand-3", "subject_id deve ser o id do candidato"
        assert exp["subject_label"] == row["name"]

        # score é o valor real, não fabricado
        assert abs(exp["score"] - 91.0) < 0.001, "score deve vir do row, não inventado"
        assert exp["score_label"] == "Score LIA"

        # unverified=False quando há opinion_id (fonte verificável)
        assert exp["unverified"] is False, (
            "bloco com opinion_id deve ser unverified=False"
        )

        # confidence_basis derivada do recommendation do parecer
        assert exp["confidence_basis"], "confidence_basis não pode ser vazio com parecer"

    def test_no_score_explainer_mixed_rows(self):
        """Na lista mista, só candidatos com opinion_id geram score_explainer."""
        from app.shared.rrp_ranking_builder import build_candidate_ranking_blocks

        rows = [
            _row_without_opinion(cid="cand-no-1"),
            _row_with_opinion(cid="cand-with-1"),
            _row_without_opinion(cid="cand-no-2"),
        ]
        blocks = build_candidate_ranking_blocks(job_id="job-test-4", rows=rows)

        explainers = [b for b in blocks if b.get("kind") == "score_explainer"]
        assert len(explainers) == 1, (
            f"apenas 1 candidato tem opinion_id; encontrados {len(explainers)}"
        )
        assert explainers[0]["subject_id"] == "cand-with-1"

    def test_empty_rows_returns_no_blocks(self):
        """Lista vazia não deve gerar blocos (sem bloco vazio ou fabricado)."""
        from app.shared.rrp_ranking_builder import build_candidate_ranking_blocks

        blocks = build_candidate_ranking_blocks(job_id="job-empty", rows=[])
        assert blocks == [], f"esperava lista vazia, got {blocks}"

    def test_candidate_card_without_opinion_is_unverified(self):
        """CandidateCard sem opinion_id deve ser unverified=True e score=None."""
        from app.shared.rrp_ranking_builder import build_candidate_card_block

        row = _row_without_opinion(cid="cand-card-1", score=70.0)
        blocks = build_candidate_card_block(row)
        assert blocks, "deve retornar pelo menos um bloco"
        card = blocks[0]
        assert card["kind"] == "candidate_card"
        assert card["unverified"] is True, "sem opinion_id o card deve ser unverified"
        assert card["score"] is None, (
            "score não deve ser exibido sem opinion_id (proveniência honesta)"
        )

    def test_candidate_card_with_opinion_has_score(self):
        """CandidateCard com opinion_id tem score real e unverified=False."""
        from app.shared.rrp_ranking_builder import build_candidate_card_block

        row = _row_with_opinion(cid="cand-card-2", score=85.0)
        blocks = build_candidate_card_block(row)
        assert blocks
        card = blocks[0]
        assert card["unverified"] is False
        assert card["score"] is not None
        assert abs(card["score"] - 85.0) < 0.001

    def test_score_explainer_block_id_links_to_table_row(self):
        """comparison_table row.score_block_id deve apontar para o score_explainer."""
        from app.shared.rrp_ranking_builder import build_candidate_ranking_blocks

        row = _row_with_opinion(cid="cand-link-1")
        blocks = build_candidate_ranking_blocks(job_id="job-link", rows=[row])

        tables = [b for b in blocks if b.get("kind") == "comparison_table"]
        explainers = [b for b in blocks if b.get("kind") == "score_explainer"]
        assert tables and explainers

        table = tables[0]
        table_rows = table["rows"]
        matching_row = next(
            (r for r in table_rows if r["entity_id"] == "cand-link-1"), None
        )
        assert matching_row is not None
        assert matching_row.get("score_block_id") == explainers[0]["block_id"], (
            "table row deve linkar ao score_explainer via score_block_id"
        )

    def test_row_without_opinion_has_no_score_block_id(self):
        """comparison_table row sem opinion_id NÃO deve ter score_block_id."""
        from app.shared.rrp_ranking_builder import build_candidate_ranking_blocks

        row = _row_without_opinion(cid="cand-nolink-1")
        blocks = build_candidate_ranking_blocks(job_id="job-nolink", rows=[row])

        tables = [b for b in blocks if b.get("kind") == "comparison_table"]
        assert tables
        table_rows = tables[0]["rows"]
        matching_row = next(
            (r for r in table_rows if r["entity_id"] == "cand-nolink-1"), None
        )
        assert matching_row is not None
        assert matching_row.get("score_block_id") is None, (
            "sem opinion_id o score_block_id deve ser None (sem link fantasma)"
        )


# ---------------------------------------------------------------------------
# D7-05 — Tipos de bloco exaustivos (assertNever pattern no BE)
# ---------------------------------------------------------------------------

class TestRRPExhaustiveness:
    """D7-05 — tipos de bloco exaustivos (union discriminada, sem bloco fantasma)."""

    # Conjunto de kinds conhecidos e esperados no catálogo
    EXPECTED_KINDS = {
        "prose",
        "comparison_table",
        "score_explainer",
        "evidence_stack",
        "funnel",
        "candidate_card",
    }

    def test_all_expected_kinds_are_registered(self):
        """Todos os kinds esperados estão no _KIND_MAP (catálogo discriminado)."""
        from app.shared.rrp_blocks import _KIND_MAP

        missing = self.EXPECTED_KINDS - set(_KIND_MAP.keys())
        assert not missing, (
            f"kinds esperados ausentes do _KIND_MAP: {missing}. "
            "Adicione o tipo em rrp_blocks.py e atualize ResponseBlock."
        )

    def test_no_extra_undocumented_kinds(self):
        """_KIND_MAP não tem kinds não-documentados (sem tipo órfão/fantasma)."""
        from app.shared.rrp_blocks import _KIND_MAP

        undocumented = set(_KIND_MAP.keys()) - self.EXPECTED_KINDS
        assert not undocumented, (
            f"kinds não-documentados em _KIND_MAP: {undocumented}. "
            "Adicione ao EXPECTED_KINDS neste teste ou remova de rrp_blocks.py."
        )

    def test_kind_map_values_are_block_classes(self):
        """Cada entry do _KIND_MAP é uma classe Pydantic instanciável."""
        from app.shared.rrp_blocks import _KIND_MAP
        from pydantic import BaseModel

        for kind, cls in _KIND_MAP.items():
            assert issubclass(cls, BaseModel), (
                f"_KIND_MAP['{kind}'] = {cls} não é subclasse de BaseModel"
            )

    def test_unknown_block_type_rejected_by_response_block(self):
        """ResponseBlock (union discriminada) rejeita kind desconhecido."""
        from pydantic import TypeAdapter
        from app.shared.rrp_blocks import ResponseBlock

        ta = TypeAdapter(ResponseBlock)
        with pytest.raises((ValidationError, Exception)):
            ta.validate_python({"kind": "unknown_invented_kind", "block_id": "x"})

    def test_schema_extra_fields_forbidden_on_score_explainer(self):
        """extra='forbid' em ScoreExplainerBlock rejeita campo fantasma."""
        from app.shared.rrp_blocks import ScoreExplainerBlock

        with pytest.raises(ValidationError):
            ScoreExplainerBlock(
                block_id="x",
                subject_id="c",
                subject_label="C",
                score=50.0,
                ghost_field="boom",
            )

    def test_schema_extra_fields_forbidden_on_comparison_table(self):
        """extra='forbid' em ComparisonTableBlock rejeita campo fantasma."""
        from app.shared.rrp_blocks import ComparisonTableBlock

        with pytest.raises(ValidationError):
            ComparisonTableBlock(
                block_id="x",
                title="Test",
                ghost_column="boom",
            )

    def test_all_kinds_produce_valid_block_ids(self):
        """Blocos gerados pelo builder têm block_id no formato 'kind:...'."""
        from app.shared.rrp_ranking_builder import (
            build_candidate_ranking_blocks,
            build_candidate_card_block,
            build_pipeline_funnel_block,
            build_candidate_comparison_blocks,
        )

        # ranking com opinion
        blocks_ranking = build_candidate_ranking_blocks(
            job_id="job-ids", rows=[_row_with_opinion()]
        )
        for b in blocks_ranking:
            kind = b.get("kind", "")
            block_id = b.get("block_id", "")
            assert block_id.startswith(kind + ":"), (
                f"block_id '{block_id}' deve começar com '{kind}:'"
            )

        # funnel
        blocks_funnel = build_pipeline_funnel_block(
            title="Pipeline", stages={"triagem": 10, "entrevista": 5}, total=15
        )
        for b in blocks_funnel:
            kind = b.get("kind", "")
            block_id = b.get("block_id", "")
            assert block_id.startswith(kind + ":"), (
                f"funnel block_id '{block_id}' deve começar com '{kind}:'"
            )

        # candidate card (sem opinion = unverified)
        blocks_card = build_candidate_card_block(_row_without_opinion())
        for b in blocks_card:
            kind = b.get("kind", "")
            block_id = b.get("block_id", "")
            assert block_id.startswith(kind + ":"), (
                f"card block_id '{block_id}' deve começar com '{kind}:'"
            )

    def test_response_block_discriminator_roundtrip(self):
        """Blocos emitidos pelo builder são deserializáveis como ResponseBlock."""
        from pydantic import TypeAdapter
        from app.shared.rrp_ranking_builder import build_candidate_ranking_blocks
        from app.shared.rrp_blocks import ResponseBlock

        ta = TypeAdapter(ResponseBlock)
        rows = [_row_without_opinion(), _row_with_opinion()]
        blocks = build_candidate_ranking_blocks(job_id="job-rt", rows=rows)

        for raw in blocks:
            # não deve levantar exceção — todos os kinds emitidos são válidos
            parsed = ta.validate_python(raw)
            assert parsed.kind == raw["kind"]
