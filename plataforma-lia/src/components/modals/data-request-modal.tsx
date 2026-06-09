"use client"

import { useState, useCallback } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Send, Mail, MessageSquare, Phone, FileText, User, Clock, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { DEFAULT_DATA_FIELDS, DataField } from '@/hooks/company/use-data-request-config'

export interface DataRequestCandidate {
  id: string
  name: string
  email?: string
  phone?: string
  avatar?: string | null
}

interface DataRequestModalProps {
  isOpen: boolean
  onClose: () => void
  candidates: DataRequestCandidate[]
  jobTitle?: string
  onSubmit: (data: DataRequestSubmitData) => Promise<void>
}

export interface DataRequestSubmitData {
  candidateIds: string[]
  fields: string[]
  channel: 'email' | 'whatsapp' | 'both' | 'voice'
  expirationDays: number
  templateId?: string
}

interface DataRequestTemplate {
  id: string
  name: string
  description: string
  fields: string[]
}

const DATA_REQUEST_TEMPLATES: DataRequestTemplate[] = [
  {
    id: 'basic',
    name: 'Dados Básicos',
    description: 'Nome, email e telefone',
    fields: ['full_name', 'email', 'phone']
  },
  {
    id: 'screening',
    name: 'Triagem Inicial',
    description: 'Dados básicos + currículo',
    fields: ['full_name', 'email', 'phone', 'cv_document']
  },
  {
    id: 'interview',
    name: 'Pré-Entrevista',
    description: 'Dados pessoais para agendamento',
    fields: ['full_name', 'email', 'phone', 'cpf', 'birth_date']
  },
  {
    id: 'offer',
    name: 'Proposta/Admissão',
    description: 'Documentos para contratação',
    fields: ['full_name', 'email', 'phone', 'cpf', 'birth_date', 'address', 'rg', 'ctps', 'pis', 'bank_info', 'id_document', 'proof_of_address']
  },
  {
    id: 'custom',
    name: 'Personalizado',
    description: 'Selecione os campos manualmente',
    fields: []
  }
]

export function DataRequestModal({
  isOpen,
  onClose,
  candidates,
  jobTitle,
  onSubmit
}: DataRequestModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('basic')
  const [selectedFields, setSelectedFields] = useState<Set<string>>(new Set(['full_name', 'email', 'phone']))
  const [channel, setChannel] = useState<'email' | 'whatsapp' | 'both' | 'voice'>('email')
  const [expirationDays, setExpirationDays] = useState(7)
  const [showAllFields, setShowAllFields] = useState(false)

  const isSingleCandidate = candidates.length === 1
  const availableFields = DEFAULT_DATA_FIELDS.filter(f => f.enabled)
  const displayedFields = showAllFields ? availableFields : availableFields.slice(0, 8)

  const handleTemplateChange = useCallback((templateId: string) => {
    setSelectedTemplate(templateId)
    const template = DATA_REQUEST_TEMPLATES.find(t => t.id === templateId)
    if (template && templateId !== 'custom') {
      setSelectedFields(new Set(template.fields))
    }
  }, [])

  const toggleField = useCallback((fieldId: string) => {
    setSelectedTemplate('custom')
    setSelectedFields(prev => {
      const newSet = new Set(prev)
      if (newSet.has(fieldId)) {
        newSet.delete(fieldId)
      } else {
        newSet.add(fieldId)
      }
      return newSet
    })
  }, [])

  const handleSubmit = async () => {
    if (selectedFields.size === 0) return
    
    setIsSubmitting(true)
    try {
      await onSubmit({
        candidateIds: candidates.map(c => c.id),
        fields: Array.from(selectedFields),
        channel,
        expirationDays,
        templateId: selectedTemplate !== 'custom' ? selectedTemplate : undefined
      })
      onClose()
    } catch (err) {
    } finally {
      setIsSubmitting(false)
    }
  }

  const getFieldIcon = (type: DataField['type']) => {
    switch (type) {
      case 'file': return <FileText className="w-3 h-3" />
      default: return null
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto rounded-md" data-testid="data-request-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-sm font-semibold text-lia-text-primary">
            <Send className="w-4 h-4 text-lia-text-secondary" />
            Solicitar Dados
          </DialogTitle>
          <DialogDescription className="text-xs text-lia-text-secondary">
            {isSingleCandidate 
              ? `Solicitar informações de ${candidates[0]?.name}`
              : `Solicitar informações de ${candidates.length} candidatos`
            }
            {jobTitle && <span className="text-lia-text-tertiary"> · {jobTitle}</span>}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-4">
          <div className="space-y-2">
            <Label className="text-xs font-medium text-lia-text-primary">Template</Label>
            <Select value={selectedTemplate} onValueChange={handleTemplateChange}>
              <SelectTrigger className="w-full h-9">
                <SelectValue placeholder="Selecione um modelo" />
              </SelectTrigger>
              <SelectContent className="z-select">
                {DATA_REQUEST_TEMPLATES.map((template) => (
                  <SelectItem key={template.id} value={template.id}>
                    <div className="flex flex-col items-start">
                      <span className="text-xs">{template.name}</span>
                      <span className="text-micro text-lia-text-secondary">{template.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs font-medium text-lia-text-primary">Campos a Solicitar</Label>
              <span className="text-xs text-lia-text-secondary">{selectedFields.size} selecionados</span>
            </div>
            <div className="border border-lia-border-subtle rounded-xl p-2 space-y-1 max-h-chart-sm overflow-y-auto">
              {displayedFields.map((field) => (
                <label
                  key={field.id}
                  className={cn(
                    "flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors",
                    selectedFields.has(field.id) 
                      ? "bg-lia-bg-tertiary border border-lia-btn-primary-bg" 
                      : "hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-hover"
                  )}
                >
                  <Checkbox
                    checked={selectedFields.has(field.id)}
                    onCheckedChange={() => toggleField(field.id)}
                  />
                  <div className="flex items-center gap-2 flex-1">
                    {getFieldIcon(field.type)}
                    <span className="text-xs text-lia-text-primary">{field.displayName}</span>
                  </div>
                  {field.type === 'file' && (
                    <span className="text-micro bg-lia-bg-tertiary text-lia-text-tertiary px-1.5 py-0.5 rounded-full">
                      Arquivo
                    </span>
                  )}
                </label>
              ))}
            </div>
            {availableFields.length > 8 && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-xs"
                onClick={() => setShowAllFields(!showAllFields)}
              >
                {showAllFields ? (
                  <>
                    <ChevronUp className="w-3 h-3 mr-1" />
                    Mostrar menos
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-3 h-3 mr-1" />
                    Ver todos os {availableFields.length} campos
                  </>
                )}
              </Button>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-xs font-medium text-lia-text-primary">Canal de Envio</Label>
              <Select value={channel} onValueChange={(v: 'email' | 'whatsapp' | 'both' | 'voice') => setChannel(v)}>
                <SelectTrigger className="h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="z-select">
                  <SelectItem value="email">
                    <div className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5" />
                      <span className="text-xs">Email</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="whatsapp">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span className="text-xs">WhatsApp</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="both">
                    <div className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5" />
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span className="text-xs">Ambos (Email + WhatsApp)</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="voice">
                    <div className="flex items-center gap-2">
                      <Phone className="w-3.5 h-3.5" />
                      <span className="text-xs">Voz (ligação)</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-xs font-medium text-lia-text-primary flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Expira em
              </Label>
              <Select value={expirationDays.toString()} onValueChange={(v) => setExpirationDays(parseInt(v))}>
                <SelectTrigger className="h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="z-select">
                  <SelectItem value="3"><span className="text-xs">3 dias</span></SelectItem>
                  <SelectItem value="5"><span className="text-xs">5 dias</span></SelectItem>
                  <SelectItem value="7"><span className="text-xs">7 dias</span></SelectItem>
                  <SelectItem value="14"><span className="text-xs">14 dias</span></SelectItem>
                  <SelectItem value="30"><span className="text-xs">30 dias</span></SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {!isSingleCandidate && (
            <div className="space-y-2">
              <Label className="text-xs font-medium text-lia-text-primary flex items-center gap-1">
                <User className="w-3 h-3" />
                Candidatos ({candidates.length})
              </Label>
              <div className="border border-lia-border-subtle rounded-xl p-2 max-h-[100px] overflow-y-auto">
                <div className="flex flex-wrap gap-1.5">
                  {candidates.slice(0, 10).map((candidate) => (
                    <span
                      key={candidate.id}
                      className="text-micro bg-lia-bg-tertiary px-2 py-1 rounded-full text-lia-text-secondary"
                    >
                      {candidate.name.split(' ')[0]}
                    </span>
                  ))}
                  {candidates.length > 10 && (
                    <span className="text-micro text-lia-text-tertiary px-2 py-1">
                      +{candidates.length - 10} mais
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 border-t border-lia-border-subtle bg-lia-bg-secondary p-4 -mx-6 -mb-6 rounded-b-xl">
          <Button variant="outline" onClick={onClose} disabled={isSubmitting} className="h-9 px-4 text-xs font-medium bg-lia-bg-primary border border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg">
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || selectedFields.size === 0}
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" />
                Enviando...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Enviar Solicitação
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
