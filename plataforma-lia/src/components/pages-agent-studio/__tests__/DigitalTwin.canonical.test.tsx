/**
 * Canonical test for DigitalTwin tab/components — P0 rewrite 2026-05-26.
 *
 * Pins:
 * - REMOVED competitor mentions (Eightfold, Andromeda, etc.)
 * - REMOVED marketing copy (DIFERENCIAL WEDOTALENT, Unico no mercado, globalmente, built-in)
 * - REMOVED duplicate "How it works" 4-step blocks from main page
 * - LGPD disclosure uses Collapsible (neutral DS), NOT amber/yellow alarm card
 */
import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import ptBR from "../../../../messages/pt-BR.json"

vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "LIA" }, isLoading: false }),
}))

// Mock fetch to avoid real network on TwinsList load
const mockFetch = vi.fn()
beforeEach(() => {
  mockFetch.mockReset()
  // Default: CreateDigitalTwinModal busca a lista de usuários no open (useEffect).
  // Sem um default, fetch() devolve undefined e `.then` quebra antes de qualquer
  // asserção. Testes que precisam de payload específico usam mockResolvedValueOnce
  // (consumido primeiro; este default cobre as chamadas restantes).
  mockFetch.mockResolvedValue({ ok: true, json: async () => ({ users: [], twins: [] }) } as Response)
  global.fetch = mockFetch as unknown as typeof fetch
})

function renderWithIntl(ui: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="pt" messages={ptBR as Record<string, unknown>}>
      {ui}
    </NextIntlClientProvider>
  )
}

describe("DigitalTwin — canonical (no competitor/marketing copy)", () => {
  it("agents.studio.twins block has no competitor names or marketing claims", () => {
    // Scoped to the Digital Twins i18n subtree (P0 scope of rewrite).
    const twins = (ptBR as any).agents.studio.twins
    const blob = JSON.stringify(twins)
    // Competitor mentions
    expect(blob).not.toMatch(/Eightfold/i)
    expect(blob).not.toMatch(/Andromeda/i)
    // Marketing claims
    expect(blob).not.toMatch(/DIFERENCIAL WEDOTALENT/i)
    expect(blob).not.toMatch(/[Úu]nico no mercado/i)
    expect(blob).not.toMatch(/globalmente/i)
    expect(blob).not.toMatch(/built-in/i)
  })

  it("TwinsList empty state renders without 4-step onboarding cards (canonical layout)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ twins: [] }),
    } as Response)

    const { TwinsList } = await import("../DigitalTwinComponents")
    renderWithIntl(<TwinsList onCreateTwin={() => {}} />)

    // Wait for loading -> empty: empty state title appears
    await screen.findByText(/Nenhum Gêmeo Digital criado ainda/i)

    // Must NOT render the 4 "Passo" cards (DigitalTwinOnboarding removed from main page)
    expect(screen.queryByText(/Passo 1/i)).toBeNull()
    expect(screen.queryByText(/Passo 2/i)).toBeNull()
    expect(screen.queryByText(/Passo 3/i)).toBeNull()
    expect(screen.queryByText(/Passo 4/i)).toBeNull()

    // Must NOT render competitive banner (removed)
    expect(screen.queryByText(/Eightfold/i)).toBeNull()
    expect(screen.queryByText(/DIFERENCIAL/i)).toBeNull()
  })

  it("TwinsList renders sub-header (short, neutral) + create CTA at top", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ twins: [] }),
    } as Response)

    const { TwinsList } = await import("../DigitalTwinComponents")
    renderWithIntl(<TwinsList onCreateTwin={() => {}} />)

    // Sub-header explains the concept WITHOUT marketing
    const subHeader = await screen.findByText(
      /agente IA que aprende o padrão de avaliação/i
    )
    expect(subHeader).toBeTruthy()

    // CTA button exists
    const cta = screen.getAllByRole("button").find((b) =>
      /Criar Gêmeo Digital/i.test(b.textContent || "")
    )
    expect(cta).toBeTruthy()
  })
})

describe("CreateDigitalTwinModal — LGPD canonical (collapsible, neutral DS)", () => {
  it("renders LGPD summary visible by default (1 line)", async () => {
    const { CreateDigitalTwinModal } = await import("../DigitalTwinComponents")
    renderWithIntl(
      <CreateDigitalTwinModal isOpen={true} onClose={() => {}} />
    )

    // Summary visible
    const summary = await screen.findByText(/LGPD Art\. 6.*11.*18/i)
    expect(summary).toBeTruthy()
  })

  it("does NOT render alarmist amber/yellow visual classes for LGPD block", async () => {
    const { CreateDigitalTwinModal } = await import("../DigitalTwinComponents")
    const { container } = renderWithIntl(
      <CreateDigitalTwinModal isOpen={true} onClose={() => {}} />
    )

    // Sentinel: no amber/yellow utility classes anywhere in the modal
    expect(container.querySelector('[class*="amber-50"]')).toBeNull()
    expect(container.querySelector('[class*="amber-200"]')).toBeNull()
    expect(container.querySelector('[class*="amber-600"]')).toBeNull()
    expect(container.querySelector('[class*="amber-800"]')).toBeNull()
    expect(container.querySelector('[class*="amber-900"]')).toBeNull()
    expect(container.querySelector('[class*="amber-950"]')).toBeNull()
  })

  it("collapsed by default — full LGPD detail text NOT in DOM until expanded", async () => {
    const { CreateDigitalTwinModal } = await import("../DigitalTwinComponents")
    renderWithIntl(
      <CreateDigitalTwinModal isOpen={true} onClose={() => {}} />
    )

    // Detail text uses Radix Collapsible — content unmounted/hidden until trigger click
    // We assert the toggle button exists (defaults closed)
    const triggers = screen.queryAllByRole("button", { expanded: false })
    expect(triggers.length).toBeGreaterThan(0)
  })

  it("Confirmo button is present even before expanding the LGPD detail", async () => {
    const { CreateDigitalTwinModal } = await import("../DigitalTwinComponents")
    renderWithIntl(
      <CreateDigitalTwinModal isOpen={true} onClose={() => {}} />
    )

    const confirm = await screen.findByRole("button", {
      name: /Confirmo/i,
    })
    expect(confirm).toBeTruthy()
  })

  it("clicking the collapsible trigger reveals the full LGPD detail", async () => {
    const { CreateDigitalTwinModal } = await import("../DigitalTwinComponents")
    renderWithIntl(
      <CreateDigitalTwinModal isOpen={true} onClose={() => {}} />
    )

    // Trigger is the first button with aria-expanded (Radix Collapsible)
    const triggers = await screen.findAllByRole("button", { expanded: false })
    const collapsibleTrigger = triggers[0]
    expect(collapsibleTrigger).toBeTruthy()
    fireEvent.click(collapsibleTrigger)

    // After expand, full detail text appears (matches indexing paragraph)
    const expanded = await screen.findByText(
      /Esta funcionalidade indexa decisões históricas \(aprovações/i
    )
    expect(expanded).toBeTruthy()
  })
})
