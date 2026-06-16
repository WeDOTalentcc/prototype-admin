/**
 * Sprint visual 2026-05-26 — QuotaMeter colapsado por default.
 *
 * Antes ocupava ~15% do header (viola 90/10 Rule canonical). Agora wrap
 * <Collapsible defaultOpen={false}>. Header compacto + chevron pra expandir.
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import ptBR from "../../../../messages/pt-BR.json"
import { QuotaMeter } from "../QuotaMeter"

// Mock useStudioQuota com dados realistas (4 resources, 1 yellow)
vi.mock("@/hooks/agent-studio/use-studio-quota", () => ({
  useStudioQuota: () => ({
    data: { plan_code: "Starter" },
    resources: [
      { resource: "custom_agents", active: 5, limit: 10, percent: 50, tier: "green", isUnlimited: false },
      { resource: "sourcing_agents", active: 9, limit: 10, percent: 90, tier: "yellow", isUnlimited: false },
      { resource: "digital_twins", active: 2, limit: 10, percent: 20, tier: "green", isUnlimited: false },
      { resource: "campaigns", active: 3, limit: 5, percent: 60, tier: "green", isUnlimited: false },
    ],
    isLoading: false,
    error: null,
  }),
}))

// Mock UpgradeRequestModal (irrelevante pra esse teste)
vi.mock("../UpgradeRequestModal", () => ({
  UpgradeRequestModal: () => null,
}))

const renderWithIntl = (ui: React.ReactElement) =>
  render(
    <NextIntlClientProvider locale="pt" messages={ptBR}>
      {ui}
    </NextIntlClientProvider>,
  )

describe("QuotaMeter — Sprint visual collapsible", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("renderiza header trigger colapsado por default (4 cards NÃO visíveis)", () => {
    renderWithIntl(<QuotaMeter />)
    const trigger = screen.getByTestId("quota-meter-trigger")
    expect(trigger).toBeTruthy()
    // Cards NÃO devem aparecer no DOM-visible (Radix CollapsibleContent hidden quando state=closed)
    // Radix renderiza com data-state="closed" — testid pode estar no DOM mas com hidden
    const content = screen.queryByTestId("quota-meter")
    if (content) {
      expect(content.getAttribute("data-state")).toBe("closed")
    }
  })

  it("expande quando trigger clicado: 4 cards de resource visíveis", () => {
    renderWithIntl(<QuotaMeter />)
    const trigger = screen.getByTestId("quota-meter-trigger")
    fireEvent.click(trigger)
    // Pos-expand: data-state="open"
    const content = screen.getByTestId("quota-meter")
    expect(content.getAttribute("data-state")).toBe("open")
    // 4 resource cards visíveis
    expect(screen.getByTestId("quota-meter-custom_agents")).toBeTruthy()
    expect(screen.getByTestId("quota-meter-sourcing_agents")).toBeTruthy()
    expect(screen.getByTestId("quota-meter-digital_twins")).toBeTruthy()
    expect(screen.getByTestId("quota-meter-campaigns")).toBeTruthy()
  })

  it("header colapsado mostra summary com maior percent (90% nesse mock)", () => {
    renderWithIntl(<QuotaMeter />)
    const trigger = screen.getByTestId("quota-meter-trigger")
    expect(trigger.textContent).toContain("90")
  })
})
