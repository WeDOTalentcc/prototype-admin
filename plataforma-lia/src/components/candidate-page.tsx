// @ts-nocheck
"use client"

import { textStyles as designTextStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { integrationsService } from "@/services/integrations-service"
import { LiaAnalysisModal } from "@/components/modals/lia-analysis-modal"
import { useCandidatePageCore } from "@/components/candidate-page/useCandidatePageCore"
import { CandidatePageProfileTab } from "@/components/candidate-page/CandidatePageProfileTab"
import { CandidatePageActivitiesTab } from "@/components/candidate-page/CandidatePageActivitiesTab"
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

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  X, ArrowLeft, Star, MapPin, Calendar, Phone, Mail,
  Linkedin, ExternalLink, MessageSquare, UserPlus, FileText,
  Clock, Building, GraduationCap, Briefcase, Award, Target,
  Brain, TrendingUp, CheckCircle, AlertCircle,
  Send, Calendar as CalendarIcon, UserCheck, Download,
  Heart, Share2, MoreVertical, Eye, Edit, Bell, History,
  Paperclip, Users, Mic, Play, Pause, Volume2, BookOpen,
  ThumbsUp, Copy, Link, AtSign, Filter, Search,
  Plus, Trash, Archive, Flag, Hash, Zap, MessageCircle, Video,
  DollarSign, ChevronRight, Activity, ChevronDown, ChevronUp, User, Globe, List,
  Languages, Home, Gift, Database, Bot, ClipboardCheck, UserCircle, Cake,
  PlusCircle, GitBranch, MessageSquareText, Upload, Image, File,
  ZoomIn, ZoomOut, RotateCw, ChevronLeft, Code, Layers, Trash2, Check,
  Github, BarChart3
} from "lucide-react"

interface CandidatePageProps {
  candidate: Record<string, unknown>
  isOpen: boolean
  onClose: () => void
  onBackToKanban: () => void
  onSendEmail?: (candidate: Record<string, unknown>) => void
  onSendWhatsApp?: (candidate: Record<string, unknown>) => void
  onSendAgendamento?: (candidate: Record<string, unknown>) => void
  onWSIScreening?: (candidate: Record<string, unknown>) => void
  onAddToVacancy?: (candidate: Record<string, unknown>) => void
  onAddToList?: (candidate: Record<string, unknown>) => void
  onSendFeedback?: (candidate: Record<string, unknown>) => void
}

export function CandidatePage({
  candidate,
  isOpen,
  onClose,
  onBackToKanban,
  onSendEmail,
  onSendWhatsApp,
  onSendAgendamento,
  onWSIScreening,
  onAddToVacancy,
  onAddToList,
  onSendFeedback,
}: CandidatePageProps) {
  const core = useCandidatePageCore(candidate)
  const {
    activeTab, setActiveTab,
    showLiaModal, setShowLiaModal,
    liaCommand, setLiaCommand,
    showVideoModal, setShowVideoModal,
    viewMode, setViewMode,
    expandedLiaPredictions, setExpandedLiaPredictions,
    periodFilter, setPeriodFilter,
    activityFilter, setActivityFilter,
    expandedActivity, setExpandedActivity,
    showAIPredictions, setShowAIPredictions,
    isDragging, setIsDragging,
    selectedFile, setSelectedFile,
    showPreview, setShowPreview,
    previewType, setPreviewType,
    videoPlaying, setVideoPlaying,
    pdfPage, setPdfPage,
    pdfTotalPages, setPdfTotalPages,
    imageZoom, setImageZoom,
    opinionsSubTab, setOpinionsSubTab,
    opinionsHistory,
    isLoadingHistory,
    expandedOpinionId, setExpandedOpinionId,
    savedAnalyses,
    isLoadingAnalyses,
    expandedAnalysisId, setExpandedAnalysisId,
    copiedItemId,
    analysisToDelete, setAnalysisToDelete,
    showLiaAnalysisModal, setShowLiaAnalysisModal,
    activities,
    aiPredictions,
    tabs,
    filteredActivities,
    textStyles,
    localBadgeStyles,
    localCardStyles,
    colorToBg,
    getBgColor,
    cleanTextForCopy,
    handleCopyOpinion,
    handleCopyAnalysis,
    handleDeleteAnalysis,
    handleAnalysisTransport,
    getScoreColor,
    formatDateShort,
    formatDate,
    calculateAge,
    hasPersonalData,
    hasPearchData,
  } = core

  if (!isOpen || !candidate) return null

  type CandidateRecord = {
    name: string
    id?: string
    candidateId?: string
    avatar_url?: string
    avatar?: string
    phone?: string
    position?: string
    location?: string
    linkedin_url?: string
    linkedinUrl?: string
    github_url?: string
    portfolio_url?: string
    website?: string
    email?: string
    liaAnalysis?: { score?: number; fitScore?: number }
    workHistory?: Record<string, unknown>[]
    work_history?: Record<string, unknown>[]
    experiences?: Record<string, unknown>[]
    education?: Record<string, unknown>[]
    additional_data?: Record<string, unknown>
    [key: string]: unknown
  }
  const _candidate = candidate as unknown as CandidateRecord

  const liaScore = _candidate.liaAnalysis?.score || 92
  const fitScore = _candidate.liaAnalysis?.fitScore || 95

  const additionalData = _candidate.additional_data as Record<string, unknown> | undefined
  const experiences = _candidate.workHistory || _candidate.work_history || _candidate.experiences || additionalData?.work_history || additionalData?.experiences || []
  const education = _candidate.education || additionalData?.education || []

  return (
    <div className="fixed inset-0 bg-white dark:bg-lia-bg-primary z-30 overflow-hidden flex flex-col">
      {/* Header Compacto como no Preview */}
      <TooltipProvider delayDuration={200}>
        <div className="bg-white dark:bg-lia-bg-secondary border-b border-lia-border-subtle dark:border-lia-border-subtle px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Avatar className="w-10 h-10">
                <AvatarImage src={(_candidate.avatar_url as string | undefined) || (_candidate.avatar as string | undefined)} alt={_candidate.name as string} />
                <AvatarFallback className="text-sm font-medium bg-gray-200 lia-text-base">
                  {(_candidate.name as string).split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-base font-semibold text-lia-text-primary">{_candidate.name as string}</h1>
                  <Badge variant="outline" className="text-xs px-1.5 py-0">
                    {_candidate.candidateId || _candidate.id}
                  </Badge>
                  <Badge className={`text-xs px-1.5 py-0 ${getScoreColor(liaScore)}`}>
                    {liaScore}% Match
                  </Badge>
                </div>
                <div className="flex items-center gap-2 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                  <span>{_candidate.position as string | undefined}</span>
                  <span className="lia-text-secondary">•</span>
                  <MapPin className="w-3 h-3" />
                  <span>{_candidate.location as string | undefined}</span>
                </div>
              </div>
            </div>

            {/* Right Side: Social Icons + LIA + Close */}
            <div className="flex items-center gap-2">
              {/* Social Icons */}
              <div className="flex items-center gap-1 mr-2">
                {(_candidate.linkedin_url || _candidate.linkedinUrl) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <a 
                        href={_candidate.linkedin_url || _candidate.linkedinUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="p-1.5 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
                      >
                        <Linkedin className="w-4 h-4 lia-text-base" />
                      </a>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">LinkedIn</TooltipContent>
                  </Tooltip>
                )}
                {((_candidate.github_url as string | undefined) || (_candidate.githubUrl as string | undefined)) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <a
                        href={(_candidate.github_url as string | undefined) || (_candidate.githubUrl as string | undefined)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
                      >
                        <Github className="w-4 h-4 text-lia-text-primary" />
                      </a>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">GitHub</TooltipContent>
                  </Tooltip>
                )}
                {((_candidate.portfolio_url as string | undefined) || (_candidate.portfolioUrl as string | undefined) || (_candidate.website as string | undefined)) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <a
                        href={(_candidate.portfolio_url as string | undefined) || (_candidate.portfolioUrl as string | undefined) || (_candidate.website as string | undefined)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
                      >
                        <Globe className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                      </a>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">Portfolio</TooltipContent>
                  </Tooltip>
                )}
              </div>

              {/* Quick Action Buttons - Same pattern as CandidatePreview */}
              <div className="flex items-center gap-1 border-l border-lia-border-subtle dark:border-lia-border-default pl-3 ml-1">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => onSendEmail ? onSendEmail(candidate) : (_candidate.email && window.open(`mailto:${_candidate.email}`, '_self'))}
                      disabled={!_candidate.email && !onSendEmail}
                    >
                      <Mail className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">Email</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => {
                        if (onSendWhatsApp) {
                          onSendWhatsApp(candidate)
                        } else if (_candidate.phone) {
                          window.open(`https://wa.me/${_candidate.phone.replace(/\D/g, '')}`, '_blank')
                        }
                      }}
                      disabled={!_candidate.phone && !onSendWhatsApp}
                    >
                      <Phone className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">WhatsApp</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => onSendAgendamento?.(candidate)}
                    >
                      <CalendarIcon className="w-4 h-4 text-wedo-orange" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">Agendar Entrevista</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => onWSIScreening?.(candidate)}
                    >
                      <ClipboardCheck className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">Triagem WSI</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => onAddToVacancy?.(candidate)}
                    >
                      <Briefcase className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">Adicionar à Vaga</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => onAddToList?.(candidate)}
                    >
                      <Users className="w-4 h-4 text-wedo-green" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">Adicionar à Lista</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => onSendFeedback?.(candidate)}
                    >
                      <MessageSquare className="w-4 h-4 text-wedo-purple" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">Enviar Feedback</TooltipContent>
                </Tooltip>
              </div>

              {/* LIA Analysis Button */}
              <LiaAnalysisModal
                isOpen={showLiaAnalysisModal}
                onOpen={() => setShowLiaAnalysisModal(true)}
                onClose={() => setShowLiaAnalysisModal(false)}
                candidate={_candidate}
                onTransportToOpinions={handleAnalysisTransport}
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 hover:bg-gray-100 border border-lia-border-default rounded-md"
                    >
                      <Brain className="w-5 h-5 text-wedo-cyan" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">Análises LIA</TooltipContent>
                </Tooltip>
              </LiaAnalysisModal>

              {/* Close Button */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="sm" onClick={onClose} className="h-7 w-7 p-0">
                    <X className="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Fechar</TooltipContent>
              </Tooltip>
            </div>
          </div>
        </div>
      </TooltipProvider>

      {/* Tabs exatamente como no preview */}
      <div className="bg-white dark:bg-lia-bg-secondary border-b border-lia-border-subtle dark:border-lia-border-subtle px-6">
        <div className="flex">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as 'activities' | 'profile' | 'files' | 'opinions')}
              className={`flex items-center gap-2 px-3 py-2.5 text-xs font-medium whitespace-nowrap transition-colors motion-reduce:transition-none ${
 activeTab === tab.id
                  ? 'border-b-2 lia-text-secondary border-gray-400'
                  : 'text-lia-text-primary dark:text-lia-text-primary hover:text-lia-text-primary dark:hover:text-lia-text-inverse'
              }`}
            >
              <tab.icon className="w-3 h-3" />
              {tab.label}
              {tab.badge !== undefined && tab.badge > 0 && (
                <Badge className="text-micro px-1.5 py-0 h-4 ml-1 bg-wedo-cyan/15">
                  {tab.badge}
                </Badge>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-lia-bg-primary">
        <div className="max-w-7xl mx-auto p-6">
          {activeTab === 'profile' && (
            <CandidatePageProfileTab
              candidate={_candidate as unknown as Parameters<typeof CandidatePageProfileTab>[0]['candidate']}
              experiences={experiences as unknown as Parameters<typeof CandidatePageProfileTab>[0]['experiences']}
              education={education as unknown as Parameters<typeof CandidatePageProfileTab>[0]['education']}
              liaScore={liaScore}
              opinionsHistory={opinionsHistory}
              formatDateShort={formatDateShort}
              formatDate={formatDate}
              calculateAge={calculateAge}
              hasPersonalData={hasPersonalData}
              hasPearchData={hasPearchData}
            />
          )}

          {activeTab === 'activities' && (
            <CandidatePageActivitiesTab
              filteredActivities={filteredActivities}
              periodFilter={periodFilter}
              setPeriodFilter={setPeriodFilter}
              viewMode={viewMode}
              setViewMode={setViewMode}
              setShowLiaModal={setShowLiaModal}
              activityFilter={activityFilter}
              setActivityFilter={setActivityFilter}
              showAIPredictions={showAIPredictions}
              setShowAIPredictions={setShowAIPredictions}
              aiPredictions={aiPredictions}
              expandedActivity={expandedActivity}
              setExpandedActivity={setExpandedActivity}
              getBgColor={getBgColor}
            />
          )}

          {activeTab === 'files' && (
            <div className="space-y-4">
              {/* Upload Area */}
              <Card className="border-2 border-dashed border-lia-border-default dark:border-lia-border-default hover:border-gray-400 dark:hover:border-gray-500">
                <CardContent className="p-6">
                  <div
                    className={`text-center cursor-pointer transition-colors motion-reduce:transition-none ${
 isDragging ? 'opacity-50' : ''
                    }`}
                    onDragOver={(e) => {
                      e.preventDefault()
                      setIsDragging(true)
                    }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={(e) => {
                      e.preventDefault()
                      setIsDragging(false)
                      const files = Array.from(e.dataTransfer.files)
                    }}
                    onClick={() => {
                      const input = document.createElement('input')
                      input.type = 'file'
                      input.multiple = true
                      input.accept = '.pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov,.mp3,.wav,.m4a,.webm,.ogg'
                      input.onchange = (e) => {
                        const files = Array.from((e.target as HTMLInputElement).files || [])
                      }
                      input.click()
                    }}
                  >
                    <Upload className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary mx-auto mb-3" />
                    <h3 className="text-sm font-medium mb-2">
                      {isDragging ? 'Solte os arquivos aqui' : 'Arraste arquivos ou clique para selecionar'}
                    </h3>
                    <p className="text-xs lia-text-base">PDF, DOC, JPG, PNG, MP4, MP3, WAV até 25MB</p>
                    <Button className="mt-3 h-7 text-xs">
                      <Plus className="w-3 h-3 mr-1" />
                      Selecionar Arquivos
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Lista de Arquivos */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* CV */}
                <Card className="hover:transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <FileText className="w-5 h-5 text-status-error" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">CV_{(_candidate.name as string).replace(' ', '_')}_2025.pdf</h4>
                        <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">2.1 MB • há 3 dias</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-status-success/15 text-status-success text-xs">✓ Verificado</Badge>
                          <Badge className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary text-xs">LIA: 95%</Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1 mt-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0"
                        onClick={() => {
                          setSelectedFile({ name: 'CV_' + (_candidate.name as string) + '.pdf', type: 'pdf' })
                          setPreviewType('pdf')
                          setShowPreview(true)
                        }}
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </Button>
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                        <Download className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Portfolio */}
                <Card className="hover:transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <FileText className="w-5 h-5 text-wedo-purple" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">Portfolio_UX_2025.pdf</h4>
                        <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">12.3 MB • há 1 dia</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-status-success/15 text-status-success text-xs">✓ Verificado</Badge>
                          <Badge className="bg-wedo-purple/15 text-wedo-purple text-xs">Destacado</Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1 mt-3">
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                        <Eye className="w-3.5 h-3.5" />
                      </Button>
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                        <Download className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Vídeo de Apresentação */}
                <Card className="hover:transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <Video className="w-5 h-5 text-status-error" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">Apresentacao_Pessoal.mp4</h4>
                        <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">25.4 MB • 3:45 min</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-status-success/15 text-status-success text-xs">✓ Analisado</Badge>
                          <Badge className="bg-status-error/15 text-status-error text-xs">Triagem</Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1 mt-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-xs gap-1"
                        onClick={() => setShowVideoModal({
                          title: 'Apresentação Pessoal',
                          url: 'video.mp4'
                        })}
                      >
                        <Play className="w-3.5 h-3.5" />
                        Assistir
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Vídeo de Case Técnico */}
                <Card className="hover:transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <Video className="w-5 h-5 text-wedo-purple" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">Case_UX_Design.mp4</h4>
                        <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">45.2 MB • 8:20 min</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-wedo-purple/15 text-wedo-purple text-xs">Destaque</Badge>
                          <Badge className="bg-status-success/15 text-status-success text-xs">Score: 88%</Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1 mt-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-xs gap-1"
                        onClick={() => setShowVideoModal({
                          title: 'Case UX Design',
                          url: 'case.mp4'
                        })}
                      >
                        <Play className="w-3.5 h-3.5" />
                        Assistir
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Gravacao de Audio - Triagem por Voz */}
                <Card className="hover:transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <Mic className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">Triagem_Voz_{_candidate.name.split(' ')[0]}.mp3</h4>
                        <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">1.8 MB • 4:32 min • há 1 dia</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary text-xs">Triagem WSI</Badge>
                          <Badge className="bg-status-success/15 text-status-success text-xs">Score: 92%</Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1 mt-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-xs gap-1"
                        onClick={() => {
                          setSelectedFile({
                            name: `Triagem_Voz_${_candidate.name.split(' ')[0]}.mp3`,
                            type: 'audio',
                            transcription: 'Olá, meu nome é Maria Oliveira e sou UX Designer há 8 anos. Trabalho atualmente na empresa XYZ como Design Lead...',
                            aiAnalysis: {
                              confidence: 92,
                              communication: 88,
                              enthusiasm: 85,
                              clarity: 90
                            }
                          })
                          setPreviewType('audio')
                          setShowPreview(true)
                        }}
                      >
                        <Play className="w-3.5 h-3.5" />
                        Ouvir
                      </Button>
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                        <Download className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Foto do Candidato */}
                <Card className="hover:transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <Image className="w-5 h-5 text-status-success" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">foto_perfil.jpg</h4>
                        <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">456 KB • há 2 horas</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-status-success/15 text-status-success text-xs">✓ Verificado</Badge>
                        </div>
                      </div>
                    </div>
                    {(_candidate.avatar_url || _candidate.avatar) && (
                      <div className="mt-3">
                        <img
                          src={_candidate.avatar_url || _candidate.avatar}
                          alt="Preview"
                          className="w-full h-24 rounded-md object-cover cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none"
                          onClick={() => {
                            setSelectedFile({
                              name: 'foto_perfil.jpg',
                              type: 'image',
                              url: _candidate.avatar_url || _candidate.avatar
                            })
                            setPreviewType('image')
                            setShowPreview(true)
                          }}
                        />
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Certificados */}
                <Card className="hover:transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <Award className="w-5 h-5 text-wedo-orange" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">Certificados.zip</h4>
                        <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">3.2 MB • há 1 semana</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-wedo-orange/15 text-wedo-orange text-xs">5 arquivos</Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1 mt-3">
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                        <Download className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* Tab Pareceres */}
          {activeTab === 'opinions' && (
            <TooltipProvider delayDuration={200}>
              <div className="space-y-4">
                {/* Subtabs Header */}
                <div className="flex items-center gap-1 border-b border-lia-border-subtle dark:border-lia-border-subtle pb-2">
                  <button
                    onClick={() => setOpinionsSubTab('pareceres')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors motion-reduce:transition-none ${
 opinionsSubTab === 'pareceres'
                        ? 'bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary border-b-2 border-gray-900 dark:border-lia-border-subtle'
                        : 'text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-disabled hover:bg-gray-50 dark:hover:bg-gray-800'
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
                    className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors motion-reduce:transition-none ${
 opinionsSubTab === 'analises'
                        ? 'bg-wedo-purple/10 dark:bg-wedo-purple/20 text-wedo-purple dark:text-wedo-purple border-b-2 border-wedo-purple/30'
                        : 'text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-disabled hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                  >
                    <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                    Análises
                    {savedAnalyses && (savedAnalyses as unknown as {total_analyses: number}).total_analyses > 0 && (
                      <Badge className="text-micro px-1.5 py-0 h-4 ml-1 bg-wedo-purple/15 text-wedo-purple">
                        {(savedAnalyses as unknown as {total_analyses: number}).total_analyses}
                      </Badge>
                    )}
                  </button>
                </div>
                
                {/* Subtab: Pareceres da LIA */}
                {opinionsSubTab === 'pareceres' && (
                  <div className="space-y-3">
                    {/* Loading State */}
                    {isLoadingHistory && (
                      <div className="space-y-3">
                        {[1, 2].map((i) => (
                          <Card key={i} className="animate-pulse motion-reduce:animate-none">
                            <CardContent className="p-4">
                              <div className="flex items-center gap-3 mb-3">
                                <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                                <div className="flex-1">
                                  <div className="w-32 h-4 bg-gray-200 rounded-md mb-1"></div>
                                  <div className="w-24 h-3 bg-gray-200 rounded-md"></div>
                                </div>
                              </div>
                              <div className="space-y-2">
                                <div className="w-full h-3 bg-gray-200 rounded-md"></div>
                                <div className="w-3/4 h-3 bg-gray-200 rounded-md"></div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                    
                    {/* Empty State */}
                    {!isLoadingHistory && opinionsHistory.length === 0 && (
                      <Card>
                        <CardContent className="p-6 text-center">
                          <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-lia-bg-elevated flex items-center justify-center mx-auto mb-3">
                            <FileText className="w-6 h-6 lia-text-secondary" />
                          </div>
                          <p className={`${textStyles.subtitle} mb-1`}>Nenhum parecer disponível</p>
                          <p className={textStyles.description}>
                            Os pareceres serão gerados automaticamente após triagens ou análises da LIA.
                          </p>
                        </CardContent>
                      </Card>
                    )}
                    
                    {/* Opinions List */}
                    {!isLoadingHistory && opinionsHistory.length > 0 && (
                      <div className="space-y-3">
                        {opinionsHistory.map((opinion: Record<string, unknown>) => {
                          const isExpanded = expandedOpinionId === opinion.id
                          const isWsiOpinion = opinion.opinion_type === 'wsi'
                          const displayScore = isWsiOpinion ? (opinion.wsi_score as number | null | undefined) : (opinion.score as number | null | undefined)
                          
                          const getOpinionScoreColor = (score: number, isWsi: boolean) => {
                            if (isWsi) {
                              if (score >= 4) return 'text-status-success'
                              if (score >= 3) return 'text-status-warning'
                              return 'text-status-error'
                            } else {
                              if (score >= 80) return 'text-status-success'
                              if (score >= 60) return 'text-status-warning'
                              return 'text-status-error'
                            }
                          }
                          
                          const getRecommendationBadge = (rec: string | null) => {
                            if (!rec) return null
                            if (rec === 'approved') {
                              return (
                                <Badge className={`${badgeStyles.success} flex items-center gap-0.5`}>
                                  <CheckCircle className="w-2.5 h-2.5" />
                                  APROVADO
                                </Badge>
                              )
                            }
                            if (rec === 'pending_review') {
                              return (
                                <Badge className={`${badgeStyles.warning} flex items-center gap-0.5`}>
                                  <Clock className="w-2.5 h-2.5" />
                                  PENDENTE
                                </Badge>
                              )
                            }
                            if (rec === 'not_approved') {
                              return (
                                <Badge className={`${badgeStyles.error} flex items-center gap-0.5`}>
                                  <X className="w-2.5 h-2.5" />
                                  NÃO APROVADO
                                </Badge>
                              )
                            }
                            return null
                          }
                          
                          return (
                            <Card key={opinion.id as string} className="overflow-hidden">
                              <div
                                onClick={() => setExpandedOpinionId(isExpanded ? null : opinion.id as string | null)}
                                className="p-3 flex items-center justify-between hover:bg-gray-50 transition-colors motion-reduce:transition-none cursor-pointer"
                              >
                                <div className="flex items-center gap-2">
                                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
 isWsiOpinion ? 'bg-wedo-purple/15' : 'bg-gray-100 dark:bg-lia-bg-secondary'
                                  }`}>
                                    {isWsiOpinion ? (
                                      <Target className="w-4 h-4 text-wedo-purple" />
                                    ) : (
                                      <Brain className="w-4 h-4 text-wedo-cyan" />
                                    )}
                                  </div>
                                  <div className="text-left">
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <span className={textStyles.label}>
                                        {isWsiOpinion ? 'Parecer WSI' : (opinion.job_vacancy_id ? 'Parecer de Vaga' : 'Parecer Geral')}
                                      </span>
                                      {opinion.job_vacancy_id && opinion.job_vacancy_title ? (
                                        <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-default dark:border-lia-border-default flex items-center gap-1">
                                          <Briefcase className="w-2.5 h-2.5" />
                                          #{String(opinion.job_vacancy_id).slice(0, 6)} - {opinion.job_vacancy_title as string}
                                        </Badge>
                                      ) : !opinion.job_vacancy_id ? (
                                        <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-subtle dark:border-lia-border-subtle">
                                          Sem vaga vinculada
                                        </Badge>
                                      ) : null}
                                    </div>
                                    <div className="flex items-center gap-2 mt-0.5">
                                      {displayScore !== null && displayScore !== undefined && (
                                        <span className={`text-micro font-semibold ${getOpinionScoreColor(displayScore, isWsiOpinion)}`}>
                                          {isWsiOpinion ? `WSI: ${(displayScore as number).toFixed(1)}/5` : `Score: ${Math.round(displayScore as number)}/100`}
                                        </span>
                                      )}
                                      {opinion.archetype && (
                                        <>
                                          <span className="lia-text-muted">•</span>
                                          <span className={textStyles.caption}>{opinion.archetype as string}</span>
                                        </>
                                      )}
                                      {getRecommendationBadge(opinion.recommendation as string | null)}
                                    </div>
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  {!!(opinion.created_at) && (
                                    <span className="text-micro lia-text-secondary">
                                      {new Date(opinion.created_at as string).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })}
                                    </span>
                                  )}
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          handleCopyOpinion(opinion, (opinion.opinion_type as string | undefined) || 'general')
                                        }}
                                        className="p-1 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
                                      >
                                        {copiedItemId === `opinion-${opinion.id as string}` ? (
                                          <Check className="w-3.5 h-3.5 text-status-success" />
                                        ) : (
                                          <Copy className="w-3.5 h-3.5 lia-text-secondary hover:lia-text-base" />
                                        )}
                                      </button>
                                    </TooltipTrigger>
                                    <TooltipContent side="top" className="text-micro">Copiar parecer</TooltipContent>
                                  </Tooltip>
                                  {isExpanded ? (
                                    <ChevronUp className="w-4 h-4 lia-text-secondary" />
                                  ) : (
                                    <ChevronDown className="w-4 h-4 lia-text-secondary" />
                                  )}
                                </div>
                              </div>
                              
                              {isExpanded && (
                                <div className="px-3 pb-3 pt-0 border-t border-lia-border-subtle space-y-3">
                                  {!!(opinion.summary) && (
                                    <div className="pt-3">
                                      <p className="text-xs text-lia-text-primary dark:text-lia-text-primary leading-relaxed">
                                        {opinion.summary as string}
                                      </p>
                                    </div>
                                  )}
                                  
                                  {!!(opinion.score_breakdown) && Object.keys(opinion.score_breakdown as Record<string, unknown>).length > 0 && (
                                    <div>
                                      <h5 className={`${textStyles.label} mb-1.5 flex items-center gap-1`}>
                                        <BarChart3 className="w-3 h-3" />
                                        Score Breakdown
                                      </h5>
                                      <div className="grid grid-cols-2 gap-1.5">
                                        {Object.entries(opinion.score_breakdown as Record<string, unknown>).map(([key, value]: [string, unknown]) => (
                                          value !== null && value !== undefined && (
                                            <div key={key} className="flex items-center justify-between text-micro bg-gray-50 dark:bg-lia-bg-elevated rounded-full px-2 py-1">
                                              <span className="lia-text-base capitalize">{key.replace(/_/g, ' ')}</span>
                                              <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">{typeof value === 'number' ? `${Math.round(value)}%` : value}</span>
                                            </div>
                                          )
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  
                                  {opinion.strengths && (opinion.strengths as string[]).length > 0 && (
                                    <div>
                                      <h5 className={`${textStyles.label} text-status-success mb-1 flex items-center gap-1`}>
                                        <CheckCircle className="w-3 h-3" />
                                        Pontos Fortes
                                      </h5>
                                      <ul className="space-y-0.5">
                                        {(opinion.strengths as string[]).map((s: string, i: number) => (
                                          <li key={i} className={`${textStyles.caption} lia-text-base flex items-start gap-1`}>
                                            <span className="text-status-success mt-0.5">•</span>
                                            {s}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {opinion.concerns && (opinion.concerns as string[]).length > 0 && (
                                    <div>
                                      <h5 className={`${textStyles.label} text-status-warning mb-1 flex items-center gap-1`}>
                                        <AlertCircle className="w-3 h-3" />
                                        Pontos de Atenção
                                      </h5>
                                      <ul className="space-y-0.5">
                                        {(opinion.concerns as string[]).map((c: string, i: number) => (
                                          <li key={i} className={`${textStyles.caption} lia-text-base flex items-start gap-1`}>
                                            <span className="text-status-warning mt-0.5">•</span>
                                            {c}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {!!(opinion.next_steps) && (
                                    <div>
                                      <h5 className={`${textStyles.label} mb-1 flex items-center gap-1`}>
                                        <TrendingUp className="w-3 h-3" />
                                        Próximos Passos
                                      </h5>
                                      <p className={`${textStyles.caption} lia-text-base`}>{opinion.next_steps as string}</p>
                                    </div>
                                  )}
                                </div>
                              )}
                            </Card>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}
                
                {/* Subtab: Análises */}
                {opinionsSubTab === 'analises' && (
                  <div className="space-y-3">
                    {/* Loading State */}
                    {isLoadingAnalyses && (
                      <div className="space-y-3">
                        {[1, 2].map((i) => (
                          <Card key={i} className="animate-pulse motion-reduce:animate-none">
                            <CardContent className="p-4">
                              <div className="flex items-center gap-3 mb-3">
                                <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                                <div className="flex-1">
                                  <div className="w-32 h-4 bg-gray-200 rounded-md mb-1"></div>
                                  <div className="w-24 h-3 bg-gray-200 rounded-md"></div>
                                </div>
                              </div>
                              <div className="space-y-2">
                                <div className="w-full h-3 bg-gray-200 rounded-md"></div>
                                <div className="w-3/4 h-3 bg-gray-200 rounded-md"></div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                    
                    {/* Empty State */}
                    {!isLoadingAnalyses && (!savedAnalyses || savedAnalyses.total_analyses === 0) && (
                      <Card>
                        <CardContent className="p-6 text-center">
                          <div className="w-12 h-12 rounded-full bg-wedo-purple/10 flex items-center justify-center mx-auto mb-3">
                            <Brain className="w-6 h-6 text-wedo-purple" />
                          </div>
                          <p className={`${textStyles.subtitle} mb-1`}>Nenhuma análise disponível</p>
                          <p className={textStyles.description}>
                            Use o ícone 🧠 no header para gerar análises de perfil e salvá-las aqui.
                          </p>
                        </CardContent>
                      </Card>
                    )}
                    
                    {/* Analyses List */}
                    {!isLoadingAnalyses && savedAnalyses && (savedAnalyses as unknown as {total_analyses: number}).total_analyses > 0 && (
                      <div className="space-y-3">
                        {(savedAnalyses as unknown as {analyses: Record<string, unknown>[]}).analyses.map((analysis: Record<string, unknown>) => {
                          const analysisLabels: Record<string, string> = {
                            'bullet_points': 'Pontos-chave',
                            'short_paragraph': 'Resumo',
                            'detailed_bullets': 'Análise Detalhada'
                          }
                          const isExpanded = expandedAnalysisId === analysis.id
                          
                          return (
                            <Card key={analysis.id as string} className="overflow-hidden hover:transition-shadow">
                              {/* Card Header */}
                              <div 
                                className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50/50 transition-colors motion-reduce:transition-none"
                                onClick={() => setExpandedAnalysisId(isExpanded ? null : analysis.id as string | null)}
                              >
                                <div className="flex items-center gap-2.5">
                                  <div className="w-8 h-8 rounded-full bg-wedo-purple/15 flex items-center justify-center flex-shrink-0">
                                    <Brain className="w-4 h-4 text-wedo-purple" />
                                  </div>
                                  <div className="min-w-0">
                                    <div className="flex items-center gap-2">
                                      <span className={`${textStyles.bodySmall} font-medium`}>Análise LIA</span>
                                      <Badge 
                                        className="text-micro px-1.5 py-0 h-4 bg-wedo-purple/15 text-wedo-purple"
                                      >
                                        {analysisLabels[analysis.analysis_type as string] || analysis.analysis_type as string}
                                      </Badge>
                                    </div>
                                    <span className={`${textStyles.caption} lia-text-secondary`}>
                                      {analysis.created_at ? new Date(analysis.created_at as string).toLocaleDateString('pt-BR', { 
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
                                        className="p-1 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
                                      >
                                        {copiedItemId === `analysis-${analysis.id}` ? (
                                          <Check className="w-3.5 h-3.5 text-status-success" />
                                        ) : (
                                          <Copy className="w-3.5 h-3.5 lia-text-secondary hover:lia-text-base" />
                                        )}
                                      </button>
                                    </TooltipTrigger>
                                    <TooltipContent side="top" className="text-micro">Copiar análise</TooltipContent>
                                  </Tooltip>
                                  <ChevronDown className={`w-4 h-4 lia-text-secondary transition-transform motion-reduce:transition-none ${isExpanded ? 'rotate-180' : ''}`} />
                                </div>
                              </div>
                              
                              {/* Card Content */}
                              {isExpanded && (
                                <div className="px-3 pb-3 border-t border-gray-50">
                                  <div className={`${textStyles.description} text-lia-text-primary dark:text-lia-text-primary leading-relaxed whitespace-pre-wrap bg-gray-50 rounded-md p-3 mt-2`}>
                                    {cleanTextForCopy(analysis.content as string)}
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
                                          className="p-1.5 hover:bg-status-error/10 rounded-md transition-colors motion-reduce:transition-none group"
                                        >
                                          <Trash2 className="w-4 h-4 lia-text-secondary group-hover:text-status-error" />
                                        </button>
                                      </TooltipTrigger>
                                      <TooltipContent side="top" className="text-micro">Remover análise</TooltipContent>
                                    </Tooltip>
                                  </div>
                                </div>
                              )}
                            </Card>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </TooltipProvider>
          )}
        </div>
      </div>

      {/* Delete Analysis AlertDialog */}
      <AlertDialog open={!!analysisToDelete} onOpenChange={(open: boolean) => !open && setAnalysisToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover Análise</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja remover esta análise? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDeleteAnalysis}
              className="bg-status-error hover:bg-status-error text-white"
            >
              Remover Definitivamente
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Modal de Vídeo */}
      {showVideoModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-lia-bg-secondary rounded-md max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="p-4 border-b border-lia-border-subtle dark:border-lia-border-subtle flex items-center justify-between">
              <h3 className="text-sm font-semibold">{showVideoModal.title as string}</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowVideoModal(null)} className="h-7 w-7 p-0">
                <X className="w-3.5 h-3.5" />
              </Button>
            </div>

            <div className="p-4">
              <div className="aspect-video bg-gray-900 rounded-md flex items-center justify-center">
                <Play className="w-16 h-16 text-white opacity-50" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* LIA Modal exatamente como no preview */}
      {showLiaModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-lia-bg-secondary rounded-md max-w-2xl w-full">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  Assistente LIA
                </h3>
                <Button variant="ghost" size="sm" onClick={() => setShowLiaModal(false)} className="h-7 w-7 p-0">
                  <X className="w-3.5 h-3.5" />
                </Button>
              </div>

              <textarea
                value={liaCommand}
                onChange={(e) => setLiaCommand(e.target.value)}
                placeholder="Digite seu comando para a LIA..."
                className="w-full p-3 border rounded-md h-20 text-xs resize-none"
              />

              <div className="flex gap-2 mt-4">
                <Button
                  onClick={() => {
                    setShowLiaModal(false)
                    setLiaCommand('')
                  }}
                  className="flex-1 bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200 text-xs h-8"
                  disabled={!liaCommand.trim()}
                >
                  <Brain className="w-3.5 h-3.5 mr-1 text-wedo-cyan" />
                  Executar Comando
                </Button>
                <Button
                  variant="outline"
                  onClick={() => { setShowLiaModal(false); setLiaCommand('') }}
                  className="text-xs h-8"
                >
                  Cancelar
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
