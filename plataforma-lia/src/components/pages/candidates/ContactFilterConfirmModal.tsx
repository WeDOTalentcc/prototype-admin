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
      <AlertDialogContent className="max-w-md border border-gray-100 dark:border-gray-700">
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
            <p className="text-sm text-gray-800 dark:text-gray-200">
              {pendingContactFilter === 'email'
                ? 'Ao ativar este filtro, a busca retornará apenas candidatos com email disponível.'
                : 'Ao ativar este filtro, a busca retornará apenas candidatos com telefone disponível.'}
            </p>

            <div className="bg-gray-50 dark:bg-gray-900 rounded-md p-4 space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-800 dark:text-gray-200">Filtro:</span>
                <span className="font-medium">{pendingContactFilter === 'email' ? 'Apenas com Email' : 'Apenas com Telefone'}</span>
              </div>
              <div className="border-t border-gray-200 dark:border-gray-700 pt-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium">Custo adicional:</span>
                  <span className="font-bold text-lg text-wedo-green">
                    +1 crédito/cand
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-status-success bg-status-success/10 p-2 rounded-md">
              <CheckCircle className="w-4 h-4 flex-shrink-0" />
              <span>Você não gastará créditos com perfis sem dados de contato disponíveis.</span>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onCancel}>
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="text-white gap-2 bg-wedo-green"
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
