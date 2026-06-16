/**
 * Snapshot sentinela — Task #1048
 *
 * TabSectionHeader é o header reutilizável das 5 abas do Agent Studio
 * (Captação, Personalizados, Marketplace, Gêmeos, Busca). Garante que o
 * componente compartilhado não sofra drift visual entre variações.
 */
import { describe, expect, it } from "vitest"
import { render } from "@testing-library/react"

import { TabSectionHeader } from "../TabSectionHeader"

describe("TabSectionHeader (Task #1048)", () => {
  it("renderiza apenas título + subtítulo (variante mínima)", () => {
    const { container } = render(
      <TabSectionHeader title="Gêmeos Digitais" subtitle="Clone seu raciocínio" />,
    )
    expect(container.firstChild).toMatchSnapshot()
  })

  it("renderiza com ícone + actions (variante Marketplace)", () => {
    const { container } = render(
      <TabSectionHeader
        title="Marketplace"
        subtitle="Agentes prontos da comunidade"
        icon={<span data-testid="icon">★</span>}
        actions={<button type="button">Ver tudo</button>}
      />,
    )
    expect(container.firstChild).toMatchSnapshot()
  })

  it("renderiza com count badge + actions (variante Personalizados)", () => {
    const { container } = render(
      <TabSectionHeader
        title="Agentes Personalizados"
        subtitle="Seus agentes customizados"
        count={3}
        actions={<button type="button">+ Novo</button>}
      />,
    )
    expect(container.firstChild).toMatchSnapshot()
  })

  it("não renderiza badge quando count = 0", () => {
    const { container } = render(
      <TabSectionHeader title="Vazio" subtitle="sem itens" count={0} />,
    )
    expect(container.querySelector(".bg-lia-interactive-active")).toBeNull()
  })

  it("h2 sempre usa text-sm font-semibold (contrato visual canônico)", () => {
    const { container } = render(<TabSectionHeader title="Qualquer" />)
    const h2 = container.querySelector("h2")
    expect(h2).not.toBeNull()
    expect(h2?.className).toContain("text-sm")
    expect(h2?.className).toContain("font-semibold")
    expect(h2?.className).toContain("text-lia-text-primary")
  })

  it("renderiza apenas título + count, sem subtítulo nem actions (variante 'Meus Agentes')", () => {
    // Cobre o uso em AgentStudioPage (aba Captação) e na subseção interna da
    // aba Personalizados, onde só o título + badge de contagem aparecem.
    const { container } = render(
      <TabSectionHeader title="Meus Agentes" count={5} />,
    )
    expect(container.firstChild).toMatchSnapshot()
  })

  it("renderiza com ícone, sem subtítulo nem actions (variante 'Como funciona')", () => {
    // Cobre a seção "Como funciona" do AgentStudioPage que mostra apenas o
    // ícone Brain + título.
    const { container } = render(
      <TabSectionHeader
        title="Como funciona"
        icon={<span data-testid="brain-icon">🧠</span>}
      />,
    )
    expect(container.firstChild).toMatchSnapshot()
  })

  it("subtítulo sempre usa text-xs text-lia-text-secondary mt-0.5", () => {
    const { container } = render(
      <TabSectionHeader title="X" subtitle="Subtitulo" />,
    )
    const p = container.querySelector("p")
    expect(p).not.toBeNull()
    expect(p?.className).toContain("text-xs")
    expect(p?.className).toContain("text-lia-text-secondary")
    expect(p?.className).toContain("mt-0.5")
  })
})
