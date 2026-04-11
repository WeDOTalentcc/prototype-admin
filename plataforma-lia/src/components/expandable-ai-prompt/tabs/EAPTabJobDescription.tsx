"use client"

import React from 'react'
import { Brain, Lightbulb } from "lucide-react"
import { useExpandableAIPromptCore } from "../useExpandableAIPromptCore"

type EAPTabJobDescriptionProps = Pick<
  ReturnType<typeof useExpandableAIPromptCore>,
  'jobDescriptionText' | 'setJobDescriptionText' | 'onCommand'
>

export const EAPTabJobDescription = React.memo(function EAPTabJobDescription(props: EAPTabJobDescriptionProps) {
  const { jobDescriptionText, setJobDescriptionText, onCommand } = props

  return (
    <div className="space-y-3">
      <p className="text-xs text-lia-text-primary" aria-live="polite" aria-atomic="true">
        Cole a descrição da vaga para extrair requisitos automaticamente
      </p>
      <textarea
        value={jobDescriptionText}
        onChange={(e) => setJobDescriptionText(e.target.value)}
        placeholder="Cole aqui a descrição completa da vaga..."
        className="border border-input bg-lia-bg-primary rounded-lg text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring w-full px-4 py-2.5 text-sm resize-none"
        rows={3}
      />
      {/* Dica contextual */}
      <div className="p-2.5 rounded-xl bg-white border border-lia-border-subtle">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
          <p className="text-xs text-lia-text-secondary">
            <strong>Dica:</strong> Cole a descrição do cargo completa para extrair automaticamente requisitos técnicos e comportamentais.
          </p>
        </div>
      </div>
      <div className="flex justify-end">
        <button
          className="px-3 py-1.5 lia-btn-primary text-xs disabled:opacity-50 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
          onClick={() => jobDescriptionText.trim() && onCommand(jobDescriptionText, 'extract_from_jd')}
          disabled={!jobDescriptionText.trim()}
        >
          <Brain className="w-3 h-3 inline mr-1 text-wedo-cyan" />
          Extrair Requisitos
        </button>
      </div>
    </div>
  )
})
EAPTabJobDescription.displayName = 'EAPTabJobDescription'
