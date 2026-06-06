import { describe, it, expect } from "vitest"
import ptBR from "../../../../messages/pt-BR.json"
import en from "../../../../messages/en.json"

// Pina P2-5: o botao passa { count: LOAD_MORE_STEP } (=15) mas a string i18n
// tinha "10" hardcoded sem placeholder {count} -> carregava 15, exibia 10.
function findValue(obj: unknown, key: string): unknown {
  if (obj && typeof obj === "object") {
    const rec = obj as Record<string, unknown>
    if (key in rec) return rec[key]
    for (const v of Object.values(rec)) {
      const r = findValue(v, key)
      if (r !== undefined) return r
    }
  }
  return undefined
}

describe("load-more label usa placeholder {count} (P2-5)", () => {
  it("pt-BR usa {count}, sem numero hardcoded", () => {
    const v = findValue(ptBR, "loadMoreCandidates") as string
    expect(v).toContain("{count}")
    expect(v).not.toMatch(/\b10\b/)
  })
  it("en usa {count}, sem numero hardcoded", () => {
    const v = findValue(en, "loadMoreCandidates") as string
    expect(v).toContain("{count}")
    expect(v).not.toMatch(/\b10\b/)
  })
})
