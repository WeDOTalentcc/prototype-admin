"use client"

export interface Client {
  id: string
  name: string
  trading_name?: string
  cnpj: string
  logo_url?: string
  status: 'active' | 'trial' | 'suspended' | 'churned' | 'pending_setup'
  plan: string
  active_users: number
  user_limit: number
  start_date: string
  account_manager?: string
  email?: string
  phone?: string
}

export const statusConfig: Record<string, { label: string, variant: 'success' | 'warning' | 'destructive' | 'info' | 'default' }> = {
  active: { label: 'Ativo', variant: 'success' },
  trial: { label: 'Trial', variant: 'info' },
  suspended: { label: 'Suspenso', variant: 'warning' },
  churned: { label: 'Churned', variant: 'destructive' },
  pending_setup: { label: 'Pendente Setup', variant: 'default' },
}

export const statusOptions = [
  { value: 'all', label: 'Todos os Status' },
  { value: 'active', label: 'Ativo' },
  { value: 'trial', label: 'Trial' },
  { value: 'suspended', label: 'Suspenso' },
  { value: 'churned', label: 'Churned' },
  { value: 'pending_setup', label: 'Pendente Setup' },
]

export const planOptions = [
  { value: 'all', label: 'Todos os Planos' },
  { value: 'starter', label: 'Starter' },
  { value: 'professional', label: 'Professional' },
  { value: 'enterprise', label: 'Enterprise' },
  { value: 'custom', label: 'Custom' },
]
