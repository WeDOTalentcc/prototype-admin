/**
 * Webhook types — mirror backend schemas.
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
