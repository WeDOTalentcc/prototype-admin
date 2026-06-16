"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Users } from "lucide-react"
import { EmptyState } from "@/components/ui/empty-state"

interface KanbanEmptyStateProps {
  onAddCandidates: () => void
}

export const KanbanEmptyState = React.memo(function KanbanEmptyState({ onAddCandidates }: KanbanEmptyStateProps) {
  const t = useTranslations('kanban')
  return (
    <EmptyState
      icon={<Users />}
      title={t('emptyTitle')}
      description={t('emptyDescription')}
      action={{
        label: t('searchCandidates'),
        onClick: onAddCandidates,
      }}
      className="h-64 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
    />
  )
})

KanbanEmptyState.displayName = "KanbanEmptyState"
