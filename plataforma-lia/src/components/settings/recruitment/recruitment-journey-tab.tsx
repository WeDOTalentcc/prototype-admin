"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  RECRUITMENT_STAGES
} from "@/lib/recruitment-stages"
import {
  Edit, Plus, CheckCircle, Workflow, FileText, ClipboardList,
  Brain, Lock, Target, Settings, Check, X, ArrowUp, ArrowDown,
  Trash2,
} from "lucide-react"

export function RecruitmentJourneyTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [activeSubTab, setActiveSubTab] = useState("pipeline")
  const [stages, setStages] = useState(() =>
    RECRUITMENT_STAGES.filter(s => s.name !== 'standby' && s.name !== 'interview_manager2').map((stage, index) => ({
      ...stage,
      isActive: true,
      order: index + 1,
    }))
  )
  const [isEditing, setIsEditing] = useState(false)

  const subTabs = [
    { id: "pipeline", label: "Pipeline", icon: Workflow },
    { id: "eligibility", label: "Perguntas de Elegibilidade", icon: FileText },
    { id: "data-request", label: "Solicitação de Dados", icon: ClipboardList },
    { id: "lia-instructions", label: "Instruções LIA", icon: Brain },
  ]

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'system': return <Lock className="w-3.5 h-3.5 text-lia-text-tertiary" />
      case 'default': return <Target className="w-3.5 h-3.5 text-lia-text-tertiary" />
      case 'custom': return <Settings className="w-3.5 h-3.5 text-lia-text-tertiary" />
      default: return null
    }
  }

  const toggleStageActive = (stageName: string) => {
    setStages(prev => prev.map(s =>
      s.name === stageName ? { ...s, isActive: !s.isActive } : s
    ))
    onSettingsChange(true)
  }

  const moveStage = (fromIndex: number, direction: 'up' | 'down') => {
    const newStages = [...stages]
    const toIndex = direction === 'up' ? fromIndex - 1 : fromIndex + 1
    if (toIndex >= 0 && toIndex < newStages.length) {
      const fromStage = newStages[fromIndex]
      const toStage = newStages[toIndex]
      if (fromStage.stageCategory === 'system' || toStage.stageCategory === 'system') return
      ;[newStages[fromIndex], newStages[toIndex]] = [newStages[toIndex], newStages[fromIndex]]
      newStages.forEach((s, i) => { s.order = i + 1 })
      setStages(newStages)
      onSettingsChange(true)
    }
  }

  const addCustomStage = () => {
    const newStage = {
      name: `custom_${Date.now()}`,
      displayName: 'Nova Etapa',
      stageOrder: stages.length + 1,
      color: 'var(--lia-text-tertiary)',
      icon: 'plus-circle',
      stageType: 'active' as const,
      isInitial: false,
      isFinal: false,
      stageCategory: 'custom' as const,
      allowedTransitions: [] as string[],
      isActive: true,
      order: stages.length + 1,
    }
    const offerIndex = stages.findIndex(s => s.name === 'offer')
    if (offerIndex !== -1) {
      const newStages = [...stages]
      newStages.splice(offerIndex, 0, newStage)
      newStages.forEach((s, i) => { s.order = i + 1 })
      setStages(newStages)
    } else {
      setStages([...stages, newStage])
    }
    onSettingsChange(true)
  }

  const removeStage = (stageName: string) => {
    const stage = stages.find(s => s.name === stageName)
    if (stage?.stageCategory === 'system') return
    setStages(prev => {
      const filtered = prev.filter(s => s.name !== stageName)
      filtered.forEach((s, i) => { s.order = i + 1 })
      return filtered
    })
    onSettingsChange(true)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-medium font-inter">Recrutamento</CardTitle>
              <p className="text-sm text-lia-text-secondary mt-1">Pipeline e elegibilidade</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-status-success border-status-success/30 bg-status-success/10 dark:bg-status-success gap-1.5">
                <CheckCircle className="w-3 h-3" />
                Sincronizado
              </Badge>
            </div>
          </div>

          <div className="flex items-center gap-1 mt-4 dark:border-lia-border-subtle">
            {subTabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors rounded-lg -mb-px",
                  activeSubTab === tab.id
                    ? "border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary"
                    : "border-transparent text-lia-text-secondary hover:text-lia-text-primary"
                )}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </CardHeader>

        <CardContent>
          {activeSubTab === "pipeline" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className="text-status-error border-status-error/30 bg-status-error/10 dark:bg-status-error gap-1.5 cursor-pointer hover:bg-status-error/15">
                    <Trash2 className="w-3 h-3" />
                    Deletar Template
                  </Badge>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditing(!isEditing)}
                    className="gap-1.5"
                  >
                    <Edit className="w-3.5 h-3.5" />
                    {isEditing ? 'Concluir' : 'Editar'}
                  </Button>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-lia-text-primary mb-1">Jornada de Recrutamento</h3>
                <p className="text-sm text-lia-text-secondary mb-4">Visualize as etapas do processo seletivo configuradas.</p>

                <div className="flex items-center gap-6 text-xs text-lia-text-secondary mb-6 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-lg">
                  <div className="flex items-center gap-1.5">
                    <Lock className="w-3.5 h-3.5" />
                    <span><strong>Sistema:</strong> Etapas fixas (Funil, Triagem, Entrevista RH, Contratado, Reprovado)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Target className="w-3.5 h-3.5" />
                    <span><strong>Padrão:</strong> Editável nome e SLA</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Settings className="w-3.5 h-3.5" />
                    <span><strong>Custom:</strong> Totalmente editável</span>
                  </div>
                </div>

                <div className="space-y-3">
                  {stages.map((stage, index) => (
                    <div
                      key={stage.name}
                      className={cn(
                        "flex items-center gap-4 p-4 border rounded-md transition-colors",
                        stage.isActive
                          ? "border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary"
                          : "border-lia-border-subtle dark:border-lia-border-strong bg-lia-bg-secondary dark:bg-lia-bg-primary/50 opacity-60"
                      )}
                    >
                      <div className="flex items-center gap-3 min-w-10">
                        <span className="w-8 h-8 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-lg flex items-center justify-center text-sm font-medium text-lia-text-secondary">
                          {stage.order}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 flex-1">
                        {getCategoryIcon(stage.stageCategory)}
                        <span className="font-medium text-lia-text-primary">{stage.displayName}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        {isEditing && stage.stageCategory !== 'system' && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => moveStage(index, 'up')}
                              disabled={index === 0}
                              className="h-7 w-7 p-0"
                            >
                              <ArrowUp className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => moveStage(index, 'down')}
                              disabled={index === stages.length - 1}
                              className="h-7 w-7 p-0"
                            >
                              <ArrowDown className="w-3.5 h-3.5" />
                            </Button>
                          </>
                        )}

                        {stage.stageCategory === 'system' ? (
                          <span className="text-xs text-lia-text-tertiary flex items-center gap-1">
                            <Lock className="w-3 h-3" />
                          </span>
                        ) : (
                          <button
                            onClick={() => toggleStageActive(stage.name)}
                            className={cn(
                              "flex items-center gap-1 text-xs px-2 py-1 rounded-md transition-colors",
                              stage.isActive
                                ? "text-lia-text-tertiary hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error"
                                : "text-status-success hover:bg-status-success/10 dark:hover:bg-status-success"
                            )}
                          >
                            {stage.isActive ? (
                              <>
                                <X className="w-3 h-3" />
                                Inativo
                              </>
                            ) : (
                              <>
                                <Check className="w-3 h-3" />
                                Ativar
                              </>
                            )}
                          </button>
                        )}

                        {isEditing && stage.stageCategory === 'custom' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeStage(stage.name)}
                            className="h-7 w-7 p-0 text-status-error hover:text-status-error hover:bg-status-error/10"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {isEditing && (
                  <Button
                    variant="outline"
                    onClick={addCustomStage}
                    className="w-full mt-4 gap-2 border-dashed"
                  >
                    <Plus className="w-4 h-4" />
                    Adicionar Etapa Customizada
                  </Button>
                )}
              </div>
            </div>
          )}

          {activeSubTab === "eligibility" && (
            <div className="text-center py-12 text-lia-text-secondary">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Configurações de Perguntas de Elegibilidade</p>
            </div>
          )}

          {activeSubTab === "data-request" && (
            <div className="text-center py-12 text-lia-text-secondary">
              <ClipboardList className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Configurações de Solicitação de Dados</p>
            </div>
          )}

          {activeSubTab === "lia-instructions" && (
            <div className="text-center py-12 text-lia-text-secondary">
              <Brain className="w-12 h-12 mx-auto mb-3 opacity-30 text-wedo-cyan" />
              <p className="text-sm">Instruções para a LIA</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
