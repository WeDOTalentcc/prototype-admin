"use client"

import { memo } from 'react'
import { useTranslations, useLocale } from 'next-intl'

import {
  Target, X, Search, Zap, CheckCircle, Globe, Users,
  Building, MapPin, Briefcase, Share2, BarChart3, Bookmark,
  Plus, Trash2, AlertCircle, UserCheck
} from"lucide-react"
import { Linkedin } from"lucide-react"
import { Edit2 } from"lucide-react"
import { AlertTriangle } from"lucide-react"
import { Layers3 } from"lucide-react"
import { Card } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { textStyles } from"@/lib/design-tokens"
import { useDepartmentsList } from '@/hooks/settings/useDepartmentsList'
import type { Job } from '@/components/jobs'

interface SavedSearch {
  id: string
  name: string
  query?: string
  createdAt: Date | string
}

interface JobFilters {
  status?: { statuses?: string[]; stages?: string[]; priorities?: string[] }
  position?: { workModels?: string[]; levels?: string[]; locations?: string[] }
  team?: { departments?: string[] }
  publishing?: { channels?: string[]; unpublished?: boolean }
  funnel?: { emptyPipeline?: boolean }
  metrics?: { lowConversion?: boolean }
}

interface TableFiltersPanelProps {
  isOpen: boolean
  onClose: () => void
  searchTerm: string
  onSearchTermChange: (value: string) => void
  jobFilters: JobFilters
  onToggleFilter: (category: string, key: string, value: unknown) => void
  onClearAllFilters: () => void
  getActiveFiltersCount: () => number
  hasActiveFilters: () => boolean
  savedSearches: SavedSearch[]
  onSaveSearch: (name: string) => void
  onApplySavedSearch: (id: string) => void
  onRenameSavedSearch: (id: string, name: string) => void
  onDeleteSavedSearch: (id: string) => void
  /** Lista de vagas reais usada para derivar opções de Localização. Opcional
   *  para não quebrar callers legados — fallback = [] (sem chips). */
  allJobs?: Job[]
}

const TableFiltersPanel = memo(function TableFiltersPanel({
  isOpen,
  onClose,
  searchTerm,
  onSearchTermChange,
  jobFilters,
  onToggleFilter,
  onClearAllFilters,
  getActiveFiltersCount,
  hasActiveFilters,
  savedSearches,
  onSaveSearch,
  onApplySavedSearch,
  onRenameSavedSearch,
  onDeleteSavedSearch,
  allJobs,
}: TableFiltersPanelProps) {
  const tf = useTranslations('jobs.tableFilters')
  const locale = useLocale()
  const { departments } = useDepartmentsList()

  // Derivar localizações distintas das vagas reais (RV-019)
  const locationOptions: string[] = [
    ...new Set((allJobs ?? []).map(j => j.location).filter(Boolean)),
  ].sort()

  const statusLabels: Record<string, string> = {
    'Ativa': tf('statusValues.Ativa'),
    'Rascunho': tf('statusValues.Rascunho'),
    'Paralisada': tf('statusValues.Paralisada'),
    'Aguardando aprovação': tf('statusValues.Aguardando aprovação'),
    'Fechada (preenchida)': tf('statusValues.Fechada (preenchida)'),
    'Cancelada': tf('statusValues.Cancelada'),
  }
  const stageLabels: Record<string, string> = {
    'Planejamento': tf('stageValues.Planejamento'),
    'Aprovação': tf('stageValues.Aprovação'),
    'Publicada': tf('stageValues.Publicada'),
    'Triagem': tf('stageValues.Triagem'),
    'Entrevistas': tf('stageValues.Entrevistas'),
    'Finalização': tf('stageValues.Finalização'),
    'Encerrada': tf('stageValues.Encerrada'),
  }
  const workModelLabels: Record<string, string> = {
    'presencial': tf('workModelValues.presencial'),
    'híbrido': tf('workModelValues.híbrido'),
    'remoto': tf('workModelValues.remoto'),
  }
  const seniorityLabels: Record<string, string> = {
    'Estágio': tf('seniorityValues.Estágio'),
    'Júnior': tf('seniorityValues.Júnior'),
    'Pleno': tf('seniorityValues.Pleno'),
    'Sênior': tf('seniorityValues.Sênior'),
    'Especialista': tf('seniorityValues.Especialista'),
    'Coordenador': tf('seniorityValues.Coordenador'),
    'Gerente': tf('seniorityValues.Gerente'),
    'Diretor': tf('seniorityValues.Diretor'),
  }
  const pubLabels: Record<string, string> = {
    'linkedin': tf('publishingValues.linkedin'),
    'website': tf('publishingValues.website'),
    'indeed': tf('publishingValues.indeed'),
  }

  if (!isOpen) return null

  const activeCount = getActiveFiltersCount()

  return (
    <div className="w-80 flex-shrink-0 transition-colors motion-reduce:transition-none duration-300" data-testid="table-filters-panel">
      <Card className="h-full max-h-[calc(100vh-180px)] flex flex-col overflow-hidden bg-lia-bg-primary border border-lia-border-subtle">
        {/* Header */}
        <div className="flex-shrink-0 p-4 border-b border-b-lia-border-subtle bg-lia-bg-secondary">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-lia-text-secondary" />
              <div>
                <h3 className="text-sm font-semibold text-lia-text-primary">
                  {tf('advancedFilters')}
                </h3>
                <p className={textStyles.bodySmall}>
                  {activeCount > 0
                    ? tf('activeFiltersCount', { count: activeCount })
                    : tf('refineResults')}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-7 w-7 p-0 rounded-full hover:opacity-70 transition-opacity motion-reduce:transition-none"
            >
              <X className="w-4 h-4 text-lia-text-primary" />
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="flex-shrink-0 px-4 py-3 border-b border-b-lia-border-subtle">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-primary" />
            <input
              type="text"
              placeholder={tf('searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => onSearchTermChange(e.target.value)}
              className="w-full pl-9 pr-8 py-2 text-xs rounded-xl border focus:outline-none focus:border-lia-text-primary transition-colors motion-reduce:transition-none border border-lia-border-subtle bg-lia-bg-secondary"
            />
            {searchTerm && (
              <button
                onClick={() => onSearchTermChange('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-lia-text-primary hover:text-lia-text-primary"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Filters - scrollable */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">

          {/* Quick Filters */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-lia-text-secondary" />
              {tf('quickFilters')}
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onToggleFilter('status', 'statuses', 'Ativa')}
                className={`h-8 text-xs justify-start ${jobFilters.status?.statuses?.includes('Ativa') ? 'bg-lia-bg-tertiary border-lia-text-primary text-lia-text-primary font-semibold dark:bg-lia-bg-secondary' : ''}`}
              >
                <CheckCircle className="w-3 h-3 mr-1.5" />
                {tf('active')}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onToggleFilter('status', 'priorities', 'alta')}
                className={`h-8 text-xs justify-start ${jobFilters.status?.priorities?.includes('alta') ? 'bg-status-error/10 border-status-error/30 text-status-error font-semibold' : ''}`}
              >
                <AlertTriangle className="w-3 h-3 mr-1.5" />
                {tf('urgent')}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onToggleFilter('position', 'workModels', 'remoto')}
                className={`h-8 text-xs justify-start ${jobFilters.position?.workModels?.includes('remoto') ? 'bg-lia-bg-tertiary border-lia-text-primary text-lia-text-primary font-semibold' : ''}`}
              >
                <Globe className="w-3 h-3 mr-1.5" />
                {tf('remote')}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onToggleFilter('funnel', 'emptyPipeline', true)}
                className={`h-8 text-xs justify-start ${jobFilters.funnel?.emptyPipeline ? 'bg-lia-bg-tertiary border-lia-border-subtle text-lia-text-secondary font-semibold' : ''}`}
              >
                <Users className="w-3 h-3 mr-1.5" />
                {tf('noCandidates')}
              </Button>
            </div>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5" />
              {tf('jobStatus')}
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Ativa', 'Rascunho', 'Paralisada', 'Aguardando aprovação', 'Fechada (preenchida)', 'Cancelada'].map(status => (
                <Chip
                  key={status}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                    jobFilters.status?.statuses?.includes(status)
                      ? 'bg-lia-bg-tertiary border-lia-text-primary text-lia-text-primary font-medium dark:bg-lia-bg-secondary'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('status', 'statuses', status)}
                >
                  {statusLabels[status] || status}
                </Chip>
              ))}
            </div>
          </div>

          {/* Process Stage */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Layers3 className="w-3.5 h-3.5" />
              {tf('processStage')}
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Planejamento', 'Aprovação', 'Publicada', 'Triagem', 'Entrevistas', 'Finalização', 'Encerrada'].map(stage => (
                <Chip
                  key={stage}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                    jobFilters.status?.stages?.includes(stage)
                      ? 'bg-lia-bg-tertiary border-lia-border-subtle text-lia-text-secondary font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('status', 'stages', stage)}
                >
                  {stageLabels[stage] || stage}
                </Chip>
              ))}
            </div>
          </div>

          {/* Priority */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5" />
              {tf('priority')}
            </h4>
            <div className="flex gap-2">
              {[
                { value: 'alta', label: tf('high'), color: 'bg-status-error/15 border-status-error/30 text-status-error' },
                { value: 'média', label: tf('medium'), color: 'bg-status-warning/15 border-status-warning/30 text-status-warning' },
                { value: 'baixa', label: tf('low'), color: 'bg-status-success/15 border-status-success/30 text-status-success' },
              ].map(priority => (
                <Chip
                  key={priority.value}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none ${
                    jobFilters.status?.priorities?.includes(priority.value)
                      ? priority.color + ' font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('status', 'priorities', priority.value)}
                >
                  {priority.label}
                </Chip>
              ))}
            </div>
          </div>

          {/* Work Model */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Building className="w-3.5 h-3.5" />
              {tf('workModel')}
            </h4>
            <div className="flex gap-2">
              {['presencial', 'híbrido', 'remoto'].map(model => (
                <Chip
                  key={model}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                    jobFilters.position?.workModels?.includes(model)
                      ? 'bg-lia-bg-tertiary border-lia-text-primary text-lia-text-primary font-medium dark:bg-lia-bg-secondary'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('position', 'workModels', model)}
                >
                  {workModelLabels[model] || model}
                </Chip>
              ))}
            </div>
          </div>

          {/* Seniority */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <UserCheck className="w-3.5 h-3.5" />
              {tf('seniority')}
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Estágio', 'Júnior', 'Pleno', 'Sênior', 'Especialista', 'Coordenador', 'Gerente', 'Diretor'].map(level => (
                <Chip
                  key={level}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                    jobFilters.position?.levels?.includes(level)
                      ? 'bg-lia-bg-tertiary border-lia-text-primary text-lia-text-primary font-medium dark:bg-lia-bg-secondary'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('position', 'levels', level)}
                >
                  {seniorityLabels[level] || level}
                </Chip>
              ))}
            </div>
          </div>

          {/* Location — derivado das vagas reais (RV-019) */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5" />
              {tf('location')}
            </h4>
            {locationOptions.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {locationOptions.map(loc => (
                  <Chip
                    key={loc}
                    variant="neutral"
                    className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                      jobFilters.position?.locations?.includes(loc)
                        ? 'bg-lia-bg-tertiary border-lia-text-primary text-lia-text-primary font-medium dark:bg-lia-bg-secondary'
                        : 'bg-lia-bg-primary text-lia-text-primary'
                    }`}
                    onClick={() => onToggleFilter('position', 'locations', loc)}
                  >
                    {loc}
                  </Chip>
                ))}
              </div>
            ) : (
              <p className="text-xs text-lia-text-tertiary">{tf('noLocationsAvailable', { defaultValue: 'Nenhuma localização disponível' })}</p>
            )}
          </div>

          {/* Department */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Briefcase className="w-3.5 h-3.5" />
              {tf('department')}
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {departments.map(dept => (
                <Chip
                  key={dept.id}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                    jobFilters.team?.departments?.includes(dept.name)
                      ? 'bg-lia-bg-tertiary border-lia-text-primary text-lia-text-primary font-medium dark:bg-lia-bg-secondary'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('team', 'departments', dept.name)}
                >
                  {dept.name}
                </Chip>
              ))}
            </div>
          </div>

          {/* Publishing */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Share2 className="w-3.5 h-3.5" />
              {tf('publishing')}
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {[
                { value: 'linkedin', Icon: Linkedin },
                { value: 'website', Icon: Globe },
                { value: 'indeed', Icon: Briefcase },
              ].map(channel => (
                <Chip
                  key={channel.value}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none flex items-center gap-1 ${
                    jobFilters.publishing?.channels?.includes(channel.value)
                      ? 'bg-lia-bg-tertiary border-lia-text-primary text-lia-text-primary font-medium dark:bg-lia-bg-secondary'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('publishing', 'channels', channel.value)}
                >
                  <channel.Icon className="w-3 h-3" />
                  {pubLabels[channel.value] || channel.value}
                </Chip>
              ))}
              <Chip
                variant="neutral"
                className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                  jobFilters.publishing?.unpublished
                    ? 'bg-lia-bg-tertiary border-lia-border-subtle text-lia-text-secondary font-medium'
                    : 'bg-lia-bg-primary text-lia-text-primary'
                }`}
                onClick={() => onToggleFilter('publishing', 'unpublished', !jobFilters.publishing?.unpublished)}
              >
                {tf('unpublished')}
              </Chip>
            </div>
          </div>

          {/* Metrics */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <BarChart3 className="w-3.5 h-3.5" />
              {tf('metrics')}
            </h4>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs p-2 hover:bg-lia-interactive-hover rounded-xl bg-lia-bg-secondary">
                <input
                  type="checkbox"
                  className="w-3 h-3"
                  checked={jobFilters.funnel?.emptyPipeline || false}
                  onChange={(e) => onToggleFilter('funnel', 'emptyPipeline', e.target.checked)}
                />
                <span className="text-lia-text-secondary">{tf('emptyPipeline')}</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-xs p-2 hover:bg-lia-interactive-hover rounded-xl bg-lia-bg-secondary">
                <input
                  type="checkbox"
                  className="w-3 h-3"
                  checked={jobFilters.metrics?.lowConversion || false}
                  onChange={(e) => onToggleFilter('metrics', 'lowConversion', e.target.checked)}
                />
                <span className="text-lia-text-secondary">{tf('lowConversion')}</span>
              </label>
            </div>
          </div>

          {/* Saved Searches */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                <Bookmark className="w-3.5 h-3.5" />
                {tf('savedSearches')}
              </h4>
              {hasActiveFilters() && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    const name = prompt(tf('searchNamePrompt'))
                    if (name) onSaveSearch(name)
                  }}
                  className="h-6 text-xs px-2 text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
                >
                  <Plus className="w-3 h-3 mr-1" />
                  {tf('saveSearch')}
                </Button>
              )}
            </div>
            {savedSearches.length > 0 ? (
              <div className="space-y-1.5 max-h-card-lg overflow-y-auto">
                {savedSearches.map((search) => (
                  <div
                    key={search.id}
                    className="group flex items-center justify-between p-2 bg-lia-bg-secondary rounded-xl hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none cursor-pointer"
                    onClick={() => onApplySavedSearch(search.id)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <Search className="w-3 h-3 text-lia-text-secondary flex-shrink-0" />
                        <span className="text-xs font-medium text-lia-text-primary truncate">
                          {search.name}
                        </span>
                      </div>
                      <p className="text-micro text-lia-text-secondary mt-0.5 truncate">
                        {new Date(search.createdAt).toLocaleDateString(locale)}
                        {search.query && ` -"${search.query}"`}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          const newName = prompt(tf('renamePrompt'), search.name)
                          if (newName) onRenameSavedSearch(search.id, newName)
                        }}
                        className="h-6 w-6 p-0"
                        title={tf('rename')}
                      >
                        <Edit2 className="w-3 h-3 text-lia-text-secondary" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          onDeleteSavedSearch(search.id)
                        }}
                        className="h-6 w-6 p-0"
                        title={tf('remove')}
                      >
                        <Trash2 className="w-3 h-3 text-status-error" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-3 bg-lia-bg-secondary rounded-xl">
                <Bookmark className="w-5 h-5 text-lia-text-secondary mx-auto mb-1" />
                <p className="text-xs text-lia-text-tertiary">{tf('noSavedSearches')}</p>
                <p className="text-micro text-lia-text-secondary mt-0.5">{tf('noSavedSearchesHint')}</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 p-3 border-t border-lia-border-subtle bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>
              {tf('filterCount', { count: activeCount })}
            </span>
            {activeCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClearAllFilters}
                className="h-7 text-xs text-lia-text-primary hover:text-lia-text-primary"
              >
                <X className="w-3 h-3 mr-1" />
                {tf('clear')}
              </Button>
            )}
          </div>
        </div>
      </Card>
    </div>
  )
})
TableFiltersPanel.displayName = 'TableFiltersPanel'

export { TableFiltersPanel }
