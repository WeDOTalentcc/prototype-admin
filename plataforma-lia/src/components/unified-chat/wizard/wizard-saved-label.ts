/**
 * Pure formatter for the wizard's "auto-save" header indicator.
 *
 * Extracted from `UnifiedChat` so the timing edge cases (rehydrate skip,
 * < 5s "Salvando…" window, minute/hour buckets) can be unit-tested in
 * isolation without rendering the full chat surface (Task #836).
 */
export function formatWizardSavedLabel(
  savedAt: Date | null,
  now: Date,
  wizardActive: boolean,
): string | null {
  if (!wizardActive || !savedAt) return null
  const diff = now.getTime() - savedAt.getTime()
  if (diff < 5_000) return "Salvando…"
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return "Salvo agora"
  if (minutes === 1) return "Salvo há 1 min"
  if (minutes < 60) return `Salvo há ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours === 1) return "Salvo há 1 hora"
  return `Salvo há ${hours} horas`
}
