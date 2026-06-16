"use client"

import React, { useCallback, useEffect, useRef, useState } from "react"

export interface PipelineRailNode {
  key: string
  displayName: string
  color: string
  count: number
  Icon: React.ComponentType<{ className?: string; style?: React.CSSProperties; strokeWidth?: number }>
  isSelected: boolean
  onClick: () => void
  /**
   * Onda 2 F7 (2026-05-27) — pingo cyan no header da etapa.
   * - `agentDeployed`: existe pelo menos um agent acoplado a este stage (static dot)
   * - `agentRunning`: ha um agent EXECUTANDO neste stage AGORA (pulsing dot)
   *
   * Quando ambos truthy, pulsing ganha. Tooltip muda conforme estado.
   */
  agentDeployed?: boolean
  agentRunning?: boolean
}

export interface PipelineRailProps {
  nodes: PipelineRailNode[]
  emptyMessage?: React.ReactNode
}

const DOCK_MAX_SCALE = 1.4
const DOCK_NEIGHBOR_1_SCALE = 1.2
const DOCK_NEIGHBOR_2_SCALE = 1.1
const DOCK_INFLUENCE_RADIUS = 120

function hexToRgba(hex: string, alpha: number): string {
  const clean = hex.replace("#", "")
  const r = parseInt(clean.substring(0, 2), 16)
  const g = parseInt(clean.substring(2, 4), 16)
  const b = parseInt(clean.substring(4, 6), 16)
  if (isNaN(r) || isNaN(g) || isNaN(b)) return `rgba(99, 102, 241, ${alpha})`
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function useMagnifier(containerRef: React.RefObject<HTMLDivElement | null>) {
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
    if (distance < DOCK_INFLUENCE_RADIUS * 0.33) return 1 + (DOCK_MAX_SCALE - 1) * eased
    if (distance < DOCK_INFLUENCE_RADIUS * 0.66) return 1 + (DOCK_NEIGHBOR_1_SCALE - 1) * eased
    return 1 + (DOCK_NEIGHBOR_2_SCALE - 1) * eased
  }, [mouseX, prefersReducedMotion])

  return { handleMouseMove, handleMouseLeave, getScale }
}

export function PipelineRail({ nodes, emptyMessage }: PipelineRailProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const nodeRefs = useRef<(HTMLElement | null)[]>([])
  const { handleMouseMove, handleMouseLeave, getScale } = useMagnifier(scrollRef)

  if (nodes.length === 0) {
    return <>{emptyMessage}</>
  }

  return (
    <div
      ref={scrollRef}
      className="overflow-x-auto scrollbar-none"
      style={{
        scrollbarWidth: "none",
        msOverflowStyle: "none",
        clipPath: "inset(-30px 0 0 0)",
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div className="flex items-end gap-0 min-w-max px-1 pt-8 pb-2">
        {nodes.map((node, index) => {
          const isLast = index === nodes.length - 1
          const stageColor = node.color || "#2D2D2D"
          const Icon = node.Icon
          const scale = getScale(index, nodeRefs)

          return (
            <div key={node.key} className="flex items-center">
              <button
                ref={(el) => { nodeRefs.current[index] = el }}
                onClick={node.onClick}
                className="group flex flex-col items-center gap-1.5 px-3 cursor-pointer origin-bottom motion-reduce:!transition-none"
                style={{
                  transform: scale !== 1 ? `scale(${scale})` : undefined,
                  transition: "transform 0.15s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
                  willChange: scale !== 1 ? "transform" : "auto",
                }}
              >
                <div
                  className="relative w-10 h-10 rounded-full flex items-center justify-center transition-all duration-150 border-2"
                  style={{
                    backgroundColor: node.isSelected
                      ? stageColor
                      : node.count > 0
                      ? hexToRgba(stageColor, 0.08)
                      : "var(--lia-bg-tertiary)",
                    borderColor: node.isSelected
                      ? stageColor
                      : node.count > 0
                      ? stageColor
                      : "var(--lia-border-subtle)",
                    boxShadow: node.isSelected
                      ? `0 0 0 3px ${hexToRgba(stageColor, 0.08)}`
                      : undefined,
                  }}
                >
                  <Icon
                    className="w-4 h-4 transition-colors"
                    style={{
                      color: node.isSelected
                        ? "var(--lia-text-on-accent, #fff)"
                        : node.count > 0
                        ? stageColor
                        : "var(--lia-text-disabled)",
                    }}
                  />
                  {/* Onda 2 F7 — pingo cyan no canto top-right do node. Pulsing
                     quando agentRunning; static quando apenas deployed. */}
                  {(node.agentRunning || node.agentDeployed) && (
                    <span
                      className={`absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-wedo-cyan ring-2 ring-lia-bg-primary dark:ring-lia-bg-primary ${
                        node.agentRunning
                          ? "animate-agent-pulse motion-reduce:animate-none"
                          : ""
                      }`}
                      aria-label={
                        node.agentRunning
                          ? "Agente trabalhando agora nesta etapa"
                          : "Agente acoplado a esta etapa"
                      }
                      title={
                        node.agentRunning
                          ? "Agente trabalhando agora nesta etapa"
                          : "Agente acoplado a esta etapa"
                      }
                      role="img"
                    />
                  )}
                </div>

                <span
                  className="text-micro font-medium transition-colors whitespace-nowrap"
                  style={{
                    color: node.isSelected
                      ? stageColor
                      : node.count > 0
                      ? "var(--lia-text-primary)"
                      : "var(--lia-text-disabled)",
                  }}
                >
                  {node.displayName}
                </span>

                {node.count > 0 ? (
                  <span
                    className="text-micro font-bold rounded-full px-1.5 py-0.5"
                    style={{ backgroundColor: hexToRgba(stageColor, 0.08), color: stageColor }}
                  >
                    {node.count}
                  </span>
                ) : (
                  <span
                    className="w-1 h-1 rounded-full"
                    style={{ backgroundColor: stageColor, opacity: 0.3 }}
                  />
                )}
              </button>

              {!isLast && (
                <div
                  className="h-px w-6 flex-shrink-0 self-center -mt-6"
                  style={{ backgroundColor: "var(--lia-border-default)" }}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
