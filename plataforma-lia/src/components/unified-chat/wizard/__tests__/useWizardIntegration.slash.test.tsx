import { describe, expect, it, vi } from "vitest"
import { renderHook } from "@testing-library/react"
import { useWizardIntegration } from "../useWizardIntegration"

describe("useWizardIntegration.handleSlashCommand", () => {
  function setup() {
    const sendMessage = vi.fn()
    const { result } = renderHook(() =>
      useWizardIntegration({ isWizardActive: false, currentStage: null, sendMessage }),
    )
    return { sendMessage, handle: result.current.handleSlashCommand }
  }

  it("intercepts /criar vaga and /job (alias)", () => {
    const { sendMessage, handle } = setup()
    expect(handle("/criar vaga")).toBe(true)
    expect(handle("/job")).toBe(true)
    expect(sendMessage).toHaveBeenNthCalledWith(1, "Criar nova vaga")
    expect(sendMessage).toHaveBeenNthCalledWith(2, "Criar nova vaga")
  })

  it("intercepts /buscar and /talent (alias) — bare and mention forms", () => {
    const { sendMessage, handle } = setup()
    expect(handle("/buscar")).toBe(true)
    expect(handle("/talent")).toBe(true)
    expect(handle("/talent @Ana Souza")).toBe(true)
    expect(sendMessage).toHaveBeenNthCalledWith(1, "Buscar candidatos")
    expect(sendMessage).toHaveBeenNthCalledWith(2, "Buscar candidatos")
    expect(sendMessage).toHaveBeenNthCalledWith(3, "Buscar candidato: Ana Souza")
  })

  it("returns false for unknown bare commands", () => {
    const { sendMessage, handle } = setup()
    expect(handle("/desconhecido")).toBe(false)
    expect(sendMessage).not.toHaveBeenCalled()
  })
})
