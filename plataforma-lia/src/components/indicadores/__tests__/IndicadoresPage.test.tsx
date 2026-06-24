import { describe, it, expect } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { IndicadoresPage } from "@/components/indicadores/IndicadoresPage"

describe("IndicadoresPage — Apollo-pattern analytics", () => {
  it("renderiza sem erros e exibe header", () => {
    render(<IndicadoresPage />)
    expect(screen.getByText("Indicadores")).toBeTruthy()
    expect(
      screen.getByText(/Análise preditiva do seu pipeline/i)
    ).toBeTruthy()
  })

  it("exibe filtro de período com 3 opções", () => {
    render(<IndicadoresPage />)
    const select = screen.getByRole("combobox", { name: /período/i })
    expect(select).toBeTruthy()
    const options = screen.getAllByRole("option")
    expect(options.length).toBeGreaterThanOrEqual(3)
  })

  it("exibe KPI cards (candidatos ativos, taxa de conversão, SLA)", () => {
    render(<IndicadoresPage />)
    expect(screen.getByText("Candidatos Ativos")).toBeTruthy()
    expect(screen.getByText("Taxa de Conversão")).toBeTruthy()
    expect(screen.getByText("SLA em Risco")).toBeTruthy()
  })

  it("exibe seção premium locked com 'Upgrade Plan' e badge Enterprise", () => {
    render(<IndicadoresPage />)
    expect(screen.getByText("Análise Avançada")).toBeTruthy()
    expect(screen.getByText("Enterprise")).toBeTruthy()
    expect(screen.getByText(/Upgrade Plan/i)).toBeTruthy()
    expect(
      screen.getByText(/Disponível no plano Enterprise/i)
    ).toBeTruthy()
  })

  it("rules of hooks — mudar período não lança erro", () => {
    render(<IndicadoresPage />)
    const select = screen.getByRole("combobox", { name: /período/i })
    fireEvent.change(select, { target: { value: "90d" } })
    // Ainda renderiza sem crash
    expect(screen.getByText("Indicadores")).toBeTruthy()
    fireEvent.change(select, { target: { value: "180d" } })
    expect(screen.getByText("Indicadores")).toBeTruthy()
  })
})
