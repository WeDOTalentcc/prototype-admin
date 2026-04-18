"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Plus, Edit, Eye, MessageCircle } from"lucide-react"
import type { NotificationTemplate } from"./integrations-page.types"

interface IntegrationsTemplatesProps {
  templates: NotificationTemplate[]
  onNewTemplate: () => void
  onEditTemplate: (template: NotificationTemplate) => void
}

export function IntegrationsTemplates({ templates, onNewTemplate, onEditTemplate }: IntegrationsTemplatesProps) {
  return (
    <Card className="mt-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5" />
            Templates de Notificação
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={onNewTemplate}
            className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Novo Modelo
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {templates.map((template) => (
            <div key={template.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-semibold text-lia-text-primary">
                      {template.name}
                    </h4>
                    <Chip variant="neutral" muted className="text-xs">
                      {template.active ? 'Ativo' : 'Inativo'}
                    </Chip>
                    <Chip variant="neutral" className="text-xs">
                      {template.event}
                    </Chip>
                  </div>

                  <p className="text-sm text-lia-text-secondary mb-2">
                    {template.title}
                  </p>

                  <div className="text-xs text-lia-text-secondary">
                    Usado em: {template.integrations.join(', ')}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEditTemplate(template)}
                    className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                  >
                    <Edit className="w-4 h-4" />
                    Editar
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    className="gap-2"
                  >
                    <Eye className="w-4 h-4" />
                    Preview
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
