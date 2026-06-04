// src/types/rrp-blocks.ts — Rich Response Protocol (RRP) block catalog (TS mirror).
//
// Espelho 1:1 de lia-agent-system/app/shared/rrp_blocks.py (Pydantic).
// AD1: single source of truth é o Pydantic; este arquivo deveria ser GERADO via
// codegen (datamodel-code-generator / pydantic→JSON Schema→ts). Até o codegen
// existir, manter em sincronia manual — qualquer campo novo no .py exige mudar aqui.
// Puro tipos + 1 helper de exaustividade; sem imports → não pode quebrar o build.

export type BlockRole = "answer" | "support" | "evidence" | "action";
export type BlockLayout = "inline" | "wide" | "panel";
export type BlockState = "loading" | "partial" | "ready" | "error";
export type Confidence = "low" | "medium" | "high";

export interface BlockError {
  reason: string;
  recoverable: boolean;
}

interface BaseBlock {
  block_id: string;
  role: BlockRole;
  layout: BlockLayout;
  state: BlockState;
  error?: BlockError | null;
}

// ── prose ────────────────────────────────────────────────────────────────────
export interface ProseBlock extends BaseBlock {
  kind: "prose";
  markdown: string;
}

// ── evidence_stack ────────────────────────────────────────────────────────────
export type EvidenceSourceType =
  | "linkedin"
  | "resume"
  | "assessment"
  | "interview"
  | "internal_record";

export interface EvidenceItem {
  source_type: EvidenceSourceType;
  ref_id: string;
  label: string;
  captured_at?: string | null;
  url?: string | null;
  excerpt?: string | null;
}

export interface EvidenceStackBlock extends BaseBlock {
  kind: "evidence_stack";
  items: EvidenceItem[];
  count: number;
}

// ── score_explainer (o moat) ──────────────────────────────────────────────────
export interface ScoreFactor {
  label: string;
  weight: number;
  contribution: "+" | "-";
  detail?: string;
  evidence_refs: string[];
}

export interface ScoreExplainerBlock extends BaseBlock {
  kind: "score_explainer";
  subject_id: string;
  subject_label: string;
  score: number; // 0–100
  score_label: string;
  confidence: Confidence;
  confidence_basis?: string;
  factors: ScoreFactor[];
  summary?: string;
  unverified: boolean;
  provenance_note?: string;
}

// ── comparison_table ──────────────────────────────────────────────────────────
export type ComparisonCellType = "score" | "text" | "badge" | "number";

export interface ComparisonColumn {
  key: string;
  label: string;
  type: ComparisonCellType;
  sortable: boolean;
}

export interface ComparisonRow {
  entity_id: string;
  cells: Record<string, unknown>;
  score_block_id?: string | null;
  highlight?: "attention" | "top" | null;
}

export interface ComparisonTableBlock extends BaseBlock {
  kind: "comparison_table";
  title: string;
  entity_type: "candidate" | "job";
  columns: ComparisonColumn[];
  rows: ComparisonRow[];
  default_sort?: Record<string, string> | null;
  total_count: number;
  shown_count: number;
}

// ── União discriminada ────────────────────────────────────────────────────────
export type ResponseBlock =
  | ProseBlock
  | ComparisonTableBlock
  | ScoreExplainerBlock
  | EvidenceStackBlock;

export type ResponseBlockKind = ResponseBlock["kind"];

/**
 * Exaustividade em compile-time (espelha o padrão assertNeverAction canônico).
 * USAR no `default` do switch do <ResponseBlockRenderer> SOMENTE depois de um
 * guard de runtime para kind desconhecido (AD6: backend pode emitir um kind novo
 * que esta union ainda não conhece — nesse caso renderizar fallback, NUNCA throw).
 */
export function assertNeverBlock(x: never): never {
  throw new Error(`ResponseBlock kind não tratado: ${JSON.stringify(x)}`);
}
