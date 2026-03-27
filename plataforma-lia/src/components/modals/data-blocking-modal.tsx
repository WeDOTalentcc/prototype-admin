"use client"

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
          <span className="text-micro bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded-full">
            Aguardando
          </span>
        )
      case 'expired':
        return (
          <span className="text-micro bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full">
            Expirado
          </span>
        )
      case 'never_requested':
      default:
        return (
          <span className="text-micro bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">
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
      <DialogContent className="max-w-sm rounded-md dark:bg-gray-900 dark:border-gray-700">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
            <AlertTriangle className="w-5 h-5" />
            Dados Pendentes
          </DialogTitle>
          <DialogDescription className="dark:text-gray-400">
            {candidate.name} não possui todos os dados necessários para avançar para {stageDisplay}.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3">
            <p className="text-sm text-amber-800 dark:text-amber-300">
              Esta etapa requer informações adicionais do candidato. 
              Você pode solicitar os dados ou avançar mesmo assim.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Campos Pendentes</span>
              <span className="text-xs text-gray-500 dark:text-gray-400">{pendingFields.length} campos</span>
            </div>
            <div className="border border-gray-200 dark:border-gray-700 rounded-md divide-y divide-gray-200 dark:divide-gray-700 max-h-[200px] overflow-y-auto">
              {pendingFields.map((field) => (
                <div
                  key={field.id}
                  className="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <div className="flex items-center gap-3">
                    <div className="text-gray-400 dark:text-gray-500">
                      {getFieldIcon(field.id)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{field.displayName}</p>
                      {field.lastRequestedAt && (
                        <p className="text-xs text-gray-500">
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

          <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
            <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">
              {candidate.avatar ? (
                <img src={candidate.avatar} alt="" className="w-10 h-10 rounded-full" />
              ) : (
                <User className="w-5 h-5 text-gray-500" />
              )}
            </div>
            <div>
              <p className="font-medium text-sm text-gray-900 dark:text-gray-100">{candidate.name}</p>
              {candidate.email && (
                <p className="text-xs text-gray-500 dark:text-gray-400">{candidate.email}</p>
              )}
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col gap-2 sm:flex-col border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4 -mx-6 -mb-6 rounded-b-xl">
          <Button
            onClick={handleResendRequest}
            disabled={isResending || isProceeding}
            className="w-full h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
          >
            {isResending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
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
            className="w-full bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 dark:text-gray-200"
          >
            {isProceeding ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
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
            className="w-full dark:text-gray-300 dark:hover:bg-gray-800"
          >
            <X className="w-4 h-4 mr-2" />
            Cancelar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
