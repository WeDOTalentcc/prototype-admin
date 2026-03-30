"use client"

import { useState, useRef, useEffect } from "react"
import { ChevronDown, Info } from "lucide-react"
import { cn } from "@/lib/utils"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

interface DegreeRequirementsInputProps {
  mode: 'regular' | 'nested'
  onModeChange: (mode: 'regular' | 'nested') => void
  value: string | null
  onChange: (degree: string | null) => void
}

const DEGREE_OPTIONS = [
  { value: "not_selected", label: "Não selecionado" },
  { value: "associates_or_above", label: "Técnico ou Superior" },
  { value: "bachelors_or_above", label: "Graduação ou Superior" },
  { value: "masters_or_above", label: "Mestrado ou Superior" },
  { value: "doctorate", label: "Doutorado" },
  { value: "only_bachelors", label: "Apenas Graduação" },
  { value: "only_masters", label: "Apenas Mestrado" },
]

export function DegreeRequirementsInput({
  mode,
  onModeChange,
  value,
  onChange
}: DegreeRequirementsInputProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  return (
    <div className="space-y-3">
      <div className="relative inline-block" ref={dropdownRef}>
        <button
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-[width,height]",
            mode === 'regular'
              ? "border-lia-border-default bg-lia-bg-primary lia-text-800 dark:text-lia-text-primary"
              : "border-gray-900 dark:lia-border-50 bg-gray-100 dark:bg-lia-bg-secondary lia-text-900 dark:lia-text-50"
          )}
        >
          {mode === 'regular' ? 'Regular' : 'Nested'}
          <ChevronDown className="w-3 h-3" />
        </button>

        {isDropdownOpen && (
          <div className="absolute z-50 mt-1 w-72 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
            <button
              onClick={() => {
                onModeChange('regular')
                setIsDropdownOpen(false)
              }}
              className={cn(
                "w-full text-left px-4 py-3 transition-colors motion-reduce:transition-none hover:bg-gray-50 rounded-t-lg",
                mode === 'regular' && "bg-gray-50"
              )}
            >
              <div className="flex items-center gap-2">
                <div className={cn(
                  "w-3 h-3 rounded-full border-2",
                  mode === 'regular' 
                    ? "border-gray-700 bg-gray-700" 
                    : "border-lia-border-default"
                )}>
                  {mode === 'regular' && (
                    <div className="w-full h-full rounded-full bg-lia-bg-primary scale-50" />
                  )}
                </div>
                <span className="font-medium text-sm lia-text-800">Regular</span>
              </div>
              <p className="text-xs lia-text-500 mt-1 ml-5">
                Find people who have this degree from any university
              </p>
            </button>

            <button
              onClick={() => {
                onModeChange('nested')
                setIsDropdownOpen(false)
              }}
              className={cn(
                "w-full text-left px-4 py-3 transition-colors motion-reduce:transition-none hover:bg-gray-50 rounded-b-lg border-t border-lia-border-subtle",
                mode === 'nested' && "bg-gray-50 dark:bg-lia-bg-secondary/50"
              )}
            >
              <div className="flex items-center gap-2">
                <div className={cn(
                  "w-3 h-3 rounded-full border-2",
                  mode === 'nested' 
                    ? "border-gray-900 bg-gray-900 dark:lia-border-50 dark:lia-bg-50" 
                    : "border-lia-border-default"
                )}>
                  {mode === 'nested' && (
                    <div className="w-full h-full rounded-full bg-lia-bg-primary scale-50" />
                  )}
                </div>
                <span className="font-medium text-sm lia-text-800">Nested</span>
              </div>
              <p className="text-xs lia-text-500 mt-1 ml-5">
                Find people who have this degree from selected universities
              </p>
            </button>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Popover>
          <PopoverTrigger asChild>
            <button className="lia-text-400 hover:lia-text-600 transition-colors motion-reduce:transition-none">
              <Info className="w-3.5 h-3.5" />
            </button>
          </PopoverTrigger>
          <PopoverContent className="w-64 p-3 text-xs bg-lia-bg-elevated" side="right">
            <p className="lia-text-600 leading-relaxed">
              <strong>Regular:</strong> Matches candidates with this degree from any university.
            </p>
            <p className="lia-text-600 leading-relaxed mt-2">
              <strong>Nested:</strong> Only matches candidates who have this degree from the universities you've selected above.
            </p>
          </PopoverContent>
        </Popover>
      </div>

      <Select
        value={value || "not_selected"}
        onValueChange={(val) => onChange(val === "not_selected" ? null : val)}
      >
        <SelectTrigger className="border-lia-border-subtle focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 bg-lia-bg-secondary text-xs">
          <SelectValue placeholder="Selecione o grau" />
        </SelectTrigger>
        <SelectContent className="bg-lia-bg-secondary">
          {DEGREE_OPTIONS.map(option => (
            <SelectItem 
              key={option.value} 
              value={option.value}
              className={cn(
                "py-2 text-xs",
                option.value === "not_selected" && value === null && "lia-text-800 dark:text-lia-text-primary"
              )}
            >
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

export default DegreeRequirementsInput
