import { describe, expect, it, vi } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useWizardIntegration } from "../useWizardIntegration"

/**
 * Item 2 polish (2026-06-05) — botão "Gerar novas" (todas) do WsiQuestionsPanel.
 *
 * O botão dispara `lia:wizard-regenerate-all`; esta suíte garante que vira uma
 * mensagem de chat que o wsi_questions_gate classifica como regenerate_all —
 * caminho PROVADO (sendMessage→classifier), NÃO sendApproval (que no-opa sem
 * hitlRef no estágio do wizard). Sem isto o botão apareceria mas não faria nada.
 */
describe("useWizardIntegration — lia:wizard-regenerate-all", () => {
  function setup(isWizardActive = true) {
    const sendMessage = vi.fn()
    renderHook(() =>
      useWizardIntegration({
        isWizardActive,
        currentStage: "wsi_questions",
        sendMessage,
      }),
    )
    return { sendMessage }
  }

  it("converte o evento em mensagem de regenerar todas", () => {
    const { sendMessage } = setup()
    act(() => {
      window.dispatchEvent(new CustomEvent("lia:wizard-regenerate-all"))
    })
    expect(sendMessage).toHaveBeenCalledWith(
      "Regenerar todas as perguntas de triagem",
    )
  })

  it("não escuta quando o wizard não está ativo", () => {
    const { sendMessage } = setup(false)
    act(() => {
      window.dispatchEvent(new CustomEvent("lia:wizard-regenerate-all"))
    })
    expect(sendMessage).not.toHaveBeenCalled()
  })
})
