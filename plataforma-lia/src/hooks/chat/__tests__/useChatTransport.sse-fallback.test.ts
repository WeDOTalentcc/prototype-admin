/**
 * Sensor 0.3a (2026-06-04): fallback de transporte SSE->REST.
 *
 * O SSE ja falha alto (maxSseFailures retries + erro claro), mas — diferente
 * do path WS — NAO caía pro REST ao esgotar. Quando NEXT_PUBLIC_CHAT_TRANSPORT=sse
 * e o SSE esgota, o turno deve ser reenviado via sendViaRest em vez de travar
 * num erro terminal. Sem isso, ligar a flag SSE degrada a resiliencia vs WS.
 *
 * Estrutural (regex sobre source) — estilo canonico deste hook (ver
 * useChatTransport.metadata.test.ts). Computacional, deterministico.
 *
 * Fix se falhar: useChatTransport.ts — sendMessageViaSSE ganha 6o param
 * `onExhausted?: () => void`, chamado no branch de esgotamento; useChatMessages.ts
 * passa `() => void sendViaRest(content, domain, context)` ao rotear por SSE.
 */
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, test } from "vitest"

const TRANSPORT = readFileSync(join(__dirname, "..", "useChatTransport.ts"), "utf8")
const MESSAGES = readFileSync(
  join(__dirname, "..", "useChatMessages.ts"),
  "utf8",
)

describe("0.3a — fallback de transporte SSE->REST", () => {
  test("Guard 1: sendMessageViaSSE expoe onExhausted na interface", () => {
    expect(TRANSPORT).toMatch(
      /sendMessageViaSSE[\s\S]*?onExhausted\?\s*:\s*\(\)\s*=>\s*void/,
    )
  })

  test("Guard 2: o closure de sendMessageViaSSE recebe onExhausted", () => {
    const block = TRANSPORT.split("const sendMessageViaSSE = useCallback")[1]
    expect(block).toBeDefined()
    expect(block).toMatch(/onExhausted\?\s*:\s*\(\)\s*=>\s*void/)
  })

  test("Guard 3: no esgotamento, chama onExhausted (fallback de transporte)", () => {
    const block = TRANSPORT.split("const sendMessageViaSSE = useCallback")[1]
    expect(block).toMatch(/onExhausted\s*\?\.\s*\(\)/)
  })

  test("Guard 4: useChatMessages reenvia via sendViaRest no fallback SSE", () => {
    expect(MESSAGES).toMatch(/0\.3a[\s\S]*?sendViaRest/)
  })
})
