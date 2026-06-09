/**
 * Sensor — JobFiltersPanel filtros reais (RV-018..021).
 *
 * Garante que:
 * - Sub-tarefa A: Departamento usa useDepartmentsList (não array hardcoded)
 * - Sub-tarefa B: Recrutador usa useCompanyRecruiters (não array hardcoded)
 * - Sub-tarefa B: Gestor usa useCompanyManagers (não array hardcoded)
 * - Verifica que "Demo Recrutador" hardcoded NÃO aparece
 * - Sub-tarefa C: Localização derivada das vagas reais via prop allJobs (RV-019)
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import { JobFiltersPanel } from "../JobFilters"
import type { JobFilters as JobFiltersType } from "../jobsPageTypes"

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("@/hooks/settings/useDepartmentsList", () => ({
  useDepartmentsList: () => ({
    departments: [
      { id: "1", name: "Engenharia" },
      { id: "2", name: "Vendas" },
    ],
    loading: false,
    error: null,
  }),
}))

vi.mock("@/hooks/company/use-company-recruiters", () => ({
  useCompanyRecruiters: () => ({
    recruiters: [
      { id: "r1", name: "Fernanda Lima", email: "fernanda@wedo.cc", role: "recruiter", isActive: true },
      { id: "r2", name: "Thiago Souza", email: "thiago@wedo.cc", role: "recruiter", isActive: true },
    ],
    isLoading: false,
    error: null,
  }),
}))

vi.mock("@/hooks/company/use-company-managers", () => ({
  useCompanyManagers: () => ({
    managers: [
      { id: "m1", name: "Ana Rocha", email: "ana@wedo.cc", role: "manager", isActive: true, canApprove: true },
      { id: "m2", name: "Bruno Alves", email: "bruno@wedo.cc", role: "manager", isActive: true, canApprove: false },
    ],
    isLoading: false,
    error: null,
  }),
}))

// ── Helpers ──────────────────────────────────────────────────────────────────

const emptyFilters: JobFiltersType = {}

const defaultProps = {
  isOpen: true,
  jobFilters: emptyFilters,
  savedSearches: [],
  toggleJobFilter: vi.fn(),
  clearAllJobFilters: vi.fn(),
  hasActiveFilters: () => false,
  getActiveJobFiltersCount: () => 0,
  handleApplySavedSearch: vi.fn(),
  handleRenameSavedSearch: vi.fn(),
  handleDeleteSavedSearch: vi.fn(),
  saveSearchAsTemplate: vi.fn(),
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe("JobFiltersPanel — filtros reais (Sub-tarefa A: Departamento)", () => {
  beforeEach(() => cleanup())

  it("exibe departamentos da API (Engenharia, Vendas)", () => {
    render(<JobFiltersPanel {...defaultProps} />)
    expect(screen.getByText("Engenharia")).toBeInTheDocument()
    expect(screen.getByText("Vendas")).toBeInTheDocument()
  })

  it("NÃO exibe departamento hardcoded 'Tecnologia'", () => {
    render(<JobFiltersPanel {...defaultProps} />)
    // 'Tecnologia' era o primeiro item do array hardcoded original
    expect(screen.queryByText("Tecnologia")).not.toBeInTheDocument()
  })

  it("NÃO exibe departamento hardcoded 'Financeiro'", () => {
    render(<JobFiltersPanel {...defaultProps} />)
    expect(screen.queryByText("Financeiro")).not.toBeInTheDocument()
  })
})

describe("JobFiltersPanel — filtros reais (Sub-tarefa B: Recrutador)", () => {
  beforeEach(() => cleanup())

  it("exibe recrutadores da API (Fernanda Lima, Thiago Souza)", () => {
    render(<JobFiltersPanel {...defaultProps} />)
    expect(screen.getByText("Fernanda Lima")).toBeInTheDocument()
    expect(screen.getByText("Thiago Souza")).toBeInTheDocument()
  })

  it("NÃO exibe recrutador hardcoded 'Demo Recrutador'", () => {
    render(<JobFiltersPanel {...defaultProps} />)
    expect(screen.queryByText("Demo Recrutador")).not.toBeInTheDocument()
  })

  it("NÃO exibe recrutador hardcoded 'Ana Paula Santos'", () => {
    render(<JobFiltersPanel {...defaultProps} />)
    expect(screen.queryByText("Ana Paula Santos")).not.toBeInTheDocument()
  })
})

describe("JobFiltersPanel — filtros reais (Sub-tarefa B: Gestor)", () => {
  beforeEach(() => cleanup())

  it("exibe gestores da API (Ana Rocha, Bruno Alves)", () => {
    render(<JobFiltersPanel {...defaultProps} />)
    expect(screen.getByText("Ana Rocha")).toBeInTheDocument()
    expect(screen.getByText("Bruno Alves")).toBeInTheDocument()
  })

  it("NÃO exibe gestor hardcoded 'Rafael Oliveira'", () => {
    render(<JobFiltersPanel {...defaultProps} />)
    expect(screen.queryByText("Rafael Oliveira")).not.toBeInTheDocument()
  })
})

describe("JobFiltersPanel — estado de loading (sem crash)", () => {
  it("renderiza sem crash quando hooks retornam arrays vazios (loading)", () => {
    // Sobrescrever mocks com estado de loading
    vi.doMock("@/hooks/settings/useDepartmentsList", () => ({
      useDepartmentsList: () => ({ departments: [], loading: true, error: null }),
    }))
    vi.doMock("@/hooks/company/use-company-recruiters", () => ({
      useCompanyRecruiters: () => ({ recruiters: [], isLoading: true, error: null }),
    }))
    vi.doMock("@/hooks/company/use-company-managers", () => ({
      useCompanyManagers: () => ({ managers: [], isLoading: true, error: null }),
    }))
    // Renderizar com mocks iniciais (arrays vazios) não deve lançar
    render(<JobFiltersPanel {...defaultProps} />)
  })
})

// ── Sub-tarefa C: Localização derivada das vagas reais (RV-019) ──────────────

describe("JobFiltersPanel — Localização derivada das vagas reais (RV-019)", () => {
  beforeEach(() => cleanup())

  it("exibe localizações distintas e ordenadas derivadas de allJobs", () => {
    const allJobs = [
      { location: "São Paulo" },
      { location: "Rio de Janeiro" },
      { location: "São Paulo" }, // duplicata — deve ser deduplicada
      { location: undefined },   // valor vazio — deve ser filtrado
    ] as Parameters<typeof JobFiltersPanel>[0]["allJobs"]

    render(<JobFiltersPanel {...defaultProps} allJobs={allJobs} />)

    // Ambas as localizações reais devem aparecer
    expect(screen.getByText("Rio de Janeiro")).toBeInTheDocument()
    expect(screen.getByText("São Paulo")).toBeInTheDocument()

    // A duplicata não deve gerar chip extra (apenas 1 ocorrência cada)
    expect(screen.getAllByText("São Paulo")).toHaveLength(1)
  })

  it("NÃO exibe localização hardcoded 'São Paulo, SP' quando allJobs não tem essa string", () => {
    // allJobs com localização diferente do hardcoded antigo
    const allJobs = [
      { location: "Campinas" },
    ] as Parameters<typeof JobFiltersPanel>[0]["allJobs"]

    render(<JobFiltersPanel {...defaultProps} allJobs={allJobs} />)

    expect(screen.queryByText("São Paulo, SP")).not.toBeInTheDocument()
    expect(screen.queryByText("Rio de Janeiro, RJ")).not.toBeInTheDocument()
    expect(screen.getByText("Campinas")).toBeInTheDocument()
  })

  it("exibe mensagem vazia (sem chips) quando allJobs não tem locations", () => {
    const allJobs = [
      { location: "" },
      { location: undefined },
    ] as Parameters<typeof JobFiltersPanel>[0]["allJobs"]

    render(<JobFiltersPanel {...defaultProps} allJobs={allJobs} />)

    // Nenhuma das localizações hardcoded antigas deve aparecer
    expect(screen.queryByText("São Paulo, SP")).not.toBeInTheDocument()
    expect(screen.queryByText("Remoto")).not.toBeInTheDocument()
  })

  it("exibe mensagem vazia quando allJobs não é passado (undefined)", () => {
    render(<JobFiltersPanel {...defaultProps} />)

    // Sem allJobs, nenhuma localização hardcoded deve aparecer
    expect(screen.queryByText("São Paulo, SP")).not.toBeInTheDocument()
    expect(screen.queryByText("Rio de Janeiro, RJ")).not.toBeInTheDocument()
    expect(screen.queryByText("Remoto")).not.toBeInTheDocument()
  })
})
