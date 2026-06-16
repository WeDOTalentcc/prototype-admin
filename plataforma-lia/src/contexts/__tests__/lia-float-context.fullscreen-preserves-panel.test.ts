// @vitest-environment jsdom
/**
 * Sensor: a transição bolha/lateral → TELA CHEIA (fullscreen) NÃO pode destruir
 * o painel dinâmico do wizard (`dynamicPanel`) nem o `entityContext`.
 *
 * Bug confirmado (2026-06-05): o painel lateral do wizard abria mas FECHAVA a
 * cada interação. Kill chain:
 *   1. UnifiedChat tem um efeito de auto-escalada que, no primeiro SPLIT_STAGE,
 *      chama `handleModeChange("fullscreen")`.
 *   2. `handleModeChange("fullscreen")` chamava `close()`.
 *   3. `close()` (dismiss canônico) zera `{isOpen, entityContext, dynamicPanel}`.
 *      → zerar `dynamicPanel` é o que derruba o painel (gate `hasDynamicPanel`).
 *
 * Fix canônico (no PRODUTOR, não no consumidor): a transição de fullscreen passa
 * a usar `enterFullscreen()`, que esconde o overlay (`isOpen:false`) SEM zerar
 * `dynamicPanel`/`entityContext`. O overlay já some sozinho em
 * `mode === "fullscreen"` (UnifiedChat retorna null pro overlay), então o
 * `close()` ali era redundante pra esconder E destrutivo pro painel.
 *
 * Invariante protegida: `close()` (user dismiss) CONTINUA zerando o painel —
 * isso é correto pra dismiss. Só o caminho de transição de fullscreen muda.
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

import {
  LiaFloatProvider,
  useLiaFloat,
  type DynamicPanelData,
  type EntityContext,
} from "@/contexts/lia-float-context"

function wrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(LiaFloatProvider, null, children)
}

const WIZARD_PANEL: DynamicPanelData = {
  panelType: "job_creation",
  data: { stage: "intake" },
  stage: "intake",
  requires_approval: false,
}

const JOB_ENTITY: EntityContext = {
  type: "job",
  id: "job-123",
  name: "Engenheiro Backend",
}

describe("Transição fullscreen PRESERVA o painel dinâmico do wizard", () => {
  beforeEach(() => {
    window.sessionStorage.clear()
  })

  it("enterFullscreen() PRESERVA dynamicPanel + entityContext (só esconde overlay)", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.open()
      result.current.openDynamicPanel(WIZARD_PANEL)
      result.current.setEntityContext(JOB_ENTITY)
    })
    expect(result.current.dynamicPanel).not.toBeNull()
    expect(result.current.entityContext).not.toBeNull()

    act(() => {
      result.current.enterFullscreen()
    })

    // overlay escondido…
    expect(result.current.isOpen).toBe(false)
    // …mas o painel do wizard e o contexto da entidade SOBREVIVEM.
    expect(result.current.dynamicPanel).not.toBeNull()
    expect(result.current.dynamicPanel?.panelType).toBe("job_creation")
    expect(result.current.dynamicPanel?.stage).toBe("intake")
    expect(result.current.entityContext).not.toBeNull()
    expect(result.current.entityContext?.id).toBe("job-123")
  })

  it("close() (user dismiss) CONTINUA zerando dynamicPanel + entityContext", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.open()
      result.current.openDynamicPanel(WIZARD_PANEL)
      result.current.setEntityContext(JOB_ENTITY)
    })
    expect(result.current.dynamicPanel).not.toBeNull()
    expect(result.current.entityContext).not.toBeNull()

    act(() => {
      result.current.close()
    })

    // dismiss canônico: tudo zerado (semântica preservada).
    expect(result.current.isOpen).toBe(false)
    expect(result.current.dynamicPanel).toBeNull()
    expect(result.current.entityContext).toBeNull()
  })

  it("closeAll() (dismiss total) também zera o painel (regressão de semântica)", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.open()
      result.current.openDynamicPanel(WIZARD_PANEL)
    })
    expect(result.current.dynamicPanel).not.toBeNull()

    act(() => {
      result.current.closeAll()
    })

    expect(result.current.dynamicPanel).toBeNull()
    expect(result.current.isOpen).toBe(false)
    expect(result.current.isExpanded).toBe(false)
  })
})
