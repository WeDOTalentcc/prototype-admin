"use client"

import { textStyles, cardStyles, badgeStyles, formatScorePercent } from '@/lib/design-tokens'
import { useCandidatePreviewCore } from "@/components/candidate-preview/useCandidatePreviewCore"
import { OpinionCard } from "@/components/candidate-preview/OpinionCard"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CandidateAvatar } from "@/components/candidate-profile/CandidateAvatar"

import {
  X, Maximize2, Minimize2, Star, MapPin, Calendar, Phone, Mail,
  Linkedin, ExternalLink, MessageSquare, MessageCircle, UserPlus, FileText,
  Clock, Building, GraduationCap, Briefcase, Award, Target,
  Brain, TrendingUp, CheckCircle, AlertCircle,
  Send, Calendar as CalendarIcon, UserCheck, Download,
  Heart, Share2, MoreVertical, Eye, Edit, ChevronLeft, ChevronRight,
  Activity, Video, Plus, Archive, ChevronDown, ChevronUp, Accessibility,
  Code, Globe, Users, Shield, Zap, BookOpen, BarChart3, Mic, Expand,
  DollarSign, Gift, Home, Languages, MessageSquareText, FileVideo,
  ClipboardCheck, UserCircle, Bot, PlusCircle, Filter, Upload, Image,
  File, Play, Pause, ZoomIn, ZoomOut, RotateCw, Tag, Database,
  List, GitBranch, ThumbsUp, ThumbsDown, User, Copy, Check, Trash2
} from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
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
import { InsufficientDataModal } from "@/components/modals/insufficient-data-modal"
import { ExperienceHighlightCard } from "@/components/experience-highlight-card"
import dynamic from "next/dynamic"
import type { ScreeningQuestion, TranscriptionSegment } from "@/components/modals/screening-media-modal"

const LiaAnalysisModal = dynamic(() => import("@/components/modals/lia-analysis-modal").then(m => ({ default: m.LiaAnalysisModal })), { ssr: false })
const ScreeningMediaModal = dynamic(() => import("@/components/modals/screening-media-modal").then(m => ({ default: m.ScreeningMediaModal })), { ssr: false })
const DISCAssessmentModal = dynamic(() => import("@/components/disc-assessment-modal").then(m => ({ default: m.DISCAssessmentModal })), { ssr: false })
const BigFiveModal = dynamic(() => import("@/components/big-five-modal").then(m => ({ default: m.BigFiveModal })), { ssr: false })
import { LiaChatModal } from "@/components/candidate-preview/LiaChatModal"
import { CandidateFilesTab } from "@/components/candidate-preview/CandidateFilesTab"
import { CandidateActivitiesTab } from "@/components/candidate-preview/CandidateActivitiesTab"
import { CandidatePreviewProfileTab } from "@/components/candidate-preview/CandidatePreviewProfileTab"
import { CandidateOpinionsTab } from "@/components/candidate-preview/CandidateOpinionsTab"
import { toast } from "sonner"

interface CandidatePreviewProps {
  candidate: Record<string, unknown>
  isOpen: boolean
  onClose: () => void
  isMaximized?: boolean
  onToggleMaximize?: () => void
  candidates?: Record<string, unknown>[]
  currentIndex?: number
  onNavigateCandidate?: (index: number) => void
  onOpenFullPage?: (candidate: Record<string, unknown>) => void
  onScheduleInterview?: (candidate: Record<string, unknown>) => void
  onAddToVacancy?: (candidate: Record<string, unknown>) => void
  onToggleFavorite?: (candidateId: string) => void
  onWSIScreening?: (candidate: Record<string, unknown>) => void
  onOpenTriagemDetails?: (candidate: Record<string, unknown>) => void
  isFavorite?: boolean
  onSendEmail?: (candidate: Record<string, unknown>) => void
  onSendWhatsApp?: (candidate: Record<string, unknown>) => void  
  onSendTriagem?: (candidate: Record<string, unknown>) => void
  onSendAgendamento?: (candidate: Record<string, unknown>) => void
  onSendFeedback?: (candidate: Record<string, unknown>) => void
  onContact?: (candidate: Record<string, unknown>, channel?: 'email' | 'whatsapp') => void
  onSchedule?: (candidate: Record<string, unknown>) => void
  onAddToList?: (candidate: Record<string, unknown>) => void
  jobId?: string
}

export function CandidatePreview({
  candidate,
  isOpen,
  onClose,
  isMaximized = false,
  onToggleMaximize,
  candidates = [],
  currentIndex = 0,
  onNavigateCandidate,
  onOpenFullPage,
  onScheduleInterview,
  onAddToVacancy,
  onToggleFavorite,
  onWSIScreening,
  onOpenTriagemDetails,
  isFavorite = false,
  onSendEmail,
  onSendWhatsApp,
  onSendTriagem,
  onSendAgendamento,
  onSendFeedback,
  onContact,
  onSchedule,
  onAddToList,
  jobId,
}: CandidatePreviewProps) {
  const core = useCandidatePreviewCore(candidate)
const {
    activeTab, setActiveTab,
    showLiaModal, setShowLiaModal,
    liaConversation, setLiaConversation,
    selectedFile, setSelectedFile,
    showPreview, setShowPreview,
    previewType, setPreviewType,
    isAnalyzingWithLia,
    lastAnalysisDate,
    liaChatMessages,
    isLiaChatLoading,
    opinionsData,
    isLoadingOpinions,
    expandedOpinionId, setExpandedOpinionId,
    opinionsHistory,
    isLoadingHistory,
    savedAnalyses, setSavedAnalyses,
    isLoadingAnalyses,
    opinionsSubTab, setOpinionsSubTab,
    expandedAnalysisId, setExpandedAnalysisId,
    showUpdateOpinionAlert, setShowUpdateOpinionAlert,
    showInsufficientDataModal, setShowInsufficientDataModal,
    dataRequirements,
    lastOpinionDate,
    showLiaAnalysisModal, setShowLiaAnalysisModal,
    screeningModalOpen, setScreeningModalOpen,
    screeningModalData, setScreeningModalData,
    discModalOpen, setDiscModalOpen,
    discModalData, setDiscModalData,
    bigFiveModalOpen, setBigFiveModalOpen,
    bigFiveModalCandidate, setBigFiveModalCandidate,
    copiedItemId,
    analysisToDelete, setAnalysisToDelete,
    isDeletingAnalysis,
    sendLiaMessage,
    generateNewOpinion,
    handleAnalyzeWithLia,
    handleProceedWithLimitedData,
    formatAnalysisDate,
    generateShortId,
    cleanTextForCopy,
    handleCopyOpinion,
    handleCopyAnalysis,
    handleDeleteAnalysis,
    handleAnalysisTransport,
    formatCurrency,
    getLanguagesData,
    hasSalaryData,
    hasAddressData,
    getAddressString,
    hasAdditionalDetails,
  } = core

  if (!isOpen || !candidate) return null

  candidate = {
    ...candidate,
    education: Array.isArray(candidate.education) ? candidate.education : (candidate.education ? [candidate.education] : []),
    workHistory: Array.isArray(candidate.workHistory) ? candidate.workHistory : (candidate.workHistory ? [candidate.workHistory] : []),
    skills: Array.isArray(candidate.skills) ? candidate.skills : (candidate.skills ? [candidate.skills] : []),
    certifications: Array.isArray(candidate.certifications) ? candidate.certifications : (candidate.certifications ? [candidate.certifications] : []),
    projects: Array.isArray(candidate.projects) ? candidate.projects : (candidate.projects ? [candidate.projects] : []),
    awards: Array.isArray(candidate.awards) ? candidate.awards : (candidate.awards ? [candidate.awards] : []),
  }

  type CandidateData = {
    name: string
    id?: string
    candidateId?: string
    pearch_id?: string
    avatar_url?: string
    avatar?: string
    photo_url?: string
    photoUrl?: string
    email?: string
    phone?: string
    position?: string
    location?: string
    seniority_level?: string
    seniorityLevel?: string
    years_of_experience?: number | null
    yearsOfExperience?: number | null
    linkedin_url?: string
    github_url?: string
    liaAnalysis?: { score?: number; fitScore?: number }
    lia_analysis?: { score?: number; fit_score?: number }
    [key: string]: unknown
  }
  const c = candidate as unknown as CandidateData
  const languagesData = getLanguagesData()

  const tabs = [
    { id: 'profile', label: 'Perfil Completo', icon: UserCheck },
    { id: 'activities', label: 'Atividades', icon: Activity },
    { id: 'files', label: 'Arquivos', icon: FileText },
    { id: 'opinions', label: 'Pareceres e Análises', icon: Brain, badge: ((opinionsData as unknown as {total_opinions?: number} | undefined)?.total_opinions || 0) + ((savedAnalyses as unknown as {total_analyses?: number} | undefined)?.total_analyses || 0) }
  ]

  const liaActions = [
    { id: 'auto-contact', title: 'Contato Automático', icon: '📧', buttonText: 'Enviar convite para conversa' },
    { id: 'add-to-job', title: 'Adicionar à Vaga', icon: '🎯', buttonText: 'Adicionar ao processo seletivo' },
    { id: 'schedule-interview', title: 'Agendar Entrevista', icon: '📅', buttonText: 'Sugerir horários disponíveis' },
    { id: 'request-portfolio', title: 'Solicitar Portfólio', icon: '📂', buttonText: 'Enviar solicitação automática' },
    { id: 'reference-check', title: 'Verificar Referências', icon: '✅', buttonText: 'Iniciar verificação' },
    { id: 'salary-analysis', title: 'Análise Salarial', icon: '💰', buttonText: 'Gerar relatório salarial' }
  ]

  const liaScore = c.liaAnalysis?.score || c.lia_analysis?.score
  const fitScore = c.liaAnalysis?.fitScore || c.lia_analysis?.fit_score

  return (
    <div className="h-full bg-lia-bg-primary dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle flex flex-col transition-[width,height] duration-300 w-full">
      {/* Header */}
      <TooltipProvider delayDuration={200}>
        <div className="p-3 border-b border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary">
          {/* Top Row: Avatar + Name/Title + Header Action Buttons (LIA, Expand, Close) */}
          <div className="flex items-start gap-3 mb-1.5">
            {/* Avatar */}
            <CandidateAvatar
              name={c.name as string}
              avatarUrl={(c.avatar_url as string | undefined) || (c.avatar as string | undefined) || (c.photo_url as string | undefined) || (c.photoUrl as string | undefined)}
              size="lg"
              showRing
            />

            {/* Info Section */}
            <div className="flex-1 min-w-0">
              {/* Row 1: Name + Short ID + Seniority + Experience + LGPD */}
              <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
                <h3 className={`${textStyles.title} truncate`}>
                  {c.name as string}
                </h3>
                <Badge className="text-micro px-1.5 py-0 h-4 flex-shrink-0 font-mono font-medium bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-default">
                  {generateShortId(c.name as string, (c.id as string | undefined) || (c.candidateId as string | undefined) || (c.pearch_id as string | undefined))}
                </Badge>
                {(c.seniority_level || c.seniorityLevel) && (
                  <Badge className={badgeStyles.warning}>
                    {(c.seniority_level as string | undefined) || (c.seniorityLevel as string | undefined)}
                  </Badge>
                )}
                {(c.years_of_experience !== undefined && c.years_of_experience !== null) || 
                 (c.yearsOfExperience !== undefined && c.yearsOfExperience !== null) ? (
                  <Badge className={badgeStyles.default}>
                    {typeof (c.years_of_experience || c.yearsOfExperience) === 'number' 
                      ? `${((c.years_of_experience as number | undefined) || (c.yearsOfExperience as number | undefined) || 0).toFixed(1)} anos` 
                      : `${c.years_of_experience || c.yearsOfExperience} anos`}
                  </Badge>
                ) : null}
                {(c.communication_consent !== undefined || c.communicationConsent !== undefined) && (
                  <Badge className={`text-micro px-1.5 py-0 h-4 flex items-center gap-0.5 ${(c.communication_consent ?? c.communicationConsent) ? 'bg-status-success/10 text-status-success' : 'bg-status-error/10 text-status-error'}`}>
                    {(c.communication_consent ?? c.communicationConsent) ? <CheckCircle className="w-2.5 h-2.5" /> : <AlertCircle className="w-2.5 h-2.5" />}
                    LGPD
                  </Badge>
                )}
              </div>

              {/* Row 2: Title • Company • Segment */}
              <div className="flex items-center gap-1.5 flex-wrap">
                <p className={`${textStyles.bodySmall} truncate`}>
                  {(c.position || c.title || 'Cargo não informado') as React.ReactNode}
                </p>
                <span className={`${textStyles.bodySmall} text-lia-text-secondary`}>•</span>
                <p className={`${textStyles.bodySmall} truncate`}>
                  {c.workHistory?.[0]?.company || c.current_company || c.company || 'Empresa'}
                </p>
                {(c.workHistory?.[0]?.industry || c.workHistory?.[0]?.segment || c.company_segment || c.industry) && (
                  <>
                    <span className={`${textStyles.description} text-lia-text-secondary`}>•</span>
                    <p className={`${textStyles.description} truncate`}>
                      {c.workHistory?.[0]?.industry || c.workHistory?.[0]?.segment || c.company_segment || c.industry}
                    </p>
                  </>
                )}
              </div>
            </div>

            {/* Header Action Buttons - Top Right Corner */}
            <div className="flex items-center gap-1 flex-shrink-0">
              {/* LIA Brain Icon - Larger */}
              <LiaAnalysisModal
                isOpen={showLiaAnalysisModal}
                onOpen={() => setShowLiaAnalysisModal(true)}
                onClose={() => setShowLiaAnalysisModal(false)}
                candidate={c}
                onTransportToOpinions={handleAnalysisTransport}
              >
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 hover:bg-lia-bg-tertiary border border-lia-border-default rounded-md flex-shrink-0"
                  title="Análises LIA"
                >
                  <Brain className="w-5 h-5 text-wedo-cyan" />
                </Button>
              </LiaAnalysisModal>

              {/* Expand Button */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onOpenFullPage?.(candidate)}
                    className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                  >
                    <Expand className="w-4 h-4 text-lia-text-tertiary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Expandir</TooltipContent>
              </Tooltip>

              {/* Close Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              >
                <X className="w-4 h-4 text-lia-text-tertiary" />
              </Button>
            </div>
          </div>

          {/* Row 3: Dates Only - ALIGNED TO LEFT EDGE */}
          {(() => {
            const lastContactedAt = c.last_contacted_at || c.lastContactedAt
            const updatedAt = c.updated_at || c.updatedAt
            const createdAt = c.created_at || c.createdAt
            
            const formatDate = (dateStr: string | Date | null | undefined): string => {
              if (!dateStr) return ''
              try {
                const date = new Date(dateStr)
                return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
              } catch {
                return ''
              }
            }
            
            if (!createdAt && !updatedAt && !lastContactedAt) return null
            
            return (
              // @ts-ignore TODO: fix type
              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                {(createdAt as any) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="text-micro text-lia-text-secondary flex items-center gap-0.5 cursor-help">
                        {/* @ts-ignore TODO: fix type */}
                        <Calendar className="w-2.5 h-2.5" />
                        {formatDate(createdAt as string | Date | null | undefined)}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">Data de cadastro</TooltipContent>
                  </Tooltip>
                )}
                {(updatedAt as any) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="text-micro text-lia-text-secondary flex items-center gap-0.5 cursor-help">
                        {/* @ts-ignore TODO: fix type */}
                        <Clock className="w-2.5 h-2.5" />
                        {(formatDate(updatedAt as string | Date | null | undefined) as React.ReactNode)}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">Última atualização</TooltipContent>
                  </Tooltip>
                )}
                {(lastContactedAt as any) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="text-micro text-lia-text-tertiary flex items-center gap-0.5 cursor-help">
                        {/* @ts-ignore TODO: fix type */}
                        <MessageSquare className="w-2.5 h-2.5" />
                        {(formatDate(lastContactedAt as string | Date | null | undefined) as React.ReactNode)}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">Último contato</TooltipContent>
                  </Tooltip>
                )}
              </div>
            )
          })()}

          {/* Row 4: Quick Action Buttons + Social Icons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 flex-wrap">
              
              {/* Quick Action Buttons */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                    onClick={() => onSendEmail ? onSendEmail(candidate) : (c.email && window.open(`mailto:${c.email}`, '_self'))}
                    disabled={!c.email && !onSendEmail}
                  >
                    <Mail className="w-3.5 h-3.5 text-lia-text-secondary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Email</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                    onClick={() => {
                      if (onSendWhatsApp) {
                        onSendWhatsApp(candidate)
                      } else if (c.phone) {
                        window.open(`https://wa.me/${(c.phone as string).replace(/\D/g, '')}`, '_blank')
                      }
                    }}
                    disabled={!c.phone && !onSendWhatsApp}
                  >
                    <Phone className="w-3.5 h-3.5 text-lia-text-secondary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">WhatsApp</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                    onClick={() => onSendAgendamento ? onSendAgendamento(candidate) : onScheduleInterview?.(candidate)}
                  >
                    <CalendarIcon className="w-3.5 h-3.5 text-wedo-orange" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Agendar Entrevista</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                    onClick={() => onWSIScreening ? onWSIScreening(candidate) : onSendTriagem?.(candidate)}
                  >
                    <ClipboardCheck className="w-3.5 h-3.5 text-lia-text-secondary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Triagem WSI</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                    onClick={() => onAddToVacancy?.(candidate)}
                  >
                    <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Atribuir à Vaga</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={`h-6 w-6 p-0 ${isFavorite ? 'bg-status-warning/15' : 'hover:bg-status-warning/10'}`}
                    onClick={() => {
                      onToggleFavorite?.(c.id as string)
                      toast.success(isFavorite ? "Removido dos favoritos" : "Adicionado aos favoritos", { description: isFavorite ? "Candidato removido da lista de favoritos" : "Candidato adicionado à lista de favoritos" })
                    }}
                  >
                    <Star className={`w-3.5 h-3.5 ${isFavorite ? 'text-status-warning fill-amber-500' : 'text-status-warning'}`} />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">{isFavorite ? 'Remover dos Favoritos' : 'Adicionar aos Favoritos'}</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                    onClick={() => onSendFeedback?.(candidate)}
                  >
                    <MessageSquareText className="w-3.5 h-3.5 text-wedo-purple" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Enviar Feedback</TooltipContent>
              </Tooltip>

              {/* Separator before Social Icons */}
              <span className="lia-text-muted mx-0.5">|</span>

              {/* Social Icons */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <a 
                    href={((c.linkedin as string | undefined) || (c.linkedin_url as string | undefined) || '#')} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${(c.linkedin || c.linkedin_url) ? 'hover:bg-wedo-cyan/10' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(c.linkedin || c.linkedin_url) && e.preventDefault()}
                  >
                    <Linkedin className="w-3.5 h-3.5" style={{color: (c.linkedin || c.linkedin_url) ? 'var(--lia-text-secondary)' : 'var(--lia-text-tertiary)'}} />
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">LinkedIn</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <a 
                    href={((c.github as string | undefined) || (c.github_url as string | undefined) || '#')} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${(c.github || c.github_url) ? 'hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(c.github || c.github_url) && e.preventDefault()}
                  >
                    <svg className="w-3.5 h-3.5" fill={(c.github || c.github_url) ? 'var(--lia-btn-primary-bg)' : 'var(--lia-text-tertiary)'} viewBox="0 0 24 24">
                      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">GitHub</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <a 
                    href={((c.stackoverflow as string | undefined) || (c.stackoverflow_url as string | undefined) || '#')} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${(c.stackoverflow || c.stackoverflow_url) ? 'hover:bg-wedo-orange/10' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(c.stackoverflow || c.stackoverflow_url) && e.preventDefault()}
                  >
                    <svg className="w-3.5 h-3.5" fill={(c.stackoverflow || c.stackoverflow_url) ? 'var(--lia-text-secondary)' : 'var(--lia-text-tertiary)'} viewBox="0 0 24 24">
                      <path d="M15 21h-10v-2h10v2zm6-11.665l-1.621-9.335-1.993.346 1.62 9.335 1.994-.346zm-5.964 6.937l-9.746-.975-.186 2.016 9.755.879.177-1.92zm.538-2.587l-9.276-2.608-.526 1.954 9.306 2.5.496-1.846zm1.204-2.413l-8.297-4.864-1.029 1.743 8.298 4.865 1.028-1.744zm1.866-1.467l-5.339-7.829-1.672 1.14 5.339 7.829 1.672-1.14zm-2.644 4.195v8h-12v-8h-2v10h16v-10h-2z"/>
                    </svg>
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Stack Overflow</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <a 
                    href={((c.twitter as string | undefined) || (c.twitter_url as string | undefined) || (c.x_url as string | undefined) || '#')} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${(c.twitter || c.twitter_url || c.x_url) ? 'hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(c.twitter || c.twitter_url || c.x_url) && e.preventDefault()}
                  >
                    <svg className="w-3.5 h-3.5" fill={(c.twitter || c.twitter_url || c.x_url) ? 'var(--lia-btn-primary-bg)' : 'var(--lia-text-tertiary)'} viewBox="0 0 24 24">
                      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">X (Twitter)</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <a 
                    href={((c.behance as string | undefined) || (c.behance_url as string | undefined) || '#')}
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${(c.behance || c.behance_url) ? 'hover:bg-wedo-cyan/10' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(c.behance || c.behance_url) && e.preventDefault()}
                  >
                    <svg className="w-3.5 h-3.5" fill={(c.behance || c.behance_url) ? 'var(--lia-text-secondary)' : 'var(--lia-text-tertiary)'} viewBox="0 0 24 24">
                      <path d="M22 7h-7v-2h7v2zm1.726 10c-.442 1.297-2.029 3-5.101 3-3.074 0-5.564-1.729-5.564-5.675 0-3.91 2.325-5.92 5.466-5.92 3.082 0 4.964 1.782 5.375 4.426.078.506.109 1.188.095 2.14h-8.027c.13 3.211 3.483 3.312 4.588 2.029h3.168zm-7.686-4h4.965c-.105-1.547-1.136-2.219-2.477-2.219-1.466 0-2.277.768-2.488 2.219zm-9.574 6.988h-6.466v-14.967h6.953c5.476.081 5.58 5.444 2.72 6.906 3.461 1.26 3.577 8.061-3.207 8.061zm-3.466-8.988h3.584c2.508 0 2.906-3-.312-3h-3.272v3zm3.391 3h-3.391v3.016h3.341c3.055 0 2.868-3.016.05-3.016z"/>
                    </svg>
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Behance</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <a 
                    href={((c.portfolio as string | undefined) || (c.portfolio_url as string | undefined) || '#')} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${(c.portfolio || c.portfolio_url) ? 'hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(c.portfolio || c.portfolio_url) && e.preventDefault()}
                  >
                    <ExternalLink className={`w-3.5 h-3.5 ${(c.portfolio || c.portfolio_url) ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`} />
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Portfolio</TooltipContent>
              </Tooltip>
            </div>

          </div>
        </div>
      </TooltipProvider>

      {/* Tabs */}
      <div className="border-b border-lia-border-subtle dark:border-lia-border-subtle flex items-center">
        <div className="flex overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as 'activities' | 'profile' | 'files' | 'opinions')}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium whitespace-nowrap transition-colors motion-reduce:transition-none ${
 activeTab === tab.id
                  ? 'border-b-2 border-lia-border-strong text-lia-text-primary font-semibold'
                  : 'text-lia-text-secondary hover:text-lia-text-primary'
              }`}
            >
              <tab.icon className="w-3 h-3" />
              {tab.label}
              {'badge' in tab && tab.badge! > 0 && (
                <Badge className="text-micro px-1 py-0 h-4 ml-1 bg-wedo-cyan/15">
                  {tab.badge}
                </Badge>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <TooltipProvider delayDuration={200}>
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'profile' && (
          // @ts-ignore TODO: fix type
          <CandidatePreviewProfileTab
            candidate={c}
            jobId={jobId}
            opinionsData={opinionsData}
            isLoadingOpinions={isLoadingOpinions}
            isAnalyzingWithLia={isAnalyzingWithLia}
            lastAnalysisDate={lastAnalysisDate}
            formatAnalysisDate={formatAnalysisDate}
            handleAnalyzeWithLia={handleAnalyzeWithLia}
            formatCurrency={formatCurrency}
            languagesData={languagesData}
            hasSalaryData={hasSalaryData}
            hasAddressData={hasAddressData}
            getAddressString={getAddressString}
          />
        )}

        {activeTab === 'activities' && (
          <CandidateActivitiesTab
            candidate={c}
            jobId={jobId}
            onShowLiaModal={() => setShowLiaModal(true)}
            onOpenTriagemDetails={onOpenTriagemDetails}
            onSetScreeningModalData={setScreeningModalData}
            onSetScreeningModalOpen={setScreeningModalOpen}
            onSetDiscModalData={setDiscModalData}
            onSetDiscModalOpen={setDiscModalOpen}
            onSetBigFiveModalCandidate={setBigFiveModalCandidate}
            onSetBigFiveModalOpen={setBigFiveModalOpen}
            onSetSelectedFile={setSelectedFile}
            onSetPreviewType={setPreviewType}
            onSetShowPreview={setShowPreview}
          />
        )}

        {activeTab === 'files' && (
          <CandidateFilesTab
            candidate={c}
          />
        )}

        {/* Tab Pareceres e Análises */}
        {activeTab === 'opinions' && (
          <CandidateOpinionsTab
            opinionsSubTab={opinionsSubTab}
            // @ts-ignore TODO: fix type
            setOpinionsSubTab={setOpinionsSubTab}
            opinionsHistory={opinionsHistory}
            isLoadingHistory={isLoadingHistory}
            savedAnalyses={savedAnalyses}
            isLoadingAnalyses={isLoadingAnalyses}
            // @ts-ignore TODO: fix type
            expandedOpinionId={expandedOpinionId}
            // @ts-ignore TODO: fix type
            setExpandedOpinionId={setExpandedOpinionId}
            expandedAnalysisId={expandedAnalysisId}
            // @ts-ignore TODO: fix type
            setExpandedAnalysisId={setExpandedAnalysisId}
            // @ts-ignore TODO: fix type
            analysisToDelete={analysisToDelete}
            // @ts-ignore TODO: fix type
            setAnalysisToDelete={setAnalysisToDelete}
            copiedItemId={copiedItemId}
            // @ts-ignore TODO: fix type
            handleCopyOpinion={handleCopyOpinion}
            handleCopyAnalysis={handleCopyAnalysis}
            cleanTextForCopy={cleanTextForCopy}
          />
        )}
      </div>

      {/* Modal Fale com a LIA - Estilo padronizado */}
      {/* Chat da LIA - Individual */}
      <LiaChatModal
        isOpen={showLiaModal}
        onClose={() => setShowLiaModal(false)}
        candidate={c}
        liaActions={liaActions}
        chatMessages={liaChatMessages}
        isLiaChatLoading={isLiaChatLoading}
        liaConversation={liaConversation}
        onConversationChange={setLiaConversation}
        onSendMessage={sendLiaMessage}
        onContact={onContact as unknown as never}
        onSendEmail={onSendEmail as unknown as never}
        onSchedule={onSchedule as unknown as never}
        onScheduleInterview={onScheduleInterview as unknown as never}
        onSendAgendamento={onSendAgendamento as unknown as never}
        onAddToList={onAddToList as unknown as never}
        onAddToVacancy={onAddToVacancy as unknown as never}
      />

      
      {/* AlertDialog para confirmação de novo parecer */}
      <AlertDialog open={showUpdateOpinionAlert} onOpenChange={setShowUpdateOpinionAlert}>
        <AlertDialogContent className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
          <AlertDialogHeader>
            <AlertDialogTitle className={textStyles.title}>
              Parecer Existente
            </AlertDialogTitle>
            <AlertDialogDescription className={textStyles.bodySmall}>
              Já existe um parecer gerado há {lastOpinionDate ? Math.floor((Date.now() - lastOpinionDate.getTime()) / (1000 * 60 * 60 * 24)) : 0} dias. 
              Deseja gerar um novo parecer? O anterior será arquivado.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="text-xs">Cancelar</AlertDialogCancel>
            <AlertDialogAction 
              onClick={generateNewOpinion}
              className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-xs text-white"
            >
              Gerar Novo Parecer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* AlertDialog para confirmação de exclusão de análise */}
      <AlertDialog open={!!analysisToDelete} onOpenChange={(open: boolean) => !open && setAnalysisToDelete(null)}>
        <AlertDialogContent className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
          <AlertDialogHeader>
            <AlertDialogTitle className={textStyles.title}>
              Remover Análise
            </AlertDialogTitle>
            <AlertDialogDescription className={textStyles.bodySmall}>
              Esta ação irá remover permanentemente esta análise. Deseja continuar?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="text-xs" disabled={isDeletingAnalysis}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={() => analysisToDelete && handleDeleteAnalysis(analysisToDelete)}
              className="bg-status-error hover:bg-status-error text-xs text-white"
              disabled={isDeletingAnalysis}
            >
              {isDeletingAnalysis ? 'Removendo...' : 'Remover Definitivamente'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* Modal para dados insuficientes */}
      <InsufficientDataModal
        isOpen={showInsufficientDataModal}
        onClose={() => setShowInsufficientDataModal(false)}
        onProceedAnyway={dataRequirements.filter(r => r.required && !r.hasData).length === 0 ? handleProceedWithLimitedData : undefined}
        requirements={dataRequirements}
        candidateName={c?.name as string | undefined}
      />

      {/* Modal para triagem de áudio/vídeo */}
      {screeningModalData && (
        <ScreeningMediaModal
          isOpen={screeningModalOpen}
          onClose={() => {
            setScreeningModalOpen(false)
            setScreeningModalData(null)
          }}
          type={screeningModalData.type}
          title={screeningModalData.title}
          duration={screeningModalData.duration}
          mediaUrl={screeningModalData.mediaUrl}
          jobTitle={(c?.job_title as string | undefined) || (c?.jobTitle as string | undefined)}
          candidateName={c?.name as string | undefined}
          questions={screeningModalData.questions}
          transcription={screeningModalData.transcription}
          highlights={screeningModalData.highlights}
          onOpenFullEvaluation={onOpenTriagemDetails ? () => {
            setScreeningModalOpen(false)
            setScreeningModalData(null)
            onOpenTriagemDetails(candidate)
          } : undefined}
        />
      )}
      
      {/* Modal DISC Assessment */}
      {discModalData && (
        // @ts-ignore TODO: fix type
        <DISCAssessmentModal
          isOpen={discModalOpen}
          onClose={() => {
            setDiscModalOpen(false)
            setDiscModalData(null)
          }}
          candidate={c}
          assessmentData={{
            discScores: discModalData.discScores || {
              dominance: discModalData.dominance || 75,
              influence: discModalData.influence || 85,
              steadiness: discModalData.steadiness || 45,
              conscientiousness: discModalData.conscientiousness || 60
            },
            profile: discModalData.profile || 'DI',
            profileDescription: discModalData.profileDescription || '',
            culturalFitScore: discModalData.culturalFitScore || discModalData.culturalFit || 82,
          }}
        />
      )}
      
      {/* Modal Big Five Assessment */}
      {bigFiveModalCandidate && (
        <BigFiveModal
          isOpen={bigFiveModalOpen}
          onClose={() => {
            setBigFiveModalOpen(false)
            setBigFiveModalCandidate(null)
          }}
          candidate={bigFiveModalCandidate}
        />
      )}
      
      </TooltipProvider>
    </div>
  )
}
