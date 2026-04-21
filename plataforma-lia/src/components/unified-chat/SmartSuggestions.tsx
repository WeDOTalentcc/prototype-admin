"use client"

import React, { useMemo } from "react"
import { cn } from "@/lib/utils"
import {
  Briefcase, Search, BarChart2, Users, FileText,
  Brain, Calendar, MessageCircle, HelpCircle, Zap,
} from "lucide-react"
import { useTranslations } from 'next-intl'

interface Suggestion {
  icon: React.ElementType
  labelKey: string
  promptKey: string
  category: "criar" | "buscar" | "analisar" | "comunicar" | "ajuda"
}

interface Props {
  contextPage?: string
  mode: "sidebar" | "floating" | "fullscreen"
  onSuggestionClick: (prompt: string) => void
}

const ALL_SUGGESTIONS: Suggestion[] = [
  { icon: Briefcase, labelKey: "createJob", promptKey: "createJob", category: "criar" },
  { icon: FileText, labelKey: "enrichJD", promptKey: "enrichJD", category: "criar" },
  { icon: Brain, labelKey: "generateWSI", promptKey: "generateWSI", category: "criar" },
  { icon: Search, labelKey: "searchCandidates", promptKey: "searchCandidates", category: "buscar" },
  { icon: Users, labelKey: "talentPool", promptKey: "talentPool", category: "buscar" },
  { icon: Zap, labelKey: "autoSourcing", promptKey: "autoSourcing", category: "buscar" },
  { icon: BarChart2, labelKey: "weeklyReport", promptKey: "weeklyReport", category: "analisar" },
  { icon: BarChart2, labelKey: "funnelHealth", promptKey: "funnelHealth", category: "analisar" },
  { icon: Brain, labelKey: "jobAnalytics", promptKey: "jobAnalytics", category: "analisar" },
  { icon: MessageCircle, labelKey: "candidateFeedback", promptKey: "candidateFeedback", category: "comunicar" },
  { icon: Calendar, labelKey: "scheduleInterview", promptKey: "scheduleInterview", category: "comunicar" },
  { icon: HelpCircle, labelKey: "whatCanIDo", promptKey: "whatCanIDo", category: "ajuda" },
]


const PAGE_PRIORITIES: Record<string, string[]> = {
  "jobs": ["criar", "analisar"],
  "candidates": ["buscar", "comunicar"],
  "pipeline": ["analisar", "comunicar"],
  "dashboard": ["analisar", "criar"],
  "agent-studio": ["buscar", "criar"],
}

function useGreeting(): string {
  const t = useTranslations('chat')
  const hour = new Date().getHours()
  if (hour < 12) return t("greetingMorning")
  if (hour < 18) return t("greetingAfternoon")
  return t("greetingEvening")
}

export function SmartSuggestions({ contextPage, mode, onSuggestionClick }: Props) {
  const t = useTranslations('chat')
  const greeting = useGreeting()

  const suggestions = useMemo(() => {
    const priorities = PAGE_PRIORITIES[contextPage || ""] || ["criar", "buscar"]
    const sorted = [...ALL_SUGGESTIONS].sort((a, b) => {
      const aIdx = priorities.indexOf(a.category)
      const bIdx = priorities.indexOf(b.category)
      const aPri = aIdx >= 0 ? aIdx : 99
      const bPri = bIdx >= 0 ? bIdx : 99
      return aPri - bPri
    })
    return sorted.slice(0, mode === "fullscreen" ? 6 : 4)
  }, [contextPage, mode])

  const isCompact = mode === "sidebar" || mode === "floating"

  return (
    <div className="flex flex-col items-center justify-center flex-1 px-4 py-8">
      <div className="text-center mb-6">
        <div className="w-10 h-10 rounded-full bg-wedo-cyan/10 flex items-center justify-center mx-auto mb-3">
          <Brain className="w-5 h-5 text-wedo-cyan" />
        </div>
        <h3 className={cn(
          "font-semibold text-lia-text-primary",
          isCompact ? "text-sm" : "text-lg",
        )}>
          {greeting}! {t("iAmLia")}
        </h3>
        <p className="text-xs text-lia-text-secondary mt-1">
          {t("greetingFull")}
        </p>
      </div>

      <div className={cn(
        "w-full max-w-md gap-2",
        isCompact ? "flex flex-col" : "grid grid-cols-2",
      )}>
        {suggestions.map((s, i) => {
          const Icon = s.icon
          return (
            <button
              key={i}
              onClick={() => onSuggestionClick(t(`smartPrompts.${s.promptKey}`))}
              className="flex items-start gap-2.5 px-3 py-2.5 rounded-xl border border-lia-border-subtle bg-lia-bg-primary text-left hover:border-wedo-cyan/40 hover:bg-wedo-cyan/5 transition-colors motion-reduce:transition-none group"
            >
              <Icon className="w-4 h-4 text-lia-text-disabled group-hover:text-wedo-cyan flex-shrink-0 mt-0.5 transition-colors" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-lia-text-primary">
                  {t(`smartSuggestions.${s.labelKey}`)}
                </p>
              </div>
            </button>
          )
        })}
      </div>

      <p className="text-[10px] text-lia-text-tertiary mt-4">
        {t("helpHint")}
      </p>
    </div>
  )
}

export function getHelpResponse(t: ReturnType<typeof useTranslations>) {
  return t('helpResponse')
}

