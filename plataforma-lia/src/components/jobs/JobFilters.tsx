"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Card } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  Search, Plus, MapPin, Users, Edit2, Share2,
  BarChart3, Target, CheckCircle, Linkedin, Globe,
  Building, UserCheck, AlertCircle, AlertTriangle,
  X, Bookmark, Trash2, Layers3, Briefcase, Filter, User
} from"lucide-react"
import { textStyles } from '@/lib/design-tokens'
import type { JobFilters as JobFiltersType, Job } from './jobsPageTypes'
import type { SavedSearch } from '@/stores/job-filters-store'
import { useDepartmentsList } from '@/hooks/settings/useDepartmentsList'
import { useCompanyRecruiters } from '@/hooks/company/use-company-recruiters'
import { useCompanyManagers } from '@/hooks/company/use-company-managers'

export interface JobFiltersProps {
  isOpen: boolean
  jobFilters: JobFiltersType
  savedSearches: SavedSearch[]
  toggleJobFilter: (category: keyof JobFiltersType, field: string, value: unknown) => void
  clearAllJobFilters: () => void
  hasActiveFilters: () => boolean
  getActiveJobFiltersCount: () => number
  handleApplySavedSearch: (id: string) => void
  handleRenameSavedSearch: (id: string, name: string) => void
  handleDeleteSavedSearch: (id: string) => void
  saveSearchAsTemplate: (name: string) => void
  /** Lista de vagas reais para derivar opções de Localização. Opcional —
   *  fallback = [] (seção Localização fica vazia mas não quebra). */
  allJobs?: Job[]
}

export function JobFiltersPanel({
  isOpen,
  jobFilters,
  savedSearches,
  toggleJobFilter,
  clearAllJobFilters,
  hasActiveFilters,
  getActiveJobFiltersCount,
  handleApplySavedSearch,
  handleRenameSavedSearch,
  handleDeleteSavedSearch,
  saveSearchAsTemplate,
  allJobs,
}: JobFiltersProps) {
  // ── Hooks SEMPRE no topo (Rules of Hooks) ──────────────────────────────────
  const { departments } = useDepartmentsList()
  const { recruiters } = useCompanyRecruiters()
  const { managers } = useCompanyManagers()

  // Derivar localizações distintas das vagas reais (RV-019)
  const locationOptions: string[] = React.useMemo(
    () => [...new Set((allJobs ?? []).map(j => j.location).filter(Boolean))].sort(),
    [allJobs],
  )

  // Early return APÓS todos os hooks
  if (!isOpen) return null

  return (
    <div className="w-72 flex-shrink-0 h-full">
      <Card className="h-full flex flex-col bg-lia-bg-primary overflow-hidden rounded-xl">
        <div className="flex-shrink-0 px-3 py-2 bg-lia-bg-secondary flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-lia-text-primary" />
            <h3 className="text-xs font-semibold text-lia-text-primary">Filtros de Vagas</h3>
          </div>
          {getActiveJobFiltersCount() > 0 && (
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center">
              {getActiveJobFiltersCount()}
            </Chip>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Bookmark className="w-3.5 h-3.5" />
              Filtros Rápidos
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => toggleJobFilter('status', 'statuses', 'Ativa')}
                className={`h-8 text-xs justify-start ${
                  jobFilters.status?.statuses?.includes('Ativa')
                    ? 'bg-lia-bg-tertiary border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary font-semibold'
                    : ''
                }`}
              >
                <CheckCircle className="w-3 h-3 mr-1.5" />
                Ativas
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => toggleJobFilter('status', 'priorities', 'alta')}
                className={`h-8 text-xs justify-start ${
                  jobFilters.status?.priorities?.includes('alta')
                    ? 'bg-status-error/10 border-status-error/30 text-status-error font-semibold'
                    : ''
                }`}
              >
                <AlertTriangle className="w-3 h-3 mr-1.5" />
                Urgentes
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => toggleJobFilter('position', 'workModels', 'remoto')}
                className={`h-8 text-xs justify-start ${
                  jobFilters.position?.workModels?.includes('remoto')
                    ? 'bg-lia-bg-secondary border-lia-btn-primary-bg dark:border-lia-border-subtle text-wedo-cyan-text font-semibold'
                    : ''
                }`}
              >
                <Globe className="w-3 h-3 mr-1.5" />
                Remotas
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => toggleJobFilter('funnel', 'emptyPipeline', true)}
                className={`h-8 text-xs justify-start ${
                  jobFilters.funnel?.emptyPipeline
                    ? 'bg-wedo-orange/10 border-wedo-orange/30 text-wedo-orange-text font-semibold'
                    : ''
                }`}
              >
                <Users className="w-3 h-3 mr-1.5" />
                Sem Candidatos
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5" />
              Status da Vaga
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Ativa', 'Rascunho', 'Paralisada', 'Aguardando aprovação', 'Fechada (preenchida)', 'Cancelada'].map(status => (
                <Chip
                  key={status}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                    jobFilters.status?.statuses?.includes(status)
                      ? 'bg-lia-bg-tertiary border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => toggleJobFilter('status', 'statuses', status)}
                >
                  {status}
                </Chip>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Layers3 className="w-3.5 h-3.5" />
              Etapa do Processo
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Planejamento', 'Aprovação', 'Publicada', 'Triagem', 'Entrevistas', 'Finalização', 'Encerrada'].map(stage => (
                <Chip
                  key={stage}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                    jobFilters.status?.stages?.includes(stage)
                      ? 'bg-wedo-purple/10 border-wedo-purple/30 text-wedo-purple-text font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => toggleJobFilter('status', 'stages', stage)}
                >
                  {stage}
                </Chip>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5" />
              Prioridade
            </h4>
            <div className="flex gap-2">
              {[
                { value: 'alta', label: 'Alta', color: 'bg-status-error/15 border-status-error/30 text-status-error' },
                { value: 'média', label: 'Média', color: 'bg-status-warning/15 border-status-warning/30 text-status-warning' },
                { value: 'baixa', label: 'Baixa', color: 'bg-status-success/15 border-status-success/30 text-status-success' }
              ].map(priority => (
                <Chip
                  key={priority.value}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none ${
                    jobFilters.status?.priorities?.includes(priority.value)
                      ? priority.color + ' font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => toggleJobFilter('status', 'priorities', priority.value)}
                >
                  {priority.label}
                </Chip>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Building className="w-3.5 h-3.5" />
              Modelo de Trabalho
            </h4>
            <div className="flex gap-2">
              {['presencial', 'híbrido', 'remoto'].map(model => (
                <Chip
                  key={model}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none capitalize ${
                    jobFilters.position?.workModels?.includes(model)
                      ? 'bg-lia-bg-tertiary border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => toggleJobFilter('position', 'workModels', model)}
                >
                  {model}
                </Chip>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <UserCheck className="w-3.5 h-3.5" />
              Senioridade
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Estágio', 'Júnior', 'Pleno', 'Sênior', 'Especialista', 'Coordenador', 'Gerente', 'Diretor'].map(level => (
                <Chip
                  key={level}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                    jobFilters.position?.levels?.includes(level)
                      ? 'bg-lia-bg-tertiary border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => toggleJobFilter('position', 'levels', level)}
                >
                  {level}
                </Chip>
              ))}
            </div>
          </div>

          {/* Localização — derivado das vagas reais (RV-019) */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5" />
              Localização
            </h4>
            {locationOptions.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {locationOptions.map(loc => (
                  <Chip
                    key={loc}
                    variant="neutral"
                    className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                      jobFilters.position?.locations?.includes(loc)
                        ? 'bg-lia-bg-tertiary border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary font-medium'
                        : 'bg-lia-bg-primary text-lia-text-primary'
                    }`}
                    onClick={() => toggleJobFilter('position', 'locations', loc)}
                  >
                    {loc}
                  </Chip>
                ))}
              </div>
            ) : (
              <p className="text-xs text-lia-text-tertiary">Nenhuma localização disponível</p>
            )}
          </div>

          {/* Sub-tarefa A: Departamento — fonte real via useDepartmentsList */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Briefcase className="w-3.5 h-3.5" />
              Departamento
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {departments.map(dept => (
                <Chip
                  key={dept.id}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                    jobFilters.team?.departments?.includes(dept.name)
                      ? 'bg-lia-bg-tertiary border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => toggleJobFilter('team', 'departments', dept.name)}
                >
                  {dept.name}
                </Chip>
              ))}
            </div>
          </div>

          {/* Sub-tarefa B: Recrutador — fonte real via useCompanyRecruiters */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5" />
              Recrutador
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {recruiters.map(recruiter => (
                <Chip
                  key={recruiter.id}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                    jobFilters.team?.recruiters?.includes(recruiter.name)
                      ? 'bg-lia-bg-tertiary border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => toggleJobFilter('team', 'recruiters', recruiter.name)}
                >
                  {recruiter.name}
                </Chip>
              ))}
            </div>
          </div>

          {/* Sub-tarefa B: Gestor — fonte real via useCompanyManagers */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <UserCheck className="w-3.5 h-3.5" />
              Gestor
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {managers.map(manager => (
                <Chip
                  key={manager.id}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                    jobFilters.team?.managers?.includes(manager.name)
                      ? 'bg-lia-bg-tertiary border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => toggleJobFilter('team', 'managers', manager.name)}
                >
                  {manager.name}
                </Chip>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <Share2 className="w-3.5 h-3.5" />
              Publicação
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {[
                { value: 'linkedin', label: 'LinkedIn', Icon: Linkedin },
                { value: 'website', label: 'Website', Icon: Globe },
                { value: 'indeed', label: 'Indeed', Icon: Briefcase }
              ].map(channel => (
                <Chip
                  key={channel.value}
                  variant="neutral"
                  className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none flex items-center gap-1 ${
                    jobFilters.publishing?.channels?.includes(channel.value)
                      ? 'bg-lia-bg-tertiary border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => toggleJobFilter('publishing', 'channels', channel.value)}
                >
                  <channel.Icon className="w-3 h-3" />
                  {channel.label}
                </Chip>
              ))}
              <Chip
                variant="neutral"
                className={`text-xs cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none ${
                  jobFilters.publishing?.unpublished
                    ? 'bg-wedo-orange/10 border-wedo-orange/30 text-wedo-orange-text font-medium'
                    : 'bg-lia-bg-primary text-lia-text-primary'
                }`}
                onClick={() => toggleJobFilter('publishing', 'unpublished', !jobFilters.publishing?.unpublished)}
              >
                Não Publicadas
              </Chip>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
              <BarChart3 className="w-3.5 h-3.5" />
              Métricas
            </h4>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs p-2 hover:bg-lia-interactive-hover rounded-xl bg-lia-bg-secondary">
                <input
                  type="checkbox"
                  className="w-3 h-3"
                  checked={jobFilters.funnel?.emptyPipeline || false}
                  onChange={(e) => toggleJobFilter('funnel', 'emptyPipeline', e.target.checked)}
                />
                <span className="text-lia-text-primary">Pipeline vazio (sem candidatos)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-xs p-2 hover:bg-lia-interactive-hover rounded-xl bg-lia-bg-secondary">
                <input
                  type="checkbox"
                  className="w-3 h-3"
                  checked={jobFilters.metrics?.lowConversion || false}
                  onChange={(e) => toggleJobFilter('metrics', 'lowConversion', e.target.checked)}
                />
                <span className="text-lia-text-primary">Baixa conversão</span>
              </label>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                <Search className="w-3.5 h-3.5" />
                Buscas Salvas
              </h4>
              {hasActiveFilters() && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    const name = prompt("Nome da busca:")
                    if (name) saveSearchAsTemplate(name)
                  }}
                  className="h-6 text-xs px-2 text-lia-text-secondary hover:text-lia-text-secondary/80"
                >
                  <Plus className="w-3 h-3 mr-1" />
                  Salvar Busca
                </Button>
              )}
            </div>
            {savedSearches.length > 0 ? (
              <div className="space-y-1.5 max-h-card-lg overflow-y-auto">
                {savedSearches.map((search) => (
                  <div
                    key={search.id}
                    className="group flex items-center justify-between p-2 bg-lia-bg-secondary rounded-xl hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none cursor-pointer"
                    onClick={() => handleApplySavedSearch(search.id)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <Search className="w-3 h-3 text-lia-text-secondary flex-shrink-0" />
                        <span className="text-xs font-medium text-lia-text-primary truncate">
                          {search.name}
                        </span>
                      </div>
                      <p className="text-micro text-lia-text-secondary mt-0.5 truncate">
                        {new Date(search.createdAt).toLocaleDateString('pt-BR')}
                        {search.query && ` -"${search.query}"`}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          const newName = prompt("Novo nome:", search.name)
                          if (newName) handleRenameSavedSearch(search.id, newName)
                        }}
                        className="h-6 w-6 p-0"
                        title="Renomear"
                      >
                        <Edit2 className="w-3 h-3 text-lia-text-secondary" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteSavedSearch(search.id)
                        }}
                        className="h-6 w-6 p-0"
                        title="Remover"
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
                <p className="text-xs text-lia-text-secondary">
                  Nenhuma busca salva
                </p>
                <p className="text-micro text-lia-text-secondary mt-0.5">
                  Aplique filtros e clique em"Salvar Busca"
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="flex-shrink-0 p-3 border-t border-lia-border-subtle bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>
              {getActiveJobFiltersCount() > 0
                ? `${getActiveJobFiltersCount()} filtro${getActiveJobFiltersCount() > 1 ? 's' : ''}`
                : 'Nenhum filtro'}
            </span>
            {getActiveJobFiltersCount() > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAllJobFilters}
                className="h-7 text-xs text-lia-text-primary hover:text-lia-text-primary"
              >
                <X className="w-3 h-3 mr-1" />
                Limpar
              </Button>
            )}
          </div>
        </div>
      </Card>
    </div>
  )
}
