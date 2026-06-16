// @vitest-environment jsdom
/**
 * Sensor TDD — WizardFullscreenPromptCard (F3 consent card)
 * Spec: seção 5 do wizard Manus spec.
 * Verifica que os dois CTAs (accept/decline) e o botão X disparam os callbacks
 * corretos e que o componente sobrevive a rerenders (Rules of Hooks).
 *
 * framer-motion é mockado via alias no vitest.config.ts (framer-motion → __mocks__).
 */
import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { WizardFullscreenPromptCard } from "../WizardFullscreenPromptCard"

describe("WizardFullscreenPromptCard — F3 consent card", () => {
  const onAccept = vi.fn()
  const onDecline = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("renderiza botão 'Ir para tela cheia' e botão 'Continuar aqui'", () => {
    render(<WizardFullscreenPromptCard onAccept={onAccept} onDecline={onDecline} />)
    // Usa "ir para tela cheia" (texto do botão exato) — não o título do card
    expect(screen.getByText(/ir para tela cheia/i)).toBeInTheDocument()
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
