"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { Loader2 } from "lucide-react"
import { ConsentVersion, ConsentType, SubjectHistory } from "@/services/admin/consent-management-service"

const CONSENT_TYPE_LABELS: Record<string, string> = {
  personal_data: 'Dados Pessoais',
  marketing: 'Comunicações Marketing',
  sensitive_data: 'Dados Sensíveis',
  data_sharing: 'Compartilhamento com Clientes',
  cookies: 'Cookies',
  analytics: 'Analytics',
  third_party: 'Terceiros',
}

function getEventStatusBadge(eventType: string) {
  switch (eventType) {
    case 'granted':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Concedido</Badge>
    case 'revoked':
      return <Badge className="bg-wedo-purple/15 text-wedo-purple hover:bg-wedo-purple/15">Revogado</Badge>
    case 'expired':
      return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">Expirado</Badge>
    case 'renewed':
 return <Badge className="text-lia-text-primary dark:text-lia-text-primary hover:bg-lia-bg-tertiary">Renovado</Badge>
    default:
      return <Badge>{eventType}</Badge>
  }
}

interface CreateVersionModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  selectedVersion: ConsentVersion | null
  form: { consentType: ConsentType | ''; title: string; content: string; summary: string; validityMonths: number }
  setForm: React.Dispatch<React.SetStateAction<{ consentType: ConsentType | ''; title: string; content: string; summary: string; validityMonths: number }>>
  onSubmit: () => void
  onClose: () => void
}

export function CreateVersionModal({ open, onOpenChange, selectedVersion, form, setForm, onSubmit, onClose }: CreateVersionModalProps) {
  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {selectedVersion ? 'Criar Nova Versão do Termo' : 'Criar Novo Tipo de Consentimento'}
          </DialogTitle>
          <DialogDescription>
            {selectedVersion 
              ? `Criar nova versão do termo "${CONSENT_TYPE_LABELS[selectedVersion.consentType] || selectedVersion.consentType}"`
              : 'Defina um novo tipo de consentimento para coleta de dados.'
            }
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          {selectedVersion && (
            <div className="p-3 rounded-md bg-status-warning/10 border border-status-warning/30">
              <p className="text-xs text-status-warning">
                <strong>Atenção:</strong> Ao criar uma nova versão, todos os titulares com consentimento ativo 
                serão notificados para aceitar o novo termo.
              </p>
            </div>
          )}
          
          {!selectedVersion && (
            <div className="grid gap-2">
              <Label htmlFor="consent-type">Tipo de Consentimento</Label>
              <Select 
                value={form.consentType} 
                onValueChange={(v) => setForm(prev => ({ ...prev, consentType: v as ConsentType }))}
              >
                <SelectTrigger id="consent-type">
                  <SelectValue placeholder="Selecione o tipo" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(CONSENT_TYPE_LABELS).map(([key, label]) => (
                    <SelectItem key={key} value={key}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          
          <div className="grid gap-2">
            <Label htmlFor="title">Título do Termo</Label>
            <Input 
              id="title" 
              placeholder="Ex: Termo de Consentimento para Coleta de Dados Pessoais"
              value={form.title}
              onChange={(e) => setForm(prev => ({ ...prev, title: e.target.value }))}
            />
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="summary">Resumo (opcional)</Label>
            <Input 
              id="summary" 
              placeholder="Breve descrição do propósito deste termo"
              value={form.summary}
              onChange={(e) => setForm(prev => ({ ...prev, summary: e.target.value }))}
            />
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="content">Conteúdo do Termo (HTML)</Label>
            <Textarea 
              id="content" 
              placeholder="<p>Digite aqui o conteúdo completo do termo de consentimento...</p>"
              value={form.content}
              onChange={(e) => setForm(prev => ({ ...prev, content: e.target.value }))}
              className="min-h-chart-sm font-mono text-sm"
            />
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="validity">Validade (meses)</Label>
            <Input 
              id="validity" 
              type="number" 
              value={form.validityMonths}
              onChange={(e) => setForm(prev => ({ ...prev, validityMonths: parseInt(e.target.value) || 12 }))}
            />
          </div>
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>Cancelar</Button>
          <Button 
            type="submit" 
            onClick={onSubmit}
            disabled={!form.title || !form.content || (!selectedVersion && !form.consentType)}
          >
            {selectedVersion ? 'Publicar Nova Versão' : 'Criar Tipo'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface HistoryModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  subjectHistory: SubjectHistory | null
}

export function HistoryModal({ open, onOpenChange, subjectHistory }: HistoryModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Histórico do Titular</DialogTitle>
          <DialogDescription>
            {subjectHistory && (
              <span>
                {subjectHistory.subjectName || subjectHistory.subjectEmail || subjectHistory.subjectIdentifier}
              </span>
            )}
          </DialogDescription>
        </DialogHeader>
        {subjectHistory ? (
          <div className="space-y-4">
            {subjectHistory.currentConsents.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2 text-lia-text-primary dark:text-lia-text-primary">
                  Consentimentos Atuais
                </h4>
                <div className="space-y-2">
                  {subjectHistory.currentConsents.map((consent, index) => (
                    <div key={`${consent.consentType}-${index}`} className="flex items-center justify-between p-3 rounded-md bg-lia-bg-secondary">
                      <div>
                        <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">
                          {CONSENT_TYPE_LABELS[consent.consentType] || consent.consentType}
                        </span>
                        <span className="text-xs ml-2 text-lia-text-tertiary dark:text-lia-text-secondary">
                          v{consent.version}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={
                          consent.status === 'active' 
                            ? 'bg-status-success/15 text-status-success' 
                            : consent.status === 'revoked'
                            ? 'bg-wedo-purple/15 text-wedo-purple'
                            : 'bg-status-error/15 text-status-error'
                        }>
                          {consent.status === 'active' ? 'Ativo' : consent.status === 'revoked' ? 'Revogado' : 'Expirado'}
                        </Badge>
                        <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                          até {new Date(consent.expiresAt).toLocaleDateString('pt-BR')}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div>
              <h4 className="text-sm font-medium mb-2 text-lia-text-primary dark:text-lia-text-primary">
                Histórico de Eventos
              </h4>
              <div className="space-y-2">
                {subjectHistory.events.map((event) => (
                  <div key={event.id} className="flex items-center justify-between p-3 rounded-md border">
                    <div className="flex items-center gap-3">
                      {getEventStatusBadge(event.eventType)}
                      <div>
                        <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">
                          {CONSENT_TYPE_LABELS[event.consentType] || event.consentType}
                        </span>
                        <span className="text-xs ml-2 text-lia-text-tertiary dark:text-lia-text-secondary">
                          v{event.version}
                        </span>
                      </div>
                    </div>
                    <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                      {new Date(event.createdAt).toLocaleDateString('pt-BR', {
                        day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
                      })}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-secondary dark:text-lia-text-tertiary" />
          </div>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Fechar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
