/**
 * Task #895 — smoke test for the Webhooks tab in Configurações.
 *
 * The component itself was already shipped (318 LoC) but it was orphan.
 * After this task it became the 8ª seção do menu. The test exercises:
 *
 *   1. Empty state renders the canonical "Nenhum webhook configurado"
 *      placeholder when the SWR hook returns an empty list — this is the
 *      smoke check the task spec asks for ("smoke E2E que abre a tab e
 *      lista (mesmo vazio)").
 *
 *   2. Populated state renders the webhook name and HTTPS URL coming
 *      from the backend so the operator can manage them via the UI.
 *
 * The hub is not rendered through `SettingsPageEnhanced` because that
 * page lazy-loads 9 dynamic chunks plus a `next/navigation` search-params
 * subscriber. Mounting the manager directly is the same isolation strategy
 * used by `settings-page-target-resolution.test.ts` for `resolveSettingsTarget`.
 */
import React from "react"
import { render, screen } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import { vi, describe, it, expect, beforeEach } from "vitest"

const mockUseWebhooks = vi.fn()

vi.mock("@/hooks/agents", () => ({
  useWebhooks: (...args: unknown[]) => mockUseWebhooks(...args),
}))

import { WebhooksManager } from "@/components/settings/WebhooksManager"

// Mensagens mínimas espelhando `messages/pt-BR.json → settings.webhooks`. Só
// inclui as chaves usadas pelo componente — manter sincronizado se o JSON
// canônico mudar nomes de chave (valores podem divergir; o teste só assere
// strings exibidas no render aqui coberto).
const WEBHOOKS_MESSAGES = {
  settings: {
    webhooks: {
      title: "Webhooks externos",
      newWebhook: "Novo webhook",
      description: "desc",
      loading: "Carregando...",
      noneConfigured: "Nenhum webhook configurado",
      noneHint: "hint",
      active: "Ativo",
      paused: "Pausado",
      lastStatus: "Último: {code}",
      deliveries: "{count} entrega(s)",
      failures: "{count} falha(s)",
      name: "Nome",
      namePlaceholder: "ph",
      urlLabel: "URL",
      urlPlaceholder: "ph",
      events: "Eventos",
      cancel: "Cancelar",
      creating: "Criando...",
      create: "Criar",
      createdTitle: "Criado",
      saveSecretWarning: "warn",
      secretWarningDesc: "desc",
      secretLabel: "Secret",
      understood: "Entendi",
      eventLabels: {
        agent_execution_completed: "Execução concluída",
        agent_execution_failed: "Execução falhou",
        agent_deployment_created: "Vínculo criado",
        agent_deployment_paused: "Vínculo pausado",
        agent_approval_requested: "Aprovação solicitada",
        agent_approval_reviewed: "Aprovação revisada",
      },
    },
  },
} as const

function renderWithIntl(ui: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={WEBHOOKS_MESSAGES}>
      {ui}
    </NextIntlClientProvider>,
  )
}

describe("WebhooksManager — Task #895", () => {
  beforeEach(() => {
    mockUseWebhooks.mockReset()
  })

  it("renders the empty state when the company has no webhooks yet", () => {
    mockUseWebhooks.mockReturnValue({
      webhooks: [],
      total: 0,
      isLoading: false,
      isError: false,
      mutate: vi.fn(),
    })

    renderWithIntl(<WebhooksManager />)

    expect(screen.getByText("Webhooks externos")).toBeInTheDocument()
    expect(screen.getByText("Nenhum webhook configurado")).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: /Novo webhook/i }),
    ).toBeInTheDocument()
  })

  it("lists existing webhooks coming from the backend", () => {
    mockUseWebhooks.mockReturnValue({
      webhooks: [
        {
          id: "wh_1",
          company_id: "co_1",
          name: "Slack notifications",
          url: "https://hooks.slack.com/services/T000/B000/XYZ",
          events: ["agent.execution.completed"],
          is_active: true,
          total_deliveries: 12,
          total_failures: 0,
          last_delivery_at: null,
          last_status_code: 200,
          last_error: null,
          created_by: "user_1",
          created_at: null,
        },
      ],
      total: 1,
      isLoading: false,
      isError: false,
      mutate: vi.fn(),
    })

    renderWithIntl(<WebhooksManager />)

    expect(screen.getByText("Slack notifications")).toBeInTheDocument()
    expect(
      screen.getByText("https://hooks.slack.com/services/T000/B000/XYZ"),
    ).toBeInTheDocument()
    expect(screen.getByText(/Ativo/i)).toBeInTheDocument()
  })
})
