/**
 * Task #1056 — Sentinela TDD do bridge canônico
 * `lia:wizard-stage-payload` (WS/REST) → `useWizardFlow` →
 * `useWizardChatCards` → mensagem `WIZARD_TEMPLATE_MESSAGE_ID` com
 * metadata `wizard_template_select`.
 *
 * Cobre o caminho fim-a-fim que o pw-cenario-A
 * (`e2e/tests/wizard/02-vaga-tecnica.spec.ts`) exige no turno 1 do
 * intake: o backend (`app/domains/job_creation/graph.py::intake_node`)
 * emite `data.suggestions_data.pipeline_template = { suggested_type,
 * templates }`. Os transports propagam isso como `detail.data` do
 * evento. Aqui simulamos o evento com o shape EXATO do backend e
 * exigimos que a mensagem do card seja injetada — sem isso, a próxima
 * regressão do tipo "FE perde o evento de intake" só apareceria no
 * Playwright (10+min de LLM real) em vez de em Vitest (<1s).
 *
 * Pina também:
 *   - Shape canônico: `data.suggestions_data.pipeline_template`
 *   - Shape legacy:   `data.pipeline_template`
 *   - No-op quando o intake_node não consegue sugerir (sem título)
 */
import React, { useState } from "react"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { act, cleanup, render } from "@testing-library/react"

import { useWizardFlow } from "../useWizardFlow"
import { useWizardChatCards } from "../useWizardChatCards"
import {
  WIZARD_TEMPLATE_MESSAGE_ID,
  type PipelineTemplateCardData,
} from "../wizard-plan-card"
import type { LiaChatMessage } from "@/hooks/chat/lia-chat-connection-types"

interface CapturedState {
  messages: LiaChatMessage[]
}

const captured: CapturedState = { messages: [] }

function Harness() {
  const flow = useWizardFlow({ userId: "user-test-1056" })
  const [messages, setMessages] = useState<LiaChatMessage[]>([])
  useWizardChatCards({
    wizardStage: flow.currentStage,
    wizardStageData: flow.stageData,
    setChatMessages: setMessages,
  })
  captured.messages = messages
  return <div data-testid="harness" />
}

function dispatchIntake(data: Record<string, unknown>) {
  window.dispatchEvent(
    new CustomEvent("lia:wizard-stage-payload", {
      detail: {
        type: "wizard_stage",
        stage: "intake",
        data,
        completeness: 0.05,
        requires_approval: false,
      },
    }),
  )
}

beforeEach(() => {
  captured.messages = []
  localStorage.clear()
})

afterEach(() => {
  cleanup()
  localStorage.clear()
})

describe("Wizard template card bridge — Task #1056", () => {
  it("injects WIZARD_TEMPLATE_MESSAGE_ID when intake_node emits the canonical suggestions_data.pipeline_template", () => {
    render(<Harness />)
    // Antes do evento, nenhum card.
    expect(
      captured.messages.find((m) => m.id === WIZARD_TEMPLATE_MESSAGE_ID),
    ).toBeUndefined()

    act(() => {
      // Shape EXATO emitido por intake_node (graph.py L218-222 +
      // _suggest_pipeline_template L132-135) para "Engenheiro Pleno":
      dispatchIntake({
        raw_input: "Engenheiro Pleno",
        parsed_title: "Engenheiro Pleno",
        suggestions_data: {
          pipeline_template: {
            suggested_type: "technical",
            templates: [
              "technical",
              "executive",
              "operational",
              "mass_hiring",
              "intern",
            ],
          },
        },
      })
    })

    const templateMsg = captured.messages.find(
      (m) => m.id === WIZARD_TEMPLATE_MESSAGE_ID,
    )
    expect(templateMsg, "card de template não foi injetado").toBeDefined()
    expect(templateMsg?.metadata?.type).toBe("wizard_template_select")
    const card = templateMsg?.metadata?.templateCard as
      | PipelineTemplateCardData
      | undefined
    expect(card?.suggestedType).toBe("technical")
    expect(card?.allowedTypes).toEqual([
      "technical",
      "executive",
      "operational",
      "mass_hiring",
      "intern",
    ])
  })

  it("aceita o shape legacy data.pipeline_template (sem wrapper suggestions_data)", () => {
    render(<Harness />)
    act(() => {
      dispatchIntake({
        raw_input: "Diretor Comercial",
        parsed_title: "Diretor Comercial",
        pipeline_template: {
          suggested_type: "executive",
          templates: ["executive", "technical"],
        },
      })
    })
    const templateMsg = captured.messages.find(
      (m) => m.id === WIZARD_TEMPLATE_MESSAGE_ID,
    )
    expect(templateMsg).toBeDefined()
    const card = templateMsg?.metadata?.templateCard as
      | PipelineTemplateCardData
      | undefined
    expect(card?.suggestedType).toBe("executive")
    expect(card?.allowedTypes).toEqual(["executive", "technical"])
  })

  it("não injeta card quando intake_node não conseguiu sugerir (data sem suggestions_data nem pipeline_template)", () => {
    render(<Harness />)
    act(() => {
      dispatchIntake({ raw_input: "oi", parsed_title: null })
    })
    expect(
      captured.messages.find((m) => m.id === WIZARD_TEMPLATE_MESSAGE_ID),
    ).toBeUndefined()
  })

  it("dedupa o card quando o backend re-emite o mesmo intake (turno 1 reentrante)", () => {
    render(<Harness />)
    const payload = {
      raw_input: "Engenheiro Pleno",
      parsed_title: "Engenheiro Pleno",
      suggestions_data: {
        pipeline_template: {
          suggested_type: "technical",
          templates: [
            "technical",
            "executive",
            "operational",
            "mass_hiring",
            "intern",
          ],
        },
      },
    }
    act(() => dispatchIntake(payload))
    act(() => dispatchIntake({ ...payload }))
    const cards = captured.messages.filter(
      (m) => m.id === WIZARD_TEMPLATE_MESSAGE_ID,
    )
    expect(cards).toHaveLength(1)
  })
})
