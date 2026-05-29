// Onda C4.2 (2026-05-29) — MorningDigest canonical tests.
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { MorningDigest } from "../MorningDigest"
import type { DailyDigestResponse, DigestItem } from "@/types/agents/daily-digest"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, vars?: Record<string, unknown>) => {
    if (key.startsWith("greeting.")) return `g:${key.split(".")[1]}`
    if (key === "footer" && vars) return `footer:${vars.runs}/${vars.candidates}/${vars.hours}`
    return key
  },
}))

vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "Lia", tone: "profissional" } }),
}))

beforeEach(() => {
  Object.defineProperty(window, "localStorage", {
    value: { getItem: vi.fn(() => "token") },
    configurable: true,
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

function renderWith(ui: React.ReactNode) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

function mockFetch(resp: DailyDigestResponse) {
  global.fetch = vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => resp,
  })) as unknown as typeof fetch
}

const baseResp = (items: DigestItem[], extra: Partial<DailyDigestResponse> = {}): DailyDigestResponse => ({
  period_hours: 24,
  generated_at: "2026-05-29T08:00:00Z",
  items,
  total_runs: 127,
  total_candidates_processed: 48,
  ...extra,
})

describe("MorningDigest — canonical Onda C4.2", () => {
  it("renderiza empty state quando items=[]", async () => {
    mockFetch(baseResp([]))
    renderWith(<MorningDigest onOpenReasoning={() => {}} />)
    await waitFor(() => {
      expect(screen.getByTestId("morning-digest-empty")).toBeTruthy()
    })
    // saudação contextual presente
    expect(screen.getByRole("heading", { level: 3 }).textContent).toMatch(/^g:/)
  })

  it("renderiza items com summary + footer agregado", async () => {
    const items: DigestItem[] = [
      {
        kind: "decision_approved",
        agent_id: "a1",
        agent_name: "Catarina",
        summary: "Catarina aprovou 4 candidato(s) · Dev Sênior",
        target_type: "job",
        target_name: "Dev Sênior",
        count: 4,
        severity: "celebration",
        execution_id: "exec-1",
        timestamp: "2026-05-29T07:00:00Z",
      },
      {
        kind: "pending_approval",
        agent_id: "a2",
        agent_name: "Sofia",
        summary: "3 aprovação(ões) aguardando você",
        target_type: "custom_agent",
        target_name: "Sofia",
        count: 3,
        severity: "attention",
        execution_id: null,
        timestamp: "2026-05-29T06:00:00Z",
      },
    ]
    mockFetch(baseResp(items))
    renderWith(<MorningDigest onOpenReasoning={() => {}} />)
    await waitFor(() => {
      expect(screen.getByText(/Catarina aprovou 4/)).toBeTruthy()
      expect(screen.getByText(/3 aprovação/)).toBeTruthy()
      expect(screen.getByText("footer:127/48/24")).toBeTruthy()
    })
    // aria-live na lista (a11y canonical)
    const list = screen.getByTestId("morning-digest-list")
    expect(list.getAttribute("aria-live")).toBe("polite")
  })

  it("clique em item com execution_id abre o drawer (onOpenReasoning)", async () => {
    const onOpen = vi.fn()
    const items: DigestItem[] = [
      {
        kind: "agent_error",
        agent_id: "a1",
        agent_name: "Pedro",
        summary: "Pedro teve uma falha de execução",
        target_type: "job",
        target_name: null,
        count: null,
        severity: "attention",
        execution_id: "exec-99",
        timestamp: "2026-05-29T07:00:00Z",
      },
    ]
    mockFetch(baseResp(items))
    renderWith(<MorningDigest onOpenReasoning={onOpen} />)
    await waitFor(() => {
      expect(screen.getByTestId("digest-item-agent_error")).toBeTruthy()
    })
    fireEvent.click(screen.getByTestId("digest-item-agent_error"))
    expect(onOpen).toHaveBeenCalledWith("exec-99")
  })

  it("item sem execution_id (pending) NÃO é clicável (sem botão)", async () => {
    const onOpen = vi.fn()
    const items: DigestItem[] = [
      {
        kind: "pending_approval",
        agent_id: "a2",
        agent_name: "Sofia",
        summary: "2 aprovação(ões) aguardando você",
        target_type: "custom_agent",
        target_name: "Sofia",
        count: 2,
        severity: "attention",
        execution_id: null,
        timestamp: "2026-05-29T06:00:00Z",
      },
    ]
    mockFetch(baseResp(items))
    renderWith(<MorningDigest onOpenReasoning={onOpen} />)
    await waitFor(() => {
      expect(screen.getByTestId("digest-item-pending_approval")).toBeTruthy()
    })
    const el = screen.getByTestId("digest-item-pending_approval")
    expect(el.tagName.toLowerCase()).toBe("li")
    expect(el.querySelector("button")).toBeNull()
  })

  it("saudação contextual renderiza no heading", async () => {
    mockFetch(baseResp([]))
    renderWith(<MorningDigest onOpenReasoning={() => {}} />)
    await waitFor(() => {
      const heading = screen.getByRole("heading", { level: 3 })
      expect(heading.textContent).toMatch(/^g:(morning|afternoon|evening)$/)
    })
  })
})
