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


def build_candidate_comparison_blocks(candidates: list[dict]) -> list[dict]:
    """comparison_table de PERFIL (sem score) — candidatos lado a lado.
    candidates: dicts com id, name, title, seniority, experience, skills(list), location."""
    from app.shared.rrp_blocks import (
        ComparisonColumn,
        ComparisonRow,
        ComparisonTableBlock,
    )

    if not candidates:
        return []
    rows = [
        ComparisonRow(
            entity_id=str(c.get("id")),
            cells={
                "name": c.get("name") or ("ID " + str(c.get("id"))),
                "title": c.get("title") or "-",
                "seniority": c.get("seniority") or "-",
                "experience": (str(c.get("experience")) + " anos")
                if c.get("experience") else "-",
                "skills": c.get("skills") or [],
                "location": c.get("location") or "-",
            },
        )
        for c in candidates
    ]
    table = ComparisonTableBlock(
        block_id="comparison_table:compare_candidates:"
        + "-".join(str(c.get("id")) for c in candidates),
        role="support",
        layout="wide",
        title="Comparacao de candidatos",
        entity_type="candidate",
        columns=[
            ComparisonColumn(key="name", label="Candidato", type="text"),
            ComparisonColumn(key="title", label="Cargo", type="text"),
            ComparisonColumn(key="seniority", label="Senioridade", type="text"),
            ComparisonColumn(key="experience", label="Experiencia", type="text"),
            ComparisonColumn(key="skills", label="Skills", type="text"),
            ComparisonColumn(key="location", label="Local", type="text"),
        ],
        rows=rows,
        total_count=len(candidates),
        shown_count=len(candidates),
    )
    return [table.model_dump(mode="json")]


def build_pipeline_funnel_block(
    title: str, stages: dict, total: int = 0, conversion_rate: float = 0.0
) -> list[dict]:
    """funnel de pipeline a partir de {etapa: contagem}."""
    from app.shared.rrp_blocks import FunnelBlock, FunnelStage

    if not stages:
        return []
    fstages = [FunnelStage(label=str(k), count=int(v)) for k, v in stages.items()]
    blk = FunnelBlock(
        block_id="funnel:pipeline:" + str(title),
        role="support",
        layout="wide",
        title=str(title),
        stages=fstages,
        total=int(total),
        conversion_rate=float(conversion_rate),
    )
    return [blk.model_dump(mode="json")]


def build_candidate_card_block(row: dict) -> list[dict]:
    """candidate_card de UM candidato. row: id, name, title, seniority,
    location, experience, skills(list), + OPCIONAIS de parecer:
    score, recommendation, summary, opinion_id.
    Score/recommendation/summary so quando ha LiaOpinion (opinion_id) — senao
    unverified=True (proveniencia honesta, sem numero fabricado)."""
    from app.shared.rrp_blocks import CandidateCardBlock

    cid = str(row.get("id"))
    has_op = row.get("opinion_id") is not None
    score = _num(row.get("score")) if has_op else None
    blk = CandidateCardBlock(
        block_id="candidate_card:" + cid,
        role="answer",
        layout="inline",
        candidate_id=cid,
        name=row.get("name") or ("ID " + cid),
        title=row.get("title"),
        seniority=row.get("seniority"),
        location=row.get("location"),
        experience_years=(
            int(row["experience"]) if row.get("experience") is not None else None
        ),
        top_skills=(row.get("skills") or [])[:5],
        score=(max(0.0, min(100.0, score)) if score is not None else None),
        score_label="Score LIA" if has_op else None,
        recommendation=row.get("recommendation") if has_op else None,
        summary=row.get("summary") if has_op else None,
        unverified=not has_op,
    )
    return [blk.model_dump(mode="json")]
