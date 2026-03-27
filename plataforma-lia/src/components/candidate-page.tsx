"use client"

import { useState, useEffect } from "react"
import { textStyles as designTextStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { integrationsService } from "@/services/integrations-service"
import { toast } from "sonner"
import { LiaAnalysisModal } from "@/components/modals/lia-analysis-modal"
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
  const [activeTab, setActiveTab] = useState<'profile' | 'activities' | 'files' | 'opinions'>('profile')
  const [showLiaModal, setShowLiaModal] = useState(false)
  const [liaCommand, setLiaCommand] = useState('')
  const [showVideoModal, setShowVideoModal] = useState<any>(null)
  const [viewMode, setViewMode] = useState<'timeline' | 'list'>('timeline')
  const [expandedLiaPredictions, setExpandedLiaPredictions] = useState(false)
  const [periodFilter, setPeriodFilter] = useState('all')
  const [activityFilter, setActivityFilter] = useState('all')
  const [expandedActivity, setExpandedActivity] = useState<string | null>(null)
  const [showAIPredictions, setShowAIPredictions] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<any>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [previewType, setPreviewType] = useState<'pdf' | 'image' | 'video' | 'audio' | null>(null)
  const [videoPlaying, setVideoPlaying] = useState(false)
  const [pdfPage, setPdfPage] = useState(1)
  const [pdfTotalPages, setPdfTotalPages] = useState(5)
  const [imageZoom, setImageZoom] = useState(100)
  
  const [opinionsSubTab, setOpinionsSubTab] = useState<'pareceres' | 'analises'>('pareceres')
  const [opinionsHistory, setOpinionsHistory] = useState<any[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [expandedOpinionId, setExpandedOpinionId] = useState<string | null>(null)
  const [savedAnalyses, setSavedAnalyses] = useState<any>(null)
  const [isLoadingAnalyses, setIsLoadingAnalyses] = useState(false)
  const [expandedAnalysisId, setExpandedAnalysisId] = useState<string | null>(null)
  const [copiedItemId, setCopiedItemId] = useState<string | null>(null)
  const [analysisToDelete, setAnalysisToDelete] = useState<any>(null)
  const [showLiaAnalysisModal, setShowLiaAnalysisModal] = useState(false)

  // Mock completo de atividades do candidato (mesmo do preview)
  const activities = [
    {
      id: 'lia-eval-1',
      type: 'lia-evaluation',
      icon: Brain,
      iconColor: '#374151', // Ciano WeDo - automação LIA
      title: 'Avaliação da LIA - UX Designer Sênior',
      author: 'LIA AI',
      authorRole: 'Sistema',
      date: 'Hoje às 14:30',
      timestamp: new Date().toISOString(),
      jobId: 'UXD-2024-001',
      jobTitle: 'UX Designer Sênior',
      score: 95,
      status: 'approved',
      statusLabel: 'Aprovado',
      summary: 'Candidato altamente qualificado com excelente fit cultural e técnico.',
      details: {
        technicalScore: 92,
        culturalFit: 98,
        experience: 95,
        softSkills: 93,
        strengths: ['Design Systems', 'Liderança', 'Visão Estratégica'],
        improvements: ['Conhecimento em Motion Design', 'Analytics avançado'],
        recommendation: 'Altamente recomendado para próxima fase',
        notes: 'Perfil excepcional com experiência comprovada em grandes empresas tech.'
      }
    },
    {
      id: 'offer-sent-1',
      type: 'offer-sent',
      icon: FileText,
      iconColor: '#60D186', // Verde WeDo - sucesso/aprovação
      title: 'Carta Oferta Enviada',
      author: 'Ana Silva',
      authorRole: 'Recrutadora',
      date: 'Hoje às 10:00',
      timestamp: new Date().toISOString(),
      jobId: 'UXD-2024-001',
      jobTitle: 'UX Designer Sênior',
      status: 'sent',
      statusLabel: 'Enviada',
      summary: 'Oferta formal enviada com salário de R$ 20.000 CLT + benefícios.',
      details: {
        salary: 'R$ 20.000',
        contractType: 'CLT',
        benefits: ['Vale Refeição', 'Vale Alimentação', 'Plano de Saúde', 'Gympass'],
        startDate: '01/02/2025',
        expirationDate: '15/01/2025',
        approvedBy: 'Roberto Silva - VP Produto'
      }
    },
    {
      id: 'technical-test-1',
      type: 'technical-test',
      icon: Code,
      iconColor: '#9860D1', // Roxo WeDo - insights/avaliação
      title: 'Teste Técnico Realizado',
      author: 'Carlos Mendes',
      authorRole: 'Tech Lead',
      date: 'Ontem às 16:00',
      timestamp: new Date(Date.now() - 86400000).toISOString(),
      jobId: 'UXD-2024-001',
      jobTitle: 'UX Designer Sênior',
      status: 'completed',
      statusLabel: 'Concluído',
      score: 88,
      summary: 'Case de design system concluído com nota 88/100.',
      details: {
        testType: 'Design System Case',
        duration: '4 horas',
        score: 88,
        maxScore: 100,
        evaluator: 'Carlos Mendes',
        strengths: ['Componentização', 'Documentação', 'Tokens de design'],
        weaknesses: ['Performance em mobile'],
        recommendation: 'Aprovado para próxima fase'
      }
    },
    {
      id: 'whatsapp-screening',
      type: 'lia-screening',
      icon: Bot,
      iconColor: '#374151', // Ciano WeDo - automação LIA
      title: 'Triagem via WhatsApp - LIA',
      author: 'LIA Bot',
      authorRole: 'AI Assistant',
      date: 'Há 3 dias',
      timestamp: new Date(Date.now() - 259200000).toISOString(),
      platform: 'WhatsApp',
      status: 'completed',
      summary: 'Triagem inicial completa com 12 perguntas respondidas.',
      details: {
        conversation: [
          { sender: 'LIA', message: 'Olá! Sou a LIA, assistente de recrutamento. Você tem alguns minutos?', time: '14:00' },
          { sender: 'Candidato', message: 'Olá! Sim, claro. Estou disponível.', time: '14:02' },
          { sender: 'LIA', message: 'Ótimo! Primeiro, pode me contar sobre sua experiência atual?', time: '14:02' },
          { sender: 'Candidato', message: 'Trabalho como UX Designer Sênior há 2 anos.', time: '14:05' }
        ],
        keyPoints: {
          availability: 'Imediata após 30 dias',
          salary: 'R$ 18-22k CLT',
          english: 'Fluente',
          remote: 'Aceita híbrido ou remoto',
          motivation: 'Busca novos desafios e crescimento'
        }
      }
    },
    {
      id: 'video-interview-1',
      type: 'video-interview',
      icon: Video,
      iconColor: '#D160AB', // Magenta WeDo - urgência/destaque
      title: 'Vídeo de apresentação gravado',
      author: candidate.name,
      authorRole: 'Candidato',
      date: 'Há 6 dias',
      timestamp: new Date(Date.now() - 518400000).toISOString(),
      status: 'completed',
      duration: '3:45',
      summary: 'Vídeo de apresentação pessoal enviado pelo candidato.',
      details: {
        videoUrl: '/videos/candidate-presentation.mp4',
        thumbnail: '/thumbnails/presentation.jpg',
        questions: [
          'Apresentação pessoal',
          'Por que você quer trabalhar conosco?',
          'Principais conquistas profissionais'
        ],
        transcription: 'Olá, meu nome é Maria Oliveira e sou UX Designer há 8 anos...',
        aiAnalysis: {
          confidence: 92,
          communication: 95,
          enthusiasm: 88,
          clarity: 90
        }
      }
    },
    {
      id: 'hiring-manager-note',
      type: 'interview-note',
      icon: UserCircle,
      iconColor: '#D19960', // Laranja WeDo - tempo/processos
      title: 'Feedback do Hiring Manager',
      author: 'Roberto Silva',
      authorRole: 'VP de Produto',
      date: 'Há 2 dias',
      timestamp: new Date(Date.now() - 172800000).toISOString(),
      status: 'completed',
      summary: 'Forte candidato, alinhado com nossa cultura.',
      details: {
        culturalFit: 9,
        technicalSkills: 8,
        leadership: 9,
        communication: 10,
        overallImpression: 'Excelente candidato com potencial de crescimento',
        concerns: 'Nenhuma preocupação significativa',
        recommendation: 'Fazer oferta',
        suggestedLevel: 'Senior',
        suggestedSalary: 'R$ 20.000'
      }
    }
  ]

  // Previsões da IA para próximas etapas
  const aiPredictions = [
    {
      id: 'response-time',
      title: 'Resposta à Oferta',
      probability: 85,
      timeframe: '2-3 dias',
      recommendation: 'Follow-up recomendado em 48h',
      icon: '📧',
      color: '#A8D5B7' // Verde WeDo - sucesso/qualidade
    },
    {
      id: 'negotiation',
      title: 'Possível Negociação',
      probability: 30,
      timeframe: '3-5 dias',
      recommendation: 'Preparar margem de negociação de até 10%',
      icon: '💰',
      color: '#D5BFA8' // Laranja WeDo - custos/tempo
    },
    {
      id: 'acceptance',
      title: 'Aceitação da Oferta',
      probability: 75,
      timeframe: '5-7 dias',
      recommendation: 'Iniciar preparação do onboarding',
      icon: '✅',
      color: '#A8CED5' // Ciano WeDo - automação/progresso
    },
    {
      id: 'start-date',
      title: 'Confirmação de Início',
      probability: 90,
      timeframe: '30 dias',
      recommendation: 'Agendar primeira semana de integração',
      icon: '🎯',
      color: '#BFA8D5' // Roxo WeDo - insights premium
    }
  ]

  // Definir as tabs exatamente como no preview
  const tabs = [
    { id: 'profile', label: 'Perfil Completo', icon: UserCheck },
    { id: 'activities', label: 'Atividades', icon: Activity },
    { id: 'files', label: 'Arquivos', icon: FileText },
    { id: 'opinions', label: 'Pareceres', icon: Brain, badge: opinionsHistory.length + (savedAnalyses?.total_analyses || 0) }
  ]

  // Filtrar atividades
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

  const filteredActivities = activities.filter(activity => {
    const typeFilter = activityFilter === 'all' ||
      (activityFilter === 'emails' && activity.type.includes('email')) ||
      (activityFilter === 'interviews' && (activity.type.includes('interview') || activity.type === 'video-interview')) ||
      (activityFilter === 'lia' && (activity.type.includes('lia') || activity.type === 'assessment')) ||
      (activityFilter === 'tests' && activity.type.includes('test')) ||
      (activityFilter === 'offers' && (activity.type === 'offer-sent' || activity.type === 'onboarding'))

    return typeFilter && filterByPeriod(activity)
  })

  if (!isOpen || !candidate) return null

  const liaScore = candidate.liaAnalysis?.score || 92
  const fitScore = candidate.liaAnalysis?.fitScore || 95

  // Dynamic data extraction (same as full page)
  const experiences = (candidate as any).workHistory || (candidate as any).work_history || (candidate as any).experiences || ((candidate as any).additional_data as any)?.work_history || ((candidate as any).additional_data as any)?.experiences || []
  const education = (candidate as any).education || ((candidate as any).additional_data as any)?.education || []

  const formatDateShort = (dateStr: string | null | undefined) => {
    if (!dateStr) return ''
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', { 
        month: 'short', 
        year: 'numeric' 
      })
    } catch {
      return dateStr
    }
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

  const hasPersonalData = (c: any): boolean => {
    return !!(c.date_of_birth || c.gender || c.nationality || 
              c.marital_status || c.estimated_age)
  }

  const hasPearchData = (c: any): boolean => {
    return !!(c.headline || c.is_open_to_work || c.is_decision_maker || 
              c.is_top_universities || c.is_hiring || c.linkedin_followers_count || 
              c.linkedin_connections_count || c.pearch_profile_id)
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return "bg-wedo-green-pastel text-gray-950 dark:text-gray-50" // Verde WeDo - sucesso/qualidade
    if (score >= 80) return "bg-gray-100 text-gray-950 dark:text-gray-50" // Ciano WeDo - automação/progresso
    if (score >= 70) return "bg-gray-200 text-gray-950 dark:text-gray-50" // Laranja WeDo - tempo/custos
    return "bg-gray-100 text-gray-950 dark:text-gray-50" // Magenta WeDo - urgência/atenção
  }

  const textStyles = {
    title: 'text-sm font-semibold text-gray-950 dark:text-gray-50',
    subtitle: 'text-xs font-medium text-gray-800 dark:text-gray-200',
    body: 'text-xs text-gray-600 dark:text-gray-400',
    bodySmall: 'text-xs text-gray-600 dark:text-gray-400',
    caption: 'text-micro text-gray-500 dark:text-gray-500',
    label: 'text-micro font-medium text-gray-800 dark:text-gray-200 uppercase tracking-wider',
    description: 'text-micro text-gray-500 dark:text-gray-500'
  }

  const badgeStyles = {
    default: 'text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-0',
    success: 'text-micro px-1.5 py-0 h-4 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border-0',
    warning: 'text-micro px-1.5 py-0 h-4 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border-0',
    error: 'text-micro px-1.5 py-0 h-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-0',
    info: 'text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-0'
  }

  const cardStyles = {
    default: 'bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md'
  }

  const cleanTextForCopy = (text: string): string => {
    if (!text) return ''
    return text
      .replace(/^#+\s*/gm, '')
      .replace(/\*\*/g, '')
      .replace(/^\*\s+/gm, '• ')
      .replace(/^-\s+/gm, '• ')
      .trim()
  }

  const handleCopyOpinion = async (opinion: any, type: string) => {
    const analysisLabels: Record<string, string> = {
      'quick': 'Triagem Rápida',
      'general': 'Parecer Geral',
      'wsi': 'Parecer WSI'
    }
    const header = `PARECER LIA - ${candidate.name}\nTipo: ${analysisLabels[type] || type}\n${opinion.job_vacancy_title ? `Vaga: ${opinion.job_vacancy_title}\n` : ''}Score: ${opinion.score || opinion.wsi_score || 'N/A'}/100\nData: ${opinion.created_at ? new Date(opinion.created_at).toLocaleDateString('pt-BR') : 'N/A'}\n\n`
    const content = cleanTextForCopy(opinion.summary || opinion.content || '')
    await navigator.clipboard.writeText(header + content)
    setCopiedItemId(`opinion-${opinion.id}`)
    setTimeout(() => setCopiedItemId(null), 2000)
    toast.success('Parecer copiado!')
  }

  const handleCopyAnalysis = async (analysis: any) => {
    const analysisLabels: Record<string, string> = {
      'bullet_points': 'Pontos-chave',
      'short_paragraph': 'Resumo',
      'detailed_bullets': 'Análise Detalhada'
    }
    const header = `ANÁLISE LIA - ${candidate.name}\nTipo: ${analysisLabels[analysis.analysis_type] || analysis.analysis_type}\nData: ${analysis.created_at ? new Date(analysis.created_at).toLocaleDateString('pt-BR') : 'N/A'}\n\n`
    const content = cleanTextForCopy(analysis.content || '')
    await navigator.clipboard.writeText(header + content)
    setCopiedItemId(`analysis-${analysis.id}`)
    setTimeout(() => setCopiedItemId(null), 2000)
    toast.success('Análise copiada!')
  }

  const handleDeleteAnalysis = async () => {
    if (!analysisToDelete) return
    try {
      const response = await fetch(`/api/backend-proxy/lia/profile-analysis/${candidate.id}/${analysisToDelete.analysis_type}?company_id=demo_company`, {
        method: 'DELETE'
      })
      if (response.ok) {
        setSavedAnalyses((prev: any) => ({
          ...prev,
          analyses: prev.analyses.filter((a: any) => a.id !== analysisToDelete.id),
          total_analyses: prev.total_analyses - 1
        }))
        toast.success('Análise removida com sucesso')
      }
    } catch (error) {
      toast.error('Erro ao remover análise')
    }
    setAnalysisToDelete(null)
  }

  const handleAnalysisTransport = async () => {
    try {
      const response = await fetch(`/api/backend-proxy/lia/profile-analysis/candidate/${candidate.id}?company_id=demo_company`)
      if (response.ok) {
        const data = await response.json()
        setSavedAnalyses(data)
        toast.success('Análise adicionada à aba Pareceres')
        setOpinionsSubTab('analises')
      }
    } catch (error) {
      console.error('Error refreshing analyses:', error)
    }
  }

  useEffect(() => {
    const fetchOpinionsHistory = async () => {
      if (!candidate?.id) return
      setIsLoadingHistory(true)
      try {
        const response = await fetch(`/api/backend-proxy/opinions/history/${candidate.id}?company_id=demo_company`)
        if (response.ok) {
          const data = await response.json()
          setOpinionsHistory(data.opinions || [])
        }
      } catch (error) {
        console.error('Error fetching opinions:', error)
      } finally {
        setIsLoadingHistory(false)
      }
    }

    const fetchSavedAnalyses = async () => {
      if (!candidate?.id) return
      setIsLoadingAnalyses(true)
      try {
        const response = await fetch(`/api/backend-proxy/lia/profile-analysis/candidate/${candidate.id}?company_id=demo_company`)
        if (response.ok) {
          const data = await response.json()
          setSavedAnalyses(data)
        }
      } catch (error) {
        console.error('Error fetching analyses:', error)
      } finally {
        setIsLoadingAnalyses(false)
      }
    }

    fetchOpinionsHistory()
    fetchSavedAnalyses()
  }, [candidate?.id])

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
                        <Linkedin className="w-4 h-4" style={{ color: '#0A66C2' }} />
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
                        <Github className="w-4 h-4" style={{ color: '#181717' }} />
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
                <Badge className="text-micro px-1.5 py-0 h-4 ml-1" style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}>
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
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Coluna Esquerda - Informações Principais */}
              <div className="lg:col-span-2 space-y-4">
                {/* Skills Principais */}
                <Card>
                  <CardContent className="p-4">
                    <h4 className="text-sm font-medium text-gray-950 dark:text-gray-50 mb-3">Skills Principais</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {(candidate.skills || ['Figma', 'Sketch', 'Design Systems', 'Prototipagem', 'User Research', 'Wireframing', 'Adobe XD', 'Prototyping', 'UI Design', 'UX Strategy']).map((skill: string, index: number) => (
                        <Badge key={index} variant="outline" className="text-xs px-2 py-0.5">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Parecer LIA - Versão com info da vaga */}
                <Card className="border border-gray-200 dark:border-gray-700 overflow-hidden">
                  <div className="p-3">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-micro font-medium text-gray-800 dark:text-gray-200 uppercase tracking-wider">Parecer LIA</span>
                            <span className="text-micro font-semibold text-emerald-600">
                              Score: {opinionsHistory[0]?.score || liaScore}/100
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            {opinionsHistory[0]?.job_vacancy_id ? (
                              <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 flex items-center gap-1">
                                <Briefcase className="w-2.5 h-2.5" />
                                #{String(opinionsHistory[0].job_vacancy_id).slice(0, 6)} - {opinionsHistory[0].job_vacancy_title || 'Vaga vinculada'}
                              </Badge>
                            ) : (
                              <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                                Sem vaga vinculada
                              </Badge>
                            )}
                            {opinionsHistory[0]?.archetype && (
                              <span className="text-micro text-gray-500">{opinionsHistory[0].archetype}</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {opinionsHistory[0]?.recommendation === 'approved' && (
                          <Badge className="text-micro px-1.5 py-0 h-4 bg-green-50 text-green-700 flex items-center gap-0.5">
                            <CheckCircle className="w-2.5 h-2.5" />
                            APROVADO
                          </Badge>
                        )}
                        {opinionsHistory[0]?.recommendation === 'pending_review' && (
                          <Badge className="text-micro px-1.5 py-0 h-4 bg-amber-50 text-amber-700 flex items-center gap-0.5">
                            <Clock className="w-2.5 h-2.5" />
                            PENDENTE
                          </Badge>
                        )}
                      </div>
                    </div>
                    
                    {/* Summary - fonte reduzida */}
                    <p className="text-micro text-gray-800 dark:text-gray-200 leading-relaxed mb-2">
                      {opinionsHistory[0]?.summary || 'UX Designer sênior com 5+ anos de experiência em produtos digitais. Excelente liderança técnica e visão estratégica.'}
                    </p>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <h4 className="text-micro font-medium mb-1 flex items-center gap-1" style={{ color: '#2E8B57' }}>
                          <CheckCircle className="w-3 h-3" />
                          Pontos Fortes
                        </h4>
                        <ul className="space-y-0.5">
                          {(opinionsHistory[0]?.strengths || ['Ferramentas de design', 'Design systems', 'Liderança de equipes']).slice(0, 3).map((s: string, i: number) => (
                            <li key={i} className="text-micro text-gray-600 dark:text-gray-400 flex items-start gap-1">
                              <span className="text-emerald-500">•</span> {s}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h4 className="text-micro font-medium mb-1 flex items-center gap-1" style={{ color: '#FFA500' }}>
                          <AlertCircle className="w-3 h-3" />
                          A Desenvolver
                        </h4>
                        <ul className="space-y-0.5">
                          {(opinionsHistory[0]?.concerns || ['Acessibilidade avançada', 'Analytics de UX', 'Motion design']).slice(0, 3).map((c: string, i: number) => (
                            <li key={i} className="text-micro text-gray-600 dark:text-gray-400 flex items-start gap-1">
                              <span className="text-amber-500">•</span> {c}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Experiência Profissional - Dynamic */}
                <Card>
                  <CardHeader className="py-3 bg-gray-50 dark:bg-gray-800">
                    <div className="flex items-center gap-2">
                      <Briefcase className="w-4 h-4 text-gray-700 dark:text-gray-300" />
                      <CardTitle className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                        Experiência Profissional
                      </CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 space-y-4">
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
 <div key={index} className={`border-l-2 ${index === 0 ? 'border-gray-700' : 'border-gray-300 dark:border-gray-600'} pl-3`}>
                            <div className="flex items-start justify-between gap-2 mb-1">
                              <div>
                                <h5 className="text-sm font-medium text-gray-800 dark:text-gray-200">{title || 'Cargo não informado'}</h5>
                                <p className="text-xs text-gray-600 dark:text-gray-400">
                                  {company || 'Empresa não informada'}
                                  {location && ` • ${location}`}
                                  {exp.duration_years && <span className="text-gray-400 ml-1">({exp.duration_years.toFixed(1)} anos)</span>}
                                </p>
                              </div>
                              <span className="text-xs text-gray-500 dark:text-gray-500 whitespace-nowrap">
                                {formatDateShort(startDate)}{startDate && endDate ? ' - ' : ''}{endDate === 'Atual' ? 'Atual' : formatDateShort(endDate)}
                              </span>
                            </div>
                            
                            {/* Metadata Row */}
                            <div className="flex flex-wrap gap-1.5 mb-2">
                              {industries.slice(0, 2).map((ind: string, idx: number) => (
                                <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-600">
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
                            {technologies.length > 0 && (
                              <div className="flex flex-wrap gap-1 mb-2">
                                <span className="text-micro text-gray-400 flex items-center gap-0.5">
                                  <Code className="w-2.5 h-2.5" />
                                  Stack:
                                </span>
                                {technologies.slice(0, 6).map((tech: string, idx: number) => (
                                  <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200">
                                    {tech}
                                  </span>
                                ))}
                                {technologies.length > 6 && (
                                  <span className="text-micro text-gray-400">+{technologies.length - 6}</span>
                                )}
                              </div>
                            )}
                            
                            {description && (
                              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{description}</p>
                            )}
                          </div>
                        )
                      })
                    ) : (
                      <p className="text-sm text-gray-500 dark:text-gray-500 italic">Não informado</p>
                    )}
                  </CardContent>
                </Card>

                {/* Formação Acadêmica - Dynamic */}
                <Card>
                  <CardHeader className="py-3 bg-gray-50 dark:bg-gray-800">
                    <div className="flex items-center gap-2">
                      <GraduationCap className="w-4 h-4 text-purple-600" />
                      <CardTitle className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                        Formação Acadêmica
                      </CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 space-y-3">
                    {education.length > 0 ? (
                      education.map((edu: any, index: number) => (
                        <div key={index} className={`flex items-start justify-between gap-2 ${index < education.length - 1 ? 'pb-3 border-b border-gray-100' : ''}`}>
                          <div>
                            <h5 className="text-sm font-medium text-gray-800 dark:text-gray-200">
                              {edu.degree || edu.title || 'Formação'}
                              {(edu.field_of_study || edu.fieldOfStudy) && ` em ${edu.field_of_study || edu.fieldOfStudy}`}
                            </h5>
                            <p className="text-xs text-gray-600 dark:text-gray-400">{edu.school || edu.institution || 'Instituição não informada'}</p>
                          </div>
                          <span className="text-xs text-gray-500 dark:text-gray-500 whitespace-nowrap">
                            {edu.start_date || edu.startDate || ''}{(edu.start_date || edu.startDate) && (edu.end_date || edu.endDate) ? ' - ' : ''}{edu.end_date || edu.endDate || ''}
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500 dark:text-gray-500 italic">Não informado</p>
                    )}
                  </CardContent>
                </Card>

                {/* Certificações - Dynamic */}
                {candidate.certifications && candidate.certifications.length > 0 && (
                  <Card>
                    <CardHeader className="py-3 bg-gray-50 dark:bg-gray-800">
                      <div className="flex items-center gap-2">
                        <Award className="w-4 h-4 text-green-600" />
                        <CardTitle className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                          Certificações
                        </CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent className="p-4">
                      <div className="flex flex-wrap gap-1.5">
                        {candidate.certifications.map((cert: string, idx: number) => (
                          <Badge key={idx} variant="outline" className="text-xs px-2 py-0.5 bg-green-50 text-green-700 border-green-200">
                            {cert}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Coluna Direita - Informações Complementares */}
              <div className="space-y-4">
                {/* Remuneração e Benefícios - Card Combinado Detalhado */}
                <Card className="">
                  <CardHeader className="py-3 bg-wedo-green/10 dark:bg-wedo-green/20">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <DollarSign className="w-4 h-4 text-green-600" />
                        <CardTitle className="text-sm font-bold text-gray-950 dark:text-gray-50">
                          Pacote de Remuneração Total
                        </CardTitle>
                      </div>
                      <Badge className="text-xs px-2 py-0.5" style={{ backgroundColor: 'var(--status-success)', color: 'white' }}>
                        Total Compensation
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4">
                    <div className="space-y-3">
                      {/* Salário Base */}
                      <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-md">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs text-gray-600 dark:text-gray-400">Salário Mensal</span>
                          <span className="text-sm font-bold text-gray-950 dark:text-gray-50">
                            R$ 15.000,00
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-600 dark:text-gray-400">Anualizado (13,33x)</span>
                          <span className="text-sm font-semibold text-green-600">
                            R$ 199.950,00
                          </span>
                        </div>
                      </div>

                      {/* Remuneração Variável */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-600 dark:text-gray-400">Bônus Anual</span>
                          <span className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                            R$ 45.000,00
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-600 dark:text-gray-400">Stock Options</span>
                          <span className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                            R$ 25.000,00
                          </span>
                        </div>
                      </div>

                      {/* Benefícios */}
                      <div>
                        <p className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2">Benefícios Inclusos:</p>
                        <div className="flex flex-wrap gap-1">
                          <Badge className="bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 text-xs">VR R$1.500</Badge>
                          <Badge className="bg-green-50 text-green-700 text-xs">Saúde Premium</Badge>
                          <Badge className="bg-purple-50 text-purple-700 text-xs">Gympass</Badge>
                          <Badge className="bg-orange-50 text-orange-700 text-xs">Home Office</Badge>
                        </div>
                      </div>

                      {/* Total */}
                      <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-bold text-gray-950 dark:text-gray-50">
                            TOTAL ANUAL
                          </span>
                          <span className="text-lg font-bold text-green-600">
                            R$ 349.190,00
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Idiomas */}
                <Card>
                  <CardHeader className="py-3 bg-gray-50 dark:bg-gray-800">
                    <div className="flex items-center gap-2">
                      <Languages className="w-4 h-4 text-indigo-600" />
                      <CardTitle className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                        Idiomas
                      </CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                        Português
                      </span>
                      <Badge className="text-xs px-2 py-0.5" style={{ backgroundColor: '#B8E6D3', color: '#2E8B57' }}>
                        Nativo
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                        Inglês
                      </span>
                      <Badge className="text-xs px-2 py-0.5" style={{ backgroundColor: '#6B9BD1', color: 'white' }}>
                        Fluente
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                        Espanhol
                      </span>
                      <Badge className="text-xs px-2 py-0.5" style={{ backgroundColor: '#FFD700', color: '#856404' }}>
                        Intermediário
                      </Badge>
                    </div>
                  </CardContent>
                </Card>

                {/* Detalhes Adicionais - Dynamic */}
                <Card>
                  <CardHeader className="py-3 bg-gray-50 dark:bg-gray-800">
                    <div className="flex items-center gap-2">
                      <Home className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <CardTitle className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                        Detalhes Adicionais
                      </CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 space-y-3">
                    {/* Location */}
                    <div>
                      <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1">Localização</h5>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {[candidate.location_city, candidate.location_state, candidate.location_country]
                          .filter(Boolean).join(', ') || candidate.location || 'Não informado'}
                      </p>
                      {(candidate.address_street || candidate.address_district) && (
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-0.5">
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
                          <Badge variant="outline" className="text-xs bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-600">Remoto</Badge>
                        )}
                        {candidate.willing_to_relocate && (
                          <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">Aceita Relocação</Badge>
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
                      <div className="space-y-0.5 text-xs text-gray-600 dark:text-gray-400">
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
                        <Badge variant="outline" className={`text-xs ${candidate.is_active ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'}`}>
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
                          {candidate.tags.map((tag: string, idx: number) => (
                            <Badge key={idx} className="text-xs bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-600">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Dados Pessoais - Dynamic */}
                {hasPersonalData(candidate) && (
                  <Card>
                    <CardHeader className="py-3 bg-gray-50 dark:bg-gray-800">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        <CardTitle className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                          Dados Pessoais
                        </CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent className="p-4 space-y-2">
                      {((candidate as any).date_of_birth || (candidate as any).estimated_age) && (
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-gray-500 dark:text-gray-500 flex items-center gap-1">
                            <Cake className="w-3.5 h-3.5" />
                            Idade
                          </span>
                          <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
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
                          <span className="text-xs text-gray-500 dark:text-gray-500">Gênero</span>
                          <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{(candidate as any).gender}</span>
                        </div>
                      )}
                      {(candidate as any).nationality && (
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-gray-500 dark:text-gray-500">Nacionalidade</span>
                          <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{(candidate as any).nationality}</span>
                        </div>
                      )}
                      {(candidate as any).marital_status && (
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-gray-500 dark:text-gray-500">Estado Civil</span>
                          <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{(candidate as any).marital_status}</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* LinkedIn Insights - Dynamic */}
                {hasPearchData(candidate) && (
                  <Card className="border-l-4 border-l-[#0A66C2]">
                    <CardHeader className="py-3 bg-gray-50 dark:bg-gray-800">
                      <div className="flex items-center gap-2">
                        <Linkedin className="w-4 h-4 text-[#0A66C2]" />
                        <CardTitle className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                          LinkedIn Insights
                        </CardTitle>
                        {(candidate as any).pearch_profile_id && (
                          <Badge className="text-micro px-1.5 py-0 bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">Pearch</Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="p-4 space-y-3">
                      {(candidate as any).headline && (
                        <div>
                          <p className="text-sm text-gray-800 dark:text-gray-200 italic">"{(candidate as any).headline}"</p>
                        </div>
                      )}
                      
                      {/* Status Badges */}
                      <div className="flex flex-wrap gap-1.5">
                        {(candidate as any).is_open_to_work && (
                          <Badge className="text-xs bg-green-50 text-green-700 border-green-200">
                            ✓ Open to Work
                          </Badge>
                        )}
                        {(candidate as any).is_decision_maker && (
                          <Badge className="text-xs bg-purple-50 text-purple-700 border-purple-200">
                            👔 Decision Maker
                          </Badge>
                        )}
                        {(candidate as any).is_top_universities && (
                          <Badge className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                            🎓 Top Universities
                          </Badge>
                        )}
                        {(candidate as any).is_hiring && (
                          <Badge className="text-xs bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-600">
                            📢 Hiring
                          </Badge>
                        )}
                      </div>

                      {/* Connections & Followers */}
                      {((candidate as any).linkedin_connections_count || (candidate as any).linkedin_followers_count) && (
                        <div className="flex gap-4 pt-2 border-t border-gray-100">
                          {(candidate as any).linkedin_connections_count && (
                            <div className="text-center">
                              <p className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                                {(candidate as any).linkedin_connections_count.toLocaleString('pt-BR')}
                              </p>
                              <p className="text-micro text-gray-500 dark:text-gray-500">Conexões</p>
                            </div>
                          )}
                          {(candidate as any).linkedin_followers_count && (
                            <div className="text-center">
                              <p className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                                {(candidate as any).linkedin_followers_count.toLocaleString('pt-BR')}
                              </p>
                              <p className="text-micro text-gray-500 dark:text-gray-500">Seguidores</p>
                            </div>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          )}

          {activeTab === 'activities' && (
            <div className="space-y-4">
              {/* Header com filtros */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                      <Activity className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      Feed de Atividades
                      <Badge className="text-xs px-1.5 py-0">{filteredActivities.length}</Badge>
                    </h4>
                    <div className="flex items-center gap-2">
                      {/* Filtro de Período */}
                      <select
                        value={periodFilter}
                        onChange={(e) => setPeriodFilter(e.target.value)}
                        className="text-xs px-2 py-1 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded focus:outline-none focus:ring-1 focus:ring-gray-400/20"
                      >
                        <option value="7days">Últimos 7 dias</option>
                        <option value="30days">Últimos 30 dias</option>
                        <option value="3months">Últimos 3 meses</option>
                        <option value="all">Todo período</option>
                      </select>

                      {/* Toggle de Visualização */}
                      <div className="flex items-center bg-white dark:bg-gray-700 rounded-md p-0.5 border border-gray-200 dark:border-gray-600">
                        <button
                          onClick={() => setViewMode('timeline')}
                          className={`p-1.5 rounded transition-colors ${
                            viewMode === 'timeline'
                              ? 'bg-gray-200 dark:bg-gray-600 text-gray-900 dark:text-gray-100'
                              : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100'
                          }`}
                          title="Visualização Timeline"
                        >
                          <GitBranch className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setViewMode('list')}
                          className={`p-1.5 rounded transition-colors ${
                            viewMode === 'list'
                              ? 'bg-gray-200 dark:bg-gray-600 text-gray-900 dark:text-gray-100'
                              : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100'
                          }`}
                          title="Visualização Lista"
                        >
                          <List className="w-4 h-4" />
                        </button>
                      </div>

                      <Button
                        onClick={() => setShowLiaModal(true)}
                        size="sm"
                        className="gap-1 text-white px-3 py-1.5 text-xs h-7"
                        style={{ backgroundColor: '#E85A5A' }}
                      >
                        <PlusCircle className="w-3.5 h-3.5" />
                        Nova Atividade
                      </Button>
                    </div>
                  </div>

                  {/* Filtros de tipo */}
                  <div className="flex gap-1 flex-wrap">
                    <button
                      onClick={() => setActivityFilter('all')}
                      className={`px-2 py-1 text-xs rounded transition-colors ${
                        activityFilter === 'all'
                          ? 'bg-gray-600 text-white'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
                      }`}
                    >
                      Todas
                    </button>
                    <button
                      onClick={() => setActivityFilter('emails')}
                      className={`px-2 py-1 text-xs rounded transition-colors ${
                        activityFilter === 'emails'
                          ? 'bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      📧 Emails
                    </button>
                    <button
                      onClick={() => setActivityFilter('interviews')}
                      className={`px-2 py-1 text-xs rounded transition-colors ${
                        activityFilter === 'interviews'
                          ? 'bg-purple-600 text-white'
                          : 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 hover:bg-purple-200'
                      }`}
                    >
                      🎤 Entrevistas
                    </button>
                    <button
                      onClick={() => setActivityFilter('tests')}
                      className={`px-2 py-1 text-xs rounded transition-colors ${
                        activityFilter === 'tests'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 hover:bg-indigo-200'
                      }`}
                    >
                      📝 Testes
                    </button>
                    <button
                      onClick={() => setActivityFilter('lia')}
                      className={`px-2 py-1 text-xs rounded transition-colors ${
                        activityFilter === 'lia'
                          ? 'bg-red-600 text-white'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 hover:bg-red-200'
                      }`}
                    >
                      🤖 LIA
                    </button>
                    <button
                      onClick={() => setActivityFilter('offers')}
                      className={`px-2 py-1 text-xs rounded transition-colors ${
                        activityFilter === 'offers'
                          ? 'bg-green-600 text-white'
                          : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 hover:bg-green-200'
                      }`}
                    >
                      💼 Ofertas
                    </button>
                  </div>
                </CardContent>
              </Card>

              {/* Card de Previsões da IA */}
              <Card className="bg-gray-50 dark:bg-gray-800/50">
                <CardHeader
                  className="pb-3 cursor-pointer hover:bg-purple-100/30 dark:hover:bg-purple-900/30 transition-colors"
                  onClick={() => setShowAIPredictions(!showAIPredictions)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Brain className="w-4 h-4 text-wedo-cyan" />
                      <CardTitle className="text-sm">Previsão de Próximas Etapas - IA</CardTitle>
                      <Badge className="text-xs px-1.5 py-0.5" style={{ backgroundColor: '#8B5CF6', color: 'white' }}>
                        Análise Preditiva
                      </Badge>
                    </div>
                    <ChevronDown
                      className={`w-4 h-4 text-purple-600 transition-transform ${
                        showAIPredictions ? 'rotate-180' : ''
                      }`}
                    />
                  </div>
                </CardHeader>

                {showAIPredictions && (
                  <CardContent className="pt-0">
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                      {aiPredictions.map((prediction) => (
                        <div key={prediction.id} className="bg-white dark:bg-gray-800 rounded-md p-3">
                          <div className="flex items-start gap-2">
                            <span className="text-xl">{prediction.icon}</span>
                            <div className="flex-1">
                              <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                                {prediction.title}
                              </h5>
                              <Badge
                                className="text-xs px-1 py-0 h-4 mt-1"
                                style={{
                                  backgroundColor: `${prediction.color}20`,
                                  color: prediction.color
                                }}
                              >
                                {prediction.probability}%
                              </Badge>
                              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                {prediction.timeframe}
                              </p>
                              <p className="text-xs text-gray-600 dark:text-gray-400 italic mt-1">
                                💡 {prediction.recommendation}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                )}
              </Card>

              {/* Timeline/Lista de Atividades */}
              <Card>
                <CardContent className="p-4">
                  {viewMode === 'timeline' ? (
                    <div className="relative">
                      {/* Linha vertical da timeline */}
                      <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-wedo-green opacity-20"></div>

                      <div className="space-y-4">
                        {filteredActivities.map((activity) => (
                          <div key={activity.id} className="relative flex items-start">
                            {/* Ponto na timeline */}
                            <div
                              className="absolute left-5 w-3 h-3 rounded-full border-2 border-white dark:border-gray-800 z-10"
                              style={{
                                backgroundColor: activity.iconColor,
                                marginTop: '6px'
                              }}
                            ></div>

                            {/* Card da atividade */}
                            <div className="ml-12 flex-1">
                              <Card className="border border-gray-200 dark:border-gray-700">
                                <CardContent
                                  className="p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                                  onClick={() => setExpandedActivity(expandedActivity === activity.id ? null : activity.id)}
                                >
                                  <div className="flex items-start gap-3">
                                    <div
                                      className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                                      style={{ backgroundColor: `${activity.iconColor}20` }}
                                    >
                                      <activity.icon className="w-4 h-4" style={{ color: activity.iconColor }} />
                                    </div>

                                    <div className="flex-1">
                                      <div className="flex items-start justify-between">
                                        <div>
                                          <h5 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                                            {activity.title}
                                          </h5>
                                          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                            {activity.author} • {activity.date}
                                          </p>
                                          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                            {activity.summary}
                                          </p>
                                        </div>
                                        <div className="flex items-center gap-2">
                                          {activity.score && (
                                            <Badge
                                              className="text-xs"
                                              style={{
                                                backgroundColor: activity.score >= 80 ? '#B8E6D3' : '#FFE4B5',
                                                color: activity.score >= 80 ? '#2E8B57' : '#D2691E'
                                              }}
                                            >
                                              {activity.score}%
                                            </Badge>
                                          )}
                                          <ChevronDown
                                            className={`w-4 h-4 text-gray-600 dark:text-gray-400 transition-transform ${
                                              expandedActivity === activity.id ? 'rotate-180' : ''
                                            }`}
                                          />
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                </CardContent>

                                {/* Detalhes expandidos */}
                                {expandedActivity === activity.id && activity.details && (
                                  <CardContent className="pt-0 pb-3 border-t border-gray-100 dark:border-gray-800">
                                    {/* Renderizar detalhes baseado no tipo */}
                                    {activity.type === 'lia-evaluation' && (
                                      <div className="mt-2 space-y-2">
                                        <div className="grid grid-cols-2 gap-2">
                                          <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                            <span className="text-xs text-gray-800 dark:text-gray-200">Score Técnico</span>
                                            <p className="text-sm font-semibold">{activity.details.technicalScore}%</p>
                                          </div>
                                          <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                                            <span className="text-xs text-gray-800 dark:text-gray-200">Fit Cultural</span>
                                            <p className="text-sm font-semibold">{activity.details.culturalFit}%</p>
                                          </div>
                                        </div>
                                      </div>
                                    )}

                                    {activity.type === 'whatsapp-screening' && activity.details.conversation && (
                                      <div className="mt-2 space-y-2">
                                        <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded max-h-48 overflow-y-auto">
                                          <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">Conversa via {activity.platform}</p>
                                          <div className="space-y-2">
                                            {activity.details.conversation.map((msg: any, i: number) => (
                                              <div
                                                key={i}
                                                className={`flex ${msg.sender === 'LIA' ? 'justify-start' : 'justify-end'}`}
                                              >
                                                <div
                                                  className={`max-w-[70%] px-3 py-2 rounded-md text-xs ${
                                                    msg.sender === 'LIA'
                                                      ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-900 dark:text-purple-300'
                                                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                                                  }`}
                                                >
                                                  <p>{msg.message}</p>
                                                  <span className="text-xs opacity-70">{msg.time}</span>
                                                </div>
                                              </div>
                                            ))}
                                          </div>
                                        </div>
                                      </div>
                                    )}
                                  </CardContent>
                                )}
                              </Card>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {filteredActivities.map((activity) => (
                        <Card key={activity.id} className="border border-gray-200 dark:border-gray-700">
                          <CardContent className="p-3">
                            <div className="flex items-start gap-3">
                              <div
                                className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                                style={{ backgroundColor: `${activity.iconColor}20` }}
                              >
                                <activity.icon className="w-4 h-4" style={{ color: activity.iconColor }} />
                              </div>
                              <div className="flex-1">
                                <h5 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                                  {activity.title}
                                </h5>
                                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                  {activity.author} • {activity.date}
                                </p>
                                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                  {activity.summary}
                                </p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
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
                      console.log('Files dropped:', files)
                    }}
                    onClick={() => {
                      const input = document.createElement('input')
                      input.type = 'file'
                      input.multiple = true
                      input.accept = '.pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov,.mp3,.wav,.m4a,.webm,.ogg'
                      input.onchange = (e) => {
                        const files = Array.from((e.target as HTMLInputElement).files || [])
                        console.log('Files selected:', files)
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
                      <FileText className="w-5 h-5 text-red-600" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">CV_{candidate.name.replace(' ', '_')}_2025.pdf</h4>
                        <p className="text-xs text-gray-800 dark:text-gray-200">2.1 MB • há 3 dias</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-green-100 text-green-700 text-xs">✓ Verificado</Badge>
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
                      <FileText className="w-5 h-5 text-purple-600" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">Portfolio_UX_2025.pdf</h4>
                        <p className="text-xs text-gray-800 dark:text-gray-200">12.3 MB • há 1 dia</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-green-100 text-green-700 text-xs">✓ Verificado</Badge>
                          <Badge className="bg-purple-100 text-purple-700 text-xs">Destacado</Badge>
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
                      <Video className="w-5 h-5 text-red-600" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">Apresentacao_Pessoal.mp4</h4>
                        <p className="text-xs text-gray-800 dark:text-gray-200">25.4 MB • 3:45 min</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-green-100 text-green-700 text-xs">✓ Analisado</Badge>
                          <Badge className="bg-red-100 text-red-700 text-xs">Triagem</Badge>
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
                      <Video className="w-5 h-5 text-purple-600" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">Case_UX_Design.mp4</h4>
                        <p className="text-xs text-gray-800 dark:text-gray-200">45.2 MB • 8:20 min</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-purple-100 text-purple-700 text-xs">Destaque</Badge>
                          <Badge className="bg-green-100 text-green-700 text-xs">Score: 88%</Badge>
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
                          <Badge className="bg-green-100 text-green-700 text-xs">Score: 92%</Badge>
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
                      <Image className="w-5 h-5 text-green-600" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">foto_perfil.jpg</h4>
                        <p className="text-xs text-gray-800 dark:text-gray-200">456 KB • há 2 horas</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-green-100 text-green-700 text-xs">✓ Verificado</Badge>
                        </div>
                      </div>
                    </div>
                    {(candidate.avatar_url || candidate.avatar) && (
                      <div className="mt-3">
                        <img
                          src={candidate.avatar_url || candidate.avatar}
                          alt="Preview"
                          className="w-full h-24 rounded object-cover cursor-pointer hover:opacity-80 transition-opacity"
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
                      <Award className="w-5 h-5 text-orange-600" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">Certificados.zip</h4>
                        <p className="text-xs text-gray-800 dark:text-gray-200">3.2 MB • há 1 semana</p>
                        <div className="flex gap-1 mt-2">
                          <Badge className="bg-orange-100 text-orange-700 text-xs">5 arquivos</Badge>
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
                      <Badge className="text-micro px-1.5 py-0 h-4 ml-1" style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}>
                        {opinionsHistory.length}
                      </Badge>
                    )}
                  </button>
                  <button
                    onClick={() => setOpinionsSubTab('analises')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors ${
                      opinionsSubTab === 'analises'
                        ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 border-b-2 border-purple-500'
                        : 'text-gray-500 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                  >
                    <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                    Análises
                    {savedAnalyses && savedAnalyses.total_analyses > 0 && (
                      <Badge className="text-micro px-1.5 py-0 h-4 ml-1" style={{ backgroundColor: 'rgba(147, 51, 234, 0.15)', color: '#9333ea' }}>
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
                                  <div className="w-32 h-4 bg-gray-200 rounded mb-1"></div>
                                  <div className="w-24 h-3 bg-gray-200 rounded"></div>
                                </div>
                              </div>
                              <div className="space-y-2">
                                <div className="w-full h-3 bg-gray-200 rounded"></div>
                                <div className="w-3/4 h-3 bg-gray-200 rounded"></div>
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
                              if (score >= 4) return 'text-emerald-600'
                              if (score >= 3) return 'text-amber-600'
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
                          
                          return (
                            <Card key={opinion.id} className="overflow-hidden">
                              <div
                                onClick={() => setExpandedOpinionId(isExpanded ? null : opinion.id)}
                                className="p-3 flex items-center justify-between hover:bg-gray-50 transition-colors cursor-pointer"
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
                                        className="p-1 hover:bg-gray-100 rounded transition-colors"
                                      >
                                        {copiedItemId === `opinion-${opinion.id}` ? (
                                          <Check className="w-3.5 h-3.5 text-green-500" />
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
                                      <h5 className={`${textStyles.label} text-emerald-700 mb-1 flex items-center gap-1`}>
                                        <CheckCircle className="w-3 h-3" />
                                        Pontos Fortes
                                      </h5>
                                      <ul className="space-y-0.5">
                                        {opinion.strengths.map((s: string, i: number) => (
                                          <li key={i} className={`${textStyles.caption} text-gray-600 flex items-start gap-1`}>
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
                                          <li key={i} className={`${textStyles.caption} text-gray-600 flex items-start gap-1`}>
                                            <span className="text-amber-500 mt-0.5">•</span>
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
                                  <div className="w-32 h-4 bg-gray-200 rounded mb-1"></div>
                                  <div className="w-24 h-3 bg-gray-200 rounded"></div>
                                </div>
                              </div>
                              <div className="space-y-2">
                                <div className="w-full h-3 bg-gray-200 rounded"></div>
                                <div className="w-3/4 h-3 bg-gray-200 rounded"></div>
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
                          <div className="w-12 h-12 rounded-full bg-purple-50 flex items-center justify-center mx-auto mb-3">
                            <Brain className="w-6 h-6 text-purple-300" />
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
                                  <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                                    <Brain className="w-4 h-4 text-purple-600" />
                                  </div>
                                  <div className="min-w-0">
                                    <div className="flex items-center gap-2">
                                      <span className={`${textStyles.bodySmall} font-medium`}>Análise LIA</span>
                                      <Badge 
                                        className="text-micro px-1.5 py-0 h-4"
                                        style={{ backgroundColor: 'rgba(147, 51, 234, 0.15)', color: '#9333ea' }}
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
              className="bg-red-600 hover:bg-red-700 text-white"
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
                    console.log('Executando:', liaCommand)
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
