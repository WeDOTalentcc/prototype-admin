import React from "react"
import { describe, it, expect } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
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
  it("destaca o passo atual em PT e recolhe os concluídos (nunca mostra inglês cru)", () => {
    renderWithIntl(<ThinkingStepsCard steps={["understanding", "composing"]} />)
    // último passo = em foco (visível)
    expect(screen.getByText("Preparando a resposta")).toBeInTheDocument()
    // passos anteriores recuam para o contador discreto (escondidos até expandir)
    expect(
      screen.queryByText("Entendendo sua solicitação"),
    ).not.toBeInTheDocument()
    // expandir o contador revela o concluído, já localizado
    fireEvent.click(screen.getByRole("button"))
    expect(screen.getByText("Entendendo sua solicitação")).toBeInTheDocument()
    expect(screen.queryByText("understanding")).not.toBeInTheDocument()
    expect(screen.queryByText("composing")).not.toBeInTheDocument()
  })

  it("localiza para EN quando o locale é inglês", () => {
    renderWithIntl(
      <ThinkingStepsCard steps={["understanding", "composing"]} />,
      "en",
    )
    // passo atual em foco
    expect(screen.getByText("Composing the response")).toBeInTheDocument()
    // concluído escondido até expandir
    expect(
      screen.queryByText("Understanding your request"),
    ).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole("button"))
    expect(screen.getByText("Understanding your request")).toBeInTheDocument()
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
