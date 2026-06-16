"""
Admin compliance endpoint: fairness report exportável.

GET /api/v1/admin/compliance/fairness/report

Retorna relatório de disparate impact (Four-Fifths Rule) por grupo protegido,
em formato JSON, CSV ou PDF, para auditores externos.

Fonte de dados: BiasAuditSnapshot — armazena resultados agregados por dimensão
(gender, age_group, disability, region) de auditorias anteriores.

Conformidade:
- NYC Local Law 144 — relatório de disparate impact obrigatório para ATS/screening
- EU AI Act Art. 13 / Recital 55 — transparência de sistemas de alto risco em RH
"""
from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/compliance", tags=["Admin - Compliance"])

FOUR_FIFTHS_THRESHOLD = 0.80

_SIGNING_KEY_ENV = "REPORT_SIGNING_KEY"


# TODO(phase2): extract to repository — admin compliance fairness
def _sign_payload(payload: str) -> str:
    """
    HMAC-SHA256 signature over the report payload for auditability.

    Auditors can verify the signature using the REPORT_SIGNING_KEY to confirm
    the report has not been tampered with after generation. This satisfies
    NYC LL 144 / EU AI Act Art. 13 tamper-evidence requirements.

    Falls back to a deterministic placeholder when the key is not set
    (development / environments without secrets configured) — logged as warning.
    """
    key_raw = os.environ.get(_SIGNING_KEY_ENV)
    if not key_raw:
        logger.warning(
            "REPORT_SIGNING_KEY not set — fairness report will not be cryptographically signed."
        )
        return "unsigned"
    return hmac.new(
        key_raw.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class GroupMetrics(BaseModel):
    dimension: str
    group: str
    total_evaluated: int
    total_approved: int
    approval_rate: float


class FourFifthsResult(BaseModel):
    dimension: str
    reference_group: str
    reference_rate: float
    groups: list[GroupMetrics]
    min_adverse_impact_ratio: float
    passes_four_fifths_rule: bool


class FairnessReportResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    generated_at: str
    company_id: str | None
    total_candidates_evaluated: int
    four_fifths_by_dimension: list[FourFifthsResult]
    overall_pass: bool
    report_version: str = "1.0"
    # HMAC-SHA256 signature over the JSON payload body (excludes this field itself).
    # Auditors verify with REPORT_SIGNING_KEY. Value is "unsigned" when key is absent.
    report_signature: str = "unsigned"


def _parse_period(period: str, start: str | None, end: str | None) -> tuple[datetime, datetime]:
    """Parse period string or custom date range into (start, end) datetimes."""
    now = datetime.now(timezone.utc)
    if period == "7d":
        return now - timedelta(days=7), now
    elif period == "30d":
        return now - timedelta(days=30), now
    elif period == "90d":
        return now - timedelta(days=90), now
    elif period == "custom":
        if not start or not end:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_date and end_date required for period=custom",
            )
        try:
            s = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
            e = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid date format: {exc}",
            ) from exc
        if s >= e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_date must be before end_date",
            )
        return s, e
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid period '{period}'. Use 7d, 30d, 90d, or custom.",
        )


def _compute_four_fifths(dimension: str, groups_data: list[dict]) -> FourFifthsResult:
    """
    Compute Four-Fifths Rule for one dimension across multiple protected groups.

    groups_data: list of {group, total, approved} dicts from BiasAuditSnapshot.

    Reference group = group with the highest approval rate.
    AIR = group_rate / reference_rate for each other group.
    Fails if ANY group has AIR < 0.80.
    """
    group_metrics: list[GroupMetrics] = []
    for g in groups_data:
        total = g.get("total", 0)
        approved = g.get("approved", 0)
        rate = approved / total if total > 0 else 0.0
        group_metrics.append(GroupMetrics(
            dimension=dimension,
            group=g.get("group", "unknown"),
            total_evaluated=total,
            total_approved=approved,
            approval_rate=round(rate, 4),
        ))

    if not group_metrics:
        return FourFifthsResult(
            dimension=dimension,
            reference_group="N/A",
            reference_rate=0.0,
            groups=[],
            min_adverse_impact_ratio=1.0,
            passes_four_fifths_rule=True,
        )

    reference = max(group_metrics, key=lambda g: g.approval_rate)
    ref_rate = reference.approval_rate

    if ref_rate == 0:
        return FourFifthsResult(
            dimension=dimension,
            reference_group=reference.group,
            reference_rate=0.0,
            groups=group_metrics,
            min_adverse_impact_ratio=1.0,
            passes_four_fifths_rule=True,
        )

    airs = [
        g.approval_rate / ref_rate
        for g in group_metrics
        if g.group != reference.group and g.total_evaluated > 0
    ]
    min_air = min(airs) if airs else 1.0

    return FourFifthsResult(
        dimension=dimension,
        reference_group=reference.group,
        reference_rate=round(ref_rate, 4),
        groups=group_metrics,
        min_adverse_impact_ratio=round(min_air, 4),
        passes_four_fifths_rule=min_air >= FOUR_FIFTHS_THRESHOLD,
    )


async def _build_report(
    db: AsyncSession,
    start_dt: datetime,
    end_dt: datetime,
    company_id: str | None,
) -> FairnessReportResponse:
    """
    Build Four-Fifths fairness report from BiasAuditSnapshot data.

    Aggregates across all snapshots in the period, merging per-group totals
    per dimension (gender, age_group, disability, region).
    """
    from app.models.bias_audit_snapshot import BiasAuditSnapshot

    stmt = select(
        BiasAuditSnapshot.dimensions_json,
        BiasAuditSnapshot.total_candidates,
        BiasAuditSnapshot.company_id,
    ).where(
        and_(
            BiasAuditSnapshot.evaluated_at >= start_dt,
            BiasAuditSnapshot.evaluated_at <= end_dt,
        )
    )

    if company_id:
        import uuid as _uuid
        try:
            cid = _uuid.UUID(company_id)
            stmt = stmt.where(BiasAuditSnapshot.company_id == cid)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid company_id: {exc}") from exc

    rows = (await db.execute(stmt)).all()

    dimension_aggregates: dict[str, dict[str, dict]] = {}
    total_candidates = 0

    for row in rows:
        total_candidates += row.total_candidates or 0
        if not row.dimensions_json:
            continue
        try:
            dimensions = json.loads(row.dimensions_json)
        except (json.JSONDecodeError, TypeError):
            continue

        for dim_entry in dimensions:
            dim_name = dim_entry.get("dimension") or dim_entry.get("name", "unknown")
            groups = dim_entry.get("groups", [])
            if dim_name not in dimension_aggregates:
                dimension_aggregates[dim_name] = {}
            for g in groups:
                gname = g.get("group", g.get("label", "unknown"))
                if gname not in dimension_aggregates[dim_name]:
                    dimension_aggregates[dim_name][gname] = {"total": 0, "approved": 0}
                dimension_aggregates[dim_name][gname]["total"] += g.get("total", g.get("count", 0))
                dimension_aggregates[dim_name][gname]["approved"] += g.get("approved", g.get("passed", 0))

    four_fifths_results: list[FourFifthsResult] = []
    for dim_name, groups_dict in dimension_aggregates.items():
        groups_data = [
            {"group": g, "total": v["total"], "approved": v["approved"]}
            for g, v in groups_dict.items()
        ]
        four_fifths_results.append(_compute_four_fifths(dim_name, groups_data))

    overall_pass = all(r.passes_four_fifths_rule for r in four_fifths_results) if four_fifths_results else True

    report = FairnessReportResponse(
        period=f"{start_dt.date().isoformat()} to {end_dt.date().isoformat()}",
        start_date=start_dt.isoformat(),
        end_date=end_dt.isoformat(),
        generated_at=datetime.now(timezone.utc).isoformat(),
        company_id=company_id,
        total_candidates_evaluated=total_candidates,
        four_fifths_by_dimension=four_fifths_results,
        overall_pass=overall_pass,
    )
    # Sign the canonical payload (excludes report_signature itself) for auditability.
    payload_to_sign = report.model_dump_json(exclude={"report_signature"})
    report.report_signature = _sign_payload(payload_to_sign)
    return report


def _report_to_csv(report: FairnessReportResponse) -> str:
    """Serialize report to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["LIA Fairness Report — Four-Fifths Rule (Disparate Impact Analysis)"])
    writer.writerow(["Generated At", report.generated_at])
    writer.writerow(["Period", report.period])
    writer.writerow(["Company ID", report.company_id or "all"])
    writer.writerow(["Total Candidates Evaluated", report.total_candidates_evaluated])
    writer.writerow(["Overall Pass (Four-Fifths)", report.overall_pass])
    writer.writerow([])

    writer.writerow([
        "Dimension",
        "Group",
        "Total Evaluated",
        "Total Approved",
        "Approval Rate",
        "Reference Group",
        "Reference Rate",
        "Min Adverse Impact Ratio",
        "Passes Four-Fifths Rule (AIR >= 0.80)",
    ])
    for result in report.four_fifths_by_dimension:
        for grp in result.groups:
            writer.writerow([
                result.dimension,
                grp.group,
                grp.total_evaluated,
                grp.total_approved,
                f"{grp.approval_rate:.4f}",
                result.reference_group,
                f"{result.reference_rate:.4f}",
                f"{result.min_adverse_impact_ratio:.4f}",
                "PASS" if result.passes_four_fifths_rule else "FAIL",
            ])

    return output.getvalue()


def _report_to_pdf_bytes(report: FairnessReportResponse) -> bytes:
    """
    Generate a PDF from the fairness report using WeasyPrint.

    Raises RuntimeError if WeasyPrint is not available — callers must handle.
    """
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>LIA Fairness Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }}
    h1 {{ color: #1a237e; }}
    h2 {{ color: #283593; margin-top: 24px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th {{ background: #3949ab; color: white; padding: 8px; text-align: left; }}
    td {{ border: 1px solid #ccc; padding: 6px; }}
    tr:nth-child(even) {{ background: #f5f5f5; }}
    .pass {{ color: #2e7d32; font-weight: bold; }}
    .fail {{ color: #c62828; font-weight: bold; }}
    .meta {{ font-size: 0.9em; color: #555; margin-bottom: 8px; }}
    .stamp {{ margin-top: 40px; font-size: 0.8em; color: #999; border-top: 1px solid #ccc; padding-top: 12px; }}
  </style>
</head>
<body>
  <h1>LIA — Fairness Report (Four-Fifths Rule / Disparate Impact)</h1>
  <div class="meta">
    <strong>Período:</strong> {report.period}<br>
    <strong>Empresa:</strong> {report.company_id or 'Todas'}<br>
    <strong>Total de candidatos avaliados:</strong> {report.total_candidates_evaluated}<br>
    <strong>Overall Pass:</strong>
    <span class="{'pass' if report.overall_pass else 'fail'}">
      {'&#10003; APROVADO' if report.overall_pass else '&#10007; REPROVADO'}
    </span>
  </div>

  <h2>Resultados por Dimensão</h2>
  <table>
    <thead>
      <tr>
        <th>Dimensão</th>
        <th>Grupo</th>
        <th>Avaliados</th>
        <th>Aprovados</th>
        <th>Taxa Aprovação</th>
        <th>Grupo Referência</th>
        <th>Taxa Referência</th>
        <th>Min AIR</th>
        <th>Four-Fifths Rule</th>
      </tr>
    </thead>
    <tbody>
"""
    for result in report.four_fifths_by_dimension:
        pass_cls = "pass" if result.passes_four_fifths_rule else "fail"
        pass_label = "&#10003; PASS" if result.passes_four_fifths_rule else "&#10007; FAIL"
        for grp in result.groups:
            html += f"""
      <tr>
        <td>{result.dimension}</td>
        <td>{grp.group}</td>
        <td>{grp.total_evaluated}</td>
        <td>{grp.total_approved}</td>
        <td>{grp.approval_rate:.1%}</td>
        <td>{result.reference_group}</td>
        <td>{result.reference_rate:.1%}</td>
        <td>{result.min_adverse_impact_ratio:.4f}</td>
        <td class="{pass_cls}">{pass_label}</td>
      </tr>"""

    html += f"""
    </tbody>
  </table>

  <div class="stamp">
    Relatório gerado em {report.generated_at} pelo WeDOTalent v{report.report_version}.
    Destinado a auditores de compliance. NYC Local Law 144 / EU AI Act Art. 13.
    Método: Four-Fifths Rule (AIR &ge; 0.80 por grupo vs. grupo de referência).
  </div>
</body>
</html>"""

    import weasyprint  # Raises ImportError if not installed
    return weasyprint.HTML(string=html).write_pdf()


@router.get("/fairness/report", response_model=None)
async def get_fairness_report(
    period: Literal["7d", "30d", "90d", "custom"] = Query(
        "30d",
        description="Período de análise: 7d, 30d, 90d ou custom (requer start_date e end_date)",
    ),
    format: Literal["json", "csv", "pdf"] = Query(
        "json",
        description="Formato de saída: json, csv ou pdf",
    ),
    company_id: str | None = Query(None, description="Filtrar por UUID da empresa"),
    start_date: str | None = Query(None, description="Data de início (ISO 8601) para period=custom"),
    end_date: str | None = Query(None, description="Data de fim (ISO 8601) para period=custom"),
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Exporta relatório de fairness (Four-Fifths Rule / disparate impact).

    Parâmetros
    ----------
    period : 7d | 30d | 90d | custom
        Período de análise. Use 'custom' com start_date e end_date.
    format : json | csv | pdf
        Formato de saída.
        - JSON: dados estruturados com Four-Fifths Result por dimensão
        - CSV: arquivo tabular para Excel/auditores
        - PDF: relatório formatado com timestamp (NYC LL 144 / EU AI Act); retorna 503
          se WeasyPrint não estiver instalado (instalar via pip install weasyprint)
    company_id : UUID (opcional)
        Filtrar por empresa específica.

    Acesso restrito a administradores.
    """
    start_dt, end_dt = _parse_period(period, start_date, end_date)

    # Onda 4.2h-C4 (2026-05-24): company_id fail-closed = JWT quando query
    # param ausente. Antes None passava direto pro _build_report e retornava
    # BiasAuditSnapshots de TODAS empresas (cross-tenant leak P0). LGPD Art.
    # 33 + EU AI Act Art. 9-13. wedotalent_admin que precise cross-tenant
    # deve passar explicit ?company_id=<uuid>.
    if company_id is None:
        company_id = _company_gate

    report = await _build_report(db, start_dt, end_dt, company_id)

    if format == "json":
        return report

    if format == "csv":
        csv_content = _report_to_csv(report)
        filename = f"fairness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    if format == "pdf":
        try:
            pdf_bytes = _report_to_pdf_bytes(report)
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail=(
                    "PDF generation requires WeasyPrint. "
                    "Install it via: pip install weasyprint. "
                    "Use format=json or format=csv as alternatives."
                ),
            )
        filename = f"fairness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
