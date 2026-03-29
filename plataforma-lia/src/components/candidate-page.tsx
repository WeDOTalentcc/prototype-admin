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
  candidate: any
  isOpen: boolean
  onClose: () => void
  onBackToKanban: () => void
  onSendEmail?: (candidate: any) => void
  onSendWhatsApp?: (candidate: any) => void
  onSendAgendamento?: (candidate: any) => void
  onWSIScreening?: (candidate: any) => void
  onAddToVacancy?: (candidate: any) => void
  onAddToList?: (candidate: any) => void
  onSendFeedback?: (candidate: any) => void
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

  const liaScore = candidate.liaAnalysis?.score || 92
  const fitScore = candidate.liaAnalysis?.fitScore || 95

  const experiences = (candidate as any).workHistory || (candidate as any).work_history || (candidate as any).experiences || ((candidate as any).additional_data as any)?.work_history || ((candidate as any).additional_data as any)?.experiences || []
  const education = (candidate as any).education || ((candidate as any).additional_data as any)?.education || []

  return (
    <div className="fixed inset-0 bg-white dark:bg-gray-900 z-30 overflow-hidden flex flex-col">
      {/* Header Compacto como no Preview */}
      <TooltipProvider delayDuration={200}>
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Avatar className="w-10 h-10">
                <AvatarImage src={candidate.avatar_url || candidate.avatar} alt={candidate.name} />
                <AvatarFallback className="text-sm font-medium bg-gray-200 text-gray-700">
                  {candidate.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-base font-semibold text-gray-950 dark:text-gray-50">{candidate.name}</h1>
                  <Badge variant="outline" className="text-xs px-1.5 py-0">
                    {candidate.candidateId || candidate.id}
                  </Badge>
                  <Badge className={`text-xs px-1.5 py-0 ${getScoreColor(liaScore)}`}>
                    {liaScore}% Match
                  </Badge>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                  <span>{candidate.position}</span>
                  <span className="text-gray-400">•</span>
                  <MapPin className="w-3 h-3" />
                  <span>{candidate.location}</span>
                </div>
              </div>
            </div>

            {/* Right Side: Social Icons + LIA + Close */}
            <div className="flex items-center gap-2">
              {/* Social Icons */}
              <div className="flex items-center gap-1 mr-2">
                {(candidate.linkedin_url || candidate.linkedinUrl) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <a 
                        href={candidate.linkedin_url || candidate.linkedinUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
                      >
                        <Linkedin className="w-4 h-4 text-gray-600" />
                      </a>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">LinkedIn</TooltipContent>
                  </Tooltip>
                )}
                {(candidate.github_url || candidate.githubUrl) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <a 
                        href={candidate.github_url || candidate.githubUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
                      >
                        <Github className="w-4 h-4 text-gray-950" />
                      </a>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">GitHub</TooltipContent>
                  </Tooltip>
                )}
                {(candidate.portfolio_url || candidate.portfolioUrl || candidate.website) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <a 
                        href={candidate.portfolio_url || candidate.portfolioUrl || candidate.website} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
                      >
                        <Globe className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      </a>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">Portfolio</TooltipContent>
                  </Tooltip>
                )}
              </div>

              {/* Quick Action Buttons - Same pattern as CandidatePreview */}
              <div className="flex items-center gap-1 border-l border-gray-200 dark:border-gray-600 pl-3 ml-1">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => onSendEmail ? onSendEmail(candidate) : (candidate.email && window.open(`mailto:${candidate.email}`, '_self'))}
                      disabled={!candidate.email && !onSendEmail}
                    >
                      <Mail className="w-4 h-4 text-gray-600 dark:text-gray-400" />
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
                        } else if (candidate.phone) {
                          window.open(`https://wa.me/${candidate.phone.replace(/\D/g, '')}`, '_blank')
                        }
                      }}
                      disabled={!candidate.phone && !onSendWhatsApp}
                    >
                      <Phone className="w-4 h-4 text-gray-600 dark:text-gray-400" />
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
                      <ClipboardCheck className="w-4 h-4 text-gray-600 dark:text-gray-400" />
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
                      <Briefcase className="w-4 h-4 text-gray-600 dark:text-gray-400" />
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
                candidate={candidate}
                onTransportToOpinions={handleAnalysisTransport}
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 hover:bg-gray-100 border border-gray-300 rounded-md"
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
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6">
        <div className="flex">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3 py-2.5 text-xs font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 text-gray-400 border-gray-400'
                  : 'text-gray-800 dark:text-gray-200 hover:text-gray-950 dark:hover:text-gray-50'
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
      <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto p-6">
          {activeTab === 'profile' && (
            <CandidatePageProfileTab
              candidate={candidate}
              experiences={experiences}
              education={education}
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
              <Card className="border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500">
                <CardContent className="p-6">
                  <div
                    className={`text-center cursor-pointer transition-all ${
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
                    <Upload className="w-8 h-8 text-gray-600 dark:text-gray-400 mx-auto mb-3" />
                    <h3 className="text-sm font-medium mb-2">
                      {isDragging ? 'Solte os arquivos aqui' : 'Arraste arquivos ou clique para selecionar'}
                    </h3>
                    <p className="text-xs text-gray-600">PDF, DOC, JPG, PNG, MP4, MP3, WAV até 25MB</p>
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
                        <h4 className="font-medium text-sm truncate">CV_{candidate.name.replace(' ', '_')}_2025.pdf</h4>
                        <p className="text-xs text-gray-800 dark:text-gray-200">2.1 MB • há 3 dias</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-status-success/15 text-status-success text-xs">✓ Verificado</Badge>
                          <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs">LIA: 95%</Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1 mt-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0"
                        onClick={() => {
                          setSelectedFile({ name: 'CV_' + candidate.name + '.pdf', type: 'pdf' })
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
                        <p className="text-xs text-gray-800 dark:text-gray-200">12.3 MB • há 1 dia</p>
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
                        <p className="text-xs text-gray-800 dark:text-gray-200">25.4 MB • 3:45 min</p>
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
                        <p className="text-xs text-gray-800 dark:text-gray-200">45.2 MB • 8:20 min</p>
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
                      <Mic className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">Triagem_Voz_{candidate.name.split(' ')[0]}.mp3</h4>
                        <p className="text-xs text-gray-800 dark:text-gray-200">1.8 MB • 4:32 min • há 1 dia</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs">Triagem WSI</Badge>
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
                            name: `Triagem_Voz_${candidate.name.split(' ')[0]}.mp3`,
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
                        <p className="text-xs text-gray-800 dark:text-gray-200">456 KB • há 2 horas</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-status-success/15 text-status-success text-xs">✓ Verificado</Badge>
                        </div>
                      </div>
                    </div>
                    {(candidate.avatar_url || candidate.avatar) && (
                      <div className="mt-3">
                        <img
                          src={candidate.avatar_url || candidate.avatar}
                          alt="Preview"
                          className="w-full h-24 rounded-md object-cover cursor-pointer hover:opacity-80 transition-opacity"
                          onClick={() => {
                            setSelectedFile({
                              name: 'foto_perfil.jpg',
                              type: 'image',
                              url: candidate.avatar_url || candidate.avatar
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
                        <p className="text-xs text-gray-800 dark:text-gray-200">3.2 MB • há 1 semana</p>
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
                <div className="flex items-center gap-1 border-b border-gray-200 dark:border-gray-700 pb-2">
                  <button
                    onClick={() => setOpinionsSubTab('pareceres')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors ${
                      opinionsSubTab === 'pareceres'
                        ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-b-2 border-gray-900 dark:border-gray-100'
                        : 'text-gray-500 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
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
                        ? 'bg-wedo-purple/10 dark:bg-wedo-purple/20 text-wedo-purple dark:text-wedo-purple border-b-2 border-wedo-purple/30'
                        : 'text-gray-500 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                  >
                    <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                    Análises
                    {savedAnalyses && savedAnalyses.total_analyses > 0 && (
                      <Badge className="text-micro px-1.5 py-0 h-4 ml-1 bg-wedo-purple/15 text-wedo-purple">
                        {savedAnalyses.total_analyses}
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
                          <Card key={i} className="animate-pulse">
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
                          <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-3">
                            <FileText className="w-6 h-6 text-gray-400" />
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
                        {opinionsHistory.map((opinion: any) => {
                          const isExpanded = expandedOpinionId === opinion.id
                          const isWsiOpinion = opinion.opinion_type === 'wsi'
                          const displayScore = isWsiOpinion ? opinion.wsi_score : opinion.score
                          
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
                            <Card key={opinion.id} className="overflow-hidden">
                              <div
                                onClick={() => setExpandedOpinionId(isExpanded ? null : opinion.id)}
                                className="p-3 flex items-center justify-between hover:bg-gray-50 transition-colors cursor-pointer"
                              >
                                <div className="flex items-center gap-2">
                                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                    isWsiOpinion ? 'bg-wedo-purple/15' : 'bg-gray-100 dark:bg-gray-800'
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
                                        <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 flex items-center gap-1">
                                          <Briefcase className="w-2.5 h-2.5" />
                                          #{String(opinion.job_vacancy_id).slice(0, 6)} - {opinion.job_vacancy_title}
                                        </Badge>
                                      ) : !opinion.job_vacancy_id ? (
                                        <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700">
                                          Sem vaga vinculada
                                        </Badge>
                                      ) : null}
                                    </div>
                                    <div className="flex items-center gap-2 mt-0.5">
                                      {displayScore !== null && displayScore !== undefined && (
                                        <span className={`text-micro font-semibold ${getOpinionScoreColor(displayScore, isWsiOpinion)}`}>
                                          {isWsiOpinion ? `WSI: ${displayScore.toFixed(1)}/5` : `Score: ${Math.round(displayScore)}/100`}
                                        </span>
                                      )}
                                      {opinion.archetype && (
                                        <>
                                          <span className="text-gray-300">•</span>
                                          <span className={textStyles.caption}>{opinion.archetype}</span>
                                        </>
                                      )}
                                      {getRecommendationBadge(opinion.recommendation)}
                                    </div>
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  {opinion.created_at && (
                                    <span className="text-micro text-gray-400">
                                      {new Date(opinion.created_at).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })}
                                    </span>
                                  )}
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          handleCopyOpinion(opinion, opinion.opinion_type || 'general')
                                        }}
                                        className="p-1 hover:bg-gray-100 rounded-md transition-colors"
                                      >
                                        {copiedItemId === `opinion-${opinion.id}` ? (
                                          <Check className="w-3.5 h-3.5 text-status-success" />
                                        ) : (
                                          <Copy className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />
                                        )}
                                      </button>
                                    </TooltipTrigger>
                                    <TooltipContent side="top" className="text-micro">Copiar parecer</TooltipContent>
                                  </Tooltip>
                                  {isExpanded ? (
                                    <ChevronUp className="w-4 h-4 text-gray-400" />
                                  ) : (
                                    <ChevronDown className="w-4 h-4 text-gray-400" />
                                  )}
                                </div>
                              </div>
                              
                              {isExpanded && (
                                <div className="px-3 pb-3 pt-0 border-t border-gray-100 space-y-3">
                                  {opinion.summary && (
                                    <div className="pt-3">
                                      <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed">
                                        {opinion.summary}
                                      </p>
                                    </div>
                                  )}
                                  
                                  {opinion.score_breakdown && Object.keys(opinion.score_breakdown).length > 0 && (
                                    <div>
                                      <h5 className={`${textStyles.label} mb-1.5 flex items-center gap-1`}>
                                        <BarChart3 className="w-3 h-3" />
                                        Score Breakdown
                                      </h5>
                                      <div className="grid grid-cols-2 gap-1.5">
                                        {Object.entries(opinion.score_breakdown).map(([key, value]: [string, any]) => (
                                          value !== null && value !== undefined && (
                                            <div key={key} className="flex items-center justify-between text-micro bg-gray-50 dark:bg-gray-700 rounded-full px-2 py-1">
                                              <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}</span>
                                              <span className="font-medium text-gray-800 dark:text-gray-200">{typeof value === 'number' ? `${Math.round(value)}%` : value}</span>
                                            </div>
                                          )
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  
                                  {opinion.strengths && opinion.strengths.length > 0 && (
                                    <div>
                                      <h5 className={`${textStyles.label} text-status-success mb-1 flex items-center gap-1`}>
                                        <CheckCircle className="w-3 h-3" />
                                        Pontos Fortes
                                      </h5>
                                      <ul className="space-y-0.5">
                                        {opinion.strengths.map((s: string, i: number) => (
                                          <li key={i} className={`${textStyles.caption} text-gray-600 flex items-start gap-1`}>
                                            <span className="text-status-success mt-0.5">•</span>
                                            {s}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {opinion.concerns && opinion.concerns.length > 0 && (
                                    <div>
                                      <h5 className={`${textStyles.label} text-status-warning mb-1 flex items-center gap-1`}>
                                        <AlertCircle className="w-3 h-3" />
                                        Pontos de Atenção
                                      </h5>
                                      <ul className="space-y-0.5">
                                        {opinion.concerns.map((c: string, i: number) => (
                                          <li key={i} className={`${textStyles.caption} text-gray-600 flex items-start gap-1`}>
                                            <span className="text-status-warning mt-0.5">•</span>
                                            {c}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {opinion.next_steps && (
                                    <div>
                                      <h5 className={`${textStyles.label} mb-1 flex items-center gap-1`}>
                                        <TrendingUp className="w-3 h-3" />
                                        Próximos Passos
                                      </h5>
                                      <p className={`${textStyles.caption} text-gray-600`}>{opinion.next_steps}</p>
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
                          <Card key={i} className="animate-pulse">
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
                            <Card key={analysis.id} className="overflow-hidden hover:transition-shadow">
                              {/* Card Header */}
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
                                        className="text-micro px-1.5 py-0 h-4 bg-wedo-purple/15 text-wedo-purple"
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
                                          <Copy className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />
                                        )}
                                      </button>
                                    </TooltipTrigger>
                                    <TooltipContent side="top" className="text-micro">Copiar análise</TooltipContent>
                                  </Tooltip>
                                  <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                                </div>
                              </div>
                              
                              {/* Card Content */}
                              {isExpanded && (
                                <div className="px-3 pb-3 border-t border-gray-50">
                                  <div className={`${textStyles.description} text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap bg-gray-50 rounded-md p-3 mt-2`}>
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
          <div className="bg-white dark:bg-gray-800 rounded-md max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 className="text-sm font-semibold">{showVideoModal.title}</h3>
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
          <div className="bg-white dark:bg-gray-800 rounded-md max-w-2xl w-full">
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
                  className="flex-1 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-xs h-8"
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
