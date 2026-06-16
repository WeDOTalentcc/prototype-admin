"use client"

/**
 * OnboardingChatBanner — P2-2 Sprint B.1 entry point.
 *
 * Card de onboarding (Callout variante `info`) que aparece no topo do dashboard
 * quando o recrutador tem setup_progress < threshold (canonical 80%) e não
 * dispensou. Cyan é usado APENAS como acento de IA/LIA (ícone, superfície/borda
 * sutil do Callout e o texto "{progress}% completo") — nunca em botões.
 *
 * 3 CTAs:
 *   1. "Configure via chat" → abre chat LIA com modo onboarding (Button primary)
 *   2. "Prefiro formulário" → navega pra /configuracoes (Button outline)
 *   3. "Dispensar" → marca dismissed em localStorage (não reaparece). Botão "X"
 *      ancorado no canto superior direito do card.
 *
 * Layout compacto: subtítulo + CTAs na mesma linha (frase à esquerda, botões
 * à direita), padding reduzido para minimizar a altura do card.
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
import { useLocale } from "next-intl"
import { useOnboardingFlow } from "@/components/onboarding/useOnboardingFlow"
import { Callout } from "@/components/ui/callout"
import { Button } from "@/components/ui/button"

const DISMISSED_KEY = "lia-onboarding-banner-dismissed"
const RESHOW_PROGRESS_THRESHOLD = 50  // se cair abaixo, re-show

interface Props {
  onOpenChat?: () => void  // callback pra abrir chat com onboarding mode
  className?: string
}

export function OnboardingChatBanner({ onOpenChat, className = "" }: Props) {
  const router = useRouter()
  const locale = useLocale()
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
    router.push(`/${locale}/configuracoes`)
  }, [router, locale])

  // Gate: não renderiza se loading, completed, ou dismissed
  if (loading || !needsOnboarding || dismissed) return null

  const progress = setupProgress ?? 0

  return (
    <Callout
      variant="info"
      data-testid="onboarding-chat-banner"
      role="region"
      aria-label="Banner de onboarding conversacional"
      className={`relative items-center rounded-xl p-3 ${className}`}
      icon={
        <Brain className="h-5 w-5 text-wedo-cyan" aria-hidden="true" />
      }
      title={
        <span className="block pr-8">Configure sua empresa em 15 minutos via chat</span>
      }
    >
      {/* Botão dispensar — ancorado no canto superior direito do card */}
      <button
        type="button"
        onClick={handleDismiss}
        data-testid="banner-dismiss"
        aria-label="Dispensar banner"
        className="absolute right-3 top-3 shrink-0 text-lia-text-secondary hover:text-lia-text-primary"
      >
        <X className="h-4 w-4" aria-hidden="true" />
      </button>
      {/* Frase + CTAs na mesma linha (frase à esquerda, botões à direita) */}
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <p className="text-xs leading-snug text-lia-text-secondary">
          Mais rápido que preencher 80+ campos sozinho.
          <span className="ml-2 font-medium text-lia-text-secondary">
            {progress}% completo
          </span>
        </p>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="primary"
            size="sm"
            onClick={handleOpenChat}
            data-testid="banner-open-chat"
          >
            <MessageCircle aria-hidden="true" />
            Configure via chat
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleOpenSettings}
            data-testid="banner-open-settings"
          >
            <Settings aria-hidden="true" />
            Prefiro formulário
          </Button>
        </div>
      </div>
    </Callout>
  )
}
