/**
 * Tests — Breadcrumbs component
 *
 * Covers:
 *  - Null render on root / single-crumb paths
 *  - Auto-generation from typical PT-BR dashboard paths
 *  - Locale prefix stripping
 *  - UUID segment skipping
 *  - Manual items override
 *  - aria-current="page" on last item
 *  - Home icon + Início label always first
 *  - Unknown segments shown as-is
 *  - generateBreadcrumbs pure function (no DOM)
 */

import { render, screen } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"

vi.mock("next/navigation", () => ({ usePathname: vi.fn() }))
vi.mock("next/link", () => ({
  default: ({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) => (
    <a href={href} className={className}>{children}</a>
  ),
}))

import { usePathname } from "next/navigation"
import { Breadcrumbs, generateBreadcrumbs } from "../Breadcrumbs"

const mockPathname = usePathname as ReturnType<typeof vi.fn>

describe("generateBreadcrumbs (pure function)", () => {
  it("returns only Início for root path", () => {
    const crumbs = generateBreadcrumbs("/")
    expect(crumbs).toHaveLength(1)
    expect(crumbs[0].label).toBe("Início")
  })

  it("strips locale prefix /pt/ and generates crumbs", () => {
    const crumbs = generateBreadcrumbs("/pt/recrutar")
    expect(crumbs).toHaveLength(2)
    expect(crumbs[0]).toEqual({ label: "Início", href: "/" })
    expect(crumbs[1]).toEqual({ label: "Recrutar" })  // last has no href
  })

  it("strips locale prefix /en/", () => {
    const crumbs = generateBreadcrumbs("/en/configuracoes")
    expect(crumbs).toHaveLength(2)
    expect(crumbs[1].label).toBe("Configurações")
  })

  it("skips UUID segments", () => {
    const uuid = "550e8400-e29b-41d4-a716-446655440000"
    const crumbs = generateBreadcrumbs(`/pt/projetos/${uuid}`)
    const labels = crumbs.map((c) => c.label)
    expect(labels).not.toContain(uuid)
    expect(labels).toContain("Projetos")
  })

  it("last crumb has no href", () => {
    const crumbs = generateBreadcrumbs("/pt/recrutar")
    const last = crumbs[crumbs.length - 1]
    expect(last.href).toBeUndefined()
  })

  it("intermediate crumbs have href", () => {
    const crumbs = generateBreadcrumbs("/pt/configuracoes/ai-credits")
    // Início, Configurações (href), Créditos de IA (no href)
    expect(crumbs.length).toBeGreaterThanOrEqual(3)
    expect(crumbs[1].href).toBeDefined()
    expect(crumbs[crumbs.length - 1].href).toBeUndefined()
  })

  it("uses raw segment for unknown paths", () => {
    const crumbs = generateBreadcrumbs("/pt/unknown-page")
    const labels = crumbs.map((c) => c.label)
    expect(labels).toContain("unknown-page")
  })

  it("maps funil-de-talentos to correct label", () => {
    const crumbs = generateBreadcrumbs("/pt/funil-de-talentos")
    expect(crumbs[1].label).toBe("Funil de Talentos")
  })
})

describe("Breadcrumbs component", () => {
  beforeEach(() => {
    mockPathname.mockReturnValue("/pt/recrutar")
  })

  it("renders null on root path", () => {
    mockPathname.mockReturnValue("/")
    const { container } = render(<Breadcrumbs />)
    expect(container.firstChild).toBeNull()
  })

  it("renders null when pathname has no parseable route", () => {
    mockPathname.mockReturnValue("/pt")
    const { container } = render(<Breadcrumbs />)
    // only "Início" would be generated → null
    expect(container.firstChild).toBeNull()
  })

  it("renders nav with Início and route label", () => {
    mockPathname.mockReturnValue("/pt/recrutar")
    render(<Breadcrumbs />)
    expect(screen.getByRole("navigation", { name: /localização/i })).toBeTruthy()
    expect(screen.getByText("Início")).toBeInTheDocument()
    expect(screen.getByText("Recrutar")).toBeInTheDocument()
  })

  it("last item has aria-current=page", () => {
    mockPathname.mockReturnValue("/pt/candidatos")
    render(<Breadcrumbs />)
    const last = screen.getByText("Candidatos")
    expect(last.getAttribute("aria-current")).toBe("page")
  })

  it("intermediate items are links, last is not", () => {
    mockPathname.mockReturnValue("/pt/configuracoes/ai-credits")
    render(<Breadcrumbs />)
    // "Configurações" should be a link
    const configLink = screen.getByRole("link", { name: "Configurações" })
    expect(configLink).toBeTruthy()
    // Last item "Créditos de IA" should not be a link
    const lastSpan = screen.getByText("Créditos de IA")
    expect(lastSpan.tagName).not.toBe("A")
  })

  it("renders custom items when provided (ignores pathname)", () => {
    mockPathname.mockReturnValue("/any")
    render(
      <Breadcrumbs
        items={[
          { label: "Início", href: "/" },
          { label: "Seção Custom", href: "/custom" },
          { label: "Detalhe" },
        ]}
      />,
    )
    expect(screen.getByText("Seção Custom")).toBeInTheDocument()
    expect(screen.getByText("Detalhe")).toBeInTheDocument()
  })

  it("does not render UUID segments in output", () => {
    const uuid = "550e8400-e29b-41d4-a716-446655440000"
    mockPathname.mockReturnValue(`/pt/projetos/${uuid}`)
    render(<Breadcrumbs />)
    expect(screen.queryByText(uuid)).not.toBeInTheDocument()
  })

  it("applies custom className to nav element", () => {
    mockPathname.mockReturnValue("/pt/recrutar")
    render(<Breadcrumbs className="custom-test-class" />)
    const nav = screen.getByRole("navigation", { name: /localização/i })
    expect(nav.className).toContain("custom-test-class")
  })
})
