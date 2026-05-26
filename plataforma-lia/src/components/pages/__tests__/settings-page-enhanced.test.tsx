/**
 * Tests — SettingsPageEnhanced (Task #896, updated 2026-05-25)
 *
 * Actualizado para refletir a consolidação do menu 2026-05-25:
 *   - hub 'pipeline' (standalone) → subsection de 'recrutamento-lia'
 *   - hub 'screening' (standalone) → subsection de 'recrutamento-lia'
 *   - hub 'templates-assinatura' → absorvido por 'comunicacao-alertas'
 *   - hub 'governanca' → dissolvido; panels movidos para FairnessComplianceHub + /wedo-admin/
 *   - hub 'webhooks' → removido do menu cliente (Wave 1+)
 *   - hub 'ai-credits' → NOVO no menu
 *
 * Seções actuais (7):
 *   minha-empresa | recrutamento-lia | comunicacao-alertas |
 *   usuarios-departamentos | integrations | ai-credits | fairness-compliance
 *
 * Cobre:
 *   1. Sidebar renderiza os 8 hubs definidos em getDefaultSections().
 *   2. O switch renderSectionContent() carrega o hub correto por activeSection.
 *   3. O listener de window.dispatchEvent('settings-open-tab', sectionId) muda a tab.
 *   4. O alias 'alertas' é traduzido para 'comunicacao-alertas'.
 *   5. Regressão Task #712 — bridge lia:settings-action abre tab e faz scrollIntoView.
 *   6. A11y básico — nav role + aria-label + foco visível.
 */

import React from "react"
import { render, screen, waitFor, act } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest"

// ── matchMedia / ResizeObserver shims (jsdom não implementa) ──────────────

beforeAll(() => {
  if (typeof window !== "undefined" && !window.matchMedia) {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: (query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addEventListener: () => {},
        removeEventListener: () => {},
        addListener: () => {},
        removeListener: () => {},
        dispatchEvent: () => false,
      }),
    })
  }
  if (typeof window !== "undefined" && !(window as unknown as { ResizeObserver?: unknown }).ResizeObserver) {
    ;(window as unknown as { ResizeObserver: unknown }).ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
  }
  // jsdom não implementa scrollIntoView
  if (typeof Element !== "undefined") {
    Element.prototype.scrollIntoView = vi.fn()
  }
  // requestAnimationFrame em ambiente headless
  if (typeof window !== "undefined" && !window.requestAnimationFrame) {
    window.requestAnimationFrame = (cb: FrameRequestCallback) => {
      return window.setTimeout(() => cb(0), 0) as unknown as number
    }
  }
})

// ── Mocks de dependências (todos hoisted por vi.mock) ─────────────────────

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, params?: Record<string, unknown>) =>
    params ? `${key}:${JSON.stringify(params)}` : key,
  useLocale: () => "pt-BR",
}))

vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({
    companyId: "test-company-id",
    tenantInfo: {
      companyId: "test-company-id",
      clientAccountId: null,
      companyProfileId: null,
      companyName: "Empresa Teste",
      planId: "pro",
      status: "active",
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
}))

vi.mock("@/lib/sidebar/useHoverDebounce", () => ({
  useHoverDebounce: () => ({
    handleMouseEnter: vi.fn(),
    handleMouseLeave: vi.fn(),
  }),
}))

// Stubs leves para cada hub — assertam apenas que o switch trocou para o
// componente certo. Nenhum hub é instanciado de verdade.
vi.mock("@/components/settings/MinhaEmpresaHub", () => ({
  MinhaEmpresaHub: () => (
    <div data-testid="hub-minha-empresa">
      <div data-field="culture.values">Campo: cultura</div>
    </div>
  ),
}))
vi.mock("@/components/settings/RecruitmentPipelineTab", () => ({
  RecruitmentPipelineTab: () => <div data-testid="hub-recrutamento-lia-pipeline" />,
}))
vi.mock("@/components/settings/RecruitmentScreeningTab", () => ({
  RecruitmentScreeningTab: () => <div data-testid="hub-recrutamento-lia-screening" />,
}))
vi.mock("@/components/settings/CommunicationHub", () => ({
  CommunicationHub: (props: { activeSubsection?: string; visibleTabs?: string[]; stacked?: boolean }) => {
    const tabs = props.visibleTabs ?? []
    return (
      <div
        data-testid="hub-comunicacao-alertas"
        data-active-subsection={props.activeSubsection ?? ""}
        data-visible-tabs={tabs.join(",")}
        data-stacked={props.stacked ? "true" : "false"}
      />
    )
  },
}))
vi.mock("@/components/settings/IntegrationsHub", () => ({
  IntegrationsHub: (props: { activeSubsection?: string }) => (
    <div data-testid="hub-integrations" data-active-subsection={props.activeSubsection ?? ""} />
  ),
}))
vi.mock("@/components/settings/UsuariosDepartamentosHub", () => ({
  UsuariosDepartamentosHub: () => <div data-testid="hub-usuarios-departamentos" />,
}))
vi.mock("@/components/settings/FairnessComplianceHub", () => ({
  FairnessComplianceHub: (props: { activeSubsection?: string }) => (
    <div data-testid="hub-fairness-compliance" data-active-subsection={props.activeSubsection ?? ""} />
  ),
}))
vi.mock("@/components/pages/ai-credits-page", () => ({
  AiCreditsPage: () => <div data-testid="hub-ai-credits" />,
}))

// `next/dynamic` no jsdom: invoca o loader e renderiza o módulo resolvido.
vi.mock("next/dynamic", () => ({
  default: (loader: () => Promise<{ default?: React.ComponentType<unknown> }>, options?: { loading?: () => React.ReactNode }) => {
    function DynamicMock(props: Record<string, unknown>) {
      const [Comp, setComp] = React.useState<React.ComponentType<unknown> | null>(null)
      React.useEffect(() => {
        let mounted = true
        Promise.resolve(loader()).then((mod) => {
          if (!mounted) return
          const Resolved = (mod && (mod.default ?? (mod as unknown as React.ComponentType<unknown>))) || null
          setComp(() => Resolved)
        })
        return () => {
          mounted = false
        }
      }, [])
      if (!Comp) return options?.loading ? <>{options.loading()}</> : null
      return <Comp {...props} />
    }
    DynamicMock.displayName = "NextDynamicMock"
    return DynamicMock
  },
}))

// fetch mock para `/api/backend-proxy/settings/progress/`
const fetchMock = vi.fn()
beforeEach(() => {
  fetchMock.mockReset()
  fetchMock.mockResolvedValue({
    ok: true,
    json: async () => ({
      overall: 42,
      sections: {
        "minha-empresa": 50,
        "recrutamento-lia": 0,
        "comunicacao-alertas": 10,
        "usuarios-departamentos": 20,
        integrations: 5,
        "ai-credits": 0,
        "fairness-compliance": 0,
      },
      subsections: {},
    }),
  } as unknown as Response)
  global.fetch = fetchMock as unknown as typeof fetch
})

afterEach(() => {
  vi.clearAllMocks()
})

// Imports que dependem dos mocks acima
import SettingsPageEnhanced from "@/components/pages/settings-page-enhanced"

// ── 1. Sidebar: 8 hubs + estado inicial ──────────────────────────────────

describe("SettingsPageEnhanced — sidebar", () => {
  it("renderiza os 8 hubs definidos em getDefaultSections()", async () => {
    render(<SettingsPageEnhanced />)

    // Seções actuais: 7 pós-consolidação 2026-05-25 + 'lia-personalizacao' (P1-4 2026-05-26).
    const expected = [
      "minha-empresa",
      "lia-personalizacao",
      "recrutamento-lia",
      "comunicacao-alertas",
      "usuarios-departamentos",
      "integrations",
      "ai-credits",
      "fairness-compliance",
    ]
    for (const id of expected) {
      expect(screen.getByTestId(`settings-menu-${id}`)).toBeInTheDocument()
    }
    // 8 itens, nem mais nem menos — protege contra regressão silenciosa
    const allMenuButtons = screen.getAllByRole("button").filter((b) =>
      b.getAttribute("data-testid")?.startsWith("settings-menu-"),
    )
    expect(allMenuButtons).toHaveLength(8)
    // Drena o microtask do dynamic-import
    await screen.findByTestId("hub-minha-empresa")
  })

  it("seções removidas (pipeline, screening, templates-assinatura, governanca, webhooks) NÃO existem no menu", () => {
    render(<SettingsPageEnhanced />)

    const removed = ["pipeline", "screening", "templates-assinatura", "governanca", "webhooks"]
    for (const id of removed) {
      expect(screen.queryByTestId(`settings-menu-${id}`)).not.toBeInTheDocument()
    }
  })

  it("começa com 'minha-empresa' ativo e renderiza o hub correspondente", async () => {
    render(<SettingsPageEnhanced />)

    const minhaEmpresaButton = screen.getByTestId("settings-menu-minha-empresa")
    expect(minhaEmpresaButton.getAttribute("data-active")).toBe("true")
    expect(minhaEmpresaButton.getAttribute("aria-current")).toBe("page")

    await screen.findByTestId("hub-minha-empresa")
  })
})

// ── 2. Switch renderSectionContent — cada activeSection carrega o hub certo

describe("SettingsPageEnhanced — switch de hubs por activeSection", () => {
  const cases: Array<{ id: string; testid: string }> = [
    { id: "minha-empresa", testid: "hub-minha-empresa" },
    { id: "recrutamento-lia", testid: "hub-recrutamento-lia-pipeline" },
    { id: "comunicacao-alertas", testid: "hub-comunicacao-alertas" },
    { id: "usuarios-departamentos", testid: "hub-usuarios-departamentos" },
    { id: "integrations", testid: "hub-integrations" },
    { id: "ai-credits", testid: "hub-ai-credits" },
    { id: "fairness-compliance", testid: "hub-fairness-compliance" },
  ]

  for (const { id, testid } of cases) {
    it(`clicar em '${id}' carrega <${testid} />`, async () => {
      const user = userEvent.setup()
      render(<SettingsPageEnhanced />)

      await user.click(screen.getByTestId(`settings-menu-${id}`))

      await waitFor(() => {
        expect(screen.getByTestId(testid)).toBeInTheDocument()
      })
      const contentArea = screen.getByTestId("settings-content-area")
      expect(contentArea.getAttribute("data-active-section")).toBe(id)
    })
  }

  it("'recrutamento-lia' renderiza RecruitmentPipelineTab por default", async () => {
    const user = userEvent.setup()
    render(<SettingsPageEnhanced />)

    await user.click(screen.getByTestId("settings-menu-recrutamento-lia"))

    const hub = await screen.findByTestId("hub-recrutamento-lia-pipeline")
    expect(hub).toBeInTheDocument()
  })

  it("'comunicacao-alertas' renderiza CommunicationHub com todas as tabs", async () => {
    const user = userEvent.setup()
    render(<SettingsPageEnhanced />)

    await user.click(screen.getByTestId("settings-menu-comunicacao-alertas"))

    const hub = await screen.findByTestId("hub-comunicacao-alertas")
    expect(hub).toBeInTheDocument()
    // Deve expor templates + signature + schedule + alerts + abtesting
    const tabs = hub.getAttribute("data-visible-tabs") ?? ""
    expect(tabs).toContain("templates")
    expect(tabs).toContain("signature")
    expect(tabs).toContain("alerts")
  })
})

// ── 3. Listener `settings-open-tab` ───────────────────────────────────────

describe("SettingsPageEnhanced — listener 'settings-open-tab'", () => {
  it("abre a tab 'recrutamento-lia' quando o evento é despachado", async () => {
    render(<SettingsPageEnhanced />)
    // Aguarda hub default montar antes de despachar
    await screen.findByTestId("hub-minha-empresa")

    await act(async () => {
      window.dispatchEvent(new CustomEvent("settings-open-tab", { detail: "recrutamento-lia" }))
    })

    await waitFor(() => {
      expect(screen.getByTestId("hub-recrutamento-lia-pipeline")).toBeInTheDocument()
    })
    expect(screen.getByTestId("settings-content-area").getAttribute("data-active-section")).toBe(
      "recrutamento-lia",
    )
  })

  it("traduz o alias 'alertas' para 'comunicacao-alertas'", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    await act(async () => {
      window.dispatchEvent(new CustomEvent("settings-open-tab", { detail: "alertas" }))
    })

    await waitFor(() => {
      expect(screen.getByTestId("hub-comunicacao-alertas")).toBeInTheDocument()
    })
    expect(screen.getByTestId("settings-content-area").getAttribute("data-active-section")).toBe(
      "comunicacao-alertas",
    )
  })

  it("ignora detail desconhecido sem trocar a tab", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    await act(async () => {
      window.dispatchEvent(new CustomEvent("settings-open-tab", { detail: "secao-inexistente" }))
    })

    expect(screen.getByTestId("settings-content-area").getAttribute("data-active-section")).toBe(
      "minha-empresa",
    )
  })

  it("ignora detalhes de seções removidas (pipeline, governanca, templates-assinatura)", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    for (const removed of ["pipeline", "governanca", "templates-assinatura", "webhooks"]) {
      await act(async () => {
        window.dispatchEvent(new CustomEvent("settings-open-tab", { detail: removed }))
      })
      // Tab não deve mudar — permanece em minha-empresa
      expect(screen.getByTestId("settings-content-area").getAttribute("data-active-section")).toBe(
        "minha-empresa",
      )
    }
  })
})

// ── 4. Regressão Task #712 — bridge `lia:settings-action` ─────────────────

describe("SettingsPageEnhanced — bridge 'lia:settings-action' (Task #712)", () => {
  it("dispatchEvent({ section, field }) abre a tab e dispara scrollIntoView no campo", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    const scrollSpy = Element.prototype.scrollIntoView as unknown as ReturnType<typeof vi.fn>
    scrollSpy.mockClear()

    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("lia:settings-action", {
          detail: { section: "minha-empresa", field: "culture.values" },
        }),
      )
    })

    // Tab abre/permanece em minha-empresa
    expect(screen.getByTestId("settings-content-area").getAttribute("data-active-section")).toBe(
      "minha-empresa",
    )

    // scrollIntoView foi chamado dentro do requestAnimationFrame → aguarda tick
    await waitFor(() => {
      expect(scrollSpy).toHaveBeenCalled()
    })
  })

  it("section válido sem field apenas troca a tab (sem scroll)", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    const scrollSpy = Element.prototype.scrollIntoView as unknown as ReturnType<typeof vi.fn>
    scrollSpy.mockClear()

    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("lia:settings-action", {
          detail: { section: "integrations" },
        }),
      )
    })

    await waitFor(() => {
      expect(screen.getByTestId("hub-integrations")).toBeInTheDocument()
    })
    expect(scrollSpy).not.toHaveBeenCalled()
  })

  it("section inválido é ignorado", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("lia:settings-action", {
          detail: { section: "secao-fantasma", field: "x" },
        }),
      )
    })

    expect(screen.getByTestId("settings-content-area").getAttribute("data-active-section")).toBe(
      "minha-empresa",
    )
  })
})

// ── 5. A11y básico ────────────────────────────────────────────────────────

describe("SettingsPageEnhanced — acessibilidade básica da sidebar", () => {
  it("expõe a sidebar como <nav role='navigation'> rotulada", () => {
    render(<SettingsPageEnhanced />)
    const nav = screen.getByRole("navigation", { name: /configurações/i })
    expect(nav).toBeInTheDocument()
  })

  it("cada item da sidebar tem aria-label igual ao título do hub", () => {
    render(<SettingsPageEnhanced />)
    const expected: Record<string, string> = {
      "minha-empresa": "Minha Empresa",
      "recrutamento-lia": "Recrutamento & LIA",
      "comunicacao-alertas": "Comunicação",
      "usuarios-departamentos": "Usuários & Departamentos",
      integrations: "Integrações",
      "ai-credits": "AI Credits",
      "fairness-compliance": "Compliance & LGPD",
    }
    for (const [id, label] of Object.entries(expected)) {
      const btn = screen.getByTestId(`settings-menu-${id}`)
      expect(btn.getAttribute("aria-label")).toBe(label)
    }
  })

  it("os botões da sidebar são focáveis na ordem do tab e expõem foco visível", async () => {
    const user = userEvent.setup()
    render(<SettingsPageEnhanced />)

    // Tabula até alcançar o primeiro item de menu
    let safety = 0
    let firstMenuFocused = false
    while (safety < 30 && !firstMenuFocused) {
      await user.tab()
      const focused = document.activeElement as HTMLElement | null
      if (focused?.getAttribute("data-testid") === "settings-menu-minha-empresa") {
        firstMenuFocused = true
        break
      }
      safety += 1
    }
    expect(firstMenuFocused).toBe(true)

    const focused = document.activeElement as HTMLElement
    // Foco visível garantido por classe Tailwind `focus-visible:outline-*`
    expect(focused.className).toMatch(/focus-visible:outline/)
  })
})
