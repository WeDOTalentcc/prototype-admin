'use client'

import React, { useState, useMemo } from 'react'
import { Search, Filter, X, SlidersHorizontal, Hash, Calendar, User, Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Chip } from '@/components/ui/chip'
import { cn } from '@/lib/utils'

export interface SearchFilters {
  query: string
  categories: string[]
  types: string[]
  tags: string[]
  priority: 'all' | 'high' | 'medium' | 'low'
  dateRange: 'all' | 'today' | 'week' | 'month'
  author: string
  favorites: boolean
}

interface AdvancedSearchProps {
  filters: SearchFilters
  onFiltersChange: (filters: SearchFilters) => void
  suggestions?: string[]
  className?: string
}

const filterCategories = [
  { id: 'recrutamento', label: 'Recrutamento', color: 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary' },
  { id: 'triagem', label: 'Triagem', color: ' dark:bg-status-success/20 dark:text-status-success' },
  { id: 'entrevistas', label: 'Entrevistas', color: ' dark:bg-wedo-purple/20 dark:text-wedo-purple' },
  { id: 'onboarding', label: 'Onboarding', color: ' dark:bg-wedo-orange/20 dark:text-wedo-orange' },
  { id: 'analytics', label: 'Analytics', color: 'bg-wedo-magenta/15 text-wedo-magenta-text dark:bg-wedo-magenta/20 dark:text-wedo-magenta' },
  { id: 'integracao', label: 'Integração', color: ' dark:bg-wedo-purple/20 dark:text-wedo-purple' }
]

const filterTypes = [
  { id: 'comando', label: 'Comando', icon: '⚡' },
  { id: 'template', label: 'Template', icon: '📝' },
  { id: 'workflow', label: 'Workflow', icon: '🔄' },
  { id: 'integracao', label: 'Integração', icon: '🔗' },
  { id: 'relatorio', label: 'Relatório', icon: '📊' },
  { id: 'automacao', label: 'Automação', icon: '🤖' }
]

const popularTags = [
  'urgente', 'automatico', 'manual', 'personalizado', 'experimental',
  'aprovado', 'novo', 'atualizado', 'deprecated', 'beta'
]

export function AdvancedSearch({ filters, onFiltersChange, suggestions = [], className }: AdvancedSearchProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [searchFocused, setSearchFocused] = useState(false)

  const activeFiltersCount = useMemo(() => {
    let count = 0
    if (filters.categories.length > 0) count++
    if (filters.types.length > 0) count++
    if (filters.tags.length > 0) count++
    if (filters.priority !== 'all') count++
    if (filters.dateRange !== 'all') count++
    if (filters.author) count++
    if (filters.favorites) count++
    return count
  }, [filters])

  const updateFilter = <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const toggleArrayFilter = <K extends keyof SearchFilters>(key: K, value: string) => {
    const currentArray = filters[key] as string[]
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value]
    updateFilter(key, newArray as SearchFilters[K])
  }

  const clearAllFilters = () => {
    onFiltersChange({
      query: '',
      categories: [],
      types: [],
      tags: [],
      priority: 'all',
      dateRange: 'all',
      author: '',
      favorites: false
    })
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Search Input Principal */}
      <div className="relative">
        <div className="relative rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle transition-shadow duration-200 focus-within:shadow-lia-focus">
          <div className="flex items-center">
            <Search className="absolute left-3 w-4 h-4 text-lia-text-secondary" />
            <input
              type="text"
              placeholder="Buscar comandos, templates, workflows..."
              value={filters.query}
              onChange={(e) => updateFilter('query', e.target.value)}
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
              className="w-full pl-10 pr-12 py-3 bg-transparent border-0 focus:outline-none text-lia-text-primary placeholder-lia-text-tertiary"
            />
            <div className="absolute right-2 flex items-center gap-1">
              {activeFiltersCount > 0 && (
                <div>
                  <Chip density="relaxed" variant="neutral" muted >
                    {activeFiltersCount}
                  </Chip>
                </div>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className={cn("h-8 w-8 p-0",
 showAdvanced &&"bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary"
                )}
              >
                <SlidersHorizontal className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Search Suggestions */}
        {searchFocused && suggestions.length > 0 && (
          <div
            className="absolute top-full left-0 right-0 mt-1 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl z-10"
           
          >
            <div className="p-2">
              <p className="text-xs text-lia-text-secondary mb-2">Sugestões:</p>
              <div className="space-y-1">
                {suggestions.slice(0, 5).map((suggestion, index) => (
                  <button
                    key={suggestion}
                    onClick={() => {
                      updateFilter('query', suggestion)
                      setSearchFocused(false)
                    }}
                    className="w-full text-left px-2 py-1 text-sm hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse rounded-xl"
                    style={{animation: `fadeInRight 0.2s ease-out ${index * 0.05}s backwards`}}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant={filters.favorites ?"primary" :"outline"}
          size="sm"
          onClick={() => updateFilter('favorites', !filters.favorites)}
          className="h-8"
        >
          <Star className={cn("w-3 h-3 mr-1", filters.favorites &&"fill-current")} />
          Favoritos
        </Button>

        <Button
          variant={filters.priority === 'high' ?"primary" :"outline"}
          size="sm"
          onClick={() => updateFilter('priority', filters.priority === 'high' ? 'all' : 'high')}
          className="h-8"
        >
          ⚡ Alta Prioridade
        </Button>

        <Button
          variant={filters.dateRange === 'today' ?"primary" :"outline"}
          size="sm"
          onClick={() => updateFilter('dateRange', filters.dateRange === 'today' ? 'all' : 'today')}
          className="h-8"
        >
          <Calendar className="w-3 h-3 mr-1" />
          Hoje
        </Button>

        {activeFiltersCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAllFilters}
            className="h-8 text-status-error hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/20"
          >
            <X className="w-3 h-3 mr-1" />
            Limpar
          </Button>
        )}
      </div>

      {/* Advanced Filters */}
      {showAdvanced && (
        <div
          className="overflow-hidden"
         
        >
          <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl p-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 space-y-4">
            {/* Categorias */}
            <div>
              <h4 className="text-sm font-medium text-lia-text-primary mb-2 flex items-center gap-2">
                <Hash className="w-4 h-4" />
                Categorias
              </h4>
              <div className="flex flex-wrap gap-2">
                {filterCategories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => toggleArrayFilter('categories', category.id)}
                    className={cn("px-3 py-1 rounded-full text-xs font-medium transition-[width,height]","hover:scale-[1.05] active:scale-[0.95]",
                      filters.categories.includes(category.id)
                        ? category.color
 :"text-lia-text-primary hover:dark:bg-lia-bg-elevated dark:hover:bg-lia-border-medium"
                    )}
                  >
                    {category.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Tipos */}
            <div>
              <h4 className="text-sm font-medium text-lia-text-primary mb-2 flex items-center gap-2">
                <Filter className="w-4 h-4" />
                Tipos
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {filterTypes.map((type) => (
                  <button
                    key={type.id}
                    onClick={() => toggleArrayFilter('types', type.id)}
                    className={cn("flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors border","hover:scale-[1.02] active:scale-[0.98]",
                      filters.types.includes(type.id)
                        ?"bg-lia-bg-tertiary text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-default"
 :"bg-lia-bg-primary text-lia-text-primary border-lia-border-subtle hover:dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:bg-lia-bg-inverse"
                    )}
                  >
                    <span>{type.icon}</span>
                    {type.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Tags Populares */}
            <div>
              <h4 className="text-sm font-medium text-lia-text-primary mb-2">
                Tags Populares
              </h4>
              <div className="flex flex-wrap gap-1">
                {popularTags.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => toggleArrayFilter('tags', tag)}
                    className={cn("px-2 py-1 rounded-md text-xs font-medium transition-colors","hover:scale-[1.05] active:scale-[0.95]",
                      filters.tags.includes(tag)
                        ?" dark:bg-status-success/20 dark:text-status-success"
                        :"bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active dark:bg-lia-bg-elevated dark:hover:bg-lia-border-medium"
                    )}
                  >
                    #{tag}
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
          className="flex flex-wrap items-center gap-2"
         
        >
          <span className="text-xs text-lia-text-secondary">Filtros ativos:</span>
          {filters.categories.map((category) => (
            <Chip density="relaxed" key={category} variant="neutral" muted >
              {filterCategories.find(c => c.id === category)?.label}
              <button
                onClick={() => toggleArrayFilter('categories', category)}
                className="ml-1 hover:bg-lia-border-default dark:hover:bg-lia-border-medium rounded-full"
              >
                <X className="w-3 h-3" />
              </button>
            </Chip>
          ))}
          {filters.types.map((type) => (
            <Chip density="relaxed" key={type} variant="neutral" muted >
              {filterTypes.find(t => t.id === type)?.label}
              <button
                onClick={() => toggleArrayFilter('types', type)}
                className="ml-1 hover:bg-lia-border-default dark:hover:bg-lia-border-medium rounded-full"
              >
                <X className="w-3 h-3" />
              </button>
            </Chip>
          ))}
          {filters.tags.map((tag) => (
            <Chip density="relaxed" key={tag} variant="neutral" muted >
              #{tag}
              <button
                onClick={() => toggleArrayFilter('tags', tag)}
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
