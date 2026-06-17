import { useState, useCallback } from 'react'

export interface EmptyFieldAction {
  action: string
  label: string
  description: string
}

export interface EmptyFieldNotification {
  field_key: string
  field_label: string
  impact_description: string
  has_fallback: boolean
  fallback_strategies: string[]
  times_reminded: number
  actions: EmptyFieldAction[]
}

export interface EmptyFieldsResponse {
  company_id: string
  user_id: string
  notifications: EmptyFieldNotification[]
  total_empty_fields: number
}

export interface ReminderPreferenceResponse {
  field_key: string
  action: string
  remind_me: boolean
  snooze_until: string | null
  times_reminded: number
  times_filled_with_lia: number
}

export interface FieldValueSuggestion {
  field_key: string
  field_label: string
  suggested_value: unknown
  source: string
  source_icon: string
  source_explanation: string
  confidence: number
  formatted_value: string
}

interface UseEmptyFieldNotificationsReturn {
  notifications: EmptyFieldNotification[]
  isLoading: boolean
  error: string | null
  hasPendingNotifications: boolean
  currentNotification: EmptyFieldNotification | null
  fetchNotifications: (companyId: string) => Promise<void>
  handleAction: (companyId: string, fieldKey: string, action: string) => Promise<ReminderPreferenceResponse | null>
  getSuggestion: (companyId: string, fieldKey: string, jobContext?: Record<string, unknown>) => Promise<FieldValueSuggestion | null>
  dismissCurrentNotification: () => void
  clearNotifications: () => void
}

export function useEmptyFieldNotifications(): UseEmptyFieldNotificationsReturn {
  const [notifications, setNotifications] = useState<EmptyFieldNotification[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentIndex, setCurrentIndex] = useState(0)

  const fetchNotifications = useCallback(async (companyId: string) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/backend-proxy/lia-field-toggles/${companyId}/empty-fields`)
      
      if (!response.ok) {
        // On error, clear notifications to avoid blocking the user
        setNotifications([])
        setCurrentIndex(0)
        return
      }
      
      const data: EmptyFieldsResponse = await response.json()
      setNotifications(data.notifications)
      setCurrentIndex(0)
    } catch (err) {
      // On network error, don't block the user - just log and clear
      setError(null) // Don't show error to user, just proceed
      setNotifications([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleAction = useCallback(async (
    companyId: string, 
    fieldKey: string, 
    action: string
  ): Promise<ReminderPreferenceResponse | null> => {
    try {
      const response = await fetch(
        `/api/backend-proxy/lia-field-toggles/${companyId}/empty-fields/${fieldKey}/action`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action })
        }
      )
      
      if (!response.ok) {
        throw new Error('Falha ao processar ação')
      }
      
      const result: ReminderPreferenceResponse = await response.json()
      
      // For all actions, remove the notification from pending list
      // fill_now action is handled differently - user sees suggestion first
      // but notification is still removed so send button is not blocked
      setNotifications(prev => prev.filter(n => n.field_key !== fieldKey))
      
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao processar ação')
      return null
    }
  }, [])

  const getSuggestion = useCallback(async (
    companyId: string,
    fieldKey: string,
    jobContext?: Record<string, unknown>
  ): Promise<FieldValueSuggestion | null> => {
    try {
      const response = await fetch(
        `/api/backend-proxy/lia-field-toggles/${companyId}/empty-fields/${fieldKey}/suggest`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_context: jobContext || null })
        }
      )
      
      if (!response.ok) {
        throw new Error('Falha ao obter sugestão')
      }
      
      return await response.json()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao obter sugestão')
      return null
    }
  }, [])

  const dismissCurrentNotification = useCallback(() => {
    if (currentIndex < notifications.length - 1) {
      setCurrentIndex(prev => prev + 1)
    } else {
      setNotifications([])
      setCurrentIndex(0)
    }
  }, [currentIndex, notifications.length])

  const clearNotifications = useCallback(() => {
    setNotifications([])
    setCurrentIndex(0)
    setError(null)
  }, [])

  return {
    notifications,
    isLoading,
    error,
    hasPendingNotifications: notifications.length > 0,
    currentNotification: notifications[currentIndex] || null,
    fetchNotifications,
    handleAction,
    getSuggestion,
    dismissCurrentNotification,
    clearNotifications
  }
}
