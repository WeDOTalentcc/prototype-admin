"use client"

import { textStyles as designTextStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { integrationsService } from "@/services/integrations-service"
import { LiaAnalysisModal } from "@/components/modals/lia-analysis-modal"
import { useCandidatePageCore } from "@/components/candidate-page/useCandidatePageCore"
import { CandidatePageHeader } from "@/components/candidate-page/CandidatePageHeader"
import { CandidatePageFilesTab } from "@/components/candidate-page/CandidatePageFilesTab"
import { CandidatePageOpinionsTab } from "@/components/candidate-page/CandidatePageOpinionsTab"
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
    <div className="fixed inset-0 bg-lia-bg-primary dark:bg-lia-bg-primary z-30 overflow-hidden flex flex-col">
      {/* Header Compacto como no Preview */}
      <CandidatePageHeader
        _candidate={_candidate}
        liaScore={liaScore}
        showLiaAnalysisModal={showLiaAnalysisModal}
        setShowLiaAnalysisModal={setShowLiaAnalysisModal}
        handleAnalysisTransport={handleAnalysisTransport}
        getScoreColor={getScoreColor}
        onClose={onClose}
        onSendEmail={onSendEmail}
        onSendWhatsApp={onSendWhatsApp}
        onSendAgendamento={onSendAgendamento}
        onWSIScreening={onWSIScreening}
        onAddToVacancy={onAddToVacancy}
        onAddToList={onAddToList}
        onSendFeedback={onSendFeedback}
        candidate={candidate}
      />

      {/* Tabs exatamente como no preview */}
      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border-b border-lia-border-subtle dark:border-lia-border-subtle px-6">
        <div className="flex">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as 'activities' | 'profile' | 'files' | 'opinions')}
              className={`flex items-center gap-2 px-3 py-2.5 text-xs font-medium whitespace-nowrap transition-colors motion-reduce:transition-none ${
 activeTab === tab.id
                  ? 'border-b-2 lia-text-secondary border-lia-border-medium'
                  : 'text-lia-text-primary hover:text-lia-text-primary dark:hover:text-lia-text-inverse'
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
      <div className="flex-1 overflow-y-auto bg-lia-bg-primary dark:bg-lia-bg-primary">
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
            <CandidatePageFilesTab
              _candidate={_candidate}
              isDragging={isDragging}
              setIsDragging={setIsDragging}
              setSelectedFile={setSelectedFile}
              // @ts-ignore TODO: fix type — Type 'Dispatch<SetStateAction<"audio" | "video" | "image" | "pdf" | null>>' is n
              setPreviewType={setPreviewType}
              setShowPreview={setShowPreview}
              setShowVideoModal={setShowVideoModal}
            />
          )}

          {/* Tab Pareceres */}
          {activeTab === 'opinions' && (
            <CandidatePageOpinionsTab
              opinionsSubTab={opinionsSubTab}
              setOpinionsSubTab={setOpinionsSubTab}
              opinionsHistory={opinionsHistory}
              isLoadingHistory={isLoadingHistory}
              expandedOpinionId={expandedOpinionId}
              setExpandedOpinionId={setExpandedOpinionId}
              savedAnalyses={savedAnalyses}
              isLoadingAnalyses={isLoadingAnalyses}
              expandedAnalysisId={expandedAnalysisId}
              setExpandedAnalysisId={setExpandedAnalysisId}
              copiedItemId={copiedItemId}
              analysisToDelete={analysisToDelete}
              setAnalysisToDelete={setAnalysisToDelete}
              textStyles={textStyles}
              badgeStyles={localBadgeStyles}
              cleanTextForCopy={cleanTextForCopy}
              handleCopyOpinion={handleCopyOpinion}
              handleCopyAnalysis={handleCopyAnalysis}
              handleDeleteAnalysis={handleDeleteAnalysis}
            />
          )}
        </div>
      </div>

      {/* Modal de Vídeo */}
      {showVideoModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="p-4 border-b border-lia-border-subtle dark:border-lia-border-subtle flex items-center justify-between">
              <h3 className="text-sm font-semibold">{showVideoModal.title as string}</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowVideoModal(null)} className="h-7 w-7 p-0">
                <X className="w-3.5 h-3.5" />
              </Button>
            </div>

            <div className="p-4">
              <div className="aspect-video bg-lia-btn-primary-bg rounded-md flex items-center justify-center">
                <Play className="w-16 h-16 text-white opacity-50" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* LIA Modal exatamente como no preview */}
      {showLiaModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md max-w-2xl w-full">
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
                  className="flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active text-xs h-8"
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
