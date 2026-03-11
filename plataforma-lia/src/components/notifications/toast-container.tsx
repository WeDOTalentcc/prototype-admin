'use client'

import React from 'react'
import { useNotifications } from './notification-context'
import { Toast } from './toast'

export function ToastContainer() {
  const { notifications } = useNotifications()

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm w-full pointer-events-none">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className="pointer-events-auto"
        >
          <Toast notification={notification} />
        </div>
      ))}
    </div>
  )
}
