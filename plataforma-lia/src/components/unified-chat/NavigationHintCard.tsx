"use client"

import React from "react"
import { ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface NavigationHint {
  page: string
  entity_id?: string
}

interface Props {
  hint: NavigationHint
  className?: string
}

/**
 * NavigationHintCard — Renders a navigation suggestion inline in chat messages.
 *
 * When the backend returns a navigation_hint in message metadata,
 * this card shows a button to navigate to the relevant page.
 * Used for: Agent Studio after agent creation, Vagas after job creation, etc.
 */
export function NavigationHintCard({ hint, className }: Props) {
  const handleNavigate = () => {
    window.dispatchEvent(new CustomEvent("lia:navigation-hint", {
      detail: { page: hint.page, hint: null },
    }))
  }

  return (
    <button
      onClick={handleNavigate}
      className={cn(
        "flex items-center gap-2 mt-2 px-3 py-2 rounded-md",
        "border border-wedo-cyan/30 bg-wedo-cyan/5",
        "text-sm text-wedo-cyan-text hover:bg-wedo-cyan/10",
        "transition-colors motion-reduce:transition-none",
        "",
        className
      )}
    >
      <span>Ir para {hint.page}</span>
      <ArrowRight className="w-3.5 h-3.5" />
    </button>
  )
}
