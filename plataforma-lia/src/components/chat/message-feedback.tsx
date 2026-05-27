"use client"

import React, { useState } from "react"
import { ThumbsUp, ThumbsDown, Star, MessageSquare, Check, Loader2, Edit3 } from "lucide-react"
import { toast } from "@/lib/toast"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import { submitThumbsFeedback, submitRatingFeedback, submitCorrectionFeedback } from "@/services/lia-api"

interface MessageFeedbackProps {
  sessionId: string
  messageId: string
  originalResponse: string
  onFeedbackSubmitted?: (type: 'thumbs' | 'rating' | 'correction') => void
  className?: string
}

export function MessageFeedback({ 
  sessionId, 
  messageId, 
  originalResponse,
  onFeedbackSubmitted,
  className 
}: MessageFeedbackProps) {
  const [thumbsState, setThumbsState] = useState<'up' | 'down' | null>(null)
  const [rating, setRating] = useState<number>(0)
  const [hoveredStar, setHoveredStar] = useState<number>(0)
  const [showCorrectionInput, setShowCorrectionInput] = useState(false)
  const [correction, setCorrection] = useState("")
  const [correctionSubmitted, setCorrectionSubmitted] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [ratingPopoverOpen, setRatingPopoverOpen] = useState(false)
  const [correctionPopoverOpen, setCorrectionPopoverOpen] = useState(false)

  const handleThumbs = async (value: 'up' | 'down') => {
    if (thumbsState === value) return
    const previous = thumbsState
    setThumbsState(value)
    try {
      await submitThumbsFeedback(sessionId, messageId, value)
      onFeedbackSubmitted?.('thumbs')
    } catch {
      // Audit #569 F2: feedback-api now throws on non-2xx. Revert optimistic
      // state and surface a toast so the user knows the click did not stick.
      setThumbsState(previous)
      toast.error("Não foi possível registrar seu feedback")
    }
  }

  const handleRating = async (stars: number) => {
    if (rating === stars) return
    const previous = rating
    setRating(stars)
    try {
      await submitRatingFeedback(sessionId, messageId, stars)
      onFeedbackSubmitted?.('rating')
      setTimeout(() => setRatingPopoverOpen(false), 500)
    } catch {
      setRating(previous)
      toast.error("Não foi possível registrar seu feedback")
    }
  }

  const handleCorrection = async () => {
    if (!correction.trim() || isSubmitting) return
    setIsSubmitting(true)
    try {
      await submitCorrectionFeedback(sessionId, messageId, originalResponse, correction)
      setCorrectionSubmitted(true)
      onFeedbackSubmitted?.('correction')
      setTimeout(() => setCorrectionPopoverOpen(false), 1000)
    } catch {
      // Keep popover open so the user can retry; surface error explicitly.
      toast.error("Não foi possível enviar sua correção")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <button
        onClick={() => handleThumbs('up')}
        className={cn(
          "p-1.5 rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-lia-border-default",
          thumbsState === 'up'
            ? "bg-status-success/15 text-status-success"
            : "text-lia-text-tertiary hover:text-lia-text-secondary hover:bg-lia-interactive-hover"
        )}
        title="Resposta útil"
        aria-label="Resposta útil"
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      
      <button
        onClick={() => handleThumbs('down')}
        className={cn(
          "p-1.5 rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-lia-border-default",
          thumbsState === 'down'
            ? "bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error"
            : "text-lia-text-tertiary hover:text-lia-text-secondary hover:bg-lia-interactive-hover"
        )}
        title="Resposta não útil"
        aria-label="Resposta não útil"
      >
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>

      <Popover open={ratingPopoverOpen} onOpenChange={setRatingPopoverOpen}>
        <PopoverTrigger asChild>
          <button
            className={cn(
              "p-1.5 rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-lia-border-default",
              rating > 0
                ? "bg-status-warning/15 text-status-warning dark:bg-status-warning/30"
                : "text-lia-text-tertiary hover:text-lia-text-secondary hover:bg-lia-interactive-hover"
            )}
            title="Avaliar resposta"
            aria-label="Avaliar resposta"
          >
            <Star className={cn("w-3.5 h-3.5", rating > 0 && "fill-current")} />
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-3" align="start" sideOffset={8}>
          <div className="flex flex-col gap-2">
            <span className="text-xs font-medium text-lia-text-primary">
              Avalie esta resposta
            </span>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => handleRating(star)}
                  onMouseEnter={() => setHoveredStar(star)}
                  onMouseLeave={() => setHoveredStar(0)}
                  aria-label={`Avaliar ${star} estrela${star > 1 ? 's' : ''}`}
                  className={cn(
                    "p-1 rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-lia-border-default",
                    (hoveredStar >= star || rating >= star)
                      ? "text-status-warning"
                      : "text-lia-text-disabled"
                  )}
                >
                  <Star 
                    className={cn(
                      "w-5 h-5 transition-colors",
                      (hoveredStar >= star || rating >= star) && "fill-current"
                    )} 
                  />
                </button>
              ))}
            </div>
            {rating > 0 && (
              <div className="flex items-center gap-1 text-xs text-status-success">
                <Check className="w-3 h-3" />
                <span>Avaliação enviada!</span>
              </div>
            )}
          </div>
        </PopoverContent>
      </Popover>

      <Popover open={correctionPopoverOpen} onOpenChange={setCorrectionPopoverOpen}>
        <PopoverTrigger asChild>
          <button
            className={cn(
              "p-1.5 rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-lia-border-default",
              correctionSubmitted
                ? "bg-wedo-cyan/15 text-wedo-cyan-dark"
                : "text-lia-text-tertiary hover:text-lia-text-secondary hover:bg-lia-interactive-hover"
            )}
            title="Sugerir correção"
            aria-label="Sugerir correção"
          >
            <Edit3 className="w-3.5 h-3.5" />
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-80 p-3" align="start" sideOffset={8}>
          <div className="flex flex-col gap-3">
            <div>
              <span className="text-xs font-medium text-lia-text-primary">
                Sugerir correção
              </span>
              <p className="text-micro text-lia-text-secondary mt-0.5">
                Ajude a IA a melhorar suas respostas
              </p>
            </div>
            
            {!correctionSubmitted ? (
              <>
                <Textarea
                  value={correction}
                  onChange={(e) => setCorrection(e.target.value)}
                  placeholder="Qual seria a resposta correta ou mais adequada?"
                  className="min-h-20 text-xs"
                />
                <div className="flex justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setCorrectionPopoverOpen(false)}
                    className="h-7 text-xs"
                  >
                    Cancelar
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleCorrection}
                    disabled={!correction.trim() || isSubmitting}
                    className="h-7 text-xs"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none mr-1" />
                        Enviando...
                      </>
                    ) : (
                      'Enviar correção'
                    )}
                  </Button>
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2 py-2 text-xs text-status-success">
                <Check className="w-4 h-4" />
                <span>Correção enviada! Obrigado pelo feedback.</span>
              </div>
            )}
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}
