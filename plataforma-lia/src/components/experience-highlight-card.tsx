"use client"

import { useMemo } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useCurrentCompany } from "@/hooks/company/use-current-company"
import { Brain, RefreshCw, AlertCircle, Sparkles } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { formatDate } from "@/lib/format-utils"
import { CANDIDATE_AI_QUERY_KEYS } from "@/hooks/candidates/candidate-ai-query-keys"

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
    work_history?: Record<string, unknown>[]
    workHistory?: Record<string, unknown>[]
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

export function ExperienceHighlightCard({ candidate, companyId: companyIdProp }: ExperienceHighlightCardProps) {
  const { companyId: currentCompanyId } = useCurrentCompany()
  const companyId = companyIdProp || currentCompanyId || ''
  const hasCompany = Boolean(companyId)
  const candidateId = candidate?.id || ''
  const queryClient = useQueryClient()

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

  // GET do cache — NUNCA auto-gera (gerar dispara LLM e causa o storm de 502).
  // 404 = "ainda não gerado" → resolve para null, não é erro.
  const {
    data: highlight,
    isLoading,
    isError,
    refetch,
  } = useQuery<HighlightData | null>({
    queryKey: CANDIDATE_AI_QUERY_KEYS.experienceHighlight(candidateId, companyId),
    queryFn: async () => {
      const res = await fetch(
        `/api/backend-proxy/experience-highlights/${candidateId}?company_id=${encodeURIComponent(companyId)}`
      )
      if (res.status === 404) return null
      if (!res.ok) throw new Error('Falha ao carregar resumo')
      return res.json()
    },
    enabled: Boolean(candidateId) && hasCompany,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  // Geração/regeneração é user-initiated (CTA ou botão regenerar).
  const generateMutation = useMutation<HighlightData, Error, { force: boolean }>({
    mutationFn: async ({ force }) => {
      const res = await fetch(
        `/api/backend-proxy/experience-highlights/generate?company_id=${encodeURIComponent(companyId)}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_id: candidateId,
            candidate_name: candidate.name,
            current_title: currentTitle,
            current_company: currentCompany,
            location,
            years_of_experience: yearsOfExperience,
            technical_skills: technicalSkills,
            work_history: workHistory,
            force_regenerate: force,
          }),
        }
      )
      if (!res.ok) throw new Error('Não foi possível gerar o resumo')
      return res.json()
    },
    onSuccess: (data) => {
      queryClient.setQueryData(
        CANDIDATE_AI_QUERY_KEYS.experienceHighlight(candidateId, companyId),
        data
      )
    },
  })

  if (!candidateId) return null

  const isGenerating = generateMutation.isPending
  const hasValidHighlight = Boolean(highlight?.highlight_text?.trim())

  // Carregando o cache ou gerando.
  if (isLoading || isGenerating) {
    return (
      <Card className="bg-lia-bg-primary border border-lia-border-subtle p-4 mb-4">
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

  // Erro ao carregar o cache (não-404) ou ao gerar — falha alto, com retry.
  if ((isError || generateMutation.isError) && !hasValidHighlight) {
    const retry = isError
      ? () => refetch()
      : () => generateMutation.mutate({ force: false })
    return (
      <Card className="bg-lia-bg-primary border border-lia-border-subtle p-4 mb-4">
        <div className="flex items-center gap-3 text-lia-text-secondary">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-status-warning" />
          <span className="text-sm">Não foi possível gerar o resumo</span>
          <Button variant="ghost" size="sm" onClick={retry} className="ml-auto text-xs">
            Tentar novamente
          </Button>
        </div>
      </Card>
    )
  }

  // Ainda não gerado (404/vazio) — CTA explícito, sem auto-gerar.
  if (!hasValidHighlight) {
    return (
      <Card className="bg-lia-bg-primary border border-lia-border-subtle p-3 mb-4">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-wedo-cyan flex-shrink-0" />
          <span className="text-xs text-lia-text-secondary flex-1">
            Resumo do perfil ainda não gerado
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => generateMutation.mutate({ force: false })}
            className="h-6 gap-1 text-xs text-wedo-cyan hover:text-wedo-cyan"
          >
            <Sparkles className="h-3 w-3" />
            Gerar resumo
          </Button>
        </div>
      </Card>
    )
  }

  const generatedLabel = formatDate(highlight!.generated_at)

  return (
    <Card className="bg-lia-bg-primary border border-lia-border-subtle p-3 mb-4">
      <div className="flex items-start gap-2">
        <Brain className="h-4 w-4 text-wedo-cyan flex-shrink-0 mt-0.5" />
        <p className="text-xs font-medium text-lia-text-primary leading-relaxed flex-1">
          {highlight!.highlight_text}
        </p>
      </div>
      <div className="flex items-center justify-between mt-2">
        {generatedLabel ? (
          <p className="text-micro text-lia-text-secondary">
            Gerado pela LIA em {generatedLabel}
          </p>
        ) : (
          <span />
        )}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => generateMutation.mutate({ force: true })}
                disabled={isGenerating}
                className="h-5 w-5 p-0 text-lia-text-secondary hover:text-lia-text-primary"
              >
                <RefreshCw className={`h-3 w-3 ${isGenerating ? 'animate-spin motion-reduce:animate-none' : ''}`} />
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
