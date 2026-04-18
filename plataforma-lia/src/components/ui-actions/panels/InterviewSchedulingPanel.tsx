"use client"

import React, { useState, useMemo } from"react"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Label } from"@/components/ui/label"
import { Checkbox } from"@/components/ui/checkbox"
import { Chip } from "@/components/ui/chip"
import { Textarea } from"@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from"@/components/ui/select"
import { Popover, PopoverContent, PopoverTrigger } from"@/components/ui/popover"
import { 
  Loader2, 
  Calendar as CalendarIcon, 
  Clock, 
  MapPin, 
  Video, 
  Phone, 
  Users,
  ChevronLeft,
  ChevronRight
} from"lucide-react"
import { InterviewSlot, InterviewSchedulingData } from"../types"

interface PanelProps {
  initialData?: Record<string, unknown>
  onSubmit: (data: unknown) => Promise<void>
  isLoading?: boolean
}

type InterviewType ="presencial" |"teams" |"meet" |"telefone"
type Duration = 30 | 45 | 60 | 90

const INTERVIEW_TYPES: { value: InterviewType; label: string; icon: React.ReactNode }[] = [
  { value:"presencial", label:"Presencial", icon: <MapPin className="h-4 w-4" /> },
  { value:"teams", label:"Teams", icon: <Video className="h-4 w-4" /> },
  { value:"meet", label:"Google Meet", icon: <Video className="h-4 w-4" /> },
  { value:"telefone", label:"Telefone", icon: <Phone className="h-4 w-4" /> }
]

const DURATION_OPTIONS: { value: Duration; label: string }[] = [
  { value: 30, label:"30 minutos" },
  { value: 45, label:"45 minutos" },
  { value: 60, label:"1 hora" },
  { value: 90, label:"1h30" }
]

const MOCK_INTERVIEWERS = [
  { id:"1", name:"Ana Silva", role:"Tech Lead" },
  { id:"2", name:"Carlos Santos", role:"Engineering Manager" },
  { id:"3", name:"Maria Oliveira", role:"HR Business Partner" },
  { id:"4", name:"João Costa", role:"Senior Developer" },
  { id:"5", name:"Fernanda Lima", role:"Product Manager" }
]

const TIME_SLOTS = ["08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30","12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30","16:00","16:30","17:00","17:30","18:00"
]

function formatDate(date: Date): string {
  return date.toISOString().split("T")[0]
}

function formatDisplayDate(date: Date): string {
  return date.toLocaleDateString("pt-BR", {
    weekday:"long",
    day:"numeric",
    month:"long"
  })
}

function generateAvailableSlots(date: Date): string[] {
  const dayOfWeek = date.getDay()
  if (dayOfWeek === 0 || dayOfWeek === 6) return []
  
  const seed = date.getDate() + date.getMonth()
  return TIME_SLOTS.filter((_, index) => (index + seed) % 3 !== 0)
}

export function InterviewSchedulingPanel({
  initialData = {},
  onSubmit,
  isLoading = false
}: PanelProps) {
  const candidateName = (initialData.candidate_name as string) ||"Candidato"
  const candidateId = (initialData.candidate_id as string) ||""

  const [selectedDate, setSelectedDate] = useState<Date>(() => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    while (tomorrow.getDay() === 0 || tomorrow.getDay() === 6) {
      tomorrow.setDate(tomorrow.getDate() + 1)
    }
    return tomorrow
  })
  const [selectedTime, setSelectedTime] = useState<string | null>(null)
  const [duration, setDuration] = useState<Duration>(60)
  const [interviewType, setInterviewType] = useState<InterviewType>("teams")
  const [selectedInterviewers, setSelectedInterviewers] = useState<string[]>([])
  const [notes, setNotes] = useState<string>("")
  const [currentMonth, setCurrentMonth] = useState(new Date())

  const availableSlots = useMemo(() => {
    return generateAvailableSlots(selectedDate)
  }, [selectedDate])

  const handleToggleInterviewer = (interviewerId: string) => {
    setSelectedInterviewers((prev) =>
      prev.includes(interviewerId)
        ? prev.filter((id) => id !== interviewerId)
        : [...prev, interviewerId]
    )
  }

  const handleSubmit = async () => {
    if (!selectedTime) return

    const slot: InterviewSlot = {
      id: `slot_${Date.now()}`,
      date: formatDate(selectedDate),
      time: selectedTime,
      duration,
      type: interviewType,
      available: true
    }

    const data: InterviewSchedulingData = {
      candidate_id: candidateId,
      candidate_name: candidateName,
      selected_slot: slot,
      interviewers: selectedInterviewers,
      notes: notes || undefined
    }
    await onSubmit(data)
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

  const isDateSelectable = (date: Date | null) => {
    if (!date) return false
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const dayOfWeek = date.getDay()
    return date >= today && dayOfWeek !== 0 && dayOfWeek !== 6
  }

  const handlePrevMonth = () => {
    setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1))
  }

  const handleNextMonth = () => {
    setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1))
  }

  const days = getDaysInMonth(currentMonth)
  const monthLabel = currentMonth.toLocaleDateString("pt-BR", { month:"long", year:"numeric" })

  return (
    <div className="space-y-6">
      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 font-sans text-lia-text-primary">
            👤 Candidato
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm font-medium text-lia-text-primary">{candidateName}</p>
          {candidateId && (
            <p className="text-xs text-lia-text-tertiary">ID: {candidateId}</p>
          )}
        </CardContent>
      </Card>

      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 font-sans text-lia-text-primary">
            <CalendarIcon className="h-4 w-4 text-lia-text-secondary" />
            Data da Entrevista
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-xl p-3 dark:border-lia-border-subtle border border-lia-border-subtle">
            <div className="flex items-center justify-between mb-4">
              <Button variant="ghost" size="icon" className="dark:text-lia-text-secondary dark:hover:bg-lia-bg-inverse" onClick={handlePrevMonth}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm font-medium capitalize text-lia-text-primary">{monthLabel}</span>
              <Button variant="ghost" size="icon" className="dark:text-lia-text-secondary dark:hover:bg-lia-bg-inverse" onClick={handleNextMonth}>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
            <div className="grid grid-cols-7 gap-1 text-center mb-2">
              {["Dom","Seg","Ter","Qua","Qui","Sex","Sáb"].map((day) => (
                <div
                  key={day}
                  className="text-xs font-medium py-1 text-lia-text-tertiary"
                >
                  {day}
                </div>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-1">
              {days.map((date, index) => {
                const isSelectable = isDateSelectable(date)
                const isSelected = date && formatDate(date) === formatDate(selectedDate)
                const isToday = date && formatDate(date) === formatDate(new Date())

                return (
                  <button
                    key={`cal-cell-${index}`}
                    type="button"
                    disabled={!isSelectable}
                    onClick={() => date && isSelectable && setSelectedDate(date)}
                    className="h-8 w-full rounded-md text-sm transition-colors motion-reduce:transition-none"
                    style={{visibility: !date ? 'hidden' : 'visible',
                      backgroundColor: isSelected ? 'var(--lia-btn-primary-bg)' : 'transparent',
                      color: isSelected 
                        ? 'var(--lia-btn-primary-text)' 
                        : !isSelectable && date 
                          ? 'var(--lia-text-disabled)' 
                          : isToday 
                            ? 'var(--lia-text-primary)' 
                            : 'var(--lia-text-secondary)',
                      border: !isSelected && isToday ? '1px solid var(--lia-border-default)' : 'none',
                      cursor: !isSelectable ? 'not-allowed' : 'pointer'}}
                    onMouseEnter={(e) => {
                      if (isSelectable && !isSelected) {
                        e.currentTarget.style.backgroundColor = 'var(--lia-interactive-hover)'
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.backgroundColor = 'transparent'
                      }
                    }}
                  >
                    {date?.getDate()}
                  </button>
                )
              })}
            </div>
          </div>
          <p
            className="text-xs mt-2 text-center capitalize text-lia-text-tertiary"
          >
            {formatDisplayDate(selectedDate)}
          </p>
        </CardContent>
      </Card>

      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 font-sans text-lia-text-primary">
            <Clock className="h-4 w-4 text-lia-text-secondary" />
            Horário Disponível
          </CardTitle>
        </CardHeader>
        <CardContent>
          {availableSlots.length === 0 ? (
            <div className="text-center py-4 text-sm text-lia-text-tertiary">
              Sem horários disponíveis nesta data.
              <br />
              Selecione outro dia útil.
            </div>
          ) : (
            <div className="grid grid-cols-4 gap-2">
              {availableSlots.map((time) => (
                <button
                  key={time}
                  type="button"
                  onClick={() => setSelectedTime(time)}
                  className="py-2 px-3 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none"
                  style={{backgroundColor: selectedTime === time ? 'var(--lia-btn-primary-bg)' : 'transparent',
                    color: selectedTime === time ? 'var(--lia-btn-primary-text)' : 'var(--lia-text-secondary)',
                    border: `1px solid ${selectedTime === time ? 'var(--lia-btn-primary-bg)' : 'var(--lia-border-subtle)'}`}}
                  onMouseEnter={(e) => {
                    if (selectedTime !== time) {
                      e.currentTarget.style.backgroundColor = 'var(--lia-interactive-hover)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedTime !== time) {
                      e.currentTarget.style.backgroundColor = 'transparent'
                    }
                  }}
                >
                  {time}
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 font-sans text-lia-text-primary">
            ⏱️ Duração
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-2">
            {DURATION_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setDuration(option.value)}
                className="py-2 px-3 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none"
                style={{backgroundColor: duration === option.value ? 'var(--lia-btn-primary-bg)' : 'transparent',
                  color: duration === option.value ? 'var(--lia-btn-primary-text)' : 'var(--lia-text-secondary)',
                  border: `1px solid ${duration === option.value ? 'var(--lia-btn-primary-bg)' : 'var(--lia-border-subtle)'}`}}
                onMouseEnter={(e) => {
                  if (duration !== option.value) {
                    e.currentTarget.style.backgroundColor = 'var(--lia-interactive-hover)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (duration !== option.value) {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }
                }}
              >
                {option.label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 font-sans text-lia-text-primary">
            📍 Tipo de Entrevista
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2">
            {INTERVIEW_TYPES.map((type) => (
              <button
                key={type.value}
                type="button"
                onClick={() => setInterviewType(type.value)}
                className="py-3 px-4 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
                style={{backgroundColor: interviewType === type.value ? 'var(--lia-btn-primary-bg)' : 'transparent',
                  color: interviewType === type.value ? 'var(--lia-btn-primary-text)' : 'var(--lia-text-secondary)',
                  border: `1px solid ${interviewType === type.value ? 'var(--lia-btn-primary-bg)' : 'var(--lia-border-subtle)'}`}}
                onMouseEnter={(e) => {
                  if (interviewType !== type.value) {
                    e.currentTarget.style.backgroundColor = 'var(--lia-interactive-hover)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (interviewType !== type.value) {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }
                }}
              >
                {type.icon}
                {type.label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 font-sans text-lia-text-primary">
            <Users className="h-4 w-4 text-lia-text-secondary" />
            Entrevistadores
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {MOCK_INTERVIEWERS.map((interviewer) => (
            <div
              key={interviewer.id}
              className="flex items-center gap-3 p-2 rounded-xl cursor-pointer transition-colors motion-reduce:transition-none dark:hover:bg-lia-bg-inverse"
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--lia-interactive-hover)'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <Checkbox
                id={`interviewer-${interviewer.id}`}
                checked={selectedInterviewers.includes(interviewer.id)}
                onCheckedChange={() => handleToggleInterviewer(interviewer.id)}
              />
              <label
                htmlFor={`interviewer-${interviewer.id}`}
                className="flex-1 cursor-pointer"
              >
                <p className="text-sm font-medium text-lia-text-primary">{interviewer.name}</p>
                <p className="text-xs text-lia-text-tertiary">{interviewer.role}</p>
              </label>
            </div>
          ))}
          {selectedInterviewers.length > 0 && (
            <div className="pt-2 mt-3 border-t border-lia-border-subtle">
              <p className="text-xs text-lia-text-tertiary">
                {selectedInterviewers.length} entrevistador(es) selecionado(s)
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 font-sans text-lia-text-primary">
            📝 Notas para o Candidato
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Instruções especiais, preparação sugerida, link de acesso..."
            rows={4}
            className="dark:bg-lia-bg-primary dark:border-lia-border-subtle"
          />
        </CardContent>
      </Card>

      {selectedTime && (
        <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle bg-lia-bg-secondary border-lia-border-default">
          <CardContent className="pt-4">
            <div className="flex items-start gap-3">
              <CalendarIcon className="h-5 w-5 shrink-0 mt-0.5 text-lia-text-secondary" />
              <div>
                <p className="text-sm font-medium text-lia-text-primary">Resumo do Agendamento</p>
                <p className="text-xs mt-1 text-lia-text-tertiary">
                  {formatDisplayDate(selectedDate)} às {selectedTime}
                </p>
                <div className="flex flex-wrap gap-2 mt-2">
                  <Chip
                    variant="neutral" muted
                    className="text-xs border-0 bg-lia-bg-tertiary text-lia-text-secondary"
                  >
                    {DURATION_OPTIONS.find((d) => d.value === duration)?.label}
                  </Chip>
                  <Chip
                    variant="neutral" muted
                    className="text-xs border-0 bg-lia-bg-tertiary text-lia-text-secondary"
                  >
                    {INTERVIEW_TYPES.find((t) => t.value === interviewType)?.label}
                  </Chip>
                  {selectedInterviewers.length > 0 && (
                    <Chip
                      variant="neutral" muted
                      className="text-xs border-0 bg-lia-bg-tertiary text-lia-text-secondary"
                    >
                      {selectedInterviewers.length} entrevistador(es)
                    </Chip>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Button
        onClick={handleSubmit}
        disabled={isLoading || !selectedTime}
        className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
        size="lg"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none mr-2" />
            Agendando...
          </>
        ) : ("Agendar Entrevista"
        )}
      </Button>
    </div>
  )
}
