/**
 * Tests — SettingsPageEnhanced (Task #896)
 *
 * Estabelece a rede de proteção mínima do menu Configurações antes das
 * próximas ondas de refactor (cluster Goals/Workforce/GlobalSearch órfão,
 * unificação Templates+Communication, etc).
 *
 * Cobre:
 *   1. Sidebar renderiza os 10 hubs definidos em `getDefaultSections()`.
 *   2. O switch `renderSectionContent()` carrega o hub correto por
 *      `activeSection` (via dynamic import — mockado abaixo).
 *   3. O listener de `window.dispatchEvent('settings-open-tab', sectionId)`
 *      muda a tab ativa e expande a seção.
 *   4. O alias `'alertas'` é traduzido para `'comunicacao-alertas'`.
 *   5. Regressão Task #712 — `dispatchEvent('lia:settings-action',
 *      { section, field })` abre a tab e faz scrollIntoView no
 *      `[data-field="..."]`.
 *   6. A11y básico — `<nav role="navigation">` + cada item com
 *      `aria-label` e foco visível ao tabular.
 *
 * Out of scope: cobertura interna de cada hub (tasks subsequentes).
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
  // requestAnimationFrame em ambiente headless: invoca callback em timeout 0
  if (typeof window !== "undefined" && !window.requestAnimationFrame) {
    window.requestAnimationFrame = (cb: FrameRequestCallback) => {
      return window.setTimeout(() => cb(0), 0) as unknown as number
    }
  }
})

// ── Mocks de dependências (todos hoisted por vi.mock) ─────────────────────

// next-intl: SettingsPageEnhanced e os hubs chamam useTranslations direto.
// Sem este mock, qualquer render falha com "context from NextIntlClientProvider
// was not found" (regressão Task #904, quando a Page passou a usar i18n direto).
// Padrão alinhado com CandidatesTableArea.test.
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
// componente certo. Nenhum hub é instanciado de verdade (eles puxariam
// dezenas de hooks/fetches que estão fora do escopo desta task).
vi.mock("@/components/settings/MinhaEmpresaHub", () => ({
  MinhaEmpresaHub: () => (
    <div data-testid="hub-minha-empresa">
      <div data-field="culture.values">Campo: cultura</div>
    </div>
  ),
}))
vi.mock("@/components/settings/RecruitmentPipelineTab", () => ({
  RecruitmentPipelineTab: () => <div data-testid="hub-pipeline" />,
}))
vi.mock("@/components/settings/RecruitmentScreeningTab", () => ({
  RecruitmentScreeningTab: () => <div data-testid="hub-screening" />,
}))
vi.mock("@/components/settings/CommunicationHub", () => ({
  CommunicationHub: (props: { activeSubsection?: string; visibleTabs?: string[]; stacked?: boolean }) => {
    const tabs = props.visibleTabs ?? []
    // Task #900 — o mesmo CommunicationHub canônico atende duas tabs do
    // menu (templates+signature ↔ schedule+alerts+abtesting). O testid
    // muda conforme `visibleTabs` para distinguir as duas instâncias.
    // A flag `stacked` é refletida em data-stacked para preservar a
    // paridade visual do antigo TemplatesAssinaturaHub (Templates +
    // Signature renderizados juntos, sem pill nav).
    const testid = tabs.includes("templates")
      ? "hub-templates-assinatura"
      : "hub-comunicacao-alertas"
    return (
      <div
        data-testid={testid}
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
vi.mock("@/components/settings/governance/GovernancaHub", () => ({
  GovernancaHub: (props: { activeSubsection?: string }) => (
    <div data-testid="hub-governanca" data-active-subsection={props.activeSubsection ?? ""} />
  ),
}))

// `next/dynamic` no jsdom: invoca o loader e renderiza o módulo resolvido.
// Casado com os mocks acima, garante que o hub correto aparece dentro do
// switch `renderSectionContent()`. Loading é renderizado até o microtask
// resolver (≤ 1 tick).
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
        pipeline: 0,
        screening: 0,
        "templates-assinatura": 30,
        "comunicacao-alertas": 10,
        "usuarios-departamentos": 20,
        integrations: 5,
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

// ── 1. Sidebar: 10 hubs + estado inicial ──────────────────────────────────

describe("SettingsPageEnhanced — sidebar", () => {
  it("renderiza os 10 hubs definidos em getDefaultSections()", async () => {
    render(<SettingsPageEnhanced />)

    const expected = [
      "minha-empresa",
      "pipeline",
      "screening",
      "templates-assinatura",
      "comunicacao-alertas",
      "usuarios-departamentos",
      "integrations",
      "webhooks",
      "fairness-compliance",
      "governanca",
    ]
    for (const id of expected) {
      expect(screen.getByTestId(`settings-menu-${id}`)).toBeInTheDocument()
    }
    // 10 itens, nem mais nem menos — protege contra regressão silenciosa
    const allMenuButtons = screen.getAllByRole("button").filter((b) =>
      b.getAttribute("data-testid")?.startsWith("settings-menu-"),
    )
    expect(allMenuButtons).toHaveLength(10)
    // Drena o microtask do dynamic-import para evitar contaminar o
    // próximo teste com state-updates pendentes do MinhaEmpresaHub.
    await screen.findByTestId("hub-minha-empresa")
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
    { id: "pipeline", testid: "hub-pipeline" },
    { id: "screening", testid: "hub-screening" },
    { id: "templates-assinatura", testid: "hub-templates-assinatura" },
    { id: "comunicacao-alertas", testid: "hub-comunicacao-alertas" },
    { id: "usuarios-departamentos", testid: "hub-usuarios-departamentos" },
    { id: "integrations", testid: "hub-integrations" },
    { id: "fairness-compliance", testid: "hub-fairness-compliance" },
    { id: "governanca", testid: "hub-governanca" },
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

  // Task #900 — paridade visual: 'templates-assinatura' deve renderizar
  // CommunicationHub no modo stacked (Templates + Signature empilhados,
  // sem pill nav), preservando o layout do antigo TemplatesAssinaturaHub.
  it("'templates-assinatura' renderiza CommunicationHub com stacked=true e visibleTabs=templates,signature", async () => {
    const user = userEvent.setup()
    render(<SettingsPageEnhanced />)

    await user.click(screen.getByTestId("settings-menu-templates-assinatura"))

    const hub = await screen.findByTestId("hub-templates-assinatura")
    expect(hub.getAttribute("data-stacked")).toBe("true")
    expect(hub.getAttribute("data-visible-tabs")).toBe("templates,signature")
  })

  it("'comunicacao-alertas' renderiza CommunicationHub sem stacked (modo pill)", async () => {
    const user = userEvent.setup()
    render(<SettingsPageEnhanced />)

    await user.click(screen.getByTestId("settings-menu-comunicacao-alertas"))

    const hub = await screen.findByTestId("hub-comunicacao-alertas")
    expect(hub.getAttribute("data-stacked")).toBe("false")
  })
})

// ── 3. Listener `settings-open-tab` ───────────────────────────────────────

describe("SettingsPageEnhanced — listener 'settings-open-tab'", () => {
  it("abre a tab indicada quando o evento é despachado", async () => {
    render(<SettingsPageEnhanced />)
    // Aguarda hub default montar antes de despachar
    await screen.findByTestId("hub-minha-empresa")

    await act(async () => {
      window.dispatchEvent(new CustomEvent("settings-open-tab", { detail: "pipeline" }))
    })

    await waitFor(() => {
      expect(screen.getByTestId("hub-pipeline")).toBeInTheDocument()
    })
    expect(screen.getByTestId("settings-content-area").getAttribute("data-active-section")).toBe(
      "pipeline",
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
      pipeline: "Pipeline",
      screening: "Screening",
      "templates-assinatura": "Templates & Assinatura",
      "comunicacao-alertas": "Comunicação & Alertas",
      "usuarios-departamentos": "Usuários & Departamentos",
      integrations: "Integrações",
      "fairness-compliance": "Fairness & LGPD",
    }
    for (const [id, label] of Object.entries(expected)) {
      const btn = screen.getByTestId(`settings-menu-${id}`)
      expect(btn.getAttribute("aria-label")).toBe(label)
    }
  })

  it("os botões da sidebar são focáveis na ordem do tab e expõem foco visível", async () => {
    const user = userEvent.setup()
    render(<SettingsPageEnhanced />)

    // Tabula até alcançar o primeiro item de menu (pode haver botões antes
    // — lock toggle etc — então iteramos com limite seguro).
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
