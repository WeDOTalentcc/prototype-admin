"use client"

import Link from "next/link"
import { ChevronLeft } from "lucide-react"
import MarketplaceTab from "@/components/pages-agent-studio/MarketplaceTab"

/**
 * MarketplaceClient — Studio Restructure Fase 2 (2026-05-26).
 *
 * Renderiza MarketplaceTab standalone na rota /agents/marketplace.
 * Substitui a tab "Marketplace" antiga do AgentStudioPage.
 *
 * Header canonical:
 *  - Breadcrumb/back link "← Estúdio de Agentes" para /agent-studio
 *  - Título "Marketplace de Agentes"
 *
 * Princípios: DESIGN.md Quiet Operator — sem cyan, tokens DS, flat by default.
 */
export default function MarketplaceClient() {
  return (
    <div className="h-full flex flex-col">
      <div className="flex-shrink-0 px-4 pt-3 pb-2 border-b border-lia-border-subtle">
        <Link
          href="/agent-studio"
          className="inline-flex items-center gap-1.5 text-xs text-lia-text-secondary hover:text-lia-text-primary transition-colors mb-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30 rounded"
          data-testid="marketplace-back-to-studio"
        >
          <ChevronLeft className="w-3.5 h-3.5" aria-hidden="true" />
          Estúdio de Agentes
        </Link>
        <h1 className="text-lg font-semibold text-lia-text-primary">
          Marketplace de Agentes
        </h1>
      </div>
      <div className="flex-1 overflow-auto px-4 py-4">
        <MarketplaceTab />
      </div>
    </div>
  )
}
