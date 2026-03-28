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
import { LiaAnalysisModal } from "@/components/modals/lia-analysis-modal"

type ActiveTab = 'profile' | 'activities' | 'files' | 'opinions'
type ActivityCategory = 'all' | 'interview' | 'screening' | 'general'

interface OpinionData {
  current_general_opinion?: any
  vacancy_opinions?: any[]
}

export default function CandidateProfilePage() {
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
          const additionalData = (data as any)?.additional_data
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
          const additionalData = (data as any)?.additional_data
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

  const hasPearchData = (c: any): boolean => {
    return !!(c.headline || c.is_open_to_work || c.is_decision_maker || 
              c.is_top_universities || c.is_hiring || c.linkedin_followers_count || 
              c.linkedin_connections_count || c.pearch_profile_id)
  }

  const hasPersonalData = (c: any): boolean => {
    return !!(c.date_of_birth || c.gender || c.nationality || 
              c.marital_status || c.estimated_age)
  }

  const hasAdditionalContacts = (c: any): boolean => {
    return !!(c.secondary_email || c.secondary_phone || c.best_personal_email || 
              c.best_business_email || c.preferred_contact_method || c.best_time_to_contact)
  }

  const hasDocuments = (c: any): boolean => {
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
      'cv': { bg: '#10B98120', text: 'var(--status-success)' },
      'photo': { bg: 'var(--gray-200)', text: 'var(--gray-600)' },
      'portfolio': { bg: 'var(--gray-200)', text: 'var(--gray-600)' },
      'video': { bg: '#EF444420', text: 'var(--status-error)' },
      'certificate': { bg: '#F59E0B20', text: 'var(--status-warning)' },
      'document': { bg: '#6B728020', text: 'var(--gray-400)' },
      'screening': { bg: '#F9731620', text: 'var(--status-warning)' },
      'interview': { bg: '#8B5CF620', text: 'var(--wedo-purple)' },
      'transcript': { bg: '#8B5CF620', text: 'var(--wedo-purple)' },
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-gray-600 dark:text-gray-400 mx-auto mb-3" />
          <p className="text-sm text-gray-600 dark:text-gray-400">Carregando perfil...</p>
        </div>
      </div>
    )
  }

  if (error || !candidate) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <p className="text-sm text-status-error mb-4">{error || "Candidato não encontrado"}</p>
          <Button variant="outline" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar
          </Button>
        </div>
      </div>
    )
  }

  const languagesData = parseLanguages(candidate.languages)
  const skillCategories = categorizeSkills([...(candidate.technical_skills || []), ...(candidate.expertise || [])])
  const experiences = (candidate as any).workHistory || (candidate as any).work_history || (candidate as any).experiences || ((candidate as any).additional_data as any)?.work_history || ((candidate as any).additional_data as any)?.experiences || []
  const education = (candidate as any).education || ((candidate as any).additional_data as any)?.education || []
  const opinion = opinionsData?.current_general_opinion || opinionsData?.vacancy_opinions?.[0]

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => router.back()}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar
          </Button>

          {/* HEADER */}
          <Card className="mb-4 border-gray-100">
            <CardContent className="py-5 px-6">
              <div className="flex items-start gap-5">
                <Avatar className="h-20 w-20 border-2 border-gray-100">
                  {candidate.avatar_url && <AvatarImage src={candidate.avatar_url} alt={candidate.name} />}
                  <AvatarFallback className="bg-gray-100 text-gray-600 text-xl font-semibold">
                    {getInitials(candidate.name)}
                  </AvatarFallback>
                </Avatar>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1.5 flex-wrap">
                    <h1 className="text-xl font-semibold text-gray-950 dark:text-gray-50">
                      {candidate.name}
                    </h1>
                    <span className="text-xs font-mono text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                      {getShortId(candidate.id)}
                    </span>
                    
                    {candidate.seniority_level && (
                      <Badge className={badgeStyles.primary}>{candidate.seniority_level}</Badge>
                    )}
                    {candidate.years_of_experience && (
                      <Badge variant="outline" className="text-xs">{candidate.years_of_experience} anos exp.</Badge>
                    )}
                    {candidate.communication_consent && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Badge className="text-xs bg-status-success/10 text-status-success border-status-success/30">
                            <Shield className="w-3 h-3 mr-1" />
                            LGPD
                          </Badge>
                        </TooltipTrigger>
                        <TooltipContent>Consentimento LGPD obtido</TooltipContent>
                      </Tooltip>
                    )}
                    {candidate.is_blacklisted && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Badge className="text-xs bg-status-error/10 text-status-error border-status-error/30">⚠️ LCNU</Badge>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p className="font-medium">Lista de Candidatos Não Utilizáveis</p>
                          {candidate.blacklist_reason && <p className="text-xs">{candidate.blacklist_reason}</p>}
                        </TooltipContent>
                      </Tooltip>
                    )}
                    
                    {/* Tags: Tech & Potencial */}
                    {(candidate as any).is_tech && (
                      <Badge variant="outline" className="text-xs bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600">
                        Tech
                      </Badge>
                    )}
                    {(candidate as any).is_potential && (
                      <Badge variant="outline" className="text-xs bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                        Potencial
                      </Badge>
                    )}
                    
                    {/* Status do Candidato */}
                    {(() => {
                      const status = (candidate as any).candidate_status || 'active'
                      const statusConfig: Record<string, { label: string, bg: string, text: string, border: string }> = {
                        'active': { label: 'Ativo', bg: 'bg-status-success/10', text: 'text-status-success', border: 'border-status-success/30' },
                        'do_not_use': { label: 'Não Utilizar', bg: 'bg-status-error/10', text: 'text-status-error', border: 'border-status-error/30' },
                        'hired': { label: 'Contratado', bg: 'bg-gray-50 dark:bg-gray-900', text: 'text-gray-900 dark:text-gray-50', border: 'border-gray-300 dark:border-gray-600' },
                        'inactive': { label: 'Inativo', bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-300' }
                      }
                      const config = statusConfig[status] || statusConfig['active']
                      return (
                        <Badge className={`text-xs ${config.bg} ${config.text} ${config.border}`}>
                          {config.label}
                        </Badge>
                      )
                    })()}
                    
                    {/* Ícone Cérebro LIA - Análises */}
                    <LiaAnalysisModal
                      isOpen={showLiaAnalysisModal}
                      onClose={() => setShowLiaAnalysisModal(false)}
                      onOpen={() => setShowLiaAnalysisModal(true)}
                      candidate={candidate}
                      onTransportToOpinions={() => {
                        fetchSavedAnalyses()
                      }}
                    >
                      <button 
                        className="p-1.5 rounded-full hover:bg-gray-100 dark:bg-gray-800 transition-colors"
                        title="Análise LIA do Perfil"
                      >
                        <Brain className="w-5 h-5 text-wedo-cyan" />
                      </button>
                    </LiaAnalysisModal>
                  </div>

                  <div className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200 mb-1">
                    {candidate.current_title && (
                      <>
                        <Briefcase className="w-4 h-4 text-gray-400" />
                        <span className="font-medium">{candidate.current_title}</span>
                      </>
                    )}
                    {candidate.current_company && (
                      <>
                        <span className="text-gray-400">•</span>
                        <Building className="w-4 h-4 text-gray-400" />
                        <span>{candidate.current_company}</span>
                      </>
                    )}
                  </div>

                  {(candidate.location_city || candidate.location_state) && (
                    <div className="flex items-center gap-1.5 text-sm text-gray-500 mb-3">
                      <MapPin className="w-4 h-4" />
                      <span>
                        {[candidate.location_city, candidate.location_state, candidate.location_country]
                          .filter(Boolean).join(', ')}
                      </span>
                    </div>
                  )}

                  <div className="flex items-center gap-4 flex-wrap">
                    {candidate.email && (
                      <a href={`mailto:${candidate.email}`} className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
                        <Mail className="w-4 h-4" />
                        {candidate.email}
                      </a>
                    )}
                    {(candidate.phone || candidate.mobile_phone) && (
                      <a href={`tel:${candidate.mobile_phone || candidate.phone}`} className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
                        <Phone className="w-4 h-4" />
                        {candidate.mobile_phone || candidate.phone}
                      </a>
                    )}
                    {/* Social Icons - Always visible */}
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a 
                          href={candidate.linkedin_url || '#'} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`p-1.5 rounded-md transition-colors ${candidate.linkedin_url ? 'hover:bg-gray-100 dark:hover:bg-gray-800' : 'opacity-30 cursor-default'}`}
                          onClick={(e) => !candidate.linkedin_url && e.preventDefault()}
                        >
                          <Linkedin className="w-5 h-5" style={{ color: candidate.linkedin_url ? '#0A66C2' : 'var(--gray-400)' }} />
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>LinkedIn</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a 
                          href={candidate.github_url || '#'} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`p-1.5 rounded-md transition-colors ${candidate.github_url ? 'hover:bg-gray-100' : 'opacity-30 cursor-default'}`}
                          onClick={(e) => !candidate.github_url && e.preventDefault()}
                        >
                          <Github className="w-5 h-5" style={{ color: candidate.github_url ? '#181717' : 'var(--gray-400)' }} />
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>GitHub</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a 
                          href={(candidate as any).stackoverflow_url || '#'} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`p-1.5 rounded-md transition-colors ${(candidate as any).stackoverflow_url ? 'hover:bg-wedo-orange/10' : 'opacity-30 cursor-default'}`}
                          onClick={(e) => !(candidate as any).stackoverflow_url && e.preventDefault()}
                        >
                          <svg className="w-5 h-5" viewBox="0 0 24 24" fill={(candidate as any).stackoverflow_url ? '#F48024' : 'var(--gray-400)'}><path d="M15 21H3v-8h2v6h10v-6h2v8z"/><path d="M5 15h10v-2H5v2zm0-3.5h10v-2H5v2zm.05-3.45l9.85 2.05.4-1.95L5.45 6l-.4 1.95zM7.15 4.55l8.95 4.55.85-1.7L8 2.85l-.85 1.7z"/></svg>
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>StackOverflow</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a 
                          href={(candidate as any).twitter_url || (candidate as any).x_url || '#'} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`p-1.5 rounded-md transition-colors ${((candidate as any).twitter_url || (candidate as any).x_url) ? 'hover:bg-gray-100' : 'opacity-30 cursor-default'}`}
                          onClick={(e) => !((candidate as any).twitter_url || (candidate as any).x_url) && e.preventDefault()}
                        >
                          <svg className="w-5 h-5" viewBox="0 0 24 24" fill={((candidate as any).twitter_url || (candidate as any).x_url) ? '#000000' : 'var(--gray-400)'}><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>X / Twitter</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a 
                          href={(candidate as any).behance_url || '#'} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`p-1.5 rounded-md transition-colors ${(candidate as any).behance_url ? 'hover:bg-gray-100 dark:hover:bg-gray-800' : 'opacity-30 cursor-default'}`}
                          onClick={(e) => !(candidate as any).behance_url && e.preventDefault()}
                        >
                          <svg className="w-5 h-5" viewBox="0 0 24 24" fill={(candidate as any).behance_url ? '#1769FF' : 'var(--gray-400)'}><path d="M7.5 11c1.5 0 2.5-.8 2.5-2.2S9 6.5 7.5 6.5H4v4.5h3.5zm.5 1H4v5h4c1.8 0 3-1.1 3-2.5S9.8 12 8 12zm8.5-1c-1.5 0-2.5.8-2.5 2h5c0-1.2-1-2-2.5-2z"/><path d="M22.5 6H14v1.5h8.5V6zm-.5 5c0-2.5-2-4.5-4.5-4.5S13 8.5 13 11s2 4.5 4.5 4.5c1.5 0 3-.8 3.8-2h-1.8c-.5.6-1.2 1-2 1-1.5 0-2.5-1-2.5-2.5h6.5v-.5c0-.2 0-.3-.5-.5z"/></svg>
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>Behance</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a 
                          href={candidate.portfolio_url || '#'} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`p-1.5 rounded-md transition-colors ${candidate.portfolio_url ? 'hover:bg-gray-100 dark:hover:bg-gray-800' : 'opacity-30 cursor-default'}`}
                          onClick={(e) => !candidate.portfolio_url && e.preventDefault()}
                        >
                          <Globe className="w-5 h-5" style={{ color: candidate.portfolio_url ? 'var(--gray-950)' : 'var(--gray-400)' }} />
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>Portfolio</TooltipContent>
                    </Tooltip>
                  </div>

                </div>

                {/* RIGHT SIDE COLUMN - Extended Info */}
                <div className="text-right space-y-3 min-w-[200px]">
                  {/* Work Preferences (Híbrido, CLT, etc) */}
                  <div className="flex flex-wrap gap-1.5 justify-end">
                    {(candidate as any).work_model && (
                      <Badge variant="outline" className="text-xs bg-gray-50 text-gray-800 dark:text-gray-200 border-gray-200">
                        {(candidate as any).work_model}
                      </Badge>
                    )}
                    {(candidate as any).work_mode && (
                      <Badge variant="outline" className="text-xs bg-gray-50 text-gray-800 dark:text-gray-200 border-gray-200">
                        {(candidate as any).work_mode}
                      </Badge>
                    )}
                    {(candidate as any).contract_type && (
                      <Badge variant="outline" className="text-xs bg-gray-50 text-gray-800 dark:text-gray-200 border-gray-200">
                        {(candidate as any).contract_type}
                      </Badge>
                    )}
                    {(candidate as any).is_remote && (
                      <Badge variant="outline" className="text-xs bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-50 border-gray-300 dark:border-gray-600">
                        🌐 Remoto
                      </Badge>
                    )}
                    {(candidate as any).willing_to_relocate && (
                      <Badge variant="outline" className="text-xs bg-status-success/10 text-status-success border-status-success/30">
                        ✈️ Aceita Mudança
                      </Badge>
                    )}
                    {(candidate as any).mobility && (
                      <Badge variant="outline" className="text-xs bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                        🚗 Mobilidade
                      </Badge>
                    )}
                    {(candidate as any).availability && (
                      <Badge variant="outline" className="text-xs bg-gray-50 text-gray-800 dark:text-gray-200 border-gray-200">
                        {(candidate as any).availability}
                      </Badge>
                    )}
                  </div>
                  
                  {/* Dates Section */}
                  <div className="text-xs text-gray-500 space-y-0.5">
                    <p className="font-medium text-gray-800 dark:text-gray-200">Datas</p>
                    {candidate.updated_at && (
                      <p>Atualizado: {formatDate(candidate.updated_at)}</p>
                    )}
                    {(candidate as any).last_contact_at && (
                      <p>Último contato: {formatDate((candidate as any).last_contact_at)}</p>
                    )}
                    {(candidate as any).last_activity_at && (
                      <p>Última atividade: {formatDate((candidate as any).last_activity_at)}</p>
                    )}
                    {!candidate.updated_at && !(candidate as any).last_contact_at && !(candidate as any).last_activity_at && candidate.created_at && (
                      <p>Cadastro: {formatDate(candidate.created_at)}</p>
                    )}
                  </div>
                  
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ACTION BAR - Ícones coloridos como no CandidatePreview */}
          <Card className="mb-4 border-gray-100">
            <CardContent className="py-3 px-4">
              <div className="flex items-center gap-2 flex-wrap">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => openCommunicationModal('email')} className="gap-1.5">
                      <Mail className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      Email
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Enviar Email</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => openCommunicationModal('whatsapp')} className="gap-1.5">
                      <MessageSquare className="w-4 h-4 text-status-success" />
                      WhatsApp
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Enviar WhatsApp</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => openCommunicationModal('agendamento')} className="gap-1.5">
                      <CalendarDays className="w-4 h-4 text-wedo-orange" />
                      Agendar Entrevista
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Agendar Entrevista</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => openCommunicationModal('triagem')} className="gap-1.5">
                      <ClipboardCheck className="w-4 h-4 text-wedo-purple" />
                      Triagem WSI
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Enviar Triagem WSI</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => setShowAddToVacancyModal(true)} className="gap-1.5">
                      <UserPlus className="w-4 h-4 text-gray-600" />
                      Adicionar à Vaga
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Adicionar à Vaga</TooltipContent>
                </Tooltip>
                <Separator orientation="vertical" className="h-6 mx-2" />
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button 
                      size="sm" 
                      variant={isFavorite ? "default" : "outline"} 
                      onClick={handleToggleFavorite} 
                      className={`gap-1.5 ${isFavorite ? 'bg-wedo-magenta hover:bg-wedo-magenta text-white' : ''}`}
                    >
                      <Heart className={`w-4 h-4 ${isFavorite ? 'fill-current text-white' : 'text-wedo-magenta'}`} />
                      {isFavorite ? 'Favoritado' : 'Favoritar'}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>{isFavorite ? 'Remover dos Favoritos' : 'Adicionar aos Favoritos'}</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => setShowAddToListModal(true)} className="gap-1.5">
                      <Plus className="w-4 h-4 text-gray-600" />
                      Adicionar à Lista
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Adicionar à Lista</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button 
                      size="sm" 
                      variant={isHidden ? "default" : "outline"} 
                      onClick={handleHideCandidate}
                      className={`gap-1.5 ${isHidden ? 'bg-gray-500 hover:bg-gray-600 text-white' : ''}`}
                    >
                      <EyeOff className={`w-4 h-4 ${isHidden ? 'text-white' : 'text-gray-500'}`} />
                      {isHidden ? 'Oculto' : 'Ocultar'}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>{isHidden ? 'Mostrar Candidato' : 'Ocultar Candidato'}</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => openCommunicationModal('feedback')} className="gap-1.5">
                      <Send className="w-4 h-4 text-gray-600" />
                      Feedback
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Enviar Feedback</TooltipContent>
                </Tooltip>
              </div>
            </CardContent>
          </Card>

          {/* TABS */}
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as ActiveTab)} className="space-y-4">
            <TabsList className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
              <TabsTrigger value="profile" className="gap-1.5">
                <FileText className="w-4 h-4" />
                Perfil Completo
              </TabsTrigger>
              <TabsTrigger value="activities" className="gap-1.5">
                <Activity className="w-4 h-4" />
                Atividades
              </TabsTrigger>
              <TabsTrigger value="files" className="gap-1.5">
                <List className="w-4 h-4" />
                Arquivos
              </TabsTrigger>
              <TabsTrigger value="opinions" className="gap-1.5">
                <Brain className="w-4 h-4 text-wedo-cyan" />
                Pareceres e Análises
              </TabsTrigger>
            </TabsList>

            {/* Experience Highlight - AI-generated summary */}
            {candidate && (
              <ExperienceHighlightCard candidate={candidate as any} companyId="demo_company" />
            )}

            {/* TAB: PROFILE */}
            <TabsContent value="profile" className="mt-4">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* LEFT COLUMN (2/3) */}
                <div className="lg:col-span-2 space-y-4">
                  {/* Technical Skills */}
                  {candidate.technical_skills && candidate.technical_skills.length > 0 && (
                    <Card className="border-gray-100">
                      <CardHeader className="py-2.5 px-4">
                        <CardTitle className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                          <Code className="w-4 h-4 text-gray-600" />
                          Skills Principais
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="px-4 pb-4">
                        <div className="flex flex-wrap gap-1.5">
                          {candidate.technical_skills.map((skill, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs px-2 py-0.5">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Skills Map - Categorized */}
                  {skillCategories.length > 0 && (
                    <Card className="border-gray-100">
                      <CardHeader className="py-2.5 px-4">
                        <CardTitle className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                          <Code className="w-4 h-4 text-gray-600" />
                          Mapa de Skills
                          <Badge className="text-xs bg-gray-200 text-gray-800 dark:text-gray-200">
                            {candidate.technical_skills?.length || 0} itens
                          </Badge>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="px-4 pb-4 space-y-3">
                        {skillCategories.map(([key, category]) => (
                          <div key={key}>
                            <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5">{category.label}</h5>
                            <div className="flex flex-wrap gap-1.5">
                              {category.skills.map((skill, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs px-2 py-0.5 bg-gray-50">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        ))}
                        
                        {/* Soft Skills */}
                        {candidate.soft_skills && candidate.soft_skills.length > 0 && (
                          <div>
                            <h5 className="text-xs font-medium text-status-warning mb-1.5 flex items-center gap-1">
                              <Users className="w-3 h-3" /> Soft Skills
                            </h5>
                            <div className="flex flex-wrap gap-1.5">
                              {candidate.soft_skills.map((skill, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs px-2 py-0.5 bg-status-warning/10 text-status-warning border-status-warning/30">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}

                  {/* Professional Experience */}
                  <Card className="border-gray-100">
                    <CardHeader className="py-2.5 px-4">
                      <CardTitle className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                        <Briefcase className="w-4 h-4 text-gray-600" />
                        Experiência Profissional
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="px-4 pb-4 space-y-4">
                      {experiences.length > 0 ? (
                        experiences.map((exp: any, index: number) => {
                          const title = exp.title || exp.position || exp.role || ''
                          const company = exp.company || exp.company_name || ''
                          const location = exp.location || ''
                          const startDate = exp.start_date || exp.startDate || ''
                          const endDate = exp.is_current ? 'Atual' : (exp.end_date || exp.endDate || '')
                          const description = exp.description || ''
                          const industries = Array.isArray(exp.industries) ? exp.industries : []
                          const technologies = Array.isArray(exp.technologies) ? exp.technologies : []
                          const companySize = exp.company_size || exp.company_size_range || null
                          const isStartup = exp.is_startup
                          
                          return (
                            <div key={index} className={`border-l-2 ${index === 0 ? 'border-gray-700' : 'border-gray-300'} pl-3`}>
                              <div className="flex items-start justify-between gap-2 mb-1">
                                <div>
                                  <h5 className="text-sm font-medium text-gray-800">{title || 'Cargo não informado'}</h5>
                                  <p className="text-sm text-gray-600">
                                    {company || 'Empresa não informada'}
                                    {location && ` • ${location}`}
                                    {exp.duration_years && <span className="text-gray-400 ml-1">({exp.duration_years.toFixed(1)} anos)</span>}
                                  </p>
                                </div>
                                <span className="text-xs text-gray-500 whitespace-nowrap">
                                  {formatDateShort(startDate)}{startDate && endDate ? ' - ' : ''}{endDate === 'Atual' ? 'Atual' : formatDateShort(endDate)}
                                </span>
                              </div>
                              
                              {/* Metadata Row */}
                              <div className="flex flex-wrap gap-1.5 mb-2">
                                {industries.slice(0, 2).map((ind: string, idx: number) => (
                                  <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-50 border border-gray-200 dark:border-gray-700">
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
                                  <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-micro bg-gray-50 text-gray-600 border border-gray-100">
                                    <Users className="w-2.5 h-2.5" />
                                    {companySize}
                                  </span>
                                )}
                              </div>

                              {/* Technologies */}
                              {technologies.length > 0 && (
                                <div className="flex flex-wrap gap-1 mb-2">
                                  <span className="text-micro text-gray-400 flex items-center gap-0.5">
                                    <Code className="w-2.5 h-2.5" />
                                    Stack:
                                  </span>
                                  {technologies.slice(0, 6).map((tech: string, idx: number) => (
                                    <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-gray-100 text-gray-800 dark:text-gray-200">
                                      {tech}
                                    </span>
                                  ))}
                                  {technologies.length > 6 && (
                                    <span className="text-micro text-gray-400">+{technologies.length - 6}</span>
                                  )}
                                </div>
                              )}
                              
                              {description && (
                                <p className="text-xs text-gray-600 mt-1">{description}</p>
                              )}
                            </div>
                          )
                        })
                      ) : (
                        <p className="text-sm text-gray-500 italic">Não informado</p>
                      )}
                    </CardContent>
                  </Card>

                  {/* Education */}
                  <Card className="border-gray-100">
                    <CardHeader className="py-2.5 px-4">
                      <CardTitle className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                        <GraduationCap className="w-4 h-4 text-gray-600" />
                        Formação Acadêmica
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="px-4 pb-4 space-y-3">
                      {education.length > 0 ? (
                        education.map((edu: any, index: number) => (
                          <div key={index} className={`flex items-start justify-between gap-2 ${index < education.length - 1 ? 'pb-3 border-b border-gray-100' : ''}`}>
                            <div>
                              <h5 className="text-sm font-medium text-gray-800">
                                {edu.degree || edu.title || 'Formação'}
                                {(edu.field_of_study || edu.fieldOfStudy) && ` em ${edu.field_of_study || edu.fieldOfStudy}`}
                              </h5>
                              <p className="text-sm text-gray-600">{edu.school || edu.institution || 'Instituição não informada'}</p>
                            </div>
                            <span className="text-xs text-gray-500 whitespace-nowrap">
                              {edu.start_date || edu.startDate || ''}{(edu.start_date || edu.startDate) && (edu.end_date || edu.endDate) ? ' - ' : ''}{edu.end_date || edu.endDate || ''}
                            </span>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500 italic">Não informado</p>
                      )}
                    </CardContent>
                  </Card>

                  {/* Certifications */}
                  {candidate.certifications && candidate.certifications.length > 0 && (
                    <Card className="border-gray-100">
                      <CardHeader className="py-2.5 px-4">
                        <CardTitle className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                          <Award className="w-4 h-4 text-gray-600" />
                          Certificações
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="px-4 pb-4">
                        <div className="flex flex-wrap gap-2">
                          {candidate.certifications.map((cert, idx) => {
                            const certName = typeof cert === 'string' ? cert : (cert as any).name || 'Certificação'
                            return (
                              <Badge key={idx} variant="secondary" className="text-xs px-2 py-1">
                                {certName}
                              </Badge>
                            )
                          })}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>

                {/* RIGHT COLUMN (1/3) */}
                <div className="space-y-4">
                  {/* Salary Card */}
                  <Card className="border-gray-100">
                    <CardHeader className="py-2.5 px-4">
                      <CardTitle className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                        <DollarSign className="w-4 h-4 text-gray-600" />
                        Remuneração
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="px-4 pb-4 space-y-2">
                      {candidate.current_salary && (
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-gray-500">Salário Atual</span>
                          <span className="text-sm font-medium text-gray-800">{formatCurrency(candidate.current_salary, candidate.salary_currency || 'BRL')}</span>
                        </div>
                      )}
                      {candidate.salary_expectation_clt && (
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-gray-500">Pretensão CLT</span>
                          <span className="text-sm font-medium text-gray-800">{formatCurrency(candidate.salary_expectation_clt)}</span>
                        </div>
                      )}
                      {candidate.salary_expectation_pj && (
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-gray-500">Pretensão PJ</span>
                          <span className="text-sm font-medium text-gray-800">{formatCurrency(candidate.salary_expectation_pj)}</span>
                        </div>
                      )}
                      {candidate.salary_expectation_freelance && (
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-gray-500">Freelance</span>
                          <span className="text-sm font-medium text-gray-800">{formatCurrency(candidate.salary_expectation_freelance)}</span>
                        </div>
                      )}
                      {(candidate.desired_salary_min || candidate.desired_salary_max) && (
                        <div className="flex justify-between items-center pt-2 border-t border-gray-100">
                          <span className="text-xs text-gray-500">Faixa Desejada</span>
                          <span className="text-sm font-medium text-gray-800">
                            {formatCurrency(candidate.desired_salary_min)} - {formatCurrency(candidate.desired_salary_max)}
                          </span>
                        </div>
                      )}
                      {candidate.salary_expectation_clt && (
                        <div className="flex justify-between items-center pt-2 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 -mx-4 px-4 py-2">
                          <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Total Anual (CLT)</span>
                          <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                            {formatCurrency(candidate.salary_expectation_clt * 13.33)}
                          </span>
                        </div>
                      )}
                      {!candidate.current_salary && !candidate.salary_expectation_clt && !candidate.salary_expectation_pj && (
                        <p className="text-sm text-gray-500 italic">Não informado</p>
                      )}
                    </CardContent>
                  </Card>

                  {/* Languages Card */}
                  <Card className="border-gray-100">
                    <CardHeader className="py-2.5 px-4">
                      <CardTitle className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                        <Languages className="w-4 h-4 text-gray-600" />
                        Idiomas
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="px-4 pb-4 space-y-3">
                      {languagesData.length > 0 ? (
                        languagesData.map((lang, index) => {
                          const levelInfo = getLanguageLevel(lang.level)
                          return (
                            <div key={index} className="space-y-1">
                              <div className="flex justify-between items-center">
                                <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{lang.language}</span>
                                <span className="text-xs text-gray-500">{levelInfo.label}</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-1.5">
                                <div 
                                  className={`h-1.5 rounded-full ${levelInfo.color}`} 
                                  style={{ width: `${levelInfo.percent}%` }}
                                />
                              </div>
                            </div>
                          )
                        })
                      ) : (
                        <p className="text-sm text-gray-500 italic">Não informado</p>
                      )}
                    </CardContent>
                  </Card>

                  {/* Additional Details Card */}
                  <Card className="border-gray-100">
                    <CardHeader className="py-2.5 px-4">
                      <CardTitle className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                        <Home className="w-4 h-4 text-gray-600" />
                        Detalhes Adicionais
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="px-4 pb-4 space-y-3">
                      {/* Location */}
                      <div>
                        <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1">Localização</h5>
                        <p className="text-sm text-gray-600">
                          {[candidate.location_city, candidate.location_state, candidate.location_country]
                            .filter(Boolean).join(', ') || 'Não informado'}
                        </p>
                        {(candidate.address_street || candidate.address_district) && (
                          <p className="text-xs text-gray-500 mt-0.5">
                            {[candidate.address_street, candidate.address_number, candidate.address_district, candidate.address_zip, (candidate as any).address_complement]
                              .filter(Boolean).join(', ')}
                          </p>
                        )}
                      </div>

                      {/* Work Preferences */}
                      <div>
                        <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5">Preferências de Trabalho</h5>
                        <div className="flex flex-wrap gap-1.5">
                          {candidate.is_remote && (
                            <Badge variant="outline" className="text-xs bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-50 border-gray-300 dark:border-gray-600">Remoto</Badge>
                          )}
                          {candidate.willing_to_relocate && (
                            <Badge variant="outline" className="text-xs bg-status-success/10 text-status-success border-status-success/30">Aceita Relocação</Badge>
                          )}
                          {candidate.work_model_preference && (
                            <Badge variant="outline" className="text-xs">{candidate.work_model_preference}</Badge>
                          )}
                          {candidate.contract_type_preference && (
                            <Badge variant="outline" className="text-xs">{candidate.contract_type_preference}</Badge>
                          )}
                        </div>
                      </div>

                      {/* Dates */}
                      <div>
                        <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1">Datas</h5>
                        <div className="space-y-0.5 text-xs text-gray-600">
                          {candidate.created_at && <p>Cadastro: {formatDate(candidate.created_at)}</p>}
                          {candidate.updated_at && <p>Atualizado: {formatDate(candidate.updated_at)}</p>}
                          {candidate.last_contacted_at && <p>Último contato: {formatDate(candidate.last_contacted_at)}</p>}
                          {candidate.last_activity_at && <p>Última atividade: {formatDate(candidate.last_activity_at)}</p>}
                        </div>
                      </div>

                      {/* Status */}
                      <div>
                        <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5">Status</h5>
                        <div className="flex flex-wrap gap-1.5">
                          <Badge variant="outline" className={`text-xs ${candidate.is_active ? 'bg-status-success/10 text-status-success' : 'bg-gray-100 text-gray-600'}`}>
                            {candidate.is_active ? 'Ativo' : 'Inativo'}
                          </Badge>
                          {candidate.source && (
                            <Badge variant="outline" className="text-xs">{candidate.source}</Badge>
                          )}
                        </div>
                      </div>

                      {/* Tags */}
                      {candidate.tags && candidate.tags.length > 0 && (
                        <div>
                          <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5">Tags</h5>
                          <div className="flex flex-wrap gap-1">
                            {candidate.tags.map((tag, idx) => (
                              <Badge key={idx} className="text-xs bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Personal Data Card - Dados Pessoais */}
                  {hasPersonalData(candidate) && (
                    <Card className="border-gray-100">
                      <CardHeader className="py-2.5 px-4">
                        <CardTitle className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                          <User className="w-4 h-4 text-gray-600" />
                          Dados Pessoais
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="px-4 pb-4 space-y-2">
                        {((candidate as any).date_of_birth || (candidate as any).estimated_age) && (
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-gray-500 flex items-center gap-1">
                              <Cake className="w-3.5 h-3.5" />
                              Idade
                            </span>
                            <span className="text-sm font-medium text-gray-800">
                              {calculateAge((candidate as any).date_of_birth) || (candidate as any).estimated_age} anos
                              {(candidate as any).date_of_birth && (
                                <span className="text-xs text-gray-400 ml-1">
                                  ({formatDate((candidate as any).date_of_birth)})
                                </span>
                              )}
                            </span>
                          </div>
                        )}
                        {(candidate as any).gender && (
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-gray-500">Gênero</span>
                            <span className="text-sm font-medium text-gray-800">{(candidate as any).gender}</span>
                          </div>
                        )}
                        {(candidate as any).nationality && (
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-gray-500">Nacionalidade</span>
                            <span className="text-sm font-medium text-gray-800">{(candidate as any).nationality}</span>
                          </div>
                        )}
                        {(candidate as any).marital_status && (
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-gray-500">Estado Civil</span>
                            <span className="text-sm font-medium text-gray-800">{(candidate as any).marital_status}</span>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}

                  {/* LinkedIn/Pearch Insights Card */}
                  {hasPearchData(candidate) && (
                    <Card className="border-gray-100 border-l-4 border-l-[#0A66C2]">
                      <CardHeader className="py-2.5 px-4">
                        <CardTitle className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                          <Linkedin className="w-4 h-4 text-[#0A66C2]" />
                          LinkedIn Insights
                          {(candidate as any).pearch_profile_id && (
                            <Badge className="text-micro px-1.5 py-0 bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">Pearch</Badge>
                          )}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="px-4 pb-4 space-y-3">
                        {(candidate as any).headline && (
                          <div>
                            <p className="text-sm text-gray-800 dark:text-gray-200 italic">"{(candidate as any).headline}"</p>
                          </div>
                        )}
                        
                        {/* Badges de Status */}
                        <div className="flex flex-wrap gap-1.5">
                          {(candidate as any).is_open_to_work && (
                            <Badge className="text-xs bg-status-success/10 text-status-success border-status-success/30">
                              ✓ Open to Work
                            </Badge>
                          )}
                          {(candidate as any).is_decision_maker && (
                            <Badge className="text-xs bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                              👔 Decision Maker
                            </Badge>
                          )}
                          {(candidate as any).is_top_universities && (
                            <Badge className="text-xs bg-status-warning/10 text-status-warning border-status-warning/30">
                              🎓 Top Universities
                            </Badge>
                          )}
                          {(candidate as any).is_hiring && (
                            <Badge className="text-xs bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-50 border-gray-300 dark:border-gray-600">
                              📢 Hiring
                            </Badge>
                          )}
                        </div>

                        {/* Connections & Followers */}
                        {((candidate as any).linkedin_connections_count || (candidate as any).linkedin_followers_count) && (
                          <div className="flex gap-4 pt-2 border-t border-gray-100">
                            {(candidate as any).linkedin_connections_count && (
                              <div className="text-center">
                                <p className="text-lg font-semibold text-gray-800">
                                  {(candidate as any).linkedin_connections_count.toLocaleString('pt-BR')}
                                </p>
                                <p className="text-micro text-gray-500">Conexões</p>
                              </div>
                            )}
                            {(candidate as any).linkedin_followers_count && (
                              <div className="text-center">
                                <p className="text-lg font-semibold text-gray-800">
                                  {(candidate as any).linkedin_followers_count.toLocaleString('pt-BR')}
                                </p>
                                <p className="text-micro text-gray-500">Seguidores</p>
                              </div>
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}

                  {/* Documents Card */}
                  {hasDocuments(candidate) && (
                    <Card className="border-gray-100">
                      <CardHeader className="py-2.5 px-4">
                        <CardTitle className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                          <FileText className="w-4 h-4 text-gray-600" />
                          Documentos
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="px-4 pb-4 space-y-3">
                        {(candidate as any).resume_url && (
                          <div>
                            <a 
                              href={(candidate as any).resume_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 rounded-md text-sm text-gray-800 dark:text-gray-200 transition-colors"
                            >
                              <Download className="w-4 h-4" />
                              Baixar Currículo
                              <ExternalLink className="w-3 h-3 text-gray-400" />
                            </a>
                          </div>
                        )}
                        
                        {(candidate as any).self_introduction && (
                          <div>
                            <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 flex items-center gap-1">
                              <Brain className="w-3 h-3 text-wedo-cyan" />
                              Apresentação Profissional
                            </h5>
                            <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md leading-relaxed">
                              {(candidate as any).self_introduction.length > 300 
                                ? `${(candidate as any).self_introduction.slice(0, 300)}...` 
                                : (candidate as any).self_introduction}
                            </p>
                          </div>
                        )}
                        
                        {(candidate as any).cover_letter && (
                          <div>
                            <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 flex items-center gap-1">
                              <Mail className="w-3 h-3" />
                              Carta de Apresentação
                            </h5>
                            <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md leading-relaxed">
                              {(candidate as any).cover_letter.length > 300 
                                ? `${(candidate as any).cover_letter.slice(0, 300)}...` 
                                : (candidate as any).cover_letter}
                            </p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}

                  {/* Interests Card */}
                  {(candidate as any).interests && (candidate as any).interests.length > 0 && (
                    <Card className="border-gray-100">
                      <CardHeader className="py-2.5 px-4">
                        <CardTitle className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                          <Lightbulb className="w-4 h-4 text-gray-600" />
                          Interesses
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="px-4 pb-4">
                        <div className="flex flex-wrap gap-1.5">
                          {((candidate as any).interests as string[]).map((interest: string, idx: number) => (
                            <Badge key={idx} variant="outline" className="text-xs px-2 py-0.5 bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                              {interest}
                            </Badge>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </div>
            </TabsContent>

            {/* TAB: ACTIVITIES */}
            <TabsContent value="activities" className="mt-4">
              <Card className="border-gray-100">
                <CardContent className="p-0">
                  <div className="flex flex-col">
                    {/* Header com filtros e botão de adicionar */}
                    <div className="p-4 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-medium text-gray-800 flex items-center gap-2">
                          <Activity className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                          Feed de Atividades
                          <Badge className="text-xs px-1.5 py-0">{activities.length}</Badge>
                        </h4>
                        <div className="flex items-center gap-2">
                          <select
                            value={periodFilter}
                            onChange={(e) => setPeriodFilter(e.target.value as any)}
                            className="text-xs px-2 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-100/20 dark:text-gray-200"
                          >
                            <option value="7days">Últimos 7 dias</option>
                            <option value="30days">Últimos 30 dias</option>
                            <option value="3months">Últimos 3 meses</option>
                            <option value="all">Todo período</option>
                          </select>
                          <div className="flex items-center bg-white dark:bg-gray-800 rounded-md p-0.5 border border-gray-200 dark:border-gray-600">
                            <button
                              onClick={() => setActivityView('timeline')}
                              className={`p-1.5 rounded transition-colors ${
                                activityView === 'timeline' ? 'bg-gray-200 text-gray-800 dark:text-gray-200' : 'text-gray-600 hover:text-gray-700'
                              }`}
                              title="Visualização Timeline"
                            >
                              <GitBranch className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setActivityView('list')}
                              className={`p-1.5 rounded transition-colors ${
                                activityView === 'list' ? 'bg-gray-200 text-gray-800 dark:text-gray-200' : 'text-gray-600 hover:text-gray-700'
                              }`}
                              title="Visualização Lista"
                            >
                              <List className="w-4 h-4" />
                            </button>
                          </div>
                          <Button size="sm" className="gap-1.5 px-3 py-1.5 text-xs h-8 bg-gray-100 hover:bg-gray-200 text-gray-800 dark:text-gray-200 border border-gray-200">
                            <PlusCircle className="w-3.5 h-3.5" />
                            Nova Atividade
                          </Button>
                        </div>
                      </div>

                      {/* Filtros coloridos */}
                      <div className="flex gap-1.5 flex-wrap">
                        <button
                          onClick={() => setActivityFilter('all')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'all' ? 'bg-gray-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          Todas
                        </button>
                        <button
                          onClick={() => setActivityFilter('emails')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'emails' ? 'bg-gray-700 text-white font-semibold' : 'bg-gray-100 text-gray-800 dark:text-gray-200 hover:bg-gray-200'
                          }`}
                        >
                          📧 Emails
                        </button>
                        <button
                          onClick={() => setActivityFilter('interviews')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'interviews' ? 'bg-gray-700 text-white font-semibold' : 'bg-gray-100 text-gray-800 dark:text-gray-200 hover:bg-gray-200'
                          }`}
                        >
                          🎤 Entrevistas
                        </button>
                        <button
                          onClick={() => setActivityFilter('tests')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'tests' ? 'bg-gray-700 text-white font-semibold' : 'bg-gray-100 text-gray-800 dark:text-gray-200 hover:bg-gray-200'
                          }`}
                        >
                          📝 Testes
                        </button>
                        <button
                          onClick={() => setActivityFilter('lia')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'lia' ? 'bg-status-error text-white' : 'bg-status-error/15 text-status-error hover:bg-status-error/20'
                          }`}
                        >
                          🤖 LIA
                        </button>
                        <button
                          onClick={() => setActivityFilter('offers')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'offers' ? 'bg-gray-700 text-white font-semibold' : 'bg-gray-100 text-gray-800 dark:text-gray-200 hover:bg-gray-200'
                          }`}
                        >
                          💼 Ofertas
                        </button>
                        <button
                          onClick={() => setActivityFilter('applications')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'applications' ? 'bg-gray-700 text-white font-semibold' : 'bg-gray-100 text-gray-800 dark:text-gray-200 hover:bg-gray-200'
                          }`}
                        >
                          📋 Inscrições
                        </button>
                        <button
                          onClick={() => setActivityFilter('notes')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'notes' ? 'bg-status-warning text-white' : 'bg-status-warning/15 text-status-warning hover:bg-status-warning/20'
                          }`}
                        >
                          📝 Notas
                        </button>
                      </div>
                    </div>

                    {/* Seção de Adicionar Nota */}
                    {(activityFilter === 'notes' || activityFilter === 'all') && (
                      <div className="p-4 border-b border-gray-100 bg-status-warning/10/30">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 rounded-full bg-status-warning/15 flex items-center justify-center flex-shrink-0 mt-1">
                            <FileText className="w-4 h-4 text-status-warning" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Categoria:</span>
                              <select 
                                value={newNoteCategory}
                                onChange={(e) => setNewNoteCategory(e.target.value as any)}
                                className="text-xs px-2 py-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-400 dark:text-gray-200"
                              >
                                <option value="general">📋 Nota Geral</option>
                                <option value="interview">🎤 Nota de Entrevista</option>
                                <option value="screening">📞 Nota de Triagem</option>
                                <option value="feedback">💬 Feedback Interno</option>
                                <option value="technical">💻 Avaliação Técnica</option>
                              </select>
                            </div>
                            <textarea 
                              value={newNoteContent}
                              onChange={(e) => setNewNoteContent(e.target.value)}
                              placeholder="Adicione uma nota sobre este candidato..."
                              className="w-full text-sm px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-md resize-none focus:outline-none focus:ring-1 focus:ring-amber-400 bg-white dark:bg-gray-800 dark:text-gray-200"
                              rows={2}
                            />
                          </div>
                          <Button 
                            size="sm" 
                            className="gap-1.5 mt-6 bg-status-warning hover:bg-status-warning/10 text-white"
                            disabled={!newNoteContent.trim()}
                            onClick={() => {
                              if (newNoteContent.trim()) {
                                // Add note to local activities (will persist when backend API is available)
                                const newNote = {
                                  id: `note-${Date.now()}`,
                                  type: 'note',
                                  category: newNoteCategory,
                                  content: newNoteContent.trim(),
                                  created_at: new Date().toISOString(),
                                  author: 'Recrutador'
                                }
                                setActivities(prev => [newNote, ...prev])
                                toast({
                                  title: "Nota adicionada",
                                  description: "A nota foi registrada no histórico do candidato"
                                })
                                setNewNoteContent('')
                                setNewNoteCategory('general')
                              }
                            }}
                          >
                            <Plus className="w-3.5 h-3.5" />
                            Salvar
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* Feed de Atividades */}
                    <div className="flex-1 p-4">
                      {isLoadingActivities ? (
                        <div className="flex items-center justify-center py-12">
                          <Loader2 className="w-6 h-6 animate-spin text-gray-600 dark:text-gray-400" />
                        </div>
                      ) : (() => {
                        const getCategoryLabel = (cat: string) => {
                          const labels: Record<string, string> = {
                            'general': 'Geral',
                            'interview': 'Entrevista',
                            'screening': 'Triagem',
                            'feedback': 'Feedback',
                            'technical': 'Técnica'
                          }
                          return labels[cat] || 'Geral'
                        }
                        
                        const parseNotes = () => {
                          if (!candidate?.notes) return []
                          if (typeof candidate.notes === 'string') {
                            return [{
                              id: 'note-legacy',
                              type: 'note',
                              category: 'general',
                              content: candidate.notes,
                              created_at: candidate.updated_at || new Date().toISOString()
                            }]
                          }
                          if (Array.isArray(candidate.notes)) {
                            return candidate.notes.map((note: any, idx: number) => ({
                              id: note.id || `note-${idx}`,
                              type: 'note',
                              category: note.category || 'general',
                              content: note.content || note.text || note,
                              created_at: note.created_at || note.date || candidate.updated_at
                            }))
                          }
                          return []
                        }
                        
                        const candidateNotes = parseNotes()
                        
                        const allItems = [
                          ...activities.map(a => ({ ...a, itemType: a.activity_type || a.type || 'activity' })),
                          ...candidateNotes.map(n => ({ ...n, itemType: 'note' }))
                        ].sort((a, b) => {
                          const dateA = new Date(a.created_at || a.timestamp || 0).getTime()
                          const dateB = new Date(b.created_at || b.timestamp || 0).getTime()
                          return dateB - dateA
                        })
                        
                        const filteredItems = allItems.filter(item => {
                          if (activityFilter === 'all') return true
                          if (activityFilter === 'notes') return item.itemType === 'note'
                          if (activityFilter === 'emails') return item.itemType === 'email' || item.type === 'email'
                          if (activityFilter === 'interviews') return item.itemType === 'interview' || item.type === 'interview'
                          if (activityFilter === 'lia') return item.itemType === 'lia' || item.type === 'lia' || item.source === 'lia'
                          if (activityFilter === 'tests') return item.itemType === 'test' || item.type === 'test'
                          if (activityFilter === 'offers') return item.itemType === 'offer' || item.type === 'offer'
                          if (activityFilter === 'applications') return item.itemType === 'application' || item.type === 'application'
                          return true
                        })
                        
                        if (filteredItems.length === 0) {
                          return (
                            <div className="flex flex-col items-center justify-center py-12 px-4">
                              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                                {activityFilter === 'notes' ? (
                                  <FileText className="w-8 h-8 text-status-warning" />
                                ) : (
                                  <Activity className="w-8 h-8 text-gray-600" />
                                )}
                              </div>
                              <h3 className="text-sm font-medium text-gray-800 mb-2">
                                {activityFilter === 'notes' 
                                  ? 'Nenhuma nota registrada ainda'
                                  : 'Nenhuma atividade registrada ainda'}
                              </h3>
                              <p className="text-xs text-gray-600 text-center max-w-xs">
                                {activityFilter === 'notes'
                                  ? 'Use o formulário acima para adicionar notas sobre este candidato'
                                  : 'As atividades aparecerão aqui conforme o processo avança'}
                              </p>
                            </div>
                          )
                        }
                        
                        return (
                          <div className="space-y-3">
                            {filteredItems.map((item: any, index: number) => {
                              if (item.itemType === 'note') {
                                return (
                                  <div key={item.id || index} className="flex items-start gap-3 p-3 bg-status-warning/10/50 rounded-md border border-status-warning/30 hover:transition-all">
                                    <div className="w-8 h-8 rounded-full bg-status-warning/15 flex items-center justify-center flex-shrink-0">
                                      <FileText className="w-4 h-4 text-status-warning" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                                        <span className="text-xs font-medium text-gray-800">Nota Interna</span>
                                        <Badge className="text-micro px-1.5 py-0 bg-status-warning/15 text-status-warning border-status-warning/30">
                                          {getCategoryLabel(item.category)}
                                        </Badge>
                                        <span className="text-xs text-gray-400">
                                          {formatRelativeTime(item.created_at)}
                                        </span>
                                      </div>
                                      <p className="text-sm text-gray-600">{item.content}</p>
                                      {item.user_name && (
                                        <p className="text-xs text-gray-500 mt-1">Por: {item.user_name}</p>
                                      )}
                                    </div>
                                  </div>
                                )
                              }
                              
                              return (
                                <div key={item.id || index} className="flex gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700 hover:transition-all">
                                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                                    <Activity className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center justify-between mb-1">
                                      <span className="text-sm font-medium text-gray-800">
                                        {item.activity_type || item.type || item.title || 'Atividade'}
                                      </span>
                                      <span className="text-xs text-gray-500">
                                        {formatRelativeTime(item.created_at || item.timestamp)}
                                      </span>
                                    </div>
                                    {(item.description || item.content || item.details) && (
                                      <p className="text-sm text-gray-600">
                                        {item.description || item.content || item.details}
                                      </p>
                                    )}
                                    {item.user_name && (
                                      <p className="text-xs text-gray-500 mt-1">Por: {item.user_name}</p>
                                    )}
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        )
                      })()}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* TAB: FILES */}
            <TabsContent value="files" className="mt-4">
              <Card className="border-gray-100">
                <CardContent className="p-0">
                  <div className="flex flex-col">
                    {/* Header com botão de adicionar */}
                    <div className="p-4 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-medium text-gray-800 dark:text-gray-200 flex items-center gap-2">
                          <FileText className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                          Arquivos e Documentos
                          <Badge className="text-xs px-1.5 py-0">{candidateFiles.length}</Badge>
                          {isLoadingFiles && (
                            <div className="animate-spin rounded-full h-3.5 w-3.5 border border-gray-400 border-t-gray-700"></div>
                          )}
                        </h4>
                        <Button
                          size="sm"
                          className="gap-1.5 px-3 py-1.5 text-xs h-8 bg-gray-100 hover:bg-gray-200 text-gray-800 dark:text-gray-200 border border-gray-200"
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
                          <Plus className="w-3.5 h-3.5" />
                          {isUploading ? 'Enviando...' : 'Adicionar Arquivo'}
                        </Button>
                      </div>

                      {/* Categorias */}
                      <div className="flex gap-1.5 flex-wrap">
                        <Badge 
                          variant="outline" 
                          className={`text-xs px-2 py-0.5 cursor-pointer hover:bg-gray-100 ${!selectedCategory ? 'bg-gray-100' : ''}`}
                          onClick={() => setSelectedCategory(null)}
                        >
                          📁 Todos ({candidateFiles.length})
                        </Badge>
                        {fileCategories.filter((c: any) => c.count > 0).map((cat: any) => (
                          <Badge 
                            key={cat.category}
                            variant="outline" 
                            className={`text-xs px-2 py-0.5 cursor-pointer hover:bg-gray-100 ${selectedCategory === cat.category ? 'bg-gray-100' : ''}`}
                            onClick={() => setSelectedCategory(selectedCategory === cat.category ? null : cat.category)}
                          >
                            {cat.icon} {cat.label} ({cat.count})
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Lista de Arquivos */}
                    <div className="flex-1 p-4 space-y-3">
                      {/* Drag and Drop Area */}
                      <div
                        className={`border-2 border-dashed rounded-md p-6 text-center transition-all cursor-pointer group ${
                          isDragging ? 'border-gray-400 bg-gray-100' : 'border-gray-300 hover:border-gray-400'
                        }`}
                        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
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
                              <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center mb-3">
                                <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-400 border-t-gray-700"></div>
                              </div>
                              <p className="text-sm text-gray-800 dark:text-gray-200 font-medium mb-2">Enviando... {uploadProgress}%</p>
                              <div className="w-40 h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div className="h-full bg-gray-600 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                              </div>
                            </>
                          ) : (
                            <>
                              <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-3 transition-colors ${isDragging ? 'bg-gray-200' : 'bg-gray-100 group-hover:bg-gray-200'}`}>
                                <Upload className={`w-6 h-6 ${isDragging ? 'text-gray-800 dark:text-gray-200' : 'text-gray-600 group-hover:text-gray-700'}`} />
                              </div>
                              <p className="text-sm text-gray-800 dark:text-gray-200 mb-1">
                                {isDragging ? 'Solte os arquivos aqui' : 'Arraste arquivos ou clique para selecionar'}
                              </p>
                              <p className="text-xs text-gray-500">PDF, DOC, DOCX, JPG, PNG, MP4 • Máx 10MB</p>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Lista de arquivos da API */}
                      {candidateFiles
                        .filter((file: any) => !selectedCategory || file.file_type === selectedCategory)
                        .map((file: any) => {
                          const colors = getCategoryColor(file.file_type)
                          return (
                            <div key={file.id} className="border border-gray-100 dark:border-gray-700 rounded-md hover:transition-all">
                              <div className="p-3">
                                <div className="flex items-start gap-3">
                                  <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                                    {getFileIcon(file.file_type, file.mime_type)}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <h5 className="text-sm font-medium text-gray-800 truncate">{file.file_name}</h5>
                                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                                          <span className="text-xs text-gray-500">
                                            {formatFileSize(file.file_size)} • {file.file_name.split('.').pop()?.toUpperCase()}
                                          </span>
                                          <span className="text-xs text-gray-500">{formatRelativeTime(file.created_at)}</span>
                                          <Badge className="text-xs px-1.5 py-0 h-4" style={{ backgroundColor: colors.bg, color: colors.text }}>
                                            <Tag className="w-2.5 h-2.5 mr-0.5" />
                                            {getCategoryLabel(file.file_type)}
                                          </Badge>
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-1.5">
                                        <Button size="sm" variant="ghost" className="p-1.5 h-7 w-7" onClick={() => handleDownloadFile(file.file_url, file.file_name)} title="Baixar arquivo">
                                          <Download className="w-3.5 h-3.5" />
                                        </Button>
                                        <Button size="sm" variant="ghost" className="p-1.5 h-7 w-7 text-status-error hover:text-status-error hover:bg-status-error/10" onClick={() => handleDeleteFile(file.id)} title="Excluir arquivo">
                                          <X className="w-3.5 h-3.5" />
                                        </Button>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )
                        })}

                      {/* Empty state */}
                      {candidateFiles.length === 0 && !isLoadingFiles && (
                        <div className="text-center py-8 text-gray-500">
                          <FileText className="w-10 h-10 mx-auto mb-3 text-gray-300" />
                          <p className="text-sm">Nenhum arquivo enviado</p>
                          <p className="text-xs text-gray-400 mt-1">Arraste arquivos ou clique acima para enviar</p>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* TAB: OPINIONS & ANALYSES */}
            <TabsContent value="opinions" className="mt-4">
              <Card className="border-gray-100">
                <CardContent className="p-4 space-y-4">
                  {/* SubTabs */}
                  <div className="flex items-center gap-4 border-b border-gray-100 pb-3">
                    <button
                      onClick={() => setOpinionsSubTab('pareceres')}
                      className={`flex items-center gap-2 pb-2 text-sm font-medium transition-colors ${
                        opinionsSubTab === 'pareceres' 
                          ? 'text-gray-600 dark:text-gray-400 border-b-2 border-gray-900 dark:border-gray-50' 
                          : 'text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      <Brain className="w-4 h-4 text-wedo-cyan" />
                      Pareceres da LIA
                      {opinionsHistory.length > 0 && (
                        <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-900" style={{ color: 'white' }}>
                          {opinionsHistory.length}
                        </Badge>
                      )}
                    </button>
                    <button
                      onClick={() => setOpinionsSubTab('analises')}
                      className={`flex items-center gap-2 pb-2 text-sm font-medium transition-colors ${
                        opinionsSubTab === 'analises' 
                          ? 'text-wedo-purple border-b-2 border-wedo-purple/30' 
                          : 'text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      <Brain className="w-4 h-4 text-wedo-cyan" />
                      Análises
                      {(savedAnalyses?.total_analyses || 0) > 0 && (
                        <Badge className="text-micro px-1.5 py-0 h-4 bg-wedo-purple text-white">
                          {savedAnalyses?.total_analyses || 0}
                        </Badge>
                      )}
                    </button>
                  </div>
                  
                  {/* PARECERES SUBTAB */}
                  {opinionsSubTab === 'pareceres' && (
                    <>
                  {/* Loading State */}
                  {isLoadingOpinions && (
                    <div className="space-y-3">
                      {[1, 2].map((i) => (
                        <div key={i} className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md p-4 animate-pulse">
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
                  {!isLoadingOpinions && opinionsHistory.length === 0 && (
                    <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md p-8 text-center">
                      <div className="w-14 h-14 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-4">
                        <FileText className="w-7 h-7 text-gray-400" />
                      </div>
                      <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">Nenhum parecer disponível</p>
                      <p className="text-xs text-gray-500">
                        Os pareceres serão gerados automaticamente após triagens ou análises da LIA.
                      </p>
                    </div>
                  )}
                  
                  {/* Opinions List */}
                  {!isLoadingOpinions && opinionsHistory.length > 0 && (
                    <div className="space-y-3">
                      {opinionsHistory.map((opinion: any) => {
                        const isExpanded = expandedOpinionId === opinion.id
                        const isWsi = opinion.opinion_type === 'wsi'
                        const displayScore = isWsi ? opinion.wsi_score : opinion.score
                        
                        const getScoreColor = (score: number | null) => {
                          if (score === null || score === undefined) return 'text-gray-600'
                          if (score >= 80) return 'text-status-success'
                          if (score >= 60) return 'text-status-warning'
                          return 'text-status-error'
                        }
                        
                        const getRecommendationBadge = (rec: string | null) => {
                          if (!rec) return null
                          if (rec === 'approved') return <Badge className="bg-status-success/15 text-status-success text-xs flex items-center gap-0.5"><CheckCircle className="w-2.5 h-2.5" />APROVADO</Badge>
                          if (rec === 'pending_review') return <Badge className="bg-status-warning/15 text-status-warning text-xs flex items-center gap-0.5"><Clock className="w-2.5 h-2.5" />PENDENTE</Badge>
                          if (rec === 'not_approved') return <Badge className="bg-status-error/15 text-status-error text-xs flex items-center gap-0.5"><X className="w-2.5 h-2.5" />NÃO APROVADO</Badge>
                          return null
                        }
                        
                        return (
                          <div key={opinion.id} className="relative">
                            {!opinion.is_current && (
                              <Badge className="absolute top-2 right-2 text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-500 z-10">
                                v{opinion.version} - Histórico
                              </Badge>
                            )}
                            <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md overflow-hidden">
                              <button
                                onClick={() => setExpandedOpinionId(isExpanded ? null : opinion.id)}
                                className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                              >
                                <div className="flex items-center gap-3">
                                  <div className={`w-9 h-9 rounded-full flex items-center justify-center ${isWsi ? 'bg-wedo-purple/15' : 'bg-gray-100 dark:bg-gray-800'}`}>
                                    {isWsi ? <Target className="w-4 h-4 text-wedo-purple" /> : <Brain className="w-4 h-4 text-wedo-cyan" />}
                                  </div>
                                  <div className="text-left">
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <span className="text-sm font-medium text-gray-800">{isWsi ? 'Parecer WSI' : 'Parecer Geral'}</span>
                                      {opinion.job_vacancy_id && opinion.job_vacancy_title ? (
                                        <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-50 border-gray-300 dark:border-gray-600 flex items-center gap-1">
                                          <Briefcase className="w-2.5 h-2.5" />
                                          #{String(opinion.job_vacancy_id).slice(0, 6)} - {opinion.job_vacancy_title}
                                        </Badge>
                                      ) : opinion.job_vacancy_title ? (
                                        <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-50 border-gray-300 dark:border-gray-600 flex items-center gap-1">
                                          <Briefcase className="w-2.5 h-2.5" />
                                          {opinion.job_vacancy_title}
                                        </Badge>
                                      ) : null}
                                    </div>
                                    <div className="flex items-center gap-2 mt-0.5">
                                      {displayScore !== null && displayScore !== undefined && (
                                        <span className={`text-xs font-semibold ${getScoreColor(displayScore)}`}>
                                          {isWsi ? `WSI: ${displayScore.toFixed(1)}/5` : `Score: ${Math.round(displayScore)}/100`}
                                        </span>
                                      )}
                                      {opinion.archetype && <><span className="text-gray-300">•</span><span className="text-xs text-gray-500">{opinion.archetype}</span></>}
                                      {getRecommendationBadge(opinion.recommendation)}
                                    </div>
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          const parecerText = [
                                            opinion.summary,
                                            opinion.strengths?.length ? `Pontos Fortes:\n${opinion.strengths.join('\n')}` : '',
                                            opinion.gaps?.length ? `Gaps:\n${opinion.gaps.join('\n')}` : '',
                                            opinion.next_steps ? `Próximos Passos: ${opinion.next_steps}` : ''
                                          ].filter(Boolean).join('\n\n')
                                          copyToClipboard(parecerText, 'Parecer')
                                        }}
                                        className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
                                      >
                                        <Copy className="w-4 h-4 text-gray-400" />
                                      </button>
                                    </TooltipTrigger>
                                    <TooltipContent>Copiar Parecer</TooltipContent>
                                  </Tooltip>
                                  {opinion.created_at && <span className="text-micro text-gray-400">{formatDate(opinion.created_at)}</span>}
                                  {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                                </div>
                              </button>
                              
                              {isExpanded && (
                                <div className="px-4 pb-4 pt-0 border-t border-gray-100 space-y-4">
                                  {opinion.summary && (
                                    <div className="pt-4">
                                      <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">{opinion.summary}</p>
                                    </div>
                                  )}
                                  
                                  {opinion.score_breakdown && Object.keys(opinion.score_breakdown).length > 0 && (
                                    <div>
                                      <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                        <BarChart3 className="w-3.5 h-3.5" />
                                        Score Breakdown
                                      </h5>
                                      <div className="grid grid-cols-2 gap-2">
                                        {Object.entries(opinion.score_breakdown).map(([key, value]: [string, any]) => (
                                          value !== null && value !== undefined && (
                                            <div key={key} className="flex items-center justify-between text-xs bg-gray-50 dark:bg-gray-700 rounded-md px-3 py-2">
                                              <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}</span>
                                              <span className="font-medium text-gray-800">{typeof value === 'number' ? `${Math.round(value)}%` : value}</span>
                                            </div>
                                          )
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  
                                  {opinion.strengths && opinion.strengths.length > 0 && (
                                    <div>
                                      <h5 className="text-xs font-medium text-status-success mb-2 flex items-center gap-1">
                                        <CheckCircle className="w-3.5 h-3.5" />
                                        Pontos Fortes
                                      </h5>
                                      <ul className="space-y-1">
                                        {opinion.strengths.map((s: string, i: number) => (
                                          <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                                            <span className="text-status-success mt-0.5">•</span>{s}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {opinion.gaps && opinion.gaps.length > 0 && (
                                    <div>
                                      <h5 className="text-xs font-medium text-status-error mb-2 flex items-center gap-1">
                                        <AlertCircle className="w-3.5 h-3.5" />
                                        Gaps Identificados
                                      </h5>
                                      <ul className="space-y-1">
                                        {opinion.gaps.map((g: string, i: number) => (
                                          <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                                            <span className="text-status-error mt-0.5">•</span>{g}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {opinion.next_steps && (
                                    <div>
                                      <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                        <TrendingUp className="w-3.5 h-3.5" />
                                        Próximos Passos
                                      </h5>
                                      <p className="text-xs text-gray-600">{opinion.next_steps}</p>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                    </>
                  )}

                  {/* ANALYSES SUBTAB */}
                  {opinionsSubTab === 'analises' && (
                    <>
                      {/* Loading State */}
                      {isLoadingAnalyses && (
                        <div className="space-y-3">
                          {[1, 2].map((i) => (
                            <div key={i} className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md p-4 animate-pulse">
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
                      {!isLoadingAnalyses && (!savedAnalyses?.analyses || savedAnalyses.analyses.length === 0) && (
                        <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md p-8 text-center">
                          <div className="w-14 h-14 rounded-full bg-wedo-purple/10 flex items-center justify-center mx-auto mb-4">
                            <Brain className="w-7 h-7 text-wedo-purple" />
                          </div>
                          <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">Nenhuma análise salva</p>
                          <p className="text-xs text-gray-500">
                            Use o ícone 🧠 no perfil do candidato para gerar análises.
                          </p>
                        </div>
                      )}

                      {/* Analyses List */}
                      {!isLoadingAnalyses && savedAnalyses?.analyses?.length > 0 && (
                        <div className="space-y-3">
                          {savedAnalyses.analyses.map((analysis: any) => {
                            const isExpanded = expandedAnalysisId === analysis.id
                            const analysisLabels: Record<string, string> = {
                              'bullet_points': 'Pontos-chave',
                              'short_paragraph': 'Resumo',
                              'detailed_bullets': 'Análise Detalhada'
                            }
                            
                            return (
                              <div key={analysis.id} className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md overflow-hidden">
                                <button
                                  onClick={() => setExpandedAnalysisId(isExpanded ? null : analysis.id)}
                                  className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                                >
                                  <div className="flex items-center gap-3">
                                    <div className="w-9 h-9 rounded-full bg-wedo-purple/15 flex items-center justify-center">
                                      <Brain className="w-4 h-4 text-wedo-purple" />
                                    </div>
                                    <div className="text-left">
                                      <div className="flex items-center gap-2">
                                        <span className="text-sm font-medium text-gray-800">
                                          {analysisLabels[analysis.analysis_type] || analysis.analysis_type}
                                        </span>
                                        <Badge className="text-micro px-1.5 py-0 h-4 bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                                          Análise LIA
                                        </Badge>
                                      </div>
                                      <span className="text-micro text-gray-400 mt-0.5">
                                        {analysis.created_at ? new Date(analysis.created_at).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Data não disponível'}
                                      </span>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation()
                                            copyToClipboard(analysis.content, 'Análise')
                                          }}
                                          className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
                                        >
                                          <Copy className="w-4 h-4 text-gray-400" />
                                        </button>
                                      </TooltipTrigger>
                                      <TooltipContent>Copiar Análise</TooltipContent>
                                    </Tooltip>
                                    {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                                  </div>
                                </button>
                                
                                {isExpanded && (
                                  <div className="px-4 pb-4 border-t border-gray-100 pt-4">
                                    <div className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">
                                      {cleanMarkdown(analysis.content)}
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
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* MODALS */}
        {candidate && (
          <>
            <UnifiedCommunicationModal
              isOpen={showCommunicationModal}
              onClose={() => setShowCommunicationModal(false)}
              candidate={{
                id: candidate.id,
                name: candidate.name,
                role: candidate.current_title || '',
                email: candidate.email || '',
                phone: candidate.phone || candidate.mobile_phone || '',
                location: candidate.location_city,
                avatar: candidate.avatar_url
              }}
              type={communicationType}
              companyId="demo_company"
            />
            
            <AddToListModal
              isOpen={showAddToListModal}
              onClose={() => setShowAddToListModal(false)}
              candidateIds={[candidate.id]}
              candidateNames={[candidate.name]}
            />
            
            <AddCandidatesToVacancyModal
              isOpen={showAddToVacancyModal}
              onClose={() => setShowAddToVacancyModal(false)}
              candidateIds={[candidate.id]}
              candidateNames={[candidate.name]}
            />
            
          </>
        )}
      </div>
    </TooltipProvider>
  )
}
