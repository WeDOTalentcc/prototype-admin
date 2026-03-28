"use client"

import { useState, useEffect, useCallback, useRef, useMemo } from "react"
import { Brain, RefreshCw, AlertCircle } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface ExperienceHighlightCardProps {
  candidate: {
    id: string
    name: string
    current_title?: string
    currentTitle?: string
    current_company?: string
    currentCompany?: string
    location_city?: string
    locationCity?: string
    location_state?: string
    locationState?: string
    location_country?: string
    locationCountry?: string
    years_of_experience?: number
    yearsOfExperience?: number
    technical_skills?: string[]
    technicalSkills?: string[]
    work_history?: any[]
    workHistory?: any[]
  }
  companyId?: string
}

interface HighlightData {
  id: string
  candidate_id: string
  highlight_text: string
  generated_at: string
  expires_at: string
  is_cached: boolean
  model_used: string
}

export function ExperienceHighlightCard({ candidate, companyId = "demo_company" }: ExperienceHighlightCardProps) {
  const [highlight, setHighlight] = useState<HighlightData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fetchedRef = useRef<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const currentTitle = candidate.current_title || candidate.currentTitle
  const currentCompany = candidate.current_company || candidate.currentCompany
  const locationCity = candidate.location_city || candidate.locationCity
  const locationState = candidate.location_state || candidate.locationState
  const locationCountry = candidate.location_country || candidate.locationCountry
  const yearsOfExperience = candidate.years_of_experience || candidate.yearsOfExperience
  const technicalSkills = useMemo(
    () => candidate.technical_skills || candidate.technicalSkills || [],
    [candidate.technical_skills, candidate.technicalSkills]
  )
  const workHistory = useMemo(
    () => candidate.work_history || candidate.workHistory || [],
    [candidate.work_history, candidate.workHistory]
  )

  const location = [locationCity, locationState, locationCountry]
    .filter(Boolean)
    .join(", ")

  const fetchOrGenerateHighlight = useCallback(async (forceRegenerate = false) => {
    if (!candidate?.id) return

    if (!forceRegenerate && fetchedRef.current === candidate.id) return

    if (abortRef.current) {
      abortRef.current.abort()
    }
    const controller = new AbortController()
    abortRef.current = controller

    if (forceRegenerate) {
      setIsRegenerating(true)
    } else {
      setIsLoading(true)
    }
    setError(null)

    try {
      if (!forceRegenerate) {
        const cacheResponse = await fetch(
          `/api/backend-proxy/experience-highlights/${candidate.id}?company_id=${companyId}`,
          { signal: controller.signal }
        )
        
        if (cacheResponse.ok) {
          const data = await cacheResponse.json()
          setHighlight(data)
          setIsLoading(false)
          fetchedRef.current = candidate.id
          return
        }
      }

      const generateResponse = await fetch(
        `/api/backend-proxy/experience-highlights/generate?company_id=${companyId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            candidate_id: candidate.id,
            candidate_name: candidate.name,
            current_title: currentTitle,
            current_company: currentCompany,
            location: location,
            years_of_experience: yearsOfExperience,
            technical_skills: technicalSkills,
            work_history: workHistory,
            force_regenerate: forceRegenerate,
          }),
          signal: controller.signal,
        }
      )

      if (!generateResponse.ok) {
        throw new Error('Failed to generate highlight')
      }

      const data = await generateResponse.json()
      setHighlight(data)
      fetchedRef.current = candidate.id
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      setError('Não foi possível gerar o resumo')
    } finally {
      setIsLoading(false)
      setIsRegenerating(false)
    }
  }, [candidate?.id, candidate?.name, currentTitle, currentCompany, location, yearsOfExperience, technicalSkills, workHistory, companyId])

  useEffect(() => {
    if (candidate?.id && fetchedRef.current !== candidate.id) {
      fetchOrGenerateHighlight()
    }

    return () => {
      if (abortRef.current) {
        abortRef.current.abort()
      }
    }
  }, [candidate?.id, fetchOrGenerateHighlight])

  const handleRegenerate = () => {
    fetchedRef.current = null
    fetchOrGenerateHighlight(true)
  }

  if (!candidate?.id) {
    return null
  }

  if (isLoading) {
    return (
      <Card className="bg-white border border-gray-100 p-4 mb-4">
        <div className="flex items-start gap-3">
          <Skeleton className="h-5 w-5 rounded-full flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        </div>
      </Card>
    )
  }

  if (error && !highlight) {
    return (
      <Card className="bg-white border border-gray-100 p-4 mb-4">
        <div className="flex items-center gap-3 text-gray-500">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-status-warning" />
          <span className="text-sm">{error}</span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              fetchedRef.current = null
              fetchOrGenerateHighlight()
            }}
            className="ml-auto text-xs"
          >
            Tentar novamente
          </Button>
        </div>
      </Card>
    )
  }

  if (!highlight) {
    return null
  }

  const formatGeneratedDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
    } catch {
      return ''
    }
  }

  return (
    <Card className="bg-white border border-gray-100 p-3 mb-4">
      <div className="flex items-start gap-2">
        <Brain className="h-4 w-4 text-wedo-cyan flex-shrink-0 mt-0.5" />
        <p className="text-xs font-medium text-gray-800 leading-relaxed flex-1">
          {highlight.highlight_text}
        </p>
      </div>
      <div className="flex items-center justify-between mt-2">
        <p className="text-micro text-gray-400">
          Gerado pela LIA em {formatGeneratedDate(highlight.generated_at)}
        </p>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRegenerate}
                disabled={isRegenerating}
                className="h-5 w-5 p-0 text-gray-400 hover:text-gray-900 dark:hover:text-gray-50"
              >
                <RefreshCw className={`h-3 w-3 ${isRegenerating ? 'animate-spin' : ''}`} />
              </Button>
            </TooltipTrigger>
            <TooltipContent className="text-xs py-1 px-2">
              <p className="text-micro">Regenerar resumo</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </Card>
  )
}
