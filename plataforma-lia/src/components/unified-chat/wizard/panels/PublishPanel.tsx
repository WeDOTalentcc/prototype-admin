"use client"

import React from "react"
import { Globe, Mail, Phone, MessageCircle, Rocket } from "lucide-react"
import { cn } from "@/lib/utils"
import type { PublishData } from "../wizard-types"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

const PLATFORM_ICONS: Record<string, string> = {
  linkedin: "LinkedIn",
  indeed: "Indeed",
  website: "Website",
}

export function PublishPanel({ data }: Props) {
  const d = data as unknown as PublishData

  return (
    <div className="px-4 py-3 space-y-4">
      {/* Platforms */}
      <div>
        <div className="flex items-center gap-1.5 mb-1.5">
          <Globe className="w-4 h-4 text-wedo-cyan" />
          <span className="text-xs font-medium text-lia-text-secondary font-['Open_Sans',sans-serif]">Plataformas</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {(d.platforms || []).map((p, i) => (
            <span key={i} className="px-2 py-0.5 rounded bg-wedo-cyan/10 text-wedo-cyan text-xs font-medium font-['Open_Sans',sans-serif]">
              {PLATFORM_ICONS[p] || p}
            </span>
          ))}
          {(!d.platforms || d.platforms.length === 0) && (
            <span className="text-xs text-lia-text-tertiary font-['Open_Sans',sans-serif]">Nenhuma selecionada</span>
          )}
        </div>
      </div>

      {/* Sourcing mode */}
      {d.sourcing_mode && (
        <div className="flex items-center gap-2 text-xs font-['Open_Sans',sans-serif]">
          <Rocket className="w-3.5 h-3.5 text-wedo-cyan" />
          <span className="text-lia-text-secondary">Sourcing:</span>
          <span className="text-lia-text-primary font-medium capitalize">{d.sourcing_mode}</span>
        </div>
      )}

      {/* Contact channels */}
      {d.contact_channels?.length > 0 && (
        <div>
          <span className="text-xs font-medium text-lia-text-secondary font-['Open_Sans',sans-serif]">Canais de contato</span>
          <div className="flex items-center gap-2 mt-1">
            {d.contact_channels.map((c, i) => (
              <span key={i} className="px-2 py-0.5 rounded bg-lia-bg-secondary border border-lia-border-subtle text-xs text-lia-text-primary font-['Open_Sans',sans-serif]">
                {c}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Auto-screen toggle */}
      <div className="flex items-center justify-between p-2.5 rounded-md bg-lia-bg-secondary border border-lia-border-subtle">
        <span className="text-xs text-lia-text-primary font-['Open_Sans',sans-serif]">Auto-screening</span>
        <span className={cn(
          "text-xs font-medium font-['Open_Sans',sans-serif]",
          d.auto_screen ? "text-status-success" : "text-lia-text-tertiary"
        )}>
          {d.auto_screen ? "Ativo" : "Inativo"}
        </span>
      </div>

      {/* Share link */}
      {d.share_link && (
        <div className="p-2.5 rounded-md bg-wedo-cyan/5 border border-wedo-cyan/20">
          <p className="text-xs text-wedo-cyan font-medium font-['Open_Sans',sans-serif] mb-1">Link de compartilhamento</p>
          <p className="text-xs text-lia-text-primary font-['Open_Sans',sans-serif] break-all">{d.share_link}</p>
        </div>
      )}
    </div>
  )
}
