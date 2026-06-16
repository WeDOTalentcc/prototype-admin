import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import type { ReactElement } from "react"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  QualificationMatrixCard,
  type QualificationMatrixData,
} from "../QualificationMatrixCard"

function renderWithClient(ui: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

const grouped: QualificationMatrixData = {
  mode: "grouped",
  criteria: [
    { id: "tech:python", label: "Python", group: "must_have", status: "met", explanation: "Skill presente.", provenance: "resume" },
    { id: "behav:lid", label: "Liderança", group: "must_have", status: "unknown", provenance: "none" },
    { id: "tech:go", label: "Go", group: "preferred", status: "not_met", explanation: "Não mencionada.", provenance: "resume" },
  ],
  met_count: 1,
  total_count: 3,
  must_have_met: 1,
  must_have_total: 2,
  overall_label: "Atende 1/3 qualificações",
}

const flat: QualificationMatrixData = {
  mode: "flat",
  criteria: [
    { id: "skill:python", label: "Python", group: "criteria", status: "met", provenance: "resume" },
    { id: "seniority:pleno", label: "Senioridade: Pleno", group: "criteria", status: "partial", provenance: "profile", is_inference: true },
  ],
  met_count: 1,
  total_count: 2,
  overall_label: "Atende 1/2 critérios",
}

describe("QualificationMatrixCard", () => {
  it("modo grouped: seções Obrigatórios/Desejáveis + header + proveniência", () => {
    renderWithClient(<QualificationMatrixCard candidateId="c1" companyId="co1" matrix={grouped} />)
    expect(screen.getByText("Atende 1/3 qualificações")).toBeInTheDocument()
    expect(screen.getByText("Obrigatórios")).toBeInTheDocument()
    expect(screen.getByText("Desejáveis")).toBeInTheDocument()
    expect(screen.getByText("Python")).toBeInTheDocument()
    expect(screen.getAllByText("com base no currículo").length).toBeGreaterThan(0)
  })

  it("modo flat: lista única 'Critérios da busca'", () => {
    renderWithClient(<QualificationMatrixCard candidateId="c1" companyId="co1" matrix={flat} />)
    expect(screen.getByText("Critérios da busca")).toBeInTheDocument()
    expect(screen.getByText("Atende 1/2 critérios")).toBeInTheDocument()
  })

  it("sem matrix e sem searchCriteria: não renderiza nada", () => {
    const { container } = renderWithClient(
      <QualificationMatrixCard candidateId="c1" companyId="co1" />
    )
    expect(container.firstChild).toBeNull()
  })

  it("matrix vazia: não renderiza", () => {
    const empty = { ...grouped, criteria: [] }
    const { container } = renderWithClient(
      <QualificationMatrixCard candidateId="c1" companyId="co1" matrix={empty} />
    )
    expect(container.firstChild).toBeNull()
  })
})


describe("QualificationMatrixCard — jobId on-the-fly (sem matrix salva)", () => {
  const groupedApiResponse: QualificationMatrixData = {
    mode: "grouped",
    criteria: [
      { id: "tech:python", label: "Python", group: "must_have", status: "met", explanation: "OK", provenance: "resume" },
    ],
    met_count: 1,
    total_count: 1,
    must_have_met: 1,
    must_have_total: 1,
    overall_label: "Atende 1/1 qualificações",
  }

  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 200,
        ok: true,
        json: async () => groupedApiResponse,
      })
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("jobId presente + sem matrix: dispara fetch POST com job_id no body", async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <QualificationMatrixCard candidateId="cand-1" companyId="co-1" jobId="job-abc" />
      </QueryClientProvider>
    )
    await screen.findByText("Atende 1/1 qualificações")
    const fetchMock = vi.mocked(globalThis.fetch)
    expect(fetchMock).toHaveBeenCalledOnce()
    const [, opts] = fetchMock.mock.calls[0]!
    expect(JSON.parse((opts as RequestInit).body as string)).toMatchObject({ job_id: "job-abc" })
    expect(JSON.parse((opts as RequestInit).body as string)).not.toHaveProperty("search_criteria")
  })

  it("jobId presente + sem matrix: nao dispara fetch quando matrix esta presente", async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <QualificationMatrixCard candidateId="cand-1" companyId="co-1" matrix={groupedApiResponse} jobId="job-abc" />
      </QueryClientProvider>
    )
    // matrix prop é exibida diretamente
    await screen.findByText("Atende 1/1 qualificações")
    expect(vi.mocked(globalThis.fetch)).not.toHaveBeenCalled()
  })
})

describe("QualificationMatrixCard — envelope unwrap (ResponseEnvelopeMiddleware)", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("resposta {ok,data,meta} do backend é desempacotada corretamente", async () => {
    const innerMatrix: QualificationMatrixData = {
      mode: "grouped",
      criteria: [
        { id: "behav:lideranca", label: "Liderança Técnica", group: "must_have", status: "met", explanation: "Evidenciado", provenance: "resume" },
      ],
      met_count: 1,
      total_count: 1,
      must_have_met: 1,
      must_have_total: 1,
      overall_label: "Atende 1/1 qualificações",
    }
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 200,
        ok: true,
        json: async () => ({ ok: true, data: innerMatrix, meta: {} }),
      })
    )
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <QualificationMatrixCard candidateId="cand-2" companyId="co-1" jobId="job-xyz" />
      </QueryClientProvider>
    )
    // Deve mostrar o label do inner data — nao falhar por causa do envelope
    await screen.findByText("Liderança Técnica")
    expect(screen.queryByText(/erro/i)).not.toBeInTheDocument()
  })
})
