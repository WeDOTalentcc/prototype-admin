"use client"

import React, { useState } from "react"
import { useTranslations } from "next-intl"
import { Bot, ChevronRight, Zap } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  textStyles, cardStyles, badgeStyles, buttonStyles
} from "@/lib/design-tokens"

interface WizardAgentStepProps {
  jobTitle: string
  onActivate: (config: AgentWizardConfig) => void
  onSkip: () => void
}

interface AgentWizardConfig {
  enabled: boolean
  sectorTemplate: string | null
  candidatesPerDay: number
  notifyFrequency: string
  channels: string[]
  shouldCalibrate: boolean
}

const SECTOR_KEYS = ["technology", "manufacturing", "healthcare", "retail", "transportation"] as const
const SECTOR_ICONS: Record<string, string> = {
  technology: "💻",
  manufacturing: "🏭",
  healthcare: "🏥",
  retail: "🛒",
  transportation: "🚛",
}

export default function WizardAgentStep({ jobTitle, onActivate, onSkip }: WizardAgentStepProps) {
  const t = useTranslations('agents.wizard')
  const [wantsAgent, setWantsAgent] = useState<boolean | null>(null)
  const [sectorTemplate, setSectorTemplate] = useState<string | null>(null)
  const [candidatesPerDay, setCandidatesPerDay] = useState(20)
  const [notifyFrequency, setNotifyFrequency] = useState("daily")

  if (wantsAgent === null) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <Bot className="w-12 h-12 text-lia-text-tertiary mx-auto mb-3" />
          <h3 className={textStyles.h3}>{t('automaticSourcing')}</h3>
          <p className={`${textStyles.body} mt-2 max-w-md mx-auto`}>
            {t('automaticSourcingDesc')}
          </p>
        </div>

        <div className="flex justify-center gap-4">
          <Button className={buttonStyles.primary} onClick={() => setWantsAgent(true)}>
            <Zap className="w-4 h-4 mr-1" />
            {t('activateSourcing')}
          </Button>
          <Button className={buttonStyles.secondary} onClick={onSkip}>
            {t('searchManually')}
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-lg mx-auto">
      <div>
        <h3 className={textStyles.h3}>{t('configureAgent')} — {jobTitle}</h3>
        <p className={textStyles.caption}>{t('chooseTemplateHint')}</p>
      </div>

      <div>
        <label className={textStyles.label}>{t('sectorTemplate')}</label>
        <div className="grid grid-cols-3 gap-2 mt-2">
          {SECTOR_KEYS.map(s => (
            <button
              key={s}
              onClick={() => setSectorTemplate(s === sectorTemplate ? null : s)}
              className={`p-3 rounded-md border text-center text-sm transition-colors ${
                sectorTemplate === s
                  ? "border-lia-text-primary bg-lia-bg-secondary text-lia-text-primary"
                  : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
              }`}
            >
              <span className="text-lg">{SECTOR_ICONS[s]}</span>
              <p className="mt-1">{t(`sectors.${s}`)}</p>
            </button>
          ))}
          <button
            onClick={() => setSectorTemplate(null)}
            className={`p-3 rounded-md border text-center text-sm transition-colors ${
              sectorTemplate === null
                ? "border-lia-text-primary bg-lia-bg-secondary text-lia-text-primary"
                : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
            }`}
          >
            <span className="text-lg">✨</span>
            <p className="mt-1">{t('sectors.auto')}</p>
          </button>
        </div>
      </div>

      <div>
        <label className={textStyles.label}>{t('candidatesPerDay')}</label>
        <div className="flex gap-2 mt-2">
          {[10, 20, 30, 50].map(n => (
            <button
              key={n}
              onClick={() => setCandidatesPerDay(n)}
              className={`px-4 py-2 rounded-md text-sm border transition-colors ${
                candidatesPerDay === n
                  ? "border-lia-text-primary bg-lia-bg-secondary text-lia-text-primary"
                  : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className={textStyles.label}>{t('notifications')}</label>
        <div className="flex gap-2 mt-2">
          {[
            { id: "realtime", labelKey: "realtime" },
            { id: "daily", labelKey: "dailySummary" },
            { id: "weekly", labelKey: "weekly" },
          ].map(opt => (
            <button
              key={opt.id}
              onClick={() => setNotifyFrequency(opt.id)}
              className={`px-4 py-2 rounded-md text-sm border transition-colors ${
                notifyFrequency === opt.id
                  ? "border-lia-text-primary bg-lia-bg-secondary text-lia-text-primary"
                  : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
              }`}
            >
              {t(`notifyOptions.${opt.labelKey}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="flex justify-between pt-4 border-t border-lia-border-subtle">
        <Button className={buttonStyles.secondary} onClick={() => setWantsAgent(null)}>
          {t('back')}
        </Button>
        <Button
          className={buttonStyles.primary}
          onClick={() => onActivate({
            enabled: true,
            sectorTemplate,
            candidatesPerDay,
            notifyFrequency,
            channels: ["internal", "linkedin"],
            shouldCalibrate: true,
          })}
        >
          {t('activateAndCalibrate')} <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </div>

      <p className={`${textStyles.caption} text-center`}>
        {t('calibrationHint')}
      </p>
    </div>
  )
}
