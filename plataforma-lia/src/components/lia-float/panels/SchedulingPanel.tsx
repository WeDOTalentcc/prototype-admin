"use client"

import React, { useState } from "react"
import { Calendar, Clock, CheckCircle2, User } from "lucide-react"
import { cn } from "@/lib/utils"

interface TimeSlot {
  id: string
  time: string
  available: boolean
}

interface DaySlots {
  date: string
  label: string
  slots: TimeSlot[]
}

interface SchedulingPanelProps {
  data: Record<string, unknown>
  onUpdateData?: (data: Record<string, unknown>) => void
}

export function SchedulingPanel({ data, onUpdateData }: SchedulingPanelProps) {
  const [selectedSlot, setSelectedSlot] = useState<string | null>(
    (data.selected_slot as string) || null
  )

  const candidateName = (data.candidate_name as string) || "Candidato"
  const jobTitle = (data.job_title as string) || ""
  const confirmed = (data.confirmed as boolean) || false

  const days: DaySlots[] = (data.days as DaySlots[]) || [
    {
      date: "2026-04-06",
      label: "Seg, 6 Abr",
      slots: [
        { id: "s1", time: "09:00", available: true },
        { id: "s2", time: "10:00", available: true },
        { id: "s3", time: "14:00", available: true },
        { id: "s4", time: "15:00", available: false },
      ],
    },
    {
      date: "2026-04-07",
      label: "Ter, 7 Abr",
      slots: [
        { id: "s5", time: "09:00", available: true },
        { id: "s6", time: "11:00", available: true },
        { id: "s7", time: "14:00", available: false },
        { id: "s8", time: "16:00", available: true },
      ],
    },
    {
      date: "2026-04-08",
      label: "Qua, 8 Abr",
      slots: [
        { id: "s9", time: "10:00", available: true },
        { id: "s10", time: "13:00", available: true },
        { id: "s11", time: "15:00", available: true },
      ],
    },
  ]

  const handleSelectSlot = (slotId: string) => {
    setSelectedSlot(slotId)
    onUpdateData?.({ selected_slot: slotId })
  }

  const handleConfirm = () => {
    if (!selectedSlot) return
    onUpdateData?.({ confirmed: true, selected_slot: selectedSlot })
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 flex items-center gap-2">
        <Calendar className="w-4 h-4 text-wedo-cyan" />
        <span className="text-sm font-semibold text-lia-text-primary">Agendamento</span>
      </div>

      <div className="px-4 py-3 bg-lia-bg-secondary">
        <div className="flex items-center gap-2 mb-1">
          <User className="w-3.5 h-3.5 text-lia-text-secondary" />
          <span className="text-xs font-medium text-lia-text-primary">{candidateName}</span>
        </div>
        {jobTitle && <p className="text-micro text-lia-text-disabled ml-5">{jobTitle}</p>}
      </div>

      {confirmed ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
          <CheckCircle2 className="w-12 h-12 text-status-success mb-3" />
          <p className="text-sm font-semibold text-lia-text-primary">Entrevista Agendada</p>
          <p className="text-xs text-lia-text-secondary mt-1">
            Confirmação enviada para {candidateName}
          </p>
        </div>
      ) : (
        <>
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
            {days.map((day) => (
              <div key={day.date}>
                <p className="text-xs font-semibold text-lia-text-primary mb-2">{day.label}</p>
                <div className="grid grid-cols-3 gap-2">
                  {day.slots.map((slot) => (
                    <button
                      key={slot.id}
                      onClick={() => slot.available && handleSelectSlot(slot.id)}
                      disabled={!slot.available}
                      className={cn(
                        "flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-colors border",
                        !slot.available
                          ? "bg-lia-bg-tertiary text-lia-text-disabled border-transparent cursor-not-allowed line-through"
                          : selectedSlot === slot.id
                            ? "bg-wedo-cyan/10 text-wedo-cyan-text border-wedo-cyan"
                            : "bg-lia-bg-primary text-lia-text-primary border-lia-border-subtle hover:border-wedo-cyan/50"
                      )}
                    >
                      <Clock className="w-3 h-3" />
                      {slot.time}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="px-4 py-3 border-t border-lia-border-subtle flex-shrink-0">
            <button
              onClick={handleConfirm}
              disabled={!selectedSlot}
              className={cn(
                "w-full py-2.5 rounded-lg text-sm font-medium transition-colors",
                selectedSlot
                  ? "bg-wedo-cyan text-white hover:bg-wedo-cyan/90"
                  : "bg-lia-bg-tertiary text-lia-text-disabled cursor-not-allowed"
              )}
            >
              Confirmar Agendamento
            </button>
          </div>
        </>
      )}
    </div>
  )
}
