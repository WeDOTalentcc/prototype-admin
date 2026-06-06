/**
 * Sensor: JobRemuneracaoSection — faixa salarial HERDADA da empresa + override
 * + "A combinar" (nao divulgar).
 *
 * Skill: harness-engineering (sensor) + lia-testing.
 *
 * Audit 2026-06-06 (Paulo): a faixa salarial (min/max) da vaga deve ser
 * IMPORTADA da empresa (Configuracoes -> Faixas Salariais por Nivel), casada
 * pelo nivel + departamento que a vaga ja conhece. Decisoes: (1) Herdado +
 * override; (2) fallback no benchmark de mercado quando nao ha banda; (3) o
 * recrutador pode marcar "A combinar" (nao divulgar) mesmo havendo banda.
 *
 * Edge resolvido (2026-06-06): badge desambiguado ("Faixa herdada da empresa")
 * p/ nao colidir com o badge de PIPELINE "Herdado da empresa" (KanbanJobHeader).
 */

import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import "@testing-library/jest-dom/vitest"

vi.mock("@/components/compensation/VacancyVariableCompManager", () => ({
  VacancyVariableCompManager: () => null,
}))
vi.mock("@/components/benefits/VacancyBenefitsManager", () => ({
  VacancyBenefitsManager: () => null,
}))
vi.mock("@/hooks/company/useSalaryBands", () => ({
  useResolvedSalaryBand: vi.fn(),
  useSalaryBenchmark: vi.fn(),
}))

import { JobRemuneracaoSection } from "../JobRemuneracaoSection"
import { useResolvedSalaryBand, useSalaryBenchmark } from "@/hooks/company/useSalaryBands"

const mockBand = useResolvedSalaryBand as unknown as ReturnType<typeof vi.fn>
const mockMarket = useSalaryBenchmark as unknown as ReturnType<typeof vi.fn>

const JR_BAND = {
  level: "junior",
  min: 4000,
  max: 8000,
  currency: "BRL",
  departments: { tecnologia: true },
  contract_types: ["clt"],
}

function setBand(band: unknown, isFetched = true) {
  mockBand.mockReturnValue({ data: band, isFetched })
}
function setMarket(market: unknown) {
  mockMarket.mockReturnValue({ data: market })
}

function renderSection(form: Record<string, unknown> = {}, isEditing = true) {
  const updateField = vi.fn()
  render(
    <JobRemuneracaoSection
      jobEditForm={{ level: "junior", department: "Tecnologia", type: "clt", title: "Dev", ...form }}
      isEditing={isEditing}
      updateField={updateField}
    />,
  )
  return { updateField }
}

describe("JobRemuneracaoSection — faixa herdada da empresa", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setBand(null)
    setMarket(null)
  })

  it("banda casa + faixa vazia -> HERDADO travado com valor da banda", () => {
    setBand(JR_BAND)
    renderSection({ salaryMin: "", salaryMax: "" })
    expect(screen.getByText(/Faixa herdada da empresa/i)).toBeInTheDocument()
    const inputs = screen.getAllByRole("spinbutton") as HTMLInputElement[]
    expect(inputs[0]).toHaveValue(4000)
    expect(inputs[0]).toBeDisabled()
    expect(screen.getByText(/Personalizar faixa desta vaga/i)).toBeInTheDocument()
  })

  it("Personalizar destrava e semeia os valores da banda", () => {
    setBand(JR_BAND)
    const { updateField } = renderSection({ salaryMin: "", salaryMax: "" })
    fireEvent.click(screen.getByText(/Personalizar faixa desta vaga/i))
    expect(updateField).toHaveBeenCalledWith("salaryMin", 4000)
    expect(updateField).toHaveBeenCalledWith("salaryMax", 8000)
    const inputs = screen.getAllByRole("spinbutton") as HTMLInputElement[]
    expect(inputs[0]).not.toBeDisabled()
  })

  it("sem banda + estimativa de mercado -> sugestao rotulada estimativa", () => {
    setBand(null)
    setMarket({ min: 12000, max: 18000, currency: "BRL", is_estimate: true })
    const { updateField } = renderSection({ salaryMin: "", salaryMax: "" })
    expect(screen.getByText(/Estimativa de mercado/i)).toBeInTheDocument()
    fireEvent.click(screen.getByText(/Usar estimativa/i))
    expect(updateField).toHaveBeenCalledWith("salaryMin", 12000)
    expect(updateField).toHaveBeenCalledWith("salaryMax", 18000)
  })

  it("sem banda + sem mercado -> manual, sem badge de heranca", () => {
    setBand(null)
    setMarket(null)
    renderSection({ salaryMin: "9000", salaryMax: "12000" })
    expect(screen.queryByText(/Faixa herdada da empresa/i)).not.toBeInTheDocument()
    const inputs = screen.getAllByRole("spinbutton") as HTMLInputElement[]
    expect(inputs[0]).toHaveValue(9000)
    expect(inputs[0]).not.toBeDisabled()
  })

  it("valores != banda -> personalizada + Restaurar faixa da empresa", () => {
    setBand(JR_BAND)
    renderSection({ salaryMin: "5000", salaryMax: "9000" })
    expect(screen.getByText(/Faixa personalizada/i)).toBeInTheDocument()
    expect(screen.getByText(/Restaurar faixa da empresa/i)).toBeInTheDocument()
    const inputs = screen.getAllByRole("spinbutton") as HTMLInputElement[]
    expect(inputs[0]).not.toBeDisabled()
  })

  it("A combinar (undisclosed) -> NAO herda, mostra 'A combinar', inputs travados", () => {
    setBand(JR_BAND) // banda existe, mas recrutador marcou A combinar
    renderSection({ salaryUndisclosed: true, salaryMin: "", salaryMax: "" })
    expect(screen.getByText("A combinar")).toBeInTheDocument()
    expect(screen.queryByText(/Faixa herdada da empresa/i)).not.toBeInTheDocument()
    const inputs = screen.getAllByRole("spinbutton") as HTMLInputElement[]
    expect(inputs[0]).toBeDisabled()
    // checkbox marcado
    expect(screen.getByRole("checkbox")).toBeChecked()
  })

  it("marcar 'Nao divulgar faixa' seta o flag e limpa a faixa", () => {
    setBand(JR_BAND)
    const { updateField } = renderSection({ salaryMin: "4000", salaryMax: "8000" })
    fireEvent.click(screen.getByRole("checkbox"))
    expect(updateField).toHaveBeenCalledWith("salaryUndisclosed", true)
    expect(updateField).toHaveBeenCalledWith("salaryMin", "")
    expect(updateField).toHaveBeenCalledWith("salaryMax", "")
  })
})
