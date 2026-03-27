"use client"

import React, { useState } from "react"
import { ThumbsUp, ThumbsDown, Star, MessageSquare, Check, Loader2, Edit3 } from "lucide-react"
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
    setThumbsState(value)
    try {
      await submitThumbsFeedback(sessionId, messageId, value)
      onFeedbackSubmitted?.('thumbs')
    } catch (error) {
      console.warn('Failed to submit thumbs feedback:', error)
    }
  }

  const handleRating = async (stars: number) => {
    if (rating === stars) return
    setRating(stars)
    try {
      await submitRatingFeedback(sessionId, messageId, stars)
      onFeedbackSubmitted?.('rating')
      setTimeout(() => setRatingPopoverOpen(false), 500)
    } catch (error) {
      console.warn('Failed to submit rating feedback:', error)
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
    } catch (error) {
      console.warn('Failed to submit correction feedback:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <button
        onClick={() => handleThumbs('up')}
        className={cn(
          "p-1.5 rounded-md transition-all focus-visible:ring-2 focus-visible:ring-gray-400",
          thumbsState === 'up'
            ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400"
            : "text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 dark:hover:text-gray-300"
        )}
        title="Resposta útil"
        aria-label="Resposta útil"
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      
      <button
        onClick={() => handleThumbs('down')}
        className={cn(
          "p-1.5 rounded-md transition-all focus-visible:ring-2 focus-visible:ring-gray-400",
          thumbsState === 'down'
            ? "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400"
            : "text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 dark:hover:text-gray-300"
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
              "p-1.5 rounded-md transition-all focus-visible:ring-2 focus-visible:ring-gray-400",
              rating > 0
                ? "bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400"
                : "text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 dark:hover:text-gray-300"
            )}
            title="Avaliar resposta"
            aria-label="Avaliar resposta"
          >
            <Star className={cn("w-3.5 h-3.5", rating > 0 && "fill-current")} />
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-3" align="start" sideOffset={8}>
          <div className="flex flex-col gap-2">
            <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
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
                    "p-1 rounded transition-all focus-visible:ring-2 focus-visible:ring-gray-400",
                    (hoveredStar >= star || rating >= star)
                      ? "text-amber-500"
                      : "text-gray-300 dark:text-gray-600"
                  )}
                >
                  <Star 
                    className={cn(
                      "w-5 h-5 transition-all",
                      (hoveredStar >= star || rating >= star) && "fill-current"
                    )} 
                  />
                </button>
              ))}
            </div>
            {rating > 0 && (
              <div className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
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
              "p-1.5 rounded-md transition-all focus-visible:ring-2 focus-visible:ring-gray-400",
              correctionSubmitted
                ? "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400"
                : "text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 dark:hover:text-gray-300"
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
              <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                Sugerir correção
              </span>
              <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
                Ajude a LIA a melhorar suas respostas
              </p>
            </div>
            
            {!correctionSubmitted ? (
              <>
                <Textarea
                  value={correction}
                  onChange={(e) => setCorrection(e.target.value)}
                  placeholder="Qual seria a resposta correta ou mais adequada?"
                  className="min-h-[80px] text-xs"
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
                        <Loader2 className="w-3 h-3 animate-spin mr-1" />
                        Enviando...
                      </>
                    ) : (
                      'Enviar correção'
                    )}
                  </Button>
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2 py-2 text-xs text-emerald-600 dark:text-emerald-400">
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
