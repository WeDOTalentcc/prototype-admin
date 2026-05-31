import { describe, it, expect } from "vitest"
import { DEFAULT_PEARCH_OPTIONS } from "../candidates-core.constants"

// Decisao Paulo: email e padrao no funil (sem email nao ha disparo de triagem).
// Telefone permanece opcional. Recrutador pode desmarcar qualquer combinacao.
describe("DEFAULT_PEARCH_OPTIONS — email padrao", () => {
  it("requireEmails vem marcado por default", () => {
    expect(DEFAULT_PEARCH_OPTIONS.requireEmails).toBe(true)
  })
  it("requirePhoneNumbers permanece opcional (default false)", () => {
    expect(DEFAULT_PEARCH_OPTIONS.requirePhoneNumbers).toBe(false)
  })
})
