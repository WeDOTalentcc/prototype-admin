"use client"

import { cn } from "@/lib/utils"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"

interface GraduationYearInputProps {
  minYear: number | null
  maxYear: number | null
  onMinYearChange: (year: number | null) => void
  onMaxYearChange: (year: number | null) => void
}

const MAX_YEAR = 2028
const MIN_YEAR = 1950
const YEARS = Array.from({ length: MAX_YEAR - MIN_YEAR + 1 }, (_, i) => MAX_YEAR - i)

export function GraduationYearInput({
  minYear,
  maxYear,
  onMinYearChange,
  onMaxYearChange
}: GraduationYearInputProps) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <Label className="text-xs mb-1.5 block font-medium text-lia-text-secondary">
          Ano de Formatura (Mín)
        </Label>
        <Select
          value={minYear?.toString() || "not_selected"}
          onValueChange={(val) => onMinYearChange(val === "not_selected" ? null : parseInt(val))}
        >
          <SelectTrigger className="border-lia-border-subtle focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 bg-lia-bg-secondary text-xs">
            <SelectValue placeholder="Não selecionado" />
          </SelectTrigger>
          <SelectContent className="bg-lia-bg-secondary max-h-64">
            <SelectItem 
              value="not_selected"
              className={cn(
                "py-2 text-xs",
                minYear === null && "text-lia-text-primary"
              )}
            >
              Não selecionado
            </SelectItem>
            {YEARS.map(year => (
              <SelectItem 
                key={year} 
                value={year.toString()}
                className="py-2 text-xs"
                disabled={maxYear !== null && year > maxYear}
              >
                {year}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label className="text-xs mb-1.5 block font-medium text-lia-text-secondary">
          Ano de Formatura (Máx)
        </Label>
        <Select
          value={maxYear?.toString() || "not_selected"}
          onValueChange={(val) => onMaxYearChange(val === "not_selected" ? null : parseInt(val))}
        >
          <SelectTrigger className="border-lia-border-subtle focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 bg-lia-bg-secondary text-xs">
            <SelectValue placeholder="Não selecionado" />
          </SelectTrigger>
          <SelectContent className="bg-lia-bg-secondary max-h-64">
            <SelectItem 
              value="not_selected"
              className={cn(
                "py-2 text-xs",
                maxYear === null && "text-lia-text-primary"
              )}
            >
              Não selecionado
            </SelectItem>
            {YEARS.map(year => (
              <SelectItem 
                key={year} 
                value={year.toString()}
                className="py-2 text-xs"
                disabled={minYear !== null && year < minYear}
              >
                {year}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}

export default GraduationYearInput
