// Onda 1 F5 (2026-05-27) — Studio Control Room canonical drawer.
//
// CANONICAL — este componente será reutilizado pelas Ondas 2 (AgentsCard Decidir)
// e 3 (job/funil). Mudanças aqui têm impacto em produtos a jusante.
//
// Props canonical (sensor check_decision_tree_drawer_uses_canonical_props.py):
//   - executionId: string | null   (null = drawer fechado)
//   - onClose: () => void
//
// Decisão UX (Paulo, calibrada no plano): híbrido resumido + "Ver detalhes
// técnicos" expandindo todos os steps. Cyan canonical exclusivo da IA via
// tokens lia-cyan-* em tailwind.config.ts.
"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import { Brain, Check, ChevronDown, Database, FileLock2, Loader2, Sparkles, X } from "lucide-react"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import { useExecutionReasoning } from "./use-execution-reasoning"
import type { AgentReasoningStep, ExecutionReasoningResponse } from "./types"
import { downloadLgpdTrailCsv } from "./lgpd-csv"

export interface DecisionTreeDrawerProps {
  executionId: string | null
  onClose: () => void
}

type ChipVariant = "neutral" | "success" | "warning" | "danger" | "info"

const STEP_TYPE_STYLES: Record<
  AgentReasoningStep["step_type"],
  { dot: string; variant: ChipVariant; chipClassName?: string }
> = {
  action: {
    dot: "bg-lia-cyan",
    // Cyan canonical exclusivo IA — override do variant info.
    variant: "info",
    chipClassName: "!border-lia-cyan/40 !bg-lia-cyan/10 !text-lia-cyan",
  },
  thought: {
    dot: "bg-violet-500",
    variant: "info",
  },
  observation: {
    dot: "bg-amber-500",
    variant: "warning",
  },
  criterion: {
    dot: "bg-emerald-500",
    variant: "success",
  },
}

function formatDuration(startedAt: string | null, completedAt: string | null): string | null {
  if (!startedAt || !completedAt) return null
  const start = new Date(startedAt).getTime()
  const end = new Date(completedAt).getTime()
  if (Number.isNaN(start) || Number.isNaN(end) || end < start) return null
  const ms = end - start
  if (ms < 1000) return `${ms}ms`
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60_000)}min ${Math.round((ms % 60_000) / 1000)}s`
}

function formatCost(cost: number | null): string | null {
  if (cost === null || cost === undefined) return null
  if (cost === 0) return "$0.00"
  if (cost < 0.01) return `$${cost.toFixed(4)}`
  return `$${cost.toFixed(3)}`
}

function formatTokens(input: number | null, output: number | null): string | null {
  if (input === null && output === null) return null
  const total = (input ?? 0) + (output ?? 0)
  if (total === 0) return null
  if (total < 1000) return `${total}`
  return `${(total / 1000).toFixed(1)}k`
}

interface MetaRowProps {
  label: string
  value: string | null
}

function MetaRow({ label, value }: MetaRowProps) {
  if (!value) return null
  return (
    <div className="flex items-center justify-between gap-2 text-xs">
      <span className="text-lia-text-tertiary">{label}</span>
      <span className="text-lia-text-secondary font-medium">{value}</span>
    </div>
  )
}

interface DecisionTreeBodyProps {
  reasoning: ExecutionReasoningResponse
  agentDisplayName: string
}

function DecisionTreeBody({ reasoning, agentDisplayName }: DecisionTreeBodyProps) {
  const t = useTranslations("agents.studio.decisionTree")
  const [showTechnical, setShowTechnical] = React.useState(false)

  const criteria = React.useMemo(
    () => reasoning.reasoning_trace.filter((s) => s.step_type === "criterion"),
    [reasoning.reasoning_trace],
  )
  const tokensLabel = formatTokens(reasoning.input_tokens, reasoning.output_tokens)
  const costLabel = formatCost(reasoning.cost_usd)
  const durationLabel = formatDuration(reasoning.started_at, reasoning.completed_at)

  return (
    <div className="flex flex-col gap-5">
      {/* Header bloco — agente + meta */}
      <div className="flex items-start gap-3 rounded-md border border-lia-border-subtle bg-lia-cyan/5 p-3">
        <div
          className={cn(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-lia-cyan text-white",
          )}
          aria-hidden="true"
        >
          <Brain className="h-4.5 w-4.5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-lia-text-primary truncate">
            {agentDisplayName}
          </div>
          <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-1">
            <MetaRow label={t("meta.model")} value={reasoning.model_used} />
            <MetaRow label={t("meta.tokens")} value={tokensLabel} />
            <MetaRow label={t("meta.cost")} value={costLabel} />
            <MetaRow label={t("meta.duration")} value={durationLabel} />
          </div>
        </div>
      </div>

      {/* Critérios principais */}
      <section aria-labelledby="dt-criteria-heading">
        <h3
          id="dt-criteria-heading"
          className="mb-2 flex items-center gap-2 text-sm font-semibold text-lia-text-primary"
        >
          <Sparkles className="h-4 w-4 text-lia-cyan" aria-hidden="true" />
          {t("criteriaTitle")}
        </h3>
        {criteria.length === 0 ? (
          <p className="text-xs text-lia-text-tertiary italic">{t("noCriteria")}</p>
        ) : (
          <ul className="space-y-1.5">
            {criteria.map((c, idx) => (
              <li
                key={`crit-${idx}`}
                className="flex items-center justify-between gap-3 rounded-md border border-lia-border-subtle bg-lia-bg-elevated px-3 py-2"
              >
                <div className="flex items-center gap-2 min-w-0">
                  {c.matched === false ? (
                    <X
                      className="h-4 w-4 shrink-0 text-rose-500"
                      aria-label={t("criterionNotMatched")}
                    />
                  ) : (
                    <Check
                      className="h-4 w-4 shrink-0 text-emerald-500"
                      aria-label={t("criterionMatched")}
                    />
                  )}
                  <span className="truncate text-sm text-lia-text-primary">{c.label}</span>
                </div>
                {c.score !== null && c.score !== undefined ? (
                  <span className="shrink-0 text-xs font-medium tabular-nums text-lia-text-secondary">
                    {c.score.toFixed(2)}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* LGPD */}
      <section
        aria-labelledby="dt-lgpd-heading"
        className="rounded-md border border-lia-border-subtle bg-lia-bg-elevated p-3"
      >
        <h3
          id="dt-lgpd-heading"
          className="mb-2 flex items-center gap-2 text-sm font-semibold text-lia-text-primary"
        >
          <FileLock2 className="h-4 w-4 text-lia-cyan" aria-hidden="true" />
          {t("lgpdTitle")}
        </h3>

        <div className="space-y-3">
          <div>
            <div className="text-xs font-medium text-lia-text-secondary mb-1">
              {t("lgpdRead")}
            </div>
            {reasoning.data_fields_accessed_summary.length === 0 ? (
              <p className="text-xs text-lia-text-tertiary italic">
                {t("lgpdNoFieldsRead")}
              </p>
            ) : (
              <div className="flex flex-wrap gap-1">
                {reasoning.data_fields_accessed_summary.map((field) => (
                  <Chip key={field} variant="neutral" density="compact" muted>
                    {field}
                  </Chip>
                ))}
              </div>
            )}
          </div>

          <div>
            <div className="text-xs font-medium text-lia-text-secondary mb-1">
              {t("lgpdNotAccessed")}
            </div>
            <div className="flex flex-wrap gap-1">
              {reasoning.data_fields_NOT_accessed.map((field) => (
                <Chip
                  key={field}
                  variant="danger"
                  density="compact"
                  muted
                  className="line-through"
                >
                  {field}
                </Chip>
              ))}
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => downloadLgpdTrailCsv(reasoning)}
            className="mt-1 gap-2 border-lia-border-default text-lia-text-primary hover:bg-lia-bg-tertiary"
            data-testid="decision-tree-export-lgpd"
          >
            <Database className="h-3.5 w-3.5" aria-hidden="true" />
            {t("exportLgpd")}
          </Button>
        </div>
      </section>

      {/* Detalhes técnicos (Collapsible) */}
      <Collapsible open={showTechnical} onOpenChange={setShowTechnical}>
        <CollapsibleTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="w-full justify-between text-lia-text-secondary hover:text-lia-text-primary"
            data-testid="decision-tree-technical-toggle"
          >
            <span className="text-sm font-medium">
              {showTechnical ? t("technicalDetailsHide") : t("technicalDetails")}
            </span>
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform motion-reduce:transition-none",
                showTechnical && "rotate-180",
              )}
              aria-hidden="true"
            />
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-2">
          {reasoning.reasoning_trace.length === 0 ? (
            <p className="text-xs text-lia-text-tertiary italic px-3 py-2">{t("noSteps")}</p>
          ) : (
            <ol className="space-y-2" data-testid="decision-tree-steps-list">
              {reasoning.reasoning_trace.map((step, idx) => {
                const style = STEP_TYPE_STYLES[step.step_type]
                const detailTrunc =
                  step.detail && step.detail.length > 200
                    ? `${step.detail.slice(0, 200)}…`
                    : step.detail
                return (
                  <li
                    key={`step-${idx}`}
                    className="rounded-md border border-lia-border-subtle bg-lia-bg-elevated p-2.5"
                  >
                    <div className="flex items-start gap-2">
                      <span
                        className={cn("mt-1.5 h-2 w-2 shrink-0 rounded-full", style.dot)}
                        aria-hidden="true"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Chip
                            variant={style.variant}
                            density="compact"
                            className={cn("uppercase tracking-wide", style.chipClassName)}
                          >
                            {t(`stepType.${step.step_type}`)}
                          </Chip>
                          {step.score !== null && step.score !== undefined ? (
                            <span className="text-[10px] tabular-nums text-lia-text-tertiary">
                              {t("stepScore", { score: step.score.toFixed(2) })}
                            </span>
                          ) : null}
                        </div>
                        <div className="mt-1 text-sm text-lia-text-primary break-words">
                          {step.label}
                        </div>
                        {detailTrunc ? (
                          <div className="mt-1 text-xs text-lia-text-secondary break-words">
                            {detailTrunc}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </li>
                )
              })}
            </ol>
          )}
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}

export function DecisionTreeDrawer({ executionId, onClose }: DecisionTreeDrawerProps) {
  const t = useTranslations("agents.studio.decisionTree")
  const { persona } = useAiPersona()
  const { data, isLoading, isError, isLegacy } = useExecutionReasoning(executionId)
  const open = executionId !== null
  // White-label canonical: nome do agente passa pelo useAiPersona — se o agente
  // for o assistente padrão (sem nome custom), exibe o persona.name configurado;
  // senão usa o agent_name canonical (custom agent tem nome próprio).
  const agentDisplayName = data?.agent_name || persona?.name || "Agente"

  return (
    <Sheet open={open} onOpenChange={(o) => (!o ? onClose() : undefined)}>
      <SheetContent
        side="right"
        data-testid="decision-tree-drawer"
        className="flex w-full flex-col gap-4 overflow-y-auto border-lia-border-default bg-lia-bg-primary sm:max-w-md"
      >
        <SheetHeader className="border-b border-lia-border-subtle pb-3">
          <SheetTitle className="text-base font-semibold text-lia-text-primary">
            {t("title")}
          </SheetTitle>
          <SheetDescription className="sr-only">{t("title")}</SheetDescription>
        </SheetHeader>

        {isLoading ? (
          <div
            className="flex flex-col gap-3"
            aria-busy="true"
            aria-live="polite"
            data-testid="decision-tree-loading"
          >
            <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
              <Loader2 className="h-3.5 w-3.5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
              <span>{t("loading")}</span>
            </div>
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        ) : isLegacy ? (
          <div
            className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-200"
            data-testid="decision-tree-legacy"
          >
            {t("legacyNotice")}
          </div>
        ) : isError ? (
          <div
            className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900 dark:border-rose-900/40 dark:bg-rose-950/20 dark:text-rose-200"
            data-testid="decision-tree-error"
          >
            {t("loadError")}
          </div>
        ) : data ? (
          <DecisionTreeBody reasoning={data} agentDisplayName={agentDisplayName} />
        ) : null}
      </SheetContent>
    </Sheet>
  )
}
