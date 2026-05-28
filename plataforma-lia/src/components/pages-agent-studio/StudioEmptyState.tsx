// Onda 4 F6.1 (2026-05-28) — empty state canonical do Studio.
//
// Reusable: Custom Agents tab + qualquer surface que mostre lista vazia.
// Persona-aware: persona name vem de useAiPersona() (default "LIA").
//
// Decisões de design:
//   - Card centralizado, sem border-dashed (já tem em outros empty states locais)
//   - 2 CTAs: explorar marketplace + conversar com persona
//   - Cyan badge sutil no topo (LIA cyan exclusivo da IA)
"use client"

import { useRouter, usePathname } from "next/navigation"
import { useTranslations } from "next-intl"
import { MessageCircle, Sparkles } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useAiPersona } from "@/hooks/company/use-ai-persona"

interface StudioEmptyStateProps {
  /** Callback opcional para "explorar marketplace" (default: switch tab interno). */
  onExploreMarketplace?: () => void
  /** Callback opcional para "conversar com persona" (default: abre chat). */
  onChatWithPersona?: () => void
}

export function StudioEmptyState({
  onExploreMarketplace,
  onChatWithPersona,
}: StudioEmptyStateProps) {
  const t = useTranslations("agents.studio.empty")
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "LIA"
  const router = useRouter()
  const pathname = usePathname()

  function handleMarketplace() {
    if (onExploreMarketplace) return onExploreMarketplace()
    // Default: navigate to studio with marketplace tab
    const locale = pathname.split("/")[1] || "pt"
    router.push(`/${locale}/agent-studio?tab=marketplace`)
  }

  function handleChat() {
    if (onChatWithPersona) return onChatWithPersona()
    // Default: dispatch open-chat event (chat sidebar listener)
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("lia:open-chat"))
    }
  }

  return (
    <Card
      className="border border-lia-border-subtle shadow-none"
      data-testid="studio-empty-state"
    >
      <CardContent className="flex flex-col items-center gap-3 px-6 py-12 text-center">
        <span
          aria-hidden="true"
          className="text-2xl text-wedo-cyan"
        >
          🩵
        </span>
        <h2 className="font-sans text-base font-semibold text-lia-text-primary">
          {t("title")}
        </h2>
        <p className="max-w-md text-sm text-lia-text-secondary">
          {t("description", { personaName })}
        </p>
        <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleMarketplace}
            className="gap-1.5"
          >
            <Sparkles className="h-3.5 w-3.5" />
            {t("cta.marketplace")}
          </Button>
          <Button
            type="button"
            size="sm"
            onClick={handleChat}
            className="gap-1.5"
          >
            <MessageCircle className="h-3.5 w-3.5" />
            {t("cta.chat", { personaName })}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
