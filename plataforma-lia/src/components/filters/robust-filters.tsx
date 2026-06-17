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
import { Chip } from '@/components/ui/chip'
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
  { id: 'novo', label: 'Novo', color: 'bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary', count: 45 },
  { id: 'em_triagem', label: 'Em Triagem', color: '', count: 23 },
  { id: 'aprovado', label: 'Aprovado', color: '', count: 12 },
  { id: 'entrevista', label: 'Entrevista', color: '', count: 8 },
  { id: 'finalista', label: 'Finalista', color: '', count: 5 },
  { id: 'contratado', label: 'Contratado', color: '', count: 3 }
]

const jobStatuses = [
  { id: 'ativa', label: 'Ativa', color: '', count: 15 },
  { id: 'pausada', label: 'Pausada', color: '', count: 5 },
  { id: 'fechada', label: 'Fechada', color: 'bg-lia-bg-tertiary text-lia-text-primary', count: 8 },
  { id: 'urgente', label: 'Urgente', color: '', count: 3 },
  { id: 'rascunho', label: 'Rascunho', color: 'bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary', count: 2 }
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
    <div data-testid="robust-filters" className={cn("space-y-4", className)}>
      {/* Search Bar */}
      <div className="relative">
        <div className="relative rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle transition-shadow duration-200 focus-within:shadow-lia-focus">
          <div className="flex items-center">
            <Search className="absolute left-3 w-4 h-4 text-lia-text-secondary" />
            <input
              type="text"
              placeholder={type === 'candidates' ?"Buscar candidatos..." :"Buscar vagas..."}
              value={filters.search}
              onChange={(e) => updateFilter('search', e.target.value)}
              className="w-full pl-10 pr-20 py-3 bg-transparent border-0 focus:outline-none text-lia-text-primary placeholder-lia-text-secondary"
            />
            <div className="absolute right-2 flex items-center gap-2">
              {resultsCount !== undefined && (
                <span className="text-xs text-lia-text-secondary">
                  {resultsCount} resultado{resultsCount !== 1 ? 's' : ''}
                </span>
              )}
              {activeFiltersCount > 0 && (
                <Chip density="relaxed" variant="neutral" muted >
                  {activeFiltersCount}
                </Chip>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className={cn("h-8 w-8 p-0",
                  showAdvanced &&"bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary"
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
            className={cn("flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-[width,height] border","hover:scale-[1.02] active:scale-[0.98]",
              filters.status.includes(status.id)
                ? status.color +" border-current"
                :"bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle hover:bg-lia-interactive-active dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:bg-lia-bg-inverse"
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
         
        >
          <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl p-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 space-y-6">

            {/* Grid Layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

              {/* Localização */}
              <div>
                <h4 className="text-sm font-medium text-lia-text-primary mb-3 flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Localização
                </h4>
                <div className="space-y-2">
                  {locations.map((location) => (
                    <button
                      key={location}
                      onClick={() => toggleArrayFilter('location', location)}
                      className={cn("w-full text-left px-3 py-2 rounded-md text-sm transition-colors border","hover:scale-[1.02] active:scale-[0.98]",
                        filters.location.includes(location)
                          ?"bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary border-lia-btn-primary-bg"
                          :"bg-lia-bg-primary text-lia-text-primary border-lia-border-subtle hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:bg-lia-bg-inverse"
                      )}
                    >
                      {location}
                    </button>
                  ))}
                </div>
              </div>

              {/* Experiência */}
              <div>
                <h4 className="text-sm font-medium text-lia-text-primary mb-3 flex items-center gap-2">
                  <Briefcase className="w-4 h-4" />
                  Experiência
                </h4>
                <div className="space-y-2">
                  {experienceLevels.map((level) => (
                    <button
                      key={level}
                      onClick={() => toggleArrayFilter('experience', level)}
                      className={cn("w-full text-left px-3 py-2 rounded-md text-sm transition-colors border","hover:scale-[1.02] active:scale-[0.98]",
                        filters.experience.includes(level)
                          ?" border-status-success/30"
                          :"bg-lia-bg-primary text-lia-text-primary border-lia-border-subtle hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:bg-lia-bg-inverse"
                      )}
                    >
                      {level}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tipo de Contrato */}
              <div>
                <h4 className="text-sm font-medium text-lia-text-primary mb-3 flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Tipo de Contrato
                </h4>
                <div className="space-y-2">
                  {contractTypes.map((contract) => (
                    <button
                      key={contract}
                      onClick={() => toggleArrayFilter('contractType', contract)}
                      className={cn("w-full text-left px-3 py-2 rounded-md text-sm transition-colors border","hover:scale-[1.02] active:scale-[0.98]",
                        filters.contractType.includes(contract)
                          ?" border-wedo-purple/30"
                          :"bg-lia-bg-primary text-lia-text-primary border-lia-border-subtle hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:bg-lia-bg-inverse"
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
              <h4 className="text-sm font-medium text-lia-text-primary mb-3 flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                Faixa Salarial
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-lia-text-secondary mb-1 block">
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
                    className="w-full px-3 py-2 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium"
                  />
                </div>
                <div>
                  <label className="text-xs text-lia-text-secondary mb-1 block">
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
                    className="w-full px-3 py-2 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium"
                  />
                </div>
              </div>
            </div>

            {/* Skills */}
            <div>
              <h4 className="text-sm font-medium text-lia-text-primary mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Habilidades Populares
              </h4>
              <div className="flex flex-wrap gap-2">
                {popularSkills.map((skill) => (
                  <button
                    key={skill}
                    onClick={() => toggleArrayFilter('skills', skill)}
                    className={cn("px-3 py-1 rounded-full text-xs font-medium transition-[width,height]","hover:scale-[1.05] active:scale-[0.95]",
                      filters.skills.includes(skill)
                        ?""
 :"text-lia-text-primary hover:dark:bg-lia-bg-elevated dark:hover:bg-lia-border-medium"
                    )}
                  >
                    {skill}
                  </button>
                ))}
              </div>
            </div>

            {/* All Status Options */}
            <div>
              <h4 className="text-sm font-medium text-lia-text-primary mb-3 flex items-center gap-2">
                <Users className="w-4 h-4" />
                Status Completo
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {statuses.map((status) => (
                  <button
                    key={status.id}
                    onClick={() => toggleArrayFilter('status', status.id)}
                    className={cn("flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors border","hover:scale-[1.02] active:scale-[0.98]",
                      filters.status.includes(status.id)
                        ? status.color +" border-current"
                        :"bg-lia-bg-primary text-lia-text-primary border-lia-border-subtle hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:bg-lia-bg-inverse"
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
          className="flex flex-wrap items-center gap-2 p-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl"
         
        >
          <span className="text-sm font-medium text-lia-text-primary">
            Filtros aplicados ({activeFiltersCount}):
          </span>
          {filters.status.map((status) => (
            <Chip density="relaxed" key={status} variant="neutral" muted >
              {statuses.find(s => s.id === status)?.label}
              <button
                onClick={() => toggleArrayFilter('status', status)}
                className="ml-1 hover:bg-lia-border-default dark:hover:bg-lia-border-medium rounded-full"
              >
                <X className="w-3 h-3" />
              </button>
            </Chip>
          ))}
          {filters.location.map((location) => (
            <Chip density="relaxed" key={location} variant="neutral" muted >
              📍 {location}
              <button
                onClick={() => toggleArrayFilter('location', location)}
                className="ml-1 hover:bg-lia-border-default dark:hover:bg-lia-border-medium rounded-full"
              >
                <X className="w-3 h-3" />
              </button>
            </Chip>
          ))}
          {filters.skills.map((skill) => (
            <Chip density="relaxed" key={skill} variant="neutral" muted >
              🏷️ {skill}
              <button
                onClick={() => toggleArrayFilter('skills', skill)}
                className="ml-1 hover:bg-lia-border-default dark:hover:bg-lia-border-medium rounded-full"
              >
                <X className="w-3 h-3" />
              </button>
            </Chip>
          ))}
        </div>
      )}
    </div>
  )
}
