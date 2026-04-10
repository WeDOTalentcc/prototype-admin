"use client"

import React, { useState, useEffect } from "react"
import { Lightbulb, X } from "lucide-react"
import type { WizardStage } from "./wizard-types"

/**
 * ProgressiveDisclosure — "Você sabia?" chips that appear AFTER interactions.
 *
 * Shows contextual tips based on current wizard stage.
 * Each tip shown only once per user (localStorage).
 * Dismissible with X button.
 */

const TIPS_BY_STAGE: Record<string, string[]> = {
  jd_enrichment: [
    "Voce pode arrastar um PDF de JD direto no chat para comecar.",
    "A IA verifica automaticamente bias e linguagem inclusiva no JD.",
  ],
  wsi_questions: [
    "Voce pode editar cada pergunta individualmente clicando em 'Editar'.",
    "Perguntas sao calibradas por Bloom (profundidade) e Dreyfus (maturidade).",
    "Use 'Regenerar' para gerar uma nova versao de qualquer pergunta.",
  ],
  competency: [
    "Modo Compacto (7 perguntas) e ideal para triagens rapidas.",
    "Modo Completo (12 perguntas) oferece avaliacao mais profunda.",
  ],
  calibration: [
    "Calibre pelo menos 3 perfis para garantir um threshold confiavel.",
    "O match score combina skills tecnicas e competencias comportamentais.",
  ],
  publish: [
    "Apos publicar, o screening automatico comeca imediatamente.",
    "Voce pode compartilhar o link da vaga por email ou WhatsApp.",
  ],
  eligibility: [
    "Perguntas eliminatorias descartam candidatos que nao atendem requisitos minimos.",
  ],
  salary: [
    "Use os sliders para ajustar a faixa salarial antes de publicar.",
  ],
}

const STORAGE_KEY = "lia-wizard-seen-tips"

function getSeenTips(): Set<string> {
  if (typeof window === "undefined") return new Set()
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? new Set(JSON.parse(stored)) : new Set()
  } catch {
    return new Set()
  }
}

function markTipSeen(tipId: string): void {
  if (typeof window === "undefined") return
  try {
    const seen = getSeenTips()
    seen.add(tipId)
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...seen]))
  } catch { /* ignore */ }
}

interface Props {
  currentStage: WizardStage | null
  interactionCount: number
}

export function ProgressiveDisclosure({ currentStage, interactionCount }: Props) {
  const [currentTip, setCurrentTip] = useState<{ id: string; text: string } | null>(null)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    if (!currentStage || interactionCount < 1 || dismissed) {
      setCurrentTip(null)
      return
    }

    const tips = TIPS_BY_STAGE[currentStage] || []
    const seen = getSeenTips()

    // Find first unseen tip for current stage
    for (let i = 0; i < tips.length; i++) {
      const id = `${currentStage}_${i}`
      if (!seen.has(id)) {
        setCurrentTip({ id, text: tips[i] })
        return
      }
    }

    setCurrentTip(null)
  }, [currentStage, interactionCount, dismissed])

  if (!currentTip) return null

  const dismissTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null)

  // Cleanup timer on unmount
  React.useEffect(() => {
    return () => {
      if (dismissTimerRef.current) clearTimeout(dismissTimerRef.current)
    }
  }, [])

  const handleDismiss = () => {
    markTipSeen(currentTip.id)
    setDismissed(true)
    if (dismissTimerRef.current) clearTimeout(dismissTimerRef.current)
    dismissTimerRef.current = setTimeout(() => setDismissed(false), 5000)
  }

  return (
    <div className="mx-4 mb-2 flex items-start gap-2 px-3 py-2 rounded-lg bg-wedo-cyan/5 border border-wedo-cyan/15 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <Lightbulb className="w-3.5 h-3.5 text-wedo-cyan flex-shrink-0 mt-0.5" />
      <p className="flex-1 text-xs text-lia-text-secondary font-['Open_Sans',sans-serif] leading-relaxed">
        <span className="font-medium text-wedo-cyan">Voce sabia? </span>
        {currentTip.text}
      </p>
      <button
        onClick={handleDismiss}
        className="p-0.5 rounded text-lia-text-disabled hover:text-lia-text-secondary flex-shrink-0"
      >
        <X className="w-3 h-3" />
      </button>
    </div>
  )
}
