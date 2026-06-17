"use client"

import React from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { ScrollArea } from"@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from"@/components/ui/select"
import {
  Brain, RefreshCw, Target, Loader2, AlertCircle,
  Zap, MessageCircle, Clock, Repeat, FileText, Mic, Bell,
  ArrowRight, AlertTriangle
} from"lucide-react"
import { cn } from"@/lib/utils"
import { AIDisclaimer } from"@/components/ui/ai-disclaimer"
import type { ScreeningQuestionsPanelProps } from"./ScreeningPanelConstants"
import { WSI_BLOCKS } from"./ScreeningPanelConstants"
import { useScreeningQuestionsPanel } from"./useScreeningQuestionsPanel"
import { ScreeningBlockSection, SuggestionCard } from"./ScreeningBlockSection"

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
    isLoading,
    error,
    qualityWarnings,
    blockDistribution,
    toggleQuestion,
    screeningModel,
    expandedBlocks,
    hasGenerated,
    setHasGenerated,
    selectedBlockForSuggestion,
    setSelectedBlockForSuggestion,
    isGeneratingMore,
    questionsByBlock,
    selectedCount,
    totalDuration,
    questionCountLabel,
    suggestionsForSelectedBlock,
    handleGenerateMoreForBlock,
    handleAddSuggestion,
    toggleBlock,
    handleModelChange,
  } = useScreeningQuestionsPanel({
    jobTitle, department, seniority, bigFiveProfile, skills,
    behavioralCompetencies, isAffirmative, affirmativeType, onQuestionsChange,
  })

  if (isLoading && !hasGenerated) {
    return (
      <Card className={cn("w-full", className)}>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-3" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="h-8 w-8 animate-spin motion-reduce:animate-none mx-auto text-lia-text-secondary" />
            <p className="text-xs text-lia-text-secondary">
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
            <Button variant="outline" size="sm" onClick={() => setHasGenerated(false)} className="text-xs">
              Tentar novamente
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  const editableBlocks = WSI_BLOCKS.filter(b => b.editable && b.id !== 2)

  const configItems = [
    { icon: MessageCircle, label: 'Canal', value: 'WhatsApp', sublabel: 'mensageria' },
    { icon: Clock, label: 'Duração', value: `~${totalDuration} min`, sublabel: 'tempo total' },
    { icon: Repeat, label: 'Tentativas', value: '3', sublabel: 'de contato' },
    { icon: FileText, label: 'Perguntas', value: questionCountLabel, sublabel: 'fixas + adaptativas' },
    { icon: Mic, label: 'Formato', value: 'Texto/Áudio', sublabel: 'resposta híbrida' },
    { icon: Bell, label: 'Feedback', value: '24 horas', sublabel: 'automático' }
  ]

  const distributionItems = Object.entries(blockDistribution).map(([key, count]) => {
    const blockNames: Record<string, string> = { '2': 'Empresa', '3': 'Técnico', '4': 'Situacional' }
    return { key, name: blockNames[key] || `Bloco ${key}`, count }
  }).filter(item => ['2', '3', '4'].includes(item.key))

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-wedo-cyan" />
            <CardTitle className="text-sm font-medium">Roteiro WSI de Triagem</CardTitle>
            <Chip variant="success" className="text-micro px-1.5 py-0 rounded-full">
              Ativo
            </Chip>
            <AIDisclaimer />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div
            className={cn("p-3 rounded-md border cursor-pointer transition-colors duration-200",
              screeningModel === 'compact' ?"border-lia-btn-primary-bg bg-lia-bg-secondary ring-1 ring-lia-btn-primary-bg/10" :"border-lia-border-subtle hover:border-lia-border-default"
            )}
            onClick={() => handleModelChange('compact')}
          >
            <div className="flex items-center gap-2 mb-1">
              <Zap className={cn("h-4 w-4", screeningModel === 'compact' ?"text-lia-text-primary" :"lia-text-secondary")} />
              <span className="text-xs font-medium text-lia-text-primary">Compacto</span>
            </div>
            <p className="text-xs text-lia-text-secondary">8 perguntas WSI • ~15 min</p>
            <p className="text-micro text-lia-text-secondary mt-0.5">Triagem rápida para alto volume</p>
          </div>
          <div
            className={cn("p-3 rounded-md border cursor-pointer transition-colors duration-200",
              screeningModel === 'full' ?"border-lia-btn-primary-bg bg-lia-bg-secondary ring-1 ring-lia-btn-primary-bg/10" :"border-lia-border-subtle hover:border-lia-border-default"
            )}
            onClick={() => handleModelChange('full')}
          >
            <div className="flex items-center gap-2 mb-1">
              <Target className={cn("h-4 w-4", screeningModel === 'full' ?"text-lia-text-primary" :"lia-text-secondary")} />
              <span className="text-xs font-medium text-lia-text-primary">Completo</span>
            </div>
            <p className="text-xs text-lia-text-secondary">12 perguntas WSI • ~30 min</p>
            <p className="text-micro text-lia-text-secondary mt-0.5">Avaliação aprofundada</p>
          </div>
        </div>

        {distributionItems.length > 0 && (
          <div className="mb-3">
            <p className="text-micro font-medium text-lia-text-secondary uppercase tracking-wide mb-1.5">Distribuição por Bloco</p>
            <div className="flex flex-wrap items-center gap-1.5">
              {distributionItems.map((item, idx) => (
                <React.Fragment key={item.key}>
                  {idx > 0 && <span className="lia-text-muted text-micro">|</span>}
                  <Chip variant="neutral" className="text-micro px-2 py-0.5 bg-lia-bg-secondary text-lia-text-secondary border-lia-border-subtle">
                    Bloco {item.key} · {item.name}: {item.count} {item.count === 1 ? 'pergunta' : 'perguntas'}
                  </Chip>
                </React.Fragment>
              ))}
            </div>
          </div>
        )}

        {qualityWarnings && qualityWarnings.length > 0 && (
          <div className="mb-3 space-y-1.5">
            {qualityWarnings.map((warning, idx) => (
              <div key={idx} className="flex items-start gap-2 p-2 bg-status-warning/10 border border-status-warning/30 rounded-xl">
                <AlertTriangle className="h-3.5 w-3.5 text-status-warning mt-0.5 flex-shrink-0" />
                <p className="text-micro text-status-warning">{warning}</p>
              </div>
            ))}
          </div>
        )}

        <div className="grid grid-cols-6 gap-2 mb-4 p-3 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
          {configItems.map((item, idx) => (
            <div key={idx} className="flex flex-col items-center text-center">
              <item.icon className="h-4 w-4 text-lia-text-secondary mb-1" />
              <span className="text-micro text-lia-text-secondary uppercase tracking-wide">{item.label}</span>
              <span className="text-xs font-semibold text-lia-text-primary">{item.value}</span>
              <span className="text-micro text-lia-text-secondary">{item.sublabel}</span>
            </div>
          ))}
        </div>

        <div className="flex gap-4">
          <div className="flex-1">
            <ScrollArea className="h-[420px] pr-2">
              <div className="space-y-2">
                {WSI_BLOCKS.map(block => (
                  <ScreeningBlockSection
                    key={block.id}
                    block={block}
                    questions={questionsByBlock[block.id] || []}
                    isExpanded={expandedBlocks[block.id]}
                    isAffirmative={isAffirmative}
                    onToggleBlock={toggleBlock}
                    onToggleQuestion={toggleQuestion}
                    onSelectBlockForSuggestion={setSelectedBlockForSuggestion}
                  />
                ))}
              </div>
            </ScrollArea>
          </div>

          <div className="w-[280px] space-y-3">
            <div className="relative">
              <input
                type="text"
                placeholder="Peça para a IA gerar mais perguntas..."
                className="w-full h-10 pl-3 pr-10 text-xs border border-lia-border-default rounded-xl focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:border-lia-btn-primary-bg"
              />
              <Button variant="ghost" size="sm" className="absolute right-1 top-1 h-8 w-8 p-0 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active rounded-md">
                <ArrowRight className="h-4 w-4 text-white" />
              </Button>
            </div>

            <div className="p-3 rounded-xl border bg-wedo-cyan/10 border-wedo-cyan/20">
              <div className="flex items-start gap-2">
                <Brain className="h-4 w-4 mt-0.5 flex-shrink-0 text-wedo-cyan" />
                <div>
                  <p className="text-xs font-medium text-lia-text-primary">Metodologia WSI</p>
                  <p className="text-micro text-lia-text-secondary leading-relaxed mt-0.5" aria-live="polite" aria-atomic="true">
                    A IA gera perguntas seguindo a metodologia WeDoTalent Skill Index,
                    calibrando complexidade conforme senioridade e skills da vaga.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Brain className="h-3.5 w-3.5 text-wedo-cyan" />
                  <span className="text-xs font-medium text-lia-text-secondary">Sugestões da LIA</span>
                </div>
              </div>

              <ScrollArea className="h-[240px]">
                <div className="space-y-2 pr-2">
                  {suggestionsForSelectedBlock.length > 0 ? (
                    suggestionsForSelectedBlock.map(q => <SuggestionCard key={q.id} question={q} onAdd={handleAddSuggestion} />)
                  ) : (
                    <div className="p-4 text-center">
                      <p className="text-xs text-lia-text-secondary">Todas as sugestões foram adicionadas ao roteiro</p>
                    </div>
                  )}
                </div>
              </ScrollArea>

              <div className="pt-2 border-t border-lia-border-subtle">
                <div className="flex items-center gap-2">
                  <Select value={String(selectedBlockForSuggestion)} onValueChange={(v) => setSelectedBlockForSuggestion(Number(v))}>
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
                  <Button variant="outline" size="sm" className="h-8 text-xs px-3" onClick={handleGenerateMoreForBlock} disabled={isGeneratingMore}>
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
          <div className="flex items-center gap-4 text-xs text-lia-text-secondary">
            <span>{selectedCount} pergunta(s) no roteiro</span>
            <span className="lia-text-secondary">|</span>
            <span>Blocos editáveis: 2, 3, 4, 5</span>
          </div>
          <Button variant="ghost" size="sm" className="h-7 text-xs text-lia-text-secondary">
            Fechar
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default ScreeningQuestionsPanel
