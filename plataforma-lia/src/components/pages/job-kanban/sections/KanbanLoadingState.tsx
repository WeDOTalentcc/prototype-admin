"use client"

import React from "react"
import { useTranslations } from "next-intl"

export const KanbanLoadingState = React.memo(function KanbanLoadingState() {
  const t = useTranslations('kanban')
  return (
    <div className="flex items-center justify-center h-screen bg-lia-bg-primary" role="status" aria-live="polite" aria-label={t('loading')}>
      <div className="flex flex-col items-center gap-4" role="status" aria-live="polite" aria-label={t('loading')}>
        <div className="animate-spin motion-reduce:animate-none rounded-full h-8 w-8 border-b-2 border-lia-border-medium" role="status" aria-live="polite" aria-label={t('loading')}></div>
        <span className="text-sm text-lia-text-tertiary font-open-sans">{t('loading')}</span>
      </div>
    </div>
  )
})

KanbanLoadingState.displayName = "KanbanLoadingState"
