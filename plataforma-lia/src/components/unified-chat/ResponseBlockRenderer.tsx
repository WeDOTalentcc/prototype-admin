"use client";

// src/components/unified-chat/ResponseBlockRenderer.tsx
// Rich Response Protocol — renderer único dos blocos tipados (Fase 0 slice).
// Exaustivo por `kind` + fallback de kind desconhecido (AD6: nunca throw).
// State-aware (AD7): comparison_table transpõe em sidebar/floating (sem scroll-h).
// score baixo = neutro/mudo (fairness). i18n via useTranslations('rrp').

import React, { useState } from "react";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { renderMarkdown } from "@/lib/render-markdown";
import type {
  ResponseBlock,
  ProseBlock,
  ComparisonTableBlock,
  ScoreExplainerBlock,
  EvidenceStackBlock,
  ScoreFactor,
} from "@/types/rrp-blocks";

type TFn = ReturnType<typeof useTranslations>;

function scoreTone(score: number): string {
  // Fairness/LGPD: baixo = neutro/mudo (NÃO vermelho).
  if (score >= 85) return "text-wedo-cyan";
  if (score >= 70) return "text-lia-text-primary";
  return "text-lia-text-tertiary";
}

function formatCell(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (Array.isArray(v)) return v.join(", ");
  return String(v);
}

function ProseView({ block }: { block: ProseBlock }) {
  return (
    <div
      className="text-sm text-lia-text-primary leading-relaxed [&_table]:w-full [&_th]:text-left [&_td]:py-1 [&_th]:py-1 [&_a]:text-wedo-cyan"
      dangerouslySetInnerHTML={{ __html: renderMarkdown(block.markdown) }}
    />
  );
}

function ScoreExplainerView({ block }: { block: ScoreExplainerBlock }) {
  const t = useTranslations("rrp");
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-2 text-left"
      >
        <span className="text-sm font-medium text-lia-text-primary">
          {block.subject_label}
        </span>
        <span
          className={cn(
            "text-sm font-semibold tabular-nums",
            scoreTone(block.score),
          )}
        >
          {block.score_label} {Math.round(block.score)}% ·{" "}
          <span className="font-normal text-lia-text-tertiary">
            {open ? t("hide") : t("why")}
          </span>
        </span>
      </button>
      {open && (
        <div className="mt-2 space-y-1.5 border-t border-lia-border-subtle pt-2">
          {block.confidence_basis ? (
            <p className="text-xs text-lia-text-tertiary">
              {t("confidenceLine", {
                level: block.confidence,
                basis: block.confidence_basis,
              })}
            </p>
          ) : null}
          {block.unverified ? (
            <p className="text-xs italic text-lia-text-tertiary">
              ⚠ {block.provenance_note || t("unverifiedDefault")}
            </p>
          ) : null}
          <ul className="space-y-1">
            {block.factors.map((f: ScoreFactor, i: number) => (
              <li
                key={i}
                className="flex items-start gap-2 text-xs text-lia-text-secondary"
              >
                <span
                  className={
                    f.contribution === "+"
                      ? "text-wedo-cyan"
                      : "text-lia-text-tertiary"
                  }
                >
                  {f.contribution}
                </span>
                <span className="flex-1">
                  <span className="text-lia-text-primary">{f.label}</span>
                  {f.detail ? ` — ${f.detail}` : ""}
                  {f.weight > 0 ? (
                    <span className="text-lia-text-tertiary">
                      {" "}
                      {t("weight", { pct: Math.round(f.weight * 100) })}
                    </span>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function EvidenceStackView({ block }: { block: EvidenceStackBlock }) {
  const t = useTranslations("rrp");
  const [open, setOpen] = useState(false);
  const n = block.count || block.items.length;
  if (!block.items || block.items.length === 0) return null;
  return (
    <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="text-xs text-lia-text-secondary"
      >
        📎 {t("sources", { count: n })} {open ? "▲" : "▼"}
      </button>
      {open && (
        <ul className="mt-1.5 space-y-1">
          {block.items.map((it, i) => (
            <li key={i} className="text-xs text-lia-text-tertiary">
              <span className="text-lia-text-secondary">{it.source_type}</span> ·{" "}
              {it.label}
              {it.captured_at ? ` (${it.captured_at})` : ""}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function scoreCellValue(v: unknown): React.ReactNode {
  if (typeof v === "number") {
    return (
      <span className={cn("font-semibold tabular-nums", scoreTone(v))}>
        {Math.round(v)}%
      </span>
    );
  }
  return formatCell(v);
}

// AD7: variante estreita (sidebar/floating) — transpõe a tabela em cards
// empilhados (candidato = card; coluna = label:valor), sem scroll horizontal.
function ComparisonTableNarrow({
  block,
  t,
}: {
  block: ComparisonTableBlock;
  t: TFn;
}) {
  return (
    <div className="space-y-2">
      {block.title ? (
        <div className="text-xs font-medium text-lia-text-secondary">
          {block.title}
        </div>
      ) : null}
      {block.rows.map((row) => (
        <div
          key={row.entity_id}
          className={cn(
            "rounded-lg border border-lia-border-subtle p-2",
            row.highlight === "top" || row.highlight === "attention"
              ? "bg-lia-bg-secondary"
              : "",
          )}
        >
          {block.columns.map((c) => (
            <div key={c.key} className="flex justify-between gap-2 py-0.5 text-xs">
              <span className="text-lia-text-tertiary">{c.label}</span>
              <span className="text-right text-lia-text-primary">
                {c.type === "score"
                  ? scoreCellValue(row.cells[c.key])
                  : formatCell(row.cells[c.key])}
              </span>
            </div>
          ))}
        </div>
      ))}
      {block.total_count > block.shown_count ? (
        <p className="text-[11px] text-lia-text-tertiary">
          {t("showingOf", { shown: block.shown_count, total: block.total_count })}
        </p>
      ) : null}
    </div>
  );
}

function ComparisonTableWide({
  block,
  t,
}: {
  block: ComparisonTableBlock;
  t: TFn;
}) {
  return (
    <div className="overflow-x-auto rounded-lg border border-lia-border-subtle">
      {block.title ? (
        <div className="border-b border-lia-border-subtle bg-lia-bg-tertiary px-2 py-1.5 text-xs font-medium text-lia-text-secondary">
          {block.title}
        </div>
      ) : null}
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="border-b border-lia-border-subtle bg-lia-bg-tertiary">
            {block.columns.map((c) => (
              <th
                key={c.key}
                scope="col"
                className="px-2 py-1.5 text-left font-medium text-lia-text-secondary"
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {block.rows.map((row) => (
            <tr
              key={row.entity_id}
              className={cn(
                "border-b border-lia-border-subtle last:border-0",
                (row.highlight === "attention" || row.highlight === "top") &&
                  "bg-lia-bg-secondary",
              )}
            >
              {block.columns.map((c) => (
                <td
                  key={c.key}
                  className={cn(
                    "px-2 py-1.5",
                    c.type === "score"
                      ? ""
                      : "text-lia-text-primary",
                  )}
                >
                  {c.type === "score"
                    ? scoreCellValue(row.cells[c.key])
                    : formatCell(row.cells[c.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {block.total_count > block.shown_count ? (
        <p className="px-2 py-1 text-[11px] text-lia-text-tertiary">
          {t("showingOf", { shown: block.shown_count, total: block.total_count })}
        </p>
      ) : null}
    </div>
  );
}

function ComparisonTableView({
  block,
  narrow,
}: {
  block: ComparisonTableBlock;
  narrow: boolean;
}) {
  const t = useTranslations("rrp");
  return narrow ? (
    <ComparisonTableNarrow block={block} t={t} />
  ) : (
    <ComparisonTableWide block={block} t={t} />
  );
}

function RenderOne({
  block,
  narrow,
}: {
  block: ResponseBlock;
  narrow: boolean;
}) {
  const t = useTranslations("rrp");
  switch (block.kind) {
    case "prose":
      return <ProseView block={block} />;
    case "score_explainer":
      return <ScoreExplainerView block={block} />;
    case "evidence_stack":
      return <EvidenceStackView block={block} />;
    case "comparison_table":
      return <ComparisonTableView block={block} narrow={narrow} />;
    default:
      // AD6: kind desconhecido (skew de deploy FE/BE) → fallback, nunca throw.
      return (
        <p className="text-xs italic text-lia-text-tertiary">
          {t("unsupportedBlock")}
        </p>
      );
  }
}

export function ResponseBlockRenderer({
  blocks,
  mode,
}: {
  blocks?: ResponseBlock[] | null;
  mode?: string;
}) {
  const t = useTranslations("rrp");
  if (!blocks || blocks.length === 0) return null;
  const narrow = mode === "sidebar" || mode === "floating";
  return (
    <div className="mt-2 space-y-2">
      {blocks.map((block, i) => {
        try {
          return (
            <RenderOne key={block.block_id || i} block={block} narrow={narrow} />
          );
        } catch {
          return (
            <p key={i} className="text-xs italic text-lia-text-tertiary">
              {t("blockError")}
            </p>
          );
        }
      })}
    </div>
  );
}
