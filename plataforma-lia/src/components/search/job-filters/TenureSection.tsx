"use client"

import { Clock, TrendingUp, Info } from "lucide-react"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import type { SearchFilters } from '../hooks/useAdvancedFiltersCore'
import { timeInRoleOptions, tenureOptions } from '../advancedFiltersTypes'

export interface TenureSectionProps {
  filters: SearchFilters
  updateFilter: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string | string[] | number | boolean | null) => void
}

export const TenureSection = ({ filters, updateFilter }: TenureSectionProps) => {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="p-3 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
        <div className="flex items-center gap-1.5 mb-2">
          <Clock className="w-4 h-4 text-lia-text-secondary" />
          <Label className="text-xs font-medium">Tempo na Função Atual</Label>
          <Popover>
            <PopoverTrigger asChild>
              <button className="text-lia-text-tertiary hover:text-lia-text-secondary">
                <Info className="w-3 h-3" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-2 bg-lia-bg-elevated text-xs">
              Filtrar candidatos pelo tempo que estão no cargo atual
            </PopoverContent>
          </Popover>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-lia-text-secondary">Entre</span>
          <Select
            value={filters.job?.timeInRoleMin || "no_limit"}
            onValueChange={(value) => updateFilter("job", "timeInRoleMin", value)}
          >
            <SelectTrigger className="h-7 flex-1 text-xs border-lia-border-subtle">
              <SelectValue placeholder="Sem limite" />
            </SelectTrigger>
            <SelectContent className="bg-lia-bg-secondary">
              {timeInRoleOptions.map(opt => (
                <SelectItem key={opt.value} value={opt.value} className="text-xs">
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="text-xs text-lia-text-secondary">e</span>
          <Select
            value={filters.job?.timeInRoleMax || "no_limit"}
            onValueChange={(value) => updateFilter("job", "timeInRoleMax", value)}
          >
            <SelectTrigger className="h-7 flex-1 text-xs border-lia-border-subtle">
              <SelectValue placeholder="Sem limite" />
            </SelectTrigger>
            <SelectContent className="bg-lia-bg-secondary">
              {timeInRoleOptions.map(opt => (
                <SelectItem key={opt.value} value={opt.value} className="text-xs">
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="p-3 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
        <div className="flex items-center gap-1.5 mb-2">
          <TrendingUp className="w-4 h-4 text-lia-text-secondary" />
          <Label className="text-xs font-medium">Tempo Médio nas Empresas</Label>
          <Popover>
            <PopoverTrigger asChild>
              <button className="text-lia-text-tertiary hover:text-lia-text-secondary">
                <Info className="w-3 h-3" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-2 bg-lia-bg-elevated text-xs">
              Candidatos com média de permanência mínima em cada empresa
            </PopoverContent>
          </Popover>
        </div>
        <Select
          value={filters.job?.minAverageTenure || "no_limit"}
          onValueChange={(value) => updateFilter("job", "minAverageTenure", value)}
        >
          <SelectTrigger className="h-7 text-xs border-lia-border-subtle">
            <SelectValue placeholder="Selecionar duração" />
          </SelectTrigger>
          <SelectContent className="bg-lia-bg-secondary">
            {tenureOptions.map(opt => (
              <SelectItem key={opt.value} value={opt.value} className="text-xs">
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
