"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Palette, Sun, Moon, Monitor, Globe, Bot } from "lucide-react"

export interface SettingsGeneralTabProps {
  onSettingsChange: (changed: boolean) => void
}

export function SettingsGeneralTab({ onSettingsChange }: SettingsGeneralTabProps) {
  return (
    <div className="space-y-8">
      <PreferencesTab onSettingsChange={onSettingsChange} />
      <LIATab onSettingsChange={onSettingsChange} />
    </div>
  )
}

function PreferencesTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const t = useTranslations("settings.general")
  const [theme, setTheme] = useState("light")
  const [language, setLanguage] = useState("pt-BR")
  const [timezone, setTimezone] = useState("America/Sao_Paulo")

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Palette className="w-4 h-4" />
            {t("appearance")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              {t("theme")}
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: "light", name: t("light"), icon: Sun },
                { id: "dark", name: t("dark"), icon: Moon },
                { id: "system", name: t("system"), icon: Monitor }
              ].map((themeOption) => (
                <button
                  key={themeOption.id}
                  onClick={() => {
                    setTheme(themeOption.id)
                    onSettingsChange(true)
                  }}
                  className={`p-3 rounded-md border text-center transition-colors motion-reduce:transition-none ${
                    theme === themeOption.id
 ? 'border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-secondary text-lia-text-primary'
                      : 'border-lia-border-subtle dark:border-lia-border-subtle hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover'
                  }`}
                >
                  <themeOption.icon className="w-5 h-5 mx-auto mb-1" />
                  <div className="text-sm font-medium">{themeOption.name}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              {t("language")}
            </label>
            <select
              value={language}
              onChange={(e) => {
                setLanguage(e.target.value)
                onSettingsChange(true)
              }}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
            >
              <option value="pt-BR">{t("portugueseBrazil")}</option>
              <option value="en-US">{t("englishUS")}</option>
              <option value="es-ES">{t("spanish")}</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Globe className="w-4 h-4" />
            {t("localization")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              {t("timezone")}
            </label>
            <select
              value={timezone}
              onChange={(e) => {
                setTimezone(e.target.value)
                onSettingsChange(true)
              }}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
            >
              <option value="America/Sao_Paulo">{t("tzSaoPaulo")}</option>
              <option value="America/New_York">{t("tzNewYork")}</option>
              <option value="Europe/London">{t("tzLondon")}</option>
            </select>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function LIATab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const t = useTranslations("settings.general")
  const [liaSettings, setLiaSettings] = useState({
    personality: "professional",
    responseStyle: "detailed",
    autoSuggestions: true,
    contextAwareness: true,
    proactiveInsights: true,
    learningMode: true
  })

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Bot className="w-4 h-4" />
            {t("liaPersonality")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              {t("communicationStyle")}
            </label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { id: "professional", name: t("professional"), desc: t("professionalDesc") },
                { id: "casual", name: t("casual"), desc: t("casualDesc") },
                { id: "concise", name: t("concise"), desc: t("conciseDesc") },
                { id: "detailed", name: t("detailed"), desc: t("detailedDesc") }
              ].map((style) => (
                <button
                  key={style.id}
                  onClick={() => {
                    setLiaSettings(prev => ({ ...prev, personality: style.id }))
                    onSettingsChange(true)
                  }}
                  className={`p-3 rounded-md border text-left transition-colors motion-reduce:transition-none ${
                    liaSettings.personality === style.id
                      ? 'border-lia-btn-primary-bg dark:border-lia-border-subtle bg-wedo-cyan/10 dark:bg-wedo-cyan/20'
                      : 'border-lia-border-subtle dark:border-lia-border-subtle hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover'
                  }`}
                >
                  <div className="font-medium text-sm">{style.name}</div>
                  <div className="text-xs text-lia-text-primary">{style.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { key: "autoSuggestions", label: t("autoSuggestions"), desc: t("autoSuggestionsDesc") },
              { key: "contextAwareness", label: t("contextAwareness"), desc: t("contextAwarenessDesc") },
              { key: "proactiveInsights", label: t("proactiveInsights"), desc: t("proactiveInsightsDesc") },
              { key: "learningMode", label: t("learningMode"), desc: t("learningModeDesc") }
            ].map((setting) => (
              <div key={setting.key} className="flex items-start gap-3 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                <input
                  type="checkbox"
                  checked={liaSettings[setting.key as keyof typeof liaSettings] as boolean}
                  onChange={(e) => {
                    setLiaSettings(prev => ({ ...prev, [setting.key]: e.target.checked }))
                    onSettingsChange(true)
                  }}
                  className="mt-1"
                />
                <div>
                  <div className="text-sm font-medium text-lia-text-primary">{setting.label}</div>
                  <div className="text-xs text-lia-text-primary">{setting.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
