"use client"

import { useCallback } from "react"
import {
  useVacancyAlertPreferences,
  type AlertFrequency,
  type VacancyAlertPreference,
} from "@/hooks/alerts/useVacancyAlertPreferences"

const ALERT_TYPES = [
  { key: "new_candidate", label: "Novo candidato" },
  { key: "screening_complete", label: "Triagem concluída" },
  { key: "stage_change", label: "Mudança de etapa" },
] as const

const FREQUENCY_OPTIONS: { value: AlertFrequency; label: string }[] = [
  { value: "daily", label: "Diário" },
  { value: "twice_daily", label: "2x ao dia" },
  { value: "weekly", label: "Semanal" },
  { value: "monthly", label: "Mensal" },
  { value: "off", label: "Desativado" },
]

interface VacancyAlertSettingsProps {
  vacancyId: string
  userId: string
}

export function VacancyAlertSettings({ vacancyId, userId }: VacancyAlertSettingsProps) {
  const { data, isLoading, savePreferences, isSaving } =
    useVacancyAlertPreferences(vacancyId, userId)

  const getFrequency = useCallback(
    (alertType: string): AlertFrequency => {
      const pref = data?.preferences?.find((p) => p.alert_type === alertType)
      return pref?.frequency ?? "daily"
    },
    [data],
  )

  const handleChange = useCallback(
    (alertType: string, frequency: AlertFrequency) => {
      const current = data?.preferences ?? []
      const updated: VacancyAlertPreference[] = ALERT_TYPES.map((at) => ({
        alert_type: at.key,
        frequency: at.key === alertType ? frequency : getFrequency(at.key),
      }))
      savePreferences(updated)
    },
    [data, getFrequency, savePreferences],
  )

  if (!vacancyId) return null

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Carregando alertas...</p>
  }

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium">Frequência de alertas desta vaga</h4>
      {ALERT_TYPES.map((at) => (
        <div key={at.key} className="flex items-center justify-between gap-4">
          <span className="text-sm">{at.label}</span>
          <select
            role="combobox"
            className="rounded border px-2 py-1 text-sm"
            value={getFrequency(at.key)}
            disabled={isSaving}
            onChange={(e) =>
              handleChange(at.key, e.target.value as AlertFrequency)
            }
          >
            {FREQUENCY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      ))}
    </div>
  )
}
