"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ChevronLeft, Loader2, Bot } from "lucide-react"
import { useTranslations } from "next-intl"
import { CreateCustomAgentModal } from "@/components/pages-agent-studio/CustomAgentsTab"

// Shape esperado pelo CreateCustomAgentModal (interface local de CustomAgentsTab.tsx).
// Não importamos o `CustomAgent` canonical de `./custom-agents/types` porque ele
// tem campos distintos. Esta cópia espelha exatamente os campos lidos pelo modal.
interface EditAgentShape {
  id: string
  name: string
  role: string
  description: string | null
  system_prompt: string
  allowed_tools: string[]
  domain: string
  icon: string
  status: string
  version: number
  total_executions: number
  avg_confidence: number
  is_marketplace_published: boolean
  created_at: string | null
  updated_at: string | null
  max_steps?: number
  temperature?: number
  config?: Record<string, unknown>
}
import { cn } from "@/lib/utils"
import { textStyles } from "@/lib/design-tokens"

/**
 * Sub-surface /agent-studio/[id]/edit — Wave B2.1 (2026-05-27).
 *
 * Reusa CreateCustomAgentModal (form canonical já existente em CustomAgentsTab).
 * Header: back link → /agent-studio + nome do agente.
 *
 * Decisão (Paulo): manter o form em CustomAgentsTab.tsx como única fonte
 * (DRY canonical). Apenas exportamos a função pra que esta sub-surface
 * a consuma diretamente. Extrair pra arquivo standalone foi descartado:
 * o form tem ~250 LOC com dependências internas (useTranslations, fetch
 * available-tools, error state), e mover sem caller dual aumentaria
 * tech-debt sem ganho funcional.
 */

interface EditAgentClientProps {
  agentId: string
}

export default function EditAgentClient({ agentId }: EditAgentClientProps) {
  const t = useTranslations("agents.customAgents")
  const router = useRouter()
  const [agent, setAgent] = useState<EditAgentShape | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
        const res = await fetch(`/api/backend-proxy/custom-agents/${agentId}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        if (!res.ok) throw new Error(`Failed to load agent: ${res.status}`)
        const data = await res.json()
        if (!cancelled) setAgent(data)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Unknown error")
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [agentId])

  const handleClose = () => {
    router.push("/agent-studio")
  }

  const handleSaved = () => {
    router.push("/agent-studio")
  }

  return (
    <div className="h-full flex flex-col">
      <header className="border-b border-lia-border-subtle bg-lia-bg-base px-6 py-3">
        <div className="flex items-center gap-3 max-w-5xl mx-auto">
          <Link
            href="/agent-studio"
            className="inline-flex items-center gap-1 text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30 rounded-md px-2 py-1"
            data-testid="back-to-studio"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            {t("backToStudio")}
          </Link>
          <span className="text-lia-text-disabled">/</span>
          <div className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-graphite" />
            <h1 className={cn(textStyles.title, "text-sm")}>
              {isLoading ? t("loading") : agent?.name ?? t("editBtn")}
            </h1>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-5 h-5 animate-spin text-lia-text-secondary" />
            <span className="ml-2 text-sm text-lia-text-secondary">{t("loading")}</span>
          </div>
        ) : error ? (
          <div className="max-w-md mx-auto mt-20 p-4 rounded-md border border-red-200 bg-red-50 text-sm text-red-800">
            {error}
          </div>
        ) : agent ? (
          <CreateCustomAgentModal
            agent={agent}
            onClose={handleClose}
            onSaved={handleSaved}
          />
        ) : null}
      </main>
    </div>
  )
}
