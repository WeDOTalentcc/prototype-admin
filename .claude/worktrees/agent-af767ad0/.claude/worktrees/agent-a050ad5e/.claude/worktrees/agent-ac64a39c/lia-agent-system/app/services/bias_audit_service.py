"""
Bias Audit Service — E.2

Calcula adverse impact real (dados de RubricEvaluation + Candidate) por vaga,
retornando apenas estatísticas agregadas sem PII (LGPD-safe).

Dimensões auditadas:
  - gender: masculino, feminino, outro/não informado
  - age_group: <30, 30-44, 45+
  - disability: com PCD, sem PCD
  - region: por location_state

Referências:
- dei-fairness §4 (Four-Fifths Rule — adverse_impact_ratio >= 0.80)
- LGPD Art. 5 (dados pessoais / dado sensível)
- EU AI Act Art. 10 (dados de treino e auditoria)
- SOX / ISO 27001: evidência de fairness com dados reais
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.rubric import RubricEvaluation
from app.models.candidate import Candidate
from app.models.bias_audit_snapshot import BiasAuditSnapshot

logger = logging.getLogger(__name__)

# Alinhado com golden dataset (tests/fixtures/golden_dataset.py)
APPROVAL_THRESHOLD = 60.0
FOUR_FIFTHS_THRESHOLD = 0.80

# Faixas etárias (screening-compliance §4)
AGE_GROUP_YOUNG = "<30"
AGE_GROUP_MID = "30-44"
AGE_GROUP_SENIOR = "45+"

NOT_INFORMED = "não informado"


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

@dataclass
class DemographicAuditResult:
    """Resultado de adverse impact para uma dimensão demográfica."""
    dimension: str                         # "gender" | "age_group" | "disability" | "region"
    groups: Dict[str, Dict]                # {label: {"count": N, "approved": N, "rate": float}}
    adverse_impact_ratio: float            # menor_taxa / maior_taxa (Four-Fifths Rule)
    below_threshold: bool                  # ratio < FOUR_FIFTHS_THRESHOLD
    alert_level: str                       # "ok" | "warning"


@dataclass
class BiasAuditReport:
    """Relatório completo de auditoria de viés para uma vaga."""
    job_id: str
    evaluated_at: datetime
    total_candidates: int
    dimensions: List[DemographicAuditResult] = field(default_factory=list)
    has_alerts: bool = False


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def _age_group(dob: Optional[date]) -> str:
    """Classifica data de nascimento em faixa etária."""
    if dob is None:
        return NOT_INFORMED
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 30:
        return AGE_GROUP_YOUNG
    if age < 45:
        return AGE_GROUP_MID
    return AGE_GROUP_SENIOR


def _adverse_impact_ratio(groups: Dict[str, Dict]) -> float:
    """
    Calcula o adverse impact ratio: menor_taxa / maior_taxa.

    Considera todos os grupos com pelo menos 1 candidato (count > 0).
    Se todos os grupos tiverem rate=0 ou houver apenas 1 grupo com candidatos, retorna 1.0.

    Four-Fifths Rule: se o grupo com menor taxa tiver rate=0 e algum grupo tiver rate>0,
    o ratio é 0.0 — claramente abaixo do limiar de 0.80.
    """
    rates = [v["rate"] for v in groups.values() if v["count"] > 0]
    if len(rates) < 2:
        return 1.0
    max_rate = max(rates)
    if max_rate == 0.0:
        return 1.0  # todos com taxa zero — sem adverse impact calculável
    return round(min(rates) / max_rate, 4)


def _audit_dimension(
    records: list[tuple[RubricEvaluation, Candidate]],
    dimension: str,
    key_fn,
) -> DemographicAuditResult:
    """
    Computa contagens e taxas de aprovação por grupo dentro de uma dimensão.

    Args:
        records: pares (avaliação, candidato) da vaga
        dimension: nome da dimensão (para o relatório)
        key_fn: função que extrai o rótulo do grupo a partir do Candidate
    """
    groups: Dict[str, Dict] = {}

    for evaluation, candidate in records:
        label = key_fn(candidate) or NOT_INFORMED
        if label not in groups:
            groups[label] = {"count": 0, "approved": 0, "rate": 0.0}
        groups[label]["count"] += 1
        if evaluation.score is not None and evaluation.score >= APPROVAL_THRESHOLD:
            groups[label]["approved"] += 1

    for stats in groups.values():
        stats["rate"] = round(
            stats["approved"] / stats["count"] if stats["count"] > 0 else 0.0, 4
        )

    ratio = _adverse_impact_ratio(groups)
    below = ratio < FOUR_FIFTHS_THRESHOLD

    return DemographicAuditResult(
        dimension=dimension,
        groups=groups,
        adverse_impact_ratio=ratio,
        below_threshold=below,
        alert_level="warning" if below else "ok",
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class BiasAuditService:
    """
    Auditoria de adverse impact por vaga usando dados reais de avaliação.

    Retorna apenas contagens agregadas — sem IDs individuais de candidatos (LGPD-safe).
    """

    async def get_adverse_impact_by_job(
        self,
        db: AsyncSession,
        job_id: UUID,
        company_id: Optional[UUID] = None,
    ) -> BiasAuditReport:
        """
        Consulta RubricEvaluation JOIN Candidate para a vaga e calcula adverse impact
        nas 4 dimensões: gênero, faixa etária, PCD, região.

        Args:
            db: AsyncSession de banco de dados.
            job_id: UUID da vaga (job_vacancy_id).

        Returns:
            BiasAuditReport com stats agregadas (sem PII).
        """
        result = await db.execute(
            select(RubricEvaluation, Candidate)
            .join(Candidate, RubricEvaluation.candidate_id == Candidate.id)
            .where(RubricEvaluation.job_vacancy_id == job_id)
        )
        rows = result.all()
        records = [(row[0], row[1]) for row in rows]

        dimensions: List[DemographicAuditResult] = []

        if records:
            # Dimensão 1: Gênero
            dimensions.append(_audit_dimension(
                records, "gender",
                lambda c: (c.gender or NOT_INFORMED).lower()
            ))

            # Dimensão 2: Faixa etária
            dimensions.append(_audit_dimension(
                records, "age_group",
                lambda c: _age_group(c.date_of_birth)
            ))

            # Dimensão 3: PCD
            dimensions.append(_audit_dimension(
                records, "disability",
                lambda c: "pcd" if c.diversity_disability else "sem pcd"
            ))

            # Dimensão 4: Região (estado)
            dimensions.append(_audit_dimension(
                records, "region",
                lambda c: (c.location_state or NOT_INFORMED).upper()
            ))

        has_alerts = any(d.below_threshold for d in dimensions)

        report = BiasAuditReport(
            job_id=str(job_id),
            evaluated_at=datetime.utcnow(),
            total_candidates=len(records),
            dimensions=dimensions,
            has_alerts=has_alerts,
        )

        # Persiste snapshot para rastreabilidade histórica (SOX/ISO 27001)
        if company_id is not None:
            try:
                await self.save_snapshot(db, company_id, report)
            except Exception as exc:
                logger.warning("Falha ao salvar snapshot de bias audit: %s", exc)

        return report

    async def save_snapshot(
        self,
        db: AsyncSession,
        company_id: UUID,
        report: BiasAuditReport,
    ) -> None:
        """
        Persiste um snapshot de auditoria de viés no banco de dados.

        Apenas dados agregados — sem PII (LGPD-safe).
        Exigido por SOX / ISO 27001 para rastreabilidade histórica.
        """
        dimensions_data = [
            {
                "dimension": d.dimension,
                "groups": d.groups,
                "adverse_impact_ratio": d.adverse_impact_ratio,
                "below_threshold": d.below_threshold,
                "alert_level": d.alert_level,
            }
            for d in report.dimensions
        ]
        snapshot = BiasAuditSnapshot(
            company_id=company_id,
            job_id=report.job_id,
            evaluated_at=report.evaluated_at,
            total_candidates=report.total_candidates,
            has_alerts=report.has_alerts,
            dimensions_json=json.dumps(dimensions_data),
        )
        db.add(snapshot)
        await db.flush()

    async def get_snapshot_history(
        self,
        db: AsyncSession,
        company_id: UUID,
        job_id: str,
        limit: int = 10,
    ) -> list[BiasAuditSnapshot]:
        """
        Retorna histórico de snapshots para uma vaga, ordenado por data decrescente.

        Isolamento multi-tenant: filtra por company_id.
        """
        result = await db.execute(
            select(BiasAuditSnapshot)
            .where(
                BiasAuditSnapshot.company_id == company_id,
                BiasAuditSnapshot.job_id == job_id,
            )
            .order_by(BiasAuditSnapshot.evaluated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


bias_audit_service = BiasAuditService()
