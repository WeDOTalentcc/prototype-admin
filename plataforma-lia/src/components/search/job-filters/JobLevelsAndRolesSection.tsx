"use client"

import { useState, useRef } from"react"
import { X, Zap, Loader2, Info } from"lucide-react"
import { cn } from"@/lib/utils"
import { Input } from"@/components/ui/input"
import { Label } from"@/components/ui/label"
import { Chip } from "@/components/ui/chip"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"
import { useSemanticSearch } from"@/hooks/search/useSemanticSearch"
import type { SearchFilters } from '../hooks/useAdvancedFiltersCore'
import { experienceLevels, jobRoles } from '../advancedFiltersTypes'

export interface JobLevelsAndRolesSectionProps {
  filters: SearchFilters
  addToArray: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string) => void
  removeFromArray: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string) => void
}

export const JobLevelsAndRolesSection = ({
  filters,
  addToArray,
  removeFromArray,
}: JobLevelsAndRolesSectionProps) => {
  const [roleInput, setRoleInput] = useState("")
  const [showRoleSuggestions, setShowRoleSuggestions] = useState(false)
  const roleInputRef = useRef<HTMLInputElement>(null)

  const {
    suggestions: roleSuggestions,
    isLoading: isLoadingRoles,
    search: searchRoles,
    clearSuggestions: clearRoleSuggestions
  } = useSemanticSearch({ domain:"roles", debounceMs: 400 })

  const handleAddRole = (role: string) => {
    if (role.trim()) {
      addToArray("job","roles", role.trim())
      setRoleInput("")
      clearRoleSuggestions()
      setShowRoleSuggestions(false)
    }
  }

  const handleRoleInputChange = (value: string) => {
    setRoleInput(value)
    if (value.trim().length >= 2) {
      searchRoles(value, filters.job?.roles || [])
      setShowRoleSuggestions(true)
    } else {
      clearRoleSuggestions()
      setShowRoleSuggestions(false)
    }
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Job Title Levels */}
      <div className="space-y-2">
        <div className="flex items-center gap-1.5">
          <Label className="text-xs font-medium">Níveis de Cargo</Label>
          <Popover>
            <PopoverTrigger asChild>
              <button className="text-lia-text-tertiary hover:text-lia-text-secondary">
                <Info className="w-3 h-3" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-2 bg-lia-bg-elevated text-xs">
              Filtrar por nível hierárquico do cargo
            </PopoverContent>
          </Popover>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {experienceLevels.map(level => {
            const isSelected = filters.job?.levels?.includes(level.value)
            return (
              <button
                key={level.value}
                onClick={() => {
                  if (isSelected) {
                    removeFromArray("job","levels", level.value)
                  } else {
                    addToArray("job","levels", level.value)
                  }
                }}
                className={cn("px-2.5 py-1 rounded-md text-xs border transition-colors",
                  isSelected
                    ?"border-lia-border-medium bg-lia-bg-tertiary text-lia-text-primary font-medium"
                    :"border-lia-border-subtle hover:border-lia-border-default text-lia-text-secondary"
                )}
              >
                {level.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Roles/Areas */}
      <div className="space-y-2">
        <div className="flex items-center gap-1.5">
          <Label className="text-xs font-medium">Funções/Áreas</Label>
          <Popover>
            <PopoverTrigger asChild>
              <button className="text-lia-text-tertiary hover:text-lia-text-secondary">
                <Info className="w-3 h-3" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-2 bg-lia-bg-elevated text-xs">
              Filtrar por área funcional de atuação. Selecione da lista ou digite para adicionar uma área customizada.
            </PopoverContent>
          </Popover>
        </div>

        {/* Custom Role Input */}
        <div className="relative">
          <div className="relative">
            <Input
              ref={roleInputRef}
              value={roleInput}
              onChange={(e) => handleRoleInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key ==="Enter" && roleInput.trim()) {
                  e.preventDefault()
                  handleAddRole(roleInput)
                } else if (e.key ==="Escape") {
                  setShowRoleSuggestions(false)
                }
              }}
              onFocus={() => roleInput.length >= 2 && setShowRoleSuggestions(true)}
              onBlur={() => setTimeout(() => setShowRoleSuggestions(false), 200)}
              placeholder="Digite área e pressione Enter"
              className="h-7 text-xs border border-lia-border-subtle focus:ring-1 focus:ring-lia-border-medium"
            />
            {isLoadingRoles && (
              <div className="absolute right-2 top-1/2 -translate-y-1/2" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-3 h-3 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
              </div>
            )}
          </div>

          {/* Semantic Suggestions for Roles */}
          {showRoleSuggestions && roleSuggestions.length > 0 && (
            <div className="absolute z-50 mt-1 w-full bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-40 overflow-y-auto">
              <div className="p-1 dark:border-lia-border-subtle">
                <div className="flex items-center gap-1 text-micro text-lia-text-secondary">
                  <Zap className="w-2.5 h-2.5" />
                  <span>Sugestões AI</span>
                </div>
              </div>
              {roleSuggestions.map((suggestion) => (
                <button
                  key={suggestion.term}
                  onMouseDown={(e) => {
                    e.preventDefault()
                    handleAddRole(suggestion.term)
                  }}
                  className="w-full text-left px-2 py-1.5 text-xs hover:bg-lia-bg-secondary flex items-center justify-between gap-2"
                >
                  <span>{suggestion.term}</span>
                  <span className="text-micro text-lia-text-tertiary">
                    {Math.round(suggestion.confidence * 100)}%
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Custom Roles (added by user) */}
        {(filters.job?.roles?.filter(r => !jobRoles.find(jr => jr.value === r))?.length || 0) > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {filters.job?.roles?.filter(r => !jobRoles.find(jr => jr.value === r)).map(role => (
              <Chip
                key={role}
                variant="neutral" muted
                className="bg-wedo-purple/10 border border-wedo-purple/30 text-wedo-purple-text pl-2 pr-1 py-0.5 flex items-center gap-1"
              >
                <span className="text-xs">{role}</span>
                <button
                  onClick={() => removeFromArray("job","roles", role)}
                  className="ml-1 hover:bg-wedo-purple/20 rounded-md p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </Chip>
            ))}
          </div>
        )}

        {/* Predefined Roles */}
        <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
          {jobRoles.map(role => {
            const isSelected = filters.job?.roles?.includes(role.value)
            return (
              <button
                key={role.value}
                onClick={() => {
                  if (isSelected) {
                    removeFromArray("job","roles", role.value)
                  } else {
                    addToArray("job","roles", role.value)
                  }
                }}
                className={cn("px-2.5 py-1 rounded-md text-xs border transition-colors",
                  isSelected
                    ?"border-lia-border-medium bg-lia-bg-tertiary text-lia-text-primary font-medium"
                    :"border-lia-border-subtle hover:border-lia-border-default text-lia-text-secondary"
                )}
              >
                {role.label}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
