"""Contract sensor — moat (score_explainer + evidence_stack) na superficie de ranking.

Pina que a SHAPE emitida por sourcing_actions._rank_candidates (lendo LiaOpinion
persistido) passa no gate de proveniencia: score real + fatores de strengths/concerns
(qualitativos, weight=0, sem evidence_refs) + evidence_stack com refs internos reais
(opinion:/wsi:). Honesto: zero fabricacao.

Se falhar: a montagem do bloco no _rank_candidates deixou de respeitar proveniencia
(ex: marcou unverified sem rotulo, ou citou evidence_ref que nao resolve). Conserte
o produtor (sourcing_actions), nunca afrouxe o gate.
"""
from app.shared.rrp_blocks import (
    EvidenceItem,
    EvidenceStackBlock,
    ScoreExplainerBlock,
    ScoreFactor,
    verify_block_provenance,
)

# resolver simula registros reais (opinion + wsi persistidos)
_REAL = {"opinion:op-1", "wsi:wsi-1"}


def _resolver(ref_id: str) -> bool:
    return ref_id in _REAL


def test_score_explainer_from_strengths_concerns_passes():
    block = ScoreExplainerBlock(
        block_id="score_explainer:rank:cand-1",
        role="evidence",
        subject_id="cand-1",
        subject_label="Ana Souza",
        score=88.0,
        score_label="Score LIA",
        confidence="high",
        confidence_basis="Recomendado",
        factors=[
            ScoreFactor(label="5 anos em Python", weight=0.0, contribution="+"),
            ScoreFactor(label="Sem experiencia em K8s", weight=0.0, contribution="-"),
        ],
        summary="Forte fit tecnico, gap pontual.",
        unverified=False,
    )
    # fatores qualitativos sem evidence_refs -> gate nao tem o que recusar
    assert verify_block_provenance(block, _resolver) == []


def test_evidence_stack_internal_refs_resolve():
    block = EvidenceStackBlock(
        block_id="evidence_stack:rank:cand-1",
        role="evidence",
        items=[
            EvidenceItem(source_type="internal_record", ref_id="opinion:op-1",
                         label="Parecer LIA"),
            EvidenceItem(source_type="assessment", ref_id="wsi:wsi-1",
                         label="Entrevista WSI"),
        ],
        count=2,
    )
    assert verify_block_provenance(block, _resolver) == []


def test_evidence_stack_unresolved_ref_flagged():
    block = EvidenceStackBlock(
        block_id="evidence_stack:rank:cand-2",
        role="evidence",
        items=[
            EvidenceItem(source_type="internal_record", ref_id="opinion:ghost",
                         label="Parecer LIA"),
        ],
        count=1,
    )
    violations = verify_block_provenance(block, _resolver)
    assert violations and "não resolve" in violations[0]
