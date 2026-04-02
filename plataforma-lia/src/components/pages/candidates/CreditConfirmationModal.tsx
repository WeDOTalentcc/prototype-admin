"use client"

import { Zap, Mail, Phone, AlertCircle } from "lucide-react"
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
import { Switch } from "@/components/ui/switch"

interface CreditEstimate {
  total_estimated: number
  breakdown: {
    base: number
    emails: number
    phone_numbers: number
  }
}

interface PearchSearchOptions {
  searchType: string
  limit: number
  requireEmails: boolean
  requirePhoneNumbers: boolean
}

interface CreditConfirmationModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  creditEstimate: CreditEstimate | null
  pearchSearchOptions: PearchSearchOptions
  onSearchOptionsChange: (options: PearchSearchOptions) => void
  onCancel: () => void
  onConfirm: () => void
}

export function CreditConfirmationModal({
  open,
  onOpenChange,
  creditEstimate,
  pearchSearchOptions,
  onSearchOptionsChange,
  onCancel,
  onConfirm,
}: CreditConfirmationModalProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-wedo-cyan/15">
              <Zap className="w-4 h-4 text-lia-text-secondary" />
            </div>
            Confirmar Busca na Base Global
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-4">
            <p className="text-sm text-lia-text-primary">
              Esta busca utilizará créditos da sua conta.
            </p>

            {creditEstimate && (
              <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-md p-4 space-y-3">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-lia-text-primary">Tipo de busca:</span>
                  <span className="font-medium capitalize">{pearchSearchOptions.searchType}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-lia-text-primary">Limite de resultados:</span>
                  <span className="font-medium">{pearchSearchOptions.limit}</span>
                </div>

                {/* Filtros de Otimização de Créditos */}
                <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-3 space-y-2">
                  <span className="text-xs font-medium text-lia-text-tertiary uppercase tracking-wide">Filtros de Contato</span>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-lia-text-tertiary" />
                      <span className="text-sm text-lia-text-primary">Apenas com Email</span>
                      <span className="text-xs text-lia-text-tertiary">(+1 cr)</span>
                    </div>
                    <Switch
                      checked={pearchSearchOptions.requireEmails}
                      onCheckedChange={(checked) => onSearchOptionsChange({ ...pearchSearchOptions, requireEmails: checked })}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-status-success" />
                      <span className="text-sm text-lia-text-primary">Apenas com Telefone</span>
                      <span className="text-xs text-lia-text-tertiary">(+1 cr)</span>
                    </div>
                    <Switch
                      checked={pearchSearchOptions.requirePhoneNumbers}
                      onCheckedChange={(checked) => onSearchOptionsChange({ ...pearchSearchOptions, requirePhoneNumbers: checked })}
                    />
                  </div>
                  {(pearchSearchOptions.requireEmails || pearchSearchOptions.requirePhoneNumbers) && (
                    <p className="text-xs text-status-success dark:text-status-success bg-status-success/10 dark:bg-status-success/20 p-2 rounded-md">
                      Filtrando candidatos com contato disponível - você não gastará créditos com perfis sem dados de contato.
                    </p>
                  )}
                </div>

                <div className="flex justify-between items-center text-sm">
                  <span className="text-lia-text-primary">Custo base:</span>
                  <span className="font-medium">{creditEstimate.breakdown.base} créditos</span>
                </div>
                {creditEstimate.breakdown.emails > 0 && (
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-lia-text-primary">E-mails (+):</span>
                    <span className="font-medium">{creditEstimate.breakdown.emails} créditos</span>
                  </div>
                )}
                {creditEstimate.breakdown.phone_numbers > 0 && (
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-lia-text-primary">Telefones (+):</span>
                    <span className="font-medium">{creditEstimate.breakdown.phone_numbers} créditos</span>
                  </div>
                )}
                <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-2">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Total estimado:</span>
                    <span className="text-base-ui font-semibold text-lia-text-secondary">
                      {creditEstimate.total_estimated} créditos
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center gap-2 text-xs text-status-warning dark:text-status-warning bg-status-warning/10 dark:bg-status-warning/20 p-2 rounded-md">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>O custo final pode variar dependendo dos resultados encontrados.</span>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onCancel}>
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="text-white bg-lia-btn-primary-bg"
          >
            Confirmar Busca
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
