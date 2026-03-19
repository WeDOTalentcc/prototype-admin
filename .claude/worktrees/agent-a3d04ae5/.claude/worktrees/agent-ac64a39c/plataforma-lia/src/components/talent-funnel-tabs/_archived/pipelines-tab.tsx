"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ExpandableAIPrompt } from "@/components/expandable-ai-prompt"
import { LIAIcon } from "@/components/ui/lia-icon"
import { callOrchestratedPipelineChat } from "@/lib/api/kanban-assistant"
import {
  Plus, Settings, Users, Target, Calendar,
  TrendingUp, Clock, CheckCircle, Play, Edit,
  MoreVertical, Eye, ArrowRight, Zap, Brain,
  AlertCircle, BarChart3, Copy, Pause, FileText
} from "lucide-react"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

// Mock de pipelines
const mockPipelines = [
  {
    id: 'pipeline-1',
    name: 'Desenvolvedores Frontend',
    description: 'Pipeline especializado para recrutar desenvolvedores React/Vue.js',
    status: 'active',
    candidatesCount: 47,
    stagesCount: 5,
    avgTimeToHire: 12,
    successRate: 85,
    createdAt: '2024-01-15',
    stages: [
      { name: 'Triagem Inicial', candidates: 47, duration: 2 },
      { name: 'Teste Técnico', candidates: 23, duration: 3 },
      { name: 'Entrevista Técnica', candidates: 15, duration: 1 },
      { name: 'Entrevista Cultural', candidates: 8, duration: 1 },
      { name: 'Proposta', candidates: 5, duration: 5 }
    ],
    criteria: {
      skills: ['React', 'TypeScript', 'JavaScript'],
      experience: '3+ anos',
      location: 'São Paulo, Remoto',
      salary: 'R$ 8.000 - R$ 15.000'
    }
  },
  {
    id: 'pipeline-2',
    name: 'UX Designers Sênior',
    description: 'Fluxo otimizado para designers UX/UI com foco em produto',
    status: 'active',
    candidatesCount: 23,
    stagesCount: 4,
    avgTimeToHire: 8,
    successRate: 92,
    createdAt: '2024-02-01',
    stages: [
      { name: 'Análise Portfolio', candidates: 23, duration: 1 },
      { name: 'Case Study', candidates: 12, duration: 5 },
      { name: 'Entrevista Design', candidates: 8, duration: 1 },
      { name: 'Apresentação Final', candidates: 4, duration: 1 }
    ],
    criteria: {
      skills: ['Figma', 'User Research', 'Prototyping'],
      experience: '5+ anos',
      location: 'São Paulo',
      salary: 'R$ 12.000 - R$ 20.000'
    }
  },
  {
    id: 'pipeline-3',
    name: 'Liderança Tech',
    description: 'Pipeline para posições de liderança técnica e gestão',
    status: 'draft',
    candidatesCount: 8,
    stagesCount: 6,
    avgTimeToHire: 18,
    successRate: 94,
    createdAt: '2024-02-10',
    stages: [
      { name: 'Screening Executive', candidates: 8, duration: 3 },
      { name: 'Assessment Técnico', candidates: 6, duration: 2 },
      { name: 'Painel Técnico', candidates: 4, duration: 2 },
      { name: 'Entrevista Cultural', candidates: 3, duration: 1 },
      { name: 'Case de Liderança', candidates: 2, duration: 7 },
      { name: 'Aprovação Final', candidates: 1, duration: 3 }
    ],
    criteria: {
      skills: ['Liderança', 'Arquitetura', 'Gestão de Pessoas'],
      experience: '8+ anos',
      location: 'São Paulo',
      salary: 'R$ 20.000+'
    }
  }
]

interface LiaMessage {
  id: string
  type: 'response' | 'error' | 'info' | 'user'
  content: string
  timestamp: number
}

export function PipelinesTab() {
  const [pipelines] = useState(mockPipelines)
  const [selectedPipeline, setSelectedPipeline] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [showPipelineModal, setShowPipelineModal] = useState(false)
  const [selectedPipelineForModal, setSelectedPipelineForModal] = useState<any>(null)
  const [liaMessages, setLiaMessages] = useState<LiaMessage[]>([])
  const [isLiaLoading, setIsLiaLoading] = useState(false)
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([])

  // Mock pipeline details modal
  const PipelineDetailsModal = ({ pipeline, isOpen, onClose }: any) => {
    if (!isOpen || !pipeline) return null

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-900 rounded-md max-w-6xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-md flex items-center justify-center">
                  <Target className="w-6 h-6 text-gray-700 dark:text-gray-300" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-950 dark:text-gray-50">{pipeline.name}</h2>
                  <p className="text-gray-800 dark:text-gray-200">{pipeline.description}</p>
                </div>
              </div>
              <Button variant="outline" onClick={onClose}>✕</Button>
            </div>
          </div>

          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Performance Metrics */}
              <Card>
                <CardHeader>
                  <CardTitle>📊 Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span>Taxa de Sucesso:</span>
                      <span className="font-semibold text-green-600">{pipeline.successRate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Candidatos Ativos:</span>
                      <span className="font-semibold">{pipeline.candidatesCount}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Tempo Médio:</span>
                      <span className="font-semibold">{pipeline.avgTimeToHire} dias</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Estágios:</span>
                      <span className="font-semibold">{pipeline.stagesCount}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Status:</span>
                      <Badge className={pipeline.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-800 dark:text-gray-200'}>
                        {pipeline.status === 'active' ? 'Ativo' : 'Rascunho'}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Criteria */}
              <Card>
                <CardHeader>
                  <CardTitle>🎯 Critérios</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Skills:</label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {pipeline.criteria.skills.map((skill: string, index: number) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Experiência:</label>
                      <p className="text-sm text-gray-800 dark:text-gray-200">{pipeline.criteria.experience}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Localização:</label>
                      <p className="text-sm text-gray-800 dark:text-gray-200">{pipeline.criteria.location}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Salário:</label>
                      <p className="text-sm text-gray-800 dark:text-gray-200">{pipeline.criteria.salary}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Stages Overview */}
              <Card>
                <CardHeader>
                  <CardTitle>🏗️ Funil de Conversão</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {pipeline.stages.map((stage: any, index: number) => {
                      const conversionRate = index === 0 ? 100 : Math.round((stage.candidates / pipeline.stages[0].candidates) * 100)
                      return (
                        <div key={index} className="space-y-1">
                          <div className="flex justify-between text-sm">
                            <span className="font-medium">{stage.name}</span>
                            <span className="text-gray-600 dark:text-gray-400">{stage.candidates} ({conversionRate}%)</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-gray-900 h-2 rounded-full"
                              style={{ width: `${conversionRate}%` }}
                            ></div>
                          </div>
                          <p className="text-xs text-gray-600 dark:text-gray-400">{stage.duration} dias médio</p>
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Stages Detail */}
            <Card className="mt-8">
              <CardHeader>
                <CardTitle>🔄 Detalhamento dos Estágios</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {pipeline.stages.map((stage: any, index: number) => (
                    <div key={index} className="bg-white dark:bg-gray-800 rounded-md p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium text-gray-950 dark:text-gray-50">{stage.name}</h4>
                        <Badge variant="secondary">{stage.candidates} candidatos</Badge>
                      </div>
                      <div className="space-y-2 text-sm text-gray-800 dark:text-gray-200">
                        <div className="flex justify-between">
                          <span>Duração média:</span>
                          <span>{stage.duration} dias</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Taxa conversão:</span>
                          <span>{index === 0 ? 100 : Math.round((stage.candidates / pipeline.stages[index-1].candidates) * 100)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Status:</span>
                          <span className="text-green-600">Normal</span>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full mt-3"
                        onClick={() => handleViewStageCandidates(pipeline.id, stage.name)}
                      >
                        <Users className="w-3 h-3 mr-2" />
                        Ver Candidatos
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-3 mt-6 pt-6">
              <Button onClick={() => handleViewPipelineCandidates(pipeline.id)}>
                <Users className="w-4 h-4 mr-2" />
                Ver Todos Candidatos ({pipeline.candidatesCount})
              </Button>
              <Button variant="outline" onClick={() => handleEditPipeline(pipeline.id)}>
                <Edit className="w-4 h-4 mr-2" />
                Editar Pipeline
              </Button>
              <Button variant="outline" onClick={() => handleClonePipeline(pipeline.id)}>
                <Copy className="w-4 h-4 mr-2" />
                Clonar
              </Button>
              <Button variant="outline" onClick={() => handleExportPipelineReport(pipeline.id)}>
                <FileText className="w-4 h-4 mr-2" />
                Exportar Relatório
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const addLiaMessage = (content: string, type: 'response' | 'error' | 'info' | 'user' = 'response') => {
    const message: LiaMessage = {
      id: `msg-${Date.now()}`,
      type,
      content,
      timestamp: Date.now()
    }
    setLiaMessages(prev => [...prev, message])
  }

  const handleUIAction = (action: string, params?: Record<string, unknown>) => {
    switch (action) {
      case 'view_pipeline':
        if (params?.pipeline_id) {
          handleViewPipelineDetails(params.pipeline_id as string)
        }
        break
      case 'view_candidates':
        if (params?.pipeline_id) {
          handleViewPipelineCandidates(params.pipeline_id as string)
        }
        break
      case 'edit_pipeline':
        if (params?.pipeline_id) {
          handleEditPipeline(params.pipeline_id as string)
        }
        break
      case 'create_pipeline':
        handleCreateNewPipeline()
        break
      default:
        console.log('UI action not implemented:', action, params)
    }
  }

  const handleAICommand = async (command: string) => {
    setIsLiaLoading(true)
    
    addLiaMessage(command, 'user')
    
    try {
      const response = await callOrchestratedPipelineChat({
        message: command,
        mode: 'pipeline',
        context: {
          pipelines: pipelines.map(p => ({
            id: p.id,
            name: p.name,
            description: p.description,
            status: p.status,
            candidatesCount: p.candidatesCount,
            stagesCount: p.stagesCount,
            avgTimeToHire: p.avgTimeToHire,
            successRate: p.successRate,
            stages: p.stages,
            criteria: p.criteria
          })),
          selectedPipeline: selectedPipeline,
          totalPipelines: pipelines.length,
          activePipelines: pipelines.filter(p => p.status === 'active').length,
          totalCandidates: pipelines.reduce((acc, p) => acc + p.candidatesCount, 0)
        }
      })
      
      addLiaMessage(response.content)
      
      if (response.ui_action) {
        handleUIAction(response.ui_action, response.ui_action_params)
      }
      
      if (response.suggested_prompts?.length > 0) {
        setSuggestedPrompts(response.suggested_prompts)
      }
    } catch (error) {
      console.error('Error calling pipeline chat:', error)
      addLiaMessage('Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente.', 'error')
    } finally {
      setIsLiaLoading(false)
    }
  }

  const handleLIAInsights = () => {
    alert(`🧠 Análise LIA - Pipelines\n\n` +
          `📊 Performance Insights:\n\n` +
          `🏆 Top Performer: "UX Designers Sênior"\n` +
          `• 92% taxa de sucesso (excepcional)\n` +
          `• 8 dias time-to-hire (otimizado)\n` +
          `• 23 candidatos ativos\n` +
          `• Processo bem calibrado\n\n` +
          `⚠️ Atenção: "Liderança Tech"\n` +
          `• Status rascunho há 10 dias\n` +
          `• Apenas 8 candidatos\n` +
          `• 18 dias timeline (muito longo)\n` +
          `• Bottleneck no Case de Liderança\n\n` +
          `💡 Oportunidades:\n` +
          `• Replicar processo UX para outras áreas\n` +
          `• Ativar pipeline Liderança Tech\n` +
          `• Otimizar gargalos identificados\n` +
          `• Criar pipeline DevOps (demanda detectada)\n\n` +
          `🎯 Ação Recomendada: Ativar Liderança Tech e otimizar processo`)
  }

  // Enhanced handlers for pipeline actions
  const handleViewPipelineDetails = (pipelineId: string) => {
    const pipeline = pipelines.find(p => p.id === pipelineId)
    if (pipeline) {
      setSelectedPipelineForModal(pipeline)
      setShowPipelineModal(true)
    }
  }

  const handleViewPipelineCandidates = (pipelineId: string) => {
    const pipeline = pipelines.find(p => p.id === pipelineId)
    if (pipeline) {
      const filterData = {
        type: 'pipeline_filter',
        pipelineId: pipelineId,
        pipelineName: pipeline.name,
        expectedCount: pipeline.candidatesCount
      }

      sessionStorage.setItem('candidateFilter', JSON.stringify(filterData))

      alert(`🎯 Filtro de Pipeline Aplicado\n\n` +
            `📋 Pipeline: ${pipeline.name}\n` +
            `👥 Candidatos: ${pipeline.candidatesCount}\n\n` +
            `🔍 Filtros Aplicados:\n` +
            `• Status: Em processo ativo\n` +
            `• Skills: ${pipeline.criteria.skills.join(', ')}\n` +
            `• Experiência: ${pipeline.criteria.experience}\n` +
            `• Localização: ${pipeline.criteria.location}\n\n` +
            `📊 Breakdown por Estágio:\n` +
            `${pipeline.stages.map((stage: any) => `• ${stage.name}: ${stage.candidates} candidatos`).join('\n')}\n\n` +
            `➡️ Navegando para aba Candidatos...`)

      // Navigate to candidates tab
      setTimeout(() => {
        const candidatesTab = document.querySelector('[role="tab"][aria-label*="Candidatos"]') as HTMLElement
        if (candidatesTab) {
          candidatesTab.click()
        }
      }, 1500)
    }
  }

  const handleViewStageCandidates = (pipelineId: string, stageName: string) => {
    const pipeline = pipelines.find(p => p.id === pipelineId)
    const stage = pipeline?.stages.find(s => s.name === stageName)

    if (pipeline && stage) {
      alert(`🔍 Candidatos no Estágio: ${stageName}\n\n` +
            `📋 Pipeline: ${pipeline.name}\n` +
            `👥 Candidatos neste estágio: ${stage.candidates}\n` +
            `⏱️ Duração média: ${stage.duration} dias\n\n` +
            `🎯 Próximas Ações Possíveis:\n` +
            `• Agendar entrevistas pendentes\n` +
            `• Enviar feedbacks automáticos\n` +
            `• Mover candidatos aprovados\n` +
            `• Identificar gargalos\n\n` +
            `💡 Esta view mostraria lista detalhada dos candidatos neste estágio específico`)
    }
  }

  const handleEditPipeline = (pipelineId: string) => {
    const pipeline = pipelines.find(p => p.id === pipelineId)
    if (pipeline) {
      alert(`✏️ Editando Pipeline: ${pipeline.name}\n\n` +
            `🔧 Funcionalidades Disponíveis:\n\n` +
            `📋 Configurações Básicas:\n` +
            `• Nome e descrição\n` +
            `• Critérios de match\n` +
            `• Skills obrigatórias/preferenciais\n` +
            `• Faixas salariais\n\n` +
            `🏗️ Estágios do Pipeline:\n` +
            `• Adicionar/remover estágios\n` +
            `• Reordenar sequência\n` +
            `• Configurar durações\n` +
            `• Templates de comunicação\n\n` +
            `🤖 Automações:\n` +
            `• Auto-sourcing ativo/inativo\n` +
            `• Triggers automáticos\n` +
            `• Notificações personalizadas\n` +
            `• Scoring LIA\n\n` +
            `⚙️ Configurações Avançadas:\n` +
            `• Regras de progressão\n` +
            `• Aprovações necessárias\n` +
            `• Integrações calendar\n` +
            `• Analytics específicos\n\n` +
            `💡 Esta funcionalidade abriria um editor visual completo`)
    }
  }

  const handleClonePipeline = (pipelineId: string) => {
    const pipeline = pipelines.find(p => p.id === pipelineId)
    if (pipeline) {
      alert(`📋 Clonando Pipeline: ${pipeline.name}\n\n` +
            `🔄 Processo de Clonagem:\n\n` +
            `✅ Elementos Copiados:\n` +
            `• Estrutura de estágios (${pipeline.stagesCount})\n` +
            `• Critérios de match\n` +
            `• Configurações de automação\n` +
            `• Templates de comunicação\n` +
            `• Regras de progressão\n\n` +
            `🆕 Personalização Necessária:\n` +
            `• Nome do novo pipeline\n` +
            `• Ajustes de critérios específicos\n` +
            `• Adaptação de skills\n` +
            `• Faixa salarial específica\n\n` +
            `💡 Opções de Clone:\n` +
            `• [C]ompleto: copia tudo\n` +
            `• [E]strutura: apenas estágios\n` +
            `• [C]ritérios: apenas match rules\n\n` +
            `🎯 Casos de Uso:\n` +
            `• Posições similares (Frontend → Backend)\n` +
            `• Diferentes senioridades\n` +
            `• Adaptação regional\n` +
            `• A/B testing de processos\n\n` +
            `Nome sugerido: "${pipeline.name} - Copy"\n\n` +
            `✅ Confirma clonagem?`)

      setTimeout(() => {
        if (confirm('Confirma a clonagem do pipeline?')) {
          alert(`🎉 Pipeline Clonado com Sucesso!\n\n` +
                `📝 Novo Pipeline Criado:\n` +
                `• Nome: "${pipeline.name} - Copy"\n` +
                `• Status: Rascunho\n` +
                `• Estágios: ${pipeline.stagesCount} copiados\n` +
                `• Critérios: Herdados do original\n\n` +
                `🔧 Próximos Passos:\n` +
                `• Personalizar nome e critérios\n` +
                `• Ajustar configurações específicas\n` +
                `• Ativar quando pronto\n\n` +
                `💡 Pipeline clone disponível na lista`)
        }
      }, 1000)
    }
  }

  const handleActivatePipeline = (pipelineId: string) => {
    const pipeline = pipelines.find(p => p.id === pipelineId)
    if (pipeline) {
      if (pipeline.status === 'active') {
        alert(`⏸️ Pausando Pipeline: ${pipeline.name}\n\n` +
              `🔄 Ações ao Pausar:\n\n` +
              `⏹️ Auto-sourcing: Desativado\n` +
              `📧 Notificações: Pausadas\n` +
              `👥 Candidatos atuais: Mantidos\n` +
              `📊 Analytics: Continuam ativos\n\n` +
              `💡 Candidatos em processo:\n` +
              `• Continuam no pipeline\n` +
              `• Não recebem novos matches\n` +
              `• Processos manuais funcionam normalmente\n\n` +
              `⚠️ Importante:\n` +
              `• Sourcing automático para\n` +
              `• Novas aplicações não são aceitas\n` +
              `• Pipeline pode ser reativado a qualquer momento\n\n` +
              `✅ Confirma pausar pipeline?`)
      } else {
        alert(`▶️ Ativando Pipeline: ${pipeline.name}\n\n` +
              `🚀 Validações de Ativação:\n\n` +
              `✅ Critérios definidos\n` +
              `✅ Estágios configurados (${pipeline.stagesCount})\n` +
              `✅ Templates de comunicação\n` +
              `✅ Aprovadores definidos\n\n` +
              `🔄 Ações na Ativação:\n\n` +
              `🎯 Auto-sourcing: Ativado\n` +
              `📧 Notificações: Habilitadas\n` +
              `🤖 LIA Scoring: Ativo\n` +
              `📊 Analytics: Tracking iniciado\n\n` +
              `🚀 Sourcing Inicial:\n` +
              `• Busca automática de candidatos\n` +
              `• Aplicação de critérios de match\n` +
              `• Estimativa: 15-25 candidatos em 48h\n\n` +
              `💰 Custo estimado: R$ 350/mês (sourcing ativo)\n\n` +
              `✅ Confirma ativação do pipeline?`)
      }
    }
  }

  const handleExportPipelineReport = (pipelineId: string) => {
    const pipeline = pipelines.find(p => p.id === pipelineId)
    if (pipeline) {
      alert(`📊 Exportando Relatório: ${pipeline.name}\n\n` +
            `📋 Relatório Completo Gerado:\n\n` +
            `📈 Performance Metrics:\n` +
            `• Taxa de sucesso: ${pipeline.successRate}%\n` +
            `• Tempo médio: ${pipeline.avgTimeToHire} dias\n` +
            `• Candidatos processados: ${pipeline.candidatesCount}\n` +
            `• Conversão por estágio detalhada\n\n` +
            `📊 Analytics Inclusos:\n` +
            `• Funil de conversão visual\n` +
            `• Gargalos identificados\n` +
            `• Benchmarks vs. mercado\n` +
            `• Trends temporais\n\n` +
            `👥 Candidate Analytics:\n` +
            `• Source breakdown\n` +
            `• Skills distribution\n` +
            `• Geographic analysis\n` +
            `• Salary distribution\n\n` +
            `💰 Cost Analysis:\n` +
            `• Cost per hire\n` +
            `• ROI calculation\n` +
            `• Budget utilization\n\n` +
            `📋 Formatos Disponíveis:\n` +
            `• PDF Executive Summary\n` +
            `• Excel Detailed Analytics\n` +
            `• PowerPoint Presentation\n` +
            `• CSV Raw Data\n\n` +
            `💾 Relatório salvo em: Downloads/pipeline_${pipeline.name.toLowerCase().replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`)
    }
  }

  const handleCreateNewPipeline = () => {
    alert(`🆕 Criar Novo Pipeline\n\n` +
          `🎯 Métodos de Criação:\n\n` +
          `🤖 LIA Smart Creation:\n` +
          `• Baseado em job description\n` +
          `• AI sugere estágios otimizados\n` +
          `• Critérios auto-calibrados\n` +
          `• Templates pré-configurados\n\n` +
          `📋 Template Library:\n` +
          `• Pipelines pré-definidos por área\n` +
          `• Best practices do mercado\n` +
          `• Personalizáveis\n\n` +
          `🔧 Custom Build:\n` +
          `• Criação do zero\n` +
          `• Full customization\n` +
          `• Máxima flexibilidade\n\n` +
          `📊 Clone & Adapt:\n` +
          `• Baseado em pipeline existente\n` +
          `• Adaptação específica\n` +
          `• Rápido deployment\n\n` +
          `💡 Recomendação LIA:\n` +
          `Detectei demanda por DevOps Engineers.\n` +
          `Posso criar pipeline otimizado automaticamente?\n\n` +
          `Escolha: [S]mart, [T]emplate, [C]ustom, ou [A]uto DevOps?`)
  }

  // Handlers for insight actions
  const handlePipelineInsightAction = (actionType: string, data?: any) => {
    switch (actionType) {
      case 'optimize_pipelines':
        alert(`🔧 Otimização de Pipelines\n\n` +
              `🧠 LIA Performance Analysis:\n\n` +
              `🏆 Best Practices Identificadas:\n` +
              `• UX Pipeline: 92% sucesso (benchmark)\n` +
              `• Processo otimizado em 4 estágios\n` +
              `• Portfolio review elimina 52% early\n` +
              `• Case study como diferencial\n\n` +
              `⚡ Otimizações Sugeridas:\n\n` +
              `📋 Frontend Pipeline:\n` +
              `• Adicionar code review step\n` +
              `• Reduzir teste técnico duration (-1 dia)\n` +
              `• Split entrevista técnica em 2 rounds\n` +
              `• ROI esperado: +15% conversão\n\n` +
              `🎯 Liderança Pipeline:\n` +
              `• Mover screening executive para início\n` +
              `• Paralelizar assessment + painel\n` +
              `• Reduzir case duration (7→4 dias)\n` +
              `• ROI esperado: -30% time-to-hire\n\n` +
              `🚀 Auto-Apply Changes?\n` +
              `• Backup automático de configs atuais\n` +
              `• A/B testing por 30 dias\n` +
              `• Rollback automático se performance cair\n\n` +
              `✅ Aplicar otimizações automaticamente?`)
        break

      case 'activate_drafts':
        alert(`▶️ Ativação de Pipelines Draft\n\n` +
              `📋 Pipeline: "Liderança Tech"\n` +
              `⏱️ Em draft há: 10 dias\n\n` +
              `🔍 Análise Pre-Ativação:\n\n` +
              `✅ Readiness Check:\n` +
              `• Estágios configurados: 6/6\n` +
              `• Critérios definidos: ✅\n` +
              `• Aprovadores: ✅\n` +
              `• Templates: ✅\n` +
              `• Budget approval: ✅\n\n` +
              `💡 LIA Recommendations:\n` +
              `• Reduzir case duration: 7→4 dias\n` +
              `• Adicionar pre-screening call\n` +
              `• Configurar auto-sourcing seletivo\n\n` +
              `🎯 Expected Performance:\n` +
              `• Candidates/month: 12-18\n` +
              `• Success rate: 85-90%\n` +
              `• Time-to-hire: 15-18 dias\n` +
              `• Cost per hire: R$ 8.500\n\n` +
              `🚀 Ativar com otimizações LIA?\n` +
              `[S]im com otimizações\n` +
              `[A]tivar como está\n` +
              `[C]ancelar`)
        break

      case 'create_devops_pipeline':
        alert(`🆕 Criação Automática: Pipeline DevOps\n\n` +
              `🎯 LIA Market Intelligence:\n\n` +
              `📊 Demanda Detectada:\n` +
              `• 67% das empresas target contratando DevOps\n` +
              `• 23 vagas abertas identificadas\n` +
              `• Salary range: R$ 12-22k\n` +
              `• Urgência: Alta\n\n` +
              `🧬 Pipeline Auto-Generated:\n\n` +
              `📋 Suggested Stages (5):\n` +
              `1. Tech Screening (2d) - infra knowledge\n` +
              `2. Hands-on Challenge (3d) - AWS/K8s\n` +
              `3. Architecture Review (1d) - system design\n` +
              `4. Cultural Fit (1d) - DevOps mindset\n` +
              `5. Final Proposal (3d) - negotiation\n\n` +
              `🎯 Auto-Generated Criteria:\n` +
              `• Core: AWS, Docker, Kubernetes, Terraform\n` +
              `• Preferred: Python, Monitoring, CI/CD\n` +
              `• Experience: 3-8 anos\n` +
              `• Location: São Paulo, Remoto\n\n` +
              `🤖 Smart Features:\n` +
              `• Auto-sourcing: GitHub analysis\n` +
              `• Technical screening: automated\n` +
              `• Reference check: LinkedIn API\n\n` +
              `📈 Predicted Performance:\n` +
              `• Success rate: 82% (based on similar)\n` +
              `• Time-to-hire: 12 dias\n` +
              `• Candidates/month: 15-20\n\n` +
              `⏱️ Creation time: 5 minutos\n` +
              `✅ Criar pipeline DevOps automaticamente?`)
        break

      default:
        console.log('Pipeline insight action not implemented:', actionType)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'border-green-400'
      case 'draft': return 'border-yellow-400'
      case 'paused': return 'border-gray-400'
      default: return 'border-gray-200'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active': return 'Ativo'
      case 'draft': return 'Rascunho'
      case 'paused': return 'Pausado'
      default: return 'Desconhecido'
    }
  }

  return (
    <div className="space-y-4">
      {/* LIA Prompt - AI First */}
      <div className="flex flex-col lg:flex-row gap-2 mb-4">
        <div className="flex-1">
          <ExpandableAIPrompt
            selectedCandidates={[]}
            onCommand={handleAICommand}
            filteredCount={pipelines.reduce((acc, p) => acc + p.candidatesCount, 0)}
            totalCount={pipelines.reduce((acc, p) => acc + p.candidatesCount, 0)}
            candidateContext={null}
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-2 text-xs h-8 px-3 bg-green-50 hover:bg-green-100 border-green-200"
            onClick={handleLIAInsights}
            title="LIA analisa pipelines e sugere otimizações"
          >
            <LIAIcon size="sm" />
            LIA Insights
          </Button>
        </div>
      </div>

      {/* ✨ Insights Estratégicos da LIA - At the top */}
      <Card className="bg-gray-100 dark:bg-gray-800">
        <CardContent className="p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-gray-700 dark:bg-gray-300 rounded-md flex items-center justify-center">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="font-medium text-gray-950 dark:text-gray-50">
                🚀 Otimização de Pipelines
              </h3>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                Performance analysis e oportunidades de melhoria
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="bg-white dark:bg-gray-800 rounded-md p-3">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                  Performance Boost
                </span>
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">
                UX pipeline com 92% sucesso - replicar best practices
              </p>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
                💡 Otimizações detectadas
              </p>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-6 text-xs flex-1"
                  onClick={() => handlePipelineInsightAction('optimize_pipelines')}
                >
                  <Zap className="w-3 h-3 mr-1" />
                  Otimizar
                </Button>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-md p-3">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="w-4 h-4 text-orange-600" />
                <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                  Pipeline Inativo
                </span>
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">
                "Liderança Tech" em draft há 10 dias - pronto para ativação
              </p>
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                💡 Ativar agora
              </p>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-6 text-xs flex-1"
                  onClick={() => handlePipelineInsightAction('activate_drafts')}
                >
                  <Play className="w-3 h-3 mr-1" />
                  Ativar
                </Button>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-md p-3">
              <div className="flex items-center gap-2 mb-2">
                <Plus className="w-4 h-4 text-gray-700 dark:text-gray-300" />
                <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                  Demanda Detectada
                </span>
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">
                DevOps: alta demanda, nenhum pipeline ativo
              </p>
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                💡 Pipeline auto-criado
              </p>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-6 text-xs flex-1"
                  onClick={() => handlePipelineInsightAction('create_devops_pipeline')}
                >
                  <Plus className="w-3 h-3 mr-1" />
                  Criar
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Enhanced Pipeline Cards */}
      <div className="space-y-4">
        {pipelines.map((pipeline) => (
          <Card key={pipeline.id} className={`border-l-4 ${getStatusColor(pipeline.status)}`}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                {/* Informações principais - lado esquerdo */}
                <div className="flex-1 space-y-4">
                  {/* Header */}
                  <div className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <CardTitle className="text-lg">{pipeline.name}</CardTitle>
                        <Badge className={`text-xs px-2 py-1 ${getStatusColor(pipeline.status)}`}>
                          {getStatusLabel(pipeline.status)}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-800 dark:text-gray-200">
                        {pipeline.description}
                      </p>
                    </div>
                  </div>

                  {/* Métricas em linha */}
                  <div className="flex items-center gap-8">
                    <div className="text-center">
                      <p className="text-lg font-semibold text-gray-700 dark:text-gray-300">{pipeline.candidatesCount}</p>
                      <p className="text-xs text-gray-600">Candidatos</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold text-green-600">{pipeline.successRate}%</p>
                      <p className="text-xs text-gray-600">Taxa Sucesso</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold text-purple-600">{pipeline.avgTimeToHire}d</p>
                      <p className="text-xs text-gray-600">Tempo Médio</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold text-orange-600">{pipeline.stagesCount}</p>
                      <p className="text-xs text-gray-600">Etapas</p>
                    </div>
                  </div>

                  {/* Progress dos Estágios */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs text-gray-600">
                      <span>Progresso dos Estágios</span>
                      <span>{pipeline.stages.length} etapas configuradas</span>
                    </div>
                    <div className="flex gap-1">
                      {pipeline.stages.map((stage, index) => (
                        <div
                          key={index}
                          className="flex-1 h-2 bg-gray-200 rounded"
                          style={{
                            backgroundColor: stage.candidates > 0 ? '#1f2937' : '#e5e7eb',
                            opacity: stage.candidates > 0 ? 1 : 0.3
                          }}
                          title={`${stage.name}: ${stage.candidates} candidatos`}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Critérios */}
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-gray-800 dark:text-gray-200">Critérios:</p>
                    <div className="flex flex-wrap gap-1 mb-2">
                      {pipeline.criteria.skills.slice(0, 4).map((skill, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                      {pipeline.criteria.skills.length > 4 && (
                        <Badge variant="secondary" className="text-xs text-gray-600">
                          +{pipeline.criteria.skills.length - 4} mais
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-gray-600">
                      {pipeline.criteria.experience} • {pipeline.criteria.location} • {pipeline.criteria.salary}
                    </p>
                  </div>
                </div>

                {/* Enhanced Actions */}
                <div className="flex flex-col gap-2 ml-6 min-w-[180px]">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewPipelineDetails(pipeline.id)}
                  >
                    <Eye className="w-3 h-3 mr-2" />
                    Ver Detalhes
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewPipelineCandidates(pipeline.id)}
                  >
                    <Users className="w-3 h-3 mr-2" />
                    Candidatos ({pipeline.candidatesCount})
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEditPipeline(pipeline.id)}
                  >
                    <Edit className="w-3 h-3 mr-2" />
                    Editar
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleClonePipeline(pipeline.id)}
                  >
                    <Copy className="w-3 h-3 mr-2" />
                    Clonar
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleActivatePipeline(pipeline.id)}
                    className={pipeline.status === 'active' ? 'text-orange-700 border-orange-300' : 'text-green-700 border-green-300'}
                  >
                    {pipeline.status === 'active' ? (
                      <>
                        <Pause className="w-3 h-3 mr-2" />
                        Pausar
                      </>
                    ) : (
                      <>
                        <Play className="w-3 h-3 mr-2" />
                        Ativar
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Enhanced Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-50">
            Pipelines de Recrutamento ({pipelines.length})
          </h2>
          <p className="text-sm text-gray-800 dark:text-gray-200">
            Processos estruturados para diferentes posições
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Configurar
          </Button>

          <Button size="sm" onClick={handleCreateNewPipeline}>
            <Plus className="w-4 h-4 mr-2" />
            Novo Pipeline
          </Button>
        </div>
      </div>

      {/* Pipeline Details Modal */}
      <PipelineDetailsModal
        pipeline={selectedPipelineForModal}
        isOpen={showPipelineModal}
        onClose={() => {
          setShowPipelineModal(false)
          setSelectedPipelineForModal(null)
        }}
      />

      {/* Empty State (se não houver pipelines) */}
      {pipelines.length === 0 && (
        <Card className="text-center py-12">
          <CardContent>
            <Target className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-950 dark:text-gray-50 mb-2">
              Nenhum pipeline criado
            </h3>
            <p className="text-gray-800 dark:text-gray-200 mb-4">
              Crie seu primeiro pipeline para organizar candidatos por tipo de vaga
            </p>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Criar Primeiro Pipeline
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
