'use client'

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  duration?: number
  timestamp: Date
  actions?: Array<{
    label: string
    action: () => void
    variant?: 'primary' | 'secondary'
  }>
  realTime?: boolean
}

interface NotificationContextType {
  notifications: Notification[]
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void
  removeNotification: (id: string) => void
  clearAll: () => void
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider')
  }
  return context
}

interface NotificationProviderProps {
  children: React.ReactNode
}

export function NotificationProvider({ children }: NotificationProviderProps) {
  const [notifications, setNotifications] = useState<Notification[]>([])

  const addNotification = useCallback((notificationData: Omit<Notification, 'id' | 'timestamp'>) => {
    const id = Math.random().toString(36).substr(2, 9)
    const notification: Notification = {
      ...notificationData,
      id,
      timestamp: new Date(),
      duration: notificationData.duration || 5000
    }

    setNotifications(prev => [notification, ...prev])

    // Também adicionar ao feed de atividades da LIA
    const liaActivityEvent = new CustomEvent('lia-notification', {
      detail: {
        title: notification.title,
        message: notification.message,
        type: notification.type,
        timestamp: notification.timestamp
      }
    })
    window.dispatchEvent(liaActivityEvent)

    // Auto remove após duration
    if (notification.duration && notification.duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, notification.duration)
    }
  }, [])

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }, [])

  const clearAll = useCallback(() => {
    setNotifications([])
  }, [])

  // Simular notificações em tempo real
  useEffect(() => {
    const realTimeNotifications = [
      {
        type: 'info' as const,
        title: 'Nova Candidatura',
        message: 'Maria Silva se candidatou para Desenvolvedor Frontend',
        realTime: true
      },
      {
        type: 'success' as const,
        title: 'Entrevista Agendada',
        message: 'João Santos confirmou entrevista para amanhã às 14h',
        realTime: true
      },
      {
        type: 'warning' as const,
        title: 'Vaga Expirando',
        message: 'A vaga "Designer UX" expira em 2 dias',
        realTime: true
      },
      {
        type: 'info' as const,
        title: 'LIA Processou Currículo',
        message: 'Análise automática de 5 novos currículos concluída',
        realTime: true
      },
      {
        type: 'success' as const,
        title: 'Match Perfeito',
        message: 'LIA encontrou candidato ideal para "Product Manager"',
        realTime: true
      }
    ]

    const intervals: NodeJS.Timeout[] = []

    // Primeira notificação após 3 segundos
    const firstTimeout = setTimeout(() => {
      addNotification(realTimeNotifications[0])
    }, 3000)

    // Notificações subsequentes a cada 15-30 segundos
    realTimeNotifications.slice(1).forEach((notification, index) => {
      const delay = 8000 + (index * 12000) + Math.random() * 8000
      const timeout = setTimeout(() => {
        addNotification(notification)
      }, delay)
      intervals.push(timeout)
    })

    return () => {
      clearTimeout(firstTimeout)
      intervals.forEach(clearTimeout)
    }
  }, [addNotification])

  return (
    <NotificationContext.Provider value={{
      notifications,
      addNotification,
      removeNotification,
      clearAll
    }}>
      {children}
    </NotificationContext.Provider>
  )
}
