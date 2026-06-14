"use client"

import React, { useState, useEffect } from "react"
import { useModalA11y } from "@/hooks/ui/use-modal-a11y"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Mail, Phone, MessageSquare, Send, X, Clock, Brain, Eye, RefreshCw
} from "lucide-react"
import { liaApi } from "@/services/lia-api"
import { textStyles, cardStyles } from "@/lib/design-tokens"
import { toast } from "sonner"

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

  const dialogRef = useModalA11y(isOpen, onClose)
  if (!isOpen || !candidate) return null

  const handleTemplateSelect = (template: { id?: string; subject?: string; message?: string }) => {
    if (activeTab === 'email') {
      setSubject(template.subject || '')
      setMessage(template.message || '')
    } else {
      setMessage(template.message || '')
    }
    setTemplateType(template.id || '')
  }

  const generateLiaSuggestions = async (context: string) => {
    setIsLiaGenerating(true)
    setShowLiaSuggestions(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    const suggestions = generateContextualSuggestions(context, candidate, activeTab)
    setLiaSuggestions(suggestions)
    setIsLiaGenerating(false)
  }

  const generateContextualSuggestions = (context: string, candidate: Candidate, channel: string) => {
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
        content: (baseTemplates as Record<string, Record<string, unknown>>)[context]?.[channel] ?? baseTemplates.professional[channel as keyof typeof baseTemplates.professional],
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

  const generateAlternativeMessage = (context: string, candidate: Candidate, channel: string) => {
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

  const applyLiaSuggestion = (suggestion: { content?: { subject?: string; message?: string }; id?: string }) => {
    if (activeTab === 'email') {
      setSubject(suggestion.content?.subject || '')
      setMessage(suggestion.content?.message || '')
    } else {
      setMessage(suggestion.content?.message || '')
    }
    setShowLiaSuggestions(false)
    setTemplateType(`lia-${suggestion.id || ''}`)
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
      alert(`❌ Erro ao enviar mensagem: ${error instanceof Error ? error.message : 'Erro desconhecido'}`)
    }

    setIsSending(false)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-lia-overlay/70 backdrop-blur-[1px] z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="contact-modal-title" className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle rounded-md w-full max-w-4xl max-h-[90vh] overflow-y-auto`} onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 dark:border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <Avatar className="h-12 w-12">
              <AvatarImage src={candidate.avatar} />
              <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
            </Avatar>
            <div>
              <h3 id="contact-modal-title" className={`${textStyles.title}`}>
                Contatar {candidate.name}
              </h3>
              <p className={textStyles.bodySmall}>
                {candidate.role} • {candidate.location}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-xl text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan" aria-label="Fechar contato" data-dismiss="true">
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <div className="flex">
          {/* Tabs de Canal */}
          <div className="w-48 border-r border-lia-border-subtle p-4">
            <h4 className={`${textStyles.label} mb-3`}>
              Canal de Contato
            </h4>
            <div className="space-y-2">
              <button
                onClick={() => setActiveTab('email')}
                className={`w-full flex items-center gap-3 p-3 rounded-md text-left transition-colors motion-reduce:transition-none ${
 activeTab === 'email'
                    ? 'bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle'
                    : 'hover:bg-lia-bg-secondary text-lia-text-primary border border-transparent'
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
                className={`w-full flex items-center gap-3 p-3 rounded-md text-left transition-colors motion-reduce:transition-none ${
 activeTab === 'whatsapp'
                    ? 'bg-status-success/10 text-status-success border border-status-success/30'
                    : 'hover:bg-lia-bg-secondary text-lia-text-primary border border-transparent'
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
                className={`w-full flex items-center gap-3 p-3 rounded-md text-left transition-colors motion-reduce:transition-none ${
 activeTab === 'phone'
                    ? 'bg-wedo-purple/10 text-wedo-purple-text border border-wedo-purple/30'
                    : 'hover:bg-lia-bg-secondary text-lia-text-primary border border-transparent'
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
                <div className="flex items-center gap-1 text-micro text-lia-text-secondary">
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  <span>LIA disponível abaixo</span>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {(activeTab === 'email' ? emailTemplates : whatsappTemplates).map((template) => (
                  <button
                    key={template.id}
                    onClick={() => handleTemplateSelect(template)}
                    className={`p-3 border rounded-md text-left transition-colors motion-reduce:transition-none ${
 templateType === template.id
                        ? 'border-lia-border-default bg-lia-bg-tertiary'
                        : 'border-lia-border-subtle hover:bg-lia-bg-secondary hover:border-lia-border-subtle'
                    }`}
                  >
                    <div className={textStyles.label}>{template.name}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* LIA Assistant */}
            <div className="border-t border-lia-border-subtle pt-6">
              <div className="flex items-center justify-between mb-3">
                <h4 className={`${textStyles.label} flex items-center gap-2`}>
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  LIA - Assistente Inteligente
                </h4>
                <div className="flex items-center gap-2">
                  <select
                    value={liaContext}
                    onChange={(e) => setLiaContext(e.target.value as 'professional' | 'warm' | 'urgent' | 'follow_up')}
                    className="text-micro border border-lia-border-subtle rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg"
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
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-1.5 text-xs font-medium rounded-xl border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none disabled:opacity-50"
                >
                  {isLiaGenerating ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin motion-reduce:animate-none" />
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
                  className="px-3 py-1.5 rounded-xl text-lia-text-secondary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
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
                        <RefreshCw className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-secondary mx-auto mb-2" />
                        <p className="text-xs text-lia-text-secondary">LIA analisando perfil e gerando sugestões...</p>
                      </div>
                    </div>
                  ) : (
                    liaSuggestions.map((suggestion) => (
                      <div key={suggestion.id} className="border border-lia-border-subtle rounded-xl p-4 bg-lia-bg-secondary">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Brain className="w-4 h-4 text-wedo-cyan" />
                            <h5 className="text-xs font-medium text-lia-text-primary">
                              {suggestion.title}
                            </h5>
                          </div>
                          <button
                            onClick={() => applyLiaSuggestion(suggestion)}
                            className="text-micro h-6 px-2 rounded-full border border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-secondary transition-[width,height]"
                          >
                            Usar Esta
                          </button>
                        </div>

                        {activeTab === 'email' && suggestion.content.subject && (
                          <div className="mb-2">
                            <span className="text-micro font-medium text-lia-text-secondary">Assunto:</span>
                            <p className="text-micro text-lia-text-primary bg-lia-bg-primary p-2 rounded-xl border border-lia-border-subtle mt-1">
                              {suggestion.content.subject}
                            </p>
                          </div>
                        )}

                        <div className="mb-3">
                          <span className="text-micro font-medium text-lia-text-secondary">Mensagem:</span>
                          <p className="text-micro text-lia-text-primary bg-lia-bg-primary p-2 rounded-xl border border-lia-border-subtle mt-1 whitespace-pre-line">
                            {suggestion.content.message}
                          </p>
                        </div>

                        <div className="border-t border-lia-border-subtle pt-2">
                          <span className="text-micro font-medium text-lia-text-secondary">Por que a LIA sugere:</span>
                          <ul className="text-micro text-lia-text-secondary mt-1 space-y-1">
                            {suggestion.reasons.map((reason: string, idx: number) => (
                              <li key={idx} className="flex items-start gap-1">
                                <span className="text-lia-text-secondary mt-0.5">•</span>
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
                  <label className="block text-xs font-medium text-lia-text-primary mb-1.5">
                    Assunto
                  </label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-md placeholder:lia-text-secondary focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg dark:bg-lia-bg-secondary dark:border-lia-border-default"
                    placeholder="Assunto do email"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-lia-text-primary mb-1.5">
                  Mensagem
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={activeTab === 'email' ? 8 : 6}
                  className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-md placeholder:lia-text-secondary focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20"
                  placeholder={`Digite sua mensagem...`}
                />
              </div>

              {activeTab === 'phone' && (
                <div className="bg-lia-bg-secondary p-4 rounded-xl border border-lia-border-subtle">
                  <div className="flex items-center gap-2 mb-2">
                    <Phone className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-xs font-medium text-lia-text-primary">
                      Ligação Telefônica
                    </span>
                  </div>
                  <p className="text-xs text-lia-text-primary">
                    Ligue para {candidate.phone} e registre as informações da conversa no campo de mensagem acima.
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-6 pt-5 border-t border-lia-border-subtle">
              <button
                onClick={onClose}
                className="px-3 py-1.5 text-xs font-medium rounded-xl border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
              >
                Cancelar
              </button>
              <button
                onClick={handleSend}
                disabled={isSending || !message.trim()}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text transition-colors motion-reduce:transition-none disabled:opacity-50"
              >
                {isSending ? (
                  <>
                    <Clock className="w-4 h-4 animate-spin motion-reduce:animate-none" />
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
