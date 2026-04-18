"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Plus, Edit, Eye, MoreHorizontal, Copy } from"lucide-react"
import { messageTemplates } from"./onboarding-premium-types"

export function OnboardingTemplatesView() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xs font-medium text-lia-text-primary">Modelos de Comunicação</h3>
          <p className="text-sm text-lia-text-secondary">Personalize mensagens automáticas para cada etapa</p>
        </div>
        <Button className="gap-2">
          <Plus className="w-4 h-4" />
          Novo Modelo
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {messageTemplates.map(template => (
          <Card key={template.id} className="hover:transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">{template.name}</CardTitle>
                  <Chip variant="neutral" className="mt-1">
                    {template.type === 'email' ? '📧 Email' :
                     template.type === 'whatsapp' ? '📱 WhatsApp' :
                     template.type === 'sms' ? '💬 SMS' : '📞 Ligação'}
                  </Chip>
                </div>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <MoreHorizontal className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {template.subject && (
                  <div>
                    <p className="text-sm font-medium text-lia-text-secondary">Assunto:</p>
                    <p className="text-sm text-lia-text-primary">{template.subject}</p>
                  </div>
                )}

                <div>
                  <p className="text-sm font-medium text-lia-text-secondary">Conteúdo:</p>
                  <p className="text-sm text-lia-text-primary line-clamp-4">
                    {template.content}
                  </p>
                </div>

                <div className="flex gap-2">
                  <Button size="sm" variant="outline" className="flex-1 gap-2">
                    <Edit className="w-4 h-4" />
                    Editar
                  </Button>
                  <Button size="sm" variant="outline" className="gap-2">
                    <Eye className="w-4 h-4" />
                    Visualizar
                  </Button>
                  <Button size="sm" variant="outline" className="gap-2">
                    <Copy className="w-4 h-4" />
                    Duplicar
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
