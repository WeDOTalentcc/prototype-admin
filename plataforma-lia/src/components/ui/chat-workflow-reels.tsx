"use client"

import React, { useState, useRef, useEffect, useCallback, useMemo } from "react"
import {
  Briefcase, Search, UserCheck, Calendar, FileText,
  TrendingUp, ChevronRight, ChevronLeft, BarChart3,
  Sparkles, Settings
} from "lucide-react"
import { useTranslations } from 'next-intl'

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
  pulseStageId?: string
  color: {
    accent: string
    accentBg: string
    nodeBorder: string
    cardBorder: string
  }
  suggestions: WorkflowReelSuggestion[]
}

interface PipelinePulseData {
  stages: Array<{ macro_stage: string; count: number }>
  total: number
}

function usePipelinePulse() {
  const [pulse, setPulse] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetch("/api/backend-proxy/pipeline-pulse")
      .then((res) => (res.ok ? res.json() : null))
      .then((data: PipelinePulseData | null) => {
        if (cancelled || !data) return
        const map: Record<string, number> = {}
        for (const s of data.stages) {
          map[s.macro_stage] = s.count
        }
        setPulse(map)
      })
      .catch((err) => { console.warn('[chatWorkflowReels] pulse fetch failed', err) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  return { pulse, loading }
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
        title: "Usar modelo de vaga",
        description: "Comece a partir de um modelo existente",
        command: "Criar vaga a partir de template",
      },
    ],
  },
  {
    id: "sourcing",
    label: "Captação",
    shortLabel: "Captação",
    icon: Search,
    pulseStageId: "sourcing",
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
    pulseStageId: "triagem",
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
        description: "Modifique situação no funil",
        command: "Atualize status do candidato",
      },
    ],
  },
  {
    id: "entrevista",
    label: "Entrevista",
    shortLabel: "Entrevista",
    icon: Calendar,
    pulseStageId: "entrevista",
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
    pulseStageId: "oferta",
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
    shortLabel: "Contratação",
    icon: TrendingUp,
    pulseStageId: "contratacao",
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
    label: "Análises",
    shortLabel: "Análises",
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

const DOCK_MAX_SCALE = 1.4
const DOCK_NEIGHBOR_1_SCALE = 1.2
const DOCK_NEIGHBOR_2_SCALE = 1.1
const DOCK_INFLUENCE_RADIUS = 120
const DRAG_THRESHOLD = 5

function useDockMagnifier(containerRef: React.RefObject<HTMLDivElement | null>) {
  const mouseXRef = useRef<number | null>(null)
  const [mouseX, setMouseX] = useState<number | null>(null)
  const rafId = useRef<number>(0)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
    setPrefersReducedMotion(mq.matches)
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches)
    mq.addEventListener("change", handler)
    return () => mq.removeEventListener("change", handler)
  }, [])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (prefersReducedMotion) return
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return
    const x = e.clientX - rect.left + (containerRef.current?.scrollLeft ?? 0)
    mouseXRef.current = x
    if (!rafId.current) {
      rafId.current = requestAnimationFrame(() => {
        setMouseX(mouseXRef.current)
        rafId.current = 0
      })
    }
  }, [containerRef, prefersReducedMotion])

  const handleMouseLeave = useCallback(() => {
    mouseXRef.current = null
    if (rafId.current) {
      cancelAnimationFrame(rafId.current)
      rafId.current = 0
    }
    setMouseX(null)
  }, [])

  const getScale = useCallback((nodeIndex: number, nodeRefs: React.RefObject<(HTMLElement | null)[]>) => {
    if (mouseX === null || prefersReducedMotion) return 1
    const nodeEl = nodeRefs.current?.[nodeIndex]
    if (!nodeEl) return 1
    const nodeCenter = nodeEl.offsetLeft + nodeEl.offsetWidth / 2
    const distance = Math.abs(mouseX - nodeCenter)
    if (distance > DOCK_INFLUENCE_RADIUS) return 1

    const ratio = 1 - distance / DOCK_INFLUENCE_RADIUS
    const eased = Math.cos((1 - ratio) * Math.PI / 2)

    if (distance < DOCK_INFLUENCE_RADIUS * 0.33) {
      return 1 + (DOCK_MAX_SCALE - 1) * eased
    } else if (distance < DOCK_INFLUENCE_RADIUS * 0.66) {
      return 1 + (DOCK_NEIGHBOR_1_SCALE - 1) * eased
    } else {
      return 1 + (DOCK_NEIGHBOR_2_SCALE - 1) * eased
    }
  }, [mouseX, prefersReducedMotion])

  return { handleMouseMove, handleMouseLeave, getScale, isActive: mouseX !== null }
}

function useDragToScroll(scrollRef: React.RefObject<HTMLDivElement | null>) {
  const isDragging = useRef(false)
  const startX = useRef(0)
  const startScroll = useRef(0)
  const dragDistance = useRef(0)
  const [grabbing, setGrabbing] = useState(false)

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    const el = scrollRef.current
    if (!el) return
    isDragging.current = true
    dragDistance.current = 0
    startX.current = e.clientX
    startScroll.current = el.scrollLeft
  }, [scrollRef])

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return
      const el = scrollRef.current
      if (!el) return
      const dx = e.clientX - startX.current
      dragDistance.current = Math.abs(dx)
      if (dragDistance.current > DRAG_THRESHOLD) {
        setGrabbing(true)
        e.preventDefault()
        el.scrollLeft = startScroll.current - dx
      }
    }

    const onMouseUp = () => {
      isDragging.current = false
      setGrabbing(false)
    }

    window.addEventListener("mousemove", onMouseMove)
    window.addEventListener("mouseup", onMouseUp)
    return () => {
      window.removeEventListener("mousemove", onMouseMove)
      window.removeEventListener("mouseup", onMouseUp)
    }
  }, [scrollRef])

  const wasDragging = useCallback(() => {
    return dragDistance.current > DRAG_THRESHOLD
  }, [])

  return { onMouseDown, grabbing, wasDragging }
}

function safeTrans(t: (key: string) => string, key: string, fallback: string): string {
  const result = t(key)
  return result === key || result.startsWith("chat.") ? fallback : result
}

function useTranslatedStages(stages: WorkflowReelStage[], t: (key: string) => string): WorkflowReelStage[] {
  return useMemo(() => stages.map(stage => ({
    ...stage,
    label: safeTrans(t, `stages.${stage.id}.label`, stage.label),
    shortLabel: safeTrans(t, `stages.${stage.id}.shortLabel`, stage.shortLabel || stage.label),
    suggestions: stage.suggestions.map(s => ({
      ...s,
      title: safeTrans(t, `suggestions.${s.id}.title`, s.title),
      description: safeTrans(t, `suggestions.${s.id}.description`, s.description),
      command: safeTrans(t, `suggestions.${s.id}.command`, s.command),
    })),
  })), [stages, t])
}

export function ChatWorkflowReels({
  onSelect,
  compact = false,
  stages = RECRUITMENT_STAGES,
  utilityNodes = UTILITY_NODES,
}: ChatWorkflowReelsProps) {
  const t = useTranslations('chat')
  const translatedStages = useTranslatedStages(stages, t)
  const translatedUtility = useTranslatedStages(utilityNodes, t)
  const allNodes = [...translatedStages, ...translatedUtility]
  const nodesWithSuggestions = allNodes.filter((s) => s.suggestions.length > 0)
  const firstWithSuggestions = nodesWithSuggestions[0]?.id ?? null

  const { pulse } = usePipelinePulse()
  const [activeStageId, setActiveStageId] = useState<string | null>(firstWithSuggestions)
  const scrollRef = useRef<HTMLDivElement>(null)
  const nodeRefs = useRef<(HTMLElement | null)[]>([])
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)

  const activeStage = allNodes.find((s) => s.id === activeStageId) ?? null

  const { handleMouseMove, handleMouseLeave, getScale } = useDockMagnifier(scrollRef)
  const { onMouseDown, grabbing, wasDragging } = useDragToScroll(scrollRef)

  const handleNodeClick = (nodeId: string, hasSuggestions: boolean) => {
    if (wasDragging()) return
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

  const setNodeRef = useCallback((index: number) => (el: HTMLElement | null) => {
    nodeRefs.current[index] = el
  }, [])

  if (compact) {
    return (
      <CompactReels
        stages={translatedStages}
        utilityNodes={translatedUtility}
        onSelect={onSelect}
      />
    )
  }

  let nodeIndex = 0

  return (
    <div className="w-full space-y-5">
      <div className="relative" style={{ overflow: "visible" }}>
        {canScrollLeft && (
          <button
            onClick={() => scroll("left")}
            className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1 z-10 w-6 h-6 rounded-full flex items-center justify-center bg-lia-bg-primary/80 border border-lia-border-subtle shadow-sm hover:bg-lia-bg-tertiary transition-colors opacity-60 hover:opacity-100"
            aria-label={t("scrollLeft")}
          >
            <ChevronLeft className="w-3.5 h-3.5 text-lia-text-secondary" />
          </button>
        )}
        {canScrollRight && (
          <button
            onClick={() => scroll("right")}
            className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1 z-10 w-6 h-6 rounded-full flex items-center justify-center bg-lia-bg-primary/80 border border-lia-border-subtle shadow-sm hover:bg-lia-bg-tertiary transition-colors opacity-60 hover:opacity-100"
            aria-label={t("scrollRight")}
          >
            <ChevronRight className="w-3.5 h-3.5 text-lia-text-secondary" />
          </button>
        )}

        <div
          ref={scrollRef}
          className="overflow-x-auto scrollbar-none"
          style={{
            scrollbarWidth: "none",
            msOverflowStyle: "none",
            cursor: grabbing ? "grabbing" : "grab",
            clipPath: "inset(-30px 0 0 0)",
          }}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          onMouseDown={onMouseDown}
        >
          <div className="flex items-end gap-0 min-w-max px-1 pt-8 pb-2">
            {translatedStages.map((stage, idx) => {
              const currentIndex = nodeIndex++
              return (
                <React.Fragment key={stage.id}>
                  <StageNode
                    ref={setNodeRef(currentIndex)}
                    stage={stage}
                    isActive={activeStageId === stage.id}
                    pulseCount={stage.pulseStageId ? pulse[stage.pulseStageId] : undefined}
                    onClick={() => handleNodeClick(stage.id, stage.suggestions.length > 0)}
                    scale={getScale(currentIndex, nodeRefs)}
                  />
                  {idx < translatedStages.length - 1 && (
                    <div
                      className="h-px w-6 flex-shrink-0 transition-colors self-center"
                      style={{
                        backgroundColor: stage.suggestions.length > 0 && translatedStages[idx + 1].suggestions.length > 0
                          ? "var(--lia-border-default)"
                          : "var(--lia-border-subtle)",
                      }}
                    />
                  )}
                </React.Fragment>
              )
            })}

            {translatedUtility.length > 0 && (
              <>
                <div className="flex-shrink-0 w-px h-8 mx-3 bg-lia-border-subtle self-center" />
                {translatedUtility.map((node, idx) => {
                  const currentIndex = nodeIndex++
                  return (
                    <React.Fragment key={node.id}>
                      <StageNode
                        ref={setNodeRef(currentIndex)}
                        stage={node}
                        isActive={activeStageId === node.id}
                        onClick={() => handleNodeClick(node.id, node.suggestions.length > 0)}
                        scale={getScale(currentIndex, nodeRefs)}
                      />
                      {idx < translatedUtility.length - 1 && (
                        <div className="w-3 flex-shrink-0" />
                      )}
                    </React.Fragment>
                  )
                })}
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

const StageNode = React.forwardRef<
  HTMLButtonElement,
  {
    stage: WorkflowReelStage
    isActive: boolean
    pulseCount?: number
    onClick: () => void
    scale?: number
  }
>(function StageNode({ stage, isActive, pulseCount, onClick, scale = 1 }, ref) {
  const t = useTranslations('chat')
  const Icon = stage.icon
  const hasSuggestions = stage.suggestions.length > 0
  const showPulse = pulseCount !== undefined && pulseCount > 0

  const handlePulseClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    window.location.href = "/funil-de-talentos?tab=pipeline"
  }

  return (
    <button
      ref={ref}
      onClick={onClick}
      disabled={!hasSuggestions}
      className="flex flex-col items-center gap-1.5 group px-2 disabled:cursor-default origin-bottom motion-reduce:!transition-none"
      title={hasSuggestions ? t("suggestionCount", { label: stage.label, count: stage.suggestions.length }) : stage.label}
      style={{
        transform: scale !== 1 ? `scale(${scale})` : undefined,
        transition: "transform 0.15s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        willChange: scale !== 1 ? "transform" : "auto",
      }}
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
      {showPulse ? (
        <span
          className="text-xs font-bold cursor-pointer rounded-full px-1.5 py-0.5"
          style={{ backgroundColor: stage.color.accentBg, color: stage.color.accent }}
          onClick={handlePulseClick}
          title={t("pulseBadge", { count: pulseCount })}
        >
          {pulseCount}
        </span>
      ) : hasSuggestions ? (
        <span
          className="w-1 h-1 rounded-full transition-colors"
          style={{
            backgroundColor: stage.color.accent,
            opacity: isActive ? 1 : 0.5,
          }}
        />
      ) : null}
    </button>
  )
})

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
              className="w-full flex items-center gap-2.5 p-2.5 rounded-xl text-left border transition-colors"
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
