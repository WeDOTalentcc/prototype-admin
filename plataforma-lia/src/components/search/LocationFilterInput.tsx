"use client"

import { useState, useRef, useEffect, useCallback } from"react"
import { X, Search, Save, List, RotateCcw } from"lucide-react"
import { cn } from"@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { RadiusDropdown, RadiusValue } from"./RadiusDropdown"
import { TimezoneDropdown } from"./TimezoneDropdown"
import { LocationPresetsModal, LocationItem } from"./LocationPresetsModal"
export type { LocationItem }
import { LOCATION_CITIES as CITIES, LOCATION_COUNTRIES as COUNTRIES, LOCATION_REGIONS as REGIONS, LocationData } from"@/data/location-data"

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


export function LocationFilterInput({
  value,
  onChange,
  radius = '25mi',
  onRadiusChange,
  timezone = null,
  onTimezoneChange,
  placeholder ="Type location and press Enter (city, country, or region)",
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
          <span className="text-xs font-semibold text-lia-text-secondary">Localização</span>
          {showRadius && onRadiusChange && (
            <RadiusDropdown value={radius} onChange={onRadiusChange} />
          )}
        </div>
        <div className="flex items-center gap-3">
          {value.length > 0 && (
            <button
              onClick={clearAll}
              className="text-xs text-lia-text-secondary hover:text-status-error flex items-center gap-1 transition-colors motion-reduce:transition-none"
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
                className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="w-3.5 h-3.5" />
                Salvar Preset
              </button>
              <button
                onClick={() => setIsPresetsModalOpen(true)}
                className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1"
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

          {isDropdownOpen && hasResults && (
            <div 
              ref={dropdownRef}
              className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-80 overflow-y-auto"
            >
              {allItems.map((item, index) => {
                if (item.type === 'header') {
                  return (
                    <div 
                      key={`header-${item.label}`}
                      className="px-3 py-1.5 text-xs font-semibold text-lia-text-secondary bg-lia-bg-secondary border-t border-lia-border-subtle first:border-t-0"
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
                    className={cn("w-full text-left px-3 py-2 text-sm transition-colors",
                      focusedIndex === currentSelectableIndex ?"bg-lia-bg-tertiary" :"hover:bg-lia-bg-secondary"
                    )}
                  >
                    <span className="text-lia-text-primary">{item.label}</span>
                  </button>
                )
              })}
            </div>
          )}

          {value.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {value.map(location => (
                <Chip variant="neutral" muted
                  key={location.value}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle"
                >
                  <span className="text-micro font-semibold text-lia-text-secondary uppercase">
                    {getTypeLabel(location.type)}
                  </span>
                  <span>{location.value.split(',')[0]}</span>
                  <button
                    onClick={() => removeLocation(location.value)}
                    className="hover:bg-lia-interactive-active rounded-md p-0.5 transition-colors motion-reduce:transition-none ml-0.5"
                    title="Remove"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Chip>
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
