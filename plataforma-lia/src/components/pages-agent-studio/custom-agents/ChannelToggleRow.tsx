"use client"

import React from "react"
import { Switch } from "@/components/ui/switch"

/**
 * W-Channels-A (2026-05-23) — reusable channel row renderer.
 *
 * Extraido de AgentCard.tsx (refactor 2026-06-09) para ser reusavel por
 * outras surfaces (ex: card do agente + futuras). Comportamento identico.
 *
 * Cada um dos 4 canais (whatsapp / voice / voip / triagem_invite) e renderizado
 * por este componente para garantir consistencia visual + ARIA. Os toggles
 * sao INDEPENDENTES — nao ha regra de exclusao mutua, cliente combina como
 * preferir (mental model Paulo, decisao Opcao B 2026-05-23).
 */
export interface ChannelToggleRowProps {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>
  label: string
  enabled: boolean
  disabled: boolean
  onToggle: (next: boolean) => void
  ariaOn: string
  ariaOff: string
  testId: string
  trailing?: React.ReactNode
}

export function ChannelToggleRow({
  icon: Icon,
  label,
  enabled,
  disabled,
  onToggle,
  ariaOn,
  ariaOff,
  testId,
  trailing,
}: ChannelToggleRowProps) {
  return (
    <div className="flex items-center justify-between gap-2 pt-2 border-t border-lia-border-subtle">
      <div className="flex items-center gap-2 text-xs">
        <Icon className="w-3.5 h-3.5 text-lia-text-muted" aria-hidden="true" />
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
