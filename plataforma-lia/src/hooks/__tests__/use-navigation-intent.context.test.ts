/**
 * Task #1165 — testes do helper puro `resolveNavigationIntentMode`.
 *
 * Cobre os 3 ramos:
 *  1. confiança abaixo do threshold → page=null (passthrough)
 *  2. já em /chat + alvo é "Vagas"  → page=null (supressão)
 *  3. outra rota + alvo elegível    → mode="ask"
 *
 * Estes testes blindam o contrato com `UnifiedChat.tsx` (forwarda
 * `result.mode` no dispatch) e com `DashboardApp` (handler que ramifica
 * em `detail.mode === "ask"` para propor a transição via chat).
 */

import {
  resolveNavigationIntentMode,
  CHAT_FIRST_TARGET_PAGES,
} from "../shared/use-navigation-intent"

describe("resolveNavigationIntentMode (Task #1165)", () => {
  it("zera page/hint quando confidence < 0.65 (sem mode)", () => {
    const r = resolveNavigationIntentMode(
      { page: "Vagas", confidence: 0.4, hint: "ver vagas" },
      "/pt-BR/funil-de-talentos",
    )
    expect(r.page).toBeNull()
    expect(r.hint).toBeNull()
    expect(r.mode).toBeUndefined()
  })

  it("suprime hint quando já estamos em /chat e alvo é Vagas", () => {
    const r = resolveNavigationIntentMode(
      { page: "Vagas", confidence: 0.9, hint: "criar vaga" },
      "/pt-BR/chat",
    )
    expect(r.page).toBeNull()
    expect(r.hint).toBeNull()
    expect(r.mode).toBeUndefined()
  })

  it("suprime hint mesmo em sub-rotas de /chat (e.g. /chat/abc)", () => {
    const r = resolveNavigationIntentMode(
      { page: "Vagas", confidence: 0.85, hint: null },
      "/pt-BR/chat/conversa-123",
    )
    expect(r.page).toBeNull()
  })

  it('anota mode="ask" quando o recrutador está em outra página', () => {
    const r = resolveNavigationIntentMode(
      { page: "Vagas", confidence: 0.85, hint: "abrir vagas" },
      "/pt-BR/funil-de-talentos",
    )
    expect(r.page).toBe("Vagas")
    expect(r.mode).toBe("ask")
  })

  it('não suprime para alvos fora de CHAT_FIRST_TARGET_PAGES mesmo em /chat', () => {
    // "Funil de Talentos" não está na lista → segue como ask.
    expect(CHAT_FIRST_TARGET_PAGES.has("Funil de Talentos")).toBe(false)
    const r = resolveNavigationIntentMode(
      { page: "Funil de Talentos", confidence: 0.8, hint: null },
      "/pt-BR/chat",
    )
    expect(r.page).toBe("Funil de Talentos")
    expect(r.mode).toBe("ask")
  })
})
