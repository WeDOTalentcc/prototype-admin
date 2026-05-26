"use client"

/**
 * EventTriggerPicker — Sprint 7C Part 3.
 *
 * Multi-select checkboxes pra event triggers canonical.
 * Output: array de event types pra schedule_config.event_triggers.
 *
 * Lista canonical sincronizada com backend (Sprint 7C Part 2 RabbitMQ consumer).
 */
import React from "react"
import { useTranslations } from "next-intl"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { textStyles } from "@/lib/design-tokens"

/** Canonical event types. Sync with backend. */
export const CANONICAL_EVENT_TYPES = [
  "candidate_added_to_pool",
  "candidate_screened",
  "agent_completed_review",
  "weekly_summary",
] as const

export type EventTriggerType = (typeof CANONICAL_EVENT_TYPES)[number]

export interface EventTriggerPickerProps {
  value: string[]
  onChange: (events: string[]) => void
}

export function EventTriggerPicker({ value, onChange }: EventTriggerPickerProps) {
  const t = useTranslations("talentPool.schedule.eventPicker")

  const toggle = (evt: EventTriggerType) => {
    const next = value.includes(evt)
      ? value.filter((v) => v !== evt)
      : [...value, evt]
    onChange(next)
  }

  return (
    <div className="space-y-3" data-testid="event-trigger-picker">
      <p className={textStyles.h4}>{t("title")}</p>
      <div className="space-y-2">
        {CANONICAL_EVENT_TYPES.map((evt) => (
          <div key={evt} className="flex items-center gap-2">
            <Checkbox
              id={`evt-${evt}`}
              checked={value.includes(evt)}
              onCheckedChange={() => toggle(evt)}
              data-testid={`event-checkbox-${evt}`}
            />
            <Label htmlFor={`evt-${evt}`} className="cursor-pointer">
              {t(`events.${evt}` as never)}
            </Label>
          </div>
        ))}
      </div>
    </div>
  )
}
