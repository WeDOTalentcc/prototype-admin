"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import {
  X, Lightbulb, Clock, Zap, Archive, Settings,
  Brain, FileText, ChevronRight
} from "lucide-react"

interface TemplateSuggestion {
  id: string
  command: string
  reason: string
  complexity: number
  repetitions: number
  estimatedTime: number
  suggested: boolean
}

interface TemplateSuggestionToastProps {
  suggestion: TemplateSuggestion | null
  onCreateTemplate: (suggestion: TemplateSuggestion) => void
  onDismiss: (suggestionId: string) => void
  onNotAskAgain: () => void
  position?: 'bottom-right' | 'bottom-left' | 'top-right'
}

export function TemplateSuggestionToast({
  suggestion,
  onCreateTemplate,
  onDismiss,
  onNotAskAgain,
  position = 'bottom-right'
}: TemplateSuggestionToastProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [isDismissing, setIsDismissing] = useState(false)

  // Mostrar/ocultar toast baseado na sugestão
  useEffect(() => {
    if (suggestion) {
      setIsVisible(true)
      setIsDismissing(false)

      // Auto-dismiss após 15 segundos
      const timer = setTimeout(() => {
        handleDismiss()
      }, 15000)

      return () => clearTimeout(timer)
    } else {
      setIsVisible(false)
    }
  }, [suggestion])

  // Handler para dismiss com animação
  const handleDismiss = () => {
    if (!suggestion) return

    setIsDismissing(true)
    setTimeout(() => {
      onDismiss(suggestion.id)
      setIsVisible(false)
      setIsDismissing(false)
    }, 300)
  }

  // Handler para criar template
  const handleCreateTemplate = () => {
    if (!suggestion) return

    setIsDismissing(true)
    setTimeout(() => {
      onCreateTemplate(suggestion)
      setIsVisible(false)
      setIsDismissing(false)
    }, 300)
  }

  if (!suggestion || !isVisible) return null

  // Posicionamento dinâmico
  const getPositionClasses = () => {
    switch (position) {
      case 'bottom-left':
        return 'bottom-6 left-6'
      case 'top-right':
        return 'top-6 right-6'
      case 'bottom-right':
      default:
        return 'bottom-6 right-6'
    }
  }

  // Ícone baseado no motivo
  const getReasonIcon = () => {
    if (suggestion.repetitions >= 3) {
      return <Zap className="w-4 h-4 text-wedo-orange" />
    } else if (suggestion.complexity >= 8) {
      return <Brain className="w-4 h-4 text-wedo-cyan" />
    } else {
      return <Lightbulb className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
    }
  }

  // Cor do badge baseado no motivo
  const getBadgeColor = () => {
    if (suggestion.repetitions >= 3) {
      return 'bg-wedo-orange/15 text-wedo-orange border-wedo-orange/30'
    } else if (suggestion.complexity >= 8) {
      return 'bg-wedo-purple/15 text-wedo-purple border-wedo-purple/30'
    } else {
      return 'bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-default dark:border-lia-border-default'
    }
  }

  return (
    <div
      className={`fixed ${getPositionClasses()} z-50 transform transition-colors motion-reduce:transition-none duration-300 ease-in-out ${
        isDismissing ? 'translate-y-full opacity-0' : 'translate-y-0 opacity-100'
      }`}
    >
      <Card className="w-80 border-l-4 border-l-gray-400 dark:border-l-gray-500 bg-white dark:bg-lia-bg-secondary">
        <CardContent className="p-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {getReasonIcon()}
              <span className="font-medium text-lia-text-primary text-sm">
                Sugestão de Template
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDismiss}
              className="h-6 w-6 p-0 lia-text-base hover:lia-text-base"
            >
              <X className="w-3 h-3" />
            </Button>
          </div>

          {/* Motivo */}
          <div className="mb-3">
            <Badge className={`text-xs px-2 py-1 ${getBadgeColor()}`}>
              {suggestion.reason}
            </Badge>
          </div>

          {/* Comando */}
          <div className="mb-3 p-2 bg-gray-50 dark:bg-lia-bg-elevated rounded-md text-xs font-mono text-lia-text-primary dark:text-lia-text-primary line-clamp-2">
            "{suggestion.command}"
          </div>

          {/* Benefícios */}
          <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
            <div className="flex items-center gap-1 text-lia-text-secondary dark:text-lia-text-tertiary">
              <Clock className="w-3 h-3" />
              <span>~{Math.round(suggestion.estimatedTime/60)}min economia</span>
            </div>
            <div className="flex items-center gap-1 text-lia-text-secondary dark:text-lia-text-tertiary">
              <FileText className="w-3 h-3" />
              <span>Complexidade {suggestion.complexity}/10</span>
            </div>
          </div>

          {/* Ações */}
          <div className="space-y-2">
            <Button
              onClick={handleCreateTemplate}
              className="w-full gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200 text-sm h-8"
            >
              <Archive className="w-3 h-3" />
              Criar Template
            </Button>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleDismiss}
                className="flex-1 text-xs h-7"
              >
                Agora Não
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={onNotAskAgain}
                className="flex-1 text-xs h-7 lia-text-strong hover:lia-text-strong"
              >
                Não Perguntar
              </Button>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-3 pt-2 border-t border-lia-border-subtle dark:border-lia-border-default flex items-center justify-between text-xs text-lia-text-primary dark:text-lia-text-primary">
            <span>💡 LIA Intelligence</span>
            <button
              onClick={() => {/* Abrir configurações */}}
              className="hover:lia-text-base transition-colors motion-reduce:transition-none"
            >
              <Settings className="w-3 h-3" />
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Indicador de progresso (auto-dismiss) */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 dark:bg-lia-bg-elevated rounded-b">
        <div
          className="h-full bg-gray-700 rounded-b transition-[width,height] duration-[15000ms] ease-linear"
          style={{width: isVisible ? '0%' : '100%'}}
        />
      </div>
    </div>
  )
}

// Hook para gerenciar múltiplas sugestões
export const useTemplateSuggestionQueue = () => {
  const [suggestionQueue, setSuggestionQueue] = useState<TemplateSuggestion[]>([])
  const [currentSuggestion, setCurrentSuggestion] = useState<TemplateSuggestion | null>(null)

  // Adicionar sugestão à fila
  const addSuggestion = (suggestion: TemplateSuggestion) => {
    setSuggestionQueue(prev => [...prev, suggestion])
  }

  // Processar próxima sugestão da fila
  useEffect(() => {
    if (!currentSuggestion && suggestionQueue.length > 0) {
      setCurrentSuggestion(suggestionQueue[0])
      setSuggestionQueue(prev => prev.slice(1))
    }
  }, [currentSuggestion, suggestionQueue])

  // Limpar sugestão atual
  const clearCurrentSuggestion = () => {
    setCurrentSuggestion(null)
  }

  return {
    currentSuggestion,
    addSuggestion,
    clearCurrentSuggestion,
    queueLength: suggestionQueue.length
  }
}
