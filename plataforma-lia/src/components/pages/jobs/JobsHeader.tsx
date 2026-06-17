"use client"

import React, { memo } from"react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Tabs, TabsList, TabsTrigger } from"@/components/ui/tabs"
import { ViewToggle } from"@/components/ui/view-toggle"
import { Briefcase, Plus, LayoutGrid, List, Kanban } from"lucide-react"
import { useTranslations } from 'next-intl'
import type { JobMetrics } from"./types"

interface JobsHeaderProps {
  metrics: JobMetrics | null
  currentTab: 'all' | 'active' | 'drafts' | 'closed'
  viewMode: 'list' | 'cards' | 'kanban'
  onTabChange: (tab: 'all' | 'active' | 'drafts' | 'closed') => void
  onViewModeChange: (mode: 'list' | 'cards' | 'kanban') => void
  onCreateJob: () => void
}

const JobsHeader = memo(function JobsHeader({
  metrics,
  currentTab,
  viewMode,
  onTabChange,
  onViewModeChange,
  onCreateJob,
}: JobsHeaderProps) {
  const t = useTranslations('jobs')
  const tt = useTranslations('jobs.headerTabs')
  const tb = useTranslations('jobs.headerBadges')

  return (
    <div className="space-y-4 px-6 py-4" data-testid="jobs-header">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Briefcase className="h-5 w-5 text-lia-text-muted" />
            <h1 className="text-lg font-semibold text-lia-text-primary">{t('pageTitle')}</h1>
          </div>

          {metrics && (
            <div className="flex items-center gap-2">
              <Chip variant="neutral" className="border-lia-border-default dark:border-lia-border-default text-lia-text-secondary">
                {tb('total', { count: metrics.totalJobs })}
              </Chip>
              <Chip variant="success" >
                {tb('active', { count: metrics.activeJobs })}
              </Chip>
              <Chip variant="warning" >
                {tb('drafts', { count: metrics.draftJobs })}
              </Chip>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <ViewToggle
            value={viewMode}
            onChange={(v) => onViewModeChange(v as 'list' | 'cards' | 'kanban')}
            ariaLabel="Modo de visualização"
            size="md"
            iconOnly
            options={[
              { value: 'list', label: 'Lista', icon: List },
              { value: 'cards', label: 'Cards', icon: LayoutGrid },
              { value: 'kanban', label: 'Kanban', icon: Kanban },
            ]}
          />

          <Button
            variant="primary"
            size="sm"
            onClick={onCreateJob}
          >
            <Plus className="h-4 w-4 mr-2" />
            {t('newJob')}
          </Button>
        </div>
      </div>

      <Tabs value={currentTab} onValueChange={(v) => onTabChange(v as typeof currentTab)}>
        <TabsList className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
          <TabsTrigger
            value="all"
            className="data-[state=active]:bg-lia-bg-primary dark:data-[state=active]:bg-lia-bg-inverse data-[state=active]:text-lia-text-primary dark:data-[state=active]:text-lia-text-inverse"
          >
            {tt('all')}
          </TabsTrigger>
          <TabsTrigger
            value="active"
            className="data-[state=active]:bg-lia-bg-primary dark:data-[state=active]:bg-lia-bg-inverse data-[state=active]:text-lia-text-primary dark:data-[state=active]:text-lia-text-inverse"
          >
            {tt('active')}
          </TabsTrigger>
          <TabsTrigger
            value="drafts"
            className="data-[state=active]:bg-lia-bg-primary dark:data-[state=active]:bg-lia-bg-inverse data-[state=active]:text-lia-text-primary dark:data-[state=active]:text-lia-text-inverse"
          >
            {tt('drafts')}
          </TabsTrigger>
          <TabsTrigger
            value="closed"
            className="data-[state=active]:bg-lia-bg-primary dark:data-[state=active]:bg-lia-bg-inverse data-[state=active]:text-lia-text-primary dark:data-[state=active]:text-lia-text-inverse"
          >
            {tt('closed')}
          </TabsTrigger>
        </TabsList>
      </Tabs>
    </div>
  )
})
JobsHeader.displayName = 'JobsHeader'

export { JobsHeader }
