"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { CheckCircle, MessageCircle, FileText, BarChart3 } from "lucide-react"
import type { Integration, NotificationTemplate, WebhookEvent } from "./integrations-page.types"

interface IntegrationsStatsCardsProps {
  integrations: Integration[]
  templates: NotificationTemplate[]
  webhookEvents: WebhookEvent[]
}

export function IntegrationsStatsCards({ integrations, templates, webhookEvents }: IntegrationsStatsCardsProps) {
  return (
    <div className="grid grid-cols-4 gap-6 mb-8">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-lia-text-secondary">
                Integrações Ativas
              </p>
              <p className="text-2xl font-bold text-lia-text-primary">
                {integrations.filter(i => i.status === 'active').length}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-status-success" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-lia-text-secondary">
                Mensagens Enviadas
              </p>
              <p className="text-2xl font-bold text-lia-text-primary">
                {integrations.reduce((acc, i) => acc + i.messagesCount, 0)}
              </p>
            </div>
            <MessageCircle className="w-8 h-8 text-lia-text-secondary" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-lia-text-secondary">
                Templates Ativos
              </p>
              <p className="text-2xl font-bold text-lia-text-primary">
                {templates.filter(t => t.active).length}
              </p>
            </div>
            <FileText className="w-8 h-8 text-wedo-purple" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-lia-text-secondary">
                Taxa de Sucesso
              </p>
              <p className="text-2xl font-bold text-lia-text-primary">
                {Math.round(((webhookEvents.filter(e => e.status === 'success').length / webhookEvents.length) * 100) || 0)}%
              </p>
            </div>
            <BarChart3 className="w-8 h-8 text-wedo-orange" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
