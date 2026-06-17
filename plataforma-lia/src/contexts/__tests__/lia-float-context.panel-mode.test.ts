// @vitest-environment jsdom
/**
 * Sensor: `wizardPanelMode` ("docked" | "expanded") no LiaFloatContext
 * (Wizard Manus F1 — Task 1).
 *
 * Invariantes protegidas:
 *   1. Default é "docked".
 *   2. O modo é STICKY: novos payloads `lia:wizard-stage-payload` SEM
 *      `panel_pref` NÃO resetam o modo escolhido.
 *   3. Stage terminal ("done" / "handoff") força "docked" (recolhe pro dock).
 *   4. Payload com `data.panel_pref` ("expanded" | "docked") aplica o modo
 *      (tool open/close_panel do backend).
 *
 * Harness espelha `lia-float-context.fullscreen-preserves-panel.test.ts`
 * (sensor comportamental, jsdom + renderHook, conexão de chat mockada).
 *
 * Skill canônica: harness-engineering [sensor comportamental].
 */
import { act, renderHook } from "@testing-library/react"
import React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"

// Mock da camada de conexão de chat — só importa o state do provider, não WS.
vi.mock("@/hooks/chat/use-lia-chat-connection", () => {
  let conversationId: string | null = null
  return {
    useLiaChatConnection: () => ({
      conversationId,
      setConversationId: (id: string | null) => {
        conversationId = id
      },
      sendMessage: vi.fn(async () => {}),
      initConversation: vi.fn(async () => null),
      loadHistory: vi.fn(async () => []),
      sendApproval: vi.fn(),
      isConnected: false,
      transportMode: "ws" as const,
      isReconnecting: false,
      isStreaming: false,
      streamingContent: "",
      hitlPending: null,
      backgroundTasks: [],
      clearBackgroundTask: vi.fn(),
      resetBackgroundTasks: vi.fn(),
      seedBackgroundTask: vi.fn(),
      isCreating: false,
      isFetchingHistory: false,
      isThinking: false,
      thinkingSteps: [],
      planProgressSteps: [],
      activePlanId: null,
      fairnessWarnings: [],
      dismissFairnessWarnings: vi.fn(),
      connect: vi.fn(),
      disconnect: vi.fn(),
    }),
  }
})

vi.mock("@/hooks/chat/useUIAction", () => ({
  useUIAction: () => ({ dispatchOrEmit: vi.fn() }),
}))

// O provider lê usePathname (badge URL-reactive, commit 02df27363) — jsdom
// não tem App Router; mock determinístico.
vi.mock("next/navigation", () => ({
  usePathname: () => "/pt/recrutar",
}))

import { LiaFloatProvider, useLiaFloat } from "@/contexts/lia-float-context"

function wrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(LiaFloatProvider, null, children)
}

function dispatchStagePayload(detail: Record<string, unknown>) {
  act(() => {
    window.dispatchEvent(
      new CustomEvent("lia:wizard-stage-payload", { detail }),
    )
  })
}

describe("Manus F1 — wizardPanelMode docked|expanded", () => {
  beforeEach(() => {
    window.sessionStorage.clear()
  })

  it("default é 'docked'", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })
    expect(result.current.wizardPanelMode).toBe("docked")
  })

  it("setWizardPanelMode('expanded') persiste através de novos wizard_stage payloads (sticky)", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.setWizardPanelMode("expanded")
    })
    expect(result.current.wizardPanelMode).toBe("expanded")

    dispatchStagePayload({ stage: "wsi_questions", data: {} })

    // Sticky: payload sem panel_pref NÃO reseta o modo.
    expect(result.current.wizardPanelMode).toBe("expanded")
    // A bridge continua abrindo o painel normalmente.
    expect(result.current.dynamicPanel?.stage).toBe("wsi_questions")
  })

  it("stage done/handoff força 'docked'", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.setWizardPanelMode("expanded")
    })
    expect(result.current.wizardPanelMode).toBe("expanded")

    dispatchStagePayload({ stage: "done", data: {} })
    expect(result.current.wizardPanelMode).toBe("docked")

    // handoff também recolhe.
    act(() => {
      result.current.setWizardPanelMode("expanded")
    })
    dispatchStagePayload({ stage: "handoff", data: {} })
    expect(result.current.wizardPanelMode).toBe("docked")
  })

  it("payload com data.panel_pref aplica o modo", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    dispatchStagePayload({
      stage: "wsi_questions",
      data: { panel_pref: "expanded" },
    })
    expect(result.current.wizardPanelMode).toBe("expanded")

    dispatchStagePayload({
      stage: "wsi_questions",
      data: { panel_pref: "docked" },
    })
    expect(result.current.wizardPanelMode).toBe("docked")
  })
})
