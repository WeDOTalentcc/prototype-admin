import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { DynamicContextPanel } from "../DynamicContextPanel"

/**
 * Fase 5 shell polish — card inset + transição dinâmica de conteúdo por estágio.
 * O corpo do painel é envolto num wrapper keyed por `stage` (re-monta na troca
 * de estágio) com animação enter via transform/opacity (ease-out, motion-reduce
 * safe). Pinamos a presença do wrapper + render do header; sem stage → nada.
 */
describe("DynamicContextPanel — shell dinâmico", () => {
  it("stage=null não renderiza (sem throw)", () => {
    const { container } = render(
      <DynamicContextPanel stage={null} data={{}} requiresApproval={false} />,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it("com stage: header + body wrapper com animação enter", () => {
    render(
      <DynamicContextPanel stage="intake" data={{}} requiresApproval={false} />,
    )
    // header (h3) com rótulo do estágio
    expect(screen.getByRole("heading", { level: 3 })).toBeInTheDocument()
    // body wrapper keyed (transição dinâmica)
    const body = screen.getByTestId("wizard-stage-body")
    expect(body).toBeInTheDocument()
    expect(body.className).toMatch(/animate-in/)
    expect(body.className).toMatch(/motion-reduce:animate-none/)
  })
})
