"use client"

import React, { useState, useEffect } from 'react'
import { toast } from 'sonner'
import {
  Settings2, ChevronDown, ChevronUp, Edit2, MessageSquare, Globe, Phone,
  CheckCircle, CheckCircle2, BarChart3, Clock, RotateCcw, CalendarClock,
  Shield, ShieldAlert, ShieldCheck, CalendarCheck, AlertTriangle, Save, ListChecks,
  Layers, Info, Brain, Loader2, X, Archive, Gauge, GraduationCap, Target,
  Scale, ClipboardList, FileText, Edit, Calendar, Play, Pause, AlertCircle
} from 'lucide-react'
import { useScreeningConfig, limitToApprovalPreset, approvalPresetToLimit } from '@/hooks/recruitment/useScreeningConfig'
import { wsiPresetToScore } from '@/lib/wsi/visual'
import { CompanyBankQuestions } from './CompanyBankQuestions'
import { CompanyDefaultQuestions } from "./CompanyDefaultQuestions"
import { CustomQuestions } from './CustomQuestions'
import type { CustomQuestion } from './CustomQuestions'
import { WSI_BLOCKS, WSI_AUTOMATIC_MESSAGES, formatMessageWithVariables, getBloomComplexity, getEstimatedTime, getBloomLabelPTBR, getDreyfusLabelPTBR } from '@/components/jobs/jobsPageConstants'
import { JDEvaluationPanel } from '@/components/wsi'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { textStyles } from '@/lib/design-tokens'

const BIG_FIVE_PT_BR: Record<string, string> = {
  openness: 'Abertura a mudanças',
  conscientiousness: 'Organização e disciplina',
  extraversion: 'Sociabilidade',
  agreeableness: 'Cooperação',
  neuroticism: 'Estabilidade emocional',
}

import { useScreeningConfigManagerCore } from "./hooks/useScreeningConfigManagerCore"

function getBigFiveLabelPTBR(trait: string | null | undefined): string {
  if (!trait) return ''
  const key = trait.toLowerCase().replace(/\s+/g, '_')
  return BIG_FIVE_PT_BR[key] || trait
}

interface ScreeningConfigManagerProps {
  job: Record<string, unknown>
  onJobUpdate?: (updatedJob: Record<string, unknown>) => void
  onFormUpdate?: (updates: Record<string, unknown>) => void
}

interface ScreeningConfigContentProps {
  job: Record<string, unknown>
  onJobUpdate?: (updatedJob: Record<string, unknown>) => void
  onFormUpdate?: (updates: Record<string, unknown>) => void
  activeSection: 'configuracoes' | 'descricao' | 'perguntas'
}

// Inline component — company default questions with opt-out toggle
import { SCMSectionContent } from "./SCMSectionContent"


export const SCREENING_SECTIONS = [
  {
    id: "configuracoes",
    title: "Configurações do Roteiro",
    icon: Settings2,
    description: "Formato e duração da triagem",
  },
  {
    id: "descricao",
    title: "Descrição do Cargo",
    icon: FileText,
    description: "Informações da vaga para a IA",
  },
  {
    id: "perguntas",
    title: "Perguntas de Triagem",
    icon: ListChecks,
    description: "Blocos WSI de avaliação",
  },
]

function ScreeningConfigManager({ job, onJobUpdate, onFormUpdate, _externalActiveSection, _hideOwnSidebar }: ScreeningConfigManagerProps & { _externalActiveSection?: string; _hideOwnSidebar?: boolean }) {
  const core = useScreeningConfigManagerCore({ job, onJobUpdate, onFormUpdate, _externalActiveSection, _hideOwnSidebar })
  const {
    companyScreeningDefaults, activeSection, companyQuestions, configDone, currentSection, customQuestions, disabledCompanyQIds, editAutoApprovalPreset, editAvailableHours, editAvailableHoursInherited, editCalendarProvider, editChannels, editChannelsMasterEnabled, editWhatsappMode, editFallbackOrder, editInterviewDuration, editMaxRetries, editMinScorePreset, editPrimaryChannel, editSchedulingEnabled, editSchedulingMinScorePreset, editTimeoutHours, getConfigStatusInfo, isEditingScreening, isEditingScreeningConfig, screeningConfigLoadError, retryScreeningConfig, jdDone, questionsDone, resetScreeningEditing, screeningConfig, selectedBankQuestions, setActiveSection, setEditAutoApprovalPreset, setEditAvailableHours, setEditAvailableHoursInherited, setEditCalendarProvider, setEditChannels, setEditChannelsMasterEnabled, setEditWhatsappMode, setEditFallbackOrder, setEditInterviewDuration, setEditMaxRetries, setEditMinScorePreset, setEditPrimaryChannel, setEditSchedulingEnabled, setEditSchedulingMinScorePreset, setEditTimeoutHours, setIsEditingScreening, setIsEditingScreeningConfig, setShowScreeningToggleConfirm, showScreeningToggleConfirm, updateScreeningConfig,
  } = core

  if (screeningConfigLoadError) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4" role="alert" aria-live="assertive">
        <AlertCircle className="w-8 h-8 text-status-error" />
        <p className="text-sm text-status-error text-center">{screeningConfigLoadError}</p>
        <Button variant="outline" size="sm" onClick={retryScreeningConfig}>
          <RotateCcw className="w-3.5 h-3.5 mr-2" />Tentar novamente
        </Button>
      </div>
    )
  }


  return (
    <div className={_hideOwnSidebar ? "" : "flex gap-6"}>
      {!_hideOwnSidebar && (
      <div className="flex-shrink-0">
        <Card className="border border-lia-border-subtle bg-lia-bg-primary rounded-xl overflow-hidden">
          <nav className="space-y-1 p-3 h-full overflow-y-auto">
            {SCREENING_SECTIONS.map((section) => {
              const sectionDone = section.id === 'configuracoes' ? configDone : section.id === 'descricao' ? jdDone : questionsDone
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded-md text-left transition-colors motion-reduce:transition-none font-open-sans text-xs leading-[1.125rem] font-medium ${
 activeSection === section.id
                      ? 'bg-lia-bg-secondary border border-lia-btn-primary-bg text-wedo-cyan-text'
                      : 'hover:bg-lia-interactive-hover text-lia-text-primary border border-transparent'
                  }`}
                  
                >
                  <section.icon className="w-4 h-4 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className={`${textStyles.h4} 2xl:text-xs`}>{section.title}</div>
                    <div className={`${textStyles.description} 2xl:text-xs`}>{section.description}</div>
                  </div>
                  {sectionDone && (
                    <CheckCircle className="w-3.5 h-3.5 text-status-success flex-shrink-0" />
                  )}
                </button>
              )
            })}
          </nav>
        </Card>
      </div>
      )}

      <div className="flex-1 min-w-0">
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-lia-bg-primary rounded-xl p-4">
            <div className="flex items-center gap-3">
              <currentSection.icon className="w-5 h-5 text-lia-text-secondary" />
              <div>
                <h2 className={textStyles.h3}>{currentSection.title}</h2>
                <p className={textStyles.description}>{currentSection.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {activeSection === 'configuracoes' && (
                <>
                  <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-lia-bg-tertiary text-lia-text-secondary">
                    {getConfigStatusInfo()}
                  </span>
                  {!isEditingScreeningConfig ? (
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 text-xs rounded-md"
                      onClick={() => setIsEditingScreeningConfig(true)}
                    >
                      <Edit className="w-3.5 h-3.5" />
                      Editar Configurações
                    </Button>
                  ) : (
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" className="text-xs rounded-md" onClick={() => {
                        setIsEditingScreeningConfig(false)
                        if (screeningConfig) {
                          setEditChannels({
                            whatsapp: screeningConfig.channels?.whatsapp?.enabled ?? true,
                            chat_web: screeningConfig.channels?.chat_web?.enabled ?? true,
                            phone_pstn: screeningConfig.channels?.phone_pstn?.enabled ?? screeningConfig.channels?.phone?.enabled ?? false,
                            voice_web: screeningConfig.channels?.voice_web?.enabled ?? screeningConfig.channels?.voip_web?.enabled ?? true,
                          })
                          setEditChannelsMasterEnabled(screeningConfig.channels_master_enabled !== false)
                          {
                            const wm = (screeningConfig.channels?.whatsapp as { mode?: string } | undefined)?.mode
                            setEditWhatsappMode(wm === 'twilio_direct' || wm === 'both' ? wm : 'wa_link')
                          }
                          setEditPrimaryChannel(screeningConfig.screening_channels?.primary_channel ?? 'chat_web')
                          setEditFallbackOrder(screeningConfig.screening_channels?.fallback_order ?? ['whatsapp'])
                          setEditMinScorePreset(screeningConfig.settings?.min_score_preset ?? 'recommended')
                          setEditTimeoutHours(screeningConfig.settings?.response_timeout_hours ?? companyScreeningDefaults?.settings?.response_timeout_hours ?? 48)
                          setEditMaxRetries(screeningConfig.settings?.max_retries ?? companyScreeningDefaults?.settings?.max_retries ?? 2)
                          setEditSchedulingEnabled(screeningConfig.scheduling?.auto_enabled ?? true)
                          setEditSchedulingMinScorePreset(screeningConfig.scheduling?.min_score_for_auto_preset ?? 'recommended')
                          setEditCalendarProvider(screeningConfig.scheduling?.calendar_provider ?? 'Microsoft')
                          setEditAvailableHours(screeningConfig.scheduling?.available_hours ?? '9h-18h')
                          setEditAvailableHoursInherited(screeningConfig.scheduling?.available_hours_inherited ?? true)
                          setEditInterviewDuration(screeningConfig.scheduling?.interview_duration_min ?? 60)
                          setEditAutoApprovalPreset(screeningConfig.settings?.auto_approval_preset ?? limitToApprovalPreset(screeningConfig.settings?.auto_approval_limit) ?? companyScreeningDefaults?.settings?.auto_approval_preset ?? recommended)
                        }
                      }}>
                        Cancelar
                      </Button>
                      <Button size="sm" className="gap-1.5 text-xs rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover" onClick={async () => {
                        try {
                          // wsiPresetToScore importado de @/lib/wsi/visual
                          const success = await updateScreeningConfig({
                            channels_master_enabled: editChannelsMasterEnabled,
                            channels: {
                              whatsapp: { enabled: editChannels.whatsapp, label: 'WhatsApp', mode: editWhatsappMode },
                              chat_web: { enabled: editChannels.chat_web, label: 'Chat Web' },
                              phone_pstn: { enabled: editChannels.phone_pstn, label: 'Ligação (PSTN)' },
                              voice_web: { enabled: editChannels.voice_web, label: 'Voz no Navegador' },
                            },
                            screening_channels: {
                              primary_channel: editPrimaryChannel,
                              fallback_order: editFallbackOrder
                                .filter(k => k !== editPrimaryChannel)
                                .filter(k => {
                                  if (k === 'phone_pstn') return editChannels.phone_pstn
                                  if (k === 'voice_web') return editChannels.voice_web
                                  if (k === 'whatsapp') return editChannels.whatsapp
                                  if (k === 'chat_web') return editChannels.chat_web
                                  return true
                                }),
                            },
                            settings: {
                              min_score: wsiPresetToScore(editMinScorePreset),
                              min_score_preset: editMinScorePreset,
                              response_timeout_hours: editTimeoutHours,
                              max_retries: editMaxRetries,
                              auto_approval_limit: approvalPresetToLimit(editAutoApprovalPreset),
                              auto_approval_preset: editAutoApprovalPreset,
                              auto_approvals_count: screeningConfig?.settings?.auto_approvals_count ?? 0,
                              auto_approval_paused: screeningConfig?.settings?.auto_approval_paused ?? false
                            },
                            scheduling: {
                              auto_enabled: editSchedulingEnabled,
                              min_score_for_auto: wsiPresetToScore(editSchedulingMinScorePreset),
                              min_score_for_auto_preset: editSchedulingMinScorePreset,
                              calendar_provider: editCalendarProvider,
                              available_hours: editAvailableHours,
                              available_hours_inherited: editAvailableHoursInherited,
                              interview_duration_min: editInterviewDuration
                            }
                          })
                          if (success) {
                            setIsEditingScreeningConfig(false)
                            toast.success('Configurações salvas com sucesso!')
                          } else {
                            toast.error('Erro ao salvar configurações. Tente novamente.')
                          }
                        } catch {
                          toast.error('Erro ao salvar configurações. Tente novamente.')
                        }
                      }}>
                        <Save className="w-3.5 h-3.5" />
                        Salvar
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-xs rounded-md gap-1 text-lia-text-secondary hover:text-lia-text-primary"
                        title="Carregar padrões de triagem configurados em Dados da Empresa"
                        onClick={async () => {
                          try {
                            const res = await fetch("/api/backend-proxy/company/screening-config-defaults")
                            if (!res.ok) return
                            const d = await res.json()
                            const cfg = d?.screening_config_defaults ?? d
                            const s = cfg?.settings ?? {}
                            const ch = cfg?.channels ?? {}
                            if (s.min_score != null) {
                              setEditMinScorePreset(s.min_score_preset ?? "custom")
                            }
                            if (s.response_timeout_hours != null) setEditTimeoutHours(Number(s.response_timeout_hours))
                            if (s.max_retries != null) setEditMaxRetries(Number(s.max_retries))
                            if (Object.keys(ch).length > 0) {
                              setEditChannels({
                                whatsapp: ch.whatsapp?.enabled ?? true,
                                chat_web: ch.chat_web?.enabled ?? true,
                                phone_pstn: ch.phone_pstn?.enabled ?? false,
                                voice_web: ch.voice_web?.enabled ?? false,
                              })
                            }
                            const sched = cfg?.scheduling ?? {}
                            if (sched.auto_enabled != null) setEditSchedulingEnabled(Boolean(sched.auto_enabled))
                            if (sched.interview_duration_min != null) setEditInterviewDuration(Number(sched.interview_duration_min))
                            if (typeof window !== "undefined") {
                              import("sonner").then(({ toast }) =>
                                toast.success("Padrões da empresa carregados. Revise e salve.")
                              )
                            }
                          } catch {}
                        }}
                      >
                        <RotateCcw className="w-3 h-3" />
                        Restaurar padrão
                      </Button>
                    </div>
                  )}
                </>
              )}
              {activeSection === 'descricao' && (
                <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-lia-bg-tertiary text-lia-text-secondary">
                  {jdDone ? 'Descrição preenchida' : 'Descrição pendente'}
                </span>
              )}
              {activeSection === 'perguntas' && (
                <>
                  <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-lia-bg-tertiary text-lia-text-secondary">
                    {(job.screeningQuestions as unknown[] | undefined)?.length || 0} WSI
                    {((companyQuestions.length - disabledCompanyQIds.size) + selectedBankQuestions.length + customQuestions.length) > 0 && (
                      <> · {(companyQuestions.length - disabledCompanyQIds.size) + selectedBankQuestions.length + customQuestions.length} extras</>
                    )}
                  </span>
                  <div className="flex items-center gap-2 border-l border-lia-border-subtle pl-3 ml-1">
                    <span className="text-micro text-lia-text-tertiary" >
                      Triagem
                    </span>
                    {(job.screeningStatus === 'not_configured' || !job.screeningStatus) ? (
                      <button
                        onClick={() => {
                          const hasQuestions = ((job.screeningQuestions as unknown[] | undefined)?.length || 0) > 0
                          if (!hasQuestions) {
                            toast.error('Configure pelo menos 3 perguntas antes de ativar a triagem.')
                            return
                          }
                          setShowScreeningToggleConfirm('activate')
                        }}
                        className="relative inline-flex h-5 w-9 items-center rounded-full transition-colors motion-reduce:transition-none duration-200 bg-lia-border-default"
                      >
                        <span
                          className="inline-block h-3.5 w-3.5 transform translate-x-[2px] rounded-full bg-lia-bg-secondary transition-transform motion-reduce:transition-none duration-200"
                        />
                      </button>
                    ) : job.screeningStatus === 'completed' ? (
                      <span className="text-micro font-medium px-2 py-0.5 rounded-full bg-wedo-cyan/15 text-wedo-cyan-text">
                        Concluída
                      </span>
                    ) : (
                      <button
                        onClick={() => {
                          if (job.screeningStatus === 'active') {
                            setShowScreeningToggleConfirm('pause')
                          } else {
                            const hasQuestions = ((job.screeningQuestions as unknown[] | undefined)?.length || 0) > 0
                            if (!hasQuestions) {
                              toast.error('Configure pelo menos 3 perguntas antes de ativar a triagem.')
                              return
                            }
                            setShowScreeningToggleConfirm('activate')
                          }
                        }}
                        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors motion-reduce:transition-none duration-200 ${
 job.screeningStatus === 'active' ? 'bg-status-success' : 'bg-lia-border-default'
                        }`}
                      >
                        <span
                          className="inline-block h-3.5 w-3.5 transform rounded-full bg-lia-bg-secondary transition-transform motion-reduce:transition-none duration-200"
                          style={{transform: job.screeningStatus === 'active' ? 'translateX(17px)' : 'translateX(2px)'}}
                        />
                      </button>
                    )}
                  </div>
                  {!isEditingScreening ? (
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 text-xs rounded-md"
                      onClick={() => setIsEditingScreening(true)}
                    >
                      <Edit className="w-3.5 h-3.5" />
                      Editar Perguntas
                    </Button>
                  ) : (
                    <Button variant="outline" size="sm" className="gap-1.5 text-xs rounded-md" onClick={() => resetScreeningEditing()}>
                      <X className="w-3.5 h-3.5" />
                      Cancelar Edição
                    </Button>
                  )}
                </>
              )}
            </div>
          </div>

          {showScreeningToggleConfirm && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-lia-overlay">
              <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle w-[380px] p-5 animate-in fade-in zoom-in-95 duration-200">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center bg-lia-bg-tertiary">
                    {showScreeningToggleConfirm === 'activate'
                      ? <Play className="w-5 h-5 text-lia-text-secondary" />
                      : <Pause className="w-5 h-5 text-lia-text-secondary" />
                    }
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-lia-text-primary">
                      {showScreeningToggleConfirm === 'activate' ? 'Ativar Triagem' : 'Pausar Triagem'}
                    </h3>
                    <p className="text-xs text-lia-text-tertiary">
                      {(job.title as React.ReactNode)}
                    </p>
                  </div>
                </div>
                <div className="rounded-xl p-3 mb-4 border border-lia-border-subtle bg-lia-bg-secondary/50">
                  <div className="flex items-start gap-2.5">
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
 showScreeningToggleConfirm === 'activate' ? 'bg-status-success/15 dark:bg-status-success/30' : 'bg-status-warning/15 dark:bg-status-warning/30'
                    }`}>
                      {showScreeningToggleConfirm === 'activate'
                        ? <Play className="w-3 h-3 text-status-success" />
                        : <Pause className="w-3 h-3 text-status-warning" />
                      }
                    </div>
                    <p className="text-xs leading-relaxed text-lia-text-secondary"  aria-live="polite" aria-atomic="true">
                      {showScreeningToggleConfirm === 'activate'
                        ? 'A IA começará a avaliar candidatos automaticamente conforme as configurações definidas neste roteiro.'
                        : 'Candidatos em avaliação serão mantidos no estado atual até a reativação. Nenhum novo candidato será triado enquanto a triagem estiver pausada.'
                      }
                    </p>
                  </div>
                </div>
                <div className="flex items-center justify-end gap-2 pt-1">
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs rounded-xl px-4 border-lia-border-subtle"
                    onClick={() => setShowScreeningToggleConfirm(null)}
                  >
                    Cancelar
                  </Button>
                  <Button
                    size="sm"
                    className="text-xs rounded-md px-4 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                    onClick={() => {
                      const newStatus = showScreeningToggleConfirm === 'activate' ? 'active' : 'paused'
                      onJobUpdate?.({ ...job, screeningStatus: newStatus })
                      toast.success(newStatus === 'active' ? 'Triagem ativada com sucesso!' : 'Triagem pausada.')
                      setShowScreeningToggleConfirm(null)
                    }}
                  >
                    {showScreeningToggleConfirm === 'activate' ? 'Ativar' : 'Pausar'}
                  </Button>
                </div>
              </div>
            </div>
          )}


          <SCMSectionContent {...core} />

        </div>
      </div>
    </div>
  )
}

export function ScreeningConfigContent({ job, onJobUpdate, onFormUpdate, activeSection }: ScreeningConfigContentProps) {
  return (
    <ScreeningConfigManager
      job={job}
      onJobUpdate={onJobUpdate}
      onFormUpdate={onFormUpdate}
      _externalActiveSection={activeSection}
      _hideOwnSidebar={true}
    />
  )
}

export default ScreeningConfigManager

