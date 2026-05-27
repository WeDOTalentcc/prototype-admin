/**
 * Sprint 3.7 W4-1 — AgentCard voice UI sentinels
 *
 * Wave A P0 #6 (2026-05-27): trailing "Iniciar chamada" button foi removido
 * (pertencia a surface com contexto de candidato — kanban/perfil). Asserts
 * referentes ao botao foram deletadas. Toggle de canal continua canonical.
 *
 * Cobre:
 * - Switch de voz renderiza com aria-label correto (WCAG 2.2 AA)
 * - Toggle dispara mutation no useToggleAgentVoice
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

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
    expect(toggle.getAttribute("aria-label") || "").toMatch(/Habilitar|enableVoice/i)
  })

  it("Toggle dispara useToggleAgentVoice.mutate(true) quando clicado em OFF", () => {
    renderCard(makeAgent({ voice_enabled: false }))
    const toggle = screen.getByTestId("agent-card-voice-toggle")
    fireEvent.click(toggle)
    expect(toggleVoiceTrigger).toHaveBeenCalledWith(true)
  })
})
