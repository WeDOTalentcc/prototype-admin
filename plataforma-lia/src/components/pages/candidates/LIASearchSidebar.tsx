"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { LIAIcon } from "@/components/ui/lia-icon"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { ProactiveInsightCard, type SearchAnalytics } from "@/components/proactive-insight-card"
import { CalibrationCard, type CalibrationCandidate } from "@/components/calibration-card"
import { LiaSearchQueriesGuide } from "@/components/ui/lia-search-queries-guide"
import {
  Brain, X, Maximize2, PanelLeftClose,
  Search, Loader2,
  Paperclip, Mic,
  Lightbulb, Users, Code, Filter, Check
} from "lucide-react"
import { LIASearchSidebarChat, LIASearchSidebarInput } from './lia-sidebar'

type SearchTab = 'ia-natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'

interface ApiExperience {
  company_info?: { name?: string; location?: string; is_startup?: boolean }
  company_roles?: { title?: string; start_date?: string; end_date?: string; description?: string }[]
  company?: string
  title?: string
  start_date?: string
  end_date?: string
  duration?: string
  location?: string
  description?: string
}

interface ApiEducation {
  school?: string
  degree?: string
  field_of_study?: string
  start_date?: string
  end_date?: string
}

interface ApiCandidate {
  id?: string
  name?: string
  email?: string
  phone?: string
  headline?: string
  current_title?: string
  current_company?: string
  location?: string
  linkedin_url?: string
  avatar_url?: string
  picture_url?: string
  skills?: string[]
  seniority_level?: string
  years_experience?: number
  total_experience_years?: number
  match_score?: number
  source?: string
  has_email?: boolean
  has_phone?: boolean
  is_opentowork?: boolean
  is_decision_maker?: boolean
  is_top_universities?: boolean
  is_startup?: boolean
  company_info?: { is_startup?: boolean }
  expertise?: string
  outreach_message?: string
  experiences?: ApiExperience[]
  education?: ApiEducation[]
}

type ChatMessage = {
  id: string
  type: 'user' | 'lia' | 'proactive_insight' | 'calibration'
  content: string
  timestamp: Date
  searchResults?: {
    localCount: number
    globalCount: number
    query: string
  }
  analytics?: SearchAnalytics
  candidates?: CalibrationCandidate[]
  metadata?: {
    action_executed?: boolean
    action_result?: Record<string, unknown>
    action_type?: string
    needs_confirmation?: boolean
    needs_params?: boolean
    pending_action_id?: string
    conversation_id?: string
  }
}

interface LIASearchSidebarProps {
  isLiaSuperChat: boolean
  setIsLiaSuperChat: (v: boolean) => void
  liaWidth: number
  setLiaWidth: (v: number) => void
  isResizingLIA: boolean
  setIsResizingLIA: (v: boolean) => void
  activeSearchTab: SearchTab
  setActiveSearchTab: (tab: SearchTab) => void
  liaPromptValue: string
  setLiaPromptValue: React.Dispatch<React.SetStateAction<string>>
  chatMessages: ChatMessage[]
  setChatMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>
  searchResults: {
    query: string
    isLoading: boolean
    localCount: number
    globalCount: number
    showGlobalResults: boolean
    globalDismissed: boolean
    local: unknown[]
    global: unknown[]
  }
  setSearchResults: React.Dispatch<React.SetStateAction<LIASearchSidebarProps['searchResults']>>
  currentSearchSource: string
  searchSource: string
  pearchSearchOptions: { searchType: string }
  activeSearchFilters: Record<string, Record<string, unknown>>
  setActiveSearchFilters: (v: Record<string, Record<string, unknown>>) => void
  showTableFiltersPanel: boolean
  setShowTableFiltersPanel: (v: boolean) => void
  isCreatingArchetype: boolean
  setIsCreatingArchetype: (v: boolean) => void
  archetypeCreationStep: string
  setArchetypeCreationStep: (v: string) => void
  setNewArchetypeData: (v: { name: string; description: string; query: string; emoji: string }) => void
  setShowSaveAsArchetypeModal: (v: boolean) => void
  setShowGlobalExpansionConfirm: (v: boolean) => void
  selectedCandidatesForBatch: Set<string>
  setCandidates: (v: unknown[]) => void
  setHasSearchResults: (v: boolean) => void
  setSearchResultsCount: (v: number) => void
  setLocalResultsCount: (v: number) => void
  setPearchResultsCount: (v: number) => void
  setShowSearchResults: (v: boolean) => void
  setDisplayedResultsCount: (v: number) => void
  onLIAChatMessage: (message: string) => void
  onAICommand: (command: string) => void
  onQuickAction: (actionId: string, actionType: string) => void
  onCalibrationLike: (candidateId: string) => void
  onCalibrationDislike: (candidateId: string, reason?: string) => void
  onClose: () => void
  chatScrollRef: React.RefObject<HTMLDivElement>
}

export function LIASearchSidebar({
  isLiaSuperChat,
  setIsLiaSuperChat,
  liaWidth,
  setLiaWidth,
  isResizingLIA,
  setIsResizingLIA,
  activeSearchTab,
  setActiveSearchTab,
  liaPromptValue,
  setLiaPromptValue,
  chatMessages,
  setChatMessages,
  searchResults,
  setSearchResults,
  currentSearchSource,
  searchSource,
  pearchSearchOptions,
  activeSearchFilters,
  setActiveSearchFilters,
  showTableFiltersPanel,
  setShowTableFiltersPanel,
  isCreatingArchetype,
  setIsCreatingArchetype,
  archetypeCreationStep,
  setArchetypeCreationStep,
  setNewArchetypeData,
  setShowSaveAsArchetypeModal,
  setShowGlobalExpansionConfirm,
  selectedCandidatesForBatch,
  setCandidates,
  setHasSearchResults,
  setSearchResultsCount,
  setLocalResultsCount,
  setPearchResultsCount,
  setShowSearchResults,
  setDisplayedResultsCount,
  onLIAChatMessage,
  onAICommand,
  onQuickAction,
  onCalibrationLike,
  onCalibrationDislike,
  onClose,
  chatScrollRef,
}: LIASearchSidebarProps) {
  const [superChatWidth, setSuperChatWidth] = useState(600)
  const [jobDescriptionText, setJobDescriptionText] = useState("")
  const [booleanSearchValue, setBooleanSearchValue] = useState("")
  const [similarProfileUrl, setSimilarProfileUrl] = useState("")
  const [isSearchingSimilar, setIsSearchingSimilar] = useState(false)
  const [isSearchingJD, setIsSearchingJD] = useState(false)
  const [extractedJDCriteria, setExtractedJDCriteria] = useState<{
    job_title?: string
    seniority?: string
    skills: string[]
    experience_years?: number
    location?: string
    languages: string[]
  } | null>(null)
  return (
    <div
      className={`transition-colors motion-reduce:transition-none duration-300 relative group ${isLiaSuperChat ? 'flex-1 z-10' : 'flex-shrink-0'}`}
      style={{width: isLiaSuperChat ? 'auto' : `${liaWidth}px`,
        maxWidth: isLiaSuperChat ? 'none' : `${liaWidth}px`}}
    >
      <Card className="h-full flex flex-col overflow-hidden border border-lia-border-default bg-white dark:bg-lia-bg-secondary">
        {/* Header do Prompt Expandido - Design Specs v3.1 */}
        <div className="flex-shrink-0 px-4 py-3 bg-white dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div
                className="w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0 bg-gray-50 dark:bg-lia-bg-primary"
              >
                <Brain className="w-6 h-6 text-wedo-cyan" strokeWidth={2.5} />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-semibold leading-tight truncate text-lia-text-primary dark:text-lia-text-primary">
                  Olá! Sou a Lia.
                </h3>
                <p className="text-xs leading-tight truncate mt-0.5 text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                  Posso criar vagas, buscar candidatos, analisar métricas e muito mais!
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {/* Botão Expandir/Retrair Superchat */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        if (isLiaSuperChat) {
                          setIsLiaSuperChat(false)
                        } else {
                          setIsLiaSuperChat(true)
                          setSuperChatWidth(Math.max(superChatWidth, 600))
                        }
                      }}
                      className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors motion-reduce:transition-none flex-shrink-0"
                    >
                      {isLiaSuperChat ? (
                        <PanelLeftClose className="w-4 h-4 text-lia-text-secondary" />
                      ) : (
                        <Maximize2 className="w-4 h-4 text-lia-text-tertiary" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-xs">{isLiaSuperChat ? 'Retrair chat' : 'Expandir para Superchat'}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              {/* Botão Fechar */}
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors motion-reduce:transition-none flex-shrink-0"
              >
                <X className="w-4 h-4 text-lia-text-tertiary" />
              </Button>
            </div>
          </div>
        </div>

        {/* Ações movidas para banner acima da tabela */}

        {/* Conteúdo das Abas */}
        <div className="flex-1 flex flex-col overflow-hidden mx-3 mb-3">

          {/* ABA 1: IA NATURAL - Chat Format */}
          {activeSearchTab === 'ia-natural' && (
            <div className="flex flex-col flex-1 min-h-0">
              <LIASearchSidebarChat
                chatScrollRef={chatScrollRef}
                searchResults={searchResults}
                setSearchResults={setSearchResults}
                currentSearchSource={currentSearchSource}
                chatMessages={chatMessages}
                setShowSaveAsArchetypeModal={setShowSaveAsArchetypeModal}
                setShowGlobalExpansionConfirm={setShowGlobalExpansionConfirm}
                onQuickAction={onQuickAction}
                onCalibrationLike={onCalibrationLike}
                onCalibrationDislike={onCalibrationDislike}
              />

              <LIASearchSidebarInput
                liaPromptValue={liaPromptValue}
                setLiaPromptValue={setLiaPromptValue}
                isCreatingArchetype={isCreatingArchetype}
                setIsCreatingArchetype={setIsCreatingArchetype}
                archetypeCreationStep={archetypeCreationStep}
                setArchetypeCreationStep={setArchetypeCreationStep}
                setNewArchetypeData={setNewArchetypeData}
                setShowSaveAsArchetypeModal={setShowSaveAsArchetypeModal}
                searchResults={searchResults}
                setChatMessages={setChatMessages}
                selectedCandidatesForBatch={selectedCandidatesForBatch}
                onLIAChatMessage={onLIAChatMessage}
                onAICommand={onAICommand}
              />
            </div>
          )}

          {/* Abas removidas: JOB DESCRIPTION, SIMILAR, BOOLEAN - funcionalidades movidas para página principal */}
          {activeSearchTab === 'job-description' && (
            <div className="space-y-4 overflow-y-auto flex-1 p-4">
              {/* Descrição */}
              <p className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                Cole sua descrição de vaga e a IA extrairá os critérios automaticamente
              </p>

              {/* Textarea Grande */}
              <div className="relative">
                <textarea
                  placeholder="Cole aqui a descrição da vaga completa..."
                  value={jobDescriptionText}
                  onChange={(e) => setJobDescriptionText(e.target.value)}
                  className="w-full h-48 p-4 pb-12 text-xs rounded-md border focus:outline-none transition-colors motion-reduce:transition-none resize-none bg-white dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary border border-lia-border-subtle"
                  onFocus={(e) => e.target.style.borderColor = 'var(--gray-200)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--gray-50)'}
                />
                {/* Botões de Anexo e Áudio */}
                <div className="absolute bottom-3 right-3 flex gap-2">
                  <button
                    type="button"
                    className="p-2 rounded-md hover:bg-gray-100 transition-colors motion-reduce:transition-none"
                    title="Anexar documento"
                    onClick={() => {
                      // TODO: Implementar upload de arquivo
                    }}
                  >
                    <Paperclip className="w-4 h-4 text-lia-text-primary" />
                  </button>
                  <button
                    type="button"
                    className="p-2 rounded-md hover:bg-gray-100 transition-colors motion-reduce:transition-none"
                    title="Gravar áudio"
                    onClick={() => {
                      // TODO: Implementar gravação de áudio
                    }}
                  >
                    <Mic className="w-4 h-4 text-lia-text-primary" />
                  </button>
                </div>
              </div>

              {/* Critérios Extraídos */}
              {extractedJDCriteria && (
                <div className="p-3 rounded-md border bg-wedo-cyan/[0.06] border-wedo-cyan/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">
                      Critérios Extraídos
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {extractedJDCriteria.job_title && (
                      <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary">
                        {extractedJDCriteria.job_title}
                      </span>
                    )}
                    {extractedJDCriteria.seniority && (
                      <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary">
                        {extractedJDCriteria.seniority}
                      </span>
                    )}
                    {extractedJDCriteria.skills.map((skill, idx) => (
                      <span key={idx} className="px-2 py-1 text-xs rounded-full bg-gray-100 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary">
                        {skill}
                      </span>
                    ))}
                    {extractedJDCriteria.experience_years && (
                      <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary">
                        {extractedJDCriteria.experience_years}+ anos
                      </span>
                    )}
                    {extractedJDCriteria.location && (
                      <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary">
                        {extractedJDCriteria.location}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Botão Extrair e Buscar */}
              <button
                className="w-full h-11 text-sm font-semibold flex items-center justify-center gap-2 rounded-md disabled:opacity-50"
                style={{backgroundColor: isSearchingJD ? 'var(--gray-400)' : 'var(--gray-950)',
                  color: 'var(--gray-50)'}}
                onClick={async () => {
                  if (jobDescriptionText.trim() && !isSearchingJD) {
                    setIsSearchingJD(true)
                    setExtractedJDCriteria(null)

                    const userMessage: ChatMessage = {
                      id: `user-jd-${Date.now()}`,
                      type: 'user',
                      content: `Buscar candidatos pela descrição da vaga:\n\n"${jobDescriptionText.substring(0, 200)}${jobDescriptionText.length > 200 ? '...' : ''}"`,
                      timestamp: new Date()
                    }
                    setChatMessages(prev => [...prev, userMessage])

                    try {
                      const response = await fetch('/api/backend-proxy/search/candidates/by-job-description', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                          job_description: jobDescriptionText.trim(),
                          limit: 20,
                          search_pearch: searchSource !== 'local',
                          pearch_type: pearchSearchOptions.searchType
                        })
                      })

                      if (!response.ok) throw new Error('Erro na busca')

                      const data = await response.json()

                      if (data.extracted_criteria) {
                        setExtractedJDCriteria({
                          job_title: data.extracted_criteria.job_title,
                          seniority: data.extracted_criteria.seniority,
                          skills: data.extracted_criteria.skills || [],
                          experience_years: data.extracted_criteria.experience_years,
                          location: data.extracted_criteria.location,
                          languages: data.extracted_criteria.languages || []
                        })
                      }

                      if (data.candidates && data.candidates.length > 0) {
                        const mappedCandidates = (data.candidates as ApiCandidate[]).map((c) => ({
                          id: c.id || `jd-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                          candidateId: c.id?.substring(0, 8).toUpperCase() || 'JD',
                          name: c.name || 'Nome não disponível',
                          email: c.email || '',
                          phone: c.phone || '',
                          current_title: c.headline || c.current_title || '',
                          current_company: c.current_company || '',
                          location: c.location || '',
                          linkedin_url: c.linkedin_url,
                          avatar_url: c.avatar_url || c.picture_url,
                          avatar: c.avatar_url,
                          technical_skills: c.skills || [],
                          skills: c.skills || [],
                          seniority_level: c.seniority_level,
                          years_of_experience: c.years_experience || c.total_experience_years,
                          experience: c.years_experience || c.total_experience_years || 0,
                          score: c.match_score ? Math.round(c.match_score * 25) : 75,
                          source: c.source || 'pearch',
                          has_email: c.has_email ?? true,
                          has_phone: c.has_phone ?? true,
                          is_opentowork: c.is_opentowork,
                          is_decision_maker: c.is_decision_maker,
                          is_top_universities: c.is_top_universities,
                          is_startup: c.is_startup || c.company_info?.is_startup,
                          expertise: c.expertise,
                          outreach_message: c.outreach_message,
                          experiences: c.experiences || [],
                          workHistory: (c.experiences || []).map((exp: ApiExperience) => ({
                            company: exp.company_info?.name || exp.company || '',
                            title: exp.company_roles?.[0]?.title || exp.title || '',
                            startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
                            endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
                            duration: exp.duration || '',
                            location: exp.company_info?.location || exp.location || '',
                            description: exp.company_roles?.[0]?.description || exp.description || ''
                          })),
                          education: (c.education || []).map((edu: ApiEducation) => ({
                            school: edu.school || '',
                            degree: edu.degree || '',
                            field_of_study: edu.field_of_study || '',
                            fieldOfStudy: edu.field_of_study || '',
                            startDate: edu.start_date || '',
                            endDate: edu.end_date || ''
                          }))
                        }))

                        const localCandidates = mappedCandidates.filter((c) => c.source === 'local')
                        const globalCandidates = mappedCandidates.filter((c) => c.source === 'pearch')

                        // Respeitar searchSource selecionado pelo usuário
                        const shouldAutoShowGlobal = searchSource === 'global' || searchSource === 'hybrid'
                        const candidatesForTable = shouldAutoShowGlobal ? mappedCandidates : localCandidates

                        setCandidates(candidatesForTable)
                        setHasSearchResults(true)
                        setSearchResultsCount(data.total_count || mappedCandidates.length)
                        setLocalResultsCount(data.local_count || localCandidates.length)
                        setPearchResultsCount(data.pearch_count || globalCandidates.length)
                        setShowSearchResults(true)
                        setDisplayedResultsCount(10)

                        setSearchResults(prev => ({
                          local: localCandidates,
                          global: globalCandidates,
                          localCount: data.local_count || localCandidates.length,
                          globalCount: data.pearch_count || globalCandidates.length,
                          query: data.query_generated || jobDescriptionText.substring(0, 50),
                          isLoading: false,
                          showGlobalResults: shouldAutoShowGlobal,
                          globalDismissed: prev.globalDismissed
                        }))

                        const localCount = data.local_count || localCandidates.length
                        const liaMessage: ChatMessage = {
                          id: `lia-jd-result-${Date.now()}`,
                          type: 'lia',
                          content: `**Busca por Job Description concluída!**\n\nQuery gerada: "${data.query_generated}"\n\nEncontrei **${localCount} candidato${localCount > 1 ? 's' : ''}** na sua base local.`,
                          timestamp: new Date(),
                          searchResults: {
                            localCount: localCount,
                            globalCount: 0,
                            query: data.query_generated || ''
                          }
                        }
                        setChatMessages(prev => [...prev, liaMessage])
                      } else {
                        const liaMessage: ChatMessage = {
                          id: `lia-jd-noresult-${Date.now()}`,
                          type: 'lia',
                          content: `Não encontrei candidatos com os critérios extraídos da descrição da vaga.\n\nTente ajustar a descrição ou usar a busca por IA Natural com termos mais específicos.`,
                          timestamp: new Date()
                        }
                        setChatMessages(prev => [...prev, liaMessage])
                      }
                    } catch (error) {
                      const liaMessage: ChatMessage = {
                        id: `lia-jd-error-${Date.now()}`,
                        type: 'lia',
                        content: `Erro ao buscar candidatos pela descrição da vaga. Por favor, tente novamente.`,
                        timestamp: new Date()
                      }
                      setChatMessages(prev => [...prev, liaMessage])
                    } finally {
                      setIsSearchingJD(false)
                    }
                  }
                }}
                disabled={!jobDescriptionText.trim() || jobDescriptionText.length < 50 || isSearchingJD}
              >
                {isSearchingJD ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                    Analisando...
                  </>
                ) : (
                  <>
                    <span
                      className="flex items-center justify-center w-5 h-5 rounded-md bg-gray-900"
                    >
                      <Brain className="w-3 h-3 text-white" />
                    </span>
                    Extrair e Buscar
                  </>
                )}
              </button>

              {jobDescriptionText.length > 0 && jobDescriptionText.length < 50 && (
                <p className="text-xs text-status-warning">
                  A descrição precisa ter pelo menos 50 caracteres para análise adequada.
                </p>
              )}
            </div>
          )}

          {/* ABA 4: SIMILAR */}
          {activeSearchTab === 'similar' && (
            <div className="space-y-4 overflow-y-auto flex-1 p-4">
              <p className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                Encontre candidatos similares a um perfil específico
              </p>

              <div className="relative">
                <input
                  type="text"
                  value={similarProfileUrl}
                  onChange={(e) => setSimilarProfileUrl(e.target.value)}
                  placeholder="Cole o link do LinkedIn ou nome do candidato..."
                  className="w-full p-3 text-xs rounded-md border focus:outline-none transition-colors motion-reduce:transition-none bg-white dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary border border-lia-border-subtle"
                />
              </div>

              <div className="p-3 rounded-md bg-wedo-cyan/[0.06]">
                <div className="flex items-start gap-2">
                  <Lightbulb className="w-4 h-4 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
                  <p className="text-xs text-lia-text-primary dark:text-lia-text-tertiary">
                    <strong>Dica:</strong> Cole o link do LinkedIn de um candidato que você considera ideal para encontrar perfis similares.
                  </p>
                </div>
              </div>

              <Button
                className={`w-full h-11 !text-sm font-semibold text-white font-open-sans ${isSearchingSimilar ? 'bg-gray-400' : 'bg-wedo-cyan-dark'}`}
                onClick={async () => {
                  if (similarProfileUrl.trim() && !isSearchingSimilar) {
                    setIsSearchingSimilar(true)

                    const isLinkedInUrl = similarProfileUrl.includes('linkedin.com/in/')

                    const userMessage: ChatMessage = {
                      id: `user-similar-${Date.now()}`,
                      type: 'user',
                      content: isLinkedInUrl
                        ? `Buscar candidatos similares ao perfil: ${similarProfileUrl}`
                        : `Buscar candidatos similares: ${similarProfileUrl}`,
                      timestamp: new Date()
                    }
                    setChatMessages(prev => [...prev, userMessage])

                    try {
                      const requestBody: { linkedin_url?: string; candidate_id?: string; limit: number; search_pearch: boolean; pearch_type: string } = {
                        limit: 20,
                        search_pearch: searchSource !== 'local',
                        pearch_type: pearchSearchOptions.searchType
                      }

                      if (isLinkedInUrl) {
                        requestBody.linkedin_url = similarProfileUrl.trim()
                      } else {
                        requestBody.candidate_id = similarProfileUrl.trim()
                      }

                      const response = await fetch('/api/backend-proxy/search/candidates/similar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(requestBody)
                      })

                      if (!response.ok) {
                        const errorData = await response.json().catch(() => ({}))
                        throw new Error(errorData.detail || 'Erro na busca')
                      }

                      const data = await response.json()

                      if (data.candidates && data.candidates.length > 0) {
                        const mappedCandidates = (data.candidates as ApiCandidate[]).map((c) => ({
                          id: c.id || `similar-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                          candidateId: c.id?.substring(0, 8).toUpperCase() || 'SIM',
                          name: c.name || 'Nome não disponível',
                          email: c.email || '',
                          phone: c.phone || '',
                          current_title: c.headline || c.current_title || '',
                          current_company: c.current_company || '',
                          location: c.location || '',
                          linkedin_url: c.linkedin_url,
                          avatar_url: c.avatar_url || c.picture_url,
                          avatar: c.avatar_url,
                          technical_skills: c.skills || [],
                          skills: c.skills || [],
                          seniority_level: c.seniority_level,
                          years_of_experience: c.years_experience || c.total_experience_years,
                          experience: c.years_experience || c.total_experience_years || 0,
                          score: c.match_score ? Math.round(c.match_score * 25) : 75,
                          source: c.source || 'pearch',
                          has_email: c.has_email ?? true,
                          has_phone: c.has_phone ?? true,
                          is_opentowork: c.is_opentowork,
                          is_decision_maker: c.is_decision_maker,
                          is_top_universities: c.is_top_universities,
                          is_startup: c.is_startup || c.company_info?.is_startup,
                          expertise: c.expertise,
                          outreach_message: c.outreach_message,
                          experiences: c.experiences || [],
                          workHistory: (c.experiences || []).map((exp: ApiExperience) => ({
                            company: exp.company_info?.name || exp.company || '',
                            title: exp.company_roles?.[0]?.title || exp.title || '',
                            startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
                            endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
                            duration: exp.duration || '',
                            location: exp.company_info?.location || exp.location || '',
                            description: exp.company_roles?.[0]?.description || exp.description || ''
                          })),
                          education: (c.education || []).map((edu: ApiEducation) => ({
                            school: edu.school || '',
                            degree: edu.degree || '',
                            field_of_study: edu.field_of_study || '',
                            fieldOfStudy: edu.field_of_study || '',
                            startDate: edu.start_date || '',
                            endDate: edu.end_date || ''
                          }))
                        }))

                        const localCandidates = mappedCandidates.filter((c) => c.source === 'local')
                        const globalCandidates = mappedCandidates.filter((c) => c.source === 'pearch')

                        // Respeitar searchSource selecionado pelo usuário
                        const shouldAutoShowGlobal = searchSource === 'global' || searchSource === 'hybrid'
                        const candidatesForTable = shouldAutoShowGlobal ? mappedCandidates : localCandidates

                        setCandidates(candidatesForTable)
                        setHasSearchResults(true)
                        setSearchResultsCount(data.total_count || mappedCandidates.length)
                        setLocalResultsCount(data.local_count || localCandidates.length)
                        setPearchResultsCount(data.pearch_count || globalCandidates.length)
                        setShowSearchResults(true)
                        setDisplayedResultsCount(10)

                        setSearchResults(prev => ({
                          local: localCandidates,
                          global: globalCandidates,
                          localCount: data.local_count || localCandidates.length,
                          globalCount: data.pearch_count || globalCandidates.length,
                          query: data.query_generated || 'Similar Search',
                          isLoading: false,
                          showGlobalResults: shouldAutoShowGlobal,
                          globalDismissed: prev.globalDismissed
                        }))

                        const refProfileInfo = data.reference_profile
                          ? `\n\n**Perfil de referência:** ${data.reference_profile.name || data.reference_profile.linkedin_url || 'ID: ' + data.reference_profile.id}`
                          : ''

                        const localCount = data.local_count || localCandidates.length
                        const liaMessage: ChatMessage = {
                          id: `lia-similar-result-${Date.now()}`,
                          type: 'lia',
                          content: `**Busca de perfis similares concluída!**${refProfileInfo}\n\nQuery gerada: "${data.query_generated}"\n\nEncontrei **${localCount} candidato${localCount > 1 ? 's' : ''} similar${localCount > 1 ? 'es' : ''}** na sua base local.`,
                          timestamp: new Date(),
                          searchResults: {
                            localCount: localCount,
                            globalCount: 0,
                            query: data.query_generated || ''
                          }
                        }
                        setChatMessages(prev => [...prev, liaMessage])
                      } else {
                        const liaMessage: ChatMessage = {
                          id: `lia-similar-noresult-${Date.now()}`,
                          type: 'lia',
                          content: `Não encontrei candidatos similares ao perfil informado.\n\nVerifique se o link do LinkedIn está correto ou tente com outro perfil de referência.`,
                          timestamp: new Date()
                        }
                        setChatMessages(prev => [...prev, liaMessage])
                      }
                    } catch (error: unknown) {
                      const liaMessage: ChatMessage = {
                        id: `lia-similar-error-${Date.now()}`,
                        type: 'lia',
                        content: `Erro ao buscar candidatos similares: ${error instanceof Error ? error.message : 'Por favor, tente novamente.'}`,
                        timestamp: new Date()
                      }
                      setChatMessages(prev => [...prev, liaMessage])
                    } finally {
                      setIsSearchingSimilar(false)
                    }
                  }
                }}
                disabled={!similarProfileUrl.trim() || isSearchingSimilar}
              >
                {isSearchingSimilar ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                    Buscando...
                  </>
                ) : (
                  <>
                    <Users className="w-4 h-4 mr-2" />
                    Encontrar Similares
                  </>
                )}
              </Button>
            </div>
          )}

          {/* ABA 5: BOOLEAN */}
          {activeSearchTab === 'boolean' && (
            <div className="space-y-4 overflow-y-auto flex-1 p-4">
              <p className="text-xs text-lia-text-tertiary">
                Use operadores booleanos para buscas avançadas
              </p>

              <div className="flex flex-wrap gap-1 mb-2">
                {['AND', 'OR', 'NOT', '"..."', '(...)'].map((op) => (
                  <button
                    key={op}
                    onClick={() => setBooleanSearchValue(prev => prev + ' ' + op)}
                    className="px-2 py-1 text-xs rounded-full bg-gray-100 hover:bg-gray-200 text-lia-text-primary font-mono transition-colors motion-reduce:transition-none"
                  >
                    {op}
                  </button>
                ))}
              </div>

              <textarea
                value={booleanSearchValue}
                onChange={(e) => setBooleanSearchValue(e.target.value)}
                placeholder='Ex: ("Node.js" OR "Python") AND "sênior" NOT "júnior"'
                className="w-full h-32 p-3 text-xs rounded-md border focus:outline-none transition-colors motion-reduce:transition-none resize-none bg-white dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary font-mono border border-lia-border-subtle"
              />

              <div className="p-3 rounded-md bg-wedo-cyan/[0.06]">
                <div className="flex items-start gap-2">
                  <Lightbulb className="w-4 h-4 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
                  <p className="text-xs text-lia-text-primary dark:text-lia-text-tertiary">
                    <strong>Dica:</strong> Use aspas para termos exatos e parênteses para agrupar condições.
                  </p>
                </div>
              </div>

              <Button
                className="w-full h-11 !text-sm font-semibold bg-wedo-cyan-dark text-white font-open-sans"
                onClick={() => {
                  if (booleanSearchValue.trim()) {
                  }
                }}
                disabled={!booleanSearchValue.trim()}
              >
                <Code className="w-4 h-4 mr-2" />
                Buscar com Boolean
              </Button>
            </div>
          )}

          {/* ABA 6: FILTROS - Padronizado com Modal */}
          {activeSearchTab === 'filtros' && (
            <div className="space-y-4 overflow-y-auto flex-1 p-4">
              {/* Dica contextual */}
              <div className="p-3 rounded-md bg-wedo-cyan/[0.06]">
                <div className="flex items-start gap-2">
                  <Lightbulb className="w-4 h-4 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
                  <p className="text-xs text-lia-text-primary dark:text-lia-text-tertiary">
                    <strong>Dica:</strong> Use os filtros avançados para refinar sua busca por localização, experiência, skills, idiomas e muito mais.
                  </p>
                </div>
              </div>

              {/* Resumo dos filtros ativos */}
              {Object.values(activeSearchFilters).some(category =>
                Object.values(category as Record<string, unknown>).some(v => v === true || (typeof v === 'string' && v.length > 0))
              ) && (
                <div className="p-3 rounded-md border bg-status-success/5 border-status-success/30">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-status-success" />
                      <span className="text-xs font-medium text-status-success">
                        Filtros ativos
                      </span>
                    </div>
                    <button
                      onClick={() => setActiveSearchFilters({
                        ppiOptions: {},
                        general: {},
                        locations: {},
                        job: {},
                        company: {},
                        skills: {},
                        education: {},
                        languages: {}
                      })}
                      className="text-xs text-lia-text-primary hover:text-status-error transition-colors motion-reduce:transition-none"

                    >
                      Limpar todos
                    </button>
                  </div>
                </div>
              )}

              {/* Botão para abrir painel lateral de filtros da tabela */}
              <Button
                className="w-full h-12 !text-sm font-semibold"
                style={{backgroundColor: showTableFiltersPanel ? 'var(--gray-800)' : 'var(--gray-600)',
                  color: 'var(--gray-50)'}}
                onClick={() => setShowTableFiltersPanel(!showTableFiltersPanel)}
              >
                <Filter className="w-4 h-4 mr-2" />
                {showTableFiltersPanel ? 'Fechar Filtros' : 'Abrir Filtros Avançados'}
              </Button>

              {/* Info sobre filtros laterais */}
              {!showTableFiltersPanel && (
                <p className="text-xs text-lia-text-primary text-center mt-2" aria-live="polite" aria-atomic="true">
                  Os filtros aparecerão ao lado da tabela de candidatos
                </p>
              )}
            </div>
          )}

        </div>
      </Card>

      {/* Resize Handle - Sempre visível */}
      <div
        className={`absolute -right-1.5 top-1/2 -translate-y-1/2 w-3 cursor-ew-resize hover:scale-125 transition-transform motion-reduce:transition-none z-10 flex items-center justify-center ${isLiaSuperChat ? 'h-full' : 'h-12'}`}
        title="Arraste para ajustar a largura"
        onMouseDown={(e) => {
          e.preventDefault()
          setIsResizingLIA(true)
          const startX = e.clientX
          const startWidth = isLiaSuperChat ? superChatWidth : liaWidth

          const handleMouseMove = (e: MouseEvent) => {
            const deltaX = e.clientX - startX
            if (isLiaSuperChat) {
              // Em modo superchat, permite largura maior (até 80% da tela)
              const maxWidth = Math.floor(window.innerWidth * 0.8)
              const newWidth = Math.max(500, Math.min(maxWidth, startWidth + deltaX))
              setSuperChatWidth(newWidth)
            } else {
              const newWidth = Math.max(400, Math.min(800, startWidth + deltaX))
              setLiaWidth(newWidth)
            }
          }

          const handleMouseUp = () => {
            setIsResizingLIA(false)
            document.removeEventListener('mousemove', handleMouseMove)
            document.removeEventListener('mouseup', handleMouseUp)
          }

          document.addEventListener('mousemove', handleMouseMove)
          document.addEventListener('mouseup', handleMouseUp)
        }}
      >
 <div className={`w-1 rounded-full transition-colors motion-reduce:transition-none ${isLiaSuperChat ? 'h-24 bg-gray-900' : 'h-8 dark:bg-lia-bg-elevated hover:dark:hover:bg-gray-800'}`} />
      </div>
    </div>
  )
}
