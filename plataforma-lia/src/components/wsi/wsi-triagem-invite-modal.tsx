"use client"

import React, { useState, useEffect, useCallback, useRef } from "react"
import { createPortal } from "react-dom"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Textarea } from "@/components/ui/textarea"
import {
  Mail, Phone, MessageSquare, Send, 
  X, Eye, ChevronDown, ChevronUp,
  Info, Loader2,
  ClipboardList, ListChecks, Briefcase
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { Switch } from "@/components/ui/switch"
import { textStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import { MessageComposer } from "@/components/communication"

type ContactChannel = 'email' | 'whatsapp' | 'telefone' | 'both'

interface Candidate {
  id: string
  name: string
  role?: string
  email?: string
  phone?: string
  location?: string
  avatar?: string
}

interface ScreeningQuestion {
  id: string
  question: string
  category?: string
  bloomLevel?: number
}

interface JobVacancy {
  id: string
  title: string
  department?: string
  location?: string
  status?: string
}

const PIPELINE_STAGES = [
  { value: 'novo', label: 'Novo' },
  { value: 'triagem', label: 'Triagem' },
  { value: 'entrevista', label: 'Entrevista' },
  { value: 'avaliacao', label: 'Avaliação' },
  { value: 'oferta', label: 'Oferta' }
]

interface WSITriagemInviteModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate | null
  jobTitle?: string
  jobId?: string
  screeningQuestions?: ScreeningQuestion[]
  onSend?: (data: any) => void
  companyId?: string
}

const DEFAULT_SCREENING_QUESTIONS: ScreeningQuestion[] = [
  { id: '1', question: 'Descreva uma situação onde você precisou resolver um problema complexo. Como você abordou?', category: 'Resolução de Problemas', bloomLevel: 4 },
  { id: '2', question: 'Como você se mantém atualizado com as novidades da sua área de atuação?', category: 'Aprendizado Contínuo', bloomLevel: 3 },
  { id: '3', question: 'Conte sobre um projeto que você liderou ou teve grande participação. Qual foi seu papel?', category: 'Experiência Prática', bloomLevel: 5 },
  { id: '4', question: 'Como você lida com prazos apertados e múltiplas demandas simultâneas?', category: 'Gestão de Tempo', bloomLevel: 3 },
  { id: '5', question: 'Quais são suas expectativas para os próximos anos em sua carreira?', category: 'Objetivos', bloomLevel: 2 }
]

export function WSITriagemInviteModal({
  isOpen,
  onClose,
  candidate,
  jobTitle = 'a vaga',
  jobId,
  screeningQuestions = DEFAULT_SCREENING_QUESTIONS,
  onSend,
  companyId
}: WSITriagemInviteModalProps) {
  const [channel, setChannel] = useState<ContactChannel>('email')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [showQuestions, setShowQuestions] = useState(true)
  const [mounted, setMounted] = useState(false)
  const messageTextareaRef = useRef<HTMLTextAreaElement>(null)
  
  const [linkToVacancy, setLinkToVacancy] = useState(false)
  const [selectedVacancyId, setSelectedVacancyId] = useState<string | null>(null)
  const [selectedStage, setSelectedStage] = useState('triagem')
  const [vacancies, setVacancies] = useState<JobVacancy[]>([])
  const [isLoadingVacancies, setIsLoadingVacancies] = useState(false)
  
  const { toast } = useToast()

  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  const loadVacancies = useCallback(async () => {
    if (vacancies.length > 0) return
    setIsLoadingVacancies(true)
    try {
      const response = await fetch('/api/backend-proxy/job-vacancies/')
      const data = await response.json()
      const vacancyList = data.vacancies || data.items || data || []
      setVacancies(Array.isArray(vacancyList) ? vacancyList : [])
    } catch (error) {
      setVacancies([])
    } finally {
      setIsLoadingVacancies(false)
    }
  }, [vacancies.length])

  useEffect(() => {
    if (linkToVacancy) {
      loadVacancies()
    }
  }, [linkToVacancy, loadVacancies])

  useEffect(() => {
    if (isOpen && jobId && vacancies.length > 0) {
      const exists = vacancies.some(v => v.id === jobId)
      if (exists) {
        setSelectedVacancyId(jobId)
        setLinkToVacancy(true)
      }
    }
  }, [isOpen, jobId, vacancies])

  const generatePhoneScript = useCallback(() => {
    if (!candidate) return ''
    return `📞 SCRIPT DE LIGAÇÃO - LIA

[Início da chamada]

"Olá, bom dia/tarde! Eu sou a LIA, assistente virtual da equipe de recrutamento da [Empresa].

Estou ligando para ${candidate.name} referente ao processo seletivo para a posição de ${jobTitle}.

[Se a pessoa confirmar que é ela]

Que ótimo falar com você! Gostaria de realizar uma triagem rápida, que leva aproximadamente 15 a 20 minutos. Posso prosseguir agora ou prefere que eu retorne em outro momento?

[Se sim, prosseguir]

Perfeito! Antes de começarmos, preciso informar que esta conversa será gravada para fins de avaliação, conforme nossa política de privacidade. Você concorda em prosseguir?

[Após confirmação]

Ótimo! Vou fazer algumas perguntas sobre sua experiência e forma de trabalhar. Pode responder com calma, não há resposta certa ou errada.

[Iniciar perguntas de triagem]"`
  }, [candidate, jobTitle])

  useEffect(() => {
    if (isOpen && candidate && channel === 'telefone') {
      setMessage(generatePhoneScript())
      setSubject('')
    }
  }, [isOpen, channel, candidate, generatePhoneScript])

  useEffect(() => {
    if (!isOpen) {
      setChannel('email')
      setMessage('')
      setSubject('')
      setShowQuestions(true)
      setLinkToVacancy(false)
      setSelectedVacancyId(null)
      setSelectedStage('triagem')
    }
  }, [isOpen])

  const handleSend = async () => {
    if (!candidate) return
    
    if (linkToVacancy && !selectedVacancyId) {
      toast({
        title: "Selecione uma vaga",
        description: "Para vincular o candidato, você precisa selecionar uma vaga.",
        variant: "destructive"
      })
      return
    }
    
    if ((channel === 'email' || channel === 'both') && !candidate.email) {
      toast({
        title: "Email não informado",
        description: "O candidato não possui email cadastrado.",
        variant: "destructive"
      })
      return
    }
    
    if ((channel === 'whatsapp' || channel === 'both') && !candidate.phone) {
      toast({
        title: "Telefone não informado",
        description: "O candidato não possui telefone cadastrado.",
        variant: "destructive"
      })
      return
    }
    
    setIsSending(true)
    
    try {
      if (linkToVacancy && selectedVacancyId) {
        try {
          const response = await fetch(`/api/backend-proxy/search/vacancy/${selectedVacancyId}/add-candidates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              candidate_ids: [candidate.id],
              stage: selectedStage
            })
          })
          
          if (!response.ok) {
          } else {
            const selectedVacancy = vacancies.find(v => v.id === selectedVacancyId)
            toast({
              title: "Candidato vinculado à vaga",
              description: `${candidate.name} foi adicionado à vaga "${selectedVacancy?.title || 'selecionada'}"`,
            })
          }
        } catch (error) {
        }
      }

      const selectedVacancy = linkToVacancy ? vacancies.find(v => v.id === selectedVacancyId) : null
      
      const sendChannel = channel === 'both' ? 'email' : channel
      
      const inviteResponse = await fetch('/api/backend-proxy/communication/send-screening-invite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: sendChannel,
          candidate_id: candidate.id,
          candidate_name: candidate.name,
          candidate_email: candidate.email,
          candidate_phone: candidate.phone,
          subject: (channel === 'email' || channel === 'both') ? subject : undefined,
          message,
          vacancy_id: linkToVacancy ? selectedVacancyId : jobId,
          vacancy_title: selectedVacancy?.title || jobTitle,
          screening_question_ids: screeningQuestions.map(q => q.id),
          stage: linkToVacancy ? selectedStage : 'triagem',
        })
      })
      
      const inviteData = await inviteResponse.json()
      
      if (!inviteResponse.ok || !inviteData.success) {
        toast({
          title: "Erro ao enviar convite",
          description: inviteData.error || "Não foi possível enviar o convite. Tente novamente.",
          variant: "destructive"
        })
        return
      }
      
      if ((channel === 'whatsapp' || channel === 'both') && candidate.phone) {
        const whatsappUrl = `https://wa.me/${candidate.phone.replace(/\D/g, '')}?text=${encodeURIComponent(message)}`
        window.open(whatsappUrl, '_blank')
      }
      
      const successMessages: Record<string, { title: string; description: string }> = {
        email: {
          title: "✅ Convite enviado com sucesso!",
          description: `Email de triagem enviado para ${candidate.name}${inviteData.mock ? ' (modo desenvolvimento)' : ''}`
        },
        whatsapp: {
          title: "✅ Convite registrado!",
          description: `WhatsApp aberto para ${candidate.name}. Convite registrado no sistema.`
        },
        telefone: {
          title: "✅ Script de ligação preparado!",
          description: `Script para ${candidate.name} está pronto. Inicie a ligação quando desejar.`
        },
        both: {
          title: "✅ Convite enviado por email e WhatsApp!",
          description: `Email enviado e WhatsApp aberto para ${candidate.name}${inviteData.mock ? ' (modo desenvolvimento)' : ''}`
        }
      }
      
      const successMsg = successMessages[channel] || successMessages.email
      toast({
        title: successMsg.title,
        description: successMsg.description,
      })
      
      onSend?.({
        channel,
        subject: channel === 'email' ? subject : undefined,
        message,
        candidateId: candidate.id,
        screeningQuestions: screeningQuestions.map(q => q.id),
        vacancyId: linkToVacancy ? selectedVacancyId : undefined,
        stage: linkToVacancy ? selectedStage : undefined,
        messageId: inviteData.message_id,
        communicationLogged: inviteData.communication_logged,
      })
      
      onClose()
    } catch (error) {
      toast({
        title: "Erro ao enviar",
        description: "Erro de conexão. Verifique sua internet e tente novamente.",
        variant: "destructive"
      })
    } finally {
      setIsSending(false)
    }
  }

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
  }

  const formatPreviewMessage = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\[(.*?)\]/g, '<span class="text-gray-600 dark:text-lia-text-tertiary underline cursor-pointer">$1</span>')
      .replace(/•/g, '&bull;')
      .replace(/\n/g, '<br>')
  }

  if (!isOpen || !candidate || !mounted) return null

  const modalContent = (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-[1px] z-modal flex items-center justify-center p-4">
      <div 
        className={`${cardStyles.elevated} w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col rounded-md`}
       
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-100 dark:bg-lia-bg-secondary rounded-full flex items-center justify-center">
              <ClipboardList className="w-5 h-5 text-gray-600 dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h2 className={textStyles.titleLarge}>
                Enviar Convite de Triagem WSI
              </h2>
              <p className={textStyles.description}>
                {candidate.name} • {candidate.role || jobTitle}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="w-4 h-4 lia-text-secondary" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Left Panel - Form */}
          <div className="w-1/2 border-r border-lia-border-subtle overflow-y-auto p-5 space-y-5">
            {/* Canal de Contato */}
            <div>
              <label className={`${textStyles.subtitle} mb-2 block`}>
                Canal de Contato
              </label>
              <div className="flex flex-col gap-2">
                <button
                  onClick={() => setChannel('email')}
                  className={`flex items-center gap-3 p-3 rounded-md border transition-colors text-left ${
 channel === 'email' 
                      ? 'border-gray-900 bg-gray-50 dark:bg-lia-bg-secondary/50' 
                      : 'border-lia-border-subtle hover:border-lia-border-default'
                  }`}
                >
                  <Mail className={`w-4 h-4 ${channel === 'email' ? 'text-gray-600 dark:text-lia-text-tertiary' : 'text-gray-500'}`} />
                  <div className="flex-1">
                    <div className={textStyles.subtitle}>Email</div>
                    <div className={textStyles.caption}>{candidate.email || 'Não informado'}</div>
                  </div>
                </button>
                
                <button
                  onClick={() => setChannel('whatsapp')}
                  className={`flex items-center gap-3 p-3 rounded-md border transition-colors text-left ${
 channel === 'whatsapp' 
                      ? 'border-gray-900 bg-gray-50 dark:bg-lia-bg-secondary/50' 
                      : 'border-lia-border-subtle hover:border-lia-border-default'
                  }`}
                >
                  <MessageSquare className={`w-4 h-4 ${channel === 'whatsapp' ? 'text-gray-600 dark:text-lia-text-tertiary' : 'text-gray-500'}`} />
                  <div className="flex-1">
                    <div className={textStyles.subtitle}>WhatsApp</div>
                    <div className={textStyles.caption}>{candidate.phone || 'Não informado'}</div>
                  </div>
                </button>
                
                <button
                  onClick={() => setChannel('telefone')}
                  className={`flex items-center gap-3 p-3 rounded-md border transition-colors text-left ${
 channel === 'telefone' 
                      ? 'border-gray-900 bg-gray-50 dark:bg-lia-bg-secondary/50' 
                      : 'border-lia-border-subtle hover:border-lia-border-default'
                  }`}
                >
                  <Phone className={`w-4 h-4 ${channel === 'telefone' ? 'text-gray-600 dark:text-lia-text-tertiary' : 'text-gray-500'}`} />
                  <div className="flex-1">
                    <div className={textStyles.subtitle}>Telefone (Ligação)</div>
                    <div className={textStyles.caption}>{candidate.phone || 'Não informado'}</div>
                  </div>
                </button>
                
                <button
                  onClick={() => setChannel('both')}
                  className={`flex items-center gap-3 p-3 rounded-md border transition-colors text-left ${
 channel === 'both' 
                      ? 'border-gray-900 bg-gray-50 dark:bg-lia-bg-secondary/50' 
                      : 'border-lia-border-subtle hover:border-lia-border-default'
                  }`}
                >
                  <div className="flex items-center gap-0.5">
                    <Mail className={`w-3.5 h-3.5 ${channel === 'both' ? 'text-gray-600 dark:text-lia-text-tertiary' : 'text-gray-500'}`} />
                    <MessageSquare className={`w-3.5 h-3.5 ${channel === 'both' ? 'text-gray-600 dark:text-lia-text-tertiary' : 'text-gray-500'}`} />
                  </div>
                  <div className="flex-1">
                    <div className={textStyles.subtitle}>Ambos (Email + WhatsApp)</div>
                    <div className={textStyles.caption}>Email + WA simultâneo</div>
                  </div>
                </button>
              </div>
            </div>

            {/* MessageComposer for email/whatsapp/both, Manual editor for telefone */}
            {channel !== 'telefone' ? (
              <MessageComposer
                channel={(channel === 'both' ? 'email' : channel) as 'email' | 'whatsapp'}
                situation="triagem"
                initialSubject={subject}
                initialMessage={message}
                onSubjectChange={setSubject}
                onMessageChange={setMessage}
                showTemplateSelector={true}
                showLiaAdjust={true}
                showVariableSelector={true}
                candidateContext={{
                  name: candidate.name,
                  role: candidate.role,
                  location: candidate.location
                }}
                jobContext={{
                  title: jobTitle
                }}
              />
            ) : (
              <div>
                <label className="text-xs font-medium text-gray-800 dark:text-lia-text-primary mb-2 block">
                  Script de Abordagem
                </label>
                <Textarea
                  ref={messageTextareaRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Script para ligação..."
                  className="min-h-[180px] text-xs focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 resize-none border-lia-border-subtle"
                />
              </div>
            )}

            {/* Vincular à Vaga */}
            <div className="border border-lia-border-subtle rounded-md overflow-hidden">
              <div className="flex items-center justify-between p-3 bg-gray-50">
                <div className="flex items-center gap-2">
                  <Briefcase className="w-4 h-4 lia-text-base" />
                  <div>
                    <span className={textStyles.subtitle}>Vincular à Vaga</span>
                    <span className={`${textStyles.description} ml-2`}>(opcional)</span>
                  </div>
                </div>
                <Switch
                  checked={linkToVacancy}
                  onCheckedChange={setLinkToVacancy}
                />
              </div>
              
              {linkToVacancy && (
                <div className="p-3 space-y-3 border-t border-lia-border-subtle">
                  <div>
                    <label className={`${textStyles.subtitle} mb-1.5 block`}>
                      Selecione a Vaga
                    </label>
                    {isLoadingVacancies ? (
                      <div className="flex items-center gap-2 text-xs lia-text-secondary py-2">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Carregando vagas...
                      </div>
                    ) : vacancies.length === 0 ? (
                      <div className="text-xs lia-text-secondary py-2">
                        Nenhuma vaga disponível
                      </div>
                    ) : (
                      <select
                        value={selectedVacancyId || ''}
                        onChange={(e) => setSelectedVacancyId(e.target.value || null)}
                        className="w-full text-xs border border-lia-border-subtle rounded-md px-3 py-2 bg-lia-bg-primary focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                      >
                        <option value="">Selecione uma vaga...</option>
                        {vacancies.map((vacancy) => (
                          <option key={vacancy.id} value={vacancy.id}>
                            {vacancy.title}
                            {vacancy.department ? ` - ${vacancy.department}` : ''}
                            {vacancy.location ? ` (${vacancy.location})` : ''}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                  
                  <div>
                    <label className={`${textStyles.subtitle} mb-1.5 block`}>
                      Etapa do Pipeline
                    </label>
                    <select
                      value={selectedStage}
                      onChange={(e) => setSelectedStage(e.target.value)}
                      className="w-full text-xs border border-lia-border-subtle rounded-md px-3 py-2 bg-lia-bg-primary focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                    >
                      {PIPELINE_STAGES.map((stage) => (
                        <option key={stage.value} value={stage.value}>
                          {stage.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {selectedVacancyId && (
                    <div className="p-2 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md border border-lia-border-default dark:border-lia-border-default">
                      <p className="text-xs lia-text-base">
                        Ao enviar, o candidato será automaticamente adicionado à vaga selecionada na etapa <strong className="text-gray-600 dark:text-lia-text-tertiary">{PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}</strong>
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Perguntas de Triagem */}
            <div className="border border-lia-border-subtle rounded-md overflow-hidden">
              <button
                onClick={() => setShowQuestions(!showQuestions)}
                className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <ListChecks className="w-4 h-4 text-gray-600 dark:text-lia-text-tertiary" />
                  <span className={textStyles.subtitle}>
                    Roteiro de Triagem ({screeningQuestions.length} perguntas)
                  </span>
                </div>
                {showQuestions ? (
                  <ChevronUp className="w-4 h-4 lia-text-secondary" />
                ) : (
                  <ChevronDown className="w-4 h-4 lia-text-secondary" />
                )}
              </button>
              
              {showQuestions && (
                <div className="p-3 space-y-2 max-h-[200px] overflow-y-auto">
                  {screeningQuestions.map((q, idx) => (
                    <div 
                      key={q.id} 
                      className={cardStyles.compact}
                    >
                      <div className="flex items-start gap-2">
                        <span className={badgeStyles.primary}>
                          {idx + 1}
                        </span>
                        <div className="flex-1">
                          <p className={textStyles.bodySmall}>{q.question}</p>
                          {q.category && (
                            <span className={`${textStyles.caption} mt-1 block`}>
                              {q.category}
                              {q.bloomLevel && ` • Bloom ${q.bloomLevel}`}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - Preview */}
          <div className="w-1/2 bg-gray-50 p-5 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-gray-600 dark:text-lia-text-tertiary" />
                <span className={textStyles.subtitle}>Preview da Mensagem</span>
              </div>
              <Badge variant="outline" className="text-micro">
                {channel === 'email' ? 'Email' : channel === 'whatsapp' ? 'WhatsApp' : channel === 'both' ? 'Email + WhatsApp' : 'Telefone'}
              </Badge>
            </div>

            {/* Preview Card - Different styles per channel */}
            <div className={`rounded-md overflow-hidden ${
 channel === 'whatsapp' ? 'bg-whatsapp-bg' : 'bg-lia-bg-primary border border-lia-border-subtle'
            }`}>
              {(channel === 'email' || channel === 'both') ? (
                <>
                  {/* Email Preview Header */}
                  <div className="p-4 border-b border-lia-border-subtle bg-gray-50/50">
                    <div className="flex items-center gap-3">
                      <Avatar className="w-8 h-8">
                        <AvatarFallback className="text-micro bg-gray-900 text-white">
                          RH
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className={textStyles.subtitle}>Equipe de Recrutamento</div>
                        <div className={textStyles.caption}>recrutamento@empresa.com</div>
                      </div>
                    </div>
                    <div className={`mt-2 ${textStyles.bodySmall}`}>
                      Para: {candidate.email || 'email@candidato.com'}
                    </div>
                  </div>
                  {/* Email Subject */}
                  {subject && (
                    <div className="px-4 py-2 border-b border-lia-border-subtle">
                      <div className={textStyles.subtitle}>
                        {subject}
                      </div>
                    </div>
                  )}
                  {/* Email Body */}
                  <div className="p-4">
                    <div 
                      className={`${textStyles.body} leading-relaxed`}
                      dangerouslySetInnerHTML={{ __html: formatPreviewMessage(message) || '<span class="lia-text-secondary">A mensagem aparecerá aqui...</span>' }}
                    />
                  </div>
                </>
              ) : channel === 'whatsapp' ? (
                <div className="p-3">
                  {/* WhatsApp Chat Bubble */}
                  <div className="flex justify-end mb-2">
                    <div className="bg-whatsapp-bubble rounded-md p-3 max-w-[85%]">
                      <div 
                        className="text-xs lia-text-strong leading-relaxed whitespace-pre-wrap"
                        dangerouslySetInnerHTML={{ __html: formatPreviewMessage(message) || '<span class="lia-text-secondary">A mensagem aparecerá aqui...</span>' }}
                      />
                      <div className="text-micro lia-text-secondary text-right mt-1">
                        {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} ✓✓
                      </div>
                    </div>
                  </div>
                  {/* WhatsApp Info */}
                  <div className="text-center mt-3">
                    <span className="text-micro lia-text-secondary bg-lia-bg-primary/60 rounded-full py-1 px-3">
                      Será aberto o WhatsApp Web/App
                    </span>
                  </div>
                </div>
              ) : (
                <>
                  {/* Telefone/Script Preview */}
                  <div className="p-4 border-b border-lia-border-subtle bg-status-warning/10/50">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-status-warning/15 rounded-full flex items-center justify-center">
                        <Phone className="w-4 h-4 text-status-warning" />
                      </div>
                      <div>
                        <div className={textStyles.subtitle}>Script de Ligação</div>
                        <div className={textStyles.caption}>LIA realizará a chamada</div>
                      </div>
                    </div>
                  </div>
                  {/* Script Content */}
                  <div className="p-4">
                    <div 
                      className="text-xs text-gray-800 dark:text-lia-text-primary leading-relaxed font-mono bg-gray-50 p-3 rounded-md border border-lia-border-subtle"
                      dangerouslySetInnerHTML={{ __html: formatPreviewMessage(message) || '<span class="lia-text-secondary">O script aparecerá aqui...</span>' }}
                    />
                  </div>
                </>
              )}
            </div>

            {/* Info Box - Different per channel */}
            {(channel === 'email' || channel === 'both') && (
              <div className={`mt-4 p-3 ${badgeStyles.info} rounded-md border border-lia-border-default dark:border-lia-border-default bg-gray-50 dark:bg-lia-bg-secondary/50`}>
                <div className="flex items-start gap-2">
                  <Info className="w-4 h-4 text-gray-600 dark:text-lia-text-tertiary mt-0.5" />
                  <div>
                    <div className={textStyles.label}>{channel === 'both' ? 'Envio Simultâneo:' : 'Após Confirmação:'}</div>
                    <ul className={`${textStyles.caption} mt-1 space-y-0.5`}>
                      {channel === 'both' && <li>• Email será enviado via sistema + WhatsApp Web será aberto</li>}
                      <li>• Candidato escolhe canal preferido (Chat ou WhatsApp)</li>
                      <li>• Recebe termos LGPD para aceite</li>
                      <li>• LIA inicia triagem automaticamente</li>
                      <li>• Você recebe notificação ao concluir</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {channel === 'whatsapp' && (
              <div className={`mt-4 p-3 ${badgeStyles.success} rounded-md border border-status-success/30 bg-status-success/10`}>
                <div className="flex items-start gap-2">
                  <MessageSquare className="w-4 h-4 text-status-success mt-0.5" />
                  <div>
                    <div className={textStyles.label}>Fluxo WhatsApp:</div>
                    <ul className={`${textStyles.caption} mt-1 space-y-0.5`}>
                      <li>• Candidato responde "SIM" para iniciar</li>
                      <li>• LIA apresenta termos LGPD</li>
                      <li>• Triagem WSI inicia automaticamente</li>
                      <li>• Você recebe notificação ao concluir</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {channel === 'telefone' && (
              <div className={`mt-4 p-3 ${badgeStyles.warning} rounded-md border border-status-warning/30 bg-status-warning/10`}>
                <div className="flex items-start gap-2">
                  <Phone className="w-4 h-4 text-status-warning mt-0.5" />
                  <div>
                    <div className={textStyles.label}>Ligação com LIA:</div>
                    <ul className={`${textStyles.caption} mt-1 space-y-0.5`}>
                      <li>• LIA realizará a ligação no horário agendado</li>
                      <li>• Conversa gravada para análise</li>
                      <li>• Transcrição disponível após chamada</li>
                      <li>• Score WSI calculado automaticamente</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-primary dark:border-lia-border-subtle">
          <div className={`flex items-center gap-2 ${textStyles.description}`}>
            <Mail className="w-3.5 h-3.5" />
            {channel === 'email' 
              ? 'Email será enviado via sistema' 
              : channel === 'whatsapp'
              ? 'WhatsApp será aberto no navegador'
              : channel === 'both'
              ? 'Email enviado via sistema + WhatsApp aberto no navegador'
              : 'Script para ligação com LIA'}
          </div>
          <div className="flex items-center gap-3">
            <Button
              onClick={onClose}
              variant="outline"
              className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-gray-700 hover:bg-gray-50 dark:border-lia-border-default dark:text-lia-text-secondary dark:hover:bg-gray-700"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleSend}
              disabled={isSending || !message.trim()}
              className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200"
            >
              {isSending ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />
                  Enviando...
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5 mr-2" />
                  {channel === 'email' ? 'Enviar Email' : 
                   channel === 'whatsapp' ? 'Enviar WhatsApp' : 
                   channel === 'both' ? 'Enviar Email + WhatsApp' :
                   'Iniciar Ligação'}
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )

  return createPortal(modalContent, document.body)
}
