"use client"

import React from "react"
import { Shield, X } from "lucide-react"

interface Props {
  isOpen: boolean
  fileName: string
  onConfirm: () => void
  onCancel: () => void
}

/**
 * LgpdConsentDialog — C.3 LGPD compliance.
 *
 * Shown before processing CVs to ensure candidate data consent.
 * Required by LGPD Art. 7 (legal basis for data processing).
 * Design follows lia-* token system.
 */
export function LgpdConsentDialog({ isOpen, fileName, onConfirm, onCancel }: Props) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle w-[400px] max-w-[90vw] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5">
          <div className="flex items-center gap-2">
            <Shield className="w-4.5 h-4.5 text-wedo-cyan" />
            <h3 className="text-sm font-semibold text-lia-text-primary font-['Open_Sans',sans-serif]">
              Consentimento LGPD
            </h3>
          </div>
          <button
            onClick={onCancel}
            className="p-1 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="px-5 py-4 space-y-3">
          <p className="text-sm text-lia-text-primary font-['Open_Sans',sans-serif] leading-relaxed">
            O arquivo <strong>{fileName}</strong> foi identificado como curriculo.
          </p>
          <p className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif] leading-relaxed">
            De acordo com a LGPD (Lei 13.709/2018), o processamento de dados pessoais
            de candidatos requer base legal. Ao prosseguir, voce confirma que:
          </p>
          <ul className="space-y-1.5 ml-4">
            <li className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif] list-disc">
              O candidato autorizou o uso do curriculo para esta vaga
            </li>
            <li className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif] list-disc">
              Os dados serao usados exclusivamente para triagem
            </li>
            <li className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif] list-disc">
              O candidato pode solicitar exclusao a qualquer momento
            </li>
          </ul>

          <div className="p-2.5 rounded-xl bg-wedo-cyan/5 border border-wedo-cyan/20">
            <p className="text-[10px] text-wedo-cyan font-['Open_Sans',sans-serif]">
              Os dados serao processados pela IA para triagem e descartados apos o periodo
              de retencao configurado nas politicas da empresa.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center gap-2 px-5 py-3 border-t border-lia-border-subtle">
          <button
            onClick={onCancel}
            className="flex-1 px-3 py-2 rounded-xl border border-lia-border-subtle text-sm font-medium text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none font-['Open_Sans',sans-serif]"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-3 py-2 rounded-md bg-wedo-cyan text-white text-sm font-medium hover:bg-wedo-cyan/90 transition-colors motion-reduce:transition-none font-['Open_Sans',sans-serif]"
          >
            Confirmar e processar
          </button>
        </div>
      </div>
    </div>
  )
}
