"use client"

import React, { use, useState, useEffect, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Plug,
  Bell,
  CheckCircle2,
  XCircle,
  Clock,
  Settings,
  RefreshCw,
  Loader2
} from "lucide-react"

interface Integration {
  id: string
  name: string
  description: string
  status: 'connected' | 'disconnected' | 'pending'
  last_sync: string | null
  config?: Record<string, unknown>
  created_at: string
  updated_at: string
}

const INTEGRATION_LABELS: Record<string, { label: string; description: string }> = {
  gupy: { label: 'Gupy', description: 'ATS para gestão de candidatos' },
  linkedin: { label: 'LinkedIn Recruiter', description: 'Busca e importação de candidatos' },
  greenhouse: { label: 'Greenhouse', description: 'Sistema de rastreamento de candidatos' },
  slack: { label: 'Slack', description: 'Notificações e alertas' },
  whatsapp: { label: 'WhatsApp Business', description: 'Comunicação com candidatos' },
  email: { label: 'Email SMTP', description: 'Envio de emails transacionais' }
}

export default function ClientIntegracoesPage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchIntegrations = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/integrations`)
      
      if (!response.ok) {
        throw new Error('Erro ao carregar integrações')
      }
      
      const data = await response.json()
      if (data.success && data.data?.integrations) {
        setIntegrations(data.data.integrations)
      } else {
        setIntegrations([])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido')
    } finally {
      setLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchIntegrations()
  }, [fetchIntegrations])

  const handleSyncAll = async () => {
    try {
      setSyncing(true)
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/integrations/sync-all`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error('Erro ao sincronizar integrações')
      }
      
      await fetchIntegrations()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao sincronizar')
    } finally {
      setSyncing(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'connected':
        return <Badge variant="success">Conectado</Badge>
      case 'disconnected':
        return <Badge variant="destructive">Desconectado</Badge>
      case 'pending':
        return <Badge variant="warning">Pendente</Badge>
      default:
        return <Badge variant="default">{status}</Badge>
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle2 className="w-5 h-5 text-status-success" />
      case 'disconnected':
        return <XCircle className="w-5 h-5 text-status-error" />
      case 'pending':
        return <Clock className="w-5 h-5 text-status-warning" />
      default:
        return null
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Nunca'
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateStr
    }
  }

  const getIntegrationLabel = (name: string) => {
    return INTEGRATION_LABELS[name]?.label || name
  }

  const getIntegrationDescription = (integration: Integration) => {
    return integration.description || INTEGRATION_LABELS[integration.name]?.description || ''
  }

  const connectedCount = integrations.filter(i => i.status === 'connected').length
  const pendingCount = integrations.filter(i => i.status === 'pending').length
  const disconnectedCount = integrations.filter(i => i.status === 'disconnected').length

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="flex flex-col items-center gap-3" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none lia-text-600 dark:text-lia-text-tertiary" />
          <p className="text-sm lia-text-400 dark:lia-text-500">
            Carregando integrações...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Plug className="w-6 h-6 lia-text-600 dark:text-lia-text-tertiary" />
            <h2 
              className="text-lg font-semibold lia-text-800 dark:text-lia-text-primary"
            >
              Integrações
            </h2>
          </div>
          <p className="text-sm lia-text-400 dark:lia-text-500">
            Conexões com sistemas externos
          </p>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={handleSyncAll}
          disabled={syncing || connectedCount === 0}
        >
          {syncing ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          Sincronizar Todas
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
                Estas integrações são específicas para este cliente.
                Todas as chamadas de API utilizarão o header X-Company-ID: {clientId}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-status-error/30 bg-status-error/10/50 dark:border-status-error/30 dark:bg-status-error/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <XCircle className="w-5 h-5 text-status-error" />
              <p className="text-sm text-status-error dark:text-status-error">{error}</p>
              <Button variant="ghost" size="sm" onClick={fetchIntegrations}>
                Tentar novamente
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-status-success">{connectedCount}</p>
            <p className="text-sm lia-text-400 dark:lia-text-500">
              Conectadas
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-status-warning">{pendingCount}</p>
            <p className="text-sm lia-text-400 dark:lia-text-500">
              Pendentes
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-status-error">{disconnectedCount}</p>
            <p className="text-sm lia-text-400 dark:lia-text-500">
              Desconectadas
            </p>
          </CardContent>
        </Card>
      </div>

      {integrations.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Plug className="w-12 h-12 mx-auto mb-4 lia-text-300" />
            <p className="text-lg font-medium lia-text-800 dark:text-lia-text-primary">
              Nenhuma integração configurada
            </p>
            <p className="text-sm mt-2 lia-text-400 dark:lia-text-500">
              Este cliente ainda não possui integrações configuradas.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {integrations.map((integration) => (
            <Card 
              key={integration.id}
              className="hover:border-gray-900 dark:hover:border-gray-50 transition-colors motion-reduce:transition-none"
            >
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-md bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center shrink-0">
                    <Plug className="w-6 h-6 lia-text-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 
                        className="font-medium lia-text-800 dark:text-lia-text-primary"
                      >
                        {getIntegrationLabel(integration.name)}
                      </h3>
                      {getStatusBadge(integration.status)}
                    </div>
                    <p 
                      className="text-sm lia-text-400 dark:lia-text-500"
                    >
                      {getIntegrationDescription(integration)}
                    </p>
                    <p 
                      className="text-xs mt-1 lia-text-400 dark:lia-text-500"
                    >
                      Última sincronização: {formatDate(integration.last_sync)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(integration.status)}
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
