"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import {
  Calendar, Clock, MapPin, DollarSign, Heart, Shield, Building, Lock, Globe,
  ChevronRight, ClipboardList, Lightbulb,
  Brain, CheckCircle, Target, BarChart3,
  FileText, Layers3, CalendarCheck, Settings, MessageSquare, Phone,
  ChevronDown, ChevronUp
} from "lucide-react"
import { type Job } from "@/components/jobs"
import { type ScreeningConfig } from "@/hooks/useScreeningConfig"
import { WSI_BLOCKS, WSI_AUTOMATIC_MESSAGES, formatMessageWithVariables } from "@/components/jobs/jobsPageConstants"
import {
  type TechnicalRequirement,
  type BehavioralCompetency,
  type Requirement,
  type Benefit,
  type InterviewStage,
  type Language,
  type ScreeningQuestion,
} from "../job-preview.types"

interface JobScreeningSectionProps {
  previewJob: Job
  screeningConfig: ScreeningConfig | undefined
  isLoadingScreeningConfig: boolean
  collapsedPreviewSections: string[]
  expandedBlocks: number[]
  onToggleSection: (section: string) => void
  onToggleBlock: (blockId: number) => void
}

export function JobScreeningSection({
  previewJob,
  screeningConfig,
  isLoadingScreeningConfig,
  collapsedPreviewSections,
  expandedBlocks,
  onToggleSection,
  onToggleBlock,
}: JobScreeningSectionProps) {
  return (
                    <div className="space-y-4">
                      {/* Loading State Guard */}
                      {isLoadingScreeningConfig ? (
                        <div className="space-y-4">
                          {/* Skeleton for Performance Card */}
                          <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
                            <div className="h-4 bg-lia-interactive-active rounded-md w-32 mb-3"></div>
                            <div className="grid grid-cols-4 gap-2">
                              {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="text-center">
                                  <div className="h-6 bg-lia-interactive-active rounded-md mb-1"></div>
                                  <div className="h-3 bg-lia-bg-tertiary rounded-md w-12 mx-auto"></div>
                                </div>
                              ))}
                            </div>
                            <div className="grid grid-cols-4 gap-2 mt-2 pt-2 border-t border-lia-border-subtle">
                              {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="text-center">
                                  <div className="h-6 bg-lia-interactive-active rounded-md mb-1"></div>
                                  <div className="h-3 bg-lia-bg-tertiary rounded-md w-12 mx-auto"></div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Skeleton for Skills Card */}
                          <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
                            <div className="h-4 bg-lia-interactive-active rounded-md w-32 mb-3"></div>
                            <div className="flex flex-wrap gap-1.5">
                              {[1, 2, 3, 4, 5, 6].map((i) => (
                                <div key={i} className="h-6 bg-lia-interactive-active rounded-md px-2 w-24"></div>
                              ))}
                            </div>
                          </div>

                          {/* Skeleton for Questions Card */}
                          <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
                            <div className="h-4 bg-lia-interactive-active rounded-md w-40 mb-3"></div>
                            <div className="space-y-3">
                              {[1, 2, 3].map((i) => (
                                <div key={i} className="p-2 bg-lia-bg-secondary rounded-md border border-lia-border-subtle">
                                  <div className="h-4 bg-lia-interactive-active rounded-md w-3/4 mb-2"></div>
                                  <div className="h-3 bg-lia-bg-tertiary rounded-md w-1/2"></div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-4">
                      {/* 4. Descrição da Vaga */}
                      {previewJob.description && (
                        <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
                          <div className="flex items-center justify-between cursor-pointer" onClick={() => onToggleSection('descricao')}>
                            <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                              <FileText className="w-3.5 h-3.5 text-lia-text-secondary" />
                              Descrição da Vaga
                            </h5>
                            {collapsedPreviewSections.includes('descricao') ? (
                              <ChevronDown className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                            ) : (
                              <ChevronUp className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                            )}
                          </div>
                          {!collapsedPreviewSections.includes('descricao') && (
                            <p className="text-micro text-lia-text-secondary leading-relaxed whitespace-pre-line line-clamp-6 mt-2">
                              {previewJob.description}
                            </p>
                          )}
                        </div>
                      )}

                      {/* 3. Competências Avaliadas */}
                      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => onToggleSection('competencias')}>
                          <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                            Competências Avaliadas
                          </h5>
                          {collapsedPreviewSections.includes('competencias') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('competencias') && (<>
                        {(() => {
                          // @ts-ignore TODO: fix type
                          const technicalSkills = (previewJob.technicalRequirements || [] as TechnicalRequirement[]).map((tr: TechnicalRequirement) => typeof tr === 'string' ? tr : tr.technology || tr.name).filter(Boolean)
                          // @ts-ignore TODO: fix type
                          const behavioralSkills = (previewJob.behavioralCompetencies || [] as BehavioralCompetency[]).map((bc: BehavioralCompetency) => typeof bc === 'string' ? bc : bc.competency || bc.name).filter(Boolean)
                          const responsibilitySkills = (previewJob.requirements || [] as Requirement[]).map((r: Requirement) => typeof r === 'string' ? r : r.requirement || r.text || r.name).filter(Boolean)
                          const hasData = technicalSkills.length > 0 || behavioralSkills.length > 0 || responsibilitySkills.length > 0

                          if (!hasData) {
                            const fallbackSkills = screeningConfig?.wsi_skills || ['Comunicação', 'Resolução de Problemas', 'Adaptabilidade', 'Trabalho em Equipe']
                            return (
                              <div className="flex flex-wrap gap-1.5">
                                {fallbackSkills.slice(0, 6).map((skill: string) => (
                                  <Badge key={skill} className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary text-[0.625rem] leading-none px-1.5 py-0.5 font-medium">
                                    {skill}
                                  </Badge>
                                ))}
                              </div>
                            )
                          }

                          return (
                            <div className="space-y-2">
                              {technicalSkills.length > 0 && (
                                <div>
                                  <span className="text-micro font-medium text-lia-text-tertiary uppercase tracking-wide">Técnicas</span>
                                  <div className="flex flex-wrap gap-1.5 mt-1">
                                    {(technicalSkills as string[]).map((skill: string) => (
                                      <Badge key={skill} className="bg-wedo-cyan/10 dark:bg-wedo-cyan/30 text-wedo-cyan-dark dark:text-wedo-cyan-dark text-[0.625rem] leading-none px-1.5 py-0.5 font-medium border border-wedo-cyan/30">
                                        {skill}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {behavioralSkills.length > 0 && (
                                <div>
                                  <span className="text-micro font-medium text-lia-text-tertiary uppercase tracking-wide">Comportamentais</span>
                                  <div className="flex flex-wrap gap-1.5 mt-1">
                                    {(behavioralSkills as string[]).map((skill: string) => (
                                      <Badge key={skill} className="bg-wedo-purple/10 dark:bg-wedo-purple/30 text-wedo-purple dark:text-wedo-purple text-[0.625rem] leading-none px-1.5 py-0.5 font-medium border border-wedo-purple/30">
                                        {skill}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {responsibilitySkills.length > 0 && (
                                <div>
                                  <span className="text-micro font-medium text-lia-text-tertiary uppercase tracking-wide">Responsabilidades</span>
                                  <div className="flex flex-wrap gap-1.5 mt-1">
                                    {(responsibilitySkills as string[]).slice(0, 8).map((skill: string) => (
                                      <Badge key={skill} className="bg-status-warning/10 dark:bg-status-warning/30 text-status-warning dark:text-status-warning text-[0.625rem] leading-none px-1.5 py-0.5 font-medium border border-status-warning/30">
                                        {skill}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })()}
                        <p className="text-micro text-lia-text-disabled mt-2 flex items-center gap-1">
                          <Lightbulb className="w-3 h-3" />
                          Extraídas automaticamente do perfil da vaga via metodologia WSI
                        </p>
                        </>)}
                      </div>

                      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => onToggleSection('idiomas')}>
                          <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                            <Globe className="w-3.5 h-3.5 text-lia-text-secondary" />
                            Idiomas
                          </h5>
                          {collapsedPreviewSections.includes('idiomas') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('idiomas') && (
                          previewJob.languages && previewJob.languages.length > 0 ? (
                            <div className="space-y-1.5 mt-2">
                              {(previewJob.languages as Language[]).map((lang: Language, idx: number) => (
                                <div key={`lang-${idx}`} className="flex items-center gap-2">
                                  <span className="text-micro text-lia-text-secondary font-medium">
                                    {lang.language}
                                  </span>
                                  {lang.level && (
                                    <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-primary">
                                      {lang.level}
                                    </Badge>
                                  )}
                                  {lang.required && (
                                    <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-status-error/10 text-status-error border border-status-error/30">
                                      Obrigatório
                                    </Badge>
                                  )}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-micro text-lia-text-tertiary italic mt-2">
                              Nenhum idioma configurado
                            </p>
                          )
                        )}
                      </div>

                      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => onToggleSection('remuneracao')}>
                          <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                            <DollarSign className="w-3.5 h-3.5 text-lia-text-secondary" />
                            Remuneração e Benefícios
                          </h5>
                          {collapsedPreviewSections.includes('remuneracao') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('remuneracao') && (
                          <div className="space-y-2 mt-2">
                            {(() => {
                              // @ts-ignore TODO: fix type
                              const salaryMin = previewJob.salaryRange?.min ?? previewJob.salaryMin
                              // @ts-ignore TODO: fix type
                              const salaryMax = previewJob.salaryRange?.max ?? previewJob.salaryMax
                              const hasSalary = salaryMin || salaryMax
                              // @ts-ignore TODO: fix type
                              const bonusMin = previewJob.bonusRange?.min ?? previewJob.bonus_range?.min ?? previewJob.bonusMin
                              // @ts-ignore TODO: fix type
                              const bonusMax = previewJob.bonusRange?.max ?? previewJob.bonus_range?.max ?? previewJob.bonusMax
                              const hasBonus = bonusMin || bonusMax
                              const benefits = previewJob.benefits || []
                              const fmt = (v: number | string | null | undefined) => {
                                if (!v) return ''
                                const n = typeof v === 'string' ? parseFloat(v) : v
                                return isNaN(n) ? '' : `R$ ${n.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
                              }
                              return (
                                <>
                                  {hasSalary ? (
                                    <div className="flex items-center gap-1.5">
                                      <span className="text-micro text-lia-text-tertiary">Salário:</span>
                                      <span className="text-micro font-medium text-lia-text-primary">
                                        {fmt(salaryMin)}{salaryMax ? ` - ${fmt(salaryMax)}` : ''}
                                      </span>
                                    </div>
                                  ) : (
                                    <p className="text-micro text-lia-text-tertiary italic">
                                      Faixa salarial não informada
                                    </p>
                                  )}
                                  {hasBonus && (
                                    <div className="flex items-center gap-1.5">
                                      <span className="text-micro text-lia-text-tertiary">Bônus:</span>
                                      <span className="text-micro font-medium text-lia-text-primary">
                                        {fmt(bonusMin)}{bonusMax ? ` - ${fmt(bonusMax)}` : ''}
                                      </span>
                                    </div>
                                  )}
                                  {benefits.length > 0 && (
                                    <div>
                                      <span className="text-micro text-lia-text-tertiary block mb-1">Benefícios:</span>
                                      <div className="flex flex-wrap gap-1.5">
                                        {(benefits as Benefit[]).map((b: Benefit, idx: number) => (
                                          <Badge key={`benefit-${idx}`} className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-primary">
                                            {typeof b === 'string' ? b : b.name}
                                          </Badge>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </>
                              )
                            })()}
                          </div>
                        )}
                      </div>

                      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => onToggleSection('etapas')}>
                          <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                            <Layers3 className="w-3.5 h-3.5 text-lia-text-secondary" />
                            Etapas do Processo
                          </h5>
                          {collapsedPreviewSections.includes('etapas') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('etapas') && (
                          <div className="mt-2">
                            {previewJob.hiringProcess && previewJob.hiringProcess.length > 0 ? (
                              <div className="flex items-center gap-1 overflow-x-auto pb-1">
                                {previewJob.hiringProcess.map((step: string, idx: number) => (
                                  <React.Fragment key={`step-${idx}`}>
                                    {idx > 0 && (
                                      <ChevronRight className="w-3 h-3 text-lia-text-disabled flex-shrink-0" />
                                    )}
                                    <div className="flex items-center gap-1 px-2 py-1 bg-lia-bg-secondary border border-lia-border-subtle rounded-md flex-shrink-0">
                                      <span className="text-micro font-medium text-lia-text-secondary">{step}</span>
                                    </div>
                                  </React.Fragment>
                                ))}
                              </div>
                            ) : previewJob.interviewStages && previewJob.interviewStages.length > 0 ? (
                              <div className="flex items-center gap-1 overflow-x-auto pb-1">
                                {previewJob.interviewStages
                                  .sort((a: InterviewStage, b: InterviewStage) => (a.order || 0) - (b.order || 0))
                                  .map((stage: InterviewStage, idx: number) => (
                                    <React.Fragment key={`stage-${idx}`}>
                                      {idx > 0 && (
                                        <ChevronRight className="w-3 h-3 text-lia-text-disabled flex-shrink-0" />
                                      )}
                                      <div className="flex items-center gap-1 px-2 py-1 bg-lia-bg-secondary border border-lia-border-subtle rounded-md flex-shrink-0">
                                        {stage.liaAssisted && (
                                          <span className="w-1.5 h-1.5 rounded-full bg-wedo-cyan flex-shrink-0" />
                                        )}
                                        <span className="text-micro font-medium text-lia-text-secondary">{stage.stageName}</span>
                                      </div>
                                    </React.Fragment>
                                  ))}
                              </div>
                            ) : (
                              <p className="text-micro text-lia-text-tertiary italic">
                                Nenhuma etapa configurada
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                          <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle" />

                          {/* Roteiro de Triagem Automática */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <ClipboardList className="w-4 h-4 text-lia-text-secondary" />
                              <h4 className="text-xs font-semibold text-lia-text-primary">Roteiro de Triagem Automática</h4>
                              <Badge 
                                className={`text-[0.625rem] leading-none px-1.5 py-0.5 text-lia-text-primary ${(screeningConfig?.status?.enabled ?? true) ? 'bg-wedo-green-pastel' : 'bg-lia-interactive-active'}`}
                              >
                                {(screeningConfig?.status?.enabled ?? true) ? 'Ativo' : 'Pausado'}
                              </Badge>
                            </div>
                          </div>

                      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => onToggleSection('fluxo-resumido')}>
                          <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                            <ClipboardList className="w-3.5 h-3.5 text-lia-text-secondary" />
                            Resumo da Triagem
                            <Badge
                              className={`text-[0.625rem] leading-none px-1.5 py-0.5 text-lia-text-primary ${(screeningConfig?.status?.enabled ?? true) ? 'bg-wedo-green-pastel' : 'bg-lia-interactive-active'}`}
                            >
                              {(screeningConfig?.status?.enabled ?? true) ? 'Ativo' : 'Pausado'}
                            </Badge>
                          </h5>
                          {collapsedPreviewSections.includes('fluxo-resumido') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('fluxo-resumido') && (
                          <div className="mt-2">
                            <div className="grid grid-cols-2 gap-2">
                              <div className="text-center p-2 bg-lia-bg-secondary rounded-md">
                                <div className="text-base-ui font-semibold text-lia-text-primary">{(previewJob.screeningQuestions || []).length}</div>
                                <p className="text-micro text-lia-text-tertiary">Perguntas</p>
                              </div>
                              <div className="text-center p-2 bg-lia-bg-secondary rounded-md">
                                <div className="text-base-ui font-semibold text-lia-text-primary">{Math.ceil(((previewJob.screeningQuestions || []) as ScreeningQuestion[]).reduce((acc: number, q: ScreeningQuestion) => acc + ((q.time_limit as number) || 120), 0) / 60)}min</div>
                                <p className="text-micro text-lia-text-tertiary">Tempo Est.</p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* 5. Blocos WSI do Roteiro de Triagem */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => onToggleSection('fluxo-wsi')}>
                          <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                            <Layers3 className="w-3.5 h-3.5 text-lia-text-secondary" />
                            Fluxo de Triagem WSI
                            <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-interactive-active text-lia-text-primary">
                              6 Blocos
                            </Badge>
                          </h5>
                          {collapsedPreviewSections.includes('fluxo-wsi') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          )}
                        </div>

                        {!collapsedPreviewSections.includes('fluxo-wsi') && (
                        <div className="space-y-2">
                          {WSI_BLOCKS.map((block) => {
                            // @ts-ignore TODO: fix type
                            const isExpanded = expandedBlocks.includes(block.id)
                            
                            const allQuestions = previewJob.screeningQuestions || []
                            const cat = (q: ScreeningQuestion) => (q.category || '').toLowerCase()
                            const typ = (q: ScreeningQuestion) => (q.type || '').toLowerCase()

                            const isBlock2 = (q: ScreeningQuestion) => {
                              if (typ(q) === 'eliminatory' || q.required) return true
                              if (cat(q).includes('elegib') || cat(q).includes('elimin')) return true
                              if (cat(q).includes('fit') && cat(q).includes('básico')) return true
                              if (cat(q).includes('disponib') || cat(q).includes('eligib')) return true
                              return false
                            }
                            
                            const isBlock3 = (q: ScreeningQuestion) => {
                              if (isBlock2(q)) return false
                              return cat(q).includes('tecn') || cat(q).includes('tech') ||
                                cat(q).includes('skill') || cat(q).includes('técnica') ||
                                typ(q).includes('tech')
                            }
                            
                            const isBlock4 = (q: ScreeningQuestion) => {
                              if (isBlock2(q) || isBlock3(q)) return false
                              return true
                            }
                            
                            const blockQuestions = (allQuestions as ScreeningQuestion[]).filter((q: ScreeningQuestion) => {
                              if (q.block_id !== undefined && q.block_id !== null) {
                                return q.block_id === block.id
                              }
                              if (block.id === 2) return isBlock2(q)
                              if (block.id === 3) return isBlock3(q)
                              if (block.id === 4) return isBlock4(q)
                              return false
                            })
                            
                            const eliminatoryCount = blockQuestions.filter((q: ScreeningQuestion) => q.type === 'eliminatory' || q.required).length
                            const informativeCount = blockQuestions.length - eliminatoryCount
                            
                            return (
                              <div 
                                key={block.id} 
                                className={`border rounded-md overflow-hidden ${
                                  block.editable ? 'border-lia-border-subtle' : 'border-lia-border-subtle bg-lia-bg-secondary/50'
                                }`}
                              >
                                {/* Block Header */}
                                <div 
                                  className={`flex items-center justify-between p-2.5 cursor-pointer transition-colors motion-reduce:transition-none ${
                                    block.editable 
                                      ? 'bg-lia-bg-secondary hover:bg-lia-bg-tertiary' 
                                      : 'bg-lia-bg-tertiary/80'
                                  }`}
                                  // @ts-ignore TODO: fix type
                                  onClick={() => onToggleBlock(block.id)}
                                >
                                  <div className="flex items-center gap-2">
                                    <span className={`w-5 h-5 rounded-full text-white text-micro font-bold flex items-center justify-center ${
                                      block.editable ? 'bg-lia-bg-inverse' : 'bg-lia-border-medium'
                                    }`}>
                                      {block.id}
                                    </span>
                                    <div>
                                      <span className={`text-xs font-semibold ${block.editable ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`}>
                                        {block.name}
                                      </span>
                                      <span className="text-micro text-lia-text-tertiary ml-1.5">({block.duration})</span>
                                    </div>
                                    {!block.editable && (
                                      <Badge className="text-micro px-1 py-0 h-3.5 bg-lia-interactive-active text-lia-text-tertiary">
                                        Auto
                                      </Badge>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-1.5">
                                    {block.editable && blockQuestions.length > 0 && (
                                      <>
                                        {eliminatoryCount > 0 && (
                                          <Badge className="text-micro px-1.5 py-0 bg-status-error/10 text-status-error border border-status-error/30">
                                            {eliminatoryCount} Elim.
                                          </Badge>
                                        )}
                                        {informativeCount > 0 && (
                                          <Badge className="text-micro px-1.5 py-0 bg-lia-bg-tertiary text-lia-text-secondary">
                                            {informativeCount} Info.
                                          </Badge>
                                        )}
                                      </>
                                    )}
                                    {isExpanded ? (
                                      <ChevronUp className="w-3.5 h-3.5 text-lia-text-tertiary" />
                                    ) : (
                                      <ChevronDown className="w-3.5 h-3.5 text-lia-text-tertiary" />
                                    )}
                                  </div>
                                </div>
                                
                                {/* Block Content */}
                                {isExpanded && (
                                  <div className={`p-2.5 space-y-1.5 ${!block.editable ? 'bg-lia-bg-secondary/30' : ''}`}>
                                    {/* Non-editable blocks show automatic WSI messages */}
                                    {!block.editable ? (
                                      WSI_AUTOMATIC_MESSAGES[block.id] ? (
                                        <div className="rounded-md border border-lia-border-default dark:border-lia-border-default bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 overflow-hidden">
                                          <div className="px-2.5 py-2 border-b border-lia-btn-primary-bg dark:border-lia-border-medium/10 bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                                            <p className="text-xs font-medium text-lia-text-primary">
                                              {WSI_AUTOMATIC_MESSAGES[block.id].title}
                                            </p>
                                          </div>
                                          <div className="p-2.5">
                                            <div className="text-micro text-lia-text-primary leading-relaxed whitespace-pre-line">
                                              {formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id].message)}
                                            </div>
                                          </div>
                                          <div className="px-2.5 py-2 border-t border-lia-btn-primary-bg dark:border-lia-border-medium/10 bg-lia-bg-secondary">
                                            <p className="text-micro text-lia-text-tertiary italic">
                                              {WSI_AUTOMATIC_MESSAGES[block.id].note}
                                            </p>
                                          </div>
                                        </div>
                                      ) : (
                                        <div className="p-2.5 bg-lia-bg-primary/60 border border-lia-border-subtle rounded-md">
                                          <p className="text-micro text-lia-text-secondary italic">
                                            {block.description}
                                          </p>
                                          <p className="text-micro text-lia-text-disabled mt-1">
                                            Gerenciado automaticamente pela LIA
                                          </p>
                                        </div>
                                      )
                                    ) : (
                                      <>
                                        {blockQuestions.length === 0 ? (
                                          <div className="p-3 bg-lia-bg-secondary border border-lia-border-subtle border-dashed rounded-md text-center">
                                            <p className="text-micro text-lia-text-tertiary">
                                              Nenhuma pergunta neste bloco
                                            </p>
                                          </div>
                                        ) : (
                                          blockQuestions.map((item: ScreeningQuestion, idx: number) => (
                                            <div 
                                              key={item.id || idx} 
                                              className="p-2.5 bg-lia-bg-primary border border-lia-border-subtle rounded-md"
                                            >
                                              <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                                                <Badge className={`text-[0.625rem] leading-none px-1.5 py-0.5 rounded-full ${
                                                  item.category === 'behavioral' || item.category === 'Comportamental'
                                                    ? 'bg-wedo-purple/15 text-wedo-purple border border-wedo-purple/30'
                                                    : item.category === 'technical' || item.category === 'Técnica'
                                                    ? 'bg-wedo-cyan/10 text-wedo-cyan-dark border border-wedo-cyan/30'
                                                    : item.category === 'eligibility' || item.category === 'Elegibilidade'
                                                    ? 'bg-status-success/15 text-status-success border border-status-success/30'
                                                    : 'bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle'
                                                }`}>
                                                  {item.category === 'behavioral' ? 'Comport.' 
                                                    : item.category === 'technical' ? 'Técnica' 
                                                    : item.category === 'eligibility' ? 'Elegibilidade'
                                                    : item.category === 'cultural' ? 'Cultural'
                                                    : item.category || 'Geral'}
                                                </Badge>
                                                {(item.type === 'eliminatory' || item.required) && (
                                                  <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 rounded-full bg-status-error/10 text-status-error border border-status-error/30">
                                                    Eliminatória
                                                  </Badge>
                                                )}
                                              </div>
                                              <p className="text-micro text-lia-text-primary leading-relaxed mb-1.5">
                                                {item.question}
                                              </p>
                                              <div className="flex items-center gap-2 flex-wrap">
                                                {item.skill_targeted && (
                                                  <span className="inline-flex items-center gap-0.5 text-micro text-lia-text-tertiary">
                                                    <Target className="w-2.5 h-2.5 text-lia-text-disabled" />
                                                    {item.skill_targeted}
                                                  </span>
                                                )}
                                                <span className="inline-flex items-center gap-0.5 text-micro text-lia-text-tertiary">
                                                  <MessageSquare className="w-2.5 h-2.5 text-lia-text-disabled" />
                                                  {item.type === 'eliminatory' ? 'Sim/Não' 
                                                    // @ts-ignore TODO: fix type
                                                    : item.options?.length ? 'Múltipla escolha'
                                                    : 'Texto livre'}
                                                </span>
                                                {item.weight != null && (
                                                  <span className="inline-flex items-center gap-0.5 text-micro text-lia-text-tertiary">
                                                    <BarChart3 className="w-2.5 h-2.5 text-lia-text-disabled" />
                                                    Peso {typeof (item as any).weight === 'number' ? (item as any).weight.toFixed(2) : (item as any).weight}
                                                  </span>
                                                )}
                                                <span className="inline-flex items-center gap-0.5 text-micro text-lia-text-tertiary">
                                                  <Clock className="w-2.5 h-2.5 text-lia-text-disabled" />
                                                  {item.type === 'eliminatory' ? '30s' : '2 min'}
                                                </span>
                                              </div>
                                            </div>
                                          ))
                                        )}
                                      </>
                                    )}
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                        )}
                      </div>

                      {/* 2. Agendamento Automático */}
                      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => onToggleSection('agendamento')}>
                          <div className="flex items-center gap-2">
                            <CalendarCheck className="w-3.5 h-3.5 text-lia-text-secondary" />
                            <h5 className="text-xs font-semibold text-lia-text-primary">Agendamento Automático</h5>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Badge className={`${(screeningConfig?.scheduling?.auto_enabled ?? true) ? 'bg-lia-bg-inverse text-white dark:bg-lia-bg-elevated' : 'bg-lia-border-medium text-white'} text-[0.625rem] leading-none px-1.5 py-0.5`}>
                              {(screeningConfig?.scheduling?.auto_enabled ?? true) ? 'Ativo' : 'Inativo'}
                            </Badge>
                            {collapsedPreviewSections.includes('agendamento') ? (
                              <ChevronDown className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                            ) : (
                              <ChevronUp className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                            )}
                          </div>
                        </div>
                        {!collapsedPreviewSections.includes('agendamento') && (<>
                        <p className="text-micro text-lia-text-tertiary mb-2 mt-2">Aprovados na triagem são agendados automaticamente para entrevista</p>

                        <div className="grid grid-cols-2 gap-2">
                          <div className="flex items-center justify-between p-1.5 bg-lia-bg-secondary rounded-md">
                            <span className="text-micro text-lia-text-tertiary">Score Mínimo</span>
                            <span className="text-micro font-medium text-lia-text-secondary">{(() => {
                              const preset = screeningConfig?.scheduling?.min_score_for_auto_preset
                              switch(preset) {
                                case 'rigorous': return 'Rigoroso'
                                case 'flexible': return 'Flexível'
                                default: return 'Recomendado'
                              }
                            })()}</span>
                          </div>
                          <div className="flex items-center justify-between p-1.5 bg-lia-bg-secondary rounded-md">
                            <span className="text-micro text-lia-text-tertiary">Calendário</span>
                            <span className="text-micro font-medium text-lia-text-secondary">{screeningConfig?.scheduling?.calendar_provider || 'Microsoft'}</span>
                          </div>
                          <div className="flex items-center justify-between p-1.5 bg-lia-bg-secondary rounded-md">
                            <span className="text-micro text-lia-text-tertiary">Horários</span>
                            <span className="text-micro font-medium text-lia-text-secondary">{screeningConfig?.scheduling?.available_hours || '9h-18h'}</span>
                          </div>
                          <div className="flex items-center justify-between p-1.5 bg-lia-bg-secondary rounded-md">
                            <span className="text-micro text-lia-text-tertiary">Duração</span>
                            <span className="text-micro font-medium text-lia-text-secondary">{screeningConfig?.scheduling?.interview_duration_min ?? 45}min</span>
                          </div>
                        </div>
                        </>)}
                      </div>

                          {/* 1. Canais + Configurações Agrupados */}
                          <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => onToggleSection('canais')}>
                          <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                            <Settings className="w-3.5 h-3.5 text-lia-text-secondary" />
                            Canais de Comunicação
                          </h5>
                          {collapsedPreviewSections.includes('canais') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-lia-text-disabled transition-transform motion-reduce:transition-none" />
                          )}
                        </div>

                        {!collapsedPreviewSections.includes('canais') && (<>
                        {/* Canais em linha */}
                        <div className="flex items-center gap-3 mb-3 mt-3 pb-3 border-b border-lia-border-subtle">
                          <span className="text-[0.625rem] text-lia-text-tertiary">Canais:</span>
                          <div className="flex items-center gap-2">
                            <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded-md ${(screeningConfig?.channels?.whatsapp?.enabled ?? true) ? 'bg-status-success/10 text-status-success' : 'bg-lia-bg-tertiary text-lia-text-secondary'}`}>
                              <MessageSquare className="w-2.5 h-2.5" />
                              <span className="text-[0.625rem] font-medium">WhatsApp</span>
                              {(screeningConfig?.channels?.whatsapp?.enabled ?? true) && <CheckCircle className="w-2.5 h-2.5" />}
                            </div>
                            <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded-md ${(screeningConfig?.channels?.chat_web?.enabled ?? true) ? 'bg-status-success/10 text-status-success' : 'bg-lia-bg-tertiary text-lia-text-secondary'}`}>
                              <Globe className="w-2.5 h-2.5" />
                              <span className="text-[0.625rem] font-medium">Chat Web</span>
                              {(screeningConfig?.channels?.chat_web?.enabled ?? true) && <CheckCircle className="w-2.5 h-2.5" />}
                            </div>
                            <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded-md ${(screeningConfig?.channels?.phone?.enabled ?? false) ? 'bg-status-success/10 text-status-success' : 'bg-lia-bg-tertiary text-lia-text-secondary'}`}>
                              <Phone className="w-2.5 h-2.5" />
                              <span className="text-[0.625rem] font-medium">Ligação</span>
                              {(screeningConfig?.channels?.phone?.enabled ?? false) && <CheckCircle className="w-2.5 h-2.5" />}
                            </div>
                          </div>
                        </div>

                        {/* Configurações em grid */}
                        <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-[0.625rem] text-lia-text-tertiary">Score Mínimo{'\n'}Aprovação</span>
                            <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-inverse text-white">{(() => {
                              const preset = screeningConfig?.settings?.min_score_preset
                              switch(preset) {
                                case 'rigorous': return 'Rigoroso'
                                case 'flexible': return 'Flexível'
                                default: return 'Recomendado'
                              }
                            })()}</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-[0.625rem] text-lia-text-tertiary">Timeout Resposta</span>
                            <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-primary">{screeningConfig?.settings?.response_timeout_hours ?? 48}h</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-[0.625rem] text-lia-text-tertiary">Re-tentativas</span>
                            <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-primary">{screeningConfig?.settings?.max_retries ?? 2}x</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-[0.625rem] text-lia-text-tertiary">Fallback</span>
                            <Badge className="text-[0.625rem] leading-none px-1.5 py-0.5 bg-wedo-orange/15 text-wedo-orange">Revisão Manual</Badge>
                          </div>
                        </div>

                      </>)}
                      </div>

                      
                      </div>
                      )}
                    </div>
  )
}
