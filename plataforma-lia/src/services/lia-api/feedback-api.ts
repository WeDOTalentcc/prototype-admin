import { BACKEND_URL } from './base'
import type {
  ThumbsFeedbackResponse,
  RatingFeedbackResponse,
  CorrectionFeedbackResponse,
  FeedbackMetrics,
} from './types'

export async function submitThumbsFeedback(
  sessionId: string,
  messageId: string,
  thumbs: 'up' | 'down',
  userId?: string
): Promise<ThumbsFeedbackResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/feedback/thumbs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message_id: messageId,
        thumbs,
        user_id: userId || 'default_user'
      })
    })
    if (!response.ok) {
      return { feedback_id: '', status: 'error' }
    }
    return response.json()
  } catch {
    return { feedback_id: '', status: 'error' }
  }
}

export async function submitRatingFeedback(
  sessionId: string,
  messageId: string,
  rating: number,
  feedbackText?: string,
  category?: string
): Promise<RatingFeedbackResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/feedback/rating`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message_id: messageId,
        rating,
        feedback_text: feedbackText,
        category
      })
    })
    if (!response.ok) {
      return { feedback_id: '', status: 'error' }
    }
    return response.json()
  } catch {
    return { feedback_id: '', status: 'error' }
  }
}

export async function submitCorrectionFeedback(
  sessionId: string,
  messageId: string,
  originalResponse: string,
  correction: string
): Promise<CorrectionFeedbackResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/feedback/correction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message_id: messageId,
        original_response: originalResponse,
        correction
      })
    })
    if (!response.ok) {
      return { feedback_id: '', status: 'error' }
    }
    return response.json()
  } catch {
    return { feedback_id: '', status: 'error' }
  }
}

export async function getFeedbackMetrics(days?: number): Promise<FeedbackMetrics> {
  try {
    const params = days ? `?days=${days}` : ''
    const response = await fetch(`${BACKEND_URL}/lia/feedback/metrics${params}`, {
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      return { satisfaction_rate: 0, total_feedback: 0, rating_average: 0 }
    }
    return response.json()
  } catch {
    return { satisfaction_rate: 0, total_feedback: 0, rating_average: 0 }
  }
}
