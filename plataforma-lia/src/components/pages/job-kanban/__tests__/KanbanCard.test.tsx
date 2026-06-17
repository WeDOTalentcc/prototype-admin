import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import { KanbanCard } from "../KanbanCard"
import type { KanbanItem } from "../types"
import ptBRMessages from "../../../../../messages/pt-BR.json"

const baseItem: KanbanItem = {
  id: "1",
  title: "Engenheiro de Software",
  subtitle: "Tecnologia",
  tertiary: "São Paulo, BR",
  avatarFallback: "TE",
  chips: [
    { icon: "briefcase", label: "remoto" },
    { icon: "star", label: "Pleno" },
    { icon: "users", label: "10 candidatos" },
  ],
}

const funnelLabels = {
  screening: "Triagem",
  interview: "Entrevista",
  final: "Final",
  hired: "Contratado",
}

const infoLabels = {
  ageDays: (d: number) => `Aberta há ${d}d`,
  ownerLabel: "Responsável",
}

function renderCard(item: KanbanItem) {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={ptBRMessages}>
      <KanbanCard
        item={item}
        index={0}
        onClick={vi.fn()}
        isDragDisabled
        funnelLabels={funnelLabels}
        infoLabels={infoLabels}
      />
    </NextIntlClientProvider>,
  )
}

describe("KanbanCard (Task #562)", () => {
  it("renderiza estado healthy: título, subtitle, tertiary e chips, sem ribbon", () => {
    renderCard(baseItem)
    expect(screen.getByText("Engenheiro de Software")).toBeInTheDocument()
    expect(screen.getByText("Tecnologia")).toBeInTheDocument()
    expect(screen.getByText("São Paulo, BR")).toBeInTheDocument()
    expect(screen.getByText("remoto")).toBeInTheDocument()
    expect(screen.queryByTestId("job-card-ribbon")).not.toBeInTheDocument()
  })

  it("renderiza ribbon com label + reason visíveis (action-required)", () => {
    renderCard({
      ...baseItem,
      ribbon: {
        label: "Ação Necessária",
        variant: "danger",
        reason: "Deadline vencido há 5d",
      },
    })
    const ribbon = screen.getByTestId("job-card-ribbon")
    expect(ribbon).toHaveAttribute("data-variant", "danger")
    expect(ribbon).toHaveTextContent("Ação Necessária")
    expect(ribbon).toHaveTextContent("Deadline vencido há 5d")
  })

  it("omite linha do owner quando ausente (sem placeholder fake)", () => {
    renderCard(baseItem)
    expect(screen.queryByText("Responsável")).not.toBeInTheDocument()
  })

  it("renderiza owner quando fornecido (avatar + nome)", () => {
    renderCard({
      ...baseItem,
      owner: { name: "Ana Souza", initials: "AS" },
    })
    expect(screen.getByText("Ana Souza")).toBeInTheDocument()
    expect(screen.getByText("AS")).toBeInTheDocument()
  })

  it("renderiza mini funil quando funnel.total > 0", () => {
    renderCard({
      ...baseItem,
      funnel: { total: 10, screening: 5, interview: 3, final: 1, hired: 1 },
    })
    expect(screen.getByTestId("mini-funnel-screening")).toBeInTheDocument()
    expect(screen.getByTestId("mini-funnel-interview")).toBeInTheDocument()
    expect(screen.getByTestId("mini-funnel-final")).toBeInTheDocument()
    expect(screen.getByTestId("mini-funnel-hired")).toBeInTheDocument()
  })

  it("omite mini funil quando funnel ausente; cai para barra de progresso simples", () => {
    renderCard({
      ...baseItem,
      progressPercent: 50,
    })
    expect(screen.queryByTestId("mini-funnel-screening")).not.toBeInTheDocument()
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "50")
  })

  it("renderiza chip de idade quando ageDays presente", () => {
    renderCard({ ...baseItem, ageDays: 30 })
    expect(screen.getByText("Aberta há 30d")).toBeInTheDocument()
  })

  it("renderiza chip de deadline com variante de status", () => {
    renderCard({
      ...baseItem,
      dateLabel: "Vence em 3d",
      deadlineStatus: "warning",
    })
    expect(screen.getByText("Vence em 3d")).toBeInTheDocument()
  })
})
