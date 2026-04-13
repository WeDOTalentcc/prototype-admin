"use client"

import React from "react"
import { Users } from "lucide-react"
import { EmptyState } from "@/components/ui/empty-state"

interface KanbanEmptyStateProps {
  onAddCandidates: () => void
}

export const KanbanEmptyState = React.memo(function KanbanEmptyState({ onAddCandidates }: KanbanEmptyStateProps) {
  return (
    <EmptyState
      icon={<Users />}
      title="Nenhum candidato neste funil ainda"
      description="Adicione candidatos ou busque no banco de talentos para iniciar o processo."
      action={{
        label: "Buscar candidatos",
        onClick: onAddCandidates,
      }}
      className="h-64 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
    />
  )
})

KanbanEmptyState.displayName = "KanbanEmptyState"
