"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { X, Search } from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"

interface UniversityLocationsInputProps {
  value: string[]
  onChange: (locations: string[]) => void
  placeholder?: string
}

interface LocationItem {
  name: string
  type: 'city' | 'country'
}

const CITIES: LocationItem[] = [
  { name: "New York, New York, United States", type: 'city' },
  { name: "London, England, United Kingdom", type: 'city' },
  { name: "Los Angeles, California, United States", type: 'city' },
  { name: "Houston, Texas, United States", type: 'city' },
  { name: "Chicago, Illinois, United States", type: 'city' },
  { name: "Philadelphia, Pennsylvania, United States", type: 'city' },
  { name: "São Paulo, São Paulo, Brazil", type: 'city' },
  { name: "Rio de Janeiro, Rio de Janeiro, Brazil", type: 'city' },
  { name: "Boston, Massachusetts, United States", type: 'city' },
  { name: "San Francisco, California, United States", type: 'city' },
  { name: "Seattle, Washington, United States", type: 'city' },
  { name: "Austin, Texas, United States", type: 'city' },
  { name: "Atlanta, Georgia, United States", type: 'city' },
  { name: "Toronto, Ontario, Canada", type: 'city' },
  { name: "Montreal, Quebec, Canada", type: 'city' },
  { name: "Vancouver, British Columbia, Canada", type: 'city' },
  { name: "Paris, Île-de-France, France", type: 'city' },
  { name: "Berlin, Berlin, Germany", type: 'city' },
  { name: "Munich, Bavaria, Germany", type: 'city' },
  { name: "Singapore, Singapore", type: 'city' },
  { name: "Hong Kong, Hong Kong", type: 'city' },
  { name: "Tokyo, Tokyo, Japan", type: 'city' },
  { name: "Sydney, New South Wales, Australia", type: 'city' },
  { name: "Melbourne, Victoria, Australia", type: 'city' },
  { name: "Beijing, Beijing, China", type: 'city' },
  { name: "Shanghai, Shanghai, China", type: 'city' },
  { name: "Seoul, Seoul, South Korea", type: 'city' },
  { name: "Mumbai, Maharashtra, India", type: 'city' },
  { name: "New Delhi, Delhi, India", type: 'city' },
  { name: "Bangalore, Karnataka, India", type: 'city' },
]

const COUNTRIES: LocationItem[] = [
  { name: "United States", type: 'country' },
  { name: "United Kingdom", type: 'country' },
  { name: "Brazil", type: 'country' },
  { name: "Germany", type: 'country' },
  { name: "France", type: 'country' },
  { name: "Canada", type: 'country' },
  { name: "Australia", type: 'country' },
  { name: "India", type: 'country' },
  { name: "China", type: 'country' },
  { name: "Japan", type: 'country' },
  { name: "South Korea", type: 'country' },
  { name: "Singapore", type: 'country' },
  { name: "Switzerland", type: 'country' },
  { name: "Netherlands", type: 'country' },
  { name: "Sweden", type: 'country' },
  { name: "Spain", type: 'country' },
  { name: "Italy", type: 'country' },
  { name: "Mexico", type: 'country' },
  { name: "Argentina", type: 'country' },
  { name: "Chile", type: 'country' },
]

export function UniversityLocationsInput({
  value,
  onChange,
  placeholder = "Examples: San Francisco / United States / NYC / ..."
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
            <span className="text-xs text-gray-500">
              {value.length} location{value.length !== 1 ? 's' : ''} selected
            </span>
            <button
              onClick={clearAll}
              className="text-xs text-gray-600 dark:text-gray-400 hover:text-[#50a3b8] font-medium"
            >
              Clear all
            </button>
          </>
        )}
      </div>

      <div className="relative">
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
            className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md max-h-64 overflow-y-auto"
          >
            {allItems.map((item, index) => {
              if (item.type === 'header') {
                return (
                  <div
                    key={`header-${item.label}`}
                    className="px-3 py-1.5 text-xs font-semibold text-purple-600 bg-gray-50 uppercase tracking-wider"
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

export default UniversityLocationsInput
