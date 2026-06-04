import { describe, it, expect } from "vitest"
import { fullscreenTransitionEvents } from "../mode-transition"

/**
 * Bug 2026-06-04 ("design da bolha desconfigura ao sair da tela cheia para flutuante").
 * Causa raiz: handleModeChange so disparava lia:leave-fullscreen-chat no caminho
 * sidebar; o caminho floating nao avisava o dashboard -> ChatPageFullscreen ficava
 * montada (hasInlineChat=true) e o chat renderizava quebrado dentro da pagina.
 * Regra canonica: TODA saida de fullscreen avisa.
 */
describe("fullscreenTransitionEvents", () => {
  it("BUG: fullscreen -> floating emite lia:leave-fullscreen-chat", () => {
    const evs = fullscreenTransitionEvents("fullscreen", "floating")
    expect(evs.some((e) => e.type === "lia:leave-fullscreen-chat")).toBe(true)
  })

  it("fullscreen -> sidebar tambem emite leave (preserva o que ja funcionava)", () => {
    const evs = fullscreenTransitionEvents("fullscreen", "sidebar")
    expect(evs.some((e) => e.type === "lia:leave-fullscreen-chat")).toBe(true)
  })

  it("leave carrega targetMode = novo modo", () => {
    const leave = fullscreenTransitionEvents("fullscreen", "floating").find(
      (e) => e.type === "lia:leave-fullscreen-chat",
    )
    expect(leave?.detail).toMatchObject({ targetMode: "floating" })
  })

  it("sidebar -> floating NAO emite leave (nao estava em fullscreen)", () => {
    const evs = fullscreenTransitionEvents("sidebar", "floating")
    expect(evs.some((e) => e.type === "lia:leave-fullscreen-chat")).toBe(false)
  })

  it("entrar em fullscreen emite lia:navigate-chat-page", () => {
    const evs = fullscreenTransitionEvents("sidebar", "fullscreen")
    expect(evs.some((e) => e.type === "lia:navigate-chat-page")).toBe(true)
  })

  it("fullscreen -> fullscreen nao emite leave nem navigate (no-op)", () => {
    const evs = fullscreenTransitionEvents("fullscreen", "fullscreen")
    expect(evs).toEqual([])
  })
})
