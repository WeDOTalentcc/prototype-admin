"use client"

import React from "react"
import { Brain, Maximize2, Send } from "lucide-react"
import { ThinkingDots } from "@/components/ui/thinking-dots"

export interface CompactLIAPromptProps {
  isLIAThinking: boolean
  liaPromptValue: string
  setLiaPromptValue: (value: string) => void
  setShowExpandedLIA: (value: boolean) => void
  onAICommand: (cmd: string) => void
}

export function CompactLIAPrompt({
  isLIAThinking,
  liaPromptValue,
  setLiaPromptValue,
  setShowExpandedLIA,
  onAICommand,
}: CompactLIAPromptProps) {
  return (
    <div className="flex-1 max-w-panel-sm">
      <div
        className={`relative flex items-center h-10 rounded-md bg-lia-bg-primary transition-colors motion-reduce:transition-none ${
          isLIAThinking ? 'cursor-wait' : ''
        } border border-lia-border-subtle`}
        style={{ paddingLeft: '16px', paddingRight: '80px' }}
      >
        <input
          type="text"
          placeholder={isLIAThinking ? "LIA está pensando..." : "Ex: Analisar candidatos com..."}
          value={liaPromptValue}
          onChange={(e) => setLiaPromptValue(e.target.value)}
          disabled={isLIAThinking}
          className="flex-1 h-full text-base-ui bg-transparent focus:outline-none text-lia-text-primary placeholder:text-lia-text-secondary"
          onFocus={(e) => {
            const container = e.target.parentElement
            if (container) {
              container.style.borderColor = 'var(--gray-200)'
              container.style.boxShadow = '0 0 0 2px var(--wedo-cyan-bg-12)'
            }
            if (!isLIAThinking) {
              setShowExpandedLIA(true)
            }
          }}
          onBlur={(e) => {
            const container = e.target.parentElement
            if (container) {
              container.style.borderColor = 'var(--gray-200)'
              container.style.boxShadow = 'none'
            }
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && liaPromptValue.trim() && !isLIAThinking) {
              onAICommand(liaPromptValue)
              setLiaPromptValue('')
            }
          }}
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          <button
            className="p-1.5 rounded-full hover:bg-gray-100 transition-colors motion-reduce:transition-none"
            onClick={() => setShowExpandedLIA(true)}
            title="Expandir"
            aria-label="Expandir chat da LIA"
          >
            <Maximize2 className="w-4 h-4 text-lia-text-secondary" aria-hidden="true" />
          </button>
          <button
            className={`p-1.5 rounded-full transition-colors motion-reduce:transition-none ${
              isLIAThinking ? 'cursor-wait opacity-50' : 'hover:bg-gray-100'
            }`}
            onClick={() => {
              if (liaPromptValue.trim() && !isLIAThinking) {
                onAICommand(liaPromptValue)
                setLiaPromptValue('')
              }
            }}
            disabled={isLIAThinking}
            title="Enviar"
            aria-label="Enviar mensagem para a LIA"
          >
            {isLIAThinking ? (
              <div className="w-4 h-4 border-2 border-gray-900 dark:border-lia-border-medium border-t-transparent rounded-full animate-spin motion-reduce:animate-none" aria-hidden="true" />
            ) : (
              <Send className="w-4 h-4 text-lia-text-secondary" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      {isLIAThinking && (
        <div className="mt-2 flex items-center gap-2 text-xs px-3 py-1.5 rounded-md animate-fade-in bg-gray-200/30 border border-wedo-cyan/20">
          <Brain className="w-3 h-3 animate-pulse motion-reduce:animate-none text-wedo-cyan" />
          <span className="font-medium text-lia-text-primary">LIA está pensando</span>
          <div className="flex gap-0.5">
            <ThinkingDots dotClassName="bg-gray-600" size="sm" />
          </div>
        </div>
      )}
    </div>
  )
}
