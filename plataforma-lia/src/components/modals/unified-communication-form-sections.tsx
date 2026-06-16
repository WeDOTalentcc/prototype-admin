"use client"

import React from "react"
import {
  Mail, MessageSquare, Calendar, Briefcase, Clock, CheckCircle
} from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { textStyles, cardStyles } from '@/lib/design-tokens'
import type {
  CommunicationChannel,
  CommunicationType,
  Candidate,
  InterviewSettings,
  JobVacancy
} from "./unified-communication-types"
import {
  PIPELINE_STAGES,
  interviewTypes,
  platforms,
  interviewers
} from "./unified-communication-types"

interface ChannelSelectorProps {
  channel: CommunicationChannel
  setChannel: (channel: CommunicationChannel) => void
  candidate: Candidate
}

export function ChannelSelector({ channel, setChannel, candidate }: ChannelSelectorProps) {
  return (
    <div>
      <h4 className={`${textStyles.label} mb-2`}>
        Canal de Envio
      </h4>
      <div className="grid grid-cols-3 gap-2">
        <button
          onClick={() => setChannel('email')}
          className={`flex items-center gap-2 p-3 rounded-md border transition-colors motion-reduce:transition-none ${
            channel === 'email'
              ? 'border-lia-btn-primary-bg bg-lia-bg-secondary text-lia-text-primary'
              : 'border-lia-border-subtle hover:border-lia-border-default text-lia-text-primary'
          }`}
          aria-label="Enviar por Email"
        >
          <Mail className="w-4 h-4" />
          <div className="text-left">
            <div className="text-xs font-medium">Email</div>
            <div className="text-micro opacity-70 truncate max-w-[120px]">{candidate.email}</div>
          </div>
        </button>
        <button
          onClick={() => setChannel('whatsapp')}
          className={`flex items-center gap-2 p-3 rounded-md border transition-colors motion-reduce:transition-none ${
            channel === 'whatsapp'
              ? 'border-status-success/30 bg-status-success/10 text-status-success'
              : 'border-lia-border-subtle hover:border-lia-border-default text-lia-text-primary'
          }`}
          aria-label="Enviar por WhatsApp"
        >
          <MessageSquare className="w-4 h-4" />
          <div className="text-left">
            <div className="text-xs font-medium">WhatsApp</div>
            <div className="text-micro opacity-70">{candidate.phone}</div>
          </div>
        </button>
        <button
          onClick={() => setChannel('both')}
          className={`flex items-center gap-2 p-3 rounded-md border transition-colors motion-reduce:transition-none ${
            channel === 'both'
              ? 'border-lia-btn-primary-bg bg-lia-bg-secondary text-lia-text-primary'
              : 'border-lia-border-subtle hover:border-lia-border-default text-lia-text-primary'
          }`}
          aria-label="Enviar por Email e WhatsApp"
        >
          <div className="flex items-center -space-x-1">
            <Mail className="w-3.5 h-3.5" />
            <MessageSquare className="w-3.5 h-3.5" />
          </div>
          <div className="text-left">
            <div className="text-xs font-medium">Ambos</div>
            <div className="text-micro opacity-70">Email + WA</div>
          </div>
        </button>
      </div>
    </div>
  )
}

interface InterviewSettingsSectionProps {
  interviewSettings: InterviewSettings
  setInterviewSettings: React.Dispatch<React.SetStateAction<InterviewSettings>>
}

export function InterviewSettingsSection({ interviewSettings, setInterviewSettings }: InterviewSettingsSectionProps) {
  return (
    <div className={`space-y-4 p-4 ${cardStyles.flat}`}>
      <h4 className={`${textStyles.label} flex items-center gap-2`}>
        <Calendar className="w-3.5 h-3.5 text-lia-text-secondary" />
        Configurações da Entrevista
      </h4>

      <div>
        <label className={`${textStyles.caption} font-medium mb-1.5 block`}>Tipo de Entrevista</label>
        <div className="grid grid-cols-2 gap-2">
          {interviewTypes.map((iType) => (
            <button
              key={iType.id}
              onClick={() => setInterviewSettings(prev => ({ ...prev, interviewType: iType.id as typeof prev.interviewType }))}
              className={`p-2 rounded-md border text-left transition-colors motion-reduce:transition-none ${
                interviewSettings.interviewType === iType.id
                  ? 'border-lia-btn-primary-bg bg-lia-bg-secondary'
                  : 'border-lia-border-subtle hover:border-lia-border-default'
              }`}
            >
              <iType.icon className={`w-3.5 h-3.5 mb-1 ${
                interviewSettings.interviewType === iType.id ? 'text-lia-text-primary' : 'text-lia-text-secondary'
              }`} />
              <div className="text-micro font-medium text-lia-text-primary">{iType.name}</div>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className={`${textStyles.caption} font-medium mb-1.5 block`}>Plataforma</label>
        <div className="grid grid-cols-4 gap-2">
          {platforms.map((plat) => (
            <button
              key={plat.id}
              onClick={() => setInterviewSettings(prev => ({ ...prev, platform: plat.id as typeof prev.platform }))}
              className={`p-2 rounded-md border text-center transition-colors motion-reduce:transition-none ${
                interviewSettings.platform === plat.id
                  ? 'border-lia-btn-primary-bg bg-lia-bg-secondary'
                  : 'border-lia-border-subtle hover:border-lia-border-default'
              }`}
            >
              <plat.icon className={`w-3.5 h-3.5 mx-auto mb-1 ${
                interviewSettings.platform === plat.id ? 'text-lia-text-primary' : 'text-lia-text-secondary'
              }`} />
              <div className="text-micro text-lia-text-primary">{plat.name}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div>
          <label className={`${textStyles.caption} font-medium mb-1 block`}>Duração</label>
          <select
            value={interviewSettings.duration}
            onChange={(e) => setInterviewSettings(prev => ({ ...prev, duration: e.target.value }))}
            className="w-full h-9 text-xs border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20"
          >
            <option value="30">30 min</option>
            <option value="45">45 min</option>
            <option value="60">1 hora</option>
            <option value="90">1h 30min</option>
          </select>
        </div>
        <div>
          <label className={`${textStyles.caption} font-medium mb-1 block`}>Data</label>
          <input
            type="date"
            value={interviewSettings.date}
            onChange={(e) => setInterviewSettings(prev => ({ ...prev, date: e.target.value }))}
            min={new Date().toISOString().split('T')[0]}
            className="w-full h-9 text-xs border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20"
          />
        </div>
        <div>
          <label className={`${textStyles.caption} font-medium mb-1 block`}>Horário</label>
          <input
            type="time"
            value={interviewSettings.time}
            onChange={(e) => setInterviewSettings(prev => ({ ...prev, time: e.target.value }))}
            className="w-full h-9 text-xs border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20"
          />
        </div>
      </div>

      <div>
        <label className={`${textStyles.caption} font-medium mb-1 block`}>Entrevistador</label>
        <select
          value={interviewSettings.interviewer}
          onChange={(e) => setInterviewSettings(prev => ({ ...prev, interviewer: e.target.value }))}
          className="w-full h-9 text-xs border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20"
        >
          <option value="">Selecione...</option>
          {interviewers.map((person) => (
            <option key={person} value={person}>{person}</option>
          ))}
        </select>
      </div>
    </div>
  )
}

interface VacancyLinkingSectionProps {
  type: CommunicationType
  linkToVacancy: boolean
  setLinkToVacancy: (value: boolean) => void
  selectedVacancyId: string | null
  setSelectedVacancyId: (value: string | null) => void
  selectedStage: string
  setSelectedStage: (value: string) => void
  vacancies: JobVacancy[]
  isLoadingVacancies: boolean
  linkOnCompletionOnly: boolean
  setLinkOnCompletionOnly: (value: boolean) => void
  isBulkMode: boolean
  selectedCandidatesCount: number
}

export function VacancyLinkingSection({
  type,
  linkToVacancy,
  setLinkToVacancy,
  selectedVacancyId,
  setSelectedVacancyId,
  selectedStage,
  setSelectedStage,
  vacancies,
  isLoadingVacancies,
  linkOnCompletionOnly,
  setLinkOnCompletionOnly,
  isBulkMode,
  selectedCandidatesCount
}: VacancyLinkingSectionProps) {
  return (
    <div className={`${cardStyles.default} p-4`}>
      <div className="flex items-center justify-between mb-3">
        <h4 className={`${textStyles.label} flex items-center gap-2`}>
          <Briefcase className="w-4 h-4 text-lia-text-secondary" />
          Vincular à Vaga
        </h4>
        <Switch
          checked={linkToVacancy}
          onCheckedChange={setLinkToVacancy}
        />
      </div>

      {linkToVacancy && (
        <div className="space-y-3">
          <div>
            <label className={`${textStyles.caption} font-medium mb-1.5 block`}>
              Selecionar Vaga
            </label>
            <select
              value={selectedVacancyId || ''}
              onChange={(e) => setSelectedVacancyId(e.target.value || null)}
              disabled={isLoadingVacancies}
              className="w-full h-9 text-xs border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 bg-lia-bg-primary disabled:bg-lia-bg-tertiary disabled:cursor-not-allowed"
            >
              <option value="">
                {isLoadingVacancies ? 'Carregando vagas...' : 'Selecione uma vaga'}
              </option>
              {vacancies.map((vacancy) => (
                <option key={vacancy.id} value={vacancy.id}>
                  {vacancy.title}
                  {vacancy.department ? ` - ${vacancy.department}` : ''}
                  {vacancy.status ? ` (${vacancy.status})` : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className={`${textStyles.caption} font-medium mb-1.5 block`}>
              Etapa do Pipeline
            </label>
            <select
              value={selectedStage}
              onChange={(e) => setSelectedStage(e.target.value)}
              className="w-full h-9 text-xs border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 bg-lia-bg-primary"
            >
              {PIPELINE_STAGES.map((stage) => (
                <option key={stage.value} value={stage.value}>
                  {stage.label}
                </option>
              ))}
            </select>
          </div>

          {type === 'triagem' && (
            <div className="bg-status-warning/10 border border-status-warning/30 rounded-xl p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5 text-status-warning flex-shrink-0" />
                  <div>
                    <span className="text-xs font-medium text-status-warning">
                      Vincular após completar triagem
                    </span>
                    <p className="text-micro text-status-warning mt-0.5">
                      Candidato só entra na vaga se responder a triagem
                    </p>
                  </div>
                </div>
                <Switch
                  checked={linkOnCompletionOnly}
                  onCheckedChange={setLinkOnCompletionOnly}
                />
              </div>
            </div>
          )}

          {selectedVacancyId && (
            <div className={`${type === 'triagem' && linkOnCompletionOnly ? 'bg-status-warning/10 border-status-warning/30' : 'bg-status-success/10 border-status-success/30'} border rounded-md p-2.5`}>
              <div className="flex items-center gap-2">
                {type === 'triagem' && linkOnCompletionOnly ? (
                  <Clock className="w-3.5 h-3.5 text-status-warning flex-shrink-0" />
                ) : (
                  <CheckCircle className="w-3.5 h-3.5 text-status-success flex-shrink-0" />
                )}
                <span className={`text-micro ${type === 'triagem' && linkOnCompletionOnly ? 'text-status-warning' : 'text-status-success'}`}>
                  {type === 'triagem' && linkOnCompletionOnly ? (
                    isBulkMode
                      ? `${selectedCandidatesCount} candidato(s) serão vinculados à vaga "${PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}" somente após completarem a triagem`
                      : `Candidato será vinculado à vaga na etapa "${PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}" somente após completar a triagem`
                  ) : (
                    isBulkMode
                      ? `${selectedCandidatesCount} candidato(s) serão vinculados à vaga selecionada na etapa "${PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}"`
                      : `Candidato será vinculado à vaga selecionada na etapa "${PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}"`
                  )}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
