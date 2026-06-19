// @vitest-environment jsdom
/**
 * Sensor tests — Inline enriched cards (T1–T4)
 *
 * T1: useWizardChatCards stage card injection effect
 * T2: WizardIntakeCard renders from structured payload
 * T3: WizardCompetencyCard renders from structured payload
 * T4: Stage card metadata contract (type + wizardStage + wizardStageData)
 */
import React from "react"
import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { act, renderHook } from "@testing-library/react"
import { useState } from "react"

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_target: object, tag: string) =>
        ({ children, ...props }: React.HTMLAttributes<HTMLElement> & { children?: React.ReactNode }) =>
          React.createElement(tag, props, children),
    },
  ),
  AnimatePresence: ({ children }: { children?: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}))

import { WizardIntakeCard } from "../WizardIntakeCard"
import { WizardCompetencyCard } from "../WizardCompetencyCard"
import {
  useWizardChatCards,
  WIZARD_STAGE_CARD_MESSAGE_ID,
} from "../useWizardChatCards"
import type { WizardStage } from "../wizard-types"
import type { LiaChatMessage } from "@/hooks/chat/lia-chat-connection-types"

// ── Harness ────────────────────────────────────────────────────────────────────

interface HookProps {
  wizardStage: WizardStage | null
  wizardStageData: Record<string, unknown> | null
}

function useHarness(initial: HookProps) {
  const [props, setProps] = useState<HookProps>(initial)
  const [messages, setMessages] = useState<LiaChatMessage[]>([])
  useWizardChatCards({
    wizardStage: props.wizardStage,
    wizardStageData: props.wizardStageData,
    setChatMessages: setMessages,
  })
  return { messages, setProps, resetMessages: () => setMessages([]) }
}

// ── T1: Stage card injection ───────────────────────────────────────────────────

describe("useWizardChatCards — stage card injection", () => {
  it("injects a stage card when wizardStage is intake + data present", () => {
    const stageData = { parsed_title: "Dev Sênior", parsed_seniority: "senior" }
    const { result } = renderHook(() =>
      useHarness({ wizardStage: "intake", wizardStageData: stageData }),
    )
    const stageCard = result.current.messages.find(
      (m) => m.id === WIZARD_STAGE_CARD_MESSAGE_ID,
    )
    expect(stageCard).toBeDefined()
    expect(stageCard?.metadata?.type).toBe("wizard_stage_card")
    expect(stageCard?.metadata?.wizardStage).toBe("intake")
    expect(stageCard?.metadata?.wizardStageData).toEqual(stageData)
  })

  it("does NOT inject a stage card for non-card stages (e.g. review)", () => {
    const { result } = renderHook(() =>
      useHarness({ wizardStage: "review", wizardStageData: { some: "data" } }),
    )
    const stageCard = result.current.messages.find(
      (m) => m.id === WIZARD_STAGE_CARD_MESSAGE_ID,
    )
    expect(stageCard).toBeUndefined()
  })

  it("does NOT inject when wizardStageData is null", () => {
    const { result } = renderHook(() =>
      useHarness({ wizardStage: "intake", wizardStageData: null }),
    )
    const stageCard = result.current.messages.find(
      (m) => m.id === WIZARD_STAGE_CARD_MESSAGE_ID,
    )
    expect(stageCard).toBeUndefined()
  })

  it("updates the card in-place when stageData changes for the same stage", () => {
    const data1 = { parsed_title: "Dev" }
    const data2 = { parsed_title: "Dev Sênior", parsed_seniority: "senior" }
    const { result } = renderHook(() =>
      useHarness({ wizardStage: "intake", wizardStageData: data1 }),
    )
    act(() => {
      result.current.setProps({ wizardStage: "intake", wizardStageData: data2 })
    })
    const cards = result.current.messages.filter(
      (m) => m.metadata?.type === "wizard_stage_card",
    )
    expect(cards).toHaveLength(1)
    expect(cards[0].metadata?.wizardStageData).toEqual(data2)
  })

  it("promotes old stage card to permanent ID when stage changes", () => {
    const { result } = renderHook(() =>
      useHarness({
        wizardStage: "intake",
        wizardStageData: { parsed_title: "Dev" },
      }),
    )
    act(() => {
      result.current.setProps({
        wizardStage: "jd_enrichment",
        wizardStageData: { jd_enriched: { titulo_padronizado: "Dev" }, quality_score: 80 },
      })
    })
    const permanentIntake = result.current.messages.find(
      (m) => m.id === "lia-wizard-stage-intake",
    )
    expect(permanentIntake).toBeDefined()
    expect(permanentIntake?.metadata?.wizardStage).toBe("intake")

    const activeCard = result.current.messages.find(
      (m) => m.id === WIZARD_STAGE_CARD_MESSAGE_ID,
    )
    expect(activeCard?.metadata?.wizardStage).toBe("jd_enrichment")
  })

  it("injects cards for all 5 eligible stages", () => {
    const stages: WizardStage[] = [
      "intake",
      "jd_enrichment",
      "competency",
      "wsi_questions",
      "calibration",
    ]
    for (const stage of stages) {
      const { result } = renderHook(() =>
        useHarness({ wizardStage: stage, wizardStageData: { test: true } }),
      )
      const stageCard = result.current.messages.find(
        (m) => m.id === WIZARD_STAGE_CARD_MESSAGE_ID,
      )
      expect(stageCard, `stage card must exist for stage '${stage}'`).toBeDefined()
      expect(stageCard?.metadata?.wizardStage).toBe(stage)
    }
  })

  it("re-injects stage card after messages are cleared (Bug A reconnect regression)", () => {
    // Simulates: after WebSocket reconnect, chatMessages are reset but
    // wizardStage stays "wsi_questions". Hydration GETs checkpoint and
    // calls handleStagePayload → new object reference for stageData.
    // The effect re-fires because stageData ref changed; without the latch
    // guard on idx===-1, the card is re-injected.
    const stageData1 = { questions: [{ question: "Q1", block: "technical" }] }
    // Hydration returns a new object (same content, different reference)
    const stageData2 = { questions: [{ question: "Q1", block: "technical" }] }
    const { result } = renderHook(() =>
      useHarness({ wizardStage: "wsi_questions", wizardStageData: stageData1 }),
    )
    // 1. Initial mount: card injected, latch set to true
    expect(
      result.current.messages.find((m) => m.id === WIZARD_STAGE_CARD_MESSAGE_ID),
    ).toBeDefined()

    // 2. Simulate reconnect: messages cleared (non-persisted cards evicted)
    act(() => {
      result.current.resetMessages()
    })
    expect(result.current.messages).toHaveLength(0)

    // 3. Hydration fires with new stageData reference → effect re-fires
    // Card MUST be re-injected even though latch was set from before reset
    act(() => {
      result.current.setProps({ wizardStage: "wsi_questions", wizardStageData: stageData2 })
    })
    const reinjected = result.current.messages.find(
      (m) => m.id === WIZARD_STAGE_CARD_MESSAGE_ID,
    )
    expect(reinjected).toBeDefined()
    expect(reinjected?.metadata?.wizardStage).toBe("wsi_questions")
  })
})

// ── T2: WizardIntakeCard ───────────────────────────────────────────────────────

describe("WizardIntakeCard — payload determinístico", () => {
  const baseData = {
    parsed_title: "Engenheira de Dados Pleno",
    parsed_seniority: "Pleno",
    parsed_model: "Remoto",
    parsed_department: "Engenharia",
    parsed_manager: "Carlos",
  }

  it("renderiza o título no header", () => {
    render(<WizardIntakeCard data={baseData} />)
    expect(screen.getByText("Engenheira de Dados Pleno")).toBeInTheDocument()
  })

  it("mostra contador de campos preenchidos", () => {
    render(<WizardIntakeCard data={baseData} />)
    expect(screen.getByText("5/5 campos preenchidos")).toBeInTheDocument()
  })

  it("mostra campos parcialmente preenchidos (2/5)", () => {
    render(<WizardIntakeCard data={{ parsed_title: "Dev", parsed_seniority: "Junior" }} />)
    expect(screen.getByText("2/5 campos preenchidos")).toBeInTheDocument()
  })

  it("expande accordion ao clicar no header", () => {
    render(<WizardIntakeCard data={baseData} />)
    const header = screen.getByRole("button", { expanded: false })
    fireEvent.click(header)
    expect(screen.getByText("Remoto")).toBeInTheDocument()
    expect(screen.getByText("Engenharia")).toBeInTheDocument()
    expect(screen.getByText("Carlos")).toBeInTheDocument()
  })

  it("mostra badge de vaga afirmativa quando is_affirmative=true", () => {
    render(
      <WizardIntakeCard
        data={{
          ...baseData,
          is_affirmative: true,
          affirmative_criteria_primary: "disability",
        }}
      />,
    )
    const header = screen.getByRole("button", { expanded: false })
    fireEvent.click(header)
    expect(screen.getByText("Vaga afirmativa")).toBeInTheDocument()
  })

  it("retorna null quando nenhum campo preenchido e sem message", () => {
    const { container } = render(<WizardIntakeCard data={{}} />)
    expect(container.firstChild).toBeNull()
  })

  it("chama onOpenPanel ao clicar em 'Abrir no painel'", () => {
    const onOpenPanel = vi.fn()
    render(<WizardIntakeCard data={baseData} onOpenPanel={onOpenPanel} />)
    const header = screen.getByRole("button", { expanded: false })
    fireEvent.click(header)
    fireEvent.click(screen.getByText(/abrir no painel/i))
    expect(onOpenPanel).toHaveBeenCalledTimes(1)
  })

  it("smoke: rerender mount/unmount sem throw (Rules of Hooks)", () => {
    const { rerender, unmount } = render(<WizardIntakeCard data={baseData} />)
    rerender(<WizardIntakeCard data={{ parsed_title: "QA" }} />)
    unmount()
  })
})

// ── T3: WizardCompetencyCard ───────────────────────────────────────────────────

describe("WizardCompetencyCard — payload determinístico", () => {
  const tree = [
    { skill: "Python", block: "technical" as const },
    { skill: "FastAPI", block: "technical" as const },
    { skill: "Comunicação", block: "behavioral" as const },
    { skill: "Liderança", block: "behavioral" as const },
    { skill: "Docker", block: "technical" as const },
    { skill: "Resiliência", block: "behavioral" as const },
  ]

  const baseData = {
    competency_tree: tree,
    seniority_display: "Sênior",
    screening_mode: "compact",
    distribution: { technical: 3, behavioral: 3 },
  }

  it("renderiza contador de competências no header", () => {
    render(<WizardCompetencyCard data={baseData} />)
    expect(screen.getByText("6 competências mapeadas")).toBeInTheDocument()
  })

  it("mostra distribuição técnica/comportamental no subtítulo", () => {
    render(<WizardCompetencyCard data={baseData} />)
    expect(screen.getByText(/3 técnicas · 3 comportamentais · Sênior/)).toBeInTheDocument()
  })

  it("renderiza primeiras 4 competências sem expandir", () => {
    render(<WizardCompetencyCard data={baseData} />)
    expect(screen.getByText("Python")).toBeInTheDocument()
    expect(screen.getByText("FastAPI")).toBeInTheDocument()
    expect(screen.getByText("Comunicação")).toBeInTheDocument()
    expect(screen.getByText("Liderança")).toBeInTheDocument()
  })

  it("expande para mostrar todas ao clicar no header", () => {
    render(<WizardCompetencyCard data={baseData} />)
    const header = screen.getByRole("button", { name: /6 competências mapeadas/i })
    fireEvent.click(header)
    expect(screen.getByText("Docker")).toBeInTheDocument()
    expect(screen.getByText("Resiliência")).toBeInTheDocument()
  })

  it("mostra pill do screening_mode", () => {
    render(<WizardCompetencyCard data={baseData} />)
    expect(screen.getByText("compact")).toBeInTheDocument()
  })

  it("retorna null quando competency_tree está vazio", () => {
    const { container } = render(
      <WizardCompetencyCard data={{ competency_tree: [] }} />,
    )
    expect(container.firstChild).toBeNull()
  })

  it("chama onOpenPanel ao clicar em 'Abrir no painel'", () => {
    const onOpenPanel = vi.fn()
    render(<WizardCompetencyCard data={baseData} onOpenPanel={onOpenPanel} />)
    fireEvent.click(screen.getByText(/abrir no painel/i))
    expect(onOpenPanel).toHaveBeenCalledTimes(1)
  })

  it("smoke: rerender mount/unmount sem throw (Rules of Hooks)", () => {
    const { rerender, unmount } = render(
      <WizardCompetencyCard data={baseData} />,
    )
    rerender(
      <WizardCompetencyCard data={{ ...baseData, seniority_display: "Pleno" }} />,
    )
    unmount()
  })
})

// ── T4: Metadata contract ──────────────────────────────────────────────────────

describe("Stage card metadata contract", () => {
  it("WIZARD_STAGE_CARD_MESSAGE_ID is exported and has the canonical prefix", () => {
    expect(WIZARD_STAGE_CARD_MESSAGE_ID).toBe("lia-wizard-stage-card")
  })

  it("stage card metadata has the 3 required fields", () => {
    const stageData = { parsed_title: "Dev" }
    const { result } = renderHook(() =>
      useHarness({ wizardStage: "intake", wizardStageData: stageData }),
    )
    const card = result.current.messages.find(
      (m) => m.id === WIZARD_STAGE_CARD_MESSAGE_ID,
    )
    expect(card?.metadata).toHaveProperty("type", "wizard_stage_card")
    expect(card?.metadata).toHaveProperty("wizardStage", "intake")
    expect(card?.metadata).toHaveProperty("wizardStageData", stageData)
  })
})
