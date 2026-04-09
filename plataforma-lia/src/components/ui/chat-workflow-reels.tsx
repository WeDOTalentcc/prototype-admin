"use client"

import React, { useState, useRef, useEffect } from "react"
import {
  Briefcase, Search, UserCheck, Calendar, FileText,
  TrendingUp, ChevronRight, ChevronLeft
} from "lucide-react"

export interface WorkflowReelSuggestion {
  id: string
  title: string
  description: string
  command: string
}

export interface WorkflowReelStage {
  id: string
  label: string
  shortLabel: string
  icon: React.ElementType
  color: {
    accent: string
    accentBg: string
    nodeBorder: string
    cardBorder: string
  }
  suggestions: WorkflowReelSuggestion[]
}

const RECRUITMENT_STAGES: WorkflowReelStage[] = [
  {
    id: "definir-vaga",
    label: "Definir Vaga",
    shortLabel: "Vaga",
    icon: Briefcase,
    color: {
      accent: "var(--wedo-cyan, #60BED1)",
      accentBg: "rgba(96, 190, 209, 0.10)",
      nodeBorder: "var(--wedo-cyan, #60BED1)",
      cardBorder: "rgba(96, 190, 209, 0.25)",
    },
    suggestions: [
      {
        id: "create-job",
        title: "Criar nova vaga",
        description: "Configure requisitos com descrição detalhada",
        command: "Criar uma nova vaga",
      },
    ],
  },
  {
    id: "sourcing",
    label: "Sourcing",
    shortLabel: "Sourcing",
    icon: Search,
    color: {
      accent: "var(--wedo-green, #5DA47A)",
      accentBg: "rgba(93, 164, 122, 0.10)",
      nodeBorder: "var(--wedo-green, #5DA47A)",
      cardBorder: "rgba(93, 164, 122, 0.25)",
    },
    suggestions: [
      {
        id: "search-candidates",
        title: "Buscar candidatos",
        description: "Encontre perfis por skills ou experiência",
        command: "Buscar candidatos",
      },
      {
        id: "add-candidate",
        title: "Adicionar candidato",
        description: "Cadastre novo perfil no banco de talentos",
        command: "Adicione novo candidato",
      },
    ],
  },
  {
    id: "triagem",
    label: "Triagem",
    shortLabel: "Triagem",
    icon: UserCheck,
    color: {
      accent: "var(--wedo-green, #5DA47A)",
      accentBg: "rgba(93, 164, 122, 0.10)",
      nodeBorder: "var(--wedo-green, #5DA47A)",
      cardBorder: "rgba(93, 164, 122, 0.25)",
    },
    suggestions: [
      {
        id: "candidate-info",
        title: "Consultar candidato",
        description: "Obtenha histórico específico e completo",
        command: "Consulte informações sobre candidato",
      },
      {
        id: "update-status",
        title: "Atualizar status",
        description: "Modifique situação no pipeline",
        command: "Atualize status do candidato",
      },
    ],
  },
  {
    id: "entrevista",
    label: "Entrevista",
    shortLabel: "Entrevista",
    icon: Calendar,
    color: {
      accent: "var(--wedo-orange, #D19960)",
      accentBg: "rgba(209, 153, 96, 0.10)",
      nodeBorder: "var(--wedo-orange, #D19960)",
      cardBorder: "rgba(209, 153, 96, 0.25)",
    },
    suggestions: [
      {
        id: "reschedule-interview",
        title: "Reagendar entrevista",
        description: "Cancele horário e notifique participantes",
        command: "Reagende uma entrevista",
      },
    ],
  },
  {
    id: "oferta",
    label: "Oferta",
    shortLabel: "Oferta",
    icon: FileText,
    color: {
      accent: "var(--wedo-purple, #9860D1)",
      accentBg: "rgba(152, 96, 209, 0.10)",
      nodeBorder: "var(--wedo-purple, #9860D1)",
      cardBorder: "rgba(152, 96, 209, 0.25)",
    },
    suggestions: [],
  },
  {
    id: "contratacao",
    label: "Contratação",
    shortLabel: "Hire",
    icon: TrendingUp,
    color: {
      accent: "var(--wedo-purple, #9860D1)",
      accentBg: "rgba(152, 96, 209, 0.10)",
      nodeBorder: "var(--wedo-purple, #9860D1)",
      cardBorder: "rgba(152, 96, 209, 0.25)",
    },
    suggestions: [],
  },
]

interface ChatWorkflowReelsProps {
  onSelect: (command: string) => void
  compact?: boolean
  stages?: WorkflowReelStage[]
}

export function ChatWorkflowReels({
  onSelect,
  compact = false,
  stages = RECRUITMENT_STAGES,
}: ChatWorkflowReelsProps) {
  const stagesWithSuggestions = stages.filter((s) => s.suggestions.length > 0)
  const firstWithSuggestions = stagesWithSuggestions[0]?.id ?? null

  const [activeStageId, setActiveStageId] = useState<string | null>(firstWithSuggestions)
  const scrollRef = useRef<HTMLDivElement>(null)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)

  const activeStage = stages.find((s) => s.id === activeStageId) ?? null

  const updateScrollState = () => {
    const el = scrollRef.current
    if (!el) return
    setCanScrollLeft(el.scrollLeft > 4)
    setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 4)
  }

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    updateScrollState()
    el.addEventListener("scroll", updateScrollState, { passive: true })
    const ro = new ResizeObserver(updateScrollState)
    ro.observe(el)
    return () => {
      el.removeEventListener("scroll", updateScrollState)
      ro.disconnect()
    }
  }, [])

  const scroll = (dir: "left" | "right") => {
    const el = scrollRef.current
    if (!el) return
    el.scrollBy({ left: dir === "left" ? -160 : 160, behavior: "smooth" })
  }

  if (compact) {
    return (
      <CompactReels
        stages={stages}
        stagesWithSuggestions={stagesWithSuggestions}
        onSelect={onSelect}
      />
    )
  }

  return (
    <div className="w-full space-y-5">
      <div className="relative">
        {canScrollLeft && (
          <button
            onClick={() => scroll("left")}
            className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1 z-10 w-7 h-7 rounded-full flex items-center justify-center bg-lia-bg-primary border border-lia-border-subtle shadow-lia-sm hover:bg-lia-bg-tertiary transition-colors"
            aria-label="Scroll left"
          >
            <ChevronLeft className="w-4 h-4 text-lia-text-secondary" />
          </button>
        )}
        {canScrollRight && (
          <button
            onClick={() => scroll("right")}
            className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1 z-10 w-7 h-7 rounded-full flex items-center justify-center bg-lia-bg-primary border border-lia-border-subtle shadow-lia-sm hover:bg-lia-bg-tertiary transition-colors"
            aria-label="Scroll right"
          >
            <ChevronRight className="w-4 h-4 text-lia-text-secondary" />
          </button>
        )}

        <div
          ref={scrollRef}
          className="overflow-x-auto scrollbar-none pb-1"
          style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
        >
          <div className="flex items-center gap-0 min-w-max px-1 py-2">
            {stages.map((stage, idx) => {
              const Icon = stage.icon
              const hasSuggestions = stage.suggestions.length > 0
              const isActive = activeStageId === stage.id

              return (
                <React.Fragment key={stage.id}>
                  <button
                    onClick={() =>
                      setActiveStageId(isActive ? null : hasSuggestions ? stage.id : null)
                    }
                    disabled={!hasSuggestions}
                    className="flex flex-col items-center gap-1.5 group transition-all duration-150 px-2 disabled:cursor-default"
                    title={hasSuggestions ? `${stage.label} — ${stage.suggestions.length} sugestão` : stage.label}
                  >
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center transition-all duration-150 border-2"
                      style={{
                        backgroundColor: isActive
                          ? stage.color.accent
                          : hasSuggestions
                          ? stage.color.accentBg
                          : "var(--lia-bg-tertiary)",
                        borderColor: isActive
                          ? stage.color.accent
                          : hasSuggestions
                          ? stage.color.nodeBorder
                          : "var(--lia-border-subtle)",
                        boxShadow: isActive
                          ? `0 0 0 3px ${stage.color.accentBg}`
                          : undefined,
                      }}
                    >
                      <Icon
                        className="w-4 h-4 transition-colors"
                        style={{
                          color: isActive
                            ? "#fff"
                            : hasSuggestions
                            ? stage.color.accent
                            : "var(--lia-text-disabled)",
                        }}
                      />
                    </div>
                    <span
                      className="text-micro font-medium transition-colors whitespace-nowrap"
                      style={{
                        color: isActive
                          ? stage.color.accent
                          : hasSuggestions
                          ? "var(--lia-text-primary)"
                          : "var(--lia-text-disabled)",
                      }}
                    >
                      {stage.shortLabel}
                    </span>
                    {hasSuggestions && (
                      <span
                        className="w-1 h-1 rounded-full transition-colors"
                        style={{
                          backgroundColor: isActive
                            ? stage.color.accent
                            : stage.color.accent,
                          opacity: isActive ? 1 : 0.5,
                        }}
                      />
                    )}
                  </button>

                  {idx < stages.length - 1 && (
                    <div
                      className="h-px w-6 flex-shrink-0 transition-colors"
                      style={{
                        backgroundColor:
                          stagesWithSuggestions.indexOf(stage) >= 0 &&
                          stagesWithSuggestions.indexOf(stages[idx + 1]) >= 0
                            ? "var(--lia-border-default)"
                            : "var(--lia-border-subtle)",
                      }}
                    />
                  )}
                </React.Fragment>
              )
            })}
          </div>
        </div>
      </div>

      {activeStage && activeStage.suggestions.length > 0 && (
        <div className="animate-fade-in-up">
          <div className="flex flex-wrap gap-3">
            {activeStage.suggestions.map((suggestion) => (
              <button
                key={suggestion.id}
                onClick={() => onSelect(suggestion.command)}
                className="flex items-start gap-3 p-4 text-left rounded-xl bg-lia-bg-primary border transition-all duration-150 hover:-translate-y-0.5 group flex-1 min-w-[180px]"
                style={{
                  borderColor: activeStage.color.cardBorder,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = activeStage.color.nodeBorder
                  e.currentTarget.style.backgroundColor = activeStage.color.accentBg
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = activeStage.color.cardBorder
                  e.currentTarget.style.backgroundColor = "var(--lia-bg-primary)"
                }}
              >
                <div
                  className="rounded-lg p-2 flex-shrink-0"
                  style={{
                    backgroundColor: activeStage.color.accentBg,
                    color: activeStage.color.accent,
                  }}
                >
                  {React.createElement(activeStage.icon, { className: "w-4 h-4" })}
                </div>
                <div className="min-w-0">
                  <span className="text-[14px] font-semibold text-lia-text-primary block mb-0.5">
                    {suggestion.title}
                  </span>
                  <span className="text-xs leading-snug text-lia-text-secondary block">
                    {suggestion.description}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

    </div>
  )
}

function CompactReels({
  stages,
  stagesWithSuggestions,
  onSelect,
}: {
  stages: WorkflowReelStage[]
  stagesWithSuggestions: WorkflowReelStage[]
  onSelect: (command: string) => void
}) {
  const firstWithSuggestions = stagesWithSuggestions[0]?.id ?? null
  const [activeStageId, setActiveStageId] = useState<string | null>(firstWithSuggestions)
  const activeStage = stages.find((s) => s.id === activeStageId) ?? null

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1 overflow-x-auto scrollbar-none py-1" style={{ scrollbarWidth: "none" }}>
        {stages.map((stage, idx) => {
          const Icon = stage.icon
          const hasSuggestions = stage.suggestions.length > 0
          const isActive = activeStageId === stage.id

          return (
            <React.Fragment key={stage.id}>
              <button
                onClick={() => setActiveStageId(isActive ? null : hasSuggestions ? stage.id : null)}
                disabled={!hasSuggestions}
                className="flex-shrink-0 flex flex-col items-center gap-1 px-1 disabled:cursor-default"
                title={stage.label}
              >
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center border transition-colors"
                  style={{
                    backgroundColor: isActive
                      ? stage.color.accent
                      : hasSuggestions
                      ? stage.color.accentBg
                      : "var(--lia-bg-tertiary)",
                    borderColor: isActive
                      ? stage.color.accent
                      : hasSuggestions
                      ? stage.color.nodeBorder
                      : "var(--lia-border-subtle)",
                  }}
                >
                  <Icon
                    className="w-3 h-3"
                    style={{
                      color: isActive
                        ? "#fff"
                        : hasSuggestions
                        ? stage.color.accent
                        : "var(--lia-text-disabled)",
                    }}
                  />
                </div>
                <span
                  className="text-micro font-medium whitespace-nowrap"
                  style={{ color: hasSuggestions ? "var(--lia-text-secondary)" : "var(--lia-text-disabled)" }}
                >
                  {stage.shortLabel}
                </span>
              </button>
              {idx < stages.length - 1 && (
                <div className="h-px w-4 flex-shrink-0 bg-lia-border-subtle" />
              )}
            </React.Fragment>
          )
        })}
      </div>

      {activeStage && activeStage.suggestions.length > 0 && (
        <div className="space-y-1 animate-fade-in-up">
          {activeStage.suggestions.map((suggestion) => (
            <button
              key={suggestion.id}
              onClick={() => onSelect(suggestion.command)}
              className="w-full flex items-center gap-2.5 p-2.5 rounded-md text-left border transition-colors"
              style={{
                borderColor: activeStage.color.cardBorder,
                backgroundColor: "var(--lia-bg-primary)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = activeStage.color.accentBg
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "var(--lia-bg-primary)"
              }}
            >
              <div
                className="p-1.5 rounded-md flex-shrink-0"
                style={{ backgroundColor: activeStage.color.accentBg, color: activeStage.color.accent }}
              >
                {React.createElement(activeStage.icon, { className: "w-3.5 h-3.5" })}
              </div>
              <span className="text-base-ui font-medium text-lia-text-primary">{suggestion.title}</span>
            </button>
          ))}
        </div>
      )}

    </div>
  )
}
