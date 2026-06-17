"""Contract sensor — proveniência honesta dos blocos do Rich Response Protocol.

CLAUDE.md ("Proveniência honesta em saídas de IA"): todo score/evidência exibido
com atribuição de fonte DEVE ter fonte verificável. Sem retrieval real →
unverified=True + confidence='low' + rótulo explícito; NUNCA citar fonte real
para número derivado só do LLM.

Se este teste falhar:
  → Um score_explainer/evidence_stack está sendo construído com evidence_refs que
    não resolvem a registros reais escopados por JWT (proveniência fabricada), ou
    um bloco unverified não foi rotulado (confidence!='low' / sem provenance_note /
    citando fontes). Corrija a montagem do bloco no produtor (render-tool), nunca
    afrouxe o gate. Ver app/shared/rrp_blocks.py::verify_block_provenance.
"""
import pytest

from app.shared.rrp_blocks import (
    EvidenceItem,
    EvidenceStackBlock,
    ScoreExplainerBlock,
    ScoreFactor,
    verify_block_provenance,
)

# Resolver fake: só estes ref_ids "existem" (simula registros reais buscados).
_REAL_REFS = {"cand:42:linkedin", "cand:42:resume", "cand:42:assessment"}


def _resolver(ref_id: str) -> bool:
    return ref_id in _REAL_REFS


def test_score_with_resolvable_evidence_passes():
    block = ScoreExplainerBlock(
        block_id="score_explainer:present_scored_comparison:cand:42",
        subject_id="cand:42",
        subject_label="Maria Silva",
        score=87.0,
        confidence="high",
        confidence_basis="LinkedIn + currículo + assessment",
        factors=[
            ScoreFactor(
                label="Stack técnico",
                weight=0.4,
                contribution="+",
                detail="Python 5 anos",
                evidence_refs=["cand:42:linkedin", "cand:42:resume"],
            ),
        ],
        summary="Match 87% · por quê?",
    )
    assert verify_block_provenance(block, _resolver) == []


def test_score_with_fabricated_evidence_ref_is_flagged():
    block = ScoreExplainerBlock(
        block_id="score_explainer:present_scored_comparison:cand:99",
        subject_id="cand:99",
        subject_label="Fulano",
        score=80.0,
        confidence="high",
        factors=[
            ScoreFactor(
                label="Stack",
                weight=0.5,
                contribution="+",
                evidence_refs=["cand:99:inventado"],  # não resolve
            ),
        ],
    )
    violations = verify_block_provenance(block, _resolver)
    assert violations, "ref fabricado deveria ser flagado"
    assert "não resolve" in violations[0]


def test_unverified_score_must_be_low_confidence():
    block = ScoreExplainerBlock(
        block_id="score_explainer:x:cand:1",
        subject_id="cand:1",
        subject_label="X",
        score=70.0,
        confidence="medium",  # ← unverified exige 'low'
        unverified=True,
        provenance_note="estimativa do LLM sem busca",
    )
    violations = verify_block_provenance(block, _resolver)
    assert any("confidence" in v for v in violations)


def test_unverified_score_requires_provenance_note():
    block = ScoreExplainerBlock(
        block_id="score_explainer:x:cand:2",
        subject_id="cand:2",
        subject_label="Y",
        score=65.0,
        confidence="low",
        unverified=True,
        provenance_note="",  # ← faltando rótulo
    )
    violations = verify_block_provenance(block, _resolver)
    assert any("provenance_note" in v for v in violations)


def test_unverified_score_cannot_cite_sources():
    """Núcleo do invariante salarial: estimativa do LLM não pode citar fonte real."""
    block = ScoreExplainerBlock(
        block_id="score_explainer:x:cand:3",
        subject_id="cand:3",
        subject_label="Z",
        score=60.0,
        confidence="low",
        unverified=True,
        provenance_note="estimativa sem busca",
        factors=[
            ScoreFactor(
                label="Reputação",
                weight=0.3,
                contribution="+",
                evidence_refs=["cand:42:linkedin"],  # cita fonte sendo unverified
            ),
        ],
    )
    violations = verify_block_provenance(block, _resolver)
    assert any("fabricada" in v for v in violations)


def test_evidence_stack_with_dead_ref_is_flagged():
    block = EvidenceStackBlock(
        block_id="evidence_stack:present_scored_comparison:cand:7",
        items=[
            EvidenceItem(
                source_type="linkedin",
                ref_id="cand:7:ghost",  # não resolve
                label="Perfil LinkedIn",
            ),
        ],
        count=1,
    )
    violations = verify_block_provenance(block, _resolver)
    assert violations and "não resolve" in violations[0]


def test_clean_evidence_stack_passes():
    block = EvidenceStackBlock(
        block_id="evidence_stack:present_scored_comparison:cand:42",
        items=[
            EvidenceItem(
                source_type="resume",
                ref_id="cand:42:resume",
                label="Currículo enviado",
            ),
        ],
        count=1,
    )
    assert verify_block_provenance(block, _resolver) == []


def test_extra_field_forbidden():
    """REGRA 1 pydantic — schemas de bloco recusam fields fantasma."""
    with pytest.raises(Exception):
        ScoreExplainerBlock(
            block_id="x",
            subject_id="c",
            subject_label="C",
            score=50.0,
            ghost_field="boom",  # extra='forbid'
        )
