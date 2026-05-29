// P1-5 (2026-05-29) — JobAgentBadge canonical tests.
//
// Cobertura:
//   1. Renderiza badge com plural correto quando há deployments ativos.
//   2. Singular para 1 agente.
//   3. Oculto quando nenhum deployment ativo.
//   4. Oculto quando jobId undefined.
//   5. i18n canonical contract — sem MISSING_MESSAGE (pt-BR real).
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import { JobAgentBadge } from "../JobAgentBadge"
import type { DeploymentListResponse } from "@/types/agents/agent-deployment"
import ptBRMessages from "../../../../messages/pt-BR.json"

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

function renderWithIntl(
  ui: React.ReactElement,
  onError?: (err: Error) => void,
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <NextIntlClientProvider
      locale="pt-BR"
      messages={ptBRMessages}
      onError={onError}
    >
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

function deployment(id: string, active = true): DeploymentListResponse["deployments"][number] {
  return {
    id,
    agent_id: `agent-${id}`,
    target_type: "job",
    target_id: "job-1",
    target_name: null,
    is_active: active,
    created_at: null,
    updated_at: null,
  }
}

describe("JobAgentBadge", () => {
  it("renderiza plural quando há 2+ agentes ativos", async () => {
    mockFetchOnce({ total: 2, deployments: [deployment("d1"), deployment("d2")] })
    renderWithIntl(<JobAgentBadge jobId="job-1" />)
    await waitFor(() => {
      expect(screen.getByText(/2 agentes ativos/)).toBeInTheDocument()
    })
  })

  it("usa singular para 1 agente ativo", async () => {
    mockFetchOnce({ total: 1, deployments: [deployment("d1")] })
    renderWithIntl(<JobAgentBadge jobId="job-1" />)
    await waitFor(() => {
      expect(screen.getByText(/1 agente ativo/)).toBeInTheDocument()
    })
  })

  it("oculto quando nenhum deployment ativo", async () => {
    mockFetchOnce({ total: 1, deployments: [deployment("d1", false)] })
    const { container } = renderWithIntl(<JobAgentBadge jobId="job-1" />)
    await waitFor(() => {
      expect(container.querySelector("a")).toBeNull()
    })
  })

  it("oculto quando jobId undefined", () => {
    const fetchMock = vi.fn()
    global.fetch = fetchMock as unknown as typeof fetch
    const { container } = renderWithIntl(<JobAgentBadge jobId={undefined} />)
    expect(container.querySelector("a")).toBeNull()
  })

  it("i18n canonical contract — sem MISSING_MESSAGE (pt-BR real)", async () => {
    const errors: Error[] = []
    mockFetchOnce({ total: 3, deployments: [deployment("d1"), deployment("d2"), deployment("d3")] })
    renderWithIntl(<JobAgentBadge jobId="job-1" />, (err) => errors.push(err))
    await waitFor(() => {
      expect(screen.getByText(/3 agentes ativos/)).toBeInTheDocument()
    })
    expect(
      errors.filter((e) => e.message.includes("MISSING_MESSAGE")),
    ).toEqual([])
  })
})
