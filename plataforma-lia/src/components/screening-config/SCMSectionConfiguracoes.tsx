"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { SCREENING_STATUS_LABELS, type ScreeningStatus } from "@/types/screening"
import { Card, CardContent } from "@/components/ui/card"
import { approvalPresetToLimit, type ScreeningChannelKey } from '@/hooks/recruitment/useScreeningConfig'
import {
  AlertCircle, AlertTriangle, Calendar, CalendarCheck,
  CheckCircle, Clock, Globe, MessageSquare, Pause, Phone, Play, ShieldAlert,
  Wifi, ArrowRight, Star, GripVertical
} from "lucide-react"
import type { useScreeningConfigManagerCore } from "./hooks/useScreeningConfigManagerCore"

type Props = ReturnType<typeof useScreeningConfigManagerCore>

const CHANNEL_DEFS: { key: ScreeningChannelKey; label: string; icon: React.ElementType; desc: string; comingSoon?: boolean }[] = [
  { key: 'chat_web', label: 'Chat Web', icon: Globe, desc: 'Chat via portal de carreiras' },
  { key: 'whatsapp', label: 'WhatsApp', icon: MessageSquare, desc: 'Mensagens via WhatsApp Business' },
  { key: 'phone_pstn', label: 'Ligação (PSTN)', icon: Phone, desc: 'Chamada de voz via Twilio' },
  { key: 'voice_web', label: 'Voz no Navegador', icon: Wifi, desc: 'Conversa por voz via Gemini Live' },
]

export function SCMSectionConfiguracoes({
  job, onJobUpdate,
  screeningConfig,
  isEditingScreeningConfig,
  editChannels, setEditChannels,
  editChannelsMasterEnabled, setEditChannelsMasterEnabled,
  editWhatsappMode, setEditWhatsappMode,
  editPrimaryChannel, setEditPrimaryChannel,
  editFallbackOrder, setEditFallbackOrder,
  editMinScorePreset, setEditMinScorePreset,
  editTimeoutHours, setEditTimeoutHours,
  editMaxRetries, setEditMaxRetries,
  editAutoApprovalPreset, setEditAutoApprovalPreset,
  editSchedulingEnabled, setEditSchedulingEnabled,
  editSchedulingMinScorePreset, setEditSchedulingMinScorePreset,
  editCalendarProvider, setEditCalendarProvider,
  editAvailableHours, setEditAvailableHours,
  editAvailableHoursInherited, setEditAvailableHoursInherited,
  editInterviewDuration, setEditInterviewDuration,
  setShowScreeningToggleConfirm,
}: Props) {
  const statusValue = (job.screeningStatus || 'not_configured') as ScreeningStatus

  return (
    <Card className="border border-lia-border-subtle">
      {!isEditingScreeningConfig && (
        <CardContent className="p-4">
          <div className="space-y-4">
            {/* Status Row */}
            <div className="px-3 py-3 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary/50/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center ${
                    statusValue === 'active' ? 'bg-status-success/15 dark:bg-status-success/30' :
                    statusValue === 'paused' ? 'bg-status-warning/15 dark:bg-status-warning/30' :
                    statusValue === 'completed' ? 'bg-wedo-cyan/15' :
                    'bg-lia-bg-tertiary'
                  }`}>
                    {statusValue === 'active' && <Play className="w-3.5 h-3.5 text-status-success" />}
                    {statusValue === 'paused' && <Pause className="w-3.5 h-3.5 text-status-warning" />}
                    {statusValue === 'completed' && <CheckCircle className="w-3.5 h-3.5 text-wedo-cyan-text" />}
                    {statusValue === 'not_started' && <Clock className="w-3.5 h-3.5 text-lia-text-secondary" />}
                    {statusValue === 'not_configured' && <AlertCircle className="w-3.5 h-3.5 text-lia-text-secondary" />}
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-lia-text-primary">Status da Triagem</span>
                    <span className={`ml-2 text-micro font-medium px-2 py-0.5 rounded-full ${
                      statusValue === 'active' ? 'bg-status-success/15 text-status-success dark:bg-status-success/30' :
                      statusValue === 'paused' ? 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30' :
                      statusValue === 'completed' ? 'bg-wedo-cyan/15 text-wedo-cyan-text' :
                      statusValue === 'not_started' ? 'bg-lia-interactive-active text-lia-text-secondary' :
                      'bg-lia-bg-tertiary text-lia-text-tertiary'
                    }`}>
                      {SCREENING_STATUS_LABELS[statusValue]}
                    </span>
                  </div>
                </div>
                {(job.screeningStatus === 'not_configured' || job.screeningStatus === 'completed') ? null : (
                  <div className="flex items-center gap-2.5 opacity-50 cursor-not-allowed" title="Clique em Editar Configurações para alterar">
                    <span className="text-micro text-lia-text-disabled">{job.screeningStatus === 'active' ? 'Ativa' : 'Inativa'}</span>
                    <div className={`relative inline-flex h-5 w-9 items-center rounded-full ${job.screeningStatus === 'active' ? 'bg-status-success' : 'bg-lia-interactive-active'}`}>
                      <span className="inline-block h-3.5 w-3.5 transform rounded-full bg-lia-bg-secondary" style={{transform: job.screeningStatus === 'active' ? 'translateX(17px)' : 'translateX(2px)'}} />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Channels preview — Task #425: 4 canonical channels + master toggle status */}
            <div>
              <div className="flex items-center justify-between px-1 mb-3">
                <h3 className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider">Canais Habilitados</h3>
                {(() => {
                  const masterOn = screeningConfig?.channels_master_enabled !== false
                  return (
                    <span className={`text-micro font-medium px-2 py-0.5 rounded-full border ${masterOn ? 'border-lia-border-subtle text-lia-text-secondary bg-lia-bg-secondary' : 'border-status-error/30 text-status-error bg-status-error/10'}`}>
                      {masterOn ? 'Triagem ativa' : 'Triagem desligada'}
                    </span>
                  )
                })()}
              </div>
              <div className="border border-lia-border-subtle rounded-xl divide-y divide-lia-border-subtle">
                {[
                  { key: 'chat_web', label: 'Chat Web', icon: Globe, enabled: screeningConfig?.channels?.chat_web?.enabled ?? true },
                  { key: 'whatsapp', label: 'WhatsApp', icon: MessageSquare, enabled: screeningConfig?.channels?.whatsapp?.enabled ?? true },
                  { key: 'phone_pstn', label: 'Ligação automática (PSTN)', icon: Phone, enabled: screeningConfig?.channels?.phone_pstn?.enabled ?? screeningConfig?.channels?.phone?.enabled ?? false },
                  { key: 'voice_web', label: 'Voz no navegador (Gemini Live)', icon: Phone, enabled: screeningConfig?.channels?.voice_web?.enabled ?? screeningConfig?.channels?.voip_web?.enabled ?? true },
                ].map((ch) => {
                  const masterOn = screeningConfig?.channels_master_enabled !== false
                  const effective = masterOn && ch.enabled
                  const ChIcon = ch.icon
                  return (
                    <div key={ch.key} className="flex items-center justify-between px-3 py-2">
                      <div className="flex items-center gap-2">
                        <ChIcon className="w-3.5 h-3.5 text-lia-text-disabled" />
                        <span className="text-xs font-medium text-lia-text-secondary">{ch.label}</span>
                        {!masterOn && <span className="text-micro text-lia-text-disabled">(triagem desligada)</span>}
                      </div>
                      <div className={`relative inline-flex h-5 w-9 items-center rounded-full ${effective ? 'bg-lia-border-medium' : 'bg-lia-interactive-active'}`}>
                        <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-lia-bg-primary ${effective ? 'translate-x-4' : 'translate-x-0.5'}`} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Canal de Triagem preview */}
            <div>
              <h3 className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider px-1 mb-3">Canal de Triagem</h3>
              {(() => {
                const primaryKey = screeningConfig?.screening_channels?.primary_channel ?? 'chat_web'
                const fallbackKeys = screeningConfig?.screening_channels?.fallback_order ?? ['whatsapp']
                const primaryDef = CHANNEL_DEFS.find(c => c.key === primaryKey)
                const PrimaryIcon = primaryDef?.icon ?? Globe
                return (
                  <div className="space-y-2">
                    <div className="border border-lia-border-subtle rounded-xl p-2.5 flex items-center gap-2.5 bg-lia-bg-secondary">
                      <Star className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
                      <PrimaryIcon className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
                      <div className="flex-1">
                        <div className="text-xs font-semibold text-lia-text-primary">{primaryDef?.label ?? primaryKey}</div>
                        <div className="text-micro text-lia-text-tertiary">Canal principal</div>
                      </div>
                      {primaryDef?.comingSoon && (
                        <span className="text-micro px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-disabled rounded-xl">Em breve</span>
                      )}
                    </div>
                    {fallbackKeys.length > 0 && (
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-micro text-lia-text-disabled">Secundários:</span>
                        {fallbackKeys.map((fk, i) => {
                          const fDef = CHANNEL_DEFS.find(c => c.key === fk)
                          const FIcon = fDef?.icon ?? Globe
                          return (
                            <div key={fk} className="flex items-center gap-1">
                              {i > 0 && <ArrowRight className="w-2.5 h-2.5 text-lia-text-disabled" />}
                              <div className="flex items-center gap-1 px-1.5 py-0.5 bg-lia-bg-tertiary rounded-xl border border-lia-border-subtle">
                                <FIcon className="w-2.5 h-2.5 text-lia-text-tertiary" />
                                <span className="text-micro text-lia-text-secondary">{fDef?.label ?? fk}</span>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })()}
            </div>

            {/* Settings preview */}
            <div>
              <h3 className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider px-1 mb-3">Configurações</h3>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-lia-text-primary block mb-2">Score Mínimo Aprovação (WSI)</label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { key: 'rigorous', label: 'Rigoroso', score: '≥ 8.4/10', desc: 'Só aprovados automaticamente' },
                      { key: 'recommended', label: 'Recomendado', score: '≥ 7.6/10', desc: 'Inclui revisão manual' },
                      { key: 'flexible', label: 'Flexível', score: '≥ 6.0/10', desc: 'Todos acima do corte' },
                    ].map((preset) => {
                      const isSelected = (screeningConfig?.settings?.min_score_preset ?? 'recommended') === preset.key
                      return (
                        <div key={preset.key} className={`p-2 rounded-md border text-left ${isSelected ? 'border-lia-border-default bg-lia-bg-secondary/50' : 'border-lia-border-subtle bg-lia-bg-primary/50'}`}>
                          <div className="flex items-center justify-between mb-0.5">
                            <span className={`text-micro font-semibold ${isSelected ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`}>{preset.label}</span>
                            {isSelected && <CheckCircle className="w-3 h-3 text-lia-text-disabled" />}
                          </div>
                          <span className={`text-micro font-medium block ${isSelected ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`}>{preset.score}</span>
                          <span className="text-micro text-lia-text-disabled block mt-0.5">{preset.desc}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-lia-text-primary block mb-2">Timeout Resposta</label>
                    <div className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-secondary text-lia-text-secondary opacity-60">
                      {screeningConfig?.settings?.response_timeout_hours ?? 48}h
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-lia-text-primary block mb-2">Re-tentativas</label>
                    <div className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-secondary text-lia-text-secondary opacity-60">
                      {screeningConfig?.settings?.max_retries ?? 2}x
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Deadline preview */}
            <div className="pt-3 border-t border-lia-border-subtle">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-3.5 h-3.5 text-lia-text-disabled" />
                <span className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider">Prazo da Triagem</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-lia-text-primary block mb-2">Data Limite</label>
                  <div className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-secondary text-lia-text-secondary opacity-60">
                    {job.deadlineScreening ? new Date(String(job.deadlineScreening)).toLocaleDateString('pt-BR') : 'Não definido'}
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-lia-text-primary block mb-2">Dias Restantes</label>
                  <div className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-secondary text-lia-text-secondary opacity-60">
                    {job.deadlineScreening ? (() => { const days = Math.ceil((new Date(String(job.deadlineScreening)).getTime() - Date.now()) / (1000*60*60*24)); return days > 0 ? `${days} dias` : days === 0 ? 'Hoje' : 'Expirado' })() : '—'}
                  </div>
                </div>
              </div>
            </div>

            {/* Controle de Paralização preview */}
            <div className="pt-3 border-t border-lia-border-subtle">
              <div className="flex items-center gap-2 mb-2">
                <ShieldAlert className="w-3.5 h-3.5 text-lia-text-disabled" />
                <span className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider">Controle de Paralização</span>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-lia-text-primary block mb-2">Limite de aprovações automáticas</label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { key: 'conservative' as const, label: 'Conservador', limit: '5 aprovações', desc: 'Revisão humana frequente' },
                      { key: 'recommended' as const, label: 'Recomendado', limit: '10 aprovações', desc: 'Equilíbrio automação/supervisão' },
                      { key: 'autonomous' as const, label: 'Autônomo', limit: '25 aprovações', desc: 'Máxima automação' },
                    ].map((preset) => {
                      const currentPreset = screeningConfig?.settings?.auto_approval_preset ?? 'recommended'
                      const isSelected = currentPreset === preset.key
                      return (
                        <div key={preset.key} className={`p-2 rounded-md border text-left ${isSelected ? 'border-lia-border-default bg-lia-bg-secondary/50' : 'border-lia-border-subtle bg-lia-bg-primary/50'}`}>
                          <div className="flex items-center justify-between mb-0.5">
                            <span className={`text-micro font-semibold ${isSelected ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`}>{preset.label}</span>
                            {isSelected && <CheckCircle className="w-3 h-3 text-lia-text-disabled" />}
                          </div>
                          <span className={`text-micro font-medium block ${isSelected ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`}>{preset.limit}</span>
                          <span className="text-micro text-lia-text-disabled block mt-0.5">{preset.desc}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
                {(screeningConfig?.settings?.auto_approvals_count ?? 0) > 0 && (
                  <div className="border border-lia-border-subtle rounded-xl p-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-micro text-lia-text-disabled">Progresso atual</span>
                      <span className="text-micro font-medium text-lia-text-tertiary">
                        {screeningConfig?.settings?.auto_approvals_count ?? 0}/{screeningConfig?.settings?.auto_approval_limit ?? 10} aprovações
                      </span>
                    </div>
                    <div className="w-full h-1.5 bg-lia-bg-tertiary rounded-full mt-1">
                      <div
                        className={`h-1.5 rounded-full transition-[width,height] ${(screeningConfig?.settings?.auto_approvals_count ?? 0) >= (screeningConfig?.settings?.auto_approval_limit ?? 10) ? 'bg-status-warning' : 'bg-lia-border-default'}`}
                        style={{width: `${Math.min(100, ((screeningConfig?.settings?.auto_approvals_count ?? 0) / (screeningConfig?.settings?.auto_approval_limit ?? 10)) * 100)}%`}}
                      />
                    </div>
                  </div>
                )}
                {screeningConfig?.settings?.auto_approval_paused && (
                  <div className="flex items-center gap-1.5 px-2 py-1.5 bg-status-warning/10/50 dark:bg-status-warning/10 rounded-xl text-status-warning">
                    <AlertTriangle className="w-3 h-3" />
                    <span className="text-micro font-medium">Triagem pausada — limite atingido, aguardando revisão humana</span>
                  </div>
                )}
              </div>
            </div>

            {/* Agendamento Automático preview */}
            <div className="pt-3 border-t border-lia-border-subtle">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <CalendarCheck className="w-3.5 h-3.5 text-lia-text-disabled" />
                  <span className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider">Agendamento Automático</span>
                </div>
                <div className={`relative inline-flex h-5 w-9 items-center rounded-full ${(screeningConfig?.scheduling?.auto_enabled ?? true) ? 'bg-lia-border-medium' : 'bg-lia-interactive-active'}`}>
                  <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-lia-bg-primary ${(screeningConfig?.scheduling?.auto_enabled ?? true) ? 'translate-x-4' : 'translate-x-0.5'}`} />
                </div>
              </div>
              {(screeningConfig?.scheduling?.auto_enabled ?? true) && (
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-medium text-lia-text-primary block mb-2">Score Mínimo para Agendamento (WSI)</label>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { key: 'rigorous', label: 'Rigoroso', score: '≥ 8.4/10', desc: 'Só aprovados automaticamente' },
                        { key: 'recommended', label: 'Recomendado', score: '≥ 7.6/10', desc: 'Inclui revisão manual' },
                        { key: 'flexible', label: 'Flexível', score: '≥ 6.0/10', desc: 'Todos acima do corte' },
                      ].map((preset) => {
                        const isSelected = (screeningConfig?.scheduling?.min_score_for_auto_preset ?? 'recommended') === preset.key
                        return (
                          <div key={preset.key} className={`p-2 rounded-md border text-left ${isSelected ? 'border-lia-border-default bg-lia-bg-secondary/50' : 'border-lia-border-subtle bg-lia-bg-primary/50'}`}>
                            <div className="flex items-center justify-between mb-0.5">
                              <span className={`text-micro font-semibold ${isSelected ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`}>{preset.label}</span>
                              {isSelected && <CheckCircle className="w-3 h-3 text-lia-text-disabled" />}
                            </div>
                            <span className={`text-micro font-medium block ${isSelected ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`}>{preset.score}</span>
                            <span className="text-micro text-lia-text-disabled block mt-0.5">{preset.desc}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-xs font-medium text-lia-text-primary block mb-2">Calendário</label>
                      <div className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-secondary text-lia-text-secondary opacity-60">
                        {screeningConfig?.scheduling?.calendar_provider || 'Microsoft'}
                      </div>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-lia-text-primary block mb-2">Horários</label>
                      <div className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-secondary text-lia-text-secondary opacity-60">
                        {screeningConfig?.scheduling?.available_hours || '9h-18h'}
                      </div>
                      {(screeningConfig?.scheduling?.available_hours_inherited ?? true) && (
                        <span className="text-micro text-lia-text-disabled mt-0.5 block">Conforme config. da empresa</span>
                      )}
                    </div>
                    <div>
                      <label className="text-xs font-medium text-lia-text-primary block mb-2">Duração</label>
                      <div className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-secondary text-lia-text-secondary opacity-60">
                        {screeningConfig?.scheduling?.interview_duration_min ?? 60}min
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      )}

      {isEditingScreeningConfig && (
        <CardContent className="p-4">
          <div className="space-y-4">
            {/* Status editing */}
            <div className="px-3 py-3 rounded-xl border border-lia-border-subtle bg-lia-bg-primary">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center ${
                    statusValue === 'active' ? 'bg-status-success/15 dark:bg-status-success/30' :
                    statusValue === 'paused' ? 'bg-status-warning/15 dark:bg-status-warning/30' :
                    statusValue === 'completed' ? 'bg-wedo-cyan/15' :
                    'bg-lia-bg-tertiary'
                  }`}>
                    {statusValue === 'active' && <Play className="w-3.5 h-3.5 text-status-success" />}
                    {statusValue === 'paused' && <Pause className="w-3.5 h-3.5 text-status-warning" />}
                    {statusValue === 'completed' && <CheckCircle className="w-3.5 h-3.5 text-wedo-cyan-text" />}
                    {statusValue === 'not_started' && <Clock className="w-3.5 h-3.5 text-lia-text-secondary" />}
                    {statusValue === 'not_configured' && <AlertCircle className="w-3.5 h-3.5 text-lia-text-secondary" />}
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-lia-text-primary">Status da Triagem</span>
                    <span className={`ml-2 text-micro font-medium px-2 py-0.5 rounded-full ${
                      statusValue === 'active' ? 'bg-status-success/15 text-status-success dark:bg-status-success/30' :
                      statusValue === 'paused' ? 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30' :
                      statusValue === 'completed' ? 'bg-wedo-cyan/15 text-wedo-cyan-text' :
                      statusValue === 'not_started' ? 'bg-lia-interactive-active text-lia-text-secondary' :
                      'bg-lia-bg-tertiary text-lia-text-tertiary'
                    }`}>
                      {SCREENING_STATUS_LABELS[statusValue]}
                    </span>
                  </div>
                </div>
                {(job.screeningStatus === 'not_configured' || job.screeningStatus === 'completed') ? null : (
                  <div className="flex items-center gap-2.5">
                    <span className="text-micro text-lia-text-tertiary">{job.screeningStatus === 'active' ? 'Ativa' : 'Inativa'}</span>
                    <button
                      onClick={() => setShowScreeningToggleConfirm(job.screeningStatus === 'active' ? 'pause' : 'activate')}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors motion-reduce:transition-none duration-200 ${job.screeningStatus === 'active' ? 'bg-status-success' : 'bg-lia-border-default'}`}
                    >
                      <span className="inline-block h-3.5 w-3.5 transform rounded-full bg-lia-bg-secondary transition-transform motion-reduce:transition-none duration-200" style={{transform: job.screeningStatus === 'active' ? 'translateX(17px)' : 'translateX(2px)'}} />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Channels editing — Task #425: master toggle is now editable */}
            <div>
              <div className="flex items-center justify-between px-1 mb-3">
                <h3 className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider">Canais Habilitados</h3>
                <div className="flex items-center gap-2">
                  <span className={`text-micro font-medium ${editChannelsMasterEnabled ? 'text-lia-text-secondary' : 'text-status-error'}`}>
                    {editChannelsMasterEnabled ? 'Master ligado' : 'Master desligado'}
                  </span>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={editChannelsMasterEnabled}
                    aria-label="Master de canais"
                    onClick={() => setEditChannelsMasterEnabled(!editChannelsMasterEnabled)}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors motion-reduce:transition-none ${editChannelsMasterEnabled ? 'bg-status-success' : 'bg-lia-border-default'}`}
                  >
                    <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-lia-bg-primary transition-transform motion-reduce:transition-none ${editChannelsMasterEnabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
                  </button>
                </div>
              </div>
              {!editChannelsMasterEnabled && (
                <div className="mb-2 px-3 py-2 rounded-md border border-status-warning/30 bg-status-warning/10 text-micro text-status-warning">
                  Master desligado: nenhum canal estará disponível para o candidato, mesmo se individualmente habilitado.
                </div>
              )}
              <div className="border border-lia-border-subtle rounded-xl divide-y divide-lia-border-subtle">
                {([
                  { key: 'chat_web' as const, label: 'Chat Web', icon: Globe },
                  { key: 'whatsapp' as const, label: 'WhatsApp', icon: MessageSquare },
                  { key: 'phone_pstn' as const, label: 'Ligação (PSTN)', icon: Phone },
                  { key: 'voice_web' as const, label: 'Voz no Navegador', icon: Phone },
                ] as const).map((ch) => {
                  const ChIcon = ch.icon
                  const enabled = editChannels[ch.key]
                  return (
                    <div key={ch.key} className="px-3 py-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <ChIcon className="w-3.5 h-3.5 text-lia-text-secondary" />
                          <span className="text-xs font-medium text-lia-text-primary">{ch.label}</span>
                          {ch.key === 'phone_pstn' && !enabled && <span className="text-micro text-lia-text-disabled">(Integração pendente)</span>}
                        </div>
                        <button onClick={() => setEditChannels(prev => ({ ...prev, [ch.key]: !prev[ch.key] }))}
                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors motion-reduce:transition-none ${enabled ? 'bg-lia-btn-primary-bg' : 'bg-lia-border-default'}`}>
                          <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-lia-bg-primary transition-transform motion-reduce:transition-none ${enabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
                        </button>
                      </div>
                      {ch.key === 'whatsapp' && enabled && (
                        <div className="mt-2 ml-5">
                          <div className="text-micro text-lia-text-tertiary mb-1">Modo de envio</div>
                          <div className="grid grid-cols-3 gap-1">
                            {([
                              { key: 'wa_link' as const, label: 'Link wa.me', desc: 'Candidato clica e abre conversa' },
                              { key: 'twilio_direct' as const, label: 'Twilio WA Business', desc: 'Envio direto via API' },
                              { key: 'both' as const, label: 'Ambos', desc: 'Link + envio Twilio' },
                            ]).map(opt => {
                              const sel = editWhatsappMode === opt.key
                              return (
                                <button
                                  key={opt.key}
                                  type="button"
                                  onClick={() => setEditWhatsappMode(opt.key)}
                                  className={`text-left rounded-md border px-2 py-1.5 transition-colors motion-reduce:transition-none ${sel ? 'border-lia-btn-primary-bg bg-lia-bg-secondary ring-1 ring-lia-btn-primary-bg/30' : 'border-lia-border-subtle bg-lia-bg-primary hover:border-lia-border-default'}`}
                                  title={opt.desc}
                                >
                                  <div className={`text-micro font-semibold ${sel ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`}>{opt.label}</div>
                                  <div className="text-micro text-lia-text-disabled leading-tight">{opt.desc}</div>
                                </button>
                              )
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Canal de Triagem editing */}
            <div>
              <h3 className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider px-1 mb-1">Canal de Triagem</h3>
              <p className="text-micro text-lia-text-disabled px-1 mb-3">Escolha o canal principal e os canais secundários caso o candidato não responda</p>
              <div className="space-y-2">
                {CHANNEL_DEFS.map((ch) => {
                  const ChIcon = ch.icon
                  const isPrimary = editPrimaryChannel === ch.key
                  const fallbackIdx = editFallbackOrder.indexOf(ch.key)
                  const isInFallback = fallbackIdx !== -1
                  const isTwilioChannel = ch.key === 'phone_pstn'

                  const isUnavailable = ch.comingSoon || (isTwilioChannel && !editChannels.phone_pstn)

                  const handleSelectPrimary = () => {
                    if (isUnavailable) return
                    setEditPrimaryChannel(ch.key)
                    setEditFallbackOrder(prev => prev.filter(k => k !== ch.key))
                  }

                  const handleToggleFallback = () => {
                    if (isPrimary || isUnavailable) return
                    if (isInFallback) {
                      setEditFallbackOrder(prev => prev.filter(k => k !== ch.key))
                    } else {
                      setEditFallbackOrder(prev => [...prev, ch.key])
                    }
                  }

                  return (
                    <div
                      key={ch.key}
                      className={`border rounded-md p-2.5 transition-colors motion-reduce:transition-none ${
                        isPrimary
                          ? 'border-lia-btn-primary-bg bg-lia-bg-secondary ring-1 ring-lia-btn-primary-bg/30'
                          : 'border-lia-border-subtle bg-lia-bg-primary'
                      } ${isUnavailable ? 'opacity-60' : ''}`}
                    >
                      <div className="flex items-center gap-2.5">
                        <ChIcon className={`w-4 h-4 flex-shrink-0 ${isPrimary ? 'text-lia-text-secondary' : 'text-lia-text-tertiary'}`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className={`text-xs font-medium ${isPrimary ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`}>
                              {ch.label}
                            </span>
                            {ch.comingSoon && (
                              <span className="text-micro px-1 py-0 bg-lia-bg-tertiary text-lia-text-disabled rounded-xl">Em breve</span>
                            )}
                            {isTwilioChannel && !editChannels.phone_pstn && !ch.comingSoon && (
                              <span className="text-micro px-1 py-0 bg-status-warning/10 text-status-warning rounded-xl border border-status-warning/20">Não disponível — config. pendente</span>
                            )}
                          </div>
                          <div className="text-micro text-lia-text-disabled">{ch.desc}</div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          {!isPrimary && !isUnavailable && (
                            <button
                              onClick={handleToggleFallback}
                              className={`text-micro px-2 py-1 rounded-md border transition-colors motion-reduce:transition-none ${
                                isInFallback
                                  ? 'bg-lia-bg-tertiary border-lia-border-default text-lia-text-secondary'
                                  : 'border-lia-border-subtle text-lia-text-disabled hover:border-lia-border-default'
                              }`}
                              title={isInFallback ? `Secundário ${fallbackIdx + 1} — clique para remover` : 'Adicionar como secundário'}
                            >
                              {isInFallback ? `Secundário ${fallbackIdx + 1}` : '+ Secundário'}
                            </button>
                          )}
                          <button
                            onClick={handleSelectPrimary}
                            disabled={isUnavailable}
                            className={`text-micro px-2 py-1 rounded-md border transition-colors motion-reduce:transition-none ${
                              isPrimary
                                ? 'bg-lia-btn-primary-bg border-lia-btn-primary-bg text-lia-btn-primary-text'
                                : isUnavailable
                                ? 'border-lia-border-subtle text-lia-text-disabled cursor-not-allowed'
                                : 'border-lia-border-subtle text-lia-text-secondary hover:border-lia-border-default hover:text-lia-text-primary'
                            }`}
                          >
                            {isPrimary ? '★ Principal' : 'Definir principal'}
                          </button>
                        </div>
                      </div>
                      {isInFallback && !isPrimary && editFallbackOrder.length > 1 && (
                        <div className="mt-1.5 flex items-center gap-1">
                          <span className="text-micro text-lia-text-disabled">Posição entre os secundários:</span>
                          <div className="flex items-center gap-0.5">
                            {editFallbackOrder.map((fk, i) => (
                              <span key={fk} className={`text-micro px-1 py-0 rounded ${fk === ch.key ? 'bg-lia-border-default text-white' : 'text-lia-text-disabled'}`}>
                                {i + 1}°
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Settings editing */}
            <div>
              <h3 className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider px-1 mb-3">Configurações</h3>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-lia-text-primary block mb-2">Score Mínimo Aprovação (WSI)</label>
                  <div className="grid grid-cols-3 gap-2">
                    {([
                      { key: 'rigorous' as const, label: 'Rigoroso', score: '≥ 8.4/10', desc: 'Só aprovados automaticamente' },
                      { key: 'recommended' as const, label: 'Recomendado', score: '≥ 7.6/10', desc: 'Inclui revisão manual' },
                      { key: 'flexible' as const, label: 'Flexível', score: '≥ 6.0/10', desc: 'Todos acima do corte' },
                    ] as const).map((preset) => {
                      const isSelected = editMinScorePreset === preset.key
                      return (
                        <button key={preset.key} onClick={() => setEditMinScorePreset(preset.key)}
                          className={`p-2 rounded-md border text-left transition-colors motion-reduce:transition-none ${isSelected ? 'border-lia-btn-primary-bg bg-lia-bg-secondary ring-1 ring-lia-btn-primary-bg' : 'border-lia-border-subtle bg-lia-bg-primary hover:border-lia-border-default'}`}>
                          <div className="flex items-center justify-between mb-0.5">
                            <span className={`text-micro font-semibold ${isSelected ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`}>{preset.label}</span>
                            {isSelected && <CheckCircle className="w-3 h-3 text-lia-text-primary" />}
                          </div>
                          <span className="text-micro font-medium text-lia-text-primary block">{preset.score}</span>
                          <span className="text-micro text-lia-text-tertiary block mt-0.5">{preset.desc}</span>
                        </button>
                      )
                    })}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-lia-text-primary block mb-2">Timeout Resposta</label>
                    <select value={editTimeoutHours} onChange={(e) => setEditTimeoutHours(Number(e.target.value))} className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-secondary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none">
                      {[12, 24, 48, 72].map(h => (<option key={h} value={h}>{h}h</option>))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-lia-text-primary block mb-2">Re-tentativas</label>
                    <select value={editMaxRetries} onChange={(e) => setEditMaxRetries(Number(e.target.value))} className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-secondary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none">
                      {[1, 2, 3, 4, 5].map(n => (<option key={n} value={n}>{n}x</option>))}
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Controle de Paralização editing */}
            <div className="pt-3 border-t border-lia-border-subtle">
              <div className="flex items-center gap-2 mb-2">
                <ShieldAlert className="w-3.5 h-3.5 text-lia-text-tertiary" />
                <span className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider">Controle de Paralização</span>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-lia-text-primary block mb-2">Limite de aprovações automáticas</label>
                  <div className="grid grid-cols-3 gap-2">
                    {([
                      { key: 'conservative' as const, label: 'Conservador', limit: '5 aprovações', desc: 'Revisão humana frequente' },
                      { key: 'recommended' as const, label: 'Recomendado', limit: '10 aprovações', desc: 'Equilíbrio automação/supervisão' },
                      { key: 'autonomous' as const, label: 'Autônomo', limit: '25 aprovações', desc: 'Máxima automação' },
                    ] as const).map((preset) => {
                      const isSelected = editAutoApprovalPreset === preset.key
                      return (
                        <button key={preset.key} onClick={() => setEditAutoApprovalPreset(preset.key)}
                          className={`p-2 rounded-md border text-left transition-colors motion-reduce:transition-none ${isSelected ? 'border-lia-btn-primary-bg bg-lia-bg-secondary ring-1 ring-lia-btn-primary-bg' : 'border-lia-border-subtle bg-lia-bg-primary hover:border-lia-border-default'}`}>
                          <div className="flex items-center justify-between mb-0.5">
                            <span className={`text-micro font-semibold ${isSelected ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`}>{preset.label}</span>
                            {isSelected && <CheckCircle className="w-3 h-3 text-lia-text-primary" />}
                          </div>
                          <span className="text-micro font-medium text-lia-text-primary block">{preset.limit}</span>
                          <span className="text-micro text-lia-text-tertiary block mt-0.5">{preset.desc}</span>
                        </button>
                      )
                    })}
                  </div>
                </div>
                {(screeningConfig?.settings?.auto_approvals_count ?? 0) > 0 && (
                  <div className="border border-lia-border-subtle rounded-xl p-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-micro text-lia-text-tertiary">Progresso atual</span>
                      <span className="text-micro font-medium text-lia-text-secondary">
                        {screeningConfig?.settings?.auto_approvals_count ?? 0}/{approvalPresetToLimit(editAutoApprovalPreset)} aprovações
                      </span>
                    </div>
                    <div className="w-full h-1.5 bg-lia-bg-tertiary rounded-full mt-1">
                      <div
                        className={`h-1.5 rounded-full transition-[width,height] ${(screeningConfig?.settings?.auto_approvals_count ?? 0) >= approvalPresetToLimit(editAutoApprovalPreset) ? 'bg-status-warning' : 'bg-lia-border-medium'}`}
                        style={{width: `${Math.min(100, ((screeningConfig?.settings?.auto_approvals_count ?? 0) / approvalPresetToLimit(editAutoApprovalPreset)) * 100)}%`}}
                      />
                    </div>
                  </div>
                )}
                {screeningConfig?.settings?.auto_approval_paused && (
                  <div className="flex items-center gap-1.5 px-2 py-1.5 bg-status-warning/10 dark:bg-status-warning/20 rounded-xl text-status-warning">
                    <AlertTriangle className="w-3 h-3" />
                    <span className="text-micro font-medium">Triagem pausada — limite atingido</span>
                    <button onClick={() => {}} className="ml-auto text-micro font-medium text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse underline">Retomar</button>
                  </div>
                )}
              </div>
            </div>

            {/* Prazo da Triagem editing */}
            <div className="pt-3 border-t border-lia-border-subtle">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider">Prazo da Triagem</span>
              </div>
              <div>
                <label className="text-xs font-medium text-lia-text-primary block mb-2">Data Limite</label>
                <input
                  type="date"
                  value={job.deadlineScreening ? new Date(String(job.deadlineScreening)).toISOString().split('T')[0] : ''}
                  onChange={(e) => onJobUpdate?.({ ...job, deadlineScreening: e.target.value || null })}
                  className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary text-lia-text-primary"
                />
              </div>
            </div>

            {/* Agendamento editing */}
            <div className="pt-3 border-t border-lia-border-subtle">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <CalendarCheck className="w-3.5 h-3.5 text-lia-text-tertiary" />
                  <span className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider">Agendamento Automático</span>
                </div>
                <button onClick={() => setEditSchedulingEnabled(!editSchedulingEnabled)}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors motion-reduce:transition-none ${editSchedulingEnabled ? 'bg-lia-btn-primary-bg' : 'bg-lia-border-default'}`}>
                  <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-lia-bg-primary transition-transform motion-reduce:transition-none ${editSchedulingEnabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
                </button>
              </div>
              {editSchedulingEnabled && (
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-medium text-lia-text-primary block mb-2">Score Mínimo para Agendamento (WSI)</label>
                    <div className="grid grid-cols-3 gap-2">
                      {([
                        { key: 'rigorous' as const, label: 'Rigoroso', score: '≥ 8.4/10', desc: 'Só aprovados automaticamente' },
                        { key: 'recommended' as const, label: 'Recomendado', score: '≥ 7.6/10', desc: 'Inclui revisão manual' },
                        { key: 'flexible' as const, label: 'Flexível', score: '≥ 6.0/10', desc: 'Todos acima do corte' },
                      ] as const).map((preset) => {
                        const isSelected = editSchedulingMinScorePreset === preset.key
                        return (
                          <button key={preset.key} onClick={() => setEditSchedulingMinScorePreset(preset.key)}
                            className={`p-2 rounded-md border text-left transition-colors motion-reduce:transition-none ${isSelected ? 'border-lia-btn-primary-bg bg-lia-bg-secondary ring-1 ring-lia-btn-primary-bg' : 'border-lia-border-subtle bg-lia-bg-primary hover:border-lia-border-default'}`}>
                            <div className="flex items-center justify-between mb-0.5">
                              <span className={`text-micro font-semibold ${isSelected ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`}>{preset.label}</span>
                              {isSelected && <CheckCircle className="w-3 h-3 text-lia-text-primary" />}
                            </div>
                            <span className="text-micro font-medium text-lia-text-primary block">{preset.score}</span>
                            <span className="text-micro text-lia-text-tertiary block mt-0.5">{preset.desc}</span>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-xs font-medium text-lia-text-primary block mb-2">Calendário</label>
                      <select value={editCalendarProvider} onChange={(e) => setEditCalendarProvider(e.target.value)} className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-secondary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none">
                        <option value="Microsoft">Microsoft</option>
                        <option value="Google">Google</option>
                        <option value="Outlook">Outlook</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-lia-text-primary block mb-2">Horários</label>
                      <input type="text" value={editAvailableHours} onChange={(e) => { setEditAvailableHours(e.target.value); setEditAvailableHoursInherited(false) }} className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-secondary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none" />
                      {editAvailableHoursInherited && <span className="text-micro text-lia-text-disabled mt-0.5 block">Conforme config. da empresa</span>}
                    </div>
                    <div>
                      <label className="text-xs font-medium text-lia-text-primary block mb-2">Duração</label>
                      <select value={editInterviewDuration} onChange={(e) => setEditInterviewDuration(Number(e.target.value))} className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-secondary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none">
                        {[30, 45, 60, 90].map(d => (<option key={d} value={d}>{d}min</option>))}
                      </select>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  )
}
