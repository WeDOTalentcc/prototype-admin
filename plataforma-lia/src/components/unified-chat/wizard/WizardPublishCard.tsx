import React, { useState } from "react"
import {
  ChevronDown,
  Rocket,
  Check,
  Loader2,
  Link as LinkIcon,
  Zap,
  ZapOff,
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import type { PublishData } from "./wizard-types"

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const PLATFORM_OPTIONS = [
  { value: "linkedin", label: "LinkedIn" },
  { value: "indeed", label: "Indeed" },
  { value: "website", label: "Site da empresa" },
] as const

/* ------------------------------------------------------------------ */
/*  Props                                                              */
/* ------------------------------------------------------------------ */

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

/**
 * WizardPublishCard — card inline no chat para o stage de publicação.
 *
 * Renderiza no chat em qualquer modo (sidebar, floating, fullscreen).
 * Permite selecionar plataformas, alternar auto-screening e disparar a
 * publicação diretamente no chat. Despacha CustomEvents para que o
 * orchestrator consuma as ações de forma homogênea.
 */
export function WizardPublishCard({ data, onUpdate }: Props) {
  const [expanded, setExpanded] = useState(true)
  const [publishing, setPublishing] = useState(false)

  const d = data as unknown as PublishData
  const platforms = d.platforms ?? []
  const sourcingMode = d.sourcing_mode ?? null
  const contactChannels = d.contact_channels ?? []
  const shareLink = d.share_link ?? null
  const autoScreen = d.auto_screen ?? false
  const jobId = d.job_id ?? null
  const isPublished = jobId !== null

  /* ---- handlers -------------------------------------------------- */

  const togglePlatform = (platform: string) => {
    const current = new Set(platforms)
    if (current.has(platform)) {
      current.delete(platform)
    } else {
      current.add(platform)
    }
    onUpdate?.({ platforms: Array.from(current) })
  }

  const toggleAutoScreen = () => {
    onUpdate?.({ auto_screen: !autoScreen })
  }

  const handlePublish = () => {
    if (platforms.length === 0 || publishing) return
    setPublishing(true)
    window.dispatchEvent(
      new CustomEvent("lia:prefill-message", {
        detail: { text: "Publicar vaga agora" },
      }),
    )
  }

  /* ---- render ---------------------------------------------------- */

  return (
    <div
      role="region"
      aria-label="Publicação da vaga"
      className="mt-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary overflow-hidden"
    >
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-lia-interactive-hover transition-colors text-left"
      >
        <Rocket
          className="w-4 h-4 text-wedo-cyan flex-shrink-0"
          aria-hidden="true"
        />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-lia-text-primary">
            Publicação da vaga
          </p>
        </div>

        {isPublished && (
          <span className="inline-flex items-center gap-1 rounded-full bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-600">
            <Check className="w-3 h-3" aria-hidden="true" />
            Publicada
          </span>
        )}

        <ChevronDown
          className={cn(
            "w-4 h-4 text-lia-text-secondary transition-transform duration-200",
            expanded && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>

      {/* Body */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="publish-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 space-y-3">
              {/* ---- Platform toggles ---- */}
              <div className="space-y-1.5">
                <p className="text-xs font-medium text-lia-text-secondary">
                  Plataformas
                </p>
                <div className="space-y-1">
                  {PLATFORM_OPTIONS.map(({ value, label }) => {
                    const selected = platforms.includes(value)
                    return (
                      <button
                        key={value}
                        type="button"
                        onClick={() => togglePlatform(value)}
                        className={cn(
                          "w-full flex items-center justify-between rounded-lg border px-3 py-2 text-sm transition-colors",
                          selected
                            ? "border-wedo-cyan bg-wedo-cyan/5 text-wedo-cyan-text"
                            : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary",
                        )}
                      >
                        <span>{label}</span>
                        {selected && (
                          <Check
                            className="w-4 h-4 text-wedo-cyan"
                            aria-hidden="true"
                          />
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* ---- Sourcing mode ---- */}
              {sourcingMode && (
                <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
                  <Rocket className="w-3.5 h-3.5" aria-hidden="true" />
                  <span>
                    Sourcing:{" "}
                    <span className="font-medium text-lia-text-primary">
                      {sourcingMode}
                    </span>
                  </span>
                </div>
              )}

              {/* ---- Contact channels ---- */}
              {contactChannels.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {contactChannels.map((ch) => (
                    <span
                      key={ch}
                      className="inline-flex items-center rounded-full bg-lia-bg-tertiary px-2 py-0.5 text-xs text-lia-text-secondary"
                    >
                      {ch}
                    </span>
                  ))}
                </div>
              )}

              {/* ---- Auto-screening toggle ---- */}
              <div className="flex items-center justify-between">
                <span className="text-xs text-lia-text-secondary">
                  Triagem automática
                </span>
                <button
                  type="button"
                  onClick={toggleAutoScreen}
                  className={cn(
                    "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium transition-colors",
                    autoScreen
                      ? "bg-green-500/10 text-green-600"
                      : "bg-lia-bg-tertiary text-lia-text-secondary",
                  )}
                >
                  {autoScreen ? (
                    <>
                      <Zap className="w-3 h-3" aria-hidden="true" />
                      Ativo
                    </>
                  ) : (
                    <>
                      <ZapOff className="w-3 h-3" aria-hidden="true" />
                      Inativo
                    </>
                  )}
                </button>
              </div>

              {/* ---- Share link ---- */}
              {shareLink && (
                <div className="flex items-center gap-2 rounded-lg bg-wedo-cyan/5 px-3 py-2">
                  <LinkIcon
                    className="w-3.5 h-3.5 text-wedo-cyan flex-shrink-0"
                    aria-hidden="true"
                  />
                  <span className="text-xs text-wedo-cyan-text truncate">
                    {shareLink}
                  </span>
                </div>
              )}

              {/* ---- Publish button (pre-publish) ---- */}
              {!isPublished && (
                <div className="space-y-1.5">
                  <button
                    type="button"
                    onClick={handlePublish}
                    disabled={platforms.length === 0 || publishing}
                    className={cn(
                      "w-full rounded-lg py-2 text-sm font-medium transition-colors",
                      platforms.length > 0 && !publishing
                        ? "bg-wedo-cyan text-white hover:bg-wedo-cyan/90"
                        : "bg-lia-bg-tertiary text-lia-text-secondary cursor-not-allowed",
                    )}
                  >
                    {publishing ? (
                      <span className="inline-flex items-center gap-2">
                        <Loader2
                          className="w-4 h-4 animate-spin"
                          aria-hidden="true"
                        />
                        Publicando...
                      </span>
                    ) : (
                      "Publicar vaga"
                    )}
                  </button>
                  {platforms.length === 0 && (
                    <p className="text-xs text-amber-500 text-center">
                      Selecione pelo menos uma plataforma
                    </p>
                  )}
                </div>
              )}

              {/* ---- Published success state ---- */}
              {isPublished && (
                <div className="flex items-center gap-2 rounded-lg bg-green-500/10 px-3 py-2.5">
                  <Check
                    className="w-4 h-4 text-green-600 flex-shrink-0"
                    aria-hidden="true"
                  />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-green-600">
                      Vaga publicada!
                    </p>
                    <p className="text-xs text-green-600/80">
                      ID: {String(jobId)}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
