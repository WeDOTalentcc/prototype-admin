/**
 * Webhook types — mirror backend schemas.
 *
 * Sprint 5 catalogos dinamicos (2026-05-21): WEBHOOK_EVENTS constant array
 * removida. Catalogo de events canonical agora vive per-tenant no DB
 * (`webhook_event_types`) e e consumido via hook `useWebhookEventTypes()`
 * em `@/hooks/webhooks/use-webhook-event-types`.
 *
 * Este arquivo passa a conter APENAS o interface `Webhook` (shape do
 * recurso studio_webhooks) usado por `useWebhooks()` + `WebhooksManager`.
 *
 * Para novos eventos: NAO adicione constants aqui — adicione no master
 * canonical via migration alembic (vide `alembic/versions/157_webhook_event_types.py`)
 * ou crie custom event type via wizard (tool `create_custom_webhook_event_type`).
 */

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
