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
  it("traduz as chaves de fase cruas para PT (nunca mostra inglês cru)", () => {
    renderWithIntl(<ThinkingStepsCard steps={["understanding", "composing"]} />)
    expect(screen.getByText("Entendendo sua solicitação")).toBeInTheDocument()
    expect(screen.getByText("Preparando a resposta")).toBeInTheDocument()
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

  it("renderiza o estado vazio 'pensando' sem passos", () => {
    const { container } = renderWithIntl(<ThinkingStepsCard steps={[]} />)
    expect(container.querySelector('[role="status"]')).toBeInTheDocument()
  })
})
