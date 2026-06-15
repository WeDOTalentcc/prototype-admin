/**
 * Sentinela visual — Task #1044
 *
 * Garante que as abas Gêmeos Digitais e Busca Inteligente do Agent Studio
 * mantenham o mesmo padrão visual do trio (Captação / Personalizados /
 * Marketplace) e não voltem ao layout "hero" antigo.
 */
import { describe, expect, it, vi } from "vitest"
import { act, render, waitFor } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, vars?: Record<string, unknown>) => {
    if (vars && "number" in vars) return `${key} ${vars.number}`
    return key
  },
}))

import {
  TwinsList,
} from "../DigitalTwinComponents"
import SourcingTab from "@/components/pages-talent-pools/sub-tabs/sourcing-tab"

// Sprint 4 v3 (2026-05-25): SourcingTab requires poolId. Mock useIdealProfile to avoid SWR fetch.
import { vi as _viCanonical } from "vitest"
_viCanonical.mock("@/hooks/talent-pools/use-ideal-profile", () => ({
  useIdealProfile: () => ({ data: null, isLoading: false, error: null }),
}))

describe("Agent Studio — harmonização visual (Task #1044)", () => {
  it("DigitalTwinOnboarding REMOVIDO (P0 rewrite 2026-05-26): export não existe", async () => {
    // Antes da rewrite, página Gêmeos Digitais renderizava 4 cards "Passo 1-4"
    // + banner com citação concorrente (Eightfold Andromeda). Paulo locked 2026-05-26:
    // página agora segue layout canonical Marketplace/Personalizados — sem onboarding
    // inline, sem citação concorrente. Validar via import dinâmico que symbol não existe.
    const mod = await import("../DigitalTwinComponents")
    expect((mod as Record<string, unknown>).DigitalTwinOnboarding).toBeUndefined()
    expect((mod as Record<string, unknown>).TwinCompetitiveBanner).toBeUndefined()
  })

  it("SourcingTab: inputs usam rounded-md e focus ring tokenizado", () => {
    const { container } = render(<SourcingTab poolId="pool-test" />)
    const inputs = container.querySelectorAll("input[type='text']")
    expect(inputs.length).toBe(3)
    inputs.forEach((input) => {
      const cls = input.className
      expect(cls).toContain("rounded-md")
      expect(cls).not.toContain("rounded-xl")
      expect(cls).toContain("border-lia-border-subtle")
      expect(cls).toContain("focus:ring-2")
      expect(cls).toContain("focus:ring-lia-btn-primary-bg/20")
      expect(cls).not.toContain("focus:ring-gray-400")
    })
  })

  it("SourcingTab: container externo usa space-y-6 (alinhado ao trio)", () => {
    const { container } = render(<SourcingTab poolId="pool-test" />)
    const root = container.firstElementChild
    expect(root?.className).toContain("space-y-6")
  })

  it("TwinsList: NÃO renderiza onboarding quando twins.length > 0", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        twins: [
          {
            id: "tw-1",
            twin_name: "Ana Recrutadora",
            specialties: ["Backend"],
            decision_count: 12,
            accuracy_pct: 87,
            is_active: true,
          },
        ],
      }),
    })
    vi.stubGlobal("fetch", fetchMock)
    let result: ReturnType<typeof render> | null = null
    await act(async () => {
      result = render(<TwinsList onCreateTwin={() => {}} />)
    })
    const { container } = result!
    await waitFor(() => {
      expect(container.querySelector("section")).toBeNull()
    })
    // Card do twin renderizado (não está no estado vazio)
    expect(container.textContent).toContain("Ana Recrutadora")
    vi.unstubAllGlobals()
  })

  it("TwinsList: empty state canonical (sem onboarding 4-steps, sem banner concorrente)", async () => {
    // P0 rewrite 2026-05-26: empty state agora é simples (icon + título + CTA),
    // sem "Passo 1-4" e sem TwinCompetitiveBanner (Eightfold Andromeda).
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ twins: [] }),
    })
    vi.stubGlobal("fetch", fetchMock)
    let result: ReturnType<typeof render> | null = null
    await act(async () => {
      result = render(<TwinsList onCreateTwin={() => {}} />)
    })
    const { container } = result!
    await waitFor(() => {
      // Loading concluído (estado vazio renderizado).
      expect(container.textContent).not.toContain("loadingTwins")
    })
    // Header duplicado removido: TwinsList NÃO renderiza header próprio
    // (headerTitle/subheader) — o header é do pai (AgentStudioPage via TabSectionHeader).
    expect(container.textContent).not.toMatch(/subheader|headerTitle/i)
    // NÃO renderiza 4-step onboarding section nem banner concorrente.
    // (Conteúdo do banner removido: "Eightfold" / "DIFERENCIAL" / 4 step blocks.)
    expect(container.textContent).not.toMatch(/Eightfold/i)
    expect(container.textContent).not.toMatch(/DIFERENCIAL/i)
    // step1Title/step2Title/... (keys do onboarding antigo) também sumiram
    expect(container.textContent).not.toMatch(/step1Title|step2Title|step3Title|step4Title/i)
    vi.unstubAllGlobals()
  })
})
