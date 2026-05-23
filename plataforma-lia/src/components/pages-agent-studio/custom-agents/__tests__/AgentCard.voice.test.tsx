/**
 * Sprint 3.7 W4-1 — AgentCard voice UI sentinels
 *
 * Cobre:
 * - Switch de voz renderiza com aria-label correto (WCAG 2.2 AA)
 * - "Iniciar chamada" button disabled quando voice_enabled = false
 * - "Iniciar chamada" button habilitado quando voice_enabled = true
 * - Toggle dispara mutation no useToggleAgentVoice
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"
// Note: project uses SWR — no provider wrapper needed for these mock-level tests

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

// Mocks dos hooks — controlamos isPending + mutate spy
const toggleVoiceTrigger = vi.fn()
const initiateVoiceTrigger = vi.fn()

vi.mock("@/hooks/agent-studio/use-agent-voice", () => ({
  useToggleAgentVoice: () => ({ trigger: toggleVoiceTrigger, isMutating: false }),
  useInitiateVoiceCall: () => ({ trigger: initiateVoiceTrigger, isMutating: false }),
}))

import { AgentCard } from "../AgentCard"
import type { CustomAgent } from "../types"

function makeAgent(overrides: Partial<CustomAgent> = {}): CustomAgent {
  return {
    id: "agent-uuid-1",
    company_id: "co-1",
    name: "VoiceTestAgent",
    role: "Recruiter",
    description: "Test agent",
    system_prompt: "You are LIA.",
    allowed_tools: [],
    domain: "screening",
    icon: "🤖",
    status: "draft",
    config: {},
    max_steps: 8,
    temperature: 0.7,
    model_override: null,
    enable_memory: true,
    context_level: "full",
    excluded_tools: [],
    voice_enabled: false,
    total_executions: 0,
    avg_confidence: 0,
    last_executed_at: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  } as CustomAgent
}

function renderCard(agent: CustomAgent) {
  return render(
    <AgentCard
      agent={agent}
      onTest={() => {}}
      onDeploy={() => {}}
      onToggleStatus={() => {}}
    />,
  )
}

describe("AgentCard — voice UI (Sprint 3.7 W4-1)", () => {
  beforeEach(() => {
    toggleVoiceTrigger.mockClear()
    initiateVoiceTrigger.mockClear()
  })

  it("renderiza Switch de voz com aria-label (WCAG)", () => {
    renderCard(makeAgent({ voice_enabled: false }))
    const toggle = screen.getByTestId("agent-card-voice-toggle")
    expect(toggle).toBeInTheDocument()
    // aria-label deve refletir estado (Habilitar quando OFF)
    expect(toggle.getAttribute("aria-label") || "").toMatch(/Habilitar|enableVoice/i)
  })

  it('"Iniciar chamada" button DISABLED quando voice_enabled = false', () => {
    renderCard(makeAgent({ voice_enabled: false }))
    const btn = screen.getByTestId("agent-card-initiate-voice") as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })

  it('"Iniciar chamada" button HABILITADO quando voice_enabled = true', () => {
    renderCard(makeAgent({ voice_enabled: true }))
    const btn = screen.getByTestId("agent-card-initiate-voice") as HTMLButtonElement
    expect(btn.disabled).toBe(false)
    // aria-label semântico
    expect(btn.getAttribute("aria-label") || "").toMatch(/Iniciar|startVoiceCall/i)
  })

  it("Toggle dispara useToggleAgentVoice.mutate(true) quando clicado em OFF", () => {
    renderCard(makeAgent({ voice_enabled: false }))
    const toggle = screen.getByTestId("agent-card-voice-toggle")
    fireEvent.click(toggle)
    expect(toggleVoiceTrigger).toHaveBeenCalledWith(true)
  })

  it("Click no Iniciar chamada NÃO dispara mutation se voice_enabled = false", () => {
    renderCard(makeAgent({ voice_enabled: false }))
    const btn = screen.getByTestId("agent-card-initiate-voice")
    fireEvent.click(btn)
    expect(initiateVoiceTrigger).not.toHaveBeenCalled()
  })

  it("Click no Iniciar chamada dispara initiate mutation quando habilitado", () => {
    renderCard(makeAgent({ voice_enabled: true }))
    const btn = screen.getByTestId("agent-card-initiate-voice")
    fireEvent.click(btn)
    expect(initiateVoiceTrigger).toHaveBeenCalledTimes(1)
  })
})
