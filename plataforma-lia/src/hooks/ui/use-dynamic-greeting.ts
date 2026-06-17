"use client"

/**
 * useDynamicGreeting — frase de abertura dinâmica (Task #1315 / Opção B).
 *
 * Renderiza uma saudação variada que reflete o contexto real do recrutador
 * (briefing diário) quando há dados, caindo para uma rotação de frases curadas
 * quando não houver. Reaproveita `useDailyBriefing` (sem infra nova).
 *
 * Hidratação: na 1ª renderização (server + 1º paint client) retorna `fallback`
 * estático; só após montar (seed definido em useEffect) troca para a versão
 * dinâmica — evita mismatch de hidratação e tela em branco.
 *
 * Vue/Nuxt: mapeia para composable useDynamicGreeting(surface, fallback).
 */
import { useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { useJWTAuth } from "@/contexts/auth-context"
import { useDailyBriefing } from "@/hooks/ai/use-daily-briefing"
import {
  selectGreeting,
  type GreetingBriefingInput,
  type GreetingSurface,
} from "@/lib/dynamic-greeting"

export function useDynamicGreeting(surface: GreetingSurface, fallback: string): string {
  const t = useTranslations("dynamicGreetings")
  const { user } = useJWTAuth()
  const { briefing } = useDailyBriefing()

  const [seed, setSeed] = useState<number | null>(null)
  useEffect(() => {
    setSeed(Math.floor(Math.random() * 100000))
  }, [])

  const briefingInput: GreetingBriefingInput | null = useMemo(() => {
    if (!briefing) return null
    const pipeline = briefing.pipeline_summary
    const metrics = briefing.metrics
    return {
      activeJobs: pipeline?.active_jobs ?? 0,
      candidatesToContact: pipeline?.candidates_to_contact ?? 0,
      awaitingFeedback: pipeline?.awaiting_feedback ?? 0,
      offersPending: pipeline?.offers_pending ?? 0,
      interviewsToday: metrics?.interviews_today ?? 0,
    }
  }, [briefing])

  return useMemo(() => {
    if (seed === null) return fallback

    const plan = selectGreeting({
      surface,
      now: new Date(),
      briefing: briefingInput,
      name: user?.name ?? null,
      seed,
    })

    try {
      if (plan.kind === "context") {
        return t(`${surface}.context.${plan.key}`, {
          greeting: t(`timeOfDay.${plan.timeKey}`),
          name: plan.name,
          ...plan.counts,
        })
      }

      const poolKey = plan.named ? `${surface}.curatedNamed` : `${surface}.curated`
      const pool = t.raw(poolKey) as unknown
      if (!Array.isArray(pool) || pool.length === 0) return fallback
      const phrase = String(pool[plan.index % pool.length])
      if (plan.named && plan.name) {
        return `${t(`timeOfDay.${plan.timeKey}`)}, ${plan.name}. ${phrase}`
      }
      return phrase
    } catch {
      // Requisito do produto: nunca tela em branco / sem estado de erro.
      return fallback
    }
  }, [seed, briefingInput, user?.name, surface, fallback, t])
}
