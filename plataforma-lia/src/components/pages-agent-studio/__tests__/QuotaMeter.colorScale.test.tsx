/**
 * QuotaMeter — escala de cor canonical + fix 0/0 (2026-05-30).
 *
 * Regressão da saga "cards vermelhos 0/0 100%": vermelho era disparado pra
 * estado saudável (sem limite configurado). Esses sensores pinam:
 *   1. computeStatus: tier por uso real (green <75, yellow 75-94, red 95+).
 *   2. limit 0/null/undefined → noLimit (NÃO 100% vermelho).
 *   3. QuotaMeter: noLimit renderiza texto neutro, sem barra, sem warning.
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import ptBR from "../../../../messages/pt-BR.json"
import { computeStatus } from "@/hooks/agent-studio/use-studio-quota"

describe("computeStatus — escala de cor canonical por uso real", () => {
  it("green em 0-74% usado (estado calmo, sem vermelho)", () => {
    expect(computeStatus(0, 10, "custom_agents").tier).toBe("green")
    expect(computeStatus(7, 10, "custom_agents").tier).toBe("green") // 70%
    expect(computeStatus(74, 100, "custom_agents").tier).toBe("green")
  })

  it("yellow em 75-94% usado (atenção âmbar)", () => {
    expect(computeStatus(75, 100, "custom_agents").tier).toBe("yellow")
    expect(computeStatus(9, 10, "custom_agents").tier).toBe("yellow") // 90%
    expect(computeStatus(94, 100, "custom_agents").tier).toBe("yellow")
  })

  it("red SÓ em 95%+ usado (crítico real)", () => {
    expect(computeStatus(95, 100, "custom_agents").tier).toBe("red")
    expect(computeStatus(10, 10, "custom_agents").tier).toBe("red") // 100%
  })

  it("limit -1 (enterprise unlimited) → green, percent null, isUnlimited", () => {
    const r = computeStatus(50, -1, "campaigns")
    expect(r.tier).toBe("green")
    expect(r.percent).toBeNull()
    expect(r.isUnlimited).toBe(true)
    expect(r.noLimit).toBe(false)
  })

  it("FIX 0/0: limit 0 → green + noLimit + percent null (NÃO 100% vermelho)", () => {
    const r = computeStatus(0, 0, "digital_twins")
    expect(r.tier).toBe("green")
    expect(r.noLimit).toBe(true)
    expect(r.percent).toBeNull()
    expect(r.isUnlimited).toBe(false)
  })

  it("FIX null/undefined limit → noLimit neutro (nunca NaN nem 100% red)", () => {
    const a = computeStatus(0, null, "campaigns")
    const b = computeStatus(undefined, undefined, "sourcing_agents")
    for (const r of [a, b]) {
      expect(r.tier).toBe("green")
      expect(r.noLimit).toBe(true)
      expect(r.percent).toBeNull()
    }
  })
})

vi.mock("../UpgradeRequestModal", () => ({ UpgradeRequestModal: () => null }))

const renderWithIntl = (ui: React.ReactElement) =>
  render(
    <NextIntlClientProvider locale="pt" messages={ptBR}>
      {ui}
    </NextIntlClientProvider>,
  )

function mockResources(
  resources: Array<Partial<import("@/hooks/agent-studio/use-studio-quota").QuotaResourceStatus> & { resource: string }>,
) {
  vi.doMock("@/hooks/agent-studio/use-studio-quota", () => ({
    useStudioQuota: () => ({
      data: { plan_code: "Starter" },
      resources,
      isLoading: false,
      error: null,
    }),
  }))
}

describe("QuotaMeter — render noLimit (0/0) estado neutro", () => {
  it("4 recursos sem limite: SEM warning, header mostra 'Sem limite definido'", async () => {
    vi.resetModules()
    mockResources([
      { resource: "custom_agents", active: 0, limit: 0, percent: null, tier: "green", isUnlimited: false, noLimit: true },
      { resource: "sourcing_agents", active: 0, limit: 0, percent: null, tier: "green", isUnlimited: false, noLimit: true },
      { resource: "digital_twins", active: 0, limit: 0, percent: null, tier: "green", isUnlimited: false, noLimit: true },
      { resource: "campaigns", active: 0, limit: 0, percent: null, tier: "green", isUnlimited: false, noLimit: true },
    ])
    const { QuotaMeter } = await import("../QuotaMeter")
    renderWithIntl(<QuotaMeter />)
    const trigger = screen.getByTestId("quota-meter-trigger")
    // Header neutro, NÃO "0% usado", NÃO vermelho
    expect(trigger.textContent).toContain("Sem limite definido")
    // Sem aviso de "próximo do limite"
    fireEvent.click(trigger)
    expect(screen.queryByTestId("quota-meter-contact-am")).toBeNull()
    // Card mostra texto neutro, sem barra de progresso (sem %)
    const card = screen.getByTestId("quota-meter-custom_agents")
    expect(card.getAttribute("data-tier")).toBe("green")
    expect(card.textContent).not.toContain("100%")
    expect(card.textContent).toContain("Sem limite definido")
  })

  it("recurso real ≥75% dispara warning; noLimit no mesmo set NÃO interfere", async () => {
    vi.resetModules()
    mockResources([
      { resource: "custom_agents", active: 9, limit: 10, percent: 90, tier: "yellow", isUnlimited: false, noLimit: false },
      { resource: "sourcing_agents", active: 0, limit: 0, percent: null, tier: "green", isUnlimited: false, noLimit: true },
      { resource: "digital_twins", active: 0, limit: 0, percent: null, tier: "green", isUnlimited: false, noLimit: true },
      { resource: "campaigns", active: 0, limit: 0, percent: null, tier: "green", isUnlimited: false, noLimit: true },
    ])
    const { QuotaMeter } = await import("../QuotaMeter")
    renderWithIntl(<QuotaMeter />)
    const trigger = screen.getByTestId("quota-meter-trigger")
    // Header mostra 90% (maior percent de recurso COM limite)
    expect(trigger.textContent).toContain("90")
    fireEvent.click(trigger)
    // Warning aparece (recurso real em 90%)
    expect(screen.getByTestId("quota-meter-contact-am")).toBeTruthy()
  })
})
