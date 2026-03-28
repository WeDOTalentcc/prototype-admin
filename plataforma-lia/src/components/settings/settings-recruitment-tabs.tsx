"use client"

  import { useState } from "react"
  import { cn } from "@/lib/utils"
  import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
  import { Button } from "@/components/ui/button"
  import { Badge } from "@/components/ui/badge"
  import { hasModuleAccess } from "@/utils/license-manager"
  import { ModuleUpsell } from "@/components/module-access/module-upsell"
  import {
    RECRUITMENT_STAGES
  } from "@/lib/recruitment-stages"
  import {
    Mail, Bell, MessageSquare, Phone, Zap, Plus, Edit,
    MoreVertical, CheckCircle, Workflow, FileText, ClipboardList,
    Brain, Lock, Target, Settings, Check, X, ArrowUp, ArrowDown,
    Trash2, Star, BarChart3, Activity, Download, MoreHorizontal
  } from "lucide-react"

  export interface SettingsRecruitmentTabProps {
    onSettingsChange: (changed: boolean) => void
  }

  // Componente de Central de Comunicação
export function CommunicationTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [activeSubTab, setActiveSubTab] = useState<'templates' | 'notifications' | 'whatsapp' | 'sms' | 'automation'>('templates')
  const [templates, setTemplates] = useState([
    {
      id: 'welcome',
      name: 'Boas-vindas',
      subject: 'Bem-vindo(a) ao processo seletivo da {empresa}',
      type: 'email',
      status: 'ativo',
      trigger: 'Novo candidato',
      lastModified: '2024-01-15'
    },
    {
      id: 'interview-invite',
      name: 'Convite para Entrevista',
      subject: 'Convite para entrevista - {vaga}',
      type: 'email',
      status: 'ativo',
      trigger: 'Agendamento de entrevista',
      lastModified: '2024-01-18'
    },
    {
      id: 'rejection',
      name: 'Feedback Negativo',
      subject: 'Agradecemos seu interesse - {vaga}',
      type: 'email',
      status: 'ativo',
      trigger: 'Candidato rejeitado',
      lastModified: '2024-01-10'
    },
    {
      id: 'offer',
      name: 'Proposta de Emprego',
      subject: 'Proposta de emprego - {vaga}',
      type: 'email',
      status: 'ativo',
      trigger: 'Aprovação final',
      lastModified: '2024-01-20'
    }
  ])

  const subTabs = [
    { id: 'templates', name: 'Templates de Email', icon: Mail },
    { id: 'notifications', name: 'Notificações', icon: Bell },
    { id: 'whatsapp', name: 'WhatsApp Business', icon: MessageSquare },
    { id: 'sms', name: 'SMS', icon: Phone },
    { id: 'automation', name: 'Automação', icon: Zap }
  ]

  const renderTemplates = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4" />
              Templates de Email
            </div>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              Novo Template
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {templates.map((template) => (
              <div key={template.id} className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-md">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-wedo-cyan/15 dark:bg-wedo-cyan/20 rounded-md flex items-center justify-center">
                    <Mail className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-950 dark:text-gray-50">{template.name}</h4>
                    <p className="text-sm text-gray-800 dark:text-gray-200">{template.subject}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-800">
                      <span>Trigger: {template.trigger}</span>
                      <span>•</span>
                      <span>Modificado em {new Date(template.lastModified).toLocaleDateString('pt-BR')}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant={template.status === 'ativo' ? 'default' : 'secondary'}>
                    {template.status}
                  </Badge>
                  <Button variant="outline" size="sm">
                    <Edit className="w-4 h-4 mr-2" />
                    Editar
                  </Button>
                  <Button variant="ghost" size="sm">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Configurações Gerais de Email</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                Nome do Remetente
              </label>
              <input
                type="text"
                defaultValue="Equipe de Recrutamento - Sodexo"
                onChange={() => onSettingsChange(true)}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                Email de Resposta
              </label>
              <input
                type="email"
                defaultValue="recrutamento@sodexo.com.br"
                onChange={() => onSettingsChange(true)}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
              Assinatura Padrão
            </label>
            <textarea
              rows={4}
              defaultValue="Atenciosamente,&#10;Equipe de Recrutamento&#10;Sodexo Brasil&#10;www.sodexo.com.br"
              onChange={() => onSettingsChange(true)}
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderNotifications = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-4 h-4" />
            Configurações de Notificação
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: "newCandidate", label: "Novo candidato se inscreveu", desc: "Notificar recrutadores sobre novas inscrições" },
            { key: "interviewScheduled", label: "Entrevista agendada", desc: "Lembrete para recrutador e candidato" },
            { key: "interviewReminder", label: "Lembrete de entrevista", desc: "Enviar 24h antes da entrevista" },
            { key: "feedbackDue", label: "Prazo de feedback", desc: "Lembrar de dar feedback após entrevistas" },
            { key: "candidateReply", label: "Resposta do candidato", desc: "Quando candidato responde emails" },
            { key: "processDeadline", label: "Prazo do processo", desc: "Alertar sobre prazos de processos seletivos" }
          ].map((notification) => (
            <div key={notification.key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div>
                <div className="text-sm font-medium text-gray-950 dark:text-gray-50">{notification.label}</div>
                <div className="text-xs text-gray-800 dark:text-gray-400">{notification.desc}</div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <input type="checkbox" defaultChecked className="text-gray-600 dark:text-gray-400" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs text-gray-800">Email</span>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" className="text-gray-600 dark:text-gray-400" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs text-gray-800">Push</span>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" className="text-gray-600 dark:text-gray-400" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs text-gray-800">WhatsApp</span>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )

  const renderWhatsApp = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            WhatsApp Business
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-status-success/10 dark:bg-status-success/20 border border-status-success/30 dark:border-status-success/30 rounded-md">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-5 h-5 text-status-success" />
              <span className="font-medium text-status-success dark:text-status-success">WhatsApp Business Conectado</span>
            </div>
            <p className="text-sm text-status-success dark:text-status-success">
              Número: +55 (11) 99999-9999
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                Mensagem de Boas-vindas
              </label>
              <textarea
                rows={3}
                defaultValue="Olá! 👋 Obrigado pelo interesse em nossa vaga. Em breve entraremos em contato."
                onChange={() => onSettingsChange(true)}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                Horário de Atendimento
              </label>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm w-16">Segunda:</span>
                  <input type="time" defaultValue="08:00" className="text-xs" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs">às</span>
                  <input type="time" defaultValue="18:00" className="text-xs" onChange={() => onSettingsChange(true)} />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm w-16">Sexta:</span>
                  <input type="time" defaultValue="08:00" className="text-xs" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs">às</span>
                  <input type="time" defaultValue="17:00" className="text-xs" onChange={() => onSettingsChange(true)} />
                </div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-3">Templates de Mensagem</h4>
            <div className="space-y-2">
              {[
                { name: "Convite para entrevista", message: "Parabéns! Você foi selecionado(a) para a próxima etapa do processo seletivo para a vaga de {vaga}. 🎉" },
                { name: "Lembrete de entrevista", message: "Olá! Lembrando que sua entrevista está agendada para amanhã às {horario}. 📅" },
                { name: "Solicitação de documentos", message: "Para prosseguir com seu processo, precisamos que envie os seguintes documentos: {documentos}" }
              ].map((template, index) => (
                <div key={index} className="p-3 border border-gray-200 dark:border-gray-700 rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{template.name}</span>
                    <Button variant="outline" size="sm">Editar</Button>
                  </div>
                  <p className="text-xs text-gray-800 dark:text-gray-400">{template.message}</p>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSMS = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Phone className="w-4 h-4" />
            SMS
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Phone className="w-12 h-12 text-gray-800 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-950 dark:text-gray-50 mb-2">SMS em Desenvolvimento</h3>
            <p className="text-gray-800 dark:text-gray-200 mb-4">
              Funcionalidade de SMS será disponibilizada em breve
            </p>
            <Button variant="outline">
              Solicitar Acesso Antecipado
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderAutomation = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Automação de Comunicação
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-4">
            {[
              {
                name: "Resposta Automática",
                description: "Enviar email de confirmação ao receber nova inscrição",
                status: "ativo",
                trigger: "Novo candidato"
              },
              {
                name: "Follow-up de Entrevista",
                description: "Solicitar feedback do candidato 2 dias após entrevista",
                status: "ativo",
                trigger: "2 dias após entrevista"
              },
              {
                name: "Lembrete de Prazo",
                description: "Alertar recrutadores sobre feedbacks pendentes",
                status: "pausado",
                trigger: "24h após prazo"
              },
              {
                name: "Reengajamento",
                description: "Contatar candidatos inativos há mais de 30 dias",
                status: "ativo",
                trigger: "30 dias de inatividade"
              }
            ].map((automation, index) => (
              <div key={index} className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-md">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
                    automation.status === 'ativo' ? 'bg-status-success/15 dark:bg-status-success/20' : 'bg-gray-100 dark:bg-gray-800'
                  }`}>
                    <Zap className={`w-5 h-5 ${
                      automation.status === 'ativo' ? 'text-status-success' : 'text-gray-800'
                    }`} />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-950 dark:text-gray-50">{automation.name}</h4>
                    <p className="text-sm text-gray-800 dark:text-gray-200">{automation.description}</p>
                    <p className="text-xs text-gray-800">Trigger: {automation.trigger}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant={automation.status === 'ativo' ? 'default' : 'secondary'}>
                    {automation.status}
                  </Badge>
                  <Button variant="outline" size="sm">
                    Configurar
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <Button className="w-full gap-2" variant="outline">
            <Plus className="w-4 h-4" />
            Nova Automação
          </Button>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Sub Navigation */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-1 overflow-x-auto">
            {subTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm font-medium whitespace-nowrap transition-colors font-crimson ${
                  activeSubTab === tab.id
 ? 'bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-300'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-800 dark:text-gray-200'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.name}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Sub Tab Content */}
      {activeSubTab === 'templates' && renderTemplates()}
      {activeSubTab === 'notifications' && renderNotifications()}
      {activeSubTab === 'whatsapp' && renderWhatsApp()}
      {activeSubTab === 'sms' && renderSMS()}
      {activeSubTab === 'automation' && renderAutomation()}
    </div>
  )
}

  
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
      case 'system': return <Lock className="w-3.5 h-3.5 text-gray-400" />
      case 'default': return <Target className="w-3.5 h-3.5 text-gray-400" />
      case 'custom': return <Settings className="w-3.5 h-3.5 text-gray-400" />
      default: return null
    }
  }

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'system': return 'Sistema'
      case 'default': return 'Padrão'
      case 'custom': return 'Custom'
      default: return ''
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
      color: 'var(--gray-400)',
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
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Pipeline e elegibilidade</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-status-success border-status-success/30 bg-status-success/10 dark:bg-status-success gap-1.5">
                <CheckCircle className="w-3 h-3" />
                Sincronizado
              </Badge>
            </div>
          </div>

          <div className="flex items-center gap-1 mt-4 border-b border-gray-200 dark:border-gray-700">
            {subTabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px",
                  activeSubTab === tab.id
                    ? "border-gray-900 dark:border-gray-50 text-gray-900 dark:text-gray-50"
                    : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
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
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-1">Jornada de Recrutamento</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Visualize as etapas do processo seletivo configuradas.</p>

                <div className="flex items-center gap-6 text-xs text-gray-500 dark:text-gray-400 mb-6 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
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

                <div className="space-y-2">
                  {stages.map((stage, index) => (
                    <div
                      key={stage.name}
                      className={cn(
                        "flex items-center gap-4 p-4 border rounded-md transition-all",
                        stage.isActive
                          ? "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
                          : "border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50 opacity-60"
                      )}
                    >
                      <div className="flex items-center gap-3 min-w-10">
                        <span className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center text-sm font-medium text-gray-600 dark:text-gray-300">
                          {stage.order}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 flex-1">
                        {getCategoryIcon(stage.stageCategory)}
                        <span className="font-medium text-gray-900 dark:text-gray-50">{stage.displayName}</span>
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
                          <span className="text-xs text-gray-400 flex items-center gap-1">
                            <Lock className="w-3 h-3" />
                          </span>
                        ) : (
                          <button
                            onClick={() => toggleStageActive(stage.name)}
                            className={cn(
                              "flex items-center gap-1 text-xs px-2 py-1 rounded transition-colors",
                              stage.isActive
                                ? "text-gray-400 hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error"
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
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Configurações de Perguntas de Elegibilidade</p>
            </div>
          )}

          {activeSubTab === "data-request" && (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <ClipboardList className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Configurações de Solicitação de Dados</p>
            </div>
          )}

          {activeSubTab === "lia-instructions" && (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <Brain className="w-12 h-12 mx-auto mb-3 opacity-30 text-wedo-cyan" />
              <p className="text-sm">Instruções para a LIA</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

  // Componente de Assessment (recuperado)
export function AssessmentTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <ClipboardList className="w-4 h-4" />
            Critérios de Avaliação
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {[
              { categoria: 'Competências Técnicas', peso: 40, criterios: ['Conhecimento específico', 'Experiência prática'] },
              { categoria: 'Soft Skills', peso: 30, criterios: ['Comunicação', 'Liderança'] },
              { categoria: 'Fit Cultural', peso: 20, criterios: ['Alinhamento com valores', 'Adaptabilidade'] },
              { categoria: 'Potencial de Crescimento', peso: 10, criterios: ['Aprendizado contínuo', 'Ambição'] }
            ].map((item, index) => (
              <div key={index} className="p-4 border border-gray-200 dark:border-gray-700 rounded-md">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-gray-950 dark:text-gray-50">
                    {item.categoria}
                  </h4>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={item.peso}
                      onChange={() => onSettingsChange(true)}
                      className="w-16 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm text-center"
                    />
                    <span className="text-sm text-gray-800">%</span>
                  </div>
                </div>
                <div className="space-y-1">
                  {item.criterios.map((criterio, idx) => (
                    <div key={idx} className="text-sm text-gray-800 dark:text-gray-200">
                      • {criterio}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

  // Componente de Automação Workflows Enterprise
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

  // Verificar se tem acesso ao módulo
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
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">Workflows Ativos</p>
                <p className="text-2xl font-bold text-status-success">
                  {workflows.filter(w => w.status === 'active').length}
                </p>
                <p className="text-xs text-gray-800">de {workflows.length} total</p>
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
                <p className="text-sm font-medium text-gray-800">Execuções Hoje</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-50">47</p>
                <p className="text-xs text-status-success">+12% vs ontem</p>
              </div>
              <div className="w-10 h-10 bg-wedo-cyan/15 rounded-md flex items-center justify-center">
                <Zap className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">Taxa de Sucesso</p>
                <p className="text-2xl font-bold text-wedo-orange">97.3%</p>
                <p className="text-xs text-gray-800">últimos 7 dias</p>
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
                <p className="text-sm font-medium text-gray-800">Templates</p>
                <p className="text-2xl font-bold text-wedo-purple">12</p>
                <p className="text-xs text-gray-800">pré-configurados</p>
              </div>
              <div className="w-10 h-10 bg-wedo-purple/15 rounded-md flex items-center justify-center">
                <FileText className="w-5 h-5 text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Workflows List */}
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
              <div key={workflow.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-md hover:transition-shadow">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
                    workflow.status === 'active' ? 'bg-status-success/15' : 'bg-gray-100'
                  }`}>
                    <Workflow className={`w-5 h-5 ${
                      workflow.status === 'active' ? 'text-status-success' : 'text-gray-800'
                    }`} />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-950">{workflow.name}</h4>
                    <p className="text-sm text-gray-800">{workflow.description}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-800">
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

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Ações Rápidas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-auto p-4 justify-start gap-3">
              <Plus className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <div className="text-left">
                <div className="font-medium">Criar Workflow</div>
                <div className="text-sm text-gray-800">Do zero ou usando template</div>
              </div>
            </Button>

            <Button variant="outline" className="h-auto p-4 justify-start gap-3">
              <Download className="w-5 h-5 text-status-success" />
              <div className="text-left">
                <div className="font-medium">Importar Template</div>
                <div className="text-sm text-gray-800">Da biblioteca de templates</div>
              </div>
            </Button>

            <Button variant="outline" className="h-auto p-4 justify-start gap-3">
              <BarChart3 className="w-5 h-5 text-wedo-purple" />
              <div className="text-left">
                <div className="font-medium">Ver Analytics</div>
                <div className="text-sm text-gray-800">Performance detalhada</div>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderBuilder = () => (
    <div className="text-center py-12">
      <Workflow className="w-12 h-12 text-gray-800 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-950 mb-2">Workflow Builder Visual</h3>
      <p className="text-gray-800">Interface de arrastar e soltar para criar workflows</p>
    </div>
  )

  const renderTemplates = () => (
    <div className="text-center py-12">
      <FileText className="w-12 h-12 text-gray-800 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-950 mb-2">Biblioteca de Templates</h3>
      <p className="text-gray-800">Templates pré-configurados para casos comuns</p>
    </div>
  )

  const renderLogs = () => (
    <div className="text-center py-12">
      <Activity className="w-12 h-12 text-gray-800 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-950 mb-2">Logs de Execução</h3>
      <p className="text-gray-800">Histórico detalhado de todas as execuções</p>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-950 flex items-center gap-2">
            <Workflow className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            Automação Workflows Enterprise
          </h2>
          <p className="text-sm text-gray-800">
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

      {/* Navigation Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-md w-fit">
        {[
          { id: 'overview', label: 'Visão Geral', icon: BarChart3 },
          { id: 'builder', label: 'Builder', icon: Workflow },
          { id: 'templates', label: 'Templates', icon: FileText },
          { id: 'logs', label: 'Logs', icon: Activity }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setSelectedView(tab.id as any)}
            className={`flex items-center gap-2 px-3 py-3 rounded-md text-sm font-medium transition-colors font-crimson ${
              selectedView === tab.id
                ? 'bg-white text-gray-950'
                : 'text-gray-800 hover:text-gray-950'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {selectedView === 'overview' && renderOverview()}
      {selectedView === 'builder' && renderBuilder()}
      {selectedView === 'templates' && renderTemplates()}
      {selectedView === 'logs' && renderLogs()}
    </div>
  )
}

  // Componente de NPS (recuperado)
export function NPSTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Star className="w-4 h-4" />
            Configurações do Sistema NPS
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Escala de NPS
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              >
                <option>0-10 (Padrão NPS)</option>
                <option>1-5 (Simplificado)</option>
                <option>1-10 (Personalizado)</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Frequência de Envio
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              >
                <option>Após cada processo seletivo</option>
                <option>Semanal</option>
                <option>Mensal</option>
                <option>Trimestral</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
              Pergunta Principal
            </label>
            <textarea
              rows={3}
              defaultValue="De 0 a 10, o quanto você recomendaria nossa empresa como um lugar para trabalhar?"
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
  