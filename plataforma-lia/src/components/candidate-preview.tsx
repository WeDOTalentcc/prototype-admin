"use client"

import { textStyles, cardStyles, badgeStyles, formatScorePercent } from '@/lib/design-tokens'
import { useCandidatePreviewCore } from "@/components/candidate-preview/useCandidatePreviewCore"
import { OpinionCard } from "@/components/candidate-preview/OpinionCard"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

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

  const languagesData = getLanguagesData()

  const tabs = [
    { id: 'profile', label: 'Perfil Completo', icon: UserCheck },
    { id: 'activities', label: 'Atividades', icon: Activity },
    { id: 'files', label: 'Arquivos', icon: FileText },
    { id: 'opinions', label: 'Pareceres e Análises', icon: Brain, badge: (opinionsData?.total_opinions || 0) + (savedAnalyses?.total_analyses || 0) }
  ]

  const liaActions = [
    { id: 'auto-contact', title: 'Contato Automático', icon: '📧', buttonText: 'Enviar convite para conversa' },
    { id: 'add-to-job', title: 'Adicionar à Vaga', icon: '🎯', buttonText: 'Adicionar ao processo seletivo' },
    { id: 'schedule-interview', title: 'Agendar Entrevista', icon: '📅', buttonText: 'Sugerir horários disponíveis' },
    { id: 'request-portfolio', title: 'Solicitar Portfólio', icon: '📂', buttonText: 'Enviar solicitação automática' },
    { id: 'reference-check', title: 'Verificar Referências', icon: '✅', buttonText: 'Iniciar verificação' },
    { id: 'salary-analysis', title: 'Análise Salarial', icon: '💰', buttonText: 'Gerar relatório salarial' }
  ]

  const liaScore = candidate.liaAnalysis?.score || candidate.lia_analysis?.score
  const fitScore = candidate.liaAnalysis?.fitScore || candidate.lia_analysis?.fit_score

  return (
    <div className="h-full bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle flex flex-col transition-[width,height] duration-300 w-full">
      {/* Header */}
      <TooltipProvider delayDuration={200}>
        <div className="p-3 border-b border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-primary">
          {/* Top Row: Avatar + Name/Title + Header Action Buttons (LIA, Expand, Close) */}
          <div className="flex items-start gap-3 mb-1.5">
            {/* Avatar */}
            <Avatar className="w-12 h-12 flex-shrink-0 ring-2 ring-white">
              <AvatarImage src={candidate.avatar_url || candidate.avatar || candidate.photo_url || candidate.photoUrl} alt={candidate.name} />
              <AvatarFallback className="font-semibold text-sm bg-gray-200 lia-text-base">
                {candidate.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>

            {/* Info Section */}
            <div className="flex-1 min-w-0">
              {/* Row 1: Name + Short ID + Seniority + Experience + LGPD */}
              <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
                <h3 className={`${textStyles.title} truncate`}>
                  {candidate.name}
                </h3>
                <Badge className="text-micro px-1.5 py-0 h-4 flex-shrink-0 font-mono font-medium bg-gray-100 lia-text-base border border-lia-border-default">
                  {generateShortId(candidate.name, candidate.id || candidate.candidateId || candidate.pearch_id)}
                </Badge>
                {(candidate.seniority_level || candidate.seniorityLevel) && (
                  <Badge className={badgeStyles.warning}>
                    {candidate.seniority_level || candidate.seniorityLevel}
                  </Badge>
                )}
                {(candidate.years_of_experience !== undefined && candidate.years_of_experience !== null) || 
                 (candidate.yearsOfExperience !== undefined && candidate.yearsOfExperience !== null) ? (
                  <Badge className={badgeStyles.default}>
                    {typeof (candidate.years_of_experience || candidate.yearsOfExperience) === 'number' 
                      ? `${(candidate.years_of_experience || candidate.yearsOfExperience).toFixed(1)} anos` 
                      : `${candidate.years_of_experience || candidate.yearsOfExperience} anos`}
                  </Badge>
                ) : null}
                {(candidate.communication_consent !== undefined || candidate.communicationConsent !== undefined) && (
                  <Badge className={`text-micro px-1.5 py-0 h-4 flex items-center gap-0.5 ${(candidate.communication_consent ?? candidate.communicationConsent) ? 'bg-status-success/10 text-status-success' : 'bg-status-error/10 text-status-error'}`}>
                    {(candidate.communication_consent ?? candidate.communicationConsent) ? <CheckCircle className="w-2.5 h-2.5" /> : <AlertCircle className="w-2.5 h-2.5" />}
                    LGPD
                  </Badge>
                )}
              </div>

              {/* Row 2: Title • Company • Segment */}
              <div className="flex items-center gap-1.5 flex-wrap">
                <p className={`${textStyles.bodySmall} truncate`}>
                  {candidate.position || candidate.title || 'Cargo não informado'}
                </p>
                <span className={`${textStyles.bodySmall} lia-text-secondary`}>•</span>
                <p className={`${textStyles.bodySmall} truncate`}>
                  {candidate.workHistory?.[0]?.company || candidate.current_company || candidate.company || 'Empresa'}
                </p>
                {(candidate.workHistory?.[0]?.industry || candidate.workHistory?.[0]?.segment || candidate.company_segment || candidate.industry) && (
                  <>
                    <span className={`${textStyles.description} lia-text-secondary`}>•</span>
                    <p className={`${textStyles.description} truncate`}>
                      {candidate.workHistory?.[0]?.industry || candidate.workHistory?.[0]?.segment || candidate.company_segment || candidate.industry}
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
                candidate={candidate}
                onTransportToOpinions={handleAnalysisTransport}
              >
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 hover:bg-gray-100 border border-lia-border-default rounded-md flex-shrink-0"
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
                    className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <Expand className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-tertiary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Expandir</TooltipContent>
              </Tooltip>

              {/* Close Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-tertiary" />
              </Button>
            </div>
          </div>

          {/* Row 3: Dates Only - ALIGNED TO LEFT EDGE */}
          {(() => {
            const lastContactedAt = candidate.last_contacted_at || candidate.lastContactedAt
            const updatedAt = candidate.updated_at || candidate.updatedAt
            const createdAt = candidate.created_at || candidate.createdAt
            
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
              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                {createdAt && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="text-micro lia-text-secondary flex items-center gap-0.5 cursor-help">
                        <Calendar className="w-2.5 h-2.5" />
                        {formatDate(createdAt)}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">Data de cadastro</TooltipContent>
                  </Tooltip>
                )}
                {updatedAt && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="text-micro lia-text-secondary flex items-center gap-0.5 cursor-help">
                        <Clock className="w-2.5 h-2.5" />
                        {formatDate(updatedAt)}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">Última atualização</TooltipContent>
                  </Tooltip>
                )}
                {lastContactedAt && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary flex items-center gap-0.5 cursor-help">
                        <MessageSquare className="w-2.5 h-2.5" />
                        {formatDate(lastContactedAt)}
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
                    className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => onSendEmail ? onSendEmail(candidate) : (candidate.email && window.open(`mailto:${candidate.email}`, '_self'))}
                    disabled={!candidate.email && !onSendEmail}
                  >
                    <Mail className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Email</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => {
                      if (onSendWhatsApp) {
                        onSendWhatsApp(candidate)
                      } else if (candidate.phone) {
                        window.open(`https://wa.me/${candidate.phone.replace(/\D/g, '')}`, '_blank')
                      }
                    }}
                    disabled={!candidate.phone && !onSendWhatsApp}
                  >
                    <Phone className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">WhatsApp</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
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
                    className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => onWSIScreening ? onWSIScreening(candidate) : onSendTriagem?.(candidate)}
                  >
                    <ClipboardCheck className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Triagem WSI</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => onAddToVacancy?.(candidate)}
                  >
                    <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
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
                      onToggleFavorite?.(candidate.id)
                      toast({ 
                        title: isFavorite ? "Removido dos favoritos" : "Adicionado aos favoritos",
                        description: isFavorite ? "Candidato removido da lista de favoritos" : "Candidato adicionado à lista de favoritos"
                      })
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
                    className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
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
                    href={candidate.linkedin || candidate.linkedin_url || '#'} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={`p-1 rounded-md transition-colors ${(candidate.linkedin || candidate.linkedin_url) ? 'hover:bg-wedo-cyan/10' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(candidate.linkedin || candidate.linkedin_url) && e.preventDefault()}
                  >
                    <Linkedin className="w-3.5 h-3.5" style={{color: (candidate.linkedin || candidate.linkedin_url) ? 'var(--gray-600)' : 'var(--gray-400)'}} />
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">LinkedIn</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <a 
                    href={candidate.github || candidate.github_url || '#'} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={`p-1 rounded-md transition-colors ${(candidate.github || candidate.github_url) ? 'hover:bg-gray-100 dark:hover:bg-gray-700' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(candidate.github || candidate.github_url) && e.preventDefault()}
                  >
                    <svg className="w-3.5 h-3.5" fill={(candidate.github || candidate.github_url) ? 'var(--gray-950)' : 'var(--gray-400)'} viewBox="0 0 24 24">
                      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">GitHub</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <a 
                    href={candidate.stackoverflow || candidate.stackoverflow_url || '#'} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={`p-1 rounded-md transition-colors ${(candidate.stackoverflow || candidate.stackoverflow_url) ? 'hover:bg-wedo-orange/10' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(candidate.stackoverflow || candidate.stackoverflow_url) && e.preventDefault()}
                  >
                    <svg className="w-3.5 h-3.5" fill={(candidate.stackoverflow || candidate.stackoverflow_url) ? 'var(--gray-600)' : 'var(--gray-400)'} viewBox="0 0 24 24">
                      <path d="M15 21h-10v-2h10v2zm6-11.665l-1.621-9.335-1.993.346 1.62 9.335 1.994-.346zm-5.964 6.937l-9.746-.975-.186 2.016 9.755.879.177-1.92zm.538-2.587l-9.276-2.608-.526 1.954 9.306 2.5.496-1.846zm1.204-2.413l-8.297-4.864-1.029 1.743 8.298 4.865 1.028-1.744zm1.866-1.467l-5.339-7.829-1.672 1.14 5.339 7.829 1.672-1.14zm-2.644 4.195v8h-12v-8h-2v10h16v-10h-2z"/>
                    </svg>
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Stack Overflow</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <a 
                    href={candidate.twitter || candidate.twitter_url || candidate.x_url || '#'} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={`p-1 rounded-md transition-colors ${(candidate.twitter || candidate.twitter_url || candidate.x_url) ? 'hover:bg-gray-100 dark:hover:bg-gray-700' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(candidate.twitter || candidate.twitter_url || candidate.x_url) && e.preventDefault()}
                  >
                    <svg className="w-3.5 h-3.5" fill={(candidate.twitter || candidate.twitter_url || candidate.x_url) ? 'var(--gray-950)' : 'var(--gray-400)'} viewBox="0 0 24 24">
                      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">X (Twitter)</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <a 
                    href={candidate.behance || candidate.behance_url || '#'} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={`p-1 rounded-md transition-colors ${(candidate.behance || candidate.behance_url) ? 'hover:bg-wedo-cyan/10' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(candidate.behance || candidate.behance_url) && e.preventDefault()}
                  >
                    <svg className="w-3.5 h-3.5" fill={(candidate.behance || candidate.behance_url) ? 'var(--gray-600)' : 'var(--gray-400)'} viewBox="0 0 24 24">
                      <path d="M22 7h-7v-2h7v2zm1.726 10c-.442 1.297-2.029 3-5.101 3-3.074 0-5.564-1.729-5.564-5.675 0-3.91 2.325-5.92 5.466-5.92 3.082 0 4.964 1.782 5.375 4.426.078.506.109 1.188.095 2.14h-8.027c.13 3.211 3.483 3.312 4.588 2.029h3.168zm-7.686-4h4.965c-.105-1.547-1.136-2.219-2.477-2.219-1.466 0-2.277.768-2.488 2.219zm-9.574 6.988h-6.466v-14.967h6.953c5.476.081 5.58 5.444 2.72 6.906 3.461 1.26 3.577 8.061-3.207 8.061zm-3.466-8.988h3.584c2.508 0 2.906-3-.312-3h-3.272v3zm3.391 3h-3.391v3.016h3.341c3.055 0 2.868-3.016.05-3.016z"/>
                    </svg>
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Behance</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <a 
                    href={candidate.portfolio || candidate.portfolio_url || '#'} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={`p-1 rounded-md transition-colors ${(candidate.portfolio || candidate.portfolio_url) ? 'hover:bg-gray-100 dark:hover:bg-gray-700' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(candidate.portfolio || candidate.portfolio_url) && e.preventDefault()}
                  >
                    <ExternalLink className={`w-3.5 h-3.5 ${(candidate.portfolio || candidate.portfolio_url) ? 'text-lia-text-secondary dark:text-lia-text-tertiary' : 'text-lia-text-disabled'}`} />
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
              onClick={() => setActiveTab(tab.id as string)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium whitespace-nowrap transition-colors ${
 activeTab === tab.id
                  ? 'border-b-2 border-gray-800 text-lia-text-primary dark:text-lia-text-primary font-semibold'
                  : 'text-lia-text-secondary dark:text-lia-text-tertiary hover:text-lia-text-primary'
              }`}
            >
              <tab.icon className="w-3 h-3" />
              {tab.label}
              {'badge' in tab && tab.badge > 0 && (
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
          <CandidatePreviewProfileTab
            candidate={candidate}
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
            candidate={candidate}
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
            candidate={candidate}
          />
        )}

        {/* Tab Pareceres e Análises */}
        {activeTab === 'opinions' && (
          <div className="p-3 space-y-3">
            {/* Subtabs Header */}
            <div className="flex items-center gap-1 border-b border-lia-border-subtle dark:border-lia-border-subtle pb-2">
              <button
                onClick={() => setOpinionsSubTab('pareceres')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors ${
 opinionsSubTab === 'pareceres'
                    ? 'bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary border-b-2 border-gray-900 dark:border-lia-border-subtle'
 : 'text-lia-text-tertiary hover:text-lia-text-secondary dark:text-lia-text-secondary hover:bg-gray-50'
                }`}
              >
                <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                Pareceres da LIA
                {opinionsHistory.length > 0 && (
                  <Badge className="text-micro px-1.5 py-0 h-4 ml-1 bg-wedo-cyan/15">
                    {opinionsHistory.length}
                  </Badge>
                )}
              </button>
              <button
                onClick={() => setOpinionsSubTab('analises')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors ${
 opinionsSubTab === 'analises'
                    ? 'bg-wedo-purple/10 text-wedo-purple border-b-2 border-wedo-purple/30'
 : 'text-lia-text-tertiary hover:text-lia-text-secondary dark:text-lia-text-secondary hover:bg-gray-50'
                }`}
              >
                <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                Análises
                {savedAnalyses && savedAnalyses.total_analyses > 0 && (
                  <Badge className="text-micro px-1.5 py-0 h-4 ml-1" style={{backgroundColor: 'var(--gray-100)', color: 'var(--wedo-purple)'}}>
                    {savedAnalyses.total_analyses}
                  </Badge>
                )}
              </button>
            </div>
            
            {/* Subtab: Pareceres da LIA */}
            {opinionsSubTab === 'pareceres' && (
              <>
                {/* Loading State */}
                {isLoadingHistory && (
                  <div className="space-y-3">
                    {[1, 2].map((i) => (
                      <div key={i} className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-4 animate-pulse">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="w-8 h-8 bg-gray-200 dark:bg-lia-bg-elevated rounded-full"></div>
                          <div className="flex-1">
                            <div className="w-32 h-4 bg-gray-200 dark:bg-lia-bg-elevated rounded-md mb-1"></div>
                            <div className="w-24 h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="w-full h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                          <div className="w-3/4 h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Empty State */}
                {!isLoadingHistory && opinionsHistory.length === 0 && (
                  <div className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-6 text-center">
                    <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center mx-auto mb-3">
                      <FileText className="w-6 h-6 text-lia-text-disabled" />
                    </div>
                    <p className={`${textStyles.subtitle} mb-1`}>Nenhum parecer disponível</p>
                    <p className={textStyles.description}>
                      Os pareceres serão gerados automaticamente após triagens ou análises da LIA.
                    </p>
                  </div>
                )}
                
                {/* Opinions List - Full History */}
                {!isLoadingHistory && opinionsHistory.length > 0 && (
                  <div className="space-y-3">
                    {opinionsHistory.map((opinion: Record<string, unknown>) => (
                      <div key={opinion.id} className="relative">
                        {!opinion.is_current && (
                          <Badge className="absolute top-2 right-2 text-micro px-1.5 py-0 h-4 bg-gray-100 text-lia-text-tertiary dark:text-lia-text-tertiary z-10">
                            v{opinion.version} - Histórico
                          </Badge>
                        )}
                        <OpinionCard 
                          opinion={opinion}
                          isExpanded={expandedOpinionId === opinion.id}
                          onToggle={() => setExpandedOpinionId(
                            expandedOpinionId === opinion.id ? null : opinion.id
                          )}
                          type={opinion.opinion_type === 'wsi' ? 'wsi' : 'general'}
                          copiedItemId={copiedItemId}
                          onCopyOpinion={handleCopyOpinion}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
            
            {/* Subtab: Análises */}
            {opinionsSubTab === 'analises' && (
              <>
                {/* Loading State */}
                {isLoadingAnalyses && (
                  <div className="space-y-3">
                    {[1, 2].map((i) => (
                      <div key={i} className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-4 animate-pulse">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="w-8 h-8 bg-gray-200 dark:bg-lia-bg-elevated rounded-full"></div>
                          <div className="flex-1">
                            <div className="w-32 h-4 bg-gray-200 dark:bg-lia-bg-elevated rounded-md mb-1"></div>
                            <div className="w-24 h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="w-full h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                          <div className="w-3/4 h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Empty State */}
                {!isLoadingAnalyses && (!savedAnalyses || savedAnalyses.total_analyses === 0) && (
                  <div className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-6 text-center">
                    <div className="w-12 h-12 rounded-full bg-wedo-purple/10 flex items-center justify-center mx-auto mb-3">
                      <Brain className="w-6 h-6 text-wedo-purple" />
                    </div>
                    <p className={`${textStyles.subtitle} mb-1`}>Nenhuma análise disponível</p>
                    <p className={textStyles.description}>
                      Use o ícone 🧠 no header para gerar análises de perfil e salvá-las aqui.
                    </p>
                  </div>
                )}
                
                {/* Analyses List with Expandable Cards */}
                {!isLoadingAnalyses && savedAnalyses && savedAnalyses.total_analyses > 0 && (
                  <div className="space-y-3">
                    {savedAnalyses.analyses.map((analysis: Record<string, unknown>) => {
                      const analysisLabels: Record<string, string> = {
                        'bullet_points': 'Pontos-chave',
                        'short_paragraph': 'Resumo',
                        'detailed_bullets': 'Análise Detalhada'
                      }
                      const isExpanded = expandedAnalysisId === analysis.id
                      
                      return (
                        <div 
                          key={analysis.id} 
                          className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md overflow-hidden hover:transition-shadow"
                        >
                          {/* Card Header - Always Visible */}
                          <div 
                            className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50/50 transition-colors"
                            onClick={() => setExpandedAnalysisId(isExpanded ? null : analysis.id)}
                          >
                            <div className="flex items-center gap-2.5">
                              <div className="w-8 h-8 rounded-full bg-wedo-purple/15 flex items-center justify-center flex-shrink-0">
                                <Brain className="w-4 h-4 text-wedo-purple" />
                              </div>
                              <div className="min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className={`${textStyles.bodySmall} font-medium`}>Análise LIA</span>
                                  <Badge 
                                    className="text-micro px-1.5 py-0 h-4"
                                    style={{backgroundColor: 'var(--gray-100)', color: 'var(--wedo-purple)'}}
                                  >
                                    {analysisLabels[analysis.analysis_type] || analysis.analysis_type}
                                  </Badge>
                                </div>
                                <span className={`${textStyles.caption} lia-text-secondary`}>
                                  {analysis.created_at ? new Date(analysis.created_at).toLocaleDateString('pt-BR', { 
                                    day: '2-digit', 
                                    month: '2-digit', 
                                    year: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  }) : 'Data não disponível'}
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      handleCopyAnalysis(analysis)
                                    }}
                                    className="p-1 hover:bg-gray-100 rounded-md transition-colors"
                                  >
                                    {copiedItemId === `analysis-${analysis.id}` ? (
                                      <Check className="w-3.5 h-3.5 text-status-success" />
                                    ) : (
                                      <Copy className="w-3.5 h-3.5 text-lia-text-disabled hover:text-lia-text-secondary dark:text-lia-text-tertiary" />
                                    )}
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent side="top" className="text-micro">Copiar análise</TooltipContent>
                              </Tooltip>
                              <ChevronDown className={`w-4 h-4 lia-text-secondary transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                            </div>
                          </div>
                          
                          {/* Card Content - Expandable */}
                          {isExpanded && (
                            <div className="px-3 pb-3 border-t border-gray-50">
                              <div className={`${textStyles.description} text-lia-text-primary dark:text-lia-text-primary leading-relaxed whitespace-pre-wrap bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3 mt-2`}>
                                {cleanTextForCopy(analysis.content)}
                              </div>
                              {/* Delete button */}
                              <div className="flex justify-end mt-2">
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        setAnalysisToDelete(analysis)
                                      }}
                                      className="p-1.5 hover:bg-status-error/10 rounded-md transition-colors group"
                                    >
                                      <Trash2 className="w-4 h-4 lia-text-secondary group-hover:text-status-error" />
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent side="top" className="text-micro">Remover análise</TooltipContent>
                                </Tooltip>
                              </div>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Modal Fale com a LIA - Estilo padronizado */}
      {/* Chat da LIA - Individual */}
      <LiaChatModal
        isOpen={showLiaModal}
        onClose={() => setShowLiaModal(false)}
        candidate={candidate}
        liaActions={liaActions}
        chatMessages={liaChatMessages}
        isLiaChatLoading={isLiaChatLoading}
        liaConversation={liaConversation}
        onConversationChange={setLiaConversation}
        onSendMessage={sendLiaMessage}
        onContact={onContact}
        onSendEmail={onSendEmail}
        onSchedule={onSchedule}
        onScheduleInterview={onScheduleInterview}
        onSendAgendamento={onSendAgendamento}
        onAddToList={onAddToList}
        onAddToVacancy={onAddToVacancy}
      />

      
      {/* AlertDialog para confirmação de novo parecer */}
      <AlertDialog open={showUpdateOpinionAlert} onOpenChange={setShowUpdateOpinionAlert}>
        <AlertDialogContent className="bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
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
              className="bg-gray-900 hover:bg-gray-800 text-xs text-white"
            >
              Gerar Novo Parecer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* AlertDialog para confirmação de exclusão de análise */}
      <AlertDialog open={!!analysisToDelete} onOpenChange={(open: boolean) => !open && setAnalysisToDelete(null)}>
        <AlertDialogContent className="bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
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
        candidateName={candidate?.name}
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
          jobTitle={candidate?.job_title || candidate?.jobTitle}
          candidateName={candidate?.name}
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
        <DISCAssessmentModal
          isOpen={discModalOpen}
          onClose={() => {
            setDiscModalOpen(false)
            setDiscModalData(null)
          }}
          candidate={candidate}
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
