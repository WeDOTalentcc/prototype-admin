"use client"

import React, { useState, useCallback, useMemo, useRef } from "react"
import { cn } from "@/lib/utils"
import { SCREENING_STATUS_LABELS, type ScreeningStatus } from "@/types/screening"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Progress } from "@/components/ui/progress"
import { toast } from 'sonner'
import {
  AlertCircle, AlertTriangle, Archive, Brain, Calendar, CalendarCheck,
  CheckCircle, CheckCircle2, ChevronDown, ChevronUp, Clock,
  Gauge, Globe, GraduationCap, Loader2, MessageSquare, Pause, Phone, Play, Scale, ShieldAlert, Target, X
} from "lucide-react"
import { approvalPresetToLimit } from '@/hooks/useScreeningConfig'
import { WSI_BLOCKS, WSI_AUTOMATIC_MESSAGES, formatMessageWithVariables, getBloomComplexity, getEstimatedTime } from '@/components/jobs/jobsPageConstants'
import { JDEvaluationPanel } from '@/components/wsi'
import { CompanyBankQuestions } from './CompanyBankQuestions'
import { CompanyDefaultQuestions } from './CompanyDefaultQuestions'
import { CustomQuestions } from './CustomQuestions'
import type { CustomQuestion } from './CustomQuestions'
import { useScreeningConfigManagerCore } from "./hooks/useScreeningConfigManagerCore"
import type { ScreeningQuestionItem } from './SCMScreeningTypes'
import { SCMQuestionDetailView } from './SCMQuestionDetail'

type SCMSectionContentProps = ReturnType<typeof useScreeningConfigManagerCore>

export function SCMSectionContent(props: SCMSectionContentProps) {
  const { SectionIcon, acceptedQuestions, activeSection, bankQuestionOverrides, companyQuestions, screeningConfig,
    customQuestions, deactivatedQuestions, disabledCompanyQIds, editAutoApprovalPreset, editAvailableHours, editAvailableHoursInherited,
    editCalendarProvider, editChannels, editInterviewDuration, editMaxRetries, editMinScorePreset, editSchedulingEnabled, editSchedulingMinScorePreset, editTimeoutHours,
    expandedBlocks, expandedQuestionDetails, generatedQuestions, handleAddCustomQuestion, handleGenerateWSI, handleRemoveCustomQuestion,
    handleToggleBankQuestion, handleToggleCompanyDefault, handleUpdateBankQuestion, handleUpdateCustomQuestion, isEditingScreening, isEditingScreeningConfig, isGeneratingWSI,
    resetScreeningEditing, selectedBankQuestions, setAcceptedQuestions, setActiveSection, setDeactivatedQuestions,
    setEditAutoApprovalPreset, setEditAvailableHours, setEditAvailableHoursInherited, setEditCalendarProvider, setEditChannels, setEditInterviewDuration, setEditMaxRetries, setEditMinScorePreset,
    setEditSchedulingEnabled, setEditSchedulingMinScorePreset, setEditTimeoutHours, setExpandedBlocks, setExpandedQuestionDetails, setGeneratedQuestions,
    setShowScreeningToggleConfirm, setWsiDynamicMessage, setWsiGenerationCompleted, setWsiGenerationContext, setWsiGenerationStep, setWsiProgressCollapsed, setWsiSummaryExpanded,
    wsiDynamicMessage, wsiGeneratedCount, wsiGenerationCompleted, wsiGenerationContext, wsiGenerationMode, wsiGenerationStep, wsiProgressCollapsed, wsiSummaryExpanded,
    wsiSummaryTypedText, wsiSummaryTypingDone, wsiTypedMessage, job, onJobUpdate } = props

  return (
    <>
{activeSection === 'configuracoes' && (
  <>
  <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
  {!isEditingScreeningConfig && (
    <CardContent className="p-4">
      <div className="space-y-4">
        <div className="px-3 py-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50/50 dark:bg-lia-bg-secondary/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center ${
 (job.screeningStatus || 'not_configured') === 'active' ? 'bg-status-success/15 dark:bg-status-success/30' :
                (job.screeningStatus || 'not_configured') === 'paused' ? 'bg-status-warning/15 dark:bg-status-warning/30' :
                (job.screeningStatus || 'not_configured') === 'completed' ? 'bg-wedo-cyan/15' :
                'bg-gray-100 dark:bg-lia-bg-secondary'
              }`}>
                {(job.screeningStatus || 'not_configured') === 'active' && <Play className="w-3.5 h-3.5 text-status-success" />}
                {(job.screeningStatus || 'not_configured') === 'paused' && <Pause className="w-3.5 h-3.5 text-status-warning" />}
                {(job.screeningStatus || 'not_configured') === 'completed' && <CheckCircle className="w-3.5 h-3.5 text-wedo-cyan-dark" />}
                {(job.screeningStatus || 'not_configured') === 'not_started' && <Clock className="w-3.5 h-3.5 lia-text-secondary" />}
                {(job.screeningStatus || 'not_configured') === 'not_configured' && <AlertCircle className="w-3.5 h-3.5 lia-text-secondary" />}
              </div>
              <div>
                <span className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary">Status da Triagem</span>
                <span className={`ml-2 text-micro font-medium px-2 py-0.5 rounded-full ${
 (job.screeningStatus || 'not_configured') === 'active' ? 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success' :
                  (job.screeningStatus || 'not_configured') === 'paused' ? 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning' :
                  (job.screeningStatus || 'not_configured') === 'completed' ? 'bg-wedo-cyan/15 text-wedo-cyan-dark dark:text-wedo-cyan-dark' :
                  (job.screeningStatus || 'not_configured') === 'not_started' ? 'bg-gray-200 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary' :
                  'bg-gray-100 text-lia-text-tertiary dark:bg-lia-bg-secondary'
                }`}>
                  {SCREENING_STATUS_LABELS[(job.screeningStatus || 'not_configured') as ScreeningStatus]}
                </span>
              </div>
            </div>
            {(job.screeningStatus === 'not_configured' || job.screeningStatus === 'completed') ? null : (
              <div className="flex items-center gap-2.5 opacity-50 cursor-not-allowed" title="Clique em Editar Configurações para alterar">
                <span className="text-micro text-lia-text-disabled" >
                  {job.screeningStatus === 'active' ? 'Ativa' : 'Inativa'}
                </span>
                <div className={`relative inline-flex h-5 w-9 items-center rounded-full ${
 job.screeningStatus === 'active' ? 'bg-status-success' : 'bg-gray-200 dark:bg-lia-bg-elevated'
                }`}>
                  <span
                    className="inline-block h-3.5 w-3.5 transform rounded-full bg-lia-bg-secondary"
                    style={{transform: job.screeningStatus === 'active' ? 'translateX(17px)' : 'translateX(2px)'}}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
        <div>
          <h3 className="text-xs font-semibold text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wider px-1 font-['Open_Sans',sans-serif] mb-3">Canais</h3>
          <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md divide-y divide-gray-100 dark:divide-gray-700">
            {[
              { key: 'whatsapp', label: 'WhatsApp', icon: MessageSquare, enabled: screeningConfig?.channels?.whatsapp?.enabled ?? true },
              { key: 'chat_web', label: 'Chat Web', icon: Globe, enabled: screeningConfig?.channels?.chat_web?.enabled ?? true },
              { key: 'phone', label: 'Ligação', icon: Phone, enabled: screeningConfig?.channels?.phone?.enabled ?? false },
            ].map((ch) => {
              const ChIcon = ch.icon
              return (
                <div key={ch.key} className="flex items-center justify-between px-3 py-2">
                  <div className="flex items-center gap-2">
                    <ChIcon className="w-3.5 h-3.5 text-lia-text-disabled" />
                    <span className="text-xs font-medium text-lia-text-secondary dark:text-lia-text-tertiary" >{ch.label}</span>
                    {ch.key === 'phone' && !ch.enabled && (
                      <span className="text-micro text-lia-text-disabled">(Integração pendente)</span>
                    )}
                  </div>
                  <div className={`relative inline-flex h-5 w-9 items-center rounded-full ${ch.enabled ? 'bg-gray-400' : 'bg-gray-200 dark:bg-lia-bg-elevated'}`}>
                    <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white dark:bg-lia-bg-primary ${ch.enabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div>
          <h3 className="text-xs font-semibold text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wider px-1 font-['Open_Sans',sans-serif] mb-3">Configurações</h3>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Score Mínimo Aprovação (WSI)</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { key: 'rigorous', label: 'Rigoroso', score: '≥ 4.2/5.0', desc: 'Só aprovados automaticamente' },
                  { key: 'recommended', label: 'Recomendado', score: '≥ 3.8/5.0', desc: 'Inclui revisão manual' },
                  { key: 'flexible', label: 'Flexível', score: '≥ 3.0/5.0', desc: 'Todos acima do corte' },
                ].map((preset) => {
                  const isSelected = (screeningConfig?.settings?.min_score_preset ?? 'recommended') === preset.key
                  return (
                    <div key={preset.key} className={`p-2 rounded-md border text-left ${isSelected ? 'border-lia-border-default bg-gray-50/50' : 'border-lia-border-subtle bg-white dark:border-lia-border-subtle dark:bg-lia-bg-secondary/50'}`}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className={`text-micro font-semibold ${isSelected ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`} >{preset.label}</span>
                        {isSelected && <CheckCircle className="w-3 h-3 text-lia-text-disabled" />}
                      </div>
                      <span className={`text-micro font-medium block ${isSelected ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`} >{preset.score}</span>
                      <span className="text-micro text-lia-text-disabled block mt-0.5">{preset.desc}</span>
                    </div>
                  )
                })}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Timeout Resposta</label>
                <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-gray-50 dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary opacity-60">
                  {screeningConfig?.settings?.response_timeout_hours ?? 48}h
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Re-tentativas</label>
                <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-gray-50 dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary opacity-60">
                  {screeningConfig?.settings?.max_retries ?? 2}x
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-2 mb-2">
            <Calendar className="w-3.5 h-3.5 text-lia-text-disabled" />
            <span className="text-xs font-semibold text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wider font-['Open_Sans',sans-serif]">Prazo da Triagem</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Data Limite</label>
              <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-gray-50 dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary opacity-60">
                {job.deadlineScreening ? new Date(job.deadlineScreening).toLocaleDateString('pt-BR') : 'Não definido'}
              </div>
            </div>
            <div>
              <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Dias Restantes</label>
              <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-gray-50 dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary opacity-60">
                {job.deadlineScreening ? (() => { const days = Math.ceil((new Date(job.deadlineScreening).getTime() - Date.now()) / (1000*60*60*24)); return days > 0 ? `${days} dias` : days === 0 ? 'Hoje' : 'Expirado' })() : '—'}
              </div>
            </div>
          </div>
        </div>

        {/* Controle de Paralização preview */}
        <div className="pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-2 mb-2">
            <ShieldAlert className="w-3.5 h-3.5 text-lia-text-disabled" />
            <span className="text-xs font-semibold text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wider font-['Open_Sans',sans-serif]">Controle de Paralização</span>
          </div>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Limite de aprovações automáticas</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { key: 'conservative' as const, label: 'Conservador', limit: '5 aprovações', desc: 'Revisão humana frequente' },
                  { key: 'recommended' as const, label: 'Recomendado', limit: '10 aprovações', desc: 'Equilíbrio automação/supervisão' },
                  { key: 'autonomous' as const, label: 'Autônomo', limit: '25 aprovações', desc: 'Máxima automação' },
                ].map((preset) => {
                  const currentPreset = screeningConfig?.settings?.auto_approval_preset ?? 'recommended'
                  const isSelected = currentPreset === preset.key
                  return (
                    <div key={preset.key} className={`p-2 rounded-md border text-left ${isSelected ? 'border-lia-border-default bg-gray-50/50' : 'border-lia-border-subtle bg-white dark:border-lia-border-subtle dark:bg-lia-bg-secondary/50'}`}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className={`text-micro font-semibold ${isSelected ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`} >{preset.label}</span>
                        {isSelected && <CheckCircle className="w-3 h-3 text-lia-text-disabled" />}
                      </div>
                      <span className={`text-micro font-medium block ${isSelected ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`} >{preset.limit}</span>
                      <span className="text-micro text-lia-text-disabled block mt-0.5">{preset.desc}</span>
                    </div>
                  )
                })}
              </div>
            </div>
            {(screeningConfig?.settings?.auto_approvals_count ?? 0) > 0 && (
              <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-micro text-lia-text-disabled">Progresso atual</span>
                  <span className="text-micro font-medium text-lia-text-tertiary dark:text-lia-text-tertiary" >
                    {screeningConfig?.settings?.auto_approvals_count ?? 0}/{screeningConfig?.settings?.auto_approval_limit ?? 10} aprovações
                  </span>
                </div>
                <div className="w-full h-1.5 bg-gray-100 dark:bg-lia-bg-elevated rounded-full mt-1">
                  <div
                    className={`h-1.5 rounded-full transition-[width,height] ${(screeningConfig?.settings?.auto_approvals_count ?? 0) >= (screeningConfig?.settings?.auto_approval_limit ?? 10) ? 'bg-status-warning' : 'bg-gray-300'}`}
                    style={{width: `${Math.min(100, ((screeningConfig?.settings?.auto_approvals_count ?? 0) / (screeningConfig?.settings?.auto_approval_limit ?? 10)) * 100)}%`}}
                  />
                </div>
              </div>
            )}
            {screeningConfig?.settings?.auto_approval_paused && (
              <div className="flex items-center gap-1.5 px-2 py-1.5 bg-status-warning/10/50 dark:bg-status-warning/10 rounded-md text-status-warning dark:text-status-warning">
                <AlertTriangle className="w-3 h-3" />
                <span className="text-micro font-medium" >Triagem pausada — limite atingido, aguardando revisão humana</span>
              </div>
            )}
          </div>
        </div>

        {/* Agendamento Automático preview */}
        <div className="pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <CalendarCheck className="w-3.5 h-3.5 text-lia-text-disabled" />
              <span className="text-xs font-semibold text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wider font-['Open_Sans',sans-serif]">Agendamento Automático</span>
            </div>
            <div className={`relative inline-flex h-5 w-9 items-center rounded-full ${(screeningConfig?.scheduling?.auto_enabled ?? true) ? 'bg-gray-400' : 'bg-gray-200 dark:bg-lia-bg-elevated'}`}>
              <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white dark:bg-lia-bg-primary ${(screeningConfig?.scheduling?.auto_enabled ?? true) ? 'translate-x-4' : 'translate-x-0.5'}`} />
            </div>
          </div>
          {(screeningConfig?.scheduling?.auto_enabled ?? true) && (
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Score Mínimo para Agendamento (WSI)</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { key: 'rigorous', label: 'Rigoroso', score: '≥ 4.2/5.0', desc: 'Só aprovados automaticamente' },
                    { key: 'recommended', label: 'Recomendado', score: '≥ 3.8/5.0', desc: 'Inclui revisão manual' },
                    { key: 'flexible', label: 'Flexível', score: '≥ 3.0/5.0', desc: 'Todos acima do corte' },
                  ].map((preset) => {
                    const isSelected = (screeningConfig?.scheduling?.min_score_for_auto_preset ?? 'recommended') === preset.key
                    return (
                      <div key={preset.key} className={`p-2 rounded-md border text-left ${isSelected ? 'border-lia-border-default bg-gray-50/50' : 'border-lia-border-subtle bg-white dark:border-lia-border-subtle dark:bg-lia-bg-secondary/50'}`}>
                        <div className="flex items-center justify-between mb-0.5">
                          <span className={`text-micro font-semibold ${isSelected ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`} >{preset.label}</span>
                          {isSelected && <CheckCircle className="w-3 h-3 text-lia-text-disabled" />}
                        </div>
                        <span className={`text-micro font-medium block ${isSelected ? 'text-lia-text-secondary' : 'text-lia-text-disabled'}`} >{preset.score}</span>
                        <span className="text-micro text-lia-text-disabled block mt-0.5">{preset.desc}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Calendário</label>
                  <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-gray-50 dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary opacity-60">
                    {screeningConfig?.scheduling?.calendar_provider || 'Microsoft'}
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Horários</label>
                  <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-gray-50 dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary opacity-60">
                    {screeningConfig?.scheduling?.available_hours || '9h-18h'}
                  </div>
                  {(screeningConfig?.scheduling?.available_hours_inherited ?? true) && (
                    <span className="text-micro text-lia-text-disabled mt-0.5 block">Conforme config. da empresa</span>
                  )}
                </div>
                <div>
                  <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Duração</label>
                  <div className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-gray-50 dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary opacity-60">
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
        <div className="px-3 py-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-primary">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center ${
 (job.screeningStatus || 'not_configured') === 'active' ? 'bg-status-success/15 dark:bg-status-success/30' :
                (job.screeningStatus || 'not_configured') === 'paused' ? 'bg-status-warning/15 dark:bg-status-warning/30' :
                (job.screeningStatus || 'not_configured') === 'completed' ? 'bg-wedo-cyan/15' :
                'bg-gray-100 dark:bg-lia-bg-secondary'
              }`}>
                {(job.screeningStatus || 'not_configured') === 'active' && <Play className="w-3.5 h-3.5 text-status-success" />}
                {(job.screeningStatus || 'not_configured') === 'paused' && <Pause className="w-3.5 h-3.5 text-status-warning" />}
                {(job.screeningStatus || 'not_configured') === 'completed' && <CheckCircle className="w-3.5 h-3.5 text-wedo-cyan-dark" />}
                {(job.screeningStatus || 'not_configured') === 'not_started' && <Clock className="w-3.5 h-3.5 lia-text-secondary" />}
                {(job.screeningStatus || 'not_configured') === 'not_configured' && <AlertCircle className="w-3.5 h-3.5 lia-text-secondary" />}
              </div>
              <div>
                <span className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary">Status da Triagem</span>
                <span className={`ml-2 text-micro font-medium px-2 py-0.5 rounded-full ${
 (job.screeningStatus || 'not_configured') === 'active' ? 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success' :
                  (job.screeningStatus || 'not_configured') === 'paused' ? 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning' :
                  (job.screeningStatus || 'not_configured') === 'completed' ? 'bg-wedo-cyan/15 text-wedo-cyan-dark dark:text-wedo-cyan-dark' :
                  (job.screeningStatus || 'not_configured') === 'not_started' ? 'bg-gray-200 text-lia-text-secondary dark:bg-lia-bg-elevated dark:text-lia-text-secondary' :
                  'bg-gray-100 text-lia-text-tertiary dark:bg-lia-bg-secondary'
                }`}>
                  {SCREENING_STATUS_LABELS[(job.screeningStatus || 'not_configured') as ScreeningStatus]}
                </span>
              </div>
            </div>
            {(job.screeningStatus === 'not_configured' || job.screeningStatus === 'completed') ? null : (
              <div className="flex items-center gap-2.5">
                <span className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary" >
                  {job.screeningStatus === 'active' ? 'Ativa' : 'Inativa'}
                </span>
                <button
                  onClick={() => {
                    if (job.screeningStatus === 'active') {
                      setShowScreeningToggleConfirm('pause')
                    } else {
                      setShowScreeningToggleConfirm('activate')
                    }
                  }}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200 ${
 job.screeningStatus === 'active' ? 'bg-status-success' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className="inline-block h-3.5 w-3.5 transform rounded-full bg-lia-bg-secondary transition-transform duration-200"
                    style={{transform: job.screeningStatus === 'active' ? 'translateX(17px)' : 'translateX(2px)'}}
                  />
                </button>
              </div>
            )}
          </div>
        </div>
        <div>
          <h3 className="text-xs font-semibold text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wider px-1 font-['Open_Sans',sans-serif] mb-3">Canais</h3>
          <div className="border border-lia-border-subtle dark:border-lia-border-default rounded-md divide-y divide-gray-200 dark:divide-gray-600">
            {[
              { key: 'whatsapp' as const, label: 'WhatsApp', icon: MessageSquare },
              { key: 'chat_web' as const, label: 'Chat Web', icon: Globe },
              { key: 'phone' as const, label: 'Ligação', icon: Phone },
            ].map((ch) => {
              const ChIcon = ch.icon
              const enabled = editChannels[ch.key]
              return (
                <div key={ch.key} className="flex items-center justify-between px-3 py-2">
                  <div className="flex items-center gap-2">
                    <ChIcon className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                    <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary" >{ch.label}</span>
                    {ch.key === 'phone' && !enabled && (
                      <span className="text-micro text-lia-text-disabled">(Integração pendente)</span>
                    )}
                  </div>
                  <button
                    onClick={() => setEditChannels(prev => ({ ...prev, [ch.key]: !prev[ch.key] }))}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${enabled ? 'bg-gray-900' : 'bg-gray-300'}`}
                  >
                    <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white dark:bg-lia-bg-primary transition-transform ${enabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
                  </button>
                </div>
              )
            })}
          </div>
        </div>

        <div>
          <h3 className="text-xs font-semibold text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wider px-1 font-['Open_Sans',sans-serif] mb-3">Configurações</h3>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Score Mínimo Aprovação (WSI)</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { key: 'rigorous' as const, label: 'Rigoroso', score: '≥ 4.2/5.0', desc: 'Só aprovados automaticamente' },
                  { key: 'recommended' as const, label: 'Recomendado', score: '≥ 3.8/5.0', desc: 'Inclui revisão manual' },
                  { key: 'flexible' as const, label: 'Flexível', score: '≥ 3.0/5.0', desc: 'Todos acima do corte' },
                ].map((preset) => {
                  const isSelected = editMinScorePreset === preset.key
                  return (
                    <button key={preset.key} onClick={() => setEditMinScorePreset(preset.key)} className={`p-2 rounded-md border text-left transition-colors ${isSelected ? 'border-gray-900 bg-gray-50 ring-1 ring-gray-900 dark:ring-gray-300' : 'border-lia-border-subtle bg-white hover:border-lia-border-default dark:border-lia-border-default dark:bg-lia-bg-secondary dark:hover:border-gray-500'}`}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className={`text-micro font-semibold ${isSelected ? 'text-lia-text-primary' : 'text-lia-text-secondary dark:text-lia-text-tertiary'}`} >{preset.label}</span>
                        {isSelected && <CheckCircle className="w-3 h-3 text-lia-text-primary dark:text-lia-text-secondary" />}
                      </div>
                      <span className="text-micro font-medium text-lia-text-primary dark:text-lia-text-primary block" >{preset.score}</span>
                      <span className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary block mt-0.5">{preset.desc}</span>
                    </button>
                  )
                })}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Timeout Resposta</label>
                <select value={editTimeoutHours} onChange={(e) => setEditTimeoutHours(Number(e.target.value))} className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-secondary focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors">
                  {[12, 24, 48, 72].map(h => (<option key={h} value={h}>{h}h</option>))}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Re-tentativas</label>
                <select value={editMaxRetries} onChange={(e) => setEditMaxRetries(Number(e.target.value))} className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-secondary focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors">
                  {[1, 2, 3, 4, 5].map(n => (<option key={n} value={n}>{n}x</option>))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Controle de Paralização editing */}
        <div className="pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-2 mb-2">
            <ShieldAlert className="w-3.5 h-3.5 text-lia-text-tertiary dark:text-lia-text-tertiary" />
            <span className="text-xs font-semibold text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wider font-['Open_Sans',sans-serif]">Controle de Paralização</span>
          </div>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Limite de aprovações automáticas</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { key: 'conservative' as const, label: 'Conservador', limit: '5 aprovações', desc: 'Revisão humana frequente' },
                  { key: 'recommended' as const, label: 'Recomendado', limit: '10 aprovações', desc: 'Equilíbrio automação/supervisão' },
                  { key: 'autonomous' as const, label: 'Autônomo', limit: '25 aprovações', desc: 'Máxima automação' },
                ].map((preset) => {
                  const isSelected = editAutoApprovalPreset === preset.key
                  return (
                    <button key={preset.key} onClick={() => setEditAutoApprovalPreset(preset.key)} className={`p-2 rounded-md border text-left transition-colors ${isSelected ? 'border-gray-900 bg-gray-50 ring-1 ring-gray-900 dark:ring-gray-300' : 'border-lia-border-subtle bg-white hover:border-lia-border-default dark:border-lia-border-default dark:bg-lia-bg-secondary dark:hover:border-gray-500'}`}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className={`text-micro font-semibold ${isSelected ? 'text-lia-text-primary' : 'text-lia-text-secondary dark:text-lia-text-tertiary'}`} >{preset.label}</span>
                        {isSelected && <CheckCircle className="w-3 h-3 text-lia-text-primary dark:text-lia-text-secondary" />}
                      </div>
                      <span className="text-micro font-medium text-lia-text-primary dark:text-lia-text-primary block" >{preset.limit}</span>
                      <span className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary block mt-0.5">{preset.desc}</span>
                    </button>
                  )
                })}
              </div>
            </div>
            {(screeningConfig?.settings?.auto_approvals_count ?? 0) > 0 && (
              <div className="border border-lia-border-subtle dark:border-lia-border-default rounded-md p-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary">Progresso atual</span>
                  <span className="text-micro font-medium text-lia-text-secondary dark:text-lia-text-secondary" >
                    {screeningConfig?.settings?.auto_approvals_count ?? 0}/{approvalPresetToLimit(editAutoApprovalPreset)} aprovações
                  </span>
                </div>
                <div className="w-full h-1.5 bg-gray-100 dark:bg-lia-bg-elevated rounded-full mt-1">
                  <div
                    className={`h-1.5 rounded-full transition-[width,height] ${(screeningConfig?.settings?.auto_approvals_count ?? 0) >= approvalPresetToLimit(editAutoApprovalPreset) ? 'bg-status-warning' : 'bg-gray-400'}`}
                    style={{width: `${Math.min(100, ((screeningConfig?.settings?.auto_approvals_count ?? 0) / approvalPresetToLimit(editAutoApprovalPreset)) * 100)}%`}}
                  />
                </div>
              </div>
            )}
            {screeningConfig?.settings?.auto_approval_paused && (
              <div className="flex items-center gap-1.5 px-2 py-1.5 bg-status-warning/10 dark:bg-status-warning/20 rounded-md text-status-warning dark:text-status-warning">
                <AlertTriangle className="w-3 h-3" />
                <span className="text-micro font-medium" >Triagem pausada — limite atingido</span>
                <button onClick={() => {}} className="ml-auto text-micro font-medium text-lia-text-secondary dark:text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse underline" >
                  Retomar
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="pt-3 border-t border-lia-border-subtle dark:border-lia-border-default">
          <div className="flex items-center gap-2 mb-2">
            <Calendar className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            <span className="text-xs font-semibold text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wider font-['Open_Sans',sans-serif]">Prazo da Triagem</span>
          </div>
          <div>
            <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Data Limite</label>
            <input
              type="date"
              value={job.deadlineScreening ? new Date(job.deadlineScreening).toISOString().split('T')[0] : ''}
              onChange={(e) => onJobUpdate?.({ ...job, deadlineScreening: e.target.value || null })}
              className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-white dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary"
            />
          </div>
        </div>

        {/* Agendamento editing */}
        <div className="pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <CalendarCheck className="w-3.5 h-3.5 text-lia-text-tertiary dark:text-lia-text-tertiary" />
              <span className="text-xs font-semibold text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wider font-['Open_Sans',sans-serif]">Agendamento Automático</span>
            </div>
            <button
              onClick={() => setEditSchedulingEnabled(!editSchedulingEnabled)}
              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${editSchedulingEnabled ? 'bg-gray-900' : 'bg-gray-300'}`}
            >
              <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white dark:bg-lia-bg-primary transition-transform ${editSchedulingEnabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
            </button>
          </div>
          {editSchedulingEnabled && (
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Score Mínimo para Agendamento (WSI)</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { key: 'rigorous' as const, label: 'Rigoroso', score: '≥ 4.2/5.0', desc: 'Só aprovados automaticamente' },
                    { key: 'recommended' as const, label: 'Recomendado', score: '≥ 3.8/5.0', desc: 'Inclui revisão manual' },
                    { key: 'flexible' as const, label: 'Flexível', score: '≥ 3.0/5.0', desc: 'Todos acima do corte' },
                  ].map((preset) => {
                    const isSelected = editSchedulingMinScorePreset === preset.key
                    return (
                      <button key={preset.key} onClick={() => setEditSchedulingMinScorePreset(preset.key)} className={`p-2 rounded-md border text-left transition-colors ${isSelected ? 'border-gray-900 bg-gray-50 ring-1 ring-gray-900 dark:ring-gray-300' : 'border-lia-border-subtle bg-white hover:border-lia-border-default dark:border-lia-border-default dark:bg-lia-bg-secondary dark:hover:border-gray-500'}`}>
                        <div className="flex items-center justify-between mb-0.5">
                          <span className={`text-micro font-semibold ${isSelected ? 'text-lia-text-primary' : 'text-lia-text-secondary dark:text-lia-text-tertiary'}`} >{preset.label}</span>
                          {isSelected && <CheckCircle className="w-3 h-3 text-lia-text-primary dark:text-lia-text-secondary" />}
                        </div>
                        <span className="text-micro font-medium text-lia-text-primary dark:text-lia-text-primary block" >{preset.score}</span>
                        <span className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary block mt-0.5">{preset.desc}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Calendário</label>
                  <select value={editCalendarProvider} onChange={(e) => setEditCalendarProvider(e.target.value)} className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-secondary focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors">
                    <option value="Microsoft">Microsoft</option>
                    <option value="Google">Google</option>
                    <option value="Outlook">Outlook</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Horários</label>
                  <div className="flex items-center gap-2">
                    <input type="text" value={editAvailableHours} onChange={(e) => { setEditAvailableHours(e.target.value); setEditAvailableHoursInherited(false) }} className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-secondary focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors" />
                  </div>
                  {editAvailableHoursInherited && (
                    <span className="text-micro text-lia-text-disabled mt-0.5 block">Conforme config. da empresa</span>
                  )}
                </div>
                <div>
                  <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif] block mb-2">Duração</label>
                  <select value={editInterviewDuration} onChange={(e) => setEditInterviewDuration(Number(e.target.value))} className="w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-secondary focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors">
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
  </>
)}

{activeSection === 'descricao' && (
  <div>
    <div className="flex-1 min-w-0">
  <JDEvaluationPanel
    className="!mx-0 !mt-0"
    jobTitle={job.title}
    responsibilities={job.requirements || []}
    technicalSkills={(job.technicalRequirements || []).map((r: Record<string, unknown>) => r.technology || r.skill || r.name || (typeof r === 'string' ? r : '')).filter(Boolean)}
    behavioralCompetencies={(job.behavioralCompetencies || []).map((c: Record<string, unknown>) => c.competency || c.name || (typeof c === 'string' ? c : '')).filter(Boolean)}
    seniority={job.level || job.seniority}
    department={job.department}
    description={job.description}
    hasQuestions={(job.screeningQuestions?.length || 0) > 0}
    onGenerateQuestions={async () => {
      setActiveSection('perguntas')
      toast.success('Acesse "Perguntas de Triagem" para gerar as perguntas WSI e escolher o modo (Compacto ou Completo).')
    }}
    enrichedJd={job.enrichedJd}
    onSaveEnrichedJD={async (enrichedData) => {
      if (!job) return
      const jobId = job.backendId || job.jobId || String(job.id)
      try {
        await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enriched_jd: enrichedData })
        })
        onJobUpdate?.({ ...job, enrichedJd: enrichedData })
      } catch (error) {
        throw error
      }
    }}
    onUpdateOfficialJD={async (updates) => {
      if (!job) return
      const jobId = job.backendId || job.jobId || String(job.id)
      try {
        await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            description: updates.description,
            requirements: updates.requirements,
            technical_requirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })),
            behavioral_competencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })),
          })
        })
        onJobUpdate?.({
          ...job,
          description: updates.description || job.description,
          requirements: updates.requirements || job.requirements,
          technicalRequirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })) || job.technicalRequirements,
          behavioralCompetencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) || job.behavioralCompetencies,
        })
      } catch (error) {
        throw error
      }
    }}
    onSaveJDInline={async (updates) => {
      if (!job) return
      const jobId = job.backendId || job.jobId || String(job.id)
      try {
        await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            description: updates.description,
            requirements: updates.requirements,
            technical_requirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })),
            behavioral_competencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })),
          })
        })
        onJobUpdate?.({
          ...job,
          description: updates.description || job.description,
          requirements: updates.requirements || job.requirements,
          technicalRequirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })) || job.technicalRequirements,
          behavioralCompetencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) || job.behavioralCompetencies,
        })
      } catch (error) {
        throw error
      }
    }}
    isGenerating={isGeneratingWSI}
    companyId={(job as Record<string, unknown>).companyId as string || 'default'}
    companyName={(job as Record<string, unknown>).companyName as string || undefined}
    companyDescription={undefined}
    companyIndustry={(job as Record<string, unknown>).industry as string || undefined}
    benefits={job.benefits || []}
    interviewStages={((job as Record<string, unknown>).interviewStages as Array<Record<string, unknown>> || []).map((s: Record<string, unknown>) => typeof s === 'string' ? s : (s.stageName || s.name || '') as string)}
    onUpdateJobDescription={async (jdText) => {
      if (!job) return
      const jobId = job.backendId || job.jobId || String(job.id)
      try {
        await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ description: jdText })
        })
        onJobUpdate?.({ ...job, description: jdText })
      } catch (error) {
        throw error
      }
    }}
  />
    </div>
  </div>
)}

{activeSection === 'perguntas' && (
  <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
  {!isEditingScreening && (
    <CardContent className="p-4">
      <div className="space-y-4">
        <div>
          <h4 className="text-xs font-semibold text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wider font-['Open_Sans',sans-serif] mb-3">Blocos WSI</h4>
          <div className="flex items-center gap-3 text-micro text-lia-text-secondary dark:text-lia-text-tertiary flex-wrap mb-3">
            <span>Total: {job.screeningQuestions?.length || 0} perguntas WSI</span>
            <span>•</span>
            <span>{(job.screeningQuestions || []).filter((q: ScreeningQuestionItem) => q.type === 'eliminatory' || q.required).length} eliminatórias</span>
            <span>•</span>
            <span>{(job.screeningQuestions || []).filter((q: ScreeningQuestionItem) => q.type !== 'eliminatory' && !q.required).length} informativas</span>
          </div>
        </div>
        <div className="space-y-2">
          {WSI_BLOCKS.map((block) => {
            const blockQuestions = (job.screeningQuestions || []).filter((q: ScreeningQuestionItem) => q.block_id === block.id)
            const isAutomatic = !block.editable
            const block2Count = block.id === 2 ? (companyQuestions.length - disabledCompanyQIds.size) + selectedBankQuestions.length + customQuestions.length : 0
            const totalBlockCount = block.id === 2 ? block2Count + blockQuestions.length : blockQuestions.length
            return (
              <div key={block.id} className={`px-3 py-2 rounded-md ${isAutomatic ? 'bg-gray-50/50 border border-lia-border-subtle' : totalBlockCount > 0 ? 'bg-lia-bg-primary border border-lia-border-subtle' : 'bg-lia-bg-primary border border-lia-border-subtle border-dashed/50 dark:border-lia-border-default'}`}>
                <div className="flex items-center gap-2">
                  <span className={`text-micro font-semibold rounded-full w-5 h-5 flex items-center justify-center shrink-0 ${isAutomatic ? 'bg-gray-100' : 'text-lia-text-disabled dark:text-lia-text-tertiary dark:bg-lia-bg-elevated'}`}>{block.id}</span>
                  <span className={`text-xs font-medium ${isAutomatic ? 'text-lia-text-tertiary' : 'text-lia-text-primary dark:text-lia-text-primary'}`}>{block.name}</span>
                  {isAutomatic ? (
                    <span className="text-micro px-1.5 py-0.5 bg-gray-100 lia-text-secondary rounded-full font-medium uppercase tracking-wide dark:bg-lia-bg-elevated">Automático</span>
                  ) : totalBlockCount > 0 ? (
                    <span className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary">({totalBlockCount} {totalBlockCount === 1 ? 'pergunta' : 'perguntas'})</span>
                  ) : (
                    <span className="text-micro text-lia-text-disabled italic">Nenhuma pergunta</span>
                  )}
                </div>
                {block.id === 2 && (
                  <div className="mt-2 ml-7 space-y-3">
                    {companyQuestions.length > 0 && (
                      <CompanyDefaultQuestions
                        questions={companyQuestions}
                        disabledIds={disabledCompanyQIds}
                        isEditing={false}
                        onToggle={handleToggleCompanyDefault}
                      />
                    )}
                    {selectedBankQuestions.length > 0 && (
                      <>
                        <div className="border-t border-lia-border-subtle" />
                        <CompanyBankQuestions
                          isEditing={false}
                          selectedQuestions={selectedBankQuestions}
                          questionOverrides={bankQuestionOverrides}
                          onToggleQuestion={handleToggleBankQuestion}
                        />
                      </>
                    )}
                    {customQuestions.length > 0 && (
                      <>
                        <div className="border-t border-lia-border-subtle" />
                        <CustomQuestions
                          isEditing={false}
                          questions={customQuestions}
                          onAddQuestion={handleAddCustomQuestion}
                          onRemoveQuestion={handleRemoveCustomQuestion}
                          onUpdateQuestion={handleUpdateCustomQuestion}
                        />
                      </>
                    )}
                  </div>
                )}
                {!isAutomatic && block.id !== 2 && blockQuestions.length > 0 && (
                  <div className="space-y-1 ml-7 mt-1.5">
                    {blockQuestions.map((q: ScreeningQuestionItem, idx: number) => (
                      <p key={q.id || idx} className="text-xs text-lia-text-secondary dark:text-lia-text-secondary leading-relaxed truncate">
                        • {q.question || q.text}
                      </p>
                    ))}
                  </div>
                )}
                {isAutomatic && WSI_AUTOMATIC_MESSAGES[block.id] && (
                  <div className="ml-7 mt-1.5">
                    <p className="text-micro font-medium text-lia-text-tertiary dark:text-lia-text-tertiary mb-1">{WSI_AUTOMATIC_MESSAGES[block.id].title}</p>
                    <div className="bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-lg px-2.5 py-2">
                      <p className="text-micro text-lia-text-secondary dark:text-lia-text-secondary leading-relaxed whitespace-pre-line">{formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id].message)}</p>
                    </div>
                    <p className="text-micro text-lia-text-disabled mt-1 italic">{WSI_AUTOMATIC_MESSAGES[block.id].note}</p>
                  </div>
                )}
                {isAutomatic && !WSI_AUTOMATIC_MESSAGES[block.id] && (
                  <p className="text-micro text-lia-text-disabled ml-7 mt-0.5">{block.description}</p>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </CardContent>
  )}

  {/* Editing Mode */}
  {isEditingScreening && (
    <>
      <div className="px-5 py-3 border-t border-lia-border-subtle bg-gray-50/30">
        {(() => {
          const techSkillsCount = (job?.technicalRequirements || []).filter(Boolean).length
          const behavCompCount = (job?.behavioralCompetencies || []).filter(Boolean).length
          const showTechWarning = techSkillsCount < 9
          const showBehavWarning = behavCompCount < 5
          const showFullDisabled = techSkillsCount < 5
          if (showTechWarning || showBehavWarning) {
            return (
              <div className="mb-3 rounded-md border border-status-warning/30 bg-status-warning/10 dark:bg-status-warning/30 dark:border-status-warning/30 px-3 py-2.5">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-status-warning dark:text-status-warning mt-0.5 shrink-0" />
                  <div className="space-y-1">
                    {showTechWarning && (
                      <p className="text-xs text-status-warning dark:text-status-warning leading-relaxed">
                        {techSkillsCount === 0
                          ? 'Nenhuma competência técnica cadastrada — adicione competências na seção Job Description para gerar perguntas de triagem.'
                          : `Apenas ${techSkillsCount} competência${techSkillsCount === 1 ? '' : 's'} técnica${techSkillsCount === 1 ? '' : 's'} cadastrada${techSkillsCount === 1 ? '' : 's'}. Para triagem completa, recomendamos pelo menos 9.`
                        }
                      </p>
                    )}
                    {showBehavWarning && (
                      <p className="text-xs text-status-warning dark:text-status-warning leading-relaxed">
                        {behavCompCount === 0
                          ? 'Nenhuma competência comportamental cadastrada — a triagem usará avaliação padrão.'
                          : `${behavCompCount} competência${behavCompCount === 1 ? '' : 's'} comportamental${behavCompCount === 1 ? '' : 's'} (recomendado: 5 para cobertura completa).`
                        }
                      </p>
                    )}
                    {showFullDisabled && (
                      <p className="text-micro text-status-warning dark:text-status-warning italic">
                        Modo Completo requer pelo menos 5 competências técnicas.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )
          }
          return null
        })()}
        <div className="flex items-center gap-2">
          <button onClick={handleGenerateWSI('compact')} disabled={isGeneratingWSI} className={`flex-1 flex items-center justify-center gap-2 px-3 py-1.5 rounded-md border transition-colors disabled:opacity-50 ${wsiGenerationMode === 'compact' ? 'bg-gray-900 text-white border-gray-900 ring-2 ring-gray-900/20 ring-offset-1 dark:ring-gray-100/20' : 'bg-white lia-text-strong border-lia-border-default hover:bg-gray-50 hover:border-gray-400 dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:border-lia-border-default dark:hover:bg-gray-700'}`}>
            {isGeneratingWSI && wsiGenerationMode === 'compact' ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <>
                <span className="text-xs font-semibold">Gerar WSI Compacto</span>
                <span className={`text-micro ${wsiGenerationMode === 'compact' ? 'lia-text-secondary' : 'lia-text-secondary'}`}>~7 perguntas · 12 min</span>
              </>
            )}
          </button>
          <div className="relative flex-1 group/full">
            <button onClick={handleGenerateWSI('full')} disabled={isGeneratingWSI || (job?.technicalRequirements || []).filter(Boolean).length < 5} className={`w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-md border transition-colors disabled:opacity-50 ${wsiGenerationMode === 'full' ? 'bg-gray-900 text-white border-gray-900 ring-2 ring-gray-900/20 ring-offset-1 dark:ring-gray-100/20' : 'bg-white lia-text-strong border-lia-border-default hover:bg-gray-50 hover:border-gray-400 dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:border-lia-border-default dark:hover:bg-gray-700'}`}>
              {isGeneratingWSI && wsiGenerationMode === 'full' ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <>
                  <span className="text-xs font-semibold">Gerar WSI Completo</span>
                  <span className={`text-micro ${wsiGenerationMode === 'full' ? 'lia-text-secondary' : 'lia-text-secondary'}`}>~12 perguntas · 22 min</span>
                </>
              )}
            </button>
            {(job?.technicalRequirements || []).filter(Boolean).length < 5 && (
              <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-52 p-2 bg-gray-900 text-white text-micro rounded-md opacity-0 invisible group-hover/full:opacity-100 group-hover/full:visible transition-opacity z-50 text-center">
                <p className="leading-relaxed">Adicione pelo menos 5 competências técnicas na seção Job Description para habilitar o modo Completo.</p>
                <div className="absolute top-full left-1/2 -translate-x-1/2 -translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
              </div>
            )}
          </div>
          <div className="relative group">
            <Brain className="w-5 h-5 cursor-help text-wedo-cyan" />
            <div className="absolute right-full mr-2 top-1/2 -translate-y-1/2 w-64 p-3 bg-gray-900 text-white text-xs rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity z-50">
              <p className="leading-relaxed">A LIA gera perguntas seguindo a metodologia WeDoTalent Skill Index, calibrando complexidade conforme senioridade e skills da vaga.</p>
              <div className="absolute top-1/2 right-0 translate-x-1/2 -translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
            </div>
          </div>
        </div>

        {/* WSI Generation Progress */}
        {(isGeneratingWSI || wsiGenerationCompleted) && wsiGenerationStep > 0 && (
          <div className="mt-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-secondary overflow-hidden">
            <div className="flex items-center gap-3 px-5 py-3 cursor-pointer" onClick={() => setWsiProgressCollapsed(!wsiProgressCollapsed)}>
              <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0">
                {wsiGenerationStep < 4 ? (
                  <Loader2 className="w-5 h-5 text-lia-text-primary dark:text-lia-text-primary animate-spin" />
                ) : (
                  <Brain className="w-5 h-5 text-wedo-cyan" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-base-ui font-semibold lia-text-strong">
                  {wsiGenerationStep < 4 ? 'Gerando Roteiro e Perguntas de Triagem...' : 'Roteiro e Perguntas de Triagem'}
                </p>
                <p className="text-xs lia-text-base mt-0.5">
                  {wsiGenerationStep < 4
                    ? `Analisando ${wsiGenerationMode === 'compact' ? 'modo compacto' : 'modo completo'}`
                    : `Status: ${wsiGeneratedCount} perguntas geradas · Metodologia WeDoTalent Skill Index (WSI) Completa`
                  }
                </p>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                {wsiGenerationStep >= 4 && (
                  <button onClick={(e) => { e.stopPropagation(); setWsiGenerationCompleted(false); setWsiGenerationStep(0); setWsiDynamicMessage(''); setWsiGenerationContext(null) }} className="p-1 hover:bg-gray-100 rounded-md transition-colors">
                    <X className="w-3.5 h-3.5 lia-text-secondary" />
                  </button>
                )}
                {wsiProgressCollapsed ? <ChevronDown className="w-4 h-4 lia-text-secondary" /> : <ChevronUp className="w-4 h-4 lia-text-secondary" />}
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
                    <div className="flex flex-col items-center" style={{minWidth: '56px'}}>
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center transition-[width,height] duration-500 ${
 (wsiGenerationStep > step.num || (wsiGenerationStep === step.num && wsiGenerationCompleted))
                          ? 'text-white'
                          : wsiGenerationStep === step.num
                            ? 'border-2 bg-lia-bg-primary'
                            : 'border border-lia-border-default bg-lia-bg-primary'
                      } ${(wsiGenerationStep > step.num || (wsiGenerationStep === step.num && wsiGenerationCompleted)) ? 'bg-wedo-cyan' : wsiGenerationStep === step.num ? 'border-wedo-cyan' : ''}`}>
                        {(wsiGenerationStep > step.num || (wsiGenerationStep === step.num && wsiGenerationCompleted)) ? (
                          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                        ) : wsiGenerationStep === step.num ? (
                          <Loader2 className="w-3 h-3 animate-spin text-wedo-cyan" />
                        ) : (
                          <span className="text-micro font-semibold lia-text-secondary">{step.num}</span>
                        )}
                      </div>
                      <span className={`text-micro mt-1.5 font-medium whitespace-nowrap transition-colors duration-300 ${wsiGenerationStep >= step.num ? 'text-wedo-cyan-dark' : 'lia-text-secondary'}`}>
                        {step.label}
                      </span>
                    </div>
                    {idx < arr.length - 1 && (
                      <div className="flex-1 flex items-center" style={{marginTop: '11px'}}>
                        <div className={`w-full h-0.5 rounded-full transition-[width,height] duration-700 ${wsiGenerationStep > step.num ? 'bg-wedo-cyan' : 'bg-gray-200'}`} />
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>

            {wsiGenerationStep < 4 && wsiTypedMessage && (
              <div className="px-5 pb-3 flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-gray-900 animate-pulse" />
                <p className="text-base-ui lia-text-strong">
                  {wsiTypedMessage}
                  {wsiTypedMessage.length < wsiDynamicMessage.length && (
                    <span className="inline-block w-[2px] h-[14px] bg-gray-900 ml-0.5 align-middle animate-pulse" />
                  )}
                </p>
              </div>
            )}

            {!wsiProgressCollapsed && (
              <div className="px-5 pb-4 pt-1 space-y-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                {wsiGenerationStep >= 1 && wsiGenerationContext && (
                  <div className="pt-2">
                    <p className="text-micro font-semibold lia-text-secondary uppercase tracking-wider mb-0.5">Cargo analisado</p>
                    <p className="text-xs lia-text-strong">
                      {wsiGenerationContext.title}{wsiGenerationContext.seniority ? <span className="text-lia-text-secondary dark:text-lia-text-tertiary"> · {wsiGenerationContext.seniority}</span> : ''}
                    </p>
                  </div>
                )}

                {wsiGenerationStep >= 2 && wsiGenerationContext && (
                  <div className="space-y-2">
                    {wsiGenerationContext.responsibilities.length > 0 && (
                      <div>
                        <p className="text-micro font-semibold lia-text-secondary uppercase tracking-wider mb-1">Responsabilidades Chave</p>
                        <div className="flex flex-wrap gap-1">
                          {wsiGenerationContext.responsibilities.map((resp: string, i: number) => (
                            <span key={`resp-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-gray-50 text-lia-text-secondary dark:bg-lia-bg-secondary dark:text-lia-text-secondary border border-lia-border-subtle dark:border-lia-border-default rounded-full">
                              {resp.length > 35 ? resp.slice(0, 35) + '...' : resp}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {wsiGenerationContext.technicalSkills.length > 0 && (
                      <div>
                        <p className="text-micro font-semibold lia-text-secondary uppercase tracking-wider mb-1">Competências Técnicas</p>
                        <div className="flex flex-wrap gap-1">
                          {wsiGenerationContext.technicalSkills.map((skill: string, i: number) => (
                            <span key={`tech-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-gray-50 text-lia-text-secondary dark:bg-lia-bg-secondary dark:text-lia-text-secondary border border-lia-border-subtle dark:border-lia-border-default rounded-full">{skill}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {wsiGenerationContext.behavioralCompetencies.length > 0 && (
                      <div>
                        <p className="text-micro font-semibold text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wider mb-1">Competências Comportamentais</p>
                        <div className="flex flex-wrap gap-1">
                          {wsiGenerationContext.behavioralCompetencies.map((comp: string, i: number) => (
                            <span key={`behav-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-gray-50 text-lia-text-secondary dark:bg-lia-bg-secondary dark:text-lia-text-secondary border border-lia-border-subtle dark:border-lia-border-default rounded-full">{comp}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {wsiGenerationStep >= 3 && (
                  <div>
                    <p className="text-micro font-semibold lia-text-secondary uppercase tracking-wider mb-1">Metodologias Utilizadas para Gerar Perguntas</p>
                    {wsiGenerationStep >= 4 && wsiGenerationContext?.methodologyBreakdown && Object.keys(wsiGenerationContext.methodologyBreakdown).length > 0 ? (
                      <p className="text-xs lia-text-base">
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
                          <span key={m} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-gray-50 text-lia-text-secondary dark:bg-lia-bg-secondary dark:text-lia-text-tertiary border border-lia-border-subtle dark:border-lia-border-default rounded-full">{m}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {wsiGenerationStep >= 4 && wsiGenerationContext && (
                  <div className="space-y-4 pt-1">
                    <div>
                      <p className="text-base-ui lia-text-strong">
                        {wsiSummaryTypedText}
                        {!wsiSummaryTypingDone && (
                          <span className="inline-block w-[2px] h-[14px] bg-gray-900 ml-0.5 align-middle animate-pulse" />
                        )}
                      </p>
                    </div>

                    {wsiSummaryTypingDone && (<>
                      <div className="space-y-1.5 pl-1">
                        {(wsiGenerationContext.blockBreakdown?.[2] || 0) > 0 && (
                          <div className="flex items-start gap-2">
                            <span className="text-lia-text-disabled mt-0.5">•</span>
                            <p className="text-base-ui lia-text-strong">
                              <span className="font-semibold">{wsiGenerationContext.blockBreakdown[2]} perguntas de elegibilidade</span>, para validar aderência mínima ao cargo
                            </p>
                          </div>
                        )}
                        {(wsiGenerationContext.blockBreakdown?.[3] || 0) > 0 && (
                          <div className="flex items-start gap-2">
                            <span className="text-lia-text-disabled mt-0.5">•</span>
                            <p className="text-base-ui lia-text-strong">
                              <span className="font-semibold">{wsiGenerationContext.blockBreakdown[3]} perguntas técnicas</span>, para investigar o nível de conhecimento e experiência prática
                            </p>
                          </div>
                        )}
                        {(wsiGenerationContext.blockBreakdown?.[4] || 0) > 0 && (
                          <div className="flex items-start gap-2">
                            <span className="text-lia-text-disabled mt-0.5">•</span>
                            <p className="text-base-ui lia-text-strong">
                              <span className="font-semibold">{wsiGenerationContext.blockBreakdown[4]} perguntas comportamentais</span>, para explorar as competências exigidas para a vaga
                            </p>
                          </div>
                        )}
                      </div>

                      <div className="space-y-1">
                        <p className="text-base-ui lia-text-strong">
                          Ao todo, a triagem será composta por <span className="font-semibold">{wsiGeneratedCount} perguntas</span>.
                        </p>
                        <p className="text-base-ui lia-text-strong">
                          O tempo médio estimado de triagem é de <span className="font-semibold">15 a 20 minutos</span>, considerando o tempo de leitura e resposta do candidato.
                        </p>
                      </div>

                      {!wsiSummaryExpanded ? (
                        <button onClick={() => setWsiSummaryExpanded(true)} className="flex items-center gap-1.5 text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary dark:text-lia-text-secondary dark:hover:text-lia-text-inverse transition-colors">
                          <ChevronDown className="w-3.5 h-3.5" />
                          Ver detalhes completos
                        </button>
                      ) : (
                        <>
                          <div>
                            <p className="text-base-ui font-semibold lia-text-strong mb-1">Próximo passo</p>
                            <p className="text-base-ui lia-text-strong">Selecione as perguntas em cada um dos blocos abaixo.</p>
                          </div>
                          <div className="space-y-1.5">
                            <p className="text-base-ui lia-text-strong">
                              As perguntas foram geradas com base na metodologia <span className="font-semibold text-lia-text-primary">WeDoTalent Skill Index</span>, considerando:
                            </p>
                            <div className="space-y-0.5 pl-1">
                              <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">•</span><p className="text-base-ui lia-text-base">Senioridade do cargo</p></div>
                              <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">•</span><p className="text-base-ui lia-text-base">Responsabilidades e competências mapeadas</p></div>
                              <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">•</span><p className="text-base-ui lia-text-base">Metodologias de avaliação (CBI, Bloom, Big Five e Dreyfus)</p></div>
                            </div>
                          </div>
                          <p className="text-base-ui lia-text-base">
                            As perguntas estão organizadas em ordem de prioridade, mas você pode escolher aquelas que julgar mais adequadas ao contexto da vaga.
                          </p>
                          <p className="text-base-ui lia-text-strong font-semibold">
                            Caso deseje perguntas adicionais, utilize a opção de adicionar perguntas personalizadas manualmente em cada bloco.
                          </p>
                          <div className="border-t border-lia-border-subtle pt-3">
                            <p className="text-base-ui font-semibold lia-text-strong mb-1.5">Finalização</p>
                            <p className="text-base-ui lia-text-strong mb-1">Após concluir a seleção das perguntas:</p>
                            <div className="space-y-0.5 pl-1">
                              <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">1.</span><p className="text-base-ui lia-text-base">Salve as alterações</p></div>
                              <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">2.</span><p className="text-base-ui lia-text-base">Inicie o disparo da triagem</p></div>
                              <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">3.</span><p className="text-base-ui lia-text-base">A LIA realizará a avaliação inicial e sinalizará os candidatos aprovados para a próxima etapa</p></div>
                            </div>
                          </div>
                          {wsiGenerationContext.companyStandardFound && (
                            <div className="flex items-center gap-1.5 pt-1">
                              <CheckCircle2 className="w-3.5 h-3.5 text-status-success dark:text-status-success" />
                              <span className="text-xs lia-text-base">Perguntas padrão da empresa incluídas</span>
                            </div>
                          )}
                          <button onClick={() => setWsiSummaryExpanded(false)} className="flex items-center gap-1.5 text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary dark:text-lia-text-secondary dark:hover:text-lia-text-inverse transition-colors pt-1">
                            <ChevronUp className="w-3.5 h-3.5" />
                            Recolher detalhes
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
            const isExpanded = expandedBlocks.includes(block.id)
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
            const isBlock4 = (q: ScreeningQuestionItem) => {
              if (isBlock2(q) || isBlock3(q)) return false
              return true
            }

            const blockQuestions = allQuestions.filter((q: ScreeningQuestionItem) => {
              if (q.block_id !== undefined && q.block_id !== null) return q.block_id === block.id
              if (block.id === 2) return isBlock2(q)
              if (block.id === 3) return isBlock3(q)
              if (block.id === 4) return isBlock4(q)
              return false
            })

            const blockGenerated = generatedQuestions[block.id] || []
            const acceptedCountForBlock = blockGenerated.filter((q: ScreeningQuestionItem) => acceptedQuestions.has(q.id)).length
            const eliminatoryCount = blockQuestions.filter((q: ScreeningQuestionItem) => q.type === 'eliminatory' || q.required).length
            const informativeCount = blockQuestions.length - eliminatoryCount

            return (
              <div key={block.id} className={`border rounded-md overflow-hidden ${block.editable ? 'border-lia-border-subtle' : 'border-lia-border-subtle bg-gray-50/50 dark:bg-lia-bg-secondary/30'}`}>
                <div className={`flex items-center justify-between p-3 cursor-pointer transition-colors ${block.editable ? 'bg-gray-50 hover:bg-gray-100 dark:bg-lia-bg-secondary dark:hover:bg-gray-700' : 'bg-gray-100/80 dark:bg-lia-bg-secondary/50'}`} onClick={() => {
                  if (isExpanded) {
                    setExpandedBlocks(prev => prev.filter(id => id !== block.id))
                  } else {
                    setExpandedBlocks(prev => [...prev, block.id])
                  }
                }}>
                  <div className="flex items-center gap-2">
                    <span className={`w-6 h-6 rounded-full text-white text-xs font-bold flex items-center justify-center ${block.editable ? 'bg-gray-700' : 'bg-gray-400'}`}>{block.id}</span>
                    <div>
                      <span className={`text-xs font-semibold ${block.editable ? 'text-lia-text-primary' : 'text-lia-text-primary dark:text-lia-text-primary'}`}>{block.name}</span>
                      <span className="text-micro lia-text-base ml-2">({block.duration})</span>
                    </div>
                    {!block.editable && <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-200 lia-text-base ml-1">Automático</Badge>}
                  </div>
                  <div className="flex items-center gap-2">
                    {block.editable && blockQuestions.length > 0 && (
                      <>
                        {eliminatoryCount > 0 && <Badge className="text-micro px-2 py-0.5 bg-status-error/10 text-status-error border border-status-error/30">{eliminatoryCount} Eliminatória{eliminatoryCount > 1 ? 's' : ''}</Badge>}
                        {informativeCount > 0 && <Badge className="text-micro px-2 py-0.5 bg-gray-100 lia-text-strong">{informativeCount} Informativa{informativeCount > 1 ? 's' : ''}</Badge>}
                      </>
                    )}
                    {blockGenerated.length > 0 && (
                      <>
                        <Badge className="text-micro px-2 py-0.5 bg-gray-100 lia-text-base border border-lia-border-subtle">{acceptedCountForBlock}/{blockGenerated.length} aceitas</Badge>
                        {acceptedCountForBlock < blockGenerated.length && <span className="w-2 h-2 rounded-full bg-status-warning animate-pulse"></span>}
                      </>
                    )}
                    {isExpanded ? <ChevronUp className="w-4 h-4 lia-text-base" /> : <ChevronDown className="w-4 h-4 lia-text-base" />}
                  </div>
                </div>

                {isExpanded && (
                  <div className={`p-3 space-y-2 ${!block.editable ? 'bg-gray-50/30' : ''}`}>
                    {!block.editable ? (
                      WSI_AUTOMATIC_MESSAGES[block.id] ? (
                        <div className="rounded-md border border-lia-border-default bg-gray-50 dark:bg-lia-bg-secondary/50 overflow-hidden">
                          <div className="px-3 py-2 border-b border-lia-border-subtle dark:border-lia-border-default bg-gray-100 dark:bg-lia-bg-secondary">
                            <p className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">{WSI_AUTOMATIC_MESSAGES[block.id].title}</p>
                          </div>
                          <div className="p-3">
                            <div className="text-xs text-lia-text-primary dark:text-lia-text-primary leading-relaxed whitespace-pre-line">{formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id].message)}</div>
                          </div>
                          <div className="px-3 py-2 border-t border-lia-border-subtle dark:border-lia-border-default bg-gray-50 dark:bg-lia-bg-secondary/50">
                            <p className="text-micro text-lia-text-secondary dark:text-lia-text-tertiary italic">{WSI_AUTOMATIC_MESSAGES[block.id].note}</p>
                          </div>
                        </div>
                      ) : (
                        <div className="p-3 bg-lia-bg-primary/60 border border-lia-border-subtle rounded-md">
                          <p className="text-xs lia-text-strong italic">{block.description}</p>
                          <p className="text-micro lia-text-base mt-1">Este bloco é gerenciado automaticamente pela LIA</p>
                        </div>
                      )
                    ) : (
                      <>
                        {block.id === 2 && (
                          <div className="space-y-4 mb-3">
                            <CompanyDefaultQuestions
                              questions={companyQuestions}
                              disabledIds={disabledCompanyQIds}
                              isEditing={true}
                              onToggle={handleToggleCompanyDefault}
                            />
                            <div className="border-t border-lia-border-subtle" />
                            <CompanyBankQuestions
                              isEditing={true}
                              selectedQuestions={selectedBankQuestions}
                              questionOverrides={bankQuestionOverrides}
                              onToggleQuestion={handleToggleBankQuestion}
                              onUpdateSelectedQuestion={handleUpdateBankQuestion}
                              excludeIds={companyQuestions.map(q => q.id)}
                            />
                            <div className="border-t border-lia-border-subtle" />
                            <CustomQuestions
                              isEditing={true}
                              questions={customQuestions}
                              onAddQuestion={handleAddCustomQuestion}
                              onRemoveQuestion={handleRemoveCustomQuestion}
                              onUpdateQuestion={handleUpdateCustomQuestion}
                            />
                          </div>
                        )}
                        {blockQuestions.length === 0 && blockGenerated.length === 0 && block.id !== 2 ? (
                          <div className="p-4 bg-gray-50 dark:bg-lia-bg-secondary/50 border border-lia-border-subtle dark:border-lia-border-default border-dashed rounded-md text-center">
                            <p className="text-xs lia-text-secondary">Nenhuma pergunta neste bloco</p>
                          </div>
                        ) : block.id !== 2 || blockQuestions.length > 0 || blockGenerated.length > 0 ? (
                          <>
                            {blockQuestions.map((item: ScreeningQuestionItem, idx: number) => {
                              const isDeactivated = deactivatedQuestions.has(item.id)
                              const isDetailsExpanded = expandedQuestionDetails.has(item.id)
                              const complexity = getBloomComplexity(item.bloom_level || 3)
                              const estTime = getEstimatedTime(item.question_type || 'open')
                              return (
                                <div key={item.id || idx} className={`p-3 bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md group hover:border-lia-border-default dark:hover:border-gray-600 transition-colors ${isDeactivated ? 'opacity-50' : ''}`}>
                                  <div className="flex items-start gap-3">
                                    <SCMQuestionDetailView
                                      item={item}
                                      isDetailsExpanded={isDetailsExpanded}
                                      onToggleDetails={(id) => setExpandedQuestionDetails(prev => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next })}
                                      helpers={{ getBloomComplexity, getBloomLabelPTBR, getDreyfusLabelPTBR, getBigFiveLabelPTBR, getEstimatedTime }}
                                    />
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                                      {isDeactivated ? (
                                        <Badge className="text-micro px-2 py-0.5 h-5 rounded-full bg-gray-100 text-lia-text-tertiary border border-lia-border-subtle dark:bg-lia-bg-elevated dark:text-lia-text-tertiary dark:border-lia-border-default">Inativa</Badge>
                                      ) : (
                                        <Badge className="text-micro px-2 py-0.5 h-5 rounded-full bg-status-success/10 text-status-success border border-status-success/30 dark:bg-status-success/20 dark:text-status-success dark:border-status-success/30">
                                          <CheckCircle className="w-3 h-3 mr-1" />Aceita
                                        </Badge>
                                      )}
                                    </div>
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                      <button className={`p-1.5 rounded-md transition-colors ${isDeactivated ? 'hover:bg-status-success/10' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`} onClick={() => {
                                        setDeactivatedQuestions(prev => {
                                          const next = new Set(prev)
                                          if (next.has(item.id)) { next.delete(item.id); toast.success('Pergunta reativada') } else { next.add(item.id); toast.success('Pergunta arquivada') }
                                          return next
                                        })
                                      }} title={isDeactivated ? 'Reativar pergunta' : 'Arquivar pergunta'}>
                                        <Archive className={`w-3.5 h-3.5 ${isDeactivated ? 'text-status-success' : 'lia-text-secondary'}`} />
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              )
                            })}

                            {blockGenerated.map((item: ScreeningQuestionItem, idx: number) => {
                              const isAccepted = acceptedQuestions.has(item.id)
                              const genComplexity = getBloomComplexity(item.bloom_level || 3)
                              const genEstTime = getEstimatedTime(item.question_type || 'open')
                              const genDetailsExpanded = expandedQuestionDetails.has(item.id)
                              return (
                                <div key={item.id || `gen-${idx}`} className={`p-3 rounded-md transition-colors ${isAccepted ? 'bg-gray-50 dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default' : 'bg-white dark:bg-lia-bg-secondary border border-dashed border-lia-border-default dark:border-lia-border-default'}`}>
                                  <div className="flex items-start gap-3">
                                    <SCMQuestionDetailView
                                      item={item}
                                      isDetailsExpanded={genDetailsExpanded}
                                      onToggleDetails={(id) => setExpandedQuestionDetails(prev => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next })}
                                      helpers={{ getBloomComplexity, getBloomLabelPTBR, getDreyfusLabelPTBR, getBigFiveLabelPTBR, getEstimatedTime }}
                                    />
                                    <div className="flex items-center gap-1.5 shrink-0">
                                      {isAccepted ? (
                                        <button className="border border-lia-border-subtle lia-text-secondary text-micro px-2 py-1 rounded-full hover:bg-status-error/10 transition-colors" onClick={() => {
                                          if (confirm('Remover pergunta aceita?')) {
                                            setAcceptedQuestions(prev => { const next = new Set(prev); next.delete(item.id); return next })
                                            setGeneratedQuestions(prev => ({ ...prev, [block.id]: (prev[block.id] || []).filter((q: ScreeningQuestionItem) => q.id !== item.id) }))
                                          }
                                        }}>Remover</button>
                                      ) : (
                                        <>
                                          <button className="bg-gray-900 text-white text-micro px-2 py-1 rounded-full hover:bg-gray-800 transition-colors" onClick={() => setAcceptedQuestions(prev => new Set(prev).add(item.id))}>Aceitar</button>
                                          <button className="border border-lia-border-subtle lia-text-secondary text-micro px-2 py-1 rounded-full hover:bg-status-error/10 transition-colors" onClick={() => setGeneratedQuestions(prev => ({ ...prev, [block.id]: (prev[block.id] || []).filter((q: ScreeningQuestionItem) => q.id !== item.id) }))}>Descartar</button>
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
      <div className="flex items-center justify-between px-5 py-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
        <Button variant="outline" size="sm" className="h-7 text-micro px-3 border-lia-border-subtle text-lia-text-secondary dark:border-lia-border-default dark:text-lia-text-secondary" onClick={resetScreeningEditing}>
          Cancelar
        </Button>
        <div className="flex items-center gap-2">
          <Button size="sm" className="h-7 text-micro px-4 bg-gray-900 hover:bg-gray-800 text-white" onClick={async () => {
            const existingCount = (job.screeningQuestions || []).length
            const acceptedCount = Object.values(generatedQuestions).flat().filter((q: ScreeningQuestionItem) => acceptedQuestions.has(q.id)).length
            const totalQuestions = existingCount + acceptedCount

            if (totalQuestions === 0) {
              toast.error('Selecione pelo menos uma pergunta antes de salvar o roteiro.')
              return
            }
            if (totalQuestions < 3) {
              toast.error('O roteiro precisa ter no mínimo 3 perguntas. Atualmente: ' + totalQuestions)
              return
            }

            try {
              const jobId = job.backendId || job.jobId || String(job.id)
              const existingQuestions = (job.screeningQuestions || []).map((q: ScreeningQuestionItem) => ({
                id: q.id, text: q.question || q.text, category: q.category, type: q.type, weight: q.weight, skill_targeted: q.skill_targeted, block_id: q.block_id
              }))
              const acceptedGenerated: ScreeningQuestionItem[] = []
              Object.values(generatedQuestions).forEach((blockQs: ScreeningQuestionItem[]) => {
                blockQs.forEach((q: ScreeningQuestionItem) => {
                  if (acceptedQuestions.has(q.id)) {
                    acceptedGenerated.push({ id: q.id, text: q.question || q.text, category: q.category, type: q.type, weight: q.weight || 0.75, skill_targeted: q.skill_targeted, block_id: q.block_id })
                  }
                })
              })
              const allQuestions = [...existingQuestions, ...acceptedGenerated]
              const response = await fetch('/api/backend-proxy/wsi/questions/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_id: jobId, questions: allQuestions, source: 'manual_save' })
              })
              if (response.ok) {
                const newScreeningQuestions = [
                  ...(job.screeningQuestions || []),
                  ...Object.values(generatedQuestions).flat().filter((q: ScreeningQuestionItem) => acceptedQuestions.has(q.id)).map((q: ScreeningQuestionItem) => ({
                    ...q, question: q.question || q.text, generated: undefined
                  }))
                ]
                onJobUpdate?.({ ...job, screeningQuestions: newScreeningQuestions })
                toast.success(`Roteiro salvo com sucesso! ${allQuestions.length} perguntas salvas.`)
                resetScreeningEditing()
              } else {
                toast.error('Erro ao salvar roteiro. Tente novamente.')
              }
            } catch (error) {
              toast.error('Erro ao salvar roteiro. Tente novamente.')
            }
          }}>
            <CheckCircle className="w-3 h-3 mr-1" />
            Salvar Alterações
          </Button>
          {(job.screeningStatus !== 'active') && (
            <Button size="sm" className="h-7 text-micro px-4 bg-status-success hover:bg-status-success text-white" onClick={async () => {
              const existingCount = (job.screeningQuestions || []).length
              const acceptedCount = Object.values(generatedQuestions).flat().filter((q: ScreeningQuestionItem) => acceptedQuestions.has(q.id)).length
              const totalQuestions = existingCount + acceptedCount

              if (totalQuestions === 0) {
                toast.error('Selecione pelo menos uma pergunta antes de ativar a triagem.')
                return
              }
              if (totalQuestions < 3) {
                toast.error('O roteiro precisa ter no mínimo 3 perguntas para ativar. Atualmente: ' + totalQuestions)
                return
              }

              try {
                const jobId = job.backendId || job.jobId || String(job.id)
                const existingQuestions = (job.screeningQuestions || []).map((q: ScreeningQuestionItem) => ({
                  id: q.id, text: q.question || q.text, category: q.category, type: q.type, weight: q.weight, skill_targeted: q.skill_targeted, block_id: q.block_id
                }))
                const acceptedGenerated: ScreeningQuestionItem[] = []
                Object.values(generatedQuestions).forEach((blockQs: ScreeningQuestionItem[]) => {
                  blockQs.forEach((q: ScreeningQuestionItem) => {
                    if (acceptedQuestions.has(q.id)) {
                      acceptedGenerated.push({ id: q.id, text: q.question || q.text, category: q.category, type: q.type, weight: q.weight || 0.75, skill_targeted: q.skill_targeted, block_id: q.block_id })
                    }
                  })
                })
                const allQuestions = [...existingQuestions, ...acceptedGenerated]
                const response = await fetch('/api/backend-proxy/wsi/questions/save', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ job_id: jobId, questions: allQuestions, source: 'manual_save' })
                })
                if (response.ok) {
                  const newScreeningQuestions = [
                    ...(job.screeningQuestions || []),
                    ...Object.values(generatedQuestions).flat().filter((q: ScreeningQuestionItem) => acceptedQuestions.has(q.id)).map((q: ScreeningQuestionItem) => ({
                      ...q, question: q.question || q.text, generated: undefined
                    }))
                  ]
                  onJobUpdate?.({ ...job, screeningQuestions: newScreeningQuestions, screeningStatus: 'active' })
                  toast.success(`Roteiro salvo e triagem ativada! ${allQuestions.length} perguntas configuradas.`)
                  resetScreeningEditing()
                } else {
                  toast.error('Erro ao salvar roteiro. Tente novamente.')
                }
              } catch (error) {
                toast.error('Erro ao salvar roteiro. Tente novamente.')
              }
            }}>
              <Play className="w-3 h-3 mr-1" />
              Salvar e Ativar
            </Button>
          )}
        </div>
      </div>
    </>
  )}
  </Card>
)}

{(job.liaMetrics?.triagens_realizadas ?? 0) > 0 && (
  <div className="flex items-center gap-2 px-3 py-1.5 bg-status-warning/10 border border-status-warning/30 rounded-md dark:bg-status-warning/10 dark:border-status-warning/30">
    <AlertTriangle className="w-3.5 h-3.5 text-status-warning dark:text-status-warning shrink-0" />
    <p className="text-xs text-status-warning dark:text-status-warning">
      <span className="font-bold">Triagem em andamento</span> — <span className="font-semibold">{job.liaMetrics?.triagens_realizadas} candidatos</span> já triados. Alterar perguntas pode afetar a comparabilidade entre candidatos.
    </p>
  </div>
)}
    </>
  )
}
