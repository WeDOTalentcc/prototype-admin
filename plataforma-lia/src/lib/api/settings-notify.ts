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

export function notifyChatOfSettingsUpdate(detail: SettingsUpdateDetail): void {
  if (typeof window === "undefined") return
  window.dispatchEvent(
    new CustomEvent("lia:settings-updated", {
      detail: {
        ...detail,
        source: "ui",
        ts: Date.now(),
      },
    }),
  )
}
