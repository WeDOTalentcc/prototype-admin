import { describe, it, expect, beforeEach } from "vitest"
import { useCandidatesStore } from "@/stores/candidates-store"
import type { RevealedContacts } from "@/stores/candidates-store"

// Pina o SSOT de revealedContacts (P2 #5 handoff Funil de Talentos 2026-06-05):
// o overlay de contatos revelados (email/phone por candidate.id) passou a viver
// no candidates-store, espelhando searchFeedbacks (mesmo formato, mesmo helper
// setOrUpdate). O produtor (useRevealContact) escreve SEMPRE via updater
// funcional com merge — setRevealedContacts(prev => ({...prev, [id]: {...}})).
// Se o setter fosse plano (nao suportasse funcao), o reveal individual/lote
// sobrescreveria contatos previos (mesma classe do bug NaN de displayedResultsCount).
describe("candidates-store — SSOT revealedContacts (#5)", () => {
  beforeEach(() => {
    useCandidatesStore.getState().setRevealedContacts({})
  })

  it("inicia vazio", () => {
    expect(useCandidatesStore.getState().revealedContacts).toEqual({})
  })

  it("setRevealedContacts aceita objeto plano", () => {
    const next: RevealedContacts = { a: { email: "a@x.com" } }
    useCandidatesStore.getState().setRevealedContacts(next)
    expect(useCandidatesStore.getState().revealedContacts).toEqual(next)
  })

  it("setRevealedContacts(updater) faz merge entre candidatos diferentes", () => {
    useCandidatesStore.getState().setRevealedContacts((prev) => ({ ...prev, a: { email: "a@x.com" } }))
    useCandidatesStore.getState().setRevealedContacts((prev) => ({ ...prev, b: { phone: "+5511" } }))
    expect(useCandidatesStore.getState().revealedContacts).toEqual({
      a: { email: "a@x.com" },
      b: { phone: "+5511" },
    })
  })

  it("setRevealedContacts(updater) acumula email+phone no MESMO candidato sem perder o anterior", () => {
    useCandidatesStore.getState().setRevealedContacts((prev) => ({ ...prev, a: { ...prev.a, email: "a@x.com" } }))
    useCandidatesStore.getState().setRevealedContacts((prev) => ({ ...prev, a: { ...prev.a, phone: "+5511" } }))
    expect(useCandidatesStore.getState().revealedContacts.a).toEqual({ email: "a@x.com", phone: "+5511" })
  })
})
