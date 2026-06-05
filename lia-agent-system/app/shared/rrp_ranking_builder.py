# DRAFT -> destino: lia-agent-system/app/shared/rrp_ranking_builder.py
"""Builder compartilhado dos blocos RRP de ranking de candidatos.

Produtor UNICO (canonical-fix) consumido por:
  - sourcing_actions._rank_candidates (caminho action-executor)
  - talent_tool_registry rank_candidates (caminho agentic-loop)

`rows`: lista de dicts normalizados com chaves:
  id, name, score(num), stage, e OPCIONAIS de parecer:
  recommendation, summary, strengths(list[str]), concerns(list[str]),
  opinion_id, wsi_id.
Linhas COM opinion_id ganham score_explainer + evidence_stack (o moat);
sem opinion -> so entram na comparison_table. Proveniencia honesta.
"""
from typing import Any


def _as_list(v: Any) -> list[str]:
    return [str(x) for x in v if x] if isinstance(v, list) else []


def _num(v: Any) -> float:
    try:
        return float(v) if v is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def build_candidate_ranking_blocks(job_id: str, rows: list[dict]) -> list[dict]:
    from app.shared.rrp_blocks import (
        ComparisonColumn,
        ComparisonRow,
        ComparisonTableBlock,
        EvidenceItem,
        EvidenceStackBlock,
        ScoreExplainerBlock,
        ScoreFactor,
    )

    if not rows:
        return []

    table_rows: list[ComparisonRow] = []
    explainers: list[ScoreExplainerBlock] = []
    evidence: list[EvidenceStackBlock] = []

    for i, r in enumerate(rows, 1):
        cid = str(r.get("id"))
        score = _num(r.get("score"))
        has_op = r.get("opinion_id") is not None
        sbid = f"score_explainer:rank:{cid}" if has_op else None
        table_rows.append(
            ComparisonRow(
                entity_id=cid,
                cells={
                    "rank": i,
                    "name": r.get("name") or ("ID " + cid),
                    "score": score,
                    "stage": r.get("stage") or "-",
                },
                score_block_id=sbid,
                highlight="top" if i == 1 else None,
            )
        )
        if not has_op:
            continue
        strengths = _as_list(r.get("strengths"))
        concerns = _as_list(r.get("concerns"))
        factors = [
            ScoreFactor(label=s, weight=0.0, contribution="+") for s in strengths[:4]
        ] + [
            ScoreFactor(label=c, weight=0.0, contribution="-") for c in concerns[:4]
        ]
        explainers.append(
            ScoreExplainerBlock(
                block_id=sbid,
                role="evidence",
                layout="inline",
                subject_id=cid,
                subject_label=r.get("name") or cid,
                score=max(0.0, min(100.0, score)),
                score_label="Score LIA",
                confidence="high" if factors else "medium",
                confidence_basis=(r.get("recommendation") or "Parecer LIA consolidado"),
                factors=factors,
                summary=(r.get("summary") or "")[:280],
                unverified=False,
            )
        )
        ev = [
            EvidenceItem(
                source_type="internal_record",
                ref_id=f"opinion:{r['opinion_id']}",
                label="Parecer LIA",
            )
        ]
        if r.get("wsi_id"):
            ev.append(
                EvidenceItem(
                    source_type="assessment",
                    ref_id=f"wsi:{r['wsi_id']}",
                    label="Entrevista WSI",
                )
            )
        evidence.append(
            EvidenceStackBlock(
                block_id=f"evidence_stack:rank:{cid}",
                role="evidence",
                layout="inline",
                items=ev,
                count=len(ev),
            )
        )

    table = ComparisonTableBlock(
        block_id=f"comparison_table:rank:{job_id}",
        role="support",
        layout="wide",
        title="Ranking de candidatos",
        entity_type="candidate",
        columns=[
            ComparisonColumn(key="rank", label="#", type="number"),
            ComparisonColumn(key="name", label="Candidato", type="text"),
            ComparisonColumn(key="score", label="Score LIA", type="score"),
            ComparisonColumn(key="stage", label="Etapa", type="text"),
        ],
        rows=table_rows,
        default_sort={"column_key": "score", "dir": "desc"},
        total_count=len(rows),
        shown_count=len(rows),
    )
    blocks = [table.model_dump(mode="json")]
    for b in explainers + evidence:
        blocks.append(b.model_dump(mode="json"))
    return blocks
