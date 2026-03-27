"use client"

import React, { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Mail, Phone, MessageSquare, Calendar, Heart, Star, Send, Copy,
  X, Check, Clock, User, Briefcase, MapPin, ExternalLink,
  Users, FileText, Zap, Video, AlertCircle, CheckCircle,
  Edit, Trash2, Plus, Filter, Search, MoreVertical,
  Share2, Download, Upload, Eye, ChevronRight, Building,
  Globe, Linkedin, Facebook, Instagram, Twitter, Youtube,
  Calendar as CalendarIcon, Brain, RefreshCw, Info
} from "lucide-react"
import { liaApi } from "@/services/lia-api"
import { useToast } from "@/hooks/use-toast"
import { textStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"

// Interfaces
interface Candidate {
  id: string
  name: string
  role: string
  email: string
  phone: string
  location: string
  avatar?: string
  score: number
  status: string
  matchPercentage: number
  riskLevel: string
  culturalFit: number
  technicalMatch: number
  experience: string
  seniority: string
  availability: string
  expectedSalary: string
  preferredLocation: string
  linkedin?: string
  portfolio?: string
  skills: string[]
  lastActivity: string
  source: string
}

interface ContactModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate | null
  onSend: (type: string, message: string, recipient: string) => void
  initialAction?: 'general' | 'wsi_screening' | 'interview_invite'
  jobTitle?: string
}

interface ScheduleModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate | null
  onSchedule: (type: string, datetime: string, details: any) => void
}

interface FavoriteModalProps {
  isOpen: boolean
  onClose: () => void
  candidates: Candidate[]
  onToggleFavorite: (candidateId: string) => void
  onCreateList: (name: string, candidateIds: string[]) => void
}

interface BatchActionModalProps {
  isOpen: boolean
  onClose: () => void
  selectedCandidates: Candidate[]
  onBatchAction: (action: string, data: any) => void
}

interface QuickViewModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate | null
  onNavigateToFull: (candidateId: string) => void
}

// Modal de Contato
export function ContactModal({ isOpen, onClose, candidate, onSend, initialAction, jobTitle }: ContactModalProps) {
  const [activeTab, setActiveTab] = useState<'email' | 'whatsapp' | 'phone'>('email')
  const [message, setMessage] = useState('')
  const [subject, setSubject] = useState('')
  const [templateType, setTemplateType] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isLiaGenerating, setIsLiaGenerating] = useState(false)
  const [showLiaSuggestions, setShowLiaSuggestions] = useState(false)
  const [liaSuggestions, setLiaSuggestions] = useState<any[]>([])
  const [liaContext, setLiaContext] = useState<'professional' | 'warm' | 'urgent' | 'follow_up'>('professional')
  const [initialized, setInitialized] = useState(false)
  const [apiTemplates, setApiTemplates] = useState<any[]>([])
  const [loadingTemplates, setLoadingTemplates] = useState(true)
  const { toast } = useToast()

  const roleOrJob = jobTitle || candidate?.role || 'a vaga'

  const replaceTemplateVariables = (text: string) => {
    if (!text || !candidate) return text
    return text
      .replace(/\{\{candidate_name\}\}/g, candidate.name)
      .replace(/\{\{candidato_nome\}\}/g, candidate.name)
      .replace(/\{\{job_title\}\}/g, roleOrJob)
      .replace(/\{\{vaga\}\}/g, roleOrJob)
      .replace(/\{\{company_name\}\}/g, 'Nossa Empresa')
      .replace(/\{\{empresa_nome\}\}/g, 'Nossa Empresa')
  }

  const fallbackEmailTemplates = candidate ? [
    {
      id: 'wsi_screening',
      name: '📋 Triagem WSI (Work Sample)',
      subject: `Próximo passo: Avaliação prática - ${roleOrJob}`,
      message: `Olá ${candidate.name},\n\nEsperamos que esteja bem!\n\nEstamos avançando em nosso processo seletivo para a posição de ${roleOrJob} e gostaríamos de convidá-lo(a) para a próxima etapa: uma avaliação prática (Work Sample Interview).\n\n📋 **Sobre a avaliação:**\n• Duração estimada: 15-20 minutos\n• Formato: Perguntas práticas sobre situações reais da função\n• Objetivo: Conhecer melhor sua forma de pensar e resolver problemas\n\n🔗 **Para iniciar, basta clicar no link abaixo:**\n[INSERIR LINK DA TRIAGEM]\n\nEssa avaliação nos ajuda a entender melhor seu perfil e garantir que a vaga seja compatível com suas habilidades e expectativas.\n\nQualquer dúvida, estamos à disposição!\n\nAtenciosamente,\nEquipe de Recrutamento`,
      isWsi: true
    },
    {
      id: 'interview_invite',
      name: 'Convite para Entrevista',
      subject: `Oportunidade de emprego - ${roleOrJob}`,
      message: `Olá ${candidate.name},\n\nTemos uma excelente oportunidade que pode ser do seu interesse. Gostaríamos de convidá-lo(a) para uma conversa sobre a posição de ${roleOrJob}.\n\nPodemos agendar uma conversa?\n\nAguardo seu retorno.\n\nAtenciosamente,\nEquipe de Recrutamento`
    },
    {
      id: 'follow_up',
      name: 'Follow-up',
      subject: `Acompanhamento - ${roleOrJob}`,
      message: `Olá ${candidate.name},\n\nEspero que esteja bem! Gostaria de fazer um acompanhamento sobre sua candidatura para a posição de ${roleOrJob}.\n\nTem alguma dúvida sobre o processo ou a vaga?\n\nFico à disposição.\n\nAtenciosamente,\nEquipe de Recrutamento`
    },
    {
      id: 'feedback',
      name: 'Solicitação de Feedback',
      subject: 'Feedback sobre o processo seletivo',
      message: `Olá ${candidate.name},\n\nGostaríamos de sua opinião sobre nossa empresa e processo seletivo. Seu feedback é muito importante para melhorarmos continuamente.\n\nPoderia compartilhar sua experiência conosco?\n\nObrigado(a) pelo seu tempo.\n\nAtenciosamente,\nEquipe de Recrutamento`
    }
  ] : []

  const fallbackWhatsappTemplates = candidate ? [
    {
      id: 'wsi_screening',
      name: '📋 Triagem WSI (Work Sample)',
      message: `Olá ${candidate.name}! 👋\n\nEspero que esteja bem!\n\nEstamos avançando no processo seletivo para ${roleOrJob} e gostaríamos de convidá-lo(a) para uma avaliação prática rápida.\n\n📋 *Sobre a avaliação:*\n• Duração: 15-20 min\n• Formato: Perguntas práticas\n• Link: [INSERIR LINK]\n\nÉ uma etapa importante que nos ajuda a conhecer melhor seu perfil! 🎯\n\nPodemos contar com você? 😊`,
      isWsi: true
    },
    {
      id: 'quick_contact',
      name: 'Contato Rápido',
      message: `Olá ${candidate.name}! 👋\n\nSou da equipe de recrutamento. Temos uma oportunidade que pode interessar você.\n\nPodemos conversar? 😊`
    },
    {
      id: 'interview_reminder',
      name: 'Lembrete de Entrevista',
      message: `Olá ${candidate.name}! 📅\n\nLembrando que temos nossa conversa agendada para hoje às 15h.\n\nNos vemos em breve! 🚀`
    }
  ] : []

  const apiEmailTemplates = apiTemplates
    .filter(t => t.channel === 'email')
    .map(t => ({
      id: t.id,
      name: t.name,
      subject: replaceTemplateVariables(t.subject || ''),
      message: replaceTemplateVariables(t.body_text || (t.body_html ? t.body_html.replace(/<[^>]*>/g, '') : '')),
      isWsi: t.situation === 'wsi_screening'
    }))

  const apiWhatsappTemplates = apiTemplates
    .filter(t => t.channel === 'whatsapp')
    .map(t => ({
      id: t.id,
      name: t.name,
      message: replaceTemplateVariables(t.body_text || (t.body_html ? t.body_html.replace(/<[^>]*>/g, '') : ''))
    }))

  const emailTemplates = apiEmailTemplates.length > 0 ? apiEmailTemplates : fallbackEmailTemplates
  const whatsappTemplates = apiWhatsappTemplates.length > 0 ? apiWhatsappTemplates : fallbackWhatsappTemplates

  useEffect(() => {
    if (isOpen) {
      const fetchTemplates = async () => {
        try {
          setLoadingTemplates(true)
          const channel = activeTab === 'whatsapp' ? 'whatsapp' : 'email'
          const response = await liaApi.listEmailTemplates(undefined, true, undefined, 0, 50, channel)
          setApiTemplates(response.items || [])
        } catch (error) {
          console.error('Error fetching templates:', error)
        } finally {
          setLoadingTemplates(false)
        }
      }
      fetchTemplates()
    }
  }, [isOpen, activeTab])

  useEffect(() => {
    if (isOpen && candidate && !initialized && initialAction && !loadingTemplates) {
      if (initialAction === 'wsi_screening') {
        const wsiEmailTemplate = emailTemplates.find(t => t.id === 'wsi_screening' || t.isWsi)
        if (wsiEmailTemplate) {
          setSubject(wsiEmailTemplate.subject || '')
          setMessage(wsiEmailTemplate.message)
          setTemplateType('wsi_screening')
        }
      } else if (initialAction === 'interview_invite') {
        const interviewTemplate = emailTemplates.find(t => t.id === 'interview_invite' || t.name?.toLowerCase().includes('entrevista'))
        if (interviewTemplate) {
          setSubject(interviewTemplate.subject || '')
          setMessage(interviewTemplate.message)
          setTemplateType('interview_invite')
        }
      }
      setInitialized(true)
    }
  }, [isOpen, candidate, initialized, initialAction, loadingTemplates, emailTemplates])

  useEffect(() => {
    if (!isOpen) {
      setInitialized(false)
      setMessage('')
      setSubject('')
      setTemplateType('')
      setApiTemplates([])
    }
  }, [isOpen])

  if (!isOpen || !candidate) return null

  const handleTemplateSelect = (template: any) => {
    if (activeTab === 'email') {
      setSubject(template.subject)
      setMessage(template.message)
    } else {
      setMessage(template.message)
    }
    setTemplateType(template.id)
  }

  const generateLiaSuggestions = async (context: string) => {
    setIsLiaGenerating(true)
    setShowLiaSuggestions(true)

    // Simular geração da LIA baseada no contexto e perfil do candidato
    await new Promise(resolve => setTimeout(resolve, 2000))

    const suggestions = generateContextualSuggestions(context, candidate, activeTab)
    setLiaSuggestions(suggestions)
    setIsLiaGenerating(false)
  }

  const generateContextualSuggestions = (context: string, candidate: any, channel: string) => {
    const baseTemplates = {
      professional: {
        email: {
          subject: `Oportunidade profissional para ${candidate.role} - ${candidate.name}`,
          message: `Olá ${candidate.name},\n\nEspero que esteja bem. Analisamos seu perfil profissional e ficamos impressionados com sua experiência em ${candidate.role}.\n\nTemos uma excelente oportunidade que pode ser do seu interesse. Sua experiência com ${candidate.skills?.[0]} e ${candidate.skills?.[1]} se alinha perfeitamente com nossa vaga.\n\nGostaria de agendar uma conversa para discutirmos mais detalhes?\n\nAguardo seu retorno.\n\nAtenciosamente,\nEquipe de Recrutamento`
        },
        whatsapp: {
          message: `Olá ${candidate.name}! 👋\n\nSou da equipe de recrutamento. Analisamos seu perfil e temos uma oportunidade que pode interessar você.\n\nSua experiência em ${candidate.skills?.[0]} chamou nossa atenção! 🎯\n\nPodemos conversar? 😊`
        }
      },
      warm: {
        email: {
          subject: `${candidate.name}, que tal uma nova aventura profissional? 🚀`,
          message: `Oi ${candidate.name}!\n\nEspero que esteja tendo uma ótima semana! 😊\n\nEstou entrando em contato porque encontrei seu perfil e fiquei muito empolgado(a) com sua trajetória profissional. Sua experiência em ${candidate.role} é exatamente o que estamos procurando!\n\nTemos um ambiente super colaborativo e várias oportunidades de crescimento. Que tal batermos um papo sobre como podemos crescer juntos?\n\nVamos marcar um café virtual? ☕\n\nUm abraço!`
        },
        whatsapp: {
          message: `Oi ${candidate.name}! 😄\n\nTudo bem? Sou da equipe de RH e achei seu perfil incrível!\n\nTemos uma vaga que tem tudo a ver com você! ✨\n\nQuer saber mais? 🤔`
        }
      },
      urgent: {
        email: {
          subject: `URGENTE: Oportunidade única para ${candidate.role} - ${candidate.name}`,
          message: `${candidate.name},\n\nBom dia! Espero que esteja bem.\n\nTenho uma oportunidade URGENTE que precisa ser preenchida rapidamente e seu perfil é perfeito para a posição!\n\nVaga: ${candidate.role}\nLocalização: ${candidate.location}\nModalidade: Híbrida\n\nPrecisamos tomar uma decisão até o final desta semana. Está disponível para uma conversa ainda hoje?\n\nPor favor, me responda o mais breve possível.\n\nGrato pela atenção!`
        },
        whatsapp: {
          message: `${candidate.name}, bom dia! ⏰\n\nTenho uma oportunidade URGENTE para ${candidate.role}!\n\nSeu perfil é perfeito! 🎯\n\nPodemos falar HOJE? É importante! 🔥`
        }
      },
      follow_up: {
        email: {
          subject: `Acompanhamento - Nossa conversa sobre a vaga de ${candidate.role}`,
          message: `Olá ${candidate.name},\n\nEspero que esteja bem!\n\nGostaria de fazer um acompanhamento sobre nossa última conversa referente à posição de ${candidate.role}.\n\nVocê teve tempo para pensar sobre a oportunidade? Tem alguma dúvida que posso esclarecer?\n\nFico à disposição para qualquer informação adicional que precise.\n\nAguardo seu retorno!\n\nAtenciosamente`
        },
        whatsapp: {
          message: `Oi ${candidate.name}! 👋\n\nTudo bem por aí?\n\nSó passando para saber se você pensou na nossa conversa sobre a vaga! 🤔\n\nTem alguma dúvida que posso ajudar? 😊`
        }
      }
    }

    return [
      {
        id: '1',
        title: 'Sugestão Personalizada da LIA',
        context: context,
        content: (baseTemplates as any)[context]?.[channel] || baseTemplates.professional[channel as keyof typeof baseTemplates.professional],
        reasons: [
          `Baseado no perfil de ${candidate.role} do candidato`,
          `Considerando localização: ${candidate.location}`,
          `Skills relevantes: ${candidate.skills?.slice(0, 2).join(', ')}`,
          `Score de compatibilidade: ${candidate.matchPercentage || 95}%`
        ]
      },
      {
        id: '2',
        title: 'Versão Mais Direta',
        context: context,
        content: generateAlternativeMessage(context, candidate, channel),
        reasons: [
          'Tom mais direto e objetivo',
          'Foco nos benefícios da vaga',
          'Call-to-action claro'
        ]
      }
    ]
  }

  const generateAlternativeMessage = (context: string, candidate: any, channel: string) => {
    if (channel === 'email') {
      return {
        subject: `${candidate.name} - Vaga ${candidate.role} com match de ${candidate.matchPercentage || 95}%`,
        message: `${candidate.name},\n\nSua experiência em ${candidate.skills?.[0]} tem ${candidate.matchPercentage || 95}% de compatibilidade com nossa vaga de ${candidate.role}.\n\nDetalhes:\n• Localização: ${candidate.location}\n• Modalidade: Híbrida\n• Benefícios competitivos\n\nInteresse em saber mais?\n\nResponda este email ou me chame no WhatsApp.`
      }
    } else {
      return {
        message: `${candidate.name}, sua experiência tem ${candidate.matchPercentage || 95}% de match com nossa vaga! 🎯\n\nInteresse em saber mais? 🚀`
      }
    }
  }

  const applyLiaSuggestion = (suggestion: any) => {
    if (activeTab === 'email') {
      setSubject(suggestion.content.subject || '')
      setMessage(suggestion.content.message || '')
    } else {
      setMessage(suggestion.content.message || '')
    }
    setShowLiaSuggestions(false)
    setTemplateType(`lia-${suggestion.id}`)
  }

  const handleSend = async () => {
    setIsSending(true)

    try {
      if (activeTab === 'email') {
        const response = await liaApi.sendDirectEmail({
          recipient_email: candidate.email,
          recipient_name: candidate.name,
          subject: subject,
          body_html: `<div style="font-family: Arial, sans-serif;">${message.replace(/\n/g, '<br>')}</div>`,
          body_text: message,
          candidate_id: candidate.id,
          metadata: {
            source: 'contact_modal',
            channel: 'email'
          }
        })

        onSend(activeTab, message, candidate.email)
        
        alert(response.smtp_configured 
          ? `✅ Email enviado para ${candidate.email}` 
          : `📧 Email enfileirado para ${candidate.email}\n\nStatus: Funcional - Aguardando Configuração SMTP\nO email foi salvo no sistema e será enviado quando o SMTP for configurado.`)
      } else if (activeTab === 'whatsapp') {
        const whatsappUrl = `https://wa.me/${candidate.phone.replace(/\D/g, '')}?text=${encodeURIComponent(message)}`
        window.open(whatsappUrl, '_blank')
        onSend(activeTab, message, candidate.phone)
      } else if (activeTab === 'phone') {
        onSend(activeTab, message, candidate.phone)
        alert(`📞 Ligação registrada para ${candidate.name}`)
      }
    } catch (error) {
      console.error('Error sending message:', error)
      alert(`❌ Erro ao enviar mensagem: ${error instanceof Error ? error.message : 'Erro desconhecido'}`)
    }

    setIsSending(false)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-gray-950/70 backdrop-blur-[1px] z-50 flex items-center justify-center p-4">
      <div className={`${cardStyles.default} dark:bg-gray-900 dark:border-gray-700 rounded-md w-full max-w-4xl max-h-[90vh] overflow-y-auto`}>
        <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Avatar className="h-12 w-12">
              <AvatarImage src={candidate.avatar} />
              <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
            </Avatar>
            <div>
              <h3 className={`${textStyles.title} dark:text-gray-100`}>
                Contatar {candidate.name}
              </h3>
              <p className={textStyles.bodySmall}>
                {candidate.role} • {candidate.location}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex">
          {/* Tabs de Canal */}
          <div className="w-48 border-r border-gray-100 p-4">
            <h4 className={`${textStyles.label} mb-3`}>
              Canal de Contato
            </h4>
            <div className="space-y-2">
              <button
                onClick={() => setActiveTab('email')}
                className={`w-full flex items-center gap-3 p-3 rounded-md text-left transition-all ${
                  activeTab === 'email'
                    ? 'bg-gray-100 text-gray-800 border border-gray-200'
                    : 'hover:bg-gray-50 text-gray-800 dark:text-gray-200 border border-transparent'
                }`}
              >
                <Mail className="w-4 h-4" />
                <div>
                  <div className={textStyles.label}>Email</div>
                  <div className={textStyles.caption}>{candidate.email}</div>
                </div>
              </button>

              <button
                onClick={() => setActiveTab('whatsapp')}
                className={`w-full flex items-center gap-3 p-3 rounded-md text-left transition-all ${
                  activeTab === 'whatsapp'
                    ? 'bg-status-success/10 text-status-success border border-status-success/30'
                    : 'hover:bg-gray-50 text-gray-800 dark:text-gray-200 border border-transparent'
                }`}
              >
                <MessageSquare className="w-4 h-4" />
                <div>
                  <div className={textStyles.label}>WhatsApp</div>
                  <div className={textStyles.caption}>{candidate.phone}</div>
                </div>
              </button>

              <button
                onClick={() => setActiveTab('phone')}
                className={`w-full flex items-center gap-3 p-3 rounded-md text-left transition-all ${
                  activeTab === 'phone'
                    ? 'bg-wedo-purple/10 text-wedo-purple border border-wedo-purple/30'
                    : 'hover:bg-gray-50 text-gray-800 dark:text-gray-200 border border-transparent'
                }`}
              >
                <Phone className="w-4 h-4" />
                <div>
                  <div className={textStyles.label}>Telefone</div>
                  <div className={textStyles.caption}>{candidate.phone}</div>
                </div>
              </button>
            </div>
          </div>

          {/* Área Principal */}
          <div className="flex-1 p-5">
            {/* Templates */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h4 className={textStyles.label}>
                  Templates Rápidos
                </h4>
                <div className="flex items-center gap-1 text-micro text-gray-600 dark:text-gray-400">
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  <span>LIA disponível abaixo</span>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {(activeTab === 'email' ? emailTemplates : whatsappTemplates).map((template) => (
                  <button
                    key={template.id}
                    onClick={() => handleTemplateSelect(template)}
                    className={`p-3 border rounded-md text-left transition-all ${
                      templateType === template.id
                        ? 'border-gray-300 bg-gray-100'
                        : 'border-gray-100 hover:bg-gray-50 hover:border-gray-200'
                    }`}
                  >
                    <div className={textStyles.label}>{template.name}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* LIA Assistant */}
            <div className="border-t border-gray-100 pt-6">
              <div className="flex items-center justify-between mb-3">
                <h4 className={`${textStyles.label} flex items-center gap-2`}>
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  LIA - Assistente Inteligente
                </h4>
                <div className="flex items-center gap-2">
                  <select
                    value={liaContext}
                    onChange={(e) => setLiaContext(e.target.value as any)}
                    className="text-micro border border-gray-200 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-gray-900"
                  >
                    <option value="professional">Profissional</option>
                    <option value="warm">Caloroso</option>
                    <option value="urgent">Urgente</option>
                    <option value="follow_up">Follow-up</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => generateLiaSuggestions(liaContext)}
                  disabled={isLiaGenerating}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md border border-gray-200 bg-white text-gray-800 dark:text-gray-200 hover:bg-gray-50 transition-all disabled:opacity-50"
                >
                  {isLiaGenerating ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      LIA gerando...
                    </>
                  ) : (
                    <>
                      <Brain className="w-4 h-4 text-wedo-cyan" />
                      Gerar com LIA
                    </>
                  )}
                </button>
                <button
                  onClick={() => setShowLiaSuggestions(!showLiaSuggestions)}
                  className="px-3 py-1.5 rounded-md text-gray-500 hover:bg-gray-50 transition-all"
                  title="Ver/Ocultar sugestões"
                >
                  <Eye className="w-4 h-4" />
                </button>
              </div>

              {/* LIA Suggestions */}
              {showLiaSuggestions && (
                <div className="space-y-3 mb-4 max-h-80 overflow-y-auto">
                  {isLiaGenerating ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="text-center">
                        <RefreshCw className="w-8 h-8 animate-spin text-gray-600 dark:text-gray-400 mx-auto mb-2" />
                        <p className="text-xs text-gray-600">LIA analisando perfil e gerando sugestões...</p>
                      </div>
                    </div>
                  ) : (
                    liaSuggestions.map((suggestion) => (
                      <div key={suggestion.id} className="border border-gray-200 rounded-md p-4 bg-gray-50">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Brain className="w-4 h-4 text-wedo-cyan" />
                            <h5 className="text-xs font-medium text-gray-800">
                              {suggestion.title}
                            </h5>
                          </div>
                          <button
                            onClick={() => applyLiaSuggestion(suggestion)}
                            className="text-micro h-6 px-2 rounded-full border border-gray-200 text-gray-800 dark:text-gray-200 hover:bg-gray-50 transition-all"
                          >
                            Usar Esta
                          </button>
                        </div>

                        {activeTab === 'email' && suggestion.content.subject && (
                          <div className="mb-2">
                            <span className="text-micro font-medium text-gray-600">Assunto:</span>
                            <p className="text-micro text-gray-800 dark:text-gray-200 bg-white p-2 rounded-md border border-gray-100 mt-1">
                              {suggestion.content.subject}
                            </p>
                          </div>
                        )}

                        <div className="mb-3">
                          <span className="text-micro font-medium text-gray-600">Mensagem:</span>
                          <p className="text-micro text-gray-800 dark:text-gray-200 bg-white p-2 rounded-md border border-gray-100 mt-1 whitespace-pre-line">
                            {suggestion.content.message}
                          </p>
                        </div>

                        <div className="border-t border-gray-100 pt-2">
                          <span className="text-micro font-medium text-gray-600">Por que a LIA sugere:</span>
                          <ul className="text-micro text-gray-600 mt-1 space-y-1">
                            {suggestion.reasons.map((reason: string, idx: number) => (
                              <li key={idx} className="flex items-start gap-1">
                                <span className="text-gray-600 dark:text-gray-400 mt-0.5">•</span>
                                {reason}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Formulário */}
            <div className="space-y-4">
              {activeTab === 'email' && (
                <div>
                  <label className="block text-xs font-medium text-gray-800 mb-1.5">
                    Assunto
                  </label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-gray-200 rounded-md placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-900 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-200"
                    placeholder="Assunto do email"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-800 mb-1.5">
                  Mensagem
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={activeTab === 'email' ? 8 : 6}
                  className="w-full px-3 py-2 text-xs border border-gray-200 rounded-md placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                  placeholder={`Digite sua mensagem...`}
                />
              </div>

              {activeTab === 'phone' && (
                <div className="bg-gray-50 p-4 rounded-md border border-gray-100">
                  <div className="flex items-center gap-2 mb-2">
                    <Phone className="w-4 h-4 text-gray-600" />
                    <span className="text-xs font-medium text-gray-800">
                      Ligação Telefônica
                    </span>
                  </div>
                  <p className="text-xs text-gray-800 dark:text-gray-200">
                    Ligue para {candidate.phone} e registre as informações da conversa no campo de mensagem acima.
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-6 pt-5 border-t border-gray-100">
              <button
                onClick={onClose}
                className="px-3 py-1.5 text-xs font-medium rounded-md border border-gray-200 bg-white text-gray-800 dark:text-gray-200 hover:bg-gray-50 transition-all"
              >
                Cancelar
              </button>
              <button
                onClick={handleSend}
                disabled={isSending || !message.trim()}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md bg-gray-900 hover:bg-gray-800 text-white transition-all disabled:opacity-50"
              >
                {isSending ? (
                  <>
                    <Clock className="w-4 h-4 animate-spin" />
                    Enviando...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    {activeTab === 'email' ? 'Enviar Email' :
                     activeTab === 'whatsapp' ? 'Enviar WhatsApp' : 'Registrar Ligação'}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Modal de Agendamento
export function ScheduleModal({ isOpen, onClose, candidate, onSchedule }: ScheduleModalProps) {
  const [scheduleType, setScheduleType] = useState<'phone' | 'video' | 'presential'>('video')
  const [date, setDate] = useState('')
  const [time, setTime] = useState('')
  const [duration, setDuration] = useState('60')
  const [interviewer, setInterviewer] = useState('')
  const [notes, setNotes] = useState('')
  const [location, setLocation] = useState('')
  const [platform, setPlatform] = useState('zoom')

  // LIA states
  const [showLiaInsights, setShowLiaInsights] = useState(false)
  const [liaRecommendations, setLiaRecommendations] = useState<any>(null)
  const [isLiaAnalyzing, setIsLiaAnalyzing] = useState(false)
  const [liaFocus, setLiaFocus] = useState<'technical' | 'behavioral' | 'cultural' | 'comprehensive'>('comprehensive')

  if (!isOpen || !candidate) return null

  const interviewTypes = [
    {
      id: 'phone',
      name: 'Telefônica',
      icon: Phone,
      description: 'Conversa por telefone',
      color: 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200'
    },
    {
      id: 'video',
      name: 'Videoconferência',
      icon: Video,
      description: 'Reunião online por vídeo',
      color: 'bg-status-success/10 text-status-success border-status-success/30'
    },
    {
      id: 'presential',
      name: 'Presencial',
      icon: Building,
      description: 'Encontro no escritório',
      color: 'bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30'
    }
  ]

  const platforms = [
    { id: 'zoom', name: 'Zoom', icon: Video },
    { id: 'teams', name: 'Teams', icon: Users },
    { id: 'meet', name: 'Google Meet', icon: Video },
    { id: 'whatsapp', name: 'WhatsApp', icon: MessageSquare }
  ]

  const interviewers = [
    'Ana Silva - Recrutadora Sênior',
    'Carlos Mendes - Tech Lead',
    'Marina Costa - Gerente de Produto',
    'Roberto Santos - RH'
  ]

  const generateLiaRecommendations = async () => {
    setIsLiaAnalyzing(true)
    setShowLiaInsights(true)

    // Simular análise da LIA
    await new Promise(resolve => setTimeout(resolve, 2000))

    const recommendations = analyzeCandidateForInterview(candidate, liaFocus)
    setLiaRecommendations(recommendations)
    setIsLiaAnalyzing(false)
  }

  const analyzeCandidateForInterview = (candidate: any, focus: string) => {
    const seniorityLevel = candidate.seniority || candidate.level || 'Pleno'
    const skills = candidate.skills || []
    const experience = candidate.experience || ''
    const role = candidate.role || candidate.position || ''
    const score = candidate.matchPercentage || candidate.score || 85

    return {
      // Recomendações gerais
      recommendedType: seniorityLevel.toLowerCase().includes('senior') || seniorityLevel.toLowerCase().includes('sênior') ? 'video' : 'video',
      recommendedDuration: seniorityLevel.toLowerCase().includes('senior') ? '90' : seniorityLevel.toLowerCase().includes('junior') || seniorityLevel.toLowerCase().includes('júnior') ? '45' : '60',
      recommendedPlatform: score >= 90 ? 'zoom' : 'teams',

      // Horários sugeridos
      suggestedTimes: [
        { time: '10:00', reason: 'Horário ideal para entrevistas técnicas - candidato mais alerta' },
        { time: '14:00', reason: 'Pós-almoço, momento relaxado para avaliação comportamental' },
        { time: '16:00', reason: 'Final da tarde - bom para candidatos que trabalham' }
      ],

      // Foco da entrevista baseado no perfil
      interviewFocus: {
        technical: {
          weight: score >= 85 ? 40 : 60,
          topics: skills.slice(0, 3),
          approach: score >= 85 ? 'Validação de expertise avançada' : 'Avaliação de conhecimentos fundamentais'
        },
        behavioral: {
          weight: 30,
          topics: ['Trabalho em equipe', 'Resolução de problemas', 'Comunicação'],
          approach: seniorityLevel.toLowerCase().includes('senior') ? 'Foco em liderança e mentoria' : 'Foco em adaptabilidade e aprendizado'
        },
        cultural: {
          weight: 20,
          topics: ['Alinhamento com valores', 'Motivação', 'Objetivos de carreira'],
          approach: 'Avaliar fit com cultura organizacional'
        },
        company: {
          weight: 10,
          topics: ['Interesse na empresa', 'Conhecimento do mercado', 'Expectativas'],
          approach: 'Validar interesse genuíno na posição'
        }
      },

      // Perguntas sugeridas
      suggestedQuestions: {
        opening: [
          `Conte-me sobre sua experiência mais relevante como ${role}`,
          `O que te motivou a se candidatar para esta posição?`,
          `Como você descreveria seu estilo de trabalho?`
        ],
        technical: skills.slice(0, 3).map((skill: string) => `Descreva um projeto desafiador onde você utilizou ${skill}`),
        behavioral: [
          'Conte sobre uma situação onde você teve que resolver um conflito na equipe',
          'Descreva um momento onde você teve que aprender algo completamente novo rapidamente',
          'Como você lida com feedback negativo?'
        ],
        closing: [
          'Quais são suas expectativas para os próximos passos?',
          'Tem alguma dúvida sobre a empresa ou a posição?',
          'O que você espera encontrar nesta oportunidade?'
        ]
      },

      // Pontos de atenção
      attentionPoints: {
        strengths: [
          `Score alto de ${score}% indica forte compatibilidade`,
          `Experiência em ${skills[0]} alinhada com necessidades da vaga`,
          `Localização favorável: ${candidate.location}`
        ],
        concerns: score < 80 ? [
          'Score abaixo de 80% - investigar gaps específicos',
          'Verificar motivação real para mudança'
        ] : [
          'Candidato strong - verificar expectativas salariais',
          'Confirmar disponibilidade e interesse real'
        ],
        redFlags: [
          'Verificar estabilidade profissional',
          'Confirmar disponibilidade para início',
          'Validar expectativas de crescimento'
        ]
      },

      // Preparação do entrevistador
      preparation: {
        beforeInterview: [
          `Revisar currículo focando em experiência com ${skills.slice(0, 2).join(' e ')}`,
          'Preparar cenários práticos relacionados à vaga',
          'Definir critérios de avaliação específicos'
        ],
        duringInterview: [
          'Manter ambiente acolhedor mas profissional',
          'Fazer anotações sobre pontos técnicos e comportamentais',
          'Dar espaço para o candidato fazer perguntas'
        ],
        afterInterview: [
          'Preencher avaliação imediatamente',
          'Documentar impressões comportamentais',
          'Definir próximos passos com timeline'
        ]
      },

      // Configurações recomendadas
      settings: {
        sendReminder: true,
        reminderTime: '24h',
        includeCompanyInfo: true,
        includeInterviewerInfo: true,
        provideMaterials: score < 85
      }
    }
  }

  const applyLiaRecommendation = (type: string) => {
    if (!liaRecommendations) return

    switch (type) {
      case 'duration':
        setDuration(liaRecommendations.recommendedDuration)
        break
      case 'platform':
        setPlatform(liaRecommendations.recommendedPlatform)
        break
      case 'type':
        setScheduleType(liaRecommendations.recommendedType)
        break
      case 'notes':
        const focusAreas = Object.entries(liaRecommendations.interviewFocus)
          .sort(([,a], [,b]) => (b as any).weight - (a as any).weight)
          .slice(0, 2)
          .map(([key, value]) => `${key}: ${(value as any).approach}`)
          .join('\n')
        setNotes(`Foco da entrevista (sugerido pela LIA):\n\n${focusAreas}\n\nPontos de atenção:\n${liaRecommendations.attentionPoints.strengths[0]}`)
        break
    }
  }

  const [isScheduling, setIsScheduling] = useState(false)
  const [createdInterviewId, setCreatedInterviewId] = useState<string | null>(null)

  const handleSchedule = async () => {
    setIsScheduling(true)

    try {
      const startTime = new Date(`${date}T${time}`)
      
      const interviewModeMap: Record<string, string> = {
        'phone': 'phone',
        'video': 'video', 
        'presential': 'in_person'
      }

      const response = await liaApi.createInterview({
        candidate_id: candidate.id,
        candidate_name: candidate.name,
        candidate_email: candidate.email,
        interviewer_name: interviewer.split(' - ')[0] || interviewer,
        interviewer_email: `${interviewer.split(' - ')[0]?.toLowerCase().replace(/\s+/g, '.')}@empresa.com`,
        start_time: startTime.toISOString(),
        duration_minutes: parseInt(duration),
        interview_type: 'screening',
        interview_mode: interviewModeMap[scheduleType] || 'video',
        job_title: candidate.role,
        location: scheduleType === 'presential' ? location : platform,
        notes: notes || (liaRecommendations ? `Recomendações LIA aplicadas: ${liaFocus}` : undefined)
      })

      setCreatedInterviewId(response.id)

      const scheduleData = {
        type: scheduleType,
        date,
        time,
        duration: parseInt(duration),
        interviewer,
        notes,
        location: scheduleType === 'presential' ? location : platform,
        candidateId: candidate.id,
        candidateName: candidate.name,
        candidateEmail: candidate.email,
        candidatePhone: candidate.phone,
        liaRecommendations: liaRecommendations || null,
        interviewId: response.id
      }

      onSchedule(scheduleType, `${date}T${time}`, scheduleData)

      const confirmMsg = `✅ Entrevista agendada com sucesso!\n\n` +
        `📅 Data: ${new Date(startTime).toLocaleDateString('pt-BR')} às ${time}\n` +
        `👤 Candidato: ${candidate.name}\n` +
        `🎥 Tipo: ${scheduleType === 'video' ? 'Videoconferência' : scheduleType === 'phone' ? 'Telefone' : 'Presencial'}\n` +
        `⏱️ Duração: ${duration} minutos\n\n` +
        `Status: Funcional - Aguardando Configuração Calendar\n` +
        `Os dados foram salvos no banco. Para sincronizar com calendário, configure Microsoft Graph ou Google Calendar.`

      alert(confirmMsg)
      onClose()
    } catch (error) {
      console.error('Error scheduling interview:', error)
      alert(`❌ Erro ao agendar entrevista: ${error instanceof Error ? error.message : 'Erro desconhecido'}`)
    } finally {
      setIsScheduling(false)
    }
  }

  const handleDownloadIcs = async () => {
    if (!createdInterviewId) return

    try {
      const blob = await liaApi.downloadInterviewIcs(createdInterviewId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `entrevista_${candidate.name.replace(/\s+/g, '_')}.ics`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error downloading ICS:', error)
      alert('Erro ao baixar arquivo de calendário')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-gray-950/70 backdrop-blur-[1px] z-50 flex items-center justify-center p-4">
      <div className={`${cardStyles.default} dark:bg-gray-900 dark:border-gray-700 rounded-md w-full max-w-3xl max-h-[90vh] overflow-y-auto`}>
        <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Avatar className="h-12 w-12">
              <AvatarImage src={candidate.avatar} />
              <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
            </Avatar>
            <div>
              <h3 className={`${textStyles.title} dark:text-gray-100`}>
                Agendar Entrevista - {candidate.name}
              </h3>
              <p className={textStyles.bodySmall}>
                {candidate.role} • {candidate.location}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-6">
          {/* LIA Assistant */}
          <div className={`${cardStyles.flat} dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4`}>
            <div className="flex items-center justify-between mb-3">
              <h4 className={`${textStyles.label} flex items-center gap-2`}>
                <Brain className="w-4 h-4 text-wedo-cyan" />
                LIA - Recomendações Inteligentes
              </h4>
              <div className="flex items-center gap-2">
                <select
                  value={liaFocus}
                  onChange={(e) => setLiaFocus(e.target.value as any)}
                  className="text-micro border border-gray-200 rounded-md px-2 py-1 bg-white focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                >
                  <option value="comprehensive">Análise Completa</option>
                  <option value="technical">Foco Técnico</option>
                  <option value="behavioral">Foco Comportamental</option>
                  <option value="cultural">Foco Cultural</option>
                </select>
                <button
                  onClick={generateLiaRecommendations}
                  disabled={isLiaAnalyzing}
                  className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md border border-gray-200 text-gray-800 dark:text-gray-200 hover:bg-gray-50 transition-all disabled:opacity-50"
                >
                  {isLiaAnalyzing ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Analisando...
                    </>
                  ) : (
                    <>
                      <Brain className="w-4 h-4 text-wedo-cyan" />
                      Analisar com LIA
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* LIA Recommendations */}
            {showLiaInsights && (
              <div className="mt-4">
                {isLiaAnalyzing ? (
                  <div className="flex items-center justify-center py-6">
                    <div className="text-center">
                      <RefreshCw className="w-8 h-8 animate-spin text-gray-600 dark:text-gray-400 mx-auto mb-2" />
                      <p className="text-xs text-gray-600">LIA analisando perfil para recomendações...</p>
                    </div>
                  </div>
                ) : liaRecommendations && (
                  <div className="space-y-4">
                    {/* Quick Recommendations */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="text-center p-3 bg-white rounded-md border border-gray-100">
                        <div className="text-lg font-semibold text-gray-900 dark:text-gray-50">{liaRecommendations.recommendedDuration}min</div>
                        <div className="text-micro text-gray-600">Duração sugerida</div>
                        <button
                          onClick={() => applyLiaRecommendation('duration')}
                          className="text-micro mt-1 h-6 px-2 text-gray-800 dark:text-gray-200 hover:bg-gray-50 rounded-full transition-all"
                        >
                          Aplicar
                        </button>
                      </div>
                      <div className="text-center p-3 bg-white rounded-md border border-gray-100">
                        <div className="text-lg font-semibold text-gray-900 dark:text-gray-50 capitalize">{liaRecommendations.recommendedType}</div>
                        <div className="text-micro text-gray-600">Tipo recomendado</div>
                        <button
                          onClick={() => applyLiaRecommendation('type')}
                          className="text-micro mt-1 h-6 px-2 text-gray-800 dark:text-gray-200 hover:bg-gray-50 rounded-full transition-all"
                        >
                          Aplicar
                        </button>
                      </div>
                      <div className="text-center p-3 bg-white rounded-md border border-gray-100">
                        <div className="text-lg font-semibold text-gray-900 dark:text-gray-50 capitalize">{liaRecommendations.recommendedPlatform}</div>
                        <div className="text-micro text-gray-600">Plataforma sugerida</div>
                        <button
                          onClick={() => applyLiaRecommendation('platform')}
                          className="text-micro mt-1 h-6 px-2 text-gray-800 dark:text-gray-200 hover:bg-gray-50 rounded-full transition-all"
                        >
                          Aplicar
                        </button>
                      </div>
                    </div>

                    {/* Suggested Times */}
                    <div>
                      <h5 className="text-xs font-medium text-gray-800 mb-2">Horários Recomendados:</h5>
                      <div className="space-y-2">
                        {liaRecommendations.suggestedTimes.map((timeRec: any, idx: number) => (
                          <div key={idx} className="flex items-center justify-between p-2 bg-white rounded-md border border-gray-100">
                            <div>
                              <span className="font-medium text-gray-800 text-xs">{timeRec.time}</span>
                              <span className="text-micro text-gray-600 ml-2">{timeRec.reason}</span>
                            </div>
                            <button
                              onClick={() => setTime(timeRec.time)}
                              className="text-micro h-6 px-2 text-gray-800 dark:text-gray-200 hover:bg-gray-50 rounded-full transition-all"
                            >
                              Usar
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Interview Focus */}
                    <div>
                      <h5 className="text-xs font-medium text-gray-800 mb-2">Foco da Entrevista:</h5>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(liaRecommendations.interviewFocus)
                          .sort(([,a], [,b]) => (b as any).weight - (a as any).weight)
                          .slice(0, 4)
                          .map(([key, value]: [string, any]) => (
                          <div key={key} className="p-2 bg-white rounded-md border border-gray-100">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-micro font-medium text-gray-800 capitalize">{key}</span>
                              <span className="text-micro text-gray-600 dark:text-gray-400">{value.weight}%</span>
                            </div>
                            <p className="text-micro text-gray-600">{value.approach}</p>
                          </div>
                        ))}
                      </div>
                      <button
                        onClick={() => applyLiaRecommendation('notes')}
                        className="text-micro mt-2 px-2 py-1 text-gray-800 dark:text-gray-200 hover:bg-gray-50 rounded-full transition-all"
                      >
                        Aplicar foco nas observações
                      </button>
                    </div>

                    {/* Key Insights */}
                    <div className="border-t border-gray-100 pt-3">
                      <h5 className="text-xs font-medium text-gray-800 mb-2">Insights Principais:</h5>
                      <div className="grid grid-cols-1 gap-2">
                        <div>
                          <span className="text-micro font-medium text-gray-800 dark:text-gray-200">Pontos Fortes:</span>
                          <ul className="text-micro text-gray-600 ml-2">
                            {liaRecommendations.attentionPoints.strengths.slice(0, 2).map((strength: string, idx: number) => (
                              <li key={idx}>• {strength}</li>
                            ))}
                          </ul>
                        </div>
                        {liaRecommendations.attentionPoints.concerns.length > 0 && (
                          <div>
                            <span className="text-micro font-medium text-status-warning">Pontos de Atenção:</span>
                            <ul className="text-micro text-status-warning ml-2">
                              {liaRecommendations.attentionPoints.concerns.slice(0, 2).map((concern: string, idx: number) => (
                                <li key={idx}>• {concern}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Tipo de Entrevista */}
          <div>
            <h4 className="text-xs font-medium text-gray-800 mb-3">
              Tipo de Entrevista
            </h4>
            <div className="grid grid-cols-3 gap-3">
              {interviewTypes.map((type) => (
                <button
                  key={type.id}
                  onClick={() => setScheduleType(type.id as any)}
                  className={`p-4 border rounded-md text-left transition-all ${
                    scheduleType === type.id
                      ? 'border-gray-300 bg-gray-100'
                      : 'border-gray-100 hover:bg-gray-50 hover:border-gray-200'
                  }`}
                >
                  <type.icon className={`w-5 h-5 mb-2 ${scheduleType === type.id ? 'text-gray-900' : 'text-gray-500'}`} />
                  <div className="text-xs font-medium text-gray-800">{type.name}</div>
                  <div className="text-micro text-gray-600">{type.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Data e Hora */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-800 mb-1.5">
                Data
              </label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 text-xs border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-800 mb-1.5">
                Horário
              </label>
              <input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-800 mb-1.5">
                Duração (min)
              </label>
              <select
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900"
              >
                <option value="30">30 minutos</option>
                <option value="45">45 minutos</option>
                <option value="60">1 hora</option>
                <option value="90">1h 30min</option>
                <option value="120">2 horas</option>
              </select>
            </div>
          </div>

          {/* Local/Plataforma */}
          {scheduleType === 'video' && (
            <div>
              <label className="block text-xs font-medium text-gray-800 mb-1.5">
                Plataforma
              </label>
              <div className="grid grid-cols-4 gap-2">
                {platforms.map((plat) => (
                  <button
                    key={plat.id}
                    onClick={() => setPlatform(plat.id)}
                    className={`p-3 border rounded-md text-center transition-all ${
                      platform === plat.id
                        ? 'border-gray-300 bg-gray-100'
                        : 'border-gray-100 hover:bg-gray-50 hover:border-gray-200'
                    }`}
                  >
                    <plat.icon className={`w-5 h-5 mx-auto mb-1 ${platform === plat.id ? 'text-gray-900' : 'text-gray-500'}`} />
                    <div className="text-micro text-gray-800 dark:text-gray-200">{plat.name}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {scheduleType === 'presential' && (
            <div>
              <label className="block text-xs font-medium text-gray-800 mb-1.5">
                Local da Entrevista
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-gray-200 rounded-md placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-900 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-200"
                placeholder="Endereço completo ou sala"
              />
            </div>
          )}

          {/* Entrevistador */}
          <div>
            <label className="block text-xs font-medium text-gray-800 mb-1.5">
              Entrevistador Responsável
            </label>
            <select
              value={interviewer}
              onChange={(e) => setInterviewer(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900"
            >
              <option value="">Selecione o entrevistador</option>
              {interviewers.map((person) => (
                <option key={person} value={person}>{person}</option>
              ))}
            </select>
          </div>

          {/* Observações */}
          <div>
            <label className="block text-xs font-medium text-gray-800 mb-1.5">
              Observações para a Entrevista
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 text-xs border border-gray-200 rounded-md placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-900 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-200"
              placeholder="Pontos específicos a abordar, preparações necessárias..."
            />
          </div>

          {/* Status Info */}
          <div className="bg-status-warning/10 border border-status-warning/30 rounded-md p-3">
            <div className="flex items-center gap-2 text-status-warning">
              <Info className="w-4 h-4" />
              <span className="text-xs font-medium">Funcional - Aguardando Configuração Calendar</span>
            </div>
            <p className="text-micro text-status-warning mt-1">
              Entrevistas são salvas no banco de dados. Para sincronização automática com calendários, configure Microsoft Graph ou Google Calendar.
            </p>
          </div>

          {/* Ações */}
          <div className="flex justify-end gap-3 pt-5 border-t border-gray-100">
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-xs font-medium rounded-md border border-gray-200 bg-white text-gray-800 dark:text-gray-200 hover:bg-gray-50 transition-all"
            >
              Cancelar
            </button>
            {createdInterviewId && (
              <button
                onClick={handleDownloadIcs}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md border border-gray-200 bg-white text-gray-800 dark:text-gray-200 hover:bg-gray-50 transition-all"
              >
                <Download className="w-4 h-4" />
                Baixar .ICS
              </button>
            )}
            <button
              onClick={handleSchedule}
              disabled={!date || !time || !interviewer || isScheduling}
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md bg-gray-900 hover:bg-gray-800 text-white transition-all disabled:opacity-50"
            >
              {isScheduling ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Agendando...
                </>
              ) : (
                <>
                  <Calendar className="w-4 h-4" />
                  Agendar Entrevista
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Modal de Visualização Rápida
export function QuickViewModal({ isOpen, onClose, candidate, onNavigateToFull }: QuickViewModalProps) {
  const [showLiaInsights, setShowLiaInsights] = useState(true)
  const [liaInsights, setLiaInsights] = useState<any>(null)
  const [isLiaAnalyzing, setIsLiaAnalyzing] = useState(false)

  // Gerar insights da LIA quando o modal abrir
  const generateLiaInsights = useCallback(async () => {
    setIsLiaAnalyzing(true)

    // Simular análise da LIA
    await new Promise(resolve => setTimeout(resolve, 1500))

    const insights = analyzeCandidateQuickInsights(candidate)
    setLiaInsights(insights)
    setIsLiaAnalyzing(false)
  }, [candidate])

  const analyzeCandidateQuickInsights = (candidate: any) => {
    const score = candidate.matchPercentage || candidate.score || 85
    const skills = candidate.skills || []
    const experience = candidate.experience || ''
    const seniority = candidate.seniority || candidate.level || 'Pleno'
    const role = candidate.role || candidate.position || ''

    return {
      // Resumo executivo da LIA
      executiveSummary: score >= 90
        ? `Candidato excepcional com ${score}% de match. Profile ideal para a posição com experiência sólida em ${skills.slice(0, 2).join(' e ')}.`
        : score >= 80
        ? `Candidato qualificado com ${score}% de match. Atende a maioria dos requisitos com potencial de crescimento.`
        : `Candidato promissor com ${score}% de match. Alguns gaps identificados que podem ser desenvolvidos.`,

      // Status da candidatura
      candidateStatus: {
        priority: score >= 90 ? 'alta' : score >= 80 ? 'média' : 'baixa',
        readiness: score >= 85 ? 'Pronto para próxima etapa' : 'Necessita avaliação adicional',
        timeline: score >= 90 ? 'Fast-track recomendado' : 'Timeline normal'
      },

      // Próximos passos recomendados
      nextSteps: score >= 90 ? [
        { action: 'Agendar entrevista técnica', priority: 'alta', timeframe: '2-3 dias' },
        { action: 'Verificar disponibilidade imediata', priority: 'alta', timeframe: '24h' },
        { action: 'Preparar proposta competitiva', priority: 'média', timeframe: '1 semana' }
      ] : score >= 80 ? [
        { action: 'Entrevista comportamental', priority: 'alta', timeframe: '3-5 dias' },
        { action: 'Teste técnico complementar', priority: 'média', timeframe: '1 semana' },
        { action: 'Verificação de referências', priority: 'baixa', timeframe: '2 semanas' }
      ] : [
        { action: 'Triagem detalhada', priority: 'alta', timeframe: '2-3 dias' },
        { action: 'Assessment de skills', priority: 'alta', timeframe: '1 semana' },
        { action: 'Mentoria/desenvolvimento', priority: 'baixa', timeframe: '1 mês' }
      ],

      // Análise de strengths e concerns
      analysis: {
        strengths: score >= 90 ? [
          `Expertise avançada em ${skills[0]}`,
          'Profile senior com liderança',
          'Match cultural excelente'
        ] : score >= 80 ? [
          `Sólida experiência em ${skills[0]}`,
          'Perfil equilibrado técnico/comportamental',
          'Boa adequação à vaga'
        ] : [
          'Potencial de crescimento',
          'Motivação para aprender',
          'Disponibilidade para desenvolvimento'
        ],

        concerns: score >= 90 ? [
          'Possível overqualification',
          'Expectativas salariais altas',
          'Risco de recusa por outras ofertas'
        ] : score >= 80 ? [
          'Alguns gaps técnicos menores',
          'Necessita validação comportamental',
          'Confirmar interesse real'
        ] : [
          'Gaps significativos identificados',
          'Necessita desenvolvimento intensivo',
          'Risco de baixa performance inicial'
        ],

        redFlags: [
          'Verificar estabilidade no emprego atual',
          'Confirmar motivação para mudança',
          'Validar expectativas realistas'
        ]
      },

      // Estratégia de abordagem
      approachStrategy: {
        tone: score >= 90 ? 'Competitivo e direto' : score >= 80 ? 'Profissional e atrativo' : 'Desenvolvimentista e acolhedor',
        focus: score >= 90 ? 'Benefícios e oportunidades únicas' : score >= 80 ? 'Crescimento e aprendizado' : 'Mentoria e desenvolvimento',
        urgency: score >= 90 ? 'Alta - agir rapidamente' : score >= 80 ? 'Média - processar normalmente' : 'Baixa - avaliar com cuidado'
      },

      // Insights baseados em dados
      dataInsights: {
        compatibilityScore: score,
        experienceLevel: seniority,
        keySkills: skills.slice(0, 3),
        riskLevel: score >= 85 ? 'Baixo' : score >= 70 ? 'Médio' : 'Alto',
        successProbability: score >= 90 ? '95%' : score >= 80 ? '85%' : '70%'
      }
    }
  }

  // Executar análise quando o modal abrir
  useEffect(() => {
    if (isOpen && candidate && !liaInsights) {
      generateLiaInsights()
    }
  }, [isOpen, candidate, liaInsights, generateLiaInsights])

  if (!isOpen || !candidate) return null

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-gray-950/70 backdrop-blur-[1px] z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              <AvatarImage src={candidate.avatar} />
              <AvatarFallback className="text-lg">{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
            </Avatar>
            <div>
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-50">
                {candidate.name}
              </h3>
              <p className="text-sm text-gray-600">
                {candidate.role} • {candidate.experience} • {candidate.location}
              </p>
              <div className="flex items-center gap-3 mt-2">
                <Badge variant="outline" className="bg-status-success/10 text-status-success">
                  {candidate.matchPercentage}% Match
                </Badge>
                <Badge variant="outline">
                  {candidate.status}
                </Badge>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigateToFull(candidate.id)}
              className="gap-2"
            >
              <Eye className="w-4 h-4" />
              Ver Perfil Completo
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* LIA Insights Section */}
          <div className="mb-6 border border-status-success/30 rounded-md p-4 bg-status-success/10">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-status-success flex items-center gap-2">
                <Brain className="w-4 h-4 text-status-success" />
                Insights Instantâneos da LIA
              </h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowLiaInsights(!showLiaInsights)}
                className="text-xs text-status-success hover:bg-status-success/15"
              >
                {showLiaInsights ? 'Ocultar' : 'Mostrar'}
              </Button>
            </div>

            {showLiaInsights && (
              <div>
                {isLiaAnalyzing ? (
                  <div className="flex items-center justify-center py-4">
                    <div className="text-center">
                      <RefreshCw className="w-6 h-6 animate-spin text-status-success mx-auto mb-2" />
                      <p className="text-xs text-status-success">LIA analisando perfil...</p>
                    </div>
                  </div>
                ) : liaInsights && (
                  <div className="space-y-4">
                    {/* Executive Summary */}
                    <div className="bg-white rounded-md p-3 border border-status-success/30">
                      <h5 className="text-xs font-medium text-status-success mb-2">Resumo Executivo:</h5>
                      <p className="text-xs text-status-success">{liaInsights.executiveSummary}</p>
                    </div>

                    {/* Status and Next Steps */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-white rounded-md p-3 border border-status-success/30">
                        <h5 className="text-xs font-medium text-status-success mb-2">Status:</h5>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span>Prioridade:</span>
                            <Badge className={`text-xs ${
                              liaInsights.candidateStatus.priority === 'alta' ? 'bg-status-error/15 text-status-error' :
                              liaInsights.candidateStatus.priority === 'média' ? 'bg-status-warning/15 text-status-warning' :
                              'bg-gray-100 text-gray-800 dark:text-gray-200'
                            }`}>
                              {liaInsights.candidateStatus.priority.toUpperCase()}
                            </Badge>
                          </div>
                          <div className="text-xs text-status-success">{liaInsights.candidateStatus.readiness}</div>
                        </div>
                      </div>

                      <div className="bg-white rounded-md p-3 border border-status-success/30">
                        <h5 className="text-xs font-medium text-status-success mb-2">Estratégia:</h5>
                        <div className="space-y-1 text-xs text-status-success">
                          <div><strong>Tom:</strong> {liaInsights.approachStrategy.tone}</div>
                          <div><strong>Urgência:</strong> {liaInsights.approachStrategy.urgency}</div>
                        </div>
                      </div>
                    </div>

                    {/* Next Steps */}
                    <div className="bg-white rounded-md p-3 border border-status-success/30">
                      <h5 className="text-xs font-medium text-status-success mb-2">Próximos Passos Recomendados:</h5>
                      <div className="space-y-2">
                        {liaInsights.nextSteps.slice(0, 3).map((step: any, idx: number) => (
                          <div key={idx} className="flex items-center justify-between">
                            <div className="flex-1">
                              <span className="text-xs text-status-success">{step.action}</span>
                              <div className="flex items-center gap-2 mt-1">
                                <Badge className={`text-xs ${
                                  step.priority === 'alta' ? 'bg-status-error/15 text-status-error' :
                                  step.priority === 'média' ? 'bg-status-warning/15 text-status-warning' :
                                  'bg-gray-100 text-gray-800 dark:text-gray-200'
                                }`}>
                                  {step.priority}
                                </Badge>
                                <span className="text-xs text-status-success">{step.timeframe}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Analysis Summary */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-white rounded-md p-3 border border-status-success/30">
                        <h5 className="text-xs font-medium text-status-success mb-2 flex items-center gap-1">
                          <CheckCircle className="w-3 h-3 text-status-success" />
                          Pontos Fortes:
                        </h5>
                        <ul className="text-xs text-status-success space-y-1">
                          {liaInsights.analysis.strengths.slice(0, 3).map((strength: string, idx: number) => (
                            <li key={idx}>• {strength}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="bg-white rounded-md p-3 border border-wedo-orange/30">
                        <h5 className="text-xs font-medium text-wedo-orange mb-2 flex items-center gap-1">
                          <AlertCircle className="w-3 h-3 text-wedo-orange" />
                          Pontos de Atenção:
                        </h5>
                        <ul className="text-xs text-wedo-orange space-y-1">
                          {liaInsights.analysis.concerns.slice(0, 3).map((concern: string, idx: number) => (
                            <li key={idx}>• {concern}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Quick Data Insights */}
                    <div className="bg-white rounded-md p-3 border border-status-success/30">
                      <h5 className="text-xs font-medium text-status-success mb-2">Métricas da LIA:</h5>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="text-center">
                          <div className="font-semibold text-status-success">{liaInsights.dataInsights.compatibilityScore}%</div>
                          <div className="text-status-success">Match</div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold text-status-success">{liaInsights.dataInsights.successProbability}</div>
                          <div className="text-status-success">Sucesso</div>
                        </div>
                        <div className="text-center">
                          <div className={`font-semibold ${
                            liaInsights.dataInsights.riskLevel === 'Baixo' ? 'text-status-success' :
                            liaInsights.dataInsights.riskLevel === 'Médio' ? 'text-status-warning' :
                            'text-status-error'
                          }`}>
                            {liaInsights.dataInsights.riskLevel}
                          </div>
                          <div className="text-status-success">Risco</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 gap-6">
            {/* Coluna 1: Informações Básicas */}
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Contato</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-gray-600" />
                    <span className="text-sm">{candidate.email}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-gray-600" />
                    <span className="text-sm">{candidate.phone}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-gray-600" />
                    <span className="text-sm">{candidate.location}</span>
                  </div>
                  {candidate.linkedin && (
                    <div className="flex items-center gap-2">
                      <Linkedin className="w-4 h-4 text-gray-600" />
                      <a href={candidate.linkedin} target="_blank" className="text-sm text-gray-600 dark:text-gray-400 hover:underline">
                        LinkedIn
                      </a>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Disponibilidade</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-sm">
                    <span className="text-gray-800 dark:text-gray-200">Disponibilidade:</span>
                    <span className="ml-2 font-medium">{candidate.availability}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-gray-800 dark:text-gray-200">Salário esperado:</span>
                    <span className="ml-2 font-medium">{candidate.expectedSalary}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-gray-800 dark:text-gray-200">Local preferido:</span>
                    <span className="ml-2 font-medium">{candidate.preferredLocation}</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Coluna 2: Métricas e Skills */}
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Métricas LIA</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Match Técnico</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-status-success h-2 rounded-full"
                          style={{ width: `${candidate.technicalMatch}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{candidate.technicalMatch}%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Fit Cultural</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gray-900 dark:bg-gray-50 h-2 rounded-full"
                          style={{ width: `${candidate.culturalFit}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{candidate.culturalFit}%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Nível de Risco</span>
                    <Badge
                      variant="outline"
                      className={
                        candidate.riskLevel === 'Baixo' ? 'text-status-success border-status-success/30' :
                        candidate.riskLevel === 'Médio' ? 'text-status-warning border-status-warning/30' :
                        'text-status-error border-status-error/30'
                      }
                    >
                      {candidate.riskLevel}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Principais Skills</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-1">
                    {candidate.skills.slice(0, 8).map((skill, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {skill}
                      </Badge>
                    ))}
                    {candidate.skills.length > 8 && (
                      <Badge variant="outline" className="text-xs">
                        +{candidate.skills.length - 8} mais
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Coluna 3: Histórico */}
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Histórico Recente</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-status-success rounded-full mt-2"></div>
                    <div>
                      <div className="text-sm font-medium">Candidatura enviada</div>
                      <div className="text-xs text-gray-800 dark:text-gray-200">{candidate.lastActivity}</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-gray-900 dark:bg-gray-50 rounded-full mt-2"></div>
                    <div>
                      <div className="text-sm font-medium">Análise LIA concluída</div>
                      <div className="text-xs text-gray-800 dark:text-gray-200">Há 2 horas</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full mt-2"></div>
                    <div>
                      <div className="text-sm font-medium">Perfil visualizado</div>
                      <div className="text-xs text-gray-800 dark:text-gray-200">Há 1 dia</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Origem</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gray-100 rounded-md flex items-center justify-center">
                      <Globe className="w-4 h-4 text-gray-600" />
                    </div>
                    <div>
                      <div className="text-sm font-medium">{candidate.source}</div>
                      <div className="text-xs text-gray-800 dark:text-gray-200">Fonte de candidatura</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex justify-center gap-3 mt-6 pt-6 border-t border-gray-100">
            <Button variant="outline" className="gap-2">
              <Mail className="w-4 h-4" />
              Enviar Email
            </Button>
            <Button variant="outline" className="gap-2">
              <Calendar className="w-4 h-4" />
              Agendar Entrevista
            </Button>
            <Button variant="outline" className="gap-2">
              <Heart className="w-4 h-4" />
              Favoritar
            </Button>
            <Button
              onClick={() => onNavigateToFull(candidate.id)}
              className="gap-2"
            >
              <ChevronRight className="w-4 h-4" />
              Ver Perfil Completo
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Modal de Ações em Lote
export function BatchActionModal({ isOpen, onClose, selectedCandidates, onBatchAction }: BatchActionModalProps) {
  const [action, setAction] = useState('')
  const [stage, setStage] = useState('')
  const [comment, setComment] = useState('')
  const [assignTo, setAssignTo] = useState('')
  const [sendNotification, setSendNotification] = useState(true)

  if (!isOpen || selectedCandidates.length === 0) return null

  const batchActions = [
    {
      id: 'move_stage',
      name: 'Mover Etapa',
      description: 'Mover candidatos para uma nova etapa do processo',
      icon: ChevronRight
    },
    {
      id: 'approve',
      name: 'Aprovar',
      description: 'Aprovar todos os candidatos selecionados',
      icon: CheckCircle
    },
    {
      id: 'reject',
      name: 'Rejeitar',
      description: 'Rejeitar todos os candidatos selecionados',
      icon: X
    },
    {
      id: 'assign',
      name: 'Atribuir Responsável',
      description: 'Atribuir um recrutador responsável',
      icon: User
    },
    {
      id: 'tag',
      name: 'Adicionar Tags',
      description: 'Adicionar tags de identificação',
      icon: Star
    }
  ]

  const stages = [
    'Triagem',
    'Entrevista Inicial',
    'Teste Técnico',
    'Entrevista Final',
    'Proposta',
    'Aprovado',
    'Rejeitado'
  ]

  const recruiters = [
    'Ana Silva - Recrutadora Sênior',
    'Carlos Mendes - Tech Lead',
    'Marina Costa - Gerente de Produto',
    'Roberto Santos - RH'
  ]

  const handleExecute = () => {
    const actionData = {
      action,
      stage,
      comment,
      assignTo,
      sendNotification,
      candidateIds: selectedCandidates.map(c => c.id)
    }

    onBatchAction(action, actionData)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-gray-950/70 backdrop-blur-[1px] z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-50">
              Ações em Lote
            </h3>
            <p className="text-sm text-gray-500">
              {selectedCandidates.length} candidatos selecionados
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="p-6 space-y-6">
          {/* Candidatos Selecionados */}
          <div>
            <h4 className="text-sm font-medium text-gray-800 mb-3">
              Candidatos Selecionados
            </h4>
            <div className="max-h-32 overflow-y-auto border border-gray-100 rounded-md p-3">
              <div className="space-y-2">
                {selectedCandidates.map((candidate) => (
                  <div key={candidate.id} className="flex items-center gap-3">
                    <Avatar className="h-6 w-6">
                      <AvatarImage src={candidate.avatar} />
                      <AvatarFallback className="text-xs">{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                    </Avatar>
                    <span className="text-sm">{candidate.name}</span>
                    <span className="text-xs text-gray-800 dark:text-gray-200">- {candidate.role}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Ação */}
          <div>
            <h4 className="text-sm font-medium text-gray-800 mb-3">
              Selecione a Ação
            </h4>
            <div className="grid grid-cols-2 gap-3">
              {batchActions.map((actionItem) => (
                <button
                  key={actionItem.id}
                  onClick={() => setAction(actionItem.id)}
                  className={`p-4 border rounded-md text-left transition-colors ${
                    action === actionItem.id
                      ? 'border-gray-300 bg-gray-100'
                      : 'border-gray-100 hover:bg-gray-50'
                  }`}
                >
                  <actionItem.icon className="w-5 h-5 mb-2" />
                  <div className="text-sm font-medium">{actionItem.name}</div>
                  <div className="text-xs text-gray-500">{actionItem.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Configurações específicas por ação */}
          {action === 'move_stage' && (
            <div>
              <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                Nova Etapa
              </label>
              <select
                value={stage}
                onChange={(e) => setStage(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900"
              >
                <option value="">Selecione a etapa</option>
                {stages.map((stageOption) => (
                  <option key={stageOption} value={stageOption}>{stageOption}</option>
                ))}
              </select>
            </div>
          )}

          {action === 'assign' && (
            <div>
              <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                Atribuir para
              </label>
              <select
                value={assignTo}
                onChange={(e) => setAssignTo(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900"
              >
                <option value="">Selecione o responsável</option>
                {recruiters.map((recruiter) => (
                  <option key={recruiter} value={recruiter}>{recruiter}</option>
                ))}
              </select>
            </div>
          )}

          {/* Comentário */}
          <div>
            <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
              Comentário (opcional)
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
              className="w-full p-3 border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900"
              placeholder="Adicione um comentário sobre esta ação..."
            />
          </div>

          {/* Notificação */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="notification"
              checked={sendNotification}
              onChange={(e) => setSendNotification(e.target.checked)}
              className="rounded border-gray-200"
            />
            <label htmlFor="notification" className="text-sm text-gray-600">
              Enviar notificação para os candidatos sobre esta alteração
            </label>
          </div>

          {/* Ações */}
          <div className="flex justify-end gap-3 pt-6 border-t border-gray-200 dark:border-gray-700">
            <Button variant="outline" onClick={onClose} className="bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700">
              Cancelar
            </Button>
            <Button
              onClick={handleExecute}
              disabled={!action || (action === 'move_stage' && !stage) || (action === 'assign' && !assignTo)}
              className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
            >
              <Zap className="w-4 h-4" />
              Executar Ação
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
