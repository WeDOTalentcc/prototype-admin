"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Calendar, ChevronLeft, ChevronRight, X } from "lucide-react"

interface DateRange {
  start_date: string
  end_date: string
}

interface DateRangePickerProps {
  value?: DateRange
  onChange: (range: DateRange) => void
  className?: string
  placeholder?: string
}

const MONTHS_PT = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

const DAYS_PT = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']

const PRESET_RANGES = [
  { label: 'Últimos 7 dias', days: 7 },
  { label: 'Últimos 30 dias', days: 30 },
  { label: 'Últimos 90 dias', days: 90 },
  { label: 'Este mês', type: 'this_month' },
  { label: 'Mês passado', type: 'last_month' },
  { label: 'Este trimestre', type: 'this_quarter' },
]

export function DateRangePicker({ value, onChange, className, placeholder = "Selecionar período" }: DateRangePickerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [selecting, setSelecting] = useState<'start' | 'end'>('start')
  const [tempStart, setTempStart] = useState<Date | null>(value?.start_date ? new Date(value.start_date) : null)
  const [tempEnd, setTempEnd] = useState<Date | null>(value?.end_date ? new Date(value.end_date) : null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
  }

  const formatDateISO = (date: Date) => {
    return date.toISOString().split('T')[0]
  }

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
    if (selecting === 'start') {
      setTempStart(date)
      setTempEnd(null)
      setSelecting('end')
    } else {
      if (tempStart && date < tempStart) {
        setTempEnd(tempStart)
        setTempStart(date)
      } else {
        setTempEnd(date)
      }
      setSelecting('start')
    }
  }

  const handleApply = () => {
    if (tempStart && tempEnd) {
      onChange({
        start_date: formatDateISO(tempStart),
        end_date: formatDateISO(tempEnd)
      })
      setIsOpen(false)
    }
  }

  const handlePreset = (preset: typeof PRESET_RANGES[number]) => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    let start: Date
    let end: Date = new Date(today)

    if ('days' in preset) {
      start = new Date(today)
      start.setDate(start.getDate() - (preset as { days: number }).days)
    } else if (preset.type === 'this_month') {
      start = new Date(today.getFullYear(), today.getMonth(), 1)
      end = new Date(today.getFullYear(), today.getMonth() + 1, 0)
    } else if (preset.type === 'last_month') {
      start = new Date(today.getFullYear(), today.getMonth() - 1, 1)
      end = new Date(today.getFullYear(), today.getMonth(), 0)
    } else if (preset.type === 'this_quarter') {
      const quarter = Math.floor(today.getMonth() / 3)
      start = new Date(today.getFullYear(), quarter * 3, 1)
      end = new Date(today.getFullYear(), (quarter + 1) * 3, 0)
    } else {
      start = new Date(today)
    }

    setTempStart(start)
    setTempEnd(end)
    onChange({
      start_date: formatDateISO(start),
      end_date: formatDateISO(end)
    })
    setIsOpen(false)
  }

  const handleClear = () => {
    setTempStart(null)
    setTempEnd(null)
    onChange({ start_date: '', end_date: '' })
    setIsOpen(false)
  }

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1))
  }

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1))
  }

  const days = getDaysInMonth(currentMonth)

  const displayValue = value?.start_date && value?.end_date
    ? `${formatDate(new Date(value.start_date))} - ${formatDate(new Date(value.end_date))}`
    : placeholder

  return (
    <div ref={containerRef} className={`relative inline-block ${className}`}>
      <Button
        variant="outline"
        onClick={() => setIsOpen(!isOpen)}
        className="gap-2 text-xs min-w-sidebar-content justify-start"
      >
        <Calendar className="w-4 h-4 text-lia-text-secondary" />
        <span className={value?.start_date ? 'text-lia-text-primary' : 'lia-text-secondary'}>
          {displayValue}
        </span>
        {value?.start_date && (
          <X 
            className="w-4 h-4 ml-auto text-lia-text-secondary hover:text-lia-text-secondary" 
            onClick={(e) => {
              e.stopPropagation()
              handleClear()
            }}
          />
        )}
      </Button>

      {isOpen && (
        <Card className="absolute z-50 mt-2 p-4 bg-lia-bg-primary min-w-[360px]">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-4">
                <button 
                  onClick={prevMonth}
                  className="p-1 hover:bg-lia-interactive-hover rounded-md"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-xs font-medium text-lia-text-primary">
                  {MONTHS_PT[currentMonth.getMonth()]} {currentMonth.getFullYear()}
                </span>
                <button 
                  onClick={nextMonth}
                  className="p-1 hover:bg-lia-interactive-hover rounded-md"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-7 gap-1 mb-2">
                {DAYS_PT.map(day => (
                  <div key={day} className="text-center text-xs text-lia-text-secondary py-1">
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
                          ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text font-medium' 
                          : isInRange 
                            ? 'bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-primary' 
                            : 'hover:bg-lia-interactive-hover text-lia-text-primary'
                        }
                        ${isToday && !isSelected ? 'ring-1 ring-lia-border-medium' : ''}
                      `}
                    >
                      {date.getDate()}
                    </button>
                  )
                })}
              </div>

              <div className="flex gap-2 mt-4">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setIsOpen(false)}
                  className="flex-1 text-xs"
                >
                  Cancelar
                </Button>
                <Button 
                  size="sm" 
                  onClick={handleApply}
                  disabled={!tempStart || !tempEnd}
                  className="flex-1 text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                >
                  Aplicar
                </Button>
              </div>
            </div>

            <div className="border-l pl-4 w-40">
              <p className="text-xs font-medium text-lia-text-secondary mb-2">Atalhos</p>
              <div className="space-y-1">
                {PRESET_RANGES.map((preset) => (
                  <button
                    key={preset.label}
                    onClick={() => handlePreset(preset)}
                    className="w-full text-left text-xs py-1.5 px-2 rounded-md hover:bg-lia-interactive-hover text-lia-text-primary transition-colors motion-reduce:transition-none"
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
