"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { 
  Search, Plus, MapPin, Users, Edit2, Share2, 
  BarChart3, Target, CheckCircle, Linkedin, Globe, 
  Building, UserCheck, AlertCircle, AlertTriangle, 
  X, Bookmark, Trash2, Layers3, Briefcase, Filter, User
} from "lucide-react"
import { textStyles } from '@/lib/design-tokens'
import type { JobFilters as JobFiltersType } from './jobsPageTypes'
import type { SavedSearch } from '@/hooks/useJobFiltersPersistence'

export interface JobFiltersProps {
  isOpen: boolean
  jobFilters: JobFiltersType
  savedSearches: SavedSearch[]
  toggleJobFilter: (category: keyof JobFiltersType, field: string, value: any) => void
  clearAllJobFilters: () => void
  hasActiveFilters: () => boolean
  getActiveJobFiltersCount: () => number
  handleApplySavedSearch: (id: string) => void
  handleRenameSavedSearch: (id: string, name: string) => void
  handleDeleteSavedSearch: (id: string) => void
  saveSearchAsTemplate: (name: string) => void
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
  saveSearchAsTemplate
}: JobFiltersProps) {
  if (!isOpen) return null

  return (
    <div className="w-72 flex-shrink-0 h-full">
      <Card className="h-full flex flex-col bg-white dark:bg-gray-900 overflow-hidden rounded-md dark:border-gray-700">
        <div className="flex-shrink-0 px-3 py-2 bg-gray-50 dark:bg-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-800 dark:text-gray-200" />
            <h3 className="text-xs font-semibold text-gray-950 dark:text-gray-50">Filtros de Vagas</h3>
          </div>
          {getActiveJobFiltersCount() > 0 && (
            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-900 dark:bg-gray-50 text-white">
              {getActiveJobFiltersCount()}
            </Badge>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
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
                    ? 'bg-gray-100 dark:bg-gray-800 border-gray-900 dark:border-gray-50 text-gray-950 font-semibold' 
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
                    ? 'bg-red-50 border-red-300 text-red-700 font-semibold' 
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
                    ? 'bg-gray-50 dark:bg-gray-900 border-gray-900 dark:border-gray-50 text-wedo-cyan-dark font-semibold' 
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
                    ? 'bg-orange-50 border-orange-300 text-orange-700 font-semibold' 
                    : ''
                }`}
              >
                <Users className="w-3 h-3 mr-1.5" />
                Sem Candidatos
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5" />
              Status da Vaga
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Ativa', 'Rascunho', 'Paralisada', 'Aguardando aprovação', 'Fechada (preenchida)', 'Cancelada'].map(status => (
                <Badge
                  key={status}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                    jobFilters.status?.statuses?.includes(status)
                      ? 'bg-gray-100 dark:bg-gray-800 border-gray-900 dark:border-gray-50 text-gray-950 dark:text-gray-50 font-medium'
                      : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                  }`}
                  onClick={() => toggleJobFilter('status', 'statuses', status)}
                >
                  {status}
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
              <Layers3 className="w-3.5 h-3.5" />
              Etapa do Processo
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Planejamento', 'Aprovação', 'Publicada', 'Triagem', 'Entrevistas', 'Finalização', 'Encerrada'].map(stage => (
                <Badge
                  key={stage}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                    jobFilters.status?.stages?.includes(stage)
                      ? 'bg-purple-50 border-purple-300 text-purple-700 font-medium'
                      : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                  }`}
                  onClick={() => toggleJobFilter('status', 'stages', stage)}
                >
                  {stage}
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5" />
              Prioridade
            </h4>
            <div className="flex gap-2">
              {[
                { value: 'alta', label: 'Alta', color: 'bg-red-100 border-red-300 text-red-700' },
                { value: 'média', label: 'Média', color: 'bg-yellow-100 border-yellow-300 text-yellow-700' },
                { value: 'baixa', label: 'Baixa', color: 'bg-green-100 border-green-300 text-green-700' }
              ].map(priority => (
                <Badge
                  key={priority.value}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:opacity-80 transition-opacity ${
                    jobFilters.status?.priorities?.includes(priority.value)
                      ? priority.color + ' font-medium'
                      : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                  }`}
                  onClick={() => toggleJobFilter('status', 'priorities', priority.value)}
                >
                  {priority.label}
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
              <Building className="w-3.5 h-3.5" />
              Modelo de Trabalho
            </h4>
            <div className="flex gap-2">
              {['presencial', 'híbrido', 'remoto'].map(model => (
                <Badge
                  key={model}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors capitalize ${
                    jobFilters.position?.workModels?.includes(model)
                      ? 'bg-gray-100 dark:bg-gray-800 border-gray-900 dark:border-gray-50 text-gray-950 dark:text-gray-50 font-medium'
                      : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                  }`}
                  onClick={() => toggleJobFilter('position', 'workModels', model)}
                >
                  {model}
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
              <UserCheck className="w-3.5 h-3.5" />
              Senioridade
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Estágio', 'Júnior', 'Pleno', 'Sênior', 'Especialista', 'Coordenador', 'Gerente', 'Diretor'].map(level => (
                <Badge
                  key={level}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                    jobFilters.position?.levels?.includes(level)
                      ? 'bg-gray-100 dark:bg-gray-800 border-gray-900 dark:border-gray-50 text-gray-950 dark:text-gray-50 font-medium'
                      : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                  }`}
                  onClick={() => toggleJobFilter('position', 'levels', level)}
                >
                  {level}
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5" />
              Localização
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['São Paulo, SP', 'Rio de Janeiro, RJ', 'Belo Horizonte, MG', 'Curitiba, PR', 'Porto Alegre, RS', 'Brasília, DF', 'Remoto'].map(loc => (
                <Badge
                  key={loc}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                    jobFilters.position?.locations?.includes(loc)
                      ? 'bg-gray-100 dark:bg-gray-800 border-gray-900 dark:border-gray-50 text-gray-950 dark:text-gray-50 font-medium'
                      : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                  }`}
                  onClick={() => toggleJobFilter('position', 'locations', loc)}
                >
                  {loc}
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
              <Briefcase className="w-3.5 h-3.5" />
              Departamento
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Tecnologia', 'Design', 'Produto', 'Marketing', 'Vendas', 'RH', 'Financeiro', 'Operações'].map(dept => (
                <Badge
                  key={dept}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                    jobFilters.team?.departments?.includes(dept)
                      ? 'bg-gray-100 dark:bg-gray-800 border-gray-900 dark:border-gray-50 text-gray-950 dark:text-gray-50 font-medium'
                      : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                  }`}
                  onClick={() => toggleJobFilter('team', 'departments', dept)}
                >
                  {dept}
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5" />
              Recrutador
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Ana Paula Santos', 'Carlos Eduardo Silva', 'Marina Costa Oliveira', 'Demo Recrutador'].map(recruiter => (
                <Badge
                  key={recruiter}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                    jobFilters.team?.recruiters?.includes(recruiter)
                      ? 'bg-gray-100 dark:bg-gray-800 border-gray-900 dark:border-gray-50 text-gray-950 dark:text-gray-50 font-medium'
                      : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                  }`}
                  onClick={() => toggleJobFilter('team', 'recruiters', recruiter)}
                >
                  {recruiter}
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
              <UserCheck className="w-3.5 h-3.5" />
              Gestor
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {['Rafael Oliveira', 'Carlos Eduardo Lima', 'João Paulo Silva', 'Fernanda Almeida', 'Patricia Souza', 'Ricardo Mendes', 'Bruno Costa'].map(manager => (
                <Badge
                  key={manager}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                    jobFilters.team?.managers?.includes(manager)
                      ? 'bg-gray-100 dark:bg-gray-800 border-gray-900 dark:border-gray-50 text-gray-950 dark:text-gray-50 font-medium'
                      : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                  }`}
                  onClick={() => toggleJobFilter('team', 'managers', manager)}
                >
                  {manager}
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
              <Share2 className="w-3.5 h-3.5" />
              Publicação
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {[
                { value: 'linkedin', label: 'LinkedIn', Icon: Linkedin },
                { value: 'website', label: 'Website', Icon: Globe },
                { value: 'indeed', label: 'Indeed', Icon: Briefcase }
              ].map(channel => (
                <Badge
                  key={channel.value}
                  variant="outline"
                  className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors flex items-center gap-1 ${
                    jobFilters.publishing?.channels?.includes(channel.value)
                      ? 'bg-gray-100 dark:bg-gray-800 border-gray-900 dark:border-gray-50 text-gray-950 dark:text-gray-50 font-medium'
                      : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                  }`}
                  onClick={() => toggleJobFilter('publishing', 'channels', channel.value)}
                >
                  <channel.Icon className="w-3 h-3" />
                  {channel.label}
                </Badge>
              ))}
              <Badge
                variant="outline"
                className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                  jobFilters.publishing?.unpublished
                    ? 'bg-orange-50 border-orange-300 text-orange-700 font-medium'
                    : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                }`}
                onClick={() => toggleJobFilter('publishing', 'unpublished', !jobFilters.publishing?.unpublished)}
              >
                Não Publicadas
              </Badge>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
              <BarChart3 className="w-3.5 h-3.5" />
              Métricas
            </h4>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded bg-gray-50 dark:bg-gray-800">
                <input
                  type="checkbox"
                  className="w-3 h-3"
                  checked={jobFilters.funnel?.emptyPipeline || false}
                  onChange={(e) => toggleJobFilter('funnel', 'emptyPipeline', e.target.checked)}
                />
                <span className="text-gray-700 dark:text-gray-200">Pipeline vazio (sem candidatos)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-xs p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded bg-gray-50 dark:bg-gray-800">
                <input
                  type="checkbox"
                  className="w-3 h-3"
                  checked={jobFilters.metrics?.lowConversion || false}
                  onChange={(e) => toggleJobFilter('metrics', 'lowConversion', e.target.checked)}
                />
                <span className="text-gray-700 dark:text-gray-200">Baixa conversão</span>
              </label>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                <Bookmark className="w-3.5 h-3.5" />
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
 className="h-6 text-xs px-2 text-gray-600 hover:text-gray-600/80"
                >
                  <Plus className="w-3 h-3 mr-1" />
                  Salvar Busca
                </Button>
              )}
            </div>
            {savedSearches.length > 0 ? (
              <div className="space-y-1.5 max-h-[180px] overflow-y-auto">
                {savedSearches.map((search) => (
                  <div
                    key={search.id}
                    className="group flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                    onClick={() => handleApplySavedSearch(search.id)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <Search className="w-3 h-3 text-gray-600 dark:text-gray-400 flex-shrink-0" />
                        <span className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                          {search.name}
                        </span>
                      </div>
                      <p className="text-micro text-gray-600 dark:text-gray-400 mt-0.5 truncate">
                        {new Date(search.createdAt).toLocaleDateString('pt-BR')}
                        {search.query && ` - "${search.query}"`}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
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
                        <Edit2 className="w-3 h-3 text-gray-600 dark:text-gray-400" />
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
                        <Trash2 className="w-3 h-3 text-red-400" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <Bookmark className="w-5 h-5 text-gray-600 dark:text-gray-400 mx-auto mb-1" />
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Nenhuma busca salva
                </p>
                <p className="text-micro text-gray-600 dark:text-gray-500 mt-0.5">
                  Aplique filtros e clique em "Salvar Busca"
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="flex-shrink-0 p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
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
                className="h-7 text-xs text-gray-800 hover:text-gray-950"
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
