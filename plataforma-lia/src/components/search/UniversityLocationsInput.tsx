"use client"

import { useState, useRef, useEffect, useCallback } from"react"
import { X, Search } from"lucide-react"
import { cn } from"@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"
import { UNIVERSITY_CITIES as CITIES, UNIVERSITY_COUNTRIES as COUNTRIES } from"@/data/location-data"

interface UniversityLocationsInputProps {
  value: string[]
  onChange: (locations: string[]) => void
  placeholder?: string
}


export function UniversityLocationsInput({
  value,
  onChange,
  placeholder ="Examples: San Francisco / United States / NYC / ..."
}: UniversityLocationsInputProps) {
  const [inputValue, setInputValue] = useState("")
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const existingLocations = value.map(l => l.toLowerCase())

  const filteredCities = inputValue.trim()
    ? CITIES.filter(loc => 
        loc.name.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingLocations.includes(loc.name.toLowerCase())
      ).slice(0, 5)
    : []

  const filteredCountries = inputValue.trim()
    ? COUNTRIES.filter(loc => 
        loc.name.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingLocations.includes(loc.name.toLowerCase())
      ).slice(0, 5)
    : []

  const hasResults = filteredCities.length > 0 || filteredCountries.length > 0

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
    if (!location.trim()) return
    if (existingLocations.includes(location.toLowerCase())) return
    onChange([...value, location])
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

  const getAllItems = () => {
    const items: { type: 'header' | 'item'; label: string; value?: string }[] = []
    
    if (filteredCities.length > 0) {
      items.push({ type: 'header', label: 'CITIES' })
      filteredCities.forEach(city => {
        items.push({ type: 'item', label: city.name, value: city.name })
      })
    }
    
    if (filteredCountries.length > 0) {
      items.push({ type: 'header', label: 'COUNTRIES' })
      filteredCountries.forEach(country => {
        items.push({ type: 'item', label: country.name, value: country.name })
      })
    }
    
    return items
  }

  const allItems = getAllItems()
  const selectableItems = allItems.filter(item => item.type === 'item')

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (focusedIndex >= 0 && selectableItems[focusedIndex]) {
        addLocation(selectableItems[focusedIndex].value!)
      } else if (inputValue.trim()) {
        addLocation(inputValue.trim())
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

  let selectableIndex = -1

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        {value.length > 0 && (
          <>
            <span className="text-xs text-lia-text-secondary">
              {value.length} location{value.length !== 1 ? 's' : ''} selected
            </span>
            <button
              onClick={clearAll}
              className="text-xs text-lia-text-secondary hover:text-lia-text-primary font-medium"
            >
              Clear all
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
          />
        </div>

        {isDropdownOpen && hasResults && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-64 overflow-y-auto"
          >
            {allItems.map((item, index) => {
              if (item.type === 'header') {
                return (
                  <div
                    key={`header-${item.label}`}
                    className="px-3 py-1.5 text-xs font-semibold text-wedo-purple-text bg-lia-bg-secondary uppercase tracking-wider"
                  >
                    {item.label}
                  </div>
                )
              }
              
              selectableIndex++
              const currentSelectableIndex = selectableIndex
              
              return (
                <button
                  key={`item-${item.value}`}
                  onClick={() => addLocation(item.value!)}
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

export default UniversityLocationsInput
