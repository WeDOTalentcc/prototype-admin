// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { renderHook } from "@testing-library/react"
import { useUnsavedBackGuard } from "@/hooks/shared/useUnsavedBackGuard"
import { useNavGuardStore } from "@/stores/nav-guard-store"

// Pina o fix #6 popstate (handoff Funil de Talentos 2026-06-05): o botao
// "voltar" do browser tambem passa a ser guardado quando ha candidatos globais
// nao salvos — roteando pelo MESMO nav-guard-store que a navegacao in-app.
describe("useUnsavedBackGuard — guarda o botao voltar do browser (#6 popstate)", () => {
  beforeEach(() => {
    useNavGuardStore.setState({ active: false, pendingProceed: null })
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("active=true: popstate roteia pelo guard (arma pendingProceed, nao navega ainda)", () => {
    renderHook(() => useUnsavedBackGuard(true))
    expect(useNavGuardStore.getState().pendingProceed).toBeNull()

    window.dispatchEvent(new PopStateEvent("popstate"))

    const proceed = useNavGuardStore.getState().pendingProceed
    expect(typeof proceed).toBe("function")
  })

  it("active=false: popstate NAO arma o guard (back normal preservado)", () => {
    renderHook(() => useUnsavedBackGuard(false))
    window.dispatchEvent(new PopStateEvent("popstate"))
    expect(useNavGuardStore.getState().pendingProceed).toBeNull()
  })

  it("desmontar remove o listener (sem vazar guard apos sair da pagina)", () => {
    const { unmount } = renderHook(() => useUnsavedBackGuard(true))
    unmount()
    window.dispatchEvent(new PopStateEvent("popstate"))
    expect(useNavGuardStore.getState().pendingProceed).toBeNull()
  })
})
