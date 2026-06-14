"use client"

// Onda 2 F2 (2026-05-27) — AgentsCard canonical no Decidir.
//
// 5º card no Decidir: presença viva dos agentes IA. Top N agentes ativos do
// tenant (last hour), com status + alvo + último ação. Clicar abre o
// DecisionTreeDrawer canonical (Onda 1).
//
// CLAUDE.md REGRAS aplicadas:
//   - REGRA 1 settings/: server data via useQuery (hook canonical F1)
//   - REGRA 6 _shared/: presentational only, sem fetch inline aqui
//   - useAiPersona() para renderizar nome customizado per-tenant
//   - aria-live="polite" no container (a11y polling 10s)
//   - design tokens: wedo-cyan canonical (acento IA), sem hex hardcoded
//
// Visual: card canonical (Card + CardHeader + CardContent) — paridade com
// MyTasksCard/ActiveJobsCard. Linhas clicáveis com hover suave.

import React from "react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Brain, AlertCircle } from "lucide-react"
import Link from "next/link"
import { textStyles } from "@/lib/design-tokens"
import { useActiveAgentsSummary } from "@/hooks/agents/use-active-agents-summary"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import { FirstExecutionTooltip } from "@/components/pages-agent-studio/FirstExecutionTooltip"
import type { ActiveAgentSummaryItem } from "@/types/agents/active-summary"

export interface AgentsCardProps {
  /**
   * Abre o DecisionTreeDrawer canonical (Onda 1) com o executionId clicado.
   * Parent (tasks-page) renderiza o Drawer no nível da página.
   */
  onOpenDecisionTree: (executionId: string) => void
}

// i18n canonical (P1-5, 2026-05-29): copy migrada pra namespace
// agents.summary.* em messages/pt-BR.json + en.json. Helpers module-level
// recebem `t` por parâmetro (não podem chamar useTranslations diretamente).
type SummaryTranslator = ReturnType<typeof useTranslations>

// Badge numérico (não-localizável: "9+" é convenção universal de contagem).
function pendingBadge(n: number): string {
  return n > 9 ? "9+" : String(n)
}

function targetLabel(
  item: ActiveAgentSummaryItem,
  t: SummaryTranslator,
): string | null {
  if (!item.target_name) return null
  switch (item.target_type) {
    case "job":
      return `${t("target.job")}: ${item.target_name}`
    case "talent_pool":
      return `${t("target.pool")}: ${item.target_name}`
    case "pipeline_stage":
      return `${t("target.stage")}: ${item.target_name}`
    default:
      return item.target_name
  }
}

function statusLabel(
  status: ActiveAgentSummaryItem["status"],
  t: SummaryTranslator,
): string {
  switch (status) {
    case "running":
      return t("status.running")
    case "pending_approval":
      return t("status.pendingApproval")
    case "idle":
    default:
      return t("status.idle")
  }
}

interface AgentRowProps {
  item: ActiveAgentSummaryItem
  onOpenDecisionTree: (executionId: string) => void
  t: SummaryTranslator
}

function AgentRow({ item, onOpenDecisionTree, t }: AgentRowProps) {
  const canOpen = !!item.last_execution_id
  const pending = item.pending_approvals_count
  const target = targetLabel(item, t)

  const handleClick = () => {
    if (canOpen && item.last_execution_id) {
      onOpenDecisionTree(item.last_execution_id)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!canOpen) return
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      handleClick()
    }
  }

  return (
    <li>
      <div
        role={canOpen ? "button" : undefined}
        tabIndex={canOpen ? 0 : -1}
        onClick={canOpen ? handleClick : undefined}
        onKeyDown={handleKeyDown}
        aria-label={`${item.agent_name} — ${statusLabel(item.status, t)}`}
        className={`flex items-start gap-3 rounded-lg p-2 transition-colors motion-reduce:transition-none ${
          canOpen
            ? "cursor-pointer hover:bg-lia-interactive-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan"
            : "cursor-default"
        }`}
      >
        <div
          className="flex-shrink-0 w-8 h-8 rounded-full bg-wedo-cyan/15 flex items-center justify-center"
          aria-hidden="true"
        >
          <Brain className="w-4 h-4 text-wedo-cyan" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-lia-text-primary truncate">
              {item.agent_name}
            </span>
            <span className="text-xs text-lia-text-tertiary">·</span>
            <span className="text-xs text-lia-text-secondary capitalize">
              {item.agent_category}
            </span>
            <span className="text-xs text-lia-text-tertiary">·</span>
            <span className="text-xs text-lia-text-secondary">
              {statusLabel(item.status, t)}
            </span>
            {pending > 0 && (
              <Chip
                density="relaxed"
                variant="neutral"
                className="border-transparent bg-wedo-cyan/15 text-wedo-cyan-text dark:text-wedo-cyan font-medium"
                aria-label={t("pendingApprovals", { count: pending })}
              >
                {pendingBadge(pending)}
              </Chip>
            )}
          </div>
          {item.last_action_label && (
            <p className="text-xs text-lia-text-secondary mt-0.5 truncate">
              {item.last_action_label}
            </p>
          )}
          {target && (
            <p className="text-xs text-lia-text-tertiary mt-0.5 truncate">
              {target}
            </p>
          )}
        </div>
      </div>
    </li>
  )
}

export function AgentsCard({ onOpenDecisionTree }: AgentsCardProps) {
  const t = useTranslations("agents.summary")
  const { data, isLoading, isError, refetch } = useActiveAgentsSummary({
    surface: "decidir",
    limit: 5,
  })

  // useAiPersona() — REGRA CLAUDE.md: todo render de nome canonical da IA
  // passa por aqui. Aqui o nome do AGENTE customizado (CustomAgent.name)
  // vem do backend, então `persona` não substitui — mas garante que se
  // futuramente fallback for necessário, virá daqui.
  const { persona } = useAiPersona()
  // Evita unused-var lint quando persona não é referenciada diretamente —
  // canal de extensão Onda 3 (fallback name quando agent_name vazio).
  void persona

  const items = data?.items ?? []

  return (
    <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" aria-hidden="true" />
            <CardTitle
              className={`${textStyles.label} font-semibold text-lia-text-primary`}
            >
              {t("card.title")}
            </CardTitle>
          </div>
          <Link
            href="/agent-studio?tab=control-room"
            className="text-xs text-wedo-cyan-text dark:text-wedo-cyan hover:underline transition-colors motion-reduce:transition-none"
          >
            {t("card.viewAll")}
          </Link>
        </div>
      </CardHeader>
      <CardContent className="pt-0 pb-3">
        {/* aria-live polite: anuncia atualizações de polling sem interromper screen reader */}
        <div aria-live="polite" aria-atomic="false">
          {isLoading && (
            <div className="space-y-2" data-testid="agents-card-loading">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 p-2 animate-pulse motion-reduce:animate-none"
                >
                  <div className="w-8 h-8 rounded-full bg-lia-bg-secondary" />
                  <div className="flex-1 space-y-1.5">
                    <div className="h-3 w-1/2 rounded bg-lia-bg-secondary" />
                    <div className="h-2.5 w-2/3 rounded bg-lia-bg-secondary" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {!isLoading && isError && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-status-warning/10 border border-status-warning/30 text-sm text-status-warning">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span className="flex-1">{t("card.errorTitle")}</span>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                onClick={() => refetch()}
              >
                {t("card.retry")}
              </Button>
            </div>
          )}

          {!isLoading && !isError && items.length === 0 && (
            <div className="flex flex-col items-center gap-2 py-6 text-center">
              <div className="w-10 h-10 rounded-full bg-wedo-cyan/10 flex items-center justify-center">
                <Brain
                  className="w-5 h-5 text-wedo-cyan-text"
                  aria-hidden="true"
                />
              </div>
              <p className="text-sm font-medium text-lia-text-primary">
                {t("card.empty.title")}
              </p>
              <p className="text-xs text-lia-text-secondary max-w-xs">
                {t("card.empty.description")}
              </p>
              <Link
                href="/agent-studio"
                className="mt-1 text-xs font-medium text-wedo-cyan-text dark:text-wedo-cyan hover:underline"
              >
                {t("card.empty.cta")} →
              </Link>
            </div>
          )}

          {!isLoading && !isError && items.length > 0 && (
            <>
              {/* Onda 5.1 — tooltip 1x por agente quando primeira execução
                  acontece. Heurística: primeiro item com last_execution_id
                  (agente já rodou); storage key inclui agent_id para gate
                  per-agent (mostrar de novo se outro agente fizer 1ª exec). */}
              {(() => {
                const firstExecAgent = items.find(
                  (it) => it.last_execution_id != null,
                )
                if (!firstExecAgent) return null
                return (
                  <FirstExecutionTooltip
                    agentName={firstExecAgent.agent_name}
                    storageKey={`studio_first_execution_seen_${firstExecAgent.agent_id}`}
                    className="mb-2"
                  />
                )
              })()}
              <ul className="space-y-0.5" data-testid="agents-card-list">
                {items.map((item) => (
                  <AgentRow
                    key={item.agent_id}
                    item={item}
                    onOpenDecisionTree={onOpenDecisionTree}
                    t={t}
                  />
                ))}
              </ul>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
