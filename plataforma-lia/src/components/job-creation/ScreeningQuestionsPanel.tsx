"use client"

import React, { useState, useEffect, useMemo, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Brain, RefreshCw, ChevronDown, ChevronUp,
  Target, Users, Heart, Loader2, AlertCircle, Check,
  Lightbulb, TrendingUp, Layers, MessageCircle, Clock,
  Repeat, FileText, Mic, Bell, Lock, Settings2, Zap, Building2,
  Plus, Trash2, ArrowRight, Send, AlertTriangle
} from "lucide-react"
import { useWSIScreeningPipeline, type UnifiedScreeningQuestion, type WSIScreeningPipelineRequest, type BigFiveProfile } from "@/hooks/use-screening-questions"
import { useCompanyEligibilityQuestions, type CompanyEligibilityQuestion } from "@/hooks/use-company-eligibility-questions"
import { cn } from "@/lib/utils"
import { AIDisclaimer } from "@/components/ui/ai-disclaimer"

interface ScreeningQuestionsPanelProps {
  jobTitle: string
  department?: string
  seniority: 'junior' | 'pleno' | 'senior' | 'lead' | 'executive'
  bigFiveProfile?: BigFiveProfile
  skills: string[]
  behavioralCompetencies?: string[]
  isAffirmative?: boolean
  affirmativeType?: string
  onQuestionsChange?: (questions: Record<string, unknown>[]) => void
  className?: string
}

const WSI_BLOCKS = [
  { 
    id: 0, 
    name: 'Abordagem Inicial', 
    description: 'Template WhatsApp pré-aprovado',
    duration: '< 1 min', 
    editable: false,
    type: 'template',
    icon: MessageCircle
  },
  { 
    id: 1, 
    name: 'Apresentação da Oportunidade', 
    description: 'Pitch conversacional com detalhes da vaga',
    duration: '3 min', 
    editable: false,
    type: 'presentation',
    icon: FileText
  },
  { 
    id: 2, 
    name: 'Perguntas Padrão da Empresa', 
    description: 'Perguntas configuradas pela empresa (incluindo elegibilidade)',
    duration: '3 min', 
    editable: true,
    type: 'company',
    icon: Building2
  },
  { 
    id: 3, 
    name: 'Avaliação Técnica', 
    description: 'Skills com pesos e rubricas automáticas',
    duration: '5 min', 
    editable: true,
    type: 'technical',
    icon: Zap
  },
  { 
    id: 4, 
    name: 'Análise Situacional e Fit', 
    description: 'Perguntas situacionais com follow-ups',
    duration: '4 min', 
    editable: true,
    type: 'situational',
    icon: Users
  },
  { 
    id: 5, 
    name: 'Resultado e Encerramento', 
    description: 'Índice WSI automático e feedback',
    duration: '3 min', 
    editable: false,
    type: 'result',
    icon: Brain
  }
]

const WSI_AUTOMATIC_MESSAGES: Record<number, { title: string; message: string; note: string }> = {
  0: {
    title: "Abordagem Inicial via WhatsApp",
    message: `Olá {candidato.nome}! 👋

Aqui é a LIA, assistente de recrutamento da {empresa.nome}.

Vi que você se candidatou para a vaga de {vaga.titulo} e gostaria de conversar sobre a oportunidade.

Podemos iniciar agora? Leva menos de 10 minutos! 🚀`,
    note: "Template pré-aprovado • Enviado automaticamente ao candidato"
  },
  1: {
    title: "Apresentação da Oportunidade",
    message: `Que ótimo ter você aqui! Deixa eu te contar um pouco sobre a vaga:

📋 **Posição:** {vaga.titulo}
🏢 **Empresa:** {empresa.nome}
📍 **Modelo:** {vaga.modelo_trabalho}
💰 **Faixa Salarial:** {vaga.faixa_salarial}

{vaga.descricao_resumida}

Agora vou fazer algumas perguntas rápidas para entender melhor seu perfil. Responda naturalmente, como se estivéssemos conversando! 💬`,
    note: "Pitch conversacional • Gerado a partir dos dados da vaga"
  },
  6: {
    title: "Resultado e Encerramento",
    message: `Muito obrigada pelas suas respostas, {candidato.nome}! 🙏

Analisei todas as informações e já encaminhei seu perfil para nossa equipe de recrutamento.

📊 **Próximos passos:**
• Você receberá um feedback em até {prazo_feedback}
• Se aprovado(a), entraremos em contato para agendar a entrevista

Qualquer dúvida, estou por aqui! Boa sorte! 🍀`,
    note: "Índice WSI calculado automaticamente • Feedback enviado conforme configuração"
  }
}

function formatMessageWithVariables(message: string): React.ReactNode[] {
  const parts = message.split(/(\{[^}]+\})/g)
  return parts.map((part, index) => {
    if (part.match(/^\{[^}]+\}$/)) {
      return (
        <span key={`ph-${index}`} style={{fontWeight: 500}}>
          {part}
        </span>
      )
    }
    if (part.includes('**')) {
      const boldParts = part.split(/(\*\*[^*]+\*\*)/g)
      return boldParts.map((bp, bpIndex) => {
        if (bp.match(/^\*\*[^*]+\*\*$/)) {
          return <strong key={`${index}-${bpIndex}`}>{bp.replace(/\*\*/g, '')}</strong>
        }
        return <span key={`${index}-${bpIndex}`}>{bp}</span>
      })
    }
    return <span key={`part-${index}`}>{part}</span>
  })
}

const BLOOM_COLORS: Record<number, string> = {
  1: "bg-gray-100 lia-text-base border-lia-border-subtle",
  2: "bg-status-warning/10 text-status-warning border-status-warning/30",
  3: "bg-wedo-orange/10 text-wedo-orange border-wedo-orange/30",
  4: "bg-status-error/10 text-status-error border-status-error/30",
  5: "bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30",
  6: "bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30"
}

const DREYFUS_COLORS: Record<number, string> = {
  1: "bg-gray-100 lia-text-base border-lia-border-subtle",
  2: "bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-default dark:border-lia-border-default",
  3: "bg-status-success/10 text-status-success border-status-success/30",
  4: "bg-status-warning/10 text-status-warning border-status-warning/30",
  5: "bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30"
}

export function ScreeningQuestionsPanel({
  jobTitle,
  department,
  seniority,
  bigFiveProfile,
  skills,
  behavioralCompetencies,
  isAffirmative,
  affirmativeType,
  onQuestionsChange,
  className,
}: ScreeningQuestionsPanelProps) {
  const {
    questions: pipelineQuestions,
    blocks: pipelineBlocks,
    isLoading,
    error,
    metadata,
    qualityWarnings,
    blockDistribution,
    generatePipeline,
    toggleQuestion,
    getSelectedQuestions
  } = useWSIScreeningPipeline()

  const {
    questions: companyQuestions,
    isLoading: isLoadingCompanyQuestions
  } = useCompanyEligibilityQuestions()

  const [screeningModel, setScreeningModel] = useState<'compact' | 'full'>('compact')
  const [expandedBlocks, setExpandedBlocks] = useState<Record<number, boolean>>({
    0: false,
    1: false,
    2: true,
    3: true,
    4: true,
    5: true,
    6: false
  })
  const [hasGenerated, setHasGenerated] = useState(false)
  const [selectedBlockForSuggestion, setSelectedBlockForSuggestion] = useState<number>(4)
  const [isGeneratingMore, setIsGeneratingMore] = useState(false)

  const questionsByBlock = useMemo(() => {
    const blocks: Record<number, UnifiedScreeningQuestion[]> = {
      0: [],
      1: [],
      2: [],
      3: [],
      4: [],
      5: [],
      6: []
    }

    pipelineQuestions.forEach(q => {
      const blockId = q.block_id
      if (blocks[blockId] !== undefined) {
        blocks[blockId].push(q)
      }
    })

    companyQuestions.forEach(cq => {
      const exists = blocks[2].some(q => q.id === cq.id)
      if (!exists) {
        const unifiedQuestion: UnifiedScreeningQuestion = {
          id: cq.id,
          text: cq.question_text,
          category: 'company',
          block_id: 2,
          source: 'company',
          bloom_level: 2,
          bloom_label: 'Compreender',
          dreyfus_stage: 3,
          dreyfus_label: 'Competente',
          framework: 'CBI',
          weight: 0.7,
          expected_signals: [],
          scoring_criteria: {},
          is_selected: true,
          is_eliminatory: cq.is_eliminatory,
          question_type: cq.question_type,
          options: cq.options,
          expected_answer: cq.expected_answer,
          order: cq.order
        }
        blocks[2].push(unifiedQuestion)
      }
    })

    return blocks
  }, [pipelineQuestions, companyQuestions])

  const totalEditableQuestions = useMemo(() => {
    return questionsByBlock[2].length + questionsByBlock[3].length + questionsByBlock[4].length + questionsByBlock[5].length
  }, [questionsByBlock])

  const selectedCount = useMemo(() => {
    const pipelineSelected = pipelineQuestions.filter(q => q.is_selected).length
    const companySelected = questionsByBlock[2].filter(q => q.is_selected).length
    return pipelineSelected + companySelected
  }, [pipelineQuestions, questionsByBlock])

  const totalDuration = useMemo(() => {
    return screeningModel === 'full' ? 30 : 15
  }, [screeningModel])

  const questionCountLabel = useMemo(() => {
    return screeningModel === 'full' ? '12 WSI' : '8 WSI'
  }, [screeningModel])

  useEffect(() => {
    if (jobTitle && !hasGenerated) {
      const context: WSIScreeningPipelineRequest = {
        job_title: jobTitle,
        department,
        seniority,
        technical_skills: skills,
        behavioral_competencies: behavioralCompetencies,
        big_five_profile: bigFiveProfile,
        format: screeningModel,
        include_company_questions: true,
        is_affirmative: isAffirmative || false,
        affirmative_type: affirmativeType,
      }
      generatePipeline(context)
      setHasGenerated(true)
    }
  }, [jobTitle, department, seniority, bigFiveProfile, skills, behavioralCompetencies, generatePipeline, hasGenerated, screeningModel, isAffirmative, affirmativeType])

  const onQuestionsChangeRef = useRef(onQuestionsChange)
  onQuestionsChangeRef.current = onQuestionsChange

  useEffect(() => {
    if (onQuestionsChangeRef.current) {
      const pipelineSelected = getSelectedQuestions()
      const companySelected = (questionsByBlock[2] || []).filter(q => q.is_selected)
      // @ts-ignore TODO: fix type
      onQuestionsChangeRef.current([...companySelected, ...pipelineSelected])
    }
  }, [pipelineQuestions, companyQuestions, getSelectedQuestions, questionsByBlock])

  const suggestionsForSelectedBlock = useMemo(() => {
    const blockQuestions = questionsByBlock[selectedBlockForSuggestion] || []
    return blockQuestions.filter(q => !q.is_selected)
  }, [questionsByBlock, selectedBlockForSuggestion])

  const handleRegenerateAll = async () => {
    if (isLoading) return
    const context: WSIScreeningPipelineRequest = {
      job_title: jobTitle,
      department,
      seniority,
      technical_skills: skills,
      behavioral_competencies: behavioralCompetencies,
      big_five_profile: bigFiveProfile,
      format: screeningModel,
      include_company_questions: true,
      is_affirmative: isAffirmative || false,
      affirmative_type: affirmativeType,
    }
    await generatePipeline(context)
  }

  const handleGenerateMoreForBlock = async () => {
    if (isGeneratingMore) return
    setIsGeneratingMore(true)
    try {
      await handleRegenerateAll()
    } finally {
      setIsGeneratingMore(false)
    }
  }

  const handleAddSuggestion = (question: UnifiedScreeningQuestion) => {
    toggleQuestion(question.id)
  }

  const toggleBlock = (blockId: number) => {
    setExpandedBlocks(prev => ({
      ...prev,
      [blockId]: !prev[blockId]
    }))
  }

  const handleModelChange = (model: 'compact' | 'full') => {
    setScreeningModel(model)
    setHasGenerated(false)
  }

  const renderModelSelector = () => {
    return (
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div
          className={cn(
 "p-3 rounded-md border cursor-pointer transition-colors duration-200",
            screeningModel === 'compact'
              ? "border-gray-900 bg-gray-50 ring-1 ring-gray-900/10"
              : "border-lia-border-subtle hover:border-lia-border-default"
          )}
          onClick={() => handleModelChange('compact')}
        >
          <div className="flex items-center gap-2 mb-1">
            <Zap className={cn("h-4 w-4", screeningModel === 'compact' ? "lia-text-strong" : "lia-text-secondary")} />
            <span className="text-xs font-medium lia-text-strong">Compacto</span>
          </div>
          <p className="text-xs lia-text-base">8 perguntas WSI • ~15 min</p>
          <p className="text-micro lia-text-secondary mt-0.5">Triagem rápida para alto volume</p>
        </div>
        <div
          className={cn(
 "p-3 rounded-md border cursor-pointer transition-colors duration-200",
            screeningModel === 'full'
              ? "border-gray-900 bg-gray-50 ring-1 ring-gray-900/10"
              : "border-lia-border-subtle hover:border-lia-border-default"
          )}
          onClick={() => handleModelChange('full')}
        >
          <div className="flex items-center gap-2 mb-1">
            <Target className={cn("h-4 w-4", screeningModel === 'full' ? "lia-text-strong" : "lia-text-secondary")} />
            <span className="text-xs font-medium lia-text-strong">Completo</span>
          </div>
          <p className="text-xs lia-text-base">12 perguntas WSI • ~30 min</p>
          <p className="text-micro lia-text-secondary mt-0.5">Avaliação aprofundada</p>
        </div>
      </div>
    )
  }

  const renderBlockDistribution = () => {
    if (Object.keys(blockDistribution).length === 0) return null

    const distributionItems = Object.entries(blockDistribution).map(([key, count]) => {
      const blockNames: Record<string, string> = {
        '2': 'Empresa',
        '3': 'Técnico',
        '4': 'Situacional',
      }
      const name = blockNames[key] || `Bloco ${key}`
      return { key, name, count }
    }).filter(item => ['2', '3', '4'].includes(item.key))

    if (distributionItems.length === 0) return null

    return (
      <div className="mb-3">
        <p className="text-micro font-medium lia-text-secondary uppercase tracking-wide mb-1.5">Distribuição por Bloco</p>
        <div className="flex flex-wrap items-center gap-1.5">
          {distributionItems.map((item, idx) => (
            <React.Fragment key={item.key}>
              {idx > 0 && <span className="lia-text-muted text-micro">|</span>}
              <Badge variant="outline" className="text-micro px-2 py-0.5 bg-gray-50 lia-text-base border-lia-border-subtle">
                Bloco {item.key} · {item.name}: {item.count} {item.count === 1 ? 'pergunta' : 'perguntas'}
              </Badge>
            </React.Fragment>
          ))}
        </div>
      </div>
    )
  }

  const renderQualityWarnings = () => {
    if (!qualityWarnings || qualityWarnings.length === 0) return null

    return (
      <div className="mb-3 space-y-1.5">
        {qualityWarnings.map((warning, idx) => (
          <div key={idx} className="flex items-start gap-2 p-2 bg-status-warning/10 border border-status-warning/30 rounded-md">
            <AlertTriangle className="h-3.5 w-3.5 text-status-warning mt-0.5 flex-shrink-0" />
            <p className="text-micro text-status-warning">{warning}</p>
          </div>
        ))}
      </div>
    )
  }

  const renderConfigDashboard = () => {
    const configItems = [
      { icon: MessageCircle, label: 'Canal', value: 'WhatsApp', sublabel: 'mensageria' },
      { icon: Clock, label: 'Duração', value: `~${totalDuration} min`, sublabel: 'tempo total' },
      { icon: Repeat, label: 'Tentativas', value: '3', sublabel: 'de contato' },
      { icon: FileText, label: 'Perguntas', value: questionCountLabel, sublabel: 'fixas + adaptativas' },
      { icon: Mic, label: 'Formato', value: 'Texto/Áudio', sublabel: 'resposta híbrida' },
      { icon: Bell, label: 'Feedback', value: '24 horas', sublabel: 'automático' }
    ]

    return (
      <div className="grid grid-cols-6 gap-2 mb-4 p-3 bg-gray-50 rounded-md border border-lia-border-subtle">
        {configItems.map((item, idx) => (
          <div key={idx} className="flex flex-col items-center text-center">
            <item.icon className="h-4 w-4 lia-text-secondary mb-1" />
            <span className="text-micro lia-text-secondary uppercase tracking-wide">{item.label}</span>
            <span className="text-xs font-semibold lia-text-strong">{item.value}</span>
            <span className="text-micro lia-text-secondary">{item.sublabel}</span>
          </div>
        ))}
      </div>
    )
  }

  const renderQuestionCard = (question: UnifiedScreeningQuestion, showDelete: boolean = false) => {
    const isAffirmativeQuestion = question.id?.includes('affirmative') || false
    const getCategoryBadge = () => {
      if (isAffirmativeQuestion) return { label: 'Inclusão', color: 'bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30' }
      const cat = (question.category || '').toLowerCase()
      if (cat.includes('tech')) return { label: 'Técnica', color: 'bg-wedo-cyan/10 text-wedo-cyan-dark border-wedo-cyan/30 dark:text-wedo-cyan-dark dark:border-wedo-cyan/30' }
      if (cat.includes('behav') || cat.includes('situa')) return { label: 'Experiência', color: 'bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30' }
      if (cat.includes('elig') && question.is_eliminatory === false) return { label: 'Informativa', color: 'bg-gray-50 lia-text-base border-lia-border-subtle' }
      if (cat.includes('elig')) return { label: 'Eliminatória', color: 'bg-status-error/10 text-status-error border-status-error/30' }
      if (cat.includes('cult')) return { label: 'Cultural', color: 'bg-status-success/10 text-status-success border-status-success/30' }
      if (cat.includes('company')) return { label: 'Empresa', color: 'bg-wedo-orange/10 text-wedo-orange border-wedo-orange/30' }
      return { label: 'Informativa', color: 'bg-gray-50 lia-text-base border-lia-border-subtle' }
    }
    
    const badge = getCategoryBadge()

    return (
      <div
        key={question.id}
        className={cn(
 "p-3 rounded-md border transition-colors duration-200 group",
          question.is_selected
            ? "bg-lia-bg-primary border-lia-border-subtle"
            : "bg-gray-50/50 border-lia-border-subtle opacity-70"
        )}
      >
        <div className="flex items-start gap-3">
          <Checkbox
            checked={question.is_selected}
            onCheckedChange={() => toggleQuestion(question.id)}
            className="mt-0.5"
          />
          <div className="flex-1 space-y-2">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-1">
                <Badge variant="outline" className={cn("text-micro px-1.5 py-0 h-4 border", badge.color)}>
                  {badge.label}
                </Badge>
                {isAffirmativeQuestion && (
                  <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 border bg-status-success/10 text-status-success border-status-success/30">
                    Não eliminatória
                  </Badge>
                )}
              </div>
              {showDelete && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-5 w-5 p-0 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none"
                  onClick={() => toggleQuestion(question.id)}
                >
                  <Trash2 className="h-3 w-3 lia-text-secondary hover:text-status-error" />
                </Button>
              )}
            </div>
            <p className="text-xs lia-text-strong leading-relaxed">
              {question.text}
            </p>
            <div className="flex items-center gap-3 text-micro lia-text-secondary">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-status-success"></span>
                {question.weight ? `${Math.round(question.weight * 100)}%` : '75%'}
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-status-error"></span>
                0%
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-gray-300"></span>
                {question.dreyfus_stage ? `${(question.dreyfus_stage / 5 * 100).toFixed(0)}%` : '55%'}
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderBlockSection = (block: typeof WSI_BLOCKS[0]) => {
    const Icon = block.icon
    const isExpanded = expandedBlocks[block.id]
    const questions = questionsByBlock[block.id] || []
    const selectedInBlock = questions.filter(q => q.is_selected).length

    return (
      <div key={block.id} className="space-y-2">
        <div
          className={cn(
 "flex items-center justify-between p-2.5 rounded-md cursor-pointer transition-colors border",
            block.editable 
              ? "bg-lia-bg-primary border-lia-border-subtle hover:bg-gray-50"
              : "bg-gray-100/80 border-lia-border-subtle"
          )}
          onClick={() => toggleBlock(block.id)}
        >
          <div className="flex items-center gap-2.5">
            <div className={cn(
 "w-6 h-6 rounded-full flex items-center justify-center text-micro font-medium",
              block.editable ? "bg-gray-200 lia-text-base" : "bg-gray-100 lia-text-secondary"
            )}>
              {block.id}
            </div>
            <Icon className={cn("h-4 w-4", block.editable ? "lia-text-base" : "lia-text-secondary")} />
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-medium lia-text-strong">{block.name}</span>
                {block.id === 2 && isAffirmative && (
                  <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 border bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                    Vaga Afirmativa
                  </Badge>
                )}
              </div>
              <span className="text-micro lia-text-secondary">{block.duration}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {!block.editable && (
              <Badge 
                variant="outline" 
                className="text-micro px-1.5 py-0 bg-gray-100 lia-text-secondary border-lia-border-subtle"
              >
                <Lock className="h-2.5 w-2.5 mr-0.5" />
                Automático
              </Badge>
            )}
            {block.editable && questions.length > 0 && (
              <Badge 
                variant="outline" 
                className="text-micro px-1.5 py-0"
                style={{backgroundColor: selectedInBlock > 0 ? 'var(--wedo-green-pastel)' : 'var(--gray-100)', color: selectedInBlock > 0 ? 'var(--status-success)' : 'var(--gray-500)', borderColor: selectedInBlock > 0 ? 'var(--wedo-green-pastel)' : 'var(--gray-300)'}}
              >
                {selectedInBlock} {selectedInBlock === 1 ? 'Info.' : 'Infos.'}
              </Badge>
            )}
            {isExpanded ? (
              <ChevronUp className="h-4 w-4 lia-text-secondary" />
            ) : (
              <ChevronDown className="h-4 w-4 lia-text-secondary" />
            )}
          </div>
        </div>

        {isExpanded && (
          <div className="space-y-2 pl-3 pr-1">
            {!block.editable ? (
              WSI_AUTOMATIC_MESSAGES[block.id] ? (
                <div className="rounded-md border border-lia-border-subtle bg-gray-50 overflow-hidden">
                  <div className="px-3 py-2 border-b border-lia-border-subtle bg-gray-100">
                    <p className="text-xs font-medium lia-text-strong">
                      {WSI_AUTOMATIC_MESSAGES[block.id].title}
                    </p>
                  </div>
                  <div className="p-3">
                    <div className="text-xs text-lia-text-primary dark:text-lia-text-primary leading-relaxed whitespace-pre-line">
                      {formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id].message)}
                    </div>
                  </div>
                  <div className="px-3 py-2 border-t border-lia-border-subtle bg-gray-50">
                    <p className="text-micro lia-text-secondary italic">
                      {WSI_AUTOMATIC_MESSAGES[block.id].note}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-3 rounded-md bg-gray-50/50 border border-lia-border-subtle">
                  <p className="text-xs lia-text-secondary italic">
                    {block.description}
                  </p>
                </div>
              )
            ) : questions.length === 0 ? (
              <div className="p-3 rounded-md bg-gray-50/50 border border-lia-border-subtle border-dashed">
                <p className="text-xs lia-text-secondary italic text-center">
                  Nenhuma pergunta neste bloco
                </p>
                <div className="flex justify-center mt-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 text-micro lia-text-base"
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedBlockForSuggestion(block.id)
                    }}
                  >
                    <Plus className="h-3 w-3 mr-1" />
                    Adicionar
                  </Button>
                </div>
              </div>
            ) : (
              questions.map(q => renderQuestionCard(q, false))
            )}
          </div>
        )}
      </div>
    )
  }

  const renderSuggestionCard = (question: UnifiedScreeningQuestion) => {
    const getCategoryBadges = () => {
      const badges = []
      const isAffirmativeSuggestion = question.id?.includes('affirmative') || false
      const cat = (question.category || '').toLowerCase()
      if (isAffirmativeSuggestion) {
        // @ts-ignore TODO: fix type
        badges.push({ label: 'Inclusão', color: 'bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30' })
      } else if (cat.includes('elig') && question.is_eliminatory !== false) {
        // @ts-ignore TODO: fix type
        badges.push({ label: 'Eliminatória', color: 'bg-status-error/10 text-status-error border-status-error/30' })
      } else if (cat.includes('elig')) {
        // @ts-ignore TODO: fix type
        badges.push({ label: 'Informativa', color: 'bg-gray-50 lia-text-base border-lia-border-subtle' })
      }
      // @ts-ignore TODO: fix type
      if (cat.includes('tech')) badges.push({ label: 'Skills', color: 'bg-wedo-cyan/10 text-wedo-cyan-dark border-wedo-cyan/30 dark:text-wedo-cyan-dark dark:border-wedo-cyan/30' })
      // @ts-ignore TODO: fix type
      if (cat.includes('behav') || cat.includes('situa')) badges.push({ label: 'Experiência', color: 'bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30' })
      // @ts-ignore TODO: fix type
      if (cat.includes('cult')) badges.push({ label: 'Cultural', color: 'bg-status-success/10 text-status-success border-status-success/30' })
      // @ts-ignore TODO: fix type
      if (badges.length === 0) badges.push({ label: 'Geral', color: 'bg-wedo-orange/10 text-wedo-orange border-wedo-orange/30' })
      return badges
    }

    const badges = getCategoryBadges()

    return (
      <div
        key={question.id}
        className="p-3 rounded-md border border-lia-border-subtle bg-lia-bg-primary transition-colors motion-reduce:transition-none cursor-pointer group"
        onClick={() => handleAddSuggestion(question)}
      >
        <div className="flex items-start gap-3">
          <Checkbox
            checked={question.is_selected}
            onCheckedChange={() => handleAddSuggestion(question)}
            className="mt-0.5"
          />
          <div className="flex-1 space-y-2">
            <p className="text-xs lia-text-strong leading-relaxed">
              {question.text}
            </p>
            <div className="flex flex-wrap gap-1">

              {badges.map((badge, idx) => (

                <Badge key={idx} variant="outline" className={cn("text-micro px-1.5 py-0 h-4 border", badge.color)}>
                  {((badge as any).label as React.ReactNode)}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading && !hasGenerated) {
    // @ts-ignore TODO: fix type
    return (
      <Card className={cn("w-full", className)}>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-3" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="h-8 w-8 animate-spin motion-reduce:animate-none mx-auto lia-text-base" />
            <p className="text-xs lia-text-base">
              Gerando perguntas de triagem com metodologia WSI...
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={cn("w-full border-status-error/30", className)}>
        <CardContent className="flex items-center justify-center py-8">
          <div className="text-center space-y-3">
            <AlertCircle className="h-8 w-8 mx-auto text-status-error" />
            <p className="text-xs text-status-error">{error}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setHasGenerated(false)}
              className="text-xs"
            >
              Tentar novamente
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  const editableBlocks = WSI_BLOCKS.filter(b => b.editable && b.id !== 2)

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-wedo-cyan" />
            <CardTitle className="text-sm font-medium">Roteiro WSI de Triagem</CardTitle>
            <Badge 
              variant="outline" 
              className="text-micro px-1.5 py-0 rounded-full bg-status-success/10 text-status-success border-status-success/30"
            >
              Ativo
            </Badge>
            <AIDisclaimer />
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3">
        {renderModelSelector()}
        {renderBlockDistribution()}
        {renderQualityWarnings()}
        {renderConfigDashboard()}

        <div className="flex gap-4">
          <div className="flex-1">
            <ScrollArea className="h-[420px] pr-2">
              <div className="space-y-2">
                {WSI_BLOCKS.map(renderBlockSection)}
              </div>
            </ScrollArea>
          </div>

          <div className="w-[280px] space-y-3">
            <div className="relative">
              <input
                type="text"
                placeholder="Peça para a LIA gerar mais perguntas..."
                className="w-full h-10 pl-3 pr-10 text-xs border border-lia-border-default rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900/20 focus:border-gray-900"
              />
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1 h-8 w-8 p-0 bg-gray-900 hover:bg-gray-800 dark:hover:bg-gray-200 rounded-md"
              >
                <ArrowRight className="h-4 w-4 text-white" />
              </Button>
            </div>

            <div className="p-3 rounded-md border bg-wedo-cyan/10 border-wedo-cyan/20">
              <div className="flex items-start gap-2">
                <Brain className="h-4 w-4 mt-0.5 flex-shrink-0 text-wedo-cyan" />
                <div>
                  <p className="text-xs font-medium lia-text-strong">Metodologia WSI</p>
                  <p className="text-micro lia-text-base leading-relaxed mt-0.5" aria-live="polite" aria-atomic="true">
                    A LIA gera perguntas seguindo a metodologia WeDoTalent Skill Index, 
                    calibrando complexidade conforme senioridade e skills da vaga.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Brain className="h-3.5 w-3.5 text-wedo-cyan" />
                  <span className="text-xs font-medium lia-text-base">Sugestões da LIA</span>
                </div>
              </div>

              <ScrollArea className="h-[240px]">
                <div className="space-y-2 pr-2">
                  {suggestionsForSelectedBlock.length > 0 ? (
                    suggestionsForSelectedBlock.map(renderSuggestionCard)
                  ) : (
                    <div className="p-4 text-center">
                      <p className="text-xs lia-text-secondary">
                        Todas as sugestões foram adicionadas ao roteiro
                      </p>
                    </div>
                  )}
                </div>
              </ScrollArea>

              <div className="pt-2 border-t border-lia-border-subtle">
                <div className="flex items-center gap-2">
                  <Select 
                    value={String(selectedBlockForSuggestion)} 
                    onValueChange={(v) => setSelectedBlockForSuggestion(Number(v))}
                  >
                    <SelectTrigger className="h-8 text-xs flex-1">
                      <SelectValue placeholder="Selecionar bloco" />
                    </SelectTrigger>
                    <SelectContent>
                      {editableBlocks.map(block => (
                        <SelectItem key={block.id} value={String(block.id)} className="text-xs">
                          {block.id}. {block.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 text-xs px-3"
                    onClick={handleGenerateMoreForBlock}
                    disabled={isGeneratingMore}
                  >
                    {isGeneratingMore ? (
                      <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none" />
                    ) : (
                      <>
                        <RefreshCw className="h-3 w-3 mr-1" />
                        Gerar
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-lia-border-subtle">
          <div className="flex items-center gap-4 text-xs lia-text-base">
            <span>{selectedCount} pergunta(s) no roteiro</span>
            <span className="lia-text-secondary">|</span>
            <span>Blocos editáveis: 2, 3, 4, 5</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs lia-text-secondary"
          >
            Fechar
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default ScreeningQuestionsPanel
