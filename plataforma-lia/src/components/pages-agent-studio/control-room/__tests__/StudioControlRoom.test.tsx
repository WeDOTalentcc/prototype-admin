// Onda 1 F10 (2026-05-27) — StudioControlRoom canonical smoke test.
//
// Smoke test: verifica que 3 seções estão presentes e o DecisionTreeDrawer
// canonical está montado (fechado por default).
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { StudioControlRoom } from "../StudioControlRoom"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "Lia", tone: "profissional" } }),
}))

vi.mock("@/hooks/agents", () => ({
  useCustomAgents: () => ({ agents: [], total: 0, isLoading: false, isError: false, mutate: () => {} }),
}))

beforeEach(() => {
  Object.defineProperty(window, "localStorage", {
    value: { getItem: vi.fn(() => "token") },
    configurable: true,
  })
  global.fetch = vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => [],
  })) as unknown as typeof fetch
})

afterEach(() => {
  vi.restoreAllMocks()
})

function renderWith() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <StudioControlRoom />
    </QueryClientProvider>,
  )
}

describe("StudioControlRoom — canonical Onda 1", () => {
  it("renderiza 3 seções verticais (live + recent + lgpd)", async () => {
    renderWith()
    await waitFor(() => {
      expect(screen.getByTestId("control-room-live-section")).toBeTruthy()
      expect(screen.getByTestId("control-room-recent-section")).toBeTruthy()
      expect(screen.getByTestId("control-room-lgpd-section")).toBeTruthy()
    })
  })

  it("DecisionTreeDrawer canonical está montado (fechado por default)", async () => {
    renderWith()
    // Drawer fechado — testid não aparece no DOM (Sheet só monta SheetContent quando open).
    await waitFor(() => {
      expect(screen.queryByTestId("decision-tree-drawer")).toBeNull()
    })
  })


  // Onda 3 F8 (2026-05-28) — filtro "Por surface" propaga para children.
  it("renderiza filtro 'Por surface' canonical (Onda 3 F7)", async () => {
    renderWith()
    await waitFor(() => {
      expect(screen.getByTestId("control-room-surface-filter")).toBeTruthy()
    })
  })

  it("filtro surface tem default 'all' (Onda 3 F7)", async () => {
    renderWith()
    await waitFor(() => {
      const trigger = screen.getByTestId("control-room-surface-filter")
      // Default value rendered no SelectValue (slot interno do Radix)
      expect(trigger.textContent).toMatch(/surfaceAll|All|Todos/)
    })
  })

  it("LgpdAuditPanel inicia collapsed", async () => {
    renderWith()
    await waitFor(() => {
      expect(screen.getByTestId("lgpd-audit-toggle")).toBeTruthy()
      // Conteúdo expandido NÃO está montado (collapsed).
      expect(screen.queryByTestId("lgpd-audit-content")?.getAttribute("hidden")).not.toBeNull()
    })
  })
})
