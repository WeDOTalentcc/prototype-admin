"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, Mail } from "lucide-react"
import { textStyles } from '@/lib/design-tokens'
import type { Activity as ActivityData } from "@/data/demo-activities"

interface ActivityEmailDetailsProps {
  activity: ActivityData & { details: NonNullable<ActivityData['details']> }
}

export function ActivityEmailSentDetails({ activity }: ActivityEmailDetailsProps) {
  return (
    <div className="mt-3 space-y-3">
      <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-md overflow-hidden">
        <div className="bg-lia-bg-secondary px-4 py-3 border-b border-lia-border-subtle">
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
                <Badge key={`att-${i}`} variant="outline" className="text-micro px-1.5 py-0 bg-lia-bg-primary">
                  📎 {att}
                </Badge>
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
            <Badge key={`stime-${i}`} className="text-micro px-2 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle">
              📅 {t}
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}

export function ActivityGenericEmailDetails({ activity }: ActivityEmailDetailsProps) {
  return (
    <div className="mt-3 space-y-3">
      <div className="bg-lia-bg-primary p-3 rounded-md">
        <div className="flex items-center justify-between mb-2">
          <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1">
            <Mail className="w-3 h-3 text-lia-text-primary" />
            {activity.type === 'email-sent' ? 'Email Enviado' : 'Email Recebido'}
          </h5>
          {activity.details.opened && (
            <Badge className="text-xs px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-primary">
              ✓ Lido
            </Badge>
          )}
        </div>
        <div className="bg-lia-bg-primary p-2 rounded-md mb-2 text-xs space-y-1">
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
                      <Badge key={`file-${i}`} variant="outline" className="text-xs px-1.5 py-0.5">
                        {file}
                      </Badge>
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
  )
}
