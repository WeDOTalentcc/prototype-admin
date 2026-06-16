"use client"

import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  Plus, CheckCircle, Edit, Eye
} from"lucide-react"
import { onboardingTemplates } from"./onboarding-page.types"

export function OnboardingTemplates() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xs font-medium text-lia-text-primary">Modelos de Integração</h3>
          <p className="text-sm text-lia-text-secondary">Configure fluxos automatizados por departamento</p>
        </div>
        <Button className="gap-2">
          <Plus className="w-4 h-4" />
          Novo Modelo
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {onboardingTemplates.map(template => (
          <Card key={template.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xs">{template.name}</CardTitle>
                  <p className="text-sm text-lia-text-primary mt-1">{template.description}</p>
                </div>
                <Chip variant="neutral" muted>
                  {template.isActive ? 'Ativo' : 'Inativo'}
                </Chip>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-lia-text-secondary">Departamento</p>
                    <p className="text-sm text-lia-text-primary">{template.department}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-lia-text-secondary">Duração</p>
                    <p className="text-sm text-lia-text-primary">{template.duration} dias</p>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium text-lia-text-secondary mb-2">Tarefas ({template.tasks.length})</p>
                  <div className="space-y-2">
                    {template.tasks.slice(0, 3).map(task => (
                      <div key={task.id} className="flex items-center gap-2 text-sm">
                        <CheckCircle className={`w-4 h-4 ${task.isCompleted ? 'text-status-success' : 'text-lia-text-secondary'}`} />
                        <span className="text-lia-text-primary">{task.title}</span>
                        <Chip density="relaxed" variant="neutral" >
                          {task.type === 'document' ? 'Doc' :
                           task.type === 'meeting' ? 'Reunião' :
                           task.type === 'training' ? 'Treinamento' :
                           task.type === 'system_access' ? 'Sistema' :
                           task.type === 'equipment' ? 'Equipamento' : 'Outro'}
                        </Chip>
                      </div>
                    ))}
                    {template.tasks.length > 3 && (
                      <p className="text-xs text-lia-text-primary">+{template.tasks.length - 3} tarefas adicionais</p>
                    )}
                  </div>
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
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
