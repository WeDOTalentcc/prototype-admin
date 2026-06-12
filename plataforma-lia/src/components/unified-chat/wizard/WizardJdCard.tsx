"use client"

import React, { useState } from "react"
import { ChevronDown, FileText, ExternalLink } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { useToolSurface } from "@/contexts/ToolSurfaceContext"

interface WizardJdCardProps {
  data: Record<string, unknown>
  onOpenPanel?: () => void
}

/**
 * WizardJdCard — card inline no chat para stage .
 * Compacto por default, expande ao clicar para mostrar detalhes da JD enriquecida.
 * Tokens DS LIA v4.2.1 (sem cores hardcoded).
 * F4: accordion AnimatePresence com height animado.
 */
export function WizardJdCard({ data, onOpenPanel }: WizardJdCardProps) {
  const [expanded, setExpanded] = useState(false)

  const enriched = data.jd_enriched as Record<string, unknown> | undefined
  const score = (data.quality_score as number) ?? 0
  const title = (enriched?.titulo_padronizado as string) ?? "Descrição da vaga"
  const seniority = (enriched?.senioridade_confirmada as string) ?? ""
  const aboutRole = (enriched?.about_role as string) ?? ""
  const responsibilities = (enriched?.responsabilidades as string[]) ?? []
  const skills = (enriched?.skills_obrigatorias as Array<{ skill: string }>) ?? []

  const scoreColor =
    score >= 70
      ? "text-status-success"
      : score >= 50
        ? "text-wedo-cyan"
        : "text-status-warning"

  const surface = useToolSurface()

  if (!enriched) return null

  return (
    <div
      role="region"
      aria-label="Descrição da vaga enriquecida"
      className={cn("mt-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary", surface !== 'panel' && "overflow-hidden")}
    >
      {/* Header — sempre visível */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-lia-interactive-hover transition-colors text-left"
      >
        <FileText className="w-4 h-4 text-wedo-cyan flex-shrink-0" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-lia-text-primary truncate">{title}</p>
          {seniority && (
            <p className="text-xs text-lia-text-secondary">{seniority}</p>
          )}
        </div>
        {score > 0 && (
          <span className={cn("text-xs font-medium flex-shrink-0", scoreColor)}>
            {score}/100
          </span>
        )}
        <ChevronDown
          className={cn(
            "w-4 h-4 text-lia-text-disabled flex-shrink-0 transition-transform",
            expanded && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>

      {/* Conteúdo expandido — accordion animado */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="jd-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18, ease: "easeInOut" }}
            className="overflow-hidden border-t border-lia-border-subtle px-3 py-3 space-y-3"
          >
            {aboutRole && (
              <p className="text-xs text-lia-text-secondary leading-relaxed line-clamp-4">
                {aboutRole}
              </p>
            )}

            {responsibilities.length > 0 && (
              <div>
                <p className="text-[11px] font-medium text-lia-text-tertiary uppercase tracking-wide mb-1.5">
                  Responsabilidades ({responsibilities.length})
                </p>
                <ul className="space-y-1">
                  {responsibilities.slice(0, 5).map((r, i) => (
                    <li
                      key={i}
                      className="text-xs text-lia-text-secondary flex items-start gap-1.5"
                    >
                      <span className="text-wedo-cyan mt-0.5 flex-shrink-0" aria-hidden="true">
                        ·
                      </span>
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {skills.length > 0 && (
              <div>
                <p className="text-[11px] font-medium text-lia-text-tertiary uppercase tracking-wide mb-1.5">
                  Skills ({skills.length})
                </p>
                <div className="flex flex-wrap gap-1">
                  {skills.map((s, i) => (
                    <span
                      key={i}
                      className="text-[11px] px-2 py-0.5 rounded bg-lia-bg-primary border border-lia-border-subtle text-lia-text-secondary"
                    >
                      {s.skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {onOpenPanel && (
              <button
                type="button"
                onClick={onOpenPanel}
                className="flex items-center gap-1.5 text-[11px] text-wedo-cyan hover:underline"
              >
                <ExternalLink className="w-3 h-3" aria-hidden="true" />
                Abrir no painel
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
