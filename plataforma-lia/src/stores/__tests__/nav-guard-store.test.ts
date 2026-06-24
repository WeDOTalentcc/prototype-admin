import { describe, it, expect, vi, beforeEach } from "vitest"
import { useNavGuardStore } from "@/stores/nav-guard-store"

// Pina o fix #6 (handoff Funil de Talentos 2026-06-05): guard de navegacao p/
// candidatos globais nao salvos. Quando armado (active=true), a navegacao e
// adiada via requestLeave(proceed); a pagina mostra o modal e so navega ao
// confirmar (proceed()). clear() cancela (usuario fica).
describe("nav-guard-store — guard de navegacao p/ candidatos globais nao salvos (#6)", () => {
  beforeEach(() => {
    useNavGuardStore.setState({ active: false, pendingProceed: null })
  })

  it("setActive(true) arma o guard", () => {
    useNavGuardStore.getState().setActive(true)
    expect(useNavGuardStore.getState().active).toBe(true)
  })

  it("requestLeave difere a navegacao: guarda proceed e NAO navega ainda", () => {
    const proceed = vi.fn()
    useNavGuardStore.getState().requestLeave(proceed)
    expect(useNavGuardStore.getState().pendingProceed).toBe(proceed)
    expect(proceed).not.toHaveBeenCalled()
  })

  it("ao confirmar, pendingProceed() executa a navegacao adiada", () => {
    const proceed = vi.fn()
    useNavGuardStore.getState().requestLeave(proceed)
    useNavGuardStore.getState().pendingProceed?.()
    expect(proceed).toHaveBeenCalledTimes(1)
  })

  it("clear() cancela a navegacao pendente (usuario permanece na pagina)", () => {
    useNavGuardStore.getState().requestLeave(vi.fn())
    useNavGuardStore.getState().clear()
    expect(useNavGuardStore.getState().pendingProceed).toBeNull()
  })
})
