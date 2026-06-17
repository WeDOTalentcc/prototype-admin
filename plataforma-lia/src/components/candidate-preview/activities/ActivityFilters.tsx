"use client"

import { Activity, GitBranch, List, PlusCircle } from"lucide-react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"

export type ActivityFilterType = 'all' | 'emails' | 'interviews' | 'lia' | 'applications' | 'tests' | 'offers' | 'evaluations'
export type ActivityViewType = 'list' | 'timeline'
export type PeriodFilterType = '7days' | '30days' | '3months' | 'all'

interface ActivityFiltersProps {
  totalCount: number
  activityFilter: ActivityFilterType
  activityView: ActivityViewType
  periodFilter: PeriodFilterType
  onActivityFilterChange: (filter: ActivityFilterType) => void
  onActivityViewChange: (view: ActivityViewType) => void
  onPeriodFilterChange: (period: PeriodFilterType) => void
  onShowLiaModal: () => void
}

export function ActivityFilters({
  totalCount,
  activityFilter,
  activityView,
  periodFilter,
  onActivityFilterChange,
  onActivityViewChange,
  onPeriodFilterChange,
  onShowLiaModal,
}: ActivityFiltersProps) {
  return (
    <div className="p-3 bg-lia-bg-primary" data-testid="activity-filters">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-xs font-medium text-lia-text-primary flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-lia-text-primary" />
          Feed de Atividades
          <Chip density="relaxed" variant="neutral" muted className="px-1 py-0">{totalCount}</Chip>
        </h4>
        <div className="flex items-center gap-2">
          <select
            value={periodFilter}
            onChange={(e) => onPeriodFilterChange((e.target as HTMLSelectElement).value as PeriodFilterType)}
            className="text-xs px-2 py-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-border-default"
          >
            <option value="7days">Últimos 7 dias</option>
            <option value="30days">Últimos 30 dias</option>
            <option value="3months">Últimos 3 meses</option>
            <option value="all">Todo período</option>
          </select>
          <div className="flex items-center bg-lia-bg-primary rounded-xl p-0.5 border border-lia-border-subtle">
            <button
              onClick={() => onActivityViewChange('timeline')}
              className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${activityView === 'timeline' ? 'bg-lia-interactive-active text-lia-text-primary' : 'text-lia-text-secondary hover:text-lia-text-primary'}`}
              title="Visualização Timeline"
            >
              <GitBranch className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => onActivityViewChange('list')}
              className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${activityView === 'list' ? 'bg-lia-interactive-active text-lia-text-primary' : 'text-lia-text-secondary hover:text-lia-text-primary'}`}
              title="Visualização Lista"
            >
              <List className="w-3.5 h-3.5" />
            </button>
          </div>
          <Button
            onClick={onShowLiaModal}
            size="sm"
            className="gap-1 px-2 py-1 text-xs h-6 bg-lia-bg-tertiary hover:bg-lia-interactive-active text-lia-text-secondary border border-lia-border-subtle"
          >
            <PlusCircle className="w-3 h-3" />
            Nova Atividade
          </Button>
        </div>
      </div>
      <div className="flex gap-1 flex-wrap">
        <button
          onClick={() => onActivityFilterChange('all')}
          className={`px-2 py-1 text-xs rounded-full transition-colors motion-reduce:transition-none ${activityFilter === 'all' ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text' : 'bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active'}`}
        >
          Todas
        </button>
        <button
          onClick={() => onActivityFilterChange('emails')}
          className={`px-2 py-1 text-xs rounded-full transition-colors motion-reduce:transition-none ${activityFilter === 'emails' ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text font-semibold' : 'bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active'}`}
        >
          📧 Emails
        </button>
        <button
          onClick={() => onActivityFilterChange('interviews')}
          className={`px-2 py-1 text-xs rounded-full transition-colors motion-reduce:transition-none ${activityFilter === 'interviews' ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text font-semibold' : 'bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active'}`}
        >
          🎤 Entrevistas
        </button>
        <button
          onClick={() => onActivityFilterChange('tests')}
          className={`px-2 py-1 text-xs rounded-full transition-colors motion-reduce:transition-none ${activityFilter === 'tests' ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text font-semibold' : 'bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active'}`}
        >
          📝 Testes
        </button>
        <button
          onClick={() => onActivityFilterChange('lia')}
          className={`px-2 py-1 text-xs rounded-full transition-colors motion-reduce:transition-none ${activityFilter === 'lia' ? 'bg-lia-text-primary text-white font-semibold' : 'bg-wedo-cyan-bg-15 text-lia-text-secondary hover:opacity-80'}`}
        >
          🤖 IA
        </button>
        <button
          onClick={() => onActivityFilterChange('offers')}
          className={`px-2 py-1 text-xs rounded-full transition-colors motion-reduce:transition-none ${activityFilter === 'offers' ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text font-semibold' : 'bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active'}`}
        >
          💼 Ofertas
        </button>
        <button
          onClick={() => onActivityFilterChange('applications')}
          className={`px-2 py-1 text-xs rounded-full transition-colors motion-reduce:transition-none ${activityFilter === 'applications' ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text font-semibold' : 'bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active'}`}
        >
          📋 Inscrições
        </button>
        <button
          onClick={() => onActivityFilterChange('evaluations')}
          className={`px-2 py-1 text-xs rounded-full transition-colors motion-reduce:transition-none ${activityFilter === 'evaluations' ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text font-semibold' : 'text-lia-text-secondary hover:dark:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-bg'}`}
        >
          🎯 Avaliações
        </button>
      </div>
    </div>
  )
}
