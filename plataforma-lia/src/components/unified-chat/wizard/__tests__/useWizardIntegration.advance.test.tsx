import { describe, expect, it, vi } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useWizardIntegration } from "../useWizardIntegration"

/**
 * Sentinela do botão "Avançar" no WizardCalibrationCard.
 *
 * O card dispara `lia:wizard-advance` com `{ stage: "calibration" }`.
 * Antes de 2026-06-18 o evento era órfão (nenhum listener) — o botão
 * aparecia mas nunca avançava o wizard. Este teste garante que o evento
 * é convertido em mensagem de chat e que a regressão não pode voltar.
 *
 * Bug class H-6 (silent discard / orphan CustomEvent).
 */
describe("useWizardIntegration — lia:wizard-advance", () => {
  function setup(isWizardActive = true) {
    const sendMessage = vi.fn()
    renderHook(() =>
      useWizardIntegration({
        isWizardActive,
        currentStage: "calibration",
        sendMessage,
      }),
    )
    return { sendMessage }
  }

  it("dispara sendMessage ao receber lia:wizard-advance", () => {
    const { sendMessage } = setup()
    act(() => {
      window.dispatchEvent(
        new CustomEvent("lia:wizard-advance", { detail: { stage: "calibration" } }),
      )
    })
    expect(sendMessage).toHaveBeenCalledWith("Avançar: etapa de calibração concluída")
  })

  it("funciona sem detail (botão sem metadados)", () => {
    const { sendMessage } = setup()
    act(() => {
      window.dispatchEvent(new CustomEvent("lia:wizard-advance"))
    })
    expect(sendMessage).toHaveBeenCalledWith("Avançar: etapa de calibração concluída")
  })

  it("não escuta quando o wizard não está ativo", () => {
    const { sendMessage } = setup(false)
    act(() => {
      window.dispatchEvent(
        new CustomEvent("lia:wizard-advance", { detail: { stage: "calibration" } }),
      )
    })
    expect(sendMessage).not.toHaveBeenCalled()
  })
})
