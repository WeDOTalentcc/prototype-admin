"use client"

/**
 * OnboardingChatBanner — P2-2 Sprint B.1 entry point.
 *
 * Banner cyan que aparece no topo do dashboard quando recrutador
 * tem setup_progress < threshold (canonical 80%) e não dispensou.
 *
 * 3 CTAs:
 *   1. "Configure via chat" → abre chat LIA com modo onboarding
 *   2. "Prefiro formulário" → navega pra /configuracoes
 *   3. "Dispensar" → marca dismissed em localStorage (não reaparece)
 *
 * Persistence: localStorage "lia-onboarding-banner-dismissed" + reset
 * automático se setup_progress cair abaixo de 50% (regressão = re-show).
 *
 * RBAC (P2-3): aparece para todos os roles (admin/manager/recruiter)
 * exceto viewer (read-only não precisa onboarding ativo).
 *
 * Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md Sprint B.1
 */

import { Brain, MessageCircle, Settings, X } from "lucide-react"
import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { useOnboardingFlow } from "@/components/onboarding/useOnboardingFlow"

const DISMISSED_KEY = "lia-onboarding-banner-dismissed"
const RESHOW_PROGRESS_THRESHOLD = 50  // se cair abaixo, re-show

interface Props {
  onOpenChat?: () => void  // callback pra abrir chat com onboarding mode
  className?: string
}

export function OnboardingChatBanner({ onOpenChat, className = "" }: Props) {
  const router = useRouter()
  const { needsOnboarding, setupProgress, loading } = useOnboardingFlow()
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    if (typeof window === "undefined") return
    const stored = window.localStorage.getItem(DISMISSED_KEY)
    // Re-show se progress < 50% (regressão)
    if (stored && setupProgress !== null && setupProgress < RESHOW_PROGRESS_THRESHOLD) {
      window.localStorage.removeItem(DISMISSED_KEY)
      setDismissed(false)
    } else if (stored) {
      setDismissed(true)
    }
  }, [setupProgress])

  const handleDismiss = useCallback(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(DISMISSED_KEY, "true")
    }
    setDismissed(true)
  }, [])

  const handleOpenChat = useCallback(() => {
    onOpenChat?.()
  }, [onOpenChat])

  const handleOpenSettings = useCallback(() => {
    router.push("/configuracoes")
  }, [router])

  // Gate: não renderiza se loading, completed, ou dismissed
  if (loading || !needsOnboarding || dismissed) return null

  const progress = setupProgress ?? 0

  return (
    <div
      data-testid="onboarding-chat-banner"
      className={`rounded-xl border border-wedo-cyan/40 bg-gradient-to-r from-wedo-cyan/10 to-transparent dark:from-wedo-cyan/15 p-4 ${className}`}
      role="region"
      aria-label="Banner de onboarding conversacional"
    >
      <div className="flex items-start gap-3">
        <Brain className="w-5 h-5 text-wedo-cyan shrink-0 mt-0.5" aria-hidden="true" />
        <div className="flex-1 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-lia-text-primary">
              Configure sua empresa em 15 minutos via chat
            </h3>
            <button
              type="button"
              onClick={handleDismiss}
              data-testid="banner-dismiss"
              aria-label="Dispensar banner"
              className="text-lia-text-secondary hover:text-lia-text-primary"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
          <p className="text-xs text-lia-text-secondary leading-snug">
            A LIA conversa com você e configura tudo automaticamente. Mais rápido que preencher 80+ campos sozinho.
            <span className="ml-2 text-wedo-cyan font-medium">
              {progress}% completo
            </span>
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            <button
              type="button"
              onClick={handleOpenChat}
              data-testid="banner-open-chat"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-wedo-cyan text-white text-xs font-medium hover:bg-wedo-cyan/90 transition-colors motion-reduce:transition-none"
            >
              <MessageCircle className="w-3.5 h-3.5" aria-hidden="true" />
              Configure via chat
            </button>
            <button
              type="button"
              onClick={handleOpenSettings}
              data-testid="banner-open-settings"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-lia-bg-primary border border-lia-border-default text-xs text-lia-text-primary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
            >
              <Settings className="w-3.5 h-3.5" aria-hidden="true" />
              Prefiro formulário
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
