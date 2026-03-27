"use client"

import React, { use, useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import {
  Zap,
  Bell,
  Plus,
  Mail,
  MessageSquare,
  Settings,
  Loader2,
  Webhook,
  BellRing
} from "lucide-react"

interface Automation {
  id: string
  name: string
  description: string
  trigger: string
  action: string
  is_active: boolean
  trigger_count: number
  config?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

export default function ClientAutomacoesPage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const [automations, setAutomations] = useState<Automation[]>([])
  const [loading, setLoading] = useState(true)
  const [togglingId, setTogglingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAutomations()
  }, [clientId])

  const fetchAutomations = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/automations`)
      
      if (!response.ok) {
        throw new Error('Erro ao buscar automações')
      }
      
      const result = await response.json()
      setAutomations(result.data?.automations || [])
    } catch (err) {
      console.error('Erro ao buscar automações:', err)
      setError('Erro ao carregar automações')
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = async (automationId: string) => {
    try {
      setTogglingId(automationId)
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/automations/${automationId}/toggle`, {
        method: 'PATCH'
      })
      
      if (!response.ok) {
        throw new Error('Erro ao alternar status')
      }
      
      const result = await response.json()
      
      setAutomations(prev => 
        prev.map(a => 
          a.id === automationId 
            ? { ...a, is_active: result.data?.is_active ?? !a.is_active }
            : a
        )
      )
    } catch (err) {
      console.error('Erro ao alternar automação:', err)
    } finally {
      setTogglingId(null)
    }
  }

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'send_email':
        return <Mail className="w-5 h-5 text-gray-600 dark:text-gray-400" />
      case 'send_whatsapp':
        return <MessageSquare className="w-5 h-5 text-status-success" />
      case 'send_notification':
        return <BellRing className="w-5 h-5 text-wedo-purple" />
      case 'webhook':
        return <Webhook className="w-5 h-5 text-wedo-orange" />
      default:
        return <Zap className="w-5 h-5 text-gray-600" />
    }
  }

  const getActionBgColor = (action: string) => {
    switch (action) {
      case 'send_email':
        return 'bg-gray-100 dark:bg-gray-800'
      case 'send_whatsapp':
        return 'bg-status-success/15 dark:bg-status-success/30'
      case 'send_notification':
        return 'bg-wedo-purple/15 dark:bg-wedo-purple/30'
      case 'webhook':
        return 'bg-wedo-orange/15 dark:bg-wedo-orange/30'
      default:
        return 'bg-gray-100 dark:bg-gray-900/30'
    }
  }

  const activeCount = automations.filter(a => a.is_active).length
  const totalExecutions = automations.reduce((acc, a) => acc + (a.trigger_count || 0), 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Zap className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            <h2 
              className="text-lg font-semibold"
              style={{ color: 'var(--eleven-text-primary)' }}
            >
              Automações
            </h2>
          </div>
          <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
            Regras automáticas de comunicação e ações
          </p>
        </div>
        <Button 
          size="sm"
          className="bg-gray-800"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nova Automação
        </Button>
      </div>

      <Card className="border-status-warning/30 bg-status-warning/10/50 dark:border-status-warning/30 dark:bg-status-warning/20">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Bell className="w-5 h-5 text-status-warning mt-0.5" />
            <div>
              <p className="text-sm font-medium text-status-warning dark:text-status-warning">
                Contexto do Cliente: {clientId}
              </p>
              <p className="text-xs text-status-warning dark:text-status-warning mt-1">
                Estas automações são específicas para este cliente.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-gray-900 dark:text-gray-50">
              {loading ? '-' : automations.length}
            </p>
            <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Total de Automações
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-status-success">
              {loading ? '-' : activeCount}
            </p>
            <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Ativas
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-wedo-purple">
              {loading ? '-' : totalExecutions}
            </p>
            <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Execuções
            </p>
          </CardContent>
        </Card>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-600 dark:text-gray-400" />
          <span className="ml-3 text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
            Carregando automações...
          </span>
        </div>
      ) : error ? (
        <Card className="border-status-error/30 bg-status-error/10/50 dark:border-status-error/30 dark:bg-status-error/20">
          <CardContent className="p-6 text-center">
            <p className="text-sm text-status-error dark:text-status-error">{error}</p>
            <Button 
              variant="outline" 
              size="sm" 
              className="mt-4"
              onClick={fetchAutomations}
            >
              Tentar novamente
            </Button>
          </CardContent>
        </Card>
      ) : automations.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Zap className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-200 mb-4" />
            <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>
              Nenhuma automação configurada
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Clique em "Nova Automação" para criar a primeira.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {automations.map((automation) => (
            <Card 
              key={automation.id}
              className={`hover:border-gray-900 dark:hover:border-gray-50 transition-colors ${!automation.is_active ? 'opacity-60' : ''}`}
            >
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-md flex items-center justify-center ${getActionBgColor(automation.action)}`}>
                    {getActionIcon(automation.action)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 
                        className="font-medium"
                        style={{ color: 'var(--eleven-text-primary)' }}
                      >
                        {automation.name}
                      </h3>
                      <Badge variant={automation.is_active ? 'success' : 'default'}>
                        {automation.is_active ? 'Ativa' : 'Inativa'}
                      </Badge>
                    </div>
                    <p 
                      className="text-sm"
                      style={{ color: 'var(--eleven-text-tertiary)' }}
                    >
                      {automation.description}
                    </p>
                  </div>
                  <div className="text-right mr-4">
                    <p className="text-lg font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                      {automation.trigger_count || 0}
                    </p>
                    <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      execuções
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={automation.is_active}
                      disabled={togglingId === automation.id}
                      onCheckedChange={() => handleToggle(automation.id)}
                    />
                    <Button variant="ghost" size="sm">
                      <Settings className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
