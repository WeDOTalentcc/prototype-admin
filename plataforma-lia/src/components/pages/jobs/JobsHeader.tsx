"use client"

import React, { memo } from"react"
import { Button } from"@/components/ui/button"
import { Badge } from"@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger } from"@/components/ui/tabs"
import { Briefcase, Plus, LayoutGrid, List, Kanban } from"lucide-react"
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
  return (
    <div className="space-y-4 px-6 py-4" data-testid="jobs-header">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Briefcase className="h-5 w-5 text-lia-text-disabled" />
            <h1 className="text-lg font-semibold text-lia-text-primary">Vagas</h1>
          </div>
          
          {metrics && (
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="border-lia-border-default dark:border-lia-border-default text-lia-text-secondary">
                {metrics.totalJobs} total
              </Badge>
              <Badge variant="success" >
                {metrics.activeJobs} ativas
              </Badge>
              <Badge variant="warning" >
                {metrics.draftJobs} rascunhos
              </Badge>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <div className="flex items-center border border-lia-border-default dark:border-lia-border-default rounded-xl p-0.5">
            <Button
              variant="ghost"
              size="icon"
 className={`h-8 w-8 ${viewMode === 'list' ? 'bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-primary' : 'text-lia-text-tertiary'}`}
              onClick={() => onViewModeChange('list')}
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
 className={`h-8 w-8 ${viewMode === 'cards' ? 'bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-primary' : 'text-lia-text-tertiary'}`}
              onClick={() => onViewModeChange('cards')}
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
 className={`h-8 w-8 ${viewMode === 'kanban' ? 'bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-primary' : 'text-lia-text-tertiary'}`}
              onClick={() => onViewModeChange('kanban')}
            >
              <Kanban className="h-4 w-4" />
            </Button>
          </div>
          
          <Button
            onClick={onCreateJob}
            className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:hover:bg-lia-interactive-active"
          >
            <Plus className="h-4 w-4 mr-2" />
            Nova Vaga
          </Button>
        </div>
      </div>
      
      <Tabs value={currentTab} onValueChange={(v) => onTabChange(v as typeof currentTab)}>
        <TabsList className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
          <TabsTrigger 
            value="all" 
            className="data-[state=active]:bg-lia-bg-primary dark:data-[state=active]:bg-lia-bg-inverse data-[state=active]:text-lia-text-primary dark:data-[state=active]:text-lia-text-inverse"
          >
            Todas
          </TabsTrigger>
          <TabsTrigger 
            value="active"
            className="data-[state=active]:bg-lia-bg-primary dark:data-[state=active]:bg-lia-bg-inverse data-[state=active]:text-lia-text-primary dark:data-[state=active]:text-lia-text-inverse"
          >
            Ativas
          </TabsTrigger>
          <TabsTrigger 
            value="drafts"
            className="data-[state=active]:bg-lia-bg-primary dark:data-[state=active]:bg-lia-bg-inverse data-[state=active]:text-lia-text-primary dark:data-[state=active]:text-lia-text-inverse"
          >
            Rascunhos
          </TabsTrigger>
          <TabsTrigger 
            value="closed"
            className="data-[state=active]:bg-lia-bg-primary dark:data-[state=active]:bg-lia-bg-inverse data-[state=active]:text-lia-text-primary dark:data-[state=active]:text-lia-text-inverse"
          >
            Encerradas
          </TabsTrigger>
        </TabsList>
      </Tabs>
    </div>
  )
})
JobsHeader.displayName = 'JobsHeader'

export { JobsHeader }
