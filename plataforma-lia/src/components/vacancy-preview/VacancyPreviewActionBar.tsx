"use client"

/**
 * VacancyPreviewActionBar — Phase I.2.
 *
 * Mirror 1:1 of `CandidatePreviewActionBar` (`src/components/candidate-preview/
 * CandidatePreviewActionBar.tsx`, 256 lines). Same visual tokens (h-6 w-6 ghost
 * buttons, gap-1.5, side="bottom" tooltips with delayDuration=200, ghost variant
 * with `hover:bg-lia-bg-tertiary`). Same horizontal `flex items-center
 * justify-between` root.
 *
 * Responsibility: show universal (stage-agnostic) actions on the vacancy preview
 * top — Editar Configurações (deep-link to settings tab), Ver Kanban,
 * Compartilhar, Favoritar, Imprimir. Stage-specific decisions go in the sibling
 * `VacancyDecisionBar` (mirrors `PipelineDecisionBar`).
 *
 * See `.planning/vacancy-pipeline-plan.md` Phase I.2.c.
 */
import { Button } from "@/components/ui/button"
import {
  Settings,
  Layers3,
  Share2,
  Star,
  Printer,
} from "lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { toast } from "sonner"

interface VacancyPreviewActionBarProps {
  vacancyId: string
  vacancyTitle: string
  isFavorite?: boolean
  /** Default: deep-link to /jobs/{id}?tab=edit&section=descricao */
  onOpenSettings?: (vacancyId: string) => void
  /** Default: deep-link to /jobs/{id}?tab=management (kanban) */
  onOpenKanban?: (vacancyId: string) => void
  onShare?: (vacancyId: string) => void
  onToggleFavorite?: (vacancyId: string) => void
  onPrint?: (vacancyId: string) => void
}

export function VacancyPreviewActionBar({
  vacancyId,
  vacancyTitle,
  isFavorite = false,
  onOpenSettings,
  onOpenKanban,
  onShare,
  onToggleFavorite,
  onPrint,
}: VacancyPreviewActionBarProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-1.5 flex-wrap">
        {/* Editar Configurações — deep-link to /jobs/{id}?tab=edit&section=descricao */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              onClick={() => {
                if (onOpenSettings) onOpenSettings(vacancyId)
                else if (typeof window !== "undefined") {
                  window.open(`/jobs/${vacancyId}?tab=edit&section=descricao`, "_blank")
                }
              }}
            >
              <Settings className="w-3.5 h-3.5 text-lia-text-secondary" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">Editar Configurações</TooltipContent>
        </Tooltip>

        {/* Ver Kanban — deep-link to /jobs/{id}?tab=management */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              onClick={() => {
                if (onOpenKanban) onOpenKanban(vacancyId)
                else if (typeof window !== "undefined") {
                  window.open(`/jobs/${vacancyId}?tab=management`, "_blank")
                }
              }}
            >
              <Layers3 className="w-3.5 h-3.5 text-lia-text-secondary" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">Ver Kanban</TooltipContent>
        </Tooltip>

        {/* Compartilhar */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              onClick={() => {
                if (onShare) onShare(vacancyId)
                else if (typeof navigator !== "undefined" && navigator.clipboard) {
                  navigator.clipboard.writeText(`${window.location.origin}/jobs/${vacancyId}`)
                  toast.success("Link copiado", { description: vacancyTitle })
                }
              }}
            >
              <Share2 className="w-3.5 h-3.5 text-lia-text-secondary" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">Compartilhar</TooltipContent>
        </Tooltip>

        {/* Favoritar — same conditional bg pattern as candidate */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className={`h-6 w-6 p-0 ${isFavorite ? "bg-status-warning/15" : "hover:bg-status-warning/10"}`}
              onClick={() => {
                onToggleFavorite?.(vacancyId)
                toast.success(isFavorite ? "Removido dos favoritos" : "Adicionado aos favoritos", {
                  description: vacancyTitle,
                })
              }}
            >
              <Star className={`w-3.5 h-3.5 ${isFavorite ? "text-status-warning fill-amber-500" : "text-status-warning"}`} />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">
            {isFavorite ? "Remover dos Favoritos" : "Adicionar aos Favoritos"}
          </TooltipContent>
        </Tooltip>

        {/* Imprimir / Export PDF — opcional */}
        {onPrint && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                onClick={() => onPrint(vacancyId)}
              >
                <Printer className="w-3.5 h-3.5 text-lia-text-secondary" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="text-xs">Imprimir</TooltipContent>
          </Tooltip>
        )}
      </div>
    </div>
  )
}
