import type { ChatMode } from "./unified-chat-types"

export interface ModeTransitionEvent {
  type: string
  detail: Record<string, unknown>
}

/**
 * Eventos globais (window CustomEvent) que a transicao de/para a TELA CHEIA
 * (pagina "Conversar" / ChatPageFullscreen) precisa disparar, alem do
 * setMode/persist/`lia:chat-mode-changed` locais. Funcao PURA — testavel sem render.
 *
 * Regra canonica:
 *  - ENTRAR em fullscreen (vindo de outro modo)  -> `lia:navigate-chat-page`
 *    (dashboard troca currentPage p/ "Conversar").
 *  - SAIR de fullscreen p/ QUALQUER modo nao-fullscreen -> `lia:leave-fullscreen-chat`
 *    (dashboard restaura a pagina anterior e a ChatPageFullscreen desmonta).
 *
 * Causa raiz 2026-06-04 ("design da bolha desconfigura ao mudar de tela cheia
 * para flutuante"): o caminho `floating` em handleModeChange NAO disparava o
 * `lia:leave-fullscreen-chat` (so o `sidebar` disparava). Resultado: a
 * ChatPageFullscreen permanecia montada -> hasInlineChat=true suprimia a bolha
 * real, e o UnifiedChat interno tentava renderizar floating preso no container
 * `relative` da pagina. Centralizar a regra aqui evita a recidiva em modos futuros.
 *
 * `minimized` e tratado a parte no caller (close() + return); nao passa por aqui.
 */
export function fullscreenTransitionEvents(
  prevMode: ChatMode,
  newMode: ChatMode,
): ModeTransitionEvent[] {
  const events: ModeTransitionEvent[] = []
  if (newMode === "fullscreen" && prevMode !== "fullscreen") {
    events.push({ type: "lia:navigate-chat-page", detail: {} })
  }
  if (prevMode === "fullscreen" && newMode !== "fullscreen") {
    events.push({
      type: "lia:leave-fullscreen-chat",
      detail: { targetMode: newMode },
    })
  }
  return events
}
