import { BACKEND_URL, getAuthHeaders } from './base'
import type {
  NotificationsResponse,
  NotificationSummaryResponse,
  NotificationActionResponse,
  SendNotificationRequest,
  SendNotificationResponse,
  JobCreatedNotificationRequest,
  JobCreatedNotificationResponse,
} from './types'

export async function getNotifications(
  userId: string = 'default_user',
  unreadOnly: boolean = false,
  category?: string,
  limit: number = 50
): Promise<NotificationsResponse> {
  const params = new URLSearchParams()
  params.set('user_id', userId)
  params.set('limit', String(limit))
  if (unreadOnly) params.set('unread_only', 'true')
  if (category) params.set('category', category)

  try {
    const response = await fetch(`${BACKEND_URL}/notifications/?${params.toString()}`, {
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      return { success: false, data: { notifications: [], total: 0, unread_count: 0, urgent_count: 0, has_more: false } }
    }

    return response.json()
  } catch {
    return { success: false, data: { notifications: [], total: 0, unread_count: 0, urgent_count: 0, has_more: false } }
  }
}

export async function getNotificationSummary(userId: string = 'default_user'): Promise<NotificationSummaryResponse> {
  const response = await fetch(`${BACKEND_URL}/notifications/summary?user_id=${userId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch notification summary: ${response.statusText}`)
  }
  return response.json()
}

export async function getUnreadCount(userId: string = 'default_user'): Promise<{ success: boolean; data: { unread_count: number; urgent_count: number } }> {
  const response = await fetch(`${BACKEND_URL}/notifications/unread-count?user_id=${userId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch unread count: ${response.statusText}`)
  }
  return response.json()
}

export async function markNotificationAsRead(notificationId: string, userId: string = 'default_user'): Promise<NotificationActionResponse> {
  const response = await fetch(`${BACKEND_URL}/notifications/${notificationId}/read?user_id=${userId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to mark notification as read: ${response.statusText}`)
  }
  return response.json()
}

export async function markAllNotificationsAsRead(userId: string = 'default_user', category?: string): Promise<NotificationActionResponse> {
  const params = new URLSearchParams()
  params.set('user_id', userId)
  if (category) params.set('category', category)

  const response = await fetch(`${BACKEND_URL}/notifications/read-all?${params.toString()}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to mark all notifications as read: ${response.statusText}`)
  }
  return response.json()
}

export async function dismissNotification(notificationId: string, userId: string = 'default_user'): Promise<NotificationActionResponse> {
  const response = await fetch(`${BACKEND_URL}/notifications/${notificationId}/dismiss?user_id=${userId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to dismiss notification: ${response.statusText}`)
  }
  return response.json()
}

export async function sendNotification(request: SendNotificationRequest): Promise<SendNotificationResponse> {
  const response = await fetch(`${BACKEND_URL}/notifications/send`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to send notification')
  }
  return response.json()
}

export async function sendJobCreatedNotification(request: JobCreatedNotificationRequest): Promise<JobCreatedNotificationResponse> {
  const response = await fetch(`${BACKEND_URL}/notifications/job-created`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to send job created notification')
  }
  return response.json()
}
