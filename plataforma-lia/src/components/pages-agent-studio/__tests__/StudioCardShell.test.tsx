/**
 * Sprint visual 2026-05-25 — StudioCardShell canonical tests.
 *
 * Cobertura:
 *  - slots renderizados condicionalmente (sem slot = sem section vazia)
 *  - asButton wrapper (clickable card) com aria-label
 *  - interactive applies cardStyles.interactive (hover lift)
 *  - onClick handler dispatched
 *  - canonical icon wrapper w-8 h-8 bg-powder
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { StudioCardShell } from "../StudioCardShell"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

describe("StudioCardShell — canonical Sprint visual", () => {
  it("renderiza header obrigatório (icon + title) sem slots opcionais", () => {
    const { container } = render(
      <StudioCardShell
        icon={<span data-testid="icon">I</span>}
        title="Agent X"
      />,
    )
    expect(screen.getByText("Agent X")).toBeTruthy()
    expect(screen.getByTestId("icon")).toBeTruthy()
    // Não deve renderizar separador de actions footer quando sem actionsSlot
    expect(container.querySelector(".border-t")).toBeNull()
  })

  it("ícone wrapper canonical: w-8 h-8 bg-powder rounded-md", () => {
    const { container } = render(
      <StudioCardShell icon={<span>I</span>} title="X" />,
    )
    const wrapper = container.querySelector(".bg-powder")
    expect(wrapper).not.toBeNull()
    expect(wrapper?.className).toContain("w-8")
    expect(wrapper?.className).toContain("h-8")
    expect(wrapper?.className).toContain("rounded-md")
  })

  it("renderiza todos os slots quando providos", () => {
    render(
      <StudioCardShell
        icon={<span>I</span>}
        title="Agent X"
        subtitle="v1"
        badges={<span>BETA</span>}
        statusBadge={<span>Ativo</span>}
        metricsSlot={<div data-testid="metrics">M</div>}
        metaSlot={<div data-testid="meta">Meta</div>}
        alertSlot={<div data-testid="alert">A</div>}
        chipsSlot={<div data-testid="chips">C</div>}
        bodySlot={<div data-testid="body">B</div>}
        actionsSlot={<button>Action</button>}
      />,
    )
    expect(screen.getByText("v1")).toBeTruthy()
    expect(screen.getByText("BETA")).toBeTruthy()
    expect(screen.getByText("Ativo")).toBeTruthy()
    expect(screen.getByTestId("metrics")).toBeTruthy()
    expect(screen.getByTestId("meta")).toBeTruthy()
    expect(screen.getByTestId("alert")).toBeTruthy()
    expect(screen.getByTestId("chips")).toBeTruthy()
    expect(screen.getByTestId("body")).toBeTruthy()
    expect(screen.getByRole("button", { name: "Action" })).toBeTruthy()
  })

  it("asButton renderiza <button> + chama onClick + expõe aria-label", () => {
    const handler = vi.fn()
    render(
      <StudioCardShell
        icon={<span>I</span>}
        title="Template Y"
        asButton
        onClick={handler}
        ariaLabel="Selecionar template Y"
      />,
    )
    const btn = screen.getByRole("button", { name: "Selecionar template Y" })
    fireEvent.click(btn)
    expect(handler).toHaveBeenCalledOnce()
  })

  it("interactive=true OU asButton aplica cardStyles.interactive (hover state canonical)", () => {
    const { container } = render(
      <StudioCardShell icon={<span>I</span>} title="X" interactive />,
    )
    // cardStyles.interactive contém "hover:border-lia-border-default"
    expect(container.firstChild?.textContent).toBeTruthy()
    const root = container.firstChild as HTMLElement
    expect(root.className).toContain("hover:border-lia-border-default")
  })
})
