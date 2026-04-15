"use client"

import React, { useEffect, useState, useCallback } from "react"
import {
  Brain, MessageSquare, BarChart3, Zap, Shield, ChevronDown,
  Loader2, Check, Info, Mail, Phone, Users2, Scale,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { textStyles, cardStyles, badgeStyles, buttonStyles } from "@/lib/design-tokens"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { AIConfigPreview } from "./AIConfigPreview"

// ── Types ────────────────────────────────────────────────────────

interface AIConfig {
  persona: { tone: string; custom_name: string | null; detail_level: string }
  scoring: { technical_weight: number; behavioral_weight: number }
  channels: { email: boolean; whatsapp: boolean; teams: boolean }
  automation: {
    auto_screening: boolean
    auto_scheduling: boolean
    auto_stage_advance: boolean
    autonomy_level: string
  }
  compliance: {
    fairness_level: string
    data_retention_days: number
    salary_filter_enabled: boolean
    salary_tolerance_percent: number
  }
  setup_progress: number
}

// ── Constants ────────────────────────────────────────────────────

const TONE_OPTIONS = [
  {
    value: "professional",
    label: "Formal",
    desc: "Comunicacao corporativa e objetiva",
    icon: "briefcase",
    color: { bg: "bg-cyan-50 dark:bg-cyan-950/20", text: "text-cyan-700 dark:text-cyan-400", glow: "shadow-cyan-200/50 dark:shadow-cyan-900/30" },
  },
  {
    value: "casual",
    label: "Descontraida",
    desc: "Tom leve, como conversa entre colegas",
    icon: "smile",
    color: { bg: "bg-amber-50 dark:bg-amber-950/20", text: "text-amber-700 dark:text-amber-400", glow: "shadow-amber-200/50 dark:shadow-amber-900/30" },
  },
  {
    value: "concise",
    label: "Direta",
    desc: "Respostas breves, sem rodeios",
    icon: "zap",
    color: { bg: "bg-emerald-50 dark:bg-emerald-950/20", text: "text-emerald-700 dark:text-emerald-400", glow: "shadow-emerald-200/50 dark:shadow-emerald-900/30" },
  },
  {
    value: "detailed",
    label: "Analitica",
    desc: "Analises completas com dados e contexto",
    icon: "bar-chart",
    color: { bg: "bg-violet-50 dark:bg-violet-950/20", text: "text-violet-700 dark:text-violet-400", glow: "shadow-violet-200/50 dark:shadow-violet-900/30" },
  },
]

const AUTONOMY_OPTIONS = [
  {
    value: "low",
    label: "Sempre perguntar",
    desc: "A IA pede aprovacao para todas as acoes",
    Icon: Shield,
    color: { bg: "bg-cyan-50 dark:bg-cyan-950/20", text: "text-cyan-700 dark:text-cyan-400", glow: "shadow-cyan-200/50 dark:shadow-cyan-900/30" },
  },
  {
    value: "medium",
    label: "Equilibrado",
    desc: "Age sozinha no simples, pede ajuda no complexo",
    Icon: Scale,
    color: { bg: "bg-amber-50 dark:bg-amber-950/20", text: "text-amber-700 dark:text-amber-400", glow: "shadow-amber-200/50 dark:shadow-amber-900/30" },
  },
  {
    value: "high",
    label: "Autonoma",
    desc: "Age sozinha e avisa depois — ideal para alto volume",
    Icon: Zap,
    color: { bg: "bg-emerald-50 dark:bg-emerald-950/20", text: "text-emerald-700 dark:text-emerald-400", glow: "shadow-emerald-200/50 dark:shadow-emerald-900/30" },
  },
]

const CHANNEL_OPTIONS = [
  { key: "email" as const, label: "Email", desc: "Convites, feedback e acompanhamento", Icon: Mail },
  { key: "whatsapp" as const, label: "WhatsApp", desc: "Triagem e comunicacao rapida", Icon: Phone },
  { key: "teams" as const, label: "Microsoft Teams", desc: "Integrar com o Teams da empresa", Icon: Users2 },
]

// ── Subcomponents ────────────────────────────────────────────────

function SaveIndicator({ saving, saved }: { saving: boolean; saved: boolean }) {
  if (saving) return <Loader2 className="w-4 h-4 animate-spin text-lia-text-tertiary" />
  if (saved) {
    return (
      <span className={cn(badgeStyles.success, "gap-1")}>
        <Check className="w-3 h-3" /> Salvo
      </span>
    )
  }
  return null
}

function SectionHeader({
  Icon,
  title,
  description,
}: {
  Icon: React.ElementType
  title: string
  description: string
}) {
  return (
    <div className="mb-4">
      <h3 className={cn(textStyles.h3, "flex items-center gap-2")}>
        <Icon className="w-4 h-4 text-wedo-cyan" aria-hidden="true" />
        {title}
      </h3>
      <p className={cn(textStyles.description, "mt-0.5")}>{description}</p>
    </div>
  )
}

function ToggleRow({
  label,
  hint,
  checked,
  onCheckedChange,
}: {
  label: string
  hint: string
  checked: boolean
  onCheckedChange: (v: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-2">
      <div className="flex-1 min-w-0">
        <Label className={textStyles.label}>{label}</Label>
        <p className={cn(textStyles.caption, "mt-0.5")}>{hint}</p>
      </div>
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
    </div>
  )
}

// ── Main Component ───────────────────────────────────────────────

export function AIConfigPanel({ className }: { className?: string }) {
  const [config, setConfig] = useState<AIConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [advancedOpen, setAdvancedOpen] = useState(false)

  const fetchConfig = useCallback(async () => {
    try {
      const res = await fetch("/api/backend-proxy/ai-config")
      if (res.ok) setConfig(await res.json())
    } catch {
      /* silent */
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchConfig()
  }, [fetchConfig])

  const save = async (partial: Partial<AIConfig>) => {
    setSaving(true)
    setSaved(false)
    try {
      const res = await fetch("/api/backend-proxy/ai-config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(partial),
      })
      if (res.ok) {
        setConfig(await res.json())
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
      }
    } catch {
      /* silent */
    } finally {
      setSaving(false)
    }
  }

  if (loading || !config) {
    return (
      <div className={cn("flex items-center justify-center py-16", className)}>
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-wedo-cyan/10 flex items-center justify-center">
            <Brain className="w-5 h-5 text-wedo-cyan animate-pulse" aria-hidden="true" />
          </div>
          <p className={textStyles.description}>Carregando configuracoes...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* ── Hero Header with gradient ─────────────────────────── */}
      <section className="relative overflow-hidden rounded-xl border border-lia-border-subtle bg-gradient-to-br from-lia-bg-secondary to-lia-bg-primary dark:from-lia-bg-primary dark:to-lia-bg-secondary p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-wedo-cyan/10 dark:bg-wedo-cyan/20 flex items-center justify-center shadow-lg shadow-cyan-200/50 dark:shadow-cyan-900/30">
              <Brain className="w-5 h-5 text-wedo-cyan" aria-hidden="true" />
            </div>
            <div>
              <h2 className={textStyles.h2}>Personalidade da sua IA</h2>
              <p className={cn(textStyles.description, "mt-0.5")}>
                Configure como a LIA se comporta para sua empresa
              </p>
            </div>
          </div>
          <SaveIndicator saving={saving} saved={saved} />
        </div>
      </section>

      {/* ── 1. Tone Selection with Preview ────────────────────── */}
      <Card className={cardStyles.default}>
        <CardContent className="p-5">
          <SectionHeader
            Icon={MessageSquare}
            title="Como a IA conversa"
            description="Escolha o tom e veja um exemplo de resposta"
          />

          <div className="grid grid-cols-2 gap-2.5">
            {TONE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => save({ persona: { ...config.persona, tone: opt.value } })}
                className={cn(
                  "group relative flex flex-col items-center gap-1.5 p-4 rounded-xl border text-center transition-colors duration-200",
                  config.persona.tone === opt.value
                    ? cn("border-lia-btn-primary-bg", opt.color.bg, "shadow-lg", opt.color.glow)
                    : "border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-subtle"
                )}
              >
                <div
                  className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center transition-transform duration-200 group-hover:scale-110",
                    opt.color.bg
                  )}
                >
                  <MessageSquare className={cn("w-4 h-4", opt.color.text)} aria-hidden="true" />
                </div>
                <span className={textStyles.label}>{opt.label}</span>
                <span className={cn(textStyles.caption, "leading-tight")}>{opt.desc}</span>
              </button>
            ))}
          </div>

          {/* Live preview */}
          <div className="mt-4 pt-4 border-t border-lia-border-subtle">
            <AIConfigPreview tone={config.persona.tone} />
          </div>
        </CardContent>
      </Card>

      {/* ── 2. Autonomy Level ─────────────────────────────────── */}
      <Card className={cardStyles.default}>
        <CardContent className="p-5">
          <SectionHeader
            Icon={Zap}
            title="Nivel de autonomia"
            description="Quanto a IA pode agir sozinha sem pedir permissao"
          />

          <div className="grid grid-cols-3 gap-2.5">
            {AUTONOMY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() =>
                  save({ automation: { ...config.automation, autonomy_level: opt.value } })
                }
                className={cn(
                  "group relative flex flex-col items-center gap-1.5 p-4 rounded-xl border text-center transition-colors duration-200",
                  config.automation.autonomy_level === opt.value
                    ? cn("border-lia-btn-primary-bg", opt.color.bg, "shadow-lg", opt.color.glow)
                    : "border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-subtle"
                )}
              >
                <div
                  className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center transition-transform duration-200 group-hover:scale-110",
                    opt.color.bg
                  )}
                >
                  <opt.Icon className={cn("w-4 h-4", opt.color.text)} aria-hidden="true" />
                </div>
                <span className={textStyles.label}>{opt.label}</span>
                <span className={cn(textStyles.caption, "leading-tight")}>{opt.desc}</span>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ── 3. Communication Channels ─────────────────────────── */}
      <Card className={cardStyles.default}>
        <CardContent className="p-5">
          <SectionHeader
            Icon={MessageSquare}
            title="Canais de comunicacao"
            description="Por onde a IA pode se comunicar com candidatos"
          />

          <div className="space-y-1">
            {CHANNEL_OPTIONS.map((ch) => (
              <div
                key={ch.key}
                className={cn(
                  "flex items-center justify-between gap-4 p-3 rounded-lg transition-colors duration-200",
                  config.channels[ch.key]
                    ? "bg-lia-bg-secondary dark:bg-lia-bg-primary"
                    : "bg-transparent"
                )}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-lia-bg-tertiary dark:bg-lia-bg-primary flex items-center justify-center">
                    <ch.Icon className="w-4 h-4 text-lia-text-secondary" aria-hidden="true" />
                  </div>
                  <div>
                    <span className={textStyles.label}>{ch.label}</span>
                    <p className={textStyles.caption}>{ch.desc}</p>
                  </div>
                </div>
                <Switch
                  checked={config.channels[ch.key]}
                  onCheckedChange={(v) => save({ channels: { ...config.channels, [ch.key]: v } })}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ── 4. Advanced Settings (Progressive Disclosure) ─────── */}
      <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" className="w-full justify-between text-xs text-lia-text-secondary">
            Configuracoes avancadas
            <ChevronDown
              className={cn(
                "w-4 h-4 transition-transform duration-200",
                advancedOpen && "rotate-180"
              )}
            />
          </Button>
        </CollapsibleTrigger>

        <CollapsibleContent className="space-y-4 pt-2">
          {/* Scoring */}
          <Card className={cardStyles.default}>
            <CardContent className="p-5">
              <SectionHeader
                Icon={BarChart3}
                title="Como a IA avalia candidatos"
                description="Peso entre competencias tecnicas e comportamentais"
              />

              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className={textStyles.metricSmall}>
                    Tecnico: {Math.round(config.scoring.technical_weight * 100)}%
                  </span>
                  <span className={textStyles.metricSmall}>
                    Comportamental: {Math.round(config.scoring.behavioral_weight * 100)}%
                  </span>
                </div>

                <div className="relative">
                  <Progress
                    value={config.scoring.technical_weight * 100}
                    className="h-2.5"
                  />
                  <input
                    type="range"
                    min={30}
                    max={90}
                    value={config.scoring.technical_weight * 100}
                    onChange={(e) => {
                      const tech = Number(e.target.value) / 100
                      save({
                        scoring: {
                          technical_weight: Math.round(tech * 100) / 100,
                          behavioral_weight: Math.round((1 - tech) * 100) / 100,
                        },
                      })
                    }}
                    className="absolute inset-0 w-full opacity-0 cursor-pointer"
                  />
                </div>

                <div className="flex items-center gap-1.5">
                  <Info className="w-3 h-3 text-lia-text-tertiary" aria-hidden="true" />
                  <span className={textStyles.caption}>
                    85% das empresas do seu setor usam peso 70/30
                  </span>
                  {Math.round(config.scoring.technical_weight * 100) === 70 && (
                    <Badge className={badgeStyles.success}>No padrao</Badge>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Compliance */}
          <Card className={cardStyles.default}>
            <CardContent className="p-5">
              <SectionHeader
                Icon={Shield}
                title="Compliance e privacidade"
                description="Regras de fairness e filtros de seguranca"
              />

              <div className="space-y-1">
                <ToggleRow
                  label="Filtro de expectativa salarial"
                  hint="Exclui candidatos fora da faixa salarial da vaga"
                  checked={config.compliance.salary_filter_enabled}
                  onCheckedChange={(v) =>
                    save({ compliance: { ...config.compliance, salary_filter_enabled: v } })
                  }
                />
              </div>
            </CardContent>
          </Card>

          {/* Automations */}
          <Card className={cardStyles.default}>
            <CardContent className="p-5">
              <SectionHeader
                Icon={Zap}
                title="Automacoes"
                description="Quais tarefas a IA faz automaticamente"
              />

              <div className="space-y-1">
                <ToggleRow
                  label="Triagem automatica"
                  hint="A IA avalia CVs automaticamente quando candidato se aplica"
                  checked={config.automation.auto_screening}
                  onCheckedChange={(v) =>
                    save({ automation: { ...config.automation, auto_screening: v } })
                  }
                />
                <ToggleRow
                  label="Agendamento automatico"
                  hint="A IA agenda entrevistas sem pedir aprovacao"
                  checked={config.automation.auto_scheduling}
                  onCheckedChange={(v) =>
                    save({ automation: { ...config.automation, auto_scheduling: v } })
                  }
                />
                <ToggleRow
                  label="Avancar candidato automaticamente"
                  hint="Move candidatos no pipeline quando score for alto"
                  checked={config.automation.auto_stage_advance}
                  onCheckedChange={(v) =>
                    save({ automation: { ...config.automation, auto_stage_advance: v } })
                  }
                />
              </div>
            </CardContent>
          </Card>
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}
