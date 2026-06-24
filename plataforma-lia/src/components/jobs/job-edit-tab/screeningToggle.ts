/**
 * Onda 2F (audit 2026-06-06): o campo "Triagem" vira toggle (ativar/desativar) em vez de
 * um rótulo clicável que navegava pra aba de Config (confuso).
 *
 * Decisão pura: dado o screeningStatus da vaga, o que o controle renderiza/faz.
 *   - active/paused/not_started → toggle (Switch liga active ⇄ desliga paused)
 *   - completed                 → read-only (triagem encerrada)
 *   - not_configured            → "Configurar" (não dá pra ligar triagem sem roteiro)
 */
export type ScreeningToggleMode = "toggle" | "configure" | "readonly"

export function screeningToggleState(
  status: string | undefined | null,
): { mode: ScreeningToggleMode; checked: boolean } {
  const s = status || "not_configured"
  if (s === "active") return { mode: "toggle", checked: true }
  if (s === "paused" || s === "not_started") return { mode: "toggle", checked: false }
  if (s === "completed") return { mode: "readonly", checked: false }
  return { mode: "configure", checked: false } // not_configured / desconhecido
}
