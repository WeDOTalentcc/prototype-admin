"use client"

import React from "react"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Search } from "lucide-react"
import { statusOptions, planOptions } from "./types"

export interface ClientFiltersProps {
  search: string
  onSearchChange: (value: string) => void
  status: string
  onStatusChange: (value: string) => void
  planFilter?: string
  onPlanFilterChange?: (value: string) => void
  total?: number
  isLoading?: boolean
  mounted?: boolean
}

export function ClientFilters({
  search,
  onSearchChange,
  status,
  onStatusChange,
  planFilter,
  onPlanFilterChange,
  total = 0,
  isLoading = false,
  mounted = true,
}: ClientFiltersProps) {
  return (
    <div className="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle p-4 mb-6">
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 lia-text-secondary" />
          <Input
            placeholder="Buscar por nome, CNPJ ou email..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex flex-col sm:flex-row gap-4">
          {mounted ? (
            <>
              <Select value={status} onValueChange={onStatusChange}>
                <SelectTrigger className="w-full sm:w-[180px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  {statusOptions.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {onPlanFilterChange && (
                <Select value={planFilter || 'all'} onValueChange={onPlanFilterChange}>
                  <SelectTrigger className="w-full sm:w-[180px]">
                    <SelectValue placeholder="Plano" />
                  </SelectTrigger>
                  <SelectContent>
                    {planOptions.map(opt => (
                      <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </>
          ) : (
            <>
              <div className="w-full sm:w-[180px] h-10 bg-gray-100 dark:bg-lia-bg-elevated rounded-md animate-pulse motion-reduce:animate-none" />
              {onPlanFilterChange && (
                <div className="w-full sm:w-[180px] h-10 bg-gray-100 dark:bg-lia-bg-elevated rounded-md animate-pulse motion-reduce:animate-none" />
              )}
            </>
          )}
        </div>
      </div>
      <div className="mt-3 text-xs text-lia-text-tertiary dark:text-lia-text-tertiary">
        {isLoading ? (
          <span>Carregando...</span>
        ) : (
          <span>{total} cliente{total !== 1 ? 's' : ''} encontrado{total !== 1 ? 's' : ''}</span>
        )}
      </div>
    </div>
  )
}
