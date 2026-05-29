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
  MessageCircle,
  Mic,
  Send,
} from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { badgeStyles, textStyles } from "@/lib/design-tokens"
// Sprint B QW#15 audit 2026-05-22: 3-dot menu para Clone (era enterrado em drawer)
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { getCustomAgentStatusConfig } from "@/lib/agent-studio/status-config"
import { BetaBadge } from "@/components/ui/beta-badge"
// Onda 4 F6.4 — badge "agente novo aprendendo" quando < 5 execuções.
import { LearningBadge } from "@/components/pages-agent-studio/LearningBadge"
import { Switch } from "@/components/ui/switch"
import { useToggleAgentVoice } from "@/hooks/agent-studio/use-agent-voice"
import { useToggleAgentWhatsApp } from "@/hooks/agent-studio/use-agent-whatsapp"
import { useToggleAgentChannel } from "@/hooks/agent-studio/use-agent-channel"
import { StudioCardShell } from "@/components/pages-agent-studio/StudioCardShell"
// White-label canonical (CLAUDE.md project_white_label_ai_assistant 2026-05-25):
// agent.name é o nome custom do agente; aiPersona.name é o nome do assistente IA
// configurado pelo cliente (default "LIA"). Fallback: agent.name → persona → genérico.
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import type { CustomAgent } from "./types"
import { safeCategoryKey } from "./types"

interface AgentCardProps {
  agent: CustomAgent
  onTest: (agent: CustomAgent) => void
  onDeploy: (agent: CustomAgent) => void
  onToggleStatus: (agent: CustomAgent) => void
  /** Sprint B QW#15 audit 2026-05-22: Clone handler — opcional (caller decide se expoe) */
  onClone?: (agent: CustomAgent) => void
}

/**
 * W-Channels-A (2026-05-23) — channel row renderer.
 *
 * Cada um dos 4 canais (whatsapp / voice / voip / triagem_invite) e renderizado
 * por este sub-componente para garantir consistencia visual + ARIA. Os toggles
 * sao INDEPENDENTES — nao ha regra de exclusao mutua, cliente combina como
 * preferir (mental model Paulo, decisao Opcao B 2026-05-23).
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

/**
 * Sprint visual canonical 2026-05-26 (Agent C) — AgentCard refactor.
 *
 * Consome `<StudioCardShell tone="elevated">` canonical (Sprint visual 14855a181 +
 * v2 07272378e). Adapter pattern reusado do AgentPanel — header/metrics/body/actions
 * agora compoem via slots do shell ao inves de markup ad-hoc.
 *
 * PRESERVA 100% das features pre-refactor:
 *  - 4 ChannelToggleRow (voice/voip/whatsapp/triagem_invite) com testids intactos
 *  - DropdownMenu Clone (3-dot menu) via shell `badges` slot
 *  - BetaBadge ao lado do Clone menu
 *  - Status badge + metricas + descricao
 *  - 3 channel-specific tests existing (voice/whatsapp/triagemInvite) PASS
 */
export function AgentCard({ agent, onTest, onDeploy, onToggleStatus, onClone }: AgentCardProps) {
  const t = useTranslations("agents.card")
  // White-label canonical 2026-05-29: persona do cliente como fallback do nome.
  // Se agent.name estiver vazio (edge case durante criação/erro), exibe o nome
  // do assistente IA configurado em Configurações (default "LIA").
  const { persona: aiPersona } = useAiPersona()
  const displayName = agent.name || aiPersona?.name || "Agente"
  // W-Channels-A revisao (2026-05-23): 4 canais canonical independentes
  // (whatsapp / voice / voip / triagem_invite). in_app revertido — gap conceitual;
  // chat candidato publico vive em /api/v1/triagem/. voice = PSTN, voip = browser/Gemini Live.
  const toggleWhatsApp = useToggleAgentWhatsApp(agent.id)
  const toggleVoice = useToggleAgentVoice(agent.id)
  const toggleVoip = useToggleAgentChannel(agent.id, "voip")
  // Workstream A 2026-05-23: 4o toggle — capability "convite triagem".
  const toggleTriagemInvite = useToggleAgentChannel(agent.id, "triagem_invite")

  // Backward compat: voip=false; voice=false; whatsapp=false; triagem_invite=false.
  const whatsappEnabled = Boolean(agent.whatsapp_enabled)
  const voiceEnabled = Boolean(agent.voice_enabled)
  const voipEnabled = Boolean(agent.voip_enabled)
  const triagemInviteEnabled = Boolean(agent.triagem_invite_enabled)

  const tStatus = useTranslations("agents.status")
  const tCat = useTranslations("agents.customAgents")

  // UX-Sprint-A QW#18 Batch 3 (audit 2026-05-21): STATUS_STYLES extraido para
  // lib/agent-studio/status-config.ts canonical. Label fica local (i18n tStatus).
  const statusConfig = getCustomAgentStatusConfig(agent.status)
  const statusStyle = {
    label: tStatus(agent.status as "draft" | "active" | "paused" | "archived") || tStatus("draft"),
    badge: statusConfig.badge,
  }
  const category = safeCategoryKey(agent.domain)
  const categoryLabel = tCat("categories." + category) || agent.domain || "general"

  // Shell slots — adapter pattern (mirrors AgentPanel).
  const statusBadge = (
    <>
      <span className={cn(badgeStyles.default, "text-[10px]")}>{categoryLabel}</span>
      <span className={cn(statusStyle.badge, "text-[10px]")}>{statusStyle.label}</span>
    </>
  )

  const badges = (
    <>
      {onClone && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="p-1 rounded-md text-lia-text-disabled hover:text-lia-text-primary hover:bg-lia-bg-tertiary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30"
              aria-label={t("moreActions") || "Mais acoes"}
            >
              <MoreVertical className="w-4 h-4" aria-hidden="true" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            <DropdownMenuItem onClick={() => onClone(agent)} className="gap-2 cursor-pointer">
              <Copy className="w-3.5 h-3.5" aria-hidden="true" />
              {t("clone") || "Duplicar"}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
      <BetaBadge size="sm" />
      {/* Onda 4 F6.4 — < 5 execuções = is_learning */}
      {agent.total_executions < 5 && <LearningBadge />}
    </>
  )

  const metricsSlot = (
    <div className="flex items-center gap-4 text-xs">
      <div>
        <span className="font-bold text-lia-text-primary font-sans">{agent.total_executions}</span>
        <span className="text-lia-text-disabled ml-1">{t("executions")}</span>
      </div>
      {agent.avg_confidence > 0 && (
        <div>
          <span className="font-bold text-lia-text-primary font-sans">
            {(agent.avg_confidence * 100).toFixed(0)}%
          </span>
          <span className="text-lia-text-disabled ml-1">{t("confidence")}</span>
        </div>
      )}
    </div>
  )

  const bodySlot = (
    <>
      {agent.description && (
        <p className={cn(textStyles.caption, "text-xs line-clamp-2 mb-3")}>{agent.description}</p>
      )}

      {/* W-Channels-A revisao 2026-05-23: 4 canais canonical */}
      {/* 1. WhatsApp */}
      <ChannelToggleRow
        icon={MessageCircle}
        label={t("whatsapp") || "WhatsApp"}
        enabled={whatsappEnabled}
        disabled={toggleWhatsApp.isMutating}
        onToggle={(next) => toggleWhatsApp.trigger(next)}
        ariaOn={t("enableWhatsapp", { name: displayName }) || `Habilitar WhatsApp no agente ${displayName}`}
        ariaOff={t("disableWhatsapp", { name: displayName }) || `Desabilitar WhatsApp no agente ${displayName}`}
        testId="agent-card-whatsapp-toggle"
      />

      {/* 2. Voz PSTN (ligacao telefonica) — trailing = botao Iniciar chamada */}
      <ChannelToggleRow
        icon={Phone}
        label={t("voice") || "Ligacao telefonica"}
        enabled={voiceEnabled}
        disabled={toggleVoice.isMutating}
        onToggle={(next) => toggleVoice.trigger(next)}
        ariaOn={t("enableVoice", { name: displayName }) || `Habilitar voz no agente ${displayName}`}
        ariaOff={t("disableVoice", { name: displayName }) || `Desabilitar voz no agente ${displayName}`}
        testId="agent-card-voice-toggle"
        /* Wave A P0 #6 (2026-05-27): trailing "Iniciar chamada" removido — pertencia a surface
           com contexto de candidato (kanban/perfil), aqui disparava candidate_id="" anti-pattern.
           Toggle de canal mantido pra config global do agente. */
      />

      {/* 3. Voz no navegador (VoIP) */}
      <ChannelToggleRow
        icon={Mic}
        label={t("voip") || "Voz no navegador (VoIP)"}
        enabled={voipEnabled}
        disabled={toggleVoip.isMutating}
        onToggle={(next) => toggleVoip.trigger(next)}
        ariaOn={t("enableVoip", { name: displayName }) || `Habilitar voz no navegador (VoIP) no agente ${displayName}`}
        ariaOff={t("disableVoip", { name: displayName }) || `Desabilitar voz no navegador (VoIP) no agente ${displayName}`}
        testId="agent-card-voip-toggle"
      />

      {/* 4. Convite triagem — Workstream A 2026-05-23 */}
      <ChannelToggleRow
        icon={Send}
        label={t("triagemInvite") || "Convite triagem"}
        enabled={triagemInviteEnabled}
        disabled={toggleTriagemInvite.isMutating}
        onToggle={(next) => toggleTriagemInvite.trigger(next)}
        ariaOn={t("enableTriagemInvite", { name: displayName }) || `Habilitar criacao de convites de triagem no agente ${displayName}`}
        ariaOff={t("disableTriagemInvite", { name: displayName }) || `Desabilitar criacao de convites de triagem no agente ${displayName}`}
        testId="agent-card-triagem-invite-toggle"
        /* Wave A P0 #7 (2026-05-27): trailing "Enviar convite" removido — pertencia a surface
           com contexto de candidato+vaga (kanban), aqui disparava candidate_id="" + job_id="" anti-pattern.
           Toggle de capability mantido pra config global do agente. */
      />
    </>
  )

  const actionsSlot = (
    <>
      <button
        type="button"
        onClick={() => onTest(agent)}
        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors"
      >
        <TestTube2 className="w-3.5 h-3.5" /> {t("test")}
      </button>
      <button
        type="button"
        onClick={() => onDeploy(agent)}
        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-graphite hover:bg-powder transition-colors"
      >
        <Link2 className="w-3.5 h-3.5" /> {t("link")}
      </button>
      <button
        type="button"
        onClick={() => onToggleStatus(agent)}
        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors ml-auto"
      >
        {agent.status === "active" ? (
          <><Pause className="w-3.5 h-3.5" /> {t("pause")}</>
        ) : (
          <><Play className="w-3.5 h-3.5" /> {t("activate")}</>
        )}
      </button>
    </>
  )

  return (
    <StudioCardShell
      tone="elevated"
      icon={<Bot className="w-4 h-4 text-graphite" />}
      title={displayName}
      statusBadge={statusBadge}
      badges={badges}
      metricsSlot={metricsSlot}
      bodySlot={bodySlot}
      actionsSlot={actionsSlot}
      data-testid={`agent-card-${agent.id}`}
    />
  )
}
