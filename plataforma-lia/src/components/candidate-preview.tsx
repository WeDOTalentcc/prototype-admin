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

interface CandidatePreviewProps {
  candidate: any
  isOpen: boolean
  onClose: () => void
  isMaximized?: boolean
  onToggleMaximize?: () => void
  candidates?: any[]
  currentIndex?: number
  onNavigateCandidate?: (index: number) => void
  onOpenFullPage?: (candidate: any) => void
  onScheduleInterview?: (candidate: any) => void
  onAddToVacancy?: (candidate: any) => void
  onToggleFavorite?: (candidateId: string) => void
  onWSIScreening?: (candidate: any) => void
  onOpenTriagemDetails?: (candidate: any) => void
  isFavorite?: boolean
  onSendEmail?: (candidate: any) => void
  onSendWhatsApp?: (candidate: any) => void  
  onSendTriagem?: (candidate: any) => void
  onSendAgendamento?: (candidate: any) => void
  onSendFeedback?: (candidate: any) => void
  onContact?: (candidate: any, channel?: 'email' | 'whatsapp') => void
  onSchedule?: (candidate: any) => void
  onAddToList?: (candidate: any) => void
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
    <div className="h-full bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 flex flex-col transition-all duration-300 w-full">
      {/* Header */}
      <TooltipProvider delayDuration={200}>
        <div className="p-3 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-900">
          {/* Top Row: Avatar + Name/Title + Header Action Buttons (LIA, Expand, Close) */}
          <div className="flex items-start gap-3 mb-1.5">
            {/* Avatar */}
            <Avatar className="w-12 h-12 flex-shrink-0 ring-2 ring-white">
              <AvatarImage src={candidate.avatar_url || candidate.avatar || candidate.photo_url || candidate.photoUrl} alt={candidate.name} />
              <AvatarFallback className="font-semibold text-sm bg-gray-200 text-gray-700">
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
                <Badge className="text-micro px-1.5 py-0 h-4 flex-shrink-0 font-mono font-medium bg-gray-100 text-gray-600 border border-gray-300">
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
                <span className={`${textStyles.bodySmall} text-gray-400`}>•</span>
                <p className={`${textStyles.bodySmall} truncate`}>
                  {candidate.workHistory?.[0]?.company || candidate.current_company || candidate.company || 'Empresa'}
                </p>
                {(candidate.workHistory?.[0]?.industry || candidate.workHistory?.[0]?.segment || candidate.company_segment || candidate.industry) && (
                  <>
                    <span className={`${textStyles.description} text-gray-400`}>•</span>
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
                  className="h-8 w-8 p-0 hover:bg-gray-100 border border-gray-300 rounded-md flex-shrink-0"
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
                    <Expand className="w-4 h-4 text-gray-500 dark:text-gray-400" />
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
                <X className="w-4 h-4 text-gray-500 dark:text-gray-400" />
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
                      <span className="text-micro text-gray-400 flex items-center gap-0.5 cursor-help">
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
                      <span className="text-micro text-gray-400 flex items-center gap-0.5 cursor-help">
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
                      <span className="text-micro text-gray-500 dark:text-gray-400 flex items-center gap-0.5 cursor-help">
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
                    <Mail className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
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
                    <Phone className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
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
                    <ClipboardCheck className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
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
                    <Briefcase className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
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
              <span className="text-gray-200 mx-0.5">|</span>

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
                    <ExternalLink className={`w-3.5 h-3.5 ${(candidate.portfolio || candidate.portfolio_url) ? 'text-gray-600 dark:text-gray-400' : 'text-gray-400'}`} />
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Portfolio</TooltipContent>
              </Tooltip>
            </div>

          </div>
        </div>
      </TooltipProvider>

      {/* Tabs */}
      <div className="border-b border-gray-100 dark:border-gray-700 flex items-center">
        <div className="flex overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 border-gray-800 text-gray-800 dark:text-gray-200 font-semibold'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-800'
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
          <div className="p-3 space-y-3">
            {/* Experience Highlight - AI-generated summary */}
            <ExperienceHighlightCard candidate={candidate} companyId="demo_company" />
            
            {/* Parecer LIA - Mostrado apenas no contexto de vaga (jobId presente) */}
            {jobId && (opinionsData?.current_general_opinion || (opinionsData?.vacancy_opinions && opinionsData.vacancy_opinions.length > 0)) && (
              <Card className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700">
                <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <div className="p-0.5 rounded-md bg-gray-100 dark:bg-gray-800">
                        <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                      </div>
                      <CardTitle className={`${textStyles.label} text-gray-600 dark:text-gray-400`}>Parecer LIA</CardTitle>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className={`flex items-center gap-1 ${textStyles.caption}`}>
                        <Clock className="w-3 h-3" />
                        <span>{formatAnalysisDate(
                          opinionsData?.current_general_opinion?.created_at 
                            ? new Date(opinionsData.current_general_opinion.created_at)
                            : opinionsData?.vacancy_opinions?.[0]?.created_at
                              ? new Date(opinionsData.vacancy_opinions[0].created_at)
                              : lastAnalysisDate
                        )}</span>
                      </div>
                      <Button
                        onClick={handleAnalyzeWithLia}
                        disabled={isAnalyzingWithLia}
                        size="sm"
                        variant="ghost"
                        className={`gap-1 px-2 py-1 ${textStyles.caption} h-6 hover:bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 transition-all disabled:opacity-50`}
                      >
                        {isAnalyzingWithLia ? (
                          <>
                            <div className="w-3 h-3 border-2 border-gray-900 dark:border-gray-50 border-t-transparent rounded-full animate-spin" />
                            <span>Analisando...</span>
                          </>
                        ) : (
                          <>
                            <Brain className="w-3 h-3 text-wedo-cyan" />
                            <span>Atualizar</span>
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-2.5 pb-2.5 px-2.5">
                  {(() => {
                    const opinion = opinionsData?.current_general_opinion || opinionsData?.vacancy_opinions?.[0]
                    if (!opinion) return null
                    
                    const isWsiOpinion = opinion.opinion_type === 'wsi' || opinion.wsi_score !== null
                    const displayScore = isWsiOpinion ? opinion.wsi_score : opinion.score
                    
                    const getScoreColor = (score: number | null, isWsi: boolean = false) => {
                      if (score === null || score === undefined) return 'text-gray-600'
                      if (isWsi) {
                        return score >= 4.0 ? 'text-status-success' : score >= 3.0 ? 'text-status-warning' : 'text-status-error'
                      }
                      return score >= 80 ? 'text-status-success' : score >= 60 ? 'text-status-warning' : 'text-status-error'
                    }
                    
                    return (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          {displayScore !== null && displayScore !== undefined && (
                            <span className={`${textStyles.label} ${getScoreColor(displayScore, isWsiOpinion)}`}>
                              {isWsiOpinion ? `WSI: ${displayScore.toFixed(1)}/5` : `Score: ${Math.round(displayScore)}/100`}
                            </span>
                          )}
                          {opinion.archetype && (
                            <>
                              <span className="text-gray-300">•</span>
                              <Badge className={badgeStyles.default}>{opinion.archetype}</Badge>
                            </>
                          )}
                        </div>
                        {opinion.summary && (
                          <p className={`${textStyles.caption} text-gray-600 dark:text-gray-400 leading-relaxed`}>
                            {opinion.summary}
                          </p>
                        )}
                      </div>
                    )
                  })()}
                </CardContent>
              </Card>
            )}
            
            {/* Loading state for opinions - apenas no contexto de vaga */}
            {jobId && isLoadingOpinions && !opinionsData && (
              <div className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 rounded-md p-3 animate-pulse">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-4 h-4 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                  <div className="w-24 h-4 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                </div>
                <div className="space-y-1.5">
                  <div className="w-32 h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                  <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                </div>
              </div>
            )}
            
            {/* Mapa de Skills - Agrupado por categoria com origem diferenciada */}
            {(() => {
              const allSkills = [...(candidate.skills || []), ...(candidate.technical_skills || [])]
              const softSkillsList = candidate.soft_skills || []
              
              // LinkedIn Expertise
              const expertise = candidate.expertise ?? candidate.areas_expertise ?? candidate.areasOfExpertise
              let expertiseList: string[] = []
              if (Array.isArray(expertise)) {
                expertiseList = expertise
              } else if (typeof expertise === 'string') {
                try {
                  const parsed = JSON.parse(expertise)
                  expertiseList = Array.isArray(parsed) ? parsed : []
                } catch {
                  expertiseList = expertise.includes(',') ? expertise.split(',').map((s: string) => s.trim()) : []
                }
              }
              
              // Interests and Tags (moved from header)
              const interests = Array.isArray(candidate.interests) ? candidate.interests : []
              const tags = Array.isArray(candidate.tags) ? candidate.tags : []
              
              const totalItems = allSkills.length + softSkillsList.length + expertiseList.length + interests.length + tags.length
              if (totalItems === 0) return null
              
              // Categorização inteligente de skills - Design monocromático
              const skillCategories: Record<string, { label: string, color: string, bgColor: string, skills: string[] }> = {
                backend: { label: 'Backend', bgColor: 'bg-gray-100 dark:bg-gray-800', skills: [] },
                frontend: { label: 'Frontend', bgColor: 'bg-gray-100 dark:bg-gray-800', skills: [] },
                data: { label: 'Dados & Analytics', bgColor: 'bg-gray-100 dark:bg-gray-800', skills: [] },
                devops: { label: 'DevOps & Cloud', bgColor: 'bg-gray-100 dark:bg-gray-800', skills: [] },
                design: { label: 'Design', bgColor: 'bg-gray-100 dark:bg-gray-800', skills: [] },
                mobile: { label: 'Mobile', bgColor: 'bg-gray-100 dark:bg-gray-800', skills: [] },
                other: { label: 'Outras', bgColor: 'bg-gray-100 dark:bg-gray-800', skills: [] }
              }
              
              const backendKeywords = ['java', 'spring', 'node', 'python', 'django', 'flask', 'fastapi', 'ruby', 'rails', 'php', 'laravel', '.net', 'c#', 'go', 'golang', 'rust', 'express', 'nestjs', 'graphql', 'rest', 'api', 'microservices', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'kafka', 'rabbitmq']
              const frontendKeywords = ['react', 'angular', 'vue', 'javascript', 'typescript', 'html', 'css', 'sass', 'tailwind', 'next', 'nuxt', 'svelte', 'redux', 'webpack', 'vite', 'jquery', 'bootstrap']
              const dataKeywords = ['python', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'machine learning', 'ml', 'ai', 'data science', 'sql', 'etl', 'spark', 'hadoop', 'tableau', 'power bi', 'analytics', 'bigquery', 'databricks', 'airflow', 'dbt']
              const devopsKeywords = ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'jenkins', 'gitlab', 'github actions', 'ci/cd', 'linux', 'devops', 'sre', 'monitoring', 'grafana', 'prometheus', 'elastic']
              const designKeywords = ['figma', 'sketch', 'adobe', 'photoshop', 'illustrator', 'xd', 'ui', 'ux', 'design', 'prototyping', 'wireframe', 'invision', 'zeplin']
              const mobileKeywords = ['ios', 'android', 'swift', 'kotlin', 'react native', 'flutter', 'xamarin', 'mobile', 'objective-c']
              
              allSkills.forEach((skill: string) => {
                const skillLower = skill.toLowerCase()
                if (backendKeywords.some(k => skillLower.includes(k))) {
                  skillCategories.backend.skills.push(skill)
                } else if (frontendKeywords.some(k => skillLower.includes(k))) {
                  skillCategories.frontend.skills.push(skill)
                } else if (dataKeywords.some(k => skillLower.includes(k))) {
                  skillCategories.data.skills.push(skill)
                } else if (devopsKeywords.some(k => skillLower.includes(k))) {
                  skillCategories.devops.skills.push(skill)
                } else if (designKeywords.some(k => skillLower.includes(k))) {
                  skillCategories.design.skills.push(skill)
                } else if (mobileKeywords.some(k => skillLower.includes(k))) {
                  skillCategories.mobile.skills.push(skill)
                } else {
                  skillCategories.other.skills.push(skill)
                }
              })
              
              const categoriesWithSkills = Object.entries(skillCategories).filter(([_, cat]) => cat.skills.length > 0)
              
              return (
                <Card className="border-gray-100 dark:border-gray-700">
                  <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-gray-900">
                    <div className="flex items-center gap-1.5">
                      <Code className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                      <CardTitle className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                        Mapa de Skills
                      </CardTitle>
                      <Badge className="text-micro px-1 py-0 h-4 bg-gray-200 text-gray-800 dark:text-gray-200">
                        {totalItems} itens
                      </Badge>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="text-gray-400 cursor-help text-micro">ⓘ</span>
                        </TooltipTrigger>
                        <TooltipContent side="right" className="text-xs max-w-xs">
                          <div className="space-y-1">
                            <p><span className="inline-block w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 mr-1"></span> Skills do CV</p>
                            <p><span className="inline-block w-2 h-2 rounded-full mr-1 bg-gray-900"></span> Expertise do LinkedIn</p>
                            <p><span className="inline-block w-2 h-2 rounded-full mr-1 bg-gray-900"></span> Soft Skills (LIA)</p>
                            <p><span className="inline-block w-2 h-2 rounded-full bg-wedo-magenta mr-1"></span> Interesses</p>
                            <p><span className="inline-block w-2 h-2 rounded-full mr-1 bg-gray-900"></span> Tags</p>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    </div>
                  </CardHeader>
                  <CardContent className="p-2.5 space-y-2">
                    {/* Skills do CV por categoria */}
                    {categoriesWithSkills.map(([key, category]) => (
                      <div key={key}>
                        <div className="flex items-center gap-1.5 mb-1">
                          <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500" />
                          <span className={textStyles.label}>{category.label}</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="text-gray-300 cursor-help text-micro">ⓘ</span>
                            </TooltipTrigger>
                            <TooltipContent side="right" className="text-xs">
                              Extraído do currículo (CV)
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <div className="flex flex-wrap gap-1 ml-3.5">
                          {category.skills.map((skill: string, idx: number) => (
                            <Badge 
                              key={idx} 
                              className="text-micro px-1.5 py-0 bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 border-0"
                            >
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                    
                    {/* Soft Skills - Inferidas pela LIA */}
                    {softSkillsList.length > 0 && (
                      <div>
                        <div className="flex items-center gap-1.5 mb-1">
                          <Brain className="w-3 h-3 text-wedo-cyan" />
                          <span className={`${textStyles.label} text-gray-700`}>Soft Skills</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="cursor-help text-micro text-gray-700">ⓘ</span>
                            </TooltipTrigger>
                            <TooltipContent side="right" className="text-xs">
                              Competências comportamentais inferidas pela LIA
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <div className="flex flex-wrap gap-1 ml-3.5">
                          {softSkillsList.map((skill: string, idx: number) => (
                            <Badge 
                              key={idx} 
                              className="text-micro px-1.5 py-0 border-0 bg-wedo-cyan/15 text-gray-800"
                            >
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Expertise do LinkedIn */}
                    {expertiseList.length > 0 && (
                      <div>
                        <div className="flex items-center gap-1.5 mb-1">
                          <Linkedin className="w-3 h-3 text-gray-600" />
                          <span className={`${textStyles.label} text-gray-700 dark:text-gray-300`}>Expertise LinkedIn</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="cursor-help text-micro text-gray-400 dark:text-gray-500">ⓘ</span>
                            </TooltipTrigger>
                            <TooltipContent side="right" className="text-xs">
                              Áreas de expertise extraídas do perfil LinkedIn
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <div className="flex flex-wrap gap-1 ml-3.5">
                          {expertiseList.map((item: string, idx: number) => (
                            <Badge
                              key={idx}
                              className="text-micro px-1.5 py-0 border-0 bg-gray-200/30 text-gray-800"
                            >
                              {item}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Interesses */}
                    {interests.length > 0 && (
                      <div>
                        <div className="flex items-center gap-1.5 mb-1">
                          <Heart className="w-3 h-3 text-wedo-magenta" />
                          <span className={`${textStyles.label} text-wedo-magenta`}>Interesses</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="text-wedo-magenta cursor-help text-micro">ⓘ</span>
                            </TooltipTrigger>
                            <TooltipContent side="right" className="text-xs">
                              Áreas de interesse declaradas pelo candidato
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <div className="flex flex-wrap gap-1 ml-3.5">
                          {interests.map((interest: string, idx: number) => (
                            <Badge 
                              key={idx} 
                              className="text-micro px-1.5 py-0 bg-wedo-magenta/10 text-wedo-magenta border-0"
                            >
                              {interest}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Tags */}
                    {tags.length > 0 && (
                      <div>
                        <div className="flex items-center gap-1.5 mb-1">
                          <Tag className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                          <span className={`${textStyles.label} text-gray-700 dark:text-gray-300`}>Tags</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="cursor-help text-micro text-gray-400 dark:text-gray-500">ⓘ</span>
                            </TooltipTrigger>
                            <TooltipContent side="right" className="text-xs">
                              Tags adicionadas pelo recrutador ou sistema
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <div className="flex flex-wrap gap-1 ml-3.5">
                          {tags.map((tag: string, idx: number) => (
                            <Badge
                              key={idx}
                              className="text-micro px-1.5 py-0 border-0 bg-gray-200/30 text-gray-800"
                            >
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )
            })()}

            {/* Indicadores Pearch - Badges compactas com dados Pearch */}
            {(() => {
              const isOpenToWork = candidate.is_opentowork ?? candidate.is_open_to_work ?? candidate.isOpenToWork
              const isTopUniversity = candidate.is_top_universities ?? candidate.top_universities ?? candidate.isTopUniversities
              const isDecisionMaker = candidate.is_decision_maker ?? candidate.isDecisionMaker
              const isBlacklisted = candidate.is_blacklisted ?? candidate.blacklist_status ?? candidate.isBlacklisted
              const blacklistReason = candidate.blacklist_reason ?? candidate.motivo_lista_negra ?? candidate.blacklistReason
              
              // Guard: só mostra se houver algum indicador booleano verdadeiro
              const hasAnyIndicator = isOpenToWork === true || isTopUniversity === true || isDecisionMaker === true || isBlacklisted === true
              
              if (!hasAnyIndicator) return null
              
              return (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {isOpenToWork === true && (
                    <Badge variant="outline" className="text-micro px-2 py-0.5 h-5 bg-status-success/10 text-status-success border-status-success/30 dark:bg-status-success/20 dark:text-status-success dark:border-status-success/30 flex items-center gap-1">
                      <Globe className="w-3 h-3 text-status-success dark:text-status-success" />
                      Open to Work
                    </Badge>
                  )}
                  {isTopUniversity === true && (
                    <Badge variant="outline" className="text-micro px-2 py-0.5 h-5 bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30 flex items-center gap-1">
                      🎓 Top University
                    </Badge>
                  )}
                  {isDecisionMaker === true && (
 <Badge variant="outline" className="text-micro px-2 py-0.5 h-5 bg-gray-100 text-gray-700 dark:bg-gray-800 border-gray-200 dark:border-gray-700 flex items-center gap-1">
                      👔 Decision Maker
                    </Badge>
                  )}
                  {isBlacklisted === true && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Badge variant="outline" className="text-micro px-2 py-0.5 h-5 bg-status-error/10 text-status-error border-status-error/30 flex items-center gap-1 cursor-help">
                          ⚠️ LCNU
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent side="bottom" className="text-xs max-w-xs">
                        <p className="font-medium mb-1">Lista de Candidatos Não Utilizáveis</p>
                        {blacklistReason && <p>{blacklistReason}</p>}
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              )
            })()}

            {/* Perfil LinkedIn - Headline, seguidores (expertise movida para Mapa de Skills) */}
            {(() => {
              const headline = candidate.headline ?? candidate.linkedinHeadline
              const estimatedAge = candidate.estimated_age ?? candidate.estimatedAge ?? candidate.age
              const followersCount = candidate.linkedin_followers_count ?? candidate.followers_count ?? candidate.linkedinFollowersCount
              const connectionsCount = candidate.linkedin_connections_count ?? candidate.connections_count ?? candidate.linkedinConnectionsCount
              
              const hasLinkedInData = headline || estimatedAge || followersCount || connectionsCount
              
              if (!hasLinkedInData) return null
              
              return (
                <Card className="border-gray-100 dark:border-gray-700">
                  <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-gray-900">
                    <div className="flex items-center gap-1.5">
                      <Linkedin className="w-3.5 h-3.5 text-gray-600" />
                      <CardTitle className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                        Perfil LinkedIn
                      </CardTitle>
                      <Globe className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                    </div>
                  </CardHeader>
                  <CardContent className="p-2.5 space-y-2">
                    {headline && (
                      <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed">
                        {headline}
                      </p>
                    )}
                    
                    <div className="flex items-center gap-3 flex-wrap">
                      {estimatedAge && (
                        <div className="flex items-center gap-1">
                          <span className={textStyles.caption}>Idade estimada:</span>
                          <span className={`${textStyles.bodySmall} font-medium`}>{estimatedAge} anos</span>
                        </div>
                      )}
                      {followersCount !== undefined && followersCount !== null && (
                        <div className="flex items-center gap-1">
                          <Users className="w-3 h-3 text-gray-400 dark:text-gray-500" />
                          <span className={`${textStyles.bodySmall} font-medium`}>{followersCount.toLocaleString('pt-BR')}</span>
                          <span className={textStyles.caption}>seguidores</span>
                        </div>
                      )}
                      {connectionsCount !== undefined && connectionsCount !== null && (
                        <div className="flex items-center gap-1">
                          <UserPlus className="w-3 h-3 text-gray-400 dark:text-gray-500" />
                          <span className={`${textStyles.bodySmall} font-medium`}>{connectionsCount >= 500 ? '500+' : connectionsCount}</span>
                          <span className={textStyles.caption}>conexões</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })()}

            {/* 1. Experiência Profissional - Sempre aparece */}
            <Card className="border-gray-100 dark:border-gray-700">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-gray-900">
                <div className="flex items-center gap-1.5">
                  <Briefcase className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                  <CardTitle className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                    Experiência Profissional
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5 space-y-2.5">
                {((candidate.workHistory?.length > 0) || (candidate.work_history?.length > 0) || (candidate.experiences?.length > 0) || (candidate.additional_data?.work_history?.length > 0) || (candidate.additional_data?.experiences?.length > 0)) ? (
                  <div className="space-y-2.5">
                    {(candidate.workHistory || candidate.work_history || candidate.experiences || candidate.additional_data?.work_history || candidate.additional_data?.experiences || []).map((exp: any, index: number) => {
                      const title = exp.title || exp.position || exp.role || ''
                      const company = exp.company || exp.company_name || exp.organization || ''
                      const location = exp.location || exp.city || ''
                      const startDate = exp.start_date || exp.startDate || ''
                      const endDate = exp.end_date || exp.endDate || exp.current ? 'Atual' : ''
                      const description = exp.description || exp.responsibilities || ''
                      const descriptionList = Array.isArray(description) ? description : (description ? [description] : [])
                      const achievements = exp.achievements || exp.realizacoes || exp.accomplishments || []
                      const achievementsList = Array.isArray(achievements) ? achievements : (achievements ? [achievements] : [])
                      
                      const industries = exp.industries || exp.industry || exp.segment || exp.segmento || []
                      const industriesList = Array.isArray(industries) ? industries : (industries ? [industries] : [])
                      const technologies = exp.technologies || exp.tech_stack || exp.skills || []
                      const technologiesList = Array.isArray(technologies) ? technologies : []
                      const companySize = exp.company_size || exp.company_size_range || exp.porte || null
                      const isStartup = exp.is_startup || exp.startup
                      
                      // Enhanced company metadata
                      const companyLogo = exp.company_logo || exp.logo_url || null
                      const companyDomain = exp.company_domain || exp.domain || null
                      const companySector = exp.sector || exp.company_sector || null
                      const companySegment = exp.segment || exp.market_segment || null
                      const specialties = exp.specialties || exp.company_specialties || []
                      const specialtiesList = Array.isArray(specialties) ? specialties : (specialties ? [specialties] : [])
                      const keywords = exp.keywords || exp.company_keywords || []
                      const keywordsList = Array.isArray(keywords) ? keywords : (keywords ? [keywords] : [])
                      
                      // Calculate duration
                      let durationYears = exp.duration_years || null
                      if (!durationYears && startDate) {
                        try {
                          const start = new Date(startDate)
                          const end = endDate && endDate !== 'Atual' ? new Date(endDate) : new Date()
                          const diffMs = end.getTime() - start.getTime()
                          durationYears = Math.round((diffMs / (1000 * 60 * 60 * 24 * 365)) * 10) / 10
                        } catch { /* ignore */ }
                      }
                      
                      const formatDate = (dateStr: string) => {
                        if (!dateStr || dateStr === 'Atual') return dateStr
                        try {
                          return new Date(dateStr).toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' })
                        } catch {
                          return dateStr
                        }
                      }
                      
                      return (
                        <div key={index} className={`border-l-2 ${index === 0 ? 'border-gray-700' : 'border-gray-300 dark:border-gray-600'} pl-3`}>
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <div>
                              <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200">{title || 'Cargo não informado'}</h5>
                              <p className="text-xs text-gray-600 dark:text-gray-400">
                                {company || 'Empresa não informada'}
                                {location && ` • ${location}`}
                                {durationYears && durationYears > 0 && <span className="text-gray-400 ml-1">({durationYears.toFixed(1)} anos)</span>}
                              </p>
                            </div>
                            {(startDate || endDate) && (
                              <span className="text-micro text-gray-500 dark:text-gray-400 whitespace-nowrap">
                                {formatDate(startDate)}{startDate && endDate ? ' - ' : ''}{formatDate(endDate)}
                              </span>
                            )}
                          </div>
                          
                          {/* Metadata Row: Industries, Company Size */}
                          <div className="flex flex-wrap gap-1.5 mb-2">
                            {industriesList.slice(0, 2).map((ind: string, idx: number) => (
 <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro bg-gray-100 text-gray-700 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                                <Building className="w-2.5 h-2.5 mr-0.5" />
                                {ind}
                              </span>
                            ))}
                            {isStartup && (
                              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-status-success/10 text-status-success border border-status-success/30">
                                🚀 Startup
                              </span>
                            )}
                            {companySize && (
                              <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-micro bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-100 dark:border-gray-700">
                                <Users className="w-2.5 h-2.5" />
                                {companySize}
                              </span>
                            )}
                          </div>

                          {/* Technologies */}
                          {technologiesList.length > 0 && (
                            <div className="flex flex-wrap gap-1 mb-2">
                              <span className="text-micro text-gray-400 flex items-center gap-0.5">
                                <Code className="w-2.5 h-2.5" />
                                Stack:
                              </span>
                              {technologiesList.slice(0, 6).map((tech: string, idx: number) => (
                                <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-gray-100 text-gray-800 dark:text-gray-200">
                                  {tech}
                                </span>
                              ))}
                              {technologiesList.length > 6 && (
                                <span className="text-micro text-gray-400 dark:text-gray-500">+{technologiesList.length - 6}</span>
                              )}
                            </div>
                          )}
                          
                          {/* Description */}
                          {descriptionList.length > 0 && (
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{descriptionList[0]}</p>
                          )}
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <p className={`${textStyles.description} italic`}>Não informado</p>
                )}
              </CardContent>
            </Card>

            {/* 2. Formação Acadêmica - Sempre aparece */}
            <Card className="border-gray-100 dark:border-gray-700">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-gray-900">
                <div className="flex items-center gap-1.5">
                  <GraduationCap className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                  <CardTitle className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                    Formação Acadêmica
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5 space-y-2">
                {candidate.education && candidate.education.length > 0 ? (
                  candidate.education.map((edu: any, index: number) => (
                    <div key={index} className={`flex items-start justify-between gap-2 ${index < candidate.education.length - 1 ? 'pb-2 border-b border-gray-100' : ''}`}>
                      <div className="min-w-0 flex-1">
                        <h5 className={textStyles.label}>
                          {edu.degree || edu.title || 'Formação'}{edu.field_of_study || edu.fieldOfStudy ? ` em ${edu.field_of_study || edu.fieldOfStudy}` : ''}
                        </h5>
                        <p className={textStyles.bodySmall}>
                          {edu.school || edu.institution || 'Instituição não informada'}
                        </p>
                      </div>
                      <span className="text-xs text-gray-800 dark:text-gray-200 flex-shrink-0">
                        {edu.start_date || edu.startDate || ''}{(edu.start_date || edu.startDate) && (edu.end_date || edu.endDate) ? ' - ' : ''}{edu.end_date || edu.endDate || ''}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className={`${textStyles.description} italic`}>Não informado</p>
                )}
              </CardContent>
            </Card>

            {/* 3. Cursos e Certificações - Sempre aparece */}
            <Card className="border-gray-100 dark:border-gray-700">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-gray-900">
                <div className="flex items-center gap-1.5">
                  <Award className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                  <CardTitle className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                    Cursos e Certificações
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5 space-y-2">
                {candidate.certifications && candidate.certifications.length > 0 ? (
                  candidate.certifications.map((cert: any, index: number) => {
                    const certName = typeof cert === 'string' ? cert : (cert.name || cert.title || 'Certificação')
                    const certIssuer = typeof cert === 'object' ? (cert.issuer || cert.organization || '') : ''
                    const certDate = typeof cert === 'object' ? (cert.date || cert.year || '') : ''
                    return (
                      <div key={index} className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <h5 className={`${textStyles.label} truncate`}>
                            {certName}
                          </h5>
                          {certIssuer && <p className={textStyles.bodySmall}>{certIssuer}</p>}
                        </div>
                        {certDate && <span className="text-xs text-gray-800 dark:text-gray-200 flex-shrink-0">{certDate}</span>}
                      </div>
                    )
                  })
                ) : (
                  <p className={`${textStyles.description} italic`}>Não informado</p>
                )}
              </CardContent>
            </Card>

            {/* 4. Idiomas - Sempre aparece */}
            <Card className="border-gray-100 dark:border-gray-700">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-gray-900">
                <div className="flex items-center gap-1.5">
                  <Languages className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                  <CardTitle className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                    Idiomas
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5 space-y-1.5">
                {languagesData.length > 0 ? (
                  languagesData.map((lang, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className={`${textStyles.bodySmall} font-medium`}>
                        {lang.language}
                      </span>
                      {lang.proficiency && (
                        <Badge className="text-xs px-1.5 py-0 h-4 bg-gray-200 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-600 font-semibold">
                          {lang.proficiency}
                        </Badge>
                      )}
                    </div>
                  ))
                ) : (
                  <p className={`${textStyles.description} italic`}>Não informado</p>
                )}
              </CardContent>
            </Card>

            {/* 5. Remuneração e Benefícios - Sempre aparece */}
            <Card className="border-gray-100 dark:border-gray-700 col-span-2">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-gray-900">
                <div className="flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                  <CardTitle className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                    Remuneração
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5">
                {hasSalaryData() ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className={textStyles.bodySmall}>Salário Atual</span>
                      <span className={textStyles.label}>
                        {formatCurrency(candidate.current_salary || candidate.currentSalary, candidate.salary_currency || candidate.salaryCurrency || 'BRL')}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className={textStyles.bodySmall}>Pretensão Salarial</span>
                      <span className={textStyles.label}>
                        {(candidate.desired_salary_min || candidate.desiredSalaryMin) && (candidate.desired_salary_max || candidate.desiredSalaryMax)
                          ? `${formatCurrency(candidate.desired_salary_min || candidate.desiredSalaryMin)} - ${formatCurrency(candidate.desired_salary_max || candidate.desiredSalaryMax)}`
                          : formatCurrency(candidate.desired_salary_min || candidate.desiredSalaryMin || candidate.desired_salary_max || candidate.desiredSalaryMax)
                        }
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className={textStyles.bodySmall}>Expectativa CLT</span>
                      <span className={textStyles.label}>
                        {formatCurrency(candidate.salary_expectation_clt || candidate.salaryExpectationClt)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className={textStyles.bodySmall}>Expectativa PJ</span>
                      <span className={textStyles.label}>
                        {formatCurrency(candidate.salary_expectation_pj || candidate.salaryExpectationPj)}
                      </span>
                    </div>
                    {(candidate.salary_expectation_freelance || candidate.salaryExpectationFreelance) && (
                      <div className="flex items-center justify-between">
                        <span className={textStyles.bodySmall}>Expectativa Freelance</span>
                        <span className={textStyles.label}>
                          {formatCurrency(candidate.salary_expectation_freelance || candidate.salaryExpectationFreelance)}
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className={`${textStyles.description} italic`}>Não informado</p>
                )}
              </CardContent>
            </Card>

            {/* 6. Detalhes Adicionais e Preferências */}
            <Card className="border-gray-100 dark:border-gray-700">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-gray-900">
                <div className="flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                  <CardTitle className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                    Preferências e Dados Pessoais
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5 space-y-2">
                {/* Gênero */}
                {candidate.gender && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Gênero</span>
                    <Badge className={badgeStyles.default}>
                      {candidate.gender}
                    </Badge>
                  </div>
                )}
                {/* Modelo de Trabalho */}
                {(candidate.work_model_preference || candidate.workModelPreference || candidate.workModel) && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Modelo de Trabalho</span>
                    <Badge className={badgeStyles.default}>
                      {candidate.work_model_preference || candidate.workModelPreference || candidate.workModel}
                    </Badge>
                  </div>
                )}
                {/* Tipo de Contrato */}
                {(candidate.contract_type_preference || candidate.contractTypePreference || candidate.contractType) && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Tipo de Contrato</span>
                    <Badge className={badgeStyles.default}>
                      {candidate.contract_type_preference || candidate.contractTypePreference || candidate.contractType}
                    </Badge>
                  </div>
                )}
                {/* Aceita Remoto */}
                {candidate.is_remote !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Aceita Remoto</span>
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${candidate.is_remote ? 'bg-status-success/15 text-status-success' : 'bg-gray-100 text-gray-800 dark:text-gray-200'}`}>
                      {candidate.is_remote ? 'Sim' : 'Não'}
                    </Badge>
                  </div>
                )}
                {/* Disponibilidade para Mudança */}
                {(candidate.willing_to_relocate !== undefined || candidate.willingToRelocate !== undefined) && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Aceita Mudança</span>
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${(candidate.willing_to_relocate ?? candidate.willingToRelocate) ? 'bg-status-success/15 text-status-success' : 'bg-gray-100 text-gray-800 dark:text-gray-200'}`}>
                      {(candidate.willing_to_relocate ?? candidate.willingToRelocate) === true ? 'Sim' : 
                       (candidate.willing_to_relocate ?? candidate.willingToRelocate) === false ? 'Não' : 
                       String(candidate.willing_to_relocate ?? candidate.willingToRelocate)}
                    </Badge>
                  </div>
                )}
                {/* Disponibilidade para Viagens */}
                {candidate.mobility !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Disponibilidade Viagens</span>
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${candidate.mobility ? 'bg-status-success/15 text-status-success' : 'bg-gray-100 text-gray-800 dark:text-gray-200'}`}>
                      {candidate.mobility === true ? 'Sim' : candidate.mobility === false ? 'Não' : String(candidate.mobility)}
                    </Badge>
                  </div>
                )}
                {/* Consentimento LGPD */}
                {candidate.communication_consent !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Consentimento LGPD</span>
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${candidate.communication_consent ? 'bg-status-success/15 text-status-success' : 'bg-status-error/15 text-status-error'}`}>
                      {candidate.communication_consent ? '✓ Consentido' : '✗ Não consentido'}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 7. Endereço - Sempre aparece */}
            <Card className="border-gray-100 dark:border-gray-700">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-gray-900">
                <div className="flex items-center gap-1.5">
                  <Home className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                  <CardTitle className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                    Endereço
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5">
                {hasAddressData() ? (
                  <div className="space-y-1">
                    <div className="flex items-start gap-2">
                      <MapPin className="w-3 h-3 text-gray-600 dark:text-gray-400 mt-0.5 flex-shrink-0" />
                      <div className="text-xs text-gray-800 dark:text-gray-200 whitespace-pre-line">
                        {getAddressString()}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className={`${textStyles.description} italic`}>Não informado</p>
                )}
              </CardContent>
            </Card>
          </div>
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
            <div className="flex items-center gap-1 border-b border-gray-100 dark:border-gray-700 pb-2">
              <button
                onClick={() => setOpinionsSubTab('pareceres')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors ${
                  opinionsSubTab === 'pareceres'
                    ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-b-2 border-gray-900 dark:border-gray-100'
 : 'text-gray-500 hover:text-gray-700 dark:text-gray-300 hover:bg-gray-50'
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
 : 'text-gray-500 hover:text-gray-700 dark:text-gray-300 hover:bg-gray-50'
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
                      <div key={i} className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 rounded-md p-4 animate-pulse">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                          <div className="flex-1">
                            <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded-md mb-1"></div>
                            <div className="w-24 h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                          <div className="w-3/4 h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Empty State */}
                {!isLoadingHistory && opinionsHistory.length === 0 && (
                  <div className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 rounded-md p-6 text-center">
                    <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-3">
                      <FileText className="w-6 h-6 text-gray-400 dark:text-gray-500" />
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
                    {opinionsHistory.map((opinion: any) => (
                      <div key={opinion.id} className="relative">
                        {!opinion.is_current && (
                          <Badge className="absolute top-2 right-2 text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-500 dark:text-gray-400 z-10">
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
                      <div key={i} className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 rounded-md p-4 animate-pulse">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                          <div className="flex-1">
                            <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded-md mb-1"></div>
                            <div className="w-24 h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                          <div className="w-3/4 h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Empty State */}
                {!isLoadingAnalyses && (!savedAnalyses || savedAnalyses.total_analyses === 0) && (
                  <div className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 rounded-md p-6 text-center">
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
                    {savedAnalyses.analyses.map((analysis: any) => {
                      const analysisLabels: Record<string, string> = {
                        'bullet_points': 'Pontos-chave',
                        'short_paragraph': 'Resumo',
                        'detailed_bullets': 'Análise Detalhada'
                      }
                      const isExpanded = expandedAnalysisId === analysis.id
                      
                      return (
                        <div 
                          key={analysis.id} 
                          className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 rounded-md overflow-hidden hover:transition-shadow"
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
                                <span className={`${textStyles.caption} text-gray-400`}>
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
                                      <Copy className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600 dark:text-gray-400" />
                                    )}
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent side="top" className="text-micro">Copiar análise</TooltipContent>
                              </Tooltip>
                              <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                            </div>
                          </div>
                          
                          {/* Card Content - Expandable */}
                          {isExpanded && (
                            <div className="px-3 pb-3 border-t border-gray-50 dark:border-gray-800">
                              <div className={`${textStyles.description} text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap bg-gray-50 dark:bg-gray-800 rounded-md p-3 mt-2`}>
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
                                      <Trash2 className="w-4 h-4 text-gray-400 group-hover:text-status-error" />
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
        <AlertDialogContent className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md">
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
        <AlertDialogContent className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md">
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
