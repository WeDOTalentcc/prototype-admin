"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { usePermissions } from "@/utils/permissions"
import { useToast } from "@/hooks/use-toast"
import { textStyles, cardStyles, badgeStyles, formatScorePercent } from '@/lib/design-tokens'
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
import { InsufficientDataModal, validateCandidateDataForOpinion, DataRequirement } from "@/components/modals/insufficient-data-modal"
import { ExperienceHighlightCard } from "@/components/experience-highlight-card"
import { LiaAnalysisModal } from "@/components/modals/lia-analysis-modal"
import { ScreeningMediaModal, ScreeningQuestion, TranscriptionSegment } from "@/components/modals/screening-media-modal"
import { DISCAssessmentModal } from "@/components/disc-assessment-modal"
import { BigFiveModal } from "@/components/big-five-modal"
import { getDemoActivities } from "@/data/demo-activities"

interface LiaChatMessage {
  role: 'user' | 'lia'
  content: string
  timestamp: Date
}

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
  const [activeTab, setActiveTab] = useState<'profile' | 'activities' | 'files' | 'opinions'>('profile')
  const [showLiaModal, setShowLiaModal] = useState(false)
  const [liaConversation, setLiaConversation] = useState("")
  const [expandedActivity, setExpandedActivity] = useState<string | null>(null)
  const [activityFilter, setActivityFilter] = useState<'all' | 'emails' | 'interviews' | 'lia' | 'applications' | 'tests' | 'offers' | 'evaluations'>('all')
  const [activityView, setActivityView] = useState<'list' | 'timeline'>('timeline')
  const [periodFilter, setPeriodFilter] = useState<'7days' | '30days' | '3months' | 'all'>('all')
  const [showAIPredictions, setShowAIPredictions] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<any>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [previewType, setPreviewType] = useState<'pdf' | 'image' | 'video' | 'audio' | null>(null)
  const [audioPlaying, setAudioPlaying] = useState(false)
  const [videoPlaying, setVideoPlaying] = useState(false)
  const [pdfPage, setPdfPage] = useState(1)
  const [pdfTotalPages, setPdfTotalPages] = useState(1)
  const [imageZoom, setImageZoom] = useState(100)
  
  const [candidateFiles, setCandidateFiles] = useState<any[]>([])
  const [fileCategories, setFileCategories] = useState<any[]>([])
  const [isLoadingFiles, setIsLoadingFiles] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  
  const [isAnalyzingWithLia, setIsAnalyzingWithLia] = useState(false)
  const [lastAnalysisDate, setLastAnalysisDate] = useState<Date | null>(candidate?.lastLiaAnalysis ? new Date(candidate.lastLiaAnalysis) : new Date(Date.now() - 2 * 24 * 60 * 60 * 1000))
  
  const [liaChatMessages, setLiaChatMessages] = useState<LiaChatMessage[]>([])
  const [isLiaChatLoading, setIsLiaChatLoading] = useState(false)
  const [liaConversationId, setLiaConversationId] = useState<string | null>(null)
  
  const [opinionsData, setOpinionsData] = useState<any>(null)
  const [isLoadingOpinions, setIsLoadingOpinions] = useState(false)
  const [expandedOpinionId, setExpandedOpinionId] = useState<string | null>(null)
  const [opinionsHistory, setOpinionsHistory] = useState<any[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  
  const [savedAnalyses, setSavedAnalyses] = useState<any>(null)
  const [isLoadingAnalyses, setIsLoadingAnalyses] = useState(false)
  const [opinionsSubTab, setOpinionsSubTab] = useState<'pareceres' | 'analises'>('pareceres')
  const [expandedAnalysisId, setExpandedAnalysisId] = useState<string | null>(null)
  
  const [showUpdateOpinionAlert, setShowUpdateOpinionAlert] = useState(false)
  const [showInsufficientDataModal, setShowInsufficientDataModal] = useState(false)
  const [dataRequirements, setDataRequirements] = useState<DataRequirement[]>([])
  const [lastOpinionDate, setLastOpinionDate] = useState<Date | null>(null)
  const [showLiaAnalysisModal, setShowLiaAnalysisModal] = useState(false)
  
  const [screeningModalOpen, setScreeningModalOpen] = useState(false)
  const [screeningModalData, setScreeningModalData] = useState<{
    type: 'audio' | 'video'
    title: string
    duration: string
    mediaUrl?: string
    questions: ScreeningQuestion[]
    transcription?: TranscriptionSegment[]
    highlights?: string[]
  } | null>(null)
  
  const [discModalOpen, setDiscModalOpen] = useState(false)
  const [discModalData, setDiscModalData] = useState<any>(null)
  const [bigFiveModalOpen, setBigFiveModalOpen] = useState(false)
  const [bigFiveModalCandidate, setBigFiveModalCandidate] = useState<any>(null)
  
  const lastFetchedHistoryCandidateRef = useRef<string | null>(null)
  
  const { toast } = useToast()
  
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
  
  const fetchCandidateFiles = useCallback(async () => {
    if (!candidate?.id) return
    
    setIsLoadingFiles(true)
    try {
      const url = `${BACKEND_URL}/api/v1/candidates/${candidate.id}/files?company_id=demo_company`
      const response = await fetch(url)
      if (response.ok) {
        const data = await response.json()
        setCandidateFiles(data.attachments || [])
        setFileCategories(data.categories || [])
      }
    } catch (error) {
      console.error('Error fetching files:', error)
    } finally {
      setIsLoadingFiles(false)
    }
  }, [candidate?.id])
  
  const fetchOpinionsSummary = useCallback(async () => {
    if (!candidate?.id) return
    setIsLoadingOpinions(true)
    try {
      const response = await fetch(`/api/backend-proxy/opinions/candidate/${candidate.id}/summary?company_id=demo_company`)
      if (response.ok) {
        const data = await response.json()
        setOpinionsData(data)
      }
    } catch (error) {
      console.error('Error fetching opinions:', error)
    } finally {
      setIsLoadingOpinions(false)
    }
  }, [candidate?.id])
  
  const fetchSavedAnalyses = useCallback(async () => {
    if (!candidate?.id) return
    setIsLoadingAnalyses(true)
    try {
      const response = await fetch(`/api/backend-proxy/lia/profile-analysis/candidate/${candidate.id}?company_id=demo_company`)
      if (response.ok) {
        const data = await response.json()
        setSavedAnalyses(data)
      }
    } catch (error) {
      console.error('Error fetching saved analyses:', error)
    } finally {
      setIsLoadingAnalyses(false)
    }
  }, [candidate?.id])
  
  const saveAnalysisToBackend = async (analysis: { type: string; content: string; candidate_id: string }) => {
    try {
      const response = await fetch('/api/backend-proxy/lia/profile-analysis/save?company_id=demo_company', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: analysis.candidate_id,
          analysis_type: analysis.type,
          content: analysis.content,
          candidate_name: candidate?.name || candidate?.nome,
        })
      })
      
      if (response.ok) {
        await fetchSavedAnalyses()
        return true
      }
      return false
    } catch (error) {
      console.error('Error saving analysis:', error)
      return false
    }
  }
  
  const handleAnalysisTransport = async (analysis: { type: string; content: string; candidate_id: string }) => {
    const success = await saveAnalysisToBackend(analysis)
    if (success) {
      toast({
        title: "Análise salva",
        description: "A análise foi adicionada à aba Pareceres e Análises"
      })
    } else {
      toast({
        title: "Erro ao salvar",
        description: "Não foi possível salvar a análise. Tente novamente.",
        variant: "destructive"
      })
    }
  }
  
  const fetchOpinionsHistory = useCallback(async () => {
    if (!candidate?.id) return
    
    if (lastFetchedHistoryCandidateRef.current === candidate.id && opinionsHistory.length > 0) {
      return
    }
    
    lastFetchedHistoryCandidateRef.current = candidate.id
    setIsLoadingHistory(true)
    try {
      const response = await fetch(`/api/backend-proxy/opinions/candidate/${candidate.id}/history?company_id=demo_company`)
      if (response.ok) {
        const data = await response.json()
        setOpinionsHistory(data)
      }
    } catch (error) {
      console.error('Error fetching opinions history:', error)
    } finally {
      setIsLoadingHistory(false)
    }
  }, [candidate?.id, opinionsHistory.length])
  
  useEffect(() => {
    if (activeTab === 'files' && candidate?.id) {
      fetchCandidateFiles()
    }
  }, [activeTab, candidate?.id, fetchCandidateFiles])
  
  useEffect(() => {
    if (candidate?.id) {
      fetchOpinionsSummary()
      fetchSavedAnalyses()
    }
  }, [candidate?.id, fetchOpinionsSummary, fetchSavedAnalyses])
  
  useEffect(() => {
    if (activeTab === 'opinions' && candidate?.id) {
      fetchOpinionsHistory()
    }
  }, [activeTab, candidate?.id, fetchOpinionsHistory])
  
  useEffect(() => {
    if (candidate?.id && lastFetchedHistoryCandidateRef.current !== candidate.id) {
      setOpinionsHistory([])
    }
  }, [candidate?.id])
  
  const sendLiaMessage = async (message: string) => {
    if (!message.trim()) return
    
    setLiaChatMessages(prev => [...prev, {
      role: 'user',
      content: message,
      timestamp: new Date()
    }])
    
    setLiaConversation("")
    setIsLiaChatLoading(true)
    
    try {
      const response = await fetch('/api/backend-proxy/lia/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          context: {
            candidate_id: candidate?.id,
            candidate_name: candidate?.name,
            conversation_id: liaConversationId
          }
        })
      })
      
      if (!response.ok) {
        throw new Error(`Erro: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.success) {
        setLiaChatMessages(prev => [...prev, {
          role: 'lia',
          content: data.response,
          timestamp: new Date()
        }])
        
        if (data.conversation_id) {
          setLiaConversationId(data.conversation_id)
        }
      } else {
        throw new Error(data.error || 'Erro desconhecido')
      }
    } catch (error) {
      console.error('Error sending message to LIA:', error)
      toast({
        title: "Erro ao enviar mensagem",
        description: error instanceof Error ? error.message : "Não foi possível conectar com a LIA. Tente novamente.",
        variant: "destructive"
      })
    } finally {
      setIsLiaChatLoading(false)
    }
  }
  
  const handleFileUpload = async (files: File[]) => {
    if (!candidate?.id || files.length === 0) return
    
    setIsUploading(true)
    setUploadProgress(0)
    
    let successCount = 0
    let errorCount = 0
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      
      if (file.size > 10 * 1024 * 1024) {
        toast({
          title: "Arquivo muito grande",
          description: `${file.name} excede o limite de 10MB`,
          variant: "destructive"
        })
        errorCount++
        continue
      }
      
      const formData = new FormData()
      formData.append('file', file)
      formData.append('candidate_name', candidate.name || 'Candidato')
      formData.append('company_id', 'demo_company')
      formData.append('uploaded_by', 'user')
      formData.append('uploaded_by_name', 'Recrutador')
      
      try {
        const response = await fetch(`${BACKEND_URL}/api/v1/candidates/${candidate.id}/files`, {
          method: 'POST',
          body: formData,
        })
        
        const data = await response.json()
        
        if (data.success) {
          successCount++
        } else {
          errorCount++
          toast({
            title: "Erro no upload",
            description: data.error || `Erro ao enviar ${file.name}`,
            variant: "destructive"
          })
        }
      } catch (error) {
        errorCount++
        console.error('Upload error:', error)
      }
      
      setUploadProgress(Math.round(((i + 1) / files.length) * 100))
    }
    
    setIsUploading(false)
    setUploadProgress(0)
    
    if (successCount > 0) {
      toast({
        title: "Upload concluído",
        description: `${successCount} arquivo(s) enviado(s) com sucesso`
      })
      fetchCandidateFiles()
    }
  }
  
  const handleDeleteFile = async (attachmentId: string) => {
    if (!candidate?.id) return
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/candidates/${candidate.id}/files/${attachmentId}`, {
        method: 'DELETE',
      })
      
      const data = await response.json()
      
      if (data.success) {
        toast({
          title: "Arquivo excluído",
          description: "O arquivo foi removido com sucesso"
        })
        fetchCandidateFiles()
      } else {
        toast({
          title: "Erro",
          description: "Não foi possível excluir o arquivo",
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Delete error:', error)
      toast({
        title: "Erro",
        description: "Erro ao excluir arquivo",
        variant: "destructive"
      })
    }
  }
  
  const handleDownloadFile = (fileUrl: string, fileName: string) => {
    const downloadUrl = `${BACKEND_URL}${fileUrl}`
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = fileName
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
  
  const formatFileSize = (bytes: number): string => {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }
  
  const formatRelativeTime = (dateStr: string): string => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    
    if (diffMins < 1) return 'Agora'
    if (diffMins < 60) return `Há ${diffMins} min`
    if (diffHours < 24) return `Há ${diffHours}h`
    if (diffDays === 1) return 'Ontem'
    if (diffDays < 7) return `Há ${diffDays} dias`
    return date.toLocaleDateString('pt-BR')
  }
  
  const getFileIcon = (fileType: string, mimeType?: string) => {
    if (fileType === 'cv') return <FileText className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
    if (fileType === 'video' || mimeType?.startsWith('video/')) return <FileVideo className="w-3.5 h-3.5 text-red-600" />
    if (fileType === 'certificate') return <Award className="w-3.5 h-3.5 text-amber-600" />
    if (mimeType?.startsWith('image/')) return <Image className="w-3.5 h-3.5 text-green-600" />
    return <File className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
  }
  
  const getCategoryColor = (fileType: string) => {
    const colors: Record<string, { bg: string, text: string }> = {
      'cv': { bg: 'var(--status-error-bg)', text: 'var(--status-error)' },
      'portfolio': { bg: 'var(--gray-200)', text: 'var(--gray-600)' },
      'video': { bg: 'var(--status-error-bg)', text: 'var(--status-error)' },
      'certificate': { bg: 'var(--status-warning-bg)', text: 'var(--status-warning)' },
      'document': { bg: 'var(--gray-100)', text: 'var(--gray-400)' },
      'transcript': { bg: 'var(--gray-100)', text: 'var(--wedo-purple)' },
    }
    return colors[fileType] || colors['document']
  }
  
  const generateNewOpinion = async () => {
    setShowUpdateOpinionAlert(false)
    setIsAnalyzingWithLia(true)
    
    try {
      const candidateInput = {
        id: candidate.id,
        name: candidate.name || 'Candidato',
        position: candidate.currentPosition || candidate.position || candidate.headline || '',
        location: candidate.location || candidate.city || '',
        company: candidate.currentCompany || candidate.company || '',
        cv_text: candidate.cv_text || candidate.cvText || candidate.resumeText || '',
        skills: candidate.skills || [],
        experience_years: candidate.experienceYears || candidate.experience_years || null,
        education: Array.isArray(candidate.education) && candidate.education.length > 0 
          ? candidate.education[0]?.degree || candidate.education[0]?.institution || ''
          : '',
        seniority_level: candidate.seniorityLevel || candidate.seniority_level || ''
      }
      
      const analysisResponse = await fetch(`/api/backend-proxy/analysis/candidates?company_id=demo_company`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidates: [candidateInput],
          analysis_type: 'general'
        })
      })
      
      if (!analysisResponse.ok) {
        throw new Error('Falha na análise')
      }
      
      const analysisData = await analysisResponse.json()
      const result = analysisData.results?.[0]
      
      if (!result) {
        throw new Error('Resultado da análise vazio')
      }
      
      let recommendation = 'pending_review'
      if (result.lia_score >= 70) {
        recommendation = 'approved'
      } else if (result.lia_score < 50) {
        recommendation = 'not_approved'
      }
      
      const opinionPayload = {
        candidate_id: candidate.id,
        opinion_type: 'general',
        source: 'cv_analysis',
        score: result.lia_score || 0,
        archetype: result.archetype || 'Não Identificado',
        recommendation: recommendation,
        summary: result.explanation || 'Análise realizada pela LIA',
        score_breakdown: result.score_breakdown ? {
          skills_match: result.score_breakdown.match_tecnico || null,
          personality_fit: result.score_breakdown.fit_personalidade || null,
          experience_match: result.score_breakdown.relevancia_experiencia || null,
          cultural_fit: result.score_breakdown.alinhamento_cultural || null
        } : {},
        strengths: result.strengths || [],
        concerns: [],
        gaps: result.gaps || [],
        matched_skills: [],
        missing_skills: [],
        next_steps: result.potential_roles ? `Cargos potenciais: ${result.potential_roles.join(', ')}` : 'Validar perfil em entrevista'
      }
      
      const opinionResponse = await fetch(`/api/backend-proxy/opinions?company_id=demo_company&user_id=system`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(opinionPayload)
      })
      
      if (!opinionResponse.ok) {
        const errorData = await opinionResponse.json().catch(() => ({}))
        console.error('Opinion creation error:', errorData)
        throw new Error('Falha ao salvar parecer')
      }
      
      setLastAnalysisDate(new Date())
      
      await fetchOpinionsSummary()
      
      toast({
        title: "Parecer gerado",
        description: "A LIA gerou um novo parecer para o candidato."
      })
    } catch (error) {
      console.error('Error generating opinion:', error)
      toast({
        title: "Erro ao gerar parecer",
        description: "Não foi possível gerar o parecer. Tente novamente.",
        variant: "destructive"
      })
    } finally {
      setIsAnalyzingWithLia(false)
    }
  }
  
  const handleAnalyzeWithLia = async () => {
    if (!candidate?.id) return
    
    const validation = validateCandidateDataForOpinion(candidate)
    
    if (!validation.isValid) {
      setDataRequirements(validation.requirements)
      setShowInsufficientDataModal(true)
      return
    }
    
    if (validation.canProceedWithWarning) {
      setDataRequirements(validation.requirements)
      setShowInsufficientDataModal(true)
      return
    }
    
    try {
      const summaryResponse = await fetch(`/api/backend-proxy/opinions/candidate/${candidate.id}/summary?company_id=demo_company`)
      if (summaryResponse.ok) {
        const data = await summaryResponse.json()
        if (data.current_general_opinion?.created_at) {
          const lastDate = new Date(data.current_general_opinion.created_at)
          const daysSince = Math.floor((Date.now() - lastDate.getTime()) / (1000 * 60 * 60 * 24))
          if (daysSince < 30) {
            setLastOpinionDate(lastDate)
            setShowUpdateOpinionAlert(true)
            return
          }
        }
      }
    } catch (error) {
      console.error('Error checking existing opinion:', error)
    }
    
    await generateNewOpinion()
  }
  
  const handleProceedWithLimitedData = async () => {
    setShowInsufficientDataModal(false)
    
    try {
      const summaryResponse = await fetch(`/api/backend-proxy/opinions/candidate/${candidate.id}/summary?company_id=demo_company`)
      if (summaryResponse.ok) {
        const data = await summaryResponse.json()
        if (data.current_general_opinion?.created_at) {
          const lastDate = new Date(data.current_general_opinion.created_at)
          const daysSince = Math.floor((Date.now() - lastDate.getTime()) / (1000 * 60 * 60 * 24))
          if (daysSince < 30) {
            setLastOpinionDate(lastDate)
            setShowUpdateOpinionAlert(true)
            return
          }
        }
      }
    } catch (error) {
      console.error('Error checking existing opinion:', error)
    }
    
    await generateNewOpinion()
  }
  
  const formatAnalysisDate = (date: Date | null) => {
    if (!date) return 'Nunca analisado'
    
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    
    if (diffMins < 1) return 'Agora mesmo'
    if (diffMins < 60) return `Há ${diffMins} min`
    if (diffHours < 24) return `Há ${diffHours}h`
    if (diffDays === 1) return 'Ontem'
    if (diffDays < 7) return `Há ${diffDays} dias`
    
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
  }

  const generateShortId = (name: string, id: string | number | null | undefined): string => {
    const letters = (name || 'XX').replace(/[^a-zA-Z]/g, '').slice(0, 2).toUpperCase() || 'XX'
    const idStr = String(id || '')
    const digits = idStr.replace(/[^0-9]/g, '')
    const lastFourDigits = digits.length >= 4 
      ? digits.slice(-4) 
      : digits.padStart(4, '0').slice(-4) || String(Math.floor(1000 + Math.random() * 9000))
    return `${letters}${lastFourDigits}`
  }

  if (!isOpen || !candidate) return null

  // Normalizar campos que podem ser arrays para evitar erros .slice().map()
  candidate = {
    ...candidate,
    education: Array.isArray(candidate.education) ? candidate.education : (candidate.education ? [candidate.education] : []),
    workHistory: Array.isArray(candidate.workHistory) ? candidate.workHistory : (candidate.workHistory ? [candidate.workHistory] : []),
    skills: Array.isArray(candidate.skills) ? candidate.skills : (candidate.skills ? [candidate.skills] : []),
    certifications: Array.isArray(candidate.certifications) ? candidate.certifications : (candidate.certifications ? [candidate.certifications] : []),
    projects: Array.isArray(candidate.projects) ? candidate.projects : (candidate.projects ? [candidate.projects] : []),
    awards: Array.isArray(candidate.awards) ? candidate.awards : (candidate.awards ? [candidate.awards] : []),
  }
  
  const formatCurrency = (value: number | string | null | undefined, currency: string = 'BRL'): string => {
    if (value === null || value === undefined || value === '') return 'Não informado'
    const numValue = typeof value === 'string' ? parseFloat(value) : value
    if (isNaN(numValue)) return 'Não informado'
    return numValue.toLocaleString('pt-BR', { style: 'currency', currency })
  }
  
  const getLanguagesData = (): Array<{language: string, proficiency: string}> => {
    const langs = candidate.languages
    if (!langs) return []
    if (Array.isArray(langs)) {
      return langs.map((l: any) => {
        if (typeof l === 'string') return { language: l, proficiency: '' }
        return { language: l.language || l.name || '', proficiency: l.proficiency || l.level || '' }
      }).filter((l: any) => l.language)
    }
    if (typeof langs === 'object') {
      return Object.entries(langs).map(([language, proficiency]) => ({
        language,
        proficiency: String(proficiency)
      }))
    }
    return []
  }
  
  const hasSalaryData = (): boolean => {
    return !!(
      candidate.current_salary ||
      candidate.currentSalary ||
      candidate.desired_salary_min ||
      candidate.desiredSalaryMin ||
      candidate.desired_salary_max ||
      candidate.desiredSalaryMax ||
      candidate.salary_expectation_clt ||
      candidate.salaryExpectationClt ||
      candidate.salary_expectation_pj ||
      candidate.salaryExpectationPj
    )
  }
  
  const hasAddressData = (): boolean => {
    return !!(
      candidate.address_street ||
      candidate.addressStreet ||
      candidate.address_district ||
      candidate.addressDistrict ||
      candidate.location_city ||
      candidate.locationCity ||
      candidate.location_state ||
      candidate.locationState ||
      candidate.address_zip ||
      candidate.addressZip ||
      candidate.location
    )
  }
  
  const getAddressString = (): string => {
    const parts: string[] = []
    const street = candidate.address_street || candidate.addressStreet
    const number = candidate.address_number || candidate.addressNumber
    const complement = candidate.address_complement || candidate.addressComplement
    const district = candidate.address_district || candidate.addressDistrict
    const city = candidate.location_city || candidate.locationCity
    const state = candidate.location_state || candidate.locationState
    const zip = candidate.address_zip || candidate.addressZip
    
    if (street) {
      let line = street
      if (number) line += `, ${number}`
      if (complement) line += ` - ${complement}`
      parts.push(line)
    }
    if (district) parts.push(district)
    if (city && state) {
      parts.push(`${city} - ${state}`)
    } else if (city) {
      parts.push(city)
    } else if (state) {
      parts.push(state)
    }
    if (zip) parts.push(`CEP: ${zip}`)
    
    if (parts.length === 0 && candidate.location) {
      return candidate.location
    }
    return parts.join('\n')
  }
  
  const hasAdditionalDetails = (): boolean => {
    return !!(
      candidate.work_model_preference ||
      candidate.workModelPreference ||
      candidate.contract_type_preference ||
      candidate.contractTypePreference ||
      candidate.willing_to_relocate !== undefined ||
      candidate.willingToRelocate !== undefined ||
      candidate.mobility
    )
  }
  
  const languagesData = getLanguagesData()

  const tabs = [
    { id: 'profile', label: 'Perfil Completo', icon: UserCheck },
    { id: 'activities', label: 'Atividades', icon: Activity },
    { id: 'files', label: 'Arquivos', icon: FileText },
    { id: 'opinions', label: 'Pareceres e Análises', icon: Brain, badge: (opinionsData?.total_opinions || 0) + (savedAnalyses?.total_analyses || 0) }
  ]

  // Activities - Demo data for development team reference
  // In production, replace with real API data. Set NEXT_PUBLIC_USE_DEMO_DATA=false to disable demo data.
  const useDemoData = process.env.NEXT_PUBLIC_USE_DEMO_DATA !== 'false'
  const activities: any[] = useDemoData ? getDemoActivities() : []

  // Filtrar por período
  const filterByPeriod = (activity: any) => {
    if (periodFilter === 'all') return true

    const now = new Date()
    const activityDate = new Date(activity.timestamp)
    const daysDiff = Math.floor((now.getTime() - activityDate.getTime()) / (1000 * 60 * 60 * 24))

    if (periodFilter === '7days') return daysDiff <= 7
    if (periodFilter === '30days') return daysDiff <= 30
    if (periodFilter === '3months') return daysDiff <= 90
    return true
  }

  // Filtrar atividades baseado no filtro selecionado e período
  const filteredActivities = activities.filter(activity => {
    const typeFilter = activityFilter === 'all' ||
      (activityFilter === 'emails' && activity.type.includes('email')) ||
      (activityFilter === 'interviews' && (activity.type.includes('interview') || activity.type === 'video-interview')) ||
      (activityFilter === 'lia' && (activity.type.includes('lia') || activity.type === 'assessment')) ||
      (activityFilter === 'applications' && activity.type === 'job-application') ||
      (activityFilter === 'tests' && activity.type.includes('test')) ||
      (activityFilter === 'offers' && (activity.type === 'offer-sent' || activity.type === 'onboarding')) ||
      (activityFilter === 'evaluations' && (activity.type === 'rubric_evaluation' || activity.type.includes('evaluation')))

    return typeFilter && filterByPeriod(activity)
  })

  // AI Predictions - will come from real API when implemented
  const aiPredictions: any[] = []

  // Sugestões inteligentes da LIA - ações disponíveis para o recrutador
  const liaActions = [
    {
      id: 'auto-contact',
      title: 'Contato Automático',
      icon: '📧',
      buttonText: 'Enviar convite para conversa'
    },
    {
      id: 'add-to-job',
      title: 'Adicionar à Vaga',
      icon: '🎯',
      buttonText: 'Adicionar ao processo seletivo'
    },
    {
      id: 'schedule-interview',
      title: 'Agendar Entrevista',
      icon: '📅',
      buttonText: 'Sugerir horários disponíveis'
    },
    {
      id: 'request-portfolio',
      title: 'Solicitar Portfólio',
      icon: '📂',
      buttonText: 'Enviar solicitação automática'
    },
    {
      id: 'reference-check',
      title: 'Verificar Referências',
      icon: '✅',
      buttonText: 'Iniciar verificação'
    },
    {
      id: 'salary-analysis',
      title: 'Análise Salarial',
      icon: '💰',
      buttonText: 'Gerar relatório salarial'
    }
  ]

  const liaScore = candidate.liaAnalysis?.score || candidate.lia_analysis?.score
  const fitScore = candidate.liaAnalysis?.fitScore || candidate.lia_analysis?.fit_score

  // Function to clean text for copy/paste (remove # and * symbols)
  const cleanTextForCopy = (text: string): string => {
    return text
      .replace(/^#+\s*/gm, '')  // Remove markdown headers
      .replace(/^\*+\s*/gm, '• ') // Convert asterisks to bullets
      .replace(/\*\*/g, '')     // Remove bold markers
      .replace(/\*/g, '')       // Remove italic markers
      .replace(/^-\s+/gm, '• ') // Convert dashes to bullets
      .trim()
  }

  // State for copy feedback
  const [copiedItemId, setCopiedItemId] = useState<string | null>(null)
  
  // State for delete analysis confirmation
  const [analysisToDelete, setAnalysisToDelete] = useState<any | null>(null)
  const [isDeletingAnalysis, setIsDeletingAnalysis] = useState(false)

  // Function to copy opinion content with header
  const handleCopyOpinion = async (opinion: any, type: 'general' | 'wsi') => {
    const isWsiOpinion = type === 'wsi' || opinion.opinion_type === 'wsi'
    const displayScore = isWsiOpinion ? opinion.wsi_score : opinion.score
    
    let textToCopy = `PARECER LIA - ${candidate.name || candidate.nome}\n`
    textToCopy += `Tipo: ${isWsiOpinion ? 'Parecer WSI' : (opinion.job_vacancy_id ? 'Parecer de Vaga' : 'Parecer Geral')}\n`
    if (opinion.job_vacancy_title) {
      textToCopy += `Vaga: ${opinion.job_vacancy_title}\n`
    }
    if (displayScore !== null && displayScore !== undefined) {
      textToCopy += `Score: ${isWsiOpinion ? `${displayScore.toFixed(1)}/5` : `${Math.round(displayScore)}/100`}\n`
    }
    textToCopy += `\n`
    
    if (opinion.summary) {
      textToCopy += `${cleanTextForCopy(opinion.summary)}\n\n`
    }
    if (opinion.strengths?.length > 0) {
      textToCopy += `PONTOS FORTES:\n${opinion.strengths.map((s: string) => `• ${cleanTextForCopy(s)}`).join('\n')}\n\n`
    }
    if (opinion.concerns?.length > 0) {
      textToCopy += `PONTOS DE ATENÇÃO:\n${opinion.concerns.map((c: string) => `• ${cleanTextForCopy(c)}`).join('\n')}\n\n`
    }
    if (opinion.gaps?.length > 0) {
      textToCopy += `GAPS IDENTIFICADOS:\n${opinion.gaps.map((g: string) => `• ${cleanTextForCopy(g)}`).join('\n')}\n\n`
    }
    if (opinion.next_steps) {
      textToCopy += `PRÓXIMOS PASSOS:\n${cleanTextForCopy(opinion.next_steps)}\n`
    }
    
    try {
      await navigator.clipboard.writeText(textToCopy)
      setCopiedItemId(`opinion-${opinion.id}`)
      setTimeout(() => setCopiedItemId(null), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  // Function to copy analysis content with header
  const handleCopyAnalysis = async (analysis: any) => {
    const analysisLabels: Record<string, string> = {
      'bullet_points': 'Pontos-chave',
      'short_paragraph': 'Resumo',
      'detailed_bullets': 'Análise Detalhada'
    }
    
    let textToCopy = `ANÁLISE LIA - ${candidate.name || candidate.nome}\n`
    textToCopy += `Tipo: ${analysisLabels[analysis.analysis_type] || analysis.analysis_type}\n`
    textToCopy += `Data: ${analysis.created_at ? new Date(analysis.created_at).toLocaleDateString('pt-BR') : ''}\n`
    textToCopy += `\n`
    textToCopy += cleanTextForCopy(analysis.content)
    
    try {
      await navigator.clipboard.writeText(textToCopy)
      setCopiedItemId(`analysis-${analysis.id}`)
      setTimeout(() => setCopiedItemId(null), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  // Function to delete analysis
  const handleDeleteAnalysis = async (analysis: any) => {
    setIsDeletingAnalysis(true)
    try {
      const candidateId = candidate.id || candidate.candidate_id
      const response = await fetch(`/api/lia/profile-analysis/${candidateId}/${analysis.analysis_type}?company_id=demo_company`, {
        method: 'DELETE',
      })
      
      if (!response.ok) {
        throw new Error('Failed to delete analysis')
      }
      
      // Remove from local state
      setSavedAnalyses((prev: any) => prev?.filter((a: any) => a.id !== analysis.id) || null)
      setAnalysisToDelete(null)
      setExpandedAnalysisId(null)
      
      toast({
        title: "Análise removida",
        description: "A análise foi removida com sucesso.",
      })
    } catch (error) {
      console.error('Failed to delete analysis:', error)
      toast({
        title: "Erro ao remover",
        description: "Não foi possível remover a análise.",
        variant: "destructive",
      })
    } finally {
      setIsDeletingAnalysis(false)
    }
  }

  const OpinionCard = ({ opinion, isExpanded, onToggle, type }: { 
    opinion: any, 
    isExpanded: boolean, 
    onToggle: () => void,
    type: 'general' | 'wsi'
  }) => {
    const getScoreColor = (score: number | null, isWsi: boolean = false) => {
      if (score === null || score === undefined) return 'text-gray-600'
      if (isWsi) {
        if (score >= 4.0) return 'text-emerald-600'
        if (score >= 3.0) return 'text-amber-600'
        return 'text-red-500'
      } else {
        if (score >= 80) return 'text-emerald-600'
        if (score >= 60) return 'text-amber-600'
        return 'text-red-500'
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
    
    const isWsiOpinion = type === 'wsi' || opinion.opinion_type === 'wsi'
    const displayScore = isWsiOpinion ? opinion.wsi_score : opinion.score
    
    const formatOpinionDate = (dateStr: string | null) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
    }
    
    return (
      <div className={`${cardStyles.default} p-3 overflow-hidden dark:bg-gray-950 dark:border-gray-700`}>
        <div
          onClick={onToggle}
          className="w-full p-3 flex items-center justify-between hover:bg-gray-50 dark:bg-gray-800 transition-colors cursor-pointer"
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onToggle()}
        >
          <div className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              isWsiOpinion ? 'bg-purple-100' : 'bg-gray-100 dark:bg-gray-800'
            }`}>
              {isWsiOpinion ? (
                <Target className="w-4 h-4 text-purple-600" />
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
 <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-700 dark:bg-gray-800 border-gray-200 dark:border-gray-700 flex items-center gap-1">
                    <Briefcase className="w-2.5 h-2.5" />
                    #{String(opinion.job_vacancy_id).slice(0, 6)} - {opinion.job_vacancy_title}
                  </Badge>
                ) : opinion.job_vacancy_title ? (
 <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-700 dark:bg-gray-800 border-gray-200 dark:border-gray-700 flex items-center gap-1">
                    <Briefcase className="w-2.5 h-2.5" />
                    {opinion.job_vacancy_title}
                  </Badge>
                ) : !opinion.job_vacancy_id ? (
                  <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700">
                    Sem vaga vinculada
                  </Badge>
                ) : null}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                {displayScore !== null && displayScore !== undefined && (
                  <span className={`text-micro font-semibold ${getScoreColor(displayScore, isWsiOpinion)}`}>
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
              <span className="text-micro text-gray-400 dark:text-gray-500">{formatOpinionDate(opinion.created_at)}</span>
            )}
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleCopyOpinion(opinion, type)
                  }}
                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                >
                  {copiedItemId === `opinion-${opinion.id}` ? (
                    <Check className="w-3.5 h-3.5 text-green-500" />
                  ) : (
                    <Copy className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600 dark:text-gray-400" />
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent side="top" className="text-micro">Copiar parecer</TooltipContent>
            </Tooltip>
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-400 dark:text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400 dark:text-gray-500" />
            )}
          </div>
        </div>
        
        {isExpanded && (
          <div className="px-3 pb-3 pt-0 border-t border-gray-100 dark:border-gray-700 space-y-3">
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
                      <div key={key} className="flex items-center justify-between text-micro bg-gray-50 dark:bg-gray-800 rounded-full px-2 py-1">
                        <span className="text-gray-600 dark:text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className="font-medium text-gray-800 dark:text-gray-200">{typeof value === 'number' ? `${Math.round(value)}%` : value}</span>
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}
            
            {opinion.strengths && opinion.strengths.length > 0 && (
              <div>
                <h5 className={`${textStyles.label} text-emerald-700 mb-1 flex items-center gap-1`}>
                  <CheckCircle className="w-3 h-3" />
                  Pontos Fortes
                </h5>
                <ul className="space-y-0.5">
                  {opinion.strengths.map((s: string, i: number) => (
                    <li key={i} className={`${textStyles.caption} text-gray-600 dark:text-gray-400 flex items-start gap-1`}>
                      <span className="text-emerald-500 mt-0.5">•</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {opinion.concerns && opinion.concerns.length > 0 && (
              <div>
                <h5 className={`${textStyles.label} text-amber-700 mb-1 flex items-center gap-1`}>
                  <AlertCircle className="w-3 h-3" />
                  Pontos de Atenção
                </h5>
                <ul className="space-y-0.5">
                  {opinion.concerns.map((c: string, i: number) => (
                    <li key={i} className={`${textStyles.caption} text-gray-600 dark:text-gray-400 flex items-start gap-1`}>
                      <span className="text-amber-500 mt-0.5">•</span>
                      {c}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {opinion.gaps && opinion.gaps.length > 0 && (
              <div>
                <h5 className={`${textStyles.label} text-red-600 mb-1 flex items-center gap-1`}>
                  <AlertCircle className="w-3 h-3" />
                  Gaps Identificados
                </h5>
                <ul className="space-y-0.5">
                  {opinion.gaps.map((g: string, i: number) => (
                    <li key={i} className={`${textStyles.caption} text-gray-600 dark:text-gray-400 flex items-start gap-1`}>
                      <span className="text-red-400 mt-0.5">•</span>
                      {g}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {(opinion.matched_skills?.length > 0 || opinion.missing_skills?.length > 0) && (
              <div className="flex gap-3">
                {opinion.matched_skills?.length > 0 && (
                  <div className="flex-1">
                    <h5 className={`${textStyles.label} text-emerald-700 mb-1`}>Skills Match</h5>
                    <div className="flex flex-wrap gap-1">
                      {opinion.matched_skills.map((skill: string, i: number) => (
                        <Badge key={i} className={badgeStyles.success}>
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {opinion.missing_skills?.length > 0 && (
                  <div className="flex-1">
                    <h5 className={`${textStyles.label} text-red-600 mb-1`}>Skills Faltantes</h5>
                    <div className="flex flex-wrap gap-1">
                      {opinion.missing_skills.map((skill: string, i: number) => (
                        <Badge key={i} className={badgeStyles.error}>
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
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
            
            {opinion.recruiter_notes && (
              <div className="bg-amber-50 rounded-md p-2 border border-amber-100">
                <h5 className={`${textStyles.label} text-amber-700 mb-1 flex items-center gap-1`}>
                  <Edit className="w-3 h-3" />
                  Notas do Recrutador
                </h5>
                <p className={`${textStyles.caption} text-amber-800`}>{opinion.recruiter_notes}</p>
              </div>
            )}
            
            {opinion.recruiter_override && (
              <div className="bg-purple-50 rounded-md p-2 border border-purple-100">
                <div className="flex items-center gap-2 mb-1">
                  <h5 className={`${textStyles.label} text-purple-700`}>Override do Recrutador</h5>
                  {getRecommendationBadge(opinion.recruiter_override)}
                </div>
                {opinion.recruiter_override_reason && (
                  <p className={`${textStyles.caption} text-purple-800`}>{opinion.recruiter_override_reason}</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="h-full bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 flex flex-col transition-all duration-300 w-full" style={{ fontFamily: '"Open Sans", sans-serif' }}>
      {/* Header */}
      <TooltipProvider delayDuration={200}>
        <div className="p-3 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-900">
          {/* Top Row: Avatar + Name/Title + Header Action Buttons (LIA, Expand, Close) */}
          <div className="flex items-start gap-3 mb-1.5">
            {/* Avatar */}
            <Avatar className="w-12 h-12 flex-shrink-0 ring-2 ring-white">
              <AvatarImage src={candidate.avatar_url || candidate.avatar || candidate.photo_url || candidate.photoUrl} alt={candidate.name} />
              <AvatarFallback className="font-semibold text-sm bg-gray-200 text-gray-700" style={{ fontFamily: 'Open Sans, sans-serif' }}>
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
                  <Badge className={`text-micro px-1.5 py-0 h-4 flex items-center gap-0.5 ${(candidate.communication_consent ?? candidate.communicationConsent) ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
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
                    className={`h-6 w-6 p-0 ${isFavorite ? 'bg-amber-100' : 'hover:bg-amber-50'}`}
                    onClick={() => {
                      onToggleFavorite?.(candidate.id)
                      toast({ 
                        title: isFavorite ? "Removido dos favoritos" : "Adicionado aos favoritos",
                        description: isFavorite ? "Candidato removido da lista de favoritos" : "Candidato adicionado à lista de favoritos"
                      })
                    }}
                  >
                    <Star className={`w-3.5 h-3.5 ${isFavorite ? 'text-amber-500 fill-amber-500' : 'text-amber-500'}`} />
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
                    className={`p-1 rounded transition-colors ${(candidate.linkedin || candidate.linkedin_url) ? 'hover:bg-blue-50' : 'opacity-30 cursor-default'}`}
                    onClick={(e) => !(candidate.linkedin || candidate.linkedin_url) && e.preventDefault()}
                  >
                    <Linkedin className="w-3.5 h-3.5" style={{ color: (candidate.linkedin || candidate.linkedin_url) ? 'var(--gray-600)' : 'var(--gray-400)' }} />
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
                    className={`p-1 rounded transition-colors ${(candidate.github || candidate.github_url) ? 'hover:bg-gray-100 dark:hover:bg-gray-700' : 'opacity-30 cursor-default'}`}
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
                    className={`p-1 rounded transition-colors ${(candidate.stackoverflow || candidate.stackoverflow_url) ? 'hover:bg-orange-50' : 'opacity-30 cursor-default'}`}
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
                    className={`p-1 rounded transition-colors ${(candidate.twitter || candidate.twitter_url || candidate.x_url) ? 'hover:bg-gray-100 dark:hover:bg-gray-700' : 'opacity-30 cursor-default'}`}
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
                    className={`p-1 rounded transition-colors ${(candidate.behance || candidate.behance_url) ? 'hover:bg-blue-50' : 'opacity-30 cursor-default'}`}
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
                    className={`p-1 rounded transition-colors ${(candidate.portfolio || candidate.portfolio_url) ? 'hover:bg-gray-100 dark:hover:bg-gray-700' : 'opacity-30 cursor-default'}`}
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
                <Badge className="text-micro px-1 py-0 h-4 ml-1" style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}>
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
                      <div className="p-0.5 rounded bg-gray-100 dark:bg-gray-800">
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
                        return score >= 4.0 ? 'text-emerald-600' : score >= 3.0 ? 'text-amber-600' : 'text-red-500'
                      }
                      return score >= 80 ? 'text-emerald-600' : score >= 60 ? 'text-amber-600' : 'text-red-500'
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
                  <div className="w-4 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                  <div className="w-24 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                </div>
                <div className="space-y-1.5">
                  <div className="w-32 h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
                  <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
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
                            <p><span className="inline-block w-2 h-2 rounded-full bg-pink-500 mr-1"></span> Interesses</p>
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
                              className="text-micro px-1.5 py-0 border-0"
                              style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)', color: 'var(--gray-800)' }}
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
                          <Linkedin className="w-3 h-3" className="text-gray-600" />
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
                              className="text-micro px-1.5 py-0 border-0"
                              style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)', color: 'var(--gray-800)' }}
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
                          <Heart className="w-3 h-3 text-pink-600" />
                          <span className={`${textStyles.label} text-pink-700`}>Interesses</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="text-pink-300 cursor-help text-micro">ⓘ</span>
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
                              className="text-micro px-1.5 py-0 bg-pink-50 text-pink-700 border-0"
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
                              className="text-micro px-1.5 py-0 border-0"
                              style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)', color: 'var(--gray-800)' }}
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
                    <Badge variant="outline" className="text-micro px-2 py-0.5 h-5 bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800 flex items-center gap-1">
                      <Globe className="w-3 h-3 text-green-600 dark:text-green-400" />
                      Open to Work
                    </Badge>
                  )}
                  {isTopUniversity === true && (
                    <Badge variant="outline" className="text-micro px-2 py-0.5 h-5 bg-purple-50 text-purple-700 border-purple-200 flex items-center gap-1">
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
                        <Badge variant="outline" className="text-micro px-2 py-0.5 h-5 bg-red-50 text-red-700 border-red-200 flex items-center gap-1 cursor-help">
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
                      <Linkedin className="w-3.5 h-3.5" className="text-gray-600" />
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
                              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-green-50 text-green-700 border border-green-100">
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
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${candidate.is_remote ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-800 dark:text-gray-200'}`}>
                      {candidate.is_remote ? 'Sim' : 'Não'}
                    </Badge>
                  </div>
                )}
                {/* Disponibilidade para Mudança */}
                {(candidate.willing_to_relocate !== undefined || candidate.willingToRelocate !== undefined) && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Aceita Mudança</span>
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${(candidate.willing_to_relocate ?? candidate.willingToRelocate) ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-800 dark:text-gray-200'}`}>
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
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${candidate.mobility ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-800 dark:text-gray-200'}`}>
                      {candidate.mobility === true ? 'Sim' : candidate.mobility === false ? 'Não' : String(candidate.mobility)}
                    </Badge>
                  </div>
                )}
                {/* Consentimento LGPD */}
                {candidate.communication_consent !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Consentimento LGPD</span>
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${candidate.communication_consent ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
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
          <div className="flex flex-col h-full">
            {/* Header com filtros e botão de adicionar */}
            <div className="p-3 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-900">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-medium text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                  Feed de Atividades
                  <Badge className="text-xs px-1 py-0">{filteredActivities.length}</Badge>
                </h4>
                <div className="flex items-center gap-2">
                  {/* Filtro de Período */}
                  <select
                    value={periodFilter}
                    onChange={(e) => setPeriodFilter(e.target.value as any)}
                    className="text-xs px-2 py-1 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 rounded focus:outline-none focus:ring-1 focus:ring-gray-400"
                  >
                    <option value="7days">Últimos 7 dias</option>
                    <option value="30days">Últimos 30 dias</option>
                    <option value="3months">Últimos 3 meses</option>
                    <option value="all">Todo período</option>
                  </select>

                  {/* Toggle de Visualização */}
                  <div className="flex items-center bg-white rounded-md p-0.5 border border-gray-100 dark:border-gray-700">
                    <button
                      onClick={() => setActivityView('timeline')}
                      className={`p-1 rounded transition-colors ${
                        activityView === 'timeline'
                          ? 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                          : 'text-gray-600 dark:text-gray-400 hover:text-gray-800'
                      }`}
                      title="Visualização Timeline"
                    >
                      <GitBranch className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => setActivityView('list')}
                      className={`p-1 rounded transition-colors ${
                        activityView === 'list'
                          ? 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                          : 'text-gray-600 dark:text-gray-400 hover:text-gray-800'
                      }`}
                      title="Visualização Lista"
                    >
                      <List className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <Button
                    onClick={() => setShowLiaModal(true)}
                    size="sm"
                    className="gap-1 px-2 py-1 text-xs h-6 bg-gray-100 hover:bg-gray-200 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700"
                  >
                    <PlusCircle className="w-3 h-3" />
                    Nova Atividade
                  </Button>
                </div>
              </div>

              {/* Filtros com cores */}
              <div className="flex gap-1 flex-wrap">
                <button
                  onClick={() => setActivityFilter('all')}
                  className={`px-2 py-1 text-xs rounded-full transition-colors ${
                    activityFilter === 'all'
                      ? 'bg-gray-600 text-white'
                      : 'bg-gray-100 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
                  }`}
                >
                  Todas
                </button>
                <button
                  onClick={() => setActivityFilter('emails')}
                  className={`px-2 py-1 text-xs rounded-full transition-colors ${
                    activityFilter === 'emails'
                      ? 'bg-gray-700 text-white font-semibold'
                      : 'bg-gray-100 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
                  }`}
                >
                  📧 Emails
                </button>
                <button
                  onClick={() => setActivityFilter('interviews')}
                  className={`px-2 py-1 text-xs rounded-full transition-colors ${
                    activityFilter === 'interviews'
                      ? 'bg-gray-700 text-white font-semibold'
                      : 'bg-gray-100 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
                  }`}
                >
                  🎤 Entrevistas
                </button>
                <button
                  onClick={() => setActivityFilter('tests')}
                  className={`px-2 py-1 text-xs rounded-full transition-colors ${
                    activityFilter === 'tests'
                      ? 'bg-gray-700 text-white font-semibold'
                      : 'bg-gray-100 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
                  }`}
                >
                  📝 Testes
                </button>
                <button
                  onClick={() => setActivityFilter('lia')}
                  className={`px-2 py-1 text-xs rounded-full transition-colors ${
                    activityFilter === 'lia'
                      ? 'text-white font-semibold'
                      : 'hover:opacity-80'
                  }`}
                  style={{
                    backgroundColor: activityFilter === 'lia' ? 'var(--gray-950)' : 'rgba(96, 190, 209, 0.15)',
                    color: activityFilter === 'lia' ? 'white' : 'var(--gray-600)'
                  }}
                >
                  🤖 LIA
                </button>
                <button
                  onClick={() => setActivityFilter('offers')}
                  className={`px-2 py-1 text-xs rounded-full transition-colors ${
                    activityFilter === 'offers'
                      ? 'bg-gray-700 text-white font-semibold'
                      : 'bg-gray-100 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
                  }`}
                >
                  💼 Ofertas
                </button>
                <button
                  onClick={() => setActivityFilter('applications')}
                  className={`px-2 py-1 text-xs rounded-full transition-colors ${
                    activityFilter === 'applications'
                      ? 'bg-gray-700 text-white font-semibold'
                      : 'bg-gray-100 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
                  }`}
                >
                  📋 Inscrições
                </button>
                <button
                  onClick={() => setActivityFilter('evaluations')}
                  className={`px-2 py-1 text-xs rounded-full transition-colors ${
                    activityFilter === 'evaluations'
                      ? 'bg-gray-700 text-white font-semibold'
 : 'text-gray-700 hover:dark:bg-gray-800 dark:hover:bg-gray-700'
                  }`}
                >
                  🎯 Avaliações
                </button>
              </div>
            </div>

            {/* Feed de Atividades com Timeline ou Lista */}
            <div className="flex-1 overflow-y-auto p-3">
              {activityView === 'timeline' ? (
                // Visualização Timeline
                <div className="relative">
                  {/* Card de Previsões da IA - only show when predictions available */}
                  {aiPredictions.length > 0 && (
                    <div className="mb-4 rounded-md bg-white dark:bg-gray-900">
                      <div
                        className="p-3 cursor-pointer hover:bg-gray-100 transition-colors"
                        onClick={() => setShowAIPredictions(!showAIPredictions)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Brain className="w-4 h-4 text-wedo-cyan" />
                            <h4 className="text-xs font-bold text-gray-800 dark:text-gray-200">
                              Previsão de Próximas Etapas - IA
                            </h4>
                            <Badge className="text-xs px-1.5 py-0.5 bg-gray-700 text-white border-gray-600">
                              Análise Preditiva
                            </Badge>
                          </div>
                          <ChevronDown
                            className={`w-4 h-4 text-gray-800 dark:text-gray-200 transition-transform ${
                              showAIPredictions ? 'rotate-180' : ''
                            }`}
                          />
                        </div>
                      </div>
                      {showAIPredictions && (
                        <div className="px-4 pb-4 border-t border-gray-100 dark:border-gray-700">
                          <div className="grid grid-cols-2 gap-3 mt-3">
                            {aiPredictions.map((prediction) => (
                              <div key={prediction.id} className="bg-white dark:bg-gray-900 rounded-md p-2.5">
                                <span className="text-lg">{prediction.icon}</span>
                                <h5 className={textStyles.label}>{prediction.title}</h5>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Empty state when no activities */}
                  {filteredActivities.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-12 px-4">
                      <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                        <Activity className="w-8 h-8 text-gray-600 dark:text-gray-400" />
                      </div>
                      <h3 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                        Nenhuma atividade registrada ainda
                      </h3>
                      <p className="text-xs text-gray-800 dark:text-gray-200 text-center max-w-xs">
                        As atividades aparecerão aqui conforme o processo avança
                      </p>
                    </div>
                  )}

                  {/* Linha vertical da timeline - only show when there are activities */}
                  {filteredActivities.length > 0 && (
                    <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-wedo-green opacity-20"></div>
                  )}

                  {/* Agrupar atividades por data */}
                  {filteredActivities.length > 0 && (() => {
                    const groupedActivities: { [key: string]: typeof activities } = {}

                    filteredActivities.forEach(activity => {
                      // Simplificar agrupamento por data
                      let dateKey = activity.date
                      if (activity.date.includes('Hoje')) dateKey = 'Hoje'
                      else if (activity.date.includes('Ontem')) dateKey = 'Ontem'
                      else if (activity.date.includes('2 dias')) dateKey = 'Esta Semana'
                      else if (activity.date.includes('3 dias')) dateKey = 'Esta Semana'
                      else if (activity.date.includes('4 dias')) dateKey = 'Esta Semana'
                      else if (activity.date.includes('5 dias')) dateKey = 'Esta Semana'
                      else if (activity.date.includes('6 dias')) dateKey = 'Esta Semana'
                      else if (activity.date.includes('semana')) dateKey = 'Últimas Semanas'
                      else dateKey = 'Anteriormente'

                      if (!groupedActivities[dateKey]) {
                        groupedActivities[dateKey] = []
                      }
                      groupedActivities[dateKey].push(activity)
                    })

                    const dateOrder = ['Hoje', 'Ontem', 'Esta Semana', 'Últimas Semanas', 'Anteriormente']

                    return dateOrder.map(dateKey => {
                      if (!groupedActivities[dateKey]) return null

                      return (
                        <div key={dateKey} className="mb-6">
                          {/* Marcador de data */}
                          <div className="relative flex items-center mb-3">
                            <div className="absolute left-4 w-4 h-4 bg-white dark:bg-gray-900 rounded-full border-2 border-gray-400 dark:border-gray-500 z-10"></div>
                            <h3 className="ml-12 text-xs font-bold text-gray-800 dark:text-gray-200">
                              {dateKey}
                            </h3>
                            <div className="ml-3 flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
                          </div>

                          {/* Atividades do grupo */}
                          <div className="space-y-3">
                            {groupedActivities[dateKey].map((activity) => {
                              const ActivityIcon = activity.icon
                              const isExpanded = expandedActivity === activity.id

                              return (
                                <div key={activity.id} className="relative flex items-start ml-12">
                                  {/* Ponto na timeline */}
                                  <div
                                    className="absolute -left-6 w-3 h-3 rounded-full border-2 border-white z-10"
                                    style={{
                                      backgroundColor: activity.iconColor,
                                      marginTop: '14px'
                                    }}
                                  ></div>

                                  {/* Card da atividade */}
                                  <div className="flex-1 border border-gray-100 dark:border-gray-700 rounded-md hover:transition-all">
                                    <div
                                      className="p-3 cursor-pointer hover:bg-white dark:hover:bg-gray-800 transition-colors"
                                      onClick={() => setExpandedActivity(isExpanded ? null : activity.id)}
                                    >
                                      <div className="flex items-start gap-3">
                                        <div
                                          className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                                          style={{ backgroundColor: `${activity.iconColor}20` }}
                                        >
                                          <ActivityIcon className="w-4 h-4" style={{ color: activity.iconColor }} />
                                        </div>

                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                              <h5 className={textStyles.label}>
                                                {activity.title}
                                              </h5>

                                              <div className="flex items-center gap-2 mt-1 flex-wrap">
                                                {activity.jobId && (
                                                  <a
                                                    href={`#vaga-${activity.jobId}`}
                                                    className="text-xs text-gray-700 dark:text-gray-300 hover:text-wedo-cyan-dark hover:underline flex items-center gap-0.5"
                                                    onClick={(e) => e.stopPropagation()}
                                                  >
                                                    <Briefcase className="w-2.5 h-2.5" />
                                                    {activity.jobTitle}
                                                  </a>
                                                )}
                                                <span className={textStyles.bodySmall}>
                                                  {activity.author} • {activity.date}
                                                </span>
                                              </div>

                                              <p className={`${textStyles.bodySmall} mt-1`}>
                                                {activity.summary}
                                              </p>
                                            </div>

                                            <div className="flex items-center gap-1.5">
                                              {activity.score && (
                                                <Badge
                                                  className={`text-xs px-1.5 py-0 h-4 ${
                                                    activity.score >= 80 ? 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-600 font-semibold' :
                                                    activity.score >= 60 ? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 border-gray-100 dark:border-gray-700 font-medium' :
                                                    'bg-red-50 text-red-700 border-red-200 font-medium'
                                                  }`}
                                                >
                                                  {formatScorePercent(activity.score)}
                                                </Badge>
                                              )}
                                              {activity.statusLabel && (
                                                <Badge
                                                  className={`text-xs px-1.5 py-0 h-4 ${
                                                    activity.status === 'approved' || activity.status === 'completed' ? 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-600 font-semibold' :
                                                    activity.status === 'in-progress' ? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 border-gray-100 dark:border-gray-700 font-medium' :
                                                    activity.status === 'rejected' ? 'bg-red-50 text-red-700 border-red-200 font-medium' :
                                                    'bg-white text-gray-600 dark:text-gray-400 border-gray-100'
                                                  }`}
                                                >
                                                  {activity.statusLabel}
                                                </Badge>
                                              )}
                                              <ChevronDown
                                                className={`w-3.5 h-3.5 text-gray-600 dark:text-gray-400 transition-transform ${
                                                  isExpanded ? 'rotate-180' : ''
                                                }`}
                                              />
                                            </div>
                                          </div>
                                        </div>
                                      </div>
                                    </div>

                                    {/* Detalhes expandidos - Renderizadores completos */}
                                    {isExpanded && activity.details && (
                                      <div className="px-3 pb-3 border-t border-gray-100 dark:border-gray-700 bg-white/50 dark:bg-gray-900/50">
                                        {/* EMAIL SENT */}
                                        {activity.type === 'email-sent' && (
                                          <div className="mt-3 space-y-3">
                                            <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden">
                                              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                                                <div className="space-y-1.5">
                                                  <div className="flex items-center gap-2 text-xs">
                                                    <span className="text-gray-500 dark:text-gray-400 w-12">De:</span>
                                                    <span className="text-gray-800 dark:text-gray-200 font-medium">{activity.details.from}</span>
                                                  </div>
                                                  <div className="flex items-center gap-2 text-xs">
                                                    <span className="text-gray-500 dark:text-gray-400 w-12">Para:</span>
                                                    <span className="text-gray-800 dark:text-gray-200">{activity.details.to}</span>
                                                  </div>
                                                  {activity.details.cc && (
                                                    <div className="flex items-center gap-2 text-xs">
                                                      <span className="text-gray-500 dark:text-gray-400 w-12">Cc:</span>
                                                      <span className="text-gray-800 dark:text-gray-200">{activity.details.cc}</span>
                                                    </div>
                                                  )}
                                                  <div className="flex items-center gap-2 text-xs">
                                                    <span className="text-gray-500 dark:text-gray-400 w-12">Assunto:</span>
                                                    <span className="text-gray-800 dark:text-gray-200 font-semibold">{activity.details.subject}</span>
                                                  </div>
                                                </div>
                                              </div>
                                              <div className="px-4 py-3">
                                                <div className="text-xs text-gray-800 dark:text-gray-200 whitespace-pre-line leading-relaxed max-h-48 overflow-y-auto">
                                                  {activity.details.body}
                                                </div>
                                              </div>
                                              {activity.details.attachments && activity.details.attachments.length > 0 && (
                                                <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
                                                  <p className="text-micro text-gray-500 dark:text-gray-400 mb-1">Anexos:</p>
                                                  <div className="flex flex-wrap gap-1">
                                                    {activity.details.attachments.map((att: string, i: number) => (
                                                      <Badge key={i} variant="outline" className="text-micro px-1.5 py-0 bg-white dark:bg-gray-800">
                                                        📎 {att}
                                                      </Badge>
                                                    ))}
                                                  </div>
                                                </div>
                                              )}
                                            </div>
                                            {activity.details.opened && (
                                              <div className="flex items-center gap-2 text-xs text-green-700 bg-green-50 p-2 rounded">
                                                <CheckCircle className="w-3 h-3" />
                                                <span>Email aberto em {activity.details.openedAt}</span>
                                              </div>
                                            )}
                                            {activity.details.suggestedTimes && (
                                              <div className="flex flex-wrap gap-1">
                                                {activity.details.suggestedTimes.map((t: string, i: number) => (
 <Badge key={i} className="text-micro px-2 py-0.5 bg-gray-100 text-gray-700 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                                                    📅 {t}
                                                  </Badge>
                                                ))}
                                              </div>
                                            )}
                                          </div>
                                        )}

                                        {/* INTERVIEW SCHEDULED */}
                                        {activity.type === 'interview-scheduled' && (
                                          <div className="mt-3 space-y-3">
                                            <div className="bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700">
                                              <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                                <Calendar className="w-3 h-3 text-purple-600" />
                                                {activity.details.interviewType}
                                                {activity.details.stage && (
                                                  <Badge className="ml-2 text-micro px-1.5 py-0 bg-purple-50 text-purple-700">{activity.details.stage}</Badge>
                                                )}
                                              </h5>
                                              <div className="grid grid-cols-2 gap-2 mb-3">
                                                <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                                  <p className={textStyles.bodySmall}>Data e Hora</p>
                                                  <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{activity.details.dateTime}</p>
                                                </div>
                                                <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                                  <p className={textStyles.bodySmall}>Duração</p>
                                                  <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{activity.details.duration}</p>
                                                </div>
                                              </div>
                                              <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded mb-3">
                                                <p className={`${textStyles.bodySmall} mb-1`}>📍 Local</p>
                                                <p className="text-xs font-medium text-gray-800 dark:text-gray-200">{activity.details.location}</p>
                                                {activity.details.meetLink && (
                                                  <a href={activity.details.meetLink} target="_blank" rel="noopener noreferrer" className="text-xs text-gray-700 dark:text-gray-300 hover:underline flex items-center gap-1 mt-1">
                                                    <ExternalLink className="w-3 h-3" />
                                                    Acessar link da reunião
                                                  </a>
                                                )}
                                              </div>
                                              {activity.details.interviewers && (
                                                <div className="mb-3">
                                                  <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">👥 Entrevistadores</p>
                                                  <div className="space-y-1">
                                                    {activity.details.interviewers.map((int: any, i: number) => (
                                                      <div key={i} className="flex items-center gap-2 text-xs bg-gray-50 dark:bg-gray-800 p-1.5 rounded">
                                                        <div className="w-5 h-5 rounded-full bg-gray-200 flex items-center justify-center text-micro font-medium text-gray-600 dark:text-gray-400">
                                                          {typeof int === 'string' ? int.charAt(0) : int.name?.charAt(0)}
                                                        </div>
                                                        <span className="font-medium text-gray-800 dark:text-gray-200">{typeof int === 'string' ? int : int.name}</span>
                                                        {typeof int !== 'string' && int.role && <span className="text-gray-500 dark:text-gray-400">- {int.role}</span>}
                                                      </div>
                                                    ))}
                                                  </div>
                                                </div>
                                              )}
                                            </div>
                                          </div>
                                        )}

                                        {/* LIA EVALUATION */}
                                        {activity.type === 'lia-evaluation' && (
                                          <div className="mt-3 space-y-3">
                                            <div className="bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700">
                                              <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                                <Brain className="w-3 h-3 text-wedo-cyan" />
                                                Avaliação Automática da LIA
                                              </h5>
                                              <div className="grid grid-cols-4 gap-2 mb-3">
                                                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                                  <p className="text-base font-bold text-gray-800 dark:text-gray-200">{formatScorePercent(activity.details.technicalScore)}</p>
                                                  <p className={textStyles.bodySmall}>Técnico</p>
                                                </div>
                                                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                                  <p className="text-base font-bold text-gray-800 dark:text-gray-200">{formatScorePercent(activity.details.culturalFit)}</p>
                                                  <p className={textStyles.bodySmall}>Fit Cultural</p>
                                                </div>
                                                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                                  <p className="text-base font-bold text-gray-800 dark:text-gray-200">{formatScorePercent(activity.details.experience)}</p>
                                                  <p className={textStyles.bodySmall}>Experiência</p>
                                                </div>
                                                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                                  <p className="text-base font-bold text-gray-800 dark:text-gray-200">{formatScorePercent(activity.details.softSkills)}</p>
                                                  <p className={textStyles.bodySmall}>Soft Skills</p>
                                                </div>
                                              </div>
                                              {activity.details.strengths && (
                                                <div className="mb-2">
                                                  <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">Pontos Fortes</p>
                                                  <div className="flex flex-wrap gap-1">
                                                    {activity.details.strengths.map((s: string, i: number) => (
                                                      <Badge key={i} className="text-micro px-1.5 py-0 bg-green-50 text-green-700 border-green-200">
                                                        ✓ {s}
                                                      </Badge>
                                                    ))}
                                                  </div>
                                                </div>
                                              )}
                                              <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                                <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">Recomendação</p>
                                                <p className="text-xs text-gray-600 dark:text-gray-400">{activity.details.recommendation}</p>
                                              </div>
                                            </div>
                                          </div>
                                        )}

                                        {/* JOB APPLICATION */}
                                        {activity.type === 'job-application' && (
                                          <div className="mt-3 space-y-3">
                                            <div className="bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700">
                                              <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                                <FileText className="w-3 h-3 text-green-600" />
                                                Candidatura Recebida
                                                <Badge className="ml-2 text-micro px-1.5 py-0 bg-green-50 text-green-700">{activity.details.source}</Badge>
                                              </h5>
                                              <div className="grid grid-cols-2 gap-2 mb-3">
                                                <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                                  <p className={textStyles.bodySmall}>Método</p>
                                                  <p className="text-xs font-medium text-gray-800 dark:text-gray-200">{activity.details.applicationMethod}</p>
                                                </div>
                                                <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                                  <p className={textStyles.bodySmall}>Recebido em</p>
                                                  <p className="text-xs font-medium text-gray-800 dark:text-gray-200">{activity.details.receivedAt}</p>
                                                </div>
                                              </div>
                                              <div className="flex gap-2 mb-3">
                                                {activity.details.resumeAttached && (
 <Badge className="text-micro px-2 py-0.5 bg-gray-100 text-gray-700 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                                                    📄 CV Anexado
                                                  </Badge>
                                                )}
                                                {activity.details.coverLetter && (
                                                  <Badge className="text-micro px-2 py-0.5 bg-purple-50 text-purple-700 border-purple-200">
                                                    ✉️ Carta de Apresentação
                                                  </Badge>
                                                )}
                                              </div>
                                              {activity.details.screeningQuestions && activity.details.screeningQuestions.length > 0 && (
                                                <div>
                                                  <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">📝 Perguntas de Triagem</p>
                                                  <div className="space-y-1">
                                                    {activity.details.screeningQuestions.map((sq: any, i: number) => (
                                                      <div key={i} className={`p-2 rounded text-xs ${sq.passed ? 'bg-green-50' : 'bg-red-50'}`}>
                                                        <p className="font-medium text-gray-800 dark:text-gray-200">{sq.question}</p>
                                                        <p className={sq.passed ? 'text-green-700' : 'text-red-700'}>
                                                          {sq.passed ? '✓' : '✗'} {sq.answer}
                                                        </p>
                                                      </div>
                                                    ))}
                                                  </div>
                                                </div>
                                              )}
                                            </div>
                                          </div>
                                        )}

                                        {/* VOICE SCREENING */}
                                        {activity.type === 'voice-screening' && (
                                          <div className="mt-3 space-y-3">
                                            <div className={`${cardStyles.default} p-3`}>
                                              <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
                                                <Mic className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                                                Triagem por Voz
                                                <Badge className={`ml-2 ${badgeStyles.success}`}>
                                                  {activity.details.questionsAnswered}/{activity.details.totalQuestions} perguntas
                                                </Badge>
                                              </h5>
                                              <div className="grid grid-cols-3 gap-2 mb-3">
                                                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700">
                                                  <p className="text-sm font-bold text-gray-800 dark:text-gray-200">{activity.details.duration}</p>
                                                  <p className={textStyles.caption}>Duração</p>
                                                </div>
                                                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700">
                                                  <p className="text-sm font-bold text-gray-800 dark:text-gray-200">{activity.details.completionRate}%</p>
                                                  <p className={textStyles.caption}>Completude</p>
                                                </div>
                                                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700">
                                                  <p className="text-sm font-bold text-gray-800 dark:text-gray-200">{Math.round(activity.details.transcriptionConfidence * 100)}%</p>
                                                  <p className={textStyles.caption}>Precisão Transcrição</p>
                                                </div>
                                              </div>
                                              {activity.details.wsiScore && (
                                                <div className="mb-3 p-2 bg-gray-100 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700">
                                                  <p className={`${textStyles.labelSmall} text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1`}>
                                                    <Target className="w-3 h-3" />
                                                    Score WSI
                                                  </p>
                                                  <div className="flex items-center justify-between">
                                                    <div className="text-center">
                                                      <p className="text-base font-bold text-gray-900 dark:text-gray-100">{activity.details.wsiScore.overallWsi?.toFixed(1) || '-'}</p>
                                                      <p className={textStyles.caption}>Geral</p>
                                                    </div>
                                                    <Badge className={`${
                                                      activity.details.wsiScore.classification === 'excelente' ? badgeStyles.success :
                                                      activity.details.wsiScore.classification === 'alto' ? 'bg-green-100 text-green-700' :
                                                      activity.details.wsiScore.classification === 'medio' ? badgeStyles.warning :
                                                      badgeStyles.error
                                                    } text-micro`}>
                                                      {activity.details.wsiScore.classification}
                                                    </Badge>
                                                  </div>
                                                </div>
                                              )}
                                              <div className="flex gap-2 mt-3">
                                                <Button 
                                                  size="sm" 
                                                  className="text-xs h-7 hover:dark:bg-gray-800 dark:text-gray-900 dark:hover:bg-gray-200"
                                                  onClick={() => {
                                                    const questions: ScreeningQuestion[] = activity.details.questions?.map((q: any) => ({
                                                      id: q.id,
                                                      question: q.question,
                                                      duration: q.duration,
                                                      transcription: q.transcription,
                                                      timestamp: q.timestamp || `${q.id}:00`,
                                                      analysis: q.analysis
                                                    })) || []
                                                    
                                                    const transcription: TranscriptionSegment[] = activity.details.questions?.map((q: any, idx: number) => ({
                                                      timestamp: q.timestamp || `${idx}:00`,
                                                      speaker: 'Candidato' as const,
                                                      text: q.transcription
                                                    })) || []
                                                    
                                                    setScreeningModalData({
                                                      type: 'audio',
                                                      title: 'Triagem por Voz',
                                                      duration: activity.details.duration,
                                                      mediaUrl: activity.details.audioUrl,
                                                      questions,
                                                      transcription,
                                                      highlights: activity.details.highlights || [],
                                                    })
                                                    setScreeningModalOpen(true)
                                                  }}
                                                >
                                                  <Play className="w-3 h-3 mr-1" />
                                                  Ouvir Triagem
                                                </Button>
                                                {onOpenTriagemDetails && (
                                                  <Button 
                                                    size="sm" 
                                                    variant="outline"
                                                    className="text-xs h-7"
                                                    onClick={() => onOpenTriagemDetails(candidate)}
                                                  >
                                                    <ClipboardCheck className="w-3 h-3 mr-1" />
                                                    Ver Avaliação
                                                  </Button>
                                                )}
                                              </div>
                                            </div>
                                          </div>
                                        )}

                                        {/* TEST COMPLETED */}
                                        {activity.type === 'test-completed' && (
                                          <div className="mt-3 space-y-3">
                                            <div className={`${cardStyles.default} p-3`}>
                                              <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
                                                <Code className="w-3 h-3 text-amber-500" />
                                                {activity.details.testName}
                                                <Badge className={`ml-2 ${activity.score >= 70 ? badgeStyles.success : badgeStyles.warning}`}>
                                                  {activity.score >= 70 ? 'Aprovado' : 'Atenção'}
                                                </Badge>
                                              </h5>
                                              <div className="grid grid-cols-3 gap-2 mb-3">
                                                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700">
                                                  <p className="text-base font-bold text-gray-800 dark:text-gray-200">{activity.details.correctAnswers}/{activity.details.totalQuestions}</p>
                                                  <p className={textStyles.caption}>Acertos</p>
                                                </div>
                                                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700">
                                                  <p className="text-base font-bold text-gray-800 dark:text-gray-200">{activity.details.timeSpent}</p>
                                                  <p className={textStyles.caption}>Tempo</p>
                                                </div>
                                                <div className={`text-center p-2 rounded-md border ${activity.score >= 80 ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800' : activity.score >= 60 ? 'bg-gray-50 dark:bg-gray-800 border-gray-200' : 'bg-gray-100 border-gray-300 dark:border-gray-600'}`}>
                                                  <p className={`text-base font-bold ${activity.score >= 80 ? 'text-green-700 dark:text-green-400' : activity.score >= 60 ? 'text-gray-800 dark:text-gray-200' : 'text-gray-500'}`}>{activity.score}%</p>
                                                  <p className={textStyles.caption}>Score</p>
                                                </div>
                                              </div>
                                              {activity.details.categories && (
                                                <div className="mb-3">
                                                  <p className={`${textStyles.labelSmall} mb-2`}>📊 Performance por Categoria</p>
                                                  <div className="space-y-1.5">
                                                    {activity.details.categories.map((cat: any, i: number) => (
                                                      <div key={i} className="flex items-center gap-2">
                                                        <span className={`${textStyles.caption} w-28 truncate`}>{cat.name}</span>
                                                        <div className="flex-1 bg-gray-100 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
                                                          <div 
                                                            className={`h-full rounded-full ${cat.score >= 80 ? 'bg-green-500' : cat.score >= 60 ? 'bg-green-400/60' : 'bg-gray-300 dark:bg-gray-600'}`}
                                                            style={{ width: `${cat.score}%` }}
                                                          />
                                                        </div>
                                                        <span className="text-xs font-medium text-gray-800 dark:text-gray-200 w-8 text-right">{cat.score}%</span>
                                                      </div>
                                                    ))}
                                                  </div>
                                                </div>
                                              )}
                                            </div>
                                          </div>
                                        )}

                                        {/* OFFER SENT */}
                                        {activity.type === 'offer-sent' && (
                                          <div className="mt-3 space-y-3">
                                            <div className={`${cardStyles.default} p-3`}>
                                              <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
                                                <Gift className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                                                Proposta Salarial
                                                <Badge className={`ml-2 ${badgeStyles.primary}`}>
                                                  {activity.statusLabel || 'Enviada'}
                                                </Badge>
                                              </h5>
                                              <div className="text-center p-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-md border border-gray-200 dark:border-gray-700 mb-3">
 <p className="text-2xl font-bold text-gray-800 dark:text-gray-100">{activity.details.salary}</p>
                                                {activity.details.annualBonus && (
                                                  <p className="text-xs text-gray-600 dark:text-gray-400">+ Bônus: {activity.details.annualBonus}</p>
                                                )}
                                              </div>
                                              <div className="grid grid-cols-2 gap-2 mb-3">
                                                <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                                  <p className={textStyles.bodySmall}>Data de Início</p>
                                                  <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{activity.details.startDate}</p>
                                                </div>
                                                <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                                  <p className={textStyles.bodySmall}>Contrato</p>
                                                  <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{activity.details.contractType}</p>
                                                </div>
                                              </div>
                                              {activity.details.benefits && (
                                                <div className="flex flex-wrap gap-1">
                                                  {activity.details.benefits.map((b: any, i: number) => (
                                                    <Badge key={i} variant="outline" className="text-micro px-1.5 py-0">
                                                      {typeof b === 'object' ? b.name : b}
                                                    </Badge>
                                                  ))}
                                                </div>
                                              )}
                                            </div>
                                          </div>
                                        )}

                                        {/* RUBRIC EVALUATION */}
                                        {activity.type === 'rubric_evaluation' && (
                                          <div className="mt-3 space-y-3">
                                            <div className={`${cardStyles.default} p-3`}>
                                              <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
                                                <ClipboardCheck className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                                                Avaliação por Rubrica (CV vs Vaga)
                                                <Badge className={`ml-2 ${activity.details.overallFit >= 80 ? badgeStyles.success : activity.details.overallFit >= 60 ? badgeStyles.warning : badgeStyles.error}`}>
                                                  {activity.details.overallFit}% fit
                                                </Badge>
                                              </h5>
                                              <div className="text-center p-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-md border border-gray-200 dark:border-gray-700 mb-3">
 <p className="text-3xl font-bold text-gray-800 dark:text-gray-100">{activity.details.overallFit}%</p>
                                                <p className={textStyles.caption}>Fit Geral</p>
                                              </div>
                                              {activity.details.criteriaScores && (
                                                <div className="space-y-1.5 mb-3">
                                                  {activity.details.criteriaScores.slice(0, 4).map((c: any, i: number) => (
                                                    <div key={i} className="flex justify-between text-xs bg-gray-50 dark:bg-gray-800 p-1.5 rounded-md border border-gray-100 dark:border-gray-700">
                                                      <span className="text-gray-800 dark:text-gray-200">{c.criteria}</span>
                                                      <Badge className={`text-micro px-1.5 ${c.score >= 80 ? badgeStyles.success : c.score >= 60 ? badgeStyles.warning : badgeStyles.error}`}>
                                                        {c.score}%
                                                      </Badge>
                                                    </div>
                                                  ))}
                                                </div>
                                              )}
                                              <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded-md border border-gray-100 dark:border-gray-700">
                                                <p className={`${textStyles.labelSmall} mb-1`}>💡 Recomendação</p>
                                                <p className={`${textStyles.caption} text-gray-600`}>{activity.details.recommendation}</p>
                                              </div>
                                            </div>
                                          </div>
                                        )}

                                        {/* ASSESSMENT */}
                                        {activity.type === 'assessment' && (
                                          <div className="mt-3 space-y-3">
                                            <div className={`${cardStyles.default} p-3`}>
                                              <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
                                                <Brain className="w-3 h-3 text-wedo-cyan" />
                                                {activity.details.assessmentType || 'Assessment Comportamental'}
                                                <Badge className={`ml-2 ${badgeStyles.primary}`}>
                                                  {activity.details.profile}
                                                </Badge>
                                              </h5>
                                              <div className="text-center p-3 bg-gradient-to-r from-gray-100 dark:from-gray-800 to-gray-50 rounded-md border border-gray-300 dark:border-gray-600 mb-3">
                                                <p className="text-xl font-bold text-gray-800 dark:text-gray-200">{activity.details.profile}</p>
                                                <p className={textStyles.caption}>{activity.details.profileDescription}</p>
                                              </div>
                                              <div className="grid grid-cols-2 gap-2 mb-3">
                                                <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded-md border border-gray-100 dark:border-gray-700 text-center">
                                                  <p className="text-sm font-bold text-gray-800 dark:text-gray-200">{activity.details.culturalFit || activity.details.culturalFitScore}%</p>
                                                  <p className={textStyles.caption}>Fit Cultural</p>
                                                </div>
                                                <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded-md border border-gray-100 dark:border-gray-700 text-center">
                                                  <p className="text-sm font-bold text-gray-800 dark:text-gray-200">{activity.details.teamworkScore}%</p>
                                                  <p className={textStyles.caption}>Trabalho em Equipe</p>
                                                </div>
                                              </div>
                                              {activity.details.developmentAreas && activity.details.developmentAreas.length > 0 && (
                                                <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded-md border border-gray-200 dark:border-gray-700">
                                                  <p className={`${textStyles.labelSmall} text-gray-800 dark:text-gray-200 mb-1`}>⚠️ Áreas de Desenvolvimento</p>
                                                  <div className="flex flex-wrap gap-1">
                                                    {activity.details.developmentAreas.map((a: string, i: number) => (
                                                      <Badge key={i} variant="outline" className="text-micro px-1.5 py-0 bg-gray-100 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600">
                                                        {a}
                                                      </Badge>
                                                    ))}
                                                  </div>
                                                </div>
                                              )}
                                              <Button 
                                                size="sm" 
                                                variant="outline" 
                                                className="w-full mt-3 text-xs h-7 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:hover:bg-gray-800"
                                                onClick={() => {
                                                  if (activity.details.discScores) {
                                                    setDiscModalData(activity.details)
                                                    setDiscModalOpen(true)
                                                  } else if (activity.details.bigFiveScores) {
                                                    setBigFiveModalCandidate({
                                                      ...candidate,
                                                      bigFiveScores: activity.details.bigFiveScores
                                                    })
                                                    setBigFiveModalOpen(true)
                                                  }
                                                }}
                                              >
                                                <Eye className="w-3 h-3 mr-1" />
                                                Ver Relatório Completo
                                              </Button>
                                            </div>
                                          </div>
                                        )}

                                        {/* VIDEO INTERVIEW */}
                                        {activity.type === 'video-interview' && (
                                          <div className="mt-3 space-y-3">
                                            <div className={`${cardStyles.default} p-3`}>
                                              <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
                                                <Video className="w-3 h-3 text-purple-500" />
                                                Entrevista em Vídeo
                                                <Badge className={`ml-2 ${badgeStyles.success}`}>
                                                  {activity.details.questionsAnswered}/{activity.details.totalQuestions} perguntas
                                                </Badge>
                                              </h5>
                                              <div className="grid grid-cols-3 gap-2 mb-3">
                                                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700">
                                                  <p className="text-sm font-bold text-gray-800 dark:text-gray-200">{activity.details.duration}</p>
                                                  <p className={textStyles.caption}>Duração</p>
                                                </div>
                                                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700">
                                                  <p className="text-sm font-bold text-gray-800 dark:text-gray-200">{activity.details.completionRate || 100}%</p>
                                                  <p className={textStyles.caption}>Completude</p>
                                                </div>
                                                <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700">
                                                  <p className="text-sm font-bold text-gray-800 dark:text-gray-200">{Math.round((activity.details.transcriptionConfidence || 0.95) * 100)}%</p>
                                                  <p className={textStyles.caption}>Confiança</p>
                                                </div>
                                              </div>
                                              {activity.details.wsiScore && (
                                                <div className="mb-3 p-2 bg-purple-50/50 rounded-md border border-purple-100">
                                                  <p className={`${textStyles.labelSmall} text-purple-600 mb-2 flex items-center gap-1`}>
                                                    <Target className="w-3 h-3" />
                                                    Score WSI
                                                  </p>
                                                  <div className="flex items-center justify-between">
                                                    <div className="text-center">
                                                      <p className="text-xs font-bold text-gray-800 dark:text-gray-200">{activity.details.wsiScore.technicalWsi?.toFixed(1) || '-'}</p>
                                                      <p className={textStyles.caption}>Técnico</p>
                                                    </div>
                                                    <div className="text-center">
                                                      <p className="text-xs font-bold text-gray-800 dark:text-gray-200">{activity.details.wsiScore.behavioralWsi?.toFixed(1) || '-'}</p>
                                                      <p className={textStyles.caption}>Comportamental</p>
                                                    </div>
                                                    <div className="text-center">
                                                      <p className="text-base font-bold text-purple-600">{activity.details.wsiScore.overallWsi?.toFixed(1) || '-'}</p>
                                                      <p className={textStyles.caption}>Geral</p>
                                                    </div>
                                                    <Badge className={`${
                                                      activity.details.wsiScore.classification === 'excelente' ? badgeStyles.success :
                                                      activity.details.wsiScore.classification === 'alto' ? 'bg-green-100 text-green-700' :
                                                      activity.details.wsiScore.classification === 'medio' ? badgeStyles.warning :
                                                      badgeStyles.error
                                                    } text-micro`}>
                                                      {activity.details.wsiScore.classification}
                                                    </Badge>
                                                  </div>
                                                </div>
                                              )}
                                              {activity.details.questions && activity.details.questions.length > 0 && (
                                                <div className="mb-3">
                                                  <p className={`${textStyles.labelSmall} mb-2`}>🎬 Perguntas e Respostas</p>
                                                  <div className="space-y-2 max-h-32 overflow-y-auto">
                                                    {activity.details.questions.slice(0, 2).map((q: any) => (
                                                      <div key={q.id} className="bg-gray-50 dark:bg-gray-800 p-2 rounded-md border border-gray-100 dark:border-gray-700">
                                                        <p className={`${textStyles.bodySmall} font-medium text-gray-800`}>P{q.id}: {q.question}</p>
                                                        <p className={`${textStyles.caption} italic text-gray-600 dark:text-gray-400 line-clamp-2`}>{q.transcription}</p>
                                                      </div>
                                                    ))}
                                                  </div>
                                                </div>
                                              )}
                                              {activity.details.overallImpression && (
                                                <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded-md border border-gray-100 dark:border-gray-700 mb-3">
                                                  <p className={`${textStyles.labelSmall} mb-1`}>Impressão Geral</p>
                                                  <p className={`${textStyles.caption} text-gray-600`}>{activity.details.overallImpression}</p>
                                                </div>
                                              )}
                                              <div className="flex gap-2">
                                                <Button 
                                                  size="sm" 
                                                  className="text-xs h-7 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                                                  onClick={() => {
                                                    const questions: ScreeningQuestion[] = activity.details.questions?.map((q: any) => ({
                                                      id: q.id,
                                                      question: q.question,
                                                      duration: q.duration,
                                                      transcription: q.transcription,
                                                      timestamp: q.timestamp || `${q.id}:00`,
                                                      analysis: q.analysis
                                                    })) || []
                                                    
                                                    const transcription: TranscriptionSegment[] = activity.details.questions?.map((q: any, idx: number) => ({
                                                      timestamp: q.timestamp || `${idx}:00`,
                                                      speaker: 'Candidato' as const,
                                                      text: q.transcription
                                                    })) || []
                                                    
                                                    setScreeningModalData({
                                                      type: 'video',
                                                      title: 'Entrevista em Vídeo',
                                                      duration: activity.details.duration,
                                                      mediaUrl: activity.details.videoUrl,
                                                      questions,
                                                      transcription,
                                                      highlights: activity.details.highlights || [],
                                                    })
                                                    setScreeningModalOpen(true)
                                                  }}
                                                >
                                                  <Play className="w-3 h-3 mr-1" />
                                                  Assistir Entrevista
                                                </Button>
                                              </div>
                                            </div>
                                          </div>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )
                    }).filter(Boolean)
                  })()}

                  {/* Indicador de fim da timeline */}
                  <div className="relative flex items-center mt-6">
                    <div className="absolute left-4 w-4 h-4 bg-wedo-green rounded-full z-10"></div>
                    <span className="ml-12 text-xs text-gray-800 dark:text-gray-200">
                      Início do processo • {candidate.name} adicionado ao banco de talentos
                    </span>
                  </div>
                </div>
              ) : (
                // Visualização Lista
                <div className="space-y-2">
                  {/* Empty state for list view */}
                  {filteredActivities.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-12 px-4">
                      <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                        <Activity className="w-8 h-8 text-gray-600 dark:text-gray-400" />
                      </div>
                      <h3 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                        Nenhuma atividade registrada ainda
                      </h3>
                      <p className="text-xs text-gray-800 dark:text-gray-200 text-center max-w-xs">
                        As atividades aparecerão aqui conforme o processo avança
                      </p>
                    </div>
                  )}
                  {filteredActivities.map((activity) => {
                    const ActivityIcon = activity.icon
                    const isExpanded = expandedActivity === activity.id

                    return (
                      <div
                        key={activity.id}
                        className="border border-gray-100 dark:border-gray-700 rounded-md hover:transition-all"
                      >
                        <div
                          className="p-2.5 cursor-pointer hover:bg-white dark:hover:bg-gray-800 transition-colors"
                          onClick={() => setExpandedActivity(isExpanded ? null : activity.id)}
                        >
                          <div className="flex items-start gap-2">
                            <div
                              className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
                              style={{ backgroundColor: `${activity.iconColor}20` }}
                            >
                              <ActivityIcon className="w-3.5 h-3.5" style={{ color: activity.iconColor }} />
                            </div>

                            <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <h5 className={`${textStyles.bodySmall} font-medium`}>
                                    {activity.title}
                                  </h5>

                                  <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                                    {activity.jobId && (
                                      <a
                                        href={`#vaga-${activity.jobId}`}
                                        className="text-xs text-gray-700 dark:text-gray-300 hover:text-wedo-cyan-dark hover:underline flex items-center gap-0.5"
                                        onClick={(e) => e.stopPropagation()}
                                      >
                                        <Briefcase className="w-2.5 h-2.5" />
                                        {activity.jobId} - {activity.jobTitle}
                                      </a>
                                    )}
                                    <span className={textStyles.bodySmall}>
                                      {activity.author} • {activity.authorRole}
                                    </span>
                                    <span className={textStyles.bodySmall}>
                                      {activity.date}
                                    </span>
                                  </div>

                                  <p className={`${textStyles.bodySmall} mt-1`}>
                                    {activity.summary}
                                  </p>
                                </div>

                                <div className="flex items-center gap-1.5">
                                  {activity.score && (
                                    <Badge
                                      className={`text-xs px-1.5 py-0 h-4 ${
                                        activity.score >= 80 ? 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-600 font-semibold' :
                                        activity.score >= 60 ? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 border-gray-100 dark:border-gray-700 font-medium' :
                                        'bg-red-50 text-red-700 border-red-200 font-medium'
                                      }`}
                                    >
                                      {formatScorePercent(activity.score)}
                                    </Badge>
                                  )}
                                  {activity.statusLabel && (
                                    <Badge
                                      className={`text-xs px-1.5 py-0 h-4 ${
                                        activity.status === 'approved' || activity.status === 'completed' ? 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-600 font-semibold' :
                                        activity.status === 'in-progress' ? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 border-gray-100 dark:border-gray-700 font-medium' :
                                        activity.status === 'rejected' ? 'bg-red-50 text-red-700 border-red-200 font-medium' :
                                        'bg-white text-gray-600 dark:text-gray-400 border-gray-100'
                                      }`}
                                    >
                                      {activity.statusLabel}
                                    </Badge>
                                  )}
                                  <ChevronDown
                                    className={`w-3.5 h-3.5 text-gray-600 dark:text-gray-400 transition-transform ${
                                      isExpanded ? 'rotate-180' : ''
                                    }`}
                                  />
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Detalhes expandidos permanecem iguais */}
                        {isExpanded && activity.details && (
                          <div className="px-3 pb-3 border-t border-gray-100 dark:border-gray-700 bg-white/50 dark:bg-gray-900/50">
                            {/* Detalhes específicos por tipo de atividade */}

                            {activity.type === 'lia-evaluation' && (
                              <div className="mt-3 space-y-3">
                                <div className="bg-white dark:bg-gray-900 p-3 rounded">
                                  <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                    <Brain className="w-3 h-3 text-wedo-cyan" />
                                    Avaliação Automática da LIA
                                  </h5>

                                  <div className="grid grid-cols-4 gap-2 mb-3">
                                    <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                      <p className="text-lg font-bold text-gray-800 dark:text-gray-200">{formatScorePercent(activity.details.technicalScore)}</p>
                                      <p className={textStyles.bodySmall}>Técnico</p>
                                    </div>
                                    <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                      <p className="text-lg font-bold text-gray-800 dark:text-gray-200">{formatScorePercent(activity.details.culturalFit)}</p>
                                      <p className={textStyles.bodySmall}>Fit Cultural</p>
                                    </div>
                                    <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                      <p className="text-lg font-bold text-gray-800 dark:text-gray-200">{formatScorePercent(activity.details.experience)}</p>
                                      <p className={textStyles.bodySmall}>Experiência</p>
                                    </div>
                                    <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                      <p className="text-lg font-bold text-gray-800 dark:text-gray-200">{formatScorePercent(activity.details.softSkills)}</p>
                                      <p className={textStyles.bodySmall}>Soft Skills</p>
                                    </div>
                                  </div>

                                  {activity.details.keyHighlights && (
                                    <div className="grid grid-cols-2 gap-2 mb-3">
                                      {activity.details.keyHighlights.map((h: any, i: number) => (
                                        <div key={i} className="flex justify-between text-xs bg-gray-50 dark:bg-gray-800 p-1.5 rounded">
                                          <span className="text-gray-600 dark:text-gray-400">{h.label}:</span>
                                          <span className="font-medium text-gray-800 dark:text-gray-200">{h.value}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}

                                  <div className="mb-3">
                                    <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">Pontos Fortes</p>
                                    <div className="flex flex-wrap gap-1">
                                      {(activity.details.strengths || []).map((s: string, i: number) => (
                                        <Badge key={i} className="text-micro px-1.5 py-0 bg-green-50 text-green-700 border-green-200">
                                          ✓ {s}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>

                                  {activity.details.areasToImprove && activity.details.areasToImprove.length > 0 && (
                                    <div className="mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">Pontos de Atenção</p>
                                      <div className="flex flex-wrap gap-1">
                                        {activity.details.areasToImprove.map((a: string, i: number) => (
                                          <Badge key={i} variant="outline" className="text-micro px-1.5 py-0 bg-yellow-50 text-yellow-700 border-yellow-200">
                                            ⚠ {a}
                                          </Badge>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {activity.details.comparisonToPool && (
                                    <div className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-2 rounded mb-3">
                                      <p className="text-xs text-gray-700 dark:text-gray-300">
                                        📊 Ranking: <strong>#{activity.details.comparisonToPool.ranking}</strong> de {activity.details.comparisonToPool.totalCandidates} candidatos (Top {100 - activity.details.comparisonToPool.percentile}%)
                                      </p>
                                    </div>
                                  )}

                                  <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                    <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">Recomendação da LIA</p>
                                    <p className="text-xs text-gray-800 dark:text-gray-200 whitespace-pre-line">{activity.details.recommendation}</p>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'interview-scheduled' && (
                              <div className="mt-3 space-y-3">
                                <div className="bg-white dark:bg-gray-900 p-3 rounded">
                                  <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                    <Calendar className="w-3 h-3 text-purple-600" />
                                    {activity.details.interviewType}
                                    {activity.details.stage && (
                                      <Badge className="ml-2 text-micro px-1.5 py-0 bg-purple-50 text-purple-700">{activity.details.stage}</Badge>
                                    )}
                                  </h5>

                                  <div className="grid grid-cols-2 gap-2 mb-3">
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                      <p className={textStyles.bodySmall}>Data e Hora</p>
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{activity.details.dateTime}</p>
                                      <p className={textStyles.bodySmall}>{activity.details.timezone}</p>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                      <p className={textStyles.bodySmall}>Duração</p>
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{activity.details.duration}</p>
                                      <p className={textStyles.bodySmall}>Término: {activity.details.endTime}</p>
                                    </div>
                                  </div>

                                  <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded mb-3">
                                    <p className={`${textStyles.bodySmall} mb-1`}>📍 Local</p>
                                    <p className="text-xs font-medium text-gray-800 dark:text-gray-200">{activity.details.location}</p>
                                    {activity.details.meetLink && (
                                      <a href={activity.details.meetLink} target="_blank" rel="noopener noreferrer" className="text-xs text-gray-700 dark:text-gray-300 hover:underline flex items-center gap-1 mt-1">
                                        <ExternalLink className="w-3 h-3" />
                                        Acessar link da reunião
                                      </a>
                                    )}
                                  </div>

                                  {activity.details.interviewers && (
                                    <div className="mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">👥 Entrevistadores</p>
                                      <div className="space-y-1">
                                        {activity.details.interviewers.map((int: any, i: number) => (
                                          <div key={i} className="flex items-center gap-2 text-xs bg-gray-50 dark:bg-gray-800 p-1.5 rounded">
                                            <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-micro font-medium text-gray-600 dark:text-gray-400">
                                              {typeof int === 'string' ? int.charAt(0) : int.name?.charAt(0)}
                                            </div>
                                            <div>
                                              <p className="font-medium text-gray-800 dark:text-gray-200">{typeof int === 'string' ? int : int.name}</p>
                                              {typeof int !== 'string' && int.role && <p className="text-gray-600 dark:text-gray-400">{int.role}</p>}
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {activity.details.topics && (
                                    <div className="mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">📋 Tópicos a Abordar</p>
                                      <div className="flex flex-wrap gap-1">
                                        {activity.details.topics.map((t: string, i: number) => (
                                          <Badge key={i} variant="outline" className="text-micro px-1.5 py-0">{t}</Badge>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {activity.details.previousInterviews && activity.details.previousInterviews.length > 0 && (
                                    <div className="bg-green-50 border border-green-100 p-2 rounded mb-3">
                                      <p className="text-xs font-semibold text-green-800 mb-1">✅ Etapas Anteriores Concluídas</p>
                                      <div className="space-y-1">
                                        {activity.details.previousInterviews.map((pi: any, i: number) => (
                                          <div key={i} className="flex justify-between text-xs">
                                            <span className="text-green-700">{pi.stage} - {pi.type}</span>
                                            <span className="font-medium text-green-800">{pi.score}%</span>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  <div className="flex gap-2">
                                    <Button size="sm" className="text-xs h-7 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200">
                                      <Calendar className="w-3 h-3 mr-1" />
                                      Reagendar
                                    </Button>
                                    <Button size="sm" variant="outline" className="text-xs h-7">
                                      <Mail className="w-3 h-3 mr-1" />
                                      Enviar Lembrete
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'job-application' && (
                              <div className="mt-3 space-y-3">
                                <div className="bg-white dark:bg-gray-900 p-3 rounded">
                                  <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                    <FileText className="w-3 h-3 text-green-600" />
                                    Candidatura Recebida
                                    <Badge className="ml-2 text-micro px-1.5 py-0 bg-green-50 text-green-700">{activity.details.source}</Badge>
                                  </h5>

                                  <div className="grid grid-cols-2 gap-2 mb-3">
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                      <p className={textStyles.bodySmall}>ID da Aplicação</p>
                                      <p className="text-xs font-mono font-medium text-gray-800 dark:text-gray-200">{activity.details.applicationId}</p>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                      <p className={textStyles.bodySmall}>Método</p>
                                      <p className="text-xs font-medium text-gray-800 dark:text-gray-200">{activity.details.applicationMethod}</p>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                      <p className={textStyles.bodySmall}>Recebido em</p>
                                      <p className="text-xs font-medium text-gray-800 dark:text-gray-200">{activity.details.receivedAt}</p>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                      <p className={textStyles.bodySmall}>Dispositivo</p>
                                      <p className="text-xs font-medium text-gray-800 dark:text-gray-200">{activity.details.device}</p>
                                    </div>
                                  </div>

                                  <div className="flex gap-2 mb-3">
                                    {activity.details.resumeAttached && (
 <Badge className="text-micro px-2 py-0.5 bg-gray-100 text-gray-700 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                                        📄 CV: {activity.details.resumeFileName}
                                      </Badge>
                                    )}
                                    {activity.details.coverLetter && (
                                      <Badge className="text-micro px-2 py-0.5 bg-purple-50 text-purple-700 border-purple-200">
                                        ✉️ Carta de Apresentação
                                      </Badge>
                                    )}
                                  </div>

                                  {activity.details.screeningQuestions && activity.details.screeningQuestions.length > 0 && (
                                    <div className="mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">📝 Perguntas de Triagem</p>
                                      <div className="space-y-2">
                                        {activity.details.screeningQuestions.map((sq: any, i: number) => (
                                          <div key={i} className={`p-2 rounded border ${sq.passed ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                                            <p className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1">{sq.question}</p>
                                            <p className={`text-xs ${sq.passed ? 'text-green-700' : 'text-red-700'}`}>
                                              {sq.passed ? '✓' : '✗'} {sq.answer}
                                            </p>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {activity.details.coverLetterPreview && (
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">Carta de Apresentação (Preview)</p>
                                      <p className="text-xs text-gray-600 dark:text-gray-400 italic">"{activity.details.coverLetterPreview}"</p>
                                    </div>
                                  )}

                                  <div className="flex gap-2">
                                    <Button size="sm" variant="outline" className="text-xs h-7">
                                      <Download className="w-3 h-3 mr-1" />
                                      Baixar CV
                                    </Button>
                                    <Button size="sm" variant="outline" className="text-xs h-7">
                                      <Linkedin className="w-3 h-3 mr-1" />
                                      Ver LinkedIn
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'voice-screening' && (
                              <div className="mt-3 space-y-3">
                                <div className="bg-white dark:bg-gray-900 p-3 rounded">
                                  <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                    <Mic className="w-3 h-3 text-red-500" />
                                    Triagem por Voz
                                    <Badge className="ml-2 text-micro px-1.5 py-0 bg-green-50 text-green-700">
                                      {activity.details.questionsAnswered}/{activity.details.totalQuestions} perguntas
                                    </Badge>
                                  </h5>

                                  <div className="grid grid-cols-3 gap-2 mb-3">
                                    <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                      <p className="text-base font-bold text-gray-800 dark:text-gray-200">{activity.details.duration}</p>
                                      <p className={textStyles.bodySmall}>Duração</p>
                                    </div>
                                    <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                      <p className="text-base font-bold text-gray-800 dark:text-gray-200">{activity.details.completionRate}%</p>
                                      <p className={textStyles.bodySmall}>Completude</p>
                                    </div>
                                    <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                      <p className="text-base font-bold text-gray-800 dark:text-gray-200">{Math.round(activity.details.transcriptionConfidence * 100)}%</p>
                                      <p className={textStyles.bodySmall}>Confiança</p>
                                    </div>
                                  </div>

                                  {activity.details.aiAnalysis && (
                                    <div className="mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">🤖 Análise da LIA</p>
                                      <div className="grid grid-cols-3 gap-1">
                                        {Object.entries(activity.details.aiAnalysis).map(([key, value]: [string, any]) => (
                                          <div key={key} className="flex justify-between text-xs bg-gray-50 dark:bg-gray-800 p-1.5 rounded">
                                            <span className="text-gray-600 dark:text-gray-400 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}:</span>
                                            <span className="font-medium text-gray-800 dark:text-gray-200">{value}%</span>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {activity.details.questions && activity.details.questions.length > 0 && (
                                    <div className="mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">📝 Perguntas e Respostas</p>
                                      <div className="space-y-2 max-h-48 overflow-y-auto">
                                        {activity.details.questions.map((q: any) => (
                                          <div key={q.id} className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                            <div className="flex justify-between items-start mb-1">
                                              <p className="text-xs font-medium text-gray-800 dark:text-gray-200">P{q.id}: {q.question}</p>
                                              <Badge className="text-micro px-1 py-0">{q.duration}</Badge>
                                            </div>
                                            <p className="text-xs text-gray-600 dark:text-gray-400 italic">{q.transcription}</p>
                                            {q.analysis && (
                                              <div className="flex gap-2 mt-1">
                                                {q.analysis.keywords?.map((kw: string, i: number) => (
                                                  <Badge key={i} variant="outline" className="text-micro px-1 py-0">{kw}</Badge>
                                                ))}
                                              </div>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {activity.details.highlights && (
                                    <div className="bg-green-50 border border-green-100 p-2 rounded mb-3">
                                      <p className="text-xs font-semibold text-green-800 mb-1">✨ Destaques</p>
                                      <ul className="space-y-0.5">
                                        {activity.details.highlights.map((h: string, i: number) => (
                                          <li key={i} className="text-xs text-green-700 flex items-start gap-1">
                                            <span>•</span> {h}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded mb-3">
                                    <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">Impressão Geral</p>
                                    <p className="text-xs text-gray-600 dark:text-gray-400">{activity.details.overallImpression}</p>
                                  </div>

                                  <div className="flex gap-2">
                                    <Button size="sm" className="text-xs h-7 bg-red-600 hover:bg-red-700">
                                      <Play className="w-3 h-3 mr-1" />
                                      Ouvir Gravação
                                    </Button>
                                    <Button size="sm" variant="outline" className="text-xs h-7">
                                      <FileText className="w-3 h-3 mr-1" />
                                      Ver Transcrição
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'test-completed' && (
                              <div className="mt-3 space-y-3">
                                <div className="bg-white dark:bg-gray-900 p-3 rounded">
                                  <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                    <Code className="w-3 h-3 text-amber-600" />
                                    {activity.details.testName}
                                    <Badge className="ml-2 text-micro px-1.5 py-0 bg-amber-50 text-amber-700">{activity.details.provider}</Badge>
                                  </h5>

                                  <div className="grid grid-cols-4 gap-2 mb-3">
                                    <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                      <p className="text-lg font-bold text-gray-800 dark:text-gray-200">{activity.details.correctAnswers}/{activity.details.totalQuestions}</p>
                                      <p className={textStyles.bodySmall}>Acertos</p>
                                    </div>
                                    <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                      <p className="text-lg font-bold text-gray-800 dark:text-gray-200">{activity.details.timeSpent}</p>
                                      <p className={textStyles.bodySmall}>Tempo</p>
                                    </div>
                                    <div className="text-center p-2 bg-green-50 dark:bg-green-900/20 rounded">
                                      <p className="text-lg font-bold text-green-700 dark:text-green-400">{activity.score}%</p>
                                      <p className={textStyles.bodySmall}>Score</p>
                                    </div>
                                    <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                      <p className="text-sm font-bold text-gray-800 dark:text-gray-200">{activity.details.ranking}</p>
                                      <p className={textStyles.bodySmall}>Ranking</p>
                                    </div>
                                  </div>

                                  {activity.details.categories && (
                                    <div className="mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">📊 Performance por Categoria</p>
                                      <div className="space-y-1">
                                        {activity.details.categories.map((cat: any, i: number) => (
                                          <div key={i} className="flex items-center gap-2">
                                            <span className="text-xs text-gray-600 dark:text-gray-400 w-40 truncate">{cat.name}</span>
                                            <div className="flex-1 bg-gray-100 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
                                              <div 
                                                className={`h-full rounded-full ${cat.score >= 80 ? 'bg-green-500' : cat.score >= 60 ? 'bg-green-400/60' : 'bg-gray-300 dark:bg-gray-600'}`}
                                                style={{ width: `${cat.score}%` }}
                                              />
                                            </div>
                                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200 w-10 text-right">{cat.score}%</span>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {activity.details.codeChallenge && (
                                    <div className="bg-purple-50 border border-purple-100 p-2 rounded mb-3">
                                      <p className="text-xs font-semibold text-purple-800 mb-1">💻 Code Challenge: {activity.details.codeChallenge.name}</p>
                                      <div className="grid grid-cols-3 gap-2 text-xs">
                                        <div>
                                          <span className="text-purple-600">Qualidade:</span>
                                          <span className="font-medium text-purple-800 ml-1">{activity.details.codeChallenge.codeQuality}%</span>
                                        </div>
                                        <div>
                                          <span className="text-purple-600">Funcionalidade:</span>
                                          <span className="font-medium text-purple-800 ml-1">{activity.details.codeChallenge.functionality}%</span>
                                        </div>
                                        <div>
                                          <span className="text-purple-600">Boas Práticas:</span>
                                          <span className="font-medium text-purple-800 ml-1">{activity.details.codeChallenge.bestPractices}%</span>
                                        </div>
                                      </div>
                                      <p className="text-xs text-purple-700 mt-1 italic">{activity.details.codeChallenge.feedback}</p>
                                    </div>
                                  )}

                                  {activity.details.proctoring && (
                                    <div className={`p-2 rounded mb-3 ${activity.details.proctoring.status === 'Clean' ? 'bg-green-50 border border-green-100' : 'bg-yellow-50 border border-yellow-100'}`}>
                                      <p className="text-xs font-semibold mb-1 flex items-center gap-1">
                                        <Shield className="w-3 h-3" />
                                        Proctoring: {activity.details.proctoring.status}
                                      </p>
                                      <p className="text-xs text-gray-600 dark:text-gray-400">
                                        Tab switches: {activity.details.proctoring.tabSwitches} | Copy/Paste: {activity.details.proctoring.copyPasteEvents}
                                      </p>
                                    </div>
                                  )}

                                  <div className="flex gap-2">
                                    <Button size="sm" variant="outline" className="text-xs h-7">
                                      <Download className="w-3 h-3 mr-1" />
                                      Baixar Certificado
                                    </Button>
                                    <Button size="sm" variant="outline" className="text-xs h-7">
                                      <FileText className="w-3 h-3 mr-1" />
                                      Ver Detalhes
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'rubric_evaluation' && (
                              <div className="mt-3 space-y-3">
                                <div className="bg-white dark:bg-gray-900 p-3 rounded">
                                  <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                    <ClipboardCheck className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                                    Avaliação por Rubrica (CV vs Vaga)
 <Badge className="ml-2 text-micro px-1.5 py-0 bg-gray-100 text-gray-700 dark:bg-gray-800">{activity.details.methodVersion}</Badge>
                                  </h5>

                                  <div className="text-center p-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded mb-3">
                                    <p className="text-4xl font-bold text-gray-800 dark:text-gray-200">{activity.details.overallFit}%</p>
                                    <p className={textStyles.bodySmall}>Fit Geral com a Vaga</p>
                                  </div>

                                  {activity.details.criteriaScores && (
                                    <div className="mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">📋 Critérios Avaliados</p>
                                      <div className="space-y-2">
                                        {activity.details.criteriaScores.map((c: any, i: number) => (
                                          <div key={i} className={`p-2 rounded border ${c.status === 'exceeded' ? 'bg-green-50 border-green-200' : c.status === 'partial' ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 dark:bg-gray-800 border-gray-200'}`}>
                                            <div className="flex justify-between items-center mb-1">
                                              <span className="text-xs font-medium text-gray-800 dark:text-gray-200">{c.criteria}</span>
                                              <div className="flex items-center gap-2">
                                                <span className="text-micro text-gray-500 dark:text-gray-400">Peso: {c.weight}%</span>
                                                <Badge className={`text-micro px-1.5 py-0 ${c.score >= 90 ? 'bg-green-100 text-green-700' : c.score >= 70 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                                                  {c.score}%
                                                </Badge>
                                              </div>
                                            </div>
                                            <p className="text-xs text-gray-600 dark:text-gray-400">{c.notes}</p>
                                            <p className="text-micro text-gray-500 dark:text-gray-400 italic mt-1">{c.evidence}</p>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  <div className="grid grid-cols-2 gap-2 mb-3">
                                    {activity.details.mustHaveRequirements && (
                                      <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                        <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">✓ Requisitos Obrigatórios</p>
                                        <div className="space-y-0.5">
                                          {activity.details.mustHaveRequirements.map((r: any, i: number) => (
                                            <p key={i} className={`text-xs ${r.met ? 'text-green-700' : 'text-red-700'}`}>
                                              {r.met ? '✓' : '✗'} {r.requirement}
                                            </p>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                    {activity.details.niceToHaveRequirements && (
                                      <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                        <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">○ Requisitos Desejáveis</p>
                                        <div className="space-y-0.5">
                                          {activity.details.niceToHaveRequirements.map((r: any, i: number) => (
                                            <p key={i} className={`text-xs ${r.met ? 'text-green-700' : 'text-gray-500'}`}>
                                              {r.met ? '✓' : '○'} {r.requirement}
                                            </p>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                  </div>

                                  {activity.details.competitiveAdvantages && (
                                    <div className="bg-green-50 border border-green-100 p-2 rounded mb-3">
                                      <p className="text-xs font-semibold text-green-800 mb-1">🌟 Diferenciais Competitivos</p>
                                      <ul className="space-y-0.5">
                                        {activity.details.competitiveAdvantages.map((a: string, i: number) => (
                                          <li key={i} className="text-xs text-green-700">• {a}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {activity.details.gaps && activity.details.gaps.length > 0 && (
                                    <div className="bg-yellow-50 border border-yellow-100 p-2 rounded mb-3">
                                      <p className="text-xs font-semibold text-yellow-800 mb-1">⚠️ Gaps Identificados</p>
                                      <ul className="space-y-0.5">
                                        {activity.details.gaps.map((g: string, i: number) => (
                                          <li key={i} className="text-xs text-yellow-700">• {g}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                    <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">Recomendação</p>
                                    <p className="text-xs text-gray-600 dark:text-gray-400">{activity.details.recommendation}</p>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'offer-sent' && (
                              <div className="mt-3 space-y-3">
                                <div className="bg-white dark:bg-gray-900 p-3 rounded">
                                  <div className="flex items-center justify-between mb-2">
                                    <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1">
                                      <Gift className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                                      Proposta Salarial
 <Badge className="ml-2 text-micro px-1.5 py-0 bg-gray-100 text-gray-700 dark:bg-gray-800">{activity.details.offerNumber}</Badge>
                                    </h5>
                                    {activity.details.daysRemaining && (
                                      <Badge className="text-micro px-1.5 py-0 bg-yellow-50 text-yellow-700 border-yellow-200">
                                        ⏰ {activity.details.daysRemaining} dias restantes
                                      </Badge>
                                    )}
                                  </div>

                                  <div className="text-center p-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded mb-3">
 <p className="text-3xl font-bold text-gray-800 dark:text-gray-100">{activity.details.salary}</p>
                                    <p className={textStyles.bodySmall}>{activity.details.salaryType}</p>
                                    {activity.details.annualBonus && (
                                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">+ Bônus: {activity.details.annualBonus}</p>
                                    )}
                                    {activity.details.signingBonus && (
                                      <p className="text-xs text-green-700">+ Signing Bonus: {activity.details.signingBonus}</p>
                                    )}
                                  </div>

                                  <div className="grid grid-cols-2 gap-2 mb-3">
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                      <p className={textStyles.bodySmall}>Data de Início</p>
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{activity.details.startDate}</p>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                      <p className={textStyles.bodySmall}>Contrato</p>
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{activity.details.contractType}</p>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                      <p className={textStyles.bodySmall}>Modelo</p>
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{activity.details.workModel}</p>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                      <p className={textStyles.bodySmall}>Válido até</p>
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{activity.details.validUntil}</p>
                                    </div>
                                  </div>

                                  {activity.details.benefits && (
                                    <div className="mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">🎁 Pacote de Benefícios</p>
                                      <div className="grid grid-cols-2 gap-1">
                                        {activity.details.benefits.map((b: any, i: number) => (
                                          <div key={i} className="flex items-center gap-1 text-xs bg-gray-50 dark:bg-gray-800 p-1.5 rounded">
                                            <span>{typeof b === 'object' ? b.icon : '•'}</span>
                                            <span className="text-gray-800 dark:text-gray-200">{typeof b === 'object' ? b.name : b}</span>
                                            {typeof b === 'object' && b.value && (
                                              <span className="text-gray-500 dark:text-gray-400 ml-auto">{b.value}</span>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {activity.details.negotiationHistory && activity.details.negotiationHistory.length > 0 && (
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">📜 Histórico de Negociação</p>
                                      <div className="space-y-1">
                                        {activity.details.negotiationHistory.map((h: any, i: number) => (
                                          <div key={i} className="flex justify-between text-xs">
                                            <span className="text-gray-600 dark:text-gray-400">{h.date} - {h.action}</span>
                                            <Badge variant="outline" className="text-micro px-1">{h.status}</Badge>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {activity.details.negotiationNotes && (
                                    <div className="bg-yellow-50 border border-yellow-100 p-2 rounded mb-3">
                                      <p className="text-xs font-semibold text-yellow-800 mb-1">📝 Notas da Negociação</p>
                                      <p className="text-xs text-yellow-700">{activity.details.negotiationNotes}</p>
                                    </div>
                                  )}

                                  {activity.details.viewedAt && (
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                                      👁 Proposta visualizada em {activity.details.viewedAt}
                                    </p>
                                  )}

                                  <div className="flex gap-2">
 <Button size="sm" className="text-xs h-7 hover:dark:bg-gray-800 dark:text-gray-900 dark:hover:bg-gray-200">
                                      <Mail className="w-3 h-3 mr-1" />
                                      Enviar Lembrete
                                    </Button>
                                    <Button size="sm" variant="outline" className="text-xs h-7">
                                      <FileText className="w-3 h-3 mr-1" />
                                      Ver Proposta
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'technical-test' && (
                              <div className="mt-2 space-y-2">
                                <div className="bg-white dark:bg-gray-900 p-2 rounded">
                                  <p className={`${textStyles.bodySmall} mb-1`}>Teste Técnico</p>
                                  <div className="grid grid-cols-2 gap-1">
                                    <div>
                                      <p className={textStyles.bodySmall}>Tipo</p>
                                      <p className={`${textStyles.label}`}>{activity.details.testType}</p>
                                    </div>
                                    <div>
                                      <p className={textStyles.bodySmall}>Duração</p>
                                      <p className={`${textStyles.label}`}>{activity.details.duration}</p>
                                    </div>
                                    <div>
                                      <p className={textStyles.bodySmall}>Score</p>
                                      <p className={`${textStyles.label}`}>{activity.details.score}/{activity.details.maxScore}</p>
                                    </div>
                                    <div>
                                      <p className={textStyles.bodySmall}>Evaluador</p>
                                      <p className={`${textStyles.label}`}>{activity.details.evaluator}</p>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'english-test' && (
                              <div className="mt-2 space-y-2">
                                <div className="bg-white dark:bg-gray-900 p-2 rounded">
                                  <p className={`${textStyles.bodySmall} mb-1`}>Teste de Inglês</p>
                                  <div className="grid grid-cols-2 gap-1">
                                    <div>
                                      <p className={textStyles.bodySmall}>Nível</p>
                                      <p className={`${textStyles.label}`}>{activity.details.level}</p>
                                    </div>
                                    <div>
                                      <p className={textStyles.bodySmall}>Score CEFR</p>
                                      <p className={`${textStyles.label}`}>{activity.details.score}</p>
                                    </div>
                                    <div>
                                      <p className={textStyles.bodySmall}>Certificação</p>
                                      <p className={`${textStyles.label}`}>{activity.details.certification}</p>
                                    </div>
                                    <div>
                                      <p className={textStyles.bodySmall}>Válido até</p>
                                      <p className={`${textStyles.label}`}>{activity.details.validUntil}</p>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'assessment' && (
                              <div className="mt-3 space-y-3">
                                <div className="bg-white dark:bg-gray-900 p-3 rounded">
                                  <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                    <Brain className="w-3 h-3 text-wedo-cyan" />
                                    {activity.details.assessmentType}
                                    {activity.details.assessmentProvider && (
                                      <Badge className="ml-2 text-micro px-1.5 py-0 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600">{activity.details.assessmentProvider}</Badge>
                                    )}
                                  </h5>

                                  <div className="text-center p-3 bg-gradient-to-r from-gray-100 dark:from-gray-800 to-gray-50 rounded mb-3 border border-gray-300 dark:border-gray-600">
                                    <p className="text-2xl font-bold text-gray-800 dark:text-gray-200">{activity.details.profile}</p>
                                    <p className={textStyles.bodySmall}>{activity.details.profileDescription}</p>
                                  </div>

                                  {activity.details.discScores && (
                                    <div className="grid grid-cols-4 gap-2 mb-3">
                                      <div className="text-center p-2 bg-gray-100 dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-600">
                                        <p className="text-lg font-bold text-gray-900 dark:text-gray-50">{activity.details.discScores.dominance}</p>
                                        <p className={textStyles.bodySmall}>D</p>
                                      </div>
                                      <div className="text-center p-2 bg-gray-100 dark:bg-gray-800 rounded border border-gray-900 dark:border-gray-50/15">
                                        <p className="text-lg font-bold text-gray-900 dark:text-gray-50/80">{activity.details.discScores.influence}</p>
                                        <p className={textStyles.bodySmall}>I</p>
                                      </div>
                                      <div className="text-center p-2 bg-gray-100 rounded border border-gray-200 dark:border-gray-700">
                                        <p className="text-lg font-bold text-gray-900 dark:text-gray-50">{activity.details.discScores.steadiness}</p>
                                        <p className={textStyles.bodySmall}>S</p>
                                      </div>
                                      <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                                        <p className="text-lg font-bold text-gray-500 dark:text-gray-400">{activity.details.discScores.conscientiousness}</p>
                                        <p className={textStyles.bodySmall}>C</p>
                                      </div>
                                    </div>
                                  )}

                                  {activity.details.primaryTraits && (
                                    <div className="mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">🎯 Características Principais</p>
                                      <div className="space-y-1">
                                        {activity.details.primaryTraits.map((t: any, i: number) => (
                                          <div key={i} className="flex items-center gap-2">
                                            <span className="text-xs text-gray-600 dark:text-gray-400 w-32 truncate">{t.trait}</span>
                                            <div className="flex-1 bg-gray-100 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
                                              <div 
 className={`h-full rounded-full ${t.score >= 80 ? 'bg-gray-900' : t.score >= 60 ? 'bg-gray-200' : 'bg-gray-300 dark:bg-gray-600'}`}
                                                style={{ width: `${t.score}%` }}
                                              />
                                            </div>
                                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200 w-10 text-right">{t.score}%</span>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  <div className="grid grid-cols-2 gap-2 mb-3">
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded text-center">
                                      <p className="text-base font-bold text-gray-800 dark:text-gray-200">{activity.details.culturalFitScore}%</p>
                                      <p className={textStyles.bodySmall}>Fit Cultural</p>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded text-center">
                                      <p className="text-base font-bold text-gray-800 dark:text-gray-200">{activity.details.leadershipScore}%</p>
                                      <p className={textStyles.bodySmall}>Liderança</p>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded text-center">
                                      <p className="text-base font-bold text-gray-800 dark:text-gray-200">{activity.details.teamworkScore}%</p>
                                      <p className={textStyles.bodySmall}>Trabalho em Equipe</p>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded text-center">
                                      <p className="text-base font-bold text-gray-800 dark:text-gray-200">{activity.details.adaptabilityScore}%</p>
                                      <p className={textStyles.bodySmall}>Adaptabilidade</p>
                                    </div>
                                  </div>

                                  {activity.details.leadershipStrengths && (
                                    <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-2 rounded mb-3">
                                      <p className="text-xs font-semibold text-green-700 dark:text-green-400 mb-1">💪 Pontos Fortes de Liderança</p>
                                      <ul className="space-y-0.5">
                                        {activity.details.leadershipStrengths.map((s: string, i: number) => (
                                          <li key={i} className="text-xs text-gray-800 dark:text-gray-200">✓ {s}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {activity.details.developmentAreas && activity.details.developmentAreas.length > 0 && (
                                    <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-2 rounded mb-3">
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">📈 Áreas de Desenvolvimento</p>
                                      <ul className="space-y-0.5">
                                        {activity.details.developmentAreas.map((a: string, i: number) => (
                                          <li key={i} className="text-xs text-gray-600 dark:text-gray-400">• {a}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {activity.details.comparisonToRole && (
                                    <div className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-2 rounded mb-3">
                                      <p className="text-xs text-gray-800 dark:text-gray-200">
                                        📊 Match com perfil ideal ({activity.details.comparisonToRole.idealProfile}): <strong className="text-gray-900 dark:text-gray-100">{activity.details.comparisonToRole.matchPercentage}%</strong>
                                      </p>
                                    </div>
                                  )}

                                  <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                    <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">Recomendação</p>
                                    <p className="text-xs text-gray-600 dark:text-gray-400">{activity.details.recommendation}</p>
                                  </div>

                                  <div className="flex gap-2 mt-3">
                                    <Button size="sm" variant="outline" className="text-xs h-7">
                                      <Download className="w-3 h-3 mr-1" />
                                      Baixar Relatório
                                    </Button>
                                    <Button 
                                      size="sm" 
                                      variant="outline" 
                                      className="text-xs h-7 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:hover:bg-gray-800"
                                      onClick={() => {
                                        if (activity.details.discScores) {
                                          setDiscModalData(activity.details)
                                          setDiscModalOpen(true)
                                        } else if (activity.details.bigFiveScores) {
                                          setBigFiveModalCandidate({
                                            ...candidate,
                                            bigFiveScores: activity.details.bigFiveScores
                                          })
                                          setBigFiveModalOpen(true)
                                        }
                                      }}
                                    >
                                      <Eye className="w-3 h-3 mr-1" />
                                      Ver Completo
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'data-collection' && (
                              <div className="mt-2 space-y-2">
                                <div className="bg-white dark:bg-gray-900 p-2 rounded">
                                  <p className={`${textStyles.bodySmall} mb-1`}>Coleta de Dados</p>
                                  <div className="grid grid-cols-2 gap-1">
                                    <div>
                                      <p className={textStyles.bodySmall}>Documentos Verificados</p>
                                      <div className="flex flex-wrap gap-1">
                                        {activity.details.documentsVerified?.map((doc: string) => (
                                          <Badge key={doc} variant="outline" className="text-xs px-1.5 py-0">
                                            {doc}
                                          </Badge>
                                        ))}
                                      </div>
                                    </div>
                                    <div>
                                      <p className={textStyles.bodySmall}>Referências</p>
                                      <p className={`${textStyles.label}`}>{activity.details.referencesChecked}</p>
                                    </div>
                                    <div>
                                      <p className={textStyles.bodySmall}>Verificação</p>
                                      <p className={`${textStyles.label}`}>{activity.details.backgroundCheck}</p>
                                    </div>
                                    <div>
                                      <p className={textStyles.bodySmall}>Completeness</p>
                                      <p className={`${textStyles.label}`}>{activity.details.dataCompleteness}</p>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'onboarding' && (
                              <div className="mt-3 space-y-3">
                                <div className="bg-white dark:bg-gray-900 p-3 rounded">
                                  <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                    <UserCheck className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                                    Processo de Onboarding
                                  </h5>

                                  {/* Checklist de Onboarding */}
                                  <div className="bg-green-50 p-2 rounded mb-3">
                                    <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">
                                      📋 Checklist de Integração
                                    </p>
                                    <div className="space-y-1">
                                      <div className="flex items-center gap-2 text-xs">
                                        <CheckCircle className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                                        <span className="text-gray-800 dark:text-gray-200">Oferta aceita e assinada</span>
                                      </div>
                                      <div className="flex items-center gap-2 text-xs">
                                        <CheckCircle className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                                        <span className="text-gray-800 dark:text-gray-200">Documentação enviada</span>
                                      </div>
                                      <div className="flex items-center gap-2 text-xs">
                                        <Clock className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                                        <span className="text-gray-800 dark:text-gray-200">Equipamentos solicitados</span>
                                      </div>
                                      <div className="flex items-center gap-2 text-xs">
                                        <Clock className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                                        <span className="text-gray-800 dark:text-gray-200">Acessos em configuração</span>
                                      </div>
                                      <div className="flex items-center gap-2 text-xs">
                                        <AlertCircle className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                                        <span className="text-gray-800 dark:text-gray-200">Buddy designado (pendente)</span>
                                      </div>
                                    </div>
                                  </div>

                                  {/* Informações Detalhadas */}
                                  <div className="grid grid-cols-2 gap-2 mb-3">
                                    <div className="bg-white dark:bg-gray-900 p-2 rounded">
                                      <p className={`${textStyles.bodySmall} mb-1`}>Data de Início</p>
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">
                                        {activity.details.startDate}
                                      </p>
                                      <p className={textStyles.bodySmall}>Segunda-feira</p>
                                    </div>
                                    <div className="bg-white dark:bg-gray-900 p-2 rounded">
                                      <p className={`${textStyles.bodySmall} mb-1`}>Gestor Responsável</p>
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">
                                        {activity.details.onboardingManager}
                                      </p>
                                      <p className={textStyles.bodySmall}>People & Culture</p>
                                    </div>
                                  </div>

                                  {/* Cronograma da Primeira Semana */}
                                  <div className="bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-2 rounded mb-3">
                                    <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">
                                      📅 Agenda - Primeira Semana
                                    </p>
                                    <div className="space-y-1 text-xs text-gray-800 dark:text-gray-200">
                                      <div className="flex items-start gap-2">
                                        <span className="font-medium">Seg:</span>
                                        <span>Welcome meeting + Setup workspace</span>
                                      </div>
                                      <div className="flex items-start gap-2">
                                        <span className="font-medium">Ter:</span>
                                        <span>Apresentação da equipe + Cultura</span>
                                      </div>
                                      <div className="flex items-start gap-2">
                                        <span className="font-medium">Qua:</span>
                                        <span>Treinamento de sistemas e processos</span>
                                      </div>
                                      <div className="flex items-start gap-2">
                                        <span className="font-medium">Qui:</span>
                                        <span>1:1 com gestor + Definição de metas</span>
                                      </div>
                                      <div className="flex items-start gap-2">
                                        <span className="font-medium">Sex:</span>
                                        <span>Primeira tarefa + Feedback session</span>
                                      </div>
                                    </div>
                                  </div>

                                  {/* Status dos Preparativos */}
                                  <div className="grid grid-cols-2 gap-2">
                                    <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
                                      <FileText className="w-4 h-4 mx-auto text-gray-800 dark:text-gray-200 mb-1" />
                                      <p className={textStyles.bodySmall}>Documentos</p>
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{activity.details.documentsStatus}</p>
                                    </div>
                                    <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
                                      <Building className="w-4 h-4 mx-auto text-gray-600 dark:text-gray-400 mb-1" />
                                      <p className={textStyles.bodySmall}>Equipamentos</p>
                                      <p className="text-xs font-semibold text-gray-900 dark:text-gray-50">{activity.details.equipmentStatus}</p>
                                    </div>
                                    <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
                                      <Shield className="w-4 h-4 mx-auto text-gray-800 dark:text-gray-200 mb-1" />
                                      <p className={textStyles.bodySmall}>Acessos</p>
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{activity.details.accessesStatus}</p>
                                    </div>
                                    <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
                                      <Users className="w-4 h-4 mx-auto text-gray-800 dark:text-gray-200 mb-1" />
                                      <p className={textStyles.bodySmall}>Buddy</p>
                                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">A definir</p>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'interview-note' && (
                              <div className="mt-2 space-y-2">
                                {activity.details.technicalQuestions && (
                                  <div className="bg-white dark:bg-gray-900 p-2 rounded">
                                    <p className={`${textStyles.bodySmall} mb-1`}>Questões Técnicas</p>
                                    <div className="space-y-1">
                                      {activity.details.technicalQuestions.map((q: any, i: number) => (
                                        <div key={i} className="flex items-center justify-between">
                                          <span className={textStyles.bodySmall}>{q.question}</span>
                                          <Badge className="text-xs px-1 py-0">{q.score}/10</Badge>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {activity.details.overallScore && (
                                  <div className="bg-white dark:bg-gray-900 p-2 rounded">
                                    <div className="flex items-center justify-between">
                                      <span className={textStyles.bodySmall}>Score Geral</span>
                                      <span className="text-xs font-bold text-gray-800 dark:text-gray-200">{activity.details.overallScore}/10</span>
                                    </div>
                                    <p className={`${textStyles.bodySmall} mt-1`}>
                                      {activity.details.recommendation}
                                    </p>
                                  </div>
                                )}
                              </div>
                            )}

                            {activity.type === 'lia-screening' && activity.details.conversation && (
                              <div className="mt-2 space-y-2">
                                <div className="bg-white dark:bg-gray-800 p-2 rounded max-h-48 overflow-y-auto">
                                  <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">{activity.platform}</p>
                                  <div className="space-y-2">
                                    {activity.details.conversation.map((msg: any, i: number) => (
                                      <div
                                        key={i}
                                        className={`flex ${msg.sender === 'LIA' ? 'justify-start' : 'justify-end'}`}
                                      >
                                        <div
                                          className={`max-w-[70%] px-2 py-1 rounded-md ${
                                            msg.sender === 'LIA'
                                              ? 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                                              : 'bg-gray-50 dark:bg-gray-800 text-gray-800'
                                          }`}
                                        >
                                          <p className="text-xs">{msg.message}</p>
                                          <span className="text-xs opacity-70">{msg.time}</span>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>

                                {activity.details.keyPoints && (
                                  <div className="bg-white dark:bg-gray-900 p-2 rounded">
                                    <p className={`${textStyles.bodySmall} mb-1`}>Pontos-Chave</p>
                                    <div className="space-y-0.5">
                                      <div className="flex justify-between text-xs">
                                        <span className="text-gray-600 dark:text-gray-400">Disponibilidade:</span>
                                        <span className="text-gray-800 dark:text-gray-200">{activity.details.keyPoints.availability}</span>
                                      </div>
                                      <div className="flex justify-between text-xs">
                                        <span className="text-gray-600 dark:text-gray-400">Pretensão:</span>
                                        <span className="text-gray-800 dark:text-gray-200">{activity.details.keyPoints.salary}</span>
                                      </div>
                                      <div className="flex justify-between text-xs">
                                        <span className="text-gray-600 dark:text-gray-400">Inglês:</span>
                                        <span className="text-gray-800 dark:text-gray-200">{activity.details.keyPoints.english}</span>
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}

                            {activity.type === 'video-interview' && (
                              <div className="mt-2 space-y-2">
                                <div className="bg-white dark:bg-gray-900 p-2 rounded">
                                  <div className="flex items-center gap-2 mb-2">
                                    <FileVideo className="w-4 h-4 text-red-600" />
                                    <span className={textStyles.bodySmall}>
                                      Vídeo de {activity.duration}
                                    </span>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="ml-auto text-xs px-2 py-1 h-5"
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        setSelectedFile({
                                          name: 'Video_Entrevista.mp4',
                                          type: 'video',
                                          videoType: 'interview',
                                          duration: activity.duration,
                                          questions: activity.details.questions || []
                                        })
                                        setPreviewType('video')
                                        setShowPreview(true)
                                      }}
                                    >
                                      <Play className="w-3 h-3 mr-1" />
                                      Assistir Vídeo
                                    </Button>
                                  </div>
                                  {activity.details.aiAnalysis && (
                                    <div className="grid grid-cols-2 gap-1 text-xs">
                                      <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">Confiança:</span>
                                        <span className="font-medium">{formatScorePercent(activity.details.aiAnalysis.confidence)}</span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">Comunicação:</span>
                                        <span className="font-medium">{formatScorePercent(activity.details.aiAnalysis.communication)}</span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">Entusiasmo:</span>
                                        <span className="font-medium">{formatScorePercent(activity.details.aiAnalysis.enthusiasm)}</span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">Clareza:</span>
                                        <span className="font-medium">{formatScorePercent(activity.details.aiAnalysis.clarity)}</span>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {(activity.type === 'email-sent' || activity.type === 'email-received') && (
                              <div className="mt-3 space-y-3">
                                <div className="bg-white dark:bg-gray-900 p-3 rounded">
                                  <div className="flex items-center justify-between mb-2">
                                    <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1">
                                      <Mail className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                                      {activity.type === 'email-sent' ? 'Email Enviado' : 'Email Recebido'}
                                    </h5>
                                    {activity.details.opened && (
                                      <Badge className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200">
                                        ✓ Lido
                                      </Badge>
                                    )}
                                  </div>

                                  {/* Cabeçalho do Email */}
                                  <div className="bg-white dark:bg-gray-800 p-2 rounded mb-2 text-xs space-y-1">
                                    <div className="flex items-center gap-2">
                                      <span className="text-gray-800 dark:text-gray-200 font-medium">De:</span>
                                      <span className="text-gray-800 dark:text-gray-200">
                                        {activity.type === 'email-sent' ? activity.author : activity.details.from}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-gray-800 dark:text-gray-200 font-medium">Para:</span>
                                      <span className="text-gray-800 dark:text-gray-200">
                                        {activity.type === 'email-sent' ? activity.details.to : activity.author}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-gray-800 dark:text-gray-200 font-medium">Data:</span>
                                      <span className="text-gray-800 dark:text-gray-200">{activity.date}</span>
                                    </div>
                                  </div>

                                  {/* Assunto */}
                                  <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">
                                    {activity.details.subject}
                                  </p>

                                  {/* Corpo do Email Completo */}
                                  <div className="text-xs text-gray-800 dark:text-gray-200 space-y-2">
                                    {activity.details.body ? (
                                      <>
                                        <p>{activity.details.body}</p>
                                        {activity.details.attachments && (
                                          <div className="mt-2 pt-2 border-t">
                                            <p className={`${textStyles.bodySmall} mb-1`}>📎 Anexos:</p>
                                            <div className="flex flex-wrap gap-1">
                                              {activity.details.attachments.map((file: string, i: number) => (
                                                <Badge key={i} variant="outline" className="text-xs px-1.5 py-0.5">
                                                  {file}
                                                </Badge>
                                              ))}
                                            </div>
                                          </div>
                                        )}
                                      </>
                                    ) : (
                                      <p className="text-gray-600 dark:text-gray-400 italic">Conteúdo do email não disponível</p>
                                    )}
                                  </div>

                                  {/* Suggested Times se existir */}
                                  {activity.details.suggestedTimes && (
                                    <div className="mt-2 bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-2 rounded">
                                      <p className="text-xs text-gray-800 dark:text-gray-200 font-semibold mb-1">
                                        Horários Sugeridos:
                                      </p>
                                      <div className="flex gap-1">
                                        {activity.details.suggestedTimes.map((time: string, i: number) => (
                                          <Badge key={i} variant="outline" className="text-xs px-1.5 py-0.5">
                                            {time}
                                          </Badge>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {/* Status de Leitura */}
                                  {activity.details.opened && (
                                    <div className="mt-2 flex items-center gap-2 text-xs text-gray-800 dark:text-gray-200">
                                      <CheckCircle className="w-3 h-3" />
                                      <span>Email aberto {activity.details.openedAt}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'files' && (
          <div className="flex flex-col h-full">
            {/* Header com botão de adicionar */}
            <div className="p-3 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-900">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-medium text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                  Arquivos e Documentos
                  <Badge className="text-xs px-1 py-0">{candidateFiles.length}</Badge>
                  {isLoadingFiles && (
                    <div className="animate-spin rounded-full h-3 w-3 border border-gray-400 border-t-gray-700"></div>
                  )}
                </h4>
                <Button
                  size="sm"
                  className="gap-1 px-2 py-1 text-xs h-6 bg-gray-100 hover:bg-gray-200 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700"
                  onClick={() => {
                    const input = document.createElement('input')
                    input.type = 'file'
                    input.multiple = true
                    input.accept = '.pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov'
                    input.onchange = (e) => {
                      const files = Array.from((e.target as HTMLInputElement).files || [])
                      handleFileUpload(files)
                    }
                    input.click()
                  }}
                  disabled={isUploading}
                >
                  <Plus className="w-3 h-3" />
                  {isUploading ? 'Enviando...' : 'Adicionar Arquivo'}
                </Button>
              </div>

              {/* Categorias automáticas da LIA */}
              <div className="flex gap-1 flex-wrap">
                <Badge 
                  variant="outline" 
                  className={`text-xs px-1.5 py-0 cursor-pointer hover:bg-gray-100 ${!selectedCategory ? 'bg-gray-100' : ''}`}
                  onClick={() => setSelectedCategory(null)}
                >
                  📁 Todos ({candidateFiles.length})
                </Badge>
                {fileCategories.filter(c => c.count > 0).map((cat) => (
                  <Badge 
                    key={cat.category}
                    variant="outline" 
                    className={`text-xs px-1.5 py-0 cursor-pointer hover:bg-gray-100 ${selectedCategory === cat.category ? 'bg-gray-100' : ''}`}
                    onClick={() => setSelectedCategory(selectedCategory === cat.category ? null : cat.category)}
                  >
                    {cat.icon} {cat.label} ({cat.count})
                  </Badge>
                ))}
              </div>
            </div>

            {/* Lista de Arquivos */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {/* Drag and Drop Area */}
              <div
                className={`border-2 border-dashed rounded-md p-4 text-center transition-all cursor-pointer group ${
                  isDragging
                    ? 'border-gray-400 bg-gray-100'
                    : 'border-gray-300 hover:border-gray-400'
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
                  handleFileUpload(files)
                }}
                onClick={() => {
                  if (isUploading) return
                  const input = document.createElement('input')
                  input.type = 'file'
                  input.multiple = true
                  input.accept = '.pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov'
                  input.onchange = (e) => {
                    const files = Array.from((e.target as HTMLInputElement).files || [])
                    handleFileUpload(files)
                  }
                  input.click()
                }}
              >
                <div className="flex flex-col items-center">
                  {isUploading ? (
                    <>
                      <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center mb-2">
                        <div className="animate-spin rounded-full h-5 w-5 border-2 border-gray-400 border-t-gray-700"></div>
                      </div>
                      <p className="text-xs text-gray-800 dark:text-gray-200 font-medium mb-1">
                        Enviando... {uploadProgress}%
                      </p>
                      <div className="w-32 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gray-600 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                    </>
                  ) : (
                    <>
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 transition-colors ${
                        isDragging
                          ? 'bg-gray-200'
                          : 'bg-gray-100 group-hover:bg-gray-200'
                      }`}>
                        <Upload className={`w-5 h-5 ${isDragging ? 'text-gray-700' : 'text-gray-600 dark:text-gray-400 group-hover:text-gray-700'}`} />
                      </div>
                      <p className={`${textStyles.bodySmall} mb-1`}>
                        {isDragging ? 'Solte os arquivos aqui' : 'Arraste arquivos ou clique para selecionar'}
                      </p>
                      <p className={textStyles.bodySmall}>
                        PDF, DOC, DOCX, JPG, PNG, MP4 • Máx 10MB
                      </p>
                    </>
                  )}
                </div>
              </div>

              {/* Real files from API */}
              {candidateFiles
                .filter(file => !selectedCategory || file.file_type === selectedCategory)
                .map((file) => {
                  const colors = getCategoryColor(file.file_type)
                  return (
                    <div key={file.id} className="border border-gray-100 dark:border-gray-700 rounded-md hover:transition-all">
                      <div className="p-2.5">
                        <div className="flex items-start gap-2">
                          <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                            {getFileIcon(file.file_type, file.mime_type)}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h5 className={`${textStyles.bodySmall} font-medium truncate`}>
                                  {file.file_name}
                                </h5>
                                <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                                  <span className={textStyles.bodySmall}>
                                    {formatFileSize(file.file_size)} • {file.file_name.split('.').pop()?.toUpperCase()}
                                  </span>
                                  <span className={textStyles.bodySmall}>
                                    {formatRelativeTime(file.created_at)}
                                  </span>
                                  <Badge 
                                    className="text-xs px-1 py-0 h-3.5" 
                                    style={{ backgroundColor: colors.bg, color: colors.text }}
                                  >
                                    <Tag className="w-2.5 h-2.5 mr-0.5" />
                                    {file.file_type === 'cv' ? 'Currículo' :
                                     file.file_type === 'portfolio' ? 'Portfólio' :
                                     file.file_type === 'video' ? 'Vídeo' :
                                     file.file_type === 'certificate' ? 'Certificado' :
                                     file.file_type === 'transcript' ? 'Transcrição' :
                                     'Documento'}
                                  </Badge>
                                </div>
                                {file.description && (
                                  <p className={`${textStyles.bodySmall} mt-1 truncate`}>
                                    {file.description}
                                  </p>
                                )}
                              </div>
                              
                              <div className="flex items-center gap-1.5">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="p-1 h-6 w-6"
                                  onClick={() => handleDownloadFile(file.file_url, file.file_name)}
                                  title="Baixar arquivo"
                                >
                                  <Download className="w-3 h-3" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="p-1 h-6 w-6 text-red-500 hover:text-red-600 hover:bg-red-50"
                                  onClick={() => handleDeleteFile(file.id)}
                                  title="Excluir arquivo"
                                >
                                  <X className="w-3 h-3" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}

              {/* Empty state when no files */}
              {candidateFiles.length === 0 && !isLoadingFiles && (
                <div className="text-center py-6 text-gray-500 dark:text-gray-400">
                  <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p className="text-xs">Nenhum arquivo enviado</p>
                  <p className={textStyles.description}>Arraste arquivos ou clique acima para enviar</p>
                </div>
              )}

              {/* Currículo com Preview PDF */}
              <div className="border border-gray-100 dark:border-gray-700 rounded-md hover:transition-all">
                <div
                  className="p-2.5 cursor-pointer hover:bg-white dark:hover:bg-gray-800 transition-colors"
                  onClick={() => setExpandedActivity(expandedActivity === 'cv' ? null : 'cv')}
                >
                  <div className="flex items-start gap-2">
                    <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                      <FileText className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h5 className={`${textStyles.bodySmall} font-medium`}>
                            CV_MariaOliveira_2024.pdf
                          </h5>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className={textStyles.bodySmall}>
                              2.1 MB • PDF
                            </span>
                            <span className={textStyles.bodySmall}>
                              Enviado há 2 dias
                            </span>
                            <Badge className="text-xs px-1 py-0 h-3.5" style={{ backgroundColor: 'var(--status-error-bg)', color: 'var(--status-error)' }}>
                              <Tag className="w-2.5 h-2.5 mr-0.5" />
                              Currículo
                            </Badge>
                          </div>
                          <p className={`${textStyles.bodySmall} mt-1`}>
                            Currículo atualizado • Categorizado pela LIA
                          </p>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="p-1 h-6 w-6"
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedFile({ name: 'CV_MariaOliveira_2024.pdf', type: 'pdf' })
                              setPreviewType('pdf')
                              setShowPreview(true)
                            }}
                          >
                            <Eye className="w-3 h-3" />
                          </Button>
                          <Button size="sm" variant="ghost" className="p-1 h-6 w-6">
                            <Download className="w-3 h-3" />
                          </Button>
                          <ChevronDown
                            className={`w-3.5 h-3.5 text-gray-600 dark:text-gray-400 transition-transform ${
                              expandedActivity === 'cv' ? 'rotate-180' : ''
                            }`}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {expandedActivity === 'cv' && (
                  <div className="px-3 pb-3 border-t border-gray-100 dark:border-gray-700 bg-white/50 dark:bg-gray-900/50">
                    <div className="mt-2 space-y-2">
                      {/* Mini Preview do PDF */}
                      <div className="bg-white dark:bg-gray-900 p-2 rounded">
                        <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">Preview do documento</p>
                        <div className="bg-gray-100 dark:bg-gray-800 rounded h-32 flex items-center justify-center">
                          <div className="text-center">
                            <FileText className="w-8 h-8 text-gray-600 dark:text-gray-400 mx-auto mb-1" />
                            <p className={textStyles.bodySmall}>PDF • 5 páginas</p>
                            <Button
                              size="sm"
                              variant="outline"
                              className="mt-2 text-xs px-2 py-1 h-5"
                              onClick={() => {
                                setSelectedFile({ name: 'CV_MariaOliveira_2024.pdf', type: 'pdf' })
                                setPreviewType('pdf')
                                setShowPreview(true)
                              }}
                            >
                              Visualizar Completo
                            </Button>
                          </div>
                        </div>
                      </div>

                      <div className="bg-white dark:bg-gray-900 p-2 rounded">
                        <p className={`${textStyles.bodySmall} mb-1`}>Análise da LIA</p>
                        <p className={textStyles.bodySmall}>
                          ✓ CV bem estruturado • Match 92% com a vaga • Experiência relevante
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Foto do Candidato com Preview de Imagem */}
              <div className="border border-gray-100 dark:border-gray-700 rounded-md hover:transition-all">
                <div className="p-2.5">
                  <div className="flex items-start gap-2">
                    <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                      <Image className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h5 className={`${textStyles.bodySmall} font-medium`}>
                            foto_perfil.jpg
                          </h5>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className={textStyles.bodySmall}>
                              456 KB • JPG
                            </span>
                            <span className={textStyles.bodySmall}>
                              Enviado hoje
                            </span>
                            <Badge className="text-xs px-1 py-0 h-3.5" style={{ backgroundColor: 'var(--status-success-bg)', color: 'var(--status-success)' }}>
                              <Tag className="w-2.5 h-2.5 mr-0.5" />
                              Foto
                            </Badge>
                          </div>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="p-1 h-6 w-6"
                            onClick={() => {
                              setSelectedFile({ name: 'foto_perfil.jpg', type: 'image', url: candidate.avatar_url || candidate.avatar })
                              setPreviewType('image')
                              setShowPreview(true)
                            }}
                          >
                            <Eye className="w-3 h-3" />
                          </Button>
                          <Button size="sm" variant="ghost" className="p-1 h-6 w-6">
                            <Download className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>

                      {/* Thumbnail da imagem */}
                      {(candidate.avatar_url || candidate.avatar) && (
                        <div className="mt-2">
                          <img
                            src={candidate.avatar_url || candidate.avatar}
                            alt="Preview"
                            className="w-12 h-12 rounded object-cover cursor-pointer hover:opacity-80 transition-opacity"
                            onClick={() => {
                              setSelectedFile({ name: 'foto_perfil.jpg', type: 'image', url: candidate.avatar_url || candidate.avatar })
                              setPreviewType('image')
                              setShowPreview(true)
                            }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Vídeo de Apresentação */}
              <div className="border border-gray-100 dark:border-gray-700 rounded-md hover:transition-all">
                <div
                  className="p-2.5 cursor-pointer hover:bg-white dark:hover:bg-gray-800 transition-colors"
                  onClick={() => setExpandedActivity(expandedActivity === 'video1' ? null : 'video1')}
                >
                  <div className="flex items-start gap-2">
                    <div className="w-7 h-7 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                      <FileVideo className="w-3.5 h-3.5 text-red-600" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h5 className={`${textStyles.bodySmall} font-medium`}>
                            Apresentacao_Pessoal.mp4
                          </h5>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className={textStyles.bodySmall}>
                              25.4 MB • MP4 • 3:45
                            </span>
                            <Badge className="text-xs px-1 py-0 h-3.5 bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 border-gray-100 dark:border-gray-700">
                              <Tag className="w-2.5 h-2.5 mr-0.5" />
                              Triagem
                            </Badge>
                          </div>
                          <p className={`${textStyles.bodySmall} mt-1`}>
                            Vídeo de apresentação pessoal • Prescreening
                          </p>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <Badge className="text-xs px-1.5 py-0 h-4 bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200">
                            Analisado
                          </Badge>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="p-1 h-6 w-6"
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedFile({
                                name: 'Apresentacao_Pessoal.mp4',
                                type: 'video',
                                videoType: 'prescreening',
                                duration: '3:45'
                              })
                              setPreviewType('video')
                              setShowPreview(true)
                            }}
                          >
                            <Play className="w-3 h-3" />
                          </Button>
                          <ChevronDown
                            className={`w-3.5 h-3.5 text-gray-600 dark:text-gray-400 transition-transform ${
                              expandedActivity === 'video1' ? 'rotate-180' : ''
                            }`}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {expandedActivity === 'video1' && (
                  <div className="px-3 pb-3 border-t border-gray-100 dark:border-gray-700 bg-white/50 dark:bg-gray-900/50">
                    <div className="mt-2 space-y-2">
                      {/* Preview do vídeo com thumbnail */}
                      <div className="bg-white dark:bg-gray-900 p-2 rounded">
                        <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">Preview do vídeo de triagem</p>
                        <div className="relative bg-gray-900 rounded h-24 flex items-center justify-center group cursor-pointer"
                             onClick={() => {
                               setSelectedFile({
                                 name: 'Apresentacao_Pessoal.mp4',
                                 type: 'video',
                                 videoType: 'prescreening',
                                 duration: '3:45'
                               })
                               setPreviewType('video')
                               setShowPreview(true)
                             }}>
                          <div className="absolute inset-0 bg-black/50 rounded flex items-center justify-center group-hover:bg-black/40 transition-colors">
                            <Play className="w-8 h-8 text-white" />
                          </div>
                          <span className="absolute bottom-1 right-1 text-xs text-white bg-black/70 px-1 rounded-full">
                            3:45
                          </span>
                          <Badge className="absolute top-1 left-1 text-xs px-1.5 py-0.5" style={{ backgroundColor: 'var(--gray-700)', color: 'var(--white)' }}>
                            Prescreening
                          </Badge>
                        </div>
                      </div>

                      {/* Análise de IA do vídeo */}
                      <div className="bg-white dark:bg-gray-900 p-2 rounded">
                        <p className={`${textStyles.bodySmall} mb-1`}>Análise da LIA</p>
                        <div className="grid grid-cols-2 gap-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Confiança:</span>
                            <span className="font-medium text-gray-800 dark:text-gray-200">92%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Comunicação:</span>
                            <span className="font-medium text-gray-800 dark:text-gray-200">95%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Clareza:</span>
                            <span className="font-medium text-gray-800 dark:text-gray-200">88%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Entusiasmo:</span>
                            <span className="font-medium text-gray-800 dark:text-gray-200">90%</span>
                          </div>
                        </div>

                        {/* Mini parecer */}
                        <div className="mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
                          <p className={textStyles.bodySmall}>
                            <span className="font-semibold text-gray-800 dark:text-gray-200">Score Geral: 91%</span> - Candidato demonstra excelente comunicação e fit cultural.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Vídeo de Case Técnico */}
              <div className="border border-gray-100 dark:border-gray-700 rounded-md hover:transition-all">
                <div className="p-2.5">
                  <div className="flex items-start gap-2">
                    <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                      <Video className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h5 className={`${textStyles.bodySmall} font-medium`}>
                            Case_UX_Design.mp4
                          </h5>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className={textStyles.bodySmall}>
                              45.2 MB • MP4 • 8:20
                            </span>
                            <Badge className="text-xs px-1 py-0 h-3.5 bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 border-gray-100 dark:border-gray-700">
                              <Tag className="w-2.5 h-2.5 mr-0.5" />
                              Entrevista
                            </Badge>
                          </div>
                          <p className={`${textStyles.bodySmall} mt-1`}>
                            Apresentação de case técnico • Entrevista gravada
                          </p>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <Badge className="text-xs px-1.5 py-0 h-4 bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200">
                            Destaque
                          </Badge>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="p-1 h-6 w-6"
                            onClick={() => {
                              setSelectedFile({
                                name: 'Case_UX_Design.mp4',
                                type: 'video',
                                videoType: 'interview',
                                duration: '8:20'
                              })
                              setPreviewType('video')
                              setShowPreview(true)
                            }}
                          >
                            <Play className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Vídeo de Entrevista com Gestor - Novo */}
              <div className="border border-gray-100 dark:border-gray-700 rounded-md hover:transition-all">
                <div className="p-2.5">
                  <div className="flex items-start gap-2">
                    <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                      <Video className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h5 className={`${textStyles.bodySmall} font-medium`}>
                            Entrevista_TechLead_30min.mp4
                          </h5>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className={textStyles.bodySmall}>
                              120.5 MB • MP4 • 30:15
                            </span>
                            <Badge className="text-xs px-1 py-0 h-3.5 bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-600">
                              <Tag className="w-2.5 h-2.5 mr-0.5" />
                              Entrevista
                            </Badge>
                          </div>
                          <p className={`${textStyles.bodySmall} mt-1`}>
                            Entrevista técnica com Carlos Mendes • Gravada via Meet
                          </p>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <Badge className="text-xs px-1.5 py-0 h-4 bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200">
                            Completa
                          </Badge>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="p-1 h-6 w-6"
                            onClick={() => {
                              setSelectedFile({
                                name: 'Entrevista_TechLead_30min.mp4',
                                type: 'video',
                                videoType: 'interview',
                                duration: '30:15'
                              })
                              setPreviewType('video')
                              setShowPreview(true)
                            }}
                          >
                            <Play className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Áudio de Triagem por Voz - Card Compacto */}
              <div className="border border-gray-100 dark:border-gray-700 rounded-md hover:transition-all">
                <div className="p-2.5">
                  <div className="flex items-start gap-2">
                    <div className="w-7 h-7 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                      <Mic className="w-3.5 h-3.5 text-purple-600" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h5 className={`${textStyles.bodySmall} font-medium`}>
                            Triagem_Voz_Resposta.mp3
                          </h5>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className={textStyles.bodySmall}>
                              2.8 MB • MP3 • 4:32
                            </span>
                            <Badge className="text-xs px-1 py-0 h-3.5" style={{ backgroundColor: 'var(--gray-100)', color: 'var(--wedo-purple)' }}>
                              <Tag className="w-2.5 h-2.5 mr-0.5" />
                              Triagem
                            </Badge>
                          </div>
                          <p className={`${textStyles.bodySmall} mt-1`}>
                            Resposta de triagem por voz • OpenMic.ai
                          </p>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <Badge className="text-xs px-1.5 py-0 h-4 bg-green-100 text-green-700">
                            Transcrito
                          </Badge>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="p-1 h-6 w-6"
                            onClick={() => {
                              setSelectedFile({
                                name: 'Triagem_Voz_Resposta.mp3',
                                type: 'audio',
                                audioType: 'prescreening',
                                duration: '4:32'
                              })
                              setPreviewType('audio')
                              setShowPreview(true)
                            }}
                          >
                            <Play className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Áudio de Entrevista Gravada - Card Compacto */}
              <div className="border border-gray-100 dark:border-gray-700 rounded-md hover:transition-all">
                <div className="p-2.5">
                  <div className="flex items-start gap-2">
                    <div className="w-7 h-7 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                      <Mic className="w-3.5 h-3.5 text-purple-600" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h5 className={`${textStyles.bodySmall} font-medium`}>
                            Entrevista_RH_Audio.wav
                          </h5>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className={textStyles.bodySmall}>
                              18.5 MB • WAV • 15:20
                            </span>
                            <Badge className="text-xs px-1 py-0 h-3.5 bg-gray-200">
                              <Tag className="w-2.5 h-2.5 mr-0.5" />
                              Entrevista
                            </Badge>
                          </div>
                          <p className={`${textStyles.bodySmall} mt-1`}>
                            Gravação de entrevista com RH • Teams
                          </p>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <Badge className="text-xs px-1.5 py-0 h-4 bg-amber-100 text-amber-700">
                            Pendente
                          </Badge>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="p-1 h-6 w-6"
                            onClick={() => {
                              setSelectedFile({
                                name: 'Entrevista_RH_Audio.wav',
                                type: 'audio',
                                audioType: 'interview',
                                duration: '15:20'
                              })
                              setPreviewType('audio')
                              setShowPreview(true)
                            }}
                          >
                            <Play className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
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
                  <Badge className="text-micro px-1.5 py-0 h-4 ml-1" style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}>
                    {opinionsHistory.length}
                  </Badge>
                )}
              </button>
              <button
                onClick={() => setOpinionsSubTab('analises')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors ${
                  opinionsSubTab === 'analises'
                    ? 'bg-purple-50 text-purple-600 border-b-2 border-purple-500'
 : 'text-gray-500 hover:text-gray-700 dark:text-gray-300 hover:bg-gray-50'
                }`}
              >
                <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                Análises
                {savedAnalyses && savedAnalyses.total_analyses > 0 && (
                  <Badge className="text-micro px-1.5 py-0 h-4 ml-1" style={{ backgroundColor: 'var(--gray-100)', color: 'var(--wedo-purple)' }}>
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
                            <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded mb-1"></div>
                            <div className="w-24 h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
                          <div className="w-3/4 h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
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
                            <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded mb-1"></div>
                            <div className="w-24 h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
                          <div className="w-3/4 h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Empty State */}
                {!isLoadingAnalyses && (!savedAnalyses || savedAnalyses.total_analyses === 0) && (
                  <div className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 rounded-md p-6 text-center">
                    <div className="w-12 h-12 rounded-full bg-purple-50 flex items-center justify-center mx-auto mb-3">
                      <Brain className="w-6 h-6 text-purple-300" />
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
                              <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                                <Brain className="w-4 h-4 text-purple-600" />
                              </div>
                              <div className="min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className={`${textStyles.bodySmall} font-medium`}>Análise LIA</span>
                                  <Badge 
                                    className="text-micro px-1.5 py-0 h-4"
                                    style={{ backgroundColor: 'var(--gray-100)', color: 'var(--wedo-purple)' }}
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
                                    className="p-1 hover:bg-gray-100 rounded transition-colors"
                                  >
                                    {copiedItemId === `analysis-${analysis.id}` ? (
                                      <Check className="w-3.5 h-3.5 text-green-500" />
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
                                      className="p-1.5 hover:bg-red-50 rounded transition-colors group"
                                    >
                                      <Trash2 className="w-4 h-4 text-gray-400 group-hover:text-red-500" />
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
      {showLiaModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-900 rounded-md max-w-2xl w-full max-h-[85vh] overflow-hidden">

            {/* Header estilo padronizado com prompt da LIA */}
            <div className="bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-700">
              <div className="p-3">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Avatar className="w-6 h-6">
                      <AvatarFallback className="bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 text-xs font-bold">
                        LIA
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <span className={`${textStyles.bodySmall} font-medium`}>
                        Análise LIA para candidato específico
                      </span>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowLiaModal(false)}
                    className="h-6 w-6 p-0"
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </div>

                {/* Informações do candidato em foco */}
                <div className="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-md px-3 py-2">
                  <Avatar className="w-6 h-6">
                    <AvatarFallback className="bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 text-xs">
                      {candidate.name?.split(' ').map((n: string) => n[0]).join('')}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <div className="font-medium text-gray-800 dark:text-gray-200 text-xs">
                      {candidate.candidateId || candidate.id} • {candidate.name}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      {candidate.position} • Score: {formatScorePercent(candidate.score)}
                    </div>
                  </div>
                  <Badge className="bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 border-gray-100 dark:border-gray-700 text-xs px-2 py-0.5">
                    Foco Individual
                  </Badge>
                </div>
              </div>
            </div>

            {/* Ações rápidas sugeridas */}
            <div className="px-4 py-2 border-b border-gray-100 dark:border-gray-700 bg-white/50 dark:bg-gray-900/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Ações rápidas sugeridas</span>
 <Badge className="bg-green-100 text-gray-800 dark:bg-green-900 text-xs px-1.5 py-0.5">
                  Score {formatScorePercent(candidate.score)}
                </Badge>
              </div>
              <div className="flex gap-1">
                <button 
                  onClick={() => {
                    if (onContact) {
                      onContact(candidate)
                    } else if (onSendEmail) {
                      onSendEmail(candidate)
                    }
                  }}
                  className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-white rounded text-xs hover:bg-gray-100 transition-colors border border-gray-100 dark:border-gray-700"
                >
                  <MessageSquare className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                  Contatar
                </button>
                <button 
                  onClick={() => {
                    if (onSchedule) {
                      onSchedule(candidate)
                    } else if (onScheduleInterview) {
                      onScheduleInterview(candidate)
                    } else if (onSendAgendamento) {
                      onSendAgendamento(candidate)
                    }
                  }}
                  className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-white rounded text-xs hover:bg-gray-100 transition-colors border border-gray-100 dark:border-gray-700"
                >
                  <CalendarIcon className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                  Agendar
                </button>
                <button 
                  onClick={() => {
                    if (onAddToList) {
                      onAddToList(candidate)
                    } else if (onAddToVacancy) {
                      onAddToVacancy(candidate)
                    }
                  }}
                  className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-white rounded text-xs hover:bg-gray-100 transition-colors border border-gray-100 dark:border-gray-700"
                >
                  <UserPlus className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                  Adicionar
                </button>
              </div>
            </div>

            {/* Lista de sugestões da LIA - estilo compacto */}
            <div className="p-3 max-h-[45vh] overflow-y-auto">
              <div className="space-y-2">
                {liaActions.slice(0, 4).map((action, index) => (
                  <div
                    key={action.id}
                    className="flex items-center gap-2 p-2 bg-white dark:bg-gray-800 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 cursor-pointer group"
                    onClick={() => {
                      console.log(`Executando: ${action.id} para ${candidate.name}`)
                      setLiaConversation(action.title)
                    }}
                  >
                    <span className="text-base flex-shrink-0">{action.icon}</span>
                    <div className="flex-1 min-w-0">
 <h4 className="text-xs font-medium text-gray-800 group-hover:text-gray-800">
                        {action.title}
                      </h4>
                      <p className="text-xs text-gray-800 dark:text-gray-200 truncate">
                        {action.buttonText}
                      </p>
                    </div>
 <ChevronRight className="w-3 h-3 text-gray-600 group-hover:text-gray-700 dark:text-gray-300" />
                  </div>
                ))}
              </div>

              {/* Chat Messages Display */}
              {liaChatMessages.length > 0 && (
                <div className="p-3 border-t border-gray-100 dark:border-gray-700 max-h-48 overflow-y-auto">
                  <div className="space-y-2">
                    {liaChatMessages.map((msg, idx) => (
                      <div key={idx} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {msg.role === 'lia' && (
                          <Avatar className="w-6 h-6 flex-shrink-0">
                            <AvatarFallback className="bg-gray-900 dark:bg-gray-50 text-white text-micro font-bold">LIA</AvatarFallback>
                          </Avatar>
                        )}
                        <div className={`max-w-[80%] rounded-md px-3 py-2 ${
                          msg.role === 'user' 
                            ? 'bg-gray-800 text-white' 
                            : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                        }`}>
                          <p className="text-xs whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      </div>
                    ))}
                    {isLiaChatLoading && (
                      <div className="flex gap-2 justify-start">
                        <Avatar className="w-6 h-6 flex-shrink-0">
                          <AvatarFallback className="bg-gray-900 dark:bg-gray-50 text-white text-micro font-bold">LIA</AvatarFallback>
                        </Avatar>
                        <div className="bg-gray-100 dark:bg-gray-800 rounded-md px-3 py-2">
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Seção de prompt estilo padronizado */}
              <div className="p-4 border-t border-gray-100 dark:border-gray-700">
                <div className="bg-white rounded-md border border-gray-100 dark:border-gray-700 p-3">
                  <form onSubmit={(e) => { e.preventDefault(); if(liaConversation.trim() && !isLiaChatLoading) { sendLiaMessage(liaConversation); }}} className="flex items-center gap-2">
                    {/* LIA Icon animado */}
                    <Avatar className="w-8 h-8 flex-shrink-0">
                      <AvatarFallback className="bg-gray-900 dark:bg-gray-50 text-white text-xs font-bold">
                        LIA
                      </AvatarFallback>
                    </Avatar>

                    {/* Input Field */}
                    <input
                      type="text"
                      value={liaConversation}
                      onChange={(e) => setLiaConversation(e.target.value)}
                      placeholder={`Peça à LIA para analisar ${candidate.name}, agendar entrevista, enviar email...`}
                      className="flex-1 bg-transparent text-gray-800 dark:text-gray-200 placeholder-gray-500 text-xs focus:outline-none"
                      disabled={isLiaChatLoading}
                    />

                    {/* Status */}
                    <div className="text-xs text-gray-800 dark:text-gray-200 flex items-center gap-1">
                      {isLiaChatLoading ? (
                        <>
                          <span className="animate-pulse">●</span>
                          Processando...
                        </>
                      ) : (
                        <>
                          <span>●</span>
                          Pronta
                        </>
                      )}
                    </div>

                    {/* Mic Button */}
                    <button
                      type="button"
                      className="w-6 h-6 rounded-md flex items-center justify-center hover:bg-gray-200 transition-colors"
                      disabled={isLiaChatLoading}
                    >
                      <Mic className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                    </button>

                    {/* Send Button */}
                    <button
                      type="submit"
                      disabled={!liaConversation.trim() || isLiaChatLoading}
                      className={`w-6 h-6 rounded-md flex items-center justify-center transition-colors ${
                        liaConversation.trim() && !isLiaChatLoading
                          ? 'bg-gray-800 text-white hover:bg-gray-700'
                          : 'bg-gray-200 text-gray-600 dark:text-gray-400 cursor-not-allowed'
                      }`}
                    >
                      <Send className="w-3 h-3" />
                    </button>
                  </form>

                  {/* Sugestões rápidas */}
                  <div className="flex flex-wrap gap-1 mt-2">
                    <button
                      onClick={() => setLiaConversation(`Agendar entrevista com ${candidate.name}`)}
                      className="text-xs px-2 py-1 bg-white rounded-full border border-gray-100 dark:border-gray-700 hover:bg-gray-100 transition-colors"
                      disabled={isLiaChatLoading}
                    >
                      📅 Agendar entrevista
                    </button>
                    <button
                      onClick={() => setLiaConversation(`Enviar email de follow-up para ${candidate.name}`)}
                      className="text-xs px-2 py-1 bg-white rounded-full border border-gray-100 dark:border-gray-700 hover:bg-gray-100 transition-colors"
                      disabled={isLiaChatLoading}
                    >
                      📧 Enviar email
                    </button>
                    <button
                      onClick={() => setLiaConversation(`Fazer análise completa de ${candidate.name}`)}
                      className="text-xs px-2 py-1 bg-white rounded-full border border-gray-100 dark:border-gray-700 hover:bg-gray-100 transition-colors"
                      disabled={isLiaChatLoading}
                    >
                      🔍 Análise completa
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Preview de Arquivos */}
      {showPreview && selectedFile && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[60] flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-900 rounded-md max-w-4xl w-full max-h-[90vh] overflow-hidden">
            {/* Header do Preview */}
            <div className="flex items-center justify-between p-3 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-900">
              <div className="flex items-center gap-2">
                {previewType === 'pdf' && <FileText className="w-4 h-4 text-gray-800 dark:text-gray-200" />}
                {previewType === 'image' && <Image className="w-4 h-4 text-gray-800 dark:text-gray-200" />}
                {previewType === 'video' && <FileVideo className="w-4 h-4 text-red-600" />}
                {previewType === 'audio' && <Mic className="w-4 h-4 text-purple-600" />}
                <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  {selectedFile.name}
                </span>
              </div>

              <div className="flex items-center gap-2">
                {/* Controles específicos por tipo */}
                {previewType === 'pdf' && (
                  <>
                    <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded px-2 py-1">
                      <Button size="sm" variant="ghost" className="p-0.5 h-5 w-5" onClick={() => setPdfPage(Math.max(1, pdfPage - 1))}>
                        <ChevronLeft className="w-3 h-3" />
                      </Button>
                      <span className="text-xs text-gray-600 dark:text-gray-400 px-1">
                        {pdfPage} / {pdfTotalPages || 5}
                      </span>
                      <Button size="sm" variant="ghost" className="p-0.5 h-5 w-5" onClick={() => setPdfPage(Math.min(pdfTotalPages || 5, pdfPage + 1))}>
                        <ChevronRight className="w-3 h-3" />
                      </Button>
                    </div>
                  </>
                )}

                {previewType === 'image' && (
                  <div className="flex items-center gap-1">
                    <Button size="sm" variant="ghost" className="p-1 h-6 w-6" onClick={() => setImageZoom(Math.max(25, imageZoom - 25))}>
                      <ZoomOut className="w-3 h-3" />
                    </Button>
                    <span className="text-xs text-gray-600 dark:text-gray-400 w-10 text-center">
                      {imageZoom}%
                    </span>
                    <Button size="sm" variant="ghost" className="p-1 h-6 w-6" onClick={() => setImageZoom(Math.min(200, imageZoom + 25))}>
                      <ZoomIn className="w-3 h-3" />
                    </Button>
                    <Button size="sm" variant="ghost" className="p-1 h-6 w-6" onClick={() => setImageZoom(100)}>
                      <RotateCw className="w-3 h-3" />
                    </Button>
                  </div>
                )}

                {previewType === 'video' && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="p-1 h-6 w-6"
                    onClick={() => setVideoPlaying(!videoPlaying)}
                  >
                    {videoPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                  </Button>
                )}

                {previewType === 'audio' && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="p-1 h-6 w-6"
                    onClick={() => setAudioPlaying(!audioPlaying)}
                  >
                    {audioPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                  </Button>
                )}

                <Button size="sm" variant="outline" className="gap-1 px-2 py-1 text-xs h-6">
                  <Download className="w-3 h-3" />
                  Baixar
                </Button>

                <Button
                  size="sm"
                  variant="ghost"
                  className="p-1 h-6 w-6"
                  onClick={() => {
                    setShowPreview(false)
                    setSelectedFile(null)
                    setPreviewType(null)
                    setVideoPlaying(false)
                    setAudioPlaying(false)
                  }}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Conteúdo do Preview com Transcrição para Vídeos */}
            <div className="p-4 overflow-auto" style={{ maxHeight: 'calc(90vh - 100px)' }}>
              {previewType === 'pdf' && (
                <div className="bg-gray-100 dark:bg-gray-800 rounded-md p-8 min-h-[600px] flex items-center justify-center">
                  <div className="text-center">
                    <FileText className="w-16 h-16 text-gray-600 dark:text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600 dark:text-gray-400 mb-2">
                      Visualizando página {pdfPage} de {pdfTotalPages || 5}
                    </p>
                    <p className="text-sm text-gray-800 dark:text-gray-200">
                      [Conteúdo do PDF seria renderizado aqui]
                    </p>
                  </div>
                </div>
              )}

              {previewType === 'image' && (
                <div className="flex items-center justify-center">
                  <img
                    src={selectedFile.url || candidate.avatar_url || candidate.avatar}
                    alt={selectedFile.name}
                    style={{
                      width: `${imageZoom}%`,
                      maxWidth: '100%',
                      height: 'auto'
                    }}
                    className="rounded-md transition-all duration-300"
                  />
                </div>
              )}

              {previewType === 'video' && (
                <div className="grid grid-cols-3 gap-4">
                  {/* Vídeo Player */}
                  <div className="col-span-2">
                    <div className="bg-black rounded-md aspect-video flex items-center justify-center">
                      <div className="text-center">
                        <FileVideo className="w-16 h-16 text-gray-600 dark:text-gray-400 mx-auto mb-3" />
                        <p className="text-white mb-2">
                          {videoPlaying ? 'Reproduzindo vídeo...' : 'Clique para reproduzir'}
                        </p>
                        <p className="text-gray-600 dark:text-gray-400 text-sm">
                          {selectedFile.name}
                        </p>
                      </div>
                    </div>

                    {/* Perguntas de Triagem (se for vídeo de prescreening) */}
                    {selectedFile.videoType === 'prescreening' && (
                      <div className="mt-4 bg-white dark:bg-gray-800 rounded-md p-3">
                        <h4 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                          <MessageSquareText className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Perguntas de Triagem
                        </h4>
                        <div className="space-y-2">
                          <div className="flex items-start gap-2">
                            <span className={`${textStyles.bodySmall} font-medium`}>1.</span>
                            <p className={textStyles.bodySmall}>
                              Por favor, apresente-se e conte sobre sua experiência profissional
                            </p>
                          </div>
                          <div className="flex items-start gap-2">
                            <span className={`${textStyles.bodySmall} font-medium`}>2.</span>
                            <p className={textStyles.bodySmall}>
                              Por que você está interessado nesta vaga e em nossa empresa?
                            </p>
                          </div>
                          <div className="flex items-start gap-2">
                            <span className={`${textStyles.bodySmall} font-medium`}>3.</span>
                            <p className={textStyles.bodySmall}>
                              Quais são suas principais conquistas profissionais?
                            </p>
                          </div>
                          <div className="flex items-start gap-2">
                            <span className={`${textStyles.bodySmall} font-medium`}>4.</span>
                            <p className={textStyles.bodySmall}>
                              Qual sua disponibilidade para início e expectativa salarial?
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Análise de IA com Parecer da LIA */}
                    <div className="mt-4 bg-white dark:bg-gray-800 rounded-md p-3">
                      <h4 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                        <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                        Análise da LIA
                      </h4>
                      <div className="grid grid-cols-4 gap-2 mb-3">
                        <div className="text-center">
                          <p className={textStyles.bodySmall}>Confiança</p>
                          <p className="text-sm font-bold text-gray-800 dark:text-gray-200">92%</p>
                        </div>
                        <div className="text-center">
                          <p className={textStyles.bodySmall}>Comunicação</p>
                          <p className="text-sm font-bold text-gray-800 dark:text-gray-200">95%</p>
                        </div>
                        <div className="text-center">
                          <p className={textStyles.bodySmall}>Clareza</p>
                          <p className="text-sm font-bold text-gray-800 dark:text-gray-200">88%</p>
                        </div>
                        <div className="text-center">
                          <p className={textStyles.bodySmall}>Entusiasmo</p>
                          <p className="text-sm font-bold text-gray-800 dark:text-gray-200">90%</p>
                        </div>
                      </div>

                      {/* Parecer da LIA */}
                      <div className="border-t border-gray-100 dark:border-gray-700 pt-3">
                        <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                          <Brain className="w-3 h-3 text-wedo-cyan" />
                          Parecer da LIA
                        </h5>
                        <div className="space-y-2 text-xs text-gray-600 dark:text-gray-400">
                          <p>
                            <span className="font-semibold text-gray-800 dark:text-gray-200">Pontos Fortes:</span> O candidato demonstra excelente capacidade de comunicação,
                            com respostas claras e estruturadas. Apresenta postura profissional e confiante durante toda a entrevista.
                            Suas experiências são relevantes para a posição.
                          </p>
                          <p>
                            <span className="font-semibold text-gray-800 dark:text-gray-200">Pontos de Atenção:</span> Poderia ter elaborado mais sobre metodologias
                            específicas de design. A resposta sobre trabalho em equipe foi um pouco genérica.
                          </p>
                          <p>
                            <span className="font-semibold text-gray-800 dark:text-gray-200">Recomendação:</span> Candidato altamente recomendado para próxima fase.
                            Sugiro aprofundar questionamentos sobre liderança técnica e experiência com design systems em escala.
                          </p>
                          <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
                            <span className={textStyles.bodySmall}>Score Geral</span>
                            <Badge className="text-xs px-2 py-0.5" style={{ backgroundColor: 'var(--status-success)', color: 'white' }}>
                              91% - Altamente Recomendado
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Feed de Transcrição - Melhorado */}
                  <div className="col-span-1">
                    <div className="bg-white dark:bg-gray-800 rounded-md p-3 h-full overflow-y-auto">
                      <h4 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-3 sticky top-0 bg-white pb-2 border-b border-gray-100 dark:border-gray-700">
                        📝 Transcrição
                      </h4>

                      {/* Indicador do tipo de vídeo */}
                      <div className="mb-3 p-2 bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded">
                        <div className="flex items-center gap-2">
                          <Badge className="text-xs px-1.5 py-0.5" style={{ backgroundColor: 'var(--gray-700)', color: 'var(--white)' }}>
                            {selectedFile.videoType === 'interview' ? 'Entrevista Gravada' : 'Vídeo de Triagem'}
                          </Badge>
                          <span className={textStyles.bodySmall}>Duração: {selectedFile.duration || '3:45'}</span>
                        </div>
                      </div>

                      <div className="space-y-3 text-xs">
                        {selectedFile.transcript && selectedFile.transcript.length > 0 ? (
                          <>
                            {selectedFile.transcript.map((segment: any, idx: number) => (
                              <div key={idx} className="border-l-2 border-gray-400 dark:border-gray-500 pl-3">
                                <p className={`${textStyles.bodySmall} mb-1`}>
                                  {segment.timestamp || segment.time || ''} • {segment.speaker || segment.role || 'Participante'}
                                </p>
                                <p className="text-gray-800 dark:text-gray-200">
                                  "{segment.text || segment.content || ''}"
                                </p>
                              </div>
                            ))}
                          </>
                        ) : (
                          <div className="text-center py-4 text-gray-600 dark:text-gray-400">
                            <p className="text-xs">Transcrição não disponível para este vídeo</p>
                          </div>
                        )}

                        {/* Highlights identificados pela LIA - only show if data available */}
                        {selectedFile.highlights && selectedFile.highlights.length > 0 && (
                          <div className="mt-4 p-2 bg-white dark:bg-gray-800 rounded">
                            <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">
                              🎯 Highlights da LIA
                            </p>
                            <ul className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                              {selectedFile.highlights.map((highlight: string, idx: number) => (
                                <li key={idx}>• {highlight}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Conteúdo do Modal para Áudio */}
              {previewType === 'audio' && (
                <div className="grid grid-cols-3 gap-4">
                  {/* Áudio Player e Conteúdo Principal */}
                  <div className="col-span-2">
                    {/* Player de Áudio */}
                    <div className="bg-purple-50 rounded-md p-4 flex items-center justify-center">
                      <div className="text-center w-full">
                        <div className="flex items-center justify-center mb-3">
                          <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center">
                            <Mic className="w-8 h-8 text-purple-600" />
                          </div>
                        </div>
                        <p className="text-gray-800 dark:text-gray-200 mb-2">
                          {audioPlaying ? 'Reproduzindo áudio...' : 'Clique para reproduzir'}
                        </p>
                        <p className="text-gray-500 dark:text-gray-400 text-sm mb-3">
                          {selectedFile.name}
                        </p>
                        {/* Barra de progresso */}
                        <div className="flex items-center gap-3 max-w-md mx-auto">
                          <Button
                            size="sm"
                            variant="outline"
                            className="p-2 h-8 w-8 rounded-full bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 border-0"
                            onClick={() => setAudioPlaying(!audioPlaying)}
                          >
                            {audioPlaying ? <Pause className="w-4 h-4 text-white" /> : <Play className="w-4 h-4 text-white" />}
                          </Button>
                          <div className="flex-1">
                            <div className="h-2 bg-purple-200 rounded-full overflow-hidden">
                              <div className="h-full bg-purple-600 rounded-full transition-all" style={{ width: audioPlaying ? '35%' : '0%' }} />
                            </div>
                          </div>
                          <span className="text-xs text-gray-600 dark:text-gray-400 font-mono w-20 text-right">
                            {audioPlaying ? '1:35' : '0:00'} / {selectedFile.duration || '4:32'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Perguntas de Triagem (se for áudio de prescreening) */}
                    {selectedFile.audioType === 'prescreening' && (
                      <div className="mt-4 bg-white dark:bg-gray-800 rounded-md p-3">
                        <h4 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                          <MessageSquareText className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Perguntas de Triagem
                        </h4>
                        <div className="space-y-2">
                          <div className="flex items-start gap-2">
                            <span className={`${textStyles.bodySmall} font-medium`}>1.</span>
                            <p className={textStyles.bodySmall}>
                              Por favor, apresente-se e conte sobre sua experiência profissional
                            </p>
                          </div>
                          <div className="flex items-start gap-2">
                            <span className={`${textStyles.bodySmall} font-medium`}>2.</span>
                            <p className={textStyles.bodySmall}>
                              Por que você está interessado nesta vaga e em nossa empresa?
                            </p>
                          </div>
                          <div className="flex items-start gap-2">
                            <span className={`${textStyles.bodySmall} font-medium`}>3.</span>
                            <p className={textStyles.bodySmall}>
                              Quais são suas principais conquistas profissionais?
                            </p>
                          </div>
                          <div className="flex items-start gap-2">
                            <span className={`${textStyles.bodySmall} font-medium`}>4.</span>
                            <p className={textStyles.bodySmall}>
                              Qual sua disponibilidade para início e expectativa salarial?
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Análise de IA com Parecer da LIA */}
                    <div className="mt-4 bg-white dark:bg-gray-800 rounded-md p-3">
                      <h4 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                        <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                        Análise da LIA
                      </h4>
                      <div className="grid grid-cols-4 gap-2 mb-3">
                        <div className="text-center">
                          <p className={textStyles.bodySmall}>Clareza</p>
                          <p className="text-sm font-bold text-gray-800 dark:text-gray-200">94%</p>
                        </div>
                        <div className="text-center">
                          <p className={textStyles.bodySmall}>Confiança</p>
                          <p className="text-sm font-bold text-gray-800 dark:text-gray-200">91%</p>
                        </div>
                        <div className="text-center">
                          <p className={textStyles.bodySmall}>Conhecimento</p>
                          <p className="text-sm font-bold text-gray-800 dark:text-gray-200">96%</p>
                        </div>
                        <div className="text-center">
                          <p className={textStyles.bodySmall}>Comunicação</p>
                          <p className="text-sm font-bold text-gray-800 dark:text-gray-200">89%</p>
                        </div>
                      </div>

                      {/* Parecer da LIA */}
                      <div className="border-t border-gray-100 dark:border-gray-700 pt-3">
                        <h5 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                          <Brain className="w-3 h-3 text-wedo-cyan" />
                          Parecer da LIA
                        </h5>
                        <div className="space-y-2 text-xs text-gray-600 dark:text-gray-400">
                          <p>
                            <span className="font-semibold text-gray-800 dark:text-gray-200">Pontos Fortes:</span> O candidato demonstra excelente articulação e domínio técnico.
                            Experiência sólida em liderança de times mobile, com resultados mensuráveis (redução de 40% no tempo de desenvolvimento).
                          </p>
                          <p>
                            <span className="font-semibold text-gray-800 dark:text-gray-200">Pontos de Atenção:</span> Poderia detalhar mais sobre gestão de conflitos e metodologias ágeis.
                            A experiência com React Native é recente (últimos 2 anos).
                          </p>
                          <p>
                            <span className="font-semibold text-gray-800 dark:text-gray-200">Recomendação:</span> Candidato altamente recomendado para próxima fase.
                            Sugiro aprofundar sobre arquitetura de apps e experiência com CI/CD mobile.
                          </p>
                          <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
                            <span className={textStyles.bodySmall}>Score Geral</span>
                            <Badge className="text-xs px-2 py-0.5" style={{ backgroundColor: 'var(--status-success)', color: 'white' }}>
                              93% - Altamente Recomendado
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Feed de Transcrição - Deepgram */}
                  <div className="col-span-1">
                    <div className="bg-white dark:bg-gray-800 rounded-md p-3 h-full overflow-y-auto">
                      <h4 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-3 sticky top-0 bg-white pb-2 border-b border-gray-100 dark:border-gray-700">
                        📝 Transcrição
                      </h4>

                      {/* Indicador do tipo de áudio */}
                      <div className="mb-3 p-2 bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded">
                        <div className="flex items-center gap-2">
                          <Badge className="text-xs px-1.5 py-0.5" style={{ backgroundColor: 'var(--wedo-purple)', color: 'var(--white)' }}>
                            {selectedFile.audioType === 'interview' ? 'Entrevista Gravada' : 'Áudio de Triagem'}
                          </Badge>
                          <span className={textStyles.bodySmall}>Duração: {selectedFile.duration || '4:32'}</span>
                        </div>
                      </div>

                      <div className="space-y-3 text-xs">
                        {/* Transcrição de exemplo */}
                        <div className="border-l-2 border-purple-400 pl-3">
                          <p className={`${textStyles.bodySmall} mb-1`}>
                            0:00 • Candidato
                          </p>
                          <p className="text-gray-800 dark:text-gray-200">
                            "Olá, meu nome é Bruno Carvalho Dias e estou muito interessado nessa oportunidade de Tech Lead Mobile. Tenho mais de 8 anos de experiência em desenvolvimento mobile, sendo os últimos 4 anos focado em liderança técnica..."
                          </p>
                        </div>

                        <div className="border-l-2 border-purple-400 pl-3">
                          <p className={`${textStyles.bodySmall} mb-1`}>
                            1:15 • Candidato
                          </p>
                          <p className="text-gray-800 dark:text-gray-200">
                            "Trabalhei na Unicorn Startup onde liderei um time de 6 desenvolvedores. Implementamos React Native para unificar as plataformas iOS e Android, reduzindo o tempo de desenvolvimento em 40%..."
                          </p>
                        </div>

                        <div className="border-l-2 border-purple-400 pl-3">
                          <p className={`${textStyles.bodySmall} mb-1`}>
                            2:30 • Candidato
                          </p>
                          <p className="text-gray-800 dark:text-gray-200">
                            "Sobre minhas principais conquistas, destaco a migração completa de duas aplicações nativas para React Native, mantendo 99.5% de uptime durante todo o processo..."
                          </p>
                        </div>

                        <div className="border-l-2 border-purple-400 pl-3">
                          <p className={`${textStyles.bodySmall} mb-1`}>
                            3:45 • Candidato
                          </p>
                          <p className="text-gray-800 dark:text-gray-200">
                            "Estou disponível para início imediato e minha expectativa salarial está na faixa de R$ 25.000 a R$ 30.000, considerando o nível de senioridade e responsabilidades da posição."
                          </p>
                        </div>

                        {/* Highlights identificados pela LIA */}
                        <div className="mt-4 p-2 bg-purple-50 rounded">
                          <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-1">
                            🎯 Highlights da LIA
                          </p>
                          <ul className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                            <li>• 8+ anos de experiência em mobile</li>
                            <li>• Liderança de time de 6 devs</li>
                            <li>• Redução de 40% no tempo de dev</li>
                            <li>• Disponibilidade imediata</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
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
              className="bg-red-500 hover:bg-red-600 text-xs text-white"
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
