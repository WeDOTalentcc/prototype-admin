"use client"

import React, { useState } from"react"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Label } from"@/components/ui/label"
import { Chip } from "@/components/ui/chip"
import { Textarea } from"@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from"@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from"@/components/ui/select"
import { 
  Loader2, 
  Plus, 
  X, 
  Clock, 
  ChevronDown, 
  ChevronRight, 
  Brain,
  Lightbulb,
  Wand2
} from"lucide-react"
import { WSI_TEMPLATES, WSIQuestion, WSIQuestionsData } from"../types"

interface PanelProps {
  initialData?: Record<string, unknown>
  onSubmit: (data: unknown) => Promise<void>
  isLoading?: boolean
  jobContext?: {
    title?: string
    area?: string
    level?: string
    requirements?: string[]
    competencies?: string[]
  }
}

type BloomLevel ="Lembrar" |"Entender" |"Aplicar" |"Analisar" |"Avaliar" |"Criar"
type DreyfusLevel ="Novato" |"Iniciante Avançado" |"Competente" |"Proficiente" |"Expert"
type WSIArea = keyof typeof WSI_TEMPLATES

interface WSITemplateItem {
  question: string
  bloom_level: BloomLevel
  dreyfus_level: DreyfusLevel
  competency: string
  time_estimate: number
}

const BLOOM_OPTIONS: BloomLevel[] = ["Lembrar","Entender","Aplicar","Analisar","Avaliar","Criar"]
const DREYFUS_OPTIONS: DreyfusLevel[] = ["Novato","Iniciante Avançado","Competente","Proficiente","Expert"]

const AREA_LABELS: Record<WSIArea, { label: string; icon: string }> = {
  tech: { label:"Tecnologia", icon:"💻" },
  sales: { label:"Vendas", icon:"💼" },
  leadership: { label:"Liderança", icon:"👔" },
  hr: { label:"RH", icon:"👥" },
  marketing: { label:"Marketing", icon:"📢" },
  finance: { label:"Finanças", icon:"💰" },
  operations: { label:"Operações", icon:"⚙️" }
}

export function WSIQuestionsPanel({
  initialData = {},
  onSubmit,
  isLoading = false,
  jobContext
}: PanelProps) {
  const [questions, setQuestions] = useState<WSIQuestion[]>(() => {
    const initial = initialData.questions as WSIQuestion[] | undefined
    return initial || []
  })
  const [activeTab, setActiveTab] = useState<"ai" |"templates" |"custom">("ai")
  const [showTemplates, setShowTemplates] = useState(false)
  const [selectedArea, setSelectedArea] = useState<WSIArea>("tech")
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [isGenerating, setIsGenerating] = useState(false)
  const [aiConfig, setAiConfig] = useState({
    count: 5,
    focusAreas: [] as string[],
    difficulty:"Competente" as DreyfusLevel
  })

  const [newQuestion, setNewQuestion] = useState({
    question:"",
    bloom_level:"Aplicar" as BloomLevel,
    dreyfus_level:"Competente" as DreyfusLevel,
    competency:"",
    time_estimate: 10
  })

  const handleGenerateWithAI = async () => {
    setIsGenerating(true)
    const generatedQuestions: WSIQuestion[] = [
      {
        id: `wsi_ai_${Date.now()}_1`,
        question: `Considerando sua experiência com ${jobContext?.requirements?.[0] || 'a área técnica'}, descreva um projeto onde você precisou resolver um problema complexo. Qual foi sua abordagem e como você validou a solução?`,
        bloom_level:"Analisar",
        dreyfus_level: aiConfig.difficulty,
        competency:"Resolução de Problemas",
        time_estimate: 12
      },
      {
        id: `wsi_ai_${Date.now()}_2`,
        question: `Imagine que você precisa implementar uma solução para ${jobContext?.title || 'este cargo'}. Como você estruturaria o trabalho nas primeiras duas semanas?`,
        bloom_level:"Criar",
        dreyfus_level: aiConfig.difficulty,
        competency:"Planejamento",
        time_estimate: 10
      },
      {
        id: `wsi_ai_${Date.now()}_3`,
        question: `Conte sobre uma situação onde você precisou colaborar com pessoas de diferentes áreas para atingir um objetivo. Como você gerenciou as diferentes perspectivas?`,
        bloom_level:"Aplicar",
        dreyfus_level: aiConfig.difficulty,
        competency:"Colaboração",
        time_estimate: 8
      }
    ]
    
    await new Promise(resolve => setTimeout(resolve, 1500))
    setQuestions(prev => [...prev, ...generatedQuestions])
    setIsGenerating(false)
  }

  const handleAddTemplate = (template: WSITemplateItem) => {
    const newQ: WSIQuestion = {
      id: `wsi_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      question: template.question,
      bloom_level: template.bloom_level,
      dreyfus_level: template.dreyfus_level,
      competency: template.competency,
      time_estimate: template.time_estimate
    }
    setQuestions((prev) => [...prev, newQ])
  }

  const handleAddCustomQuestion = () => {
    if (!newQuestion.question.trim() || !newQuestion.competency.trim()) return

    const newQ: WSIQuestion = {
      id: `wsi_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      question: newQuestion.question.trim(),
      bloom_level: newQuestion.bloom_level,
      dreyfus_level: newQuestion.dreyfus_level,
      competency: newQuestion.competency.trim(),
      time_estimate: newQuestion.time_estimate
    }
    setQuestions((prev) => [...prev, newQ])
    setNewQuestion({
      question:"",
      bloom_level:"Aplicar",
      dreyfus_level:"Competente",
      competency:"",
      time_estimate: 10
    })
  }

  const handleRemoveQuestion = (id: string) => {
    setQuestions((prev) => prev.filter((q) => q.id !== id))
  }

  const handleUpdateQuestion = (id: string, field: keyof WSIQuestion, value: string | number) => {
    setQuestions((prev) =>
      prev.map((q) => (q.id === id ? { ...q, [field]: value } : q))
    )
  }

  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const handleSubmit = async () => {
    const data: WSIQuestionsData = {
      questions
    }
    await onSubmit(data)
  }

  const getTotalTime = () => {
    return questions.reduce((acc, q) => acc + (q.time_estimate || 0), 0)
  }

  const isTemplateAdded = (template: WSITemplateItem) => {
    return questions.some((q) => q.question === template.question)
  }

  return (
    <div className="space-y-6">
      <Card 
        className="border-2 border-dashed rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle border-lia-border-medium bg-lia-interactive-active/20"
      >
        <CardHeader className="pb-3 dark:border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <div 
              className="p-2 rounded-md bg-lia-border-default"
            >
              <Brain className="h-5 w-5 text-wedo-cyan" />
            </div>
            <div>
              <CardTitle className="text-base font-sans text-lia-text-primary">
                Gerar Perguntas com IA
              </CardTitle>
              <p className="text-xs mt-1 text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                A IA cria perguntas WSI personalizadas baseadas na vaga e competências definidas
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-xs text-lia-text-secondary">
                Quantidade de perguntas
              </Label>
              <Select
                value={aiConfig.count.toString()}
                onValueChange={(v) => setAiConfig(prev => ({ ...prev, count: parseInt(v) }))}
              >
                <SelectTrigger 
                  className="h-9 text-sm dark:bg-lia-bg-primary dark:border-lia-border-subtle border-[var(--lia-border-default)] bg-[var(--lia-bg-primary)]"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[3, 5, 7, 10].map((n) => (
                    <SelectItem key={n} value={n.toString()}>
                      {n} perguntas
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-xs text-lia-text-secondary">
                Nível de proficiência
              </Label>
              <Select
                value={aiConfig.difficulty}
                onValueChange={(v) => setAiConfig(prev => ({ ...prev, difficulty: v as DreyfusLevel }))}
              >
                <SelectTrigger 
                  className="h-9 text-sm dark:bg-lia-bg-primary dark:border-lia-border-subtle border-[var(--lia-border-default)] bg-[var(--lia-bg-primary)]"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DREYFUS_OPTIONS.map((level) => (
                    <SelectItem key={level} value={level}>
                      {level}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            onClick={handleGenerateWithAI}
            disabled={isGenerating}
            className="w-full h-11 text-base font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin motion-reduce:animate-none mr-2" />
                Gerando perguntas personalizadas...
              </>
            ) : (
              <>
                <Wand2 className="h-5 w-5 mr-2" />
                Gerar {aiConfig.count} Perguntas com IA
              </>
            )}
          </Button>

          <div 
            className="flex items-start gap-2 p-3 rounded-xl dark:bg-lia-bg-primary/50 bg-[var(--lia-bg-tertiary)]"
          >
            <Brain className="h-4 w-4 shrink-0 mt-0.5 text-wedo-cyan" />
            <p className="text-xs text-lia-text-secondary" aria-live="polite" aria-atomic="true">
              As perguntas são geradas considerando: requisitos técnicos da vaga, 
              competências comportamentais definidas, nível de senioridade e 
              metodologia WSI (Bloom + Dreyfus + Big Five).
            </p>
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle bg-[var(--lia-bg-secondary)]">
        <CardHeader className="pb-3 dark:border-lia-border-subtle">
          <div className="flex items-center justify-between">
            <CardTitle 
              className="text-sm flex items-center gap-2 font-sans text-lia-text-primary"
            >
              <span>📝</span> Perguntas Selecionadas ({questions.length})
            </CardTitle>
            <div 
              className="flex items-center gap-2 text-xs text-lia-text-tertiary"
            >
              <Clock className="h-3 w-3" />
              {getTotalTime()} min total
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {questions.length === 0 ? (
            <div 
              className="text-center py-8 text-sm text-lia-text-tertiary"
            >
              <Brain className="h-8 w-8 mx-auto mb-3 text-wedo-cyan opacity-50" />
              Nenhuma pergunta adicionada.
              <br />
              <span className="font-medium text-lia-text-secondary">
                Use a geração com IA acima para começar!
              </span>
            </div>
          ) : (
            questions.map((q, index) => (
              <QuestionCard
                key={q.id}
                question={q}
                index={index}
                isExpanded={expandedIds.has(q.id)}
                onToggleExpand={() => toggleExpanded(q.id)}
                onUpdate={(field, value) => handleUpdateQuestion(q.id, field, value)}
                onRemove={() => handleRemoveQuestion(q.id)}
              />
            ))
          )}
        </CardContent>
      </Card>

      <div 
        className="border rounded-xl overflow-hidden dark:border-lia-border-subtle border-[var(--lia-border-subtle)]"
      >
        <button
          type="button"
          onClick={() => setShowTemplates(!showTemplates)}
          className="w-full flex items-center justify-between p-3 transition-colors motion-reduce:transition-none dark:hover:bg-lia-bg-inverse bg-[var(--lia-bg-secondary)] text-lia-text-secondary"
        >
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4" />
            <span className="text-sm font-medium">
              Templates de Referência (Opcional)
            </span>
          </div>
          {showTemplates ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </button>

        {showTemplates && (
          <div 
            className="p-4 border-t dark:border-lia-border-subtle border-[var(--lia-border-subtle)] bg-[var(--lia-bg-primary)]"
          >
            <p 
              className="text-xs mb-4 text-lia-text-tertiary"
             aria-live="polite" aria-atomic="true">
              Use estes templates como inspiração. Para melhores resultados, 
              recomendamos a geração com IA que personaliza as perguntas para sua vaga.
            </p>

            <Tabs value={selectedArea} onValueChange={(v) => setSelectedArea(v as WSIArea)}>
              <TabsList 
                className="grid w-full grid-cols-7 h-auto bg-[var(--lia-bg-tertiary)]"
              >
                {(Object.keys(AREA_LABELS) as WSIArea[]).map((area) => (
                  <TabsTrigger
                    key={area}
                    value={area}
                    className="text-xs flex flex-col gap-1 py-2 px-1"
                  >
                    <span>{AREA_LABELS[area].icon}</span>
                    <span className="hidden sm:inline text-xs">{AREA_LABELS[area].label}</span>
                  </TabsTrigger>
                ))}
              </TabsList>

              {(Object.keys(AREA_LABELS) as WSIArea[]).map((area) => (
                <TabsContent key={area} value={area} className="mt-4 space-y-2">
                  {WSI_TEMPLATES[area].map((template, index) => (
                    <div
                      key={`template-${index}`}
                      className="border rounded-xl p-3 transition-colors motion-reduce:transition-none dark:border-lia-border-subtle border-[var(--lia-border-subtle)]"
                      style={{backgroundColor: isTemplateAdded(template) 
                          ? 'var(--lia-bg-tertiary)' 
                          : 'var(--lia-bg-primary)',
                        opacity: isTemplateAdded(template) ? 0.6 : 1}} /* dynamic */
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <p 
                            className="text-sm text-lia-text-primary"
                          >
                            {template.question}
                          </p>
                          <div className="flex flex-wrap items-center gap-2 mt-2">
                            <Chip variant="neutral" muted 
                              className="text-xs bg-[var(--lia-bg-tertiary)] text-lia-text-secondary border border-[var(--lia-border-subtle)]"
                            >
                              Bloom: {template.bloom_level}
                            </Chip>
                            <Chip variant="neutral" muted 
                              className="text-xs bg-[var(--lia-bg-tertiary)] text-lia-text-secondary border border-[var(--lia-border-subtle)]"
                            >
                              Dreyfus: {template.dreyfus_level}
                            </Chip>
                            <Chip 
                              variant="neutral" 
                              className="text-xs border-[var(--lia-border-default)] text-lia-text-tertiary"
                            >
                              {template.competency}
                            </Chip>
                            <span 
                              className="text-xs flex items-center gap-1 text-lia-text-tertiary"
                            >
                              <Clock className="h-3 w-3" />
                              {template.time_estimate}min
                            </span>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          className="shrink-0 dark:border-lia-border-default dark:hover:bg-lia-bg-inverse border-[var(--lia-border-default)]"
                          onClick={() => handleAddTemplate(template)}
                          disabled={isTemplateAdded(template)}
                          style={{color: isTemplateAdded(template) 
                              ? 'var(--lia-text-disabled)' 
                              : 'var(--lia-text-secondary)'}} /* dynamic */
                        >
                          {isTemplateAdded(template) ?"Adicionada" :"Adicionar"}
                        </Button>
                      </div>
                    </div>
                  ))}
                </TabsContent>
              ))}
            </Tabs>
          </div>
        )}
      </div>

      <div 
        className="border rounded-xl overflow-hidden dark:border-lia-border-subtle border-[var(--lia-border-subtle)]"
      >
        <div 
          className="p-4 bg-[var(--lia-bg-secondary)]"
        >
          <Label 
            className="text-sm font-medium flex items-center gap-2 mb-3 text-lia-text-primary"
          >
            <Plus className="h-4 w-4" />
            Adicionar Pergunta Manual
          </Label>
          <div className="space-y-4">
            <Textarea
              value={newQuestion.question}
              onChange={(e) => setNewQuestion((prev) => ({ ...prev, question: e.target.value }))}
              placeholder="Digite sua pergunta WSI personalizada..."
              rows={3}
              className="dark:bg-lia-bg-primary dark:border-lia-border-subtle border-[var(--lia-border-default)] bg-[var(--lia-bg-primary)] text-lia-text-primary"
            />
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="text-xs text-lia-text-secondary">
                  Nível Bloom
                </Label>
                <Select
                  value={newQuestion.bloom_level}
                  onValueChange={(v) => setNewQuestion((prev) => ({ ...prev, bloom_level: v as BloomLevel }))}
                >
                  <SelectTrigger 
                    className="h-8 text-xs dark:bg-lia-bg-primary dark:border-lia-border-subtle border-[var(--lia-border-default)] bg-[var(--lia-bg-primary)]"
                  >
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {BLOOM_OPTIONS.map((level) => (
                      <SelectItem key={level} value={level}>
                        {level}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-xs text-lia-text-secondary">
                  Nível Dreyfus
                </Label>
                <Select
                  value={newQuestion.dreyfus_level}
                  onValueChange={(v) => setNewQuestion((prev) => ({ ...prev, dreyfus_level: v as DreyfusLevel }))}
                >
                  <SelectTrigger 
                    className="h-8 text-xs dark:bg-lia-bg-primary dark:border-lia-border-subtle border-[var(--lia-border-default)] bg-[var(--lia-bg-primary)]"
                  >
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DREYFUS_OPTIONS.map((level) => (
                      <SelectItem key={level} value={level}>
                        {level}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="text-xs text-lia-text-secondary">
                  Competência
                </Label>
                <Input
                  value={newQuestion.competency}
                  onChange={(e) => setNewQuestion((prev) => ({ ...prev, competency: e.target.value }))}
                  placeholder="Ex: Resolução de Problemas"
                  className="h-8 text-xs dark:bg-lia-bg-primary dark:border-lia-border-subtle border-[var(--lia-border-default)] bg-[var(--lia-bg-primary)]"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs text-lia-text-secondary">
                  Tempo (min)
                </Label>
                <Input
                  type="number"
                  value={newQuestion.time_estimate}
                  onChange={(e) => setNewQuestion((prev) => ({ ...prev, time_estimate: parseInt(e.target.value) || 10 }))}
                  className="h-8 text-xs dark:bg-lia-bg-primary dark:border-lia-border-subtle border-[var(--lia-border-default)] bg-[var(--lia-bg-primary)]"
                  min={5}
                  max={60}
                />
              </div>
            </div>
            <Button
              onClick={handleAddCustomQuestion}
              disabled={!newQuestion.question.trim() || !newQuestion.competency.trim()}
              className="w-full dark:border-lia-border-default dark:hover:bg-lia-bg-inverse border-[var(--lia-border-default)] text-lia-text-primary"
              variant="outline"
            >
              <Plus className="h-4 w-4 mr-2" />
              Adicionar Pergunta
            </Button>
          </div>
        </div>
      </div>

      <Button
        onClick={handleSubmit}
        disabled={isLoading || questions.length === 0}
        className="w-full h-11 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
        size="lg"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none mr-2" />
            Salvando...
          </>
        ) : (
          `Confirmar ${questions.length} Pergunta${questions.length !== 1 ? 's' : ''}`
        )}
      </Button>
    </div>
  )
}

function QuestionCard({
  question,
  index,
  isExpanded,
  onToggleExpand,
  onUpdate,
  onRemove
}: {
  question: WSIQuestion
  index: number
  isExpanded: boolean
  onToggleExpand: () => void
  onUpdate: (field: keyof WSIQuestion, value: string | number) => void
  onRemove: () => void
}) {
  return (
    <div 
      className="border rounded-xl overflow-hidden dark:border-lia-border-subtle border-[var(--lia-border-subtle)]"
    >
      <button
        type="button"
        className="w-full text-left p-3 transition-colors motion-reduce:transition-none dark:hover:bg-lia-bg-inverse/50 bg-[var(--lia-bg-primary)]"
        onClick={onToggleExpand}
      >
        <div className="flex items-start gap-3">
          <div className="flex items-center gap-2 shrink-0">
            <span 
              className="text-xs font-medium text-lia-text-tertiary"
            >
              #{index + 1}
            </span>
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-lia-text-tertiary" />
            ) : (
              <ChevronRight className="h-4 w-4 text-lia-text-tertiary" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p 
              className="text-sm line-clamp-2 text-lia-text-primary"
            >
              {question.question}
            </p>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <Chip variant="neutral" muted 
                className="text-xs bg-[var(--lia-bg-tertiary)] text-lia-text-secondary border border-[var(--lia-border-subtle)]"
              >
                {question.bloom_level}
              </Chip>
              <Chip variant="neutral" muted 
                className="text-xs bg-[var(--lia-bg-tertiary)] text-lia-text-secondary border border-[var(--lia-border-subtle)]"
              >
                {question.dreyfus_level}
              </Chip>
              <Chip 
                variant="neutral" 
                className="text-xs border-[var(--lia-border-default)] text-lia-text-tertiary"
              >
                {question.competency}
              </Chip>
              <span 
                className="text-xs flex items-center gap-1 text-lia-text-tertiary"
              >
                <Clock className="h-3 w-3" />
                {question.time_estimate}min
              </span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 shrink-0 dark:hover:bg-lia-bg-inverse text-lia-text-tertiary"
            onClick={(e) => {
              e.stopPropagation()
              onRemove()
            }}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </button>

      {isExpanded && (
        <div 
          className="px-3 pb-3 pt-2 border-t space-y-3 dark:border-lia-border-subtle border-[var(--lia-border-subtle)] bg-[var(--lia-bg-tertiary)]"
        >
          <div className="space-y-2">
            <Label className="text-xs text-lia-text-secondary">
              Pergunta
            </Label>
            <Textarea
              value={question.question}
              onChange={(e) => onUpdate("question", e.target.value)}
              rows={3}
              className="text-sm dark:bg-lia-bg-primary dark:border-lia-border-subtle border-[var(--lia-border-default)] bg-[var(--lia-bg-primary)]"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label className="text-xs text-lia-text-secondary">
                Nível Bloom
              </Label>
              <Select
                value={question.bloom_level}
                onValueChange={(v) => onUpdate("bloom_level", v)}
              >
                <SelectTrigger 
                  className="h-8 text-xs dark:bg-lia-bg-primary dark:border-lia-border-subtle border-[var(--lia-border-default)] bg-[var(--lia-bg-primary)]"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {BLOOM_OPTIONS.map((level) => (
                    <SelectItem key={level} value={level}>
                      {level}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-xs text-lia-text-secondary">
                Nível Dreyfus
              </Label>
              <Select
                value={question.dreyfus_level}
                onValueChange={(v) => onUpdate("dreyfus_level", v)}
              >
                <SelectTrigger 
                  className="h-8 text-xs dark:bg-lia-bg-primary dark:border-lia-border-subtle border-[var(--lia-border-default)] bg-[var(--lia-bg-primary)]"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DREYFUS_OPTIONS.map((level) => (
                    <SelectItem key={level} value={level}>
                      {level}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label className="text-xs text-lia-text-secondary">
                Competência
              </Label>
              <Input
                value={question.competency}
                onChange={(e) => onUpdate("competency", e.target.value)}
                className="h-8 text-xs dark:bg-lia-bg-primary dark:border-lia-border-subtle border-[var(--lia-border-default)] bg-[var(--lia-bg-primary)]"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs text-lia-text-secondary">
                Tempo (min)
              </Label>
              <Input
                type="number"
                value={question.time_estimate || 10}
                onChange={(e) => onUpdate("time_estimate", parseInt(e.target.value) || 10)}
                className="h-8 text-xs dark:bg-lia-bg-primary dark:border-lia-border-subtle border-[var(--lia-border-default)] bg-[var(--lia-bg-primary)]"
                min={5}
                max={60}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
