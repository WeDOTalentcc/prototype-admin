"use client"


import React, { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { 
  ArrowLeft, MapPin, Briefcase, Mail, Phone, Linkedin, ExternalLink,
  Calendar, GraduationCap, Loader2, Building, Globe, Github, Star,
  MessageSquare, UserPlus, Heart, EyeOff, DollarSign, Clock, Users,
  Code, Award, CheckCircle, AlertCircle, Brain, Languages,
  Home, Shield, FileText, Activity, List, Send, CalendarDays, Plus,
  GitBranch, Upload, Download, Eye, X, Tag, ChevronDown, ChevronUp,
  PlusCircle, BarChart3, Target, TrendingUp, Image, File, FileVideo, Video, Play,
  Edit, User, Cake, Contact, Lightbulb, Car, Network, ClipboardCheck, Copy
} from "lucide-react"
import { liaApi, type CandidateLocal } from "@/services/lia-api"
import { textStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import { UnifiedCommunicationModal, type CommunicationType } from "@/components/modals/unified-communication-modal"
import { AddToListModal } from "@/components/modals/add-to-list-modal"
import { AddCandidatesToVacancyModal } from "@/components/modals/add-candidates-to-vacancy-modal"
import { useToast } from "@/hooks/use-toast"
import { ExperienceHighlightCard } from "@/components/experience-highlight-card"
import dynamic from "next/dynamic"

const LiaAnalysisModal = dynamic(() => import("@/components/modals/lia-analysis-modal").then(m => ({ default: m.LiaAnalysisModal })), { ssr: false })

type ActiveTab = 'profile' | 'activities' | 'files' | 'opinions'
type ActivityCategory = 'all' | 'interview' | 'screening' | 'general'

interface OpinionData {
  current_general_opinion?: Record<string, unknown>
  vacancy_opinions?: Array<Record<string, unknown>>
}

export function useCandidatePageCore() {
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()
  const candidateId = params.id as string

  
  const [candidate, setCandidate] = useState<CandidateLocal | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<ActiveTab>('profile')
  const [activityCategory, setActivityCategory] = useState<ActivityCategory>('all')
  const [isFavorite, setIsFavorite] = useState(false)
  const [isHidden, setIsHidden] = useState(false)
  
  const [showCommunicationModal, setShowCommunicationModal] = useState(false)
  const [communicationType, setCommunicationType] = useState<CommunicationType>('email')
  const [showAddToListModal, setShowAddToListModal] = useState(false)
  const [showAddToVacancyModal, setShowAddToVacancyModal] = useState(false)
  
  const [opinionsData, setOpinionsData] = useState<OpinionData | null>(null)
  const [opinionsHistory, setOpinionsHistory] = useState<any[]>([])
  const [isLoadingOpinions, setIsLoadingOpinions] = useState(false)
  const [savedAnalyses, setSavedAnalyses] = useState<any>(null)
  const [isLoadingAnalyses, setIsLoadingAnalyses] = useState(false)
  const [opinionsSubTab, setOpinionsSubTab] = useState<'pareceres' | 'analises'>('pareceres')
  const [expandedAnalysisId, setExpandedAnalysisId] = useState<string | null>(null)
  const [activities, setActivities] = useState<any[]>([])
  const [isLoadingActivities, setIsLoadingActivities] = useState(false)
  
  const [activityFilter, setActivityFilter] = useState<'all' | 'emails' | 'interviews' | 'lia' | 'applications' | 'tests' | 'offers' | 'notes'>('all')
  const [newNoteContent, setNewNoteContent] = useState('')
  const [newNoteCategory, setNewNoteCategory] = useState<'general' | 'interview' | 'screening' | 'feedback' | 'technical'>('general')
  const [activityView, setActivityView] = useState<'list' | 'timeline'>('timeline')
  const [periodFilter, setPeriodFilter] = useState<'7days' | '30days' | '3months' | 'all'>('all')
  const [isDragging, setIsDragging] = useState(false)
  const [candidateFiles, setCandidateFiles] = useState<any[]>([])
  const [fileCategories, setFileCategories] = useState<any[]>([])
  const [isLoadingFiles, setIsLoadingFiles] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [expandedOpinionId, setExpandedOpinionId] = useState<string | null>(null)
  const [expandedActivity, setExpandedActivity] = useState<string | null>(null)
  const [showLiaAnalysisModal, setShowLiaAnalysisModal] = useState(false)
  
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  useEffect(() => {
    async function loadCandidate() {
      if (!candidateId) return
      
      try {
        setLoading(true)
        const data = await liaApi.getCandidate(candidateId)
        setCandidate(data)
        
        // Initialize favorite/hidden state from candidate data or API
        try {
          const additionalData = (data as Record<string, unknown>)?.additional_data as Record<string, unknown> | undefined
          if (additionalData?.is_favorited !== undefined) {
            setIsFavorite(additionalData.is_favorited)
          } else {
            const favResponse = await fetch(`/api/backend-proxy/candidates/${candidateId}/favorite/status`)
            if (favResponse.ok) {
              const favData = await favResponse.json()
              setIsFavorite(favData?.is_favorited || false)
            }
          }
        } catch (e) {
          // Fail gracefully if endpoint doesn't exist
        }
        
        try {
          const additionalData = (data as Record<string, unknown>)?.additional_data as Record<string, unknown> | undefined
          if (additionalData?.is_hidden !== undefined) {
            setIsHidden(additionalData.is_hidden)
          } else {
            const hideResponse = await fetch(`/api/backend-proxy/candidates/${candidateId}/hide/status`)
            if (hideResponse.ok) {
              const hideData = await hideResponse.json()
              setIsHidden(hideData?.is_hidden || false)
            }
          }
        } catch (e) {
          // Fail gracefully if endpoint doesn't exist
        }
      } catch (err) {
        setError("Não foi possível carregar o perfil do candidato")
      } finally {
        setLoading(false)
      }
    }
    
    loadCandidate()
  }, [candidateId])

  const fetchOpinionsSummary = useCallback(async () => {
    if (!candidateId) return
    setIsLoadingOpinions(true)
    try {
      const response = await fetch(`/api/backend-proxy/opinions/candidate/${candidateId}/summary?company_id=demo_company`)
      if (response.ok) {
        const data = await response.json()
        setOpinionsData(data)
      }
    } catch (error) {
    } finally {
      setIsLoadingOpinions(false)
    }
  }, [candidateId])

  const fetchOpinionsHistory = useCallback(async () => {
    if (!candidateId) return
    try {
      const response = await fetch(`/api/backend-proxy/opinions/candidate/${candidateId}/history?company_id=demo_company`)
      if (response.ok) {
        const data = await response.json()
        setOpinionsHistory(data)
      }
    } catch (error) {
    }
  }, [candidateId])

  const fetchSavedAnalyses = useCallback(async () => {
    if (!candidateId) return
    setIsLoadingAnalyses(true)
    try {
      const response = await fetch(`/api/backend-proxy/lia/profile-analysis/candidate/${candidateId}?company_id=demo_company`)
      if (response.ok) {
        const data = await response.json()
        setSavedAnalyses({
          analyses: data.analyses || [],
          total_analyses: data.total || 0
        })
      }
    } catch (error) {
    } finally {
      setIsLoadingAnalyses(false)
    }
  }, [candidateId])

  const fetchCandidateFiles = useCallback(async () => {
    if (!candidateId) return
    
    setIsLoadingFiles(true)
    try {
      const url = `${BACKEND_URL}/api/v1/candidates/${candidateId}/files?company_id=demo_company`
      const response = await fetch(url)
      if (response.ok) {
        const data = await response.json()
        setCandidateFiles(data.attachments || [])
        setFileCategories(data.categories || [])
      }
    } catch (error) {
    } finally {
      setIsLoadingFiles(false)
    }
  }, [candidateId, BACKEND_URL])

  const handleFileUpload = async (files: File[]) => {
    if (!candidateId || files.length === 0) return
    
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
      formData.append('candidate_name', candidate?.name || 'Candidato')
      formData.append('company_id', 'demo_company')
      formData.append('uploaded_by', 'user')
      formData.append('uploaded_by_name', 'Recrutador')
      
      try {
        const response = await fetch(`${BACKEND_URL}/api/v1/candidates/${candidateId}/files`, {
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
    if (!candidateId) return
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/candidates/${candidateId}/files/${attachmentId}`, {
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

  useEffect(() => {
    if (candidateId) {
      fetchOpinionsSummary()
    }
  }, [candidateId, fetchOpinionsSummary])

  useEffect(() => {
    if (activeTab === 'files' && candidateId) {
      fetchCandidateFiles()
    }
  }, [activeTab, candidateId, fetchCandidateFiles])

  useEffect(() => {
    if (activeTab === 'opinions' && candidateId) {
      fetchOpinionsHistory()
      fetchSavedAnalyses()
    }
  }, [activeTab, candidateId, fetchOpinionsHistory, fetchSavedAnalyses])

  useEffect(() => {
    async function fetchActivities() {
      if (activeTab !== 'activities' || !candidateId) return
      
      setIsLoadingActivities(true)
      try {
        const response = await fetch(`/api/backend-proxy/candidates/${candidateId}/activities?company_id=demo_company`)
        if (response.ok) {
          const data = await response.json()
          setActivities(Array.isArray(data) ? data : data?.activities || [])
        }
      } catch (error) {
      } finally {
        setIsLoadingActivities(false)
      }
    }
    
    fetchActivities()
  }, [activeTab, candidateId])

  const getInitials = (name: string) => {
    const parts = name.split(" ")
    return parts.length > 1 
      ? `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
      : name.slice(0, 2).toUpperCase()
  }

  const getShortId = (id: string) => {
    return id.slice(0, 6).toUpperCase()
  }

  const formatCurrency = (value: number | null | undefined, currency: string = 'BRL') => {
    if (value === null || value === undefined) return null
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency }).format(value)
  }

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return null
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', { 
        day: '2-digit', 
        month: 'short', 
        year: 'numeric' 
      })
    } catch {
      return dateStr
    }
  }

  const formatDateShort = (dateStr: string | null | undefined) => {
    if (!dateStr) return null
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', { 
        month: 'short', 
        year: 'numeric' 
      })
    } catch {
      return dateStr
    }
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

  const cleanMarkdown = (text: string): string => {
    if (!text) return ''
    return text
      .replace(/^#{1,6}\s*/gm, '')
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/__([^_]+)__/g, '$1')
      .replace(/_([^_]+)_/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/^[-*]\s+/gm, '• ')
      .trim()
  }

  const copyToClipboard = async (text: string, label: string = 'Conteúdo') => {
    try {
      await navigator.clipboard.writeText(cleanMarkdown(text))
      toast({
        title: "Copiado!",
        description: `${label} copiado para a área de transferência.`,
      })
    } catch (err) {
      toast({
        title: "Erro ao copiar",
        description: "Não foi possível copiar o conteúdo.",
        variant: "destructive"
      })
    }
  }

  const calculateAge = (dateOfBirth: string | null | undefined): number | null => {
    if (!dateOfBirth) return null
    try {
      const birth = new Date(dateOfBirth)
      const today = new Date()
      let age = today.getFullYear() - birth.getFullYear()
      const monthDiff = today.getMonth() - birth.getMonth()
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--
      }
      return age > 0 && age < 120 ? age : null
    } catch {
      return null
    }
  }

  const hasPearchData = (c: Record<string, unknown>): boolean => {
    return !!(c.headline || c.is_open_to_work || c.is_decision_maker || 
              c.is_top_universities || c.is_hiring || c.linkedin_followers_count || 
              c.linkedin_connections_count || c.pearch_profile_id)
  }

  const hasPersonalData = (c: Record<string, unknown>): boolean => {
    return !!(c.date_of_birth || c.gender || c.nationality || 
              c.marital_status || c.estimated_age)
  }

  const hasAdditionalContacts = (c: Record<string, unknown>): boolean => {
    return !!(c.secondary_email || c.secondary_phone || c.best_personal_email || 
              c.best_business_email || c.preferred_contact_method || c.best_time_to_contact)
  }

  const hasDocuments = (c: Record<string, unknown>): boolean => {
    return !!(c.resume_url || c.cover_letter || c.self_introduction)
  }

  const getFileIcon = (fileType: string, mimeType?: string) => {
    if (fileType === 'cv') return <FileText className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
    if (fileType === 'video' || mimeType?.startsWith('video/')) return <FileVideo className="w-3.5 h-3.5 text-status-error" />
    if (fileType === 'certificate') return <Award className="w-3.5 h-3.5 text-status-warning" />
    if (mimeType?.startsWith('image/')) return <Image className="w-3.5 h-3.5 text-status-success" />
    return <File className="w-3.5 h-3.5 text-gray-600" />
  }

  const getCategoryColor = (fileType: string) => {
    const colors: Record<string, { bg: string, text: string }> = {
      'cv': { bg: 'var(--status-success-bg)', text: 'var(--status-success)' },
      'photo': { bg: 'var(--gray-200)', text: 'var(--gray-600)' },
      'portfolio': { bg: 'var(--gray-200)', text: 'var(--gray-600)' },
      'video': { bg: 'var(--status-error-bg-12)', text: 'var(--status-error)' },
      'certificate': { bg: 'var(--status-warning-bg-12)', text: 'var(--status-warning)' },
      'document': { bg: 'var(--gray-bg-12)', text: 'var(--gray-400)' },
      'screening': { bg: 'var(--status-warning-bg-12)', text: 'var(--status-warning)' },
      'interview': { bg: 'var(--wedo-purple-bg-10)', text: 'var(--wedo-purple)' },
      'transcript': { bg: 'var(--wedo-purple-bg-10)', text: 'var(--wedo-purple)' },
    }
    return colors[fileType] || colors['document']
  }

  const getCategoryLabel = (fileType: string) => {
    const labels: Record<string, string> = {
      'cv': 'Currículo',
      'photo': 'Foto',
      'portfolio': 'Portfólio',
      'video': 'Vídeo',
      'certificate': 'Certificado',
      'document': 'Documento',
      'screening': 'Triagem',
      'interview': 'Entrevista',
      'transcript': 'Transcrição',
    }
    return labels[fileType] || 'Documento'
  }

  const handleToggleFavorite = async () => {
    if (!candidate) return
    try {
      if (isFavorite) {
        await fetch(`/api/backend-proxy/candidates/${candidate.id}/favorite`, { method: 'DELETE' })
      } else {
        await fetch(`/api/backend-proxy/candidates/${candidate.id}/favorite`, { method: 'POST' })
      }
      setIsFavorite(!isFavorite)
      toast({
        title: isFavorite ? "Removido dos favoritos" : "Adicionado aos favoritos",
        description: `${candidate.name} foi ${isFavorite ? 'removido dos' : 'adicionado aos'} favoritos`
      })
    } catch (error) {
    }
  }

  const handleHideCandidate = async () => {
    if (!candidate) return
    try {
      if (isHidden) {
        await fetch(`/api/backend-proxy/candidates/${candidate.id}/hide`, { method: 'DELETE' })
      } else {
        await fetch(`/api/backend-proxy/candidates/${candidate.id}/hide`, { method: 'POST' })
      }
      setIsHidden(!isHidden)
      toast({
        title: isHidden ? "Candidato visível" : "Candidato oculto",
        description: `${candidate.name} foi ${isHidden ? 'tornado visível' : 'ocultado'}`
      })
    } catch (error) {
    }
  }

  const openCommunicationModal = (type: CommunicationType) => {
    setCommunicationType(type)
    setShowCommunicationModal(true)
  }

  const getLanguageLevel = (level: string) => {
    const levels: Record<string, { label: string; percent: number; color: string }> = {
      'native': { label: 'Nativo', percent: 100, color: 'bg-status-success' },
      'nativo': { label: 'Nativo', percent: 100, color: 'bg-status-success' },
      'fluent': { label: 'Fluente', percent: 90, color: 'bg-status-success' },
      'fluente': { label: 'Fluente', percent: 90, color: 'bg-status-success' },
      'advanced': { label: 'Avançado', percent: 75, color: 'bg-gray-700 dark:bg-gray-300' },
      'avançado': { label: 'Avançado', percent: 75, color: 'bg-gray-700 dark:bg-gray-300' },
      'intermediate': { label: 'Intermediário', percent: 50, color: 'bg-status-warning' },
      'intermediário': { label: 'Intermediário', percent: 50, color: 'bg-status-warning' },
      'basic': { label: 'Básico', percent: 25, color: 'bg-gray-400' },
      'básico': { label: 'Básico', percent: 25, color: 'bg-gray-400' },
    }
    return levels[level.toLowerCase()] || { label: level, percent: 50, color: 'bg-gray-400' }
  }

  const parseLanguages = (languages: CandidateLocal['languages']) => {
    if (!languages) return []
    if (Array.isArray(languages)) {
      return languages.map(l => ({ language: l.language, level: l.level }))
    }
    return Object.entries(languages).map(([language, level]) => ({ language, level }))
  }

  const categorizeSkills = (skills: string[]) => {
    const categories: Record<string, { label: string; skills: string[] }> = {
      backend: { label: 'Backend', skills: [] },
      frontend: { label: 'Frontend', skills: [] },
      data: { label: 'Dados & Analytics', skills: [] },
      devops: { label: 'DevOps & Cloud', skills: [] },
      mobile: { label: 'Mobile', skills: [] },
      other: { label: 'Outras', skills: [] }
    }
    
    const backendKeywords = ['java', 'spring', 'node', 'python', 'django', 'flask', 'fastapi', 'ruby', 'rails', 'php', 'laravel', '.net', 'c#', 'go', 'golang', 'rust', 'express', 'nestjs', 'graphql', 'rest', 'api', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis']
    const frontendKeywords = ['react', 'angular', 'vue', 'javascript', 'typescript', 'html', 'css', 'sass', 'tailwind', 'next', 'nuxt', 'svelte', 'redux', 'webpack']
    const dataKeywords = ['python', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'machine learning', 'ml', 'ai', 'data science', 'sql', 'spark', 'hadoop', 'tableau', 'power bi']
    const devopsKeywords = ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'jenkins', 'ci/cd', 'linux', 'devops']
    const mobileKeywords = ['ios', 'android', 'swift', 'kotlin', 'react native', 'flutter', 'mobile']
    
    skills.forEach(skill => {
      const skillLower = skill.toLowerCase()
      if (backendKeywords.some(k => skillLower.includes(k))) {
        categories.backend.skills.push(skill)
      } else if (frontendKeywords.some(k => skillLower.includes(k))) {
        categories.frontend.skills.push(skill)
      } else if (dataKeywords.some(k => skillLower.includes(k))) {
        categories.data.skills.push(skill)
      } else if (devopsKeywords.some(k => skillLower.includes(k))) {
        categories.devops.skills.push(skill)
      } else if (mobileKeywords.some(k => skillLower.includes(k))) {
        categories.mobile.skills.push(skill)
      } else {
        categories.other.skills.push(skill)
      }
    })
    
    return Object.entries(categories).filter(([_, cat]) => cat.skills.length > 0)
  }

  const languagesData = !loading && candidate ? parseLanguages(candidate.languages) : []
  const skillCategories = !loading && candidate ? categorizeSkills([...(candidate.technical_skills || []), ...(candidate.expertise || [])]) : []
  const cRecord = candidate as unknown as Record<string, unknown>
  const cAdditional = cRecord?.additional_data as Record<string, unknown> | undefined
  const experiences = cRecord?.workHistory || cRecord?.work_history || cRecord?.experiences || cAdditional?.work_history || cAdditional?.experiences || []
  const education = cRecord?.education || cAdditional?.education || []
  const opinion = opinionsData?.current_general_opinion || opinionsData?.vacancy_opinions?.[0]


  return {
    activeTab,
    activities,
    activityFilter,
    activityView,
    calculateAge,
    candidate,
    candidateFiles,
    cleanMarkdown,
    communicationType,
    copyToClipboard,
    education,
    error,
    expandedAnalysisId,
    expandedOpinionId,
    experiences,
    fetchSavedAnalyses,
    fileCategories,
    formatCurrency,
    formatDate,
    formatDateShort,
    formatFileSize,
    formatRelativeTime,
    getCategoryColor,
    getCategoryLabel,
    getFileIcon,
    getInitials,
    getLanguageLevel,
    getShortId,
    handleDeleteFile,
    handleDownloadFile,
    handleFileUpload,
    handleHideCandidate,
    handleToggleFavorite,
    hasDocuments,
    hasPearchData,
    hasPersonalData,
    isDragging,
    isFavorite,
    isHidden,
    isLoadingActivities,
    isLoadingAnalyses,
    isLoadingFiles,
    isLoadingOpinions,
    isUploading,
    languagesData,
    loading,
    router,
    newNoteCategory,
    newNoteContent,
    openCommunicationModal,
    opinion,
    opinionsHistory,
    opinionsSubTab,
    periodFilter,
    savedAnalyses,
    selectedCategory,
    setActiveTab,
    setActivities,
    setActivityFilter,
    setActivityView,
    setExpandedAnalysisId,
    setExpandedOpinionId,
    setIsDragging,
    setNewNoteCategory,
    setNewNoteContent,
    setOpinionsSubTab,
    setPeriodFilter,
    setSelectedCategory,
    setShowAddToListModal,
    setShowAddToVacancyModal,
    setShowCommunicationModal,
    setShowLiaAnalysisModal,
    showAddToListModal,
    showAddToVacancyModal,
    showCommunicationModal,
    showLiaAnalysisModal,
    skillCategories,
    toast,
    uploadProgress
  }
}
