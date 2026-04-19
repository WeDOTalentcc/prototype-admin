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
