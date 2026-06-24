"use client"

import * as React from"react"
import { useState, useEffect } from"react"
import { Chip } from "@/components/ui/chip"
import { 
  getInterviewAnalysisStatus, 
  triggerInterviewAnalysis 
} from '@/services/lia-api'
import {
  MessageSquare,
  CheckCircle,
  XCircle,
  Bot,
  ChevronDown,
  ChevronUp,
  Calendar,
  User,
  Briefcase,
  Save,
  LayoutGrid,
  List,
} from"lucide-react"
import { Card, CardHeader, CardContent } from"@/components/ui/card"
import { Button } from"@/components/ui/button"
import { Textarea } from"@/components/ui/textarea"
import { Checkbox } from"@/components/ui/checkbox"
import { StarRating, LikertRating } from"@/components/ui/interview-rating"
import { ScoreCardWSI } from"./score-card-wsi"
import { TeamsAnalysisPanel } from"./teams-analysis-panel"
import { InterviewNote, InterviewNoteQuestion, QuestionBlock, WSIScore, InterviewAnalysisStatus } from"@/types/interview-notes"
import { cn } from"@/lib/utils"
import { useAiPersona } from "@/hooks/company/use-ai-persona"

interface InterviewNoteCardProps {
  interviewNote: InterviewNote
  onSave: (note: InterviewNote) => void
  onGenerateParecer: () => Promise<string>
  onApprove: (nextStage: string) => void
  onReject: () => void
  blocks?: QuestionBlock[]
  wsiScore?: WSIScore
  onCalculateWSI?: () => void
  onEscalate?: () => void
  isLoading?: boolean
}

const categoryColors: Record<InterviewNoteQuestion["category"], string> = {
  vaga:"bg-lia-bg-tertiary text-lia-text-primary",
  gap_analysis:"bg-lia-bg-tertiary text-lia-text-primary",
  fit_cultural:"bg-lia-bg-tertiary text-lia-text-primary",
  custom:"bg-lia-bg-tertiary text-lia-text-primary",
}

const categoryLabels: Record<InterviewNoteQuestion["category"], string> = {
  vaga:"Vaga",
  gap_analysis:"Gap Analysis",
  fit_cultural:"Aderência Cultural",
  custom:"Personalizada",
}

function QuestionItem({
  question,
  onChange,
  disabled,
}: {
  question: InterviewNoteQuestion
  onChange: (updated: InterviewNoteQuestion) => void
  disabled?: boolean
}) {
  const handleStarChange = (rating: number) => {
    onChange({ ...question, starRating: rating })
  }

  const handleLikertChange = (
    value: InterviewNoteQuestion["likertRating"]
  ) => {
    onChange({ ...question, likertRating: value })
  }

  const handleNotesChange = (notes: string) => {
    onChange({ ...question, notes })
  }

  const handleSkippedChange = (skipped: boolean) => {
    onChange({ ...question, skipped })
  }

  return (
    <div
      className={cn("border rounded-md p-4 space-y-3",
        question.skipped ?"bg-lia-bg-secondary opacity-60" :"bg-lia-bg-primary"
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={cn("px-2 py-0.5 rounded-full text-micro font-medium",
                categoryColors[question.category]
              )}
            >
              {categoryLabels[question.category]}
            </span>
            {question.source && (
              <span className="text-micro text-lia-text-secondary">
                Fonte: {question.source}
              </span>
            )}
          </div>
          <p className="text-sm font-medium text-lia-text-primary">{question.text}</p>
        </div>
        <div className="flex items-center gap-2">
          <Checkbox
            checked={question.skipped}
            onCheckedChange={(checked) =>
              handleSkippedChange(checked as boolean)
            }
            disabled={disabled}
          />
          <label className="text-xs text-lia-text-secondary whitespace-nowrap">
            Não perguntei
          </label>
        </div>
      </div>

      {!question.skipped && (
        <>
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-lia-text-secondary">Avaliação:</span>
              <StarRating
                value={question.starRating}
                onChange={handleStarChange}
                disabled={disabled}
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-lia-text-secondary">Nível:</span>
              <LikertRating
                value={question.likertRating || null}
                onChange={handleLikertChange}
                disabled={question.skipped || disabled}
                size="sm"
              />
            </div>
          </div>

          <Textarea
            placeholder="Anotações sobre a resposta do candidato..."
            value={question.notes}
            onChange={(e) => handleNotesChange(e.target.value)}
            disabled={disabled}
            className="min-h-[60px]"
          />
        </>
      )}
    </div>
  )
}

export function InterviewNoteCard({
  interviewNote,
  onSave,
  onGenerateParecer,
  onApprove,
  onReject,
  blocks,
  wsiScore,
  onCalculateWSI,
  onEscalate,
  isLoading = false,
}: InterviewNoteCardProps) {
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  const [note, setNote] = useState<InterviewNote>(interviewNote)
  const [isTranscriptionOpen, setIsTranscriptionOpen] = useState(false)
  const [isGeneratingParecer, setIsGeneratingParecer] = useState(false)
  const [showScoreCard, setShowScoreCard] = useState(false)
  const [analysisStatus, setAnalysisStatus] = useState<InterviewAnalysisStatus | null>(null)
  const [isAnalysisLoading, setIsAnalysisLoading] = useState(false)

  // Load Teams analysis status when interviewId is available
  useEffect(() => {
    async function loadAnalysisStatus() {
      if (note.interviewId) {
        try {
          setIsAnalysisLoading(true)
          const status = await getInterviewAnalysisStatus(note.interviewId)
          setAnalysisStatus(status)
        } catch (error) {
        } finally {
          setIsAnalysisLoading(false)
        }
      }
    }
    loadAnalysisStatus()
  }, [note.interviewId])

  const handleQuestionChange = (updatedQuestion: InterviewNoteQuestion) => {
    setNote((prev) => ({
      ...prev,
      questions: prev.questions.map((q) =>
        q.id === updatedQuestion.id ? updatedQuestion : q
      ),
    }))
  }

  const handleGeneralNotesChange = (generalNotes: string) => {
    setNote((prev) => ({ ...prev, generalNotes }))
  }

  const handleGenerateParecer = async () => {
    setIsGeneratingParecer(true)
    try {
      const parecer = await onGenerateParecer()
      setNote((prev) => ({ ...prev, liaParecer: parecer }))
    } finally {
      setIsGeneratingParecer(false)
    }
  }

  const handleParecerChange = (liaParecer: string) => {
    setNote((prev) => ({ ...prev, liaParecer, liaParecerEditado: true }))
  }

  const handleSave = () => {
    onSave(note)
  }

  const handleAnalyzeTeams = async () => {
    if (!note.interviewId) return
    try {
      setIsAnalysisLoading(true)
      const result = await triggerInterviewAnalysis(note.interviewId, false)
      setAnalysisStatus(result)
    } catch (error) {
    } finally {
      setIsAnalysisLoading(false)
    }
  }

  const handleRefreshTeamsAnalysis = async () => {
    if (!note.interviewId) return
    try {
      setIsAnalysisLoading(true)
      const result = await triggerInterviewAnalysis(note.interviewId, true)
      setAnalysisStatus(result)
    } catch (error) {
    } finally {
      setIsAnalysisLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("pt-BR", {
      day:"2-digit",
      month:"2-digit",
      year:"numeric",
      hour:"2-digit",
      minute:"2-digit",
    })
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-lia-text-primary">
              {note.candidateName}
            </h2>
            <div className="flex flex-wrap items-center gap-3 text-xs text-lia-text-secondary">
              {note.jobTitle && (
                <div className="flex items-center gap-1">
                  <Briefcase className="h-3.5 w-3.5" />
                  <span>{note.jobTitle}</span>
                </div>
              )}
              <div className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                <span>{formatDate(note.interviewDate)}</span>
              </div>
              <div className="flex items-center gap-1">
                <User className="h-3.5 w-3.5" />
                <span>{note.recruiterName}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 self-start md:self-center">
            {blocks && blocks.length > 0 && (
              <div className="flex items-center border rounded-xl overflow-hidden">
                <button
                  type="button"
                  onClick={() => setShowScoreCard(false)}
                  className={cn("flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors",
                    !showScoreCard
                      ?"bg-lia-btn-primary-bg text-lia-btn-primary-text"
                      :"bg-lia-bg-primary text-lia-text-secondary hover:bg-lia-bg-secondary"
                  )}
                >
                  <List className="h-3.5 w-3.5" />
                  Perguntas
                </button>
                <button
                  type="button"
                  onClick={() => setShowScoreCard(true)}
                  className={cn("flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors",
                    showScoreCard
                      ?"bg-lia-btn-primary-bg text-lia-btn-primary-text"
                      :"bg-lia-bg-primary text-lia-text-secondary hover:bg-lia-bg-secondary"
                  )}
                >
                  <LayoutGrid className="h-3.5 w-3.5" />
                  Score Card
                </button>
              </div>
            )}
            <Chip
              variant={note.status ==="completed" ?"success" :"warning"}
            >
              {note.status ==="completed" ?"Concluída" :"Rascunho"}
            </Chip>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {showScoreCard && blocks && blocks.length > 0 ? (
          <ScoreCardWSI
            candidateName={interviewNote.candidateName ||""}
            jobTitle={interviewNote.jobTitle ||""}
            interviewerName={interviewNote.recruiterName ||""}
            interviewDate={interviewNote.interviewDate?.toString() || new Date().toLocaleDateString()}
            blocks={blocks}
            wsiScore={wsiScore}
            onCalculateWSI={onCalculateWSI}
            onApprove={() => onApprove(interviewNote.nextStage ||"next")}
            onReject={onReject}
            onEscalate={onEscalate}
            liaParecer={note.liaParecer || undefined}
            isLoading={isLoading}
          />
        ) : (
          <>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-lia-text-secondary" />
            <h3 className="text-sm font-semibold text-lia-text-primary">
              Perguntas da Entrevista
            </h3>
            <span className="text-xs text-lia-text-secondary">
              ({note.questions.length} perguntas)
            </span>
          </div>
          <div className="space-y-3">
            {note.questions.map((question) => (
              <QuestionItem
                key={question.id}
                question={question}
                onChange={handleQuestionChange}
                disabled={isLoading}
              />
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-lia-text-primary">
            Observações Gerais
          </label>
          <Textarea
            placeholder="Adicione observações gerais sobre a entrevista..."
            value={note.generalNotes}
            onChange={(e) => handleGeneralNotesChange(e.target.value)}
            disabled={isLoading}
            className="min-h-[100px]"
          />
        </div>

        {note.transcription !== null && (
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setIsTranscriptionOpen(!isTranscriptionOpen)}
              className="flex items-center gap-2 text-sm font-semibold text-lia-text-primary hover:text-lia-text-secondary"
            >
              {isTranscriptionOpen ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
              Transcrição da Entrevista
              {note.transcriptionSource && (
                <span className="text-micro font-normal text-lia-text-secondary">
                  (via {note.transcriptionSource})
                </span>
              )}
            </button>
            {isTranscriptionOpen && (
              <div className="bg-lia-bg-secondary rounded-xl p-4 max-h-content-md overflow-y-auto">
                <p className="text-sm text-lia-text-primary whitespace-pre-wrap">
                  {note.transcription}
                </p>
              </div>
            )}
          </div>
        )}

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-wedo-cyan" />
            <h3 className="text-sm font-semibold text-lia-text-primary">Parecer LIA</h3>
            {note.liaParecerEditado && (
              <span className="text-micro text-status-warning">(editado)</span>
            )}
          </div>
          {note.liaParecer ? (
            <Textarea
              value={note.liaParecer}
              onChange={(e) => handleParecerChange(e.target.value)}
              disabled={isLoading}
              className="min-h-[120px]"
            />
          ) : (
            <div className="bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-6 text-center">
              <Bot className="h-8 w-8 text-lia-text-secondary mx-auto mb-2" />
              <p className="text-sm text-lia-text-secondary">
                Clique em {`"Gerar Parecer com ${personaName}"`} para obter uma
                análise automática da entrevista.
              </p>
            </div>
          )}
        </div>

        {note.interviewId && (
          <TeamsAnalysisPanel
            interviewId={note.interviewId}
            status={analysisStatus}
            isLoading={isAnalysisLoading}
            onAnalyze={handleAnalyzeTeams}
            onRefresh={handleRefreshTeamsAnalysis}
          />
        )}

        <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-lia-border-subtle">
          <Button
            onClick={handleGenerateParecer}
            disabled={isLoading || isGeneratingParecer}
            variant="secondary"
            className="gap-2"
          >
            <Bot className="h-4 w-4" />
            {isGeneratingParecer ?"Gerando..." :`Gerar Parecer com ${personaName}`}
          </Button>

          <Button
            onClick={() => onApprove(note.nextStage ||"")}
            disabled={isLoading}
            className="gap-2 bg-status-success hover:bg-status-success/10"
          >
            <CheckCircle className="h-4 w-4" />
            Aprovar e Avançar
          </Button>

          <Button
            onClick={onReject}
            disabled={isLoading}
            variant="destructive"
            className="gap-2"
          >
            <XCircle className="h-4 w-4" />
            Reprovar
          </Button>

          <Button
            onClick={handleSave}
            disabled={isLoading}
            variant="outline"
            className="gap-2 ml-auto"
          >
            <Save className="h-4 w-4" />
            Salvar Rascunho
          </Button>
        </div>
        </>
        )}
      </CardContent>
    </Card>
  )
}
