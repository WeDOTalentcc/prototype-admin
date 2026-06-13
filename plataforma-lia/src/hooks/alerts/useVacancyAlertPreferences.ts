import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

export type AlertFrequency = "daily" | "twice_daily" | "weekly" | "monthly" | "off"

export interface VacancyAlertPreference {
  alert_type: string
  frequency: AlertFrequency
}

export function useVacancyAlertPreferences(vacancyId: string, userId: string) {
  const qc = useQueryClient()
  const key = ["vacancy-alert-preferences", vacancyId, userId] as const

  const query = useQuery({
    queryKey: key,
    queryFn: async () => {
      const res = await fetch(
        `/api/backend-proxy/alerts/vacancy/${vacancyId}/preferences?user_id=${encodeURIComponent(userId)}`
      )
      if (!res.ok) throw new Error("Falha ao carregar preferencias de alerta")
      return res.json() as Promise<{ preferences: VacancyAlertPreference[] }>
    },
    staleTime: 30_000,
    enabled: !!vacancyId && !!userId,
  })

  const mutation = useMutation({
    mutationFn: async (preferences: VacancyAlertPreference[]) => {
      const res = await fetch(
        `/api/backend-proxy/alerts/vacancy/${vacancyId}/preferences?user_id=${encodeURIComponent(userId)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ preferences }),
        },
      )
      if (!res.ok) throw new Error("Falha ao salvar preferencias de alerta")
      return res.json()
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: key }),
  })

  return {
    ...query,
    savePreferences: mutation.mutate,
    isSaving: mutation.isPending,
  }
}

// --- Alert Preview ---

export interface AlertPreview {
  alert_type: string
  preview_count: number
  description: string
}

export function useAlertPreview(vacancyId: string, alertType: string) {
  return useQuery({
    queryKey: ["alert-preview", vacancyId, alertType],
    queryFn: async () => {
      const params = new URLSearchParams({ alert_type: alertType })
      if (vacancyId) params.set("vacancy_id", vacancyId)
      const res = await fetch(`/api/backend-proxy/alerts/vacancy/preview?${params}`)
      if (!res.ok) return { alert_type: alertType, preview_count: 0, description: "" }
      return res.json() as Promise<AlertPreview>
    },
    staleTime: 60_000,
    refetchInterval: 120_000,
    enabled: !!alertType,
  })
}
