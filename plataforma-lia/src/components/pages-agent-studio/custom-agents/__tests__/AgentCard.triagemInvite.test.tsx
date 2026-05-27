/**
 * Workstream A 2026-05-23 — AgentCard Triagem Invite UI sentinels.
 *
 * Wave A P0 #7 (2026-05-27): trailing "Enviar convite" button foi removido
 * (pertencia a surface com contexto de candidato+vaga — kanban). Asserts
 * referentes ao botao foram deletadas. Toggle de capability continua canonical.
 *
 * Cobre:
 * - 4o ChannelToggleRow renderiza com aria-label correto (WCAG 2.2 AA)
 * - Toggle dispara useToggleAgentChannel('triagem_invite')
 * - Coexistencia: 4 toggles (whatsapp + voice + voip + triagem_invite) na mesma card
 *
 * Pattern reference: AgentCard.voice.test.tsx + AgentCard.whatsapp.test.tsx
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

const toggleVoiceTrigger = vi.fn()
const initiateVoiceTrigger = vi.fn()
const toggleWhatsAppTrigger = vi.fn()
const toggleChannelTrigger = vi.fn()
const initiateTriagemInviteTrigger = vi.fn()

vi.mock("@/hooks/agent-studio/use-agent-voice", () => ({
  useToggleAgentVoice: () => ({ trigger: toggleVoiceTrigger, isMutating: false }),
  useInitiateVoiceCall: () => ({ trigger: initiateVoiceTrigger, isMutating: false }),
}))

vi.mock("@/hooks/agent-studio/use-agent-whatsapp", () => ({
  useToggleAgentWhatsApp: () => ({ trigger: toggleWhatsAppTrigger, isMutating: false }),
}))

vi.mock("@/hooks/agent-studio/use-agent-channel", () => ({
  useToggleAgentChannel: () => ({ trigger: toggleChannelTrigger, isMutating: false }),
}))

vi.mock("@/hooks/agent-studio/use-agent-triagem-invite", () => ({
  useInitiateAgentTriagemInvite: () => ({ trigger: initiateTriagemInviteTrigger, isMutating: false }),
}))

import { AgentCard } from "../AgentCard"
import type { CustomAgent } from "../types"

function makeAgent(overrides: Partial<CustomAgent> = {}): CustomAgent {
  return {
    id: "agent-uuid-1",
    company_id: "co-1",
    name: "TriagemInviteTestAgent",
    role: "Recruiter",
    description: "Test agent",
    system_prompt: "You are LIA.",
    allowed_tools: [],
    domain: "screening",
    icon: "agent",
    status: "draft",
    config: {},
    max_steps: 8,
    temperature: 0.7,
    model_override: null,
    enable_memory: true,
    context_level: "full",
    excluded_tools: [],
    voice_enabled: false,
    voip_enabled: false,
    whatsapp_enabled: false,
    triagem_invite_enabled: false,
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

describe("AgentCard — Triagem Invite UI (Workstream A 2026-05-23)", () => {
  beforeEach(() => {
    toggleVoiceTrigger.mockClear()
    initiateVoiceTrigger.mockClear()
    toggleWhatsAppTrigger.mockClear()
    toggleChannelTrigger.mockClear()
    initiateTriagemInviteTrigger.mockClear()
  })

  it("renderiza ChannelToggleRow de triagem invite com aria-label (WCAG)", () => {
    renderCard(makeAgent({ triagem_invite_enabled: false }))
    const toggle = screen.getByTestId("agent-card-triagem-invite-toggle")
    expect(toggle).toBeInTheDocument()
    expect(toggle.getAttribute("aria-label") || "").toMatch(/Habilitar|enableTriagemInvite/i)
  })

  it("Toggle dispara useToggleAgentChannel('triagem_invite') quando clicado em OFF", () => {
    renderCard(makeAgent({ triagem_invite_enabled: false }))
    const toggle = screen.getByTestId("agent-card-triagem-invite-toggle")
    fireEvent.click(toggle)
    expect(toggleChannelTrigger).toHaveBeenCalledWith(true)
  })

  it("Coexistencia: card renderiza 4 toggles (whatsapp + voice + voip + triagem_invite)", () => {
    renderCard(makeAgent({
      whatsapp_enabled: true,
      voice_enabled: true,
      voip_enabled: true,
      triagem_invite_enabled: true,
    }))
    expect(screen.getByTestId("agent-card-whatsapp-toggle")).toBeInTheDocument()
    expect(screen.getByTestId("agent-card-voice-toggle")).toBeInTheDocument()
    expect(screen.getByTestId("agent-card-voip-toggle")).toBeInTheDocument()
    expect(screen.getByTestId("agent-card-triagem-invite-toggle")).toBeInTheDocument()
  })
})
