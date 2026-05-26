/**
 * Canonical helper para emitir eventos `lia:settings-updated` quando hooks
 * de Configurações fazem mutations (Create/Update/Delete). Listener em
 * `lia-float-context.tsx:482` absorve e gera system note no chat — LIA
 * próximo turno reage proativamente (Task #712 + Bug 6 fix 2026-05-24).
 *
 * Antes de chamar este helper, garanta que a mutation foi bem-sucedida
 * (resp.ok === true). Falhas não devem disparar o evento — listener vai
 * fazer LIA reagir a algo que não persistiu, confundindo o usuário.
 *
 * Skill canonical: harness-engineering [guide computacional].
 */
export interface SettingsUpdateDetail {
  /** Identificador da ação (ex: 'configure_workforce', 'create_compensation_policy'). */
  actionId: string
  /** Seção do hub Configurações (ex: 'workforce', 'compensation_policies', 'communication'). */
  section: string
  /** Campo específico (opcional, aparece no system note). */
  field?: string
  /** Valor (opcional, truncado a 200 chars / 3 items de lista pelo listener). */
  value?: unknown
}

// Sprint 2.4 CR-3 (2026-05-26) — debounce per (actionId+section+field) key
// pra evitar events prematuros durante typing/drag/slider. Antes do fix,
// transcript Paulo capturou "[contexto] hiring_policies · default_duration_minutes = 3"
// que era valor intermediário de typing (user provavelmente digitou "3" e
// depois "30" ou abandonou — backend Pydantic schema ge=15 rejeitaria mas
// evento UI disparava antes). 1500ms é safe-guard sem prejudicar UX.
const _settingsUpdateDebounce: Map<string, ReturnType<typeof setTimeout>> = new Map()
const SETTINGS_UPDATE_DEBOUNCE_MS = 1500

export function notifyChatOfSettingsUpdate(detail: SettingsUpdateDetail): void {
  if (typeof window === "undefined") return
  const key = `${detail.actionId}|${detail.section}|${detail.field ?? ""}`
  const existing = _settingsUpdateDebounce.get(key)
  if (existing) clearTimeout(existing)
  const timer = setTimeout(() => {
    _settingsUpdateDebounce.delete(key)
    window.dispatchEvent(
      new CustomEvent("lia:settings-updated", {
        detail: {
          ...detail,
          source: "ui",
          ts: Date.now(),
        },
      }),
    )
  }, SETTINGS_UPDATE_DEBOUNCE_MS)
  _settingsUpdateDebounce.set(key, timer)
}
