// Onda 4 F4 (2026-05-28) — modal de drilldown de execuções de consumo.
//
// Acionado ao clicar segmento do BarChart no hub Consumo > Agentes.
// Mostra lista paginada de execuções daquele agent_type via useConsumptionDrilldown.
//
// Decisões UX:
//   - 25 itens por página (denso, mas escaneável)
//   - Anterior/Próximo simples (sem jump-to-page)
//   - Tabela com timestamp, candidato (id curto), custo, tokens
//   - Loading: skeleton
//   - Empty: copy clara "Nenhuma execução encontrada"
"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState } from "react"
import { useTranslations } from "next-intl"
import { ChevronLeft, ChevronRight, RotateCw } from "lucide-react"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { useConsumptionDrilldown } from "@/hooks/consumption/use-consumption-drilldown"
import { getAgentLabel } from "@/components/settings/consumo/CreditosIaTab"

const PAGE_SIZE = 25

interface ConsumptionDrilldownModalProps {
  agentType: string | null
  studioAgentId?: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

function formatCost(cents: number): string {
  return `$${(cents / 100).toFixed(4)}`
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toString()
}

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso)
    return new Intl.DateTimeFormat("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(d)
  } catch {
    return iso
  }
}

export function ConsumptionDrilldownModal({
  agentType,
  studioAgentId,
  open,
  onOpenChange,
}: ConsumptionDrilldownModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('consumption-drilldown', open)

  const t = useTranslations("settings.consumption.drilldown")
  const [page, setPage] = useState(0)

  const { data, isLoading, error, refetch } = useConsumptionDrilldown(
    {
      agent_type: agentType ?? undefined,
      studio_agent_id: studioAgentId ?? undefined,
      since_days: 30,
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
    },
    { enabled: open && Boolean(agentType || studioAgentId) },
  )

  const totalCount = data?.total_count ?? 0
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))
  const canPrev = page > 0
  const canNext = page < totalPages - 1

  function handleOpenChange(next: boolean) {
    if (!next) setPage(0)
    onOpenChange(next)
  }

  const label = agentType ? getAgentLabel(agentType) : "—"

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="max-w-3xl"
        data-testid="consumption-drilldown-modal"
      >
        <DialogHeader>
          <DialogTitle>{t("title", { agentType: label })}</DialogTitle>
          <DialogDescription>
            {t("subtitle", { total: totalCount })}
          </DialogDescription>
        </DialogHeader>

        {isLoading && (
          <div className="space-y-2">
            {[0, 1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}

        {error && (
          <div
            className="flex flex-col items-center gap-3 py-8 text-center text-sm text-lia-text-secondary"
            role="alert"
            data-testid="drilldown-error"
          >
            <p>{t("error")}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="gap-1.5"
              data-testid="drilldown-retry"
            >
              <RotateCw className="h-3.5 w-3.5" />
              {t("errorRetry")}
            </Button>
          </div>
        )}

        {!isLoading && !error && data && data.items.length === 0 && (
          <div
            className="py-8 text-center text-sm text-lia-text-tertiary"
            data-testid="drilldown-empty"
          >
            {t("empty")}
          </div>
        )}

        {!isLoading && !error && data && data.items.length > 0 && (
          <div className="max-h-[60vh] overflow-y-auto">
            <table
              className="w-full text-xs"
              data-testid="drilldown-table"
            >
              <thead className="sticky top-0 bg-lia-bg-primary border-b border-lia-border-subtle">
                <tr className="text-left text-lia-text-tertiary">
                  <th className="py-2 font-medium">
                    {t("column.timestamp")}
                  </th>
                  <th className="py-2 font-medium">
                    {t("column.operation")}
                  </th>
                  <th className="py-2 font-medium">
                    {t("column.candidate")}
                  </th>
                  <th className="py-2 text-right font-medium">
                    {t("column.cost")}
                  </th>
                  <th className="py-2 text-right font-medium">
                    {t("column.tokens")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr
                    key={item.consumption_id}
                    className="border-b border-lia-border-subtle/60"
                  >
                    <td className="py-2 text-lia-text-secondary">
                      {formatTimestamp(item.created_at)}
                    </td>
                    <td className="py-2 text-lia-text-secondary">
                      {item.operation}
                    </td>
                    <td className="py-2 text-lia-text-secondary">
                      {item.candidate_id
                        ? item.candidate_id.slice(0, 8)
                        : "—"}
                    </td>
                    <td className="py-2 text-right tabular-nums text-lia-text-primary">
                      {formatCost(item.cost_cents)}
                    </td>
                    <td className="py-2 text-right tabular-nums text-lia-text-primary">
                      {formatTokens(item.total_tokens)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!isLoading && !error && totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-lia-border-subtle pt-3">
            <span className="text-xs text-lia-text-tertiary">
              {t("pagination.page", { page: page + 1, total: totalPages })}
            </span>
            <div className="flex gap-1">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={!canPrev}
                className={cn(
                  "inline-flex items-center gap-1 rounded-md border border-lia-border-subtle px-2.5 py-1 text-xs",
                  canPrev
                    ? "text-lia-text-secondary hover:bg-lia-bg-secondary"
                    : "cursor-not-allowed text-lia-text-disabled",
                )}
                aria-label={t("pagination.prev")}
              >
                <ChevronLeft className="h-3 w-3" />
                {t("pagination.prev")}
              </button>
              <button
                type="button"
                onClick={() => setPage((p) => p + 1)}
                disabled={!canNext}
                className={cn(
                  "inline-flex items-center gap-1 rounded-md border border-lia-border-subtle px-2.5 py-1 text-xs",
                  canNext
                    ? "text-lia-text-secondary hover:bg-lia-bg-secondary"
                    : "cursor-not-allowed text-lia-text-disabled",
                )}
                aria-label={t("pagination.next")}
              >
                {t("pagination.next")}
                <ChevronRight className="h-3 w-3" />
              </button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
