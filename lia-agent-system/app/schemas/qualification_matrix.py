"""
Schemas canônicos da matriz de qualificação do candidato (avaliação por critério,
estilo LinkedIn must-have/preferred).

Usados por:
- `criteria_derivation` (produtor puro: deriva + avalia critérios)
- `CandidateReportService.generate_parecer` (emite `qualification_matrix`)
- endpoints de parecer / criteria-match (Fase 2) e o frontend (Fase 3)

Regras de honestidade (CLAUDE.md REGRA 4 + proveniência honesta):
- `status='partial'` SEMPRE implica `is_inference=True` (o 🟡 "provável mas não
  explícito" do LinkedIn) — validado pelo model_validator.
- `provenance='none'` SEMPRE implica `status='unknown'` — nunca afirmar
  met/not_met sem fonte. Critério sem evidência fica `unknown`, nunca fabricado.
"""
from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from app.shared.types import WeDoBaseModel

CriterionGroup = Literal["must_have", "preferred", "criteria"]
CriterionStatus = Literal["met", "partial", "not_met", "unknown"]
CriterionProvenance = Literal[
    "resume", "profile", "screening", "wsi", "eligibility", "none"
]
MatrixMode = Literal["grouped", "flat"]


class QualificationCriterion(WeDoBaseModel):
    """Um critério avaliado contra o candidato, com proveniência declarada."""

    id: str
    label: str
    group: CriterionGroup
    status: CriterionStatus
    explanation: str = ""
    provenance: CriterionProvenance = "none"
    is_inference: bool = False
    confidence: float = 0.0
    source_ref: str | None = None

    @model_validator(mode="after")
    def _enforce_honesty_invariants(self) -> "QualificationCriterion":
        # partial == inferência (LinkedIn 🟡). Reforçado em código, não confiado ao LLM.
        if self.status == "partial":
            object.__setattr__(self, "is_inference", True)
        # Sem fonte → não pode afirmar atende/não-atende.
        if self.provenance == "none" and self.status in ("met", "not_met", "partial"):
            object.__setattr__(self, "status", "unknown")
        return self


class QualificationMatrix(WeDoBaseModel):
    """
    Conjunto de critérios avaliados + sumário de fit.

    mode='grouped' (vaga): renderizar agrupando por `group` (must_have/preferred).
    mode='flat' (busca): lista única; todos os critérios usam group='criteria'.
    """

    mode: MatrixMode
    criteria: list[QualificationCriterion] = []
    met_count: int = 0
    total_count: int = 0
    must_have_met: int = 0
    must_have_total: int = 0
    overall_label: str = ""
    generated_with_llm: bool = False
    degraded: bool = False
    degraded_reason: str | None = None

    @classmethod
    def build(
        cls,
        *,
        mode: MatrixMode,
        criteria: list[QualificationCriterion],
        generated_with_llm: bool = False,
        degraded: bool = False,
        degraded_reason: str | None = None,
    ) -> "QualificationMatrix":
        """Constrói a matriz computando os contadores de forma consistente."""
        met = sum(1 for c in criteria if c.status == "met")
        total = len(criteria)
        mh = [c for c in criteria if c.group == "must_have"]
        mh_met = sum(1 for c in mh if c.status == "met")
        if mode == "grouped":
            label = f"Atende {met}/{total} qualificações"
        else:
            label = f"Atende {met}/{total} critérios"
        return cls(
            mode=mode,
            criteria=criteria,
            met_count=met,
            total_count=total,
            must_have_met=mh_met,
            must_have_total=len(mh),
            overall_label=label,
            generated_with_llm=generated_with_llm,
            degraded=degraded,
            degraded_reason=degraded_reason,
        )
