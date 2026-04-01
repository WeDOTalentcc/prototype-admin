"use client"

import { memo } from 'react'

import {
  Target, X, Search, Zap, CheckCircle, Globe, Users,
  Building, MapPin, Briefcase, Share2, BarChart3, Bookmark,
  Plus, Trash2, AlertCircle, UserCheck
} from "lucide-react"
import { Linkedin } from "lucide-react"
import { Edit2 } from "lucide-react"
import { AlertTriangle } from "lucide-react"
import { Layers3 } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { textStyles } from "@/lib/design-tokens"

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
}: TableFiltersPanelProps) {
  if (!isOpen) return null

  const activeCount = getActiveFiltersCount()

  return (
    <div className="w-80 flex-shrink-0 transition-colors motion-reduce:transition-none duration-300">
      <Card className="h-full max-h-[calc(100vh-180px)] flex flex-col overflow-hidden bg-white dark:bg-lia-bg-primary border border-lia-border-subtle">
        {/* Header */}
        <div className="flex-shrink-0 p-4 border-b border-b-gray-100 bg-gray-50 dark:bg-lia-bg-secondary/50">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-lia-text-secondary" />
              <div>
                <h3 className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary">
                  Filtros Avançados
                </h3>
                <p className={textStyles.bodySmall}>
                  {activeCount > 0
                    ? `${activeCount} filtro${activeCount > 1 ? 's' : ''} ativo${activeCount > 1 ? 's' : ''}`
                    : 'Refine os resultados exibidos'}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-7 w-7 p-0 rounded-full hover:opacity-70 transition-opacity motion-reduce:transition-none"
            >
              <X className="w-4 h-4 text-lia-text-primary dark:text-lia-text-primary" />
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="flex-shrink-0 px-4 py-3 border-b border-b-gray-100">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-primary" />
            <input
              type="text"
              placeholder="Buscar por título, ID, departamento..."
              value={searchTerm}
              onChange={(e) => onSearchTermChange(e.target.value)}
              className="w-full pl-9 pr-8 py-2 text-xs rounded-md border focus:outline-none focus:border-gray-900 transition-colors motion-reduce:transition-none border border-lia-border-subtle bg-white dark:bg-lia-bg-secondary"
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

          {/* Filtros Rápidos */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-lia-text-secondary" />
              Filtros Rápidos
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onToggleFilter('status', 'statuses', 'Ativa')}
                className={`h-8 text-xs justify-start ${jobFilters.status?.statuses?.includes('Ativa') ? 'bg-gray-100 border-gray-900 text-lia-text-primary font-semibold dark:bg-lia-bg-secondary dark:border-lia-border-default dark:text-lia-text-primary' : ''}`}
              >
                <CheckCircle className="w-3 h-3 mr-1.5" />
                Ativas
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onToggleFilter('status', 'priorities', 'alta')}
                className={`h-8 text-xs justify-start ${jobFilters.status?.priorities?.includes('alta') ? 'bg-status-error/10 border-status-error/30 text-status-error font-semibold' : ''}`}
              >
                <AlertTriangle className="w-3 h-3 mr-1.5" />
                Urgentes
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onToggleFilter('position', 'workModels', 'remoto')}
                className={`h-8 text-xs justify-start ${jobFilters.position?.workModels?.includes('remoto') ? 'bg-gray-100 border-gray-900 text-lia-text-primary font-semibold' : ''}`}
              >
                <Globe className="w-3 h-3 mr-1.5" />
                Remotas
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onToggleFilter('funnel', 'emptyPipeline', true)}
                className={`h-8 text-xs justify-start ${jobFilters.funnel?.emptyPipeline ? 'bg-gray-100 dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-secondary dark:text-lia-text-secondary font-semibold' : ''}`}
              >
                <Users className="w-3 h-3 mr-1.5" />
                Sem Candidatos
              </Button>
            </div>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5" />
              Status da Vaga
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Ativa', 'Rascunho', 'Paralisada', 'Aguardando aprovação', 'Fechada (preenchida)', 'Cancelada'].map(status => (
                <Badge
                  key={status}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors motion-reduce:transition-none ${
                    jobFilters.status?.statuses?.includes(status)
                      ? 'bg-gray-100 border-gray-900 text-lia-text-primary font-medium dark:bg-lia-bg-secondary dark:border-lia-border-default dark:text-lia-text-primary'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('status', 'statuses', status)}
                >
                  {status}
                </Badge>
              ))}
            </div>
          </div>

          {/* Etapa do Processo */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
              <Layers3 className="w-3.5 h-3.5" />
              Etapa do Processo
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Planejamento', 'Aprovação', 'Publicada', 'Triagem', 'Entrevistas', 'Finalização', 'Encerrada'].map(stage => (
                <Badge
                  key={stage}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors motion-reduce:transition-none ${
                    jobFilters.status?.stages?.includes(stage)
                      ? 'bg-gray-100 dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-secondary dark:text-lia-text-secondary font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('status', 'stages', stage)}
                >
                  {stage}
                </Badge>
              ))}
            </div>
          </div>

          {/* Prioridade */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5" />
              Prioridade
            </h4>
            <div className="flex gap-2">
              {[
                { value: 'alta', label: 'Alta', color: 'bg-status-error/15 border-status-error/30 text-status-error' },
                { value: 'média', label: 'Média', color: 'bg-status-warning/15 border-status-warning/30 text-status-warning' },
                { value: 'baixa', label: 'Baixa', color: 'bg-status-success/15 border-status-success/30 text-status-success' },
              ].map(priority => (
                <Badge
                  key={priority.value}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none ${
                    jobFilters.status?.priorities?.includes(priority.value)
                      ? priority.color + ' font-medium'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('status', 'priorities', priority.value)}
                >
                  {priority.label}
                </Badge>
              ))}
            </div>
          </div>

          {/* Modelo de Trabalho */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
              <Building className="w-3.5 h-3.5" />
              Modelo de Trabalho
            </h4>
            <div className="flex gap-2">
              {['presencial', 'híbrido', 'remoto'].map(model => (
                <Badge
                  key={model}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors motion-reduce:transition-none capitalize ${
                    jobFilters.position?.workModels?.includes(model)
                      ? 'bg-gray-100 border-gray-900 text-lia-text-primary font-medium dark:bg-lia-bg-secondary dark:border-lia-border-default dark:text-lia-text-primary'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('position', 'workModels', model)}
                >
                  {model}
                </Badge>
              ))}
            </div>
          </div>

          {/* Senioridade */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
              <UserCheck className="w-3.5 h-3.5" />
              Senioridade
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Estágio', 'Júnior', 'Pleno', 'Sênior', 'Especialista', 'Coordenador', 'Gerente', 'Diretor'].map(level => (
                <Badge
                  key={level}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors motion-reduce:transition-none ${
                    jobFilters.position?.levels?.includes(level)
                      ? 'bg-gray-100 border-gray-900 text-lia-text-primary font-medium dark:bg-lia-bg-secondary dark:border-lia-border-default dark:text-lia-text-primary'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('position', 'levels', level)}
                >
                  {level}
                </Badge>
              ))}
            </div>
          </div>

          {/* Localização */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5" />
              Localização
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['São Paulo, SP', 'Rio de Janeiro, RJ', 'Belo Horizonte, MG', 'Curitiba, PR', 'Porto Alegre, RS', 'Brasília, DF', 'Remoto'].map(loc => (
                <Badge
                  key={loc}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors motion-reduce:transition-none ${
                    jobFilters.position?.locations?.includes(loc)
                      ? 'bg-gray-100 border-gray-900 text-lia-text-primary font-medium dark:bg-lia-bg-secondary dark:border-lia-border-default dark:text-lia-text-primary'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('position', 'locations', loc)}
                >
                  {loc}
                </Badge>
              ))}
            </div>
          </div>

          {/* Departamento */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
              <Briefcase className="w-3.5 h-3.5" />
              Departamento
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Tecnologia', 'Design', 'Produto', 'Marketing', 'Vendas', 'RH', 'Financeiro', 'Operações'].map(dept => (
                <Badge
                  key={dept}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors motion-reduce:transition-none ${
                    jobFilters.team?.departments?.includes(dept)
                      ? 'bg-gray-100 border-gray-900 text-lia-text-primary font-medium dark:bg-lia-bg-secondary dark:border-lia-border-default dark:text-lia-text-primary'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('team', 'departments', dept)}
                >
                  {dept}
                </Badge>
              ))}
            </div>
          </div>

          {/* Publicação */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
              <Share2 className="w-3.5 h-3.5" />
              Publicação
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {[
                { value: 'linkedin', label: 'LinkedIn', Icon: Linkedin },
                { value: 'website', label: 'Website', Icon: Globe },
                { value: 'indeed', label: 'Indeed', Icon: Briefcase },
              ].map(channel => (
                <Badge
                  key={channel.value}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors motion-reduce:transition-none flex items-center gap-1 ${
                    jobFilters.publishing?.channels?.includes(channel.value)
                      ? 'bg-gray-100 border-gray-900 text-lia-text-primary font-medium dark:bg-lia-bg-secondary dark:border-lia-border-default dark:text-lia-text-primary'
                      : 'bg-lia-bg-primary text-lia-text-primary'
                  }`}
                  onClick={() => onToggleFilter('publishing', 'channels', channel.value)}
                >
                  <channel.Icon className="w-3 h-3" />
                  {channel.label}
                </Badge>
              ))}
              <Badge
                variant="outline"
                className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors motion-reduce:transition-none ${
                  jobFilters.publishing?.unpublished
                    ? 'bg-gray-100 dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-secondary dark:text-lia-text-secondary font-medium'
                    : 'bg-lia-bg-primary text-lia-text-primary'
                }`}
                onClick={() => onToggleFilter('publishing', 'unpublished', !jobFilters.publishing?.unpublished)}
              >
                Não Publicadas
              </Badge>
            </div>
          </div>

          {/* Métricas */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
              <BarChart3 className="w-3.5 h-3.5" />
              Métricas
            </h4>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md bg-gray-50">
                <input
                  type="checkbox"
                  className="w-3 h-3"
                  checked={jobFilters.funnel?.emptyPipeline || false}
                  onChange={(e) => onToggleFilter('funnel', 'emptyPipeline', e.target.checked)}
                />
                <span className="text-lia-text-secondary">Pipeline vazio (sem candidatos)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-xs p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md bg-gray-50">
                <input
                  type="checkbox"
                  className="w-3 h-3"
                  checked={jobFilters.metrics?.lowConversion || false}
                  onChange={(e) => onToggleFilter('metrics', 'lowConversion', e.target.checked)}
                />
                <span className="text-lia-text-secondary">Baixa conversão</span>
              </label>
            </div>
          </div>

          {/* Buscas Salvas */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
                <Bookmark className="w-3.5 h-3.5" />
                Buscas Salvas
              </h4>
              {hasActiveFilters() && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    const name = prompt("Nome da busca:")
                    if (name) onSaveSearch(name)
                  }}
                  className="h-6 text-xs px-2 text-lia-text-secondary hover:text-lia-text-primary dark:text-lia-text-secondary dark:hover:text-lia-text-inverse"
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
                    className="group flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors motion-reduce:transition-none cursor-pointer"
                    onClick={() => onApplySavedSearch(search.id)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <Search className="w-3 h-3 text-lia-text-secondary flex-shrink-0" />
                        <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary truncate">
                          {search.name}
                        </span>
                      </div>
                      <p className="text-micro text-lia-text-secondary mt-0.5 truncate">
                        {new Date(search.createdAt).toLocaleDateString('pt-BR')}
                        {search.query && ` - "${search.query}"`}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          const newName = prompt("Novo nome:", search.name)
                          if (newName) onRenameSavedSearch(search.id, newName)
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
                          onDeleteSavedSearch(search.id)
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
              <div className="text-center py-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                <Bookmark className="w-5 h-5 text-lia-text-secondary mx-auto mb-1" />
                <p className="text-xs text-lia-text-tertiary">Nenhuma busca salva</p>
                <p className="text-micro text-lia-text-secondary mt-0.5">Aplique filtros e clique em "Salvar Busca"</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 p-3 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>
              {activeCount > 0 ? `${activeCount} filtro${activeCount > 1 ? 's' : ''}` : 'Nenhum filtro'}
            </span>
            {activeCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClearAllFilters}
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
})
TableFiltersPanel.displayName = 'TableFiltersPanel'

export { TableFiltersPanel }
