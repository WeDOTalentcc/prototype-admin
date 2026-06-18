"use client"

import * as React from "react"
import { Coins, Loader2 } from "lucide-react"
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'

export interface CreditConfirmationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
  candidateLimit: number
  creditPerCandidate?: number
  searchType?: 'calibration' | 'sourcing' | 'general'
  isLoading?: boolean
}

const searchTypeTexts: Record<string, string> = {
  calibration: "Buscar candidatos para calibração de perfil",
  sourcing: "Buscar candidatos para triagem da vaga",
  general: "Buscar candidatos na base global"
}

export function CreditConfirmationDialog({
  useLiaModalTracking('credit-confirmation-dialog', open)
  open,
  onOpenChange,
  onConfirm,
  candidateLimit,
  creditPerCandidate = 1,
  searchType = 'general',
  isLoading = false
}: CreditConfirmationDialogProps) {
  const totalCredits = candidateLimit * creditPerCandidate

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent 
        className="sm:max-w-[320px] w-[85vw] fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 p-4 bg-lia-bg-secondary rounded-[10px]"
      >
        <div className="space-y-3">
          <div className="flex items-center gap-2.5">
            <div 
              className="w-8 h-8 rounded-full flex items-center justify-center bg-wedo-cyan/15"
            >
              <Coins className="w-4 h-4 text-lia-text-primary" />
            </div>
            <div>
              <AlertDialogTitle 
                className="text-base-ui font-semibold text-lia-text-primary"
              >
                Confirmar Busca Global
              </AlertDialogTitle>
              <div 
                className="text-micro text-lia-text-secondary"
              >
                Esta busca irá consultar a Busca Global com 800M+ perfis
              </div>
            </div>
          </div>

          <div 
            className="rounded-xl p-3 border border-lia-border-subtle bg-lia-bg-secondary"
          >
            <div
              className="text-xs mb-2.5 font-medium text-lia-text-secondary"
            >
              {searchTypeTexts[searchType]}
            </div>
            
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-lia-text-secondary">Limite:</span>
                <span className="font-medium text-lia-text-primary" aria-live="polite" aria-atomic="true">
                  {candidateLimit} candidatos
                </span>
              </div>
              
              <div className="flex justify-between items-center text-xs">
                <span className="text-lia-text-secondary" aria-live="polite" aria-atomic="true">Custo por candidato:</span>
                <span className="font-medium text-lia-text-primary">
                  {creditPerCandidate} crédito
                </span>
              </div>
              
              <div 
                className="flex justify-between items-center pt-2 border-t text-xs border border-lia-border-subtle"
              >
                <span className="font-medium text-lia-text-primary">
                  Total estimado:
                </span>
                <span 
                  className="font-semibold text-lia-text-primary"
                >
                  {totalCredits} créditos
                </span>
              </div>
            </div>
          </div>

          <div 
            className="text-micro text-center text-lia-text-tertiary"
          >
            Créditos + enriquecimento Apify ($0.01/cand) serão aplicados ao executar a busca
          </div>
        </div>

        <AlertDialogFooter className="flex flex-row justify-end gap-2.5 sm:justify-end pt-3">
          <AlertDialogCancel
            disabled={isLoading}
            className="mt-0 h-8 text-xs px-4 font-medium text-lia-text-secondary"
          >
            Cancelar
          </AlertDialogCancel>
          
          <Button
            onClick={onConfirm}
            disabled={isLoading}
            className="text-white h-8 text-xs px-4 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover disabled:bg-lia-border-medium font-medium"
           
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin motion-reduce:animate-none" />
                Buscando...
              </>
            ) : (
              'Confirmar'
            )}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export default CreditConfirmationDialog
