"use client"

import React, { useState, useRef, useEffect, useCallback } from "react"
import { Calendar, ChevronDown, ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export interface PeriodFilterValue {
  startDate: Date
  endDate: Date
  periodLabel: string
}

export interface PeriodFilterProps {
  value?: PeriodFilterValue
  onChange: (value: PeriodFilterValue) => void
  className?: string
}

type PeriodOption = "today" | "7days" | "30days" | "90days" | "year" | "custom"

const PERIOD_OPTIONS: { value: PeriodOption; label: string }[] = [
  { value: "today", label: "Hoje" },
  { value: "7days", label: "7 dias" },
  { value: "30days", label: "30 dias" },
  { value: "90days", label: "90 dias" },
  { value: "year", label: "Ano" },
  { value: "custom", label: "Personalizado" },
]

const MONTHS_PT = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

const DAYS_PT = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]

function calculatePeriodDates(period: PeriodOption): { startDate: Date; endDate: Date } {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const endDate = new Date(today)
  endDate.setHours(23, 59, 59, 999)
  let startDate = new Date(today)

  switch (period) {
    case "today":
      break
    case "7days":
      startDate.setDate(startDate.getDate() - 6)
      break
    case "30days":
      startDate.setDate(startDate.getDate() - 29)
      break
    case "90days":
      startDate.setDate(startDate.getDate() - 89)
      break
    case "year":
      startDate = new Date(today.getFullYear(), 0, 1)
      break
    default:
      break
  }

  return { startDate, endDate }
}

function formatDateShort(date: Date): string {
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })
}

function formatDateFull(date: Date): string {
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" })
}

function formatDateISO(date: Date): string {
  return date.toISOString().split("T")[0]
}

export function PeriodFilter({ value, onChange, className }: PeriodFilterProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodOption>("30days")
  const [showCustomPicker, setShowCustomPicker] = useState(false)
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [selecting, setSelecting] = useState<"start" | "end">("start")
  const [tempStart, setTempStart] = useState<Date | null>(null)
  const [tempEnd, setTempEnd] = useState<Date | null>(null)
  const pickerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (pickerRef.current && !pickerRef.current.contains(event.target as Node)) {
        setShowCustomPicker(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  useEffect(() => {
    if (!value) {
      const { startDate, endDate } = calculatePeriodDates("30days")
      onChange({ startDate, endDate, periodLabel: "30 dias" })
    }
  }, [])

  const handlePeriodChange = useCallback((period: PeriodOption) => {
    setSelectedPeriod(period)
    
    if (period === "custom") {
      setShowCustomPicker(true)
      setTempStart(value?.startDate || null)
      setTempEnd(value?.endDate || null)
    } else {
      setShowCustomPicker(false)
      const { startDate, endDate } = calculatePeriodDates(period)
      const label = PERIOD_OPTIONS.find(p => p.value === period)?.label || ""
      onChange({ startDate, endDate, periodLabel: label })
    }
  }, [onChange, value])

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startingDay = firstDay.getDay()

    const days: (Date | null)[] = []

    for (let i = 0; i < startingDay; i++) {
      days.push(null)
    }

    for (let i = 1; i <= daysInMonth; i++) {
      days.push(new Date(year, month, i))
    }

    return days
  }

  const isDateInRange = (date: Date) => {
    if (!tempStart || !tempEnd) return false
    return date >= tempStart && date <= tempEnd
  }

  const isDateSelected = (date: Date) => {
    if (tempStart && formatDateISO(date) === formatDateISO(tempStart)) return true
    if (tempEnd && formatDateISO(date) === formatDateISO(tempEnd)) return true
    return false
  }

  const handleDateClick = (date: Date) => {
    if (selecting === "start") {
      setTempStart(date)
      setTempEnd(null)
      setSelecting("end")
    } else {
      if (tempStart && date < tempStart) {
        setTempEnd(tempStart)
        setTempStart(date)
      } else {
        setTempEnd(date)
      }
      setSelecting("start")
    }
  }

  const handleApplyCustom = () => {
    if (tempStart && tempEnd) {
      const startDate = new Date(tempStart)
      startDate.setHours(0, 0, 0, 0)
      const endDate = new Date(tempEnd)
      endDate.setHours(23, 59, 59, 999)
      
      const label = `${formatDateShort(startDate)} - ${formatDateShort(endDate)}`
      onChange({ startDate, endDate, periodLabel: label })
      setShowCustomPicker(false)
    }
  }

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1))
  }

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1))
  }

  const days = getDaysInMonth(currentMonth)

  const getDisplayValue = () => {
    if (selectedPeriod === "custom" && value) {
      return `${formatDateShort(value.startDate)} - ${formatDateShort(value.endDate)}`
    }
    return PERIOD_OPTIONS.find(p => p.value === selectedPeriod)?.label || ""
  }

  return (
    <div className={`relative inline-flex items-center gap-2 ${className}`}>
      <div className="flex items-center gap-1.5 text-sm lia-text-secondary">
        <Calendar className="w-4 h-4 text-lia-text-secondary" />
        <span className="font-medium">Período:</span>
      </div>

      <Select value={selectedPeriod} onValueChange={(v) => handlePeriodChange(v as PeriodOption)}>
        <SelectTrigger 
          className="w-[160px] h-9 text-sm border-lia-border-subtle focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
          
        >
          <SelectValue placeholder="Selecionar período" />
        </SelectTrigger>
        <SelectContent>
          {PERIOD_OPTIONS.map((option) => (
            <SelectItem 
              key={option.value} 
              value={option.value}
              className="text-sm cursor-pointer"
            >
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {showCustomPicker && (
        <div ref={pickerRef} className="absolute top-full left-0 mt-2 z-50">
          <Card className="p-4 bg-lia-bg-primary min-w-[320px]">
            <div className="flex items-center justify-between mb-4">
              <button
                onClick={prevMonth}
                className="p-1.5 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
              >
                <ChevronLeft className="w-4 h-4 text-lia-text-secondary" />
              </button>
              <span className="text-sm font-medium text-lia-text-primary">
                {MONTHS_PT[currentMonth.getMonth()]} {currentMonth.getFullYear()}
              </span>
              <button
                onClick={nextMonth}
                className="p-1.5 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
              >
                <ChevronRight className="w-4 h-4 text-lia-text-secondary" />
              </button>
            </div>

            <div className="grid grid-cols-7 gap-1 mb-2">
              {DAYS_PT.map((day) => (
                <div
                  key={day}
                  className="text-center text-xs lia-text-secondary py-1"
                 
                >
                  {day}
                </div>
              ))}
            </div>

            <div className="grid grid-cols-7 gap-1">
              {days.map((date, index) => {
                if (!date) {
                  return <div key={`empty-${index}`} className="h-8" />
                }

                const isSelected = isDateSelected(date)
                const isInRange = isDateInRange(date)
                const isToday = formatDateISO(date) === formatDateISO(new Date())

                return (
                  <button
                    key={formatDateISO(date)}
                    onClick={() => handleDateClick(date)}
                    className={`
 h-8 text-xs rounded-md transition-colors
                      ${isSelected
                        ? "bg-gray-900 text-white font-medium"
                        : isInRange
                          ? "bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-primary"
                          : "hover:bg-gray-100 text-lia-text-primary"
                      }
                      ${isToday && !isSelected ? "ring-1 ring-gray-900/20" : ""}
                    `}
                   
                  >
                    {date.getDate()}
                  </button>
                )
              })}
            </div>

            {tempStart && tempEnd && (
              <div className="mt-3 pt-3 border-t border-lia-border-subtle">
                <p className="text-xs text-lia-text-secondary mb-2">
                  Selecionado: <span className="font-medium text-lia-text-primary">
                    {formatDateFull(tempStart)} - {formatDateFull(tempEnd)}
                  </span>
                </p>
              </div>
            )}

            <div className="flex gap-2 mt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCustomPicker(false)}
                className="flex-1 text-xs"
              >
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={handleApplyCustom}
                disabled={!tempStart || !tempEnd}
                className="flex-1 text-xs text-white bg-gray-900"
              >
                Aplicar
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
