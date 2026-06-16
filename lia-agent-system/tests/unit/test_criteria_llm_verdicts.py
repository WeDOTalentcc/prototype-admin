"""
Sensor do passo LLM de resíduo (apply_llm_verdicts) — função PURA.

Pina:
- só critérios status='unknown' são atualizados (deterministicos preservados)
- honestidade reforçada pelo schema: 'met' sem fonte ⇒ unknown; 'partial' ⇒ is_inference
- generated_with_llm=True após aplicar
"""
from app.domains.analytics.services.criteria_derivation import apply_llm_verdicts
from app.schemas.qualification_matrix import QualificationCriterion, QualificationMatrix


def _matrix():
    crits = [
        QualificationCriterion(id="tech:python", label="Python", group="must_have",
                               status="met", provenance="resume", confidence=1.0),
        QualificationCriterion(id="behav:lid", label="Liderança", group="must_have",
                               status="unknown", provenance="none"),
        QualificationCriterion(id="req:viagem", label="Disponível p/ viagens", group="must_have",
                               status="unknown", provenance="none"),
    ]
    return QualificationMatrix.build(mode="grouped", criteria=crits)


def test_only_unknowns_updated_deterministic_preserved():
    m = _matrix()
    verdicts = {
        "tech:python": {"status": "not_met", "provenance": "resume"},  # deve ser IGNORADO (já met)
        "behav:lid": {"status": "partial", "explanation": "inferido de cargos de gestão",
                      "provenance": "resume", "confidence": 0.6},
    }
    out = apply_llm_verdicts(m, verdicts)
    py = next(c for c in out.criteria if c.id == "tech:python")
    lid = next(c for c in out.criteria if c.id == "behav:lid")
    assert py.status == "met"  # determinístico preservado
    assert lid.status == "partial"
    assert lid.is_inference is True  # honestidade reforçada
    assert out.generated_with_llm is True


def test_fabricated_met_without_source_downgraded_to_unknown():
    m = _matrix()
    verdicts = {"req:viagem": {"status": "met", "provenance": "none"}}  # fabricado
    out = apply_llm_verdicts(m, verdicts)
    req = next(c for c in out.criteria if c.id == "req:viagem")
    assert req.status == "unknown"  # rebaixado pelo validator


def test_unknown_without_verdict_stays_unknown():
    m = _matrix()
    out = apply_llm_verdicts(m, {})
    assert all(c.status == "unknown" for c in out.criteria if c.id.startswith(("behav", "req")))
