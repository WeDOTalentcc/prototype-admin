import { describe, expect, it, vi } from "vitest"
import { renderHook } from "@testing-library/react"
import { useWizardIntegration } from "../useWizardIntegration"

describe("useWizardIntegration.handleSlashCommand", () => {
  function setup(opts: { withLocalCommand?: boolean } = {}) {
    const sendMessage = vi.fn()
    const onLocalCommand = opts.withLocalCommand ? vi.fn() : undefined
    const { result } = renderHook(() =>
      useWizardIntegration({
        isWizardActive: false,
        currentStage: null,
        sendMessage,
        onLocalCommand,
      }),
    )
    return { sendMessage, onLocalCommand, handle: result.current.handleSlashCommand }
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

  it("resolves /ajuda locally via onLocalCommand (no backend round-trip)", () => {
    const { sendMessage, onLocalCommand, handle } = setup({ withLocalCommand: true })
    expect(handle("/ajuda")).toBe(true)
    expect(sendMessage).not.toHaveBeenCalled()
    expect(onLocalCommand).toHaveBeenCalledTimes(1)
    const [commandId, payload] = onLocalCommand!.mock.calls[0]
    expect(commandId).toBe("ajuda")
    // The shared builder always lists at least the visible commands and ends
    // with the input-discovery hint — guards copy regressions across surfaces.
    expect(payload.responseMarkdown).toMatch(/Comandos disponíveis/)
    expect(payload.responseMarkdown).toMatch(/\/ajuda/)
    expect(payload.rawInput).toBe("/ajuda")
  })

  it("falls through when onLocalCommand is absent (backend handles /ajuda)", () => {
    const { sendMessage, handle } = setup()
    expect(handle("/ajuda")).toBe(false)
    expect(sendMessage).not.toHaveBeenCalled()
  })
})
