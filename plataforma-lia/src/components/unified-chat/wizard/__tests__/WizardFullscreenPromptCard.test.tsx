// @vitest-environment jsdom
/**
 * Sensor TDD — WizardFullscreenPromptCard (F3 consent card)
 * Spec: seção 5 do wizard Manus spec.
 * Verifica que os dois CTAs (accept/decline) e o botão X disparam os callbacks
 * corretos e que o componente sobrevive a rerenders (Rules of Hooks).
 *
 * framer-motion é mockado porque não está instalado no ambiente de testes.
 * O mock preserva 100% do comportamento de renderização DOM — apenas remove
 * a camada de animação que é irrelevante para este teste comportamental.
 */
import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"

// Mock framer-motion — não instalado no ambiente de testes.
// motion.div e motion.span são renderizados como divs/spans simples.
vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_target, tag: string) =>
        // eslint-disable-next-line react/display-name
        ({ children, ...props }: React.HTMLAttributes<HTMLElement> & { children?: React.ReactNode }) =>
          React.createElement(tag, props, children),
    },
  ),
  AnimatePresence: ({ children }: { children?: React.ReactNode }) => React.createElement(React.Fragment, null, children),
}))

import { WizardFullscreenPromptCard } from "../WizardFullscreenPromptCard"

describe("WizardFullscreenPromptCard — F3 consent card", () => {
  const onAccept = vi.fn()
  const onDecline = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("renderiza botão de aceitar (tela cheia) e botão de recusar (continuar aqui)", () => {
    render(<WizardFullscreenPromptCard onAccept={onAccept} onDecline={onDecline} />)
    expect(screen.getByText(/tela cheia/i)).toBeInTheDocument()
    expect(screen.getByText(/continuar aqui/i)).toBeInTheDocument()
  })

  it("onAccept é chamado ao clicar em 'Ir para tela cheia'", () => {
    render(<WizardFullscreenPromptCard onAccept={onAccept} onDecline={onDecline} />)
    fireEvent.click(screen.getByText(/ir para tela cheia/i))
    expect(onAccept).toHaveBeenCalledTimes(1)
    expect(onDecline).not.toHaveBeenCalled()
  })

  it("onDecline é chamado ao clicar em 'Continuar aqui'", () => {
    render(<WizardFullscreenPromptCard onAccept={onAccept} onDecline={onDecline} />)
    fireEvent.click(screen.getByText(/continuar aqui/i))
    expect(onDecline).toHaveBeenCalledTimes(1)
    expect(onAccept).not.toHaveBeenCalled()
  })

  it("onDecline é chamado ao clicar no botão X (aria-label='Dispensar')", () => {
    render(<WizardFullscreenPromptCard onAccept={onAccept} onDecline={onDecline} />)
    fireEvent.click(screen.getByLabelText(/dispensar/i))
    expect(onDecline).toHaveBeenCalledTimes(1)
    expect(onAccept).not.toHaveBeenCalled()
  })

  it("smoke: rerender e unmount sem throw (Rules of Hooks)", () => {
    const { rerender, unmount } = render(
      <WizardFullscreenPromptCard onAccept={onAccept} onDecline={onDecline} />,
    )
    rerender(
      <WizardFullscreenPromptCard onAccept={vi.fn()} onDecline={vi.fn()} />,
    )
    unmount()
  })
})
