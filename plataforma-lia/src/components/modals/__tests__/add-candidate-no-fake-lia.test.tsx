import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { AddCandidateModal } from "@/components/modals/add-candidate-modal"

// Pina P0-2: a aba "Análise LIA" fabricava score/fit via Math.random+setTimeout
// e apresentava como IA real. Fix: remover a fonte da fabricacao (handler +
// botao) e exibir mensagem honesta — nenhum dado de IA falso e mostrado.
describe("AddCandidateModal — Analise LIA nao fabrica (P0-2)", () => {
  it("aba Analise LIA: mensagem honesta, sem botao 'Iniciar Analise' nem score fabricado", async () => {
    const user = userEvent.setup()
    render(<AddCandidateModal isOpen onClose={() => {}} onAdd={vi.fn()} />)
    await user.click(screen.getByRole("tab", { name: /An[aá]lise LIA/i }))
    // honesto: analise so existe apos cadastro (na ficha do candidato)
    expect(
      await screen.findByText(/dispon[ií]vel na ficha do candidato ap[oó]s o cadastro/i)
    ).toBeTruthy()
    // o gatilho da fabricacao nao pode mais existir
    expect(screen.queryByText(/Iniciar An[aá]lise/i)).toBeNull()
  })
})
