"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Bell, Edit, Trash2, AlertCircle, CheckCircle,
  Hash, Webhook, RefreshCw, PlayCircle, PauseCircle, Clock
} from "lucide-react"
import type { Integration } from "./integrations-page.types"

interface IntegrationsListProps {
  integrations: Integration[]
  testingIntegration: string | null
  onTest: (id: string) => void
  onEdit: (integration: Integration) => void
  onToggleStatus: (id: string) => void
  onDelete: (id: string) => void
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'active': return <CheckCircle className="w-4 h-4 text-status-success" />
    case 'inactive': return <PauseCircle className="w-4 h-4 text-lia-text-secondary" />
    case 'error': return <AlertCircle className="w-4 h-4 text-status-error" />
    default: return <Clock className="w-4 h-4 text-status-warning" />
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case 'active': return 'bg-status-success/15 text-status-success border-status-success/30'
    case 'inactive': return 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle'
    case 'error': return 'bg-status-error/15 text-status-error border-status-error/30'
    default: return 'bg-status-warning/15 text-status-warning border-status-warning/30'
  }
}

export function IntegrationsList({
  integrations, testingIntegration, onTest, onEdit, onToggleStatus, onDelete
}: IntegrationsListProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Webhook className="w-5 h-5" />
          Integrações Configuradas
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {integrations.map((integration) => (
            <div key={integration.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-md flex items-center justify-center ${integration.color}`}>
                    <integration.icon className="w-6 h-6" />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lia-text-primary">
                        {integration.name}
                      </h3>
                      <Badge className={`${getStatusColor(integration.status)} text-xs`}>
                        {getStatusIcon(integration.status)}
                        <span className="ml-1 capitalize">{integration.status}</span>
                      </Badge>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center gap-4 text-sm text-lia-text-secondary">
                        <div className="flex items-center gap-1">
                          <Hash className="w-4 h-4" />
                          <span>{integration.channels.join(', ')}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Bell className="w-4 h-4" />
                          <span>{integration.events.length} eventos</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 text-sm text-lia-text-secondary">
                        <div>
                          <span className="font-medium text-status-success">{integration.messagesCount}</span> mensagens enviadas
                        </div>
                        <div>
                          <span className="font-medium text-status-error">{integration.errorCount}</span> erros
                        </div>
                        <div>
                          Última atividade: {new Date(integration.lastActivity).toLocaleDateString('pt-BR')}
                        </div>
                      </div>

                      <div className="text-xs text-lia-text-secondary">
                        Criado por {integration.createdBy} em {new Date(integration.createdAt).toLocaleDateString('pt-BR')}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onTest(integration.id)}
                    disabled={testingIntegration === integration.id}
                    className="gap-2"
                  >
                    {testingIntegration === integration.id ? (
                      <RefreshCw className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                    ) : (
                      <PlayCircle className="w-4 h-4" />
                    )}
                    Testar
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(integration)}
                    className="gap-2"
                  >
                    <Edit className="w-4 h-4" />
                    Editar
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onToggleStatus(integration.id)}
                    className="gap-2"
                  >
                    {integration.status === 'active' ? (
                      <PauseCircle className="w-4 h-4" />
                    ) : (
                      <PlayCircle className="w-4 h-4" />
                    )}
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(integration.id)}
                    className="gap-2 text-status-error hover:text-status-error"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
