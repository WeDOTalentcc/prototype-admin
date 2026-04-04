"use client"

import React, { useState, useEffect, useCallback, useMemo } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Mail,
  MessageSquare,
  ArrowRight,
  ArrowLeft,
  Send,
  Check,
  Loader2,
  PartyPopper,
  Users,
  ChevronRight,
  Eye,
} from "lucide-react"
import { toast } from "sonner"
import { textStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import { useCommunicationTemplates, type CommunicationTemplate, type TemplateSituation } from "@/hooks/use-communication-templates"
import { liaApi } from "@/services/lia-api"
import { useAuth } from "@/contexts/auth-context"

export interface CloseVacancyPayload {
  hired_candidate_id: string
  hired_notification: {
    channel: 'email' | 'whatsapp' | 'both'
    message: string
    subject?: string
    candidate_email?: string
    candidate_phone?: string
  }
  other_notifications: {
    candidate_ids: string[]
    channel: 'email' | 'whatsapp' | 'both'
    message: string
    subject?: string
    candidate_emails: Record<string, string>
    candidate_phones: Record<string, string>
  }
}

export interface CloseVacancyModalProps {
  isOpen: boolean
  onClose: () => void
  vacancy: { id: string; title: string; department?: string }
  hiredCandidate: { id: string; name: string; email?: string; phone?: string }
  otherCandidates: Array<{ id: string; name: string; email?: string; phone?: string; stage: string }>
  onConfirm: (data: CloseVacancyPayload) => Promise<void>
}

type Channel = 'email' | 'whatsapp' | 'both'

const STEP_1_SITUATIONS: TemplateSituation[] = ['proposta_aceita', 'proposta']
const STEP_2_SITUATIONS: TemplateSituation[] = ['vaga_fechada', 'feedback_construtivo']

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

function replaceTemplateVariables(
  body: string,
  candidateName: string,
  vacancyTitle: string,
  companyName: string = 'Nossa Empresa'
): string {
  return body
    .replace(/\{\{candidato_nome\}\}/g, candidateName)
    .replace(/\{\{vaga\}\}/g, vacancyTitle)
    .replace(/\{\{empresa_nome\}\}/g, companyName)
    .replace(/\{\{recrutador_nome\}\}/g, 'Equipe de Recrutamento')
    .replace(/\{\{data_inicio\}\}/g, '[Data a definir]')
    .replace(/\{\{instrucoes_onboarding\}\}/g, '')
}

export function CloseVacancyModal({
  isOpen,
  onClose,
  vacancy,
  hiredCandidate,
  otherCandidates,
  onConfirm,
}: CloseVacancyModalProps) {
  const { user } = useAuth()
  const [currentStep, setCurrentStep] = useState(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const [hiredChannel, setHiredChannel] = useState<Channel>('email')
  const [hiredTemplateId, setHiredTemplateId] = useState<string>('')
  const [hiredMessage, setHiredMessage] = useState<string>('')
  
  const [othersChannel, setOthersChannel] = useState<Channel>('email')
  const [othersTemplateId, setOthersTemplateId] = useState<string>('')
  const [othersMessage, setOthersMessage] = useState<string>('')
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([])
  
  const { templates, loading: templatesLoading } = useCommunicationTemplates()
  
  const step1Templates = useMemo(() => {
    const filterChannel = hiredChannel === 'both' ? 'email' : hiredChannel
    return templates.filter(
      t => STEP_1_SITUATIONS.includes(t.situation as TemplateSituation) && 
           t.channel === filterChannel && 
           t.isActive
    )
  }, [templates, hiredChannel])
  
  const step2Templates = useMemo(() => {
    const filterChannel = othersChannel === 'both' ? 'email' : othersChannel
    return templates.filter(
      t => STEP_2_SITUATIONS.includes(t.situation as TemplateSituation) && 
           t.channel === filterChannel && 
           t.isActive
    )
  }, [templates, othersChannel])
  
  useEffect(() => {
    if (step1Templates.length > 0 && !hiredTemplateId) {
      const defaultTemplate = step1Templates[0]
      setHiredTemplateId(defaultTemplate.id)
      setHiredMessage(replaceTemplateVariables(
        defaultTemplate.body,
        hiredCandidate.name,
        vacancy.title
      ))
    }
  }, [step1Templates, hiredTemplateId, hiredCandidate.name, vacancy.title])
  
  useEffect(() => {
    if (step2Templates.length > 0 && !othersTemplateId) {
      const defaultTemplate = step2Templates[0]
      setOthersTemplateId(defaultTemplate.id)
      setOthersMessage(defaultTemplate.body)
    }
  }, [step2Templates, othersTemplateId])
  
  useEffect(() => {
    if (otherCandidates.length > 0 && selectedCandidateIds.length === 0) {
      setSelectedCandidateIds(otherCandidates.map(c => c.id))
    }
  }, [otherCandidates, selectedCandidateIds.length])
  
  useEffect(() => {
    if (!isOpen) {
      setCurrentStep(1)
      setHiredChannel('email')
      setHiredTemplateId('')
      setHiredMessage('')
      setOthersChannel('email')
      setOthersTemplateId('')
      setOthersMessage('')
      setSelectedCandidateIds([])
    }
  }, [isOpen])
  
  const handleHiredTemplateChange = useCallback((templateId: string) => {
    setHiredTemplateId(templateId)
    const template = step1Templates.find(t => t.id === templateId)
    if (template) {
      setHiredMessage(replaceTemplateVariables(
        template.body,
        hiredCandidate.name,
        vacancy.title
      ))
    }
  }, [step1Templates, hiredCandidate.name, vacancy.title])
  
  const handleOthersTemplateChange = useCallback((templateId: string) => {
    setOthersTemplateId(templateId)
    const template = step2Templates.find(t => t.id === templateId)
    if (template) {
      setOthersMessage(template.body)
    }
  }, [step2Templates])
  
  const handleHiredChannelChange = useCallback((channel: Channel) => {
    setHiredChannel(channel)
    setHiredTemplateId('')
    setHiredMessage('')
  }, [])
  
  const handleOthersChannelChange = useCallback((channel: Channel) => {
    setOthersChannel(channel)
    setOthersTemplateId('')
    setOthersMessage('')
  }, [])
  
  const toggleCandidateSelection = useCallback((candidateId: string) => {
    setSelectedCandidateIds(prev => 
      prev.includes(candidateId)
        ? prev.filter(id => id !== candidateId)
        : [...prev, candidateId]
    )
  }, [])
  
  const toggleAllCandidates = useCallback(() => {
    if (selectedCandidateIds.length === otherCandidates.length) {
      setSelectedCandidateIds([])
    } else {
      setSelectedCandidateIds(otherCandidates.map(c => c.id))
    }
  }, [selectedCandidateIds.length, otherCandidates])
  
  const handleNextStep = useCallback(() => {
    if (!hiredTemplateId) {
      toast.error('Selecione um template para o candidato contratado')
      return
    }
    setCurrentStep(2)
  }, [hiredTemplateId])
  
  const handlePreviousStep = useCallback(() => {
    setCurrentStep(1)
  }, [])
  
  const handleConfirm = useCallback(async () => {
    if (!othersTemplateId && selectedCandidateIds.length > 0) {
      toast.error('Selecione um template para os demais candidatos')
      return
    }
    
    const candidateEmails: Record<string, string> = {}
    const candidatePhones: Record<string, string> = {}
    
    for (const cand of otherCandidates) {
      if (selectedCandidateIds.includes(cand.id)) {
        if (cand.email) candidateEmails[cand.id] = cand.email
        if (cand.phone) candidatePhones[cand.id] = cand.phone
      }
    }
    
    setIsSubmitting(true)
    try {
      const payload: CloseVacancyPayload = {
        hired_candidate_id: hiredCandidate.id,
        hired_notification: {
          channel: hiredChannel,
          message: hiredMessage,
          subject: (hiredChannel === 'email' || hiredChannel === 'both') ? `Parabéns! Você foi contratado - ${vacancy.title}` : undefined,
          candidate_email: hiredCandidate.email,
          candidate_phone: hiredCandidate.phone,
        },
        other_notifications: {
          candidate_ids: selectedCandidateIds,
          channel: othersChannel,
          message: othersMessage,
          subject: (othersChannel === 'email' || othersChannel === 'both') ? `Atualização sobre sua candidatura - ${vacancy.title}` : undefined,
          candidate_emails: candidateEmails,
          candidate_phones: candidatePhones,
        },
      }
      
      await onConfirm(payload)
      
      const tenantId = user?.company || 'default'
      liaApi.updateJobOutcome({
        company_id: tenantId,
        job_id: vacancy.id,
        outcome_status: 'hired',
        hire_quality_score: 1.0
      }).catch(() => {})
      
      toast.success('Vaga fechada com sucesso!')
      onClose()
    } catch (error) {
      toast.error('Erro ao fechar vaga. Tente novamente.')
    } finally {
      setIsSubmitting(false)
    }
  }, [
    hiredChannel,
    hiredMessage,
    hiredCandidate,
    vacancy,
    othersChannel,
    othersMessage,
    selectedCandidateIds,
    otherCandidates,
    onConfirm,
    onClose,
  ])
  
  const renderChannelSelector = (
    channel: Channel,
    onChange: (channel: Channel) => void,
    disabled: boolean = false
  ) => (
    <div className="grid grid-cols-3 gap-2">
      <Button
        type="button"
        variant={channel === 'email' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onChange('email')}
        disabled={disabled}
        className={cn(
          'flex items-center gap-2 h-9 px-4 text-xs font-medium',
          channel === 'email' 
            ? 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover' 
            : 'border border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover'
        )}
      >
        <Mail className="w-3.5 h-3.5" />
        Email
      </Button>
      <Button
        type="button"
        variant={channel === 'whatsapp' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onChange('whatsapp')}
        disabled={disabled}
        className={cn(
          'flex items-center gap-2 h-9 px-4 text-xs font-medium',
          channel === 'whatsapp' 
            ? 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover' 
            : 'border border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover'
        )}
      >
        <MessageSquare className="w-3.5 h-3.5" />
        WhatsApp
      </Button>
      <Button
        type="button"
        variant={channel === 'both' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onChange('both')}
        disabled={disabled}
        className={cn(
          'flex items-center gap-2 h-9 px-4 text-xs font-medium',
          channel === 'both' 
            ? 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover' 
            : 'border border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover'
        )}
      >
        <Mail className="w-3.5 h-3.5" />
        <MessageSquare className="w-3.5 h-3.5" />
        Ambos
      </Button>
    </div>
  )
  
  const renderStep1 = () => (
    <div className="space-y-6">
      <div className={cn(cardStyles.default, 'p-4 border-status-success/30 bg-status-success/10')}>
        <div className="flex items-center gap-4">
          <div className="relative">
            <Avatar className="h-14 w-14 border-2 border-status-success/30">
              <AvatarFallback className="bg-status-success/15 text-status-success text-lg font-medium">
                {getInitials(hiredCandidate.name)}
              </AvatarFallback>
            </Avatar>
            <div className="absolute -bottom-1 -right-1 bg-status-success rounded-full p-1">
              <Check className="h-3 w-3 text-white" />
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className={cn(textStyles.titleLarge, 'text-status-success')}>
                {hiredCandidate.name}
              </span>
              <Badge className={cn(badgeStyles.success, 'gap-1')}>
                <PartyPopper className="h-3 w-3" />
                Contratado
              </Badge>
            </div>
            <p className={cn(textStyles.description, 'text-status-success')}>
              {hiredCandidate.email || hiredCandidate.phone || 'Contato não informado'}
            </p>
          </div>
        </div>
      </div>
      
      <div className="space-y-4">
        <div className="space-y-2">
          <label className={textStyles.label}>Canal de comunicação</label>
          {renderChannelSelector(hiredChannel, handleHiredChannelChange)}
        </div>
        
        <div className="space-y-2">
          <label className={textStyles.label}>Template de mensagem</label>
          <Select
            value={hiredTemplateId}
            onValueChange={handleHiredTemplateChange}
            disabled={templatesLoading || step1Templates.length === 0}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Selecione um template..." />
            </SelectTrigger>
            <SelectContent>
              {step1Templates.map(template => (
                <SelectItem key={template.id} value={template.id}>
                  {template.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {step1Templates.length === 0 && !templatesLoading && (
            <p className={cn(textStyles.caption, 'text-status-warning')}>
              Nenhum template disponível para {hiredChannel === 'email' ? 'Email' : hiredChannel === 'whatsapp' ? 'WhatsApp' : 'Email + WhatsApp'}
            </p>
          )}
        </div>
        
        {hiredMessage && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Eye className="h-4 w-4 text-lia-text-tertiary" />
              <label className={textStyles.label}>Preview da mensagem</label>
            </div>
            <div className={cn(cardStyles.flat, 'p-4 max-h-48 overflow-y-auto')}>
              <pre className={cn(textStyles.body, 'whitespace-pre-wrap font-sans')}>
                {hiredMessage}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
  
  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-lia-text-tertiary" />
            <span className={textStyles.label} aria-live="polite" aria-atomic="true">
              Demais candidatos ({otherCandidates.length})
            </span>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={toggleAllCandidates}
            className="text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg"
          >
            {selectedCandidateIds.length === otherCandidates.length
              ? 'Desmarcar todos'
              : 'Selecionar todos'}
          </Button>
        </div>
        
        <ScrollArea className="h-40 border rounded-md">
          <div className="p-2 space-y-1">
            {otherCandidates.length === 0 ? (
              <div className="flex items-center justify-center h-32 text-lia-text-tertiary">
                <p className={textStyles.description} aria-live="polite" aria-atomic="true">Não há outros candidatos na pipeline</p>
              </div>
            ) : (
              otherCandidates.map(candidate => (
                <div
                  key={candidate.id}
                  className={cn(
                    'flex items-center gap-3 p-2 rounded-md cursor-pointer transition-colors',
                    selectedCandidateIds.includes(candidate.id)
                      ? 'bg-lia-bg-secondary border border-lia-btn-primary-bg'
                      : 'hover:bg-lia-interactive-hover'
                  )}
                  onClick={() => toggleCandidateSelection(candidate.id)}
                >
                  <Checkbox
                    checked={selectedCandidateIds.includes(candidate.id)}
                    onCheckedChange={() => toggleCandidateSelection(candidate.id)}
                  />
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-lia-bg-tertiary text-lia-text-secondary text-xs">
                      {getInitials(candidate.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <p className={cn(textStyles.body, 'truncate')}>
                      {candidate.name}
                    </p>
                    <p className={cn(textStyles.caption, 'truncate')}>
                      {candidate.email || candidate.phone || candidate.stage}
                    </p>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {candidate.stage}
                  </Badge>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
        
        {selectedCandidateIds.length > 0 && (
          <p className={cn(textStyles.caption, 'text-lia-text-secondary')} aria-live="polite" aria-atomic="true">
            {selectedCandidateIds.length} candidato(s) selecionado(s) para receber feedback
          </p>
        )}
      </div>
      
      {selectedCandidateIds.length > 0 && (
        <div className="space-y-4">
          <div className="space-y-2">
            <label className={textStyles.label}>Canal de comunicação</label>
            {renderChannelSelector(othersChannel, handleOthersChannelChange)}
          </div>
          
          <div className="space-y-2">
            <label className={textStyles.label}>Template de feedback</label>
            <Select
              value={othersTemplateId}
              onValueChange={handleOthersTemplateChange}
              disabled={templatesLoading || step2Templates.length === 0}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Selecione um template..." />
              </SelectTrigger>
              <SelectContent>
                {step2Templates.map(template => (
                  <SelectItem key={template.id} value={template.id}>
                    {template.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {step2Templates.length === 0 && !templatesLoading && (
              <p className={cn(textStyles.caption, 'text-status-warning')}>
                Nenhum template disponível para {othersChannel === 'email' ? 'Email' : othersChannel === 'whatsapp' ? 'WhatsApp' : 'Email + WhatsApp'}
              </p>
            )}
          </div>
          
          {othersMessage && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-lia-text-tertiary" />
                <label className={textStyles.label}>Preview da mensagem</label>
              </div>
              <div className={cn(cardStyles.flat, 'p-4 max-h-40 overflow-y-auto')}>
                <pre className={cn(textStyles.body, 'whitespace-pre-wrap font-sans')}>
                  {othersMessage}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
  
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg rounded-md">
        <DialogHeader className="border-b border-lia-border-subtle pb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-lia-bg-tertiary flex items-center justify-center">
              <PartyPopper className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                Fechar Vaga
              </DialogTitle>
              <DialogDescription className="text-xs text-lia-text-secondary">
                {vacancy.title}
                {vacancy.department && ` • ${vacancy.department}`}
              </DialogDescription>
            </div>
          </div>
          
          <div className="flex items-center gap-2 pt-4">
            <div
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-colors',
                currentStep === 1
                  ? 'bg-lia-btn-primary-bg dark:bg-lia-btn-primary-bg text-lia-btn-primary-text'
                  : 'bg-lia-bg-tertiary text-lia-text-secondary'
              )}
            >
              <span className="font-medium">1</span>
              <span className="hidden sm:inline">Parabéns</span>
            </div>
            <ChevronRight className="h-4 w-4 text-lia-text-disabled" />
            <div
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-colors',
                currentStep === 2
                  ? 'bg-lia-btn-primary-bg dark:bg-lia-btn-primary-bg text-lia-btn-primary-text'
                  : 'bg-lia-bg-tertiary text-lia-text-secondary'
              )}
            >
              <span className="font-medium">2</span>
              <span className="hidden sm:inline">Feedback</span>
            </div>
          </div>
        </DialogHeader>
        
        <div className="py-4">
          {currentStep === 1 ? renderStep1() : renderStep2()}
        </div>
        
        <DialogFooter className="flex gap-2 sm:gap-2 border-t border-lia-border-subtle bg-lia-bg-secondary pt-4">
          {currentStep === 2 && (
            <Button
              type="button"
              variant="outline"
              onClick={handlePreviousStep}
              disabled={isSubmitting}
              className="flex items-center gap-2 h-9 px-4 text-xs font-medium border border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Voltar
            </Button>
          )}
          
          <div className="flex-1" />
          
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={isSubmitting}
            className="h-9 px-4 text-xs font-medium border border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover"
          >
            Cancelar
          </Button>
          
          {currentStep === 1 ? (
            <Button
              type="button"
              onClick={handleNextStep}
              disabled={!hiredTemplateId || templatesLoading}
              className="flex items-center gap-2 h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover"
            >
              Próximo
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          ) : (
            <Button
              type="button"
              onClick={handleConfirm}
              disabled={isSubmitting || (selectedCandidateIds.length > 0 && !othersTemplateId)}
              className="flex items-center gap-2 h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" />
                  Processando...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4" />
                  Confirmar Fechamento
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
