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
        className="sm:max-w-[320px] w-[85vw] fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 p-4"
        style={{backgroundColor: 'var(--gray-50)',
          borderRadius: '10px'}}
      >
        <div className="space-y-3">
          <div className="flex items-center gap-2.5">
            <div 
              className="w-8 h-8 rounded-full flex items-center justify-center bg-wedo-cyan/15"
            >
              <Coins className="w-4 h-4 lia-text-700" />
            </div>
            <div>
              <AlertDialogTitle 
                className="text-base-ui font-semibold lia-text-950 dark:lia-text-50"
              >
                Confirmar Busca Global
              </AlertDialogTitle>
              <div 
                className="text-micro lia-text-500"
              >
                Esta busca irá consultar a Busca Global com 800M+ perfis
              </div>
            </div>
          </div>

          <div 
            className="rounded-md p-3 border border-lia-border-subtle bg-gray-50"
          >
            <div
              className="text-xs mb-2.5 font-medium lia-text-600"
            >
              {searchTypeTexts[searchType]}
            </div>
            
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="lia-text-500">Limite:</span>
                <span className="font-medium lia-text-950 dark:lia-text-50">
                  {candidateLimit} candidatos
                </span>
              </div>
              
              <div className="flex justify-between items-center text-xs">
                <span className="lia-text-500">Custo por candidato:</span>
                <span className="font-medium lia-text-950 dark:lia-text-50">
                  {creditPerCandidate} crédito
                </span>
              </div>
              
              <div 
                className="flex justify-between items-center pt-2 border-t text-xs border border-lia-border-subtle"
              >
                <span className="font-medium lia-text-700">
                  Total estimado:
                </span>
                <span 
                  className="font-semibold lia-text-700"
                >
                  {totalCredits} créditos
                </span>
              </div>
            </div>
          </div>

          <div 
            className="text-micro text-center lia-text-400"
          >
            Créditos serão consumidos ao executar a busca
          </div>
        </div>

        <AlertDialogFooter className="flex flex-row justify-end gap-2.5 sm:justify-end pt-3">
          <AlertDialogCancel
            disabled={isLoading}
            className="mt-0 h-8 text-xs px-4 font-medium lia-text-600" style={{backgroundColor: 'transparent', borderRadius: '6px'}}
          >
            Cancelar
          </AlertDialogCancel>
          
          <Button
            onClick={onConfirm}
            disabled={isLoading}
            className="text-white h-8 text-xs px-4 bg-gray-900 hover:bg-gray-800 disabled:bg-gray-400 font-medium"
            style={{borderRadius: '6px'}}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
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
