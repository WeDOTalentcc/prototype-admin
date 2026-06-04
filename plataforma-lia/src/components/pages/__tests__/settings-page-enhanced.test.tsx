/**
 * Tests — SettingsPageEnhanced (Task #896, atualizado 2026-06-04)
 *
 * Alinhado ao `getDefaultSections()` atual (10 hubs canônicos), após a
 * re-expansão do menu (pipeline/screening voltaram a ser hubs standalone e
 * 'consumo' substituiu o antigo 'ai-credits'):
 *
 * Seções actuais (10):
 *   minha-empresa | lia-personalizacao | pipeline | screening |
 *   templates-assinatura | comunicacao-alertas | usuarios-departamentos |
 *   integrations | fairness-compliance | consumo
 *
 * Grupos visuais (5, todos com itens): empresa | processo | lia |
 *   comunicacao | plataforma
 *
 * Cobre:
 *   1. Sidebar renderiza os 10 hubs definidos em getDefaultSections().
 *   2. O switch renderSectionContent() carrega o hub correto por activeSection.
 *   3. O listener de window.dispatchEvent('settings-open-tab', 'alertas')
 *      muda a tab para 'comunicacao-alertas' (único alias tratado).
 *   4. A11y básico — nav role + aria-label + foco visível.
 *   5. Grupos visuais da sidebar (5 grupos).
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

// P2-3 RBAC: mock auth-context com admin role (todos hubs visiveis nos tests).
vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({
    user: { id: "test-user", email: "admin@test.com", role: "admin", company: "test-co" },
    isAuthenticated: true,
    isLoading: false,
  }),
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
vi.mock("@/components/settings/LiaPersonalizacaoHub", () => ({
  LiaPersonalizacaoHub: (props: { activeSubsection?: string }) => (
    <div data-testid="hub-lia-personalizacao" data-active-subsection={props.activeSubsection ?? ""} />
  ),
}))
vi.mock("@/components/settings/RecruitmentPipelineTab", () => ({
  RecruitmentPipelineTab: () => <div data-testid="hub-pipeline" />,
}))
vi.mock("@/components/settings/RecruitmentScreeningTab", () => ({
  RecruitmentScreeningTab: () => <div data-testid="hub-screening" />,
}))
// CommunicationHub serve dois hubs (templates-assinatura + comunicacao-alertas);
// os data-attrs permitem distinguir qual variante o switch montou.
vi.mock("@/components/settings/CommunicationHub", () => ({
  CommunicationHub: (props: { activeSubsection?: string; visibleTabs?: string[]; stacked?: boolean }) => {
    const tabs = props.visibleTabs ?? []
    return (
      <div
        data-testid="hub-communication"
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
vi.mock("@/components/settings/ConsumoHub", () => ({
  ConsumoHub: () => <div data-testid="hub-consumo" />,
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
        "lia-personalizacao": 0,
        pipeline: 0,
        screening: 0,
        "templates-assinatura": 0,
        "comunicacao-alertas": 10,
        "usuarios-departamentos": 20,
        integrations: 5,
        "fairness-compliance": 0,
        consumo: 0,
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

// Lista canônica dos 10 hubs (ordem de getDefaultSections()).
const HUBS: Array<{ id: string; title: string }> = [
  { id: "minha-empresa", title: "Minha Empresa" },
  { id: "lia-personalizacao", title: "LIA & Personalizacao" },
  { id: "pipeline", title: "Pipeline" },
  { id: "screening", title: "Screening" },
  { id: "templates-assinatura", title: "Templates & Assinatura" },
  { id: "comunicacao-alertas", title: "Comunicação & Alertas" },
  { id: "usuarios-departamentos", title: "Usuários & Departamentos" },
  { id: "integrations", title: "Integrações" },
  { id: "fairness-compliance", title: "Fairness & LGPD" },
  { id: "consumo", title: "Consumo" },
]

// ── 1. Sidebar: 10 hubs + estado inicial ──────────────────────────────────

describe("SettingsPageEnhanced — sidebar", () => {
  it("renderiza os 10 hubs definidos em getDefaultSections()", async () => {
    render(<SettingsPageEnhanced />)

    for (const { id } of HUBS) {
      expect(screen.getByTestId(`settings-menu-${id}`)).toBeInTheDocument()
    }
    // 10 itens, nem mais nem menos — protege contra regressão silenciosa
    const allMenuButtons = screen.getAllByRole("button").filter((b) =>
      b.getAttribute("data-testid")?.startsWith("settings-menu-"),
    )
    expect(allMenuButtons).toHaveLength(10)
    // Drena o microtask do dynamic-import
    await screen.findByTestId("hub-minha-empresa")
  })

  it("seções legadas (recrutamento-lia, ai-credits, governanca, webhooks) NÃO existem no menu", () => {
    render(<SettingsPageEnhanced />)

    const removed = ["recrutamento-lia", "ai-credits", "governanca", "webhooks"]
    for (const id of removed) {
      expect(screen.queryByTestId(`settings-menu-${id}`)).not.toBeInTheDocument()
    }
  })

  it("começa com 'minha-empresa' ativo e renderiza o hub correspondente", async () => {
    render(<SettingsPageEnhanced />)

    const minhaEmpresaButton = screen.getByTestId("settings-menu-minha-empresa")
    expect(minhaEmpresaButton.getAttribute("data-active")).toBe("true")

    await screen.findByTestId("hub-minha-empresa")
  })
})

// ── 2. Switch renderSectionContent — cada activeSection carrega o hub certo

describe("SettingsPageEnhanced — switch de hubs por activeSection", () => {
  // templates-assinatura e comunicacao-alertas compartilham o CommunicationHub
  // (data-testid="hub-communication"); só um monta por vez via activeSection.
  const cases: Array<{ id: string; testid: string }> = [
    { id: "minha-empresa", testid: "hub-minha-empresa" },
    { id: "lia-personalizacao", testid: "hub-lia-personalizacao" },
    { id: "pipeline", testid: "hub-pipeline" },
    { id: "screening", testid: "hub-screening" },
    { id: "templates-assinatura", testid: "hub-communication" },
    { id: "comunicacao-alertas", testid: "hub-communication" },
    { id: "usuarios-departamentos", testid: "hub-usuarios-departamentos" },
    { id: "integrations", testid: "hub-integrations" },
    { id: "fairness-compliance", testid: "hub-fairness-compliance" },
    { id: "consumo", testid: "hub-consumo" },
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

  it("'templates-assinatura' renderiza CommunicationHub empilhado com templates + signature", async () => {
    const user = userEvent.setup()
    render(<SettingsPageEnhanced />)

    await user.click(screen.getByTestId("settings-menu-templates-assinatura"))

    const hub = await screen.findByTestId("hub-communication")
    expect(hub).toBeInTheDocument()
    const tabs = hub.getAttribute("data-visible-tabs") ?? ""
    expect(tabs).toContain("templates")
    expect(tabs).toContain("signature")
    expect(hub.getAttribute("data-stacked")).toBe("true")
  })

  it("'comunicacao-alertas' renderiza CommunicationHub focado em alerts", async () => {
    const user = userEvent.setup()
    render(<SettingsPageEnhanced />)

    await user.click(screen.getByTestId("settings-menu-comunicacao-alertas"))

    const hub = await screen.findByTestId("hub-communication")
    expect(hub).toBeInTheDocument()
    const tabs = hub.getAttribute("data-visible-tabs") ?? ""
    expect(tabs).toContain("alerts")
    expect(hub.getAttribute("data-active-subsection")).toBe("alerts")
    expect(hub.getAttribute("data-stacked")).toBe("false")
  })

  it("'fairness-compliance' monta com a subsection 'fairness' por default", async () => {
    const user = userEvent.setup()
    render(<SettingsPageEnhanced />)

    await user.click(screen.getByTestId("settings-menu-fairness-compliance"))

    const hub = await screen.findByTestId("hub-fairness-compliance")
    expect(hub.getAttribute("data-active-subsection")).toBe("fairness")
  })
})

// ── 3. Listener `settings-open-tab` (único alias tratado: 'alertas') ──────

describe("SettingsPageEnhanced — listener 'settings-open-tab'", () => {
  it("traduz o alias 'alertas' para 'comunicacao-alertas'", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    await act(async () => {
      window.dispatchEvent(new CustomEvent("settings-open-tab", { detail: "alertas" }))
    })

    await waitFor(() => {
      expect(screen.getByTestId("hub-communication")).toBeInTheDocument()
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

  it("ignora ids de hub válidos diferentes de 'alertas' (handler só trata 'alertas')", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    for (const detail of ["pipeline", "screening", "consumo", "integrations"]) {
      await act(async () => {
        window.dispatchEvent(new CustomEvent("settings-open-tab", { detail }))
      })
      expect(screen.getByTestId("settings-content-area").getAttribute("data-active-section")).toBe(
        "minha-empresa",
      )
    }
  })
})

// ── 3b. Listener `lia:settings-action` (atalho do chat — Task #1277) ───────

describe("SettingsPageEnhanced — listener 'lia:settings-action'", () => {
  it("abre a section informada entre os 10 hubs", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("lia:settings-action", {
          detail: { actionId: "settings_open_tab", section: "integrations", source: "chat" },
        }),
      )
    })

    await waitFor(() => {
      expect(screen.getByTestId("settings-content-area").getAttribute("data-active-section")).toBe(
        "integrations",
      )
    })
  })

  it("resolve o alias de section ('alertas' → 'comunicacao-alertas')", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("lia:settings-action", {
          detail: { section: "alertas", source: "chat" },
        }),
      )
    })

    await waitFor(() => {
      expect(screen.getByTestId("settings-content-area").getAttribute("data-active-section")).toBe(
        "comunicacao-alertas",
      )
    })
  })

  it("quando 'field' é informado, rola até o campo (scrollIntoView)", async () => {
    const scrollSpy = Element.prototype.scrollIntoView as ReturnType<typeof vi.fn>
    scrollSpy.mockClear()
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("lia:settings-action", {
          detail: { section: "minha-empresa", field: "culture.values", source: "chat" },
        }),
      )
    })

    await waitFor(() => {
      expect(scrollSpy).toHaveBeenCalled()
    })
    const fieldEl = document.querySelector('[data-field="culture.values"]') as HTMLElement | null
    expect(fieldEl).toBeTruthy()
  })

  it("ignora section inválida sem trocar a aba", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("lia:settings-action", {
          detail: { section: "secao-fantasma", source: "chat" },
        }),
      )
    })

    expect(screen.getByTestId("settings-content-area").getAttribute("data-active-section")).toBe(
      "minha-empresa",
    )
  })
})

// ── 4. A11y básico ────────────────────────────────────────────────────────

describe("SettingsPageEnhanced — acessibilidade básica da sidebar", () => {
  it("expõe a sidebar como <nav role='navigation'> rotulada", () => {
    render(<SettingsPageEnhanced />)
    const nav = screen.getByRole("navigation", { name: /configurações/i })
    expect(nav).toBeInTheDocument()
  })

  it("cada item da sidebar tem aria-label igual ao título do hub", () => {
    render(<SettingsPageEnhanced />)
    for (const { id, title } of HUBS) {
      const btn = screen.getByTestId(`settings-menu-${id}`)
      expect(btn.getAttribute("aria-label")).toBe(title)
    }
  })

  it("os botões da sidebar são focáveis na ordem do tab", async () => {
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
    expect(document.activeElement?.getAttribute("data-testid")).toBe("settings-menu-minha-empresa")
  })
})

// ── 5. Grupos visuais da sidebar (5 grupos, todos com itens) ─────────────

describe("SettingsPageEnhanced — grupos visuais da sidebar", () => {
  it("renderiza os 5 grupos como containers data-group-id", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")
    // Todos os 5 grupos têm pelo menos um hub → todos renderizados.
    const expectedGroupIds = ["empresa", "processo", "lia", "comunicacao", "plataforma"]
    for (const gid of expectedGroupIds) {
      const el = document.querySelector(`[data-group-id="${gid}"]`)
      expect(el).toBeTruthy()
    }
  })
})

// ── 6. Toggle explícito de recolher/expandir (Task #1279) ─────────────────
//
// A barra agora tem um controle dedicado de "recolher para ícones" separado do
// lock. A ESCOLHA EXPLÍCITA (toggle) é o que persiste em localStorage; o hover
// é só uma prévia temporária. Estes testes blindam:
//   - existência do toggle dedicado (separado do lock);
//   - clicar recolhe e persiste em `settings-sidebar-collapsed`;
//   - a escolha de recolhido salva é respeitada em sessões seguintes.

describe("SettingsPageEnhanced — toggle explícito de recolher/expandir", () => {
  beforeEach(() => {
    try {
      localStorage.clear()
    } catch {}
  })
  afterEach(() => {
    try {
      localStorage.clear()
    } catch {}
  })

  it("expõe um toggle dedicado de recolher, separado do lock", async () => {
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    expect(screen.getByTestId("settings-sidebar-collapse-toggle")).toBeInTheDocument()
    expect(screen.getByTestId("settings-sidebar-lock-toggle")).toBeInTheDocument()
  })

  it("clicar no toggle recolhe a barra e persiste a escolha explícita", async () => {
    const user = userEvent.setup()
    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    const collapseToggle = screen.getByTestId("settings-sidebar-collapse-toggle")
    expect(collapseToggle.getAttribute("aria-label")).toBe("Recolher menu para ícones")

    await user.click(collapseToggle)

    await waitFor(() => {
      expect(localStorage.getItem("settings-sidebar-collapsed")).toBe("true")
    })
    // Recolhida → o toggle passa a oferecer "Expandir menu".
    await waitFor(() => {
      expect(
        screen.getByTestId("settings-sidebar-collapse-toggle").getAttribute("aria-label"),
      ).toBe("Expandir menu")
    })
  })

  it("respeita a escolha de recolhido salva em sessões anteriores", async () => {
    localStorage.setItem("settings-sidebar-locked", "true")
    localStorage.setItem("settings-sidebar-collapsed", "true")

    render(<SettingsPageEnhanced />)
    await screen.findByTestId("hub-minha-empresa")

    // Em repouso recolhida, o toggle dedicado oferece "Expandir menu".
    await waitFor(() => {
      expect(
        screen.getByTestId("settings-sidebar-collapse-toggle").getAttribute("aria-label"),
      ).toBe("Expandir menu")
    })
  })
})
