"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  Brain, Calendar, ExternalLink, CheckCircle, Download, Linkedin,
  ClipboardCheck, FileText, Code, Gift, UserCheck, Shield, Users,
  Building, Clock, Eye, Target, AlertCircle
} from"lucide-react"
import { textStyles, cardStyles, badgeStyles, formatScorePercent } from '@/lib/design-tokens'
import type { Activity as ActivityData } from"@/data/demo-activities"

interface ActivityOtherDetailsProps {
  activity: ActivityData & { details: NonNullable<ActivityData['details']> }
  candidate: Record<string, unknown>
  onSetDiscModalData: (data: Record<string, unknown>) => void
  onSetDiscModalOpen: (open: boolean) => void
  onSetBigFiveModalCandidate: (candidate: Record<string, unknown>) => void
  onSetBigFiveModalOpen: (open: boolean) => void
}

export function ActivityInterviewScheduledDetails({ activity }: { activity: ActivityData & { details: NonNullable<ActivityData['details']> } }) {
  return (
    <div className="mt-3 space-y-3">
      <div className="bg-lia-bg-primary p-3 rounded-xl border border-lia-border-subtle">
        <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
          <Calendar className="w-3 h-3 text-wedo-purple" />
          {activity.details.interviewType}
          {activity.details.stage && (
            <Chip variant="neutral" muted className="ml-2 text-micro px-1.5 py-0">{activity.details.stage}</Chip>
          )}
        </h5>
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="bg-lia-bg-secondary p-2 rounded-xl">
            <p className={textStyles.bodySmall}>Data e Hora</p>
            <p className="text-xs font-semibold text-lia-text-primary">{activity.details.dateTime}</p>
          </div>
          <div className="bg-lia-bg-secondary p-2 rounded-xl">
            <p className={textStyles.bodySmall}>Duração</p>
            <p className="text-xs font-semibold text-lia-text-primary">{activity.details.duration}</p>
          </div>
        </div>
        <div className="bg-lia-bg-secondary p-2 rounded-xl mb-3">
          <p className={`${textStyles.bodySmall} mb-1`}>📍 Local</p>
          <p className="text-xs font-medium text-lia-text-primary">{activity.details.location}</p>
          {activity.details.meetLink && (
            <a href={activity.details.meetLink} target="_blank" rel="noopener noreferrer" className="text-xs text-lia-text-secondary hover:underline flex items-center gap-1 mt-1">
              <ExternalLink className="w-3 h-3" />Acessar link da reunião
            </a>
          )}
        </div>
        {activity.details.interviewers && (
          <div className="mb-3">
            <p className="text-xs font-semibold text-lia-text-primary mb-1">👥 Entrevistadores</p>
            <div className="space-y-1">
              {activity.details.interviewers.map((int: Record<string, unknown> | string, i: number) => (
                <div key={`int-${i}`} className="flex items-center gap-2 text-xs bg-lia-bg-secondary p-1.5 rounded-xl">
                  <div className="w-5 h-5 rounded-full bg-lia-interactive-active flex items-center justify-center text-micro font-medium text-lia-text-secondary">
                    {typeof int === 'string' ? int.charAt(0) : String(int.name ?? '').charAt(0)}
                  </div>
                  <span className="font-medium text-lia-text-primary">{typeof int === 'string' ? int : String(int.name ?? '')}</span>
                  {typeof int !== 'string' && int.role ? <span className="text-lia-text-tertiary">- {String(int.role)}</span> : null}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export function ActivityLiaEvaluationDetails({ activity }: { activity: ActivityData & { details: NonNullable<ActivityData['details']> } }) {
  return (
    <div className="mt-3 space-y-3">
      <div className="bg-lia-bg-primary p-3 rounded-xl border border-lia-border-subtle">
        <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
          <Brain className="w-3 h-3 text-wedo-cyan" />Avaliação Automática da IA
        </h5>
        <div className="grid grid-cols-4 gap-2 mb-3">
          <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
            <p className="text-base font-bold text-lia-text-primary">{formatScorePercent(activity.details.technicalScore)}</p>
            <p className={textStyles.bodySmall}>Técnico</p>
          </div>
          <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
            <p className="text-base font-bold text-lia-text-primary">{formatScorePercent(activity.details.culturalFit)}</p>
            <p className={textStyles.bodySmall}>Fit Cultural</p>
          </div>
          <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
            <p className="text-base font-bold text-lia-text-primary">{formatScorePercent(activity.details.experience)}</p>
            <p className={textStyles.bodySmall}>Experiência</p>
          </div>
          <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
            <p className="text-base font-bold text-lia-text-primary">{formatScorePercent(activity.details.softSkills)}</p>
            <p className={textStyles.bodySmall}>Soft Skills</p>
          </div>
        </div>
        {activity.details.strengths && (
          <div className="mb-2">
            <p className="text-xs font-semibold text-lia-text-primary mb-1">Pontos Fortes</p>
            <div className="flex flex-wrap gap-1">
              {activity.details.strengths.map((s: string, i: number) => (
                <Chip variant="success" muted key={`str-${i}`} className="text-micro px-1.5 py-0">✓ {s}</Chip>
              ))}
            </div>
          </div>
        )}
        <div className="bg-lia-bg-secondary p-2 rounded-xl">
          <p className="text-xs font-semibold text-lia-text-primary mb-1">Recomendação</p>
          <p className="text-xs text-lia-text-secondary">{activity.details.recommendation}</p>
        </div>
      </div>
    </div>
  )
}

export function ActivityJobApplicationDetails({ activity }: { activity: ActivityData & { details: NonNullable<ActivityData['details']> } }) {
  return (
    <div className="mt-3 space-y-3">
      <div className="bg-lia-bg-primary p-3 rounded-xl border border-lia-border-subtle">
        <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
          <FileText className="w-3 h-3 text-status-success" />Candidatura Recebida
          <Chip variant="neutral" muted className="ml-2 text-micro px-1.5 py-0">{activity.details.source}</Chip>
        </h5>
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="bg-lia-bg-secondary p-2 rounded-xl">
            <p className={textStyles.bodySmall}>ID da Aplicação</p>
            <p className="text-xs font-mono font-medium text-lia-text-primary">{activity.details.applicationId}</p>
          </div>
          <div className="bg-lia-bg-secondary p-2 rounded-xl">
            <p className={textStyles.bodySmall}>Método</p>
            <p className="text-xs font-medium text-lia-text-primary">{activity.details.applicationMethod}</p>
          </div>
          <div className="bg-lia-bg-secondary p-2 rounded-xl">
            <p className={textStyles.bodySmall}>Recebido em</p>
            <p className="text-xs font-medium text-lia-text-primary">{activity.details.receivedAt}</p>
          </div>
          <div className="bg-lia-bg-secondary p-2 rounded-xl">
            <p className={textStyles.bodySmall}>Dispositivo</p>
            <p className="text-xs font-medium text-lia-text-primary">{activity.details.device}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" className="text-xs h-7"><Download className="w-3 h-3 mr-1" />Baixar CV</Button>
          <Button size="sm" variant="outline" className="text-xs h-7"><Linkedin className="w-3 h-3 mr-1" />Ver LinkedIn</Button>
        </div>
      </div>
    </div>
  )
}

export function ActivityOfferSentDetails({ activity }: { activity: ActivityData & { details: NonNullable<ActivityData['details']> } }) {
  return (
    <div className="mt-3 space-y-3">
      <div className={`${cardStyles.default} p-3`}>
        <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
          <Gift className="w-3 h-3 text-lia-text-secondary" />Proposta Salarial
          <Chip variant="neutral" muted className={`ml-2 ${badgeStyles.primary}`}>{activity.statusLabel || 'Enviada'}</Chip>
        </h5>
        <div className="text-center p-3 bg-gradient-to-r from-lia-bg-secondary to-lia-bg-tertiary rounded-xl border border-lia-border-subtle mb-3">
          <p className="text-2xl font-semibold text-lia-text-primary">{activity.details.salary}</p>
          {activity.details.annualBonus && <p className="text-xs text-lia-text-secondary">+ Bônus: {activity.details.annualBonus}</p>}
        </div>
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="bg-lia-bg-secondary p-2 rounded-xl">
            <p className={textStyles.bodySmall}>Data de Início</p>
            <p className="text-xs font-semibold text-lia-text-primary">{activity.details.startDate}</p>
          </div>
          <div className="bg-lia-bg-secondary p-2 rounded-xl">
            <p className={textStyles.bodySmall}>Contrato</p>
            <p className="text-xs font-semibold text-lia-text-primary">{activity.details.contractType}</p>
          </div>
        </div>
        {activity.details.benefits && (
          <div className="flex flex-wrap gap-1">
            {activity.details.benefits.map((b: Record<string, unknown> | string, i: number) => (
              <Chip key={`ben-${i}`} variant="neutral" className="text-micro px-1.5 py-0">
                {typeof b === 'object' ? String(b.name ?? '') : String(b)}
              </Chip>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export function ActivityTestCompletedDetails({ activity }: { activity: ActivityData & { details: NonNullable<ActivityData['details']> } }) {
  return (
    <div className="mt-3 space-y-3">
      <div className={`${cardStyles.default} p-3`}>
        <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
          <Code className="w-3 h-3 text-status-warning" />{activity.details.testName}
          <Chip variant="neutral" muted className={`ml-2 ${(activity.score ?? 0) >= 70 ? badgeStyles.success : badgeStyles.warning}`}>
            {(activity.score ?? 0) >= 70 ? 'Aprovado' : 'Atenção'}
          </Chip>
        </h5>
        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className="text-center p-2 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
            <p className="text-base font-bold text-lia-text-primary">{activity.details.correctAnswers}/{activity.details.totalQuestions}</p>
            <p className={textStyles.caption}>Acertos</p>
          </div>
          <div className="text-center p-2 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
            <p className="text-base font-bold text-lia-text-primary">{activity.details.timeSpent}</p>
            <p className={textStyles.caption}>Tempo</p>
          </div>
          <div className={`text-center p-2 rounded-md border ${(activity.score ?? 0) >= 80 ? 'bg-status-success/10 border-status-success/30 dark:bg-status-success/20 dark:border-status-success/30' : (activity.score ?? 0) >= 60 ? 'bg-lia-bg-secondary border-lia-border-subtle' : 'bg-lia-bg-tertiary border-lia-border-default'}`}>
            <p className={`text-base font-bold ${(activity.score ?? 0) >= 80 ? 'text-status-success' : (activity.score ?? 0) >= 60 ? 'text-lia-text-primary' : 'text-lia-text-tertiary'}`}>{activity.score}%</p>
            <p className={textStyles.caption}> Nota</p>
          </div>
        </div>
        {activity.details.categories && (
          <div className="mb-3">
            <p className={`${textStyles.labelSmall} mb-2`}>📊 Performance por Categoria</p>
            <div className="space-y-1.5">
              {activity.details.categories.map((cat: Record<string, unknown>, i: number) => {
                const catScore = Number(cat.score ?? 0)
                return (
                  <div key={i} className="flex items-center gap-2">
                    <span className={`${textStyles.caption} w-28 truncate`}>{String(cat.name ?? '')}</span>
                    <div className="flex-1 bg-lia-bg-tertiary h-2 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${catScore >= 80 ? 'bg-status-success' : catScore >= 60 ? 'bg-status-success/60' : 'bg-lia-border-default'}`} style={{width: `${catScore}%`}} />
                    </div>
                    <span className="text-xs font-medium text-lia-text-primary w-8 text-right">{catScore}%</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export function ActivityRubricEvaluationDetails({ activity }: { activity: ActivityData & { details: NonNullable<ActivityData['details']> } }) {
  return (
    <div className="mt-3 space-y-3">
      <div className={`${cardStyles.default} p-3`}>
        <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
          <ClipboardCheck className="w-3 h-3 text-lia-text-secondary" />Avaliação por Rubrica (CV vs Vaga)
          <Chip variant="neutral" muted className={`ml-2 ${activity.details.overallFit >= 80 ? badgeStyles.success : activity.details.overallFit >= 60 ? badgeStyles.warning : badgeStyles.error}`}>
            {activity.details.overallFit}% fit
          </Chip>
        </h5>
        <div className="text-center p-3 bg-gradient-to-r from-lia-bg-secondary to-lia-bg-tertiary rounded-xl border border-lia-border-subtle mb-3">
          <p className="text-3xl font-semibold text-lia-text-primary">{activity.details.overallFit}%</p>
          <p className={textStyles.caption}>Fit Geral</p>
        </div>
        {activity.details.criteriaScores && (
          <div className="space-y-1.5 mb-3">
            {activity.details.criteriaScores.slice(0, 4).map((c: Record<string, unknown>, i: number) => {
              const cScore = Number(c.score ?? 0)
              return (
                <div key={i} className="flex justify-between text-xs bg-lia-bg-secondary p-1.5 rounded-xl border border-lia-border-subtle">
                  <span className="text-lia-text-primary">{String(c.criteria ?? '')}</span>
                  <Chip variant="neutral" muted className={`text-micro px-1.5 ${cScore >= 80 ? badgeStyles.success : cScore >= 60 ? badgeStyles.warning : badgeStyles.error}`}>{cScore}%</Chip>
                </div>
              )
            })}
          </div>
        )}
        <div className="bg-lia-bg-secondary p-2 rounded-xl border border-lia-border-subtle">
          <p className={`${textStyles.labelSmall} mb-1`}>💡 Recomendação</p>
          <p className={`${textStyles.caption} text-lia-text-secondary`}>{activity.details.recommendation}</p>
        </div>
      </div>
    </div>
  )
}

export function ActivityAssessmentDetails({ activity, candidate, onSetDiscModalData, onSetDiscModalOpen, onSetBigFiveModalCandidate, onSetBigFiveModalOpen }: ActivityOtherDetailsProps) {
  return (
    <div className="mt-3 space-y-3">
      <div className={`${cardStyles.default} p-3`}>
        <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
          <Brain className="w-3 h-3 text-wedo-cyan" />
          {activity.details.assessmentType || 'Assessment Comportamental'}
          <Chip variant="neutral" muted className={`ml-2 ${badgeStyles.primary}`}>{activity.details.profile}</Chip>
        </h5>
        <div className="text-center p-3 bg-gradient-to-r from-lia-bg-tertiary to-lia-bg-secondary rounded-xl border border-lia-border-default mb-3">
          <p className="text-xl font-semibold text-lia-text-primary">{activity.details.profile}</p>
          <p className={textStyles.caption}>{activity.details.profileDescription}</p>
        </div>
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="bg-lia-bg-secondary p-2 rounded-xl border border-lia-border-subtle text-center">
            <p className="text-sm font-bold text-lia-text-primary">{activity.details.culturalFit || activity.details.culturalFitScore}%</p>
            <p className={textStyles.caption}>Fit Cultural</p>
          </div>
          <div className="bg-lia-bg-secondary p-2 rounded-xl border border-lia-border-subtle text-center">
            <p className="text-sm font-bold text-lia-text-primary">{activity.details.teamworkScore}%</p>
            <p className={textStyles.caption}>Trabalho em Equipe</p>
          </div>
        </div>
        {activity.details.developmentAreas && activity.details.developmentAreas.length > 0 && (
          <div className="bg-lia-bg-secondary p-2 rounded-xl border border-lia-border-subtle">
            <p className={`${textStyles.labelSmall} text-lia-text-primary mb-1`}>⚠️ Áreas de Desenvolvimento</p>
            <div className="flex flex-wrap gap-1">
              {activity.details.developmentAreas.map((a: string, i: number) => (
                <Chip key={`dev-${i}`} variant="neutral" className="text-micro px-1.5 py-0 bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default">{a}</Chip>
              ))}
            </div>
          </div>
        )}
        <Button
          size="sm" variant="outline"
          className="w-full mt-3 text-xs h-7 border-lia-border-default text-lia-text-secondary hover:bg-lia-bg-secondary hover:bg-lia-interactive-hover"
          onClick={() => {
            if (activity.details.discScores) { onSetDiscModalData(activity.details); onSetDiscModalOpen(true) }
            else if (activity.details.bigFiveScores) { onSetBigFiveModalCandidate({ ...candidate, bigFiveScores: activity.details.bigFiveScores }); onSetBigFiveModalOpen(true) }
          }}
        >
          <Eye className="w-3 h-3 mr-1" />Ver Relatório Completo
        </Button>
      </div>
    </div>
  )
}

export function ActivityMiscDetails({ activity }: { activity: ActivityData & { details: NonNullable<ActivityData['details']> } }) {
  if (activity.type === 'technical-test') {
    return (
      <div className="mt-2 space-y-2">
        <div className="bg-lia-bg-primary p-2 rounded-xl">
          <p className={`${textStyles.bodySmall} mb-1`}>Teste Técnico</p>
          <div className="grid grid-cols-2 gap-1">
            <div><p className={textStyles.bodySmall}>Tipo</p><p className={`${textStyles.label}`}>{activity.details.testType}</p></div>
            <div><p className={textStyles.bodySmall}>Duração</p><p className={`${textStyles.label}`}>{activity.details.duration}</p></div>
            <div><p className={textStyles.bodySmall}> Nota</p><p className={`${textStyles.label}`}>{activity.details.score}/{activity.details.maxScore}</p></div>
            <div><p className={textStyles.bodySmall}>Evaluador</p><p className={`${textStyles.label}`}>{activity.details.evaluator}</p></div>
          </div>
        </div>
      </div>
    )
  }

  if (activity.type === 'english-test') {
    return (
      <div className="mt-2 space-y-2">
        <div className="bg-lia-bg-primary p-2 rounded-xl">
          <p className={`${textStyles.bodySmall} mb-1`}>Teste de Inglês</p>
          <div className="grid grid-cols-2 gap-1">
            <div><p className={textStyles.bodySmall}>Nível</p><p className={`${textStyles.label}`}>{activity.details.level}</p></div>
            <div><p className={textStyles.bodySmall}>Score CEFR</p><p className={`${textStyles.label}`}>{activity.details.score}</p></div>
            <div><p className={textStyles.bodySmall}>Certificação</p><p className={`${textStyles.label}`}>{activity.details.certification}</p></div>
            <div><p className={textStyles.bodySmall}>Válido até</p><p className={`${textStyles.label}`}>{activity.details.validUntil}</p></div>
          </div>
        </div>
      </div>
    )
  }

  if (activity.type === 'data-collection') {
    return (
      <div className="mt-2 space-y-2">
        <div className="bg-lia-bg-primary p-2 rounded-xl">
          <p className={`${textStyles.bodySmall} mb-1`}>Coleta de Dados</p>
          <div className="grid grid-cols-2 gap-1">
            <div>
              <p className={textStyles.bodySmall}>Documentos Verificados</p>
              <div className="flex flex-wrap gap-1">
                {activity.details.documentsVerified?.map((doc: string) => (
                  <Chip density="relaxed" key={doc} variant="neutral" className="px-1.5 py-0">{doc}</Chip>
                ))}
              </div>
            </div>
            <div><p className={textStyles.bodySmall}>Referências</p><p className={`${textStyles.label}`}>{activity.details.referencesChecked}</p></div>
            <div><p className={textStyles.bodySmall}>Verificação</p><p className={`${textStyles.label}`}>{activity.details.backgroundCheck}</p></div>
            <div><p className={textStyles.bodySmall}>Completeness</p><p className={`${textStyles.label}`}>{activity.details.dataCompleteness}</p></div>
          </div>
        </div>
      </div>
    )
  }

  if (activity.type === 'onboarding') {
    return (
      <div className="mt-3 space-y-3">
        <div className="bg-lia-bg-primary p-3 rounded-xl">
          <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
            <UserCheck className="w-3 h-3 text-lia-text-primary" />Processo de Onboarding
          </h5>
          <div className="bg-status-success/10 p-2 rounded-xl mb-3">
            <p className="text-xs font-semibold text-lia-text-primary mb-2">📋 Checklist de Integração</p>
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs"><CheckCircle className="w-3 h-3 text-lia-text-primary" /><span className="text-lia-text-primary">Oferta aceita e assinada</span></div>
              <div className="flex items-center gap-2 text-xs"><CheckCircle className="w-3 h-3 text-lia-text-primary" /><span className="text-lia-text-primary">Documentação enviada</span></div>
              <div className="flex items-center gap-2 text-xs"><Clock className="w-3 h-3 text-lia-text-secondary" /><span className="text-lia-text-primary">Equipamentos solicitados</span></div>
              <div className="flex items-center gap-2 text-xs"><Clock className="w-3 h-3 text-lia-text-secondary" /><span className="text-lia-text-primary">Acessos em configuração</span></div>
              <div className="flex items-center gap-2 text-xs"><AlertCircle className="w-3 h-3 text-lia-text-secondary" /><span className="text-lia-text-primary">Buddy designado (pendente)</span></div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="bg-lia-bg-primary p-2 rounded-xl">
              <p className={`${textStyles.bodySmall} mb-1`}>Data de Início</p>
              <p className="text-xs font-semibold text-lia-text-primary">{activity.details.startDate}</p>
              <p className={textStyles.bodySmall}>Segunda-feira</p>
            </div>
            <div className="bg-lia-bg-primary p-2 rounded-xl">
              <p className={`${textStyles.bodySmall} mb-1`}>Gestor Responsável</p>
              <p className="text-xs font-semibold text-lia-text-primary">{activity.details.onboardingManager}</p>
              <p className={textStyles.bodySmall}>People & Culture</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="text-center p-2 bg-lia-bg-primary rounded-xl"><FileText className="w-4 h-4 mx-auto text-lia-text-primary mb-1" /><p className={textStyles.bodySmall}>Documentos</p><p className="text-xs font-semibold text-lia-text-primary">{activity.details.documentsStatus}</p></div>
            <div className="text-center p-2 bg-lia-bg-primary rounded-xl"><Building className="w-4 h-4 mx-auto text-lia-text-secondary mb-1" /><p className={textStyles.bodySmall}>Equipamentos</p><p className="text-xs font-semibold text-lia-text-primary">{activity.details.equipmentStatus}</p></div>
            <div className="text-center p-2 bg-lia-bg-primary rounded-xl"><Shield className="w-4 h-4 mx-auto text-lia-text-primary mb-1" /><p className={textStyles.bodySmall}>Acessos</p><p className="text-xs font-semibold text-lia-text-primary">{activity.details.accessesStatus}</p></div>
            <div className="text-center p-2 bg-lia-bg-primary rounded-xl"><Users className="w-4 h-4 mx-auto text-lia-text-primary mb-1" /><p className={textStyles.bodySmall}>Buddy</p><p className="text-xs font-semibold text-lia-text-primary">A definir</p></div>
          </div>
        </div>
      </div>
    )
  }

  if (activity.type === 'interview-note') {
    return (
      <div className="mt-2 space-y-2">
        {activity.details.technicalQuestions && (
          <div className="bg-lia-bg-primary p-2 rounded-xl">
            <p className={`${textStyles.bodySmall} mb-1`}>Questões Técnicas</p>
            <div className="space-y-1">
              {activity.details.technicalQuestions.map((q: Record<string, unknown>, i: number) => (
                <div key={i} className="flex items-center justify-between">
                  <span className={textStyles.bodySmall}>{String(q.question ?? '')}</span>
                  <Chip density="relaxed" variant="neutral" muted className="px-1 py-0">{String(q.score ?? 0)}/10</Chip>
                </div>
              ))}
            </div>
          </div>
        )}
        {activity.details.overallScore && (
          <div className="bg-lia-bg-primary p-2 rounded-xl">
            <div className="flex items-center justify-between">
              <span className={textStyles.bodySmall}>Score Geral</span>
              <span className="text-xs font-bold text-lia-text-primary">{activity.details.overallScore}/10</span>
            </div>
            <p className={`${textStyles.bodySmall} mt-1`}>{activity.details.recommendation}</p>
          </div>
        )}
      </div>
    )
  }

  if (activity.type === 'lia-screening' && activity.details.conversation) {
    return (
      <div className="mt-2 space-y-2">
        <div className="bg-lia-bg-primary p-2 rounded-xl max-h-48 overflow-y-auto">
          <p className="text-xs text-lia-text-primary mb-2">{activity.platform}</p>
          <div className="space-y-2">
            {activity.details.conversation.map((msg: Record<string, unknown>, i: number) => (
              <div key={i} className={`flex ${String(msg.sender) === 'LIA' ? 'justify-start' : 'justify-end'}`}>
                <div className={`max-w-[70%] px-2 py-1 rounded-md ${String(msg.sender) === 'LIA' ? 'bg-lia-bg-tertiary text-lia-text-primary' : 'bg-lia-bg-secondary text-lia-text-primary'}`}>
                  <p className="text-xs">{String(msg.message ?? '')}</p>
                  <span className="text-xs opacity-70">{String(msg.time ?? '')}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        {activity.details.keyPoints && (
          <div className="bg-lia-bg-primary p-2 rounded-xl">
            <p className={`${textStyles.bodySmall} mb-1`}>Pontos-Chave</p>
            <div className="space-y-0.5">
              <div className="flex justify-between text-xs"><span className="text-lia-text-secondary">Disponibilidade:</span><span className="text-lia-text-primary">{activity.details.keyPoints.availability}</span></div>
              <div className="flex justify-between text-xs"><span className="text-lia-text-secondary">Pretensão:</span><span className="text-lia-text-primary">{activity.details.keyPoints.salary}</span></div>
              <div className="flex justify-between text-xs"><span className="text-lia-text-secondary">Inglês:</span><span className="text-lia-text-primary">{activity.details.keyPoints.english}</span></div>
            </div>
          </div>
        )}
      </div>
    )
  }

  return null
}
