"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Mail, Bell, MessageSquare, Phone, Zap, Plus, Edit,
  MoreVertical, CheckCircle,
} from "lucide-react"

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
              <div key={template.id} className="flex items-center justify-between p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-wedo-cyan/15 dark:bg-wedo-cyan/20 rounded-md flex items-center justify-center">
                    <Mail className="w-5 h-5 text-lia-text-secondary" />
                  </div>
                  <div>
                    <h4 className="font-medium text-lia-text-primary">{template.name}</h4>
                    <p className="text-sm text-lia-text-primary">{template.subject}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-lia-text-primary">
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
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">
                Nome do Remetente
              </label>
              <input
                type="text"
                defaultValue="Equipe de Recrutamento - Sodexo"
                onChange={() => onSettingsChange(true)}
                className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">
                Email de Resposta
              </label>
              <input
                type="email"
                defaultValue="recrutamento@sodexo.com.br"
                onChange={() => onSettingsChange(true)}
                className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-2 block">
              Assinatura Padrão
            </label>
            <textarea
              rows={4}
              defaultValue="Atenciosamente,&#10;Equipe de Recrutamento&#10;Sodexo Brasil&#10;www.sodexo.com.br"
              onChange={() => onSettingsChange(true)}
              className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
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
            <div key={notification.key} className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
              <div>
                <div className="text-sm font-medium text-lia-text-primary">{notification.label}</div>
                <div className="text-xs text-lia-text-primary">{notification.desc}</div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <input type="checkbox" defaultChecked className="text-lia-text-secondary" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs text-lia-text-primary">Email</span>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" className="text-lia-text-secondary" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs text-lia-text-primary">Push</span>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" className="text-lia-text-secondary" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs text-lia-text-primary">WhatsApp</span>
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
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">
                Mensagem de Boas-vindas
              </label>
              <textarea
                rows={3}
                defaultValue="Olá! 👋 Obrigado pelo interesse em nossa vaga. Em breve entraremos em contato."
                onChange={() => onSettingsChange(true)}
                className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">
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
            <h4 className="font-medium text-lia-text-primary mb-3">Templates de Mensagem</h4>
            <div className="space-y-2">
              {[
                { name: "Convite para entrevista", message: "Parabéns! Você foi selecionado(a) para a próxima etapa do processo seletivo para a vaga de {vaga}. 🎉" },
                { name: "Lembrete de entrevista", message: "Olá! Lembrando que sua entrevista está agendada para amanhã às {horario}. 📅" },
                { name: "Solicitação de documentos", message: "Para prosseguir com seu processo, precisamos que envie os seguintes documentos: {documentos}" }
              ].map((template) => (
                <div key={template.name} className="p-3 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{template.name}</span>
                    <Button variant="outline" size="sm">Editar</Button>
                  </div>
                  <p className="text-xs text-lia-text-primary">{template.message}</p>
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
            <Phone className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
            <h3 className="text-lg font-medium text-lia-text-primary mb-2">SMS em Desenvolvimento</h3>
            <p className="text-lia-text-primary mb-4">
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
              <div key={`auto-${index}`} className="flex items-center justify-between p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
                    automation.status === 'ativo' ? 'bg-status-success/15 dark:bg-status-success/20' : 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary'
                  }`}>
                    <Zap className={`w-5 h-5 ${
                      automation.status === 'ativo' ? 'text-status-success' : 'text-lia-text-primary'
                    }`} />
                  </div>
                  <div>
                    <h4 className="font-medium text-lia-text-primary">{automation.name}</h4>
                    <p className="text-sm text-lia-text-primary">{automation.description}</p>
                    <p className="text-xs text-lia-text-primary">Trigger: {automation.trigger}</p>
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
                onClick={() => setActiveSubTab(tab.id as Parameters<typeof setActiveSubTab>[0])}
                className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm font-medium whitespace-nowrap transition-colors motion-reduce:transition-none font-crimson ${
                  activeSubTab === tab.id
                    ? 'bg-lia-bg-secondary dark:bg-lia-bg-secondary text-lia-text-primary'
                    : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover text-lia-text-primary'
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
