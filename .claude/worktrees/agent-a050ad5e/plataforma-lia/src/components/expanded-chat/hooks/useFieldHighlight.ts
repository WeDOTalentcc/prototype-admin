'use client'

import { useState, useCallback, useRef, useEffect } from 'react'

export interface UseFieldHighlightOptions {
  highlightDurationMs?: number
}

export interface UseFieldHighlightReturn {
  highlightField: (fieldId: string) => void
  isHighlighted: (fieldId: string) => boolean
  clearHighlight: (fieldId: string) => void
  clearAllHighlights: () => void
  highlightedFields: Set<string>
}

export function useFieldHighlight(
  options: UseFieldHighlightOptions = {}
): UseFieldHighlightReturn {
  const { highlightDurationMs = 2000 } = options

  const [highlightedFields, setHighlightedFields] = useState<Set<string>>(new Set())
  const timersRef = useRef<Map<string, NodeJS.Timeout>>(new Map())

  useEffect(() => {
    return () => {
      timersRef.current.forEach((timer) => clearTimeout(timer))
      timersRef.current.clear()
    }
  }, [])

  const highlightField = useCallback((fieldId: string) => {
    const existingTimer = timersRef.current.get(fieldId)
    if (existingTimer) {
      clearTimeout(existingTimer)
    }

    setHighlightedFields((prev) => {
      const next = new Set(prev)
      next.add(fieldId)
      return next
    })

    const timer = setTimeout(() => {
      setHighlightedFields((prev) => {
        const next = new Set(prev)
        next.delete(fieldId)
        return next
      })
      timersRef.current.delete(fieldId)
    }, highlightDurationMs)

    timersRef.current.set(fieldId, timer)
  }, [highlightDurationMs])

  const isHighlighted = useCallback((fieldId: string): boolean => {
    return highlightedFields.has(fieldId)
  }, [highlightedFields])

  const clearHighlight = useCallback((fieldId: string) => {
    const existingTimer = timersRef.current.get(fieldId)
    if (existingTimer) {
      clearTimeout(existingTimer)
      timersRef.current.delete(fieldId)
    }

    setHighlightedFields((prev) => {
      const next = new Set(prev)
      next.delete(fieldId)
      return next
    })
  }, [])

  const clearAllHighlights = useCallback(() => {
    timersRef.current.forEach((timer) => clearTimeout(timer))
    timersRef.current.clear()
    setHighlightedFields(new Set())
  }, [])

  return {
    highlightField,
    isHighlighted,
    clearHighlight,
    clearAllHighlights,
    highlightedFields,
  }
}
