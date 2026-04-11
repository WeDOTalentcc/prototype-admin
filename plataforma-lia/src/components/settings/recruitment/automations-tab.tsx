"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { hasModuleAccess } from "@/utils/license-manager"
import { ModuleUpsell } from "@/components/module-access/module-upsell"
import {
  Edit, Plus, Workflow, FileText, Zap, Target,
  Download, BarChart3, Activity, MoreHorizontal,
} from "lucide-react"

export function AutomationsTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [selectedView, setSelectedView] = useState<'overview' | 'builder' | 'templates' | 'logs'>('overview')
  const [workflows, setWorkflows] = useState([
    {
      id: '1',
      name: 'Triagem Automática de Candidatos',
      description: 'Workflow para triagem inicial baseada em critérios pré-definidos',
      status: 'active',
      trigger: 'Novo candidato',
      actions: 5,
      lastRun: '2024-01-20T14:30:00Z',
      executions: 156,
      successRate: 98
    },
    {
      id: '2',
      name: 'Notificação de Entrevistas',
      description: 'Envio automático de lembretes para candidatos e entrevistadores',
      status: 'active',
      trigger: 'Entrevista agendada',
      actions: 3,
      lastRun: '2024-01-20T12:15:00Z',
      executions: 89,
      successRate: 100
    },
    {
      id: '3',
      name: 'Follow-up Pós-entrevista',
      description: 'Coleta automática de feedback e próximos passos',
      status: 'paused',
      trigger: 'Entrevista concluída',
      actions: 4,
      lastRun: '2024-01-19T16:20:00Z',
      executions: 67,
      successRate: 94
    }
  ])

  if (!hasModuleAccess('workflow_automation')) {
    return (
      <ModuleUpsell
        moduleId="workflow_automation"
        title="Automação Avançada de Workflows"
        description="Workflow builder visual com automações inteligentes e templates pré-configurados"
      />
    )
  }

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-primary">Workflows Ativos</p>
                <p className="text-2xl font-semibold text-status-success">
                  {workflows.filter(w => w.status === 'active').length}
                </p>
                <p className="text-xs text-lia-text-primary">de {workflows.length} total</p>
              </div>
              <div className="w-10 h-10 bg-status-success/15 rounded-md flex items-center justify-center">
                <Workflow className="w-5 h-5 text-status-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-primary">Execuções Hoje</p>
                <p className="text-2xl font-semibold text-lia-text-primary">47</p>
                <p className="text-xs text-status-success">+12% vs ontem</p>
              </div>
              <div className="w-10 h-10 bg-wedo-cyan/15 rounded-md flex items-center justify-center">
                <Zap className="w-5 h-5 text-lia-text-secondary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-primary">Taxa de Sucesso</p>
                <p className="text-2xl font-semibold text-wedo-orange">97.3%</p>
                <p className="text-xs text-lia-text-primary">últimos 7 dias</p>
              </div>
              <div className="w-10 h-10 bg-wedo-orange/15 rounded-md flex items-center justify-center">
                <Target className="w-5 h-5 text-wedo-orange" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-primary">Templates</p>
                <p className="text-2xl font-semibold text-wedo-purple">12</p>
                <p className="text-xs text-lia-text-primary">pré-configurados</p>
              </div>
              <div className="w-10 h-10 bg-wedo-purple/15 rounded-md flex items-center justify-center">
                <FileText className="w-5 h-5 text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Workflows Configurados</span>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              Novo Workflow
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {workflows.map((workflow) => (
              <div key={workflow.id} className="flex items-center justify-between p-4 border border-lia-border-subtle rounded-xl hover:transition-shadow">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
                    workflow.status === 'active' ? 'bg-status-success/15' : 'bg-lia-bg-tertiary'
                  }`}>
                    <Workflow className={`w-5 h-5 ${
                      workflow.status === 'active' ? 'text-status-success' : 'text-lia-text-primary'
                    }`} />
                  </div>
                  <div>
                    <h4 className="font-medium text-lia-text-primary">{workflow.name}</h4>
                    <p className="text-sm text-lia-text-primary">{workflow.description}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-lia-text-primary">
                      <span>Trigger: {workflow.trigger}</span>
                      <span>•</span>
                      <span>{workflow.actions} ações</span>
                      <span>•</span>
                      <span>{workflow.executions} execuções</span>
                      <span>•</span>
                      <span className="text-status-success">{workflow.successRate}% sucesso</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant={workflow.status === 'active' ? 'default' : 'secondary'}>
                    {workflow.status === 'active' ? 'Ativo' : 'Pausado'}
                  </Badge>
                  <Button variant="outline" size="sm">
                    <Edit className="w-4 h-4 mr-2" />
                    Editar
                  </Button>
                  <Button variant="ghost" size="sm">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ações Rápidas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-auto p-4 justify-start gap-3">
              <Plus className="w-5 h-5 text-lia-text-secondary" />
              <div className="text-left">
                <div className="font-medium">Criar Workflow</div>
                <div className="text-sm text-lia-text-primary">Do zero ou usando template</div>
              </div>
            </Button>

            <Button variant="outline" className="h-auto p-4 justify-start gap-3">
              <Download className="w-5 h-5 text-status-success" />
              <div className="text-left">
                <div className="font-medium">Importar Template</div>
                <div className="text-sm text-lia-text-primary">Da biblioteca de templates</div>
              </div>
            </Button>

            <Button variant="outline" className="h-auto p-4 justify-start gap-3">
              <BarChart3 className="w-5 h-5 text-wedo-purple" />
              <div className="text-left">
                <div className="font-medium">Ver Analytics</div>
                <div className="text-sm text-lia-text-primary">Performance detalhada</div>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderBuilder = () => (
    <div className="text-center py-12">
      <Workflow className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
      <h3 className="text-lg font-medium text-lia-text-primary mb-2">Workflow Builder Visual</h3>
      <p className="text-lia-text-primary">Interface de arrastar e soltar para criar workflows</p>
    </div>
  )

  const renderTemplates = () => (
    <div className="text-center py-12">
      <FileText className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
      <h3 className="text-lg font-medium text-lia-text-primary mb-2">Biblioteca de Templates</h3>
      <p className="text-lia-text-primary">Templates pré-configurados para casos comuns</p>
    </div>
  )

  const renderLogs = () => (
    <div className="text-center py-12">
      <Activity className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
      <h3 className="text-lg font-medium text-lia-text-primary mb-2">Logs de Execução</h3>
      <p className="text-lia-text-primary">Histórico detalhado de todas as execuções</p>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-lia-text-primary flex items-center gap-2">
            <Workflow className="w-5 h-5 text-lia-text-secondary" />
            Automação Workflows Enterprise
          </h2>
          <p className="text-sm text-lia-text-primary">
            Builder visual para automações inteligentes de recrutamento
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-2">
            <Download className="w-4 h-4" />
            Exportar
          </Button>
          <Button size="sm" className="gap-2">
            <Plus className="w-4 h-4" />
            Novo Workflow
          </Button>
        </div>
      </div>

      <div className="flex space-x-1 bg-lia-bg-tertiary p-1 rounded-xl w-fit">
        {[
          { id: 'overview', label: 'Visão Geral', icon: BarChart3 },
          { id: 'builder', label: 'Builder', icon: Workflow },
          { id: 'templates', label: 'Templates', icon: FileText },
          { id: 'logs', label: 'Logs', icon: Activity }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setSelectedView(tab.id as Parameters<typeof setSelectedView>[0])}
            className={`flex items-center gap-2 px-3 py-3 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none ${
              selectedView === tab.id
                ? 'bg-lia-bg-primary text-lia-text-primary'
                : 'text-lia-text-primary hover:text-lia-text-primary'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {selectedView === 'overview' && renderOverview()}
      {selectedView === 'builder' && renderBuilder()}
      {selectedView === 'templates' && renderTemplates()}
      {selectedView === 'logs' && renderLogs()}
    </div>
  )
}
