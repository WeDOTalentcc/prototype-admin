"use client"


import { CURRENCY_SYMBOL } from "@/lib/pricing"
import { useState, useEffect } from "react"
import { toast } from "sonner"
import { useCurrentCompany } from '@/hooks/company/use-current-company'
import {
  Brain, FileText, Code, Bot, Video, UserCircle,
  UserCheck, Activity
} from "lucide-react"

export function useCandidatePageCore(candidate: Record<string, unknown> | null) {
  const { companyId } = useCurrentCompany()
  const [activeTab, setActiveTab] = useState<'profile' | 'activities' | 'files' | 'opinions'>('profile')
  const [showLiaModal, setShowLiaModal] = useState(false)
  const [liaCommand, setLiaCommand] = useState('')
  const [showVideoModal, setShowVideoModal] = useState<Record<string, unknown> | null>(null)
  const [viewMode, setViewMode] = useState<'timeline' | 'list'>('timeline')
  const [expandedLiaPredictions, setExpandedLiaPredictions] = useState(false)
  const [periodFilter, setPeriodFilter] = useState('all')
  const [activityFilter, setActivityFilter] = useState('all')
  const [expandedActivity, setExpandedActivity] = useState<string | null>(null)
  const [showAIPredictions, setShowAIPredictions] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<Record<string, unknown> | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [previewType, setPreviewType] = useState<'pdf' | 'image' | 'video' | 'audio' | null>(null)
  const [videoPlaying, setVideoPlaying] = useState(false)
  const [pdfPage, setPdfPage] = useState(1)
  const [pdfTotalPages, setPdfTotalPages] = useState(5)
  const [imageZoom, setImageZoom] = useState(100)

  const [opinionsSubTab, setOpinionsSubTab] = useState<'pareceres' | 'analises'>('pareceres')
  const [opinionsHistory, setOpinionsHistory] = useState<Record<string, unknown>[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [expandedOpinionId, setExpandedOpinionId] = useState<string | null>(null)
  const [savedAnalyses, setSavedAnalyses] = useState<{ total_analyses: number; analyses: Record<string, unknown>[] } | null>(null)
  const [isLoadingAnalyses, setIsLoadingAnalyses] = useState(false)
  const [expandedAnalysisId, setExpandedAnalysisId] = useState<string | null>(null)
  const [copiedItemId, setCopiedItemId] = useState<string | null>(null)
  const [analysisToDelete, setAnalysisToDelete] = useState<Record<string, unknown> | null>(null)
  const [showLiaAnalysisModal, setShowLiaAnalysisModal] = useState(false)

  const candidateName = String(candidate?.name || '')

  const activities = [
    {
      id: 'lia-eval-1',
      type: 'lia-evaluation',
      icon: Brain,
      iconColor: 'var(--lia-text-secondary)',
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
      summary: 'Candidato altamente qualificado com excelente aderência cultural e técnico.',
      details: {
        technicalNota: 92,
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
      iconColor: 'var(--status-success)',
      title: 'Carta Oferta Enviada',
      author: 'Ana Silva',
      authorRole: 'Recrutadora',
      date: 'Hoje às 10:00',
      timestamp: new Date().toISOString(),
      jobId: 'UXD-2024-001',
      jobTitle: 'UX Designer Sênior',
      status: 'sent',
      statusLabel: 'Enviada',
      summary: `Oferta formal enviada com salário de ${CURRENCY_SYMBOL} 20.000 CLT + benefícios.`,
      details: {
        salary: `${CURRENCY_SYMBOL} 20.000`,
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
      iconColor: 'var(--wedo-purple)',
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
      // @canonical-allow-100 mock string deletado em F3 (Surface 2 absorption)
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
      iconColor: 'var(--lia-text-secondary)',
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
          salary: `${CURRENCY_SYMBOL} 18-22k CLT`,
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
      iconColor: 'var(--lia-text-tertiary)',
      title: 'Vídeo de apresentação gravado',
      author: candidateName,
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
      iconColor: 'var(--wedo-orange)',
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
        suggestedSalary: `${CURRENCY_SYMBOL} 20.000`
      }
    }
  ]

  const aiPredictions = [
    {
      id: 'response-time',
      title: 'Resposta à Oferta',
      probability: 85,
      timeframe: '2-3 dias',
      recommendation: 'Follow-up recomendado em 48h',
      icon: '📧',
      color: 'var(--wedo-green-light)'
    },
    {
      id: 'negotiation',
      title: 'Possível Negociação',
      probability: 30,
      timeframe: '3-5 dias',
      recommendation: 'Preparar margem de negociação de até 10%',
      icon: '💰',
      color: 'var(--lia-border-default)'
    },
    {
      id: 'acceptance',
      title: 'Aceitação da Oferta',
      probability: 75,
      timeframe: '5-7 dias',
      recommendation: 'Iniciar preparação do onboarding',
      icon: '✅',
      color: 'var(--lia-border-subtle)'
    },
    {
      id: 'start-date',
      title: 'Confirmação de Início',
      probability: 90,
      timeframe: '30 dias',
      recommendation: 'Agendar primeira semana de integração',
      icon: '🎯',
      color: 'var(--lia-border-subtle)'
    }
  ]

  const tabs = [
    { id: 'profile', label: 'Perfil Completo', icon: UserCheck },
    { id: 'activities', label: 'Atividades', icon: Activity },
    { id: 'files', label: 'Arquivos', icon: FileText },
    { id: 'opinions', label: 'Pareceres', icon: Brain, badge: opinionsHistory.length + ((savedAnalyses?.total_analyses as number) || 0) }
  ]

  const colorToBg: Record<string, string> = {
    'var(--lia-border-subtle)': 'var(--lia-border-subtle)',
    'var(--lia-border-default)': 'var(--lia-border-default)',
    'var(--lia-text-tertiary)': 'var(--lia-bg-secondary)',
    'var(--lia-text-secondary)': 'var(--lia-bg-secondary)',
    'var(--status-success)': 'var(--status-success-bg)',
    'var(--status-error)': 'var(--status-error-bg)',
    'var(--status-warning)': 'var(--status-warning-bg)',
    'var(--wedo-green-light)': 'var(--wedo-green-light-bg-20)',
    'var(--wedo-purple)': 'var(--wedo-purple-bg-10)',
    'var(--wedo-orange)': 'var(--wedo-orange-bg-15)',
    'var(--wedo-cyan)': 'var(--wedo-cyan-bg-10)',
  }
  const getBgColor = (color: string) => colorToBg[color] || 'var(--lia-bg-secondary)'

  const filterByPeriod = (activity: Record<string, unknown>) => {
    if (periodFilter === 'all') return true
    const now = new Date()
    const activityDate = new Date(String(activity.timestamp))
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

  const textStyles = {
    title: 'text-sm font-semibold text-lia-text-primary',
    subtitle: 'text-xs font-medium text-lia-text-primary',
    body: 'text-xs text-lia-text-secondary',
    bodySmall: 'text-xs text-lia-text-secondary',
    caption: 'text-micro text-lia-text-tertiary',
    label: 'text-micro font-medium text-lia-text-primary uppercase tracking-wider',
    description: 'text-micro text-lia-text-tertiary'
  }

  const localBadgeStyles = {
    default: 'text-micro px-1.5 py-0 h-4 bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-0',
    success: 'text-micro px-1.5 py-0 h-4 bg-status-success/10 dark:bg-status-success/20 text-status-success dark:text-status-success border-0',
    warning: 'text-micro px-1.5 py-0 h-4 bg-status-warning/10 dark:bg-status-warning/20 text-status-warning dark:text-status-warning border-0',
    error: 'text-micro px-1.5 py-0 h-4 bg-status-error/10 dark:bg-status-error/20 text-status-error dark:text-status-error border-0',
    info: 'text-micro px-1.5 py-0 h-4 bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary border-0'
  }

  const localCardStyles = {
    default: 'bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md'
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

  const handleCopyOpinion = async (opinion: Record<string, unknown>, type: string) => {
    const analysisLabels: Record<string, string> = {
      'quick': 'Triagem Rápida',
      'general': 'Parecer Geral',
      'wsi': 'Parecer WSI'
    }
    const header = `PARECER LIA - ${candidateName}\nTipo: ${analysisLabels[type] || type}\n${opinion.job_vacancy_title ? `Vaga: ${opinion.job_vacancy_title}\n` : ''}Nota: ${(() => { const raw = (opinion.score ?? opinion.wsi_score); if (raw == null) return 'N/A'; const n = typeof raw === 'number' ? raw : Number(raw); const norm = isFinite(n) ? (n > 10 ? n / 10 : n) : 0; return norm.toFixed(1) + '/10'; })()}\nData: ${opinion.created_at ? new Date(String(opinion.created_at)).toLocaleDateString('pt-BR') : 'N/A'}\n\n`
    const content = cleanTextForCopy(String(opinion.summary || opinion.content || ''))
    await navigator.clipboard.writeText(header + content)
    setCopiedItemId(`opinion-${opinion.id}`)
    setTimeout(() => setCopiedItemId(null), 2000)
    toast.success('Parecer copiado!')
  }

  const handleCopyAnalysis = async (analysis: Record<string, unknown>) => {
    const analysisLabels: Record<string, string> = {
      'bullet_points': 'Pontos-chave',
      'short_paragraph': 'Resumo',
      'detailed_bullets': 'Análise Detalhada'
    }
    const header = `ANÁLISE LIA - ${candidateName}\nTipo: ${analysisLabels[String(analysis.analysis_type)] || analysis.analysis_type}\nData: ${analysis.created_at ? new Date(String(analysis.created_at)).toLocaleDateString('pt-BR') : 'N/A'}\n\n`
    const content = cleanTextForCopy(String(analysis.content || ''))
    await navigator.clipboard.writeText(header + content)
    setCopiedItemId(`analysis-${analysis.id}`)
    setTimeout(() => setCopiedItemId(null), 2000)
    toast.success('Análise copiada!')
  }

  const handleDeleteAnalysis = async () => {
    if (!analysisToDelete || !candidate) return
    try {
      if (!companyId) return
      const response = await fetch(`/api/backend-proxy/lia/profile-analysis/${candidate.id}/${analysisToDelete.analysis_type}?company_id=${encodeURIComponent(companyId)}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        setSavedAnalyses((prev) => {
          if (!prev) return prev
          return {
            ...prev,
            analyses: prev.analyses.filter((a: Record<string, unknown>) => a.id !== analysisToDelete.id),
            total_analyses: prev.total_analyses - 1
          }
        })
        toast.success('Análise removida com sucesso')
      }
    } catch {
      toast.error('Erro ao remover análise')
    }
    setAnalysisToDelete(null)
  }

  const handleAnalysisTransport = async () => {
    if (!candidate) return
    try {
      if (!companyId) return
      const response = await fetch(`/api/backend-proxy/lia/profile-analysis/candidate/${candidate.id}?company_id=${encodeURIComponent(companyId)}`)
      if (response.ok) {
        const data = await response.json()
        setSavedAnalyses(data)
        toast.success('Análise adicionada à aba Pareceres')
        setOpinionsSubTab('analises')
      }
    } catch {
    }
  }

  useEffect(() => {
    const fetchOpinionsHistory = async () => {
      if (!candidate?.id || !companyId) return
      setIsLoadingHistory(true)
      try {
        const response = await fetch(`/api/backend-proxy/opinions/history/${candidate.id}?company_id=${encodeURIComponent(companyId)}`)
        if (response.ok) {
          const data = await response.json()
          setOpinionsHistory(data.opinions || [])
        }
      } catch {
      } finally {
        setIsLoadingHistory(false)
      }
    }

    const fetchSavedAnalyses = async () => {
      if (!candidate?.id || !companyId) return
      setIsLoadingAnalyses(true)
      try {
        const response = await fetch(`/api/backend-proxy/lia/profile-analysis/candidate/${candidate.id}?company_id=${encodeURIComponent(companyId)}`)
        if (response.ok) {
          const data = await response.json()
          setSavedAnalyses(data)
        }
      } catch {
      } finally {
        setIsLoadingAnalyses(false)
      }
    }

    fetchOpinionsHistory()
    fetchSavedAnalyses()
  }, [candidate?.id, companyId])

  const getScoreColor = (score: number) => {
    if (score >= 90) return "bg-wedo-green-pastel text-lia-text-primary"
    if (score >= 80) return "bg-lia-bg-tertiary text-lia-text-primary"
    if (score >= 70) return "bg-lia-interactive-active text-lia-text-primary"
    return "bg-lia-bg-tertiary text-lia-text-primary"
  }

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

  const hasPersonalData = (c: Record<string, unknown>): boolean => {
    return !!(c.date_of_birth || c.gender || c.nationality ||
              c.marital_status || c.estimated_age)
  }

  const hasPearchData = (c: Record<string, unknown>): boolean => {
    return !!(c.headline || c.is_open_to_work || c.is_decision_maker ||
              c.is_top_universities || c.is_hiring || c.linkedin_followers_count ||
              c.linkedin_connections_count || c.pearch_profile_id)
  }

  return {
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
    savedAnalyses, setSavedAnalyses,
    isLoadingAnalyses,
    expandedAnalysisId, setExpandedAnalysisId,
    copiedItemId, setCopiedItemId,
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
  }
}
