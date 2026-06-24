"use client"

import React, { useState } from "react"
import { Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import type { EnrichedJD } from "./useJDEvaluation"
import { useAiPersona } from "@/hooks/company/use-ai-persona"

interface JDEvalResultsPanelProps {
  description?: string
  responsibilities: string[]
  technicalSkills: string[]
  behavioralCompetencies: string[]
  enrichedJd?: EnrichedJD
}

export const JDEvalResultsPanel = React.memo(function JDEvalResultsPanel({
  description,
  responsibilities,
  technicalSkills,
  behavioralCompetencies,
  enrichedJd,
}: JDEvalResultsPanelProps) {
  const [showFullDescription, setShowFullDescription] = useState(false)
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"

  return (
    <div className="grid grid-cols-2 gap-4 pt-2">
      <div className="space-y-3">
        <span className="text-xs font-semibold text-lia-text-primary uppercase tracking-wide block">DESCRIÇÃO DO CLIENTE</span>
        <div className="border border-lia-border-subtle rounded-xl p-3 bg-lia-bg-secondary/30 space-y-3">

        {description && (
          <div>
            <p
              className={cn(
                "text-xs text-lia-text-secondary leading-relaxed",
                !showFullDescription && "line-clamp-4"
              )}
            >
              {description}
            </p>
            {description.length > 200 && (
              <button
                onClick={() => setShowFullDescription(!showFullDescription)}
                className="text-micro text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-inverse mt-1 underline"
              >
                {showFullDescription ? "ver menos" : "ver mais"}
              </button>
            )}
          </div>
        )}

        {responsibilities.length > 0 && (
          <div>
            <span className="text-micro font-semibold text-lia-text-primary uppercase tracking-wide block mb-1">Responsabilidades</span>
            <ul className="space-y-0.5">
              {responsibilities.map((item, idx) => (
                <li key={`resp-${idx}`} className="flex items-start gap-1.5">
                  <span className="text-xs text-lia-text-secondary mt-0.5 shrink-0">•</span>
                  <span className="text-xs text-lia-text-secondary leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {technicalSkills.length > 0 && (
          <div>
            <span className="text-micro font-semibold text-lia-text-primary uppercase tracking-wide block mb-1">Competências Técnicas</span>
            <div className="flex flex-wrap gap-1.5">
              {technicalSkills.map((skill) => (
                <span key={skill} className="px-2 py-0.5 text-micro rounded-full bg-lia-bg-tertiary text-lia-text-secondary">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {behavioralCompetencies.length > 0 && (
          <div>
            <span className="text-micro font-semibold text-lia-text-primary uppercase tracking-wide block mb-1">Competências Comportamentais</span>
            <div className="flex flex-wrap gap-1.5">
              {behavioralCompetencies.map((comp) => (
                <span key={comp} className="px-2 py-0.5 text-micro rounded-full bg-lia-bg-tertiary text-lia-text-secondary">
                  {comp}
                </span>
              ))}
            </div>
          </div>
        )}

        </div>
      </div>

      <div className="space-y-3">
        <span className="text-xs font-semibold uppercase tracking-wide block">{`DESCRIÇÃO ENRIQUECIDA (${personaName})`}</span>

        {enrichedJd && (enrichedJd.generated_jd_text || enrichedJd.description) ? (
          <div className="border rounded-xl p-3 space-y-3 border-wedo-cyan/20 bg-wedo-cyan/[.02]">
            <p className="text-xs text-lia-text-secondary leading-relaxed whitespace-pre-wrap">
              {enrichedJd.generated_jd_text || enrichedJd.description}
            </p>

            {enrichedJd.updated_at && (
              <span className="inline-block px-2.5 py-0.5 text-micro rounded-full bg-wedo-cyan/[.08]">
                Gerado em {new Date(enrichedJd.updated_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })}
              </span>
            )}

            {enrichedJd.responsibilities && enrichedJd.responsibilities.length > 0 && (
              <div>
                <span className="text-micro font-semibold uppercase tracking-wide block mb-1">Responsabilidades</span>
                <ul className="space-y-0.5">
                  {enrichedJd.responsibilities.map((item, idx) => (
                    <li key={`resp-${idx}`} className="flex items-start gap-1.5">
                      <span className="text-xs mt-0.5 shrink-0 text-lia-text-secondary">•</span>
                      <span className="text-xs text-lia-text-secondary leading-relaxed">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {enrichedJd.technical_skills && enrichedJd.technical_skills.length > 0 && (
              <div>
                <span className="text-micro font-semibold uppercase tracking-wide block mb-1">Competências Técnicas</span>
                <div className="flex flex-wrap gap-1.5">
                  {enrichedJd.technical_skills.map((skill) => (
                    <span key={skill} className="px-2 py-0.5 text-micro rounded-full bg-wedo-cyan/10">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {enrichedJd.behavioral_competencies && enrichedJd.behavioral_competencies.length > 0 && (
              <div>
                <span className="text-micro font-semibold uppercase tracking-wide block mb-1">Competências Comportamentais</span>
                <div className="flex flex-wrap gap-1.5">
                  {enrichedJd.behavioral_competencies.map((comp) => (
                    <span key={comp} className="px-2 py-0.5 text-micro rounded-full bg-wedo-cyan/10">
                      {comp}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="border rounded-xl p-3 border-wedo-cyan/15 bg-wedo-cyan/[.02]">
            <div className="flex flex-col items-center justify-center py-6">
              <Brain className="h-8 w-8 mb-2 text-wedo-cyan opacity-40" />
              <p className="text-xs text-lia-text-muted text-center leading-relaxed">
                Nenhum JD enriquecido gerado ainda.<br />
                Clique em Editar Descrição para gerar.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
})

export default JDEvalResultsPanel
