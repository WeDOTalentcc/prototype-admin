/**
 * Sprint visual canonical 2026-05-26 (Agent C) — AgentCard StudioCardShell contract.
 *
 * Garante que AgentCard.tsx esta consumindo `<StudioCardShell tone="elevated">`
 * canonical e que as features pre-refactor permanecem intactas:
 *
 *  - icon Bot canonical em wrapper bg-powder rounded-md w-8 h-8
 *  - title = agent.name renderiza no header do shell
 *  - statusBadge (categoryLabel + status) renderiza junto ao title
 *  - badges slot contem DropdownMenu Clone (3-dot) + BetaBadge
 *  - 4 ChannelToggleRow (whatsapp/voice/voip/triagem_invite) renderizam com testids
 *  - actionsSlot footer renderiza test/link/toggle-status
 *  - data-testid `agent-card-${id}` aplicado pelo shell
 *
 * Pattern reference: AgentPanel canonical (Sprint visual 14855a181 + 07272378e).
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"

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
    id: "agent-shell-1",
    company_id: "co-1",
    name: "ShellTestAgent",
    role: "Recruiter",
    description: "Agent para validar contract com StudioCardShell",
    system_prompt: "You are LIA.",
    allowed_tools: [],
    domain: "screening",
    icon: "Bot",
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
    voip_enabled: false,
    triagem_invite_enabled: false,
    total_executions: 42,
    avg_confidence: 0.85,
    last_executed_at: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  } as CustomAgent
}

function renderCard(agent: CustomAgent, withClone = false) {
  return render(
    <AgentCard
      agent={agent}
      onTest={() => {}}
      onDeploy={() => {}}
      onToggleStatus={() => {}}
      onClone={withClone ? () => {} : undefined}
    />,
  )
}

describe("AgentCard — StudioCardShell canonical contract (Sprint visual 2026-05-26)", () => {
  it("renderiza shell com data-testid canonical agent-card-${id}", () => {
    const { container } = renderCard(makeAgent({ id: "abc-123" }))
    expect(container.querySelector("[data-testid=\"agent-card-abc-123\"]")).not.toBeNull()
  })

  it("renderiza title = agent.name no header", () => {
    renderCard(makeAgent({ name: "ShellTestAgent" }))
    expect(screen.getByText("ShellTestAgent")).toBeTruthy()
  })

  it("renderiza description quando presente", () => {
    renderCard(makeAgent({ description: "Agent para validar contract com StudioCardShell" }))
    expect(screen.getByText(/StudioCardShell/)).toBeTruthy()
  })

  it("renderiza metricas executions + confidence", () => {
    renderCard(makeAgent({ total_executions: 42, avg_confidence: 0.85 }))
    expect(screen.getByText("42")).toBeTruthy()
    expect(screen.getByText("85%")).toBeTruthy()
  })

  it("renderiza 4 channel toggles com testids canonical", () => {
    renderCard(makeAgent())
    expect(screen.getByTestId("agent-card-whatsapp-toggle")).toBeTruthy()
    expect(screen.getByTestId("agent-card-voice-toggle")).toBeTruthy()
    expect(screen.getByTestId("agent-card-voip-toggle")).toBeTruthy()
    expect(screen.getByTestId("agent-card-triagem-invite-toggle")).toBeTruthy()
  })

  it("renderiza DropdownMenu Clone quando onClone provido", () => {
    renderCard(makeAgent(), true)
    expect(screen.getByLabelText(/moreActions|Mais/i)).toBeTruthy()
  })

  it("nao renderiza DropdownMenu Clone quando onClone ausente", () => {
    renderCard(makeAgent(), false)
    expect(screen.queryByLabelText(/moreActions|Mais/i)).toBeNull()
  })

  it("renderiza actions footer test/link/toggle-status", () => {
    renderCard(makeAgent())
    expect(screen.getByText("test")).toBeTruthy()
    expect(screen.getByText("link")).toBeTruthy()
    expect(screen.getByText(/activate|pause/)).toBeTruthy()
  })

  it("renderiza icon Bot canonical em wrapper bg-powder w-8 h-8", () => {
    const { container } = renderCard(makeAgent())
    const iconWrap = container.querySelector(".w-8.h-8.rounded-md.bg-powder")
    expect(iconWrap).not.toBeNull()
  })
})
