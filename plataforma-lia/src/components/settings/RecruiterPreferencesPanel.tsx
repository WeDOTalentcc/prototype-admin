"use client"

import React, { useEffect, useState, useCallback } from "react"
import { Brain, Settings2, Sparkles, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"

interface PersonalizationSummary {
  personalization_available: boolean
  personalization_level: string
  jobs_created: number
  jobs_needed: number
  preferred_seniorities: string[]
  preferred_departments: string[]
  fields_often_corrected: string[]
  prefers_quick_flow: boolean
}

interface PersonalizationSettings {
  personalization_enabled: boolean
  data_collection_consent: boolean
  show_personalization_indicators: boolean
  allow_behavior_learning: boolean
}

const LEVEL_LABELS: Record<string, string> = {
  none: "Sem dados",
  minimal: "Basico",
  partial: "Parcial",
  full: "Completa",
  disabled: "Desativada",
}

const LEVEL_COLORS: Record<string, string> = {
  none: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
  minimal: "bg-wedo-orange/10 text-wedo-orange",
  partial: "bg-wedo-cyan/10 text-wedo-cyan",
  full: "bg-status-success/10 text-status-success",
  disabled: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500",
}

export function RecruiterPreferencesPanel({ className }: { className?: string }) {
  const [summary, setSummary] = useState<PersonalizationSummary | null>(null)
  const [settings, setSettings] = useState<PersonalizationSettings | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [summaryRes, settingsRes] = await Promise.all([
        fetch("/api/backend-proxy/recruiter-profiles/me/summary"),
        fetch("/api/backend-proxy/recruiter-profiles/me/settings"),
      ])
      if (summaryRes.ok) setSummary(await summaryRes.json())
      if (settingsRes.ok) setSettings(await settingsRes.json())
    } catch {
      // silent — panel is informational
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const toggleSetting = async (key: keyof PersonalizationSettings, value: boolean) => {
    try {
      const res = await fetch("/api/backend-proxy/recruiter-profiles/me/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [key]: value }),
      })
      if (res.ok) {
        setSettings((prev) => prev ? { ...prev, [key]: value } : prev)
      }
    } catch {
      // silent
    }
  }

  if (loading) {
    return (
      <Card className={cn("animate-pulse", className)}>
        <CardContent className="p-6">
          <div className="h-32 bg-gray-100 dark:bg-gray-800 rounded-lg" />
        </CardContent>
      </Card>
    )
  }

  const level = summary?.personalization_level || "none"

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-wedo-cyan" aria-hidden="true" />
            Personalizacao da LIA
          </span>
          <Badge className={cn("text-xs", LEVEL_COLORS[level] || LEVEL_COLORS.none)}>
            {LEVEL_LABELS[level] || level}
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Progress to full personalization */}
        {summary && !summary.personalization_available && (
          <div className="text-xs text-lia-text-secondary space-y-1">
            <p>
              Crie mais {summary.jobs_needed} vaga(s) para desbloquear
              personalizacao completa.
            </p>
            <div className="h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-wedo-cyan rounded-full transition-all"
                style={{ width: `${Math.min((summary.jobs_created / 10) * 100, 100)}%` }}
              />
            </div>
            <p className="text-[10px]">{summary.jobs_created}/10 vagas</p>
          </div>
        )}

        {/* Learned patterns */}
        {summary?.personalization_available && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-lia-text-secondary flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-wedo-cyan" aria-hidden="true" />
              Aprendido pela IA
            </p>

            {summary.preferred_seniorities.length > 0 && (
              <div className="flex flex-wrap gap-1">
                <span className="text-[10px] text-lia-text-tertiary w-full">Senioridades:</span>
                {summary.preferred_seniorities.map((s) => (
                  <Badge key={s} variant="secondary" className="text-[10px]">{s}</Badge>
                ))}
              </div>
            )}

            {summary.preferred_departments.length > 0 && (
              <div className="flex flex-wrap gap-1">
                <span className="text-[10px] text-lia-text-tertiary w-full">Departamentos:</span>
                {summary.preferred_departments.map((d) => (
                  <Badge key={d} variant="secondary" className="text-[10px]">{d}</Badge>
                ))}
              </div>
            )}

            {summary.fields_often_corrected.length > 0 && (
              <div className="flex flex-wrap gap-1">
                <span className="text-[10px] text-lia-text-tertiary w-full">Campos que voce costuma ajustar:</span>
                {summary.fields_often_corrected.map((f) => (
                  <Badge key={f} variant="outline" className="text-[10px] border-wedo-orange/30 text-wedo-orange">{f}</Badge>
                ))}
              </div>
            )}

            <div className="flex items-center gap-2 text-xs">
              <Settings2 className="w-3 h-3 text-lia-text-tertiary" aria-hidden="true" />
              <span className="text-lia-text-secondary">
                Estilo: {summary.prefers_quick_flow ? "Rapido e direto" : "Detalhado e completo"}
              </span>
            </div>
          </div>
        )}

        {/* Manual settings */}
        {settings && (
          <div className="space-y-3 pt-2 border-t border-lia-border-subtle">
            <p className="text-xs font-medium text-lia-text-secondary">Configuracoes manuais</p>

            <div className="flex items-center justify-between">
              <Label htmlFor="personalization-toggle" className="text-xs">
                Ativar personalizacao
              </Label>
              <Switch
                id="personalization-toggle"
                checked={settings.personalization_enabled}
                onCheckedChange={(v) => toggleSetting("personalization_enabled", v)}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="learning-toggle" className="text-xs">
                Aprender com minhas correcoes
              </Label>
              <Switch
                id="learning-toggle"
                checked={settings.allow_behavior_learning}
                onCheckedChange={(v) => toggleSetting("allow_behavior_learning", v)}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="indicators-toggle" className="text-xs">
                Mostrar indicadores de confianca
              </Label>
              <Switch
                id="indicators-toggle"
                checked={settings.show_personalization_indicators}
                onCheckedChange={(v) => toggleSetting("show_personalization_indicators", v)}
              />
            </div>
          </div>
        )}

        {/* Recalculate button */}
        {summary?.personalization_available && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-xs gap-1"
            onClick={async () => {
              await fetch("/api/backend-proxy/recruiter-profiles/me/recalculate", { method: "POST" })
              fetchData()
            }}
          >
            <RefreshCw className="w-3 h-3" aria-hidden="true" />
            Recalcular perfil
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
