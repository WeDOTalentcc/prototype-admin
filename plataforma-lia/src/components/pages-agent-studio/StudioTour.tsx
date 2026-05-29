// Q4.3 Tour interno do Agent Studio (2026-05-29) — fecha gap C1 do AUDIT 7
// ("tour-steps.ts cobre Studio em 1 step de spotlight — não há tour interno
// guiado").
//
// Tour leve, Studio-scoped, para o recrutador de primeira viagem. Reusa o
// componente canonical TourSpotlight (do onboarding) — sem viewer paralelo —
// e sequencia 5 passos ancorados em data-tour. Trigger: primeira visita ao
// Studio (localStorage flag `studio_tour_seen`). Dismissível a qualquer momento.
//
// Tom "The Quiet Operator": acolhedor, não intrusivo. Se um anchor não existir
// na tela (ex: tab ainda não renderizada), o passo é pulado graciosamente
// (TourSpotlight chama onDismiss quando o selector não casa).
"use client"

import React, { useEffect, useState, useCallback } from "react"
import { useTranslations } from "next-intl"
import { TourSpotlight } from "@/components/onboarding/tour/TourSpotlight"

const STORAGE_KEY = "studio_tour_seen"

interface StudioTourStep {
  id: string
  // i18n key sob agents.studio.tour.steps.*
  key: string
  selector: string
  position?: "top" | "bottom" | "left" | "right"
}

// 5 passos canonical (AUDIT C1): criar → testar → acompanhar → raciocínio →
// métricas. Cada selector tem fallbacks (vírgula) pra resistir a refactor de
// markup. Passos sem anchor visível são pulados.
const STUDIO_TOUR_STEPS: StudioTourStep[] = [
  {
    id: "create",
    key: "create",
    selector: "[data-tour='studio-create-agent']",
    position: "bottom",
  },
  {
    id: "sandbox",
    key: "sandbox",
    selector: "[data-tour='studio-tabs'], [data-tour='studio-create-agent']",
    position: "bottom",
  },
  {
    id: "controlRoom",
    key: "controlRoom",
    selector: "[data-tour='studio-tabs']",
    position: "bottom",
  },
  {
    id: "decisionTree",
    key: "decisionTree",
    selector: "[data-tour='studio-tabs']",
    position: "bottom",
  },
  {
    id: "kpis",
    key: "kpis",
    selector: "[data-tour='studio-stats'], [data-tour='studio-tabs']",
    position: "bottom",
  },
]

interface StudioTourProps {
  // Permite forçar o tour (ex: botão "rever tour"); default lê localStorage.
  forceStart?: boolean
  onFinish?: () => void
}

export function StudioTour({ forceStart = false, onFinish }: StudioTourProps) {
  const t = useTranslations("agents.studio.tour")
  const [stepIndex, setStepIndex] = useState<number>(-1) // -1 = inativo

  useEffect(() => {
    if (forceStart) {
      setStepIndex(0)
      return
    }
    // Primeira visita ao Studio → dispara o tour.
    try {
      const seen = localStorage.getItem(STORAGE_KEY)
      if (!seen) {
        setStepIndex(0)
      }
    } catch {
      // localStorage indisponível (SSR/privacy) — não dispara, sem erro.
    }
  }, [forceStart])

  const markSeen = useCallback(() => {
    try {
      localStorage.setItem(STORAGE_KEY, new Date().toISOString())
    } catch {
      // ignore — best-effort
    }
  }, [])

  const finish = useCallback(() => {
    setStepIndex(-1)
    markSeen()
    onFinish?.()
  }, [markSeen, onFinish])

  const advance = useCallback(() => {
    setStepIndex((prev) => {
      const next = prev + 1
      if (next >= STUDIO_TOUR_STEPS.length) {
        markSeen()
        onFinish?.()
        return -1
      }
      return next
    })
  }, [markSeen, onFinish])

  if (stepIndex < 0 || stepIndex >= STUDIO_TOUR_STEPS.length) return null

  const step = STUDIO_TOUR_STEPS[stepIndex]
  const isLast = stepIndex === STUDIO_TOUR_STEPS.length - 1
  const progress = `${stepIndex + 1}/${STUDIO_TOUR_STEPS.length}`

  // Mensagem acolhedora + progresso + dica de avançar/sair. Dismiss = sair do
  // tour inteiro (não só do passo).
  const message = `${progress} · ${t(`steps.${step.key}`)}\n\n${
    isLast ? t("finishHint") : t("nextHint")
  }`

  return (
    <div data-testid="studio-tour">
      <TourSpotlight
        key={step.id}
        selector={step.selector}
        message={message}
        position={step.position}
        onDismiss={advance}
      />
      {/* Botão explícito "Pular tour" — acessível, não depende só do X do
          spotlight. Fica fixo no canto pra ser sempre alcançável. */}
      <button
        type="button"
        onClick={finish}
        className="fixed bottom-4 right-4 z-[60] rounded-md border border-lia-border-subtle bg-lia-bg-primary px-3 py-1.5 text-xs font-medium text-lia-text-secondary shadow-lia-md hover:bg-lia-bg-tertiary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30"
        data-testid="studio-tour-skip"
        aria-label={t("skip")}
      >
        {t("skip")}
      </button>
    </div>
  )
}
