"use client"

import { useState, useCallback } from "react"
import { useHitlPending, type HitlPendingItem } from "@/hooks/recruitment/use-hitl-pending"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ShieldCheck, Clock, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

const ACTION_LABELS: Record<string, string> = {
  create_job: "Criar Vaga",
  move_candidate: "Mover Candidato",
  finalize_wsi: "Finalizar Avaliação WSI",
  send_email: "Enviar E-mail",
  pipeline_transition: "Transição de Funil",
}

function formatAction(action: string): string {
  return ACTION_LABELS[action] || action.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())
}

function formatTimeAgo(isoDate: string): string {
  const now = Date.now()
  const then = new Date(isoDate).getTime()
  const diffMs = now - then
  const diffMin = Math.floor(diffMs / 60000)

  if (diffMin < 1) return "agora"
  if (diffMin < 60) return `${diffMin}min`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}h`
  const diffD = Math.floor(diffH / 24)
  return `${diffD}d`
}

interface HitlPendingBadgeProps {
  onNavigateToChat?: (sessionId: string, threadId: string) => void
}

export function HitlPendingBadge({ onNavigateToChat }: HitlPendingBadgeProps) {
  const { items, count } = useHitlPending({ enabled: true, pollingIntervalMs: 30000 })
  const [isOpen, setIsOpen] = useState(false)

  const handleItemClick = useCallback(
    (item: HitlPendingItem) => {
      setIsOpen(false)
      if (onNavigateToChat) {
        onNavigateToChat(item.ws_session_id, item.thread_id)
      } else {
        window.dispatchEvent(
          new CustomEvent("lia:navigate-chat-page", {
            detail: { conversationId: item.thread_id },
          })
        )
      }
    },
    [onNavigateToChat]
  )

  if (count === 0) return null

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="relative h-7 w-7 p-0 rounded-full hover:bg-lia-interactive-hover"
          title={`${count} aprovação(ões) pendente(s)`}
        >
          <ShieldCheck className="h-4 w-4 text-lia-text-secondary" />
          <span
            className={cn(
              "absolute -top-0.5 -right-0.5 flex items-center justify-center",
              "min-w-[16px] h-4 px-1 rounded-full",
              "bg-status-error text-white text-[10px] font-semibold leading-none"
            )}
          >
            {count > 99 ? "99+" : count}
          </span>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        side="bottom"
        sideOffset={8}
        className="w-80 max-h-[400px] overflow-y-auto p-0"
      >
        <div className="px-3 py-2 border-b border-lia-border-subtle">
          <h3 className="text-xs font-semibold text-lia-text-primary">
            Aprovações Pendentes
          </h3>
          <p className="text-[10px] text-lia-text-tertiary mt-0.5">
            {count} ação(ões) aguardando sua decisão
          </p>
        </div>

        <div className="py-1">
          {items.map((item) => (
            <button
              key={item.pending_id}
              onClick={() => handleItemClick(item)}
              className="w-full flex items-start gap-2.5 px-3 py-2.5 text-left hover:bg-lia-interactive-hover transition-colors"
            >
              <div className="flex-shrink-0 mt-0.5">
                <div className="w-6 h-6 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                  <ShieldCheck className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1">
                  <span className="text-xs font-medium text-lia-text-primary truncate">
                    {formatAction(item.action)}
                  </span>
                  <div className="flex items-center gap-1 text-[10px] text-lia-text-tertiary flex-shrink-0">
                    <Clock className="w-2.5 h-2.5" />
                    {formatTimeAgo(item.requested_at || item.created_at || "")}
                  </div>
                </div>
                <p className="text-[11px] text-lia-text-secondary mt-0.5 line-clamp-2">
                  {item.description || "Ação aguardando aprovação humana"}
                </p>
                {item.domain && (
                  <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded bg-lia-bg-tertiary text-lia-text-tertiary">
                    {item.domain}
                  </span>
                )}
              </div>
              <ArrowRight className="w-3 h-3 text-lia-text-muted flex-shrink-0 mt-1" />
            </button>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
