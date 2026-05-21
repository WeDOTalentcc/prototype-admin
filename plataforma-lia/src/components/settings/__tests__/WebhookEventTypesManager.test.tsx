/**
 * Smoke tests — WebhookEventTypesManager (P0.G #4)
 *
 * Cobre patterns canonical:
 *  1. render: monta componente, espera lista render com label do event type
 *  2. filter chips: clique em "Master canonical" filtra masters apenas
 *  3. startCreate: clique em "Novo event" abre form de criação
 *  4. permission gate: isAdmin=false + currentUserId=null esconde edit/delete
 *     em customs alheios (created_by !== currentUserId)
 *
 * Pattern: mock do hook canonical via vi.mock; smoke render apenas.
 * Nota: hook retorna `eventTypes` (não `templates`) e métodos `updateEventType`/`deleteEventType`.
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, within } from "@testing-library/react"

import { WebhookEventTypesManager } from "../WebhookEventTypesManager"
import type { WebhookEventType } from "@/hooks/webhooks/use-webhook-event-types"

const masterEvent: WebhookEventType = {
  id: "master-1",
  company_id: null,
  is_master_template: true,
  parent_template_id: null,
  data: {
    event_type: "candidate.created",
    label: "Candidato criado (webhook)",
    category: "candidates",
    description: "Disparado quando candidato criado",
  },
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  created_by: null,
  deleted_at: null,
}

const customOwnEvent: WebhookEventType = {
  id: "custom-own-1",
  company_id: "company-uuid",
  is_master_template: false,
  parent_template_id: null,
  data: {
    event_type: "job.custom_event",
    label: "Event meu",
    category: "jobs",
  },
  created_at: "2026-01-02T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
  created_by: "user-self",
  deleted_at: null,
}

const customForeignEvent: WebhookEventType = {
  id: "custom-foreign-1",
  company_id: "company-uuid",
  is_master_template: false,
  parent_template_id: null,
  data: {
    event_type: "interview.custom",
    label: "Event alheio",
    category: "interviews",
  },
  created_at: "2026-01-03T00:00:00Z",
  updated_at: "2026-01-03T00:00:00Z",
  created_by: "user-other",
  deleted_at: null,
}

const hookReturnValue = {
  eventTypes: [masterEvent, customOwnEvent, customForeignEvent],
  masterCount: 1,
  customCount: 2,
  total: 3,
  isLoading: false,
  error: null,
  refetch: vi.fn(),
  createCustom: vi.fn(),
  updateEventType: vi.fn(),
  deleteEventType: vi.fn(),
  customizeMaster: vi.fn(),
}

vi.mock("@/hooks/webhooks/use-webhook-event-types", async () => {
  const actual = await vi.importActual<
    typeof import("@/hooks/webhooks/use-webhook-event-types")
  >("@/hooks/webhooks/use-webhook-event-types")
  return {
    ...actual,
    useWebhookEventTypes: vi.fn(() => hookReturnValue),
  }
})

describe("WebhookEventTypesManager — smoke (P0.G #4)", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test("renders Manager card title + lista de event types", () => {
    render(
      <WebhookEventTypesManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(screen.getByText("Gerenciador de Webhook Events")).toBeInTheDocument()
    expect(screen.getByText("Candidato criado (webhook)")).toBeInTheDocument()
    expect(screen.getByText("Event meu")).toBeInTheDocument()
    expect(screen.getByText("Event alheio")).toBeInTheDocument()
  })

  test("filter chips: clicar 'Master canonical' filtra só masters", () => {
    render(
      <WebhookEventTypesManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(screen.getByText("Event meu")).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /Master canonical/i }))

    expect(screen.getByText("Candidato criado (webhook)")).toBeInTheDocument()
    expect(screen.queryByText("Event meu")).not.toBeInTheDocument()
    expect(screen.queryByText("Event alheio")).not.toBeInTheDocument()
  })

  test("startCreate: clicar 'Novo event' abre form de criação", () => {
    render(
      <WebhookEventTypesManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(screen.queryByText("Criar event type")).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /Novo event/i }))

    expect(screen.getByText("Criar event type")).toBeInTheDocument()
  })

  test("permission gate: isAdmin=false + currentUserId=null esconde edit/delete em customs alheios", () => {
    render(
      <WebhookEventTypesManager isAdmin={false} currentUserId={null} />,
    )

    // Event alheio (created_by = "user-other"): sem edit/delete
    const foreignRow = screen
      .getByText("Event alheio")
      .closest("div.flex.items-start")
    expect(foreignRow).not.toBeNull()
    const foreignButtons = within(foreignRow as HTMLElement).queryAllByRole("button")
    expect(foreignButtons.length).toBe(0)

    // Master: aparece apenas botão "Customizar"
    const masterRow = screen
      .getByText("Candidato criado (webhook)")
      .closest("div.flex.items-start")
    const masterButtons = within(masterRow as HTMLElement).queryAllByRole("button")
    expect(masterButtons.length).toBe(1)
    expect(masterButtons[0]).toHaveAttribute("title", "Customizar")
  })
})
