"use client"

import { useState, useCallback } from"react"
import { X, Brain, Loader2, Search, ChevronDown, Info, Save, List, RotateCcw, Zap } from"lucide-react"
import { cn } from"@/lib/utils"
import { useTagInputState } from"@/hooks/ui/useTagInputState"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"
import { CompanyPresetsModal, CompanyPreset } from"./CompanyPresetsModal"
import { useSemanticSearch } from"@/hooks/search/useSemanticSearch"

export interface CompanyItem {
  name: string
  domain?: string
  linkedinUrl?: string
}

export type CompanyTimeFilter = 
  | 'current_past' 
  | 'current_only' 
  | 'past_only' 
  | 'specific_years' 
  | 'funding_stage'

interface CompanyFilterInputProps {
  value: CompanyItem[]
  onChange: (companies: CompanyItem[]) => void
  timeFilter?: CompanyTimeFilter
  onTimeFilterChange?: (filter: CompanyTimeFilter) => void
  specificYears?: { start: number; end: number }
  onSpecificYearsChange?: (years: { start: number; end: number }) => void
  fundingStages?: string[]
  onFundingStagesChange?: (stages: string[]) => void
  placeholder?: string
  showTimeFilter?: boolean
  showPresets?: boolean
}

const POPULAR_COMPANIES = [
  { name:"Nubank", domain:"nubank.com.br" },
  { name:"iFood", domain:"ifood.com.br" },
  { name:"Stone", domain:"stone.com.br" },
  { name:"PicPay", domain:"picpay.com" },
  { name:"Magalu", domain:"magazineluiza.com.br" },
  { name:"B3", domain:"b3.com.br" },
  { name:"Itaú", domain:"itau.com.br" },
  { name:"Bradesco", domain:"bradesco.com.br" },
  { name:"Santander", domain:"santander.com.br" },
  { name:"Ambev", domain:"ambev.com.br" },
  { name:"Vale", domain:"vale.com" },
  { name:"Petrobras", domain:"petrobras.com.br" },
  { name:"Globo", domain:"globo.com" },
  { name:"Natura", domain:"natura.com.br" },
  { name:"Localiza", domain:"localiza.com" },
  { name:"XP", domain:"xpinc.com" },
  { name:"BTG Pactual", domain:"btgpactual.com" },
  { name:"Mercado Livre", domain:"mercadolivre.com.br" },
  { name:"TOTVS", domain:"totvs.com" },
  { name:"VTEX", domain:"vtex.com" },
  { name:"Creditas", domain:"creditas.com" },
  { name:"QuintoAndar", domain:"quintoandar.com.br" },
  { name:"Loft", domain:"loft.com.br" },
  { name:"Kavak", domain:"kavak.com" },
  { name:"Rappi", domain:"rappi.com" },
  { name:"99", domain:"99app.com" },
  { name:"Movile", domain:"movile.com.br" },
  { name:"Wildlife Studios", domain:"wildlifestudios.com" },
  { name:"Loggi", domain:"loggi.com" },
  { name:"Olist", domain:"olist.com" },
  { name:"Ebanx", domain:"ebanx.com" },
  { name:"Gympass", domain:"gympass.com" },
  { name:"Google", domain:"google.com" },
  { name:"Meta", domain:"meta.com" },
  { name:"Amazon", domain:"amazon.com" },
  { name:"Microsoft", domain:"microsoft.com" },
  { name:"Apple", domain:"apple.com" },
  { name:"Netflix", domain:"netflix.com" },
  { name:"Salesforce", domain:"salesforce.com" },
  { name:"Oracle", domain:"oracle.com" },
  { name:"IBM", domain:"ibm.com" },
  { name:"SAP", domain:"sap.com" },
  { name:"Adobe", domain:"adobe.com" },
  { name:"Nvidia", domain:"nvidia.com" },
  { name:"Tesla", domain:"tesla.com" },
  { name:"SpaceX", domain:"spacex.com" },
  { name:"Uber", domain:"uber.com" },
  { name:"Airbnb", domain:"airbnb.com" },
  { name:"Stripe", domain:"stripe.com" },
  { name:"Databricks", domain:"databricks.com" },
  { name:"Snowflake", domain:"snowflake.com" },
  { name:"OpenAI", domain:"openai.com" },
  { name:"Anthropic", domain:"anthropic.com" },
]

const TIME_FILTER_OPTIONS: { 
  value: CompanyTimeFilter
  label: string
  description: string
}[] = [
  { 
    value: 'current_past', 
    label: 'Atual + Anterior',
    description: 'Encontrar pessoas que trabalham atualmente ou já trabalharam nas empresas selecionadas'
  },
  { 
    value: 'current_only', 
    label: 'Apenas Atual',
    description: 'Encontrar pessoas que trabalham atualmente nas empresas selecionadas'
  },
  { 
    value: 'past_only', 
    label: 'Apenas Anterior',
    description: 'Encontrar pessoas que trabalharam no passado nas empresas selecionadas'
  },
  { 
    value: 'specific_years', 
    label: 'Anos Específicos',
    description: 'Encontrar pessoas que trabalharam nas empresas selecionadas durante um período específico'
  },
  { 
    value: 'funding_stage', 
    label: 'Estágio de Funding',
    description: 'Encontrar pessoas que trabalharam nas empresas nos estágios de investimento selecionados'
  },
]

const FUNDING_STAGES = [
  'Pre-Seed', 'Seed', 'Series A', 'Series B', 'Series C', 
  'Series D+', 'Pre-IPO', 'Public'
]

export function CompanyFilterInput({
  value,
  onChange,
  timeFilter = 'current_past',
  onTimeFilterChange,
  specificYears,
  onSpecificYearsChange,
  fundingStages,
  onFundingStagesChange,
  placeholder ="Type company name and press Enter",
  showTimeFilter = true,
  showPresets = true
}: CompanyFilterInputProps) {
  const {
    inputValue, setInputValue,
    isDropdownOpen, setIsDropdownOpen,
    focusedIndex, setFocusedIndex,
    inputRef, dropdownRef,
    closeDropdown,
  } = useTagInputState()
  const [isLoadingAI, setIsLoadingAI] = useState(false)
  const [isFindingSimilar, setIsFindingSimilar] = useState(false)
  const [isPresetsModalOpen, setIsPresetsModalOpen] = useState(false)
  const [isTimeFilterOpen, setIsTimeFilterOpen] = useState(false)

  const { 
    suggestions: semanticSuggestions, 
    isLoading: isSemanticLoading, 
    search: searchSemantic,
    clearSuggestions
  } = useSemanticSearch({ domain:"companies", debounceMs: 400 })

  const existingCompanyNames = value.map(c => c.name.toLowerCase())

  const filteredSuggestions = inputValue.trim()
    ? POPULAR_COMPANIES.filter(company => 
        company.name.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingCompanyNames.includes(company.name.toLowerCase())
      ).slice(0, 6)
    : []

  const semanticItems = semanticSuggestions
    .filter(s => !existingCompanyNames.includes(s.term.toLowerCase()))
    .map(s => ({ type: 'semantic' as const, label: s.term, company: { name: s.term } as CompanyItem, confidence: s.confidence }))

  const showAskAI = inputValue.trim().length >= 2
  const dropdownItems = [
    ...semanticItems,
    ...(showAskAI && semanticItems.length === 0 ? [{ type: 'ai' as const, label: `Buscar concorrentes de"${inputValue}"`, company: null, confidence: 0 }] : []),
    ...filteredSuggestions.map(c => ({ type: 'company' as const, label: c.name, company: c, confidence: 0 }))
  ]

  const addCompany = useCallback((company: CompanyItem) => {
    if (!company.name.trim()) return
    if (existingCompanyNames.includes(company.name.toLowerCase())) return
    onChange([...value, company])
    setInputValue("")
    setIsDropdownOpen(false)
    setFocusedIndex(-1)
  }, [value, onChange, existingCompanyNames, setInputValue, setIsDropdownOpen, setFocusedIndex])

  const removeCompany = useCallback((name: string) => {
    onChange(value.filter(c => c.name !== name))
  }, [value, onChange])

  const clearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  const askAIForCompanies = useCallback(async (query: string) => {
    if (!query.trim()) return
    setIsLoadingAI(true)
    setIsDropdownOpen(false)
    
    try {
      const response = await fetch('/api/ai/suggest-companies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.suggestions && data.suggestions.length > 0) {
          const newCompanies = data.suggestions
            .filter((c: CompanyItem) => !existingCompanyNames.includes(c.name.toLowerCase()))
            .slice(0, 6)
          
          onChange([...value, ...newCompanies])
        }
      }
    } catch (error) {
    } finally {
      setIsLoadingAI(false)
      setInputValue("")
    }
  }, [value, onChange, existingCompanyNames, setInputValue, setIsDropdownOpen])

  const findSimilarCompanies = useCallback(async () => {
    if (value.length === 0) return
    setIsFindingSimilar(true)
    
    try {
      const response = await fetch('/api/ai/suggest-companies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ companies: value })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.suggestions && data.suggestions.length > 0) {
          const newCompanies = data.suggestions
            .filter((c: CompanyItem) => !existingCompanyNames.includes(c.name.toLowerCase()))
            .slice(0, 6)
          onChange([...value, ...newCompanies])
        }
      }
    } catch (error) {
    } finally {
      setIsFindingSimilar(false)
    }
  }, [value, onChange, existingCompanyNames])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (focusedIndex >= 0 && dropdownItems[focusedIndex]) {
        const item = dropdownItems[focusedIndex]
        if (item.type === 'ai') {
          askAIForCompanies(inputValue)
        } else if (item.company) {
          addCompany(item.company)
        }
      } else if (inputValue.trim()) {
        addCompany({ name: inputValue.trim() })
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setFocusedIndex(prev => Math.min(prev + 1, dropdownItems.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setFocusedIndex(prev => Math.max(prev - 1, -1))
    } else if (e.key === 'Escape') {
      setIsDropdownOpen(false)
      setFocusedIndex(-1)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    setIsDropdownOpen(newValue.length > 0)
    setFocusedIndex(-1)
    
    if (newValue.trim().length >= 2) {
      searchSemantic(newValue, value.map(c => c.name))
    } else {
      clearSuggestions()
    }
  }

  const handlePresetSelect = (companies: { name: string; domain?: string }[]) => {
    const newCompanies = companies.filter(
      c => !existingCompanyNames.includes(c.name.toLowerCase())
    )
    onChange([...value, ...newCompanies])
  }

  const currentTimeOption = TIME_FILTER_OPTIONS.find(o => o.value === timeFilter)
  const currentYear = new Date().getFullYear()

  return (
    <div className="space-y-3">
      {showTimeFilter && (
        <div className="flex items-center gap-2">
          <Popover open={isTimeFilterOpen} onOpenChange={setIsTimeFilterOpen}>
            <PopoverTrigger asChild>
              <button className="flex items-center gap-2 px-2.5 py-1 rounded-xl border border-lia-border-subtle text-xs hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none">
                <span className="text-lia-text-primary">{currentTimeOption?.label}</span>
                <ChevronDown className="w-3.5 h-3.5 text-lia-text-tertiary" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-80 p-0" align="start">
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

          {timeFilter === 'specific_years' && (
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={specificYears?.start || currentYear - 5}
                onChange={(e) => onSpecificYearsChange?.({
                  start: parseInt(e.target.value) || currentYear - 5,
                  end: specificYears?.end || currentYear
                })}
                className="w-20 text-sm"
                min={1990}
                max={currentYear}
              />
              <span className="text-lia-text-secondary">to</span>
              <Input
                type="number"
                value={specificYears?.end || currentYear}
                onChange={(e) => onSpecificYearsChange?.({
                  start: specificYears?.start || currentYear - 5,
                  end: parseInt(e.target.value) || currentYear
                })}
                className="w-20 text-sm"
                min={1990}
                max={currentYear}
              />
            </div>
          )}

          {timeFilter === 'funding_stage' && (
            <Popover>
              <PopoverTrigger asChild>
                <button className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-lia-border-subtle text-sm hover:bg-lia-bg-secondary">
                  <span className="text-lia-text-primary">
                    {fundingStages?.length ? `${fundingStages.length} selected` : 'Select stages'}
                  </span>
                  <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />
                </button>
              </PopoverTrigger>
              <PopoverContent className="w-48 p-2" align="start">
                <div className="space-y-1">
                  {FUNDING_STAGES.map(stage => (
                    <button
                      key={stage}
                      onClick={() => {
                        const current = fundingStages || []
                        if (current.includes(stage)) {
                          onFundingStagesChange?.(current.filter(s => s !== stage))
                        } else {
                          onFundingStagesChange?.([...current, stage])
                        }
                      }}
                      className={cn("w-full text-left px-2 py-1.5 rounded-md text-sm transition-colors",
                        fundingStages?.includes(stage)
                          ?"bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary"
                          :"hover:bg-lia-bg-secondary text-lia-text-primary"
                      )}
                    >
                      {stage}
                    </button>
                  ))}
                </div>
              </PopoverContent>
            </Popover>
          )}

          </div>
      )}

      <div className="flex items-center justify-end gap-3">
        <button
          onClick={clearAll}
          disabled={value.length === 0}
          className="text-xs text-lia-text-secondary hover:text-status-error flex items-center gap-1 transition-colors motion-reduce:transition-none disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:text-lia-text-secondary"
        >
          <RotateCcw className="w-3 h-3" />
          Limpar tudo
        </button>
        {showPresets && (
          <>
            <button
              onClick={() => {}}
              disabled={value.length === 0}
              className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-3 h-3" />
              Salvar Preset
            </button>
            <button
              onClick={() => setIsPresetsModalOpen(true)}
              className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1"
            >
              <List className="w-3 h-3" />
              Presets
            </button>
          </>
        )}
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
            disabled={isLoadingAI}
          />
          {isLoadingAI && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            </div>
          )}
        </div>

        {isDropdownOpen && dropdownItems.length > 0 && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-64 overflow-y-auto"
          >
            {dropdownItems.map((item, index) => (
              <button
                key={`${item.type}-${item.label}`}
                onClick={() => {
                  if (item.type === 'ai') {
                    askAIForCompanies(inputValue)
                  } else if (item.company) {
                    addCompany(item.company)
                  }
                }}
                className={cn("w-full text-left px-3 py-2 text-sm transition-colors",
                  focusedIndex === index ?"bg-lia-bg-tertiary" :"hover:bg-lia-bg-secondary",
                  item.type === 'ai' &&""
                )}
              >
                {item.type === 'ai' ? (
                  <div className="flex items-center gap-2 text-lia-text-secondary">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    <span>{item.label}</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <span className="text-lia-text-primary">{item.label}</span>
                    {item.company?.domain && (
                      <span className="text-xs text-lia-text-tertiary">{item.company.domain}</span>
                    )}
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {value.length > 0 && (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2">
            {value.map(company => (
              <Chip variant="neutral" muted
                key={company.name}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle"
              >
                <span>{company.name}</span>
                {company.domain && (
                  <span className="text-lia-text-tertiary text-micro">• {company.domain}</span>
                )}
                <button
                  onClick={() => removeCompany(company.name)}
                  className="hover:bg-lia-interactive-active rounded-md p-0.5 transition-colors motion-reduce:transition-none ml-1"
                  title="Remove"
                >
                  <X className="w-3 h-3" />
                </button>
              </Chip>
            ))}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={findSimilarCompanies}
            disabled={isFindingSimilar || value.length === 0}
            className="text-xs gap-1.5 border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover"
          >
            {isFindingSimilar ? (
              <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
            ) : (
              <Brain className="w-3 h-3 text-wedo-cyan" />
            )}
            Find Similar
          </Button>
        </div>
      )}

      <CompanyPresetsModal
        isOpen={isPresetsModalOpen}
        onClose={() => setIsPresetsModalOpen(false)}
        onSelectPreset={handlePresetSelect}
      />
    </div>
  )
}

export default CompanyFilterInput
