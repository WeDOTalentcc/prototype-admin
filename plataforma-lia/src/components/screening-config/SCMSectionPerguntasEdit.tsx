"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { toast } from 'sonner'
import {
  AlertTriangle, Archive, Brain, CheckCircle, CheckCircle2, ChevronDown,
  ChevronUp, Loader2, Play, X
} from"lucide-react"
import { WSI_BLOCKS, WSI_AUTOMATIC_MESSAGES, formatMessageWithVariables, getBloomComplexity, getEstimatedTime } from '@/components/jobs/jobsPageConstants'
import { CompanyBankQuestions } from './CompanyBankQuestions'
import { CompanyDefaultQuestions } from './CompanyDefaultQuestions'
import { CustomQuestions } from './CustomQuestions'
import { SCMQuestionDetailView } from './SCMQuestionDetail'
import type { ScreeningQuestionItem } from './SCMScreeningTypes'
import type { useScreeningConfigManagerCore } from"./hooks/useScreeningConfigManagerCore"

type Props = ReturnType<typeof useScreeningConfigManagerCore>

function getBloomLabelPTBR(level: string | number): string {
  const numLevel = typeof level === 'string' ? parseInt(level, 10) : level
  const labels: Record<number, string> = { 1: 'Conhecimento', 2: 'Compreensão', 3: 'Aplicação', 4: 'Análise', 5: 'Síntese', 6: 'Avaliação' }
  return labels[numLevel] || 'Aplicação'
}
function getDreyfusLabelPTBR(level: string | number): string {
  const key = String(level)
  const labels: Record<string, string> = { novice: 'Iniciante', advanced_beginner: 'Iniciante Avançado', competent: 'Competente', proficient: 'Proficiente', expert: 'Expert' }
  return labels[key] || key
}
function getBigFiveLabelPTBR(trait: string): string {
  const labels: Record<string, string> = { openness: 'Abertura', conscientiousness: 'Conscienciosidade', extraversion: 'Extroversão', agreeableness: 'Amabilidade', neuroticism: 'Neuroticismo' }
  return labels[trait] || trait
}

export function SCMSectionPerguntasEdit({
  job, onJobUpdate,
  acceptedQuestions, setAcceptedQuestions,
  companyQuestions, companyQuestionsLoading, companyQuestionsError, retryCompanyQuestions,
  disabledCompanyQIds,
  selectedBankQuestions, bankQuestionOverrides,
  customQuestions,
  deactivatedQuestions, setDeactivatedQuestions,
  expandedBlocks, setExpandedBlocks,
  expandedQuestionDetails, setExpandedQuestionDetails,
  generatedQuestions, setGeneratedQuestions,
  handleAddCustomQuestion, handleRemoveCustomQuestion, handleUpdateCustomQuestion,
  handleToggleBankQuestion, handleToggleCompanyDefault, handleUpdateBankQuestion,
  handleGenerateWSI, isGeneratingWSI,
  isEditingScreening, resetScreeningEditing,
  wsiDynamicMessage, wsiGeneratedCount, wsiGenerationCompleted, wsiGenerationContext,
  wsiGenerationMode, wsiGenerationStep, wsiProgressCollapsed, setWsiProgressCollapsed,
  wsiSummaryExpanded, setWsiSummaryExpanded,
  wsiSummaryTypedText, wsiSummaryTypingDone, wsiTypedMessage,
  setWsiDynamicMessage, setWsiGenerationCompleted, setWsiGenerationContext, setWsiGenerationStep,
}: Props) {
  const techSkillsCount = (Array.isArray(job?.technicalRequirements) ? job.technicalRequirements : []).filter(Boolean).length
  const behavCompCount = (Array.isArray(job?.behavioralCompetencies) ? job.behavioralCompetencies : []).filter(Boolean).length
  const showTechWarning = techSkillsCount < 9
  const showBehavWarning = behavCompCount < 5
  const showFullDisabled = techSkillsCount < 5

  return (
    <>
      {/* WSI Generation Controls */}
      <div className="px-5 py-3 border-t border-lia-border-subtle bg-lia-bg-secondary/30">
        {(showTechWarning || showBehavWarning) && (
          <div className="mb-3 rounded-xl border border-status-warning/30 bg-status-warning/10 dark:bg-status-warning/30 dark:border-status-warning/30 px-3 py-2.5">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-status-warning mt-0.5 shrink-0" />
              <div className="space-y-1">
                {showTechWarning && (
                  <p className="text-xs text-status-warning leading-relaxed">
                    {techSkillsCount === 0
                      ? 'Nenhuma competência técnica cadastrada — adicione competências na seção Job Description para gerar perguntas de triagem.'
                      : `Apenas ${techSkillsCount} competência${techSkillsCount === 1 ? '' : 's'} técnica${techSkillsCount === 1 ? '' : 's'} cadastrada${techSkillsCount === 1 ? '' : 's'}. Para triagem completa, recomendamos pelo menos 9.`
                    }
                  </p>
                )}
                {showBehavWarning && (
                  <p className="text-xs text-status-warning leading-relaxed">
                    {behavCompCount === 0
                      ? 'Nenhuma competência comportamental cadastrada — a triagem usará avaliação padrão.'
                      : `${behavCompCount} competência${behavCompCount === 1 ? '' : 's'} comportamental${behavCompCount === 1 ? '' : 's'} (recomendado: 5 para cobertura completa).`
                    }
                  </p>
                )}
                {showFullDisabled && (
                  <p className="text-micro text-status-warning italic">
                    Modo Completo requer pelo menos 5 competências técnicas.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
          <button onClick={handleGenerateWSI('compact')} disabled={isGeneratingWSI}
            className={`flex-1 flex items-center justify-center gap-2 px-3 py-1.5 rounded-md border transition-colors motion-reduce:transition-none disabled:opacity-50 ${wsiGenerationMode === 'compact' ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text border-lia-btn-primary-bg ring-2 ring-lia-btn-primary-bg/20 ring-offset-1' : 'bg-lia-bg-primary text-lia-text-primary border-lia-border-default hover:bg-lia-interactive-hover hover:border-lia-border-medium hover:bg-lia-interactive-hover'}`}>
            {isGeneratingWSI && wsiGenerationMode === 'compact' ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
            ) : (
              <>
                <span className="text-xs font-semibold">Gerar WSI Compacto</span>
                <span className={`text-micro ${wsiGenerationMode === 'compact' ? 'lia-text-secondary' : 'lia-text-secondary'}`}>~7 perguntas · 12 min</span>
              </>
            )}
          </button>
          <div className="relative flex-1 group/full">
            <button onClick={handleGenerateWSI('full')} disabled={isGeneratingWSI || techSkillsCount < 5}
              className={`w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-md border transition-colors motion-reduce:transition-none disabled:opacity-50 ${wsiGenerationMode === 'full' ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text border-lia-btn-primary-bg ring-2 ring-lia-btn-primary-bg/20 ring-offset-1' : 'bg-lia-bg-primary text-lia-text-primary border-lia-border-default hover:bg-lia-interactive-hover hover:border-lia-border-medium hover:bg-lia-interactive-hover'}`}>
              {isGeneratingWSI && wsiGenerationMode === 'full' ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
              ) : (
                <>
                  <span className="text-xs font-semibold">Gerar WSI Completo</span>
                  <span className={`text-micro ${wsiGenerationMode === 'full' ? 'lia-text-secondary' : 'lia-text-secondary'}`}>~12 perguntas · 22 min</span>
                </>
              )}
            </button>
            {techSkillsCount < 5 && (
              <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-52 p-2 bg-lia-btn-primary-bg text-lia-btn-primary-text text-micro rounded-md opacity-0 invisible group-hover/full:opacity-100 group-hover/full:visible transition-opacity motion-reduce:transition-none z-50 text-center">
                <p className="leading-relaxed">Adicione pelo menos 5 competências técnicas na seção Job Description para habilitar o modo Completo.</p>
                <div className="absolute top-full left-1/2 -translate-x-1/2 -translate-y-1/2 rotate-45 w-2 h-2 bg-lia-btn-primary-bg"></div>
              </div>
            )}
          </div>
          <div className="relative group">
            <Brain className="w-5 h-5 cursor-help text-wedo-cyan" />
            <div className="absolute right-full mr-2 top-1/2 -translate-y-1/2 w-64 p-3 bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity motion-reduce:transition-none z-50">
              <p className="leading-relaxed" aria-live="polite" aria-atomic="true">A LIA gera perguntas seguindo a metodologia WeDoTalent Skill Index, calibrando complexidade conforme senioridade e skills da vaga.</p>
              <div className="absolute top-1/2 right-0 translate-x-1/2 -translate-y-1/2 rotate-45 w-2 h-2 bg-lia-btn-primary-bg"></div>
            </div>
          </div>
        </div>

        {/* WSI Generation Progress */}
        {(isGeneratingWSI || wsiGenerationCompleted) && wsiGenerationStep > 0 && (
          <div className="mt-3 rounded-xl border border-lia-border-subtle bg-lia-bg-primary overflow-hidden" role="status" aria-live="polite" aria-label="Carregando...">
            <div className="flex items-center gap-3 px-5 py-3 cursor-pointer" onClick={() => setWsiProgressCollapsed(!wsiProgressCollapsed)}>
              <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0">
                {wsiGenerationStep < 4 ? (
                  <Loader2 className="w-5 h-5 text-lia-text-primary animate-spin motion-reduce:animate-none" />
                ) : (
                  <Brain className="w-5 h-5 text-wedo-cyan" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-base-ui font-semibold text-lia-text-primary">
                  {wsiGenerationStep < 4 ? 'Gerando Roteiro e Perguntas de Triagem...' : 'Roteiro e Perguntas de Triagem'}
                </p>
                <p className="text-xs text-lia-text-secondary mt-0.5">
                  {wsiGenerationStep < 4
                    ? `Analisando ${wsiGenerationMode === 'compact' ? 'modo compacto' : 'modo completo'}`
                    : `Status: ${wsiGeneratedCount} perguntas geradas · Metodologia WeDoTalent Skill Index (WSI) Completa`
                  }
                </p>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                {wsiGenerationStep >= 4 && (
                  <button onClick={(e) => { e.stopPropagation(); setWsiGenerationCompleted(false); setWsiGenerationStep(0); setWsiDynamicMessage(''); setWsiGenerationContext(null) }} className="p-1 hover:bg-lia-interactive-hover rounded-md transition-colors motion-reduce:transition-none">
                    <X className="w-3.5 h-3.5 text-lia-text-secondary" />
                  </button>
                )}
                {wsiProgressCollapsed ? <ChevronDown className="w-4 h-4 text-lia-text-secondary" /> : <ChevronUp className="w-4 h-4 text-lia-text-secondary" />}
              </div>
            </div>

            <div className="px-5 py-4">
              <div className="flex items-start">
                {[
                  { num: 1, label: 'Análise' },
                  { num: 2, label: 'Critérios' },
                  { num: 3, label: 'Metodologias' },
                  { num: 4, label: 'Resultado' },
                ].map((step, idx, arr) => (
                  <React.Fragment key={step.num}>
                    <div className="flex flex-col items-center">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center transition-[width,height] duration-500 ${
                        (wsiGenerationStep > step.num || (wsiGenerationStep === step.num && wsiGenerationCompleted))
                          ? 'text-white bg-wedo-cyan'
                          : wsiGenerationStep === step.num
                            ? 'border-2 bg-lia-bg-primary border-wedo-cyan'
                            : 'border border-lia-border-default bg-lia-bg-primary'
                      }`}>
                        {(wsiGenerationStep > step.num || (wsiGenerationStep === step.num && wsiGenerationCompleted)) ? (
                          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                        ) : wsiGenerationStep === step.num ? (
                          <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-wedo-cyan" />
                        ) : (
                          <span className="text-micro font-semibold text-lia-text-secondary">{step.num}</span>
                        )}
                      </div>
                      <span className={`text-micro mt-1.5 font-medium whitespace-nowrap transition-colors motion-reduce:transition-none duration-300 ${wsiGenerationStep >= step.num ? 'text-wedo-cyan-dark' : 'lia-text-secondary'}`}>
                        {step.label}
                      </span>
                    </div>
                    {idx < arr.length - 1 && (
                      <div className="flex-1 flex items-center">
                        <div className={`w-full h-0.5 rounded-full transition-[width,height] duration-700 ${wsiGenerationStep > step.num ? 'bg-wedo-cyan' : 'bg-lia-interactive-active'}`} />
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>

            {wsiGenerationStep < 4 && wsiTypedMessage && (
              <div className="px-5 pb-3 flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-lia-btn-primary-bg animate-pulse motion-reduce:animate-none" />
                <p className="text-base-ui text-lia-text-primary">
                  {wsiTypedMessage}
                  {wsiTypedMessage.length < wsiDynamicMessage.length && (
                    <span className="inline-block w-[2px] h-[14px] bg-lia-btn-primary-bg ml-0.5 align-middle animate-pulse motion-reduce:animate-none" />
                  )}
                </p>
              </div>
            )}

            {!wsiProgressCollapsed && (
              <div className="px-5 pb-4 pt-1 space-y-3 border-t border-lia-border-subtle">
                {wsiGenerationStep >= 1 && wsiGenerationContext && (
                  <div className="pt-2">
                    <p className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider mb-0.5">Cargo analisado</p>
                    <p className="text-xs text-lia-text-primary">
                      {wsiGenerationContext.title}{wsiGenerationContext.seniority ? <span className="text-lia-text-secondary"> · {wsiGenerationContext.seniority}</span> : ''}
                    </p>
                  </div>
                )}
                {wsiGenerationStep >= 2 && wsiGenerationContext && (
                  <div className="space-y-2">
                    {wsiGenerationContext.responsibilities.length > 0 && (
                      <div>
                        <p className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider mb-1">Responsabilidades Chave</p>
                        <div className="flex flex-wrap gap-1">
                          {wsiGenerationContext.responsibilities.map((resp: string, i: number) => (
                            <span key={`resp-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle rounded-full">
                              {resp.length > 35 ? resp.slice(0, 35) + '...' : resp}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {wsiGenerationContext.technicalSkills.length > 0 && (
                      <div>
                        <p className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider mb-1">Competências Técnicas</p>
                        <div className="flex flex-wrap gap-1">
                          {wsiGenerationContext.technicalSkills.map((skill: string, i: number) => (
                            <span key={`tech-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle rounded-full">{skill}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {wsiGenerationContext.behavioralCompetencies.length > 0 && (
                      <div>
                        <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider mb-1">Competências Comportamentais</p>
                        <div className="flex flex-wrap gap-1">
                          {wsiGenerationContext.behavioralCompetencies.map((comp: string, i: number) => (
                            <span key={`behav-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle rounded-full">{comp}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                {wsiGenerationStep >= 3 && (
                  <div>
                    <p className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider mb-1">Metodologias Utilizadas para Gerar Perguntas</p>
                    {wsiGenerationStep >= 4 && wsiGenerationContext?.methodologyBreakdown && Object.keys(wsiGenerationContext.methodologyBreakdown).length > 0 ? (
                      <p className="text-xs text-lia-text-secondary">
                        {Object.entries(wsiGenerationContext.methodologyBreakdown)
                          .filter(([key]) => key !== 'Dreyfus')
                          .map(([method, count]) => {
                            const labels: Record<string, string> = { 'CBI': 'CBI', 'Bloom': 'Bloom', 'BigFive': 'Big Five' }
                            return `${labels[method] || method} (${count as number})`
                          }).join(' · ')}
                        {wsiGenerationContext.methodologyBreakdown['Dreyfus'] ? ' · Dreyfus (calibração)' : ''}
                      </p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {['CBI', 'Bloom', 'Big Five', 'Dreyfus'].map(m => (
                          <span key={m} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle rounded-full">{m}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                {wsiGenerationStep >= 4 && wsiGenerationContext && (
                  <div className="space-y-4 pt-1">
                    <div>
                      <p className="text-base-ui text-lia-text-primary">
                        {wsiSummaryTypedText}
                        {!wsiSummaryTypingDone && <span className="inline-block w-[2px] h-[14px] bg-lia-btn-primary-bg ml-0.5 align-middle animate-pulse motion-reduce:animate-none" />}
                      </p>
                    </div>
                    {wsiSummaryTypingDone && (<>
                      <div className="space-y-1.5 pl-1">
                        {(wsiGenerationContext.blockBreakdown?.[2] || 0) > 0 && (
                          <div className="flex items-start gap-2"><span className="text-lia-text-disabled mt-0.5">•</span><p className="text-base-ui text-lia-text-primary"><span className="font-semibold">{wsiGenerationContext.blockBreakdown[2]} perguntas de elegibilidade</span>, para validar aderência mínima ao cargo</p></div>
                        )}
                        {(wsiGenerationContext.blockBreakdown?.[3] || 0) > 0 && (
                          <div className="flex items-start gap-2"><span className="text-lia-text-disabled mt-0.5">•</span><p className="text-base-ui text-lia-text-primary"><span className="font-semibold">{wsiGenerationContext.blockBreakdown[3]} perguntas técnicas</span>, para investigar o nível de conhecimento e experiência prática</p></div>
                        )}
                        {(wsiGenerationContext.blockBreakdown?.[4] || 0) > 0 && (
                          <div className="flex items-start gap-2"><span className="text-lia-text-disabled mt-0.5">•</span><p className="text-base-ui text-lia-text-primary"><span className="font-semibold">{wsiGenerationContext.blockBreakdown[4]} perguntas comportamentais</span>, para explorar as competências exigidas para a vaga</p></div>
                        )}
                      </div>
                      <div className="space-y-1">
                        <p className="text-base-ui text-lia-text-primary">Ao todo, a triagem será composta por <span className="font-semibold">{wsiGeneratedCount} perguntas</span>.</p>
                        <p className="text-base-ui text-lia-text-primary">O tempo médio estimado de triagem é de <span className="font-semibold">15 a 20 minutos</span>, considerando o tempo de leitura e resposta do candidato.</p>
                      </div>
                      {!wsiSummaryExpanded ? (
                        <button onClick={() => setWsiSummaryExpanded(true)} className="flex items-center gap-1.5 text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none">
                          <ChevronDown className="w-3.5 h-3.5" />Ver detalhes completos
                        </button>
                      ) : (
                        <>
                          <div><p className="text-base-ui font-semibold text-lia-text-primary mb-1">Próximo passo</p><p className="text-base-ui text-lia-text-primary">Selecione as perguntas em cada um dos blocos abaixo.</p></div>
                          <div className="space-y-1.5">
                            <p className="text-base-ui text-lia-text-primary">As perguntas foram geradas com base na metodologia <span className="font-semibold text-lia-text-primary">WeDoTalent Skill Index</span>, considerando:</p>
                            <div className="space-y-0.5 pl-1">
                              <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">•</span><p className="text-base-ui text-lia-text-secondary">Senioridade do cargo</p></div>
                              <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">•</span><p className="text-base-ui text-lia-text-secondary">Responsabilidades e competências mapeadas</p></div>
                              <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">•</span><p className="text-base-ui text-lia-text-secondary">Metodologias de avaliação (CBI, Bloom, Big Five e Dreyfus)</p></div>
                            </div>
                          </div>
                          <p className="text-base-ui text-lia-text-secondary" aria-live="polite" aria-atomic="true">As perguntas estão organizadas em ordem de prioridade, mas você pode escolher aquelas que julgar mais adequadas ao contexto da vaga.</p>
                          <p className="text-base-ui text-lia-text-primary font-semibold">Caso deseje perguntas adicionais, utilize a opção de adicionar perguntas personalizadas manualmente em cada bloco.</p>
                          <div className="border-t border-lia-border-subtle pt-3">
                            <p className="text-base-ui font-semibold text-lia-text-primary mb-1.5">Finalização</p>
                            <p className="text-base-ui text-lia-text-primary mb-1">Após concluir a seleção das perguntas:</p>
                            <div className="space-y-0.5 pl-1">
                              <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">1.</span><p className="text-base-ui text-lia-text-secondary">Salve as alterações</p></div>
                              <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">2.</span><p className="text-base-ui text-lia-text-secondary">Inicie o disparo da triagem</p></div>
                              <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">3.</span><p className="text-base-ui text-lia-text-secondary" aria-live="polite" aria-atomic="true">A LIA realizará a avaliação inicial e sinalizará os candidatos aprovados para a próxima etapa</p></div>
                            </div>
                          </div>
                          {wsiGenerationContext.companyStandardFound && (
                            <div className="flex items-center gap-1.5 pt-1">
                              <CheckCircle2 className="w-3.5 h-3.5 text-status-success" />
                              <span className="text-xs text-lia-text-secondary">Perguntas padrão da empresa incluídas</span>
                            </div>
                          )}
                          <button onClick={() => setWsiSummaryExpanded(false)} className="flex items-center gap-1.5 text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none pt-1">
                            <ChevronUp className="w-3.5 h-3.5" />Recolher detalhes
                          </button>
                        </>
                      )}
                    </>)}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* WSI Blocks Accordion */}
      <div className="px-5 py-5 overflow-y-auto">
        <div className="space-y-3">
          {WSI_BLOCKS.map((block) => {
            const isExpanded = (expandedBlocks as (string | number)[]).includes(block.id)
            const allQuestions = job.screeningQuestions || []
            const cat = (q: ScreeningQuestionItem) => (q.category || '').toLowerCase()
            const typ = (q: ScreeningQuestionItem) => (q.type || '').toLowerCase()
            const isBlock2 = (q: ScreeningQuestionItem) => {
              if (typ(q) === 'eliminatory' || q.required) return true
              if (cat(q).includes('elegib') || cat(q).includes('elimin')) return true
              if (cat(q).includes('fit') && cat(q).includes('básico')) return true
              if (cat(q).includes('disponib') || cat(q).includes('eligib')) return true
              if (cat(q).includes('experiência') || cat(q).includes('experiencia')) return true
              return false
            }
            const isBlock3 = (q: ScreeningQuestionItem) => {
              if (isBlock2(q)) return false
              return cat(q).includes('tecn') || cat(q).includes('tech') || cat(q).includes('skill') || cat(q).includes('técnica') || typ(q).includes('tech')
            }
            const isBlock4 = (q: ScreeningQuestionItem) => isBlock2(q) || isBlock3(q) ? false : true
            const blockQuestions = (Array.isArray(allQuestions) ? allQuestions : []).filter((q: ScreeningQuestionItem) => {
              if (q.block_id !== undefined && q.block_id !== null) return q.block_id === block.id
              if (block.id === 2) return isBlock2(q)
              if (block.id === 3) return isBlock3(q)
              if (block.id === 4) return isBlock4(q)
              return false
            })
            const blockGenerated = generatedQuestions[block.id as number] || []
            const acceptedCountForBlock = blockGenerated.filter((q: ScreeningQuestionItem) => acceptedQuestions.has(q.id)).length
            const eliminatoryCount = blockQuestions.filter((q: ScreeningQuestionItem) => q.type === 'eliminatory' || q.required).length
            const informativeCount = blockQuestions.length - eliminatoryCount

            return (
              <div key={block.id} className={`border rounded-md overflow-hidden ${block.editable ? 'border-lia-border-subtle' : 'border-lia-border-subtle bg-lia-bg-secondary/50/30'}`}>
                <div className={`flex items-center justify-between p-3 cursor-pointer transition-colors motion-reduce:transition-none ${block.editable ? 'bg-lia-bg-secondary hover:bg-lia-bg-tertiary hover:bg-lia-interactive-hover' : 'bg-lia-bg-tertiary/80/50'}`}
                  onClick={() => setExpandedBlocks(((prev: number[]) => isExpanded ? prev.filter(id => id !== block.id) : [...prev, block.id as number]) as any)}>
                  <div className="flex items-center gap-2">
                    <span className={`w-6 h-6 rounded-full text-white text-xs font-bold flex items-center justify-center ${block.editable ? 'bg-lia-btn-primary-bg' : 'bg-lia-border-medium'}`}>{block.id}</span>
                    <div>
                      <span className={`text-xs font-semibold ${block.editable ? 'text-lia-text-primary' : 'text-lia-text-primary'}`}>{block.name}</span>
                      <span className="text-micro text-lia-text-secondary ml-2">({block.duration})</span>
                    </div>
                    {!block.editable && <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-interactive-active text-lia-text-secondary ml-1">Automático</Chip>}
                  </div>
                  <div className="flex items-center gap-2">
                    {block.editable && blockQuestions.length > 0 && (
                      <>
                        {eliminatoryCount > 0 && <Chip variant="danger" muted className="text-micro px-2 py-0.5">{eliminatoryCount} Eliminatória{eliminatoryCount > 1 ? 's' : ''}</Chip>}
                        {informativeCount > 0 && <Chip variant="neutral" muted className="text-micro px-2 py-0.5 bg-lia-bg-tertiary text-lia-text-primary">{informativeCount} Informativa{informativeCount > 1 ? 's' : ''}</Chip>}
                      </>
                    )}
                    {blockGenerated.length > 0 && (
                      <>
                        <Chip variant="neutral" muted className="text-micro px-2 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle">{acceptedCountForBlock}/{blockGenerated.length} aceitas</Chip>
                        {acceptedCountForBlock < blockGenerated.length && <span className="w-2 h-2 rounded-full bg-status-warning animate-pulse motion-reduce:animate-none"></span>}
                      </>
                    )}
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-lia-text-secondary" /> : <ChevronDown className="w-4 h-4 text-lia-text-secondary" />}
                  </div>
                </div>

                {isExpanded && (
                  <div className={`p-3 space-y-2 ${!block.editable ? 'bg-lia-bg-secondary/30' : ''}`}>
                    {!block.editable ? (
                      WSI_AUTOMATIC_MESSAGES[block.id as number] ? (
                        <div className="rounded-xl border border-lia-border-default bg-lia-bg-secondary/50 overflow-hidden">
                          <div className="px-3 py-2 bg-lia-bg-tertiary">
                            <p className="text-xs font-medium text-lia-text-primary">{WSI_AUTOMATIC_MESSAGES[block.id as number].title}</p>
                          </div>
                          <div className="p-3">
                            <div className="text-xs text-lia-text-primary leading-relaxed whitespace-pre-line">{formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id as number].message)}</div>
                          </div>
                          <div className="px-3 py-2 border-t border-lia-border-subtle bg-lia-bg-secondary/50">
                            <p className="text-micro text-lia-text-secondary italic">{WSI_AUTOMATIC_MESSAGES[block.id as number].note}</p>
                          </div>
                        </div>
                      ) : (
                        <div className="p-3 bg-lia-bg-primary/60 border border-lia-border-subtle rounded-xl">
                          <p className="text-xs text-lia-text-primary italic">{block.description}</p>
                          <p className="text-micro text-lia-text-secondary mt-1">Este bloco é gerenciado automaticamente pela LIA</p>
                        </div>
                      )
                    ) : (
                      <>
                        {block.id === 2 && (
                          <div className="space-y-4 mb-3">
                            {companyQuestionsError ? (
                              <div className="border border-status-warning/30 bg-status-warning/10 rounded-xl px-4 py-3 flex items-start gap-3">
                                <AlertTriangle className="w-4 h-4 text-status-warning mt-0.5 shrink-0" />
                                <div className="flex-1">
                                  <p className="text-xs text-status-warning leading-relaxed">{companyQuestionsError}</p>
                                  <button
                                    type="button"
                                    onClick={retryCompanyQuestions}
                                    disabled={companyQuestionsLoading}
                                    className="mt-1 text-xs font-semibold text-status-warning hover:underline disabled:opacity-50"
                                  >
                                    {companyQuestionsLoading ? 'Carregando...' : 'Tentar novamente'}
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <CompanyDefaultQuestions questions={companyQuestions} disabledIds={disabledCompanyQIds} isEditing={true} onToggle={handleToggleCompanyDefault} />
                            )}
                            <div className="border-t border-lia-border-subtle" />
                            <CompanyBankQuestions isEditing={true} selectedQuestions={selectedBankQuestions} questionOverrides={bankQuestionOverrides} onToggleQuestion={handleToggleBankQuestion} onUpdateSelectedQuestion={handleUpdateBankQuestion} excludeIds={companyQuestions.map(q => q.id)} />
                            <div className="border-t border-lia-border-subtle" />
                            <CustomQuestions isEditing={true} questions={customQuestions} onAddQuestion={handleAddCustomQuestion} onRemoveQuestion={handleRemoveCustomQuestion} onUpdateQuestion={handleUpdateCustomQuestion} />
                          </div>
                        )}
                        {blockQuestions.length === 0 && blockGenerated.length === 0 && block.id !== 2 ? (
                          <div className="p-4 bg-lia-bg-secondary/50 border border-lia-border-subtle border-dashed rounded-xl text-center">
                            <p className="text-xs text-lia-text-secondary">Nenhuma pergunta neste bloco</p>
                          </div>
                        ) : block.id !== 2 || blockQuestions.length > 0 || blockGenerated.length > 0 ? (
                          <>
                            {blockQuestions.map((item: ScreeningQuestionItem, idx: number) => {
                              const isDeactivated = deactivatedQuestions.has(item.id)
                              const isDetailsExpanded = expandedQuestionDetails.has(item.id)
                              return (
                                <div key={item.id || idx} className={`p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md group hover:border-lia-border-default transition-colors motion-reduce:transition-none ${isDeactivated ? 'opacity-50' : ''}`}>
                                  <div className="flex items-start gap-3">
                                    <SCMQuestionDetailView
                                      item={item}
                                      isDetailsExpanded={isDetailsExpanded}
                                      onToggleDetails={(id) => setExpandedQuestionDetails(prev => { const next = new Set(prev); if (next.has(id)) { next.delete(id) } else { next.add(id) } return next })}
                                      helpers={{ getBloomComplexity, getBloomLabelPTBR, getDreyfusLabelPTBR, getBigFiveLabelPTBR, getEstimatedTime }}
                                    />
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none shrink-0">
                                      {isDeactivated ? (
                                        <Chip variant="neutral" muted className="text-micro px-2 py-0.5 h-5 rounded-full bg-lia-bg-tertiary text-lia-text-tertiary border border-lia-border-subtle">Inativa</Chip>
                                      ) : (
                                        <Chip variant="success" muted className="text-micro px-2 py-0.5 h-5 rounded-full dark:bg-status-success/20">
                                          <CheckCircle className="w-3 h-3 mr-1" />Aceita
                                        </Chip>
                                      )}
                                    </div>
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                                      <button className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${isDeactivated ? 'hover:bg-status-success/10' : 'hover:bg-lia-interactive-hover'}`}
                                        onClick={() => {
                                          setDeactivatedQuestions(prev => {
                                            const next = new Set(prev)
                                            if (next.has(item.id)) { next.delete(item.id); toast.success('Pergunta reativada') } else { next.add(item.id); toast.success('Pergunta arquivada') }
                                            return next
                                          })
                                        }}
                                        title={isDeactivated ? 'Reativar pergunta' : 'Arquivar pergunta'}>
                                        <Archive className={`w-3.5 h-3.5 ${isDeactivated ? 'text-status-success' : 'lia-text-secondary'}`} />
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              )
                            })}
                            {blockGenerated.map((item: ScreeningQuestionItem, idx: number) => {
                              const isAccepted = acceptedQuestions.has(item.id)
                              const genDetailsExpanded = expandedQuestionDetails.has(item.id)
                              return (
                                <div key={item.id || `gen-${idx}`} className={`p-3 rounded-md transition-colors motion-reduce:transition-none ${isAccepted ? 'bg-lia-bg-secondary border border-lia-border-default' : 'bg-lia-bg-primary border border-dashed border-lia-border-default'}`}>
                                  <div className="flex items-start gap-3">
                                    <SCMQuestionDetailView
                                      item={item}
                                      isDetailsExpanded={genDetailsExpanded}
                                      onToggleDetails={(id) => setExpandedQuestionDetails(prev => { const next = new Set(prev); if (next.has(id)) { next.delete(id) } else { next.add(id) } return next })}
                                      helpers={{ getBloomComplexity, getBloomLabelPTBR, getDreyfusLabelPTBR, getBigFiveLabelPTBR, getEstimatedTime }}
                                    />
                                    <div className="flex items-center gap-1.5 shrink-0">
                                      {isAccepted ? (
                                        <button className="border border-lia-border-subtle text-lia-text-secondary text-micro px-2 py-1 rounded-full hover:bg-status-error/10 transition-colors motion-reduce:transition-none" onClick={() => {
                                          if (confirm('Remover pergunta aceita?')) {
                                            setAcceptedQuestions(prev => { const next = new Set(prev); next.delete(item.id); return next })
                                            setGeneratedQuestions(prev => ({ ...prev, [block.id]: (prev[block.id as number] || []).filter((q: ScreeningQuestionItem) => q.id !== item.id) }))
                                          }
                                        }}>Remover</button>
                                      ) : (
                                        <>
                                          <button className="bg-lia-btn-primary-bg text-lia-btn-primary-text text-micro px-2 py-1 rounded-full hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none" onClick={() => setAcceptedQuestions(prev => new Set(prev).add(item.id))}>Aceitar</button>
                                          <button className="border border-lia-border-subtle text-lia-text-secondary text-micro px-2 py-1 rounded-full hover:bg-status-error/10 transition-colors motion-reduce:transition-none" onClick={() => setGeneratedQuestions(prev => ({ ...prev, [block.id]: (prev[block.id as number] || []).filter((q: ScreeningQuestionItem) => q.id !== item.id) }))}>Descartar</button>
                                        </>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              )
                            })}
                          </>
                        ) : null}
                      </>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Save/Cancel buttons */}
      <div className="flex items-center justify-between px-5 py-3 border-t border-lia-border-subtle">
        <Button variant="outline" size="sm" className="h-7 text-micro px-3 border-lia-border-subtle text-lia-text-secondary" onClick={resetScreeningEditing}>
          Cancelar
        </Button>
        <div className="flex items-center gap-2">
          <Button size="sm" className="h-7 text-micro px-4 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text" onClick={async () => {
            const screeningQs = Array.isArray(job.screeningQuestions) ? job.screeningQuestions : []
            const existingCount = screeningQs.length
            const acceptedCount = Object.values(generatedQuestions).flat().filter((q: ScreeningQuestionItem) => acceptedQuestions.has(q.id)).length
            const totalQuestions = existingCount + acceptedCount
            if (totalQuestions === 0) { toast.error('Selecione pelo menos uma pergunta antes de salvar o roteiro.'); return }
            if (totalQuestions < 3) { toast.error('O roteiro precisa ter no mínimo 3 perguntas. Atualmente: ' + totalQuestions); return }
            try {
              const jobId = job.backendId || job.jobId || String(job.id)
              const existingQuestions = screeningQs.map((q: ScreeningQuestionItem) => ({ id: q.id, text: q.question || q.text, category: q.category, type: q.type, weight: q.weight, skill_targeted: q.skill_targeted, block_id: q.block_id }))
              const acceptedGenerated: ScreeningQuestionItem[] = []
              Object.values(generatedQuestions).forEach((blockQs: ScreeningQuestionItem[]) => {
                blockQs.forEach((q: ScreeningQuestionItem) => { if (acceptedQuestions.has(q.id)) { acceptedGenerated.push({ id: q.id, text: q.question || q.text, category: q.category, type: q.type, weight: q.weight || 0.75, skill_targeted: q.skill_targeted, block_id: q.block_id }) } })
              })
              const allQuestions = [...existingQuestions, ...acceptedGenerated]
              const response = await fetch('/api/backend-proxy/wsi/questions/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ job_id: jobId, questions: allQuestions, source: 'manual_save' }) })
              if (response.ok) {
                const newScreeningQuestions = [...screeningQs, ...Object.values(generatedQuestions).flat().filter((q: ScreeningQuestionItem) => acceptedQuestions.has(q.id)).map((q: ScreeningQuestionItem) => ({ ...q, question: q.question || q.text, generated: undefined }))]
                onJobUpdate?.({ ...job, screeningQuestions: newScreeningQuestions })
                toast.success(`Roteiro salvo com sucesso! ${allQuestions.length} perguntas salvas.`)
                resetScreeningEditing()
              } else { toast.error('Erro ao salvar roteiro. Tente novamente.') }
            } catch { toast.error('Erro ao salvar roteiro. Tente novamente.') }
          }}>
            <CheckCircle className="w-3 h-3 mr-1" />Salvar Alterações
          </Button>
          {(job.screeningStatus !== 'active') && (
            <Button size="sm" className="h-7 text-micro px-4 bg-status-success hover:bg-status-success text-white" onClick={async () => {
              const screeningQs2 = Array.isArray(job.screeningQuestions) ? job.screeningQuestions : []
              const existingCount = screeningQs2.length
              const acceptedCount = Object.values(generatedQuestions).flat().filter((q: ScreeningQuestionItem) => acceptedQuestions.has(q.id)).length
              const totalQuestions = existingCount + acceptedCount
              if (totalQuestions === 0) { toast.error('Selecione pelo menos uma pergunta antes de ativar a triagem.'); return }
              if (totalQuestions < 3) { toast.error('O roteiro precisa ter no mínimo 3 perguntas para ativar. Atualmente: ' + totalQuestions); return }
              try {
                const jobId = job.backendId || job.jobId || String(job.id)
                const existingQuestions = screeningQs2.map((q: ScreeningQuestionItem) => ({ id: q.id, text: q.question || q.text, category: q.category, type: q.type, weight: q.weight, skill_targeted: q.skill_targeted, block_id: q.block_id }))
                const acceptedGenerated: ScreeningQuestionItem[] = []
                Object.values(generatedQuestions).forEach((blockQs: ScreeningQuestionItem[]) => {
                  blockQs.forEach((q: ScreeningQuestionItem) => { if (acceptedQuestions.has(q.id)) { acceptedGenerated.push({ id: q.id, text: q.question || q.text, category: q.category, type: q.type, weight: q.weight || 0.75, skill_targeted: q.skill_targeted, block_id: q.block_id }) } })
                })
                const allQuestions = [...existingQuestions, ...acceptedGenerated]
                const response = await fetch('/api/backend-proxy/wsi/questions/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ job_id: jobId, questions: allQuestions, source: 'manual_save' }) })
                if (response.ok) {
                  const newScreeningQuestions = [...screeningQs2, ...Object.values(generatedQuestions).flat().filter((q: ScreeningQuestionItem) => acceptedQuestions.has(q.id)).map((q: ScreeningQuestionItem) => ({ ...q, question: q.question || q.text, generated: undefined }))]
                  onJobUpdate?.({ ...job, screeningQuestions: newScreeningQuestions, screeningStatus: 'active' })
                  toast.success(`Roteiro salvo e triagem ativada! ${allQuestions.length} perguntas configuradas.`)
                  resetScreeningEditing()
                } else { toast.error('Erro ao salvar roteiro. Tente novamente.') }
              } catch { toast.error('Erro ao salvar roteiro. Tente novamente.') }
            }}>
              <Play className="w-3 h-3 mr-1" />Salvar e Ativar
            </Button>
          )}
        </div>
      </div>
    </>
  )
}
