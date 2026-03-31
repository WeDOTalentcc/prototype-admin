"use client"

import NextImage from "next/image"
import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Send, ArrowRight, X, FileText, User, Phone, Mail, Calendar, MapPin, CreditCard, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface PendingField {
  id: string
  name: string
  displayName: string
  type: 'text' | 'email' | 'phone' | 'date' | 'file' | 'select' | 'textarea'
  lastRequestedAt?: string
  status?: 'pending' | 'expired' | 'never_requested'
}

export interface DataBlockingCandidate {
  id: string
  name: string
  email?: string
  avatar?: string | null
}

interface DataBlockingModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: DataBlockingCandidate
  pendingFields: PendingField[]
  targetStage: string
  targetStageDisplayName: string
  onResendRequest: () => void
  onProceedAnyway: () => void
}

const STAGE_DISPLAY_NAMES: Record<string, string> = {
  sourcing: 'Sourcing',
  screening: 'Triagem',
  long_list: 'Long List',
  short_list: 'Short List',
  interview_hr: 'Entrevista RH',
  interview_technical: 'Entrevista Técnica',
  interview_manager: 'Entrevista Gestor',
  interview_final: 'Entrevista Final',
  offer: 'Proposta',
  hired: 'Contratado',
  rejected: 'Reprovado',
  offer_declined: 'Proposta Recusada'
}

export function DataBlockingModal({
  isOpen,
  onClose,
  candidate,
  pendingFields,
  targetStage,
  targetStageDisplayName,
  onResendRequest,
  onProceedAnyway
}: DataBlockingModalProps) {
  const [isResending, setIsResending] = useState(false)
  const [isProceeding, setIsProceeding] = useState(false)

  const stageDisplay = targetStageDisplayName || STAGE_DISPLAY_NAMES[targetStage] || targetStage

  const getFieldIcon = (fieldId: string) => {
    switch (fieldId) {
      case 'email': return <Mail className="w-4 h-4" />
      case 'phone': return <Phone className="w-4 h-4" />
      case 'full_name': return <User className="w-4 h-4" />
      case 'birth_date': return <Calendar className="w-4 h-4" />
      case 'address': return <MapPin className="w-4 h-4" />
      case 'cpf':
      case 'rg':
      case 'ctps':
      case 'pis':
      case 'bank_info': return <CreditCard className="w-4 h-4" />
      case 'cv_document':
      case 'id_document':
      case 'proof_of_address': return <FileText className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  const getStatusBadge = (status?: PendingField['status']) => {
    switch (status) {
      case 'pending':
        return (
          <span className="text-micro bg-status-warning/15 text-status-warning px-1.5 py-0.5 rounded-full">
            Aguardando
          </span>
        )
      case 'expired':
        return (
          <span className="text-micro bg-status-error/15 text-status-error px-1.5 py-0.5 rounded-full">
            Expirado
          </span>
        )
      case 'never_requested':
      default:
        return (
          <span className="text-micro bg-gray-100 text-lia-text-tertiary px-1.5 py-0.5 rounded-full">
            Não solicitado
          </span>
        )
    }
  }

  const handleResendRequest = async () => {
    setIsResending(true)
    try {
      onResendRequest()
    } finally {
      setIsResending(false)
    }
  }

  const handleProceedAnyway = async () => {
    setIsProceeding(true)
    try {
      onProceedAnyway()
    } finally {
      setIsProceeding(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-sm rounded-md dark:bg-lia-bg-primary dark:border-lia-border-subtle">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-status-warning dark:text-status-warning">
            <AlertTriangle className="w-5 h-5" />
            Dados Pendentes
          </DialogTitle>
          <DialogDescription className="dark:text-lia-text-tertiary">
            {candidate.name} não possui todos os dados necessários para avançar para {stageDisplay}.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="bg-status-warning/10 dark:bg-status-warning/30 border border-status-warning/30 dark:border-status-warning/30 rounded-md p-3">
            <p className="text-sm text-status-warning dark:text-status-warning" aria-live="polite" aria-atomic="true">
              Esta etapa requer informações adicionais do candidato. 
              Você pode solicitar os dados ou avançar mesmo assim.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-secondary">Campos Pendentes</span>
              <span className="text-xs text-lia-text-tertiary dark:text-lia-text-tertiary">{pendingFields.length} campos</span>
            </div>
            <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md divide-y divide-gray-200 dark:divide-gray-700 max-h-[200px] overflow-y-auto">
              {pendingFields.map((field) => (
                <div
                  key={field.id}
                  className="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <div className="flex items-center gap-3">
                    <div className="text-lia-text-disabled dark:text-lia-text-tertiary">
                      {getFieldIcon(field.id)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">{field.displayName}</p>
                      {field.lastRequestedAt && (
                        <p className="text-xs text-lia-text-tertiary">
                          Solicitado em {new Date(field.lastRequestedAt).toLocaleDateString('pt-BR')}
                        </p>
                      )}
                    </div>
                  </div>
                  {getStatusBadge(field.status)}
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
            <div className="w-10 h-10 bg-gray-200 dark:bg-lia-bg-elevated rounded-full flex items-center justify-center">
              {candidate.avatar ? (
                <NextImage src={candidate.avatar} alt="" width={40} height={40} className="w-10 h-10 rounded-full" />
              ) : (
                <User className="w-5 h-5 text-lia-text-tertiary" />
              )}
            </div>
            <div>
              <p className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary">{candidate.name}</p>
              {candidate.email && (
                <p className="text-xs text-lia-text-tertiary dark:text-lia-text-tertiary">{candidate.email}</p>
              )}
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col gap-2 sm:flex-col border-t border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-primary p-4 -mx-6 -mb-6 rounded-b-xl">
          <Button
            onClick={handleResendRequest}
            disabled={isResending || isProceeding}
            className="w-full h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200"
          >
            {isResending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" />
                Enviando...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Reenviar Solicitação
              </>
            )}
          </Button>
          <Button
            variant="outline"
            onClick={handleProceedAnyway}
            disabled={isResending || isProceeding}
            className="w-full bg-white border border-lia-border-default text-lia-text-secondary hover:bg-gray-50 dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-gray-700 dark:text-lia-text-primary"
          >
            {isProceeding ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" />
                Processando...
              </>
            ) : (
              <>
                <ArrowRight className="w-4 h-4 mr-2" />
                Avançar Mesmo Assim
              </>
            )}
          </Button>
          <Button
            variant="ghost"
            onClick={onClose}
            disabled={isResending || isProceeding}
            className="w-full dark:text-lia-text-secondary dark:hover:bg-gray-800"
          >
            <X className="w-4 h-4 mr-2" />
            Cancelar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
