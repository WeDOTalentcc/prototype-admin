"use client"

import { useEffect, useState } from "react"
import { Chip } from "@/components/ui/chip"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { hasModuleAccess } from "@/utils/license-manager"
import { ModuleUpsell } from "@/components/module-access/module-upsell"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import {
  Edit, Plus, Workflow, FileText, Zap, Target,
  Download, BarChart3, Activity, MoreHorizontal, AlertCircle,
} from "lucide-react"

// ── Trigger/action label maps ────────────────────────────────────────────

const TRIGGER_LABELS: Record<string, string> = {
  candidate_stage_changed: "Candidato movimentado",
  interview_scheduled: "Entrevista agendada",
  offer_sent: "Proposta enviada",
  screening_completed: "Triagem concluída",
  no_response_48h: "Sem resposta (48h)",
}

// ── Types ────────────────────────────────────────────────────────────────

interface ApiAutomation {
  id: string
  name: string
  description?: string | null
  trigger_type: string
  action_type: string
  is_active: boolean
  executions_count?: number | null
  last_executed_at?: string | null
  success_rate?: number | null
}

interface WorkflowItem {
  id: string
  name: string
  description: string
  status: "active" | "paused"
  trigger: string
  lastRun: string | null
  executions: number
  successRate: number
}

function mapAutomation(a: ApiAutomation): WorkflowItem {
  return {
    id: String(a.id),
    name: a.name,
    description: a.description ?? "",
    status: a.is_active ? "active" : "paused",
    trigger: TRIGGER_LABELS[a.trigger_type] ?? a.trigger_type,
    lastRun: a.last_executed_at ?? null,
    executions: a.executions_count ?? 0,
    successRate: a.success_rate ?? 100,
  }
}

// ── Component ────────────────────────────────────────────────────────────

export function AutomationsTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [selectedView, setSelectedView] = useState<"overview" | "builder" | "templates" | "logs">("overview")
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { companyId } = useCompanyId()

  useEffect(() => {
    if (!companyId) return
    setIsLoading(true)
    setError(null)
    fetch(`/api/backend-proxy/automations?company_id=${encodeURIComponent(companyId)}`)
      .then((res) => res.json())
      .then((json) => {
        if (json?.success && Array.isArray(json?.data?.automations)) {
          setWorkflows(json.data.automations.map(mapAutomation))
        } else {
          setWorkflows([])
        }
      })
      .catch((err) => {
        console.error("[AutomationsTab] Não foi possível carregar as automações:", err)
        setError("Não foi possível carregar as automações.")
      })
      .finally(() => setIsLoading(false))
  }, [companyId])

  if (!hasModuleAccess("workflow_automation")) {
    return (
      <ModuleUpsell
        moduleId="workflow_automation"
        title="Automação Avançada de Workflows"
        description="Workflow builder visual com automações inteligentes e templates pré-configurados"
      />
    )
  }

  const renderOverview = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-16">
          <div className="w-6 h-6 rounded-full border-2 border-lia-text-secondary border-t-transparent animate-spin" />
          <span className="ml-3 text-sm text-lia-text-primary">Carregando automações…</span>
        </div>
      )
    }

    if (error) {
      return (
        <Card>
          <CardContent className="flex items-center gap-3 p-6 text-status-error">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span className="text-sm">{error}</span>
          </CardContent>
        </Card>
      )
    }

    const activeCount = workflows.filter((w) => w.status === "active").length

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-lia-text-primary">Workflows Ativos</p>
                  <p className="text-2xl font-semibold text-status-success">{activeCount}</p>
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
                  <p className="text-2xl font-semibold text-lia-text-primary">
                    {workflows.reduce((sum, w) => sum + w.executions, 0)}
                  </p>
                  <p className="text-xs text-lia-text-primary">total acumulado</p>
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
                  <p className="text-2xl font-semibold text-wedo-orange">
                    {workflows.length > 0
                      ? `${Math.round(workflows.reduce((s, w) => s + w.successRate, 0) / workflows.length)}%`
                      : "—"}
                  </p>
                  <p className="text-xs text-lia-text-primary">média das automações</p>
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
                  <p className="text-sm font-medium text-lia-text-primary">Automações</p>
                  <p className="text-2xl font-semibold text-wedo-purple">{workflows.length}</p>
                  <p className="text-xs text-lia-text-primary">configuradas</p>
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
            {workflows.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Workflow className="w-10 h-10 text-lia-text-primary mb-3" />
                <p className="text-sm font-medium text-lia-text-primary mb-1">
                  Nenhuma automação configurada ainda
                </p>
                <p className="text-xs text-lia-text-primary mb-4">
                  Crie sua primeira automação para agilizar o processo seletivo
                </p>
                <Button size="sm" className="gap-2">
                  <Plus className="w-4 h-4" />
                  Criar primeira automação
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {workflows.map((workflow) => (
                  <div
                    key={workflow.id}
                    className="flex items-center justify-between p-4 border border-lia-border-subtle rounded-xl hover:transition-shadow"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={`w-10 h-10 rounded-md flex items-center justify-center ${
                          workflow.status === "active" ? "bg-status-success/15" : "bg-lia-bg-tertiary"
                        }`}
                      >
                        <Workflow
                          className={`w-5 h-5 ${
                            workflow.status === "active" ? "text-status-success" : "text-lia-text-primary"
                          }`}
                        />
                      </div>
                      <div>
                        <h4 className="font-medium text-lia-text-primary">{workflow.name}</h4>
                        {workflow.description && (
                          <p className="text-sm text-lia-text-primary">{workflow.description}</p>
                        )}
                        <div className="flex items-center gap-3 mt-1 text-xs text-lia-text-primary">
                          <span>Trigger: {workflow.trigger}</span>
                          <span>•</span>
                          <span>{workflow.executions} execuções</span>
                          <span>•</span>
                          <span className="text-status-success">{workflow.successRate}% sucesso</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Chip variant="neutral" muted={workflow.status !== "active"}>
                        {workflow.status === "active" ? "Ativo" : "Pausado"}
                      </Chip>
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
            )}
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
                  <div className="font-medium">Importar Modelo</div>
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
  }

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
      <h3 className="text-lg font-medium text-lia-text-primary mb-2">Biblioteca de Modelos</h3>
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
          { id: "overview", label: "Visão Geral", icon: BarChart3 },
          { id: "builder", label: "Builder", icon: Workflow },
          { id: "templates", label: "Templates", icon: FileText },
          { id: "logs", label: "Logs", icon: Activity },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedView(tab.id as Parameters<typeof setSelectedView>[0])}
            className={`flex items-center gap-2 px-3 py-3 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none ${
              selectedView === tab.id
                ? "bg-lia-bg-primary text-lia-text-primary"
                : "text-lia-text-primary hover:text-lia-text-primary"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {selectedView === "overview" && renderOverview()}
      {selectedView === "builder" && renderBuilder()}
      {selectedView === "templates" && renderTemplates()}
      {selectedView === "logs" && renderLogs()}
    </div>
  )
}
