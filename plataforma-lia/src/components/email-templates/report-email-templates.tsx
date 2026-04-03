"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {  X, Mail, Send, Eye, Edit, Copy, FileText, Users, BarChart3,
  Calendar, Clock, Target, TrendingUp, AlertTriangle, CheckCircle,
  Download, Share2, Building, MapPin, DollarSign, Star, Heart,
  User, Phone, MessageSquare, ExternalLink, Settings, RefreshCw,
  ChevronDown, ChevronUp, Plus, Trash2, Save
} from "lucide-react"
import { sanitizeEmailHtml } from "@/lib/sanitize"

interface EmailTemplate {
  id: string
  name: string
  subject: string
  type: 'summary' | 'detailed' | 'executive' | 'weekly' | 'custom'
  htmlContent: string
  textContent: string
  variables: string[]
  isDefault: boolean
  createdAt: string
  lastUsed?: string
  previewImage?: string
}

interface JobReportFunnel {
  total: number
  screening: number
  interview: number
  final: number
  hired: number
}

interface JobReportData {
  title: string
  jobId: string
  manager: string
  department: string
  nps: number
  funnel: JobReportFunnel
  [key: string]: unknown
}

interface EmailTemplateModalProps {
  isOpen: boolean
  onClose: () => void
  jobData: JobReportData
  onSend: (template: EmailTemplate, recipients: string[], customizations: Record<string, unknown>) => void
}

const emailTemplates: EmailTemplate[] = [
  {
    id: 'executive-summary',
    name: 'Resumo Executivo',
    subject: '📊 Relatório Executivo - {{jobTitle}} ({{jobId}})',
    type: 'executive',
    variables: ['jobTitle', 'jobId', 'totalCandidates', 'hiredCandidates', 'timeToHire', 'managerName', 'conversionRate', 'npsScore'],
    isDefault: true,
    createdAt: '2024-01-01T10:00:00Z',
    lastUsed: '2024-01-15T14:30:00Z',
    htmlContent: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; color: white; text-align: center;">
          <h1 style="margin: 0; font-size: 24px; font-weight: bold;">Relatório Executivo</h1>
          <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">{{jobTitle}} - {{jobId}}</p>
        </div>

        <div style="padding: 30px;">
          <div style="margin-bottom: 30px;">
            <h2 style="color: #333; font-size: 20px; margin-bottom: 15px;">📈 Indicadores Principais</h2>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
              <div style="background: #f8f9ff; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #667eea;">
                <div style="font-size: 28px; font-weight: bold; color: #667eea;">{{totalCandidates}}</div>
                <div style="color: #6b7280; font-size: 14px;">Total de Candidatos</div>
              </div>

              <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #22c55e;">
                <div style="font-size: 28px; font-weight: bold; color: #22c55e;">{{conversionRate}}%</div>
                <div style="color: #6b7280; font-size: 14px;">Taxa de Conversão</div>
              </div>

              <div style="background: #fef3f2; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #ef4444;">
                <div style="font-size: 28px; font-weight: bold; color: #ef4444;">{{timeToHire}}</div>
                <div style="color: #6b7280; font-size: 14px;">Dias (Time to Hire)</div>
              </div>

              <div style="background: #fefbf3; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #f59e0b;">
                <div style="font-size: 28px; font-weight: bold; color: #f59e0b;">{{npsScore}}%</div>
                <div style="color: #6b7280; font-size: 14px;">NPS Score</div>
              </div>
            </div>
          </div>

          <div style="margin-bottom: 30px;">
            <h3 style="color: #333; font-size: 18px; margin-bottom: 15px;">🎯 Principais Insights</h3>
            <ul style="color: #555; line-height: 1.6;">
              <li>Performance da vaga está <strong>{{performance_status}}</strong> em relação à média</li>
              <li>{{insight_1}}</li>
              <li>{{insight_2}}</li>
            </ul>
          </div>

          <div style="background: #f1f5f9; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
            <h3 style="color: #334155; margin-top: 0;">📋 Próximos Passos Recomendados</h3>
            <ol style="color: #475569; line-height: 1.6; margin: 0;">
              <li>{{recommendation_1}}</li>
              <li>{{recommendation_2}}</li>
              <li>{{recommendation_3}}</li>
            </ol>
          </div>

          <div style="text-align: center; margin-top: 30px;">
            <a href="{{dashboard_link}}" style="background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
              Ver Relatório Completo
            </a>
          </div>
        </div>

        <div style="background: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
          <p style="margin: 0; color: #64748b; font-size: 12px;">
            Relatório gerado pela Plataforma LIA em {{generated_date}}<br>
            © 2024 WeDO Talent - Todos os direitos reservados
          </p>
        </div>
      </div>
    `,
    textContent: `RELATÓRIO EXECUTIVO - {{jobTitle}} ({{jobId}})

INDICADORES PRINCIPAIS:
- Total de Candidatos: {{totalCandidates}}
- Taxa de Conversão: {{conversionRate}}%
- Time to Hire: {{timeToHire}} dias
- NPS Score: {{npsScore}}%

INSIGHTS:
- Performance da vaga está {{performance_status}} em relação à média
- {{insight_1}}
- {{insight_2}}

PRÓXIMOS PASSOS:
1. {{recommendation_1}}
2. {{recommendation_2}}
3. {{recommendation_3}}

Acesse o relatório completo em: {{dashboard_link}}

---
Relatório gerado pela Plataforma LIA em {{generated_date}}
© 2024 WeDO Talent`
  },
  {
    id: 'detailed-analysis',
    name: 'Análise Detalhada',
    subject: '🔍 Análise Detalhada - {{jobTitle}} | Performance e Insights',
    type: 'detailed',
    variables: ['jobTitle', 'jobId', 'totalCandidates', 'funnel_screening', 'funnel_interview', 'funnel_final', 'funnel_hired', 'source_linkedin', 'source_referrals', 'source_website', 'manager_name', 'department'],
    isDefault: true,
    createdAt: '2024-01-01T10:00:00Z',
    htmlContent: `
      <div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto; background: #ffffff;">
        <div style="background: linear-gradient(135deg, #111827 0%, #1F2937 100%); padding: 25px; color: white;">
          <h1 style="margin: 0; font-size: 22px;">🔍 Análise Detalhada</h1>
          <p style="margin: 8px 0 0 0; opacity: 0.9;">{{jobTitle}} - Departamento {{department}}</p>
        </div>

        <div style="padding: 25px;">
          <div style="margin-bottom: 25px;">
            <h2 style="color: #1f2937; font-size: 18px; margin-bottom: 12px;">📊 Funil de Recrutamento</h2>
            <div style="background: #f9fafb; padding: 15px; border-radius: 6px;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span>Candidatos Totais:</span><strong>{{totalCandidates}}</strong>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span>Triagem:</span><strong>{{funnel_screening}} ({{screening_rate}}%)</strong>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span>Entrevistas:</span><strong>{{funnel_interview}} ({{interview_rate}}%)</strong>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span>Fase Final:</span><strong>{{funnel_final}} ({{final_rate}}%)</strong>
              </div>
              <div style="display: flex; justify-content: space-between; color: #059669;">
                <span><strong>Contratados:</strong></span><strong>{{funnel_hired}} ({{hired_rate}}%)</strong>
              </div>
            </div>
          </div>

          <div style="margin-bottom: 25px;">
            <h3 style="color: #1f2937; font-size: 16px; margin-bottom: 12px;">🎯 Efetividade por Fonte</h3>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
              <div style="text-align: center; padding: 12px; background: #E0F4F7; border-radius: 6px;">
                <div style="font-weight: bold; color: #4DA8BB;">{{source_linkedin}}%</div>
                <div style="font-size: 12px; color: #64748b;">LinkedIn</div>
              </div>
              <div style="text-align: center; padding: 12px; background: #dcfce7; border-radius: 6px;">
                <div style="font-weight: bold; color: #16a34a;">{{source_referrals}}%</div>
                <div style="font-size: 12px; color: #64748b;">Indicações</div>
              </div>
              <div style="text-align: center; padding: 12px; background: #fef3c7; border-radius: 6px;">
                <div style="font-weight: bold; color: #d97706;">{{source_website}}%</div>
                <div style="font-size: 12px; color: #64748b;">Website</div>
              </div>
            </div>
          </div>

          <div style="background: #E0F4F7; padding: 15px; border-radius: 6px; border-left: 4px solid #D1D5DB;">
            <h4 style="margin-top: 0; color: #4DA8BB;">💡 Recomendações Específicas:</h4>
            <ul style="margin: 0; color: #374151;">
              <li>{{specific_recommendation_1}}</li>
              <li>{{specific_recommendation_2}}</li>
              <li>{{specific_recommendation_3}}</li>
            </ul>
          </div>
        </div>

        <div style="background: #f8fafc; padding: 15px; text-align: center; font-size: 11px; color: #64748b;">
          Enviado para {{manager_name}} | {{generated_date}}
        </div>
      </div>
    `,
    textContent: `ANÁLISE DETALHADA - {{jobTitle}}

FUNIL DE RECRUTAMENTO:
- Candidatos Totais: {{totalCandidates}}
- Triagem: {{funnel_screening}} ({{screening_rate}}%)
- Entrevistas: {{funnel_interview}} ({{interview_rate}}%)
- Fase Final: {{funnel_final}} ({{final_rate}}%)
- Contratados: {{funnel_hired}} ({{hired_rate}}%)

EFETIVIDADE POR FONTE:
- LinkedIn: {{source_linkedin}}%
- Indicações: {{source_referrals}}%
- Website: {{source_website}}%

RECOMENDAÇÕES:
- {{specific_recommendation_1}}
- {{specific_recommendation_2}}
- {{specific_recommendation_3}}

Enviado para {{manager_name}} | {{generated_date}}`
  },
  {
    id: 'weekly-digest',
    name: 'Digest Semanal',
    subject: '📅 Resumo Semanal - {{week_period}} | Atualizações de Vagas',
    type: 'weekly',
    variables: ['week_period', 'total_applications', 'new_interviews', 'completed_hires', 'top_performing_job', 'attention_needed', 'next_week_focus'],
    isDefault: false,
    createdAt: '2024-01-05T10:00:00Z',
    htmlContent: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #059669; padding: 20px; color: white; text-align: center;">
          <h1 style="margin: 0; font-size: 20px;">📅 Resumo Semanal</h1>
          <p style="margin: 5px 0 0 0;">{{week_period}}</p>
        </div>

        <div style="padding: 20px;">
          <div style="margin-bottom: 20px;">
            <h2 style="color: #065f46; font-size: 16px;">📈 Números da Semana</h2>
            <div style="background: #f0fdf4; padding: 15px; border-radius: 6px;">
              <p style="margin: 0;"><strong>{{total_applications}}</strong> novas candidaturas</p>
              <p style="margin: 5px 0;"><strong>{{new_interviews}}</strong> entrevistas agendadas</p>
              <p style="margin: 5px 0 0 0;"><strong>{{completed_hires}}</strong> contratações finalizadas</p>
            </div>
          </div>

          <div style="margin-bottom: 20px;">
            <h3 style="color: #065f46; font-size: 14px;">🏆 Destaque da Semana</h3>
            <p style="background: #ecfdf5; padding: 12px; border-radius: 4px; margin: 0;">
              {{top_performing_job}}
            </p>
          </div>

          <div style="margin-bottom: 20px;">
            <h3 style="color: #dc2626; font-size: 14px;">⚠️ Precisa de Atenção</h3>
            <p style="background: #fef2f2; padding: 12px; border-radius: 4px; margin: 0; color: #991b1b;">
              {{attention_needed}}
            </p>
          </div>

          <div>
            <h3 style="color: #4DA8BB; font-size: 14px;">🎯 Foco para Próxima Semana</h3>
            <p style="background: #E0F4F7; padding: 12px; border-radius: 4px; margin: 0; color: #4DA8BB;">
              {{next_week_focus}}
            </p>
          </div>
        </div>
      </div>
    `,
    textContent: `RESUMO SEMANAL - {{week_period}}

NÚMEROS DA SEMANA:
- {{total_applications}} novas candidaturas
- {{new_interviews}} entrevistas agendadas
- {{completed_hires}} contratações finalizadas

DESTAQUE: {{top_performing_job}}

ATENÇÃO NECESSÁRIA: {{attention_needed}}

FOCO PRÓXIMA SEMANA: {{next_week_focus}}`
  }
]

const suggestedRecipients = [
  { name: 'Pedro Silva', email: 'pedro.silva@empresa.com', role: 'Gestor', department: 'Tech' },
  { name: 'Ana Costa', email: 'ana.costa@empresa.com', role: 'Diretora de RH', department: 'RH' },
  { name: 'Carlos Mendes', email: 'carlos.mendes@empresa.com', role: 'Recrutador', department: 'RH' },
  { name: 'Juliana Oliveira', email: 'juliana.oliveira@empresa.com', role: 'CEO', department: 'Executivo' }
]

export function EmailTemplateModal({ isOpen, onClose, jobData, onSend }: EmailTemplateModalProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate>(emailTemplates[0])
  const [recipients, setRecipients] = useState<string[]>([])
  const [customSubject, setCustomSubject] = useState('')
  const [customizations, setCustomizations] = useState<Record<string, string>>({})
  const [showPreview, setShowPreview] = useState(false)
  const [activeTab, setActiveTab] = useState<'templates' | 'recipients' | 'customize' | 'preview'>('templates')
  const [isSending, setIsSending] = useState(false)

  if (!isOpen) return null

  const processTemplate = (content: string, variables: Record<string, string>) => {
    let processed = content
    Object.entries(variables).forEach(([key, value]) => {
      const regex = new RegExp(`{{${key}}}`, 'g')
      processed = processed.replace(regex, value)
    })
    return processed
  }

  const getTemplateVariables = () => {
    const { funnel } = jobData
    const baseVariables = {
      jobTitle: jobData.title,
      jobId: jobData.jobId,
      totalCandidates: funnel.total.toString(),
      hiredCandidates: funnel.hired.toString(),
      timeToHire: '28',
      managerName: jobData.manager,
      conversionRate: Math.round((funnel.hired / funnel.total) * 100).toString(),
      npsScore: jobData.nps.toString(),
      department: jobData.department,
      generated_date: new Date().toLocaleDateString('pt-BR'),
      dashboard_link: 'https://app.wedotalent.com/jobs/' + jobData.jobId,
      // Adicionar mais variáveis baseadas no template selecionado
      ...customizations
    }

    // Adicionar variáveis específicas do template
    if (selectedTemplate.id === 'detailed-analysis') {
      return {
        ...baseVariables,
        funnel_screening: funnel.screening.toString(),
        funnel_interview: funnel.interview.toString(),
        funnel_final: funnel.final.toString(),
        funnel_hired: funnel.hired.toString(),
        screening_rate: Math.round((funnel.screening / funnel.total) * 100).toString(),
        interview_rate: Math.round((funnel.interview / funnel.total) * 100).toString(),
        final_rate: Math.round((funnel.final / funnel.total) * 100).toString(),
        hired_rate: Math.round((funnel.hired / funnel.total) * 100).toString(),
        source_linkedin: '45',
        source_referrals: '23',
        source_website: '18',
        specific_recommendation_1: 'Otimizar sourcing no LinkedIn para aumentar volume qualificado',
        specific_recommendation_2: 'Implementar programa de indicações com incentivos',
        specific_recommendation_3: 'Revisar critérios de triagem para melhorar taxa de conversão'
      }
    }

    if (selectedTemplate.id === 'weekly-digest') {
      return {
        ...baseVariables,
        week_period: 'Semana de 15 a 21 de Janeiro',
        total_applications: '156',
        new_interviews: '23',
        completed_hires: '4',
        top_performing_job: 'UX Designer Sênior com 89% de taxa de conversão',
        attention_needed: 'Desenvolvedor Full Stack com apenas 12% de conversão - revisar requisitos',
        next_week_focus: 'Intensificar sourcing para vagas de tecnologia e revisar pipeline de design'
      }
    }

    return baseVariables
  }

  const handleSend = async () => {
    setIsSending(true)

    try {
      await new Promise(resolve => setTimeout(resolve, 2000)) // Simular envio

      const finalTemplate = {
        ...selectedTemplate,
        subject: customSubject || selectedTemplate.subject
      }

      onSend(finalTemplate, recipients, customizations)
      onClose()
    } catch (error) {
    } finally {
      setIsSending(false)
    }
  }

  const addRecipient = (email: string) => {
    if (!recipients.includes(email)) {
      setRecipients([...recipients, email])
    }
  }

  const removeRecipient = (email: string) => {
    setRecipients(recipients.filter(r => r !== email))
  }

  const processedSubject = processTemplate(customSubject || selectedTemplate.subject, getTemplateVariables() as Record<string, string>)
  const processedContent = processTemplate(selectedTemplate.htmlContent, getTemplateVariables() as Record<string, string>)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary rounded-md w-full max-w-5xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6">
          <div>
            <h2 className="text-xl font-semibold text-lia-text-primary">
              Templates de Email para Relatórios
            </h2>
            <p className="text-sm text-lia-text-primary">
              Vaga: {jobData.title as string} ({jobData.jobId as string})
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isSending ? (
              <Button disabled className="gap-2">
                <RefreshCw className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                Enviando...
              </Button>
            ) : (
              <Button
                onClick={handleSend}
                disabled={recipients.length === 0}
                className="gap-2"
              >
                <Send className="w-4 h-4" />
                Enviar ({recipients.length})
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          {[
            { id: 'templates', label: 'Templates', icon: FileText },
            { id: 'recipients', label: 'Destinatários', icon: Users },
            { id: 'customize', label: 'Personalizar', icon: Edit },
            { id: 'preview', label: 'Pré-visualizar', icon: Eye }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors motion-reduce:transition-none ${
 activeTab === tab.id
                  ? 'text-lia-text-secondary border-b-2 border-lia-btn-primary-bg bg-lia-bg-tertiary dark:bg-lia-bg-secondary'
                  : 'text-lia-text-secondary hover:text-lia-text-primary'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
              {tab.id === 'recipients' && recipients.length > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {recipients.length}
                </Badge>
              )}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'templates' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {emailTemplates.map((template) => (
                <Card
                  key={template.id}
                  className={`cursor-pointer transition-colors motion-reduce:transition-none hover:${
 selectedTemplate.id === template.id ? 'ring-2 ring-lia-btn-primary-bg/20 dark:ring-lia-border-subtle/20 bg-lia-bg-tertiary dark:bg-lia-bg-secondary' : ''
                  }`}
                  onClick={() => setSelectedTemplate(template)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium text-lia-text-primary">{template.name}</h3>
                      {template.isDefault && (
                        <Badge variant="secondary" className="text-xs">Padrão</Badge>
                      )}
                    </div>
                    <p className="text-sm text-lia-text-primary mb-3">
                      {processTemplate(template.subject, getTemplateVariables() as Record<string, string>)}
                    </p>
                    <div className="flex items-center justify-between">
                      <Badge
                        className={`text-xs ${
 template.type === 'executive' ? 'bg-wedo-purple/10 text-wedo-purple' :
                          template.type === 'detailed' ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary' :
                          template.type === 'weekly' ? 'bg-status-success/10 text-status-success' :
                          'bg-lia-bg-tertiary text-lia-text-primary'
                        }`}
                      >
                        {template.type}
                      </Badge>
                      {template.lastUsed && (
                        <span className="text-xs text-lia-text-secondary">
                          Usado em {new Date(template.lastUsed).toLocaleDateString('pt-BR')}
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {activeTab === 'recipients' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-lia-text-primary mb-4">Destinatários Sugeridos</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {suggestedRecipients.map((person) => (
                    <div
                      key={person.email}
                      className="flex items-center justify-between p-3 rounded-md hover:bg-lia-bg-secondary"
                    >
                      <div className="flex items-center gap-3">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary text-xs">
                            {person.name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-medium text-lia-text-primary text-sm">{person.name}</div>
                          <div className="text-xs text-lia-text-primary">{person.role} • {person.department}</div>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant={recipients.includes(person.email) ? "default" as const : "outline" as const}
                        onClick={() => {
                          if (recipients.includes(person.email)) {
                            removeRecipient(person.email)
                          } else {
                            addRecipient(person.email)
                          }
                        }}
                        className="gap-1"
                      >
                        {recipients.includes(person.email) ? (
                          <>
                            <CheckCircle className="w-3 h-3" />
                            Adicionado
                          </>
                        ) : (
                          <>
                            <Plus className="w-3 h-3" />
                            Adicionar
                          </>
                        )}
                      </Button>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-lia-text-primary mb-4">Adicionar Email Personalizado</h3>
                <div className="flex gap-2">
                  <input
                    type="email"
                    placeholder="email@empresa.com"
                    className="flex-1 px-3 py-2 border border-lia-border-default rounded-md"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        const email = (e.target as HTMLInputElement).value
                        if (email && !recipients.includes(email)) {
                          addRecipient(email)
                          ;(e.target as HTMLInputElement).value = ''
                        }
                      }
                    }}
                  />
                  <Button variant="outline">
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {recipients.length > 0 && (
                <div>
                  <h3 className="text-lg font-medium text-lia-text-primary mb-4">
                    Destinatários Selecionados ({recipients.length})
                  </h3>
                  <div className="space-y-2">
                    {recipients.map((email) => (
                      <div key={email} className="flex items-center justify-between p-2 bg-lia-bg-secondary rounded-md">
                        <span className="text-sm text-lia-text-primary">{email}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeRecipient(email)}
                        >
                          <X className="w-3 h-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'customize' && (
            <div className="space-y-6">
              <div>
                <label className="text-sm font-medium text-lia-text-primary mb-2 block">
                  Assunto do Email
                </label>
                <input
                  type="text"
                  value={customSubject}
                  onChange={(e) => setCustomSubject(e.target.value)}
                  placeholder={selectedTemplate.subject}
                  className="w-full px-3 py-2 border border-lia-border-default rounded-md"
                />
                <p className="text-xs text-lia-text-secondary mt-1">
                  Pré-visualização: {processedSubject}
                </p>
              </div>

              <div>
                <label className="text-sm font-medium text-lia-text-primary mb-2 block">
                  Variáveis Personalizadas
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {selectedTemplate.variables.map((variable) => (
                    <div key={variable}>
                      <label className="text-xs text-lia-text-secondary mb-1 block capitalize">
                        {variable.replace(/_/g, ' ')}
                      </label>
                      <input
                        type="text"
                        value={customizations[variable] || ''}
                        onChange={(e) => setCustomizations(prev => ({
                          ...prev,
                          [variable]: e.target.value
                        }))}
                        placeholder={`{{${variable}}}`}
                        className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default rounded-md p-4">
                <h4 className="font-medium text-wedo-cyan-dark mb-2">💡 Dicas de Personalização</h4>
                <ul className="text-sm text-lia-text-secondary space-y-1">
                  <li>• Use variáveis para tornar o email mais relevante</li>
                  <li>• Personalize o assunto para aumentar taxa de abertura</li>
                  <li>• Adicione insights específicos sobre a performance</li>
                  <li>• Inclua próximos passos acionáveis</li>
                </ul>
              </div>
            </div>
          )}

          {activeTab === 'preview' && (
            <div className="space-y-4">
              <div className="bg-lia-bg-secondary rounded-md p-4 border">
                <div className="flex items-center gap-2 mb-2">
                  <Mail className="w-4 h-4 text-lia-text-secondary" />
                  <strong className="text-sm">Assunto:</strong>
                </div>
                <p className="text-sm text-lia-text-primary font-medium">{processedSubject}</p>
              </div>

              <div className="flex gap-2">
                <Button
                  variant={showPreview ? "outline" as const : "default" as const}
                  size="sm"
                  onClick={() => setShowPreview(false)}
                >
                  HTML
                </Button>
                <Button
                  variant={showPreview ? "default" as const : "outline" as const}
                  size="sm"
                  onClick={() => setShowPreview(true)}
                >
                  Texto
                </Button>
              </div>

              <div className="border border-lia-border-subtle rounded-md overflow-hidden">
                {showPreview ? (
                  <div className="p-4 bg-lia-bg-secondary font-mono text-sm whitespace-pre-wrap">
                    {processTemplate(selectedTemplate.textContent, getTemplateVariables() as Record<string, string>)}
                  </div>
                ) : (
                  <div
                    className="p-4 bg-lia-bg-primary"
                    dangerouslySetInnerHTML={{
                      __html: sanitizeEmailHtml(processedContent)
                    }}
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
