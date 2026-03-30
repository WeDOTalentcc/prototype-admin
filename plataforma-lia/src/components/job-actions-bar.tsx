"use client"

import { Briefcase, Share2, Brain, Copy, Pause, Play, UserPlus, X } from "lucide-react"
import { Button } from "@/components/ui/button"

interface JobActionsBarProps {
  selectedCount: number
  onDeselectAll: () => void
  onPublish: () => void
  onInsights: () => void
  onDuplicate: () => void
  onToggleStatus: () => void
  onAssignRecruiter: () => void
  hasActiveJobs?: boolean
}

export function JobActionsBar({
  selectedCount,
  onDeselectAll,
  onPublish,
  onInsights,
  onDuplicate,
  onToggleStatus,
  onAssignRecruiter,
  hasActiveJobs = true,
}: JobActionsBarProps) {
  if (selectedCount === 0) return null

  return (
    <div className="flex-shrink-0 mb-3 p-3 rounded-md bg-gray-50 dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-gray-200 dark:bg-lia-bg-elevated flex items-center justify-center flex-shrink-0">
              <Briefcase className="w-3.5 h-3.5 text-gray-600 dark:text-lia-text-tertiary" />
            </div>
            <span className="text-sm font-semibold text-gray-950">
              {selectedCount} vaga{selectedCount > 1 ? 's' : ''} selecionada{selectedCount > 1 ? 's' : ''}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onPublish}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-gray-800 dark:bg-lia-bg-elevated dark:hover:bg-gray-600 dark:text-lia-text-tertiary"
            title="Publicar em Canais"
          >
            <Share2 className="w-3.5 h-3.5 text-gray-600 dark:text-lia-text-tertiary" />
            <span>Publicar</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onInsights}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-gray-800 dark:bg-lia-bg-elevated dark:hover:bg-gray-600 dark:text-lia-text-tertiary"
            title="Métricas + Análise LIA"
          >
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            <span>Insights</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onDuplicate}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-gray-800 dark:bg-lia-bg-elevated dark:hover:bg-gray-600 dark:text-lia-text-tertiary"
            title="Duplicar Vaga"
          >
            <Copy className="w-3.5 h-3.5 text-gray-600 dark:text-lia-text-tertiary" />
            <span>Duplicar</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onToggleStatus}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-gray-800 dark:bg-lia-bg-elevated dark:hover:bg-gray-600 dark:text-lia-text-tertiary"
            title={hasActiveJobs ? "Pausar Vagas" : "Ativar Vagas"}
          >
            {hasActiveJobs ? (
              <Pause className="w-3.5 h-3.5 text-gray-600 dark:text-lia-text-tertiary" />
            ) : (
              <Play className="w-3.5 h-3.5 text-gray-600 dark:text-lia-text-tertiary" />
            )}
            <span>{hasActiveJobs ? "Pausar" : "Ativar"}</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onAssignRecruiter}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-gray-800 dark:bg-lia-bg-elevated dark:hover:bg-gray-600 dark:text-lia-text-tertiary"
            title="Atribuir Recrutador"
          >
            <UserPlus className="w-3.5 h-3.5 text-gray-600 dark:text-lia-text-tertiary" />
            <span>Recrutador</span>
          </Button>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={onDeselectAll}
          className="h-8 px-2 text-xs text-gray-800 hover:text-gray-950 dark:text-lia-text-tertiary dark:hover:text-gray-200"
          title="Limpar seleção"
        >
          <X className="w-3 h-3" />
        </Button>
      </div>
    </div>
  )
}
