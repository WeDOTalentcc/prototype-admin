// Onda 2 F12 (2026-05-27) — JobAgentDot canonical tests.
//
// Cobertura:
//   1. Renderiza pingo quando há deployments ativos.
//   2. Oculto quando deployments vazio.
//   3. Oculto quando targetId null (sem fetch).
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import { JobAgentDot } from "../JobAgentDot"
import type { DeploymentListResponse } from "@/types/agents/agent-deployment"
import ptBRMessages from "../../../../../messages/pt-BR.json"

beforeEach(() => {
  Object.defineProperty(window, "localStorage", {
    value: {
      getItem: vi.fn(() => "token-fake"),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    },
    configurable: true,
  })
})

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={ptBRMessages}>
      <QueryClientProvider client={client}>{ui}</QueryClientProvider>
    </NextIntlClientProvider>,
  )
}

function mockFetchOnce(body: DeploymentListResponse) {
  global.fetch = vi.fn().mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  }) as unknown as typeof fetch
}

describe("JobAgentDot", () => {
  it("renderiza pingo quando há deployments ativos", async () => {
    mockFetchOnce({
      total: 2,
      deployments: [
        {
          id: "d1",
          agent_id: "a1",
          target_type: "job",
          target_id: "job-1",
          target_name: null,
          is_active: true,
          created_at: null,
          updated_at: null,
        },
        {
          id: "d2",
          agent_id: "a2",
          target_type: "job",
          target_id: "job-1",
          target_name: null,
          is_active: true,
          created_at: null,
          updated_at: null,
        },
      ],
    })
    const { container } = renderWithQuery(
      <JobAgentDot targetId="job-1" />,
    )
    await waitFor(() => {
      const dot = container.querySelector("span[role='img']")
      expect(dot).not.toBeNull()
      expect(dot?.getAttribute("title")).toMatch(/2 agentes acoplados/)
    })
  })

  it("oculto quando deployments vazio", async () => {
    mockFetchOnce({ total: 0, deployments: [] })
    const { container } = renderWithQuery(
      <JobAgentDot targetId="job-1" />,
    )
    await waitFor(() => {
      expect(container.querySelector("span[role='img']")).toBeNull()
    })
  })

  it("oculto quando targetId null (sem fetch)", () => {
    const fetchMock = vi.fn()
    global.fetch = fetchMock as unknown as typeof fetch
    const { container } = renderWithQuery(<JobAgentDot targetId={null} />)
    expect(container.querySelector("span[role='img']")).toBeNull()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it("i18n canonical contract — singular sem MISSING_MESSAGE (pt-BR real)", async () => {
    const errors: Error[] = []
    mockFetchOnce({
      total: 1,
      deployments: [
        {
          id: "d1",
          agent_id: "a1",
          target_type: "job",
          target_id: "job-9",
          target_name: null,
          is_active: true,
          created_at: null,
          updated_at: null,
        },
      ],
    })
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: 0 } },
    })
    const { container } = render(
      <NextIntlClientProvider
        locale="pt-BR"
        messages={ptBRMessages}
        onError={(err) => errors.push(err)}
      >
        <QueryClientProvider client={client}>
          <JobAgentDot targetId="job-9" />
        </QueryClientProvider>
      </NextIntlClientProvider>,
    )
    await waitFor(() => {
      const dot = container.querySelector("span[role='img']")
      expect(dot?.getAttribute("title")).toMatch(/1 agente acoplado/)
    })
    expect(
      errors.filter((e) => e.message.includes("MISSING_MESSAGE")),
    ).toEqual([])
  })
})
