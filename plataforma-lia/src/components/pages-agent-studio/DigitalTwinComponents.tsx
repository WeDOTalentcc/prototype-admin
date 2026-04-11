"use client"

import React, { useState, useEffect } from"react"
import {
  Brain, Upload, Plus, Star, Users, Activity,
  ThumbsUp, ThumbsDown, HelpCircle, ChevronRight, X
} from"lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Badge } from"@/components/ui/badge"
import { Button } from"@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from"@/components/ui/dialog"
import { Avatar, AvatarFallback } from"@/components/ui/avatar"
import { Progress } from"@/components/ui/progress"
import {
  textStyles, cardStyles, badgeStyles, buttonStyles
} from"@/lib/design-tokens"

// ---------- Types ----------

interface DigitalTwin {
  id: string
  twin_name: string
  specialties: string[]
  description: string | null
  decision_count: number
  accuracy_pct: number | null
  is_active: boolean
  created_at: string
}

interface TwinEvaluation {
  twin_id: string
  twin_name: string
  score: number
  decision:"approved" |"rejected" |"maybe"
  reasoning: string
  confidence: number
  supporting_examples: Array<{
    decision: string
    reasoning: string
    similarity: number
  }>
}

// ---------- Twin Card (for Agent Studio page or settings) ----------

interface TwinCardProps {
  twin: DigitalTwin
  onEvaluate?: (twinId: string) => void
  onManageTwin?: (twinId: string) => void
}

export function TwinCard({ twin, onEvaluate, onManageTwin }: TwinCardProps) {
  const initials = twin.twin_name.split("").map(w => w[0]).join("").slice(0, 2).toUpperCase()

  return (
    <Card className={cardStyles.default}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <Avatar className="w-10 h-10 bg-purple-100">
            <AvatarFallback className="bg-purple-100 text-purple-700 text-sm font-medium">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className={textStyles.subtitle}>{twin.twin_name}</p>
              <Badge className={twin.is_active ? badgeStyles.success : badgeStyles.warning}>
                {twin.is_active ?"Ativo" :"Inativo"}
              </Badge>
            </div>
            {twin.specialties.length > 0 && (
              <div className="flex gap-1 mt-1 flex-wrap">
                {twin.specialties.slice(0, 4).map(s => (
                  <Badge key={s} className="bg-purple-50 text-purple-700 text-xs">{s}</Badge>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 mt-3 text-sm text-lia-text-secondary">
          <span title="Decisões indexadas">
            <Brain className="w-3.5 h-3.5 inline mr-1" />{twin.decision_count}
          </span>
          {twin.accuracy_pct != null && (
            <span title="Precisão">
              <Star className="w-3.5 h-3.5 inline mr-1" />{twin.accuracy_pct}%
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 mt-3 pt-3 border-t border-lia-border-subtle">
          {onEvaluate && (
            <Button className={buttonStyles.primary} onClick={() => onEvaluate(twin.id)}>
              Avaliar candidato
            </Button>
          )}
          {onManageTwin && (
            <Button className={buttonStyles.outline} onClick={() => onManageTwin(twin.id)}>
              Gerenciar <ChevronRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// ---------- Evaluate With Twin Modal ----------

interface EvaluateWithTwinModalProps {
  twinId: string
  candidateProfile: Record<string, unknown>
  jobContext: Record<string, unknown>
  isOpen: boolean
  onClose: () => void
}

// Using Record<string, unknown> directly — no type alias needed

export function EvaluateWithTwinModal({
  twinId, candidateProfile, jobContext, isOpen, onClose,
}: EvaluateWithTwinModalProps) {
  const [evaluation, setEvaluation] = useState<TwinEvaluation | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (isOpen && twinId) runEvaluation()
  }, [isOpen, twinId])

  const runEvaluation = async () => {
    setIsLoading(true)
    try {
      const res = await fetch(`/api/backend-proxy/digital-twins/${twinId}/evaluate`, {
        method:"POST",
        headers: {"Content-Type":"application/json" },
        body: JSON.stringify({
          candidate_profile: candidateProfile,
          job_context: jobContext,
          k: 5,
        }),
      })
      const data = await res.json()
      setEvaluation(data)
    } catch (err) {
      console.error("Twin evaluation failed:", err)
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  const decisionConfig = {
    approved: { icon: ThumbsUp, color:"text-green-600", bg:"bg-green-50", label:"Aprovado" },
    rejected: { icon: ThumbsDown, color:"text-red-600", bg:"bg-red-50", label:"Rejeitado" },
    maybe: { icon: HelpCircle, color:"text-yellow-600", bg:"bg-yellow-50", label:"Talvez" },
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className={textStyles.h3}>
            <Brain className="w-5 h-5 inline mr-2 text-purple-600" />
            Avaliação Digital Twin
          </DialogTitle>
          <DialogDescription className="sr-only">Resultado da avaliação do candidato pelo Digital Twin</DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex flex-col items-center py-8">
            <Brain className="w-10 h-10 text-purple-300 animate-pulse mb-3" />
            <p className={textStyles.body}>Analisando com base no histórico do especialista...</p>
            <p className={textStyles.caption}>Buscando decisões similares e gerando avaliação</p>
          </div>
        ) : evaluation ? (
          <div className="space-y-4 py-4">
            {/* Twin identity */}
            <div className="flex items-center gap-2">
              <Avatar className="w-8 h-8 bg-purple-100">
                <AvatarFallback className="bg-purple-100 text-purple-700 text-xs">
                  {evaluation.twin_name.split("").map(w => w[0]).join("").slice(0, 2)}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className={textStyles.subtitle}>{evaluation.twin_name}</p>
                <p className={textStyles.caption}>Digital Twin</p>
              </div>
            </div>

            {/* Score + Decision */}
            {(() => {
              const dc = decisionConfig[evaluation.decision] || decisionConfig.maybe
              const Icon = dc.icon
              return (
                <div className={`flex items-center justify-between p-4 rounded-lg ${dc.bg}`}>
                  <div className="flex items-center gap-3">
                    <Icon className={`w-6 h-6 ${dc.color}`} />
                    <div>
                      <p className={`${textStyles.h4} ${dc.color}`}>{dc.label}</p>
                      <p className={textStyles.caption}>Decisão do Twin</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`${textStyles.metricLarge} ${dc.color}`}>{evaluation.score}</p>
                    <p className={textStyles.caption}>/100</p>
                  </div>
                </div>
              )
            })()}

            {/* Confidence */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className={textStyles.label}>Confiança</span>
                <span className={textStyles.caption}>{(evaluation.confidence * 100).toFixed(0)}%</span>
              </div>
              <Progress value={evaluation.confidence * 100} className="h-1.5" />
            </div>

            {/* Reasoning (in first person, SME style) */}
            <div>
              <p className={textStyles.label}>Raciocínio</p>
              <blockquote className="mt-1 border-l-2 border-purple-300 pl-3 italic text-lia-text-secondary">"{evaluation.reasoning}"
              </blockquote>
            </div>

            {/* Supporting examples */}
            {evaluation.supporting_examples.length > 0 && (
              <div>
                <p className={`${textStyles.label} mb-2`}>Decisões que embasaram</p>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {evaluation.supporting_examples.map((ex, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm">
                      <Badge className={ex.decision ==="approved" ? badgeStyles.success : badgeStyles.error}>
                        {ex.decision ==="approved" ?"✅" :"❌"}
                      </Badge>
                      <div className="min-w-0">
                        <p className={textStyles.bodySmall}>{ex.reasoning}</p>
                        <p className={textStyles.caption}>Similaridade: {(ex.similarity * 100).toFixed(0)}%</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center py-8">
            <p className={textStyles.body}>Erro ao avaliar. Tente novamente.</p>
          </div>
        )}

        <DialogFooter>
          <Button className={buttonStyles.secondary} onClick={onClose}>Fechar</Button>
          {evaluation && (
            <Button className={buttonStyles.outline} onClick={runEvaluation}>
              Reavaliar
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ---------- Twins List (for Agent Studio page) ----------

interface TwinsListProps {
  onEvaluate?: (twinId: string) => void
}

export function TwinsList({ onEvaluate }: TwinsListProps) {
  const [twins, setTwins] = useState<DigitalTwin[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => { loadTwins() }, [])

  const loadTwins = async () => {
    try {
      const res = await fetch("/api/backend-proxy/digital-twins")
      const data = await res.json()
      setTwins(data?.twins || [])
    } catch {
      // No twins
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) return <p className={textStyles.caption}>Carregando twins...</p>
  if (twins.length === 0) {
    return (
      <Card className={cardStyles.flat}>
        <CardContent className="flex flex-col items-center py-8">
          <Brain className="w-10 h-10 text-lia-text-disabled mb-2" />
          <p className={textStyles.body}>Nenhum Digital Twin criado</p>
          <p className={textStyles.caption}>Capture o raciocínio de um especialista para criar um twin.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {twins.map(t => (
        <TwinCard key={t.id} twin={t} onEvaluate={onEvaluate} />
      ))}
    </div>
  )
}
