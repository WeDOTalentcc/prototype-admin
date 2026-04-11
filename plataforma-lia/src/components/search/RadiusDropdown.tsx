"use client"

import { useState } from "react"
import { ChevronDown, Check } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

export type RadiusValue = 
  | 'exact' 
  | '15mi' | '25mi' | '50mi' | '100mi' | '150mi' | '200mi' 
  | '15km' | '25km' | '50km' | '100km' | '200km'

interface RadiusOption {
  value: RadiusValue
  label: string
  description?: string
  isSeparator?: boolean
}

const RADIUS_OPTIONS: RadiusOption[] = [
  { 
    value: 'exact', 
    label: 'Localização exata',
    description: 'Encontrar pessoas exatamente na(s) localização(ões) selecionada(s)'
  },
  { value: '15mi', label: 'Até 25 km' },
  { value: '25mi', label: 'Até 40 km' },
  { value: '50mi', label: 'Até 80 km' },
  { value: '100mi', label: 'Até 160 km' },
  { value: '150mi', label: 'Até 240 km' },
  { value: '200mi', label: 'Até 320 km' },
  { value: '15km', label: 'Até 15 km', isSeparator: true },
  { value: '25km', label: 'Até 25 km' },
  { value: '50km', label: 'Até 50 km' },
  { value: '100km', label: 'Até 100 km' },
  { value: '200km', label: 'Até 200 km' },
]

interface RadiusDropdownProps {
  value: RadiusValue
  onChange: (value: RadiusValue) => void
  className?: string
}

export function RadiusDropdown({ 
  value, 
  onChange,
  className 
}: RadiusDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)

  const selectedOption = RADIUS_OPTIONS.find(o => o.value === value) || RADIUS_OPTIONS[2]

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <button 
          className={cn(
            "flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-lia-border-subtle",
            "text-xs font-medium text-lia-text-primary hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse dark:border-lia-border-subtle transition-colors motion-reduce:transition-none",
            className
          )}
        >
          <span>{selectedOption.label}</span>
          <ChevronDown className="w-3.5 h-3.5 text-lia-text-tertiary" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-0 rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle" align="start">
        <div className="py-1 max-h-80 overflow-y-auto">
          {RADIUS_OPTIONS.map((option, index) => (
            <div key={option.value}>
              {option.isSeparator && (
                <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle my-1" />
              )}
              <button
                onClick={() => {
                  onChange(option.value)
                  setIsOpen(false)
                }}
                className={cn(
                  "w-full text-left px-3 py-2 hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse transition-colors motion-reduce:transition-none",
                  value === option.value && "bg-lia-bg-secondary dark:bg-lia-bg-elevated"
                )}
              >
                <div className="flex items-center justify-between">
                  <span className={cn(
                    "text-xs",
 value === option.value ? "font-medium text-lia-text-primary" : "text-lia-text-primary"
                  )}>
                    {option.label}
                  </span>
                  {value === option.value && (
                    <Check className="w-4 h-4 text-lia-text-secondary" />
                  )}
                </div>
                {option.description && (
                  <p className="text-xs text-lia-text-secondary mt-0.5">{option.description}</p>
                )}
              </button>
            </div>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}

export default RadiusDropdown
