"use client"
import React from"react"
import { Chip } from "@/components/ui/chip"
import { textStyles } from '@/lib/design-tokens'
import {
  Calendar, ExternalLink, CheckCircle, Mail
} from"lucide-react"
import type { TimelineActivity as ActivityData } from"./ActivityTimeline"

interface ActivityCommunicationDetailsProps {
  activity: ActivityData & { details: NonNullable<ActivityData['details']> }
}

export function ActivityCommunicationDetails({ activity }: ActivityCommunicationDetailsProps) {
  return (
    <>
      {activity.type === 'email-sent' && (
        <div className="mt-3 space-y-3">
          <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl overflow-hidden">
            <div className="bg-lia-bg-secondary px-4 py-3">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-lia-text-tertiary w-12">De:</span>
                  <span className="text-lia-text-primary font-medium">{activity.details.from}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-lia-text-tertiary w-12">Para:</span>
                  <span className="text-lia-text-primary">{activity.details.to}</span>
                </div>
                {activity.details.cc && (
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-lia-text-tertiary w-12">Cc:</span>
                    <span className="text-lia-text-primary">{activity.details.cc}</span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-lia-text-tertiary w-12">Assunto:</span>
                  <span className="text-lia-text-primary font-semibold">{activity.details.subject}</span>
                </div>
              </div>
            </div>
            <div className="px-4 py-3">
              <div className="text-xs text-lia-text-primary whitespace-pre-line leading-relaxed max-h-48 overflow-y-auto">
                {activity.details.body}
              </div>
            </div>
            {activity.details.attachments && activity.details.attachments.length > 0 && (
              <div className="px-4 py-2 bg-lia-bg-secondary border-t border-lia-border-subtle">
                <p className="text-micro text-lia-text-tertiary mb-1">Anexos:</p>
                <div className="flex flex-wrap gap-1">
                  {activity.details.attachments.map((att: string, i: number) => (
                    <Chip key={`att-${i}`} variant="neutral" className="text-micro px-1.5 py-0 bg-lia-bg-primary">
                      📎 {att}
                    </Chip>
                  ))}
                </div>
              </div>
            )}
          </div>
          {activity.details.opened && (
            <div className="flex items-center gap-2 text-xs text-status-success bg-status-success/10 p-2 rounded-md">
              <CheckCircle className="w-3 h-3" />
              <span>Email aberto em {activity.details.openedAt}</span>
            </div>
          )}
          {activity.details.suggestedTimes && (
            <div className="flex flex-wrap gap-1">
              {activity.details.suggestedTimes.map((t: string, i: number) => (
                <Chip variant="neutral" muted key={`stime-${i}`} className="text-micro px-2 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle">
                  📅 {t}
                </Chip>
              ))}
            </div>
          )}
        </div>
      )}

      {activity.type === 'interview-scheduled' && (
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
                  <ExternalLink className="w-3 h-3" />
                  Acessar link da reunião
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
      )}

      {activity.type === 'lia-screening' && activity.details.conversation && (
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
                <div className="flex justify-between text-xs">
                  <span className="text-lia-text-secondary">Disponibilidade:</span>
                  <span className="text-lia-text-primary">{activity.details.keyPoints.availability}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-lia-text-secondary">Pretensão:</span>
                  <span className="text-lia-text-primary">{activity.details.keyPoints.salary}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-lia-text-secondary">Inglês:</span>
                  <span className="text-lia-text-primary">{activity.details.keyPoints.english}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {(activity.type === 'email-sent' || activity.type === 'email-received') && activity.details.subject && !activity.details.from?.includes('@') && (
        <div className="mt-3 space-y-3">
          <div className="bg-lia-bg-primary p-3 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1">
                <Mail className="w-3 h-3 text-lia-text-primary" />
                {activity.type === 'email-sent' ? 'Email Enviado' : 'Email Recebido'}
              </h5>
              {activity.details.opened && (
                <Chip density="relaxed" variant="neutral" muted className="px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-primary">
                  ✓ Lido
                </Chip>
              )}
            </div>
            <div className="bg-lia-bg-primary p-2 rounded-xl mb-2 text-xs space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-lia-text-primary font-medium">De:</span>
                <span className="text-lia-text-primary">
                  {activity.type === 'email-sent' ? activity.author : activity.details.from}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-lia-text-primary font-medium">Para:</span>
                <span className="text-lia-text-primary">
                  {activity.type === 'email-sent' ? activity.details.to : activity.author}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-lia-text-primary font-medium">Data:</span>
                <span className="text-lia-text-primary">{activity.date}</span>
              </div>
            </div>
            <p className="text-xs font-semibold text-lia-text-primary mb-2">{activity.details.subject}</p>
            <div className="text-xs text-lia-text-primary space-y-2">
              {activity.details.body ? (
                <>
                  <p>{activity.details.body}</p>
                  {activity.details.attachments && (
                    <div className="mt-2 pt-2 border-t">
                      <p className={`${textStyles.bodySmall} mb-1`}>📎 Anexos:</p>
                      <div className="flex flex-wrap gap-1">
                        {activity.details.attachments.map((file: string, i: number) => (
                          <Chip density="relaxed" key={`file-${i}`} variant="neutral" className="px-1.5 py-0.5">
                            {file}
                          </Chip>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-lia-text-secondary italic">Conteúdo do email não disponível</p>
              )}
            </div>
            {activity.details.opened && (
              <div className="mt-2 flex items-center gap-2 text-xs text-lia-text-primary">
                <CheckCircle className="w-3 h-3" />
                <span>Email aberto {activity.details.openedAt}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
