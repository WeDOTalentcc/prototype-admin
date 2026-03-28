"use client"

import React, { useState, useEffect, useCallback, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { 
  Search, Loader2, CheckCircle2, AlertCircle, 
  Globe, FileText, Brain, RefreshCw, Edit, X
} from "lucide-react"
import { CultureProfilePreview, CultureProfile } from "./CultureProfilePreview"
import { textStyles } from "@/lib/design-tokens"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

interface CultureAnalyzerProps {
  websiteUrl: string
  linkedinUrl?: string
  companyId: string
  onAnalysisComplete: (data: CultureProfile) => void
  existingProfile?: CultureProfile | null
  onManualEdit?: () => void
}

type AnalysisStatus = "idle" | "starting" | "running" | "completed" | "failed" | "cached"

interface JobStatus {
  job_id: string
  status: string
  progress: number
  current_step: string | null
  pages_discovered: number
  pages_scraped: number
  error_message: string | null
  result_profile_id: string | null
}

const PROGRESS_STEPS = [
  { key: "connecting", label: "Conectando", icon: Globe, minProgress: 0, maxProgress: 15 },
  { key: "discovering", label: "Descobrindo páginas", icon: Globe, minProgress: 15, maxProgress: 35 },
  { key: "reading", label: "Lendo conteúdo", icon: FileText, minProgress: 35, maxProgress: 60 },
  { key: "analyzing", label: "LIA analisando", icon: Brain, minProgress: 60, maxProgress: 95 },
  { key: "completed", label: "Concluído", icon: Brain, minProgress: 95, maxProgress: 100 }
]

const PROGRESS_MESSAGES = [
  { minProgress: 0, maxProgress: 10, messages: ["Iniciando conexão...", "Preparando análise..."] },
  { minProgress: 10, maxProgress: 20, messages: ["Conectando ao website...", "Acessando servidor..."] },
  { minProgress: 20, maxProgress: 35, messages: ["Descobrindo páginas relevantes...", "Mapeando estrutura do site..."] },
  { minProgress: 35, maxProgress: 50, messages: ["Extraindo conteúdo das páginas...", "Lendo informações da empresa..."] },
  { minProgress: 50, maxProgress: 65, messages: ["Processando textos com IA...", "Identificando missão e visão..."] },
  { minProgress: 65, maxProgress: 80, messages: ["Analisando cultura organizacional...", "Identificando valores..."] },
  { minProgress: 80, maxProgress: 95, messages: ["Mapeando perfil Big Five...", "Finalizando análise..."] },
  { minProgress: 95, maxProgress: 100, messages: ["Concluído!", "Análise pronta!"] },
]

function normalizeUrl(url: string): string {
  if (!url) return url
  let normalized = url.trim()
  normalized = normalized.replace(/^httsp:\/\//i, 'https://')
  normalized = normalized.replace(/^htts:\/\//i, 'https://')
  normalized = normalized.replace(/^htpp:\/\//i, 'http://')
  normalized = normalized.replace(/^htp:\/\//i, 'http://')
  normalized = normalized.replace(/^htpps:\/\//i, 'https://')
  if (!normalized.match(/^https?:\/\//i)) {
    normalized = 'https://' + normalized
  }
  return normalized
}

export function CultureAnalyzer({
  websiteUrl,
  linkedinUrl,
  companyId,
  onAnalysisComplete,
  existingProfile,
  onManualEdit
}: CultureAnalyzerProps) {
  const [status, setStatus] = useState<AnalysisStatus>(existingProfile ? "completed" : "idle")
  const [jobId, setJobId] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [displayProgress, setDisplayProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState<string | null>(null)
  const [pagesInfo, setPagesInfo] = useState({ discovered: 0, scraped: 0 })
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [cultureProfile, setCultureProfile] = useState<CultureProfile | null>(existingProfile || null)
  const [showErrorDialog, setShowErrorDialog] = useState(false)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const progressAnimationRef = useRef<NodeJS.Timeout | null>(null)
  const isAnalyzingRef = useRef(false)

  useEffect(() => {
    if (existingProfile) {
      setCultureProfile({
        ...existingProfile,
        core_competencies: existingProfile.core_competencies || []
      })
      setStatus("completed")
    }
  }, [existingProfile])

  useEffect(() => {
    if (status === "running" && isAnalyzingRef.current) {
      progressAnimationRef.current = setInterval(() => {
        setDisplayProgress(prev => {
          const targetProgress = progress
          if (prev >= 95) return prev
          
          const progressRange = PROGRESS_MESSAGES.find(
            range => prev >= range.minProgress && prev < range.maxProgress
          )
          
          const increment = prev < 30 ? 2 : prev < 60 ? 1.5 : prev < 85 ? 0.8 : 0.3
          const newProgress = Math.min(prev + increment, targetProgress > prev ? targetProgress : Math.min(prev + increment, 90))
          
          if (progressRange) {
            const randomMessage = progressRange.messages[Math.floor(Math.random() * progressRange.messages.length)]
            setCurrentStep(randomMessage)
          }
          
          return newProgress
        })
      }, 800)
      
      return () => {
        if (progressAnimationRef.current) {
          clearInterval(progressAnimationRef.current)
        }
      }
    }
  }, [status, progress])

  useEffect(() => {
    if (status === "completed" || status === "failed") {
      if (progressAnimationRef.current) {
        clearInterval(progressAnimationRef.current)
        progressAnimationRef.current = null
      }
      if (status === "completed") {
        setDisplayProgress(100)
      }
    }
  }, [status])

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  const fetchCultureProfile = useCallback(async (resultProfileId?: string) => {
    try {
      const response = await fetch(`/api/backend-proxy/company/culture-profile?company_id=${companyId}`)
      if (response.ok) {
        const data = await response.json()
        if (!data.notFound) {
          const normalizedProfile = {
            ...data,
            core_competencies: data.core_competencies || []
          }
          setCultureProfile(normalizedProfile)
          onAnalysisComplete(normalizedProfile)
          return normalizedProfile
        }
      }
    } catch (error) {
    }
    return null
  }, [companyId, onAnalysisComplete])

  const pollJobStatus = useCallback(async () => {
    if (!jobId) return

    try {
      const response = await fetch(`/api/backend-proxy/company/culture-profile/status/${jobId}`)
      if (!response.ok) {
        throw new Error("Failed to fetch job status")
      }

      const data: JobStatus = await response.json()
      
      setProgress(data.progress)
      setPagesInfo({ discovered: data.pages_discovered, scraped: data.pages_scraped })

      if (data.status === "completed") {
        stopPolling()
        setStatus("completed")
        await fetchCultureProfile(data.result_profile_id || undefined)
      } else if (data.status === "failed") {
        stopPolling()
        setStatus("failed")
        setErrorMessage(data.error_message || "Análise falhou")
        setShowErrorDialog(true)
      }
    } catch (error) {
    }
  }, [jobId, stopPolling, fetchCultureProfile])

  useEffect(() => {
    if (status === "running" && jobId) {
      pollingRef.current = setInterval(pollJobStatus, 2000)
      pollJobStatus()
    }

    return () => {
      stopPolling()
    }
  }, [status, jobId, pollJobStatus, stopPolling])

  const startAnalysis = async (forceRefresh: boolean = false) => {
    if (!websiteUrl) {
      setErrorMessage("URL do website é obrigatória")
      return
    }

    setStatus("starting")
    setErrorMessage(null)
    setProgress(0)
    setDisplayProgress(0)
    setCurrentStep("Iniciando análise...")
    setCultureProfile(null)
    isAnalyzingRef.current = true

    try {
      setStatus("running")
      setProgress(5)
      setDisplayProgress(5)
      setCurrentStep("Conectando ao website...")

      const normalizedWebsiteUrl = normalizeUrl(websiteUrl)
      const normalizedLinkedinUrl = linkedinUrl ? normalizeUrl(linkedinUrl) : undefined
      
      const response = await fetch("/api/backend-proxy/company/culture-profile/analyze-direct", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          website_url: normalizedWebsiteUrl,
          linkedin_url: normalizedLinkedinUrl,
          company_id: companyId
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || "Falha ao analisar cultura")
      }

      const data = await response.json()
      
      isAnalyzingRef.current = false
      setProgress(100)
      setDisplayProgress(100)
      setCurrentStep("Análise concluída!")
      
      const profile: CultureProfile = {
        id: companyId,
        company_id: companyId,
        mission: data.mission,
        vision: data.vision,
        values: data.values || [],
        evp_bullets: data.evp_bullets || [],
        core_competencies: data.core_competencies || [],
        culture_description: data.culture_description,
        openness_score: data.big_five?.openness || 50,
        conscientiousness_score: data.big_five?.conscientiousness || 50,
        extraversion_score: data.big_five?.extraversion || 50,
        agreeableness_score: data.big_five?.agreeableness || 50,
        stability_score: data.big_five?.stability || 50,
        linkedin_url: data.linkedin_url,
        analyzed_pages: data.analyzed_pages || [],
        confidence_score: data.confidence_score || 0.7,
        source: "auto",
        last_analysis_at: new Date().toISOString(),
        industry: data.industry,
        employee_count: data.employee_count,
        company_size: data.company_size,
        headquarters: data.headquarters,
        locations: data.locations || [],
        founded_year: data.founded_year,
        work_model: data.work_model,
        growth_opportunities: data.growth_opportunities,
        team_dynamics: data.team_dynamics,
        leadership_style: data.leadership_style,
        dei_initiatives: data.dei_initiatives,
        sustainability: data.sustainability,
        social_impact: data.social_impact,
        tech_stack: data.tech_stack || [],
        engineering_culture: data.engineering_culture,
      }
      
      setCultureProfile(profile)
      onAnalysisComplete(profile)
      setStatus("completed")
    } catch (error) {
      isAnalyzingRef.current = false
      setStatus("failed")
      setErrorMessage(error instanceof Error ? error.message : "Erro ao analisar cultura. Tente novamente.")
      setShowErrorDialog(true)
    }
  }

  const handleAccept = (profile: CultureProfile) => {
    onAnalysisComplete(profile)
  }

  const handleSaveAdjustments = async (profile: CultureProfile) => {
    try {
      const response = await fetch(`/api/backend-proxy/company/culture-profile?company_id=${companyId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mission: profile.mission,
          vision: profile.vision,
          values: profile.values,
          evp_bullets: profile.evp_bullets,
          core_competencies: profile.core_competencies || [],
          openness_score: profile.openness_score,
          conscientiousness_score: profile.conscientiousness_score,
          extraversion_score: profile.extraversion_score,
          agreeableness_score: profile.agreeableness_score,
          stability_score: profile.stability_score
        })
      })

      if (response.ok) {
        const updatedProfile = await response.json()
        setCultureProfile(updatedProfile)
        onAnalysisComplete(updatedProfile)
      }
    } catch (error) {
    }
  }

  const handleReanalyze = () => {
    startAnalysis(true)
  }

  const getCurrentStepIndex = () => {
    const p = displayProgress
    if (p < 15) return 0
    if (p < 35) return 1
    if (p < 60) return 2
    if (p < 95) return 3
    return 4
  }

  if (status === "idle") {
    return (
      <Card className="rounded-2xl bg-gray-50/50 dark:bg-gray-900/20 backdrop-blur-sm border border-gray-200 dark:border-gray-700">
        <CardContent className="p-6 text-center">
          <div 
            className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4 bg-gray-900 dark:bg-gray-50"
          >
            <Brain className="w-7 h-7 text-white" />
          </div>
          <h3 className={`${textStyles.h3} mb-2`}>
            Análise de Cultura Organizacional
          </h3>
          <p className={`${textStyles.description} mb-4 max-w-md mx-auto`}>
            A LIA pode analisar o website da empresa para identificar automaticamente 
            missão, visão, valores e o perfil cultural organizacional.
          </p>
          <Button
            onClick={() => startAnalysis(false)}
            disabled={!websiteUrl}
            className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            <Brain className="w-4 h-4 text-wedo-cyan" />
            Analisar Empresa com IA
          </Button>
          {!websiteUrl && (
            <p className={`${textStyles.caption} text-status-warning dark:text-status-warning mt-3`}>
              Informe o website da empresa acima para habilitar a análise
            </p>
          )}
        </CardContent>
      </Card>
    )
  }

  if (status === "starting" || status === "running") {
    const currentStepIndex = getCurrentStepIndex()
    const roundedProgress = Math.round(displayProgress)
    const isLiaStep = (stepKey: string) => stepKey === "analyzing" || stepKey === "completed"

    return (
      <Card className="rounded-2xl bg-gray-50/50 dark:bg-gray-900/20 backdrop-blur-sm border border-gray-200 dark:border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 rounded-md flex items-center justify-center relative overflow-hidden bg-gray-900 dark:bg-gray-50">
              <Loader2 className="w-6 h-6 text-white animate-spin" />
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
            </div>
            <div className="flex-1">
              <h3 className={textStyles.h3}>
                Analisando {websiteUrl}
              </h3>
              <p className={`${textStyles.bodySmall} text-gray-600 dark:text-gray-400 transition-all duration-300`}>
                {currentStep || "Iniciando..."}
              </p>
            </div>
            <div className="text-right">
              <span className="text-2xl font-bold tabular-nums text-gray-600 dark:text-gray-400">
                {roundedProgress}%
              </span>
            </div>
          </div>

          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-6 overflow-hidden shadow-inner">
            <div
              className="h-3 rounded-full transition-all duration-700 ease-out relative bg-gray-900 dark:bg-gray-50"
              style={{ width: `${displayProgress}%` }}
            >
              <div 
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent"
                style={{
                  animation: 'shimmer 2s infinite',
                  backgroundSize: '200% 100%',
                }}
              />
              <div className="absolute right-0 top-0 bottom-0 w-2 bg-white/50 rounded-full blur-sm" />
            </div>
          </div>

          <div className="grid grid-cols-5 gap-1.5">
            {PROGRESS_STEPS.map((step, index) => {
              const StepIcon = step.icon
              const isActive = index === currentStepIndex
              const isCompleted = index < currentStepIndex
              const isLia = isLiaStep(step.key)
              
              return (
                <div
                  key={step.key}
                  className={`flex flex-col items-center p-2 rounded-md transition-all duration-300 ${
                    isActive
                      ? isLia 
                        ? "bg-gray-100 dark:bg-gray-800 ring-2 ring-gray-900/20 scale-105"
                        : "bg-gray-100 dark:bg-gray-800 ring-2 ring-gray-400 scale-105"
                      : isCompleted
                        ? "bg-status-success/10 dark:bg-status-success/30"
                        : "bg-gray-50 dark:bg-gray-800/50 opacity-60"
                  }`}
                >
                  <div 
                    className={`w-7 h-7 rounded-md flex items-center justify-center mb-1.5 transition-all duration-300 ${
                      isCompleted
                        ? "bg-status-success text-white"
                        : isActive
                          ? isLia
                            ? "bg-gray-900 dark:bg-gray-50 text-white"
                            : "bg-gray-700 dark:bg-gray-300 text-white dark:text-gray-900"
                          : "bg-gray-200 dark:bg-gray-700 text-gray-500"
                    }`}
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4" />
                    ) : isActive ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <StepIcon className="w-3.5 h-3.5" />
                    )}
                  </div>
                  <span 
                    className={`${textStyles.caption} text-center leading-tight ${
                      isActive
                        ? isLia
                          ? "text-wedo-cyan-dark dark:text-gray-400"
                          : "text-gray-700 dark:text-gray-300"
                        : isCompleted
                          ? "text-status-success dark:text-status-success"
                          : "text-gray-400 dark:text-gray-500"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
              )
            })}
          </div>

          {pagesInfo.scraped > 0 && (
            <div className={`mt-4 flex items-center justify-center gap-4 ${textStyles.caption} text-gray-500 dark:text-gray-400`}>
              <span className="flex items-center gap-1">
                <Globe className="w-3.5 h-3.5" />
                {pagesInfo.discovered} páginas encontradas
              </span>
              <span className="flex items-center gap-1">
                <FileText className="w-3.5 h-3.5" />
                {pagesInfo.scraped} páginas analisadas
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  if (status === "failed") {
    return (
      <>
        <AlertDialog open={showErrorDialog} onOpenChange={setShowErrorDialog}>
          <AlertDialogContent className="max-w-md">
            <AlertDialogHeader>
              <AlertDialogTitle className={`flex items-center gap-2 text-status-error ${textStyles.h3}`}>
                <AlertCircle className="w-5 h-5" />
                Não foi possível analisar automaticamente
              </AlertDialogTitle>
              <div className={`${textStyles.body} text-gray-600 space-y-3`}>
                <span className="block">
                  {errorMessage || "O website não pôde ser analisado automaticamente."}
                </span>
                <span className={`block ${textStyles.caption} bg-status-warning/10 border border-status-warning/30 rounded-md p-3 text-status-warning`}>
                  <strong>Por que isso acontece?</strong><br />
                  Sites modernos de grandes empresas frequentemente têm proteção anti-bot ou carregamento dinâmico (JavaScript/SPA), 
                  o que impede a extração automática de dados.
                </span>
                <span className={`block ${textStyles.caption}`}>
                  Você pode preencher manualmente as informações de cultura da empresa ou tentar novamente.
                </span>
              </div>
            </AlertDialogHeader>
            <AlertDialogFooter className="flex gap-2">
              <AlertDialogCancel 
                onClick={() => startAnalysis(true)}
                className="gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Tentar Novamente
              </AlertDialogCancel>
              {onManualEdit && (
                <AlertDialogAction 
                  onClick={() => {
                    setShowErrorDialog(false)
                    onManualEdit()
                  }}
                  className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                >
                  <Edit className="w-4 h-4" />
                  Preencher Manualmente
                </AlertDialogAction>
              )}
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <Card className="rounded-2xl border border-status-error/30 dark:border-status-error/30 bg-status-error/10/50 dark:bg-status-error/20 backdrop-blur-sm">
          <CardContent className="p-6 text-center">
            <div className="w-14 h-14 rounded-2xl bg-status-error/15 dark:bg-status-error/50 flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-7 h-7 text-status-error" />
            </div>
            <h3 className={`${textStyles.h3} mb-2`}>
              Análise Falhou
            </h3>
            <p className={`${textStyles.caption} text-status-error dark:text-status-error mb-2`}>
              {errorMessage || "Não foi possível analisar o website. Verifique a URL e tente novamente."}
            </p>
            <p className={`${textStyles.caption} text-gray-500 mb-4`}>
              Sites com proteção anti-bot ou carregamento dinâmico podem não ser analisados automaticamente.
            </p>
            <div className="flex gap-2 justify-center">
              <Button
                onClick={() => startAnalysis(true)}
                variant="outline"
                className="gap-2 border-status-error/30 text-status-error hover:bg-status-error/10"
              >
                <RefreshCw className="w-4 h-4" />
                Tentar Novamente
              </Button>
              {onManualEdit && (
                <Button
                  onClick={onManualEdit}
                  className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                >
                  <Edit className="w-4 h-4" />
                  Preencher Manualmente
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </>
    )
  }

  if ((status === "completed" || status === "cached") && cultureProfile) {
    return (
      <CultureProfilePreview
        profile={cultureProfile}
        onAccept={handleAccept}
        onSaveAdjustments={handleSaveAdjustments}
        onReanalyze={handleReanalyze}
      />
    )
  }

  return null
}
