/**
 * Webhook types — mirror backend schemas.
 *
 * @deprecated 2026-05-21 (Sprint 5 catalogos dinamicos) — WEBHOOK_EVENTS
 * hardcoded array foi substituido por catalogo dinamico per-tenant via
 * `useWebhookEventTypes()` hook em `@/hooks/webhooks/use-webhook-event-types`.
 *
 * Mantemos a array hardcoded como FALLBACK para uso emergencial caso o
 * backend esteja indisponivel (o hook lida com erro mas a UI precisa de
 * um set minimo de eventos pra renderizar). Refactor canonical migrou
 * `WebhooksManager.tsx` para o hook dinamico. Outros consumers devem migrar
 * incrementalmente.
 *
 * Para novos eventos: NAO adicione aqui — adicione no master canonical via
 * migration alembic (vide `alembic/versions/157_webhook_event_types.py`).
 */

export const WEBHOOK_EVENTS = [
  "agent.execution.completed",
  "agent.execution.failed",
  "agent.deployment.created",
  "agent.deployment.paused",
  "agent.approval.requested",
  "agent.approval.reviewed",
] as const

export type WebhookEvent = typeof WEBHOOK_EVENTS[number]

export interface Webhook {
  id: string
  company_id: string
  name: string
  url: string
  events: string[]
  is_active: boolean
  total_deliveries: number
  total_failures: number
  last_delivery_at: string | null
  last_status_code: number | null
  last_error: string | null
  created_by: string
  created_at: string | null
  secret?: string  // present only on create response
}
