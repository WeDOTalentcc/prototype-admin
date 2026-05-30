"use client"
import React from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import {
  CheckCircle, Download, Linkedin,
  ClipboardCheck, FileText, Code, Gift, UserCheck,
  Shield, Users, Building, Clock, AlertCircle
} from"lucide-react"
import type { TimelineActivity as ActivityData } from"./ActivityTimeline"

interface ActivityMiscDetailsProps {
  activity: ActivityData & { details: NonNullable<ActivityData['details']> }
}

export function ActivityMiscDetails({ activity }: ActivityMiscDetailsProps) {
  return (
    <>
      {activity.type === 'job-application' && (
        <div className="mt-3 space-y-3">
          <div className="bg-lia-bg-primary p-3 rounded-xl border border-lia-border-subtle">
            <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
              <FileText className="w-3 h-3 text-status-success" />
              Candidatura Recebida
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
              <Button size="sm" variant="outline" className="text-xs h-7">
                <Download className="w-3 h-3 mr-1" />
                Baixar CV
              </Button>
              <Button size="sm" variant="outline" className="text-xs h-7">
                <Linkedin className="w-3 h-3 mr-1" />
                Ver LinkedIn
              </Button>
            </div>
          </div>
        </div>
      )}

      {activity.type === 'test-completed' && (
        <div className="mt-3 space-y-3">
          <div className={`${cardStyles.default} p-3`}>
            <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
              <Code className="w-3 h-3 text-status-warning" />
              {activity.details.testName}
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
                        <div
                          className={`h-full rounded-full ${catScore >= 80 ? 'bg-status-success' : catScore >= 60 ? 'bg-status-success/60' : 'bg-lia-border-default'}`}
                          style={{width: `${catScore}%`}}
                        />
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
      )}

      {activity.type === 'offer-sent' && (
        <div className="mt-3 space-y-3">
          <div className={`${cardStyles.default} p-3`}>
            <h5 className={`${textStyles.label} mb-2 flex items-center gap-1`}>
              <Gift className="w-3 h-3 text-lia-text-secondary" />
              Proposta Salarial
              <Chip variant="neutral" muted className={`ml-2 ${badgeStyles.primary}`}>
                {activity.statusLabel || 'Enviada'}
              </Chip>
            </h5>
            <div className="text-center p-3 bg-gradient-to-r from-lia-bg-secondary to-lia-bg-tertiary rounded-xl border border-lia-border-subtle mb-3">
              <p className="text-2xl font-semibold text-lia-text-primary">{activity.details.salary}</p>
              {activity.details.annualBonus && (
                <p className="text-xs text-lia-text-secondary">+ Bônus: {activity.details.annualBonus}</p>
              )}
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
      )}

      {activity.type === 'technical-test' && (
        <div className="mt-2 space-y-2">
          <div className="bg-lia-bg-primary p-2 rounded-xl">
            <p className={`${textStyles.bodySmall} mb-1`}>Teste Técnico</p>
            <div className="grid grid-cols-2 gap-1">
              <div>
                <p className={textStyles.bodySmall}>Tipo</p>
                <p className={`${textStyles.label}`}>{activity.details.testType}</p>
              </div>
              <div>
                <p className={textStyles.bodySmall}>Duração</p>
                <p className={`${textStyles.label}`}>{activity.details.duration}</p>
              </div>
              <div>
                <p className={textStyles.bodySmall}> Nota</p>
                <p className={`${textStyles.label}`}>{activity.details.score}/{activity.details.maxScore}</p>
              </div>
              <div>
                <p className={textStyles.bodySmall}>Evaluador</p>
                <p className={`${textStyles.label}`}>{activity.details.evaluator}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {activity.type === 'english-test' && (
        <div className="mt-2 space-y-2">
          <div className="bg-lia-bg-primary p-2 rounded-xl">
            <p className={`${textStyles.bodySmall} mb-1`}>Teste de Inglês</p>
            <div className="grid grid-cols-2 gap-1">
              <div>
                <p className={textStyles.bodySmall}>Nível</p>
                <p className={`${textStyles.label}`}>{activity.details.level}</p>
              </div>
              <div>
                <p className={textStyles.bodySmall}>Score CEFR</p>
                <p className={`${textStyles.label}`}>{activity.details.score}</p>
              </div>
              <div>
                <p className={textStyles.bodySmall}>Certificação</p>
                <p className={`${textStyles.label}`}>{activity.details.certification}</p>
              </div>
              <div>
                <p className={textStyles.bodySmall}>Válido até</p>
                <p className={`${textStyles.label}`}>{activity.details.validUntil}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {activity.type === 'data-collection' && (
        <div className="mt-2 space-y-2">
          <div className="bg-lia-bg-primary p-2 rounded-xl">
            <p className={`${textStyles.bodySmall} mb-1`}>Coleta de Dados</p>
            <div className="grid grid-cols-2 gap-1">
              <div>
                <p className={textStyles.bodySmall}>Documentos Verificados</p>
                <div className="flex flex-wrap gap-1">
                  {activity.details.documentsVerified?.map((doc: string) => (
                    <Chip density="relaxed" key={doc} variant="neutral" className="px-1.5 py-0">
                      {doc}
                    </Chip>
                  ))}
                </div>
              </div>
              <div>
                <p className={textStyles.bodySmall}>Referências</p>
                <p className={`${textStyles.label}`}>{activity.details.referencesChecked}</p>
              </div>
              <div>
                <p className={textStyles.bodySmall}>Verificação</p>
                <p className={`${textStyles.label}`}>{activity.details.backgroundCheck}</p>
              </div>
              <div>
                <p className={textStyles.bodySmall}>Completeness</p>
                <p className={`${textStyles.label}`}>{activity.details.dataCompleteness}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {activity.type === 'onboarding' && (
        <div className="mt-3 space-y-3">
          <div className="bg-lia-bg-primary p-3 rounded-xl">
            <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
              <UserCheck className="w-3 h-3 text-lia-text-primary" />
              Processo de Onboarding
            </h5>
            <div className="bg-status-success/10 p-2 rounded-md mb-3">
              <p className="text-xs font-semibold text-lia-text-primary mb-2">📋 Checklist de Integração</p>
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs">
                  <CheckCircle className="w-3 h-3 text-lia-text-primary" />
                  <span className="text-lia-text-primary">Oferta aceita e assinada</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <CheckCircle className="w-3 h-3 text-lia-text-primary" />
                  <span className="text-lia-text-primary">Documentação enviada</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <Clock className="w-3 h-3 text-lia-text-secondary" />
                  <span className="text-lia-text-primary">Equipamentos solicitados</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <Clock className="w-3 h-3 text-lia-text-secondary" />
                  <span className="text-lia-text-primary">Acessos em configuração</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <AlertCircle className="w-3 h-3 text-lia-text-secondary" />
                  <span className="text-lia-text-primary">Buddy designado (pendente)</span>
                </div>
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
              <div className="text-center p-2 bg-lia-bg-primary rounded-xl">
                <FileText className="w-4 h-4 mx-auto text-lia-text-primary mb-1" />
                <p className={textStyles.bodySmall}>Documentos</p>
                <p className="text-xs font-semibold text-lia-text-primary">{activity.details.documentsStatus}</p>
              </div>
              <div className="text-center p-2 bg-lia-bg-primary rounded-xl">
                <Building className="w-4 h-4 mx-auto text-lia-text-secondary mb-1" />
                <p className={textStyles.bodySmall}>Equipamentos</p>
                <p className="text-xs font-semibold text-lia-text-primary">{activity.details.equipmentStatus}</p>
              </div>
              <div className="text-center p-2 bg-lia-bg-primary rounded-xl">
                <Shield className="w-4 h-4 mx-auto text-lia-text-primary mb-1" />
                <p className={textStyles.bodySmall}>Acessos</p>
                <p className="text-xs font-semibold text-lia-text-primary">{activity.details.accessesStatus}</p>
              </div>
              <div className="text-center p-2 bg-lia-bg-primary rounded-xl">
                <Users className="w-4 h-4 mx-auto text-lia-text-primary mb-1" />
                <p className={textStyles.bodySmall}>Buddy</p>
                <p className="text-xs font-semibold text-lia-text-primary">A definir</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {activity.type === 'interview-note' && (
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
      )}
    </>
  )
}
