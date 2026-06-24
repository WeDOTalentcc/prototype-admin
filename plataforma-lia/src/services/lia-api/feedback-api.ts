/**
 * LIA chat feedback HTTP client.
 *
 * Audit #569 (F2): the previous version masked every error as
 * `{ feedback_id: '', status: 'error' }`, so callers could not distinguish a
 * 404 (endpoint not registered) from a 500 (DB outage) from a network blip.
 * This rewrite throws `HttpError` on non-2xx; callers must `try/catch` and
 * surface failures to the user (toast + revert optimistic UI).
 */
import { BACKEND_URL, HttpError } from './base'
import type {
  ThumbsFeedbackResponse,
  RatingFeedbackResponse,
  CorrectionFeedbackResponse,
  FeedbackMetrics,
} from './types'

export interface MessageContextPayload {
  user_message?: string
  lia_response?: string
  intent?: string
  stage?: string
  response_time_ms?: number
  tools_used?: string[]
  confidence_score?: number
}

export interface MessageFeedbackEntry {
  message_id: string
  thumbs: 'up' | 'down' | null
  rating: number | null
  feedback_text: string | null
  /** Audit #570 fix: thumbs-down free text is persisted to `correction`
   *  to drive the learning-pattern signal. Hydration must read both. */
  correction: string | null
}

export interface RegenerateResponseDTO {
  user_message: string
  prior_message_id: string | null
  regenerate_of: string
  status: string
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    let detail = ''
    try {
      detail = await response.text()
    } catch {
      // best effort
    }
    throw new HttpError(
      response.status,
      `Feedback request failed: ${response.status} ${response.statusText}`,
      { body: detail },
    )
  }
  return response.json() as Promise<T>
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  })
  if (!response.ok) {
    let detail = ''
    try {
      detail = await response.text()
    } catch {
      // best effort
    }
    throw new HttpError(
      response.status,
      `Feedback request failed: ${response.status} ${response.statusText}`,
      { body: detail },
    )
  }
  return response.json() as Promise<T>
}

export async function submitThumbsFeedback(
  sessionId: string,
  messageId: string,
  thumbs: 'up' | 'down',
  opts: { feedbackText?: string; category?: string; messageContext?: MessageContextPayload } = {},
): Promise<ThumbsFeedbackResponse> {
  return postJson<ThumbsFeedbackResponse>('/lia/feedback/thumbs', {
    session_id: sessionId,
    message_id: messageId,
    thumbs,
    feedback_text: opts.feedbackText,
    category: opts.category,
    message_context: opts.messageContext,
  })
}

export async function submitRatingFeedback(
  sessionId: string,
  messageId: string,
  rating: number,
  feedbackText?: string,
  category?: string,
): Promise<RatingFeedbackResponse> {
  return postJson<RatingFeedbackResponse>('/lia/feedback/rating', {
    session_id: sessionId,
    message_id: messageId,
    rating,
    feedback_text: feedbackText,
    category,
  })
}

export async function submitCorrectionFeedback(
  sessionId: string,
  messageId: string,
  originalResponse: string,
  correction: string,
): Promise<CorrectionFeedbackResponse> {
  return postJson<CorrectionFeedbackResponse>('/lia/feedback/correction', {
    session_id: sessionId,
    message_id: messageId,
    original_response: originalResponse,
    correction,
  })
}

/**
 * Audit #570 P1: ask the backend to mark an assistant message as superseded
 * and return the prior user message text so the chat can re-invoke the
 * pipeline with `regenerate_of=<oldId>`. Centralizing this on the server
 * (instead of the client guessing the prior message) keeps the ownership
 * check in one place and keeps analytics able to distinguish a regenerated
 * turn from an organic one.
 */
export async function requestRegeneration(
  sessionId: string,
  messageId: string,
): Promise<RegenerateResponseDTO> {
  return postJson<RegenerateResponseDTO>('/lia/feedback/regenerate', {
    session_id: sessionId,
    message_id: messageId,
  })
}

export interface ImplicitSignalAck {
  persisted: boolean
  signal_type: string
  signal_id: string | null
  skipped_reason: string | null
}

/**
 * Task #1299: report a frontend-detected IMPLICIT feedback signal.
 *
 * Only `correction_delta` (recruiter edited a LIA suggestion before sending)
 * and `abandonment` (recruiter ignored a substantive answer and switched
 * topic) flow through here — `regeneration` is captured server-side in the
 * `/regenerate` endpoint. The backend is the gatekeeper: it re-applies the
 * FairnessGuard gate and the conservative abandonment criterion, so a
 * `{ persisted: false, skipped_reason }` reply is a NORMAL, non-error outcome.
 * `company_id`/`user_id` are derived from the JWT, never the body.
 */
export async function reportImplicitSignal(
  signalType: 'correction_delta' | 'abandonment',
  args: {
    sessionId: string
    messageId: string
    originalResponse?: string
    usedText?: string
    abandonedResponse?: string
    nextUserMessage?: string
    messageContext?: MessageContextPayload
  },
): Promise<ImplicitSignalAck> {
  return postJson<ImplicitSignalAck>('/lia/feedback/implicit', {
    session_id: args.sessionId,
    message_id: args.messageId,
    signal_type: signalType,
    original_response: args.originalResponse,
    used_text: args.usedText,
    abandoned_response: args.abandonedResponse,
    next_user_message: args.nextUserMessage,
    message_context: args.messageContext,
  })
}

export async function getFeedbackMetrics(days?: number): Promise<FeedbackMetrics> {
  const params = days ? `?days=${days}` : ''
  return getJson<FeedbackMetrics>(`/lia/feedback/metrics${params}`)
}

/**
 * Hydrate per-message feedback state for a conversation.
 * Returns the latest feedback row per message_id (last-write-wins) — used by
 * the chat UI to restore thumbs after a refresh (audit gap F3).
 */
export async function getConversationFeedback(
  sessionId: string,
): Promise<MessageFeedbackEntry[]> {
  const data = await getJson<{ items: MessageFeedbackEntry[] }>(
    `/lia/feedback/by-conversation/${encodeURIComponent(sessionId)}`,
  )
  return data.items ?? []
}
