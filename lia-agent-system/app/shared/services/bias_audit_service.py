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

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "bias_audit_service is deprecated and will be removed once Rails adapter routes are complete. "
    "Migrate callers to rails_adapter equivalents. "
    "See UC-P1-22 in the remediation plan (CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md).",
    DeprecationWarning,
    stacklevel=2,
)

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID

try:
    from scipy.stats import chi2 as _chi2_dist
    from scipy.stats import chi2_contingency as _chi2_contingency
    _SCIPY_AVAILABLE = True
except ImportError:
    _SCIPY_AVAILABLE = False

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.bias_audit_snapshot import BiasAuditSnapshot
from lia_models.candidate import Candidate
from lia_models.rubric import RubricEvaluation

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
    groups: dict[str, dict]                # {label: {"count": N, "approved": N, "rate": float}}
    adverse_impact_ratio: float            # menor_taxa / maior_taxa (Four-Fifths Rule)
    below_threshold: bool                  # ratio < FOUR_FIFTHS_THRESHOLD
    alert_level: str                       # "ok" | "warning"
    disparate_impact: dict = field(default_factory=dict)  # {"chi2": float, "p_value": float, "significant": bool}
    eeoc_compliant: bool = True            # Four-Fifths ok AND não significativo estatisticamente


@dataclass
class BiasAuditReport:
    """Relatório completo de auditoria de viés para uma vaga."""
    job_id: str
    evaluated_at: datetime
    total_candidates: int
    dimensions: list[DemographicAuditResult] = field(default_factory=list)
    has_alerts: bool = False


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def _age_group(dob: date | None) -> str:
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


def _chi_square_fallback(table: list) -> tuple:
    """
    Chi-square de Pearson para tabela de contingência (Python puro, sem scipy).
    Retorna (chi2, p_value) usando aproximação da distribuição chi2.
    """

    rows = len(table)
    cols = len(table[0])
    row_sums = [sum(table[r]) for r in range(rows)]
    col_sums = [sum(table[r][c] for r in range(rows)) for c in range(cols)]
    total = sum(row_sums)

    if total == 0:
        return 0.0, 1.0

    chi2_stat = 0.0
    for r in range(rows):
        for c in range(cols):
            expected = row_sums[r] * col_sums[c] / total
            if expected > 0:
                chi2_stat += (table[r][c] - expected) ** 2 / expected

    dof = (rows - 1) * (cols - 1)
    if dof <= 0:
        return chi2_stat, 1.0

    # Aproximação da p-value usando função gamma incompleta (chi2 CDF)
    try:
        # survival function: 1 - CDF(chi2, dof)
        # Usamos a função gamma incompleta regularizada
        p_value = _chi2_survival(chi2_stat, dof)
    except Exception:
        p_value = 1.0

    return chi2_stat, p_value


def _chi2_survival(x: float, k: float) -> float:
    """P(X > x) para distribuição chi2 com k graus de liberdade (aproximação)."""
    # CDF da chi2: regularized incomplete gamma function
    # P(k/2, x/2) = gammainc(k/2, x/2)
    # survival = 1 - P(k/2, x/2) = Q(k/2, x/2)
    a = k / 2
    x2 = x / 2
    return _gammaincc(a, x2)


def _gammaincc(a: float, x: float) -> float:
    """Regularized upper incomplete gamma function Q(a,x) via series expansion."""
    if x < 0:
        return 1.0
    if x == 0:
        return 1.0
    # Use continued fraction for large x, series for small x
    if x < a + 1:
        return 1.0 - _gammaincl_series(a, x)
    else:
        return _gammaincl_cf(a, x)


def _gammaincl_series(a: float, x: float) -> float:
    """Lower incomplete gamma via series."""
    import math
    try:
        ap = a
        result = 1.0 / a
        delta = result
        for _ in range(300):
            ap += 1.0
            delta *= x / ap
            result += delta
            if abs(delta) < abs(result) * 1e-10:
                break
        return result * math.exp(-x + a * math.log(x) - math.lgamma(a))
    except Exception:
        return 0.0


def _gammaincl_cf(a: float, x: float) -> float:
    """Upper incomplete gamma via continued fraction (Lentz method)."""
    import math
    try:
        fpmin = 1e-300
        b = x + 1.0 - a
        c = 1.0 / fpmin
        d = 1.0 / b
        h = d
        for i in range(1, 301):
            an = -i * (i - a)
            b += 2.0
            d = an * d + b
            if abs(d) < fpmin:
                d = fpmin
            c = b + an / c
            if abs(c) < fpmin:
                c = fpmin
            d = 1.0 / d
            delta = d * c
            h *= delta
            if abs(delta - 1.0) < 1e-10:
                break
        return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h
    except Exception:
        return 0.0


def _chi_square_test(groups: dict[str, dict]) -> dict:
    """
    Calcula chi-quadrado para significância estatística do disparate impact.

    Tabela de contingência: [[aprovados, reprovados], ...] por grupo.
    Retorna {"chi2": float, "p_value": float, "significant": bool}.
    Requer pelo menos 2 grupos com count > 0.
    Usa scipy se disponível, Python puro caso contrário.
    """
    valid = [(v["approved"], v["count"] - v["approved"]) for v in groups.values() if v["count"] > 0]
    if len(valid) < 2:
        return {"chi2": 0.0, "p_value": 1.0, "significant": False, "available": True}

    try:
        if _SCIPY_AVAILABLE:
            chi2_stat, p, _dof, _expected = _chi2_contingency(valid)
        else:
            chi2_stat, p = _chi_square_fallback(valid)

        return {
            "chi2": round(float(chi2_stat), 4),
            "p_value": round(float(p), 4),
            "significant": bool(p < 0.05),
            "available": True,
        }
    except Exception:
        return {"chi2": 0.0, "p_value": 1.0, "significant": False, "available": True}


def _adverse_impact_ratio(groups: dict[str, dict]) -> float:
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
    groups: dict[str, dict] = {}

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
    di = _chi_square_test(groups)
    # EEOC compliant: ratio >= 0.80 E não significativo (p >= 0.05)
    eeoc_ok = (not below) and (not di.get("significant", False))

    return DemographicAuditResult(
        dimension=dimension,
        groups=groups,
        adverse_impact_ratio=ratio,
        below_threshold=below,
        alert_level="warning" if below else "ok",
        disparate_impact=di,
        eeoc_compliant=eeoc_ok,
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
        company_id: UUID | None = None,
    ) -> BiasAuditReport:
        """
        Consulta RubricEvaluation JOIN Candidate para a vaga e calcula adverse impact
        nas 4 dimensões: gênero, faixa etária, PCD, região.

        Args:
            db: AsyncSession de banco de dados.
            job_id: UUID da vaga (job_vacancy_id).
            company_id: UUID da company (LGPD multi-tenancy guard).
                Onda 4.2h-C2 (2026-05-24): obrigatório para evitar cross-tenant
                bias-audit data leak. Antes, qualquer job_id retornava bias
                report (incluindo gênero/idade/PCD/região = sensitive PII).
                LGPD Art. 33 + EU AI Act Art. 9-13.

        Returns:
            BiasAuditReport com stats agregadas (sem PII individual).
        """
        # Onda 4.2h-C2: tenant guard fail-closed — Candidate.company_id é scope canonical
        if company_id is None:
            logger.warning(
                "get_adverse_impact_by_job called without company_id — "
                "returning empty report (multi-tenancy fail-closed)"
            )
            return BiasAuditReport(
                job_id=str(job_id),
                evaluated_at=datetime.utcnow(),
                total_candidates=0,
                dimensions=[],
                has_alerts=False,
            )

        result = await db.execute(
            select(RubricEvaluation, Candidate)
            .join(Candidate, RubricEvaluation.candidate_id == Candidate.id)
            .where(
                RubricEvaluation.job_vacancy_id == job_id,
                Candidate.company_id == company_id,
            )
        )
        rows = result.all()
        records = [(row[0], row[1]) for row in rows]

        dimensions: list[DemographicAuditResult] = []

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
                "disparate_impact": d.disparate_impact,
                "eeoc_compliant": d.eeoc_compliant,
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


    def audit_ranking_results(
        self,
        results: list[dict],
        dimension: str = "gender",
        top_n: int = 10,
        company_id: str | None = None,
    ) -> dict:
        """
        FAR-5: Audita disparate impact em tempo real para uma lista de candidatos rankeados.

        Aplica a Four-Fifths Rule (80%) ao top-N de resultados de busca/ranking,
        verificando se algum grupo demográfico está sub-representado.

        Args:
            results: Lista de dicts de candidatos (devem ter campo correspondente à dimension).
            dimension: Campo demográfico a auditar ("gender", "age_group", "disability", "region").
            top_n: Quantos candidatos do topo analisar.
            company_id: Para logging multi-tenant.

        Returns:
            Dict com:
              - fairness_ok: bool (True se todos os grupos >= 80% da taxa do grupo dominante)
              - dimension: str
              - group_counts: Dict[str, int]
              - adverse_impact_ratios: Dict[str, float]
              - flagged_groups: List[str] (grupos com ratio < 0.80)
              - alert: str | None (mensagem de alerta se houver problema)
        """
        top = results[:top_n]
        if not top:
            return {"fairness_ok": True, "dimension": dimension, "group_counts": {}, "adverse_impact_ratios": {}, "flagged_groups": [], "alert": None}

        from collections import Counter
        values = [r.get(dimension) for r in top if r.get(dimension)]
        if len(values) < 3:
            logger.debug(
                "[BiasAuditService][FAR-5] Dados insuficientes para auditar dimension=%s (n=%d)",
                dimension, len(values),
            )
            return {"fairness_ok": True, "dimension": dimension, "group_counts": {}, "adverse_impact_ratios": {}, "flagged_groups": [], "alert": None}

        counts = Counter(values)
        total = sum(counts.values())
        max_count = max(counts.values())
        max_rate = max_count / total

        adverse_impact_ratios: dict[str, float] = {}
        flagged_groups: list[str] = []
        for group, cnt in counts.items():
            rate = cnt / total
            ratio = rate / max_rate if max_rate > 0 else 1.0
            adverse_impact_ratios[group] = round(ratio, 3)
            if ratio < FOUR_FIFTHS_THRESHOLD:
                flagged_groups.append(group)

        fairness_ok = len(flagged_groups) == 0
        alert = None
        if not fairness_ok:
            alert = (
                f"[FAR-5] Disparate impact detectado em '{dimension}': "
                f"grupos sub-representados no top-{top_n}: {flagged_groups}. "
                f"Razões de impacto adverso: {adverse_impact_ratios}."
            )
            logger.warning(
                "[BiasAuditService][FAR-5] Disparate impact em ranking: "
                "dimension=%s flagged=%s company=%s",
                dimension, flagged_groups, company_id,
            )

        return {
            "fairness_ok": fairness_ok,
            "dimension": dimension,
            "group_counts": dict(counts),
            "adverse_impact_ratios": adverse_impact_ratios,
            "flagged_groups": flagged_groups,
            "alert": alert,
        }


bias_audit_service = BiasAuditService()
