"use client"

import { useState } from "react"
import { ChevronDown, Check, Info } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface TimezoneOption {
  value: string
  label: string
  offset: string
  group?: string
}

const TIMEZONE_OPTIONS: TimezoneOption[] = [
  { value: 'EST', label: 'Eastern Standard Time', offset: 'UTC-5:00', group: 'North America' },
  { value: 'CST', label: 'Central Standard Time', offset: 'UTC-6:00' },
  { value: 'MST', label: 'Mountain Standard Time', offset: 'UTC-7:00' },
  { value: 'PST', label: 'Pacific Standard Time', offset: 'UTC-8:00' },
  { value: 'AKST', label: 'Alaska Standard Time', offset: 'UTC-9:00' },
  { value: 'HST', label: 'Hawaii Standard Time', offset: 'UTC-10:00' },
  { value: 'AST', label: 'Atlantic Standard Time', offset: 'UTC-4:00' },
  { value: 'NST', label: 'Newfoundland Standard Time', offset: 'UTC-3:30' },
  { value: 'BRT', label: 'Brasília Time', offset: 'UTC-3:00', group: 'South America' },
  { value: 'ART', label: 'Argentina Time', offset: 'UTC-3:00' },
  { value: 'CLT', label: 'Chile Standard Time', offset: 'UTC-4:00' },
  { value: 'GMT', label: 'GMT/UTC', offset: 'UTC+0:00', group: 'Europe' },
  { value: 'CET', label: 'Central European Time', offset: 'UTC+1:00' },
  { value: 'EET', label: 'Eastern European Time', offset: 'UTC+2:00' },
  { value: 'IST', label: 'India Standard Time', offset: 'UTC+5:30', group: 'Asia/Pacific' },
  { value: 'CST_CN', label: 'China Standard Time', offset: 'UTC+8:00' },
  { value: 'JST', label: 'Japan Standard Time', offset: 'UTC+9:00' },
  { value: 'AEST', label: 'Australian Eastern Time', offset: 'UTC+10:00' },
]

interface TimezoneDropdownProps {
  value: string | null
  onChange: (value: string | null) => void
  className?: string
  showLabel?: boolean
}

export function TimezoneDropdown({ 
  value, 
  onChange,
  className,
  showLabel = true
}: TimezoneDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)

  const selectedOption = value ? TIMEZONE_OPTIONS.find(o => o.value === value) : null

  const groupedOptions: { group: string; options: TimezoneOption[] }[] = []
  let currentGroup: { group: string; options: TimezoneOption[] } | null = null
  
  for (const option of TIMEZONE_OPTIONS) {
    if (option.group) {
      currentGroup = { group: option.group, options: [option] }
      groupedOptions.push(currentGroup)
    } else if (currentGroup) {
      currentGroup.options.push(option)
    } else {
      currentGroup = { group: 'North America', options: [option] }
      groupedOptions.push(currentGroup)
    }
  }

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      {showLabel && (
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Fuso Horário</span>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="w-3.5 h-3.5 text-gray-400 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p className="text-xs">Filter candidates by their timezone</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      )}
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <button 
            className={cn(
              "flex items-center justify-between gap-2 px-3 py-2 rounded-md border border-gray-200",
              "text-sm text-gray-800 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 dark:border-gray-700 transition-colors w-full",
              !selectedOption && "text-gray-400"
            )}
          >
            <span className="truncate text-xs">
              {selectedOption 
                ? `${selectedOption.label} (${selectedOption.offset})`
                : 'Selecionar fuso horário'
              }
            </span>
            <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-72 p-0 rounded-md dark:bg-gray-800 dark:border-gray-700" align="start">
          <div className="py-1 max-h-80 overflow-y-auto">
            {value && (
              <button
                onClick={() => {
                  onChange(null)
                  setIsOpen(false)
                }}
                className="w-full text-left px-3 py-2 text-xs text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700"
              >
                Limpar seleção
              </button>
            )}
            {groupedOptions.map((group, groupIndex) => (
              <div key={group.group}>
                {group.group !== 'default' && (
                  <div className="px-3 py-1.5 text-xs font-semibold text-[#8B5CF6] bg-gray-50 dark:bg-gray-700 border-t border-gray-100 dark:border-gray-700">
                    {group.group}
                  </div>
                )}
                {group.options.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => {
                      onChange(option.value)
                      setIsOpen(false)
                    }}
                    className={cn(
                      "w-full text-left px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors",
                      value === option.value && "bg-gray-50 dark:bg-gray-700"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex flex-col">
                        <span className={cn(
                          "text-xs",
 value === option.value ? "font-medium text-gray-950" : "text-gray-800 dark:text-gray-200"
                        )}>
                          {option.label}
                        </span>
                        <span className="text-[10px] text-gray-400 dark:text-gray-500">{option.offset}</span>
                      </div>
                      {value === option.value && (
                        <Check className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            ))}
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}

export default TimezoneDropdown
