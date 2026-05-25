"use client"

import React, { useState } from "react"
import { Globe, Mail, Phone, MessageCircle, Rocket, Check, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import type { PublishData } from "../wizard-types"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

const ALL_PLATFORMS = [
  { id: "linkedin", label: "LinkedIn" },
  { id: "indeed", label: "Indeed" },
  { id: "website", label: "Website" },
]

export function PublishPanel({ data, onUpdate }: Props) {
  const d = data as unknown as PublishData
  const [isPublishing, setIsPublishing] = useState(false)
  const selectedPlatforms = new Set(d.platforms || [])

  const togglePlatform = (platformId: string) => {
    const updated = new Set(selectedPlatforms)
    if (updated.has(platformId)) {
      updated.delete(platformId)
    } else {
      updated.add(platformId)
    }
    onUpdate?.({ platforms: Array.from(updated) })
  }

  const toggleAutoScreen = () => {
    onUpdate?.({ auto_screen: !d.auto_screen })
  }

  const handlePublish = () => {
    setIsPublishing(true)
    // Send publish command as chat message (backend processes it)
    window.dispatchEvent(new CustomEvent("lia:prefill-message", {
      detail: { message: "Publicar vaga agora" },
    }))
  }

  return (
    <div className="px-4 py-3 space-y-4">
      {/* Platform toggles */}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <Globe className="w-4 h-4 text-wedo-cyan" />
          <span className="text-xs font-medium text-lia-text-secondary">Plataformas</span>
        </div>
        <div className="space-y-1.5">
          {ALL_PLATFORMS.map((p) => {
            const selected = selectedPlatforms.has(p.id)
            return (
              <button
                key={p.id}
                onClick={() => togglePlatform(p.id)}
                className={cn(
                  "w-full flex items-center justify-between px-3 py-2 rounded-md border text-sm transition-colors",
                  selected
                    ? "border-wedo-cyan bg-wedo-cyan/5 text-wedo-cyan"
                    : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
                )}
              >
                <span>{p.label}</span>
                {selected && <Check className="w-4 h-4" />}
              </button>
            )
          })}
        </div>
      </div>

      {/* Sourcing mode */}
      {d.sourcing_mode && (
        <div className="flex items-center gap-2 text-xs">
          <Rocket className="w-3.5 h-3.5 text-wedo-cyan" />
          <span className="text-lia-text-secondary">Sourcing:</span>
          <span className="text-lia-text-primary font-medium capitalize">{d.sourcing_mode}</span>
        </div>
      )}

      {/* Contact channels */}
      {d.contact_channels?.length > 0 && (
        <div>
          <span className="text-xs font-medium text-lia-text-secondary">Canais de contato</span>
          <div className="flex items-center gap-2 mt-1">
            {d.contact_channels.map((c, i) => (
              <span key={i} className="px-2 py-0.5 rounded bg-lia-bg-secondary border border-lia-border-subtle text-micro text-lia-text-primary">
                {c}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Auto-screen toggle */}
      <button
        onClick={toggleAutoScreen}
        className="w-full flex items-center justify-between p-2.5 rounded-md bg-lia-bg-secondary border border-lia-border-subtle hover:bg-lia-interactive-hover transition-colors"
      >
        <span className="text-xs text-lia-text-primary">Auto-screening</span>
        <span className={cn(
          "text-xs font-medium",
          d.auto_screen ? "text-status-success" : "text-lia-text-tertiary"
        )}>
          {d.auto_screen ? "Ativo" : "Inativo"}
        </span>
      </button>

      {/* Share link */}
      {d.share_link && (
        <div className="p-2.5 rounded-md bg-wedo-cyan/5 border border-wedo-cyan/20">
          <p className="text-xs text-wedo-cyan font-medium mb-1">Link de compartilhamento</p>
          <p className="text-xs text-lia-text-primary break-all">{d.share_link}</p>
        </div>
      )}

      {/* Publish button */}
      {!d.job_id && (
        <>
          <button
            onClick={handlePublish}
            disabled={isPublishing || selectedPlatforms.size === 0}
            className={cn(
              "w-full flex items-center justify-center gap-2 px-4 py-3 rounded-md text-sm font-semibold transition-colors",
              isPublishing || selectedPlatforms.size === 0
                ? "bg-lia-bg-tertiary text-lia-text-disabled cursor-not-allowed"
                : "bg-wedo-cyan text-white hover:bg-wedo-cyan/90"
            )}
          >
            {isPublishing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Publicando...
              </>
            ) : (
              <>
                <Rocket className="w-4 h-4" />
                Publicar Vaga
              </>
            )}
          </button>
          {selectedPlatforms.size === 0 && (
            <p className="text-[10px] text-status-warning text-center">
              Selecione pelo menos uma plataforma
            </p>
          )}
        </>
      )}

      {/* Published success */}
      {d.job_id && (
        <div className="p-3 rounded-md bg-status-success/5 border border-status-success/20 text-center">
          <Check className="w-5 h-5 text-status-success mx-auto mb-1" />
          <p className="text-sm font-medium text-status-success">Vaga publicada!</p>
          <p className="text-xs text-lia-text-secondary mt-0.5">ID: {d.job_id}</p>
        </div>
      )}
    </div>
  )
}
