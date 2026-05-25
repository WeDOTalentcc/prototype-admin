"use client"

import React from "react"
import {
  Bot,
  Play,
  Pause,
  MoreVertical,
  Link2,
  TestTube2,
  Copy,
  Phone,
  PhoneCall,
  MessageCircle,
  Mic,
  Send,
} from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles } from "@/lib/design-tokens"
// Sprint B QW#15 audit 2026-05-22: 3-dot menu para Clone (era enterrado em drawer)
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { getCustomAgentStatusConfig } from "@/lib/agent-studio/status-config"
import { BetaBadge } from "@/components/ui/beta-badge"
import { Switch } from "@/components/ui/switch"
import { useToggleAgentVoice, useInitiateVoiceCall } from "@/hooks/agent-studio/use-agent-voice"
import { useToggleAgentWhatsApp } from "@/hooks/agent-studio/use-agent-whatsapp"
import { useToggleAgentChannel } from "@/hooks/agent-studio/use-agent-channel"
import { useInitiateAgentTriagemInvite } from "@/hooks/agent-studio/use-agent-triagem-invite"
import type { CustomAgent } from "./types"
import { safeCategoryKey } from "./types"

interface AgentCardProps {
  agent: CustomAgent
  onTest: (agent: CustomAgent) => void
  onDeploy: (agent: CustomAgent) => void
  onToggleStatus: (agent: CustomAgent) => void
  /** Sprint B QW#15 audit 2026-05-22: Clone handler — opcional (caller decide se expõe) */
  onClone?: (agent: CustomAgent) => void
}

/**
 * W-Channels-A (2026-05-23) — channel row renderer.
 *
 * Cada um dos 3 canais (whatsapp / voice / voip) é renderizado por
 * este sub-componente para garantir consistência visual + ARIA. Os toggles
 * são INDEPENDENTES — não há regra de exclusão mútua, cliente combina como
 * preferir (mental model Paulo, decisão Opção B 2026-05-23).
 */
function ChannelToggleRow({
  icon: Icon,
  label,
  enabled,
  disabled,
  onToggle,
  ariaOn,
  ariaOff,
  testId,
  trailing,
}: {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>
  label: string
  enabled: boolean
  disabled: boolean
  onToggle: (next: boolean) => void
  ariaOn: string
  ariaOff: string
  testId: string
  trailing?: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-2 pt-2 border-t border-lia-border-subtle">
      <div className="flex items-center gap-2 text-xs">
        <Icon className="w-3.5 h-3.5 text-lia-text-disabled" aria-hidden="true" />
        <span className="text-lia-text-secondary">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        {trailing}
        <Switch
          checked={enabled}
          disabled={disabled}
          onCheckedChange={(next) => onToggle(next)}
          aria-label={enabled ? ariaOff : ariaOn}
          data-testid={testId}
        />
      </div>
    </div>
  )
}

export function AgentCard({ agent, onTest, onDeploy, onToggleStatus, onClone }: AgentCardProps) {
  const t = useTranslations('agents.card')
  // W-Channels-A revisão (2026-05-23): 3 canais canonical independentes
  // (whatsapp / voice / voip). in_app revertido — gap conceitual; chat candidato
  // público vive em /api/v1/triagem/. voice = PSTN, voip = browser/Gemini Live.
  const toggleWhatsApp = useToggleAgentWhatsApp(agent.id)
  const toggleVoice = useToggleAgentVoice(agent.id)
  const toggleVoip = useToggleAgentChannel(agent.id, 'voip')
  // Workstream A 2026-05-23: 4o toggle — capability "convite triagem".
  const toggleTriagemInvite = useToggleAgentChannel(agent.id, 'triagem_invite')
  const initiateVoice = useInitiateVoiceCall(agent.id)
  const initiateTriagemInvite = useInitiateAgentTriagemInvite(agent.id)

  // Backward compat: voip=false; voice=false; whatsapp=false; triagem_invite=false.
  const whatsappEnabled = Boolean(agent.whatsapp_enabled)
  const voiceEnabled = Boolean(agent.voice_enabled)
  const voipEnabled = Boolean(agent.voip_enabled)
  const triagemInviteEnabled = Boolean(agent.triagem_invite_enabled)

  const tStatus = useTranslations('agents.status')
  const tCat = useTranslations('agents.customAgents')

  // UX-Sprint-A QW#18 Batch 3 (audit 2026-05-21): STATUS_STYLES extraído para
  // lib/agent-studio/status-config.ts canonical. Label fica local (i18n tStatus).
  const statusConfig = getCustomAgentStatusConfig(agent.status)
  const statusStyle = {
    label: tStatus(agent.status as "draft" | "active" | "paused" | "archived") || tStatus("draft"),
    badge: statusConfig.badge,
  }
  const category = safeCategoryKey(agent.domain)
  const categoryLabel = tCat('categories.' + category) || agent.domain || 'general'

  return (
    <div className={cn(cardStyles.default, "p-4 flex flex-col gap-3 relative")}>
      {/* Header */}
      <div className="flex items-start justify-between">
        {/* Sprint B QW#15 audit 2026-05-22: 3-dot menu via DropdownMenu shadcn */}
        {onClone && (
          <div className="absolute top-3 right-3">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  className="p-1 rounded-md text-lia-text-disabled hover:text-lia-text-primary hover:bg-lia-bg-tertiary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30"
                  aria-label={t('moreActions') || 'Mais ações'}
                >
                  <MoreVertical className="w-4 h-4" aria-hidden="true" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40">
                <DropdownMenuItem onClick={() => onClone(agent)} className="gap-2 cursor-pointer">
                  <Copy className="w-3.5 h-3.5" aria-hidden="true" />
                  {t('clone') || 'Duplicar'}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-powder flex items-center justify-center">
            <Bot className="w-4 h-4 text-graphite" />
          </div>
          <div>
            <h4 className={cn(textStyles.subtitle, "text-sm font-semibold leading-tight")}>
              {agent.name}
            </h4>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={cn(badgeStyles.default, "text-[10px]")}>{categoryLabel}</span>
              <span className={cn(statusStyle.badge, "text-[10px]")}>{statusStyle.label}</span>
            </div>
          </div>
        </div>
        <BetaBadge size="sm" />
      </div>

      {/* Description */}
      {agent.description && (
        <p className={cn(textStyles.caption, "text-xs line-clamp-2")}>{agent.description}</p>
      )}

      {/* Metrics */}
      <div className="flex items-center gap-4 text-xs">
        <div>
          <span className="font-bold text-lia-text-primary font-sans">{agent.total_executions}</span>
          <span className="text-lia-text-disabled ml-1">{t('executions')}</span>
        </div>
        {agent.avg_confidence > 0 && (
          <div>
            <span className="font-bold text-lia-text-primary font-sans">{(agent.avg_confidence * 100).toFixed(0)}%</span>
            <span className="text-lia-text-disabled ml-1">{t('confidence')}</span>
          </div>
        )}
      </div>

      {/* W-Channels-A revisão 2026-05-23: 3 canais canonical (whatsapp / voice / voip) */}
      {/* in_app revertido — gap conceitual; chat candidato público = /api/v1/triagem/ */}
      {/* 1. WhatsApp */}
      <ChannelToggleRow
        icon={MessageCircle}
        label={t('whatsapp') || 'WhatsApp'}
        enabled={whatsappEnabled}
        disabled={toggleWhatsApp.isMutating}
        onToggle={(next) => toggleWhatsApp.trigger(next)}
        ariaOn={t('enableWhatsapp', { name: agent.name }) || `Habilitar WhatsApp no agente ${agent.name}`}
        ariaOff={t('disableWhatsapp', { name: agent.name }) || `Desabilitar WhatsApp no agente ${agent.name}`}
        testId="agent-card-whatsapp-toggle"
      />

      {/* 2. Voz PSTN (ligação telefônica) — trailing = botão Iniciar chamada */}
      <ChannelToggleRow
        icon={Phone}
        label={t('voice') || 'Ligação telefônica'}
        enabled={voiceEnabled}
        disabled={toggleVoice.isMutating}
        onToggle={(next) => toggleVoice.trigger(next)}
        ariaOn={t('enableVoice', { name: agent.name }) || `Habilitar voz no agente ${agent.name}`}
        ariaOff={t('disableVoice', { name: agent.name }) || `Desabilitar voz no agente ${agent.name}`}
        testId="agent-card-voice-toggle"
        trailing={
          <button
            type="button"
            onClick={() => {
              if (!voiceEnabled) return
              initiateVoice.trigger({ candidate_id: "" })
            }}
            disabled={!voiceEnabled || initiateVoice.isMutating}
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium text-graphite hover:bg-powder transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label={voiceEnabled ? t('startVoiceCall') : t('voiceDisabled')}
            data-testid="agent-card-initiate-voice"
          >
            <PhoneCall className="w-3.5 h-3.5" aria-hidden="true" />
            {t('startCall')}
          </button>
        }
      />

      {/* 3. Voz no navegador (VoIP) */}
      <ChannelToggleRow
        icon={Mic}
        label={t('voip') || 'Voz no navegador (VoIP)'}
        enabled={voipEnabled}
        disabled={toggleVoip.isMutating}
        onToggle={(next) => toggleVoip.trigger(next)}
        ariaOn={t('enableVoip', { name: agent.name }) || `Habilitar voz no navegador (VoIP) no agente ${agent.name}`}
        ariaOff={t('disableVoip', { name: agent.name }) || `Desabilitar voz no navegador (VoIP) no agente ${agent.name}`}
        testId="agent-card-voip-toggle"
      />

      {/* 4. Convite triagem — Workstream A 2026-05-23. */}
      {/* Capability: cria token unico + URL publica /triagem/{token} entregue via email/WhatsApp. */}
      <ChannelToggleRow
        icon={Send}
        label={t('triagemInvite') || 'Convite triagem'}
        enabled={triagemInviteEnabled}
        disabled={toggleTriagemInvite.isMutating}
        onToggle={(next) => toggleTriagemInvite.trigger(next)}
        ariaOn={t('enableTriagemInvite', { name: agent.name }) || `Habilitar criacao de convites de triagem no agente ${agent.name}`}
        ariaOff={t('disableTriagemInvite', { name: agent.name }) || `Desabilitar criacao de convites de triagem no agente ${agent.name}`}
        testId="agent-card-triagem-invite-toggle"
        trailing={
          <button
            type="button"
            onClick={() => {
              if (!triagemInviteEnabled) return
              initiateTriagemInvite.trigger({ candidate_id: "", job_id: "" })
            }}
            disabled={!triagemInviteEnabled || initiateTriagemInvite.isMutating}
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium text-graphite hover:bg-powder transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label={triagemInviteEnabled ? (t('sendTriagemInvite') || 'Enviar convite triagem') : (t('triagemInviteDisabled') || 'Convite triagem desabilitado')}
            data-testid="agent-card-initiate-triagem-invite"
          >
            <Send className="w-3.5 h-3.5" aria-hidden="true" />
            {t('sendInvite') || 'Enviar convite'}
          </button>
        }
      />

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1 border-t border-lia-border-subtle">
        <button
          type="button"
          onClick={() => onTest(agent)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors"
        >
          <TestTube2 className="w-3.5 h-3.5" /> {t('test')}
        </button>
        <button
          type="button"
          onClick={() => onDeploy(agent)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-graphite hover:bg-powder transition-colors"
        >
          <Link2 className="w-3.5 h-3.5" /> {t('link')}
        </button>
        <button
          type="button"
          onClick={() => onToggleStatus(agent)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors ml-auto"
        >
          {agent.status === "active" ? (
            <><Pause className="w-3.5 h-3.5" /> {t('pause')}</>
          ) : (
            <><Play className="w-3.5 h-3.5" /> {t('activate')}</>
          )}
        </button>
      </div>
    </div>
  )
}
