"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import { ChevronDown, ChevronRight, Check, CalendarDays, Clock } from "lucide-react"

interface SlotItem {
  date: string
  day_label: string
  time: string
  available: boolean
}

interface InterviewItem {
  id: string
  title: string
  type?: string
  candidate_name?: string
}

interface SchedulingData {
  interviews?: InterviewItem[]
  available_slots?: SlotItem[]
  job_title?: string
  candidate_name?: string
  vacancy_id?: string
}

interface Props {
  data: Record<string, unknown>
  onApprove?: () => void
}

const DURATION_OPTIONS = ["30 min", "45 min", "60 min", "90 min"]
const TIMEZONE_OPTIONS = ["BRT (UTC-3)", "AMT (UTC-4)", "UTC"]

/**
 * SchedulingPanel — workspace panel for scheduling interviews.
 * Shows a weekly time grid with multi-interview pagination (1 of N → 2 of N...).
 * Replaces the modal-based InterviewSchedulingModal for fullscreen/sidebar views.
 */
export function SchedulingPanel({ data, onApprove }: Props) {
  const d = data as SchedulingData
  const interviews = d.interviews ?? []
  const slots = d.available_slots ?? generatePlaceholderSlots()
  const jobTitle = d.job_title ?? "Vaga"
  const candidateName = d.candidate_name ?? ""

  const [currentIdx, setCurrentIdx] = useState(0)
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null)
  const [duration, setDuration] = useState("45 min")
  const [timezone, setTimezone] = useState("BRT (UTC-3)")
  const [confirmedSlots, setConfirmedSlots] = useState<Record<number, string>>({})

  const totalInterviews = Math.max(interviews.length, 1)
  const currentInterview = interviews[currentIdx] ?? { id: "1", title: "Triagem", candidate_name: candidateName }
  const isLastInterview = currentIdx === totalInterviews - 1
  const allDone = Object.keys(confirmedSlots).length === totalInterviews

  // Group slots by day
  const days = Array.from(new Set(slots.map((s) => s.date))).slice(0, 4)
  const times = Array.from(new Set(slots.map((s) => s.time))).sort()

  const handleConfirm = () => {
    if (!selectedSlot) return
    const next = { ...confirmedSlots, [currentIdx]: selectedSlot }
    setConfirmedSlots(next)
    setSelectedSlot(null)

    if (isLastInterview) {
      window.dispatchEvent(new CustomEvent("lia:scheduling-confirmed", {
        detail: { slots: next, interviews, vacancyId: d.vacancy_id },
      }))
      onApprove?.()
    } else {
      setCurrentIdx((i) => i + 1)
    }
  }

  if (allDone) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 px-4 py-10 text-center">
        <div className="w-10 h-10 rounded-full bg-status-success/10 flex items-center justify-center">
          <Check className="w-5 h-5 text-status-success" />
        </div>
        <p className="text-sm font-semibold text-lia-text-primary">
          {totalInterviews === 1 ? "Entrevista agendada!" : `${totalInterviews} entrevistas agendadas!`}
        </p>
        <p className="text-xs text-lia-text-secondary">
          Os convites serão enviados por email.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Interview info + pagination */}
      <div className="px-4 py-3 border-b border-lia-border-subtle">
        {totalInterviews > 1 && (
          <div className="flex items-center gap-1.5 mb-1">
            {Array.from({ length: totalInterviews }).map((_, i) => (
              <div
                key={i}
                className={cn(
                  "h-1 rounded-full transition-[width,background-color] duration-200",
                  i < currentIdx
                    ? "w-6 bg-status-success"
                    : i === currentIdx
                      ? "w-6 bg-wedo-cyan"
                      : "w-3 bg-lia-border-subtle"
                )}
              />
            ))}
            {/* A-09 / WCAG 2.1 AA 1.4.3: was `text-[10px] text-lia-text-muted`. */}
            <span className="ml-auto text-xs text-lia-text-secondary">
              {currentIdx + 1}/{totalInterviews}
            </span>
          </div>
        )}
        <div className="flex items-start gap-2">
          <CalendarDays className="w-4 h-4 text-wedo-cyan mt-0.5 flex-shrink-0" aria-hidden="true" />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-lia-text-primary truncate">
              {currentInterview.title}
              {totalInterviews > 1 && (
                <span className="text-lia-text-secondary font-normal ml-1">
                  · {currentIdx + 1} de {totalInterviews}
                </span>
              )}
            </p>
            <p className="text-xs text-lia-text-secondary truncate">
              {currentInterview.candidate_name || candidateName || jobTitle}
            </p>
          </div>
        </div>
      </div>

      {/* Duration + timezone selectors */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-lia-border-subtle">
        <Clock className="w-3.5 h-3.5 text-lia-text-muted flex-shrink-0" aria-hidden="true" />
        <NativeSelect
          value={duration}
          onChange={setDuration}
          options={DURATION_OPTIONS}
          aria-label="Duração"
        />
        <span className="text-lia-border-default">·</span>
        <NativeSelect
          value={timezone}
          onChange={setTimezone}
          options={TIMEZONE_OPTIONS}
          aria-label="Fuso horário"
        />
      </div>

      {/* Week grid */}
      <div className="flex-1 overflow-x-auto overflow-y-auto px-4 py-3">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr>
              <th className="w-12 pb-2 text-left text-lia-text-muted font-normal" />
              {days.map((date) => {
                const slot = slots.find((s) => s.date === date)
                return (
                  <th key={date} className="pb-2 text-center font-medium text-lia-text-secondary min-w-[56px]">
                    {slot?.day_label ?? date}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {times.map((time) => (
              <tr key={time}>
                <td className="py-0.5 pr-2 text-right text-lia-text-disabled whitespace-nowrap align-middle">
                  {time}
                </td>
                {days.map((date) => {
                  const slot = slots.find((s) => s.date === date && s.time === time)
                  const key = `${date}|${time}`
                  const isSelected = selectedSlot === key
                  const isAvailable = slot?.available ?? false

                  return (
                    <td key={date} className="py-0.5 px-1 text-center">
                      {isAvailable ? (
                        <button
                          onClick={() => setSelectedSlot(isSelected ? null : key)}
                          className={cn(
                            "w-full py-1.5 rounded-md border text-[10px] font-medium transition-colors motion-reduce:transition-none",
                            isSelected
                              ? "bg-gray-900 border-gray-900 text-white"
                              : "border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:border-lia-border-default hover:bg-lia-bg-secondary"
                          )}
                          aria-pressed={isSelected}
                          aria-label={`${time} em ${slot?.day_label}`}
                        >
                          {isSelected ? <Check className="w-3 h-3 mx-auto" aria-hidden="true" /> : "·"}
                        </button>
                      ) : (
                        <div className="w-full py-1.5 rounded-md bg-lia-bg-tertiary opacity-30" aria-hidden="true" />
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Confirm footer */}
      <div className="flex-shrink-0 px-4 py-3 border-t border-lia-border-subtle">
        <button
          onClick={handleConfirm}
          disabled={!selectedSlot}
          className={cn(
            "w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none",
            selectedSlot
              ? "bg-gray-900 text-white hover:bg-gray-800"
              : "bg-lia-bg-tertiary text-lia-text-disabled cursor-not-allowed"
          )}
        >
          {isLastInterview ? "Confirmar agendamento" : "Confirmar e avançar"}
          <ChevronRight className="w-4 h-4" aria-hidden="true" />
        </button>
        {!selectedSlot && (
          // A-09 / WCAG 2.1 AA 1.4.3: was `text-[10px] text-lia-text-muted`.
          <p className="text-center text-xs text-lia-text-secondary mt-1.5">
            Selecione um horário para continuar
          </p>
        )}
      </div>
    </div>
  )
}

function NativeSelect({
  value,
  onChange,
  options,
  "aria-label": ariaLabel,
}: {
  value: string
  onChange: (v: string) => void
  options: string[]
  "aria-label"?: string
}) {
  return (
    <div className="relative flex items-center">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={ariaLabel}
        className="appearance-none pl-2 pr-5 py-0.5 rounded-md border border-lia-border-subtle bg-lia-bg-primary text-xs text-lia-text-primary focus:outline-none focus:border-lia-border-default transition-colors motion-reduce:transition-none cursor-pointer"
      >
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
      <ChevronDown className="w-3 h-3 text-lia-text-disabled pointer-events-none absolute right-1" aria-hidden="true" />
    </div>
  )
}

function generatePlaceholderSlots(): SlotItem[] {
  const now = new Date()
  const days = ["Seg", "Ter", "Qua", "Qui"]
  const times = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
  const slots: SlotItem[] = []

  for (let d = 0; d < 4; d++) {
    const date = new Date(now)
    date.setDate(now.getDate() + d + 1)
    const dateStr = date.toISOString().split("T")[0]
    for (const time of times) {
      slots.push({
        date: dateStr,
        day_label: `${days[d]} ${date.getDate()}`,
        time,
        available: Math.random() > 0.4,
      })
    }
  }
  return slots
}
