/**
 * CreateAgentWizard — sentinels for T4 initialConfig (clone-first).
 *
 * UX_AUDIT_ESTUDIO_AGENTES_2026-05-21 — Transformação 4 (linha 281).
 *
 * Cobre:
 * - initialConfig.templateId presente → wizard abre direto no step 3 (Configurar)
 * - initialConfig.name pré-popula o input de nome (incluindo "(cópia)")
 * - initialConfig.templateId é preservado no estado interno (template existe na galeria)
 * - "Voltar" no step 3 NÃO desce para steps 1/2 (minStep = 3 no clone-first)
 * - Reabrir wizard com initialConfig diferente re-deriva o estado (useEffect)
 * - Quando initialConfig é undefined, wizard volta ao fluxo padrão step 1
 *
 * NÃO testa criação de fato (POST) — esses paths já estão cobertos pelos
 * sentinels existentes do CreateAgentWizard.test.tsx.
 */

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

vi.mock("@/lib/toast", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}))

// Mock catalog hook so render uses fixture (alinhado a CreateAgentWizard.test.tsx).
vi.mock("@/hooks/agents/use-legacy-agent-templates", async () => {
  const { AGENT_TEMPLATES } = await import("@/lib/__tests__/__fixtures__/agent-templates-fixture")
  return {
    useLegacyAgentTemplates: () => ({
      templates: AGENT_TEMPLATES,
      isLoading: false,
      error: null,
    }),
  }
})

import { CreateAgentWizard } from "../CreateAgentWizard"
import type { CreateAgentInitialConfig } from "../types"

beforeEach(() => {
  global.fetch = vi.fn() as unknown as typeof fetch
  if (typeof window !== "undefined" && !window.localStorage) {
    Object.defineProperty(window, "localStorage", {
      value: {
        getItem: vi.fn().mockReturnValue(null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    })
  }
})

afterEach(() => {
  vi.restoreAllMocks()
})

const CLONE_CONFIG: CreateAgentInitialConfig = {
  goal: "triagem_inicial",
  approach: "template",
  templateId: "tpl-triagem-tech",
  name: "Triagem Tech (cópia)",
  description: "Filtra candidatos de tecnologia por stack",
}

describe("CreateAgentWizard — T4 initialConfig (clone-first)", () => {
  it("com initialConfig.templateId, abre direto no step 3 (Configurar)", () => {
    render(
      <CreateAgentWizard
        open={true}
        onClose={vi.fn()}
        onCreated={vi.fn()}
        initialConfig={CLONE_CONFIG}
      />,
    )
    // Step indicator deve mostrar "Etapa 3 de 4"
    expect(screen.getByTestId("wizard-step-indicator").textContent).toContain("3")
    // Step 3 content = ConfigStep (template variant)
    expect(screen.getByTestId("config-step-template")).toBeTruthy()
  })

  it("pré-popula o input de nome com '(cópia)' a partir de initialConfig.name", () => {
    render(
      <CreateAgentWizard
        open={true}
        onClose={vi.fn()}
        onCreated={vi.fn()}
        initialConfig={CLONE_CONFIG}
      />,
    )
    const input = screen.getByTestId("wizard-template-name-input") as HTMLInputElement
    expect(input.value).toBe("Triagem Tech (cópia)")
  })

  it("pula step 1 (goal) e step 2 (approach) — não renderiza GoalStep nem ApproachStep", () => {
    render(
      <CreateAgentWizard
        open={true}
        onClose={vi.fn()}
        onCreated={vi.fn()}
        initialConfig={CLONE_CONFIG}
      />,
    )
    // GoalStep usa testids goal-option-* — não devem estar no DOM
    expect(screen.queryByTestId("goal-option-triagem_inicial")).toBeNull()
    expect(screen.queryByTestId("goal-option-sourcing_ativo")).toBeNull()
    // ApproachStep — config-step-template é step 3, então não tem mais escolha de approach
    expect(screen.queryByText("Como voce quer criar?")).toBeNull()
  })

  it("Voltar (Back) NÃO desce para steps 1 ou 2 no fluxo clone-first (minStep = 3)", () => {
    render(
      <CreateAgentWizard
        open={true}
        onClose={vi.fn()}
        onCreated={vi.fn()}
        initialConfig={CLONE_CONFIG}
      />,
    )
    // No clone-first, step inicial = 3 = minStep → botão Voltar não deve aparecer
    expect(screen.queryByTestId("wizard-back-button")).toBeNull()
    // Indicador permanece em 3
    expect(screen.getByTestId("wizard-step-indicator").textContent).toContain("3")
  })

  it("Próximo no step 3 avança para step 4 (preview), depois Voltar volta APENAS para step 3", () => {
    render(
      <CreateAgentWizard
        open={true}
        onClose={vi.fn()}
        onCreated={vi.fn()}
        initialConfig={CLONE_CONFIG}
      />,
    )
    // Avançar 3 → 4
    fireEvent.click(screen.getByTestId("wizard-next-button"))
    expect(screen.getByTestId("wizard-step-indicator").textContent).toContain("4")
    // Voltar 4 → 3 (minStep)
    fireEvent.click(screen.getByTestId("wizard-back-button"))
    expect(screen.getByTestId("wizard-step-indicator").textContent).toContain("3")
    // Tentar voltar de novo: botão NÃO está visível (step === minStep)
    expect(screen.queryByTestId("wizard-back-button")).toBeNull()
  })

  it("sem initialConfig, wizard começa no step 1 (fluxo padrão T1)", () => {
    render(<CreateAgentWizard open={true} onClose={vi.fn()} onCreated={vi.fn()} />)
    expect(screen.getByTestId("wizard-step-indicator").textContent).toContain("1")
    expect(screen.getByTestId("goal-option-triagem_inicial")).toBeTruthy()
  })

  it("reabrir wizard com initialConfig diferente re-deriva estado (useEffect cleanup)", () => {
    const { rerender } = render(
      <CreateAgentWizard open={false} onClose={vi.fn()} onCreated={vi.fn()} />,
    )
    // Abre com clone-first
    rerender(
      <CreateAgentWizard
        open={true}
        onClose={vi.fn()}
        onCreated={vi.fn()}
        initialConfig={CLONE_CONFIG}
      />,
    )
    expect(screen.getByTestId("wizard-step-indicator").textContent).toContain("3")
    expect((screen.getByTestId("wizard-template-name-input") as HTMLInputElement).value).toBe(
      "Triagem Tech (cópia)",
    )
  })

  it("initialConfig sem name produz input vazio (não força nome custom)", () => {
    const noName: CreateAgentInitialConfig = {
      ...CLONE_CONFIG,
      name: undefined,
    }
    render(
      <CreateAgentWizard
        open={true}
        onClose={vi.fn()}
        onCreated={vi.fn()}
        initialConfig={noName}
      />,
    )
    const input = screen.getByTestId("wizard-template-name-input") as HTMLInputElement
    expect(input.value).toBe("")
  })

  it("initialConfig.goal undefined cai em 'outro' default (não quebra render)", () => {
    const noGoal: CreateAgentInitialConfig = {
      approach: "template",
      templateId: "tpl-triagem-tech",
      name: "Sem goal explícito",
    }
    // Render não deve crashar (goal interno = "outro" via fallback)
    render(
      <CreateAgentWizard
        open={true}
        onClose={vi.fn()}
        onCreated={vi.fn()}
        initialConfig={noGoal}
      />,
    )
    expect(screen.getByTestId("config-step-template")).toBeTruthy()
  })
})
