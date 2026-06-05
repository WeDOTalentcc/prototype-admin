import { describe, it, expect } from "vitest"
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
