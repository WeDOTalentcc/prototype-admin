import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { SalaryPanel } from "../SalaryPanel"

/**
 * Fase 5 — SalaryPanel: modo confirmado vs. modo livre.
 *
 * Quando salary_confirmed=true (recrutador confirmou via right_panel_form),
 * o painel mostra a faixa como badge verde com opção de ajuste secundário.
 * Quando salary_confirmed=false/undefined, comportamento anterior (sliders).
 * Rules of Hooks: rerender sem throw.
 */

const BASE = {
  salary_min: 12000,
  salary_max: 18000,
  salary_currency: "BRL",
  benefits: [],
  benchmark: null,
  salary_used_fallback: false,
  ai_degraded_mode: null,
}

describe("SalaryPanel — Rules of Hooks", () => {
  it("rerender data vazio → confirmado → sem confirmação sem throw", () => {
    const { rerender } = render(<SalaryPanel data={{}} />)
    expect(() => {
      rerender(<SalaryPanel data={{ ...BASE, salary_confirmed: true }} />)
      rerender(<SalaryPanel data={{ ...BASE, salary_confirmed: false }} />)
      rerender(<SalaryPanel data={{}} />)
    }).not.toThrow()
  })
})

describe("SalaryPanel — modo confirmado (salary_confirmed=true)", () => {
  it("exibe badge de faixa confirmada", () => {
    render(<SalaryPanel data={{ ...BASE, salary_confirmed: true }} />)
    expect(screen.getByTestId("salary-confirmed-display")).toBeInTheDocument()
    expect(screen.getByTestId("salary-confirmed-display")).toHaveTextContent(/Faixa confirmada/i)
  })

  it("mostra os valores formatados no badge", () => {
    render(<SalaryPanel data={{ ...BASE, salary_confirmed: true }} />)
    const display = screen.getByTestId("salary-confirmed-display")
    expect(display).toHaveTextContent(/12\.000/)
    expect(display).toHaveTextContent(/18\.000/)
  })

  it("sliders não aparecem no modo confirmado", () => {
    render(<SalaryPanel data={{ ...BASE, salary_confirmed: true }} />)
    expect(screen.queryByTestId("salary-slider-min")).not.toBeInTheDocument()
    expect(screen.queryByTestId("salary-slider-max")).not.toBeInTheDocument()
  })

  it("botão Ajustar presente", () => {
    render(<SalaryPanel data={{ ...BASE, salary_confirmed: true }} />)
    expect(screen.getByTestId("salary-adjust-btn")).toBeInTheDocument()
  })

  it("clicar Ajustar mostra sliders + Confirmar ajuste", () => {
    render(<SalaryPanel data={{ ...BASE, salary_confirmed: true }} />)
    fireEvent.click(screen.getByTestId("salary-adjust-btn"))
    expect(screen.getByTestId("salary-slider-min")).toBeInTheDocument()
    expect(screen.getByTestId("salary-confirm-adjust-btn")).toBeInTheDocument()
  })

  it("Confirmar ajuste chama onUpdate com novos valores", () => {
    const onUpdate = vi.fn()
    render(<SalaryPanel data={{ ...BASE, salary_confirmed: true }} onUpdate={onUpdate} />)
    fireEvent.click(screen.getByTestId("salary-adjust-btn"))
    const sliderMin = screen.getByTestId("salary-slider-min") as HTMLInputElement
    fireEvent.change(sliderMin, { target: { value: "15000" } })
    fireEvent.click(screen.getByTestId("salary-confirm-adjust-btn"))
    expect(onUpdate).toHaveBeenCalledWith(
      expect.objectContaining({ salary_min: 15000 }),
    )
  })
})

describe("SalaryPanel — modo livre (salary_confirmed=false ou ausente)", () => {
  it("mostra sliders diretamente", () => {
    render(<SalaryPanel data={BASE} />)
    expect(screen.getByTestId("salary-slider-min")).toBeInTheDocument()
    expect(screen.getByTestId("salary-slider-max")).toBeInTheDocument()
  })

  it("badge de confirmado não aparece", () => {
    render(<SalaryPanel data={BASE} />)
    expect(screen.queryByTestId("salary-confirmed-display")).not.toBeInTheDocument()
  })

  it("slider min chama onUpdate com salary_min", () => {
    const onUpdate = vi.fn()
    render(<SalaryPanel data={BASE} onUpdate={onUpdate} />)
    fireEvent.change(screen.getByTestId("salary-slider-min"), { target: { value: "14000" } })
    expect(onUpdate).toHaveBeenCalledWith(expect.objectContaining({ salary_min: 14000 }))
  })
})
