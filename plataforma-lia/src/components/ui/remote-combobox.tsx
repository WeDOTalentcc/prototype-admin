"use client"

import * as React from "react"
import { Check, ChevronsUpDown, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

export interface RemoteComboboxOption {
  id: string | number
  name: string
  description?: string
}

interface RemoteComboboxProps {
  value: RemoteComboboxOption | null
  onChange: (value: RemoteComboboxOption | null) => void
  options: RemoteComboboxOption[]
  isLoading?: boolean
  onSearchChange?: (query: string) => void
  placeholder?: string
  emptyText?: string
  disabled?: boolean
  className?: string
  triggerClassName?: string
  readOnly?: boolean
}

export function RemoteCombobox({
  value, onChange, options, isLoading, onSearchChange,
  placeholder = "Selecionar…", emptyText = "Nenhum resultado",
  disabled = false, className, triggerClassName, readOnly = false,
}: RemoteComboboxProps) {
  const [open, setOpen] = React.useState(false)
  const [query, setQuery] = React.useState("")

  React.useEffect(() => {
    if (!onSearchChange) return
    const t = setTimeout(() => onSearchChange(query), 250)
    return () => clearTimeout(t)
  }, [query, onSearchChange])

  const label = value?.name ?? placeholder
  const buttonDisabled = disabled || readOnly

  return (
    <div className={className}>
      <Popover open={open} onOpenChange={buttonDisabled ? undefined : setOpen}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            role="combobox"
            aria-expanded={open}
            disabled={buttonDisabled}
            className={cn(
              "w-full justify-between h-9 text-xs font-normal",
              !value && "text-lia-text-tertiary",
              triggerClassName,
            )}
          >
            <span className="truncate">{label}</span>
            <ChevronsUpDown className="ml-2 h-3.5 w-3.5 shrink-0 opacity-50" aria-hidden="true" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="p-0 w-[var(--radix-popover-trigger-width)]" align="start">
          <Command shouldFilter={!onSearchChange}>
            <CommandInput
              value={query}
              onValueChange={setQuery}
              placeholder="Buscar…"
              className="h-9"
            />
            <CommandList>
              {isLoading && (
                <div className="flex items-center justify-center py-4 text-lia-text-tertiary">
                  <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                </div>
              )}
              {!isLoading && options.length === 0 && (
                <CommandEmpty>{emptyText}</CommandEmpty>
              )}
              {!isLoading && options.length > 0 && (
                <CommandGroup>
                  {options.map((option) => (
                    <CommandItem
                      key={`${option.id}`}
                      value={option.name}
                      onSelect={() => {
                        onChange(option)
                        setOpen(false)
                      }}
                    >
                      <Check
                        className={cn(
                          "mr-2 h-4 w-4",
                          value?.id === option.id ? "opacity-100" : "opacity-0",
                        )}
                        aria-hidden="true"
                      />
                      <span className="truncate">{option.name}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  )
}
