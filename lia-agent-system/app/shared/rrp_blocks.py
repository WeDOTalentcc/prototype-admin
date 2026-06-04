"""
app/shared/rrp_blocks.py — Rich Response Protocol (RRP) block catalog.

Catálogo tipado de blocos de resposta da LIA (Fase 0 slice). Discriminado por
`kind`. ADITIVO — não altera ChatResponse/structured_data existentes; um campo
`response_blocks: list[ResponseBlock]` será adicionado a ChatResponse num passo
de wiring posterior (hot file — fazer só com a árvore limpa).

Invariante de proveniência (CLAUDE.md "Proveniência honesta em saídas de IA"):
  todo score/evidência apresentado com atribuição de fonte DEVE ter fonte
  verificável. Sem retrieval real → unverified=True + confidence='low' + rótulo
  explícito. NUNCA citar fonte real para número derivado só do LLM.
  Enforçado por verify_block_provenance() + tests/contract/test_rrp_provenance_gate.py.
"""
from __future__ import annotations

from typing import Annotated, Any, Callable, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

# ── Vocabulário comum ────────────────────────────────────────────────────────
BlockRole = Literal["answer", "support", "evidence", "action"]
BlockLayout = Literal["inline", "wide", "panel"]
BlockState = Literal["loading", "partial", "ready", "error"]
Confidence = Literal["low", "medium", "high"]


class BlockError(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str
    recoverable: bool = False


class _BlockBase(BaseModel):
    """Envelope comum. Sem company_id; blocos são montados server-side a partir
    de dados já escopados por JWT (multi-tenancy — company_id nunca vem do LLM)."""

    model_config = ConfigDict(extra="forbid")

    block_id: str  # dedup/React key: f"{kind}:{source_tool}:{entity_id}"
    role: BlockRole = "support"
    layout: BlockLayout = "inline"
    state: BlockState = "ready"
    error: BlockError | None = None  # só quando state in {error, partial}


# ── prose (role:answer) ──────────────────────────────────────────────────────
class ProseBlock(_BlockBase):
    kind: Literal["prose"] = "prose"
    role: BlockRole = "answer"
    layout: BlockLayout = "inline"
    markdown: str


# ── evidence_stack (role:evidence) ───────────────────────────────────────────
class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_type: Literal[
        "linkedin", "resume", "assessment", "interview", "internal_record"
    ]
    ref_id: str  # server-issued; DEVE resolver a registro real escopado por JWT
    label: str
    captured_at: str | None = None
    url: str | None = None
    excerpt: str | None = None


class EvidenceStackBlock(_BlockBase):
    kind: Literal["evidence_stack"] = "evidence_stack"
    role: BlockRole = "evidence"
    items: list[EvidenceItem] = Field(default_factory=list)
    count: int = 0


# ── score_explainer (role:evidence) — o moat ─────────────────────────────────
class ScoreFactor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str
    weight: float
    contribution: Literal["+", "-"]
    detail: str = ""
    evidence_refs: list[str] = Field(default_factory=list)  # -> EvidenceItem.ref_id


class ScoreExplainerBlock(_BlockBase):
    kind: Literal["score_explainer"] = "score_explainer"
    role: BlockRole = "evidence"
    subject_id: str
    subject_label: str
    score: float = Field(ge=0, le=100)
    score_label: str = "Match"
    confidence: Confidence = "low"
    confidence_basis: str = ""
    factors: list[ScoreFactor] = Field(default_factory=list)
    summary: str = ""  # linha colapsada: "Match 82% · por quê?"
    unverified: bool = False
    provenance_note: str = ""


# ── comparison_table (role:support, layout:wide) ─────────────────────────────
class ComparisonColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    label: str
    type: Literal["score", "text", "badge", "number"] = "text"
    sortable: bool = True


class ComparisonRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entity_id: str
    cells: dict[str, Any] = Field(default_factory=dict)
    score_block_id: str | None = None  # liga à célula de score → score_explainer
    highlight: Literal["attention", "top"] | None = None


class ComparisonTableBlock(_BlockBase):
    kind: Literal["comparison_table"] = "comparison_table"
    role: BlockRole = "support"
    layout: BlockLayout = "wide"
    title: str
    entity_type: Literal["candidate", "job"] = "candidate"
    columns: list[ComparisonColumn] = Field(default_factory=list)
    rows: list[ComparisonRow] = Field(default_factory=list)
    default_sort: dict[str, str] | None = None
    total_count: int = 0  # truncação explícita — sem cap silencioso (REGRA 4)
    shown_count: int = 0


# ── União discriminada ───────────────────────────────────────────────────────
ResponseBlock = Annotated[
    Union[
        ProseBlock,
        ComparisonTableBlock,
        ScoreExplainerBlock,
        EvidenceStackBlock,
    ],
    Field(discriminator="kind"),
]

_KIND_MAP: dict[str, type[BaseModel]] = {
    "prose": ProseBlock,
    "comparison_table": ComparisonTableBlock,
    "score_explainer": ScoreExplainerBlock,
    "evidence_stack": EvidenceStackBlock,
}


# ── Gate de proveniência (AD9 — rastreabilidade, não presença) ───────────────
def verify_block_provenance(
    block: BaseModel,
    resolver: Callable[[str], bool],
) -> list[str]:
    """Retorna lista de violações de proveniência (vazia = OK).

    `resolver(ref_id) -> bool`: True se o ref_id resolve a um registro REAL
    escopado por JWT que a tool de fato buscou. Refs fabricados/não-resolvíveis
    são violação — score/evidência não pode ser apresentado como fato sem fonte.

    Regras pinadas (espelha o espírito de test_salary_benchmark_provenance.py):
      1. Todo evidence_ref de um ScoreFactor resolve via resolver.
      2. Todo EvidenceItem.ref_id resolve via resolver.
      3. Se unverified=True → confidence DEVE ser 'low' E provenance_note não-vazio
         (estimativa sem busca tem que ser rotulada, nunca apresentada como fato).
      4. Se unverified=True → NÃO pode haver evidence_refs citados (fonte fabricada).
    """
    violations: list[str] = []

    if isinstance(block, ScoreExplainerBlock):
        if block.unverified:
            if block.confidence != "low":
                violations.append(
                    f"score_explainer[{block.subject_id}] unverified=True mas "
                    f"confidence='{block.confidence}' (deve ser 'low')"
                )
            if not block.provenance_note.strip():
                violations.append(
                    f"score_explainer[{block.subject_id}] unverified=True sem "
                    f"provenance_note (estimativa precisa ser rotulada)"
                )
            cited = [r for f in block.factors for r in f.evidence_refs]
            if cited:
                violations.append(
                    f"score_explainer[{block.subject_id}] unverified=True mas cita "
                    f"fontes {cited} (proveniência fabricada — proibido)"
                )
        else:
            for f in block.factors:
                for ref in f.evidence_refs:
                    if not resolver(ref):
                        violations.append(
                            f"score_explainer[{block.subject_id}] fator '{f.label}': "
                            f"evidence_ref '{ref}' não resolve a registro real"
                        )

    if isinstance(block, EvidenceStackBlock):
        for item in block.items:
            if not resolver(item.ref_id):
                violations.append(
                    f"evidence_stack item '{item.label}': ref_id '{item.ref_id}' "
                    f"não resolve a registro real"
                )

    return violations
