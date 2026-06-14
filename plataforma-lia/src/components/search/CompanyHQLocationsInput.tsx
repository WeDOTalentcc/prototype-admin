"use client"

import { useState, useRef, useEffect, useCallback } from"react"
import { X, Search, ChevronDown } from"lucide-react"
import { cn } from"@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"
import { COMPANY_HQ_CITIES, COMPANY_HQ_REGIONS } from"@/data/location-data"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"

export type CompanyHQTimeFilter = 'current_past' | 'current_only'

interface CompanyHQLocationsInputProps {
  value: string[]
  onChange: (locations: string[]) => void
  timeFilter?: CompanyHQTimeFilter
  onTimeFilterChange?: (filter: CompanyHQTimeFilter) => void
  placeholder?: string
  disabled?: boolean
}

const ALL_LOCATIONS = [...COMPANY_HQ_CITIES, ...COMPANY_HQ_REGIONS]

const TIME_FILTER_OPTIONS: { 
  value: CompanyHQTimeFilter
  label: string
  description: string
}[] = [
  { 
    value: 'current_past', 
    label: 'Atual + Anterior',
    description: 'Encontrar pessoas que trabalham ou já trabalharam em empresas sediadas nestas localidades'
  },
  { 
    value: 'current_only', 
    label: 'Apenas Atual',
    description: 'Encontrar pessoas que trabalham atualmente em empresas sediadas nestas localidades'
  },
]

export function CompanyHQLocationsInput({
  value,
  onChange,
  timeFilter = 'current_past',
  onTimeFilterChange,
  placeholder ="Examples: San Francisco / United States / NYC / ...",
  disabled = false
}: CompanyHQLocationsInputProps) {
  const [inputValue, setInputValue] = useState("")
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const [isTimeFilterOpen, setIsTimeFilterOpen] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const existingLocations = value.map(l => l.toLowerCase())

  const filteredCities = inputValue.trim()
    ? COMPANY_HQ_CITIES.filter(loc => 
        loc.name.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingLocations.includes(loc.name.toLowerCase())
      ).slice(0, 5)
    : []

  const filteredRegions = inputValue.trim()
    ? COMPANY_HQ_REGIONS.filter(loc => 
        loc.name.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingLocations.includes(loc.name.toLowerCase())
      ).slice(0, 5)
    : []

  const hasResults = filteredCities.length > 0 || filteredRegions.length > 0

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
          inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const addLocation = useCallback((location: string) => {
    const trimmed = location.trim()
    if (!trimmed) return
    if (existingLocations.includes(trimmed.toLowerCase())) return
    onChange([...value, trimmed])
    setInputValue("")
    setIsDropdownOpen(false)
    setFocusedIndex(-1)
  }, [value, onChange, existingLocations])

  const removeLocation = useCallback((location: string) => {
    onChange(value.filter(l => l !== location))
  }, [value, onChange])

  const clearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      const allItems = [...filteredCities, ...filteredRegions]
      if (focusedIndex >= 0 && allItems[focusedIndex]) {
        addLocation(allItems[focusedIndex].name)
      } else if (inputValue.trim()) {
        addLocation(inputValue)
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      const totalItems = filteredCities.length + filteredRegions.length
      setFocusedIndex(prev => Math.min(prev + 1, totalItems - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setFocusedIndex(prev => Math.max(prev - 1, -1))
    } else if (e.key === 'Escape') {
      setIsDropdownOpen(false)
      setFocusedIndex(-1)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value)
    setIsDropdownOpen(e.target.value.length > 0)
    setFocusedIndex(-1)
  }

  const currentTimeOption = TIME_FILTER_OPTIONS.find(o => o.value === timeFilter)

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Popover open={!disabled && isTimeFilterOpen} onOpenChange={disabled ? undefined : setIsTimeFilterOpen}>
          <PopoverTrigger asChild>
            <button 
              className={cn("flex items-center gap-2 px-2.5 py-1 rounded-md border text-xs transition-colors",
                disabled 
                  ?"border-lia-border-subtle bg-lia-bg-tertiary text-lia-text-tertiary cursor-not-allowed" 
                  :"border-lia-border-subtle hover:bg-lia-bg-secondary text-lia-text-primary"
              )}
              disabled={disabled}
            >
              <span>{currentTimeOption?.label}</span>
              <ChevronDown className={cn("w-3.5 h-3.5", disabled ?"text-lia-text-disabled" :"text-lia-text-tertiary")} />
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
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {value.length > 0 && (
            <span className="text-xs text-lia-text-secondary">
              {value.length} localidade{value.length !== 1 ? 's' : ''} selecionada{value.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        {value.length > 0 && !disabled && (
          <button
            onClick={clearAll}
            className="text-xs text-lia-text-secondary hover:text-lia-text-primary font-medium"
          >
            Limpar tudo
          </button>
        )}
      </div>

      <div className="relative">
        <div className="relative">
          <Search className={cn("absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4", disabled ?"text-lia-text-disabled" :"text-lia-text-tertiary")} />
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => !disabled && inputValue.length > 0 && setIsDropdownOpen(true)}
            placeholder={placeholder}
            disabled={disabled}
            className={cn("pl-9 pr-3 border-lia-border-subtle focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium",
              disabled &&"bg-lia-bg-tertiary cursor-not-allowed"
            )}
          />
        </div>

        {isDropdownOpen && hasResults && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-64 overflow-y-auto"
          >
            {filteredCities.length > 0 && (
              <>
                <div className="px-3 py-1.5 text-xs font-semibold text-wedo-purple-text uppercase tracking-wide bg-lia-bg-secondary">
                  Cities
                </div>
                {filteredCities.map((location, index) => (
                  <button
                    key={location.name}
                    onClick={() => addLocation(location.name)}
                    className={cn("w-full text-left px-3 py-2 text-sm transition-colors",
                      focusedIndex === index ?"bg-lia-bg-tertiary" :"hover:bg-lia-bg-secondary"
                    )}
                  >
                    <span className="text-lia-text-primary">{location.name}</span>
                  </button>
                ))}
              </>
            )}
            
            {filteredRegions.length > 0 && (
              <>
                <div className="px-3 py-1.5 text-xs font-semibold text-wedo-purple-text uppercase tracking-wide bg-lia-bg-secondary border-t">
                  Regions
                </div>
                {filteredRegions.map((location, index) => (
                  <button
                    key={location.name}
                    onClick={() => addLocation(location.name)}
                    className={cn("w-full text-left px-3 py-2 text-sm transition-colors",
                      focusedIndex === (filteredCities.length + index) ?"bg-lia-bg-tertiary" :"hover:bg-lia-bg-secondary"
                    )}
                  >
                    <span className="text-lia-text-primary">{location.name}</span>
                  </button>
                ))}
              </>
            )}
          </div>
        )}
      </div>

      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map(location => (
            <Chip variant="neutral" muted
              key={location}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle"
            >
              <span>{location}</span>
              <button
                onClick={() => removeLocation(location)}
                className="hover:bg-lia-interactive-active rounded-md p-0.5 transition-colors motion-reduce:transition-none ml-1"
                title="Remove"
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

export default CompanyHQLocationsInput
