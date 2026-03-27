"use client"

import * as React from "react"
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Calculator,
  User,
  Briefcase,
  Calendar,
  Bot,
} from "lucide-react"
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  QuestionBlock,
  WSIScore,
  BLOCK_WEIGHTS,
  WSI_THRESHOLDS,
} from "@/types/interview-notes"
import { cn } from "@/lib/utils"

interface ScoreCardWSIProps {
  candidateName: string
  jobTitle: string
  interviewerName: string
  interviewDate: string
  blocks: QuestionBlock[]
  wsiScore?: WSIScore
  onCalculateWSI?: () => void
  onApprove?: () => void
  onReject?: () => void
  onEscalate?: () => void
  liaParecer?: string
  isLoading?: boolean
}

const blockLabels: Record<string, string> = {
  technical: "Competências Técnicas",
  behavioral: "Competências Comportamentais",
  gap_analysis: "Experiência Profissional",
  contextual: "Fit Cultural e Alinhamento",
}

const blockWeightLabels: Record<string, string> = {
  technical: "50%",
  behavioral: "20%",
  gap_analysis: "15%",
  contextual: "15%",
}

function calculateBlockScore(block: QuestionBlock): number {
  const validQuestions = block.questions.filter(
    (q) => !q.skipped && q.starRating !== null
  )
  if (validQuestions.length === 0) return 0
  const sum = validQuestions.reduce((acc, q) => acc + (q.starRating || 0), 0)
  return sum / validQuestions.length
}

function calculateWSILocally(blocks: QuestionBlock[]): WSIScore {
  const technicalBlock = blocks.find((b) => b.type === "technical")
  const behavioralBlock = blocks.find((b) => b.type === "behavioral")
  const gapBlock = blocks.find((b) => b.type === "gap_analysis")
  const contextualBlock = blocks.find((b) => b.type === "contextual")

  const technicalScore = technicalBlock
    ? technicalBlock.subtotalScore ?? calculateBlockScore(technicalBlock)
    : 0
  const behavioralScore = behavioralBlock
    ? behavioralBlock.subtotalScore ?? calculateBlockScore(behavioralBlock)
    : 0
  const gapAnalysisScore = gapBlock
    ? gapBlock.subtotalScore ?? calculateBlockScore(gapBlock)
    : 0
  const contextualScore = contextualBlock
    ? contextualBlock.subtotalScore ?? calculateBlockScore(contextualBlock)
    : 0

  const totalWSI =
    technicalScore * BLOCK_WEIGHTS.technical +
    behavioralScore * BLOCK_WEIGHTS.behavioral +
    gapAnalysisScore * BLOCK_WEIGHTS.gap_analysis +
    contextualScore * BLOCK_WEIGHTS.contextual

  let decision: WSIScore["decision"]
  let decisionLabel: string

  if (totalWSI >= WSI_THRESHOLDS.approved) {
    decision = "approved"
    decisionLabel = "Aprovado"
  } else if (totalWSI >= WSI_THRESHOLDS.humanReview) {
    decision = "human_review"
    decisionLabel = "Revisão Humana"
  } else {
    decision = "rejected"
    decisionLabel = "Reprovado"
  }

  return {
    technicalScore,
    behavioralScore,
    gapAnalysisScore,
    contextualScore,
    totalWSI,
    decision,
    decisionLabel,
  }
}

function getDecisionBadgeStyles(decision: WSIScore["decision"]): string {
  switch (decision) {
    case "approved":
      return "bg-status-success/15 text-status-success border-status-success/30"
    case "human_review":
      return "bg-status-warning/15 text-status-warning border-status-warning/30"
    case "rejected":
      return "bg-status-error/15 text-status-error border-status-error/30"
    default:
      return "bg-gray-100 text-gray-800 border-gray-200"
  }
}

function getDecisionIcon(decision: WSIScore["decision"]) {
  switch (decision) {
    case "approved":
      return <CheckCircle className="h-4 w-4" />
    case "human_review":
      return <AlertTriangle className="h-4 w-4" />
    case "rejected":
      return <XCircle className="h-4 w-4" />
    default:
      return null
  }
}

function BlockSection({
  block,
  score,
}: {
  block: QuestionBlock
  score: number
}) {
  const progressValue = (score / 5) * 100

  return (
    <div className="border border-gray-200 rounded-md p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
            {blockLabels[block.type]}
          </span>
          <span className="text-xs text-gray-500">
            (Peso: {blockWeightLabels[block.type]})
          </span>
        </div>
        <span className="text-sm font-semibold text-gray-950 dark:text-gray-50">
          {score.toFixed(2)} / 5.00
        </span>
      </div>

      <Progress value={progressValue} className="h-2" />

      <div className="space-y-2">
        {block.questions.map((question) => (
          <div
            key={question.id}
            className={cn(
              "flex items-center justify-between py-1.5 px-2 rounded text-xs",
              question.skipped ? "bg-gray-50 text-gray-400" : "bg-gray-50"
            )}
          >
            <span className="flex-1 truncate text-gray-600">
              {question.skillName || question.text}
            </span>
            <span
              className={cn(
                "font-medium ml-2",
                question.skipped
                  ? "text-gray-400"
                  : question.starRating && question.starRating >= 4
                    ? "text-status-success"
                    : question.starRating && question.starRating >= 3
                      ? "text-status-warning"
                      : "text-gray-600"
              )}
            >
              {question.skipped
                ? "N/A"
                : question.starRating
                  ? `${question.starRating}/5`
                  : "-"}
            </span>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-gray-100">
        <span className="text-xs text-gray-500">Subtotal do Bloco</span>
        <span className="text-sm font-semibold text-gray-700">
          {score.toFixed(2)}
        </span>
      </div>
    </div>
  )
}

export function ScoreCardWSI({
  candidateName,
  jobTitle,
  interviewerName,
  interviewDate,
  blocks,
  wsiScore: providedWsiScore,
  onCalculateWSI,
  onApprove,
  onReject,
  onEscalate,
  liaParecer,
  isLoading = false,
}: ScoreCardWSIProps) {
  const wsiScore = providedWsiScore || calculateWSILocally(blocks)

  const blockScores: Record<string, number> = {
    technical: wsiScore.technicalScore,
    behavioral: wsiScore.behavioralScore,
    gap_analysis: wsiScore.gapAnalysisScore,
    contextual: wsiScore.contextualScore,
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      })
    } catch {
      return dateString
    }
  }

  return (
    <Card className="w-full border-gray-200">
      <CardHeader className="pb-4 border-b border-gray-200">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div className="space-y-2">
            <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-50">
              Score Card WSI
            </h2>
            <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600">
              <div className="flex items-center gap-1.5">
                <User className="h-3.5 w-3.5 text-gray-400" />
                <span className="font-medium text-gray-800 dark:text-gray-200">
                  {candidateName}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <Briefcase className="h-3.5 w-3.5 text-gray-400" />
                <span>{jobTitle}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <User className="h-3.5 w-3.5 text-gray-400" />
                <span>Entrevistador: {interviewerName}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-gray-400" />
                <span>{formatDate(interviewDate)}</span>
              </div>
            </div>
          </div>

          <div
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-medium",
              getDecisionBadgeStyles(wsiScore.decision)
            )}
          >
            {getDecisionIcon(wsiScore.decision)}
            <span>{wsiScore.decisionLabel}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="py-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {blocks.map((block) => (
            <BlockSection
              key={block.type}
              block={block}
              score={blockScores[block.type] || 0}
            />
          ))}
        </div>

        <div className="border border-gray-200 rounded-md p-4 bg-gray-50">
          <div className="flex items-center gap-2 mb-4">
            <Calculator className="h-4 w-4 text-gray-700" />
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
              Cálculo do WSI Final
            </h3>
          </div>

          <div className="space-y-3">
            <div className="text-xs text-gray-600 font-mono bg-white p-3 rounded border border-gray-200">
              WSI = (Téc × 50%) + (Comp × 20%) + (Gap × 15%) + (Ctx × 15%)
            </div>

            <div className="text-xs text-gray-600 font-mono bg-white p-3 rounded border border-gray-200">
              WSI = ({wsiScore.technicalScore.toFixed(2)} × 0.50) + (
              {wsiScore.behavioralScore.toFixed(2)} × 0.20) + (
              {wsiScore.gapAnalysisScore.toFixed(2)} × 0.15) + (
              {wsiScore.contextualScore.toFixed(2)} × 0.15)
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-gray-200">
              <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                WSI Final
              </span>
              <div className="flex items-center gap-3">
                <Progress
                  value={(wsiScore.totalWSI / 5) * 100}
                  className="w-32 h-3"
                />
                <span
                  className="text-xl font-bold text-gray-700"
                >
                  {wsiScore.totalWSI.toFixed(2)}
                </span>
                <span className="text-sm text-gray-500">/ 5.00</span>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-gray-500 pt-2">
              <span>Limiares: Aprovado ≥ 4.2 | Revisão: 3.8 - 4.2 | Reprovado &lt; 3.8</span>
            </div>
          </div>
        </div>

        {liaParecer && (
          <div className="border border-gray-200 rounded-md p-4">
            <div className="flex items-center gap-2 mb-3">
              <Bot className="h-4 w-4 text-wedo-cyan" />
              <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                Parecer LIA
              </h3>
            </div>
            <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed">
              {liaParecer}
            </p>
          </div>
        )}
      </CardContent>

      <CardFooter className="pt-4 border-t border-gray-200 flex flex-wrap gap-3">
        {onCalculateWSI && (
          <Button
            onClick={onCalculateWSI}
            disabled={isLoading}
            variant="outline"
            className="gap-2"
          >
            <Calculator className="h-4 w-4" />
            Recalcular WSI
          </Button>
        )}

        <div className="flex-1" />

        {onApprove && (
          <Button
            onClick={onApprove}
            disabled={isLoading}
            className="gap-2 bg-status-success hover:bg-status-success/10 text-white"
          >
            <CheckCircle className="h-4 w-4" />
            Aprovar
          </Button>
        )}

        {onReject && (
          <Button
            onClick={onReject}
            disabled={isLoading}
            variant="destructive"
            className="gap-2"
          >
            <XCircle className="h-4 w-4" />
            Reprovar
          </Button>
        )}

        {onEscalate && (
          <Button
            onClick={onEscalate}
            disabled={isLoading}
            variant="outline"
            className="gap-2 border-status-warning/30 text-status-warning hover:bg-status-warning/10"
          >
            <AlertTriangle className="h-4 w-4" />
            Escalar p/ Gestor
          </Button>
        )}
      </CardFooter>
    </Card>
  )
}
