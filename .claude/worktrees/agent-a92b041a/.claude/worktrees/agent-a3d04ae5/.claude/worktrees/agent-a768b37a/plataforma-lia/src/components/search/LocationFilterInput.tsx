"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { X, Search, Save, List, RotateCcw } from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { RadiusDropdown, RadiusValue } from "./RadiusDropdown"
import { TimezoneDropdown } from "./TimezoneDropdown"
import { LocationPresetsModal, LocationItem } from "./LocationPresetsModal"
export type { LocationItem }

interface LocationFilterInputProps {
  value: LocationItem[]
  onChange: (locations: LocationItem[]) => void
  radius?: RadiusValue
  onRadiusChange?: (radius: RadiusValue) => void
  timezone?: string | null
  onTimezoneChange?: (timezone: string | null) => void
  placeholder?: string
  showRadius?: boolean
  showTimezone?: boolean
  showPresets?: boolean
}

interface LocationData {
  name: string
  type: 'city' | 'country' | 'region'
}

const CITIES: LocationData[] = [
  { name: "New York, New York, United States", type: 'city' },
  { name: "San Francisco, California, United States", type: 'city' },
  { name: "Los Angeles, California, United States", type: 'city' },
  { name: "Chicago, Illinois, United States", type: 'city' },
  { name: "Houston, Texas, United States", type: 'city' },
  { name: "Seattle, Washington, United States", type: 'city' },
  { name: "Austin, Texas, United States", type: 'city' },
  { name: "Boston, Massachusetts, United States", type: 'city' },
  { name: "Denver, Colorado, United States", type: 'city' },
  { name: "Atlanta, Georgia, United States", type: 'city' },
  { name: "Miami, Florida, United States", type: 'city' },
  { name: "Dallas, Texas, United States", type: 'city' },
  { name: "São Paulo, São Paulo, Brazil", type: 'city' },
  { name: "Sao Paulo, São Paulo, Brazil", type: 'city' },
  { name: "Rio de Janeiro, Rio de Janeiro, Brazil", type: 'city' },
  { name: "Belo Horizonte, Minas Gerais, Brazil", type: 'city' },
  { name: "Campinas, São Paulo, Brazil", type: 'city' },
  { name: "Guarulhos, São Paulo, Brazil", type: 'city' },
  { name: "São Bernardo do Campo, São Paulo, Brazil", type: 'city' },
  { name: "Sorocaba, São Paulo, Brazil", type: 'city' },
  { name: "Curitiba, Paraná, Brazil", type: 'city' },
  { name: "Porto Alegre, Rio Grande do Sul, Brazil", type: 'city' },
  { name: "London, England, United Kingdom", type: 'city' },
  { name: "Manchester, England, United Kingdom", type: 'city' },
  { name: "Paris, Île-de-France, France", type: 'city' },
  { name: "Berlin, Berlin, Germany", type: 'city' },
  { name: "Munich, Bavaria, Germany", type: 'city' },
  { name: "Amsterdam, North Holland, Netherlands", type: 'city' },
  { name: "Tokyo, Tokyo, Japan", type: 'city' },
  { name: "Osaka, Osaka, Japan", type: 'city' },
  { name: "Singapore, Singapore", type: 'city' },
  { name: "Hong Kong, Hong Kong", type: 'city' },
  { name: "Sydney, New South Wales, Australia", type: 'city' },
  { name: "Melbourne, Victoria, Australia", type: 'city' },
  { name: "Toronto, Ontario, Canada", type: 'city' },
  { name: "Vancouver, British Columbia, Canada", type: 'city' },
  { name: "Mumbai, Maharashtra, India", type: 'city' },
  { name: "Delhi, Delhi, India", type: 'city' },
  { name: "Bangalore, Karnataka, India", type: 'city' },
  { name: "Shanghai, Shanghai, China", type: 'city' },
  { name: "Beijing, Beijing, China", type: 'city' },
  { name: "Mexico City, Ciudad de México, Mexico", type: 'city' },
  { name: "Buenos Aires, Buenos Aires, Argentina", type: 'city' },
]

const COUNTRIES: LocationData[] = [
  { name: "United States", type: 'country' },
  { name: "Brazil", type: 'country' },
  { name: "United Kingdom", type: 'country' },
  { name: "Germany", type: 'country' },
  { name: "France", type: 'country' },
  { name: "Canada", type: 'country' },
  { name: "Australia", type: 'country' },
  { name: "India", type: 'country' },
  { name: "China", type: 'country' },
  { name: "Japan", type: 'country' },
  { name: "Singapore", type: 'country' },
  { name: "Mexico", type: 'country' },
  { name: "Argentina", type: 'country' },
  { name: "Portugal", type: 'country' },
  { name: "Spain", type: 'country' },
  { name: "Italy", type: 'country' },
  { name: "Netherlands", type: 'country' },
  { name: "Switzerland", type: 'country' },
  { name: "Sweden", type: 'country' },
  { name: "Ireland", type: 'country' },
  { name: "São Tomé and Príncipe", type: 'country' },
]

const REGIONS: LocationData[] = [
  { name: "California", type: 'region' },
  { name: "Texas", type: 'region' },
  { name: "Florida", type: 'region' },
  { name: "New York (state)", type: 'region' },
  { name: "Washington", type: 'region' },
  { name: "Massachusetts", type: 'region' },
  { name: "Colorado", type: 'region' },
  { name: "Illinois", type: 'region' },
  { name: "Georgia", type: 'region' },
  { name: "São Paulo (state)", type: 'region' },
  { name: "Rio de Janeiro (state)", type: 'region' },
  { name: "Minas Gerais", type: 'region' },
  { name: "Paraná", type: 'region' },
  { name: "Rio Grande do Sul", type: 'region' },
  { name: "Ontario", type: 'region' },
  { name: "Quebec", type: 'region' },
  { name: "British Columbia", type: 'region' },
  { name: "Bavaria", type: 'region' },
  { name: "England", type: 'region' },
  { name: "Scotland", type: 'region' },
  { name: "Wales", type: 'region' },
  { name: "New South Wales", type: 'region' },
  { name: "Victoria", type: 'region' },
]

export function LocationFilterInput({
  value,
  onChange,
  radius = '25mi',
  onRadiusChange,
  timezone = null,
  onTimezoneChange,
  placeholder = "Type location and press Enter (city, country, or region)",
  showRadius = true,
  showTimezone = true,
  showPresets = true
}: LocationFilterInputProps) {
  const [inputValue, setInputValue] = useState("")
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const [isPresetsModalOpen, setIsPresetsModalOpen] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const existingLocations = value.map(l => l.value.toLowerCase())

  const filteredCities = inputValue.trim()
    ? CITIES.filter(loc => 
        loc.name.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingLocations.includes(loc.name.toLowerCase())
      ).slice(0, 6)
    : []

  const filteredCountries = inputValue.trim()
    ? COUNTRIES.filter(loc => 
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

  const hasResults = filteredCities.length > 0 || filteredCountries.length > 0 || filteredRegions.length > 0

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

  const addLocation = useCallback((location: LocationData) => {
    if (!location.name.trim()) return
    if (existingLocations.includes(location.name.toLowerCase())) return
    onChange([...value, { value: location.name, type: location.type }])
    setInputValue("")
    setIsDropdownOpen(false)
    setFocusedIndex(-1)
  }, [value, onChange, existingLocations])

  const removeLocation = useCallback((locationValue: string) => {
    onChange(value.filter(l => l.value !== locationValue))
  }, [value, onChange])

  const clearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  const getAllItems = () => {
    const items: { type: 'header' | 'item'; label: string; data?: LocationData }[] = []
    
    if (filteredCities.length > 0) {
      items.push({ type: 'header', label: 'CITIES' })
      filteredCities.forEach(city => {
        items.push({ type: 'item', label: city.name, data: city })
      })
    }
    
    if (filteredCountries.length > 0) {
      items.push({ type: 'header', label: 'COUNTRIES' })
      filteredCountries.forEach(country => {
        items.push({ type: 'item', label: country.name, data: country })
      })
    }

    if (filteredRegions.length > 0) {
      items.push({ type: 'header', label: 'REGIONS' })
      filteredRegions.forEach(region => {
        items.push({ type: 'item', label: region.name, data: region })
      })
    }
    
    return items
  }

  const allItems = getAllItems()
  const selectableItems = allItems.filter(item => item.type === 'item')

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (focusedIndex >= 0 && selectableItems[focusedIndex]?.data) {
        addLocation(selectableItems[focusedIndex].data!)
      } else if (inputValue.trim()) {
        addLocation({ name: inputValue.trim(), type: 'city' })
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setFocusedIndex(prev => Math.min(prev + 1, selectableItems.length - 1))
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

  const handlePresetSelect = (locations: LocationItem[]) => {
    const newLocations = locations.filter(
      loc => !existingLocations.includes(loc.value.toLowerCase())
    )
    onChange([...value, ...newLocations])
  }

  let selectableIndex = -1

  const getTypeLabel = (type: 'city' | 'country' | 'region') => {
    switch (type) {
      case 'city': return 'CITY'
      case 'country': return 'COUNTRY'
      case 'region': return 'REGION'
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-[#8B5CF6]">Localização</span>
          {showRadius && onRadiusChange && (
            <RadiusDropdown value={radius} onChange={onRadiusChange} />
          )}
        </div>
        <div className="flex items-center gap-3">
          {value.length > 0 && (
            <button
              onClick={clearAll}
              className="text-xs text-gray-500 hover:text-red-600 flex items-center gap-1 transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              Limpar tudo
            </button>
          )}
          {showPresets && (
            <>
              <button
                onClick={() => {}}
                disabled={value.length === 0}
                className="text-xs text-gray-600 hover:text-gray-800 flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="w-3.5 h-3.5" />
                Salvar Preset
              </button>
              <button
                onClick={() => setIsPresetsModalOpen(true)}
                className="text-xs text-gray-600 hover:text-gray-800 flex items-center gap-1"
              >
                <List className="w-3.5 h-3.5" />
                Presets
              </button>
            </>
          )}
        </div>
      </div>
      {showTimezone && onTimezoneChange && (
        <div className="flex justify-end">
          <div className="w-64">
            <TimezoneDropdown 
              value={timezone} 
              onChange={onTimezoneChange}
              showLabel={true}
            />
          </div>
        </div>
      )}

      <div className="flex gap-4">
        <div className="flex-1 relative">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => inputValue.length > 0 && setIsDropdownOpen(true)}
              placeholder={placeholder}
              className="pl-9 pr-3 border-gray-200 focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
            />
          </div>

          {isDropdownOpen && hasResults && (
            <div 
              ref={dropdownRef}
              className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md max-h-80 overflow-y-auto"
            >
              {allItems.map((item, index) => {
                if (item.type === 'header') {
                  return (
                    <div 
                      key={`header-${item.label}`}
                      className="px-3 py-1.5 text-xs font-semibold text-[#8B5CF6] bg-gray-50 border-t border-gray-100 first:border-t-0"
                    >
                      {item.label}
                    </div>
                  )
                }
                
                selectableIndex++
                const currentSelectableIndex = selectableIndex
                
                return (
                  <button
                    key={`item-${item.label}`}
                    onClick={() => item.data && addLocation(item.data)}
                    className={cn(
                      "w-full text-left px-3 py-2 text-sm transition-colors",
                      focusedIndex === currentSelectableIndex ? "bg-gray-100" : "hover:bg-gray-50"
                    )}
                  >
                    <span className="text-gray-800 dark:text-gray-200">{item.label}</span>
                  </button>
                )
              })}
            </div>
          )}

          {value.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {value.map(location => (
                <Badge
                  key={location.value}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:text-gray-200 border border-gray-200"
                >
                  <span className="text-[10px] font-semibold text-gray-500 uppercase">
                    {getTypeLabel(location.type)}
                  </span>
                  <span>{location.value.split(',')[0]}</span>
                  <button
                    onClick={() => removeLocation(location.value)}
                    className="hover:bg-gray-200 rounded p-0.5 transition-colors ml-0.5"
                    title="Remove"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>

      <LocationPresetsModal
        isOpen={isPresetsModalOpen}
        onClose={() => setIsPresetsModalOpen(false)}
        onSelectPreset={handlePresetSelect}
      />
    </div>
  )
}

export default LocationFilterInput
