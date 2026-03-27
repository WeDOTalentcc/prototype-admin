"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { X, Search, ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

export type CompanyHQTimeFilter = 'current_past' | 'current_only'

interface CompanyHQLocationsInputProps {
  value: string[]
  onChange: (locations: string[]) => void
  timeFilter?: CompanyHQTimeFilter
  onTimeFilterChange?: (filter: CompanyHQTimeFilter) => void
  placeholder?: string
  disabled?: boolean
}

interface LocationItem {
  name: string
  type: 'city' | 'region'
}

const CITIES: LocationItem[] = [
  { name: "São Paulo, São Paulo, Brazil", type: 'city' },
  { name: "Campinas, São Paulo, Brazil", type: 'city' },
  { name: "Rio de Janeiro, Rio de Janeiro, Brazil", type: 'city' },
  { name: "Belo Horizonte, Minas Gerais, Brazil", type: 'city' },
  { name: "Curitiba, Paraná, Brazil", type: 'city' },
  { name: "Porto Alegre, Rio Grande do Sul, Brazil", type: 'city' },
  { name: "Brasília, Distrito Federal, Brazil", type: 'city' },
  { name: "Guarulhos, São Paulo, Brazil", type: 'city' },
  { name: "São Bernardo do Campo, São Paulo, Brazil", type: 'city' },
  { name: "Sorocaba, São Paulo, Brazil", type: 'city' },
  { name: "Salvador, Bahia, Brazil", type: 'city' },
  { name: "Fortaleza, Ceará, Brazil", type: 'city' },
  { name: "Recife, Pernambuco, Brazil", type: 'city' },
  { name: "San Francisco, California, United States", type: 'city' },
  { name: "New York, New York, United States", type: 'city' },
  { name: "London, United Kingdom", type: 'city' },
  { name: "Berlin, Germany", type: 'city' },
  { name: "Paris, France", type: 'city' },
  { name: "Singapore, Singapore", type: 'city' },
  { name: "Tokyo, Japan", type: 'city' },
]

const REGIONS: LocationItem[] = [
  { name: "São Paulo, Brazil", type: 'region' },
  { name: "Rio de Janeiro, Brazil", type: 'region' },
  { name: "California, United States", type: 'region' },
  { name: "New York, United States", type: 'region' },
  { name: "Texas, United States", type: 'region' },
  { name: "United Kingdom", type: 'region' },
  { name: "Germany", type: 'region' },
  { name: "France", type: 'region' },
]

const ALL_LOCATIONS = [...CITIES, ...REGIONS]

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
  placeholder = "Examples: San Francisco / United States / NYC / ...",
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
    ? CITIES.filter(loc => 
        loc.name.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingLocations.includes(loc.name.toLowerCase())
      ).slice(0, 5)
    : []

  const filteredRegions = inputValue.trim()
    ? REGIONS.filter(loc => 
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
              className={cn(
                "flex items-center gap-2 px-2.5 py-1 rounded-md border text-xs transition-colors",
                disabled 
                  ? "border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed" 
                  : "border-gray-200 hover:bg-gray-50 text-gray-800 dark:text-gray-200"
              )}
              disabled={disabled}
            >
              <span>{currentTimeOption?.label}</span>
              <ChevronDown className={cn("w-3.5 h-3.5", disabled ? "text-gray-300" : "text-gray-400")} />
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
                  className={cn(
                    "w-full text-left px-3 py-2 hover:bg-gray-50 transition-colors",
                    timeFilter === option.value && "bg-gray-50"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-gray-800 dark:text-gray-200">{option.label}</span>
                    {timeFilter === option.value && (
                      <div className="w-2 h-2 rounded-full bg-gray-900 dark:bg-gray-50" />
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{option.description}</p>
                </button>
              ))}
            </div>
          </PopoverContent>
        </Popover>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {value.length > 0 && (
            <span className="text-xs text-gray-500">
              {value.length} localidade{value.length !== 1 ? 's' : ''} selecionada{value.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        {value.length > 0 && !disabled && (
          <button
            onClick={clearAll}
            className="text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 font-medium"
          >
            Limpar tudo
          </button>
        )}
      </div>

      <div className="relative">
        <div className="relative">
          <Search className={cn("absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4", disabled ? "text-gray-300" : "text-gray-400")} />
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => !disabled && inputValue.length > 0 && setIsDropdownOpen(true)}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              "pl-9 pr-3 border-gray-200 focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400",
              disabled && "bg-gray-100 cursor-not-allowed"
            )}
          />
        </div>

        {isDropdownOpen && hasResults && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md max-h-64 overflow-y-auto"
          >
            {filteredCities.length > 0 && (
              <>
                <div className="px-3 py-1.5 text-xs font-semibold text-wedo-purple uppercase tracking-wide bg-gray-50 border-b border-gray-100">
                  Cities
                </div>
                {filteredCities.map((location, index) => (
                  <button
                    key={location.name}
                    onClick={() => addLocation(location.name)}
                    className={cn(
                      "w-full text-left px-3 py-2 text-sm transition-colors",
                      focusedIndex === index ? "bg-gray-100" : "hover:bg-gray-50"
                    )}
                  >
                    <span className="text-gray-800 dark:text-gray-200">{location.name}</span>
                  </button>
                ))}
              </>
            )}
            
            {filteredRegions.length > 0 && (
              <>
                <div className="px-3 py-1.5 text-xs font-semibold text-wedo-purple uppercase tracking-wide bg-gray-50 border-b border-gray-100 border-t">
                  Regions
                </div>
                {filteredRegions.map((location, index) => (
                  <button
                    key={location.name}
                    onClick={() => addLocation(location.name)}
                    className={cn(
                      "w-full text-left px-3 py-2 text-sm transition-colors",
                      focusedIndex === (filteredCities.length + index) ? "bg-gray-100" : "hover:bg-gray-50"
                    )}
                  >
                    <span className="text-gray-800 dark:text-gray-200">{location.name}</span>
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
            <Badge
              key={location}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:text-gray-200 border border-gray-200"
            >
              <span>{location}</span>
              <button
                onClick={() => removeLocation(location)}
                className="hover:bg-gray-200 rounded p-0.5 transition-colors ml-1"
                title="Remove"
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

export default CompanyHQLocationsInput
