"use client"

import React, { useState } from "react"
import { ChevronDown, Target, ExternalLink } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { useToolSurface } from "@/contexts/ToolSurfaceContext"

interface CompetencyItem {
  skill: string
  contexto?: string
  block?: "technical" | "behavioral"
  trait?: string
}

interface WizardCompetencyCardProps {
  data: Record<string, unknown>
  onOpenPanel?: () => void
}

function BlockBadge({ block }: { block?: string }) {
  if (!block) return null
  const map: Record<string, { label: string; cls: string }> = {
    technical: { label: "Técnica", cls: "bg-wedo-cyan/10 text-wedo-cyan-text" },
    behavioral: { label: "Comportamental", cls: "bg-wedo-purple/10 text-wedo-purple-text" },
  }
  const b = map[block] ?? { label: block, cls: "bg-lia-bg-primary text-lia-text-secondary" }
  return (
    <span className={cn("text-[10px] px-1.5 py-0.5 rounded-full font-medium flex-shrink-0", b.cls)}>
      {b.label}
    </span>
  )
}

export function WizardCompetencyCard({ data, onOpenPanel }: WizardCompetencyCardProps) {
  const surface = useToolSurface()
  const [expanded, setExpanded] = useState(surface === "panel")

  const tree = (data.competency_tree as CompetencyItem[]) ?? []
  const seniority = (data.seniority_display as string) ?? (data.seniority as string) ?? null
  const distribution = data.distribution as { technical?: number; behavioral?: number } | undefined
  const screeningMode = data.screening_mode as string | undefined

  if (tree.length === 0) return null

  const techCount = tree.filter((c) => c.block === "technical").length
  const behavCount = tree.filter((c) => c.block === "behavioral").length
  const firstFour = tree.slice(0, 4)
  const extraItems = tree.slice(4)

  return (
    <div
      role="region"
      aria-label="Competências mapeadas"
      className={cn(
        "mt-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary",
        surface !== "panel" && "overflow-hidden",
      )}
    >
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-lia-interactive-hover transition-colors text-left"
      >
        <Target className="w-4 h-4 text-wedo-cyan flex-shrink-0" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-lia-text-primary">
            {tree.length} competências mapeadas
          </p>
          <p className="text-xs text-lia-text-secondary">
            {techCount} técnicas · {behavCount} comportamentais
            {seniority ? ` · ${seniority}` : ""}
          </p>
        </div>
        {screeningMode && (
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-lia-bg-primary border border-lia-border-subtle text-lia-text-secondary flex-shrink-0">
            {screeningMode}
          </span>
        )}
        <ChevronDown
          className={cn(
            "w-4 h-4 text-lia-text-muted flex-shrink-0 transition-transform",
            expanded && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>

      <div className="border-t border-lia-border-subtle divide-y divide-lia-border-subtle">
        {firstFour.map((c, i) => (
          <div key={i} className="flex items-start gap-2 px-3 py-2">
            <span className="text-xs text-lia-text-primary flex-1 min-w-0">
              {c.skill}
            </span>
            <BlockBadge block={c.block} />
          </div>
        ))}

        <AnimatePresence initial={false}>
          {expanded && extraItems.map((c, idx) => (
            <motion.div
              key={"extra-" + (idx + 4)}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
              className="overflow-hidden"
            >
              <div className="flex items-start gap-2 px-3 py-2 border-t border-lia-border-subtle">
                <span className="text-xs text-lia-text-primary flex-1 min-w-0">
                  {c.skill}
                </span>
                <BlockBadge block={c.block} />
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {!expanded && extraItems.length > 0 && surface !== "panel" && (
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="w-full px-3 py-2 text-xs text-wedo-cyan-text hover:bg-lia-interactive-hover transition-colors text-left"
          >
            Ver todas as {tree.length} competências
          </button>
        )}

        {onOpenPanel && (
          <div className="px-3 py-2">
            <button
              type="button"
              onClick={onOpenPanel}
              className="flex items-center gap-1.5 text-[11px] text-wedo-cyan-text hover:underline"
            >
              <ExternalLink className="w-3 h-3" aria-hidden="true" />
              Abrir no painel
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
