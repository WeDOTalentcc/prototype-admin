'use client'

import React, { useState, useMemo } from 'react'
import {
  Filter,
  Search,
  Calendar,
  MapPin,
  DollarSign,
  GraduationCap,
  Briefcase,
  Clock,
  Star,
  TrendingUp,
  Users,
  X,
  SlidersHorizontal
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export interface RobustFilters {
  search: string
  location: string[]
  experience: string[]
  salary: {
    min: number | null
    max: number | null
  }
  skills: string[]
  status: string[]
  dateRange: string
  education: string[]
  contractType: string[]
  priority: string
  source: string[]
  tags: string[]
}

interface RobustFiltersProps {
  type: 'candidates' | 'jobs'
  filters: RobustFilters
  onFiltersChange: (filters: RobustFilters) => void
  resultsCount?: number
  className?: string
}

const candidateStatuses = [
  { id: 'novo', label: 'Novo', color: 'bg-gray-100 text-gray-600 dark:bg-lia-bg-secondary dark:text-lia-text-tertiary', count: 45 },
  { id: 'em_triagem', label: 'Em Triagem', color: 'bg-status-warning/10 text-status-warning', count: 23 },
  { id: 'aprovado', label: 'Aprovado', color: 'bg-status-success/10 text-status-success', count: 12 },
  { id: 'entrevista', label: 'Entrevista', color: 'bg-wedo-purple/15 text-wedo-purple', count: 8 },
  { id: 'finalista', label: 'Finalista', color: 'bg-wedo-orange/15 text-wedo-orange', count: 5 },
  { id: 'contratado', label: 'Contratado', color: 'bg-status-success/10 text-status-success', count: 3 }
]

const jobStatuses = [
  { id: 'ativa', label: 'Ativa', color: 'bg-status-success/10 text-status-success', count: 15 },
  { id: 'pausada', label: 'Pausada', color: 'bg-status-warning/10 text-status-warning', count: 5 },
  { id: 'fechada', label: 'Fechada', color: 'bg-gray-100 lia-text-strong', count: 8 },
  { id: 'urgente', label: 'Urgente', color: 'bg-status-error/10 text-status-error', count: 3 },
  { id: 'rascunho', label: 'Rascunho', color: 'bg-gray-100 text-gray-600 dark:bg-lia-bg-secondary dark:text-lia-text-tertiary', count: 2 }
]

const locations = ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Porto Alegre', 'Remoto', 'Híbrido']
const experienceLevels = ['Estágio', 'Júnior', 'Pleno', 'Sênior', 'Especialista', 'Gerencial']
const educationLevels = ['Ensino Médio', 'Técnico', 'Superior', 'Pós-graduação', 'Mestrado', 'Doutorado']
const contractTypes = ['CLT', 'PJ', 'Terceirizado', 'Estágio', 'Freelancer', 'Consultoria']
const popularSkills = ['React', 'Node.js', 'Python', 'JavaScript', 'TypeScript', 'SQL', 'AWS', 'Docker']

export function RobustFilters({
  type,
  filters,
  onFiltersChange,
  resultsCount,
  className
}: RobustFiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)

  const statuses = type === 'candidates' ? candidateStatuses : jobStatuses

  const activeFiltersCount = useMemo(() => {
    let count = 0
    if (filters.search) count++
    if (filters.location.length > 0) count++
    if (filters.experience.length > 0) count++
    if (filters.salary.min || filters.salary.max) count++
    if (filters.skills.length > 0) count++
    if (filters.status.length > 0) count++
    if (filters.dateRange !== 'all') count++
    if (filters.education.length > 0) count++
    if (filters.contractType.length > 0) count++
    if (filters.priority !== 'all') count++
    if (filters.source.length > 0) count++
    if (filters.tags.length > 0) count++
    return count
  }, [filters])

  const updateFilter = <K extends keyof RobustFilters>(key: K, value: RobustFilters[K]) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const toggleArrayFilter = <K extends keyof RobustFilters>(key: K, value: string) => {
    const currentArray = filters[key] as string[]
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value]
    updateFilter(key, newArray as RobustFilters[K])
  }

  const clearAllFilters = () => {
    onFiltersChange({
      search: '',
      location: [],
      experience: [],
      salary: { min: null, max: null },
      skills: [],
      status: [],
      dateRange: 'all',
      education: [],
      contractType: [],
      priority: 'all',
      source: [],
      tags: []
    })
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Search Bar */}
      <div className="relative">
        <div className="relative rounded-md bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle transition-shadow duration-200 focus-within:shadow-lia-focus">
          <div className="flex items-center">
            <Search className="absolute left-3 w-4 h-4 lia-text-base" />
            <input
              type="text"
              placeholder={type === 'candidates' ? "Buscar candidatos..." : "Buscar vagas..."}
              value={filters.search}
              onChange={(e) => updateFilter('search', e.target.value)}
              className="w-full pl-10 pr-20 py-3 bg-transparent border-0 focus:outline-none text-gray-950 placeholder-gray-600"
            />
            <div className="absolute right-2 flex items-center gap-2">
              {resultsCount !== undefined && (
                <span className="text-xs text-gray-600 dark:text-lia-text-tertiary">
                  {resultsCount} resultado{resultsCount !== 1 ? 's' : ''}
                </span>
              )}
              {activeFiltersCount > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {activeFiltersCount}
                </Badge>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className={cn(
 "h-8 w-8 p-0",
                  showAdvanced && "bg-gray-100 dark:bg-lia-bg-secondary text-gray-900"
                )}
              >
                <SlidersHorizontal className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Status Filters */}
      <div className="flex flex-wrap items-center gap-2">
        {statuses.slice(0, 4).map((status) => (
          <button
            key={status.id}
            onClick={() => toggleArrayFilter('status', status.id)}
            className={cn(
 "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-[width,height] border",
              "hover:scale-[1.02] active:scale-[0.98]",
              filters.status.includes(status.id)
                ? status.color + " border-current"
                : "bg-gray-100 text-gray-600 border-lia-border-subtle hover:bg-gray-200 dark:bg-lia-bg-secondary dark:text-lia-text-secondary dark:border-lia-border-subtle dark:hover:bg-gray-700"
            )}
          >
            {status.label}
            <span className="text-xs opacity-70">({status.count})</span>
          </button>
        ))}

        {activeFiltersCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAllFilters}
            className="h-8 text-status-error hover:text-status-error/80 hover:bg-status-error/10"
          >
            <X className="w-3 h-3 mr-1" />
            Limpar ({activeFiltersCount})
          </Button>
        )}
      </div>

      {/* Advanced Filters */}
      {showAdvanced && (
        <div
          className="overflow-hidden"
          style={{animation: 'slideInUp 0.3s ease-out'}}
        >
          <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-4 bg-gray-50 dark:bg-lia-bg-secondary/50 space-y-6">

            {/* Grid Layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

              {/* Localização */}
              <div>
                <h4 className="text-sm font-medium text-gray-950 mb-3 flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Localização
                </h4>
                <div className="space-y-2">
                  {locations.map((location) => (
                    <button
                      key={location}
                      onClick={() => toggleArrayFilter('location', location)}
                      className={cn(
 "w-full text-left px-3 py-2 rounded-md text-sm transition-colors border",
                        "hover:scale-[1.02] active:scale-[0.98]",
                        filters.location.includes(location)
                          ? "bg-gray-100 dark:bg-lia-bg-secondary text-gray-900 border-gray-900"
                          : "bg-white text-gray-800 dark:text-lia-text-primary border-lia-border-subtle hover:bg-gray-50 dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:bg-gray-700"
                      )}
                    >
                      {location}
                    </button>
                  ))}
                </div>
              </div>

              {/* Experiência */}
              <div>
                <h4 className="text-sm font-medium text-gray-950 mb-3 flex items-center gap-2">
                  <Briefcase className="w-4 h-4" />
                  Experiência
                </h4>
                <div className="space-y-2">
                  {experienceLevels.map((level) => (
                    <button
                      key={level}
                      onClick={() => toggleArrayFilter('experience', level)}
                      className={cn(
 "w-full text-left px-3 py-2 rounded-md text-sm transition-colors border",
                        "hover:scale-[1.02] active:scale-[0.98]",
                        filters.experience.includes(level)
                          ? "bg-status-success/10 text-status-success border-status-success/30"
                          : "bg-white text-gray-800 dark:text-lia-text-primary border-lia-border-subtle hover:bg-gray-50 dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:bg-gray-700"
                      )}
                    >
                      {level}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tipo de Contrato */}
              <div>
                <h4 className="text-sm font-medium text-gray-950 mb-3 flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Tipo de Contrato
                </h4>
                <div className="space-y-2">
                  {contractTypes.map((contract) => (
                    <button
                      key={contract}
                      onClick={() => toggleArrayFilter('contractType', contract)}
                      className={cn(
 "w-full text-left px-3 py-2 rounded-md text-sm transition-colors border",
                        "hover:scale-[1.02] active:scale-[0.98]",
                        filters.contractType.includes(contract)
                          ? "bg-wedo-purple/15 text-wedo-purple border-wedo-purple/30"
                          : "bg-white text-gray-800 dark:text-lia-text-primary border-lia-border-subtle hover:bg-gray-50 dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:bg-gray-700"
                      )}
                    >
                      {contract}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Salary Range */}
            <div>
              <h4 className="text-sm font-medium text-gray-950 mb-3 flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                Faixa Salarial
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-600 dark:text-lia-text-tertiary mb-1 block">
                    Salário Mínimo
                  </label>
                  <input
                    type="number"
                    placeholder="0"
                    value={filters.salary.min || ''}
                    onChange={(e) => updateFilter('salary', {
                      ...filters.salary,
                      min: e.target.value ? Number(e.target.value) : null
                    })}
                    className="w-full px-3 py-2 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-white dark:bg-lia-bg-secondary text-gray-950 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-600 dark:text-lia-text-tertiary mb-1 block">
                    Salário Máximo
                  </label>
                  <input
                    type="number"
                    placeholder="0"
                    value={filters.salary.max || ''}
                    onChange={(e) => updateFilter('salary', {
                      ...filters.salary,
                      max: e.target.value ? Number(e.target.value) : null
                    })}
                    className="w-full px-3 py-2 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-white dark:bg-lia-bg-secondary text-gray-950 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                  />
                </div>
              </div>
            </div>

            {/* Skills */}
            <div>
              <h4 className="text-sm font-medium text-gray-950 mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Habilidades Populares
              </h4>
              <div className="flex flex-wrap gap-2">
                {popularSkills.map((skill) => (
                  <button
                    key={skill}
                    onClick={() => toggleArrayFilter('skills', skill)}
                    className={cn(
 "px-3 py-1 rounded-full text-xs font-medium transition-[width,height]",
                      "hover:scale-[1.05] active:scale-[0.95]",
                      filters.skills.includes(skill)
                        ? "bg-wedo-orange/15 text-wedo-orange"
 : "text-gray-800 hover:dark:bg-lia-bg-elevated dark:text-lia-text-secondary dark:hover:bg-gray-600"
                    )}
                  >
                    {skill}
                  </button>
                ))}
              </div>
            </div>

            {/* All Status Options */}
            <div>
              <h4 className="text-sm font-medium text-gray-950 mb-3 flex items-center gap-2">
                <Users className="w-4 h-4" />
                Status Completo
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {statuses.map((status) => (
                  <button
                    key={status.id}
                    onClick={() => toggleArrayFilter('status', status.id)}
                    className={cn(
 "flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors border",
                      "hover:scale-[1.02] active:scale-[0.98]",
                      filters.status.includes(status.id)
                        ? status.color + " border-current"
                        : "bg-white text-gray-800 dark:text-lia-text-primary border-lia-border-subtle hover:bg-gray-50 dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:bg-gray-700"
                    )}
                  >
                    <span>{status.label}</span>
                    <span className="text-xs opacity-70">({status.count})</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Active Filters Summary */}
      {activeFiltersCount > 0 && (
        <div
          className="flex flex-wrap items-center gap-2 p-3 bg-gray-100 dark:bg-lia-bg-secondary rounded-md"
          style={{animation: 'fadeIn 0.3s ease-out'}}
        >
          <span className="text-sm font-medium text-gray-900">
            Filtros aplicados ({activeFiltersCount}):
          </span>
          {filters.status.map((status) => (
            <Badge key={status} variant="secondary" className="text-xs">
              {statuses.find(s => s.id === status)?.label}
              <button
                onClick={() => toggleArrayFilter('status', status)}
                className="ml-1 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-full"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
          {filters.location.map((location) => (
            <Badge key={location} variant="secondary" className="text-xs">
              📍 {location}
              <button
                onClick={() => toggleArrayFilter('location', location)}
                className="ml-1 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-full"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
          {filters.skills.map((skill) => (
            <Badge key={skill} variant="secondary" className="text-xs">
              🏷️ {skill}
              <button
                onClick={() => toggleArrayFilter('skills', skill)}
                className="ml-1 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-full"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}
