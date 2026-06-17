"use client"

import React, { useState } from "react"
import { MessageSquare, Shield, Scale, Zap, Mail, Phone, Users2, Check } from "lucide-react"
import { cn } from "@/lib/utils"
import { textStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import { Switch } from "@/components/ui/switch"
import { Chip } from "@/components/ui/chip"
import { AIConfigPreview } from "@/components/settings/AIConfigPreview"

// ── Tone Picker Card (Step 1) ────────────────────────────────────

const TONE_CARDS = [
  {
    value: "professional", label: "Formal", desc: "Corporativa e objetiva",
    color: { bg: "bg-cyan-50 dark:bg-cyan-950/20", text: "text-cyan-700 dark:text-cyan-400", glow: "shadow-cyan-200/50 dark:shadow-cyan-900/30" },
  },
  {
    value: "casual", label: "Descontraida", desc: "Leve e amigavel",
    color: { bg: "bg-amber-50 dark:bg-amber-950/20", text: "text-amber-700 dark:text-amber-400", glow: "shadow-amber-200/50 dark:shadow-amber-900/30" },
  },
  {
    value: "concise", label: "Direta", desc: "Breve, sem rodeios",
    color: { bg: "bg-emerald-50 dark:bg-emerald-950/20", text: "text-emerald-700 dark:text-emerald-400", glow: "shadow-emerald-200/50 dark:shadow-emerald-900/30" },
  },
  {
    value: "detailed", label: "Analitica", desc: "Completa com dados",
    color: { bg: "bg-violet-50 dark:bg-violet-950/20", text: "text-violet-700 dark:text-violet-400", glow: "shadow-violet-200/50 dark:shadow-violet-900/30" },
  },
]

interface TonePickerCardProps {
  currentTone?: string
  onSelect: (tone: string) => void
}

export function TonePickerCard({ currentTone = "professional", onSelect }: TonePickerCardProps) {
  const [selected, setSelected] = useState(currentTone)

  const handleSelect = (value: string) => {
    setSelected(value)
    onSelect(value)
  }

  return (
    <div className={cn(cardStyles.default, "p-4 space-y-3 max-w-sm")}>
      <p className={textStyles.label}>Como voce quer que eu me comunique?</p>

      <div className="grid grid-cols-2 gap-2">
        {TONE_CARDS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => handleSelect(opt.value)}
            className={cn(
              "group flex flex-col items-center gap-1 p-3 rounded-xl border text-center transition-colors duration-200",
              selected === opt.value
                ? cn("border-lia-btn-primary-bg", opt.color.bg, "shadow-lg", opt.color.glow)
                : "border-lia-border-subtle hover:border-lia-border-default"
            )}
          >
            <div className={cn("w-6 h-6 rounded-md flex items-center justify-center", opt.color.bg)}>
              <MessageSquare className={cn("w-3.5 h-3.5", opt.color.text)} aria-hidden="true" />
            </div>
            <span className={textStyles.labelSmall}>{opt.label}</span>
            <span className="text-[9px] text-lia-text-tertiary leading-tight">{opt.desc}</span>
          </button>
        ))}
      </div>

      <AIConfigPreview tone={selected} compact />
    </div>
  )
}

// ── Autonomy Picker Card (Step 2) ────────────────────────────────

const AUTONOMY_CARDS = [
  { value: "low", label: "Sempre perguntar", Icon: Shield, desc: "Pede aprovacao para tudo",
    color: { bg: "bg-cyan-50 dark:bg-cyan-950/20", text: "text-cyan-700 dark:text-cyan-400", glow: "shadow-cyan-200/50 dark:shadow-cyan-900/30" } },
  { value: "medium", label: "Equilibrado", Icon: Scale, desc: "Age no simples, pergunta no complexo",
    color: { bg: "bg-amber-50 dark:bg-amber-950/20", text: "text-amber-700 dark:text-amber-400", glow: "shadow-amber-200/50 dark:shadow-amber-900/30" } },
  { value: "high", label: "Autonoma", Icon: Zap, desc: "Age sozinha — ideal para volume",
    color: { bg: "bg-emerald-50 dark:bg-emerald-950/20", text: "text-emerald-700 dark:text-emerald-400", glow: "shadow-emerald-200/50 dark:shadow-emerald-900/30" } },
]

interface AutonomyPickerCardProps {
  currentLevel?: string
  onSelect: (level: string) => void
}

export function AutonomyPickerCard({ currentLevel = "low", onSelect }: AutonomyPickerCardProps) {
  const [selected, setSelected] = useState(currentLevel)

  const handleSelect = (value: string) => {
    setSelected(value)
    onSelect(value)
  }

  return (
    <div className={cn(cardStyles.default, "p-4 space-y-3 max-w-sm")}>
      <p className={textStyles.label}>Quanto posso agir sozinha?</p>

      <div className="space-y-2">
        {AUTONOMY_CARDS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => handleSelect(opt.value)}
            className={cn(
              "group w-full flex items-center gap-3 p-3 rounded-xl border text-left transition-colors duration-200",
              selected === opt.value
                ? cn("border-lia-btn-primary-bg", opt.color.bg, "shadow-lg", opt.color.glow)
                : "border-lia-border-subtle hover:border-lia-border-default"
            )}
          >
            <div className={cn("w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0", opt.color.bg)}>
              <opt.Icon className={cn("w-3.5 h-3.5", opt.color.text)} aria-hidden="true" />
            </div>
            <div className="flex-1 min-w-0">
              <span className={textStyles.labelSmall}>{opt.label}</span>
              <p className="text-[9px] text-lia-text-tertiary">{opt.desc}</p>
            </div>
            {selected === opt.value && (
              <Check className="w-4 h-4 text-status-success flex-shrink-0" aria-hidden="true" />
            )}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Channel Toggles Card (Step 3) ────────────────────────────────

const CHANNELS = [
  { key: "email" as const, label: "Email", Icon: Mail },
  { key: "whatsapp" as const, label: "WhatsApp", Icon: Phone },
  { key: "teams" as const, label: "Teams", Icon: Users2 },
]

interface ChannelTogglesCardProps {
  currentChannels?: { email: boolean; whatsapp: boolean; teams: boolean }
  onToggle: (channel: string, enabled: boolean) => void
}

export function ChannelTogglesCard({
  currentChannels = { email: true, whatsapp: false, teams: false },
  onToggle,
}: ChannelTogglesCardProps) {
  const [channels, setChannels] = useState(currentChannels)

  const handleToggle = (key: keyof typeof channels, value: boolean) => {
    setChannels((prev) => ({ ...prev, [key]: value }))
    onToggle(key, value)
  }

  return (
    <div className={cn(cardStyles.default, "p-4 space-y-3 max-w-sm")}>
      <p className={textStyles.label}>Por quais canais posso me comunicar?</p>

      <div className="space-y-2">
        {CHANNELS.map((ch) => (
          <div
            key={ch.key}
            className={cn(
              "flex items-center justify-between gap-3 p-3 rounded-lg transition-colors duration-200",
              channels[ch.key] ? "bg-lia-bg-secondary dark:bg-lia-bg-primary" : "bg-transparent"
            )}
          >
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-lia-bg-tertiary dark:bg-lia-bg-primary flex items-center justify-center">
                <ch.Icon className="w-3.5 h-3.5 text-lia-text-secondary" aria-hidden="true" />
              </div>
              <span className={textStyles.label}>{ch.label}</span>
            </div>
            <Switch
              checked={channels[ch.key]}
              onCheckedChange={(v) => handleToggle(ch.key, v)}
            />
          </div>
        ))}
      </div>

      <div className="flex gap-1.5 flex-wrap">
        {Object.entries(channels)
          .filter(([, v]) => v)
          .map(([k]) => (
            <Chip variant="neutral" muted key={k} className={badgeStyles.success}>
              {CHANNELS.find((c) => c.key === k)?.label}
            </Chip>
          ))}
      </div>
    </div>
  )
}
