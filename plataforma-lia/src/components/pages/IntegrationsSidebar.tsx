"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Bell, AlertCircle, CheckCircle, Clock, Activity } from "lucide-react"
import type { WebhookEvent } from "./integrations-page.types"
import { AVAILABLE_EVENTS } from "./useIntegrationsPage"

interface IntegrationsSidebarProps {
  showWebhookLogs: boolean
  filteredEvents: WebhookEvent[]
  filterStatus: string
  onFilterChange: (status: string) => void
}

export function IntegrationsSidebar({
  showWebhookLogs, filteredEvents, filterStatus, onFilterChange
}: IntegrationsSidebarProps) {
  return (
    <div className="col-span-4">
      {showWebhookLogs && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <Activity className="w-4 h-4" />
                Logs de Webhook
              </CardTitle>
              <select
                value={filterStatus}
                onChange={(e) => onFilterChange(e.target.value)}
                className="text-xs border rounded-md px-2 py-1"
              >
                <option value="all">Todos</option>
                <option value="success">Sucesso</option>
                <option value="failed">Falha</option>
                <option value="pending">Pendente</option>
              </select>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {filteredEvents.map((event) => (
                <div key={event.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {event.status === 'success' && <CheckCircle className="w-4 h-4 text-status-success" />}
                      {event.status === 'failed' && <AlertCircle className="w-4 h-4 text-status-error" />}
                      {event.status === 'pending' && <Clock className="w-4 h-4 text-status-warning" />}
                      <span className="text-sm font-medium text-lia-text-primary">
                        {event.event}
                      </span>
                    </div>
                    <span className="text-xs text-lia-text-secondary">
                      {new Date(event.timestamp).toLocaleTimeString('pt-BR')}
                    </span>
                  </div>

                  <p className="text-xs text-lia-text-secondary mb-1">
                    {event.integration}
                  </p>

                  {event.error && (
                    <p className="text-xs text-status-error bg-status-error/10 dark:bg-status-error/20 p-2 rounded-md">
                      {event.error}
                    </p>
                  )}

                  {event.response && (
                    <p className="text-xs text-status-success bg-status-success/10 dark:bg-status-success/20 p-2 rounded-md">
                      ✓ Enviado com sucesso
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card className={showWebhookLogs ? "mt-6" : ""}>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Bell className="w-4 h-4" />
            Eventos Disponíveis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {AVAILABLE_EVENTS.map((event) => (
              <div key={event.id} className="flex items-start gap-3 p-2 rounded-xl hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover">
                <event.icon className="w-4 h-4 text-lia-text-secondary mt-0.5" />
                <div>
                  <h5 className="text-sm font-medium text-lia-text-primary">
                    {event.label}
                  </h5>
                  <p className="text-xs text-lia-text-secondary">
                    {event.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
