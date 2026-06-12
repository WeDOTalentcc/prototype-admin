"use client"

import React from "react"
import { Maximize2, X } from "lucide-react"

interface WizardFullscreenPromptCardProps {
  onAccept: () => void
  onDecline: () => void
}

export function WizardFullscreenPromptCard({ onAccept, onDecline }: WizardFullscreenPromptCardProps) {
  return (
    <div className="mx-3 mb-2 rounded-xl border border-wedo-cyan/30 bg-wedo-cyan/5 p-3 flex items-start gap-3">
      <Maximize2 className="w-4 h-4 text-wedo-cyan flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-lia-text-primary font-medium">Abrir em tela cheia?</p>
        <p className="text-xs text-lia-text-secondary mt-0.5">
          O painel lateral com detalhes da vaga fica disponível em tela cheia.
        </p>
        <div className="flex gap-2 mt-2.5">
          <button
            type="button"
            onClick={onAccept}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-wedo-cyan text-white font-medium hover:bg-wedo-cyan/90 transition-colors"
          >
            <Maximize2 className="w-3 h-3" />
            Ir para tela cheia
          </button>
          <button
            type="button"
            onClick={onDecline}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors"
          >
            Continuar aqui
          </button>
        </div>
      </div>
      <button
        type="button"
        onClick={onDecline}
        aria-label="Dispensar"
        className="text-lia-text-disabled hover:text-lia-text-secondary transition-colors flex-shrink-0"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}
