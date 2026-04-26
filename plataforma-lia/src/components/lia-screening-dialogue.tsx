"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import {
  X, Brain, Settings, Send, Loader2
} from "lucide-react"
import { useLiaScreeningDialogue, type ScreeningData } from "@/hooks/ai/use-lia-screening-dialogue"
import { LiaScreeningRightPanel } from "./LiaScreeningRightPanel"

interface JobData {
  title?: string
  department?: string
  seniority?: string
  description?: string
  [key: string]: unknown
}

interface LiaScreeningDialogueProps {
  isOpen: boolean
  onClose: () => void
  jobData: JobData
  onComplete: (screeningData: ScreeningData) => void
}

export function LiaScreeningDialogue({ isOpen, onClose, jobData, onComplete }: LiaScreeningDialogueProps) {
  const {
    messages,
    currentInput,
    setCurrentInput,
    isLiaTyping,
    currentStep,
    screeningData,
    showCompanySettings,
    setShowCompanySettings,
    messagesEndRef,
    inputRef,
    handleSendMessage,
    handleOptionSelect,
  } = useLiaScreeningDialogue(isOpen, jobData, onComplete)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl w-full max-w-7xl h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 bg-status-success/10 dark:bg-status-success/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-status-success rounded-md flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold font-sans text-lia-text-primary">
                Construção de Roteiro de Triagem
              </h3>
              <p className="text-sm text-lia-text-primary">
                {jobData?.title} • Criando roteiro personalizado
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowCompanySettings(true)}>
              <Settings className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 flex flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[80%] ${
 message.sender === 'user'
                      ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text rounded-l-2xl rounded-tr-2xl'
                      : 'bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary rounded-r-2xl rounded-tl-2xl'
                  } p-3`}>
                    <div className="text-sm whitespace-pre-line">{message.content}</div>

                    {message.type === 'options' && message.options && (
                      <div className="mt-3 space-y-2">
                        {message.options.map((option, index) => (
                          <button
                            key={`opt-${index}`}
                            onClick={() => handleOptionSelect(option)}
                            className="block w-full text-left p-2 bg-lia-bg-primary bg-opacity-20 hover:bg-opacity-30 rounded-xl text-sm transition-colors motion-reduce:transition-none"
                          >
                            {option}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLiaTyping && (
                <div className="flex justify-start" role="status" aria-live="polite" aria-label="Carregando...">
                  <div className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-r-2xl rounded-tl-2xl p-3" role="status" aria-live="polite" aria-label="Carregando...">
                    <div className="flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-status-success" />
                      <span className="text-sm text-lia-text-secondary">Analisando...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="p-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
              <div className="flex items-center gap-3">
                <div className="flex-1 relative">
                  <input
                    ref={inputRef}
                    type="text"
                    value={currentInput}
                    onChange={(e) => setCurrentInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Digite sua resposta..."
                    className="w-full p-3 pr-12 rounded-xl focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary"
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={!currentInput.trim() || isLiaTyping}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          <div className="w-96 bg-lia-bg-secondary dark:bg-lia-bg-secondary p-4 overflow-y-auto">
            <div className="mb-4">
              <h4 className="font-medium font-sans text-lia-text-primary mb-2">
                {currentStep === 'overview' && '📋 Configurando Visão Geral'}
                {currentStep === 'approach' && '🗣️ Definindo Abordagem'}
                {currentStep === 'questions' && '❓ Criando Perguntas'}
                {currentStep === 'presentation' && '⭐ Preparando Apresentação'}
                {currentStep === 'feedback' && '💌 Estratégia de Feedback'}
                {currentStep === 'timeline' && '⏰ Timeline de Execução'}
                {currentStep === 'review' && '✅ Roteiro Finalizado'}
              </h4>
              <div className="text-xs text-lia-text-secondary">
                Etapa {['overview', 'approach', 'questions', 'presentation', 'feedback', 'timeline', 'review'].indexOf(currentStep) + 1} de 7
              </div>
            </div>
            <LiaScreeningRightPanel
              currentStep={currentStep}
              screeningData={screeningData}
              jobData={jobData}
            />
          </div>
        </div>
      </div>

      {showCompanySettings && (
        <div className="fixed inset-0 bg-black bg-opacity-75 z-60 flex items-center justify-center p-4">
          <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-4 border-b">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Configurações da Empresa</h4>
                <Button variant="ghost" size="sm" onClick={() => setShowCompanySettings(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <div className="p-4">
              <div className="space-y-4 text-sm">
                <div className="p-3 border rounded-xl">
                  <div className="font-medium">Template Padrão</div>
                  <div className="text-xs text-lia-text-secondary mt-1">Duração: 25-30 min • Foco: Técnico + Cultural</div>
                </div>
                <div className="p-3 border rounded-xl">
                  <div className="font-medium">Abordagem</div>
                  <div className="text-xs text-lia-text-secondary mt-1">Tom: Profissional, mas acolhedor</div>
                </div>
                <div className="p-3 border rounded-xl">
                  <div className="font-medium">Feedback</div>
                  <div className="text-xs text-lia-text-secondary mt-1">Aprovados: 24h • Reprovados: 48h</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
