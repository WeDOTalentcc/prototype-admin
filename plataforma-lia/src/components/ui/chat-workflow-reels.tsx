"use client"

import React, { useState, useRef, useEffect } from "react"
import {
  Briefcase, Search, UserCheck, Calendar, FileText,
  TrendingUp, ChevronRight, ChevronLeft, BarChart3,
  Sparkles, Settings
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
      {
        id: "job-template",
        title: "Usar template de vaga",
        description: "Comece a partir de um modelo existente",
        command: "Criar vaga a partir de template",
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
      {
        id: "talent-pool",
        title: "Banco de talentos",
        description: "Gerencie pools e short lists de candidatos",
        command: "Mostrar meus bancos de talentos",
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
        id: "schedule-interview",
        title: "Agendar entrevista",
        description: "Marque horário e notifique participantes",
        command: "Agendar uma entrevista",
      },
      {
        id: "reschedule-interview",
        title: "Reagendar entrevista",
        description: "Altere horário de entrevista existente",
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
    suggestions: [
      {
        id: "send-offer",
        title: "Enviar proposta",
        description: "Gere e envie proposta salarial ao candidato",
        command: "Enviar proposta para candidato",
      },
      {
        id: "compare-candidates",
        title: "Comparar finalistas",
        description: "Análise lado a lado dos candidatos finais",
        command: "Comparar candidatos finalistas",
      },
    ],
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
    suggestions: [
      {
        id: "register-hire",
        title: "Registrar contratação",
        description: "Finalize o processo e atualize o status",
        command: "Registrar contratação de candidato",
      },
      {
        id: "close-vacancy",
        title: "Encerrar vaga",
        description: "Feche a vaga e notifique candidatos",
        command: "Encerrar vaga",
      },
    ],
  },
]

const UTILITY_NODES: WorkflowReelStage[] = [
  {
    id: "analytics",
    label: "Analytics",
    shortLabel: "Analytics",
    icon: BarChart3,
    color: {
      accent: "var(--wedo-amber, #D1A960)",
      accentBg: "rgba(209, 169, 96, 0.10)",
      nodeBorder: "var(--wedo-amber, #D1A960)",
      cardBorder: "rgba(209, 169, 96, 0.25)",
    },
    suggestions: [
      {
        id: "job-report",
        title: "Relatório da vaga",
        description: "Métricas e status do processo seletivo",
        command: "Gerar relatório da vaga",
      },
      {
        id: "daily-briefing",
        title: "Briefing diário",
        description: "Resumo do dia com alertas e pendências",
        command: "Me dê o briefing de hoje",
      },
      {
        id: "hiring-predictions",
        title: "Previsões",
        description: "Estimativas de prazo e conversão do funil",
        command: "Mostrar previsões de contratação",
      },
    ],
  },
  {
    id: "ia-automacoes",
    label: "IA & Automações",
    shortLabel: "IA",
    icon: Sparkles,
    color: {
      accent: "var(--wedo-cyan, #60BED1)",
      accentBg: "rgba(96, 190, 209, 0.10)",
      nodeBorder: "var(--wedo-cyan, #60BED1)",
      cardBorder: "rgba(96, 190, 209, 0.25)",
    },
    suggestions: [
      {
        id: "configure-automations",
        title: "Configurar automações",
        description: "Regras automáticas de triagem e transição",
        command: "Configurar automações de recrutamento",
      },
      {
        id: "wsi-screening",
        title: "Triagem WSI",
        description: "Avaliação inteligente com metodologia WSI",
        command: "Iniciar triagem WSI para candidatos",
      },
      {
        id: "ai-suggestions",
        title: "Sugestões da LIA",
        description: "Recomendações baseadas no histórico",
        command: "O que você sugere para minhas vagas?",
      },
    ],
  },
  {
    id: "configuracoes",
    label: "Configurações",
    shortLabel: "Config",
    icon: Settings,
    color: {
      accent: "var(--lia-text-secondary, #8A8F98)",
      accentBg: "rgba(138, 143, 152, 0.10)",
      nodeBorder: "var(--lia-text-secondary, #8A8F98)",
      cardBorder: "rgba(138, 143, 152, 0.25)",
    },
    suggestions: [
      {
        id: "ai-credits",
        title: "Créditos IA",
        description: "Consulte saldo e consumo de créditos",
        command: "Verificar meus créditos de IA",
      },
      {
        id: "hiring-policy",
        title: "Política de contratação",
        description: "Ajuste regras e nível de automação",
        command: "Configurar política de contratação",
      },
      {
        id: "email-templates",
        title: "Templates de email",
        description: "Gerencie modelos de comunicação",
        command: "Gerenciar templates de email",
      },
    ],
  },
]

interface ChatWorkflowReelsProps {
  onSelect: (command: string) => void
  compact?: boolean
  stages?: WorkflowReelStage[]
  utilityNodes?: WorkflowReelStage[]
}

export function ChatWorkflowReels({
  onSelect,
  compact = false,
  stages = RECRUITMENT_STAGES,
  utilityNodes = UTILITY_NODES,
}: ChatWorkflowReelsProps) {
  const allNodes = [...stages, ...utilityNodes]
  const nodesWithSuggestions = allNodes.filter((s) => s.suggestions.length > 0)
  const firstWithSuggestions = nodesWithSuggestions[0]?.id ?? null

  const [activeStageId, setActiveStageId] = useState<string | null>(firstWithSuggestions)
  const scrollRef = useRef<HTMLDivElement>(null)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)

  const activeStage = allNodes.find((s) => s.id === activeStageId) ?? null

  const handleNodeClick = (nodeId: string, hasSuggestions: boolean) => {
    if (!hasSuggestions) return
    setActiveStageId(activeStageId === nodeId ? null : nodeId)
  }

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
        utilityNodes={utilityNodes}
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
            {stages.map((stage, idx) => (
              <React.Fragment key={stage.id}>
                <StageNode
                  stage={stage}
                  isActive={activeStageId === stage.id}
                  onClick={() => handleNodeClick(stage.id, stage.suggestions.length > 0)}
                />
                {idx < stages.length - 1 && (
                  <div
                    className="h-px w-6 flex-shrink-0 transition-colors"
                    style={{
                      backgroundColor: stage.suggestions.length > 0 && stages[idx + 1].suggestions.length > 0
                        ? "var(--lia-border-default)"
                        : "var(--lia-border-subtle)",
                    }}
                  />
                )}
              </React.Fragment>
            ))}

            {utilityNodes.length > 0 && (
              <>
                <div className="flex-shrink-0 w-px h-8 mx-3 bg-lia-border-subtle" />
                {utilityNodes.map((node, idx) => (
                  <React.Fragment key={node.id}>
                    <StageNode
                      stage={node}
                      isActive={activeStageId === node.id}
                      onClick={() => handleNodeClick(node.id, node.suggestions.length > 0)}
                    />
                    {idx < utilityNodes.length - 1 && (
                      <div className="w-3 flex-shrink-0" />
                    )}
                  </React.Fragment>
                ))}
              </>
            )}
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

function StageNode({
  stage,
  isActive,
  onClick,
}: {
  stage: WorkflowReelStage
  isActive: boolean
  onClick: () => void
}) {
  const Icon = stage.icon
  const hasSuggestions = stage.suggestions.length > 0

  return (
    <button
      onClick={onClick}
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
              ? "var(--lia-text-on-accent, #fff)"
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
            backgroundColor: stage.color.accent,
            opacity: isActive ? 1 : 0.5,
          }}
        />
      )}
    </button>
  )
}

function CompactReels({
  stages,
  utilityNodes,
  onSelect,
}: {
  stages: WorkflowReelStage[]
  utilityNodes: WorkflowReelStage[]
  onSelect: (command: string) => void
}) {
  const allNodes = [...stages, ...utilityNodes]
  const nodesWithSuggestions = allNodes.filter((s) => s.suggestions.length > 0)
  const firstWithSuggestions = nodesWithSuggestions[0]?.id ?? null
  const [activeStageId, setActiveStageId] = useState<string | null>(firstWithSuggestions)
  const activeStage = allNodes.find((s) => s.id === activeStageId) ?? null

  const handleNodeClick = (nodeId: string, hasSuggestions: boolean) => {
    if (!hasSuggestions) return
    setActiveStageId(activeStageId === nodeId ? null : nodeId)
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1 overflow-x-auto scrollbar-none py-1" style={{ scrollbarWidth: "none" }}>
        {stages.map((stage, idx) => (
          <React.Fragment key={stage.id}>
            <CompactNode
              stage={stage}
              isActive={activeStageId === stage.id}
              onClick={() => handleNodeClick(stage.id, stage.suggestions.length > 0)}
            />
            {idx < stages.length - 1 && (
              <div className="h-px w-4 flex-shrink-0 bg-lia-border-subtle" />
            )}
          </React.Fragment>
        ))}

        {utilityNodes.length > 0 && (
          <>
            <div className="flex-shrink-0 w-px h-5 mx-1.5 bg-lia-border-subtle" />
            {utilityNodes.map((node, idx) => (
              <React.Fragment key={node.id}>
                <CompactNode
                  stage={node}
                  isActive={activeStageId === node.id}
                  onClick={() => handleNodeClick(node.id, node.suggestions.length > 0)}
                />
                {idx < utilityNodes.length - 1 && (
                  <div className="w-1 flex-shrink-0" />
                )}
              </React.Fragment>
            ))}
          </>
        )}
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

function CompactNode({
  stage,
  isActive,
  onClick,
}: {
  stage: WorkflowReelStage
  isActive: boolean
  onClick: () => void
}) {
  const Icon = stage.icon
  const hasSuggestions = stage.suggestions.length > 0

  return (
    <button
      onClick={onClick}
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
              ? "var(--lia-text-on-accent, #fff)"
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
  )
}
