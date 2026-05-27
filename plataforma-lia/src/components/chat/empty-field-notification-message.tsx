"use client"

import React, { useState } from 'react'
import { Button } from"@/components/ui/button"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { AlertTriangle, Brain, Clock, BellOff, Loader2, CheckCircle, Info } from"lucide-react"
import type { EmptyFieldNotification, FieldValueSuggestion } from"@/hooks/candidates/use-empty-field-notifications"

interface EmptyFieldNotificationMessageProps {
  notification: EmptyFieldNotification
  onAction: (action: string) => Promise<void>
  onSuggestionAccepted?: (fieldKey: string, value: unknown) => void
  onSuggestionRejected?: () => void
  suggestion?: FieldValueSuggestion | null
  isLoadingSuggestion?: boolean
}

export function EmptyFieldNotificationMessage({
  notification,
  onAction,
  onSuggestionAccepted,
  onSuggestionRejected,
  suggestion,
  isLoadingSuggestion
}: EmptyFieldNotificationMessageProps) {
  const [isProcessing, setIsProcessing] = useState<string | null>(null)
  const [showSuggestion, setShowSuggestion] = useState(false)

  const handleActionClick = async (action: string) => {
    setIsProcessing(action)
    try {
      await onAction(action)
      if (action === 'fill_now') {
        setShowSuggestion(true)
      }
    } finally {
      setIsProcessing(null)
    }
  }

  const handleAcceptSuggestion = () => {
    if (suggestion && onSuggestionAccepted) {
      onSuggestionAccepted(notification.field_key, suggestion.suggested_value)
    }
  }

  const handleRejectSuggestion = () => {
    setShowSuggestion(false)
    if (onSuggestionRejected) {
      onSuggestionRejected()
    }
  }

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'company_config': return '🏢'
      case 'job_history': return '📊'
      case 'market_benchmark': return '📈'
      case 'role_inference': return '🤖'
      default: return '💡'
    }
  }

  return (
    <div
      className="w-full animate-in fade-in slide-in-from-bottom-2 duration-200"
    >
      <Card className="border-status-warning/30 bg-status-warning/10/50 dark:border-status-warning/30">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-full bg-status-warning/15 dark:bg-status-warning/50">
              <AlertTriangle className="w-5 h-5 text-status-warning" />
            </div>
            
            <div className="flex-1 space-y-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-foreground">
                    Campo vazio: {notification.field_label}
                  </span>
                  {notification.times_reminded > 0 && (
                    <Chip density="relaxed" variant="neutral" >
                      Lembrete #{notification.times_reminded + 1}
                    </Chip>
                  )}
                </div>
                <p className="text-sm text-lia-text-tertiary">
                  {notification.impact_description}
                </p>
              </div>

              {notification.has_fallback && (
                <div className="flex items-center gap-1 text-xs text-lia-text-tertiary">
                  <Info className="w-3 h-3" />
                  <span>
                    Posso usar dados alternativos: {notification.fallback_strategies.join(', ')}
                  </span>
                </div>
              )}

              <>
                {!showSuggestion ? (
                  <div 
                    className="flex flex-wrap gap-2 animate-in fade-in duration-150"
                  >
                    <Button
                      size="sm"
                      onClick={() => handleActionClick('fill_now')}
                      disabled={isProcessing !== null}
                      className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                    >
                      {isProcessing === 'fill_now' ? (
                        <Loader2 className="w-4 h-4 mr-1 animate-spin motion-reduce:animate-none" />
                      ) : (
                        <Brain className="w-4 h-4 mr-1 text-wedo-cyan" />
                      )}
                      Preencher Agora
                    </Button>
                    
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleActionClick('remind_later')}
                      disabled={isProcessing !== null}
                    >
                      {isProcessing === 'remind_later' ? (
                        <Loader2 className="w-4 h-4 mr-1 animate-spin motion-reduce:animate-none" />
                      ) : (
                        <Clock className="w-4 h-4 mr-1" />
                      )}
                      Lembrar Depois
                    </Button>
                    
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleActionClick('dont_remind')}
                      disabled={isProcessing !== null}
                      className="text-lia-text-tertiary"
                    >
                      {isProcessing === 'dont_remind' ? (
                        <Loader2 className="w-4 h-4 mr-1 animate-spin motion-reduce:animate-none" />
                      ) : (
                        <BellOff className="w-4 h-4 mr-1" />
                      )}
                      Não Lembrar
                    </Button>
                  </div>
                ) : (
                  <div
                    className="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-150"
                  >
                    {isLoadingSuggestion ? (
                      <div className="flex items-center gap-2 text-sm text-lia-text-tertiary" role="status" aria-live="polite" aria-label="Carregando...">
                        <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                        <span>Buscando sugestão...</span>
                      </div>
                    ) : suggestion ? (
                      <Card className="border-lia-border-default bg-lia-bg-secondary">
                        <CardContent className="p-3 space-y-2">
                          <div className="flex items-center gap-2">
                            <span className="text-lg">{getSourceIcon(suggestion.source)}</span>
                            <span className="text-sm font-medium">Sugestão da IA</span>
                            <Chip density="relaxed" variant="neutral" muted >
                              {Math.round(suggestion.confidence * 100)}% confiança
                            </Chip>
                          </div>
                          
                          <div className="p-2 bg-lia-bg-primary rounded-md border">
                            <p className="font-mono text-sm">{suggestion.formatted_value}</p>
                          </div>
                          
                          <p className="text-xs text-lia-text-tertiary">
                            {suggestion.source_explanation}
                          </p>
                          
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              onClick={handleAcceptSuggestion}
                              className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                            >
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Usar Sugestão
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={handleRejectSuggestion}
                            >
                              Descartar
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ) : (
                      <div className="space-y-2">
                        <p className="text-sm text-lia-text-tertiary">
                          Não foi possível gerar uma sugestão para este campo.
                        </p>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleRejectSuggestion}
                        >
                          Continuar sem preencher
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
