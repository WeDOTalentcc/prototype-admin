"use client"

import * as React from "react"
import { useState, useEffect } from "react"
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
} from "lucide-react"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { StarRating, LikertRating } from "@/components/ui/interview-rating"
import { ScoreCardWSI } from "./score-card-wsi"
import { TeamsAnalysisPanel } from "./teams-analysis-panel"
import { InterviewNote, InterviewNoteQuestion, QuestionBlock, WSIScore, InterviewAnalysisStatus } from "@/types/interview-notes"
import { cn } from "@/lib/utils"

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
  vaga: "bg-gray-100 text-gray-800 dark:text-gray-200",
  gap_analysis: "bg-gray-100 text-gray-800 dark:text-gray-200",
  fit_cultural: "bg-gray-100 text-gray-800 dark:text-gray-200",
  custom: "bg-gray-100 text-gray-800 dark:text-gray-200",
}

const categoryLabels: Record<InterviewNoteQuestion["category"], string> = {
  vaga: "Vaga",
  gap_analysis: "Gap Analysis",
  fit_cultural: "Fit Cultural",
  custom: "Personalizada",
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
      className={cn(
        "border rounded-md p-4 space-y-3",
        question.skipped ? "bg-gray-50 opacity-60" : "bg-white"
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={cn(
                "px-2 py-0.5 rounded-full text-[10px] font-medium",
                categoryColors[question.category]
              )}
            >
              {categoryLabels[question.category]}
            </span>
            {question.source && (
              <span className="text-[10px] text-gray-500">
                Fonte: {question.source}
              </span>
            )}
          </div>
          <p className="text-sm font-medium text-gray-950 dark:text-gray-50">{question.text}</p>
        </div>
        <div className="flex items-center gap-2">
          <Checkbox
            checked={question.skipped}
            onCheckedChange={(checked) =>
              handleSkippedChange(checked as boolean)
            }
            disabled={disabled}
          />
          <label className="text-[11px] text-gray-600 whitespace-nowrap">
            Não perguntei
          </label>
        </div>
      </div>

      {!question.skipped && (
        <>
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-gray-600">Avaliação:</span>
              <StarRating
                value={question.starRating}
                onChange={handleStarChange}
                disabled={disabled}
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-gray-600">Nível:</span>
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
          console.error('Failed to load analysis status:', error)
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
      console.error('Failed to analyze interview:', error)
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
      console.error('Failed to refresh analysis:', error)
    } finally {
      setIsAnalysisLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-50">
              {note.candidateName}
            </h2>
            <div className="flex flex-wrap items-center gap-3 text-[11px] text-gray-600">
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
              <div className="flex items-center border rounded-md overflow-hidden">
                <button
                  type="button"
                  onClick={() => setShowScoreCard(false)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors",
                    !showScoreCard
                      ? "bg-gray-900 text-white"
                      : "bg-white text-gray-600 hover:bg-gray-50"
                  )}
                >
                  <List className="h-3.5 w-3.5" />
                  Perguntas
                </button>
                <button
                  type="button"
                  onClick={() => setShowScoreCard(true)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors",
                    showScoreCard
                      ? "bg-gray-900 text-white"
                      : "bg-white text-gray-600 hover:bg-gray-50"
                  )}
                >
                  <LayoutGrid className="h-3.5 w-3.5" />
                  Score Card
                </button>
              </div>
            )}
            <Badge
              variant={note.status === "completed" ? "success" : "warning"}
            >
              {note.status === "completed" ? "Concluída" : "Rascunho"}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {showScoreCard && blocks && blocks.length > 0 ? (
          <ScoreCardWSI
            candidateName={interviewNote.candidateName || ""}
            jobTitle={interviewNote.jobTitle || ""}
            interviewerName={interviewNote.recruiterName || ""}
            interviewDate={interviewNote.interviewDate?.toString() || new Date().toLocaleDateString()}
            blocks={blocks}
            wsiScore={wsiScore}
            onCalculateWSI={onCalculateWSI}
            onApprove={() => onApprove(interviewNote.nextStage || "next")}
            onReject={onReject}
            onEscalate={onEscalate}
            liaParecer={note.liaParecer || undefined}
            isLoading={isLoading}
          />
        ) : (
          <>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-gray-600" />
            <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
              Perguntas da Entrevista
            </h3>
            <span className="text-[11px] text-gray-500">
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
          <label className="text-sm font-semibold text-gray-950 dark:text-gray-50">
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
              className="flex items-center gap-2 text-sm font-semibold text-gray-950 dark:text-gray-50 hover:text-gray-600"
            >
              {isTranscriptionOpen ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
              Transcrição da Entrevista
              {note.transcriptionSource && (
                <span className="text-[10px] font-normal text-gray-500">
                  (via {note.transcriptionSource})
                </span>
              )}
            </button>
            {isTranscriptionOpen && (
              <div className="bg-gray-50 rounded-md p-4 max-h-[300px] overflow-y-auto">
                <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
                  {note.transcription}
                </p>
              </div>
            )}
          </div>
        )}

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-wedo-cyan" />
            <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50">Parecer LIA</h3>
            {note.liaParecerEditado && (
              <span className="text-[10px] text-amber-600">(editado)</span>
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
            <div className="bg-gray-50 border border-gray-200 rounded-md p-6 text-center">
              <Bot className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500">
                Clique em &quot;Gerar Parecer com LIA&quot; para obter uma
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

        <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-gray-200">
          <Button
            onClick={handleGenerateParecer}
            disabled={isLoading || isGeneratingParecer}
            variant="secondary"
            className="gap-2"
          >
            <Bot className="h-4 w-4" />
            {isGeneratingParecer ? "Gerando..." : "Gerar Parecer com LIA"}
          </Button>

          <Button
            onClick={() => onApprove(note.nextStage || "")}
            disabled={isLoading}
            className="gap-2 bg-green-600 hover:bg-green-700"
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
