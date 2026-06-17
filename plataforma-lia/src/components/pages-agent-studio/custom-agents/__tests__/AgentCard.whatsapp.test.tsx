/**
 * T5a UX Transformação 5 — AgentCard WhatsApp UI sentinels
 *
 * Cobre:
 * - Switch de WhatsApp renderiza com aria-label correto (WCAG 2.2 AA)
 * - Toggle dispara mutation no useToggleAgentWhatsApp
 * - Estado inicial reflete agent.whatsapp_enabled
 * - Ambos toggles (voice + whatsapp) coexistem na mesma card
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

// Mocks dos hooks — controlamos isPending + mutate spy
const toggleVoiceTrigger = vi.fn()
const initiateVoiceTrigger = vi.fn()
const toggleWhatsAppTrigger = vi.fn()

vi.mock("@/hooks/agent-studio/use-agent-voice", () => ({
  useToggleAgentVoice: () => ({ trigger: toggleVoiceTrigger, isMutating: false }),
  useInitiateVoiceCall: () => ({ trigger: initiateVoiceTrigger, isMutating: false }),
}))

vi.mock("@/hooks/agent-studio/use-agent-whatsapp", () => ({
  useToggleAgentWhatsApp: () => ({ trigger: toggleWhatsAppTrigger, isMutating: false }),
}))

import { AgentCard } from "../AgentCard"
import type { CustomAgent } from "../types"

function makeAgent(overrides: Partial<CustomAgent> = {}): CustomAgent {
  return {
    id: "agent-uuid-1",
    company_id: "co-1",
    name: "WhatsAppTestAgent",
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
    whatsapp_enabled: false,
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

describe("AgentCard — WhatsApp UI (T5a UX Transformação 5)", () => {
  beforeEach(() => {
    toggleVoiceTrigger.mockClear()
    initiateVoiceTrigger.mockClear()
    toggleWhatsAppTrigger.mockClear()
  })

  it("renderiza Switch de WhatsApp com aria-label (WCAG 2.2 AA)", () => {
    renderCard(makeAgent({ whatsapp_enabled: false }))
    const toggle = screen.getByTestId("agent-card-whatsapp-toggle")
    expect(toggle).toBeInTheDocument()
    // aria-label deve refletir estado (Habilitar quando OFF)
    expect(toggle.getAttribute("aria-label")).toMatch(/Habilitar WhatsApp|enableWhatsapp/i)
  })

  it("Switch WhatsApp em estado checked quando whatsapp_enabled=true", () => {
    renderCard(makeAgent({ whatsapp_enabled: true }))
    const toggle = screen.getByTestId("agent-card-whatsapp-toggle")
    expect(toggle.getAttribute("data-state")).toBe("checked")
    expect(toggle.getAttribute("aria-label")).toMatch(/Desabilitar WhatsApp|disableWhatsapp/i)
  })

  it("Switch WhatsApp em estado unchecked quando whatsapp_enabled=false/undefined", () => {
    renderCard(makeAgent({ whatsapp_enabled: false }))
    const toggle = screen.getByTestId("agent-card-whatsapp-toggle")
    expect(toggle.getAttribute("data-state")).toBe("unchecked")
  })

  it("Toggle WhatsApp dispara mutation com novo valor", () => {
    renderCard(makeAgent({ whatsapp_enabled: false }))
    const toggle = screen.getByTestId("agent-card-whatsapp-toggle")
    fireEvent.click(toggle)
    expect(toggleWhatsAppTrigger).toHaveBeenCalledTimes(1)
    expect(toggleWhatsAppTrigger).toHaveBeenCalledWith(true)
  })

  it("Renderiza AMBOS toggles (voice + whatsapp) coexistindo na card", () => {
    renderCard(makeAgent({ voice_enabled: true, whatsapp_enabled: true }))
    expect(screen.getByTestId("agent-card-voice-toggle")).toBeInTheDocument()
    expect(screen.getByTestId("agent-card-whatsapp-toggle")).toBeInTheDocument()
  })

  it("Toggle WhatsApp é independente do Switch de voz", () => {
    renderCard(makeAgent({ voice_enabled: false, whatsapp_enabled: true }))
    const wsToggle = screen.getByTestId("agent-card-whatsapp-toggle")
    const voiceToggle = screen.getByTestId("agent-card-voice-toggle")
    // WhatsApp ON, voice OFF → estados diferentes
    expect(wsToggle.getAttribute("data-state")).toBe("checked")
    expect(voiceToggle.getAttribute("data-state")).toBe("unchecked")
  })
})
