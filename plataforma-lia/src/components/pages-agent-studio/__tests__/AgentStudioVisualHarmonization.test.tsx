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
  DigitalTwinHeader,
  DigitalTwinOnboarding,
  TwinsList,
} from "../DigitalTwinComponents"
import SourcingTab from "@/components/pages-talent-pools/sub-tabs/sourcing-tab"

// Sprint 4 v3 (2026-05-25): SourcingTab requires poolId. Mock useIdealProfile to avoid SWR fetch.
import { vi as _viCanonical } from "vitest"
_viCanonical.mock("@/hooks/talent-pools/use-ideal-profile", () => ({
  useIdealProfile: () => ({ data: null, isLoading: false, error: null }),
}))

describe("Agent Studio — harmonização visual (Task #1044)", () => {
  it("DigitalTwinHeader renderiza header curto (h2 text-sm) sem hero/gradient", () => {
    const { container } = render(<DigitalTwinHeader />)
    const h2 = container.querySelector("h2")
    expect(h2).not.toBeNull()
    expect(h2?.className).toContain("text-sm")
    expect(h2?.className).toContain("font-semibold")
    // Não deve trazer eyebrow/gradient/blob do hero antigo
    expect(container.querySelector(".bg-gradient-to-br")).toBeNull()
    expect(container.querySelector("section")).toBeNull()
  })

  it("DigitalTwinOnboarding ainda existe (renderizado quando twins.length === 0)", () => {
    const { container } = render(<DigitalTwinOnboarding />)
    expect(container.querySelector("section")).not.toBeNull()
    // Mantém o grid de 4 passos do onboarding
    const steps = container.querySelectorAll(".grid > div")
    expect(steps.length).toBe(4)
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

  it("TwinsList: renderiza onboarding quando twins.length === 0", async () => {
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
      expect(container.querySelector("section")).not.toBeNull()
    })
    const steps = container.querySelectorAll("section .grid > div")
    expect(steps.length).toBe(4)
    vi.unstubAllGlobals()
  })
})
