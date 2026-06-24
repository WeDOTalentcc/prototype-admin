"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState, useEffect, useMemo } from"react"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Textarea } from"@/components/ui/textarea"
import { Checkbox } from"@/components/ui/checkbox"
import { Chip } from "@/components/ui/chip"
import { ScrollArea } from"@/components/ui/scroll-area"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription
} from"@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import { Label } from"@/components/ui/label"
import { 
  Share2, 
  Plus, 
  X, 
  Loader2, 
  Users, 
  Search, 
  List,
  Mail,
  Clock,
  MessageSquare,
  Star,
  Eye,
  Phone,
  Send,
  ExternalLink,
  Shield
} from"lucide-react"
import { cn } from"@/lib/utils"
import { textStyles, cardStyles } from '@/lib/design-tokens'
import { useCommunicationTemplates, type CommunicationTemplate } from '@/hooks/chat/use-communication-templates'
import { useAuth } from '@/contexts/auth-context'
import { toast } from"sonner"

interface Recipient {
  id: string
  email: string
  phone?: string
  name?: string
}

interface ShareSearchModalProps {
  open: boolean
  onClose: () => void
  shareType: 'search' | 'list'
  title: string
  candidateIds: string[]
  candidateCount: number
  sourceQuery?: string
  sourceListId?: string
  onSuccess?: (sharedSearch: Record<string, unknown>) => void
}

type ShareChannel = 'email' | 'whatsapp' | 'both'

const EXPIRY_OPTIONS = [
  { value: 'none', label: 'Sem prazo' },
  { value: '7', label: '7 dias' },
  { value: '14', label: '14 dias' },
  { value: '30', label: '30 dias' },
  { value: 'custom', label: 'Personalizado' },
]

export function ShareSearchModal({
  open,
  onClose,
  shareType,
  title,
  candidateIds,
  candidateCount,
  sourceQuery,
  sourceListId,
  onSuccess
}: ShareSearchModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('share-search', open)

  const { user } = useAuth()
const [currentShareType, setCurrentShareType] = useState<'search' | 'list'>(shareType)
  const [recipients, setRecipients] = useState<Recipient[]>([])
  const [newEmail, setNewEmail] = useState('')
  const [newPhone, setNewPhone] = useState('')
  const [message, setMessage] = useState('')
  const [subject, setSubject] = useState('')
  const [expiryOption, setExpiryOption] = useState('7')
  const [customExpiryDays, setCustomExpiryDays] = useState('')
  const [canComment, setCanComment] = useState(true)
  const [canRate, setCanRate] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [channel, setChannel] = useState<ShareChannel>('email')
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')

  const templateChannel = channel === 'both' ? 'email' : channel
  const { templates, loading: templatesLoading } = useCommunicationTemplates({
    channel: templateChannel,
    situation: 'share_with_manager',
    autoLoad: true
  })

  const filteredTemplates = useMemo(() => {
    return templates.filter(t => 
      t.channel === templateChannel && 
      (t.situation === 'share_with_manager' || t.situation === 'contato_inicial')
    ).slice(0, 5)
  }, [templates, templateChannel])

  useEffect(() => {
    if (open) {
      setCurrentShareType(shareType)
      setRecipients([])
      setNewEmail('')
      setNewPhone('')
      setExpiryOption('7')
      setCustomExpiryDays('')
      setCanComment(true)
      setCanRate(true)
      setChannel('email')
      setSelectedTemplateId('')
      setSubject(`Candidatos para sua avaliação — ${title || 'Shortlist'}`)
      setMessage('')
    }
  }, [open, shareType, title])

  useEffect(() => {
    if (filteredTemplates.length > 0 && !selectedTemplateId) {
      const shareTemplate = filteredTemplates.find(t => t.situation === 'share_with_manager')
      if (shareTemplate) {
        setSelectedTemplateId(shareTemplate.id)
        if (shareTemplate.subject) setSubject(shareTemplate.subject)
        if (shareTemplate.body) setMessage(shareTemplate.body)
      }
    }
  }, [filteredTemplates, selectedTemplateId])

  const handleSelectTemplate = (template: CommunicationTemplate) => {
    setSelectedTemplateId(template.id)
    if (template.subject) setSubject(template.subject)
    if (template.body) setMessage(template.body)
  }

  const handleAddRecipient = () => {
    const email = newEmail.trim()
    if (!email) return

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      toast.error("Email inválido", { description:"Por favor, insira um email válido." })
      return
    }

    // G6-Domain: só permite destinatários do mesmo domínio da organização
    const orgDomain = user?.email?.split('@')[1]?.toLowerCase()
    if (orgDomain) {
      const recipientDomain = email.split('@')[1]?.toLowerCase()
      if (recipientDomain !== orgDomain) {
        toast.error("Domínio não permitido", {
          description: `Só é possível compartilhar com emails @${orgDomain}.`,
        })
        return
      }
    }

    if (recipients.some(r => r.email.toLowerCase() === email.toLowerCase())) {
      toast.error("Email já adicionado", { description:"Este email já está na lista de destinatários." })
      return
    }

    setRecipients([...recipients, {
      id: crypto.randomUUID(),
      email,
      phone: newPhone.trim() || undefined,
      name: ''
    }])
    setNewEmail('')
    setNewPhone('')
  }

  const handleRemoveRecipient = (id: string) => {
    setRecipients(recipients.filter(r => r.id !== id))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAddRecipient()
    }
  }

  const calculateExpiryDate = (): string | null => {
    if (expiryOption === 'none') return null
    let days: number
    if (expiryOption === 'custom') {
      days = parseInt(customExpiryDays) || 0
      if (days <= 0) return null
    } else {
      days = parseInt(expiryOption)
    }
    const expiryDate = new Date()
    expiryDate.setDate(expiryDate.getDate() + days)
    return expiryDate.toISOString()
  }

  const getExpiryLabel = (): string => {
    if (expiryOption === 'none') return 'Sem prazo'
    if (expiryOption === 'custom') {
      const days = parseInt(customExpiryDays) || 0
      return days > 0 ? `${days} dias` : 'Sem prazo'
    }
    return `${expiryOption} dias`
  }

  const renderPreview = (content: string): string => {
    const vars: Record<string, string> = {
      recruiter_name: 'Recrutador(a)',
      job_title: title || 'Vaga',
      candidate_count: String(candidateCount),
      share_link: 'https://app.wedotalent.com/shared/abc123',
      otp_code: '•••••',
      expiry_date: getExpiryLabel(),
      message: message || '',
      company_name: 'WeDoTalent'
    }
    let rendered = content
    for (const [key, value] of Object.entries(vars)) {
      rendered = rendered.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value)
    }
    return rendered
  }

  const handleSubmit = async () => {
    if (recipients.length === 0) {
      toast.error("Adicione destinatários", { description:"Adicione pelo menos um email para compartilhar." })
      return
    }

    setIsSubmitting(true)
    try {
      const hasPhone = recipients.some(r => r.phone)
      let effectiveChannel: ShareChannel = channel
      if (channel === 'whatsapp' && !hasPhone) effectiveChannel = 'email'

      const payload = {
        share_type: currentShareType,
        title,
        description: message || null,
        candidate_ids: candidateIds,
        source_query: sourceQuery || null,
        source_list_id: sourceListId || null,
        recipients: recipients.map(r => ({
          email: r.email,
          name: r.name || null,
          phone: r.phone || null,
          role: 'hiring_manager'
        })),
        message: message || null,
        subject: (effectiveChannel === 'email' || effectiveChannel === 'both') ? (subject || null) : null,
        expires_at: calculateExpiryDate(),
        can_comment: canComment,
        can_rate: canRate,
        channel: effectiveChannel
      }

      const response = await fetch('/api/backend-proxy/shared-searches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        throw new Error(error.detail || 'Erro ao compartilhar')
      }

      const sharedSearch = await response.json()

      const channelLabel = effectiveChannel === 'whatsapp' ? 'WhatsApp' : effectiveChannel === 'both' ? 'email e WhatsApp' : 'email'
      toast.success("Compartilhado com sucesso", { description: `Enviado por ${channelLabel} para ${recipients.length} destinatário${recipients.length > 1 ? 's' : ''}.` })

      onSuccess?.(sharedSearch)
      onClose()
    } catch (error) {
      toast.error("Erro ao compartilhar", { description: error instanceof Error ? error.message :"Não foi possível compartilhar. Tente novamente." })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) onClose()
  }

  const canSubmit = recipients.length > 0 && 
    (expiryOption !== 'custom' || (customExpiryDays && parseInt(customExpiryDays) > 0))

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent 
        className={`max-w-4xl h-[80vh] flex flex-col p-0 gap-0 ${cardStyles.default}`} 
        data-testid="share-search-modal"
      >
        <DialogHeader className="px-6 pt-5 pb-3 flex-shrink-0">
          <DialogTitle className={`${textStyles.title} flex items-center gap-2`}>
            <Share2 className="w-5 h-5 text-lia-text-secondary" />
            Compartilhar com Gestor
          </DialogTitle>
          <DialogDescription className={textStyles.bodySmall} asChild>
            <div>Envie candidatos para avaliação de gestores de contratação.</div>
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 flex overflow-hidden">
          <div className="w-[55%] border-r border-lia-border-subtle overflow-y-auto">
            <ScrollArea className="h-full">
              <div className="p-5 space-y-5">
                <div className={`p-3 rounded-md ${cardStyles.flat}`}>
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center bg-lia-bg-primary border border-lia-border-subtle">
                      {currentShareType === 'search' ? (
                        <Search className="w-4 h-4 text-lia-text-secondary" />
                      ) : (
                        <List className="w-4 h-4 text-lia-text-secondary" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`${textStyles.subtitle} truncate text-sm`}>{title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Chip variant="neutral" muted className="gap-1 text-micro">
                          <Users className="w-3 h-3" />
                          {candidateCount} candidato{candidateCount !== 1 ? 's' : ''}
                        </Chip>
                        {sourceQuery && (
                          <span className="text-micro text-lia-text-tertiary truncate max-w-[160px]">"{sourceQuery}"
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <Label className={`${textStyles.label} mb-2 block`}>Canal de Envio</Label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      type="button"
                      onClick={() => { setChannel('email'); setSelectedTemplateId('') }}
                      className={cn("flex items-center gap-2 p-2.5 rounded-md border transition-colors text-left",
                        channel === 'email'
                          ?"border-lia-btn-primary-bg bg-lia-bg-secondary text-lia-text-primary"
                          :"border-lia-border-subtle hover:border-lia-border-default text-lia-text-secondary"
                      )}
                    >
                      <Mail className="w-4 h-4 flex-shrink-0" />
                      <div>
                        <div className="text-xs font-medium">Email</div>
                        <div className="text-micro opacity-70">Convite</div>
                      </div>
                    </button>
                    <button
                      type="button"
                      onClick={() => { setChannel('whatsapp'); setSelectedTemplateId('') }}
                      className={cn("flex items-center gap-2 p-2.5 rounded-md border transition-colors text-left",
                        channel === 'whatsapp'
                          ?"border-status-success/30 bg-status-success/10 dark:bg-status-success/20 text-status-success"
                          :"border-lia-border-subtle hover:border-lia-border-default text-lia-text-secondary"
                      )}
                    >
                      <MessageSquare className="w-4 h-4 flex-shrink-0" />
                      <div>
                        <div className="text-xs font-medium">WhatsApp</div>
                        <div className="text-micro opacity-70">Mensagem</div>
                      </div>
                    </button>
                    <button
                      type="button"
                      onClick={() => { setChannel('both'); setSelectedTemplateId('') }}
                      className={cn("flex items-center gap-2 p-2.5 rounded-md border transition-colors text-left",
                        channel === 'both'
                          ?"border-lia-btn-primary-bg bg-lia-bg-secondary text-lia-text-primary"
                          :"border-lia-border-subtle hover:border-lia-border-default text-lia-text-secondary"
                      )}
                    >
                      <Send className="w-4 h-4 flex-shrink-0" />
                      <div>
                        <div className="text-xs font-medium">Ambos</div>
                        <div className="text-micro opacity-70">Email + WA</div>
                      </div>
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className={textStyles.label}>
                    <Mail className="w-3.5 h-3.5 inline-block mr-1 text-lia-text-tertiary" />
                    Destinatários
                  </Label>
                  <div className="flex gap-2">
                    <Input
                      type="email"
                      placeholder="Email do gestor"
                      value={newEmail}
                      onChange={(e) => setNewEmail(e.target.value)}
                      onKeyDown={handleKeyDown}
                      className="flex-1 h-9 text-xs"
                    />
                    {(channel === 'whatsapp' || channel === 'both') && (
                      <Input
                        type="tel"
                        placeholder="Telefone (opcional)"
                        value={newPhone}
                        onChange={(e) => setNewPhone(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="w-[140px] h-9 text-xs"
                      />
                    )}
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={handleAddRecipient}
                      className="flex-shrink-0 h-9 w-9"
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>

                  {recipients.length > 0 ? (
                    <div className="space-y-1.5 max-h-[100px] overflow-y-auto">
                      {recipients.map((recipient) => (
                        <div 
                          key={recipient.id} 
                          className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle"
                        >
                          <Mail className="w-3 h-3 text-lia-text-muted flex-shrink-0" />
                          <span className="text-xs text-lia-text-secondary truncate flex-1">
                            {recipient.email}
                          </span>
                          {recipient.phone && (
                            <>
                              <Phone className="w-3 h-3 text-status-success flex-shrink-0" />
                              <span className="text-micro text-lia-text-tertiary truncate">
                                {recipient.phone}
                              </span>
                            </>
                          )}
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-5 w-5 flex-shrink-0 hover:text-status-error hover:bg-status-error/10"
                            onClick={() => handleRemoveRecipient(recipient.id)}
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-micro text-status-warning bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-xl p-2">
                      Adicione pelo menos um email de gestor para compartilhar
                    </p>
                  )}
                </div>

                {filteredTemplates.length > 0 && (
                  <div className="space-y-2">
                    <Label className={textStyles.label}>Template</Label>
                    <div className="flex gap-2 overflow-x-auto pb-1">
                      {filteredTemplates.map((tpl) => (
                        <button
                          key={tpl.id}
                          type="button"
                          onClick={() => handleSelectTemplate(tpl)}
                          className={cn("flex-shrink-0 px-3 py-1.5 rounded-md border text-xs transition-colors whitespace-nowrap",
                            selectedTemplateId === tpl.id
                              ?"border-lia-btn-primary-bg bg-lia-btn-primary-bg dark:bg-lia-btn-primary-bg text-lia-btn-primary-text"
                              :"border-lia-border-subtle hover:border-lia-border-medium text-lia-text-secondary"
                          )}
                        >
                          {tpl.name}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {(channel === 'email' || channel === 'both') && (
                  <div className="space-y-1.5">
                    <Label className={`${textStyles.label} text-xs`}>Assunto</Label>
                    <Input
                      placeholder="Assunto do email"
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      className="h-8 text-xs"
                    />
                  </div>
                )}

                <div className="space-y-1.5">
                  <Label className={`${textStyles.label} text-xs`}>
                    Mensagem
                  </Label>
                  <Textarea
                    placeholder="Mensagem personalizada para o gestor..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    className="min-h-[70px] text-xs resize-none"
                  />
                </div>

                <div className="space-y-3 p-3 rounded-xl bg-lia-bg-secondary/50 border border-lia-border-subtle">
                  <Label className={`${textStyles.label} text-xs`}>Configurações de acesso</Label>
                  
                  <div className="space-y-1.5">
                    <Label className="text-micro text-lia-text-tertiary flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Validade do link
                    </Label>
                    <div className="flex gap-2">
                      <Select value={expiryOption} onValueChange={setExpiryOption}>
                        <SelectTrigger className={cn("h-8 text-xs",
                          expiryOption === 'custom' ?"w-1/2" :"w-full"
                        )}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent position="popper" sideOffset={4}>
                          {EXPIRY_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value} className="text-xs">
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {expiryOption === 'custom' && (
                        <div className="flex items-center gap-1.5 flex-1">
                          <Input
                            type="number"
                            min="1"
                            max="365"
                            placeholder="Dias"
                            value={customExpiryDays}
                            onChange={(e) => setCustomExpiryDays(e.target.value)}
                            className="h-8 w-16 text-xs"
                          />
                          <span className="text-micro text-lia-text-tertiary">dias</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2 pt-1">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="can-comment"
                        checked={canComment}
                        onCheckedChange={(checked) => setCanComment(checked === true)}
                      />
                      <Label htmlFor="can-comment" className="text-xs cursor-pointer flex items-center gap-1">
                        <MessageSquare className="w-3 h-3 text-lia-text-tertiary" />
                        Pode comentar
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="can-rate"
                        checked={canRate}
                        onCheckedChange={(checked) => setCanRate(checked === true)}
                      />
                      <Label htmlFor="can-rate" className="text-xs cursor-pointer flex items-center gap-1">
                        <Star className="w-3 h-3 text-lia-text-tertiary" />
                        Pode dar rating
                      </Label>
                    </div>
                  </div>
                </div>
              </div>
            </ScrollArea>
          </div>

          <div className="flex-1 bg-lia-bg-secondary/50/50 overflow-hidden flex flex-col">
            <div className="px-5 pt-4 pb-3 flex items-center justify-between flex-shrink-0">
              <h4 className={`${textStyles.label} flex items-center gap-2 text-xs`}>
                <Eye className="w-3.5 h-3.5 text-lia-text-tertiary" />
                Preview da Mensagem
              </h4>
              <Chip variant="neutral" className="text-micro h-5">
                {channel === 'email' ? 'Email' : channel === 'whatsapp' ? 'WhatsApp' : 'Email + WhatsApp'}
              </Chip>
            </div>

            <ScrollArea className="flex-1 px-5 pb-4">
              {(channel === 'email' || channel === 'both') ? (
                <div className="space-y-3">
                <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary overflow-hidden">
                  <div className="bg-gradient-to-r from-lia-bg-tertiary to-lia-bg-primary px-5 py-4">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-8 h-8 rounded-xl bg-lia-bg-primary/10 flex items-center justify-center">
                        <Users className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <p className="text-white text-xs font-medium">WeDoTalent</p>
                        <p className="text-white/60 text-micro">Plataforma de Recrutamento</p>
                      </div>
                    </div>
                  </div>

                  <div className="px-5 py-4 space-y-3">
                    <div className="pb-2">
                      <p className="text-micro text-lia-text-tertiary">Assunto</p>
                      <p className="text-xs font-medium text-lia-text-primary" aria-live="polite" aria-atomic="true">
                        {renderPreview(subject) || 'Candidatos para sua avaliação'}
                      </p>
                    </div>

                    <div className="space-y-2 text-xs text-lia-text-secondary">
                      <p>Olá,</p>
                      {message ? (
                        <p className="whitespace-pre-wrap">{renderPreview(message)}</p>
                      ) : (
                        <p className="text-lia-text-disabled italic">
                          Sua mensagem personalizada aparecerá aqui...
                        </p>
                      )}
                    </div>

                    <div className="bg-lia-bg-secondary/30 rounded-xl p-3 space-y-2">
                      <div className="flex items-center gap-2">
                        <Users className="w-3.5 h-3.5 text-lia-text-tertiary" />
                        <span className="text-xs font-medium text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                          {candidateCount} candidato{candidateCount !== 1 ? 's' : ''} para avaliar
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="w-3.5 h-3.5 text-lia-text-tertiary" />
                        <span className="text-micro text-lia-text-tertiary">
                          Válido por {getExpiryLabel().toLowerCase()}
                        </span>
                      </div>
                      {(!canComment || !canRate) && (
                        <div className="flex items-center gap-2">
                          <Shield className="w-3.5 h-3.5 text-lia-text-tertiary" />
                          <span className="text-micro text-lia-text-tertiary">
                            {!canRate ? 'Somente visualização' : 'Sem comentários'}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="pt-1">
                      <div className="bg-lia-bg-tertiary rounded-xl p-2.5 text-center">
                        <p className="text-micro text-lia-text-tertiary mb-1">Código de acesso</p>
                        <p className="text-sm font-mono font-bold tracking-widest text-lia-text-primary">
                          A1B2C3
                        </p>
                      </div>
                    </div>

                    <div className="flex justify-center pt-1">
                      <div className="bg-lia-btn-primary-bg dark:bg-lia-btn-primary-bg text-lia-btn-primary-text rounded-xl px-6 py-2 text-xs font-medium flex items-center gap-2">
                        <ExternalLink className="w-3.5 h-3.5" />
                        Acessar Candidatos
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-lia-border-subtle px-5 py-3">
                    <p className="text-micro text-lia-text-muted text-center">
                      Powered by WeDoTalent · Política de Privacidade
                    </p>
                  </div>
                </div>

                {channel === 'both' && (
                  <div className="mt-3">
                    <div className="flex items-center gap-2 mb-2">
                      <MessageSquare className="w-3 h-3 text-status-success" />
                      <span className="text-micro font-medium text-lia-text-tertiary">Preview WhatsApp</span>
                    </div>
                    <div className="flex justify-end">
                      <div className="max-w-[85%]">
                        <div className="bg-whatsapp-bubble dark:bg-status-success/40 rounded-xl rounded-tr-sm px-3 py-2 shadow-lia-sm">
                          <p className="text-xs text-lia-text-primary whitespace-pre-wrap">
                            {message ? renderPreview(message) : (
                              <span className="italic text-lia-text-tertiary text-micro">Mensagem...</span>
                            )}
                          </p>
                          <div className="mt-1.5 pt-1.5 border-t border-status-success/30 dark:border-status-success/30 text-micro text-lia-text-secondary space-y-0.5">
                            <p aria-live="polite" aria-atomic="true">📋 {candidateCount} candidato{candidateCount !== 1 ? 's' : ''} · 🔗 Link · 🔑 OTP</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex justify-end">
                    <div className="max-w-[85%]">
                      <div className="bg-whatsapp-bubble dark:bg-status-success/40 rounded-xl rounded-tr-sm px-3 py-2 shadow-lia-sm">
                        <p className="text-xs text-lia-text-primary whitespace-pre-wrap">
                          {message ? renderPreview(message) : (
                            <span className="italic text-lia-text-tertiary">
                              Sua mensagem aparecerá aqui...
                            </span>
                          )}
                        </p>
                        {message && (
                          <>
                            <div className="mt-2 pt-2 border-t border-status-success/30 dark:border-status-success/30">
                              <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                                📋 {candidateCount} candidato{candidateCount !== 1 ? 's' : ''} para avaliar
                              </p>
                              <p className="text-micro text-lia-text-secondary">
                                🔗 Link: app.wedotalent.com/shared/...
                              </p>
                              <p className="text-micro text-lia-text-secondary">
                                🔑 Código: A1B2C3
                              </p>
                              <p className="text-micro text-lia-text-secondary">
                                ⏰ Válido por {getExpiryLabel().toLowerCase()}
                              </p>
                            </div>
                          </>
                        )}
                        <div className="flex justify-end mt-1">
                          <span className="text-micro text-lia-text-tertiary">
                            {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </ScrollArea>
          </div>
        </div>

        <div className="px-6 py-3 border-t border-lia-border-subtle flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2 text-micro text-lia-text-tertiary">
            <Shield className="w-3 h-3" />
            Acesso protegido por OTP
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover"
            >
              Cancelar
            </Button>
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting || !canSubmit}
              className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                  Compartilhando...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Compartilhar
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
