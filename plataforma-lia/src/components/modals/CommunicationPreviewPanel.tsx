"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback } from"@/components/ui/avatar"
import {
  Mail, MessageSquare, Eye, Info, CheckCircle, CalendarDays, Clock
} from"lucide-react"
import { textStyles, badgeStyles } from '@/lib/design-tokens'
import { sanitizeHtml } from"@/lib/sanitize"
import type { CommunicationType, CommunicationChannel } from"./unified-communication-modal"

interface CommunicationPreviewPanelProps {
  channel: CommunicationChannel
  type: CommunicationType
  subject: string
  message: string
  safeCandidate: {
    name: string
    email: string
    phone: string
  }
  selectedCandidates: Array<{ id: string; name: string }>
  isBulkMode: boolean
  selectedStage: string
  linkToVacancy: boolean
  linkOnCompletionOnly: boolean
}

const PIPELINE_STAGES = [
  { value: 'novo', label: 'Novo' },
  { value: 'triagem', label: 'Triagem' },
  { value: 'entrevista', label: 'Entrevista' },
  { value: 'avaliacao', label: 'Avaliação' },
  { value: 'oferta', label: 'Oferta' }
]

const formatPreviewMessage = (text: string) => {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\[(.*?)\]/g, '<span class="text-lia-text-secondary underline cursor-pointer">$1</span>')
    .replace(/•/g, '&bull;')
    .replace(/\n/g, '<br>')
}

export function CommunicationPreviewPanel({
  channel,
  type,
  subject,
  message,
  safeCandidate,
}: CommunicationPreviewPanelProps) {
  return (
    <div className="w-1/2 bg-lia-bg-secondary overflow-y-auto" data-testid="communication-preview-panel">
      <div className="p-5">
        <div className="flex items-center justify-between mb-4">
          <h4 className={`${textStyles.label} flex items-center gap-2`}>
            <Eye className="w-3.5 h-3.5 text-lia-text-secondary" />
            Preview da Mensagem
          </h4>
          <Chip variant="neutral" className={badgeStyles.default}>
            {channel === 'email' ? 'Email' : channel === 'whatsapp' ? 'WhatsApp' : 'Email + WhatsApp'}
          </Chip>
        </div>

        <div className={`rounded-md overflow-hidden ${
          channel === 'whatsapp' ? 'bg-whatsapp-bg' : 'bg-lia-bg-primary border border-lia-border-subtle'
        }`}>
          {(channel === 'email' || channel === 'both') ? (
            <div>
              <div className="px-4 py-3 bg-lia-bg-secondary">
                <div className="flex items-center gap-2 mb-2">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="text-micro bg-lia-btn-primary-bg text-lia-btn-primary-text">RH</AvatarFallback>
                  </Avatar>
                  <div>
                    <div className={textStyles.bodySmall}>Equipe de Recrutamento</div>
                    <div className={textStyles.caption}>recrutamento@empresa.com</div>
                  </div>
                </div>
                <div className={textStyles.caption}>
                  Para: <span className="text-lia-text-primary">{safeCandidate.email}</span>
                </div>
              </div>
              <div className="px-4 py-2">
                <div className={textStyles.subtitle}>
                  {subject || 'Sem assunto'}
                </div>
              </div>
              <div className="px-4 py-4">
                <div 
                  className={`${textStyles.body} leading-relaxed`}
                  dangerouslySetInnerHTML={{ __html: sanitizeHtml(formatPreviewMessage(message) || '<span class="text-lia-text-secondary">A mensagem aparecerá aqui...</span>') }}
                />
              </div>
            </div>
          ) : (
            <div className="p-3">
              <div className="flex justify-end mb-2">
                <div className="bg-whatsapp-bubble rounded-md p-3 max-w-[85%]">
                  <div 
                    className={`${textStyles.body} leading-relaxed whitespace-pre-wrap`}
                    dangerouslySetInnerHTML={{ __html: sanitizeHtml(formatPreviewMessage(message) || '<span class="text-lia-text-secondary">A mensagem aparecerá aqui...</span>') }}
                  />
                  <div className={`${textStyles.caption} text-right mt-1`}>
                    {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} ✓✓
                  </div>
                </div>
              </div>
              <div className={`text-center ${textStyles.caption} mt-3 bg-lia-bg-primary/60 rounded-full py-1 px-3 inline-block mx-auto`}>
                Será enviado via WhatsApp Business API
              </div>
            </div>
          )}
        </div>

        {type === 'triagem' && (
          <div className="mt-4 bg-status-warning/10 border border-status-warning/30 rounded-xl p-3">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-status-warning flex-shrink-0 mt-0.5" />
              <div className="text-micro text-status-warning">
                <strong>Fluxo de Triagem:</strong>
                <ul className="mt-1 space-y-0.5 ml-2">
                  <li>• Candidato recebe a mensagem com link</li>
                  <li>• Ao clicar, visualiza aviso LGPD e aceita termos</li>
                  <li>• LIA inicia a conversa de triagem automaticamente</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {type === 'agendamento' && (
          <div className="mt-4 bg-lia-bg-tertiary border border-lia-border-default rounded-xl p-3">
            <div className="flex items-start gap-2">
              <CalendarDays className="w-4 h-4 text-lia-text-secondary flex-shrink-0 mt-0.5" />
              <div className="text-micro text-wedo-cyan-text">
                <strong>Após Confirmação:</strong>
                <ul className="mt-1 space-y-0.5 ml-2">
                  <li>• Candidato escolhe horário disponível</li>
                  <li>• Recebe email de confirmação automático</li>
                  <li>• Convite de calendário (Outlook/Google)</li>
                  <li>• Link da plataforma de vídeo incluso</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {type === 'feedback' && (
          <div className="mt-4 bg-status-success/10 border border-status-success/30 rounded-xl p-3">
            <div className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-status-success flex-shrink-0 mt-0.5" />
              <div className="text-micro text-status-success">
                <strong>Dica:</strong> Um feedback bem estruturado fortalece a marca empregadora e mantém bom relacionamento com candidatos.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
