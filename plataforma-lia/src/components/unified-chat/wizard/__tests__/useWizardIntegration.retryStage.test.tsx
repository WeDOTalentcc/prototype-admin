import { describe, expect, it, vi } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useWizardIntegration } from "../useWizardIntegration"

/**
 * Task #1067 — sentinela do botão "Tentar novamente" do banner de fallback.
 *
 * FallbackBanner (em JdEnrichment/BigFive/Salary/WsiQuestions panels)
 * dispara `lia:wizard-retry-stage` com `{ stage }`. Esta suíte garante que
 * o evento é convertido em uma mensagem de chat para reexecutar o nó —
 * sem isso o botão aparece mas não faz nada (regressão originalmente
 * apontada no code review do #1067).
 */
describe("useWizardIntegration — lia:wizard-retry-stage", () => {
  function setup(isWizardActive = true) {
    const sendMessage = vi.fn()
    renderHook(() =>
      useWizardIntegration({
        isWizardActive,
        currentStage: "jd_enrichment",
        sendMessage,
      }),
    )
    return { sendMessage }
  }

  it.each([
    ["jd_enrichment", "Tentar novamente: enriquecimento da descrição"],
    ["bigfive", "Tentar novamente: perfil Big Five"],
    ["salary", "Tentar novamente: benchmark de salário"],
    ["wsi_questions", "Tentar novamente: perguntas WSI"],
  ])("converte stage=%s em mensagem de retry", (stage, expected) => {
    const { sendMessage } = setup()
    act(() => {
      window.dispatchEvent(
        new CustomEvent("lia:wizard-retry-stage", { detail: { stage } }),
      )
    })
    expect(sendMessage).toHaveBeenCalledWith(expected)
  })

  it("ignora eventos sem stage", () => {
    const { sendMessage } = setup()
    act(() => {
      window.dispatchEvent(
        new CustomEvent("lia:wizard-retry-stage", { detail: {} }),
      )
    })
    expect(sendMessage).not.toHaveBeenCalled()
  })

  it("não escuta quando o wizard não está ativo", () => {
    const { sendMessage } = setup(false)
    act(() => {
      window.dispatchEvent(
        new CustomEvent("lia:wizard-retry-stage", {
          detail: { stage: "salary" },
        }),
      )
    })
    expect(sendMessage).not.toHaveBeenCalled()
  })
})
