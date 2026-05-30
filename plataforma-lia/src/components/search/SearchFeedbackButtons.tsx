"use client"

import React, { useState } from "react"
import { ThumbsUp, XCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { useSearchFingerprint } from "@/components/search/SearchFingerprintContext"

interface SearchFeedbackButtonsProps {
  candidateId: string
  candidateName?: string
  candidateScore?: number
  jobId?: string
  searchQuery?: string
  initialFeedback?: 'like' | 'dislike' | null
  onFeedbackChange?: (candidateId: string, feedback: 'like' | 'dislike' | null) => void
  className?: string
  size?: 'sm' | 'md'
  alwaysVisible?: boolean
}

export function SearchFeedbackButtons({
  candidateId,
  candidateName,
  candidateScore,
  jobId,
  searchQuery,
  initialFeedback = null,
  onFeedbackChange,
  className,
  size = 'md',
  alwaysVisible = false
}: SearchFeedbackButtonsProps) {
  const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(initialFeedback)
  const [isSubmitting, setIsSubmitting] = useState(false)
  // Fase 2: fingerprint da busca corrente (ancora o feedback aos criterios)
  const searchFingerprint = useSearchFingerprint()

  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : 'w-3.5 h-3.5'
  const btnSize = size === 'sm' ? 'w-7 h-7' : 'w-7 h-7'

  const handleFeedback = async (type: 'like' | 'dislike') => {
    if (isSubmitting) return

    const newFeedback = feedback === type ? null : type
    const previousFeedback = feedback
    
    setFeedback(newFeedback)
    onFeedbackChange?.(candidateId, newFeedback)
    setIsSubmitting(true)

    try {
      const response = await fetch('/api/backend-proxy/search/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidateId,
          feedback_type: type,
          job_id: jobId || null,
          search_query: searchQuery || null,
          candidate_score: candidateScore || null,
          candidate_name: candidateName || null,
          search_fingerprint: searchFingerprint || null,
        })
      })

      if (!response.ok) {
        setFeedback(previousFeedback)
        onFeedbackChange?.(candidateId, previousFeedback)
      }
    } catch {
      setFeedback(previousFeedback)
      onFeedbackChange?.(candidateId, previousFeedback)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className={cn("flex items-center justify-center gap-1.5", className)}>
      <button
        onClick={(e) => { e.stopPropagation(); handleFeedback('like') }}
        disabled={isSubmitting}
        className={cn(
          btnSize,
          "rounded-full flex items-center justify-center hover:opacity-80 transition-opacity motion-reduce:transition-none",
          isSubmitting && "opacity-50 pointer-events-none"
        , "bg-lia-btn-primary-hover")}
        title="Aprovar candidato"
      >
        <ThumbsUp className={cn(iconSize, "text-white")} strokeWidth={2} />
      </button>
      <button
        onClick={(e) => { e.stopPropagation(); handleFeedback('dislike') }}
        disabled={isSubmitting}
        className={cn(
          btnSize,
          "rounded-full flex items-center justify-center hover:opacity-80 transition-opacity motion-reduce:transition-none bg-wedo-coral",
          isSubmitting && "opacity-50 pointer-events-none"
        )}
        title="Reprovar candidato"
      >
        <XCircle className={cn(iconSize, "text-white")} strokeWidth={2} />
      </button>
    </div>
  )
}
