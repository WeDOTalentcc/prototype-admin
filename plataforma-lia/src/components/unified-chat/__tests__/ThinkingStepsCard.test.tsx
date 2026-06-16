import React from "react"
import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import ptBR from "../../../../messages/pt-BR.json"
import { ThinkingStepsCard } from "../ThinkingStepsCard"

function renderWithIntl(ui: React.ReactNode, locale = "pt") {
  return render(
    <NextIntlClientProvider
      locale={locale}
      messages={ptBR as Record<string, unknown>}
    >
      {ui}
    </NextIntlClientProvider>,
  )
}

describe("ThinkingStepsCard", () => {
  it("empilha os passos em PT (todos visíveis, evolução), nunca em inglês cru", () => {
    renderWithIntl(<ThinkingStepsCard steps={["understanding", "composing"]} />)
    // todos os passos revelados ficam visíveis, um abaixo do outro
    expect(screen.getByText("Entendendo sua solicitação")).toBeInTheDocument()
    expect(screen.getByText("Preparando a resposta")).toBeInTheDocument()
    // localizados — nada de chave crua vazando
    expect(screen.queryByText("understanding")).not.toBeInTheDocument()
    expect(screen.queryByText("composing")).not.toBeInTheDocument()
  })

  it("localiza para EN quando o locale é inglês", () => {
    renderWithIntl(
      <ThinkingStepsCard steps={["understanding", "composing"]} />,
      "en",
    )
    expect(screen.getByText("Understanding your request")).toBeInTheDocument()
    expect(screen.getByText("Composing the response")).toBeInTheDocument()
  })

  it("mantém texto livre/desconhecido como fallback seguro", () => {
    renderWithIntl(<ThinkingStepsCard steps={["🔧 sync_job…"]} />)
    expect(screen.getByText("🔧 sync_job…")).toBeInTheDocument()
  })

  it("estado vazio retorna null — sem fallback Pensando estático", () => {
    const { container } = renderWithIntl(<ThinkingStepsCard steps={[]} />)
    // Comportamento intencional: sem passos = nada renderiza.
    // O AgentActivityTimeline mostra o primeiro chip quando o 1o
    // reasoning_step/tool_started chega (~100ms após o thinking event).
    expect(container).toBeEmptyDOMElement()
  })
})
