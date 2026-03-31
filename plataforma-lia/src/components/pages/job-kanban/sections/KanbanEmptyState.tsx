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
      title="Nenhum candidato neste pipeline ainda"
      description="Adicione candidatos ou busque no banco de talentos para iniciar o processo."
      action={{
        label: "Buscar candidatos",
        onClick: onAddCandidates,
      }}
      className="h-64"
    />
  )
})

KanbanEmptyState.displayName = "KanbanEmptyState"
