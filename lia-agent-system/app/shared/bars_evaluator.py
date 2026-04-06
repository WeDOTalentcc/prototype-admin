# LIA-P04 — BARS genérico para avaliação de competências
# Behaviorally Anchored Rating Scale (BARS) — IEEE 7003 / SHRM best practice
# Referência: Eightfold AI, Findem e HireEZ usam BARS para avaliar candidatos
# de forma objetiva, reduzindo viés subjetivo em decisões de recrutamento.
# LGPD Art. 20: avaliações BARS devem ser documentadas para direito de explicação.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC
from enum import IntEnum


class BARSLevel(IntEnum):
    """Rating levels for BARS evaluation (1-5 scale)."""
    UNSATISFACTORY = 1
    BELOW_EXPECTATIONS = 2
    MEETS_EXPECTATIONS = 3
    EXCEEDS_EXPECTATIONS = 4
    OUTSTANDING = 5


@dataclass
class BARSAnchor:
    """A behavioral anchor describing observable behavior at a specific BARS level."""
    level: BARSLevel
    description: str
    examples: list[str] = field(default_factory=list)


@dataclass
class BARSCriteria:
    """A single evaluation criterion with behavioral anchors for each level."""
    criteria_id: str
    name: str
    description: str
    weight: float = 1.0  # relative weight in final score
    anchors: list[BARSAnchor] = field(default_factory=list)

    def get_anchor(self, level: BARSLevel) -> BARSAnchor | None:
        return next((a for a in self.anchors if a.level == level), None)

    def get_description_for_level(self, level: BARSLevel) -> str:
        anchor = self.get_anchor(level)
        return anchor.description if anchor else f"Level {level.value}"


@dataclass
class BARSEvaluation:
    """Result of evaluating a candidate against a BARS rubric."""
    candidate_id: str
    rubric_id: str
    scores: dict[str, int]  # criteria_id -> BARSLevel value
    justifications: dict[str, str] = field(default_factory=dict)  # criteria_id -> reasoning
    overall_score: float = 0.0
    recommendation: str = ""
    evaluated_at: str = ""
    evaluator: str = "LIA"

    @classmethod
    def compute_overall(
        cls,
        scores: dict[str, int],
        criteria: list[BARSCriteria],
    ) -> float:
        """Compute weighted average score."""
        total_weight = sum(c.weight for c in criteria if c.criteria_id in scores)
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(
            scores[c.criteria_id] * c.weight
            for c in criteria
            if c.criteria_id in scores
        )
        return round(weighted_sum / total_weight, 2)


@dataclass
class BARSRubric:
    """Complete evaluation rubric with multiple criteria."""
    rubric_id: str
    name: str
    domain: str  # which domain this rubric is for
    criteria: list[BARSCriteria] = field(default_factory=list)
    pass_threshold: float = 3.0  # minimum overall score to pass
    description: str = ""

    def add_criteria(self, criteria: BARSCriteria) -> None:
        self.criteria.append(criteria)

    def evaluate(
        self,
        candidate_id: str,
        scores: dict[str, int],
        justifications: dict[str, str] | None = None,
    ) -> BARSEvaluation:
        """Create a BARSEvaluation from raw scores."""
        from datetime import datetime

        overall = BARSEvaluation.compute_overall(scores, self.criteria)
        recommendation = "advance" if overall >= self.pass_threshold else "review"
        if overall >= 4.5:
            recommendation = "strong_advance"
        elif overall < 2.0:
            recommendation = "reject"

        return BARSEvaluation(
            candidate_id=candidate_id,
            rubric_id=self.rubric_id,
            scores=scores,
            justifications=justifications or {},
            overall_score=overall,
            recommendation=recommendation,
            evaluated_at=datetime.now(UTC).isoformat(),
        )

    def get_explanation(self, evaluation: BARSEvaluation) -> str:
        """LGPD Art. 20 — generate human-readable explanation of evaluation."""
        lines = [
            f"Avaliação BARS — {self.name}",
            f"Candidato: {evaluation.candidate_id}",
            f"Score geral: {evaluation.overall_score:.1f}/5.0",
            f"Recomendação: {evaluation.recommendation}",
            "",
            "Critérios avaliados:",
        ]
        for c in self.criteria:
            if c.criteria_id in evaluation.scores:
                level = BARSLevel(evaluation.scores[c.criteria_id])
                anchor_desc = c.get_description_for_level(level)
                justification = evaluation.justifications.get(c.criteria_id, "")
                lines.append(f"  • {c.name} ({c.weight:.0%} peso): {level.name} — {anchor_desc}")
                if justification:
                    lines.append(f"    Justificativa: {justification}")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Pre-built rubrics for common domains
# ------------------------------------------------------------------

def build_cv_screening_rubric() -> BARSRubric:
    """Standard BARS rubric for CV screening evaluation."""
    rubric = BARSRubric(
        rubric_id="cv_screening_v1",
        name="Triagem de CV — Rubrica Padrão",
        domain="cv_screening",
        pass_threshold=3.0,
    )

    # Criteria 1: Technical Skills
    technical = BARSCriteria(
        criteria_id="technical_skills",
        name="Competências Técnicas",
        description="Nível de domínio das skills técnicas requeridas",
        weight=0.35,
        anchors=[
            BARSAnchor(BARSLevel.UNSATISFACTORY, "Nenhuma skill técnica relevante encontrada"),
            BARSAnchor(BARSLevel.BELOW_EXPECTATIONS, "Skills técnicas básicas; gaps significativos"),
            BARSAnchor(BARSLevel.MEETS_EXPECTATIONS, "Skills técnicas adequadas para o cargo"),
            BARSAnchor(BARSLevel.EXCEEDS_EXPECTATIONS, "Skills avançadas com experiência comprovada"),
            BARSAnchor(BARSLevel.OUTSTANDING, "Expert reconhecido; contribuições notáveis na área"),
        ],
    )
    rubric.add_criteria(technical)

    # Criteria 2: Experience
    experience = BARSCriteria(
        criteria_id="experience",
        name="Experiência Relevante",
        description="Alinhamento da experiência anterior com os requisitos da vaga",
        weight=0.30,
        anchors=[
            BARSAnchor(BARSLevel.UNSATISFACTORY, "Sem experiência relevante"),
            BARSAnchor(BARSLevel.BELOW_EXPECTATIONS, "Experiência parcialmente relevante (<50%)"),
            BARSAnchor(BARSLevel.MEETS_EXPECTATIONS, "Experiência relevante suficiente para a vaga"),
            BARSAnchor(BARSLevel.EXCEEDS_EXPECTATIONS, "Experiência superior ao requerido"),
            BARSAnchor(BARSLevel.OUTSTANDING, "Histórico excepcional com resultados mensuráveis"),
        ],
    )
    rubric.add_criteria(experience)

    # Criteria 3: Education
    education = BARSCriteria(
        criteria_id="education",
        name="Formação Acadêmica",
        description="Nível e relevância da formação acadêmica",
        weight=0.15,
        anchors=[
            BARSAnchor(BARSLevel.UNSATISFACTORY, "Formação não atende requisito mínimo"),
            BARSAnchor(BARSLevel.BELOW_EXPECTATIONS, "Formação parcialmente adequada"),
            BARSAnchor(BARSLevel.MEETS_EXPECTATIONS, "Formação adequada conforme requisitos"),
            BARSAnchor(BARSLevel.EXCEEDS_EXPECTATIONS, "Formação superior ao requerido"),
            BARSAnchor(BARSLevel.OUTSTANDING, "Pós-graduação/doutorado em área altamente relevante"),
        ],
    )
    rubric.add_criteria(education)

    # Criteria 4: Cultural Fit Indicators
    cultural = BARSCriteria(
        criteria_id="cultural_indicators",
        name="Indicadores de Fit Cultural",
        description="Sinais de alinhamento com valores e cultura organizacional",
        weight=0.20,
        anchors=[
            BARSAnchor(BARSLevel.UNSATISFACTORY, "Nenhum indicador de fit cultural"),
            BARSAnchor(BARSLevel.BELOW_EXPECTATIONS, "Poucos indicadores; possível desalinhamento"),
            BARSAnchor(BARSLevel.MEETS_EXPECTATIONS, "Indicadores adequados de fit cultural"),
            BARSAnchor(BARSLevel.EXCEEDS_EXPECTATIONS, "Forte alinhamento com valores da empresa"),
            BARSAnchor(BARSLevel.OUTSTANDING, "Candidato representa valores culturais excepcionalmente"),
        ],
    )
    rubric.add_criteria(cultural)

    return rubric


def build_interview_rubric() -> BARSRubric:
    """Standard BARS rubric for interview evaluation."""
    rubric = BARSRubric(
        rubric_id="interview_eval_v1",
        name="Avaliação de Entrevista — Rubrica Padrão",
        domain="interview_scheduling",
        pass_threshold=3.0,
    )

    criteria_list = [
        BARSCriteria(
            criteria_id="communication",
            name="Comunicação",
            description="Clareza, objetividade e assertividade na comunicação",
            weight=0.25,
            anchors=[
                BARSAnchor(BARSLevel.UNSATISFACTORY, "Comunicação muito difícil de compreender"),
                BARSAnchor(BARSLevel.BELOW_EXPECTATIONS, "Comunicação frequentemente confusa"),
                BARSAnchor(BARSLevel.MEETS_EXPECTATIONS, "Comunicação clara e adequada"),
                BARSAnchor(BARSLevel.EXCEEDS_EXPECTATIONS, "Comunicação clara, estruturada e persuasiva"),
                BARSAnchor(BARSLevel.OUTSTANDING, "Comunicador excepcional, inspira e convence"),
            ],
        ),
        BARSCriteria(
            criteria_id="problem_solving",
            name="Resolução de Problemas",
            description="Capacidade analítica e abordagem a problemas complexos",
            weight=0.35,
            anchors=[
                BARSAnchor(BARSLevel.UNSATISFACTORY, "Não conseguiu abordar o problema proposto"),
                BARSAnchor(BARSLevel.BELOW_EXPECTATIONS, "Abordagem superficial; soluções incompletas"),
                BARSAnchor(BARSLevel.MEETS_EXPECTATIONS, "Resolução adequada com lógica consistente"),
                BARSAnchor(BARSLevel.EXCEEDS_EXPECTATIONS, "Soluções criativas e bem fundamentadas"),
                BARSAnchor(BARSLevel.OUTSTANDING, "Insights únicos; abordagem inovadora e impactante"),
            ],
        ),
        BARSCriteria(
            criteria_id="cultural_fit",
            name="Fit Cultural",
            description="Alinhamento comportamental com valores da organização",
            weight=0.20,
            anchors=[
                BARSAnchor(BARSLevel.UNSATISFACTORY, "Claro desalinhamento com valores organizacionais"),
                BARSAnchor(BARSLevel.BELOW_EXPECTATIONS, "Alguns conflitos de valores identificados"),
                BARSAnchor(BARSLevel.MEETS_EXPECTATIONS, "Boa aderência aos valores organizacionais"),
                BARSAnchor(BARSLevel.EXCEEDS_EXPECTATIONS, "Forte identificação com missão e valores"),
                BARSAnchor(BARSLevel.OUTSTANDING, "Embaixador natural da cultura organizacional"),
            ],
        ),
        BARSCriteria(
            criteria_id="motivation",
            name="Motivação e Engajamento",
            description="Nível de interesse e engajamento com a oportunidade",
            weight=0.20,
            anchors=[
                BARSAnchor(BARSLevel.UNSATISFACTORY, "Claramente desinteressado ou passivo"),
                BARSAnchor(BARSLevel.BELOW_EXPECTATIONS, "Motivação baixa ou genérica"),
                BARSAnchor(BARSLevel.MEETS_EXPECTATIONS, "Interesse genuíno pela posição"),
                BARSAnchor(BARSLevel.EXCEEDS_EXPECTATIONS, "Alta motivação com razões específicas e sólidas"),
                BARSAnchor(BARSLevel.OUTSTANDING, "Paixão evidente; candidato claramente quer esta posição"),
            ],
        ),
    ]
    for c in criteria_list:
        rubric.add_criteria(c)

    return rubric


def build_sourcing_rubric() -> BARSRubric:
    """BARS rubric for evaluating sourced candidates."""
    rubric = BARSRubric(
        rubric_id="sourcing_eval_v1",
        name="Avaliação de Sourcing — Rubrica Padrão",
        domain="sourcing",
        pass_threshold=3.0,
    )

    for name, cid, weight, desc in [
        ("Relevância do Perfil", "profile_relevance", 0.40, "Aderência do perfil à vaga"),
        ("Disponibilidade", "availability", 0.20, "Sinais de disponibilidade para mudança"),
        ("Potencial de Contato", "contact_potential", 0.20, "Probabilidade de resposta positiva"),
        ("Fit Salarial", "salary_fit", 0.20, "Alinhamento salarial estimado"),
    ]:
        rubric.add_criteria(BARSCriteria(
            criteria_id=cid,
            name=name,
            description=desc,
            weight=weight,
            anchors=[
                BARSAnchor(BARSLevel.UNSATISFACTORY, f"{name}: completamente inadequado"),
                BARSAnchor(BARSLevel.BELOW_EXPECTATIONS, f"{name}: parcialmente adequado"),
                BARSAnchor(BARSLevel.MEETS_EXPECTATIONS, f"{name}: adequado"),
                BARSAnchor(BARSLevel.EXCEEDS_EXPECTATIONS, f"{name}: acima do esperado"),
                BARSAnchor(BARSLevel.OUTSTANDING, f"{name}: excepcional"),
            ],
        ))

    return rubric


# Registry of pre-built rubrics
_RUBRIC_REGISTRY: dict[str, BARSRubric] = {}


def register_rubric(rubric: BARSRubric) -> None:
    """Register a rubric globally."""
    _RUBRIC_REGISTRY[rubric.rubric_id] = rubric


def get_rubric(rubric_id: str) -> BARSRubric | None:
    """Get a registered rubric by ID."""
    return _RUBRIC_REGISTRY.get(rubric_id)


def get_rubric_for_domain(domain: str) -> BARSRubric | None:
    """Get the default rubric for a domain."""
    return next(
        (r for r in _RUBRIC_REGISTRY.values() if r.domain == domain),
        None,
    )


# Auto-register pre-built rubrics
register_rubric(build_cv_screening_rubric())
register_rubric(build_interview_rubric())
register_rubric(build_sourcing_rubric())
