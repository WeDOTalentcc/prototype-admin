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
  FunnelBlock,
  CandidateCardBlock,
  ScoreFactor,
} from "@/types/rrp-blocks";

type TFn = ReturnType<typeof useTranslations>;

function scoreTone(score: number): string {
  // Fairness/LGPD: baixo = neutro/mudo (NÃO vermelho).
  if (score >= 85) return "text-wedo-cyan";
  if (score >= 70) return "text-lia-text-primary";
  return "text-lia-text-tertiary";
}

// Cor da mini-barra de score (familia cyan; baixo = mudo, fairness).
function scoreBarTone(score: number): string {
  if (score >= 85) return "bg-wedo-cyan";
  if (score >= 70) return "bg-wedo-cyan/50";
  return "bg-lia-text-tertiary/40";
}

// Iniciais p/ avatar do candidato (1-2 letras).
function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
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
          <ul className="space-y-1.5">
            {block.factors.map((f: ScoreFactor, i: number) => (
              <li key={i} className="flex items-center gap-2 text-xs">
                <span
                  className={cn(
                    "w-3 shrink-0 text-center font-semibold",
                    f.contribution === "+"
                      ? "text-wedo-cyan"
                      : "text-lia-text-tertiary",
                  )}
                >
                  {f.contribution}
                </span>
                <span className="min-w-0 flex-1 truncate text-lia-text-secondary">
                  <span className="text-lia-text-primary">{f.label}</span>
                  {f.detail ? (
                    <span className="text-lia-text-tertiary">: {f.detail}</span>
                  ) : null}
                </span>
                {f.weight > 0 ? (
                  <span className="flex shrink-0 items-center gap-1.5">
                    <span className="relative h-1 w-8 overflow-hidden rounded-full bg-lia-border-subtle/50">
                      <span
                        className={cn(
                          "absolute inset-y-0 left-0 rounded-full",
                          f.contribution === "+"
                            ? "bg-wedo-cyan/70"
                            : "bg-lia-text-tertiary/40",
                        )}
                        style={{
                          width: `${Math.max(Math.round(f.weight * 100), 4)}%`,
                        }}
                      />
                    </span>
                    <span className="tabular-nums text-lia-text-tertiary">
                      {Math.round(f.weight * 100)}%
                    </span>
                  </span>
                ) : null}
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
    const pct = Math.max(0, Math.min(100, v));
    return (
      <span className="flex items-center gap-1.5">
        <span className="relative h-1.5 w-10 shrink-0 overflow-hidden rounded-full bg-lia-border-subtle/50">
          <span
            className={cn("absolute inset-y-0 left-0 rounded-full", scoreBarTone(pct))}
            style={{ width: `${Math.max(pct, 3)}%` }}
          />
        </span>
        <span className={cn("tabular-nums font-semibold", scoreTone(pct))}>
          {Math.round(pct)}
        </span>
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

function FunnelView({ block }: { block: FunnelBlock }) {
  const t = useTranslations("rrp");
  // labels de etapa: reusa o mapa canonico de nomes de etapa (PT/EN);
  // fallback p/ o proprio valor (etapas custom/seedadas ja legiveis).
  const ts = useTranslations("settings.recruitment.journey.defaultStageNames");
  const stageLabel = (code: string) => (ts.has(code) ? ts(code) : code);
  const max = Math.max(1, ...block.stages.map((s) => s.count));
  // retencao relativa ao topo do funil (1a etapa = 100%).
  const top = block.stages[0]?.count ?? 0;
  return (
    <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-3">
      <p className="mb-2 text-sm font-medium text-lia-text-primary">
        {block.title}
      </p>
      <div className="space-y-1.5">
        {block.stages.map((s, i) => {
          const pct = Math.round((s.count / max) * 100);
          return (
            <div key={i} className="flex items-center gap-2">
              <span className="w-28 shrink-0 truncate text-xs text-lia-text-secondary">
                {stageLabel(s.label)}
              </span>
              <div className="relative h-5 flex-1 overflow-hidden rounded bg-lia-border-subtle/40">
                <div
                  className="h-full rounded bg-wedo-cyan/60"
                  style={{ width: `${Math.max(pct, 4)}%` }}
                />
              </div>
              <span className="w-16 shrink-0 text-right text-xs tabular-nums">
                <span className="font-medium text-lia-text-primary">
                  {s.count}
                </span>
                {top > 0 ? (
                  <span className="text-lia-text-tertiary">
                    {" "}· {Math.round((s.count / top) * 100)}%
                  </span>
                ) : null}
              </span>
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex justify-between border-t border-lia-border-subtle pt-2 text-xs text-lia-text-tertiary">
        <span>{t("funnelTotal", { count: block.total })}</span>
        <span>{t("funnelConversion", { pct: block.conversion_rate })}</span>
      </div>
    </div>
  );
}

function CandidateCardView({ block }: { block: CandidateCardBlock }) {
  const t = useTranslations("rrp");
  const meta = [
    block.title,
    block.seniority,
    block.location,
    block.experience_years != null
      ? t("candidateYears", { count: block.experience_years })
      : null,
  ]
    .filter(Boolean)
    .join(" · ");
  return (
    <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-3">
      <div className="flex items-start gap-2.5">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-wedo-cyan/10 text-xs font-semibold text-wedo-cyan">
          {initials(block.name)}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <span className="truncate text-sm font-semibold text-lia-text-primary">
              {block.name}
            </span>
            {block.score != null ? (
              <span
                className={cn(
                  "shrink-0 text-sm font-semibold tabular-nums",
                  scoreTone(block.score),
                )}
              >
                {Math.round(block.score)}%
              </span>
            ) : null}
          </div>
          {meta ? (
            <p className="mt-0.5 truncate text-xs text-lia-text-tertiary">
              {meta}
            </p>
          ) : null}
        </div>
      </div>
      {block.recommendation ? (
        <span className="mt-1.5 inline-block rounded-full bg-wedo-cyan/15 px-2 py-0.5 text-xs font-medium text-wedo-cyan">
          {block.recommendation}
        </span>
      ) : null}
      {block.top_skills.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-1">
          {block.top_skills.map((s, i) => (
            <span
              key={i}
              className="rounded bg-lia-border-subtle/40 px-1.5 py-0.5 text-xs text-lia-text-secondary"
            >
              {s}
            </span>
          ))}
        </div>
      ) : null}
      {block.summary ? (
        <p className="mt-2 text-xs leading-relaxed text-lia-text-secondary">
          {block.summary}
        </p>
      ) : null}
      {block.unverified ? (
        <p className="mt-1.5 text-xs italic text-lia-text-tertiary">
          {t("candidateUnverified")}
        </p>
      ) : null}
    </div>
  );
}

// AD5: skeleton de carregamento (state='loading') — placeholder shimmer.
function BlockSkeleton() {
  return (
    <div
      data-testid="block-skeleton"
      className="space-y-1.5 rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-3"
      aria-hidden="true"
    >
      <div className="h-3 w-1/3 animate-pulse rounded bg-lia-border-subtle/60 motion-reduce:animate-none" />
      <div className="h-3 w-2/3 animate-pulse rounded bg-lia-border-subtle/40 motion-reduce:animate-none" />
      <div className="h-3 w-1/2 animate-pulse rounded bg-lia-border-subtle/40 motion-reduce:animate-none" />
    </div>
  );
}

// AD5: estado de erro do bloco (state='error') — nunca quebra o chat.
function BlockErrorView({ t }: { t: TFn }) {
  return (
    <p className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-2 text-xs italic text-lia-text-tertiary">
      {t("blockError")}
    </p>
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
  if (block.state === "error") return <BlockErrorView t={t} />;
  if (block.state === "loading") return <BlockSkeleton />;
  switch (block.kind) {
    case "prose":
      return <ProseView block={block} />;
    case "score_explainer":
      return <ScoreExplainerView block={block} />;
    case "evidence_stack":
      return <EvidenceStackView block={block} />;
    case "comparison_table":
      return <ComparisonTableView block={block} narrow={narrow} />;
    case "funnel":
      return <FunnelView block={block} />;
    case "candidate_card":
      return <CandidateCardView block={block} />;
    default:
      // AD6: kind desconhecido (skew de deploy FE/BE) → fallback, nunca throw.
      return (
        <p className="text-xs italic text-lia-text-tertiary">
          {t("unsupportedBlock")}
        </p>
      );
  }
}

function ExpandHint() {
  const t = useTranslations("rrp");
  return (
    <button
      type="button"
      onClick={() =>
        window.dispatchEvent(
          new CustomEvent("lia:request-chat-mode", {
            detail: { mode: "fullscreen" },
          }),
        )
      }
      className="mt-1 flex items-center gap-1 text-xs text-wedo-cyan hover:underline"
    >
      {t("expandFullscreen")} →
    </button>
  );
}

// AD4: answer-first. role ordena; sort estavel preserva a ordem do produtor.
const ROLE_RANK: Record<string, number> = {
  answer: 0,
  support: 1,
  evidence: 2,
  action: 3,
};

export function ResponseBlockRenderer({
  blocks,
  mode,
}: {
  blocks?: ResponseBlock[] | null;
  mode?: string;
}) {
  const t = useTranslations("rrp");
  const [showAll, setShowAll] = useState(false);
  if (!blocks || blocks.length === 0) return null;
  const narrow = mode === "sidebar" || mode === "floating";
  const ordered = [...blocks].sort(
    (a, b) => (ROLE_RANK[a.role] ?? 9) - (ROLE_RANK[b.role] ?? 9),
  );
  // AD4 block budget: evita 'muro de cards'. Generoso p/ NAO esconder o moat
  // (rank emite ~7 blocos colapsados); so corta muro real. Ajustavel pos-live.
  const budget = narrow ? 6 : 12;
  const visible = showAll ? ordered : ordered.slice(0, budget);
  const hidden = ordered.length - visible.length;
  return (
    <div className="mt-2 space-y-2">
      {visible.map((block, i) => {
        const wide = block.layout === "wide" || block.layout === "panel";
        try {
          return (
            <div
              key={block.block_id || i}
              className="animate-in fade-in slide-in-from-bottom-2 duration-300 motion-reduce:animate-none"
              style={{
                animationDelay: `${Math.min(i, 6) * 50}ms`,
                animationFillMode: "backwards",
              }}
            >
              <RenderOne block={block} narrow={narrow} />
              {narrow && wide ? <ExpandHint /> : null}
            </div>
          );
        } catch {
          return (
            <p key={i} className="text-xs italic text-lia-text-tertiary">
              {t("blockError")}
            </p>
          );
        }
      })}
      {hidden > 0 && !showAll ? (
        <button
          type="button"
          onClick={() => setShowAll(true)}
          className="text-xs text-wedo-cyan hover:underline"
        >
          {t("showMore", { count: hidden })}
        </button>
      ) : null}
    </div>
  );
}
