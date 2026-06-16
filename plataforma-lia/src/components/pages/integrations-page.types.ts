import React from "react"

export interface Integration {
  id: string
  name: string
  type: 'teams' | 'discord' | 'email'
  status: 'active' | 'inactive' | 'error'
  icon: React.ElementType
  color: string
  webhookUrl: string
  channels: string[]
  events: string[]
  lastActivity: string
  messagesCount: number
  errorCount: number
  createdAt: string
  createdBy: string
}

export interface NotificationTemplate {
  id: string
  name: string
  event: string
  title: string
  message: string
  mentions: string[]
  active: boolean
  integrations: string[]
}

export interface WebhookEvent {
  id: string
  integration: string
  event: string
  status: 'success' | 'failed' | 'pending'
  timestamp: string
  payload: Record<string, unknown>
  response?: Record<string, unknown>
  error?: string
}

export interface NewIntegrationForm {
  name: string
  type: 'teams'
  webhookUrl: string
  channels: string[]
  events: string[]
}

export interface AvailableEvent {
  id: string
  label: string
  icon: React.ElementType
  description: string
}
