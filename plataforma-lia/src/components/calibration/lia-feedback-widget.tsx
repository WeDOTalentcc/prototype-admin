"use client"

import { useState } from "react"
import { ThumbsUp, ThumbsDown, MessageSquare, X, Brain } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"

interface LIAFeedbackWidgetProps {
  candidateId: string
  jobId?: string
  liaScore?: number
  liaRecommendation?: string
  onFeedbackSubmit?: (feedback: {
    agrees: boolean
    reason?: string
  }) => void
  compact?: boolean
  showLabel?: boolean
  className?: string
}

export function LIAFeedbackWidget({
  candidateId,
  jobId,
  liaScore,
  liaRecommendation,
  onFeedbackSubmit,
  compact = false,
  showLabel = true,
  className
}: LIAFeedbackWidgetProps) {
  const [feedbackState, setFeedbackState] = useState<"none" | "agree" | "disagree">("none")
  const [showReason, setShowReason] = useState(false)
  const [reason, setReason] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isOpen, setIsOpen] = useState(false)

  const handleFeedback = async (agrees: boolean) => {
    setFeedbackState(agrees ? "agree" : "disagree")
    
    if (!agrees) {
      setShowReason(true)
      return
    }

    await submitFeedback(agrees)
  }

  const submitFeedback = async (agrees: boolean, feedbackReason?: string) => {
    setIsSubmitting(true)
    try {
      const response = await fetch("/api/backend-proxy/calibration/feedback/explicit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: candidateId,
          job_id: jobId,
          agrees_with_lia: agrees,
          lia_score: liaScore,
          lia_recommendation: liaRecommendation,
          feedback_reason: feedbackReason || reason,
          context: {
            source: "talent_funnel",
            timestamp: new Date().toISOString()
          }
        })
      })

      if (response.ok) {
        onFeedbackSubmit?.({ agrees, reason: feedbackReason || reason })
        setShowReason(false)
        setIsOpen(false)
      }
    } catch (error) {
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleReasonSubmit = () => {
    submitFeedback(false, reason)
  }

  if (compact) {
    return (
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className={cn(
 "h-6 px-2 gap-1 text-xs",
              feedbackState === "agree" && "text-lia-text-secondary bg-lia-bg-tertiary dark:bg-lia-bg-secondary",
              feedbackState === "disagree" && "text-lia-text-primary bg-lia-bg-tertiary",
              className
            )}
          >
            <Brain className="w-3 h-3 text-wedo-cyan" />
            {feedbackState === "none" ? (
              <span className="hidden sm:inline">IA acertou?</span>
            ) : feedbackState === "agree" ? (
              <ThumbsUp className="w-3 h-3" />
            ) : (
              <ThumbsDown className="w-3 h-3" />
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-64 p-3" align="end">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-lia-text-primary">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              A avaliação da IA está correta?
            </div>
            
            {!showReason ? (
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={feedbackState === "agree" ? "primary" : "outline"}
                  className={cn(
 "flex-1 gap-1",
                    feedbackState === "agree" && "bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                  )}
                  onClick={() => handleFeedback(true)}
                  disabled={isSubmitting}
                >
                  <ThumbsUp className="w-4 h-4" />
                  Sim
                </Button>
                <Button
                  size="sm"
                  variant={feedbackState === "disagree" ? "primary" : "outline"}
                  className={cn(
 "flex-1 gap-1",
                    feedbackState === "disagree" && "bg-lia-border-medium hover:bg-lia-bg-inverse"
                  )}
                  onClick={() => handleFeedback(false)}
                  disabled={isSubmitting}
                >
                  <ThumbsDown className="w-4 h-4" />
                  Não
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                <Textarea
                  placeholder="Por que você discorda? (opcional)"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="text-sm h-20 resize-none"
                />
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1"
                    onClick={() => {
                      setShowReason(false)
                      setFeedbackState("none")
                    }}
                  >
                    Cancelar
                  </Button>
                  <Button
                    size="sm"
                    className="flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                    onClick={handleReasonSubmit}
                    disabled={isSubmitting}
                  >
                    Enviar
                  </Button>
                </div>
              </div>
            )}
          </div>
        </PopoverContent>
      </Popover>
    )
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {showLabel && (
        <span className="text-xs text-lia-text-primary flex items-center gap-1">
          <Brain className="w-3 h-3 text-wedo-cyan" />
          IA acertou?
        </span>
      )}
      
      <div className="flex gap-1">
        <Button
          variant="ghost"
          size="sm"
          className={cn(
 "h-7 w-7 p-0 rounded-full",
            feedbackState === "agree" && "bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary"
          )}
          onClick={() => handleFeedback(true)}
          disabled={isSubmitting || feedbackState !== "none"}
          title="Concordo"
        >
          <ThumbsUp className="w-4 h-4" />
        </Button>
        
        <Popover open={showReason} onOpenChange={setShowReason}>
          <PopoverTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
 "h-7 w-7 p-0 rounded-full",
                feedbackState === "disagree" && "bg-lia-interactive-active text-lia-text-secondary"
              )}
              onClick={() => handleFeedback(false)}
              disabled={isSubmitting || feedbackState !== "none"}
              title="Discordo da IA"
            >
              <ThumbsDown className="w-4 h-4" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-64 p-3" align="end">
            <div className="space-y-2">
              <p className="text-sm font-medium text-lia-text-primary">
                Por que você discorda?
              </p>
              <Textarea
                placeholder="Explique brevemente (opcional)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="text-sm h-20 resize-none"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowReason(false)
                    setFeedbackState("none")
                  }}
                >
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  className="flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                  onClick={handleReasonSubmit}
                  disabled={isSubmitting}
                >
                  Enviar
                </Button>
              </div>
            </div>
          </PopoverContent>
        </Popover>
      </div>
    </div>
  )
}
