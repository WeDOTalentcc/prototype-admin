"use client"

import { useState, useCallback } from"react"
import { X, Brain, Loader2, Search, ChevronDown, Info, RotateCcw, Save, List } from"lucide-react"
import { cn } from"@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from"@/components/ui/tooltip"
import { CompanyPresetsModal } from"./CompanyPresetsModal"
import { useTagInputState } from"@/hooks/ui/useTagInputState"
import { useUIPreferencesStore } from"@/stores/ui-preferences-store"

export interface ExcludedCompanyItem {
  name: string
  domain?: string
}

export type ExcludedTimeFilter = 'current_only' | 'current_past'

interface ExcludedCompaniesInputProps {
  value: ExcludedCompanyItem[]
  onChange: (companies: ExcludedCompanyItem[]) => void
  timeFilter?: ExcludedTimeFilter
  onTimeFilterChange?: (filter: ExcludedTimeFilter) => void
  placeholder?: string
  showPresets?: boolean
}

const POPULAR_COMPANIES = [
  { name:"Nubank", domain:"nubank.com.br" },
  { name:"iFood", domain:"ifood.com.br" },
  { name:"Stone", domain:"stone.com.br" },
  { name:"Google", domain:"google.com" },
  { name:"Meta", domain:"meta.com" },
  { name:"Amazon", domain:"amazon.com" },
  { name:"Microsoft", domain:"microsoft.com" },
  { name:"Apple", domain:"apple.com" },
  { name:"Salesforce", domain:"salesforce.com" },
  { name:"Oracle", domain:"oracle.com" },
]

const TIME_FILTER_OPTIONS: { 
  value: ExcludedTimeFilter
  label: string
  description: string
}[] = [
  { 
    value: 'current_only', 
    label: 'Apenas Atual',
    description: 'Excluir pessoas que trabalham atualmente nestas empresas'
  },
  { 
    value: 'current_past', 
    label: 'Atual + Anterior',
    description: 'Excluir pessoas que trabalham ou já trabalharam nestas empresas'
  },
]

export function ExcludedCompaniesInput({
  value,
  onChange,
  timeFilter = 'current_only',
  onTimeFilterChange,
  placeholder ="Type company to exclude...",
  showPresets = true
}: ExcludedCompaniesInputProps) {
  const {
    inputValue, setInputValue,
    isDropdownOpen, setIsDropdownOpen,
    focusedIndex, setFocusedIndex,
    inputRef, dropdownRef,
    handleKeyNavigation, closeDropdown
  } = useTagInputState()
  const { getCustomPresets, setCustomPresets } = useUIPreferencesStore()
  const [isPresetsModalOpen, setIsPresetsModalOpen] = useState(false)
  const [isTimeFilterOpen, setIsTimeFilterOpen] = useState(false)
  const [showSavePresetModal, setShowSavePresetModal] = useState(false)
  const [savePresetName, setSavePresetName] = useState("")

  const existingCompanyNames = value.map(c => c.name.toLowerCase())

  const filteredSuggestions = inputValue.trim()
    ? POPULAR_COMPANIES.filter(company => 
        company.name.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingCompanyNames.includes(company.name.toLowerCase())
      ).slice(0, 6)
    : []



  const addCompany = useCallback((company: ExcludedCompanyItem) => {
    if (!company.name.trim()) return
    if (existingCompanyNames.includes(company.name.toLowerCase())) return
    onChange([...value, company])
    setInputValue("")
    closeDropdown()
  }, [value, onChange, existingCompanyNames, closeDropdown, setInputValue])

  const removeCompany = useCallback((name: string) => {
    onChange(value.filter(c => c.name !== name))
  }, [value, onChange])

  const clearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  const handleSaveCustomPreset = useCallback(() => {
    if (!savePresetName.trim() || value.length === 0) return
    
    const existingPresets = getCustomPresets('excluded_company_custom_presets')
    const newPreset = {
      id: `custom_${Date.now()}`,
      name: savePresetName.trim(),
      companies: value,
      createdAt: new Date().toISOString()
    }
    setCustomPresets('excluded_company_custom_presets', [...existingPresets, newPreset])
    setSavePresetName("")
    setShowSavePresetModal(false)
  }, [savePresetName, value, getCustomPresets, setCustomPresets])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    handleKeyNavigation(
      e,
      filteredSuggestions.length,
      (index) => addCompany(filteredSuggestions[index]),
      () => inputValue.trim() && addCompany({ name: inputValue.trim() })
    )
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value)
    setIsDropdownOpen(e.target.value.length > 0)
    setFocusedIndex(-1)
  }

  const handlePresetSelect = (companies: { name: string; domain?: string }[]) => {
    const newCompanies = companies.filter(
      c => !existingCompanyNames.includes(c.name.toLowerCase())
    )
    onChange([...value, ...newCompanies])
  }

  const currentTimeOption = TIME_FILTER_OPTIONS.find(o => o.value === timeFilter)

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Popover open={isTimeFilterOpen} onOpenChange={setIsTimeFilterOpen}>
          <PopoverTrigger asChild>
            <button className="flex items-center gap-2 px-2.5 py-1 rounded-xl border border-lia-border-subtle text-xs hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none">
              <span className="text-lia-text-primary">{currentTimeOption?.label}</span>
              <ChevronDown className="w-3.5 h-3.5 text-lia-text-tertiary" />
            </button>
          </PopoverTrigger>
          <PopoverContent className="w-72 p-0" align="start">
            <div className="py-1">
              {TIME_FILTER_OPTIONS.map(option => (
                <button
                  key={option.value}
                  onClick={() => {
                    onTimeFilterChange?.(option.value)
                    setIsTimeFilterOpen(false)
                  }}
                  className={cn("w-full text-left px-3 py-2 hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none",
                    timeFilter === option.value &&"bg-lia-bg-secondary"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-lia-text-primary">{option.label}</span>
                    {timeFilter === option.value && (
                      <div className="w-2 h-2 rounded-full bg-lia-btn-primary-bg" />
                    )}
                  </div>
                  <p className="text-xs text-lia-text-secondary mt-0.5">{option.description}</p>
                </button>
              ))}
            </div>
          </PopoverContent>
        </Popover>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button className="p-1 text-lia-text-tertiary hover:text-lia-text-secondary">
                <Info className="w-4 h-4" />
              </button>
            </TooltipTrigger>
            <TooltipContent>
              <p className="text-xs max-w-sidebar-content">
                Excluir perfis com experiência nestas organizações
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {value.length > 0 && (
            <span className="text-xs text-lia-text-secondary">
              {value.length} empresa{value.length !== 1 ? 's' : ''} excluída{value.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={clearAll}
            className="text-xs text-lia-text-secondary hover:text-status-error flex items-center gap-1 transition-colors motion-reduce:transition-none"
          >
            <RotateCcw className="w-3 h-3" />
            Limpar tudo
          </button>
          <button 
            onClick={() => setShowSavePresetModal(true)}
            disabled={value.length === 0}
            className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-3.5 h-3.5" />
            Salvar Preset
          </button>
          {showPresets && (
            <button 
              onClick={() => setIsPresetsModalOpen(true)}
              className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1"
            >
              <List className="w-3.5 h-3.5" />
              Presets
            </button>
          )}
        </div>
      </div>

      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-tertiary" />
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => inputValue.length > 0 && setIsDropdownOpen(true)}
            placeholder={placeholder}
            className="pl-9 pr-3 border-lia-border-subtle focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium"
          />
        </div>

        {isDropdownOpen && filteredSuggestions.length > 0 && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-64 overflow-y-auto"
          >
            {filteredSuggestions.map((company, index) => (
              <button
                key={company.name}
                onClick={() => addCompany(company)}
                className={cn("w-full text-left px-3 py-2 text-sm transition-colors",
                  focusedIndex === index ?"bg-lia-bg-tertiary" :"hover:bg-lia-bg-secondary"
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-lia-text-primary">{company.name}</span>
                  {company.domain && (
                    <span className="text-xs text-lia-text-tertiary">{company.domain}</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map(company => (
            <Chip variant="warning" muted
              key={company.name}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
            >
              <span>{company.name}</span>
              {company.domain && (
                <span className="text-status-warning text-micro">• {company.domain}</span>
              )}
              <button
                onClick={() => removeCompany(company.name)}
                className="hover:bg-status-warning/15 rounded-md p-0.5 transition-colors motion-reduce:transition-none ml-1"
                title="Remove"
              >
                <X className="w-3 h-3" />
              </button>
            </Chip>
          ))}
        </div>
      )}

      <CompanyPresetsModal
        isOpen={isPresetsModalOpen}
        onClose={() => setIsPresetsModalOpen(false)}
        onSelectPreset={handlePresetSelect}
      />

      {showSavePresetModal && (
        <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50" onClick={() => setShowSavePresetModal(false)}>
          <div className="bg-lia-bg-primary rounded-xl p-4 w-80" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-medium text-sm mb-3">Salvar Preset</h3>
            <Input
              value={savePresetName}
              onChange={(e) => setSavePresetName(e.target.value)}
              placeholder="Nome do preset"
              className="mb-3"
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={() => setShowSavePresetModal(false)}>
                Cancelar
              </Button>
              <Button 
                size="sm" 
                onClick={handleSaveCustomPreset}
                disabled={!savePresetName.trim()}
                className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
              >
                <Save className="w-3.5 h-3.5 mr-1.5" />
                Salvar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ExcludedCompaniesInput
