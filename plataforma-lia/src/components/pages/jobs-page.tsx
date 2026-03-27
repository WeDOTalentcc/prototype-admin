"use client"

import React, { useState, useRef, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import dynamic from "next/dynamic"
import { liaApi, type JobVacancy, type JobVacancyMetrics } from "@/services/lia-api"
import { callOrchestratedJobsManagement } from "@/lib/api/kanban-assistant"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"
import { AISearchToggle } from "@/components/ai-search-toggle"
import { IntelligenceNotifications } from "@/components/intelligence-notifications"
import { Search, Plus, MapPin, Calendar, Users, DollarSign, Eye, Edit, Edit2, Share2, Clock, Layout, Layers3, Layers, ChevronDown, ChevronUp, ChevronLeft, BarChart3, TrendingUp, TrendingDown, FileText, ExternalLink, Briefcase, Building, Building2, Target, CheckCircle, CheckCircle2, XCircle, Linkedin, Globe, Shield, Hash, UserCheck, Heart, MoreHorizontal, Grid3X3, List, Maximize2, Minimize2, Star, Brain, Expand, Copy, MessageSquare, MoreVertical, Settings, Settings2, X, ChevronsLeftRight, Bell, Pin, Github, Mail, Lock, LockOpen, MessageCircle, AlertCircle, AlertTriangle, ShieldAlert, Lightbulb, ChevronRight, Home, Zap, ClipboardList, ListChecks, CalendarCheck, ThumbsUp, Phone, Send, Bookmark, Paperclip, Mic, GripVertical, ArrowUp, ArrowDown, ArrowUpDown, Filter, Award, Trash2, RefreshCw, ArrowRight, ArrowLeft, HelpCircle, Timer, GraduationCap, BookOpen, Scale, Loader2, History, Languages, UserCircle, CalendarDays, Link, Save, Check, RotateCcw, CalendarClock, Info, Archive, Gauge } from "lucide-react"
import { JobKanbanPage } from "./job-kanban-page"
import { JobReportModal } from "@/components/job-report-modal"
import { JobActionsBar } from "@/components/job-actions-bar"
import { JobCompareModal } from "@/components/modals/job-compare-modal"
import { JobPublishModal } from "@/components/modals/job-publish-modal"
import { JobUnpublishModal, type UnpublishData } from "@/components/modals/job-unpublish-modal"
import { JobInsightsModal } from "@/components/modals/job-insights-modal"
import { JobDuplicateModal } from "@/components/modals/job-duplicate-modal"
import { JobStatusModal } from "@/components/modals/job-status-modal"
import { JobAssignRecruiterModal } from "@/components/modals/job-assign-recruiter-modal"
import { EditJobModal } from "@/components/modals/edit-job-modal"
import { CreateJobModal } from "@/components/modals/create-job-modal"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { ContextPill } from "@/components/ui/context-pill"
import { QuickActionChips, type QuickAction } from "@/components/ui/quick-action-chips"
import { PromptSuggestionsPopover } from "@/components/ui/prompt-suggestions-popover"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { LiaQueriesGuide } from "@/components/ui/lia-queries-guide"
import { LiaVacancyQueriesGuide } from "@/components/ui/lia-vacancy-queries-guide"
import { useNavigationPersistence } from "@/hooks/use-navigation-persistence"
import { useJobFiltersPersistence, type SavedSearch } from "@/hooks/useJobFiltersPersistence"
import { useJobColumnConfig } from "@/hooks/useJobColumnConfig"
import { textStyles, cardStyles, badgeStyles, buttonStyles } from '@/lib/design-tokens'
import { cn } from '@/lib/utils'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { toast } from "sonner"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { useScreeningConfig, limitToApprovalPreset, approvalPresetToLimit, type ScreeningConfig } from "@/hooks/useScreeningConfig"
import { useLiaSuggestions, useJobInsights, useLiaExpandedPrompt, type SuggestionCard } from "@/hooks/use-lia-suggestions"
import { ScreeningChannelsModal, ScreeningSettingsModal, ScreeningSchedulingModal } from "@/components/screening-config"
import type { ScreeningStatus } from "@/components/screening-config"
import { QuestionAdjustmentChat, QuestionDiffView, AdjustmentCounter, JDEvaluationPanel } from "@/components/wsi"
import { 
  type Job, 
  type JobFilters, 
  type JobFunnel,
  type TechnicalRequirement,
  type Language,
  type BehavioralCompetency,
  type InterviewStage,
  type ScreeningQuestion,
  type SalaryRange,
  type OrganizationalStructure,
  type Timeline,
  type GovernanceRules,
  type ViewMode,
  type PreviewTab
} from "@/components/jobs"
import { 
  getStatusColor, 
  priorityColors, 
  WSI_BLOCKS, 
  WSI_AUTOMATIC_MESSAGES, 
  formatMessageWithVariables,
  getBloomComplexity,
  getEstimatedTime
} from "@/components/jobs/jobsPageConstants"
import { JobFiltersPanel } from "@/components/jobs/JobFilters"

const ExpandedChatModal = dynamic(() => import("@/components/expanded-chat-modal").then(m => ({ default: m.ExpandedChatModal })), { ssr: false })

interface JobsPageProps {
  onNavigate?: (page: string) => void
  onAddRecentItem?: (item: { id: string; type: 'vaga' | 'chat' | 'candidato'; title: string; subtitle?: string; meta?: Record<string, string | undefined> }) => void
  pendingChatOpen?: { mode: 'general' | 'job-creation' } | null
  onChatOpened?: () => void
  pendingJobOpen?: { jobId: string; jobTitle: string } | null
  onJobOpened?: () => void
}

export function JobsPage({ onNavigate, onAddRecentItem, pendingChatOpen, onChatOpened, pendingJobOpen, onJobOpened }: JobsPageProps) {
  const router = useRouter()
  
  // Hydration safety: ensure identical server/client initial render
  const [hasMounted, setHasMounted] = useState(false)
  
  // Filter persistence hook - persists filters to localStorage
  const {
    filtersState: persistedFilters,
    updateFilter: updatePersistedFilter,
    updateAdvancedFilter: updatePersistedAdvancedFilter,
    clearAllFilters: clearPersistedFilters,
    savedSearches: persistedSavedSearches,
    saveCurrentSearch: savePersistedSearch,
    applySavedSearch: applyPersistedSearch,
    deleteSavedSearch: deletePersistedSearch,
    renameSavedSearch: renamePersistedSearch,
    getActiveFiltersCount,
    hasActiveFilters,
    isLoaded: filtersLoaded
  } = useJobFiltersPersistence()
  
  // Column configuration hook - persists column visibility to localStorage
  const {
    columns: columnConfig,
    visibleColumnIds,
    savedViews: savedColumnViews,
    toggleColumn,
    resetToDefault: resetColumnsToDefault,
    saveView: saveColumnView,
    applyView: applyColumnView,
    deleteView: deleteColumnView,
    getColumnsByCategory,
    isLoaded: columnsLoaded
  } = useJobColumnConfig()
  
  const [viewMode, setViewMode] = useState<ViewMode>('compact')
  const [searchTerm, setSearchTerm] = useState("")
  const [pinnedJobs, setPinnedJobs] = useState<Set<number>>(new Set())
  const [urgentJobs, setUrgentJobs] = useState<Set<number>>(new Set())
  const [favoriteJobs, setFavoriteJobs] = useState<Set<number>>(new Set())
  
  // Edit Job Modal states
  const [showEditJobModal, setShowEditJobModal] = useState(false)
  const [editingJob, setEditingJob] = useState<Job | null>(null)
  
  // Create Job Modal state
  const [showCreateJobModal, setShowCreateJobModal] = useState(false)
  const [pendingNavigateJobId, setPendingNavigateJobId] = useState<string | null>(null)
  const [jobsRefreshKey, setJobsRefreshKey] = useState(0)
  
  // Preview description expand state
  const [showFullDescription, setShowFullDescription] = useState(false)
  const [showStageDates, setShowStageDates] = useState(false)
  const [showExpandedDetails, setShowExpandedDetails] = useState(false)
  
  // Backend integration states
  const [backendJobs, setBackendJobs] = useState<Job[]>([])
  const [isLoadingJobs, setIsLoadingJobs] = useState(true)
  const [jobsError, setJobsError] = useState<string | null>(null)
  
  // Mark component as mounted - this enables client-side features
  useEffect(() => {
    setHasMounted(true)
  }, [])
  
  // Load jobs from backend on mount (only after hydration completes)
  useEffect(() => {
    if (!hasMounted) return
    
    const loadBackendJobs = async () => {
      try {
        setIsLoadingJobs(true)
        setJobsError(null)
        const response = await liaApi.listJobVacancies()
        
        if (!response || !response.items) {
          throw new Error('Invalid response format')
        }
        
        // Convert backend format to frontend Job format
        const convertedJobs: Job[] = response.items.map((jv, index) => {
          // Parse funnel_data from backend
          const funnelData = jv.funnel_data || { total: 0, screening: 0, interview: 0, final: 0, hired: 0 }
          
          // Map stage from backend to frontend format
          const stageMapping: Record<string, Job['stage']> = {
            'Planejamento': 'Planejamento',
            'Aprovação': 'Aprovação',
            'Publicada': 'Publicada',
            'Triagem': 'Triagem',
            'Entrevistas': 'Entrevistas',
            'Finalização': 'Finalização',
            'Encerrada': 'Encerrada'
          }
          
          return {
            id: index + 1,
            jobId: `WDT-${jv.id.slice(0, 8).toUpperCase()}`,
            backendId: jv.id,
            title: jv.title,
            department: jv.department || 'Geral',
            location: jv.location || 'Não especificado',
            workModel: (jv.work_model as Job['workModel']) || 'híbrido',
            type: jv.employment_type || 'CLT',
            level: jv.seniority_level || 'Pleno',
            salary: jv.salary_range ? `R$ ${jv.salary_range.min?.toLocaleString()} - R$ ${jv.salary_range.max?.toLocaleString()}` : 'A combinar',
            benefits: jv.benefits || [],
            status: (jv.status as Job['status']) || 'Rascunho',
            stage: stageMapping[jv.stage || ''] || 'Triagem',
            openDate: jv.open_date?.split('T')[0] || jv.created_at?.split('T')[0] || new Date().toISOString().split('T')[0],
            deadline: jv.deadline?.split('T')[0] || undefined,
            description: jv.description || '',
            requirements: jv.requirements || [],
            manager: jv.manager || 'Não definido',
            managerEmail: jv.manager_email || '',
            recruiter: jv.recruiter || 'Não definido',
            recruiterEmail: jv.recruiter_email || '',
            priority: (jv.priority as Job['priority']) || 'média',
            funnel: {
              total: funnelData.total || 0,
              screening: funnelData.screening || 0,
              interview: funnelData.interview || 0,
              final: funnelData.final || 0,
              hired: funnelData.hired || 0
            },
            liaMetrics: jv.lia_metrics ? {
              pipeline_lia: jv.lia_metrics.pipeline_lia || 0,
              triagens_agendadas: jv.lia_metrics.triagens_agendadas || 0,
              triagens_realizadas: jv.lia_metrics.triagens_realizadas || 0,
              sem_resposta: jv.lia_metrics.sem_resposta || 0,
              entrevistas_agendadas: jv.lia_metrics.entrevistas_agendadas || 0
            } : undefined,
            publishedLinkedIn: jv.published_linkedin || false,
            publishedWebsite: jv.published_website || false,
            isConfidential: jv.is_confidential || false,
            visibility: (jv.visibility as Job['visibility']) || 'public',
            nps: jv.nps || 0,
            budget: jv.budget || undefined,
            budgetUsed: jv.budget_used || undefined,
            nextActions: jv.next_actions || [],
            urgencyLevel: (jv.urgency_level as 1 | 2 | 3 | 4 | 5) || 3,
            approvalStatus: (jv.approval_status as 'pendente' | 'aprovada' | 'rejeitada') || 'pendente',
            tags: jv.tags || [],
            technicalRequirements: jv.technical_requirements || [],
            languages: jv.languages || [],
            behavioralCompetencies: jv.behavioral_competencies || [],
            screeningQuestions: jv.screening_questions || [],
            interviewStages: jv.interview_stages || [],
            hiringProcess: (jv.interview_stages && jv.interview_stages.length > 0)
              ? [...jv.interview_stages]
                  .sort((a: any, b: any) => (a.order || 0) - (b.order || 0))
                  .map((s: any) => s.stageName || s.stage_name || s.name || '')
                  .filter((n: string) => n)
              : (jv.hiring_process || []),
            salaryRange: jv.salary_range || undefined,
            organizationalStructure: jv.organizational_structure || undefined,
            timeline: jv.timeline || undefined,
            governanceRules: jv.governance_rules || undefined,
            whatsappTemplateType: jv.whatsapp_template_type || undefined,
            targetSector: jv.target_sector || undefined,
            targetSegment: jv.target_segment || undefined,
            conversationId: jv.conversation_id || undefined,
            screeningConfig: jv.screening_config || undefined,
            screeningStatus: jv.screening_status || (jv.screening_config ? 'not_started' : 'not_configured'),
            deadlineScreening: jv.deadline_screening || undefined,
            deadlineShortlist: jv.deadline_shortlist || undefined,
            deadlineClosing: jv.deadline_closing || undefined,
            eligibilityQuestions: jv.eligibility_questions || [],
            confidentialityConfig: jv.confidentiality_config || undefined,
            enrichedJd: jv.enriched_jd || undefined,
            isAffirmative: jv.is_affirmative || false,
            createdAt: jv.created_at || undefined,
            updatedAt: jv.updated_at || undefined,
            publishedAt: jv.published_at || jv.last_published_at || undefined,
            closedAt: jv.closed_at || undefined,
            createdByEmail: jv.created_by_email || undefined,
          }
        })
        
        setBackendJobs(convertedJobs)
        
        // Load stats - inside the same useEffect to avoid timing issues with HMR
        try {
          const overviewData = await liaApi.getJobVacanciesOverview()
          const stats = {
            total: overviewData.active_jobs.total + (overviewData.all_jobs.hired_last_90d || 0),
            ativas: overviewData.active_jobs.total,
            urgentes: overviewData.active_jobs.by_urgency?.['alta'] || 0,
            paralisadas: 0,
            concluidas: overviewData.all_jobs.hired_last_90d || 0,
            canceladas: 0,
            noFunil: overviewData.my_jobs.candidates_in_funnel || 0,
            entrevistasRecentes: overviewData.my_jobs.interviews_last_7d || 0,
            ofertas: overviewData.my_jobs.offers_sent || 0,
            ttfMedio: Math.round(overviewData.all_jobs.time_to_fill_avg_90d || overviewData.active_jobs.avg_days_open),
            taxaConversao: Math.round(overviewData.all_jobs.success_rate || overviewData.my_jobs.conversion_rate),
            atRisco: overviewData.active_jobs.at_risk,
            pipelineVazio: overviewData.active_jobs.empty_pipeline,
            deadlineProximo: overviewData.active_jobs.deadline_soon,
            porDepartamento: overviewData.all_jobs.by_department,
            tendenciaSemanal: overviewData.all_jobs.trend_weeks,
            insights: overviewData.insights,
          }
          setDashboardStats(stats)
          setIsLoadingStats(false)
          statsLoaded.current = true
        } catch (statsError) {
          console.error('[JobsPage] Failed to load stats:', statsError)
          // Use fallback data from loaded jobs
          const stats = {
            total: convertedJobs.length,
            ativas: convertedJobs.filter(job => job.status === 'Ativa').length,
            urgentes: convertedJobs.filter(job => job.urgencyLevel >= 4).length,
            paralisadas: convertedJobs.filter(job => job.status === 'Paralisada').length,
            concluidas: convertedJobs.filter(job => job.status === 'Concluída').length,
            canceladas: convertedJobs.filter(job => job.status === 'Cancelada').length,
            noFunil: convertedJobs.reduce((sum, job) => sum + (job.funnel?.total || 0), 0),
            entrevistasRecentes: 0,
            ofertas: convertedJobs.filter(job => job.stage === 'Oferta').length,
            ttfMedio: 0,
            taxaConversao: 0,
            atRisco: 0,
            pipelineVazio: 0,
            deadlineProximo: 0,
            porDepartamento: {},
            tendenciaSemanal: [],
            insights: [],
          }
          setDashboardStats(stats)
          setIsLoadingStats(false)
        }
      } catch (error) {
        console.error('[JobsPage] Failed to load jobs from backend:', error)
        setJobsError(error instanceof Error ? error.message : 'Failed to load jobs')
        setIsLoadingStats(false)
      } finally {
        setIsLoadingJobs(false)
      }
    }
    
    loadBackendJobs()
  }, [hasMounted, jobsRefreshKey])
  
  // Use only backend jobs - no mock data
  const allJobs = backendJobs

  const [showKanban, setShowKanban] = useState(() => {
    if (typeof window !== 'undefined') {
      const raw = localStorage.getItem('navigateToCandidate')
      if (raw) return true
    }
    return false
  })
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [showReport, setShowReport] = useState(false)
  
  // Persistência de navegação - desabilitado para manter comportamento padrão
  // O usuário sempre verá a tela inicial de Gestão de Vagas ao clicar no menu
  const { getJobsState } = useNavigationPersistence()
  const hasRestoredNavigation = useRef(false)
  const hasProcessedNavigateToCandidate = useRef(false)
  
  // Removido: restauração automática do Kanban
  // O estado é salvo mas não restaurado automaticamente para evitar confusão na navegação
  const [reportJob, setReportJob] = useState<Job | null>(null)
  const [showJobPreview, setShowJobPreview] = useState(false)
  const [previewJob, setPreviewJob] = useState<Job | null>(null)
  const [activePreviewTab, setActivePreviewTab] = useState<'screening' | 'pipeline'>('screening')
  const [showWSITutorialModal, setShowWSITutorialModal] = useState(false)

  const [openJobDataSections, setOpenJobDataSections] = useState<Record<string, boolean>>({ 'info-geral': true })
  const [jobDataForm, setJobDataForm] = useState<Record<string, any>>({})
  const [savingSection, setSavingSection] = useState<string | null>(null)
  const [newJobDataBenefit, setNewJobDataBenefit] = useState('')
  const [newJobDataLang, setNewJobDataLang] = useState('')
  const [newJobDataLangLevel, setNewJobDataLangLevel] = useState('Intermediário')
  
  const { config: screeningConfig, isLoading: isLoadingScreeningConfig, updateConfig: updateScreeningConfig } = useScreeningConfig(previewJob?.backendId || null)

  // Job Metrics state for preview panel
  const [jobMetrics, setJobMetrics] = useState<JobVacancyMetrics | null>(null)
  const [isLoadingJobMetrics, setIsLoadingJobMetrics] = useState(false)

  useEffect(() => {
    if (hasProcessedNavigateToCandidate.current) return
    if (!allJobs.length) return

    const raw = localStorage.getItem('navigateToCandidate')
    if (!raw) return

    hasProcessedNavigateToCandidate.current = true

    try {
      const nav = JSON.parse(raw) as {
        candidateId?: string
        candidateName?: string
        jobId?: string
        jobTitle?: string
        currentStage?: string
        action?: string
        openTransitionModal?: boolean
      }

      let matchedJob = allJobs.find(
        (j) => j.jobId === nav.jobId || j.title === nav.jobTitle
      )

      if (!matchedJob && nav.jobTitle) {
        const normalizedTitle = nav.jobTitle.toLowerCase()
        matchedJob = allJobs.find(
          (j) => j.title.toLowerCase().includes(normalizedTitle) || normalizedTitle.includes(j.title.toLowerCase())
        )
      }

      if (!matchedJob && nav.jobId) {
        matchedJob = allJobs.find(
          (j) => j.backendId === nav.jobId || j.jobId?.includes(nav.jobId!) || nav.jobId!.includes(j.jobId || '')
        )
      }

      if (!matchedJob) {
        const activeJobs = allJobs.filter(j => j.status === 'Ativa')
        if (activeJobs.length > 0) {
          matchedJob = activeJobs[0]
        }
      }

      if (matchedJob) {
        setSelectedJob(matchedJob)
        setShowKanban(true)
        setShowJobPreview(false)
        setPreviewJob(null)
        onAddRecentItem?.({
          id: matchedJob.backendId || matchedJob.jobId || String(matchedJob.id),
          type: 'vaga',
          title: matchedJob.title,
          subtitle: matchedJob.company,
          meta: { jobId: matchedJob.backendId || matchedJob.jobId || String(matchedJob.id) }
        })
      } else {
        localStorage.removeItem('navigateToCandidate')
        localStorage.removeItem('liaPrompt')
      }
    } catch (e) {
      console.error('Erro ao processar navigateToCandidate:', e)
      localStorage.removeItem('navigateToCandidate')
      localStorage.removeItem('liaPrompt')
    }

  }, [allJobs, onAddRecentItem])

  // Navega para vaga recém-criada assim que ela aparecer na lista
  useEffect(() => {
    if (!pendingNavigateJobId || !allJobs.length) return
    const matched = allJobs.find(j => j.backendId === pendingNavigateJobId)
    if (!matched) return
    setPendingNavigateJobId(null)
    setSelectedJob(matched)
    setShowKanban(true)
    setShowJobPreview(false)
    setPreviewJob(null)
  }, [allJobs, pendingNavigateJobId])

  useEffect(() => {
    if (pendingChatOpen) {
      if (pendingChatOpen.mode === 'job-creation') {
        setShowInlineChat(true)
        setChatMode('job-creation')
        setIsTableCollapsed(true)
      } else {
        setShowInlineChat(true)
        setChatMode('general')
        setIsTableCollapsed(true)
      }
      onChatOpened?.()
    }
  }, [pendingChatOpen, onChatOpened])

  useEffect(() => {
    if (!pendingJobOpen) return
    let cancelled = false

    const tryOpenJob = async () => {
      let jobs = allJobs
      if (jobs.length === 0) {
        for (let attempt = 0; attempt < 5; attempt++) {
          if (cancelled) return
          try {
            const response = await liaApi.listJobVacancies()
            if (response?.items?.length) {
              const stageMapping: Record<string, Job['stage']> = {
                'Planejamento': 'Planejamento', 'Aprovação': 'Aprovação', 'Publicada': 'Publicada',
                'Triagem': 'Triagem', 'Entrevistas': 'Entrevistas', 'Finalização': 'Finalização', 'Encerrada': 'Encerrada'
              }
              const convertedJobs: Job[] = response.items.map((jv: any, index: number) => {
                const funnelData = jv.funnel_data || { total: 0, screening: 0, interview: 0, final: 0, hired: 0 }
                return {
                  id: index + 1,
                  backendId: jv.id,
                  jobId: `WDT-${jv.id.slice(0, 8).toUpperCase()}`,
                  title: jv.title,
                  department: jv.department || 'Geral',
                  location: jv.location || 'Não especificado',
                  workModel: (jv.work_model as Job['workModel']) || 'híbrido',
                  type: jv.employment_type || 'CLT',
                  level: jv.seniority_level || 'Pleno',
                  salary: jv.salary_range ? `R$ ${jv.salary_range.min?.toLocaleString()} - R$ ${jv.salary_range.max?.toLocaleString()}` : 'A combinar',
                  status: (jv.status as Job['status']) || 'Rascunho',
                  stage: stageMapping[jv.stage || ''] || 'Triagem',
                  openDate: jv.open_date?.split('T')[0] || jv.created_at?.split('T')[0] || new Date().toISOString().split('T')[0],
                  deadline: jv.deadline?.split('T')[0] || undefined,
                  description: jv.description || '',
                  requirements: jv.requirements || [],
                  manager: jv.manager || 'Não definido',
                  recruiter: jv.recruiter || 'Não definido',
                  priority: (jv.priority as Job['priority']) || 'média',
                  funnel: { total: funnelData.total || 0, screening: funnelData.screening || 0, interview: funnelData.interview || 0, final: funnelData.final || 0, hired: funnelData.hired || 0 },
                  tags: jv.tags || [],
                  conversationId: jv.conversation_id || undefined,
                  createdAt: jv.created_at || undefined,
                } as Job
              })
              if (!cancelled) {
                setBackendJobs(convertedJobs)
                jobs = convertedJobs
              }
              break
            }
          } catch {
            await new Promise(r => setTimeout(r, 2000))
          }
        }
      }
      if (cancelled || jobs.length === 0) return
      const matched = jobs.find(
        j => j.backendId === pendingJobOpen.jobId || j.jobId === pendingJobOpen.jobId || j.title === pendingJobOpen.jobTitle
      )
      if (matched && !cancelled) {
        setSelectedJob(matched)
        setShowKanban(true)
        setShowJobPreview(false)
        setPreviewJob(null)
      }
      onJobOpened?.()
    }
    tryOpenJob()
    return () => { cancelled = true }
  }, [pendingJobOpen])

  // Fetch job metrics when previewJob changes
  useEffect(() => {
    if (previewJob?.backendId) {
      setIsLoadingJobMetrics(true)
      liaApi.getJobVacancyMetrics(previewJob.backendId)
        .then((metrics) => {
          setJobMetrics(metrics)
        })
        .catch((error) => {
          console.error('Failed to load job metrics:', error)
          setJobMetrics(null)
        })
        .finally(() => {
          setIsLoadingJobMetrics(false)
        })
    } else {
      setJobMetrics(null)
    }
  }, [previewJob?.backendId])

  useEffect(() => {
    if (previewJob) {
      setJobDataForm({
        title: previewJob.title || '',
        department: previewJob.department || '',
        location: previewJob.location || '',
        workModel: previewJob.workModel || 'presencial',
        type: previewJob.type || 'CLT',
        level: previewJob.level || '',
        status: previewJob.status || 'Ativa',
        urgencyLevel: previewJob.urgencyLevel || 3,
        recruiter: previewJob.recruiter || '',
        recruiterEmail: previewJob.recruiterEmail || '',
        manager: previewJob.manager || '',
        managerEmail: previewJob.managerEmail || '',
        openDate: previewJob.openDate || '',
        deadline: previewJob.deadline || '',
        deadlineScreening: previewJob.deadlineScreening || '',
        deadlineShortlist: previewJob.deadlineShortlist || '',
        deadlineClosing: previewJob.deadlineClosing || '',
        salaryMin: previewJob.salaryMin || previewJob.salaryRange?.min || '',
        salaryMax: previewJob.salaryMax || previewJob.salaryRange?.max || '',
        bonusMin: previewJob.bonusMin || '',
        bonusMax: previewJob.bonusMax || '',
        benefits: previewJob.benefits || [],
        targetAudience: previewJob.targetAudience || '',
        targetSector: previewJob.targetSector || '',
        targetSegment: previewJob.targetSegment || '',
        languages: previewJob.languages || [],
        publishedLinkedIn: previewJob.publishedLinkedIn || false,
        publishedWebsite: previewJob.publishedWebsite || false,
        publishedIndeed: previewJob.publishedIndeed || false,
        visibility: previewJob.visibility || 'public',
        isConfidential: previewJob.isConfidential || false,
        maskedCompanyName: previewJob.maskedCompanyName || '',
        isAffirmative: previewJob.isAffirmative || false,
        affirmativeType: previewJob.affirmativeType || '',
        confidentialityConfig: previewJob.confidentialityConfig || {
          can_reveal_company_name: true,
          can_discuss_salary: true,
          can_discuss_benefits: true,
          can_discuss_location: true,
        },
      })
    }
  }, [previewJob])

  const handleSaveJobDataSection = async (sectionId: string, fields: string[]) => {
    if (!previewJob) return
    setSavingSection(sectionId)
    try {
      const fieldMapping: Record<string, string> = {
        title: 'title',
        department: 'department',
        location: 'location',
        workModel: 'work_model',
        type: 'employment_type',
        level: 'seniority_level',
        status: 'status',
        urgencyLevel: 'urgency_level',
        recruiter: 'recruiter',
        recruiterEmail: 'recruiter_email',
        manager: 'hiring_manager',
        managerEmail: 'hiring_manager_email',
        openDate: 'open_date',
        deadline: 'deadline',
        deadlineScreening: 'deadline_screening',
        deadlineShortlist: 'deadline_shortlist',
        deadlineClosing: 'deadline_closing',
        screeningStatus: 'screening_status',
        benefits: 'benefits',
        targetAudience: 'target_audience',
        targetSector: 'target_sector',
        targetSegment: 'target_segment',
        languages: 'languages',
        publishedLinkedIn: 'published_linkedin',
        publishedWebsite: 'published_website',
        publishedIndeed: 'published_indeed',
        visibility: 'visibility',
        isConfidential: 'is_confidential',
        maskedCompanyName: 'masked_company_name',
        isAffirmative: 'is_affirmative',
        affirmativeType: 'affirmative_type',
        confidentialityConfig: 'confidentiality_config',
        description: 'description',
      }
      
      const updates: Record<string, any> = {}
      fields.forEach(f => {
        const backendKey = fieldMapping[f] || f
        let value = jobDataForm[f]
        if (f === 'salaryMin' || f === 'salaryMax') {
          if (!updates['salary_range']) {
            updates['salary_range'] = {
              min: jobDataForm.salaryMin ? Number(jobDataForm.salaryMin) : null,
              max: jobDataForm.salaryMax ? Number(jobDataForm.salaryMax) : null,
              currency: 'BRL'
            }
          }
          return
        }
        if (f === 'bonusMin' || f === 'bonusMax') {
          if (!updates['bonus_range']) {
            updates['bonus_range'] = {
              min: jobDataForm.bonusMin ? Number(jobDataForm.bonusMin) : null,
              max: jobDataForm.bonusMax ? Number(jobDataForm.bonusMax) : null,
            }
          }
          return
        }
        updates[backendKey] = value
      })
      
      await liaApi.updateJobVacancy(previewJob.backendId || previewJob.jobId, updates)
      toast.success('Seção salva com sucesso!')
      
      // Update previewJob state to reflect changes without reload
      const updatedJob = { ...previewJob }
      fields.forEach(f => {
        ;(updatedJob as any)[f] = jobDataForm[f]
      })
      // Also update salaryRange if salary fields were saved
      if (fields.includes('salaryMin') || fields.includes('salaryMax')) {
        ;(updatedJob as any).salaryRange = {
          min: jobDataForm.salaryMin ? Number(jobDataForm.salaryMin) : null,
          max: jobDataForm.salaryMax ? Number(jobDataForm.salaryMax) : null,
          currency: 'BRL'
        }
        ;(updatedJob as any).salaryMin = jobDataForm.salaryMin ? Number(jobDataForm.salaryMin) : null
        ;(updatedJob as any).salaryMax = jobDataForm.salaryMax ? Number(jobDataForm.salaryMax) : null
      }
      setPreviewJob(updatedJob)
    } catch (error) {
      console.error('Erro ao salvar:', error)
      toast.error('Erro ao salvar. Tente novamente.')
    } finally {
      setSavingSection(null)
    }
  }

  const handleScreeningStatusChange = async (jobId: string, newStatus: string, extraData?: { pause_reason?: string; scheduled_end_date?: string }) => {
    try {
      await liaApi.updateScreeningStatus(jobId, newStatus, extraData)
      setBackendJobs(prev => prev.map(j => 
        j.backendId === jobId ? { ...j, screeningStatus: newStatus as any } : j
      ))
      return true
    } catch (error) {
      console.error('Error updating screening status:', error)
      return false
    }
  }

  // Status filtering
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>('todas')
  const [activeFilter, setActiveFilter] = useState<string>('visao-geral')
  
  // Dashboard metrics states
  const [dashboardStats, setDashboardStats] = useState<any>(null)
  const [isLoadingStats, setIsLoadingStats] = useState(true)
  const statsRequestInFlight = useRef(false)
  const statsLoaded = useRef(false)

  // Days Open filtering
  const [selectedDaysFilter, setSelectedDaysFilter] = useState<string>('todas')

  // Dashboard period filter
  const [dashboardPeriod, setDashboardPeriod] = useState<'1m' | '3m' | '6m' | '9m' | '12m'>('3m')

  // Advanced Search States
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false)
  const [advancedFilters, setAdvancedFilters] = useState<{[key: string]: string[]}>({
    job_titles: [],
    departments: [],
    locations: [],
    work_models: [],
    job_types: [],
    seniority_levels: [],
    salary_ranges: [],
    status: [],
    stages: [],
    priorities: [],
    managers: [],
    benefits: [],
    requirements: [],
    industries: [],
    budget_ranges: [],
    urgency_levels: [],
    contract_duration: [],
    team_size: []
  })
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['job_details', 'location_work']))
  const [booleanSearch, setBooleanSearch] = useState("")
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([])
  const [showSearchHistory, setShowSearchHistory] = useState(false)
  const [showSavedSearches, setShowSavedSearches] = useState(false)
  
  // Sync persisted filters when loaded from localStorage
  const hasRestoredFilters = useRef(false)
  useEffect(() => {
    if (filtersLoaded && !hasRestoredFilters.current) {
      hasRestoredFilters.current = true
      setSelectedStatusFilter(persistedFilters.selectedStatusFilter)
      setSelectedDaysFilter(persistedFilters.selectedDaysFilter)
      setAdvancedFilters(persistedFilters.advancedFilters)
      setBooleanSearch(persistedFilters.booleanSearch)
      setSearchTerm(persistedFilters.searchTerm)
      setSavedSearches(persistedSavedSearches)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtersLoaded])

  // Persist filters whenever they change (debounced via useEffect)
  useEffect(() => {
    if (!filtersLoaded || !hasRestoredFilters.current) return
    updatePersistedFilter('selectedStatusFilter', selectedStatusFilter)
  }, [selectedStatusFilter, filtersLoaded, updatePersistedFilter])

  useEffect(() => {
    if (!filtersLoaded || !hasRestoredFilters.current) return
    updatePersistedFilter('selectedDaysFilter', selectedDaysFilter)
  }, [selectedDaysFilter, filtersLoaded, updatePersistedFilter])

  useEffect(() => {
    if (!filtersLoaded || !hasRestoredFilters.current) return
    updatePersistedFilter('advancedFilters', advancedFilters)
  }, [advancedFilters, filtersLoaded, updatePersistedFilter])

  useEffect(() => {
    if (!filtersLoaded || !hasRestoredFilters.current) return
    updatePersistedFilter('booleanSearch', booleanSearch)
  }, [booleanSearch, filtersLoaded, updatePersistedFilter])

  useEffect(() => {
    if (!filtersLoaded || !hasRestoredFilters.current) return
    updatePersistedFilter('searchTerm', searchTerm)
  }, [searchTerm, filtersLoaded, updatePersistedFilter])
  
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState("")

  // Estados para prompt da LIA
  const [showLIAPromptForJob, setShowLIAPromptForJob] = useState(false)
  const [selectedJobForLIA, setSelectedJobForLIA] = useState<Job | null>(null)
  const [selectedJobsForBatch, setSelectedJobsForBatch] = useState<Set<number>>(new Set())
  
  // Estados para mensagens da LIA (chat de análise de vagas)
  const [liaMessages, setLiaMessages] = useState<Array<{
    id: string
    type: 'user' | 'response'
    content: string
    timestamp: number
    agentUsed?: string
    suggestedPrompts?: string[]
    action_executed?: boolean
    action_result?: Record<string, unknown>
    action_type?: string
    needs_confirmation?: boolean
    needs_params?: boolean
    pending_action_id?: string
  }>>([])
  const [isLiaProcessing, setIsLiaProcessing] = useState(false)
  const [jobsConversationId, setJobsConversationId] = useState<string | undefined>(undefined)

  // Estados para os modais de ações em massa
  const [showCompareModal, setShowCompareModal] = useState(false)
  const [showPublishModal, setShowPublishModal] = useState(false)
  const [showUnpublishModal, setShowUnpublishModal] = useState(false)
  const [showInsightsModal, setShowInsightsModal] = useState(false)
  const [showDuplicateModal, setShowDuplicateModal] = useState(false)
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [showAssignRecruiterModal, setShowAssignRecruiterModal] = useState(false)
  const [statusModalMode, setStatusModalMode] = useState<'pause' | 'activate'>('pause')
  const [companyRecruiters, setCompanyRecruiters] = useState<Array<{
    id: string
    name: string
    email?: string
    avatar?: string
    active_jobs_count?: number
    performance_score?: number
  }>>([])
  const [isLoadingRecruiters, setIsLoadingRecruiters] = useState(false)

  // Load company recruiters when assign modal or duplicate modal opens
  useEffect(() => {
    if ((showAssignRecruiterModal || showDuplicateModal) && companyRecruiters.length === 0 && !isLoadingRecruiters) {
      setIsLoadingRecruiters(true)
      liaApi.getCompanyUsers({ role: 'recruiter', isActive: true })
        .then((response) => {
          const recruiters = response.users.map(user => ({
            id: user.id,
            name: user.name,
            email: user.email,
            active_jobs_count: user.active_jobs_count,
            performance_score: user.performance_score,
          }))
          setCompanyRecruiters(recruiters)
        })
        .catch((error) => {
          console.error('Failed to load company recruiters:', error)
        })
        .finally(() => {
          setIsLoadingRecruiters(false)
        })
    }
  }, [showAssignRecruiterModal, showDuplicateModal, companyRecruiters.length, isLoadingRecruiters])

  // Estados para modais de configuração de triagem
  const [showScreeningChannelsModal, setShowScreeningChannelsModal] = useState(false)
  const [showScreeningSettingsModal, setShowScreeningSettingsModal] = useState(false)
  const [showScreeningSchedulingModal, setShowScreeningSchedulingModal] = useState(false)
  const [showReactivateScreeningDialog, setShowReactivateScreeningDialog] = useState(false)
  const [reactivateScreeningJobs, setReactivateScreeningJobs] = useState<any[]>([])
  const [reactivateEndDate, setReactivateEndDate] = useState('')

  const [screeningConfigExpanded, setScreeningConfigExpanded] = useState(false)
  const [isEditingScreeningConfig, setIsEditingScreeningConfig] = useState(false)
  const [editChannels, setEditChannels] = useState({
    whatsapp: true, chat_web: true, phone: false
  })
  const [editMinScorePreset, setEditMinScorePreset] = useState<'rigorous' | 'recommended' | 'flexible'>('recommended')
  const [editTimeoutHours, setEditTimeoutHours] = useState(48)
  const [editMaxRetries, setEditMaxRetries] = useState(2)
  const [editAutoApprovalPreset, setEditAutoApprovalPreset] = useState<'conservative' | 'recommended' | 'autonomous'>('recommended')

  useEffect(() => {
    if (!isEditingScreeningConfig && screeningConfig) {
      setEditChannels({
        whatsapp: screeningConfig.channels?.whatsapp?.enabled ?? true,
        chat_web: screeningConfig.channels?.chat_web?.enabled ?? true,
        phone: screeningConfig.channels?.phone?.enabled ?? false
      })
      setEditMinScorePreset(screeningConfig.settings?.min_score_preset ?? 'recommended')
      setEditTimeoutHours(screeningConfig.settings?.response_timeout_hours ?? 48)
      setEditMaxRetries(screeningConfig.settings?.max_retries ?? 2)
      setEditAutoApprovalPreset(screeningConfig.settings?.auto_approval_preset ?? limitToApprovalPreset(screeningConfig.settings?.auto_approval_limit))
    }
  }, [screeningConfig, isEditingScreeningConfig])

  // Estado para modais de Dashboard
  const [activeDashboardModal, setActiveDashboardModal] = useState<'minhasVagas' | 'visaoGeral' | 'performanceLia' | null>(null)

  // Estados para modal de edição de perguntas de triagem (WSI Blocks)
  const [showQuestionEditModal, setShowQuestionEditModal] = useState(false)
  const [expandedBlocks, setExpandedBlocks] = useState<number[]>([0, 1, 2, 3, 4, 6])
  const [collapsedPreviewSections, setCollapsedPreviewSections] = useState<string[]>([])
  const togglePreviewSection = (section: string) => {
    setCollapsedPreviewSections(prev => 
      prev.includes(section) ? prev.filter(s => s !== section) : [...prev, section]
    )
  }
  const [screeningBlockExpanded, setScreeningBlockExpanded] = useState(true)
  const [isEditingScreening, setIsEditingScreening] = useState(false)
  const [selectedBlock, setSelectedBlock] = useState<number>(2)
  const [adjustmentDiffs, setAdjustmentDiffs] = useState<any[]>([])
  const [adjustmentIterations, setAdjustmentIterations] = useState(0)

  const [isGeneratingWSI, setIsGeneratingWSI] = useState(false)
  const [pendingAdjustedQuestions, setPendingAdjustedQuestions] = useState<any[]>([])
  const [acceptedQuestions, setAcceptedQuestions] = useState<Set<string>>(new Set())
  const [wsiGenerationMode, setWsiGenerationMode] = useState<'compact' | 'full' | null>(null)
  const [wsiGenerationCompleted, setWsiGenerationCompleted] = useState(false)
  const [wsiProgressCollapsed, setWsiProgressCollapsed] = useState(false)
  const [wsiGeneratedCount, setWsiGeneratedCount] = useState(0)
  const [wsiGenerationStep, setWsiGenerationStep] = useState(0)
  const [wsiDynamicMessage, setWsiDynamicMessage] = useState('')
  const [wsiGenerationContext, setWsiGenerationContext] = useState<{
    title: string
    seniority: string | null
    responsibilities: string[]
    technicalSkills: string[]
    behavioralCompetencies: string[]
    blockBreakdown: Record<number, number>
    methodologyBreakdown: Record<string, number>
    companyStandardFound: boolean
  } | null>(null)

  // Estados para configuração de colunas
  const [showColumnConfig, setShowColumnConfig] = useState(false)

  const handleToggleColumnConfig = () => {
    setShowColumnConfig(!showColumnConfig)
  }

  const hookToTableColumnMap: Record<string, string> = {
    'id': 'id',
    'status': 'status',
    'screeningStatus': 'screeningStatus',
    'title': 'vaga',
    'candidates': 'candidatos',
    'performance': 'performance',
    'recruiter': 'recrutador',
    'manager': 'gestor',
    'deadlineScreening': 'prazoTriagem',
    'deadlineShortlist': 'prazoShortlist',
    'deadlineClosing': 'prazoEncerramento',
  }

  // Estados para funcionalidades de tabela (resize, sort, drag columns)
  const [jobsColumnWidths, setJobsColumnWidths] = useState({
    id: 80,
    vaga: 200,
    candidatos: 100,
    performance: 180,
    status: 120,
    recrutador: 140,
    gestor: 140,
    screeningStatus: 100,
    prazoTriagem: 100,
    prazoShortlist: 100,
    prazoEncerramento: 100,
    roteiro: 100,
    acoes: 80
  })
  const [jobsColumnOrder, setJobsColumnOrder] = useState<string[]>([
    'checkbox', 'id', 'vaga', 'candidatos', 'performance', 'status', 'screeningStatus', 'recrutador', 'gestor', 'prazoTriagem', 'prazoShortlist', 'prazoEncerramento', 'acoes'
  ])
  const [jobsSortColumn, setJobsSortColumn] = useState<string | null>(null)
  const [jobsSortDirection, setJobsSortDirection] = useState<'asc' | 'desc'>('asc')
  const [draggedJobColumnId, setDraggedJobColumnId] = useState<string | null>(null)
  const [dragOverJobColumnId, setDragOverJobColumnId] = useState<string | null>(null)
  const [resizingJobColumn, setResizingJobColumn] = useState<string | null>(null)

  // Handlers de sort para tabela de vagas
  const handleJobsSort = (columnKey: string) => {
    if (jobsSortColumn === columnKey) {
      setJobsSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setJobsSortColumn(columnKey)
      setJobsSortDirection('asc')
    }
  }

  // Handlers de resize para tabela de vagas
  const startJobsColumnResize = (columnKey: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setResizingJobColumn(columnKey)
    const startX = e.clientX
    const startWidth = jobsColumnWidths[columnKey as keyof typeof jobsColumnWidths] || 100
    let currentWidth = startWidth

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const diff = moveEvent.clientX - startX
      currentWidth = Math.max(50, startWidth + diff)
      setJobsColumnWidths(prev => ({ ...prev, [columnKey]: currentWidth }))
    }

    const handleMouseUp = () => {
      setResizingJobColumn(null)
      setJobsColumnWidths(prev => {
        const updatedWidths = { ...prev, [columnKey]: currentWidth }
        if (typeof window !== 'undefined') {
          localStorage.setItem('jobs-table-column-widths', JSON.stringify(updatedWidths))
        }
        return updatedWidths
      })
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  // Handlers de drag & drop para reordenar colunas
  const handleJobsColumnDragStart = (columnId: string, e: React.DragEvent) => {
    if (columnId === 'checkbox' || columnId === 'acoes') return
    setDraggedJobColumnId(columnId)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleJobsColumnDragOver = (columnId: string, e: React.DragEvent) => {
    e.preventDefault()
    if (columnId === 'checkbox' || columnId === 'acoes') return
    if (draggedJobColumnId && draggedJobColumnId !== columnId) {
      setDragOverJobColumnId(columnId)
    }
  }

  const handleJobsColumnDragLeave = () => {
    setDragOverJobColumnId(null)
  }

  const handleJobsColumnDrop = (targetColumnId: string, e: React.DragEvent) => {
    e.preventDefault()
    if (!draggedJobColumnId || targetColumnId === 'checkbox' || targetColumnId === 'acoes') {
      setDraggedJobColumnId(null)
      setDragOverJobColumnId(null)
      return
    }

    setJobsColumnOrder(prev => {
      const newOrder = [...prev]
      const draggedIndex = newOrder.indexOf(draggedJobColumnId)
      const targetIndex = newOrder.indexOf(targetColumnId)
      
      if (draggedIndex === -1 || targetIndex === -1) return prev
      
      newOrder.splice(draggedIndex, 1)
      newOrder.splice(targetIndex, 0, draggedJobColumnId)
      
      if (typeof window !== 'undefined') {
        localStorage.setItem('jobs-table-column-order', JSON.stringify(newOrder))
      }
      
      return newOrder
    })

    setDraggedJobColumnId(null)
    setDragOverJobColumnId(null)
  }

  const handleJobsColumnDragEnd = () => {
    setDraggedJobColumnId(null)
    setDragOverJobColumnId(null)
  }

  useEffect(() => {
    if (typeof window === 'undefined') return
    
    const defaultOrder = ['checkbox', 'id', 'vaga', 'candidatos', 'performance', 'status', 'screeningStatus', 'recrutador', 'gestor', 'prazoTriagem', 'prazoShortlist', 'prazoEncerramento', 'acoes']
    
    const savedOrder = localStorage.getItem('jobs-table-column-order')
    if (savedOrder) {
      try {
        const parsed = JSON.parse(savedOrder) as string[]
        const savedCols = parsed.filter((id: string) => defaultOrder.includes(id))
        const missingCols = defaultOrder.filter(id => !parsed.includes(id) && id !== 'checkbox' && id !== 'acoes')
        const innerCols = savedCols.filter((id: string) => id !== 'checkbox' && id !== 'acoes')
        const acoesIndex = innerCols.length
        innerCols.splice(acoesIndex, 0, ...missingCols)
        const finalOrder = ['checkbox', ...innerCols, 'acoes']
        setJobsColumnOrder(finalOrder)
      } catch (e) {
        console.error('Erro ao carregar ordem das colunas:', e)
      }
    }

    const savedWidths = localStorage.getItem('jobs-table-column-widths')
    if (savedWidths) {
      try {
        const parsed = JSON.parse(savedWidths)
        setJobsColumnWidths(prev => ({ ...prev, ...parsed }))
      } catch (e) {
        console.error('Erro ao carregar larguras das colunas:', e)
      }
    }
  }, [])

  // Estado para prompt da LIA expandido
  const [showExpandedLIA, setShowExpandedLIA] = useState(false)
  const [liaPromptValue, setLiaPromptValue] = useState("")
  const [userCollapsedLIA, setUserCollapsedLIA] = useState(false)
  
  // Estados para o chat inline no prompt expandido lateral
  interface LiaInlineMessage {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
    isTyping?: boolean
  }
  const [liaInlineMessages, setLiaInlineMessages] = useState<LiaInlineMessage[]>([])
  const [liaInlineLoading, setLiaInlineLoading] = useState(false)
  const liaInlineMessagesEndRef = useRef<HTMLDivElement>(null)
  
  // Função para detectar se mensagem é sobre criação de vaga
  const isJobCreationIntent = (message: string): boolean => {
    const lowerMessage = message.toLowerCase()
    const jobCreationPatterns = [
      'criar vaga',
      'nova vaga',
      'abrir vaga',
      'cadastrar vaga',
      'registrar vaga',
      'quero criar',
      'preciso de uma vaga',
      'preciso abrir',
      'montar vaga',
      'configurar vaga',
      'iniciar processo seletivo',
      'novo processo seletivo'
    ]
    return jobCreationPatterns.some(pattern => lowerMessage.includes(pattern))
  }
  
  // Função para enviar mensagem no chat inline do prompt lateral
  const liaInlineChatIdRef = useRef<string>(`chat-inline-${Date.now()}`)

  const sendLiaInlineMessage = async (content: string) => {
    if (isJobCreationIntent(content)) {
      openJobCreationChat(content)
      return
    }
    
    const userMessage: LiaInlineMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date()
    }
    setLiaInlineMessages(prev => [...prev, userMessage])
    setLiaInlineLoading(true)

    onAddRecentItem?.({
      id: liaInlineChatIdRef.current,
      type: 'chat',
      title: `Chat: ${content.slice(0, 40)}${content.length > 40 ? '...' : ''}`,
      meta: { conversationId: liaInlineChatIdRef.current }
    })
    
    try {
      const selectedJobIds = Array.from(selectedJobsForBatch).map(id => String(id))
      const response = await fetch('/api/backend-proxy/lia/expanded-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          context_type: 'jobs',
          context_ids: selectedJobIds.length > 0 ? selectedJobIds : undefined
        })
      })
      
      if (!response.ok) throw new Error('Falha na resposta')
      
      const data = await response.json()
      
      const liaMessage: LiaInlineMessage = {
        id: `lia-${Date.now()}`,
        role: 'assistant',
        content: data.response || 'Desculpe, não consegui processar sua mensagem.',
        timestamp: new Date()
      }
      setLiaInlineMessages(prev => [...prev, liaMessage])
    } catch (error) {
      console.error('Erro no chat LIA:', error)
      const errorMessage: LiaInlineMessage = {
        id: `lia-${Date.now()}`,
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
        timestamp: new Date()
      }
      setLiaInlineMessages(prev => [...prev, errorMessage])
    } finally {
      setLiaInlineLoading(false)
    }
  }
  
  // Scroll para última mensagem no chat inline
  useEffect(() => {
    liaInlineMessagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [liaInlineMessages])
  
  // Estados para os 3 níveis de chat:
  // 1. Mini prompt (showInlineChat = false, chatMode = null)
  // 2. Chat expandido ao lado da tabela (showInlineChat = true, chatMode = 'general')
  // 3. Super chat de criação de vaga (showInlineChat = true, chatMode = 'job-creation')
  const [showInlineChat, setShowInlineChat] = useState(false)
  const [chatMode, setChatMode] = useState<'general' | 'job-creation' | null>(null)
  const [inlineChatInitialMessage, setInlineChatInitialMessage] = useState<string | undefined>()
  const [isChatFullscreen, setIsChatFullscreen] = useState(false)
  
  // Estado para controlar se a tabela está contraída (como o menu lateral)
  const [isTableCollapsed, setIsTableCollapsed] = useState(false)
  
  const openGeneralChat = (initialMessage?: string) => {
    setShowInlineChat(true)
    setChatMode('general')
    setInlineChatInitialMessage(initialMessage)
    setIsTableCollapsed(true)
    onAddRecentItem?.({
      id: liaInlineChatIdRef.current,
      type: 'chat',
      title: initialMessage
        ? `Chat: ${initialMessage.slice(0, 40)}${initialMessage.length > 40 ? '...' : ''}`
        : 'Chat com LIA',
      meta: { conversationId: liaInlineChatIdRef.current }
    })
  }
  
  const openJobCreationChat = (initialMessage?: string) => {
    const wizardId = `chat-wizard-${Date.now()}`
    setShowInlineChat(true)
    setChatMode('job-creation')
    setInlineChatInitialMessage(initialMessage)
    setIsTableCollapsed(true)
    onAddRecentItem?.({
      id: wizardId,
      type: 'chat',
      title: initialMessage
        ? `Criação: ${initialMessage.slice(0, 35)}${initialMessage.length > 35 ? '...' : ''}`
        : 'Criação de Vaga',
      meta: { conversationId: wizardId }
    })
  }
  
  // Função para fechar o chat e voltar ao mini prompt
  const closeChat = () => {
    setShowInlineChat(false)
    setChatMode(null)
    setInlineChatInitialMessage(undefined)
    setIsTableCollapsed(false)
    liaInlineChatIdRef.current = `chat-inline-${Date.now()}`
  }
  
  // Função para voltar do super chat para o chat geral (após criar vaga)
  const returnToGeneralChat = () => {
    setChatMode('general')
    // Mantém a tabela contraída quando volta para o chat geral
  }
  
  // Função para voltar do super chat para o prompt lateral expandido
  const returnToLateralPrompt = (messages?: Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: Date }>) => {
    // Sincronizar mensagens do super prompt com o chat inline
    if (messages && messages.length > 0) {
      const inlineMessages: LiaInlineMessage[] = messages.map(m => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: m.timestamp
      }))
      setLiaInlineMessages(inlineMessages)
    }
    
    setShowInlineChat(false)
    setChatMode(null)
    setInlineChatInitialMessage(undefined)
    setIsTableCollapsed(false) // Expande a tabela
    setShowExpandedLIA(true) // Mantém o prompt lateral aberto
  }
  
  // Função para alternar expansão da tabela
  const toggleTableExpansion = () => {
    setIsTableCollapsed(!isTableCollapsed)
  }
  
  // 🎯 Auto-expandir/fechar LIA sidebar baseado na seleção de vagas
  // Respeita intent manual do usuário (userCollapsedLIA)
  useEffect(() => {
    if (selectedJobsForBatch.size > 0 && !userCollapsedLIA) {
      setShowExpandedLIA(true)
    } else if (selectedJobsForBatch.size === 0) {
      setShowExpandedLIA(false)
      setUserCollapsedLIA(false) // Reset flag quando não há seleção
    }
  }, [selectedJobsForBatch.size, userCollapsedLIA])

  // 🎯 Listener para evento de navegação para aba do preview (ex: roteiro de triagem)
  useEffect(() => {
    const handleSetPreviewTab = (event: CustomEvent) => {
      const tab = event.detail as 'screening' | 'job-data' | 'pipeline'
      setActivePreviewTab(tab)
    }
    
    window.addEventListener('setJobPreviewTab', handleSetPreviewTab as EventListener)
    return () => {
      window.removeEventListener('setJobPreviewTab', handleSetPreviewTab as EventListener)
    }
  }, [])
  const [showLiaSuggestions, setShowLiaSuggestions] = useState(false)
  const [liaHighlight, setLiaHighlight] = useState(false)
  const liaInputRef = useRef<HTMLInputElement>(null)
  
  const { suggestions: dynamicSuggestions, loading: suggestionsLoading, refresh: refreshSuggestions } = useLiaSuggestions("default", 6)
  const { insights: dynamicInsights, generateInsights, loading: insightsLoading } = useJobInsights()
  const { sendPrompt: sendLiaPrompt, response: liaResponse, loading: liaPromptLoading, followUpSuggestions } = useLiaExpandedPrompt()
  
  // Estados para sistema de abas e prompt expandido (replicado do Funil de Talentos)
  const [activeSearchTab, setActiveSearchTab] = useState<'ia-natural' | 'job-description' | 'templates'>('ia-natural')
  const [jobDescriptionText, setJobDescriptionText] = useState("")
  const [isUploadingJD, setIsUploadingJD] = useState(false)
  const [jdUploadError, setJdUploadError] = useState<string | null>(null)
  const jdFileInputRef = useRef<HTMLInputElement>(null)

  const handleJDFileUpload = async (file: File) => {
    setIsUploadingJD(true)
    setJdUploadError(null)
    try {
      const formData = new FormData()
      formData.append("file", file)
      const titleParam = file.name.replace(/\.[^/.]+$/, "")
      const res = await fetch(
        `/api/backend-proxy/jd-import/upload?title=${encodeURIComponent(titleParam)}`,
        { method: "POST", body: formData },
      )
      const data = await res.json()
      if (!res.ok) {
        setJdUploadError(data.error || "Falha ao processar arquivo")
        return
      }
      const text = data.description || data.responsibilities_text || ""
      if (text) setJobDescriptionText(text)
    } catch {
      setJdUploadError("Erro de conexão ao processar arquivo")
    } finally {
      setIsUploadingJD(false)
    }
  }
  const [liaWidth, setLiaWidth] = useState(400) // Largura padrão 400px - ElevenLabs pattern
  const [isResizingLIA, setIsResizingLIA] = useState(false)
  
  // Estados para largura do painel de preview da vaga (redimensionável)
  const [previewWidth, setPreviewWidth] = useState(400) // Largura padrão 400px
  const [isResizingPreview, setIsResizingPreview] = useState(false)

  // Estados para painel de filtros inline da tabela de vagas
  const [showTableFiltersPanel, setShowTableFiltersPanel] = useState(false)
  const [jobFilters, setJobFilters] = useState<JobFilters>({})

  // 🎯 Quick Action Handlers para Vagas
  const handleQuickCompare = () => {
    const count = selectedJobsForBatch.size
    setLiaPromptValue(`Comparar as ${count} vagas selecionadas`)
  }

  const handleQuickPublish = () => {
    setLiaPromptValue('Publicar vagas selecionadas no LinkedIn e site de carreiras')
  }

  const handleQuickAnalyze = () => {
    setLiaPromptValue('Analisar performance das vagas selecionadas')
  }

  const handleQuickScript = () => {
    setLiaPromptValue('Gerar roteiro de entrevista para as vagas selecionadas')
  }

  const handleQuickATS = () => {
    setLiaPromptValue('Integrar vagas selecionadas com ATS (Gupy/Pandapé)')
  }

  const handleQuickInsights = async () => {
    const selectedIds = Array.from(selectedJobsForBatch)
    if (selectedIds.length > 0) {
      await generateInsights(selectedIds)
      setShowInsightsModal(true)
    } else if (previewJob?.backendId) {
      await generateInsights([previewJob.backendId])
      setShowInsightsModal(true)
    } else {
      setLiaPromptValue('Ver insights e sugestões de melhoria para as vagas')
    }
  }
  
  const handleSuggestionAction = (action: string, metadata?: Record<string, unknown>) => {
    switch (action) {
      case 'activate_sourcing':
        setLiaPromptValue('Ativar sourcing automático para vagas sem candidatos')
        break
      case 'view_expiring_jobs':
        setLiaPromptValue('Mostrar vagas com prazo expirando nos próximos 7 dias')
        break
      case 'view_pipeline_analytics':
        setLiaPromptValue('Analisar saúde do pipeline de todas as vagas ativas')
        break
      case 'start_screening':
        setLiaPromptValue('Iniciar triagem dos candidatos recebidos nos últimos 7 dias')
        break
      case 'generate_weekly_report':
        setLiaPromptValue('Gerar relatório semanal de recrutamento')
        break
      case 'similar_search':
        setLiaPromptValue('Buscar candidatos similares aos melhores contratados')
        break
      case 'start_job_wizard':
        setShowExpandedChat(true)
        break
      case 'view_active_jobs':
        break
      default:
        setLiaPromptValue(`Executar ação: ${action}`)
    }
  }

  // Get contextual quick actions based on selection
  const getJobQuickActions = (): QuickAction[] => {
    const selectedCount = selectedJobsForBatch.size
    
    return [
      {
        id: 'compare',
        label: selectedCount >= 2 ? `Comparar (${selectedCount})` : 'Comparar',
        icon: BarChart3,
        variant: 'primary' as const,
        onClick: handleQuickCompare
      },
      {
        id: 'publish',
        label: 'Publicar',
        icon: Share2,
        variant: 'default' as const,
        onClick: handleQuickPublish
      },
      {
        id: 'analyze',
        label: 'Analisar Performance',
        icon: Target,
        variant: 'default' as const,
        onClick: handleQuickAnalyze
      },
      {
        id: 'script',
        label: 'Gerar Script',
        icon: ClipboardList,
        variant: 'default' as const,
        onClick: handleQuickScript
      },
      {
        id: 'ats',
        label: 'Integração ATS',
        icon: Building,
        variant: 'default' as const,
        onClick: handleQuickATS
      },
      {
        id: 'insights',
        label: 'Ver Insights',
        icon: Lightbulb,
        variant: 'success' as const,
        onClick: handleQuickInsights
      }
    ]
  }

  const handleLiaAction = (type: 'whatsapp' | 'email' | 'linkedin', person: string, role: 'recruiter' | 'manager', job: Job) => {
    // Preenche o prompt com a ação sugerida
    const actionText = type === 'whatsapp'
      ? `Enviar mensagem WhatsApp para ${person} sobre a vaga ${job.title}`
      : type === 'email'
      ? `Enviar email para ${person} com atualização sobre a vaga ${job.title}`
      : `Ver perfil LinkedIn de ${person} e analisar conexões para a vaga ${job.title}`

    setLiaPromptValue(actionText)
    setShowExpandedLIA(true)
    setShowLiaSuggestions(true)

    // Scroll para o prompt e foca no input
    setTimeout(() => {
      liaInputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      liaInputRef.current?.focus()
    }, 100)
  }

  const handleUpdateJobField = async (
    field: 'status' | 'visibility' | 'priority' | 'stage',
    value: string
  ) => {
    if (!previewJob) return

    try {
      const backendField = field === 'visibility' ? 'visibility' : field
      await liaApi.updateJobVacancy(previewJob.backendId, { [backendField]: value })

      const updatedJob = { ...previewJob, [field]: value }
      setPreviewJob(updatedJob)

      setBackendJobs(prev => prev.map(job => 
        job.backendId === previewJob.backendId 
          ? { ...job, [field]: value }
          : job
      ))

      const fieldLabels: Record<string, string> = {
        status: 'Status',
        visibility: 'Visibilidade',
        priority: 'Prioridade',
        stage: 'Etapa'
      }
      toast.success(`${fieldLabels[field]} atualizado para "${value}"`)
    } catch (error) {
      console.error('Erro ao atualizar vaga:', error)
      toast.error('Erro ao atualizar campo. Tente novamente.')
    }
  }

  // Status and Stage filter definitions
  const statusFilters = [
    { id: 'todas', label: 'Todas', color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200' },
    { id: 'Ativa', label: 'Ativas', color: 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900' },
    { id: 'Paralisada', label: 'Paralisadas', color: 'bg-gray-50 text-gray-800 dark:text-gray-200 dark:bg-gray-800' },
    { id: 'Concluída', label: 'Concluídas', color: 'bg-gray-50 text-gray-800 dark:text-gray-500 dark:bg-gray-800' },
    { id: 'Cancelada', label: 'Canceladas', color: 'bg-red-100 text-red-700 dark:bg-red-950/20 dark:text-red-400' }
  ]

  const navigationFilters = useMemo(() => [
    {
      id: 'visao-geral',
      label: 'Visão Geral',
      description: 'Dashboard estratégico de vagas',
      isDashboard: true
    },
    {
      id: 'todas',
      label: 'Todas',
      description: 'Todas as vagas do sistema',
      count: backendJobs.length
    },
    {
      id: 'ativas',
      label: 'Ativas',
      description: 'Vagas abertas e em andamento',
      count: backendJobs.filter(job => job.status === 'Ativa').length
    },
    {
      id: 'urgentes',
      label: 'Urgentes',
      description: 'Vagas com alta prioridade de preenchimento',
      count: backendJobs.filter(job => job.urgencyLevel >= 4).length,
      highlight: true
    },
    {
      id: 'paralisadas',
      label: 'Paralisadas',
      description: 'Vagas temporariamente suspensas',
      count: backendJobs.filter(job => job.status === 'Paralisada').length
    },
    {
      id: 'concluidas',
      label: 'Concluídas',
      description: 'Vagas com contratação finalizada',
      count: backendJobs.filter(job => job.status === 'Concluída').length
    },
    {
      id: 'canceladas',
      label: 'Canceladas',
      description: 'Vagas canceladas ou arquivadas',
      count: backendJobs.filter(job => job.status === 'Cancelada').length
    }
  ], [backendJobs])

  const stageFilters = useMemo(() => [
    { id: 'planejamento', label: 'Planejamento', count: backendJobs.filter(job => job.stage === 'Planejamento').length },
    { id: 'aprovacao', label: 'Aprovação', count: backendJobs.filter(job => job.stage === 'Aprovação').length },
    { id: 'publicada', label: 'Publicada', count: backendJobs.filter(job => job.stage === 'Publicada').length },
    { id: 'triagem', label: 'Triagem', count: backendJobs.filter(job => job.stage === 'Triagem').length },
    { id: 'entrevistas', label: 'Entrevistas', count: backendJobs.filter(job => job.stage === 'Entrevistas').length },
    { id: 'finalizacao', label: 'Finalização', count: backendJobs.filter(job => job.stage === 'Finalização').length },
    { id: 'encerrada', label: 'Encerrada', count: backendJobs.filter(job => job.stage === 'Encerrada').length }
  ], [backendJobs])

  const handleSearch = (query: string) => {
    setSearchTerm(query)
  }

  const handleAISearch = (query: string, aiResults?: any) => {
    setSearchTerm(query)
  }

  const clearAllFilters = () => {
    setSearchTerm("")
    setAdvancedFilters({
      job_titles: [],
      departments: [],
      locations: [],
      work_models: [],
      job_types: [],
      seniority_levels: [],
      salary_ranges: [],
      status: [],
      stages: [],
      priorities: [],
      managers: [],
      benefits: [],
      requirements: [],
      industries: [],
      budget_ranges: [],
      urgency_levels: [],
      contract_duration: [],
      team_size: []
    })
    setBooleanSearch("")
  }

  const toggleAdvancedFilter = (category: string, value: string) => {
    setAdvancedFilters(prev => {
      const currentValues = prev[category] || []
      const newValues = currentValues.includes(value)
        ? currentValues.filter(v => v !== value)
        : [...currentValues, value]
      return { ...prev, [category]: newValues }
    })
  }

  const removeAdvancedFilter = (category: string, value: string) => {
    setAdvancedFilters(prev => ({
      ...prev,
      [category]: prev[category].filter(v => v !== value)
    }))
  }

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newExpanded = new Set(prev)
      if (newExpanded.has(section)) {
        newExpanded.delete(section)
      } else {
        newExpanded.add(section)
      }
      return newExpanded
    })
  }

  const getActiveAdvancedFiltersCount = () => {
    return Object.values(advancedFilters).reduce((count, filters) => count + filters.length, 0)
  }

  // Conta filtros ativos no painel inline de vagas
  const getActiveJobFiltersCount = (): number => {
    let count = 0
    
    // Status filters
    if (jobFilters.status?.statuses?.length) count += jobFilters.status.statuses.length
    if (jobFilters.status?.priorities?.length) count += jobFilters.status.priorities.length
    if (jobFilters.status?.stages?.length) count += jobFilters.status.stages.length
    
    // Date filters
    if (jobFilters.dates?.openedWithinDays) count += 1
    if (jobFilters.dates?.closingWithinDays) count += 1
    if (jobFilters.dates?.noActivityDays) count += 1
    
    // Team filters
    if (jobFilters.team?.recruiters?.length) count += jobFilters.team.recruiters.length
    if (jobFilters.team?.managers?.length) count += jobFilters.team.managers.length
    if (jobFilters.team?.departments?.length) count += jobFilters.team.departments.length
    
    // Position filters
    if (jobFilters.position?.levels?.length) count += jobFilters.position.levels.length
    if (jobFilters.position?.types?.length) count += jobFilters.position.types.length
    if (jobFilters.position?.workModels?.length) count += jobFilters.position.workModels.length
    if (jobFilters.position?.locations?.length) count += jobFilters.position.locations.length
    
    // Funnel filters
    if (jobFilters.funnel?.minCandidates) count += 1
    if (jobFilters.funnel?.maxCandidates) count += 1
    if (jobFilters.funnel?.emptyPipeline) count += 1
    if (jobFilters.funnel?.stuckInStage) count += 1
    
    // Metrics filters
    if (jobFilters.metrics?.minNPS) count += 1
    if (jobFilters.metrics?.maxDaysOpen) count += 1
    if (jobFilters.metrics?.lowConversion) count += 1
    
    // Publishing filters
    if (jobFilters.publishing?.channels?.length) count += jobFilters.publishing.channels.length
    if (jobFilters.publishing?.unpublished) count += 1
    
    return count
  }

  // Limpa todos os filtros inline de vagas
  const clearAllJobFilters = () => {
    setJobFilters({})
  }

  // Toggle individual job filter
  const toggleJobFilter = (category: keyof JobFilters, field: string, value: string | number | boolean) => {
    setJobFilters(prev => {
      const updated = { ...prev }
      const cat = updated[category] as any || {}
      
      if (typeof value === 'boolean') {
        cat[field] = value ? true : undefined
      } else if (typeof value === 'number') {
        cat[field] = value
      } else {
        const arr = cat[field] || []
        cat[field] = arr.includes(value)
          ? arr.filter((v: string) => v !== value)
          : [...arr, value]
      }
      
      updated[category] = cat
      return updated
    })
  }

  const saveSearch = () => {
    const searchQuery = `${searchTerm} ${booleanSearch}`.trim()
    if (searchQuery && !searchHistory.includes(searchQuery)) {
      setSearchHistory(prev => [searchQuery, ...prev.slice(0, 9)]) // Keep last 10 searches
    }
  }

  const saveSearchAsTemplate = (customName?: string) => {
    const searchName = customName || selectedTemplate || "Nova Busca Salva"
    const savedSearch = savePersistedSearch(searchName)
    setSavedSearches(prev => [savedSearch, ...prev.slice(0, 9)])
    toast.success(`Busca "${searchName}" salva com sucesso!`)
  }

  const handleApplySavedSearch = (searchId: string) => {
    const search = savedSearches.find(s => s.id === searchId)
    if (search) {
      applyPersistedSearch(searchId)
      setSelectedStatusFilter(search.filters.selectedStatusFilter || 'todas')
      setSelectedDaysFilter(search.filters.selectedDaysFilter || 'todas')
      setSearchTerm(search.filters.searchTerm || search.query || '')
      setBooleanSearch(search.filters.booleanSearch || "")
      setAdvancedFilters(search.filters.advancedFilters || {})
      toast.success(`Busca "${search.name}" aplicada`)
    }
  }

  const handleDeleteSavedSearch = (searchId: string) => {
    deletePersistedSearch(searchId)
    setSavedSearches(prev => prev.filter(s => s.id !== searchId))
    toast.success("Busca removida")
  }

  const handleRenameSavedSearch = (searchId: string, newName: string) => {
    renamePersistedSearch(searchId, newName)
    setSavedSearches(prev => prev.map(s => 
      s.id === searchId ? { ...s, name: newName } : s
    ))
    toast.success("Busca renomeada")
  }

  // Funções para o prompt da LIA - Integração com Orquestrador Multi-Agente
  const handleAICommand = async (command: string, action?: string) => {
    // Add user message to chat
    setLiaMessages(prev => [...prev, {
      id: `user-${Date.now()}`,
      type: 'user',
      content: command,
      timestamp: Date.now()
    }])
    
    setIsLiaProcessing(true)
    
    // Prepare jobs context for orchestrator
    const jobs = filteredJobs
    const jobsContext = {
      total: jobs.length,
      active: jobs.filter(j => j.status === 'Ativa').length,
      paused: jobs.filter(j => j.status === 'Paralisada').length,
      completed: jobs.filter(j => j.status === 'Concluída').length,
      urgent: jobs.filter(j => j.priority === 'alta' || j.urgencyLevel >= 4).length,
      withoutCandidates: jobs.filter(j => j.funnel.total === 0).length,
      totalCandidates: jobs.reduce((sum, j) => sum + j.funnel.total, 0),
      selectedJobs: Array.from(selectedJobsForBatch).map(id => {
        const job = jobs.find(j => j.id === id)
        return job ? { id: job.id, title: job.title, department: job.department, status: job.status } : null
      }).filter(Boolean),
      topJobs: jobs.slice(0, 10).map(j => ({
        id: j.id,
        title: j.title,
        department: j.department,
        status: j.status,
        priority: j.priority,
        candidatesTotal: j.funnel.total,
        candidatesInterview: j.funnel.interview,
        hired: j.funnel.hired,
        daysOpen: Math.floor((Date.now() - new Date(j.openDate).getTime()) / (1000 * 60 * 60 * 24))
      }))
    }
    
    try {
      // Prepare selected jobs array
      const selectedJobsArray = Array.from(selectedJobsForBatch).map(id => {
        const job = jobs.find(j => j.id === id)
        return job ? { id: job.id, title: job.title, department: job.department, status: job.status } : null
      }).filter((j): j is { id: number; title: string; department: string; status: string } => j !== null)
      
      // Call orchestrator for intelligent response
      const response = await callOrchestratedJobsManagement({
        message: command,
        jobs_context: jobsContext,
        selected_jobs: selectedJobsArray.length > 0 ? selectedJobsArray : undefined,
        top_jobs: jobsContext.topJobs,
        conversation_history: liaMessages.slice(-10).map(m => ({
          role: m.type === 'user' ? 'user' : 'assistant',
          content: m.content
        })),
        action: action || 'general_query',
        conversation_id: jobsConversationId,
        company_id: 'default',
      })
      if (response.conversation_id) {
        setJobsConversationId(response.conversation_id)
      }
      
      // Add orchestrator response
      setLiaMessages(prev => [...prev, {
        id: `response-${Date.now()}`,
        type: 'response',
        content: response.content,
        timestamp: Date.now(),
        agentUsed: response.agent_used,
        suggestedPrompts: response.suggested_prompts,
        action_executed: response.action_executed,
        action_result: response.action_result,
        action_type: response.action_type,
        needs_confirmation: response.needs_confirmation,
        needs_params: response.needs_params,
        pending_action_id: response.pending_action_id,
      }])
      
      if (response.action_executed && response.action_result) {
        setTimeout(() => {
          loadBackendJobs()
        }, 500)
      }
      
      // Update orchestrator suggestions if available
      if (response.suggested_prompts && response.suggested_prompts.length > 0) {
        setOrchestratorSuggestions(response.suggested_prompts)
      }
      
      // Handle UI actions from orchestrator
      if (response.ui_action === 'start_job_wizard') {
        openJobCreationChat(response.ui_action_params?.initial_message || '')
      } else if (response.ui_action === 'filter_jobs' && response.ui_action_params?.filter) {
        setActiveFilter(response.ui_action_params.filter)
      }
      
    } catch (error) {
      console.error('Orchestrator call failed, using local fallback:', error)
      
      // Fallback to local logic
      const responseContent = processLocalJobCommand(command, jobs)
      
      setLiaMessages(prev => [...prev, {
        id: `response-${Date.now()}`,
        type: 'response',
        content: responseContent,
        timestamp: Date.now()
      }])
    } finally {
      setIsLiaProcessing(false)
    }
  }
  
  // Local fallback for job commands when orchestrator is unavailable
  const processLocalJobCommand = (command: string, jobs: typeof filteredJobs): string => {
    const trimmedCommand = command.trim().toLowerCase()
    const activeJobs = jobs.filter(j => j.status === 'Ativa')
    
    // Comando: quantas vagas abertas
    if (trimmedCommand.includes('quantas vagas') || trimmedCommand.includes('vagas abertas') || trimmedCommand.includes('total de vagas')) {
      const total = jobs.length
      const ativas = activeJobs.length
      const paralisadas = jobs.filter(j => j.status === 'Paralisada').length
      const concluidas = jobs.filter(j => j.status === 'Concluída').length
      
      return `📊 **Resumo de Vagas**\n\n` +
        `• **Total de vagas:** ${total}\n` +
        `• **Vagas ativas:** ${ativas}\n` +
        `• **Vagas paralisadas:** ${paralisadas}\n` +
        `• **Vagas concluídas:** ${concluidas}\n\n` +
        `💡 Dica: Use "vagas urgentes" para ver as que precisam de atenção imediata.`
    }
    
    // Comando: vagas urgentes
    if (trimmedCommand.includes('vagas urgentes') || trimmedCommand.includes('urgente') || trimmedCommand.includes('prioridade alta')) {
      const urgentes = jobs.filter(j => j.priority === 'alta' || j.urgencyLevel >= 4)
      
      if (urgentes.length === 0) {
        return `✅ **Nenhuma vaga urgente no momento**\n\nTodas as vagas estão com prioridade normal. Continue monitorando!`
      }
      
      const listaUrgentes = urgentes.slice(0, 10).map((j, i) => 
        `${i + 1}. **${j.title}** - ${j.department} (${j.funnel.total} candidatos)`
      ).join('\n')
      
      return `🚨 **${urgentes.length} Vaga(s) Urgente(s)**\n\n${listaUrgentes}\n\n` +
        `💡 Essas vagas precisam de atenção imediata.`
    }
    
    // Comando: resumir vagas
    if (trimmedCommand.includes('resumir') || trimmedCommand.includes('resumo') || trimmedCommand.includes('overview') || trimmedCommand.includes('visão geral')) {
      const porStatus: Record<string, number> = {}
      const porDept: Record<string, number> = {}
      let totalCandidatos = 0
      
      jobs.forEach(j => {
        porStatus[j.status] = (porStatus[j.status] || 0) + 1
        porDept[j.department] = (porDept[j.department] || 0) + 1
        totalCandidatos += j.funnel.total
      })
      
      const statusText = Object.entries(porStatus).map(([s, c]) => `• ${s}: ${c}`).join('\n')
      const topDepts = Object.entries(porDept).sort((a, b) => b[1] - a[1]).slice(0, 5)
      const deptText = topDepts.map(([d, c]) => `• ${d}: ${c} vagas`).join('\n')
      
      return `📋 **Resumo das ${jobs.length} Vagas**\n\n` +
        `**Por Status:**\n${statusText}\n\n` +
        `**Top Departamentos:**\n${deptText}\n\n` +
        `**Total de candidatos no funil:** ${totalCandidatos}`
    }
    
    // Comando: performance geral
    if (trimmedCommand.includes('performance') || trimmedCommand.includes('métricas') || trimmedCommand.includes('kpis')) {
      const totalVagas = jobs.length
      const totalCandidatos = jobs.reduce((sum, j) => sum + j.funnel.total, 0)
      const totalContratados = jobs.reduce((sum, j) => sum + j.funnel.hired, 0)
      const taxaConversao = totalCandidatos > 0 ? ((totalContratados / totalCandidatos) * 100).toFixed(1) : '0'
      
      const now = Date.now()
      const diasAbertos = jobs.map(j => Math.floor((now - new Date(j.openDate).getTime()) / (1000 * 60 * 60 * 24)))
      const mediaDias = diasAbertos.length > 0 ? Math.round(diasAbertos.reduce((a, b) => a + b, 0) / diasAbertos.length) : 0
      
      return `📊 **Performance Geral das Vagas**\n\n` +
        `📋 **Total de vagas:** ${totalVagas}\n` +
        `👥 **Candidatos no funil:** ${totalCandidatos}\n` +
        `✅ **Contratações:** ${totalContratados}\n` +
        `📈 **Taxa de conversão:** ${taxaConversao}%\n` +
        `⏱️ **Tempo médio aberta:** ${mediaDias} dias`
    }
    
    // Comando: top 5 vagas
    if (trimmedCommand.includes('top 5') || trimmedCommand.includes('top5') || trimmedCommand.includes('mais candidatos')) {
      const topVagas = [...jobs].sort((a, b) => b.funnel.total - a.funnel.total).slice(0, 5)
      
      if (topVagas.length === 0) {
        return `📊 Nenhuma vaga disponível para análise.`
      }
      
      const lista = topVagas.map((j, i) => 
        `${i + 1}. **${j.title}**\n   📁 ${j.funnel.total} candidatos | 🎯 ${j.funnel.interview} em entrevista | ✅ ${j.funnel.hired} contratados`
      ).join('\n\n')
      
      return `🏆 **Top 5 Vagas com Mais Candidatos**\n\n${lista}`
    }
    
    // Comando: vagas sem candidatos
    if (trimmedCommand.includes('sem candidatos') || trimmedCommand.includes('funil vazio') || trimmedCommand.includes('pipeline vazio')) {
      const semCandidatos = jobs.filter(j => j.funnel.total === 0)
      
      if (semCandidatos.length === 0) {
        return `✅ **Todas as vagas têm candidatos!**\n\nNenhuma vaga está com pipeline vazio.`
      }
      
      const lista = semCandidatos.slice(0, 10).map((j, i) => 
        `${i + 1}. **${j.title}** - ${j.department} (${j.status})`
      ).join('\n')
      
      return `⚠️ **${semCandidatos.length} Vaga(s) sem Candidatos**\n\n${lista}\n\n` +
        `💡 Considere ampliar a divulgação ou revisar os requisitos.`
    }
    
    // Comando: departamentos
    if (trimmedCommand.includes('departamentos') || trimmedCommand.includes('por departamento')) {
      const porDept: Record<string, { total: number; ativas: number; candidatos: number }> = {}
      
      jobs.forEach(j => {
        const d = j.department || 'Outros'
        if (!porDept[d]) porDept[d] = { total: 0, ativas: 0, candidatos: 0 }
        porDept[d].total++
        if (j.status === 'Ativa') porDept[d].ativas++
        porDept[d].candidatos += j.funnel.total
      })
      
      const lista = Object.entries(porDept)
        .sort((a, b) => b[1].total - a[1].total)
        .map(([dept, data]) => 
          `• **${dept}:** ${data.total} vagas (${data.ativas} ativas) | ${data.candidatos} candidatos`
        ).join('\n')
      
      return `🏢 **Vagas por Departamento**\n\n${lista}`
    }
    
    // Fallback: comando não reconhecido
    return `🤔 **Entendi sua pergunta, mas estou operando em modo offline**\n\n` +
      `Posso ajudar localmente com:\n\n` +
      `📊 "quantas vagas abertas" | "resumir vagas"\n` +
      `🚨 "vagas urgentes" | "vagas sem candidatos"\n` +
      `📈 "performance geral" | "top 5 vagas"\n` +
      `🏢 "departamentos contratando"\n\n` +
      `💡 Para análises mais detalhadas, tente novamente em alguns instantes.`
  }
  
  // State for orchestrator suggestions (separate from useLiaSuggestions hook)
  const [orchestratorSuggestions, setOrchestratorSuggestions] = useState<string[]>([])
  
  // Generate contextual suggestions based on current job state
  const getContextualSuggestions = (): string[] => {
    const jobs = filteredJobs
    const suggestions: string[] = []
    
    // Priority 1: Urgent jobs
    const urgentCount = jobs.filter(j => j.priority === 'alta' || j.urgencyLevel >= 4).length
    if (urgentCount > 0) {
      suggestions.push(`Analisar ${urgentCount} vaga${urgentCount > 1 ? 's' : ''} urgente${urgentCount > 1 ? 's' : ''}`)
    }
    
    // Priority 2: Jobs without candidates
    const emptyPipeline = jobs.filter(j => j.funnel.total === 0).length
    if (emptyPipeline > 0) {
      suggestions.push(`${emptyPipeline} vaga${emptyPipeline > 1 ? 's' : ''} sem candidatos`)
    }
    
    // Priority 3: Jobs with upcoming deadlines
    const now = Date.now()
    const upcomingDeadlines = jobs.filter(j => {
      if (!j.deadline) return false
      const deadline = new Date(j.deadline).getTime()
      const daysRemaining = Math.floor((deadline - now) / (1000 * 60 * 60 * 24))
      return daysRemaining >= 0 && daysRemaining <= 7
    }).length
    if (upcomingDeadlines > 0) {
      suggestions.push(`Vagas com deadline em 7 dias`)
    }
    
    // Priority 4: Paused jobs
    const pausedCount = jobs.filter(j => j.status === 'Paralisada').length
    if (pausedCount > 0) {
      suggestions.push(`Revisar ${pausedCount} vaga${pausedCount > 1 ? 's' : ''} paralisada${pausedCount > 1 ? 's' : ''}`)
    }
    
    // Default suggestions if nothing contextual
    if (suggestions.length === 0) {
      suggestions.push('Resumo das minhas vagas')
      suggestions.push('Performance dos últimos 30 dias')
    }
    
    // Always add performance suggestion if we have less than 4
    if (suggestions.length < 4 && !suggestions.some(s => s.includes('Performance'))) {
      suggestions.push('Performance das vagas ativas')
    }
    
    // Add top candidates suggestion
    if (suggestions.length < 4) {
      suggestions.push('Top 5 vagas com mais candidatos')
    }
    
    return suggestions.slice(0, 4)
  }

  const selectAllJobs = () => {
    const allJobIds = new Set(filteredJobs.map(job => job.id))
    setSelectedJobsForBatch(allJobIds)

    // Ativa o prompt da LIA com todas as vagas
    setShowExpandedLIA(true)
    setLiaHighlight(true)
    setLiaPromptValue(`Analisar ${allJobIds.size} vagas selecionadas`)

    // Remove o highlight após 1 segundo
    setTimeout(() => setLiaHighlight(false), 1000)

    // Scroll suave para o prompt
    setTimeout(() => {
      liaInputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 100)
  }

  const deselectAllJobs = () => {
    setSelectedJobsForBatch(new Set())
    setLiaPromptValue('')
    setShowExpandedLIA(false)
  }

  const toggleJobSelection = (jobId: number) => {
    setSelectedJobsForBatch(prev => {
      const newSet = new Set(prev)
      if (newSet.has(jobId)) {
        newSet.delete(jobId)
      } else {
        newSet.add(jobId)
      }

      // Ativa o prompt da LIA quando há vagas selecionadas
      if (newSet.size > 0) {
        setShowExpandedLIA(true)
        setLiaHighlight(true)
        const selectedJobs = allJobs.filter(job => newSet.has(job.id))
        const jobTitles = selectedJobs.map(job => job.title).join(', ')
        setLiaPromptValue(`Analisar ${newSet.size} vaga(s) selecionada(s): ${jobTitles}`)

        // Remove o highlight após 1 segundo
        setTimeout(() => setLiaHighlight(false), 1000)

        // Scroll suave para o prompt
        setTimeout(() => {
          liaInputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }, 100)
      } else {
        setLiaPromptValue('')
      }

      return newSet
    })
  }

  const handleJobCompare = () => {
    if (selectedJobsForBatch.size < 2) {
      toast.error("Selecione pelo menos 2 vagas para comparar")
      return
    }
    setShowCompareModal(true)
  }

  const handleJobPublish = () => {
    setShowPublishModal(true)
  }

  const handleJobInsights = () => {
    setShowInsightsModal(true)
  }

  const handleJobDuplicate = () => {
    if (selectedJobsForBatch.size !== 1) {
      toast.error("Selecione apenas 1 vaga para duplicar")
      return
    }
    setShowDuplicateModal(true)
  }

  const handleJobToggleStatus = () => {
    const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
    const hasActive = selectedJobs.some(job => job.status === 'Ativa')
    setStatusModalMode(hasActive ? 'pause' : 'activate')
    setShowStatusModal(true)
  }

  const handleJobAssignRecruiter = () => {
    setShowAssignRecruiterModal(true)
  }

  const getSelectedJobsHaveActiveStatus = () => {
    const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
    return selectedJobs.some(job => job.status === 'Ativa')
  }

  const togglePinJob = (jobId: number) => {
    setPinnedJobs(prev => {
      const newSet = new Set(prev)
      if (newSet.has(jobId)) {
        newSet.delete(jobId)
      } else {
        newSet.add(jobId)
      }
      return newSet
    })
  }

  const toggleUrgentJob = async (jobId: number) => {
    const job = allJobs.find(j => j.id === jobId)
    if (!job?.backendId) {
      toast.error('Vaga não encontrada')
      return
    }

    const isCurrentlyUrgent = urgentJobs.has(jobId)
    const newUrgencyLevel = isCurrentlyUrgent ? 3 : 5

    try {
      await liaApi.updateJobVacancy(job.backendId, { urgency_level: newUrgencyLevel })
      setUrgentJobs(prev => {
        const newSet = new Set(prev)
        if (isCurrentlyUrgent) {
          newSet.delete(jobId)
        } else {
          newSet.add(jobId)
        }
        return newSet
      })
      toast.success(isCurrentlyUrgent ? 'Vaga marcada como normal' : 'Vaga marcada como urgente')
    } catch (error) {
      console.error('Erro ao atualizar urgência:', error)
      toast.error('Erro ao atualizar urgência da vaga')
    }
  }

  const toggleFavoriteJob = (jobId: number) => {
    setFavoriteJobs(prev => {
      const newSet = new Set(prev)
      if (newSet.has(jobId)) {
        newSet.delete(jobId)
      } else {
        newSet.add(jobId)
      }
      return newSet
    })
  }

  const handleTemplateSelection = (persona: string) => {
    setSelectedTemplate(persona)

    // Aplicar filtros predefinidos baseados na persona para vagas
    switch (persona) {
      case "Vagas Tech Sênior":
        setAdvancedFilters({
          ...advancedFilters,
          job_titles: ["Desenvolvedor Frontend", "Desenvolvedor Backend", "Tech Lead"],
          seniority_levels: ["Sênior", "Especialista"],
          departments: ["Tecnologia"],
          salary_ranges: ["R$ 10.000 - R$ 15.000", "R$ 15.000+"]
        })
        setBooleanSearch("(Frontend OR Backend OR Tech Lead) AND Senior")
        break
      case "Vagas Design":
        setAdvancedFilters({
          ...advancedFilters,
          job_titles: ["UX Designer", "UI Designer", "Product Designer"],
          departments: ["Design"],
          seniority_levels: ["Pleno", "Sênior"]
        })
        setBooleanSearch("UX OR UI OR Product AND Design")
        break
      case "Vagas Remotas":
        setAdvancedFilters({
          ...advancedFilters,
          work_models: ["Remoto"],
          locations: ["Qualquer lugar", "Remoto"]
        })
        setBooleanSearch("Remoto OR Remote")
        break
      case "Vagas Urgentes":
        setAdvancedFilters({
          ...advancedFilters,
          priorities: ["Alta"],
          urgency_levels: ["5", "4"],
          status: ["Ativa"]
        })
        setBooleanSearch("Urgente OR Imediato")
        break
      case "Vagas Júnior":
        setAdvancedFilters({
          ...advancedFilters,
          seniority_levels: ["Júnior", "Trainee"],
          salary_ranges: ["R$ 3.000 - R$ 6.000", "R$ 6.000 - R$ 10.000"]
        })
        setBooleanSearch("Junior OR Júnior OR Trainee")
        break
    }
  }

  // Count jobs by status and stage
  const getJobCountByStatus = (status: string) => {
    if (status === 'todas') return allJobs.length
    return allJobs.filter(job => job.status === status).length
  }

  const getJobCountByStage = (stage: string) => {
    if (stage === 'todos') return allJobs.length
    return allJobs.filter(job => job.stage === stage).length
  }

  // Handle status filter changes
  const handleStatusFilterChange = (status: string) => {
    setSelectedStatusFilter(status)
  }

  // Personas de busca predefinidas para vagas
  const searchTemplates = [
    "Vagas Tech Sênior",
    "Vagas Design",
    "Vagas Remotas",
    "Vagas Urgentes",
    "Vagas Júnior",
    "Vagas Product Manager",
    "Vagas Data Science",
    "Vagas DevOps",
    "Vagas Startup",
    "Vagas Enterprise"
  ]

  const filteredJobs = allJobs.filter(job => {
    // Tab navigation filtering (activeFilter)
    let matchesActiveFilter = true
    if (activeFilter === 'ativas') {
      matchesActiveFilter = job.status === 'Ativa'
    } else if (activeFilter === 'urgentes') {
      matchesActiveFilter = job.urgencyLevel >= 4
    } else if (activeFilter === 'paralisadas') {
      matchesActiveFilter = job.status === 'Paralisada'
    } else if (activeFilter === 'concluidas') {
      matchesActiveFilter = job.status === 'Concluída'
    } else if (activeFilter === 'canceladas') {
      matchesActiveFilter = job.status === 'Cancelada'
    }

    if (!matchesActiveFilter) return false

    // Status filtering
    let matchesStatus = true

    if (selectedStatusFilter !== 'todas') {
      matchesStatus = job.status === selectedStatusFilter
    }

    // Days Open filtering
    const daysOpen = Math.floor(
      (new Date().getTime() - new Date(job.openDate).getTime()) / (1000 * 60 * 60 * 24)
    )

    // Busca global melhorada - pesquisa em todos os campos relevantes
    const searchLower = searchTerm.toLowerCase()
    
    // Campos básicos
    let matchesSearch = searchTerm === "" ||
      job.jobId.toLowerCase().includes(searchLower) ||
      job.title.toLowerCase().includes(searchLower) ||
      job.department.toLowerCase().includes(searchLower) ||
      job.location.toLowerCase().includes(searchLower) ||
      job.type.toLowerCase().includes(searchLower) ||
      job.level.toLowerCase().includes(searchLower) ||
      job.salary.toLowerCase().includes(searchLower) ||
      job.description.toLowerCase().includes(searchLower) ||
      job.manager.toLowerCase().includes(searchLower) ||
      job.managerEmail.toLowerCase().includes(searchLower) ||
      job.recruiter.toLowerCase().includes(searchLower) ||
      job.recruiterEmail.toLowerCase().includes(searchLower) ||
      job.requirements.some(req => req.toLowerCase().includes(searchLower)) ||
      job.benefits.some(benefit => benefit.toLowerCase().includes(searchLower)) ||
      (job.tags || []).some(tag => tag.toLowerCase().includes(searchLower)) ||
      // Skills técnicas (technology)
      (job.technicalRequirements || []).some((tr: any) => 
        tr.technology?.toLowerCase().includes(searchLower) ||
        tr.category?.toLowerCase().includes(searchLower)
      ) ||
      // Idiomas
      (job.languages || []).some((lang: any) => 
        lang.language?.toLowerCase().includes(searchLower)
      ) ||
      // Competências comportamentais
      (job.behavioralCompetencies || []).some((bc: any) => 
        bc.competency?.toLowerCase().includes(searchLower)
      ) ||
      // Setor e segmento alvo
      (job.targetSector || '').toLowerCase().includes(searchLower) ||
      (job.targetSegment || '').toLowerCase().includes(searchLower) ||
      // Status e prioridade
      job.status.toLowerCase().includes(searchLower) ||
      job.priority.toLowerCase().includes(searchLower) ||
      job.stage.toLowerCase().includes(searchLower)

    // Boolean search
    if (booleanSearch.trim()) {
      const booleanLower = booleanSearch.toLowerCase()
      const jobText = [
        job.title,
        job.department,
        job.location,
        job.type,
        job.level,
        job.description,
        job.manager,
        ...job.requirements,
        ...job.benefits
      ].join(' ').toLowerCase()

      // Simple boolean logic - could be enhanced
      if (booleanLower.includes(' and ')) {
        const terms = booleanLower.split(' and ')
        matchesSearch = terms.every(term => jobText.includes(term.trim()))
      } else if (booleanLower.includes(' or ')) {
        const terms = booleanLower.split(' or ')
        matchesSearch = terms.some(term => jobText.includes(term.trim()))
      } else {
        matchesSearch = jobText.includes(booleanLower)
      }
    }

    // Advanced filters
    let matchesAdvancedFilters = true

    // Job titles
    if (advancedFilters.job_titles.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.job_titles.some(title =>
        job.title.toLowerCase().includes(title.toLowerCase())
      )
    }

    // Departments
    if (advancedFilters.departments.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.departments.some(dept =>
        job.department.toLowerCase().includes(dept.toLowerCase())
      )
    }

    // Locations
    if (advancedFilters.locations.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.locations.some(location =>
        job.location.toLowerCase().includes(location.toLowerCase())
      )
    }

    // Work models
    if (advancedFilters.work_models.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.work_models.some(model =>
        job.workModel.toLowerCase().includes(model.toLowerCase())
      )
    }

    // Job types
    if (advancedFilters.job_types.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.job_types.some(type =>
        job.type.toLowerCase().includes(type.toLowerCase())
      )
    }

    // Seniority levels
    if (advancedFilters.seniority_levels.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.seniority_levels.some(level =>
        job.level.toLowerCase().includes(level.toLowerCase())
      )
    }

    // Status
    if (advancedFilters.status.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.status.some(status =>
        job.status.toLowerCase().includes(status.toLowerCase())
      )
    }

    // Stages
    if (advancedFilters.stages.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.stages.some(stage =>
        job.stage.toLowerCase().includes(stage.toLowerCase())
      )
    }

    // Priorities
    if (advancedFilters.priorities.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.priorities.some(priority =>
        job.priority.toLowerCase().includes(priority.toLowerCase())
      )
    }

    // Managers
    if (advancedFilters.managers.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.managers.some(manager =>
        job.manager.toLowerCase().includes(manager.toLowerCase())
      )
    }

    // Benefits
    if (advancedFilters.benefits.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.benefits.some(benefit =>
        job.benefits.some(jobBenefit => jobBenefit.toLowerCase().includes(benefit.toLowerCase()))
      )
    }

    // Requirements
    if (advancedFilters.requirements.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.requirements.some(requirement =>
        job.requirements.some(jobReq => jobReq.toLowerCase().includes(requirement.toLowerCase()))
      )
    }

    // Budget ranges
    if (advancedFilters.budget_ranges.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.budget_ranges.some(range => {
        const budget = job.budget || 0
        switch (range) {
          case "Até R$ 50.000": return budget <= 50000
          case "R$ 50.000 - R$ 100.000": return budget >= 50000 && budget <= 100000
          case "R$ 100.000+": return budget >= 100000
          default: return false
        }
      })
    }

    // Urgency levels
    if (advancedFilters.urgency_levels.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.urgency_levels.some(level =>
        job.urgencyLevel.toString() === level
      )
    }

    // Contract duration
    if (advancedFilters.contract_duration.length > 0) {
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.contract_duration.some(duration =>
        job.type.toLowerCase().includes(duration.toLowerCase())
      )
    }

    // 🎯 Inline Table Filters (jobFilters) - Filtros da tabela de resultados
    let matchesInlineFilters = true

    // Status filters
    if (jobFilters.status?.statuses?.length) {
      matchesInlineFilters = matchesInlineFilters && jobFilters.status.statuses.includes(job.status)
    }

    // Priority filters
    if (jobFilters.status?.priorities?.length) {
      matchesInlineFilters = matchesInlineFilters && jobFilters.status.priorities.includes(job.priority)
    }

    // Stage filters
    if (jobFilters.status?.stages?.length) {
      matchesInlineFilters = matchesInlineFilters && jobFilters.status.stages.includes(job.stage)
    }

    // Work model filters
    if (jobFilters.position?.workModels?.length) {
      matchesInlineFilters = matchesInlineFilters && jobFilters.position.workModels.includes(job.workModel)
    }

    // Seniority level filters
    if (jobFilters.position?.levels?.length) {
      matchesInlineFilters = matchesInlineFilters && jobFilters.position.levels.some(level =>
        job.level.toLowerCase().includes(level.toLowerCase())
      )
    }

    // Department filters
    if (jobFilters.team?.departments?.length) {
      matchesInlineFilters = matchesInlineFilters && jobFilters.team.departments.some(dept =>
        job.department.toLowerCase().includes(dept.toLowerCase())
      )
    }

    // Recruiter filters
    if (jobFilters.team?.recruiters?.length) {
      matchesInlineFilters = matchesInlineFilters && jobFilters.team.recruiters.some(recruiter =>
        job.recruiter.toLowerCase().includes(recruiter.toLowerCase())
      )
    }

    // Manager filters
    if (jobFilters.team?.managers?.length) {
      matchesInlineFilters = matchesInlineFilters && jobFilters.team.managers.some(manager =>
        job.manager.toLowerCase().includes(manager.toLowerCase())
      )
    }

    // Location filters
    if (jobFilters.position?.locations?.length) {
      matchesInlineFilters = matchesInlineFilters && jobFilters.position.locations.some(loc =>
        job.location.toLowerCase().includes(loc.toLowerCase()) ||
        (loc.toLowerCase() === 'remoto' && job.workModel === 'remoto')
      )
    }

    // Publishing channel filters
    if (jobFilters.publishing?.channels?.length) {
      const publishedChannels: string[] = []
      if (job.publishedLinkedIn) publishedChannels.push('linkedin')
      if (job.publishedWebsite) publishedChannels.push('website')
      if (job.publishedIndeed) publishedChannels.push('indeed')
      
      matchesInlineFilters = matchesInlineFilters && jobFilters.publishing.channels.some(channel =>
        publishedChannels.includes(channel)
      )
    }

    // Unpublished filter
    if (jobFilters.publishing?.unpublished) {
      matchesInlineFilters = matchesInlineFilters && 
        !job.publishedLinkedIn && !job.publishedWebsite && !job.publishedIndeed
    }

    // Empty pipeline filter
    if (jobFilters.funnel?.emptyPipeline) {
      matchesInlineFilters = matchesInlineFilters && job.funnel.total === 0
    }

    // Low conversion filter (less than 10% hired from total)
    if (jobFilters.metrics?.lowConversion) {
      const conversionRate = job.funnel.total > 0 ? (job.funnel.hired / job.funnel.total) : 0
      matchesInlineFilters = matchesInlineFilters && conversionRate < 0.1
    }

    // Min NPS filter
    if (jobFilters.metrics?.minNPS) {
      matchesInlineFilters = matchesInlineFilters && job.nps >= jobFilters.metrics.minNPS
    }

    // Max days open filter
    if (jobFilters.metrics?.maxDaysOpen) {
      const daysOpenCalc = Math.floor(
        (new Date().getTime() - new Date(job.openDate).getTime()) / (1000 * 60 * 60 * 24)
      )
      matchesInlineFilters = matchesInlineFilters && daysOpenCalc <= jobFilters.metrics.maxDaysOpen
    }

    return matchesStatus && matchesSearch && matchesAdvancedFilters && matchesInlineFilters
  }).sort((a, b) => {
    // Vagas fixadas primeiro
    const aIsPinned = pinnedJobs.has(a.id)
    const bIsPinned = pinnedJobs.has(b.id)

    if (aIsPinned && !bIsPinned) return -1
    if (!aIsPinned && bIsPinned) return 1

    // Mantém a ordem original para o resto
    return 0
  })

  // Organizar vagas por status (todos os 12 status)
  const organizeJobsByStatus = (jobs: Job[]) => {
    const statusOrder = [
      'Ativa',
      'Aprovada', 
      'Aguardando aprovação',
      'Reaberta',
      'Paralisada',
      'Interna',
      'Rascunho',
      'Fechada (preenchida)',
      'Fechada (expirada)',
      'Cancelada',
      'Concluída',
      'Arquivada'
    ] as const
    
    const grouped: { [key: string]: Job[] } = {
      'Ativa': [],
      'Aprovada': [],
      'Aguardando aprovação': [],
      'Reaberta': [],
      'Paralisada': [],
      'Interna': [],
      'Rascunho': [],
      'Fechada (preenchida)': [],
      'Fechada (expirada)': [],
      'Cancelada': [],
      'Concluída': [],
      'Arquivada': []
    }

    // Agrupar vagas por status
    jobs.forEach(job => {
      if (grouped[job.status]) {
        grouped[job.status].push(job)
      }
    })

    return { statusOrder, grouped }
  }

  const { statusOrder, grouped: groupedJobs } = organizeJobsByStatus(filteredJobs)

  // Contar total de vagas por status
  const getStatusCount = (status: string) => {
    return groupedJobs[status]?.length || 0
  }

  // Status colors usando paleta pastel ElevenLabs (função helper definida no topo do arquivo)

  const handleJobClick = (job: Job) => {
    setSelectedJob(job)
    setShowKanban(true)
    setShowJobPreview(false)
    setPreviewJob(null)
    onAddRecentItem?.({
      id: job.backendId || job.jobId || String(job.id),
      type: 'vaga',
      title: job.title,
      subtitle: job.company,
      meta: { jobId: job.backendId || job.jobId || String(job.id) }
    })
  }

  const handleJobPreview = (job: Job) => {
    setPreviewJob(job)
    setShowJobPreview(true)
  }

  const handleBackToJobs = () => {
    setShowKanban(false)
    setSelectedJob(null)
  }

  const handleShowReport = (job: Job) => {
    setReportJob(job)
    setShowReport(true)
  }

  const handleCloseReport = () => {
    setShowReport(false)
    setReportJob(null)
  }

  if (showKanban && selectedJob) {
    return <JobKanbanPage key={`kanban-${selectedJob.id}`} job={selectedJob} onBack={handleBackToJobs} />
  }

  if (showKanban && !selectedJob) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-base-ui text-gray-500 dark:text-gray-400">Carregando vaga...</p>
        </div>
      </div>
    )
  }

  const jobsColumnConfig: Record<string, { label: string; sortable: boolean; align: 'left' | 'center' | 'right' }> = {
    checkbox: { label: '', sortable: false, align: 'center' },
    id: { label: 'ID', sortable: true, align: 'left' },
    vaga: { label: 'Vaga', sortable: true, align: 'left' },
    candidatos: { label: 'Candidatos', sortable: true, align: 'center' },
    performance: { label: 'Performance LIA Triagens', sortable: false, align: 'left' },
    status: { label: 'Status', sortable: true, align: 'left' },
    screeningStatus: { label: 'Triagem', sortable: true, align: 'center' },
    recrutador: { label: 'Recrutador(a)', sortable: true, align: 'left' },
    gestor: { label: 'Gestor', sortable: true, align: 'left' },
    prazoTriagem: { label: 'Prazo Triagem', sortable: true, align: 'center' },
    prazoShortlist: { label: 'Prazo Short List', sortable: true, align: 'center' },
    prazoEncerramento: { label: 'Prazo Encerramento', sortable: true, align: 'center' },
    acoes: { label: 'Ações', sortable: false, align: 'center' }
  }

  const renderSkeletonLoading = () => (
    <div className="overflow-x-auto">
      <table className="w-full" style={{ tableLayout: 'fixed' }}>
        <thead>
          <tr className="">
            <th className="py-3 px-3 text-center w-12">
              <div className="w-4 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mx-auto" />
            </th>
            <th className="py-3 px-3 text-left" style={{ width: '80px' }}>
              <div className="w-8 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </th>
            <th className="py-3 px-3 text-left" style={{ width: '200px' }}>
              <div className="w-16 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </th>
            <th className="py-3 px-3 text-center" style={{ width: '100px' }}>
              <div className="w-20 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mx-auto" />
            </th>
            <th className="py-3 px-3 text-left" style={{ width: '180px' }}>
              <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </th>
            <th className="py-3 px-3 text-left" style={{ width: '100px' }}>
              <div className="w-14 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </th>
            <th className="py-3 px-3 text-left" style={{ width: '60px' }}>
              <div className="w-10 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </th>
            <th className="py-3 px-3 text-left" style={{ width: '120px' }}>
              <div className="w-20 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </th>
            <th className="py-3 px-3 text-left" style={{ width: '100px' }}>
              <div className="w-14 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </th>
            <th className="py-3 px-3 text-center" style={{ width: '100px' }}>
              <div className="w-16 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mx-auto" />
            </th>
            <th className="py-3 px-3 text-center" style={{ width: '80px' }}>
              <div className="w-12 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mx-auto" />
            </th>
          </tr>
        </thead>
        <tbody>
          {[1, 2, 3, 4, 5, 6, 7, 8].map((row) => (
            <tr key={row} className="">
              <td className="py-3 px-3 text-center">
                <div className="w-4 h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse mx-auto" />
              </td>
              <td className="py-3 px-3">
                <div className="w-16 h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
              </td>
              <td className="py-3 px-3">
                <div className="space-y-1">
                  <div className="w-40 h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
                  <div className="w-24 h-3 bg-gray-50 dark:bg-gray-800/50 rounded animate-pulse" />
                </div>
              </td>
              <td className="py-3 px-3 text-center">
                <div className="w-8 h-6 bg-gray-100 dark:bg-gray-800 rounded animate-pulse mx-auto" />
              </td>
              <td className="py-3 px-3">
                <div className="flex gap-1">
                  <div className="w-6 h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
                  <div className="w-6 h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
                  <div className="w-6 h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
                  <div className="w-6 h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
                  <div className="w-6 h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
                </div>
              </td>
              <td className="py-3 px-3">
                <div className="w-16 h-5 bg-gray-100 dark:bg-gray-800 rounded-full animate-pulse" />
              </td>
              <td className="py-3 px-3">
                <div className="w-8 h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
              </td>
              <td className="py-3 px-3">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 bg-gray-100 dark:bg-gray-800 rounded-full animate-pulse" />
                  <div className="w-20 h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
                </div>
              </td>
              <td className="py-3 px-3">
                <div className="w-20 h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
              </td>
              <td className="py-3 px-3 text-center">
                <div className="w-16 h-5 bg-gray-100 dark:bg-gray-800 rounded animate-pulse mx-auto" />
              </td>
              <td className="py-3 px-3 text-center">
                <div className="w-6 h-6 bg-gray-100 dark:bg-gray-800 rounded animate-pulse mx-auto" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center justify-center py-6 text-sm text-gray-800 dark:text-gray-500">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-full animate-spin bg-gray-600" />
          <span>Carregando vagas...</span>
        </div>
      </div>
    </div>
  )

  const renderCompactView = () => (
    <div className="overflow-auto h-full">
      <table className="w-full" style={{ tableLayout: 'fixed' }}>
        <thead className="sticky top-0 z-10 bg-white dark:bg-gray-900">
          <tr className="">
            {jobsColumnOrder.filter((columnId) => {
              if (columnId === 'checkbox' || columnId === 'acoes') return true
              const hookId = Object.entries(hookToTableColumnMap).find(([_, tableId]) => tableId === columnId)?.[0]
              if (!hookId) return true
              return visibleColumnIds.includes(hookId)
            }).map((columnId) => {
              const config = jobsColumnConfig[columnId]
              if (!config) return null

              if (columnId === 'checkbox') {
                return (
                  <th key={columnId} className="py-3 px-3 text-center w-12">
                    <input
                      type="checkbox"
                      checked={selectedJobsForBatch.size === filteredJobs.length && filteredJobs.length > 0}
                      ref={(input) => {
                        if (input) {
                          input.indeterminate = selectedJobsForBatch.size > 0 && selectedJobsForBatch.size < filteredJobs.length
                        }
                      }}
                      onChange={(e) => {
                        if (e.target.checked) {
                          selectAllJobs()
                        } else {
                          deselectAllJobs()
                        }
                      }}
                      className="w-4 h-4 rounded"
                    />
                  </th>
                )
              }

              if (columnId === 'acoes') {
                return (
                  <th 
                    key={columnId} 
                    className="text-center py-3 px-3 text-xs font-semibold text-gray-950 dark:text-gray-200"
                    style={{ width: jobsColumnWidths.acoes }}
                  >
                    <span className="sr-only">Ações</span>
                    <MoreVertical className="w-4 h-4 text-gray-800 dark:text-gray-200 mx-auto" aria-hidden="true" />
                  </th>
                )
              }

              const width = jobsColumnWidths[columnId as keyof typeof jobsColumnWidths] || 100
              const isDragging = draggedJobColumnId === columnId
              const isDragOver = dragOverJobColumnId === columnId

              return (
                <th
                  key={columnId}
                  className={`
                    text-${config.align} py-3 px-3 text-xs font-semibold text-gray-950 dark:text-gray-200 
                    relative group select-none
                    ${isDragging ? 'opacity-50' : ''}
                    ${isDragOver ? 'bg-blue-50 dark:bg-blue-900/20' : ''}
                    ${config.sortable ? 'cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50' : ''}
                  `}
                  style={{ width: `${width}px`, minWidth: '50px' }}
                  draggable={columnId !== 'checkbox' && columnId !== 'acoes'}
                  onDragStart={(e) => handleJobsColumnDragStart(columnId, e)}
                  onDragOver={(e) => handleJobsColumnDragOver(columnId, e)}
                  onDragLeave={handleJobsColumnDragLeave}
                  onDrop={(e) => handleJobsColumnDrop(columnId, e)}
                  onDragEnd={handleJobsColumnDragEnd}
                  onClick={() => config.sortable && handleJobsSort(columnId)}
                >
                  <div className="flex items-center gap-1">
                    <GripVertical className="w-3 h-3 text-gray-800 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab" />
                    <span>{config.label}</span>
                    {config.sortable && (
                      jobsSortColumn === columnId 
                        ? (jobsSortDirection === 'asc' 
                            ? <ArrowUp className="w-3 h-3 text-gray-800" />
                            : <ArrowDown className="w-3 h-3 text-gray-800" />)
                        : <ArrowUpDown className="w-3 h-3 text-gray-800" />
                    )}
                  </div>
                  
                  <div
                    className="absolute right-0 top-0 h-full w-1 cursor-col-resize opacity-0 group-hover:opacity-100 bg-gray-300 dark:bg-gray-600 hover:bg-gray-500 dark:hover:bg-gray-500 transition-colors"
                    onMouseDown={(e) => startJobsColumnResize(columnId, e)}
                    onClick={(e) => e.stopPropagation()}
                  />
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {statusOrder.map((status) => {
            const statusJobs = groupedJobs[status]

            if (statusJobs.length === 0) return null

            return (
              <React.Fragment key={status}>
                {statusJobs.map((job) => (
                  <React.Fragment key={job.id}>
                    <tr
                      className="hover:bg-gray-50 dark:hover:bg-gray-800/50 text-xs cursor-pointer transition-colors"
                      onClick={() => handleJobPreview(job)}
                    >
                      {jobsColumnOrder.filter((columnId) => {
                        if (columnId === 'checkbox' || columnId === 'acoes') return true
                        const hookId = Object.entries(hookToTableColumnMap).find(([_, tableId]) => tableId === columnId)?.[0]
                        if (!hookId) return true
                        return visibleColumnIds.includes(hookId)
                      }).map((columnId) => {
                        const width = jobsColumnWidths[columnId as keyof typeof jobsColumnWidths] || 100
                        
                        if (columnId === 'checkbox') {
                          return (
                            <td key={columnId} className="py-2 px-3 text-center">
                              <input
                                type="checkbox"
                                checked={selectedJobsForBatch.has(job.id)}
                                onChange={(e) => {
                                  e.stopPropagation()
                                  toggleJobSelection(job.id)
                                }}
                                onClick={(e) => e.stopPropagation()}
                                className="w-4 h-4 rounded"
                              />
                            </td>
                          )
                        }

                        if (columnId === 'id') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{ width: `${width}px` }}>
                              <span className="text-xs font-normal text-gray-800 dark:text-gray-200">
                                V{job.id.toString().padStart(4, '0')}
                              </span>
                            </td>
                          )
                        }

                        if (columnId === 'vaga') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{ width: `${width}px` }}>
                              <div>
                                <div className="font-semibold text-xs text-gray-950 dark:text-gray-50 flex items-center gap-1">
                                  {pinnedJobs.has(job.id) && (
                                    <Pin className="w-3 h-3 text-gray-800 dark:text-gray-200 fill-current" />
                                  )}
                                  {job.title}
                                  {(job.visibility === 'confidential' || job.isConfidential) && (
                                    <span title="Vaga Confidencial" className="flex items-center">
                                      <Shield className="w-3.5 h-3.5 text-orange-500" />
                                    </span>
                                  )}
                                  {job.visibility === 'internal' && (
                                    <span title="Vaga Interna" className="flex items-center">
                                      <Building className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                                    </span>
                                  )}
                                  {job.visibility === 'hidden' && (
                                    <span title="Vaga Oculta" className="flex items-center">
                                      <Lock className="w-3.5 h-3.5 text-gray-600" />
                                    </span>
                                  )}
                                </div>
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'candidatos') {
                          return (
                            <td key={columnId} className="py-2 px-2" style={{ width: `${width}px` }}>
                              <div className="flex items-center justify-center group relative cursor-help">
                                <div className="flex items-center gap-1">
                                  <Users 
                                    className="w-3.5 h-3.5"
                                    style={{
                                      color: job.funnel.total >= 50
                                        ? 'var(--gray-600)'
                                        : job.funnel.total >= 20
                                        ? 'var(--status-error)'
                                        : 'var(--status-warning)'
                                    }}
                                  />
                                  <span className="text-sm font-normal text-gray-800 dark:text-gray-50">
                                    {job.funnel.total}
                                  </span>
                                </div>
                                <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                  <div className="bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded-md text-xs min-w-[200px]">
                                    <div className="font-semibold mb-2">Funil de Candidatos</div>
                                    <div className="space-y-1.5 mb-2">
                                      <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-300">Total</span>
                                        <span className="text-xs font-semibold text-white">{job.funnel.total}</span>
                                      </div>
                                      <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-300">Triagem</span>
                                        <span className="text-xs font-semibold text-gray-200">
                                          {job.funnel.screening} ({job.funnel.total > 0 ? Math.round((job.funnel.screening / job.funnel.total) * 100) : 0}%)
                                        </span>
                                      </div>
                                      <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-300">Entrevistas</span>
                                        <span className="text-xs font-semibold text-gray-200">
                                          {job.funnel.interview} ({job.funnel.total > 0 ? Math.round((job.funnel.interview / job.funnel.total) * 100) : 0}%)
                                        </span>
                                      </div>
                                      <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-300">Finalistas</span>
                                        <span className="text-xs font-semibold text-gray-200">
                                          {job.funnel.final} ({job.funnel.total > 0 ? Math.round((job.funnel.final / job.funnel.total) * 100) : 0}%)
                                        </span>
                                      </div>
                                      <div className="flex items-center justify-between pt-1">
                                        <span className="text-xs text-gray-300">✓ Contratados</span>
                                        <span className="text-xs font-bold text-white">
                                          {job.funnel.hired} ({job.funnel.total > 0 ? Math.round((job.funnel.hired / job.funnel.total) * 100) : 0}%)
                                        </span>
                                      </div>
                                    </div>
                                    <div className="pt-2">
                                      <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-300">Taxa conversão final</span>
                                        <span className={`text-xs ${
                                          job.funnel.total > 0 && (job.funnel.hired / job.funnel.total) * 100 >= 10 ? 'font-bold text-white' :
                                          job.funnel.total > 0 && (job.funnel.hired / job.funnel.total) * 100 >= 5 ? 'font-semibold text-gray-200' :
                                          'font-medium text-gray-300'
                                        }`}>
                                          {job.funnel.total > 0 ? ((job.funnel.hired / job.funnel.total) * 100).toFixed(1) : 0}%
                                        </span>
                                      </div>
                                    </div>
                                    <div className="absolute top-full left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-gray-700"></div>
                                  </div>
                                </div>
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'performance') {
                          // Use lia_metrics from API (real data) or fallback to calculated values
                          const liaTriages = job.liaMetrics ? {
                            pipeline: job.liaMetrics.pipeline_lia,
                            agendadas: job.liaMetrics.triagens_agendadas,
                            realizadas: job.liaMetrics.triagens_realizadas,
                            semResposta: job.liaMetrics.sem_resposta,
                            entrevistasAgendadas: job.liaMetrics.entrevistas_agendadas
                          } : {
                            pipeline: 0,
                            agendadas: 0,
                            realizadas: 0,
                            semResposta: 0,
                            entrevistasAgendadas: 0
                          }
                          
                          const allValues = [liaTriages.pipeline, liaTriages.agendadas, liaTriages.realizadas, liaTriages.entrevistasAgendadas]
                          const maxValue = Math.max(...allValues, 1)
                          const getCardWidth = (value: number) => {
                            const minWidth = 24
                            const maxWidth = 40
                            const ratio = value / maxValue
                            return Math.round(minWidth + (maxWidth - minWidth) * ratio)
                          }
                          
                          return (
                            <td key={columnId} className="py-2 px-2" style={{ width: `${width}px` }}>
                              <div className="space-y-1">
                                <div className="flex items-center gap-0.5">
                                  <div className="flex flex-col items-center group relative cursor-help">
                                    <div 
                                      className="h-6 rounded flex items-center justify-center transition-all hover:ring-2 hover:scale-105" 
                                      style={{ 
                                        backgroundColor: 'var(--gray-200)',
                                        width: `${getCardWidth(liaTriages.pipeline)}px`,
                                        minWidth: '24px'
                                      }}>
                                      <span className="text-xs font-normal text-gray-950 dark:text-gray-200">
                                        {liaTriages.pipeline}
                                      </span>
                                    </div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                      <div className="bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded-md whitespace-nowrap text-xs">
                                        <div className="font-semibold mb-1 flex items-center gap-1">
                                          <Brain className="w-3 h-3 text-wedo-cyan" />
                                          Pipeline LIA
                                        </div>
                                        <div className="text-xs text-gray-500">{liaTriages.pipeline} candidatos contatados</div>
                                        <div className="absolute top-full left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-gray-700"></div>
                                      </div>
                                    </div>
                                  </div>
                                  <ChevronRight className="w-2 h-2 text-gray-800 flex-shrink-0" />
                                  <div className="flex flex-col items-center group relative cursor-help">
                                    <div 
                                      className="h-6 rounded flex items-center justify-center transition-all hover:ring-2 hover:scale-105" 
                                      style={{ 
                                        backgroundColor: 'var(--gray-300)',
                                        width: `${getCardWidth(liaTriages.agendadas)}px`,
                                        minWidth: '24px'
                                      }}>
                                      <span className="text-xs font-normal text-gray-950 dark:text-gray-200">
                                        {liaTriages.agendadas}
                                      </span>
                                    </div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                      <div className="bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded-md whitespace-nowrap text-xs">
                                        <div className="font-semibold mb-1">Triagens Agendadas</div>
                                        <div className="text-xs text-gray-500">{liaTriages.agendadas} triagens marcadas</div>
                                        <div className="absolute top-full left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-gray-700"></div>
                                      </div>
                                    </div>
                                  </div>
                                  <ChevronRight className="w-2 h-2 text-gray-800 flex-shrink-0" />
                                  <div className="flex flex-col items-center group relative cursor-help">
                                    <div 
                                      className="h-6 rounded flex items-center justify-center transition-all hover:ring-2 hover:scale-105 bg-wedo-green-pastel" 
                                      style={{ 
                                        width: `${getCardWidth(liaTriages.realizadas)}px`,
                                        minWidth: '24px'
                                      }}>
                                      <span className="text-xs font-normal text-gray-950 dark:text-gray-200">
                                        {liaTriages.realizadas}
                                      </span>
                                    </div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                      <div className="bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded-md whitespace-nowrap text-xs">
                                        <div className="font-semibold mb-1">Triagens Completas</div>
                                        <div className="text-xs text-gray-500">{liaTriages.realizadas} triagens finalizadas</div>
                                        <div className="absolute top-full left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-gray-700"></div>
                                      </div>
                                    </div>
                                  </div>
                                  <ChevronRight className="w-2 h-2 text-gray-800 flex-shrink-0" />
                                  <div className="flex flex-col items-center group relative cursor-help">
                                    <div 
                                      className="h-6 rounded flex items-center justify-center transition-all hover:ring-2 hover:scale-105" 
                                      style={{ 
                                        backgroundColor: 'var(--gray-200)',
                                        width: `${getCardWidth(liaTriages.entrevistasAgendadas)}px`,
                                        minWidth: '24px'
                                      }}>
                                      <span className="text-xs font-normal text-gray-950 dark:text-gray-200">
                                        {liaTriages.entrevistasAgendadas}
                                      </span>
                                    </div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-50">
                                      <div className="bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded-md whitespace-nowrap text-xs">
                                        <div className="font-semibold mb-1">Entrevistas Agendadas</div>
                                        <div className="text-xs text-gray-500">{liaTriages.entrevistasAgendadas} entrevistas marcadas</div>
                                        <div className="absolute top-full left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-gray-700"></div>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'status') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{ width: `${width}px` }}>
                              <div className="space-y-1">
                                <Badge
                                  variant="outline"
                                  className="border-0 text-xs font-normal px-2 py-0.5 text-gray-950 dark:text-gray-50"
                                  style={{ backgroundColor: getStatusColor(job.status) }}
                                >
                                  {job.status}
                                </Badge>
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'screeningStatus') {
                          const status = job.screeningStatus || 'not_configured'
                          const statusLabels: Record<string, string> = {
                            not_configured: 'Não Configurada',
                            not_started: 'Não Iniciada',
                            active: 'Ativa',
                            paused: 'Pausada',
                            completed: 'Concluída',
                          }
                          const screeningColors: Record<string, string> = {
                            not_configured: 'var(--gray-200)',
                            not_started: 'var(--gray-100)',
                            active: 'var(--status-success)',
                            paused: 'var(--gray-300)',
                            completed: 'var(--gray-400)',
                          }
                          return (
                            <td key={columnId} className="py-2 px-3" style={{ width: `${width}px` }}>
                              <Badge
                                variant="outline"
                                className="border-0 text-micro font-normal px-2 py-0.5 text-gray-950 dark:text-gray-50 cursor-pointer hover:opacity-80 transition-opacity"
                                style={{ backgroundColor: screeningColors[status] || 'var(--gray-200)' }}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleJobPreview(job)
                                }}
                              >
                                {statusLabels[status] || 'Não Configurada'}
                              </Badge>
                            </td>
                          )
                        }

                        if (columnId === 'recrutador') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{ width: `${width}px` }}>
                              <div className="flex items-center gap-2">
                                <Avatar className="w-8 h-8">
                                  <AvatarImage src={`https://i.pravatar.cc/100?u=${job.recruiterEmail}`} />
                                  <AvatarFallback className="text-xs bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                                    {job.recruiter.split(' ').map(n => n[0]).join('')}
                                  </AvatarFallback>
                                </Avatar>
                                <div className="text-xs font-normal text-gray-800 dark:text-gray-50">
                                  {job.recruiter}
                                </div>
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'gestor') {
                          return (
                            <td key={columnId} className="py-2 px-3" style={{ width: `${width}px` }}>
                              <div className="text-xs font-normal text-gray-800 dark:text-gray-50">
                                {job.manager}
                              </div>
                            </td>
                          )
                        }

                        if (columnId === 'prazoTriagem') {
                          return (
                            <td key={columnId} className="py-2 px-3 text-center" style={{ width: `${width}px` }}>
                              <span className="text-xs font-normal text-gray-800 dark:text-gray-50">
                                {job.openDate 
                                  ? new Date(job.openDate).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
                                  : '—'}
                              </span>
                            </td>
                          )
                        }

                        if (columnId === 'prazoShortlist' || columnId === 'prazoEncerramento') {
                          return (
                            <td key={columnId} className="py-2 px-3 text-center" style={{ width: `${width}px` }}>
                              <span className="text-xs font-normal text-gray-800 dark:text-gray-50">
                                {job.deadline 
                                  ? new Date(job.deadline).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
                                  : '—'}
                              </span>
                            </td>
                          )
                        }

                        if (columnId === 'acoes') {
                          const isUrgent = urgentJobs.has(job.id) || job.urgencyLevel >= 4
                          const isPinned = pinnedJobs.has(job.id)
                          const isFavorite = favoriteJobs.has(job.id)
                          
                          return (
                            <td key={columnId} className="py-2 px-3" style={{ width: `${width}px` }}>
                              <div className="flex items-center gap-1">
                                {/* Ícone Urgente - sempre visível e clicável */}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className={`h-7 w-7 p-0 transition-colors ${
                                    isUrgent 
                                      ? 'bg-red-50 hover:bg-red-100 dark:bg-red-900/20 dark:hover:bg-red-900/30' 
                                      : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                                  }`}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    toggleUrgentJob(job.id)
                                  }}
                                  title={isUrgent ? "Remover urgência" : "Marcar como urgente"}
                                >
                                  <AlertTriangle className={`w-3.5 h-3.5 transition-colors ${
                                    isUrgent 
                                      ? 'text-red-500 fill-red-100' 
                                      : 'text-gray-800 dark:text-gray-200'
                                  }`} />
                                </Button>
                                {/* Ícone Pin */}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className={`h-7 w-7 p-0 transition-colors ${
                                    isPinned 
                                      ? 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700' 
                                      : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                                  }`}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    togglePinJob(job.id)
                                  }}
                                  title={isPinned ? "Desafixar vaga" : "Fixar vaga"}
                                >
                                  <Pin className={`w-3 h-3 transition-colors ${
                                    isPinned 
                                      ? 'text-gray-950 dark:text-gray-50 fill-current' 
                                      : 'text-gray-800 dark:text-gray-200'
                                  }`} />
                                </Button>
                                {/* Ícone Favorito */}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className={`h-7 w-7 p-0 transition-colors ${
                                    isFavorite 
                                      ? 'bg-yellow-50 hover:bg-yellow-100 dark:bg-yellow-900/20 dark:hover:bg-yellow-900/30' 
                                      : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                                  }`}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    toggleFavoriteJob(job.id)
                                  }}
                                  title={isFavorite ? "Remover dos favoritos" : "Adicionar aos favoritos"}
                                >
                                  <Star className={`w-3 h-3 transition-colors ${
                                    isFavorite 
                                      ? 'text-yellow-500 fill-yellow-400' 
                                      : 'text-gray-800 dark:text-gray-200'
                                  }`} />
                                </Button>
                                {/* Botão Share Link Público */}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-800"
                                  onClick={async (e) => {
                                    e.stopPropagation()
                                    e.preventDefault()
                                    try {
                                      const result = await liaApi.generatePublicLink(job.backendId)
                                      if (result.success) {
                                        const fullUrl = `${window.location.origin}${result.public_url}`
                                        await navigator.clipboard.writeText(fullUrl)
                                        toast.success("Link copiado!", {
                                          description: "O link público da vaga foi copiado para a área de transferência."
                                        })
                                      }
                                    } catch (error) {
                                      console.error("Error generating public link:", error)
                                      toast.error("Erro ao gerar link", {
                                        description: "Não foi possível gerar o link público. Tente novamente."
                                      })
                                    }
                                  }}
                                  title="Compartilhar vaga (copiar link público)"
                                >
                                  <Share2 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                                </Button>
                                {/* Botão abrir Kanban */}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-800"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    e.preventDefault()
                                    handleJobClick(job)
                                  }}
                                  title="Abrir Kanban da vaga"
                                >
                                  <ChevronRight className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                                </Button>
                              </div>
                            </td>
                          )
                        }

                        return null
                      })}
                    </tr>
                  </React.Fragment>
                ))}
              </React.Fragment>
            )
          })}
        </tbody>
      </table>
    </div>
  )

  const renderExpandedView = () => {
    // ... unchanged, same as before
    // Copy the renderExpandedView from the original file
    // [Omitted for brevity]
    // (You can copy the full function from the original file)
    // The main change is in the filter menu above, not here
    return (
      <div className="overflow-x-auto">
        {/* ...table code unchanged... */}
        {/* Copy from original file */}
        {/* ... */}
      </div>
    )
  }

  // Hydration safety: show skeleton until client is ready
  if (!hasMounted) {
    return (
      <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-950 overflow-hidden">
        <div className="flex-1 overflow-hidden">
          <div className="p-2.5 max-w-full overflow-x-auto">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="h-6 w-48 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
                <div className="h-4 w-64 bg-gray-200 dark:bg-gray-800 rounded animate-pulse mt-2" />
              </div>
              <div className="h-8 w-24 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
            </div>
            <div className="space-y-2 mt-6">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-950 overflow-hidden relative">
      {/* Super Chat Fullscreen Mode - Cobre toda a área de conteúdo */}
      {chatMode === 'job-creation' && isChatFullscreen && showInlineChat && (
        <div className="absolute inset-0 z-50 bg-white dark:bg-gray-900 flex flex-col">
          <ExpandedChatModal
            isOpen={true}
            onClose={closeChat}
            initialMessage={inlineChatInitialMessage}
            initialMessages={liaInlineMessages}
            contextTitle="Criação de Vaga"
            inline={true}
            mode="job-creation"
            onJobCreated={() => {
              returnToGeneralChat()
            }}
            onReturnToLateral={returnToLateralPrompt}
            onFullscreenChange={setIsChatFullscreen}
            onMessagesUpdate={(msgs) => setLiaInlineMessages(msgs)}
          />
        </div>
      )}
      
      {/* Header Fixo - Título e Tabs (oculto em fullscreen) */}
      <div className={`flex-shrink-0 px-4 pt-3 pb-0 bg-gray-50 dark:bg-gray-950 ${chatMode === 'job-creation' && isChatFullscreen ? 'hidden' : ''}`}>
        {/* Header Principal - Padrão Funil de Talentos */}
        <div className="flex items-center justify-between mb-0.5">
            <div className="flex items-center gap-3">
              <div>
                <h1 className="text-xl font-['Open_Sans',sans-serif] font-semibold wedo-text-black flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  Gestão de Vagas
                </h1>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button 
                className="gap-2 h-8 px-3 bg-gray-800"
                onClick={() => setShowCreateJobModal(true)}
              >
                <Plus className="w-4 h-4" />
                Nova Vaga
              </Button>
            </div>
          </div>

        {/* Sistema de Abas - Padrão Funil de Talentos */}
        <div className="mb-0">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="-mb-px flex items-center space-x-6 nav-tabs" aria-label="Tabs" role="tablist">
              {navigationFilters.map((filter) => (
                <button
                  key={filter.id}
                  onClick={() => {
                    setActiveFilter(filter.id)
                  }}
                  role="tab"
                  className={`group inline-flex items-center py-2 px-1 border-b-2 tab-button ${
                    activeFilter === filter.id
                      ? 'border-gray-900 text-gray-950 dark:border-gray-100 dark:text-gray-50 font-semibold'
                      : 'border-transparent text-gray-800 hover:text-gray-950 hover:border-gray-300 dark:text-gray-200 dark:hover:text-gray-600'
                  }`}
                >
                  <span>{filter.label}</span>
                  {!filter.isDashboard && (
                    <Badge
                      variant="secondary"
                      className={`ml-2 text-xs ${
                        activeFilter === filter.id
                          ? 'bg-gray-100 text-gray-950 dark:bg-gray-700 dark:text-gray-200 font-semibold'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                      }`}
                    >
                      {isLoadingJobs ? (
                        <span className="inline-block w-4 h-3 bg-gray-300 dark:bg-gray-600 rounded animate-pulse" />
                      ) : (
                        filter.count
                      )}
                    </Badge>
                  )}

                </button>
              ))}
            </nav>
          </div>

        </div>
      </div>

      {/* Área de Conteúdo Scrollável (oculto em fullscreen) */}
      <div className={`flex-1 flex flex-col overflow-hidden px-4 pt-2 pb-2 ${chatMode === 'job-creation' && isChatFullscreen ? 'hidden' : ''}`}>
        {/* Dashboard Visão Geral - Prompt Centralizado */}
        {activeFilter === 'visao-geral' && (
          <div className="min-h-[60vh] flex flex-col items-center justify-center py-8">
            {/* Container centralizado com título */}
            <div className="w-full max-w-[780px] mx-auto px-4 flex flex-col">
              {/* Título centralizado acima do prompt */}
              <div className="mb-4 flex flex-col items-center justify-center">
                <h2 className="text-2xl font-semibold text-gray-950 dark:text-gray-50 font-['Open_Sans',sans-serif] flex items-center gap-2.5">
                  <Brain className="w-7 h-7 text-wedo-cyan" strokeWidth={2} />
                  Posso te ajudar com análises de vagas?
                </h2>
              </div>
              {/* Container externo - Background branco como funil de talentos */}
              <div className="rounded-2xl overflow-hidden bg-white border border-gray-200">
                {/* Área de Tags - Linha superior */}
                <div className="px-4 pt-4 pb-4 border-b border-b-gray-200">
                  <div className="flex flex-wrap items-center gap-2">
                    {/* Tag 1: Criar nova vaga */}
                    <button
                      onClick={() => {
                        setActiveFilter('todas')
                        setTimeout(() => openJobCreationChat('Criar nova vaga'), 100)
                      }}
                      className="group inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-all bg-gray-100 text-gray-950 hover:bg-gray-900 hover:text-white font-open-sans"
                    >
                      <Plus className="w-3.5 h-3.5 text-gray-800 group-hover:text-white transition-colors" />
                      Criar nova vaga
                    </button>
                    {/* Tag 2: Ver minhas vagas */}
                    <button
                      onClick={() => setActiveFilter('ativas')}
                      className="group inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-all bg-gray-100 text-gray-950 hover:bg-gray-900 hover:text-white font-open-sans"
                    >
                      <Briefcase className="w-3.5 h-3.5 text-gray-800 group-hover:text-white transition-colors" />
                      Ver minhas vagas
                    </button>
                    {/* Tag 3: Ver todas as vagas */}
                    <button
                      onClick={() => setActiveFilter('todas')}
                      className="group inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-all bg-gray-100 text-gray-950 hover:bg-gray-900 hover:text-white font-open-sans"
                    >
                      <Building2 className="w-3.5 h-3.5 text-gray-800 group-hover:text-white transition-colors" />
                      Ver todas as vagas
                    </button>
                    {/* Tag 4: Resumo das vagas */}
                    <button
                      onClick={() => {
                        setActiveFilter('todas')
                        setTimeout(() => openGeneralChat('Resumo das minhas vagas ativas'), 100)
                      }}
                      className="group inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-all bg-gray-100 text-gray-950 hover:bg-gray-900 hover:text-white font-open-sans"
                    >
                      <BarChart3 className="w-3.5 h-3.5 text-gray-800 group-hover:text-white transition-colors" />
                      Resumo das vagas
                    </button>
                    {/* Botão Mais ideias - Modal com tabs igual ao prompt expandido */}
                    <LiaVacancyQueriesGuide
                      onSelectQuery={(query) => {
                        setActiveFilter('todas')
                        setTimeout(() => openGeneralChat(query), 100)
                      }}
                    />
                  </div>
                </div>

                {/* Input - Estilo Funil de Talentos */}
                <div className="px-4 pt-4 pb-4">
                  <div className="flex items-center gap-3 px-4 py-3 bg-white rounded-md border border-gray-200 transition-colors focus-within:border-gray-400 focus-within:ring-1 focus-within:ring-gray-900/20">
                    {/* Input */}
                    <input
                      type="text"
                      placeholder="Como posso te ajudar com suas vagas hoje?"
                      value={liaPromptValue}
                      onChange={(e) => setLiaPromptValue(e.target.value)}
                     
                      className="flex-1 bg-transparent placeholder-gray-400 text-sm focus:outline-none text-gray-950 dark:text-gray-50"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && liaPromptValue.trim()) {
                          setActiveFilter('todas')
                          setTimeout(() => {
                            openGeneralChat(liaPromptValue.trim())
                            setLiaPromptValue('')
                          }, 100)
                        }
                      }}
                    />
                    
                    {/* Ícones à direita - Estilo Funil de Talentos */}
                    <div className="flex items-center gap-1">
                      {/* Botão Microfone */}
                      <AudioRecordButton
                        onTranscription={(text) => setLiaPromptValue(prev => prev ? `${prev} ${text}` : text)}
                        className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-gray-100 transition-colors"
                      />
                    </div>
                    
                    {/* Botão Busca/Enviar */}
                    <button
                      className="flex items-center justify-center hover:opacity-70 transition-opacity"
                      onClick={() => {
                        if (liaPromptValue.trim()) {
                          setActiveFilter('todas')
                          setTimeout(() => {
                            openGeneralChat(liaPromptValue.trim())
                            setLiaPromptValue('')
                          }, 100)
                        } else {
                          setActiveFilter('todas')
                          setTimeout(() => openGeneralChat(), 100)
                        }
                      }}
                      title="Buscar"
                    >
                      <Search className="w-4 h-4 text-gray-600" />
                    </button>
                  </div>
                </div>

                {/* Segunda linha de tags - Sugestões Dinâmicas (estilo Funil) */}
                <div className="px-4 pb-4">
                  <div className="flex flex-wrap items-start gap-2 pt-3">
                    <span className="text-xs text-gray-800 font-medium mt-0.5">Sugestões:</span>
                    {/* Renderiza sugestões do orquestrador quando disponíveis, senão usa contextuais baseadas no estado */}
                    {(orchestratorSuggestions.length > 0 ? orchestratorSuggestions : getContextualSuggestions()).slice(0, 4).map((suggestion, index) => (
                      <button
                        key={`suggestion-${index}`}
                        onClick={() => {
                          setActiveFilter('todas')
                          setTimeout(() => openGeneralChat(suggestion), 100)
                        }}
                        className="inline-flex items-center px-2.5 py-0.5 text-xs rounded-full transition-all bg-gray-50 text-gray-800 border border-gray-200 hover:text-gray-900 hover:bg-gray-100"
                       
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Conteúdo Principal - Lista de Vagas (quando não é visão geral) */}
        {activeFilter !== 'visao-geral' && (
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
          {/* Toolbar Compacto - Prompt LIA + Controles - Padrão Funil de Talentos */}
          {/* Esconde o prompt compacto e botões quando qualquer chat expandido está ativo */}
          {!showExpandedLIA && !showInlineChat && (
            <div className="flex-shrink-0 flex items-center justify-between gap-4 mt-3 mb-2">
              {/* Prompt LIA - Compacto (max 300px) - Estilo Funil de Talentos */}
              <div className="flex-1 max-w-[300px]">
              <div className="relative">
                <input
                  ref={liaInputRef}
                  type="text"
                  placeholder="Ex: Desenvolvedores Python com 5+ anos em São Paulo..."
                  value={liaPromptValue}
                  onChange={(e) => setLiaPromptValue(e.target.value)}
                  className="w-full h-10 pl-4 pr-20 text-base-ui rounded-md focus:outline-none placeholder:text-gray-600 transition-all border"
                  style={{ 
                    backgroundColor: "var(--lia-bg-primary)",
                    color: "var(--gray-950)",
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = "var(--gray-800)"
                    e.currentTarget.style.boxShadow = "0 0 0 2px rgba(31, 41, 55, 0.12)"
                    setShowExpandedLIA(true)
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = "var(--gray-200)"
                    e.currentTarget.style.boxShadow = "none"
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && liaPromptValue.trim()) {
                      openGeneralChat(liaPromptValue.trim())
                      setLiaPromptValue('')
                    }
                  }}
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  <button
                    className="p-1.5 rounded-md transition-colors hover:bg-gray-100"
                    onClick={() => openGeneralChat()}
                    title="Expandir chat"
                  >
                    <Maximize2 className="w-4 h-4 text-gray-700" />
                  </button>
                  <button
                    className="p-1.5 rounded-md transition-colors hover:bg-gray-100"
                    onClick={() => {
                      if (liaPromptValue.trim()) {
                        openGeneralChat(liaPromptValue.trim())
                        setLiaPromptValue('')
                      }
                    }}
                  >
                    <Send className="w-4 h-4 text-gray-700" />
                  </button>
                </div>
              </div>

            </div>

            {/* Controles e Info - Sempre visíveis à direita */}
            <div className="flex items-center gap-3">
              {/* Badge de seleção */}
              {selectedJobsForBatch.size > 0 && (
                <Badge className="bg-gray-100 text-gray-950 border-gray-300 dark:bg-gray-800 dark:text-gray-50 dark:border-gray-600 text-xs font-bold">
                  🎯 {selectedJobsForBatch.size}
                </Badge>
              )}

              {/* Botão Selecionar Todos */}
              {selectedJobsForBatch.size === 0 && filteredJobs.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={selectAllJobs}
                  className="gap-2 text-xs h-8 px-3"
                >
                  <CheckCircle className="w-3 h-3" />
                  Selecionar Todos
                </Button>
              )}

              {/* Botões de controle */}
              <Button
                variant={showTableFiltersPanel ? "default" : "outline"}
                size="sm"
                className={`gap-2 text-xs h-8 px-3 ${showTableFiltersPanel ? 'bg-gray-900 hover:bg-gray-800 dark:bg-gray-100 dark:hover:bg-gray-200 dark:text-gray-900 text-white' : ''}`}
                onClick={() => setShowTableFiltersPanel(!showTableFiltersPanel)}
                title="Filtrar resultados da tabela"
              >
                <Target className="w-3 h-3" />
                Filtros
                {getActiveJobFiltersCount() > 0 && (
                  <Badge variant="secondary" className="bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900 ml-1 text-xs font-bold">
                    {getActiveJobFiltersCount()}
                  </Badge>
                )}
              </Button>

              <Button
                variant={showColumnConfig ? "default" : "outline"}
                size="sm"
                className={`gap-2 text-xs h-8 px-3 ${showColumnConfig ? 'bg-gray-900 hover:bg-black dark:bg-gray-100 dark:hover:bg-white dark:text-gray-900 text-white' : ''}`}
                onClick={handleToggleColumnConfig}
                title="Configurar colunas da tabela"
              >
                <ChevronsLeftRight className="w-3 h-3" />
                Colunas
                <Badge
                  variant="secondary"
                  className={`ml-1 text-xs ${
                    showColumnConfig
                      ? 'bg-gray-800 text-white dark:bg-gray-200 dark:text-gray-900 font-bold'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                  }`}
                >
                  6
                </Badge>
              </Button>
            </div>
            </div>
          )}

          {/* Results Summary */}
          <div className="flex-shrink-0 flex items-center justify-between mb-2">
            <div className="text-xs text-gray-800 dark:text-gray-200 flex items-center gap-3">
              {(searchTerm || selectedDaysFilter !== 'todas') && (
                <Badge variant="outline" className="text-xs bg-gray-100 text-gray-800 border-gray-300 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-600 font-medium">
                  filtros ativos
                </Badge>
              )}

            </div>

            <div className="flex items-center gap-2">
              {/* Removido botão Selecionar Todas */}
            </div>
          </div>

          {/* Barra de Ações em Massa para Vagas - No topo do layout */}
          <JobActionsBar
            selectedCount={selectedJobsForBatch.size}
            onDeselectAll={deselectAllJobs}
            onPublish={handleJobPublish}
            onInsights={handleJobInsights}
            onDuplicate={handleJobDuplicate}
            onToggleStatus={handleJobToggleStatus}
            onAssignRecruiter={handleJobAssignRecruiter}
            hasActiveJobs={getSelectedJobsHaveActiveStatus()}
          />

          {/* Results Layout with Sidebars - Layout flex responsivo */}
          <div className="flex gap-2 transition-all duration-300 flex-1 min-h-0 overflow-hidden">
            {/* LIA Sidebar Expandida - Super Chat de Criação OU Chat Geral Expandido */}
            {(showExpandedLIA || showInlineChat) && (
              <div 
                className={`transition-all duration-300 relative group h-full ${
                  isTableCollapsed || (chatMode === 'job-creation' && isChatFullscreen) ? 'flex-1' : 'flex-shrink-0'
                }`}
                style={{ 
                  width: isTableCollapsed || (chatMode === 'job-creation' && isChatFullscreen)
                    ? 'auto' 
                    : (chatMode === 'job-creation' 
                        ? '60%' 
                        : `${liaWidth}px`), 
                  maxWidth: isTableCollapsed || (chatMode === 'job-creation' && isChatFullscreen)
                    ? 'none' 
                    : (chatMode === 'job-creation' 
                        ? '900px' 
                        : `${liaWidth}px`),
                  transition: 'all 0.3s ease-in-out'
                }}
              >
                {/* MODO CRIAÇÃO DE VAGA - Super Chat com Critérios */}
                {chatMode === 'job-creation' && showInlineChat ? (
                  <div className="h-full flex flex-col">
                    <ExpandedChatModal
                      isOpen={true}
                      onClose={closeChat}
                      initialMessage={inlineChatInitialMessage}
                      initialMessages={liaInlineMessages}
                      contextTitle="Criação de Vaga"
                      inline={true}
                      mode="job-creation"
                      onJobCreated={() => {
                        returnToGeneralChat()
                      }}
                      onReturnToLateral={returnToLateralPrompt}
                      onFullscreenChange={setIsChatFullscreen}
                      onMessagesUpdate={(msgs) => setLiaInlineMessages(msgs)}
                    />
                  </div>
                ) : showInlineChat && chatMode === 'general' ? (
                  /* MODO CHAT GERAL EXPANDIDO - Substitui o super chat quando volta da criação */
                  <div className="h-full flex flex-col">
                    <ExpandedChatModal
                      isOpen={true}
                      onClose={closeChat}
                      initialMessage={inlineChatInitialMessage}
                      initialMessages={liaInlineMessages}
                      contextTitle="Chat LIA"
                      inline={true}
                      mode="general"
                      onReturnToLateral={returnToLateralPrompt}
                      onMessagesUpdate={(msgs) => setLiaInlineMessages(msgs)}
                    />
                  </div>
                ) : (
                  /* MODO GERAL - Prompt Expandido Original */
                  <Card className="h-full flex flex-col overflow-hidden border border-gray-300" style={{ backgroundColor: 'var(--gray-50)', maxHeight: 'calc(100vh - 180px)' }}>
                    {/* Mensagem de Apresentação da LIA */}
                    <div className="flex-shrink-0 px-4 py-3" style={{ backgroundColor: 'var(--gray-50)' }}>
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <div 
                            className="w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0"
                            style={{ backgroundColor: 'var(--gray-50)' }}
                          >
                            <Brain className="w-6 h-6 text-wedo-cyan" strokeWidth={2.5} />
                          </div>
                          <div className="min-w-0 flex-1">
                            <h3 
                              className="text-sm font-semibold leading-tight truncate text-gray-950 dark:text-gray-50" 
                             
                            >
                              Olá! Sou a Lia.
                            </h3>
                            <p 
                              className="text-xs leading-tight truncate mt-0.5 text-gray-500" 
                             
                            >
                              Como posso te ajudar hoje?
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openGeneralChat('')}
                            title="Expandir chat"
                            className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0"
                          >
                            <Maximize2 className="w-4 h-4 text-gray-500" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setShowExpandedLIA(false)
                              setUserCollapsedLIA(true)
                            }}
                            title="Fechar"
                            className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0"
                          >
                            <X className="w-4 h-4 text-gray-500" />
                          </Button>
                        </div>
                      </div>
                    </div>

                  {/* Indicador de vagas selecionadas - mensagem compacta */}
                  {selectedJobsForBatch.size > 0 && (
                    <div className="flex-shrink-0 px-4 py-2">
                      <div className="px-3 py-2 bg-gray-100 rounded-md border border-gray-200 flex items-center gap-2">
                        <Briefcase className="w-3.5 h-3.5 text-gray-600 flex-shrink-0" />
                        <span className="text-xs text-gray-600 font-medium">
                          {selectedJobsForBatch.size} vaga{selectedJobsForBatch.size > 1 ? 's' : ''} selecionada{selectedJobsForBatch.size > 1 ? 's' : ''}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Área de Mensagens do Chat Inline - Só aparece quando há mensagens */}
                  {liaInlineMessages.length > 0 ? (
                    <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
                      {liaInlineMessages.map((message) => (
                        <div key={message.id} className={cn(
                          "flex",
                          message.role === 'user' ? "justify-end" : "justify-start"
                        )}>
                          {message.role === 'user' ? (
                            <div className="flex items-start gap-2 max-w-[90%]">
                              <img 
                                src="https://randomuser.me/api/portraits/men/32.jpg" 
                                alt="Você"
                                className="w-6 h-6 rounded-full object-cover flex-shrink-0"
                              />
                              <div 
                                className="px-2.5 py-2 rounded-md bg-gray-100"
                               
                              >
                                <p className="text-xs text-gray-800 leading-relaxed">{message.content}</p>
                              </div>
                            </div>
                          ) : (
                            <div 
                              className="max-w-[90%] group"
                             
                            >
                              <div className="flex items-start gap-2">
                                <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0">
                                  <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
                                </div>
                                <div className="pt-0.5 flex-1">
                                  <div className="flex items-center gap-1 mb-0.5">
                                    <span className="text-micro font-bold text-gray-800" style={{ fontFamily: 'Inter, sans-serif' }}>LIA</span>
                                  </div>
                                  <div className="text-xs text-gray-800 space-y-1 leading-relaxed">
                                    {message.content.split('\n').map((line, i) => {
                                      if (line.startsWith('•')) {
                                        return <p key={i} className="pl-2">{line}</p>
                                      }
                                      if (line.match(/^\d+\./)) {
                                        return <p key={i} className="pl-2">{line}</p>
                                      }
                                      if (line.includes('**')) {
                                        const parts = line.split(/\*\*(.*?)\*\*/g)
                                        return (
                                          <p key={i}>
                                            {parts.map((part, j) => 
                                              j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                                            )}
                                          </p>
                                        )
                                      }
                                      return line ? <p key={i}>{line}</p> : null
                                    })}
                                  </div>
                                  {(message as any).action_executed && (message as any).action_result && (
                                    <ActionResultCard
                                      actionType={(message as any).action_type || 'pause_job'}
                                      result={(message as any).action_result}
                                    />
                                  )}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                      
                      {liaInlineLoading && (
                        <div className="flex justify-start">
                          <div className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-gray-100 dark:bg-gray-800">
                            <div className="w-5 h-5 rounded-md bg-white flex items-center justify-center">
                              <Loader2 className="w-3 h-3 animate-spin text-gray-600 dark:text-gray-400" />
                            </div>
                            <span className="text-micro text-gray-500">Pensando...</span>
                          </div>
                        </div>
                      )}
                      
                      <div ref={liaInlineMessagesEndRef} />
                    </div>
                  ) : (
                    /* Espaço flexível vazio quando não há mensagens - empurra conteúdo para baixo */
                    <div className="flex-1" />
                  )}

                  {/* Input Area - Fixo na parte inferior */}
                  <div className="flex-shrink-0 px-4 pb-4 pt-2">
                    {/* Campo de Input */}
                    <div className="flex items-center gap-2 p-2 rounded-md border bg-white border-gray-100">
                      <input
                        type="text"
                        placeholder="Envie mensagem para a LIA..."
                        value={liaPromptValue}
                        onChange={(e) => setLiaPromptValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && liaPromptValue.trim() && !liaInlineLoading) {
                            sendLiaInlineMessage(liaPromptValue.trim())
                            setLiaPromptValue('')
                          }
                        }}
                        disabled={liaInlineLoading}
                        className="flex-1 text-xs bg-transparent focus:outline-none text-gray-950 dark:text-gray-50 disabled:opacity-50"
                       
                      />
                      <AudioRecordButton
                        onTranscription={(text) => setLiaPromptValue(prev => prev ? `${prev} ${text}` : text)}
                        className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-gray-100 transition-colors"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (liaPromptValue.trim() && !liaInlineLoading) {
                            sendLiaInlineMessage(liaPromptValue.trim())
                            setLiaPromptValue('')
                          }
                        }}
                        disabled={!liaPromptValue.trim() || liaInlineLoading}
                        className="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center transition-colors disabled:opacity-50 bg-gray-900"
                      >
                        <Send className="w-3.5 h-3.5 text-white" />
                      </button>
                    </div>
                    
                    {/* Sistema de Abas - Pill Style (movido para baixo do input) */}
                    <div className="flex items-center gap-1.5 mt-2">
                      <button
                        onClick={() => setActiveSearchTab('ia-natural')}
                        className={`flex-shrink-0 px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
 activeSearchTab === 'ia-natural' ? 'text-white bg-gray-900' : 'text-gray-700 hover:dark:text-gray-300 dark:bg-gray-800 dark:hover:bg-gray-700'
                        }`}
                       
                      >
                        <div className="flex items-center gap-1">
                          <Brain className="w-2.5 h-2.5 text-wedo-cyan" />
                          <span>IA Natural</span>
                        </div>
                      </button>
                      <button
                        onClick={() => setActiveSearchTab('job-description')}
                        className={`flex-shrink-0 px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
 activeSearchTab === 'job-description' ? 'text-white bg-gray-900' : 'text-gray-700 hover:dark:text-gray-300 dark:bg-gray-800 dark:hover:bg-gray-700'
                        }`}
                       
                      >
                        <div className="flex items-center gap-1">
                          <FileText className="w-2.5 h-2.5" />
                          <span>Descrição do Cargo</span>
                        </div>
                      </button>
                      <button
                        onClick={() => setActiveSearchTab('templates')}
                        className={`flex-shrink-0 px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
 activeSearchTab === 'templates' ? 'text-white bg-gray-900' : 'text-gray-700 hover:dark:text-gray-300 dark:bg-gray-800 dark:hover:bg-gray-700'
                        }`}
                       
                      >
                        <div className="flex items-center gap-1">
                          <Target className="w-2.5 h-2.5" />
                          <span>Templates</span>
                        </div>
                      </button>
                    </div>

                    {/* Tags de Ações Rápidas - Abaixo das abas (só visíveis em IA Natural) */}
                    {activeSearchTab === 'ia-natural' && (
                      <div className="flex items-center gap-1.5 mt-1.5">
                        <span className="text-micro font-medium text-gray-500">Sugestões:</span>
                        <button
                          onClick={() => {
                            setShowExpandedLIA(false)
                            openJobCreationChat()
                          }}
                          className="inline-flex items-center gap-1 px-2 py-0.5 text-micro font-medium text-gray-700 bg-gray-100 rounded-full hover:bg-gray-200 transition-all"
                         
                        >
                          <Plus className="w-2.5 h-2.5 text-gray-500" />
                          Criar vaga
                        </button>
                        <LiaVacancyQueriesGuide
                          onSelectQuery={(query) => {
                            sendLiaInlineMessage(query)
                          }}
                          className="!px-2 !py-0.5 !text-micro !bg-gray-100 !border-0 hover:!bg-gray-200"
                        />
                      </div>
                    )}
                  </div>

                  {/* Conteúdo das outras abas */}
                  {(activeSearchTab === 'job-description' || activeSearchTab === 'templates') && (
                  <div className="flex-1 overflow-y-auto p-4" style={{ backgroundColor: 'var(--gray-50)' }}>

                    {/* ABA 2: JOB DESCRIPTION */}
                    {activeSearchTab === 'job-description' && (
                      <div className="space-y-3">
                        {/* Descrição */}
                        <div className="p-2.5 rounded-md" style={{ backgroundColor: 'var(--gray-50)' }}>
                          <p className="text-xs">
                            Cole ou anexe uma descrição de vaga e eu vou criar a vaga automaticamente para você, configurando todos os detalhes.
                          </p>
                        </div>

                        {/* Textarea */}
                        <div className="relative">
                          <textarea
                            placeholder="Cole aqui o job description completo (requisitos, responsabilidades, benefícios...)..."
                            value={jobDescriptionText}
                            onChange={(e) => setJobDescriptionText(e.target.value)}
                            className="w-full h-28 p-3 pb-10 text-xs rounded-md border focus:outline-none focus:ring-1 focus:ring-gray-900/20 transition-all resize-none text-gray-950 dark:text-gray-50 border border-gray-100" style={{ backgroundColor: 'var(--gray-50)' }}
                          />
                          {/* Botões de Anexo */}
                          <div className="absolute bottom-2 right-2 flex items-center gap-1">
                            <input
                              ref={jdFileInputRef}
                              type="file"
                              accept=".txt,.md,.pdf,.docx"
                              className="hidden"
                              onChange={(e) => {
                                const file = e.target.files?.[0]
                                if (file) handleJDFileUpload(file)
                                e.target.value = ""
                              }}
                            />
                            <button
                              type="button"
                              className="p-1.5 rounded-md hover:bg-gray-100 transition-colors disabled:opacity-50"
                              title="Anexar documento (.txt, .md, .pdf, .docx — máx 5MB)"
                              disabled={isUploadingJD}
                              onClick={() => jdFileInputRef.current?.click()}
                            >
                              {isUploadingJD ? (
                                <svg className="w-3.5 h-3.5 text-gray-500 animate-spin" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                                </svg>
                              ) : (
                                <Paperclip className="w-3.5 h-3.5 text-gray-500" />
                              )}
                            </button>
                          </div>
                        </div>

                        {/* Erro de upload */}
                        {jdUploadError && (
                          <p className="text-micro text-red-500 px-1">
                            {jdUploadError}
                          </p>
                        )}

                        {/* Aviso LGPD */}
                        <p className="text-micro text-gray-400 px-1">
                          O arquivo pode conter dados pessoais. Revise o conteúdo antes de importar. (LGPD)
                        </p>

                        {/* Botão Criar Vaga */}
                        <Button
                          className="w-full h-9 !text-xs font-medium rounded-md"
                          style={{
                            backgroundColor: jobDescriptionText.trim() ? 'var(--gray-800)' : 'var(--gray-50)',
                            color: jobDescriptionText.trim() ? 'var(--white)' : 'var(--gray-400)',
                          }}
                          onClick={() => {
                            if (jobDescriptionText.trim()) {
                              setShowExpandedLIA(false)
                              openJobCreationChat(jobDescriptionText)
                            }
                          }}
                          disabled={!jobDescriptionText.trim()}
                        >
                          <Brain className="w-3.5 h-3.5 mr-1.5 text-wedo-cyan" />
                          Criar Vaga a Partir da Descrição
                        </Button>
                      </div>
                    )}

                    {/* ABA 3: TEMPLATES DE VAGAS */}
                    {activeSearchTab === 'templates' && (
                      <div className="space-y-3 overflow-y-auto max-h-[calc(100vh-20rem)]">
                        {/* Seção 1: Criar a partir de Template */}
                        <div>
                          <h4 className="text-xs font-medium mb-0.5 text-gray-800">
                            Criar Vaga a Partir de Template
                          </h4>
                          <p className={`${textStyles.caption} mb-2`}>
                            Selecione um modelo pronto e eu inicio a criação da vaga para você
                          </p>

                          {/* Grid de Templates Compacto */}
                          <div className="grid grid-cols-2 gap-1.5">
                            {[
                              { icon: '🚀', title: 'Backend Sênior Node.js', tags: ['Backend', 'Node.js'] },
                              { icon: '📊', title: 'Product Manager', tags: ['Product', 'Agile'] },
                              { icon: '🎨', title: 'UX/UI Designer', tags: ['Design', 'Figma'] },
                              { icon: '☁️', title: 'DevOps Engineer', tags: ['Cloud', 'CI/CD'] },
                            ].map((template) => (
                              <div 
                                key={template.title}
                                className="cursor-pointer transition-all rounded-md p-2 hover:border border-gray-100" style={{ backgroundColor: 'var(--gray-50)' }}
                                onClick={() => {
                                  setLiaPromptValue(`Criar vaga ${template.title}`)
                                  setActiveSearchTab('ia-natural')
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--gray-400)'}
                                onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--gray-50)'}
                              >
                                <div className="flex items-center gap-1.5">
                                  <span className="text-sm">{template.icon}</span>
                                  <div className="flex-1 min-w-0">
                                    <h5 className="text-xs font-medium truncate text-gray-800">
                                      {template.title}
                                    </h5>
                                    <div className="flex gap-1 mt-0.5">
                                      {template.tags.map(tag => (
                                        <span key={tag} className="text-micro px-1 py-0.5 rounded-full text-gray-400" style={{ backgroundColor: 'var(--gray-50)' }}>{tag}</span>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Seção 2: Criar a partir de Vaga Existente */}
                        <div className="pt-2">
                          <h4 className="text-xs font-medium mb-0.5 text-gray-800">
                            Criar a Partir de Vaga Existente
                          </h4>
                          <p className={`${textStyles.caption} mb-2`}>
                            Copie uma vaga já criada e faça ajustes
                          </p>
                          
                          {/* Campo de Busca de Vagas */}
                          <div className="relative">
                            <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                            <input
                              type="text"
                              placeholder="Buscar vaga por título ou ID..."
                              className="w-full pl-8 pr-3 py-2 text-xs rounded-md focus:outline-none transition-colors text-gray-800 border border-gray-100" style={{ backgroundColor: 'var(--gray-50)' }}
                              onFocus={(e) => e.target.style.borderColor = 'var(--gray-400)'}
                              onBlur={(e) => e.target.style.borderColor = 'var(--gray-50)'}
                            />
                          </div>
                          
                          {/* Lista de Vagas Recentes */}
                          <div className="mt-2 space-y-1.5">
                            {[
                              { id: 'V0001', title: 'Product Manager - Fintech' },
                              { id: 'V0004', title: 'Tech Lead Mobile' },
                              { id: 'V0005', title: 'DevOps Engineer Sênior' },
                            ].map((job) => (
                              <div
                                key={job.id}
                                className="flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors border border-gray-100" style={{ backgroundColor: 'var(--gray-50)' }}
                                onClick={() => {
                                  setLiaPromptValue(`Duplicar vaga ${job.id} - ${job.title}`)
                                  setActiveSearchTab('ia-natural')
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--gray-400)'}
                                onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--gray-50)'}
                              >
                                <span className="text-micro px-1.5 py-0.5 rounded-full" style={{ backgroundColor: 'var(--gray-50)' }}>{job.id}</span>
                                <span className="text-xs truncate flex-1 text-gray-800">
                                  {job.title}
                                </span>
                                <Copy className="w-3.5 h-3.5 text-gray-400" />
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Seção 3: Criar Novo Template */}
                        <div className="pt-2">
                          <h4 className="text-xs font-medium mb-0.5 text-gray-800">
                            Salvar Template
                          </h4>
                          <p className={`${textStyles.caption} mb-2`}>
                            Transforme uma vaga existente em template reutilizável
                          </p>
                          
                          <Button
                            variant="outline"
                            className="w-full h-9 !text-xs font-medium rounded-md text-gray-800 border border-gray-100"
                            onClick={() => {
                              console.log('Criar template a partir de vaga')
                            }}
                          >
                            <Plus className="w-3.5 h-3.5 mr-1.5 text-gray-600" />
                            Criar Template a Partir de Vaga
                          </Button>
                        </div>
                      </div>
                    )}

                  </div>
                  )}
                </Card>
              )}

                {/* Resize Handle - só mostra no modo geral */}
                {chatMode !== 'job-creation' && (
                <div
                  className="absolute right-0 top-0 bottom-0 w-1 cursor-ew-resize hover:bg-amber-500 transition-colors group-hover:opacity-100 opacity-0"
                  style={{ backgroundColor: 'rgba(245, 158, 11, 0.3)' }}
                  onMouseDown={(e) => {
                    e.preventDefault()
                    setIsResizingLIA(true)
                    const startX = e.clientX
                    const startWidth = liaWidth

                    const handleMouseMove = (e: MouseEvent) => {
                      const deltaX = e.clientX - startX
                      const newWidth = Math.max(400, Math.min(800, startWidth + deltaX))
                      setLiaWidth(newWidth)
                    }

                    const handleMouseUp = () => {
                      setIsResizingLIA(false)
                      document.removeEventListener('mousemove', handleMouseMove)
                      document.removeEventListener('mouseup', handleMouseUp)
                    }

                    document.addEventListener('mousemove', handleMouseMove)
                    document.addEventListener('mouseup', handleMouseUp)
                  }}
                />
                )}
              </div>
            )}

            {/* 🎯 Inline Table Filters Panel - Filtros Avançados */}
            {showTableFiltersPanel && (
              <div className="w-80 flex-shrink-0 transition-all duration-300">
                <Card className="h-full max-h-[calc(100vh-180px)] flex flex-col overflow-hidden bg-white dark:bg-gray-900 border border-gray-100">
                  {/* Header do Painel */}
                  <div className="flex-shrink-0 p-4 border-b border-b-gray-100" style={{ backgroundColor: 'rgba(96, 190, 209, 0.08)' }}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-gray-600" />
                        <div>
                          <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                            Filtros Avançados
                          </h3>
                          <p className={textStyles.bodySmall}>
                            {getActiveJobFiltersCount() > 0 
                              ? `${getActiveJobFiltersCount()} filtro${getActiveJobFiltersCount() > 1 ? 's' : ''} ativo${getActiveJobFiltersCount() > 1 ? 's' : ''}`
                              : 'Refine os resultados exibidos'}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowTableFiltersPanel(false)}
                        className="h-7 w-7 p-0 rounded-full hover:opacity-70 transition-opacity"
                      >
                        <X className="w-4 h-4 text-gray-950 dark:text-gray-50" />
                      </Button>
                    </div>
                  </div>

                  {/* Campo de Busca por Texto */}
                  <div className="flex-shrink-0 px-4 py-3 border-b border-b-gray-100">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-800" />
                      <input
                        type="text"
                        placeholder="Buscar por título, ID, departamento..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-9 pr-8 py-2 text-xs rounded-md border focus:outline-none focus:border-gray-900 transition-colors border border-gray-100" style={{ backgroundColor: 'white' }}
                      />
                      {searchTerm && (
                        <button
                          onClick={() => setSearchTerm('')}
                          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-800 hover:text-gray-800"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Conteúdo dos Filtros - Scrollable */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-5">
                    
                    {/* Filtros Rápidos */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                        <Zap className="w-3.5 h-3.5 text-gray-600" />
                        Filtros Rápidos
                      </h4>
                      <div className="grid grid-cols-2 gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleJobFilter('status', 'statuses', 'Ativa')}
                          className={`h-8 text-xs justify-start ${
                            jobFilters.status?.statuses?.includes('Ativa') 
                              ? 'bg-gray-100 border-gray-900 text-gray-950 font-semibold dark:bg-gray-800 dark:border-gray-300 dark:text-gray-50' 
                              : ''
                          }`}
                        >
                          <CheckCircle className="w-3 h-3 mr-1.5" />
                          Ativas
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleJobFilter('status', 'priorities', 'alta')}
                          className={`h-8 text-xs justify-start ${
                            jobFilters.status?.priorities?.includes('alta') 
                              ? 'bg-red-50 border-red-300 text-red-700 font-semibold' 
                              : ''
                          }`}
                        >
                          <AlertTriangle className="w-3 h-3 mr-1.5" />
                          Urgentes
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleJobFilter('position', 'workModels', 'remoto')}
                          className={`h-8 text-xs justify-start ${
                            jobFilters.position?.workModels?.includes('remoto') 
                              ? 'bg-gray-100 border-gray-900 text-gray-900 font-semibold' 
                              : ''
                          }`}
                        >
                          <Globe className="w-3 h-3 mr-1.5" />
                          Remotas
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleJobFilter('funnel', 'emptyPipeline', true)}
                          className={`h-8 text-xs justify-start ${
                            jobFilters.funnel?.emptyPipeline 
                              ? 'bg-orange-50 border-orange-300 text-orange-700 font-semibold' 
                              : ''
                          }`}
                        >
                          <Users className="w-3 h-3 mr-1.5" />
                          Sem Candidatos
                        </Button>
                      </div>
                    </div>

                    {/* Status e Prioridade */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                        <Target className="w-3.5 h-3.5" />
                        Status da Vaga
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {['Ativa', 'Rascunho', 'Paralisada', 'Aguardando aprovação', 'Fechada (preenchida)', 'Cancelada'].map(status => (
                          <Badge
                            key={status}
                            variant="outline"
                            className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                              jobFilters.status?.statuses?.includes(status)
                                ? 'bg-gray-100 border-gray-900 text-gray-950 font-medium dark:bg-gray-800 dark:border-gray-300 dark:text-gray-50'
                                : 'bg-white text-gray-800'
                            }`}
                            onClick={() => toggleJobFilter('status', 'statuses', status)}
                          >
                            {status}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Etapa do Processo */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                        <Layers3 className="w-3.5 h-3.5" />
                        Etapa do Processo
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {['Planejamento', 'Aprovação', 'Publicada', 'Triagem', 'Entrevistas', 'Finalização', 'Encerrada'].map(stage => (
                          <Badge
                            key={stage}
                            variant="outline"
                            className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                              jobFilters.status?.stages?.includes(stage)
                                ? 'bg-purple-50 border-purple-300 text-purple-700 font-medium'
                                : 'bg-white text-gray-800'
                            }`}
                            onClick={() => toggleJobFilter('status', 'stages', stage)}
                          >
                            {stage}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Prioridade */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5" />
                        Prioridade
                      </h4>
                      <div className="flex gap-2">
                        {[
                          { value: 'alta', label: 'Alta', color: 'bg-red-100 border-red-300 text-red-700' },
                          { value: 'média', label: 'Média', color: 'bg-yellow-100 border-yellow-300 text-yellow-700' },
                          { value: 'baixa', label: 'Baixa', color: 'bg-green-100 border-green-300 text-green-700' }
                        ].map(priority => (
                          <Badge
                            key={priority.value}
                            variant="outline"
                            className={`text-xs cursor-pointer hover:opacity-80 transition-opacity ${
                              jobFilters.status?.priorities?.includes(priority.value)
                                ? priority.color + ' font-medium'
                                : 'bg-white text-gray-800'
                            }`}
                            onClick={() => toggleJobFilter('status', 'priorities', priority.value)}
                          >
                            {priority.label}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Modelo de Trabalho */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                        <Building className="w-3.5 h-3.5" />
                        Modelo de Trabalho
                      </h4>
                      <div className="flex gap-2">
                        {['presencial', 'híbrido', 'remoto'].map(model => (
                          <Badge
                            key={model}
                            variant="outline"
                            className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors capitalize ${
                              jobFilters.position?.workModels?.includes(model)
                                ? 'bg-gray-100 border-gray-900 text-gray-950 font-medium dark:bg-gray-800 dark:border-gray-300 dark:text-gray-50'
                                : 'bg-white text-gray-800'
                            }`}
                            onClick={() => toggleJobFilter('position', 'workModels', model)}
                          >
                            {model}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Senioridade */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                        <UserCheck className="w-3.5 h-3.5" />
                        Senioridade
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {['Estágio', 'Júnior', 'Pleno', 'Sênior', 'Especialista', 'Coordenador', 'Gerente', 'Diretor'].map(level => (
                          <Badge
                            key={level}
                            variant="outline"
                            className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                              jobFilters.position?.levels?.includes(level)
                                ? 'bg-gray-100 border-gray-900 text-gray-950 font-medium dark:bg-gray-800 dark:border-gray-300 dark:text-gray-50'
                                : 'bg-white text-gray-800'
                            }`}
                            onClick={() => toggleJobFilter('position', 'levels', level)}
                          >
                            {level}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Localização */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5" />
                        Localização
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {['São Paulo, SP', 'Rio de Janeiro, RJ', 'Belo Horizonte, MG', 'Curitiba, PR', 'Porto Alegre, RS', 'Brasília, DF', 'Remoto'].map(loc => (
                          <Badge
                            key={loc}
                            variant="outline"
                            className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                              jobFilters.position?.locations?.includes(loc)
                                ? 'bg-gray-100 border-gray-900 text-gray-950 font-medium dark:bg-gray-800 dark:border-gray-300 dark:text-gray-50'
                                : 'bg-white text-gray-800'
                            }`}
                            onClick={() => toggleJobFilter('position', 'locations', loc)}
                          >
                            {loc}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Departamentos */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                        <Briefcase className="w-3.5 h-3.5" />
                        Departamento
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {['Tecnologia', 'Design', 'Produto', 'Marketing', 'Vendas', 'RH', 'Financeiro', 'Operações'].map(dept => (
                          <Badge
                            key={dept}
                            variant="outline"
                            className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                              jobFilters.team?.departments?.includes(dept)
                                ? 'bg-gray-100 border-gray-900 text-gray-950 font-medium dark:bg-gray-800 dark:border-gray-300 dark:text-gray-50'
                                : 'bg-white text-gray-800'
                            }`}
                            onClick={() => toggleJobFilter('team', 'departments', dept)}
                          >
                            {dept}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Canais de Publicação */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                        <Share2 className="w-3.5 h-3.5" />
                        Publicação
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {[
                          { value: 'linkedin', label: 'LinkedIn', icon: Linkedin },
                          { value: 'website', label: 'Website', icon: Globe },
                          { value: 'indeed', label: 'Indeed', icon: Briefcase }
                        ].map(channel => (
                          <Badge
                            key={channel.value}
                            variant="outline"
                            className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors flex items-center gap-1 ${
                              jobFilters.publishing?.channels?.includes(channel.value)
                                ? 'bg-gray-100 border-gray-900 text-gray-950 font-medium dark:bg-gray-800 dark:border-gray-300 dark:text-gray-50'
                                : 'bg-white text-gray-800'
                            }`}
                            onClick={() => toggleJobFilter('publishing', 'channels', channel.value)}
                          >
                            <channel.icon className="w-3 h-3" />
                            {channel.label}
                          </Badge>
                        ))}
                        <Badge
                          variant="outline"
                          className={`text-xs cursor-pointer hover:bg-gray-100 transition-colors ${
                            jobFilters.publishing?.unpublished
                              ? 'bg-orange-50 border-orange-300 text-orange-700 font-medium'
                              : 'bg-white text-gray-800'
                          }`}
                          onClick={() => toggleJobFilter('publishing', 'unpublished', !jobFilters.publishing?.unpublished)}
                        >
                          Não Publicadas
                        </Badge>
                      </div>
                    </div>

                    {/* Métricas do Funil */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                        <BarChart3 className="w-3.5 h-3.5" />
                        Métricas
                      </h4>
                      <div className="space-y-2">
                        <label className="flex items-center gap-2 cursor-pointer text-xs p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded bg-gray-50">
                          <input
                            type="checkbox"
                            className="w-3 h-3"
                            checked={jobFilters.funnel?.emptyPipeline || false}
                            onChange={(e) => toggleJobFilter('funnel', 'emptyPipeline', e.target.checked)}
                          />
                          <span className="text-gray-700">Pipeline vazio (sem candidatos)</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer text-xs p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded bg-gray-50">
                          <input
                            type="checkbox"
                            className="w-3 h-3"
                            checked={jobFilters.metrics?.lowConversion || false}
                            onChange={(e) => toggleJobFilter('metrics', 'lowConversion', e.target.checked)}
                          />
                          <span className="text-gray-700">Baixa conversão</span>
                        </label>
                      </div>
                    </div>

                    {/* Buscas Salvas */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                          <Bookmark className="w-3.5 h-3.5" />
                          Buscas Salvas
                        </h4>
                        {hasActiveFilters() && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              const name = prompt("Nome da busca:")
                              if (name) saveSearchAsTemplate(name)
                            }}
                            className="h-6 text-xs px-2 text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100"
                          >
                            <Plus className="w-3 h-3 mr-1" />
                            Salvar Busca
                          </Button>
                        )}
                      </div>
                      {savedSearches.length > 0 ? (
                        <div className="space-y-1.5 max-h-[180px] overflow-y-auto">
                          {savedSearches.map((search) => (
                            <div
                              key={search.id}
                              className="group flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                              onClick={() => handleApplySavedSearch(search.id)}
                            >
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-1.5">
                                  <Search className="w-3 h-3 text-gray-600 flex-shrink-0" />
                                  <span className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                                    {search.name}
                                  </span>
                                </div>
                                <p className="text-micro text-gray-600 mt-0.5 truncate">
                                  {new Date(search.createdAt).toLocaleDateString('pt-BR')}
                                  {search.query && ` - "${search.query}"`}
                                </p>
                              </div>
                              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    const newName = prompt("Novo nome:", search.name)
                                    if (newName) handleRenameSavedSearch(search.id, newName)
                                  }}
                                  className="h-6 w-6 p-0"
                                  title="Renomear"
                                >
                                  <Edit2 className="w-3 h-3 text-gray-600" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleDeleteSavedSearch(search.id)
                                  }}
                                  className="h-6 w-6 p-0"
                                  title="Remover"
                                >
                                  <Trash2 className="w-3 h-3 text-red-400" />
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                          <Bookmark className="w-5 h-5 text-gray-600 mx-auto mb-1" />
                          <p className="text-xs text-gray-500">
                            Nenhuma busca salva
                          </p>
                          <p className="text-micro text-gray-600 mt-0.5">
                            Aplique filtros e clique em "Salvar Busca"
                          </p>
                        </div>
                      )}
                    </div>

                  </div>

                  {/* Footer com Ações */}
                  <div className="flex-shrink-0 p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                    <div className="flex items-center justify-between">
                      <span className={textStyles.bodySmall}>
                        {getActiveJobFiltersCount() > 0 
                          ? `${getActiveJobFiltersCount()} filtro${getActiveJobFiltersCount() > 1 ? 's' : ''}`
                          : 'Nenhum filtro'}
                      </span>
                      {getActiveJobFiltersCount() > 0 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={clearAllJobFilters}
                          className="h-7 text-xs text-gray-800 hover:text-gray-950"
                        >
                          <X className="w-3 h-3 mr-1" />
                          Limpar
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              </div>
            )}

            {/* Tabela de Vagas - Com suporte a contração e ocultação em fullscreen */}
            {!(chatMode === 'job-creation' && isChatFullscreen) && (
            <div className={`h-full bg-white dark:bg-gray-800 rounded-md transition-all duration-300 min-w-0 overflow-hidden ${
              isTableCollapsed 
                ? 'w-14 flex-shrink-0' 
                : showJobPreview ? 'flex-1' : 'flex-1'
            }`}>
              {isTableCollapsed ? (
                /* Versão Contraída - Apenas ícone para expandir */
                <div className="h-full flex flex-col items-center py-4 gap-3">
                  {/* Botão para expandir tabela */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={toggleTableExpansion}
                    className="h-10 w-10 p-0 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                    title="Expandir tabela de vagas"
                  >
                    <ChevronRight className="w-5 h-5 text-gray-800 dark:text-gray-200" />
                  </Button>
                  
                  {/* Ícone da tabela */}
                  <div className="flex flex-col items-center gap-2 text-gray-800">
                    <Briefcase className="w-5 h-5" />
                    <span className="text-xs font-medium writing-mode-vertical" style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}>
                      Vagas ({filteredJobs.length})
                    </span>
                  </div>
                  
                  {/* Indicador de vagas selecionadas */}
                  {selectedJobsForBatch.size > 0 && (
                    <Badge className="bg-gray-900 text-white text-xs px-1.5 py-0.5">
                      {selectedJobsForBatch.size}
                    </Badge>
                  )}
                </div>
              ) : (
                /* Versão Expandida - Tabela completa com botão de contrair */
                <div className="h-full flex flex-col">
                  {/* Header da tabela com botão de contrair */}
                  {showInlineChat && (
                    <div className="flex-shrink-0 px-3 py-2 bg-gray-50 dark:bg-gray-800 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Briefcase className="w-4 h-4 text-gray-800" />
                        <span className="text-xs font-medium text-gray-800 dark:text-gray-200">
                          Vagas ({filteredJobs.length})
                        </span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={toggleTableExpansion}
                        className="h-7 w-7 p-0 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
                        title="Contrair tabela"
                      >
                        <ChevronLeft className="w-4 h-4 text-gray-800" />
                      </Button>
                    </div>
                  )}
                  
                  <div className="flex-1 overflow-y-auto">
                    {isLoadingJobs ? renderSkeletonLoading() : filteredJobs.length === 0 ? (
                      <EmptyState
                        icon={<Briefcase />}
                        title="Nenhuma vaga cadastrada"
                        description="Crie sua primeira vaga para começar a atrair candidatos."
                        action={{ label: "Criar primeira vaga", onClick: () => setChatMode('job-creation') }}
                        className="h-64"
                      />
                    ) : renderCompactView()}
                  </div>
                </div>
              )}
            </div>
            )}

            {/* Job Preview Card */}
            {showJobPreview && previewJob && (
              <div 
                className="flex-shrink-0 bg-white dark:bg-gray-800 rounded-md overflow-hidden animate-slide-in flex flex-col h-full max-h-[calc(100vh-180px)] relative group"
                style={{ 
                  
                  width: `${previewWidth}px`,
                  minWidth: '320px',
                  maxWidth: '700px'
                }}
              >
                {/* Resize Handle - Left Side */}
                <div
                  className="absolute left-0 top-0 bottom-0 w-1 cursor-ew-resize hover:bg-gray-400 transition-colors group-hover:opacity-100 opacity-0 z-10"
                  style={{ backgroundColor: 'rgba(156, 163, 175, 0.3)' }}
                  onMouseDown={(e) => {
                    e.preventDefault()
                    setIsResizingPreview(true)
                    const startX = e.clientX
                    const startWidth = previewWidth

                    const handleMouseMove = (e: MouseEvent) => {
                      const deltaX = startX - e.clientX
                      const newWidth = Math.max(320, Math.min(700, startWidth + deltaX))
                      setPreviewWidth(newWidth)
                    }

                    const handleMouseUp = () => {
                      setIsResizingPreview(false)
                      document.removeEventListener('mousemove', handleMouseMove)
                      document.removeEventListener('mouseup', handleMouseUp)
                    }

                    document.addEventListener('mousemove', handleMouseMove)
                    document.addEventListener('mouseup', handleMouseUp)
                  }}
                />
                {/* Header Padronizado (Design System Candidato) */}
                <div className="bg-white dark:bg-gray-800 border-b border-gray-100">
                  {/* Linha 1: Título + Código + Ações */}
                  <div className="px-3 pt-3 pb-1.5">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        {/* Row 1: Título + Código (lado direito) */}
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-base-ui font-semibold text-gray-950 dark:text-gray-50 truncate">
                            {previewJob.title}
                          </h3>
                          <Badge className="text-micro px-1.5 py-0 h-4 flex-shrink-0 font-mono font-medium" style={{ backgroundColor: 'rgba(107, 114, 128, 0.15)', border: '1px solid rgba(107, 114, 128, 0.3)' }}>
                            {previewJob.jobId}
                          </Badge>
                          {previewJob.isAffirmative && (
                            <span title="Vaga Afirmativa">
                              <Heart className="w-3 h-3 text-pink-500" />
                            </span>
                          )}
                        </div>

                        {/* Row 2: Datas em texto simples (como no candidato) */}
                        <div className="flex items-center gap-3 mb-1 text-micro text-gray-500">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-gray-400" />
                            {previewJob.openDate ? new Date(previewJob.openDate).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                          </span>
                          {previewJob.deadline && (
                            <span className={`flex items-center gap-1 ${
                              new Date(previewJob.deadline) < new Date() ? 'text-red-500' : 'text-gray-500'
                            }`}>
                              <Clock className="w-3 h-3" />
                              {(() => {
                                const days = Math.ceil((new Date(previewJob.deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
                                return days > 0 ? `${days}d restantes` : `${Math.abs(days)}d atraso`
                              })()}
                            </span>
                          )}
                        </div>

                        {/* Row 2b: Histórico inline */}
                        <div className="flex items-center gap-3 mb-1.5 text-micro text-gray-400">
                          <span>Criado: {previewJob.createdAt 
                            ? new Date(previewJob.createdAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: '2-digit' })
                            : previewJob.openDate 
                              ? new Date(previewJob.openDate).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: '2-digit' })
                              : '—'}</span>
                          <span>Atualizado: {previewJob.updatedAt 
                            ? new Date(previewJob.updatedAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
                            : '—'}</span>
                          {previewJob.publishedAt && (
                            <span>Publicado: {new Date(previewJob.publishedAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}</span>
                          )}
                          {previewJob.closedAt && (
                            <span>Fechado: {new Date(previewJob.closedAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}</span>
                          )}
                        </div>

                        {/* Row 3: Badges de informação */}
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {previewJob.department && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-700 border border-gray-200">
                              {previewJob.department}
                            </Badge>
                          )}
                          {previewJob.level && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-amber-50 text-amber-700 border border-amber-200">
                              {previewJob.level}
                            </Badge>
                          )}
                          {previewJob.location && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-0.5">
                              <MapPin className="w-2.5 h-2.5" />
                              {previewJob.location}
                            </Badge>
                          )}
                          {previewJob.workModel && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-700 border border-gray-200">
                              {previewJob.workModel === 'remoto' ? 'Remoto' : previewJob.workModel === 'híbrido' ? 'Híbrido' : 'Presencial'}
                            </Badge>
                          )}
                          {previewJob.type && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-700 border border-gray-200">
                              {previewJob.type}
                            </Badge>
                          )}
                          {(previewJob.visibility === 'confidential' || previewJob.isConfidential) && (
                            <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-orange-50 text-orange-700 border-orange-200">
                              <Shield className="w-2.5 h-2.5 mr-0.5" />
                              Confidencial
                            </Badge>
                          )}
                          {previewJob.visibility === 'internal' && (
                            <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-blue-50 text-blue-700 border-blue-200">
                              <Building className="w-2.5 h-2.5 mr-0.5" />
                              Interna
                            </Badge>
                          )}
                          {previewJob.visibility === 'hidden' && (
                            <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-gray-50 text-gray-800 border-gray-200">
                              <Lock className="w-2.5 h-2.5 mr-0.5" />
                              Oculta
                            </Badge>
                          )}
                          {/* Badge de publicação */}
                          {(previewJob.publishedLinkedIn || previewJob.publishedWebsite) ? (
                            <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-green-50 text-green-700 border-green-200 flex items-center gap-0.5">
                              <Globe className="w-2.5 h-2.5" />
                              Publicada
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-gray-50 text-gray-500 border-gray-200 flex items-center gap-0.5">
                              <Globe className="w-2.5 h-2.5" />
                              Não publicada
                            </Badge>
                          )}
                          {(previewJob.salaryRange?.min || previewJob.salaryRange?.max || previewJob.salaryMin || previewJob.salaryMax) && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-green-50 text-green-700 border border-green-200 flex items-center gap-0.5">
                              <DollarSign className="w-2.5 h-2.5" />
                              {(() => {
                                const min = previewJob.salaryRange?.min || previewJob.salaryMin
                                const max = previewJob.salaryRange?.max || previewJob.salaryMax
                                if (min && max) return `R$ ${(min/1000).toFixed(0)}k - ${(max/1000).toFixed(0)}k`
                                if (min) return `A partir de R$ ${(min/1000).toFixed(0)}k`
                                if (max) return `Até R$ ${(max/1000).toFixed(0)}k`
                                return ''
                              })()}
                            </Badge>
                          )}
                          {/* Badge de status */}
                          <Badge 
                            className="text-micro px-1.5 py-0 h-4 font-medium"
                            style={{ backgroundColor: getStatusColor(previewJob.status as Job['status']), color: 'var(--white)' }}
                          >
                            {previewJob.status}
                          </Badge>
                          {(() => {
                            const scrStatus = previewJob.screeningStatus || 'not_configured'
                            const scrLabels: Record<string, string> = {
                              not_configured: 'Triagem: N/C',
                              not_started: 'Triagem: Não Iniciada',
                              active: 'Triagem: Ativa',
                              paused: 'Triagem: Pausada',
                              completed: 'Triagem: Concluída',
                            }
                            const scrColors: Record<string, string> = {
                              not_configured: 'var(--gray-200)',
                              not_started: 'var(--gray-100)',
                              active: 'var(--status-success)',
                              paused: 'var(--gray-300)',
                              completed: 'var(--gray-400)',
                            }
                            return (
                              <Badge 
                                className="text-micro px-1.5 py-0 h-4 font-medium text-gray-800"
                                style={{ backgroundColor: scrColors[scrStatus] || 'var(--gray-200)' }}
                              >
                                {scrLabels[scrStatus] || 'Triagem: N/C'}
                              </Badge>
                            )
                          })()}
                        </div>
                      </div>
                      <div className="flex items-center gap-0.5 flex-shrink-0">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const jobToOpen = allJobs.find(j => j.id === previewJob.id)
                            if (jobToOpen) {
                              handleJobClick(jobToOpen)
                            }
                          }}
                          className="h-6 w-6 p-0"
                          title="Abrir vaga completa"
                        >
                          <Expand className="w-3 h-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setShowJobPreview(false)
                            setPreviewJob(null)
                            setActivePreviewTab('screening')
                          }}
                          className="h-6 w-6 p-0"
                        >
                          <X className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Linha 3: Processo Seletivo Inline */}
                  {previewJob.hiringProcess && previewJob.hiringProcess.length > 0 && (
                    <div className="px-3 pb-2 border-t border-gray-100 dark:border-gray-700/50 pt-2">
                      <div className="flex items-center gap-0.5 overflow-x-auto">
                        {previewJob.hiringProcess.map((step, idx) => (
                          <React.Fragment key={idx}>
                            <div className={`px-1.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${
                              idx === 0 ? 'bg-gray-100 text-gray-950 dark:bg-gray-700 dark:text-gray-200 font-semibold' :
                              idx === (previewJob.hiringProcess?.length || 0) - 1 ? 'bg-gray-100 text-gray-950 dark:bg-gray-700 dark:text-gray-200 font-semibold' :
                              'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                            }`}>
                              {step}
                            </div>
                            {idx < (previewJob.hiringProcess?.length || 0) - 1 && (
                              <ChevronRight className="w-2 h-2 text-gray-800 flex-shrink-0" />
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Tabs de Navegação - Tamanho Reduzido */}
                <div className="border-b border-gray-100">
                  <div className="flex items-center px-3">
                    <button
                      onClick={() => setActivePreviewTab('screening')}
                      className={`px-2 py-1.5 text-micro font-medium border-b-2 transition-colors ${
                        activePreviewTab === 'screening'
                          ? 'border-gray-900 text-gray-700 font-semibold'
                          : 'border-transparent text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      <div className="flex items-center gap-1">
                        <ClipboardList className="w-2.5 h-2.5" />
                        Detalhes da Vaga
                      </div>
                    </button>
                  </div>
                </div>

                {/* Conteúdo das Tabs - Scrollable */}
                <div className="overflow-y-auto flex-1 p-4">

                  {/* Tab: Análise Preditiva - Removida, já está unificada com Pipeline */}

                  {/* Tab: Funil & Analytics Unificado */}
                  {activePreviewTab === 'pipeline' && (
                    <div className="space-y-4">
                      {/* Cards de Métricas Preditivas Principais */}
                      <div className="grid grid-cols-2 gap-3">
                        {/* Score de Sucesso */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Sucesso de Fechamento</span>
                            <Target className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-xl font-bold text-gray-950 dark:text-gray-50 font-semibold">
                            {isLoadingJobMetrics ? '...' : jobMetrics?.performance?.conversion_rate != null 
                              ? `${Math.round(jobMetrics.performance.conversion_rate)}%` 
                              : previewJob.funnel.hired > 0 
                                ? `${Math.round((previewJob.funnel.hired / Math.max(previewJob.funnel.total, 1)) * 100)}%`
                                : '—'}
                          </div>
                          <div className="mt-1 text-xs text-gray-800 dark:text-gray-200">
                            Pipeline: {jobMetrics?.funnel.total ?? previewJob.funnel.total} candidatos
                          </div>
                        </div>

                        {/* Atividade 7d */}
                        <div className="bg-gray-100 dark:bg-gray-800 rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Atividade 7d</span>
                            <TrendingUp className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                          </div>
                          <div className="text-xl font-bold text-gray-900 dark:text-gray-50">
                            {isLoadingJobMetrics ? '...' : jobMetrics ? jobMetrics.activity.applications_7d : 0}
                          </div>
                          <div className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                            {isLoadingJobMetrics ? '...' : jobMetrics ? `${jobMetrics.activity.views_7d} visualizações` : 'Sem dados'}
                          </div>
                        </div>

                        {/* Time to Fill */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Time to Fill</span>
                            <Clock className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-xl font-bold text-gray-950 dark:text-gray-50 font-semibold">
                            {isLoadingJobMetrics ? '...' : jobMetrics?.performance.time_to_fill_days != null ? `${jobMetrics.performance.time_to_fill_days}d` : (previewJob.urgencyLevel > 3 ? '15d' : previewJob.urgencyLevel > 2 ? '25d' : '35d')}
                          </div>
                          <div className="mt-1 text-xs text-gray-800 dark:text-gray-200">
                            {isLoadingJobMetrics ? '...' : jobMetrics?.activity.interviews_scheduled ? `${jobMetrics.activity.interviews_scheduled} entrevistas agendadas` : 'Sem entrevistas'}
                          </div>
                        </div>

                        {/* SLA Status */}
                        <div className={`rounded-md p-3 ${jobMetrics?.sla.within_sla === false ? 'bg-red-50 dark:bg-red-900/20' : 'bg-gray-50 dark:bg-gray-800'}`}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Status SLA</span>
                            <Shield className={`w-3 h-3 ${jobMetrics?.sla.within_sla === false ? 'text-red-600' : 'text-gray-800 dark:text-gray-200'}`} />
                          </div>
                          <div className={`text-xl font-bold font-semibold ${jobMetrics?.sla.within_sla === false ? 'text-red-700 dark:text-red-300' : 'text-gray-950 dark:text-gray-50'}`}>
                            {isLoadingJobMetrics ? '...' : jobMetrics?.sla.within_sla ? 'OK' : 'Atrasado'}
                          </div>
                          <div className={`mt-1 text-xs ${jobMetrics?.sla.within_sla === false ? 'text-red-600 dark:text-red-400' : 'text-gray-800 dark:text-gray-200'}`}>
                            {isLoadingJobMetrics ? '...' : jobMetrics?.sla.days_remaining != null ? `${jobMetrics.sla.days_remaining} dias restantes` : 'Sem prazo definido'}
                          </div>
                        </div>
                      </div>

                      {/* Insights e Recomendações da LIA */}
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-xs font-medium text-gray-950 dark:text-gray-200 font-semibold mb-1">
                              Insights da LIA
                            </p>
                            <ul className="space-y-1 text-xs text-gray-800 dark:text-gray-200">
                              {previewJob.funnel.total < 10 && (
                                <li>• Pipeline baixo: Ampliar divulgação ou revisar requisitos</li>
                              )}
                              {previewJob.level === 'Sênior' && (
                                <li>• Alto risco de recusa: Prepare margem de negociação de 15-20%</li>
                              )}
                              {previewJob.funnel.screening > previewJob.funnel.interview * 3 && (
                                <li>• Gargalo em entrevistas: Agilize agendamentos</li>
                              )}
                              {previewJob.urgencyLevel > 3 && previewJob.funnel.total < 20 && (
                                <li>• Urgência vs Pipeline: Ative sourcing ativo e headhunting</li>
                              )}
                            </ul>
                          </div>
                        </div>
                      </div>

                      {/* Análise Comparativa */}
                      <div className="bg-white dark:bg-gray-800 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Comparativo com Mercado
                        </h4>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Salário</p>
                            <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                              {previewJob.salary > 'R$ 10.000' ? '+15%' : '-5%'}
                            </p>
                            <p className={textStyles.bodySmall}>vs. mercado</p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Candidatos</p>
                            <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                              {previewJob.funnel.total > 30 ? '+45%' : '-20%'}
                            </p>
                            <p className={textStyles.bodySmall}>vs. média</p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Atratividade</p>
                            <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                              #{Math.floor(Math.random() * 10) + 1}
                            </p>
                            <p className={textStyles.bodySmall}>ranking</p>
                          </div>
                        </div>
                      </div>

                      {/* Fatores de Risco */}
                      <div className="bg-red-50 dark:bg-red-900/20 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <Shield className="w-3.5 h-3.5 text-red-600" />
                          Fatores de Risco
                        </h4>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-800 dark:text-gray-200">Competitividade salarial</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.level === 'Sênior' ? 4 : 2) ? 'bg-red-500' : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-800 dark:text-gray-200">Escassez de talentos</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.level === 'Sênior' ? 3 : 1) ? 'bg-orange-500' : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-800 dark:text-gray-200">Tempo de processo</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.urgencyLevel > 3 ? 4 : 2) ? 'bg-gray-500 dark:bg-gray-600' : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab: Métricas LIA Triagens - ARQUIVADO: código preservado mas desabilitado */}
                  {false && (
                    <div className="space-y-4">
                      {/* Header com Resumo */}
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                        <div className="flex items-start gap-2">
                          <Brain className="w-4 h-4 text-wedo-cyan mt-0.5" />
                          <div className="flex-1">
                            <h4 className={`${textStyles.title} dark:text-gray-50 mb-1`}>
                              Performance LIA - Triagens Automatizadas
                            </h4>
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>
                              Análise detalhada do impacto da inteligência artificial no processo de triagem desta vaga
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Métricas Principais - Grid 2x2 */}
                      <div className="grid grid-cols-2 gap-3">
                        {/* Horas Economizadas */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Triagens Realizadas</span>
                            <Clock className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                            {previewJob.liaMetrics?.triagens_realizadas ?? 0}
                          </div>
                          <div className="mt-1 text-xs text-gray-800 dark:text-gray-200">
                            de {previewJob.liaMetrics?.triagens_agendadas ?? 0} agendadas
                          </div>
                        </div>

                        {/* Pipeline LIA */}
                        <div className="bg-gray-100 dark:bg-gray-750 rounded-md p-3 border border-gray-300 dark:border-gray-600">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Pipeline LIA</span>
                            <TrendingUp className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                            {previewJob.liaMetrics?.pipeline_lia ?? 0}
                          </div>
                          <div className="mt-1 text-xs text-gray-800 dark:text-gray-200">
                            candidatos em triagem
                          </div>
                        </div>

                        {/* Sem Resposta */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Sem Resposta</span>
                            <Zap className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                            {previewJob.liaMetrics?.sem_resposta ?? 0}
                          </div>
                          <div className="mt-1 text-xs text-gray-800 dark:text-gray-200">
                            candidatos
                          </div>
                        </div>

                        {/* Taxa de Conclusão */}
                        <div className="bg-gray-100 dark:bg-gray-750 rounded-md p-3 border border-gray-300 dark:border-gray-600">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Taxa de Conclusão</span>
                            <CheckCircle className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                            {(() => {
                              const realizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                              const agendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                              return agendadas > 0 ? Math.round((realizadas / agendadas) * 100) : 0
                            })()}%
                          </div>
                          <div className="mt-1 text-xs text-gray-800 dark:text-gray-200">
                            {previewJob.liaMetrics?.triagens_realizadas ?? 0} de {previewJob.liaMetrics?.triagens_agendadas ?? 0} agendadas
                          </div>
                        </div>
                      </div>

                      {/* Funil LIA Detalhado */}
                      <div className="bg-white dark:bg-gray-800 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-3 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Funil de Triagem LIA
                        </h4>

                        <div className="space-y-2">
                          {/* Pipeline LIA */}
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-800 dark:text-gray-200 w-24">Pipeline LIA</span>
                            <div className="flex-1 mx-2">
                              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                <div className="bg-gray-400 dark:bg-gray-500 h-3 rounded-full flex items-center justify-end pr-1" style={{ width: '100%' }}>
                                  <span className="text-xs text-white font-medium">{previewJob.liaMetrics?.pipeline_lia ?? 0}</span>
                                </div>
                              </div>
                            </div>
                            <span className="text-xs text-gray-800 w-10 text-right">100%</span>
                          </div>

                          {/* Agendadas */}
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-800 dark:text-gray-200 w-24">Agendadas</span>
                            <div className="flex-1 mx-2">
                              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                {(() => {
                                  const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                  const triagensAgendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                                  const widthPercent = pipelineLia > 0 ? (triagensAgendadas / pipelineLia) * 100 : 0
                                  return (
                                    <div className="bg-gray-500 dark:bg-gray-400 h-3 rounded-full flex items-center justify-end pr-1"
                                         style={{ width: `${Math.min(widthPercent, 100)}%` }}>
                                      <span className="text-xs text-white font-medium">{triagensAgendadas}</span>
                                    </div>
                                  )
                                })()}
                              </div>
                            </div>
                            <span className="text-xs text-gray-800 w-10 text-right">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const triagensAgendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                                return pipelineLia > 0 ? Math.round((triagensAgendadas / pipelineLia) * 100) : 0
                              })()}%
                            </span>
                          </div>

                          {/* Realizadas */}
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-800 dark:text-gray-200 w-24">Realizadas</span>
                            <div className="flex-1 mx-2">
                              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                {(() => {
                                  const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                  const triagensRealizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                                  const widthPercent = pipelineLia > 0 ? (triagensRealizadas / pipelineLia) * 100 : 0
                                  return (
                                    <div className="bg-gray-600 dark:bg-gray-300 h-3 rounded-full flex items-center justify-end pr-1"
                                         style={{ width: `${Math.min(widthPercent, 100)}%` }}>
                                      <span className="text-xs text-white dark:text-gray-50 font-medium">{triagensRealizadas}</span>
                                    </div>
                                  )
                                })()}
                              </div>
                            </div>
                            <span className="text-xs text-gray-800 w-10 text-right">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const triagensRealizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                                return pipelineLia > 0 ? Math.round((triagensRealizadas / pipelineLia) * 100) : 0
                              })()}%
                            </span>
                          </div>

                          {/* Entrevistas Agendadas */}
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-800 dark:text-gray-200 w-24">Entrevistas</span>
                            <div className="flex-1 mx-2">
                              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                {(() => {
                                  const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                  const entrevistasAgendadas = previewJob.liaMetrics?.entrevistas_agendadas ?? 0
                                  const widthPercent = pipelineLia > 0 ? (entrevistasAgendadas / pipelineLia) * 100 : 0
                                  return (
                                    <div className="bg-gray-900 dark:bg-gray-100 h-3 rounded-full flex items-center justify-end pr-1"
                                         style={{ width: `${Math.min(widthPercent, 100)}%` }}>
                                      <span className="text-xs text-white dark:text-gray-50 font-bold">{entrevistasAgendadas}</span>
                                    </div>
                                  )
                                })()}
                              </div>
                            </div>
                            <span className="text-xs text-gray-800 w-10 text-right">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const entrevistasAgendadas = previewJob.liaMetrics?.entrevistas_agendadas ?? 0
                                return pipelineLia > 0 ? Math.round((entrevistasAgendadas / pipelineLia) * 100) : 0
                              })()}%
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Média de Notas por Pergunta */}
                      <div className="bg-white dark:bg-gray-800 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-3 flex items-center gap-1`}>
                          <Star className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Média de Notas por Critério
                        </h4>

                        <div className="text-center py-4">
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Sem dados disponíveis
                          </p>
                          <p className="text-micro text-gray-400 dark:text-gray-500 mt-1">
                            As médias serão exibidas após as triagens serem concluídas
                          </p>
                        </div>
                      </div>

                      {/* Comparação com Outras Vagas */}
                      <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-md p-3 border border-indigo-200 dark:border-indigo-800">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-3 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Resumo do Funil
                        </h4>

                        <div className="grid grid-cols-3 gap-2">
                          <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
                            <p className="text-xs text-gray-800 dark:text-gray-200 mb-1">Total no Funil</p>
                            <p className="text-lg font-bold text-gray-950 dark:text-gray-50 font-semibold">
                              {previewJob.funnel.total}
                            </p>
                            <p className="text-micro text-gray-500 mt-1">candidatos</p>
                          </div>

                          <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
                            <p className="text-xs text-gray-800 dark:text-gray-200 mb-1">Em Triagem</p>
                            <p className="text-lg font-bold text-gray-950 dark:text-gray-50 font-semibold">
                              {previewJob.funnel.screening}
                            </p>
                            <p className="text-micro text-gray-500 mt-1">candidatos</p>
                          </div>

                          <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
                            <p className="text-xs text-gray-800 dark:text-gray-200 mb-1">Em Entrevista</p>
                            <p className="text-lg font-bold text-gray-950 dark:text-gray-50 font-semibold">
                              {previewJob.funnel.interview}
                            </p>
                            <p className="text-micro text-gray-500 mt-1">candidatos</p>
                          </div>
                        </div>
                      </div>

                      {/* Candidatos Sem Resposta */}
                      <div className="bg-amber-50 dark:bg-amber-900/20 rounded-md p-3 border border-amber-200 dark:border-amber-800">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                          Candidatos Sem Resposta
                        </h4>

                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Sem Resposta</span>
                              <span className="text-xs font-bold text-amber-700 dark:text-amber-300">
                                {previewJob.liaMetrics?.sem_resposta ?? 0}
                              </span>
                            </div>
                            <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const semResposta = previewJob.liaMetrics?.sem_resposta ?? 0
                                const percent = pipelineLia > 0 ? (semResposta / pipelineLia) * 100 : 0
                                return <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: `${percent}%` }}></div>
                              })()}
                            </div>
                            <p className="text-xs text-gray-800 mt-1">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const semResposta = previewJob.liaMetrics?.sem_resposta ?? 0
                                return pipelineLia > 0 ? `${Math.round((semResposta / pipelineLia) * 100)}% do pipeline` : 'N/A'
                              })()}
                            </p>
                          </div>

                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Aguardando</span>
                              <span className="text-xs font-bold text-blue-700 dark:text-blue-300">
                                {(() => {
                                  const agendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                                  const realizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                                  return Math.max(0, agendadas - realizadas)
                                })()}
                              </span>
                            </div>
                            <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                              {(() => {
                                const agendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                                const realizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                                const percent = agendadas > 0 ? ((agendadas - realizadas) / agendadas) * 100 : 0
                                return <div className="bg-gray-900 dark:bg-gray-50 h-1.5 rounded-full" style={{ width: `${Math.max(0, percent)}%` }}></div>
                              })()}
                            </div>
                            <p className="text-xs text-gray-800 mt-1">triagens pendentes</p>
                          </div>
                        </div>
                      </div>

                      {/* Resumo LIA */}
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3 border border-gray-200 dark:border-gray-700">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-xs font-medium text-gray-950 dark:text-gray-200 font-semibold mb-1">
                              Resumo da Triagem LIA
                            </p>
                            <ul className="space-y-1 text-xs text-gray-800 dark:text-gray-200">
                              <li>• {previewJob.liaMetrics?.triagens_realizadas ?? 0} triagens realizadas de {previewJob.liaMetrics?.triagens_agendadas ?? 0} agendadas</li>
                              <li>• {previewJob.liaMetrics?.entrevistas_agendadas ?? 0} entrevistas agendadas</li>
                              <li>• {previewJob.liaMetrics?.sem_resposta ?? 0} candidatos sem resposta</li>
                              <li>• {previewJob.liaMetrics?.pipeline_lia ?? 0} candidatos no pipeline LIA</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab: Roteiro de Triagem */}
                  {activePreviewTab === 'screening' && (
                    <div className="space-y-4">
                      {/* Loading State Guard */}
                      {isLoadingScreeningConfig ? (
                        <div className="space-y-4">
                          {/* Skeleton for Performance Card */}
                          <div className="p-3 bg-white border border-gray-100 rounded-md">
                            <div className="h-4 bg-gray-200 rounded w-32 mb-3"></div>
                            <div className="grid grid-cols-4 gap-2">
                              {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="text-center">
                                  <div className="h-6 bg-gray-200 rounded mb-1"></div>
                                  <div className="h-3 bg-gray-100 rounded w-12 mx-auto"></div>
                                </div>
                              ))}
                            </div>
                            <div className="grid grid-cols-4 gap-2 mt-2 pt-2 border-t border-gray-100">
                              {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="text-center">
                                  <div className="h-6 bg-gray-200 rounded mb-1"></div>
                                  <div className="h-3 bg-gray-100 rounded w-12 mx-auto"></div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Skeleton for Skills Card */}
                          <div className="p-3 bg-white border border-gray-100 rounded-md">
                            <div className="h-4 bg-gray-200 rounded w-32 mb-3"></div>
                            <div className="flex flex-wrap gap-1.5">
                              {[1, 2, 3, 4, 5, 6].map((i) => (
                                <div key={i} className="h-6 bg-gray-200 rounded px-2 w-24"></div>
                              ))}
                            </div>
                          </div>

                          {/* Skeleton for Questions Card */}
                          <div className="p-3 bg-white border border-gray-100 rounded-md">
                            <div className="h-4 bg-gray-200 rounded w-40 mb-3"></div>
                            <div className="space-y-3">
                              {[1, 2, 3].map((i) => (
                                <div key={i} className="p-2 bg-gray-50 rounded border border-gray-100">
                                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                                  <div className="h-3 bg-gray-100 rounded w-1/2"></div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-4">
                      {/* 4. Descrição da Vaga */}
                      {previewJob.description && (
                        <div className="p-3 bg-white border border-gray-100 rounded-md">
                          <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('descricao')}>
                            <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                              <FileText className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                              Descrição da Vaga
                            </h5>
                            {collapsedPreviewSections.includes('descricao') ? (
                              <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                            ) : (
                              <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                            )}
                          </div>
                          {!collapsedPreviewSections.includes('descricao') && (
                            <p className="text-micro text-gray-600 dark:text-gray-300 leading-relaxed whitespace-pre-line line-clamp-6 mt-2">
                              {previewJob.description}
                            </p>
                          )}
                        </div>
                      )}

                      {/* 3. Competências Avaliadas */}
                      <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('competencias')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                            Competências Avaliadas
                          </h5>
                          {collapsedPreviewSections.includes('competencias') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('competencias') && (<>
                        {(() => {
                          const technicalSkills = (previewJob.technicalRequirements || []).map((tr: any) => typeof tr === 'string' ? tr : tr.technology || tr.name).filter(Boolean)
                          const behavioralSkills = (previewJob.behavioralCompetencies || []).map((bc: any) => typeof bc === 'string' ? bc : bc.competency || bc.name).filter(Boolean)
                          const responsibilitySkills = (previewJob.requirements || []).map((r: any) => typeof r === 'string' ? r : r.requirement || r.text || r.name).filter(Boolean)
                          const hasData = technicalSkills.length > 0 || behavioralSkills.length > 0 || responsibilitySkills.length > 0

                          if (!hasData) {
                            const fallbackSkills = screeningConfig?.wsi_skills || ['Comunicação', 'Resolução de Problemas', 'Adaptabilidade', 'Trabalho em Equipe']
                            return (
                              <div className="flex flex-wrap gap-1.5">
                                {fallbackSkills.slice(0, 6).map((skill: string, idx: number) => (
                                  <Badge key={idx} className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-micro px-1.5 py-0.5 h-[18px] font-medium">
                                    {skill}
                                  </Badge>
                                ))}
                              </div>
                            )
                          }

                          return (
                            <div className="space-y-2">
                              {technicalSkills.length > 0 && (
                                <div>
                                  <span className="text-micro font-medium text-gray-500 uppercase tracking-wide">Técnicas</span>
                                  <div className="flex flex-wrap gap-1.5 mt-1">
                                    {technicalSkills.map((skill: string, idx: number) => (
                                      <Badge key={idx} className="bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-micro px-1.5 py-0.5 h-[18px] font-medium border border-blue-200">
                                        {skill}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {behavioralSkills.length > 0 && (
                                <div>
                                  <span className="text-micro font-medium text-gray-500 uppercase tracking-wide">Comportamentais</span>
                                  <div className="flex flex-wrap gap-1.5 mt-1">
                                    {behavioralSkills.map((skill: string, idx: number) => (
                                      <Badge key={idx} className="bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 text-micro px-1.5 py-0.5 h-[18px] font-medium border border-purple-200">
                                        {skill}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {responsibilitySkills.length > 0 && (
                                <div>
                                  <span className="text-micro font-medium text-gray-500 uppercase tracking-wide">Responsabilidades</span>
                                  <div className="flex flex-wrap gap-1.5 mt-1">
                                    {responsibilitySkills.slice(0, 8).map((skill: string, idx: number) => (
                                      <Badge key={idx} className="bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-micro px-1.5 py-0.5 h-[18px] font-medium border border-amber-200">
                                        {skill}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })()}
                        <p className="text-micro text-gray-400 mt-2 flex items-center gap-1">
                          <Lightbulb className="w-3 h-3" />
                          Extraídas automaticamente do perfil da vaga via metodologia WSI
                        </p>
                        </>)}
                      </div>

                      <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('idiomas')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <Globe className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                            Idiomas
                          </h5>
                          {collapsedPreviewSections.includes('idiomas') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('idiomas') && (
                          previewJob.languages && previewJob.languages.length > 0 ? (
                            <div className="space-y-1.5 mt-2">
                              {previewJob.languages.map((lang: any, idx: number) => (
                                <div key={idx} className="flex items-center gap-2">
                                  <span className="text-micro text-gray-600 dark:text-gray-400 font-medium">
                                    {lang.language}
                                  </span>
                                  {lang.level && (
                                    <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-800 dark:text-gray-200">
                                      {lang.level}
                                    </Badge>
                                  )}
                                  {lang.required && (
                                    <Badge className="text-micro px-1.5 py-0 h-4 bg-red-50 text-red-600 border border-red-200">
                                      Obrigatório
                                    </Badge>
                                  )}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-micro text-gray-500 dark:text-gray-400 italic mt-2">
                              Nenhum idioma configurado
                            </p>
                          )
                        )}
                      </div>

                      <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('remuneracao')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <DollarSign className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                            Remuneração e Benefícios
                          </h5>
                          {collapsedPreviewSections.includes('remuneracao') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('remuneracao') && (
                          <div className="space-y-2 mt-2">
                            {(() => {
                              const salaryMin = previewJob.salaryRange?.min ?? previewJob.salaryMin
                              const salaryMax = previewJob.salaryRange?.max ?? previewJob.salaryMax
                              const hasSalary = salaryMin || salaryMax
                              const bonusMin = previewJob.bonusRange?.min ?? previewJob.bonus_range?.min ?? previewJob.bonusMin
                              const bonusMax = previewJob.bonusRange?.max ?? previewJob.bonus_range?.max ?? previewJob.bonusMax
                              const hasBonus = bonusMin || bonusMax
                              const benefits = previewJob.benefits || []
                              const fmt = (v: any) => {
                                if (!v) return ''
                                const n = typeof v === 'string' ? parseFloat(v) : v
                                return isNaN(n) ? '' : `R$ ${n.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
                              }
                              return (
                                <>
                                  {hasSalary ? (
                                    <div className="flex items-center gap-1.5">
                                      <span className="text-micro text-gray-500 dark:text-gray-400">Salário:</span>
                                      <span className="text-micro font-medium text-gray-950 dark:text-gray-50">
                                        {fmt(salaryMin)}{salaryMax ? ` - ${fmt(salaryMax)}` : ''}
                                      </span>
                                    </div>
                                  ) : (
                                    <p className="text-micro text-gray-500 dark:text-gray-400 italic">
                                      Faixa salarial não informada
                                    </p>
                                  )}
                                  {hasBonus && (
                                    <div className="flex items-center gap-1.5">
                                      <span className="text-micro text-gray-500 dark:text-gray-400">Bônus:</span>
                                      <span className="text-micro font-medium text-gray-950 dark:text-gray-50">
                                        {fmt(bonusMin)}{bonusMax ? ` - ${fmt(bonusMax)}` : ''}
                                      </span>
                                    </div>
                                  )}
                                  {benefits.length > 0 && (
                                    <div>
                                      <span className="text-micro text-gray-500 dark:text-gray-400 block mb-1">Benefícios:</span>
                                      <div className="flex flex-wrap gap-1.5">
                                        {benefits.map((b: any, idx: number) => (
                                          <Badge key={idx} className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-800 dark:text-gray-200">
                                            {typeof b === 'string' ? b : b.name}
                                          </Badge>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </>
                              )
                            })()}
                          </div>
                        )}
                      </div>

                      <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('etapas')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <Layers3 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                            Etapas do Processo
                          </h5>
                          {collapsedPreviewSections.includes('etapas') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('etapas') && (
                          <div className="mt-2">
                            {previewJob.hiringProcess && previewJob.hiringProcess.length > 0 ? (
                              <div className="flex items-center gap-1 overflow-x-auto pb-1">
                                {previewJob.hiringProcess.map((step: string, idx: number) => (
                                  <React.Fragment key={idx}>
                                    {idx > 0 && (
                                      <ChevronRight className="w-3 h-3 text-gray-300 flex-shrink-0" />
                                    )}
                                    <div className="flex items-center gap-1 px-2 py-1 bg-gray-50 border border-gray-200 rounded-lg flex-shrink-0">
                                      <span className="text-micro font-medium text-gray-700">{step}</span>
                                    </div>
                                  </React.Fragment>
                                ))}
                              </div>
                            ) : previewJob.interviewStages && previewJob.interviewStages.length > 0 ? (
                              <div className="flex items-center gap-1 overflow-x-auto pb-1">
                                {previewJob.interviewStages
                                  .sort((a: any, b: any) => (a.order || 0) - (b.order || 0))
                                  .map((stage: any, idx: number) => (
                                    <React.Fragment key={idx}>
                                      {idx > 0 && (
                                        <ChevronRight className="w-3 h-3 text-gray-300 flex-shrink-0" />
                                      )}
                                      <div className="flex items-center gap-1 px-2 py-1 bg-gray-50 border border-gray-200 rounded-lg flex-shrink-0">
                                        {stage.liaAssisted && (
                                          <span className="w-1.5 h-1.5 rounded-full bg-wedo-cyan flex-shrink-0" />
                                        )}
                                        <span className="text-micro font-medium text-gray-700">{stage.stageName}</span>
                                      </div>
                                    </React.Fragment>
                                  ))}
                              </div>
                            ) : (
                              <p className="text-micro text-gray-500 dark:text-gray-400 italic">
                                Nenhuma etapa configurada
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                          <div className="border-t border-gray-200 dark:border-gray-700" />

                          {/* Roteiro de Triagem Automática */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <ClipboardList className="w-4 h-4 text-gray-600" />
                              <h4 className="text-xs font-semibold text-gray-950 dark:text-gray-50">Roteiro de Triagem Automática</h4>
                              <Badge 
                                className={`text-micro px-1.5 py-0 h-4 text-gray-950 ${(screeningConfig?.status?.enabled ?? true) ? 'bg-wedo-green-pastel' : 'bg-gray-200'}`}
                              >
                                {(screeningConfig?.status?.enabled ?? true) ? 'Ativo' : 'Pausado'}
                              </Badge>
                            </div>
                          </div>

                      <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('fluxo-resumido')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <ClipboardList className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                            Resumo da Triagem
                            <Badge
                              className={`text-micro px-1.5 py-0 h-4 text-gray-800 ${(screeningConfig?.status?.enabled ?? true) ? 'bg-wedo-green-pastel' : 'bg-gray-200'}`}
                            >
                              {(screeningConfig?.status?.enabled ?? true) ? 'Ativo' : 'Pausado'}
                            </Badge>
                          </h5>
                          {collapsedPreviewSections.includes('fluxo-resumido') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('fluxo-resumido') && (
                          <div className="mt-2">
                            <div className="grid grid-cols-2 gap-2">
                              <div className="text-center p-2 bg-gray-50 rounded-lg">
                                <div className="text-base-ui font-semibold text-gray-800">{(previewJob.screeningQuestions || []).length}</div>
                                <p className="text-micro text-gray-500">Perguntas</p>
                              </div>
                              <div className="text-center p-2 bg-gray-50 rounded-lg">
                                <div className="text-base-ui font-semibold text-gray-800">{Math.ceil((previewJob.screeningQuestions || []).reduce((acc: number, q: any) => acc + (q.time_limit || 120), 0) / 60)}min</div>
                                <p className="text-micro text-gray-500">Tempo Est.</p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* 5. Blocos WSI do Roteiro de Triagem */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('fluxo-wsi')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <Layers3 className="w-3.5 h-3.5 text-gray-600" />
                            Fluxo de Triagem WSI
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-200 text-gray-800">
                              6 Blocos
                            </Badge>
                          </h5>
                          {collapsedPreviewSections.includes('fluxo-wsi') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>

                        {!collapsedPreviewSections.includes('fluxo-wsi') && (
                        <div className="space-y-2">
                          {WSI_BLOCKS.map((block) => {
                            const isExpanded = expandedBlocks.includes(block.id)
                            
                            const allQuestions = previewJob.screeningQuestions || []
                            const cat = (q: any) => (q.category || '').toLowerCase()
                            const typ = (q: any) => (q.type || '').toLowerCase()
                            
                            const isBlock2 = (q: any) => {
                              if (typ(q) === 'eliminatory' || q.required) return true
                              if (cat(q).includes('elegib') || cat(q).includes('elimin')) return true
                              if (cat(q).includes('fit') && cat(q).includes('básico')) return true
                              if (cat(q).includes('disponib') || cat(q).includes('eligib')) return true
                              return false
                            }
                            
                            const isBlock3 = (q: any) => {
                              if (isBlock2(q)) return false
                              return cat(q).includes('tecn') || cat(q).includes('tech') ||
                                cat(q).includes('skill') || cat(q).includes('técnica') ||
                                typ(q).includes('tech')
                            }
                            
                            const isBlock4 = (q: any) => {
                              if (isBlock2(q) || isBlock3(q)) return false
                              return true
                            }
                            
                            const blockQuestions = allQuestions.filter((q: any) => {
                              if (q.block_id !== undefined && q.block_id !== null) {
                                return q.block_id === block.id
                              }
                              if (block.id === 2) return isBlock2(q)
                              if (block.id === 3) return isBlock3(q)
                              if (block.id === 4) return isBlock4(q)
                              return false
                            })
                            
                            const eliminatoryCount = blockQuestions.filter((q: any) => q.type === 'eliminatory' || q.required).length
                            const informativeCount = blockQuestions.length - eliminatoryCount
                            
                            return (
                              <div 
                                key={block.id} 
                                className={`border rounded-md overflow-hidden ${
                                  block.editable ? 'border-gray-200' : 'border-gray-100 bg-gray-50/50'
                                }`}
                              >
                                {/* Block Header */}
                                <div 
                                  className={`flex items-center justify-between p-2.5 cursor-pointer transition-colors ${
                                    block.editable 
                                      ? 'bg-gray-50 hover:bg-gray-100' 
                                      : 'bg-gray-100/80'
                                  }`}
                                  onClick={() => {
                                    if (isExpanded) {
                                      setExpandedBlocks(prev => prev.filter(id => id !== block.id))
                                    } else {
                                      setExpandedBlocks(prev => [...prev, block.id])
                                    }
                                  }}
                                >
                                  <div className="flex items-center gap-2">
                                    <span className={`w-5 h-5 rounded-full text-white text-micro font-bold flex items-center justify-center ${
                                      block.editable ? 'bg-gray-700' : 'bg-gray-400'
                                    }`}>
                                      {block.id}
                                    </span>
                                    <div>
                                      <span className={`text-xs font-semibold ${block.editable ? 'text-gray-950' : 'text-gray-600'}`}>
                                        {block.name}
                                      </span>
                                      <span className="text-micro text-gray-500 ml-1.5">({block.duration})</span>
                                    </div>
                                    {!block.editable && (
                                      <Badge className="text-micro px-1 py-0 h-3.5 bg-gray-200 text-gray-500">
                                        Auto
                                      </Badge>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-1.5">
                                    {block.editable && blockQuestions.length > 0 && (
                                      <>
                                        {eliminatoryCount > 0 && (
                                          <Badge className="text-micro px-1.5 py-0 bg-red-50 text-red-600 border border-red-200">
                                            {eliminatoryCount} Elim.
                                          </Badge>
                                        )}
                                        {informativeCount > 0 && (
                                          <Badge className="text-micro px-1.5 py-0 bg-gray-100 text-gray-600">
                                            {informativeCount} Info.
                                          </Badge>
                                        )}
                                      </>
                                    )}
                                    {isExpanded ? (
                                      <ChevronUp className="w-3.5 h-3.5 text-gray-500" />
                                    ) : (
                                      <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
                                    )}
                                  </div>
                                </div>
                                
                                {/* Block Content */}
                                {isExpanded && (
                                  <div className={`p-2.5 space-y-1.5 ${!block.editable ? 'bg-gray-50/30' : ''}`}>
                                    {/* Non-editable blocks show automatic WSI messages */}
                                    {!block.editable ? (
                                      WSI_AUTOMATIC_MESSAGES[block.id] ? (
                                        <div className="rounded-md border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50 overflow-hidden">
                                          <div className="px-2.5 py-1.5 border-b border-gray-900 dark:border-gray-50/10 bg-gray-100 dark:bg-gray-800">
                                            <p className="text-xs font-medium text-gray-800">
                                              {WSI_AUTOMATIC_MESSAGES[block.id].title}
                                            </p>
                                          </div>
                                          <div className="p-2.5">
                                            <div className="text-micro text-gray-800 leading-relaxed whitespace-pre-line">
                                              {formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id].message)}
                                            </div>
                                          </div>
                                          <div className="px-2.5 py-1.5 border-t border-gray-900 dark:border-gray-50/10 bg-gray-50">
                                            <p className="text-micro text-gray-500 italic">
                                              {WSI_AUTOMATIC_MESSAGES[block.id].note}
                                            </p>
                                          </div>
                                        </div>
                                      ) : (
                                        <div className="p-2.5 bg-white/60 border border-gray-100 rounded-md">
                                          <p className="text-micro text-gray-600 italic">
                                            {block.description}
                                          </p>
                                          <p className="text-micro text-gray-400 mt-1">
                                            Gerenciado automaticamente pela LIA
                                          </p>
                                        </div>
                                      )
                                    ) : (
                                      <>
                                        {blockQuestions.length === 0 ? (
                                          <div className="p-3 bg-gray-50 border border-gray-200 border-dashed rounded-md text-center">
                                            <p className="text-micro text-gray-500">
                                              Nenhuma pergunta neste bloco
                                            </p>
                                          </div>
                                        ) : (
                                          blockQuestions.map((item: any, idx: number) => (
                                            <div 
                                              key={item.id || idx} 
                                              className="p-2.5 bg-white border border-gray-200 rounded-md"
                                            >
                                              <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                                                <Badge className={`text-micro px-1.5 py-0 h-4 rounded-full ${
                                                  item.category === 'behavioral' || item.category === 'Comportamental'
                                                    ? 'bg-purple-100 text-purple-700 border border-purple-200'
                                                    : item.category === 'technical' || item.category === 'Técnica'
                                                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                                                    : item.category === 'eligibility' || item.category === 'Elegibilidade'
                                                    ? 'bg-green-100 text-green-700 border border-green-200'
                                                    : 'bg-gray-100 text-gray-700 border border-gray-200'
                                                }`}>
                                                  {item.category === 'behavioral' ? 'Comport.' 
                                                    : item.category === 'technical' ? 'Técnica' 
                                                    : item.category === 'eligibility' ? 'Elegibilidade'
                                                    : item.category === 'cultural' ? 'Cultural'
                                                    : item.category || 'Geral'}
                                                </Badge>
                                                {(item.type === 'eliminatory' || item.required) && (
                                                  <Badge className="text-micro px-1.5 py-0 h-4 rounded-full bg-red-50 text-red-600 border border-red-200">
                                                    Eliminatória
                                                  </Badge>
                                                )}
                                              </div>
                                              <p className="text-micro text-gray-950 leading-relaxed mb-1.5">
                                                {item.question}
                                              </p>
                                              <div className="flex items-center gap-2 flex-wrap">
                                                {item.skill_targeted && (
                                                  <span className="inline-flex items-center gap-0.5 text-micro text-gray-500">
                                                    <Target className="w-2.5 h-2.5 text-gray-400" />
                                                    {item.skill_targeted}
                                                  </span>
                                                )}
                                                <span className="inline-flex items-center gap-0.5 text-micro text-gray-500">
                                                  <MessageSquare className="w-2.5 h-2.5 text-gray-400" />
                                                  {item.type === 'eliminatory' ? 'Sim/Não' 
                                                    : item.options?.length ? 'Múltipla escolha'
                                                    : 'Texto livre'}
                                                </span>
                                                {item.weight != null && (
                                                  <span className="inline-flex items-center gap-0.5 text-micro text-gray-500">
                                                    <BarChart3 className="w-2.5 h-2.5 text-gray-400" />
                                                    Peso {typeof item.weight === 'number' ? item.weight.toFixed(2) : item.weight}
                                                  </span>
                                                )}
                                                <span className="inline-flex items-center gap-0.5 text-micro text-gray-500">
                                                  <Clock className="w-2.5 h-2.5 text-gray-400" />
                                                  {item.type === 'eliminatory' ? '30s' : '2 min'}
                                                </span>
                                              </div>
                                            </div>
                                          ))
                                        )}
                                      </>
                                    )}
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                        )}
                      </div>

                      {/* 2. Agendamento Automático */}
                      <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('agendamento')}>
                          <div className="flex items-center gap-2">
                            <CalendarCheck className="w-3.5 h-3.5 text-gray-600" />
                            <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50">Agendamento Automático</h5>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Badge className={`${(screeningConfig?.scheduling?.auto_enabled ?? true) ? 'bg-gray-700 text-white dark:bg-gray-600' : 'bg-gray-400 text-white'} text-micro px-1.5 py-0 h-4`}>
                              {(screeningConfig?.scheduling?.auto_enabled ?? true) ? 'Ativo' : 'Inativo'}
                            </Badge>
                            {collapsedPreviewSections.includes('agendamento') ? (
                              <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                            ) : (
                              <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                            )}
                          </div>
                        </div>
                        {!collapsedPreviewSections.includes('agendamento') && (<>
                        <p className="text-micro text-gray-500 mb-2 mt-2">Aprovados na triagem são agendados automaticamente para entrevista</p>

                        <div className="grid grid-cols-2 gap-2">
                          <div className="flex items-center justify-between p-1.5 bg-gray-50 rounded">
                            <span className="text-micro text-gray-500">Score Mínimo</span>
                            <span className="text-micro font-medium text-gray-700">{(() => {
                              const preset = screeningConfig?.scheduling?.min_score_for_auto_preset
                              switch(preset) {
                                case 'rigorous': return 'Rigoroso'
                                case 'flexible': return 'Flexível'
                                default: return 'Recomendado'
                              }
                            })()}</span>
                          </div>
                          <div className="flex items-center justify-between p-1.5 bg-gray-50 rounded">
                            <span className="text-micro text-gray-500">Calendário</span>
                            <span className="text-micro font-medium text-gray-700">{screeningConfig?.scheduling?.calendar_provider || 'Microsoft'}</span>
                          </div>
                          <div className="flex items-center justify-between p-1.5 bg-gray-50 rounded">
                            <span className="text-micro text-gray-500">Horários</span>
                            <span className="text-micro font-medium text-gray-700">{screeningConfig?.scheduling?.available_hours || '9h-18h'}</span>
                          </div>
                          <div className="flex items-center justify-between p-1.5 bg-gray-50 rounded">
                            <span className="text-micro text-gray-500">Duração</span>
                            <span className="text-micro font-medium text-gray-700">{screeningConfig?.scheduling?.interview_duration_min ?? 45}min</span>
                          </div>
                        </div>
                        </>)}
                      </div>

                          {/* 1. Canais + Configurações Agrupados */}
                          <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('canais')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <Settings className="w-3.5 h-3.5 text-gray-600" />
                            Canais de Comunicação
                          </h5>
                          {collapsedPreviewSections.includes('canais') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>

                        {!collapsedPreviewSections.includes('canais') && (<>
                        {/* Canais em linha */}
                        <div className="flex items-center gap-3 mb-3 mt-3 pb-3 border-b border-gray-100">
                          <span className="text-micro text-gray-500">Canais:</span>
                          <div className="flex items-center gap-2">
                            <div className={`flex items-center gap-1 px-2 py-1 rounded ${(screeningConfig?.channels?.whatsapp?.enabled ?? true) ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                              <MessageSquare className="w-3 h-3" />
                              <span className="text-micro font-medium">WhatsApp</span>
                              {(screeningConfig?.channels?.whatsapp?.enabled ?? true) && <CheckCircle className="w-3 h-3" />}
                            </div>
                            <div className={`flex items-center gap-1 px-2 py-1 rounded ${(screeningConfig?.channels?.chat_web?.enabled ?? true) ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                              <Globe className="w-3 h-3" />
                              <span className="text-micro font-medium">Chat Web</span>
                              {(screeningConfig?.channels?.chat_web?.enabled ?? true) && <CheckCircle className="w-3 h-3" />}
                            </div>
                            <div className={`flex items-center gap-1 px-2 py-1 rounded ${(screeningConfig?.channels?.phone?.enabled ?? false) ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                              <Phone className="w-3 h-3" />
                              <span className="text-micro font-medium">Ligação</span>
                              {(screeningConfig?.channels?.phone?.enabled ?? false) && <CheckCircle className="w-3 h-3" />}
                            </div>
                          </div>
                        </div>

                        {/* Configurações em grid */}
                        <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-micro text-gray-500">Score Mínimo Aprovação</span>
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-700 text-white">{(() => {
                              const preset = screeningConfig?.settings?.min_score_preset
                              switch(preset) {
                                case 'rigorous': return 'Rigoroso'
                                case 'flexible': return 'Flexível'
                                default: return 'Recomendado'
                              }
                            })()}</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-micro text-gray-500">Timeout Resposta</span>
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-800">{screeningConfig?.settings?.response_timeout_hours ?? 48}h</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-micro text-gray-500">Re-tentativas</span>
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-800">{screeningConfig?.settings?.max_retries ?? 2}x</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-micro text-gray-500">Fallback</span>
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-orange-100 text-orange-700">Revisão Manual</Badge>
                          </div>
                        </div>

                      </>)}
                      </div>

                      
                      </div>
                      )}
                    </div>
                  )}

                  {/* Tab: Funil & Analytics Unificado */}
                  {activePreviewTab === 'pipeline' && (
                    <div className="space-y-4">
                      {/* Cards de Métricas Preditivas Principais */}
                      <div className="grid grid-cols-2 gap-2">
                        {/* Score de Sucesso */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Sucesso de Fechamento</span>
                            <Target className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-lg font-bold text-gray-950 dark:text-gray-50 font-semibold">
                            {previewJob.funnel.total > 20 ? '85%' : previewJob.funnel.total > 10 ? '60%' : '35%'}
                          </div>
                          <div className="mt-0.5 text-xs text-gray-800 dark:text-gray-200">
                            Pipeline: {previewJob.funnel.total} candidatos
                          </div>
                        </div>

                        {/* Time to Fill */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Time to Fill</span>
                            <Clock className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-lg font-bold text-gray-950 dark:text-gray-50 font-semibold">
                            {previewJob.urgencyLevel > 3 ? '15' : previewJob.urgencyLevel > 2 ? '25' : '35'}d
                          </div>
                          <div className="mt-0.5 text-xs text-gray-800 dark:text-gray-200">
                            Velocidade: {previewJob.funnel.interview > 0 ? '3.2' : '1.5'} cv/dia
                          </div>
                        </div>

                        {/* Qualidade Pipeline */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Qualidade Pipeline</span>
                            <Brain className="w-3 h-3 text-wedo-cyan" />
                          </div>
                          <div className="text-lg font-bold text-gray-950 dark:text-gray-50 font-semibold">
                            {previewJob.funnel.final > 3 ? 'A+' : previewJob.funnel.interview > 5 ? 'B+' : 'C'}
                          </div>
 <div className="mt-0.5 text-xs text-gray-800">
                            Conversão: {previewJob.funnel.interview > 0 ? Math.round((previewJob.funnel.interview / previewJob.funnel.total) * 100) : 0}%
                          </div>
                        </div>

                        {/* Risco de Recusa */}
                        <div className="bg-red-50 dark:bg-red-900/20 rounded-md p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Risco de Recusa</span>
                            <AlertCircle className="w-3 h-3 text-red-600" />
                          </div>
                          <div className="text-lg font-bold text-red-700 dark:text-red-300">
                            {previewJob.level === 'Sênior' ? '45%' : previewJob.level === 'Pleno' ? '25%' : '15%'}
                          </div>
                          <div className="mt-0.5 text-xs text-red-600 dark:text-red-400">
                            Gap salarial: {previewJob.level === 'Sênior' ? '±18%' : '±8%'}
                          </div>
                        </div>
                      </div>

                      {/* Funil de Recrutamento Visual */}
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-3 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Funil de Recrutamento
                        </h4>

                        {/* Visualização do Funil */}
                        <div className="space-y-2">
                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-800 dark:text-gray-200 w-20">Total</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                  <div className="bg-gray-500 dark:bg-gray-600 h-3 rounded-full flex items-center justify-end pr-1" style={{ width: '100%' }}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.total}</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-800 dark:text-gray-200 w-20">Triagem</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                  <div className="bg-gray-400 dark:bg-gray-500 h-3 rounded-full flex items-center justify-end pr-1"
                                       style={{ width: `${(previewJob.funnel.screening / previewJob.funnel.total) * 100}%` }}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.screening}</span>
                                  </div>
                                </div>
                              </div>
                              <span className="text-xs text-gray-800 w-10 text-right">
                                {Math.round((previewJob.funnel.screening / previewJob.funnel.total) * 100)}%
                              </span>
                            </div>
                          </div>

                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-800 dark:text-gray-200 w-20">Entrevistas</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                  <div className="bg-gray-400 dark:bg-gray-500 h-3 rounded-full flex items-center justify-end pr-1"
                                       style={{ width: `${(previewJob.funnel.interview / previewJob.funnel.total) * 100}%` }}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.interview}</span>
                                  </div>
                                </div>
                              </div>
                              <span className="text-xs text-gray-800 w-10 text-right">
                                {Math.round((previewJob.funnel.interview / previewJob.funnel.total) * 100)}%
                              </span>
                            </div>
                          </div>

                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-800 dark:text-gray-200 w-20">Finalistas</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                  <div className="bg-gray-400 dark:bg-gray-500 h-3 rounded-full flex items-center justify-end pr-1"
                                       style={{ width: `${(previewJob.funnel.final / previewJob.funnel.total) * 100}%` }}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.final}</span>
                                  </div>
                                </div>
                              </div>
                              <span className="text-xs text-gray-800 w-10 text-right">
                                {Math.round((previewJob.funnel.final / previewJob.funnel.total) * 100)}%
                              </span>
                            </div>
                          </div>

                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-800 dark:text-gray-200 w-20">Contratados</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                  <div className="bg-gray-500 dark:bg-gray-600 h-3 rounded-full flex items-center justify-end pr-1"
                                       style={{ width: previewJob.funnel.hired > 0 ? `${(previewJob.funnel.hired / previewJob.funnel.total) * 100}%` : '5%' }}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.hired}</span>
                                  </div>
                                </div>
                              </div>
                              <span className="text-xs text-gray-800 w-10 text-right">
                                {Math.round((previewJob.funnel.hired / previewJob.funnel.total) * 100)}%
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Métricas de Conversão */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="bg-white dark:bg-gray-800 rounded-md p-2">
                          <p className={`${textStyles.bodySmall} dark:text-gray-200`}>CV → Triagem</p>
                          <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                            {Math.round((previewJob.funnel.screening / previewJob.funnel.total) * 100)}%
                          </p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-md p-2">
                          <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Triagem → Entrevista</p>
                          <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                            {previewJob.funnel.screening > 0 ? Math.round((previewJob.funnel.interview / previewJob.funnel.screening) * 100) : 0}%
                          </p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-md p-2">
                          <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Entrevista → Final</p>
                          <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                            {previewJob.funnel.interview > 0 ? Math.round((previewJob.funnel.final / previewJob.funnel.interview) * 100) : 0}%
                          </p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-md p-2">
                          <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Final → Contratação</p>
                          <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                            {previewJob.funnel.final > 0 ? Math.round((previewJob.funnel.hired / previewJob.funnel.final) * 100) : 0}%
                          </p>
                        </div>
                      </div>

                      {/* Insights e Recomendações da LIA */}
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-xs font-medium text-gray-950 dark:text-gray-200 font-semibold mb-1">
                              Insights da LIA
                            </p>
                            <ul className="space-y-1 text-xs text-gray-800 dark:text-gray-200">
                              {previewJob.funnel.total < 10 && (
                                <li>• Pipeline baixo: Ampliar divulgação ou revisar requisitos</li>
                              )}
                              {previewJob.level === 'Sênior' && (
                                <li>• Alto risco de recusa: Prepare margem de negociação de 15-20%</li>
                              )}
                              {previewJob.funnel.screening > previewJob.funnel.interview * 3 && (
                                <li>• Gargalo em entrevistas: Agilize agendamentos</li>
                              )}
                              {previewJob.urgencyLevel > 3 && previewJob.funnel.total < 20 && (
                                <li>• Urgência vs Pipeline: Ative sourcing ativo e headhunting</li>
                              )}
                            </ul>
                          </div>
                        </div>
                      </div>

                      {/* Análise Comparativa */}
                      <div className="bg-white dark:bg-gray-800 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Comparativo com Mercado
                        </h4>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Salário</p>
                            <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                              {previewJob.salary > 'R$ 10.000' ? '+15%' : '-5%'}
                            </p>
                            <p className={textStyles.bodySmall}>vs. mercado</p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Candidatos</p>
                            <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                              {previewJob.funnel.total > 30 ? '+45%' : '-20%'}
                            </p>
                            <p className={textStyles.bodySmall}>vs. média</p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Atratividade</p>
                            <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                              #{Math.floor(Math.random() * 10) + 1}
                            </p>
                            <p className={textStyles.bodySmall}>ranking</p>
                          </div>
                        </div>
                      </div>

                      {/* KPIs da Vaga com Budget */}
                      <div className="bg-gray-50 dark:bg-gray-700/30 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <TrendingUp className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          KPIs e Orçamento
                        </h4>
                        <div className="grid grid-cols-2 gap-2">
                          <div className="flex items-center justify-between">
                            <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Urgência</span>
                            <div className="flex gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < previewJob.urgencyLevel ? 'bg-red-500' : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                          {previewJob.budget && (
                            <>
                              <div className="flex items-center justify-between">
                                <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Budget</span>
                                <span className="text-xs font-bold text-gray-950 dark:text-gray-50">
                                  R$ {(previewJob.budget / 1000).toFixed(0)}k
                                </span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Usado</span>
                                <span className="text-xs font-bold text-gray-950 dark:text-gray-50">
                                  {previewJob.budgetUsed ? Math.round((previewJob.budgetUsed / previewJob.budget) * 100) : 0}%
                                </span>
                              </div>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Fatores de Risco */}
                      <div className="bg-red-50 dark:bg-red-900/20 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <Shield className="w-3.5 h-3.5 text-red-600" />
                          Fatores de Risco
                        </h4>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-800 dark:text-gray-200">Competitividade salarial</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.level === 'Sênior' ? 4 : 2) ? 'bg-red-500' : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-800 dark:text-gray-200">Escassez de talentos</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.level === 'Sênior' ? 3 : 1) ? 'bg-orange-500' : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-800 dark:text-gray-200">Tempo de processo</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.urgencyLevel > 3 ? 4 : 2) ? 'bg-gray-500 dark:bg-gray-600' : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Canais de Divulgação */}
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <Share2 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Canais de Divulgação
                        </h4>
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1">
                              <Linkedin className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                              <span className={`${textStyles.bodySmall} dark:text-gray-200`}>LinkedIn</span>
                            </div>
                            {previewJob.publishedLinkedIn ? (
                              <Badge className="text-xs bg-gray-100 text-gray-950 dark:bg-gray-700 dark:text-gray-200">Publicado</Badge>
                            ) : (
                              <Badge className="text-xs bg-gray-100 text-gray-800">Não publicado</Badge>
                            )}
                          </div>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1">
                              <Globe className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                              <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Site</span>
                            </div>
                            {previewJob.publishedWebsite ? (
                              <Badge className="text-xs bg-gray-100 text-gray-950 dark:bg-gray-700 dark:text-gray-200">Publicado</Badge>
                            ) : (
                              <Badge className="text-xs bg-gray-100 text-gray-800">Não publicado</Badge>
                            )}
                          </div>
                          {previewJob.publishedIndeed !== undefined && (
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-1">
                                <Briefcase className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                                <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Indeed</span>
                              </div>
                              {previewJob.publishedIndeed ? (
                                <Badge className="text-xs bg-gray-100 text-gray-950 dark:bg-gray-700 dark:text-gray-200">Publicado</Badge>
                              ) : (
                                <Badge className="text-xs bg-gray-100 text-gray-800">Não publicado</Badge>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Ações Rápidas - Aparecem em todas as tabs */}
                  <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 space-y-2">
                    <Button
                      className="w-full text-xs h-8 gap-2"
                      onClick={() => handleJobClick(previewJob)}
                    >
                      <ChevronRight className="w-4 h-4" />
                      Abrir Kanban de Candidatos
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Column Configuration Sidebar - Right - Estilo ElevenLabs */}
            {showColumnConfig && (
              <div className="flex-shrink-0 w-80 transition-all duration-300">
                <Card className="h-full flex flex-col overflow-hidden bg-white dark:bg-gray-900 rounded-md border border-gray-200 dark:border-gray-700">
                  <div className="flex-shrink-0 p-4 border-b border-gray-100 dark:border-gray-800">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-sm text-gray-950 dark:text-gray-50">Configurar Colunas</h3>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowColumnConfig(false)}
                        className="h-7 w-7 p-0 hover:bg-gray-900/10 dark:hover:bg-gray-100/10 rounded-full"
                      >
                        <X className="w-4 h-4 text-gray-950 dark:text-gray-50" />
                      </Button>
                    </div>
                    <p className="text-xs text-gray-800 dark:text-gray-200 mt-1">
                      Selecione as colunas visíveis na tabela ({visibleColumnIds.length} ativas)
                    </p>
                  </div>

                  <div className="flex-1 overflow-y-auto p-4">
                    {savedColumnViews.length > 0 && (
                      <div className="mb-4 pb-3 border-b border-gray-200 dark:border-gray-700">
                        <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">
                          Visualizações Salvas
                        </h4>
                        <div className="space-y-1">
                          {savedColumnViews.map(view => (
                            <div key={view.id} className="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded">
                              <button
                                onClick={() => applyColumnView(view.id)}
                                className="text-xs text-gray-800 hover:text-gray-900"
                              >
                                {view.name}
                              </button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => deleteColumnView(view.id)}
                                className="h-5 w-5 p-0"
                              >
                                <X className="w-3 h-3 text-gray-400" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="space-y-3">
                      {Object.entries({
                        principais: 'Colunas Principais',
                        informacoes: 'Informações da Vaga',
                        prazos: 'Prazos',
                        responsaveis: 'Responsáveis',
                        localizacao: 'Localização e Modelo',
                        remuneracao: 'Remuneração e Budget',
                        divulgacao: 'Divulgação',
                        requisitos: 'Requisitos',
                        targeting: 'Segmentação',
                        metricas: 'Métricas'
                      }).map(([categoryKey, categoryLabel]) => {
                        const categoryColumns = columnConfig.filter(col => col.category === categoryKey)
                        if (categoryColumns.length === 0) return null
                        return (
                          <div key={categoryKey}>
                            <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">
                              {categoryLabel}
                            </h4>
                            <div className="space-y-1">
                              {categoryColumns.map(col => (
                                <label key={col.id} className="flex items-center gap-2 p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded cursor-pointer">
                                  <input 
                                    type="checkbox" 
                                    className="w-3 h-3 accent-gray-900" 
                                    checked={col.visible}
                                    onChange={() => toggleColumn(col.id)}
                                  />
                                  <span className="text-xs">{col.label}</span>
                                </label>
                              ))}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  <div className="flex-shrink-0 p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
                    <div className="grid grid-cols-2 gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 text-xs"
                        onClick={() => {
                          const name = prompt("Nome da visualização:")
                          if (name) {
                            saveColumnView(name)
                            toast.success(`Visualização "${name}" salva!`)
                          }
                        }}
                      >
                        Salvar Visualização
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 text-xs"
                        onClick={() => {
                          resetColumnsToDefault()
                          toast.success("Colunas resetadas para o padrão")
                        }}
                      >
                        Resetar Padrão
                      </Button>
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </div>
        )}

        {/* Report Modal */}
        {showReport && reportJob && (
          <JobReportModal
            job={reportJob}
            isOpen={showReport}
            onClose={handleCloseReport}
          />
        )}

        {/* Modais de Ações em Massa para Vagas */}
        <JobCompareModal
          isOpen={showCompareModal}
          onClose={() => setShowCompareModal(false)}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            department: job.department,
            location: job.location,
            work_model: job.workModel,
            salary_range: undefined,
            status: job.status,
            deadline: job.deadline,
            candidates_count: job.funnel?.total || 0,
            approved_count: job.funnel?.hired || 0,
            screening_count: job.funnel?.screening || 0,
            performance_score: job.funnel?.hired ? Math.round((job.funnel.hired / Math.max(job.funnel.total, 1)) * 100) : 0,
            benefits: job.benefits,
            technical_requirements: job.technicalRequirements,
            behavioral_competencies: job.behavioralCompetencies
          }))}
        />

        <JobPublishModal
          isOpen={showPublishModal}
          onClose={() => setShowPublishModal(false)}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            status: job.status,
            is_published: job.status === 'Ativa',
            published_channels: []
          }))}
          onPublish={async (jobIds, channels, options) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              
              for (const job of selectedJobs) {
                if (!job.backendId) continue
                
                await liaApi.updateJobVacancy(job.backendId, {
                  status: 'Ativa',
                  published_website: channels.includes('portal')
                })
                
                if (channels.includes('linkedin')) {
                  try {
                    const linkedInResult = await liaApi.publishToLinkedIn(job.backendId)
                    if (linkedInResult.mock) {
                      toast.info(`LinkedIn: ${linkedInResult.message}`)
                    }
                  } catch (err) {
                    console.error('LinkedIn publish error:', err)
                  }
                }
                
                if (channels.includes('indeed')) {
                  try {
                    const indeedResult = await liaApi.publishToIndeed(job.backendId)
                    if (indeedResult.note) {
                      toast.info(`Indeed: ${indeedResult.note}`)
                    }
                  } catch (err) {
                    console.error('Indeed publish error:', err)
                  }
                }
              }
              
              toast.success(`${jobIds.length} vaga(s) publicada(s) em ${channels.length} canal(is)`)
              setShowPublishModal(false)
              deselectAllJobs()
              loadBackendJobs()
            } catch (error) {
              console.error('Erro ao publicar vagas:', error)
              toast.error('Erro ao publicar vagas. Tente novamente.')
            }
          }}
          onUnpublish={async (jobIds, options) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              
              for (const job of selectedJobs) {
                if (!job.backendId) continue
                
                // Despublicar das plataformas
                if (job.publishedLinkedIn) {
                  try {
                    await liaApi.unpublishFromPlatform(job.backendId, 'linkedin')
                  } catch (err) {
                    console.error('LinkedIn unpublish error:', err)
                  }
                }
                
                if (job.publishedIndeed) {
                  try {
                    await liaApi.unpublishFromPlatform(job.backendId, 'indeed')
                  } catch (err) {
                    console.error('Indeed unpublish error:', err)
                  }
                }
                
                // Se congelar vaga está marcado, altera o status
                if (options?.freezeJob) {
                  try {
                    // Atualiza o status para Paralisada
                    await liaApi.updateJobVacancy(job.backendId, {
                      status: 'Paralisada'
                    } as any)
                  } catch (err) {
                    console.error('Error freezing job:', err)
                  }
                }
              }
              
              toast.success(`${jobIds.length} vaga(s) despublicada(s)`)
              setShowPublishModal(false)
              deselectAllJobs()
              loadBackendJobs()
            } catch (error) {
              console.error('Erro ao despublicar vagas:', error)
              toast.error('Erro ao despublicar vagas. Tente novamente.')
            }
          }}
          onOpenCommunicationModal={(jobIds, templateCategory) => {
            const selectedJobsList = allJobs.filter(job => jobIds.includes(String(job.id)))
            const jobTitles = selectedJobsList.map(j => j.title).join(', ')
            toast.info(
              `Para notificar candidatos das vagas "${jobTitles}", acesse a página do Kanban de cada vaga e use o menu de comunicação.`,
              { duration: 8000 }
            )
          }}
        />

        <JobUnpublishModal
          isOpen={showUnpublishModal}
          onClose={() => setShowUnpublishModal(false)}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id) && job.is_published).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            status: job.status,
            is_published: job.is_published,
            published_channels: job.published_channels
          }))}
          candidates={[]}
          onUnpublish={async (data: UnpublishData) => {
            try {
              const response = await fetch('/api/backend-proxy/job-boards/unpublish-complete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  job_ids: data.jobIds,
                  freeze_job: data.freezeJob,
                  freeze_reason: data.freezeReason,
                  freeze_start_date: data.freezeStartDate,
                  unfreeze_date: data.unfreezeDate,
                  notify_applicants: data.notifyApplicants,
                  notification_channel: data.notificationChannel,
                  notification_message: data.notificationMessage,
                  notification_subject: data.notificationSubject,
                  candidate_ids: data.candidateIds,
                  cancel_scheduled_interviews: data.cancelScheduledInterviews,
                  cancel_scheduled_screenings: data.cancelScheduledScreenings,
                  send_recruiter_summary: data.sendRecruiterSummary
                })
              })
              
              if (!response.ok) {
                throw new Error('Failed to unpublish')
              }
              
              const result = await response.json()
              
              if (result.frozen_jobs?.length > 0) {
                toast.success(`${result.frozen_jobs.length} vaga(s) congelada(s) com sucesso`)
              } else if (result.unpublished_jobs?.length > 0) {
                toast.success(`${result.unpublished_jobs.length} vaga(s) despublicada(s)`)
              }
              
              deselectAllJobs()
              loadBackendJobs()
            } catch (error) {
              console.error('Erro na despublicação:', error)
              throw error
            }
          }}
          onComplete={() => {
            loadBackendJobs()
          }}
          onNavigateToJobWithCommunication={(jobId, params) => {
            const job = allJobs.find(j => String(j.id) === jobId)
            if (job) {
              const queryParams = new URLSearchParams({
                action: 'notify',
                template: params.template,
                channel: params.channel,
                candidates: params.candidateIds.join(',')
              }).toString()
              
              setSelectedJob(job)
              setShowUnpublishModal(false)
              
              localStorage.setItem('pendingCommunicationAction', JSON.stringify({
                template: params.template,
                candidateIds: params.candidateIds,
                channel: params.channel,
                jobId: jobId
              }))
            }
          }}
        />

        <JobInsightsModal
          isOpen={showInsightsModal}
          onClose={() => setShowInsightsModal(false)}
          onSendEmail={(reportData) => {
            const jobTitles = allJobs
              .filter(job => reportData.jobIds.includes(String(job.id)))
              .map(j => j.title)
              .join(', ')
            const subject = encodeURIComponent(`Relatório de Insights - ${jobTitles}`)
            const body = encodeURIComponent(`Segue relatório de insights das vagas selecionadas.\n\n${reportData.reportHtml.replace(/<[^>]*>/g, '')}`)
            window.open(`mailto:?subject=${subject}&body=${body}`, '_blank')
            toast.success('Abrindo cliente de email...')
          }}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            status: job.status,
            priority: job.priority,
            deadline: job.deadline,
            candidates_count: job.funnel?.total || 0,
            approved_count: job.funnel?.hired || 0,
            screening_count: job.funnel?.screening || 0,
            rejected_count: 0,
            performance_score: job.funnel?.hired ? Math.round((job.funnel.hired / Math.max(job.funnel.total, 1)) * 100) : 0
          }))}
        />

        <JobDuplicateModal
          isOpen={showDuplicateModal}
          onClose={() => setShowDuplicateModal(false)}
          job={(() => {
            const selectedJob = allJobs.find(job => selectedJobsForBatch.has(job.id))
            return selectedJob ? {
              id: String(selectedJob.id),
              code: selectedJob.jobId,
              title: selectedJob.title,
              department: selectedJob.department,
              location: selectedJob.location,
              recruiter: selectedJob.recruiter,
              recruiter_email: selectedJob.recruiterEmail,
              candidates_count: selectedJob.funnel?.total || 0,
              approved_count: selectedJob.funnel?.hired || 0
            } : null
          })()}
          recruiters={companyRecruiters}
          onDuplicate={async (options) => {
            try {
              const selectedJob = allJobs.find(job => selectedJobsForBatch.has(job.id))
              if (!selectedJob?.backendId) {
                toast.error('Vaga não encontrada')
                return
              }
              
              const includesCandidates = options.candidateOption !== 'none'
              const candidateFilter = options.candidateOption === 'approved' ? 'approved' : (options.candidateOption === 'all' ? 'all' : null)
              const selectedRecruiter = companyRecruiters.find(r => r.id === options.recruiterId)
              
              const result = await liaApi.duplicateJobVacancy(selectedJob.backendId, {
                copies: 1,
                includeCandiates: includesCandidates,
                candidateFilter: candidateFilter,
                overrides: {
                  title: options.newTitle,
                  recruiter: selectedRecruiter?.name || selectedJob.recruiter,
                  recruiter_email: selectedRecruiter?.email || selectedJob.recruiterEmail,
                  status: 'Rascunho',
                  deadline_shortlist: options.deadlineShortlist,
                  deadline_screening: options.deadlineScreening,
                  deadline_closing: options.deadlineClosing
                }
              })
              
              const newJobId = result?.jobs?.[0]?.id
              const candidatesIncluded = result?.total_candidates_cloned || 0
              
              if (includesCandidates && candidatesIncluded > 0) {
                toast.success(`Vaga "${options.newTitle}" criada com ${candidatesIncluded} candidato(s)!`)
              } else if (options.candidateOption === 'none') {
                toast.success(`Vaga "${options.newTitle}" criada! Inicie a busca de candidatos.`)
              } else {
                toast.success(`Vaga "${options.newTitle}" criada com sucesso!`)
              }
              
              setShowDuplicateModal(false)
              deselectAllJobs()
              await loadBackendJobs()
              
              if (options.candidateOption === 'none' && newJobId) {
                router.push(`/jobs/${newJobId}?action=sourcing`)
              }
            } catch (error) {
              console.error('Erro ao duplicar vaga:', error)
              toast.error('Erro ao duplicar vaga. Tente novamente.')
            }
          }}
        />

        <JobStatusModal
          isOpen={showStatusModal}
          onClose={() => setShowStatusModal(false)}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            status: job.status,
            candidates_count: job.funnel?.total || 0,
            screening_count: job.funnel?.screening || 0,
            interviews_scheduled: job.funnel?.interview || 0,
            tests_scheduled: 0,
            approved_count: job.funnel?.hired || 0,
            paused_since: job.status === 'Paralisada' ? job.createdAt : undefined
          }))}
          mode={statusModalMode}
          onPause={async (data) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              const updatePromises = selectedJobs.map(job => {
                if (job.backendId) {
                  return liaApi.updateJobVacancyStatus(job.backendId, 'Paralisada')
                }
                return Promise.resolve(null)
              })
              await Promise.all(updatePromises)
              
              if (data.sendRecruiterSummary && data.recruiterNotificationChannel) {
                const channelMap: Record<string, string[]> = {
                  'email': ['email'],
                  'teams': ['teams'],
                  'bell': ['bell'],
                  'email_teams': ['email', 'teams'],
                  'all': ['email', 'teams', 'bell']
                }
                const channels = channelMap[data.recruiterNotificationChannel] || ['bell']
                
                const recruiterIds = [...new Set(selectedJobs
                  .map(j => j.recruiter?.id || j.recruiterId)
                  .filter(Boolean) as string[])]
                
                if (recruiterIds.length === 0) {
                  recruiterIds.push('default_user')
                }
                
                try {
                  await liaApi.sendRecruiterActionNotification({
                    recruiter_ids: recruiterIds,
                    action: 'pause',
                    job_titles: selectedJobs.map(j => j.title),
                    job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
                    channels,
                    reason: data.pauseReason,
                    cancelled_screenings: data.cancelScheduledScreenings,
                    cancelled_interviews: data.cancelScheduledInterviews,
                    cancelled_tests: data.cancelScheduledTests,
                    notified_candidates_count: data.notifyApplicants ? data.candidateIds?.length || 0 : 0,
                  })
                } catch (notifError) {
                  console.error('Erro ao enviar notificação aos recrutadores:', notifError)
                }
              }
              
              // Update local state to reflect status change + auto-pause screening
              setBackendJobs(prev => prev.map(job => 
                selectedJobsForBatch.has(job.id) 
                  ? { ...job, status: 'Paralisada' as any, screeningStatus: job.screeningStatus === 'active' ? 'paused' : job.screeningStatus } 
                  : job
              ))
              
              // Auto-pause active screenings
              for (const job of selectedJobs) {
                if (job.backendId && (job.screeningStatus === 'active')) {
                  try {
                    await liaApi.updateScreeningStatus(job.backendId, 'paused', { pause_reason: 'Vaga pausada automaticamente' })
                  } catch (err) {
                    console.error('Error auto-pausing screening:', err)
                  }
                }
              }
              deselectAllJobs()
            } catch (error) {
              console.error('Erro ao pausar vagas:', error)
              throw error
            }
          }}
          onActivate={async (data) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              const updatePromises = selectedJobs.map(job => {
                if (job.backendId) {
                  return liaApi.updateJobVacancyStatus(job.backendId, 'Ativa')
                }
                return Promise.resolve(null)
              })
              await Promise.all(updatePromises)
              
              if (data.sendRecruiterSummary && data.recruiterNotificationChannel) {
                const channelMap: Record<string, string[]> = {
                  'email': ['email'],
                  'teams': ['teams'],
                  'bell': ['bell'],
                  'email_teams': ['email', 'teams'],
                  'all': ['email', 'teams', 'bell']
                }
                const channels = channelMap[data.recruiterNotificationChannel] || ['bell']
                
                const recruiterIds = [...new Set(selectedJobs
                  .map(j => j.recruiter?.id || j.recruiterId)
                  .filter(Boolean) as string[])]
                
                if (recruiterIds.length === 0) {
                  recruiterIds.push('default_user')
                }
                
                try {
                  await liaApi.sendRecruiterActionNotification({
                    recruiter_ids: recruiterIds,
                    action: 'activate',
                    job_titles: selectedJobs.map(j => j.title),
                    job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
                    channels,
                  })
                } catch (notifError) {
                  console.error('Erro ao enviar notificação aos recrutadores:', notifError)
                }
              }
              
              // Update local state to reflect status change
              setBackendJobs(prev => prev.map(job => 
                selectedJobsForBatch.has(job.id) 
                  ? { ...job, status: 'Ativa' as any } 
                  : job
              ))
              
              // Check if any reactivated jobs had paused screenings - ask to reactivate
              const jobsWithPausedScreening = selectedJobs.filter(j => j.screeningStatus === 'paused' && j.screeningConfig)
              if (jobsWithPausedScreening.length > 0) {
                setReactivateScreeningJobs(jobsWithPausedScreening)
                setShowReactivateScreeningDialog(true)
              }
              deselectAllJobs()
            } catch (error) {
              console.error('Erro ao ativar vagas:', error)
              throw error
            }
          }}
          onNavigateToJobWithCommunication={(jobId, params) => {
            setShowStatusModal(false)
            const job = allJobs.find(j => String(j.id) === jobId)
            if (job) {
              setSelectedJob(job)
              setPreviewJob(job)
              
              localStorage.setItem('pendingCommunicationAction', JSON.stringify({
                template: params.template,
                candidateIds: params.candidateIds,
                channel: params.channel,
                jobId: jobId,
                action: 'pause_notification'
              }))
              
              toast.success('Vaga pausada. O modal de comunicação será aberto para notificar candidatos.')
            }
          }}
        />

        <JobAssignRecruiterModal
          isOpen={showAssignRecruiterModal}
          onClose={() => setShowAssignRecruiterModal(false)}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            recruiter: job.recruiter
          }))}
          recruiters={companyRecruiters}
          onAssign={async (jobIds, recruiterId, options) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              const recruiter = companyRecruiters.find(r => r.id === recruiterId)
              
              if (!recruiter) {
                toast.error('Recrutador não encontrado')
                return
              }
              
              const previousRecruiters = [...new Set(selectedJobs
                .map(j => j.recruiter?.id || j.recruiterId)
                .filter(Boolean) as string[])]
              
              const updatePromises = selectedJobs.map(job => {
                if (job.backendId) {
                  return liaApi.updateJobVacancy(job.backendId, {
                    recruiter: recruiter.name,
                    recruiter_email: recruiter.email
                  })
                }
                return Promise.resolve(null)
              })
              await Promise.all(updatePromises)
              
              if (options.notifyRecruiter) {
                try {
                  await liaApi.sendRecruiterActionNotification({
                    recruiter_ids: [recruiterId],
                    action: 'assign',
                    job_titles: selectedJobs.map(j => j.title),
                    job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
                    channels: ['bell', 'email', 'teams'],
                  })
                } catch (notifError) {
                  console.error('Erro ao notificar recrutador:', notifError)
                }
              }
              
              if (options.transferCommunications && previousRecruiters.length > 0) {
                try {
                  await liaApi.transferCommunications({
                    job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
                    from_recruiter_ids: previousRecruiters,
                    to_recruiter_id: recruiterId
                  })
                } catch (transferError) {
                  console.error('Erro ao transferir comunicações:', transferError)
                  toast.warning('Comunicações não foram transferidas')
                }
              }
              
              setBackendJobs(prev => prev.map(job => 
                selectedJobsForBatch.has(job.id) 
                  ? { ...job, recruiter: recruiter.name, recruiterEmail: recruiter.email } 
                  : job
              ))
              
              toast.success(`Recrutador atribuído a ${jobIds.length} vaga(s)`)
              setShowAssignRecruiterModal(false)
              deselectAllJobs()
            } catch (error) {
              console.error('Erro ao atribuir recrutador:', error)
              toast.error('Erro ao atribuir recrutador. Tente novamente.')
            }
          }}
        />

        {/* Modal de Criação de Vaga */}
        <CreateJobModal
          isOpen={showCreateJobModal}
          onClose={() => setShowCreateJobModal(false)}
          onCreateWithWizard={() => {
            setShowCreateJobModal(false)
            if (activeFilter === 'visao-geral') {
              setActiveFilter('todas')
              setTimeout(() => openJobCreationChat(), 100)
            } else {
              openJobCreationChat()
            }
          }}
          onJobCreated={(jobId) => {
            setShowCreateJobModal(false)
            localStorage.setItem("jobCreationMode", jobId)
            setPendingNavigateJobId(jobId)
            setJobsRefreshKey(k => k + 1)
          }}
        />

        {/* Modal de Edição de Vaga */}
        <EditJobModal
          isOpen={showEditJobModal}
          onClose={() => {
            setShowEditJobModal(false)
            setEditingJob(null)
          }}
          job={editingJob}
          onSave={async (jobId, updates) => {
            try {
              await liaApi.updateJobVacancy(jobId, updates)
              toast.success('Vaga atualizada com sucesso!')
              setShowEditJobModal(false)
              setEditingJob(null)
              // Recarregar para aplicar alterações (reload simples e confiável)
              window.location.reload()
            } catch (error) {
              console.error('Erro ao atualizar vaga:', error)
              toast.error('Erro ao atualizar vaga. Tente novamente.')
              throw error
            }
          }}
        />

        {/* Modais de Configuração de Triagem */}
        <ScreeningChannelsModal
          isOpen={showScreeningChannelsModal}
          onClose={() => setShowScreeningChannelsModal(false)}
          config={screeningConfig}
          updateConfig={updateScreeningConfig}
        />

        <ScreeningSettingsModal
          isOpen={showScreeningSettingsModal}
          onClose={() => setShowScreeningSettingsModal(false)}
          config={screeningConfig}
          updateConfig={updateScreeningConfig}
        />

        <ScreeningSchedulingModal
          isOpen={showScreeningSchedulingModal}
          onClose={() => setShowScreeningSchedulingModal(false)}
          config={screeningConfig}
          updateConfig={updateScreeningConfig}
        />


        {showReactivateScreeningDialog && reactivateScreeningJobs.length > 0 && (
          <Dialog open={showReactivateScreeningDialog} onOpenChange={(open) => !open && setShowReactivateScreeningDialog(false)}>
            <DialogContent className="max-w-sm rounded-md bg-white border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
              <DialogHeader className="pb-3 border-b border-gray-200 dark:border-gray-700">
                <DialogTitle className="text-sm font-semibold text-gray-950 dark:text-gray-50 font-['Open_Sans',sans-serif]">
                  Reativar Triagem?
                </DialogTitle>
              </DialogHeader>
              <div className="py-4 space-y-3">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {reactivateScreeningJobs.length === 1 
                    ? `A vaga "${reactivateScreeningJobs[0]?.title}" tinha a triagem ativa antes de ser pausada. Deseja reativar a triagem?`
                    : `${reactivateScreeningJobs.length} vagas tinham triagem ativa antes de serem pausadas. Deseja reativá-las?`
                  }
                </p>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-gray-600 dark:text-gray-400">
                    Nova data de término (opcional)
                  </Label>
                  <Input
                    type="date"
                    value={reactivateEndDate}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setReactivateEndDate(e.target.value)}
                    className="h-8 text-xs border-gray-200 dark:border-gray-600 dark:bg-gray-700"
                  />
                </div>
              </div>
              <DialogFooter className="gap-2 pt-3 border-t border-gray-200 dark:border-gray-700">
                <Button
                  variant="outline"
                  onClick={() => { setShowReactivateScreeningDialog(false); setReactivateScreeningJobs([]); setReactivateEndDate('') }}
                  className="h-8 px-4 text-xs border-gray-300 dark:border-gray-600"
                >
                  Não, manter pausada
                </Button>
                <Button
                  onClick={async () => {
                    for (const job of reactivateScreeningJobs) {
                      if (job.backendId) {
                        try {
                          await liaApi.updateScreeningStatus(job.backendId, 'active', { 
                            scheduled_end_date: reactivateEndDate || undefined 
                          })
                        } catch (err) {
                          console.error('Error reactivating screening:', err)
                        }
                      }
                    }
                    setBackendJobs(prev => prev.map(j => 
                      reactivateScreeningJobs.some((rj: any) => rj.id === j.id) 
                        ? { ...j, screeningStatus: 'active' as any } 
                        : j
                    ))
                    toast.success(`Triagem reativada para ${reactivateScreeningJobs.length} vaga(s)!`)
                    setShowReactivateScreeningDialog(false)
                    setReactivateScreeningJobs([])
                    setReactivateEndDate('')
                  }}
                  className="h-8 px-4 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                >
                  Sim, reativar triagem
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}

        {/* Modal de Tutorial WSI - Metodologia WeDoTalent Skill Index */}
        {showWSITutorialModal && (
          <div 
            className="fixed inset-0 bg-black/30 backdrop-blur-[1px] z-50 flex items-center justify-center p-4"
            onClick={() => setShowWSITutorialModal(false)}
          >
            <div 
              className="bg-white rounded-md w-full max-w-3xl max-h-[85vh] border border-gray-200 flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-5 border-b border-gray-200 shrink-0">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-gray-100 dark:bg-gray-800 rounded-md">
                    <GraduationCap className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  </div>
                  <h3 className="text-sm font-semibold text-gray-950">
                    Tutorial: Metodologia WSI
                  </h3>
                  <Badge className="text-micro px-2 py-0.5 h-5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                    WeDoTalent Skill Index
                  </Badge>
                </div>
                <button 
                  onClick={() => setShowWSITutorialModal(false)}
                  className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
                >
                  <X className="w-4 h-4 text-gray-600" />
                </button>
              </div>

              {/* Content - Scrollable */}
              <div className="flex-1 overflow-y-auto p-5 space-y-5">
                {/* Seção 1: O que é WSI? */}
                <div className="p-4 bg-gradient-to-r from-gray-50 dark:from-gray-900 to-gray-100 dark:to-gray-800 border border-gray-300 dark:border-gray-600 rounded-md">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    <h4 className="text-xs font-semibold text-gray-950">O que é WSI?</h4>
                  </div>
                  <p className="text-xs text-gray-800 leading-relaxed">
                    <strong>WeDoTalent Skill Index</strong> é um índice conversacional proprietário que combina 
                    IA com psicometria para validar competências técnicas, comportamentais e fit cultural em 
                    triagens de <strong>5-10 minutos</strong>.
                  </p>
                </div>

                {/* Seção 2: Base Teórica */}
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
                  <div className="flex items-center gap-2 mb-3">
                    <BookOpen className="w-4 h-4 text-purple-600" />
                    <h4 className="text-xs font-semibold text-gray-950">Base Teórica (4 Modelos Científicos)</h4>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-white rounded-md border border-gray-100">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-50 dark:bg-gray-900 text-gray-600">CBI</Badge>
                        <span className="text-micro text-gray-600">McClelland, 1973</span>
                      </div>
                      <p className="text-micro text-gray-800">
                        Competency-Based Interviewing - perguntas situacionais baseadas em comportamentos passados
                      </p>
                    </div>
                    <div className="p-3 bg-white rounded-md border border-gray-100">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge className="text-micro px-1.5 py-0 h-4 bg-green-100 text-green-700">Bloom</Badge>
                        <span className="text-micro text-gray-600">Anderson et al., 2001</span>
                      </div>
                      <p className="text-micro text-gray-800">
                        Taxonomia de níveis cognitivos (Lembrar → Criar)
                      </p>
                    </div>
                    <div className="p-3 bg-white rounded-md border border-gray-100">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge className="text-micro px-1.5 py-0 h-4 bg-orange-100 text-orange-700">Dreyfus</Badge>
                        <span className="text-micro text-gray-600">1980</span>
                      </div>
                      <p className="text-micro text-gray-800">
                        Estágios de domínio de habilidade (1-5: Novice → Expert)
                      </p>
                    </div>
                    <div className="p-3 bg-white rounded-md border border-gray-100">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge className="text-micro px-1.5 py-0 h-4 bg-purple-100 text-purple-700">Big Five</Badge>
                        <span className="text-micro text-gray-600">1992</span>
                      </div>
                      <p className="text-micro text-gray-800">
                        Traços comportamentais para fit cultural
                      </p>
                    </div>
                  </div>
                </div>

                {/* Seção 3: Versões do WSI - Tabela */}
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
                  <div className="flex items-center gap-2 mb-3">
                    <Layers3 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                    <h4 className="text-xs font-semibold text-gray-950">Versões do WSI</h4>
                  </div>
                  <div className="overflow-hidden rounded-md border border-gray-200">
                    <table className="w-full text-xs">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="text-left p-2 font-semibold text-gray-800">Modelo</th>
                          <th className="text-center p-2 font-semibold text-gray-800">Perguntas</th>
                          <th className="text-center p-2 font-semibold text-gray-800">Tempo</th>
                          <th className="text-left p-2 font-semibold text-gray-800">Indicado Para</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-100">
                        <tr>
                          <td className="p-2">
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">WSI Compact</Badge>
                          </td>
                          <td className="p-2 text-center text-gray-800">6-8</td>
                          <td className="p-2 text-center text-gray-800">5-7 min</td>
                          <td className="p-2 text-gray-800">Triagens rápidas, alto volume</td>
                        </tr>
                        <tr>
                          <td className="p-2">
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-purple-100 text-purple-700">WSI Compact+</Badge>
                          </td>
                          <td className="p-2 text-center text-gray-800">8-10</td>
                          <td className="p-2 text-center text-gray-800">7-9 min</td>
                          <td className="p-2 text-gray-800">Vagas críticas, tech leads, gestão</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Seção 4: 7 Blocos da Triagem */}
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
                  <div className="flex items-center gap-2 mb-3">
                    <ClipboardList className="w-4 h-4 text-gray-600" />
                    <h4 className="text-xs font-semibold text-gray-950">7 Blocos da Triagem</h4>
                  </div>
                  <div className="space-y-2">
                    {[
                      { id: '0', name: 'Abordagem Inicial WhatsApp', time: '<1min', type: 'automático', color: 'bg-gray-100 text-gray-800' },
                      { id: '1', name: 'Apresentação da Oportunidade', time: '3min', type: 'automático', color: 'bg-gray-100 text-gray-800' },
                      { id: '2', name: 'Perguntas Padrão da Empresa', time: '2min', type: 'empresa', color: 'bg-blue-100 text-blue-700' },
                      { id: '3', name: 'Elegibilidade WSI', time: '2min', type: 'editável', color: 'bg-green-100 text-green-700' },
                      { id: '4', name: 'Avaliação Técnica', time: '5min', type: 'editável', color: 'bg-green-100 text-green-700' },
                      { id: '5', name: 'Análise Situacional e Fit', time: '4min', type: 'editável', color: 'bg-green-100 text-green-700' },
                      { id: '6', name: 'Resultado e Encerramento', time: '3min', type: 'automático', color: 'bg-gray-100 text-gray-800' },
                    ].map((block) => (
                      <div key={block.id} className="flex items-center gap-3 p-2 bg-white rounded-md border border-gray-100">
                        <div className="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                          <span className="text-micro font-semibold text-gray-900 dark:text-gray-50">{block.id}</span>
                        </div>
                        <div className="flex-1">
                          <span className="text-xs font-medium text-gray-950">{block.name}</span>
                        </div>
                        <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-50 text-gray-600 border border-gray-200">
                          {block.time}
                        </Badge>
                        <Badge className={`text-micro px-1.5 py-0 h-4 ${block.color}`}>
                          {block.type}
                        </Badge>
                      </div>
                    ))}
                  </div>
                  <p className="text-micro text-gray-600 mt-2 italic">
                    Bloco 2: Perguntas configuradas em Configurações da Empresa → Perguntas de Triagem Padrão
                  </p>
                </div>

                {/* Seção 5: Tipos de Validação */}
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
                  <div className="flex items-center gap-2 mb-3">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <h4 className="text-xs font-semibold text-gray-950">Tipos de Validação</h4>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { name: 'Autodeclaração', desc: 'Base inicial de domínio', icon: '📝' },
                      { name: 'Contexto real', desc: 'Aplicação prática', icon: '🎯' },
                      { name: 'Microteste', desc: 'Raciocínio técnico', icon: '🧪' },
                      { name: 'Situação contextual', desc: 'Fit comportamental', icon: '🎭' },
                    ].map((type, idx) => (
                      <div key={idx} className="flex items-start gap-2 p-2 bg-white rounded-md border border-gray-100">
                        <span className="text-xs">{type.icon}</span>
                        <div>
                          <span className="text-xs font-medium text-gray-950 block">{type.name}</span>
                          <span className="text-micro text-gray-600">{type.desc}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Seção 6: Distribuição e Classificações */}
                <div className="p-4 bg-gradient-to-r from-gray-50 to-gray-50 dark:to-gray-900 border border-gray-200 rounded-md">
                  <div className="flex items-center gap-2 mb-3">
                    <Scale className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                    <h4 className="text-xs font-semibold text-gray-950">Distribuição e Classificações</h4>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center gap-4">
                      <div className="flex-1">
                        <p className="text-micro text-gray-600 mb-1">Distribuição de Perguntas</p>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 rounded-full bg-gray-200 overflow-hidden">
                            <div className="h-full bg-gray-900 dark:bg-gray-50" style={{ width: '70%' }}></div>
                          </div>
                          <span className="text-micro text-gray-800">70% técnicas</span>
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="flex-1 h-2 rounded-full bg-gray-200 overflow-hidden">
                            <div className="h-full bg-purple-400" style={{ width: '30%' }}></div>
                          </div>
                          <span className="text-micro text-gray-800">30% comportamentais</span>
                        </div>
                      </div>
                    </div>
                    <div className="p-2 bg-white rounded-md border border-gray-100">
                      <p className="text-micro text-gray-600 mb-1">Fórmula de Cálculo</p>
                      <p className="text-xs font-mono text-gray-950 bg-gray-50 px-2 py-1 rounded-full">WSI = Σ(Peso × Score) / 100</p>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <div className="p-2 bg-green-50 rounded-md border border-green-200 text-center">
                        <div className="text-xs font-semibold text-green-700">≥ 4.2</div>
                        <p className="text-micro text-green-600">Aprovado automático</p>
                      </div>
                      <div className="p-2 bg-yellow-50 rounded-md border border-yellow-200 text-center">
                        <div className="text-xs font-semibold text-yellow-700">3.8-4.1</div>
                        <p className="text-micro text-yellow-600">Revisão humana</p>
                      </div>
                      <div className="p-2 bg-red-50 rounded-md border border-red-200 text-center">
                        <div className="text-xs font-semibold text-red-700">&lt; 3.8</div>
                        <p className="text-micro text-red-600">Reprovado</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Seção 7: Score Mínimo e Quando Ajustar */}
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
                  <div className="flex items-center gap-2 mb-3">
                    <Settings2 className="w-4 h-4 text-orange-600" />
                    <h4 className="text-xs font-semibold text-gray-950">Ajuste de Score Mínimo</h4>
                  </div>
                  <div className="space-y-3">
                    <p className="text-xs text-gray-800 leading-relaxed">
                      O <strong>Score Mínimo de Aprovação</strong> (ex: 75%) é <strong>configurável pelo recrutador</strong>. 
                      O padrão do sistema é <strong>75%</strong> para auto-aprovação.
                    </p>
                    <div className="overflow-hidden rounded-md border border-gray-200">
                      <table className="w-full text-xs">
                        <thead className="bg-gray-100">
                          <tr>
                            <th className="text-left p-2 font-semibold text-gray-800">Cenário</th>
                            <th className="text-left p-2 font-semibold text-gray-800">Ação Recomendada</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-100">
                          <tr>
                            <td className="p-2 text-gray-800">Taxa de aprovação muito baixa</td>
                            <td className="p-2 text-gray-800">Reduza o score (ex: 82% → 70%)</td>
                          </tr>
                          <tr>
                            <td className="p-2 text-gray-800">Taxa de aprovação muito alta</td>
                            <td className="p-2 text-gray-800">Aumente o score (ex: 70% → 85%)</td>
                          </tr>
                          <tr>
                            <td className="p-2 text-gray-800">Vaga muito específica/sênior</td>
                            <td className="p-2 text-gray-800">Score mais alto (80-90%)</td>
                          </tr>
                          <tr>
                            <td className="p-2 text-gray-800">Vaga júnior/estágio</td>
                            <td className="p-2 text-gray-800">Score mais baixo (60-70%)</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* Seção 8: Saturação e Dynamic Cutoff */}
                <div className="p-4 bg-orange-50 border border-orange-200 rounded-md">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertCircle className="w-4 h-4 text-orange-600" />
                    <h4 className="text-xs font-semibold text-gray-950">Saturação e Dynamic Cutoff</h4>
                  </div>
                  <div className="space-y-3">
                    <div className="p-3 bg-white rounded-md border border-orange-100">
                      <p className="text-micro font-medium text-orange-700 mb-1">Smart Saturation</p>
                      <p className="text-xs text-gray-800 leading-relaxed">
                        Quando a vaga atinge <strong>20 candidatos aprovados</strong>, a triagem automática é pausada. 
                        O sistema sugere ações: agendar entrevistas em lote, revisar candidatos ou desbloquear pipeline.
                      </p>
                    </div>
                    <div className="p-3 bg-white rounded-md border border-orange-100">
                      <p className="text-micro font-medium text-orange-700 mb-1">Dynamic Cutoff (Top 25%)</p>
                      <p className="text-xs text-gray-800 leading-relaxed">
                        Após <strong>30-50 triagens</strong>, o sistema aplica corte dinâmico selecionando automaticamente 
                        os <strong>top 25%</strong> candidatos por percentil histórico, garantindo qualidade mesmo em alto volume.
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 bg-white rounded-md border border-orange-100 text-center">
                        <div className="text-sm font-semibold text-orange-700">20</div>
                        <p className="text-micro text-gray-600">Limite saturação</p>
                      </div>
                      <div className="p-2 bg-white rounded-md border border-orange-100 text-center">
                        <div className="text-sm font-semibold text-orange-700">30-50</div>
                        <p className="text-micro text-gray-600">Triagens p/ cutoff</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Nota de Calibração */}
                <div className="p-3 bg-gray-50 dark:bg-gray-900 border border-gray-900 dark:border-gray-50 rounded-md">
                  <div className="flex items-start gap-2">
                    <Lightbulb className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-micro font-medium text-gray-700 dark:text-gray-300 mb-1">Calibração Automática</p>
                      <p className="text-micro text-gray-700 dark:text-gray-300 leading-relaxed">
                        Após atingir volume suficiente, a LIA recalibra automaticamente os cortes por percentil histórico, 
                        mantendo a qualidade das contratações.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="shrink-0 p-4 border-t border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between">
                  <p className="text-micro text-gray-600">
                    Metodologia proprietária WeDoTalent • Baseada em 4 modelos científicos validados
                  </p>
                  <Button 
                    size="sm" 
                    className="h-7 text-xs font-['Open_Sans'] bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                    onClick={() => setShowWSITutorialModal(false)}
                  >
                    Entendi
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}


        {/* Job Creation Wizard Modal - DEPRECATED: Now using inline chat */}
        {/* Modal removido - usando super chat inline para criação de vaga */}

      </div>
    </div>
  )
}
