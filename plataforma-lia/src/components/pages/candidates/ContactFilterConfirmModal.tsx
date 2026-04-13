"use client"

import { Mail, Phone, CheckCircle } from "lucide-react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

interface ContactFilterConfirmModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  pendingContactFilter: 'email' | 'phone' | null
  onCancel: () => void
  onConfirm: () => void
}

export function ContactFilterConfirmModal({
  open,
  onOpenChange,
  pendingContactFilter,
  onCancel,
  onConfirm,
}: ContactFilterConfirmModalProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent data-testid="contact-filter-modal" className="max-w-md border border-lia-border-subtle dark:border-lia-border-subtle">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-status-success/15">
              {pendingContactFilter === 'email' ? (
                <Mail className="w-4 h-4 text-wedo-green" />
              ) : (
                <Phone className="w-4 h-4 text-wedo-green" />
              )}
            </div>
            {pendingContactFilter === 'email' ? 'Filtrar por Email' : 'Filtrar por Telefone'}
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-4">
            <p className="text-sm text-lia-text-primary">
              {pendingContactFilter === 'email'
                ? 'Ao ativar este filtro, a busca retornará apenas candidatos com email disponível.'
                : 'Ao ativar este filtro, a busca retornará apenas candidatos com telefone disponível.'}
            </p>

            <div className="bg-lia-bg-secondary dark:bg-lia-bg-primary rounded-xl p-4 space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-lia-text-primary">Filtro:</span>
                <span className="font-medium">{pendingContactFilter === 'email' ? 'Apenas com Email' : 'Apenas com Telefone'}</span>
              </div>
              <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium">Enriquecimento via Apify:</span>
                  <span className="font-semibold text-lg text-wedo-green">
                    $0.01/candidato
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-status-success bg-status-success/10 p-2 rounded-md">
              <CheckCircle className="w-4 h-4 flex-shrink-0" />
              <span>Contatos são enriquecidos automaticamente via Apify quando não disponíveis na base.</span>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel data-testid="contact-filter-cancel-btn" onClick={onCancel}>
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction
            data-testid="contact-filter-confirm-btn"
            onClick={onConfirm}
            className="text-white gap-2 bg-wedo-green hover:bg-lia-interactive-hover transition-colors cursor-pointer"
          >
            {pendingContactFilter === 'email' ? (
              <>
                <Mail className="w-4 h-4" />
                Ativar Filtro Email
              </>
            ) : (
              <>
                <Phone className="w-4 h-4" />
                Ativar Filtro Telefone
              </>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
