"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import { ChevronDown, ChevronRight, Loader2 } from "lucide-react"
import { toast } from "sonner"
import { useCurrentCompany } from "@/hooks/company/use-current-company"

interface StageOption {
  name: string
  display_name: string
  stage_order: number
  color: string
  action_behavior?: string
  is_rejection?: boolean
  is_hired?: boolean
  sub_statuses?: Array<{ name: string; display_name: string }>
}

interface CandidateMoveDropdownProps {
  /** ID da vaga — usado para buscar o pipeline */
  jobId: string
  candidateId?: string
  vacancyCandidateId?: string
  currentStage?: string
  candidateName?: string
  /** Elemento que abre o dropdown ao ser clicado */
  trigger: React.ReactNode
  /** Direção do sub-flyout de sub-status: left (padrão) ou right */
  subFlyoutSide?: "left" | "right"
  onTransitionDone?: () => void
  onMoveRequested?: (toStage: string, subStatus?: string) => void
}

/**
 * Dropdown "Mover para" canônico — mesmo visual e lógica do PipelineDecisionBar.
 * Busca o pipeline da vaga diretamente para ter etapas e sub-status corretos.
 * Use em tabela, card kanban e qualquer outro lugar que precise de transição de etapa.
 */
export function CandidateMoveDropdown({
  jobId,
  candidateId,
  vacancyCandidateId,
  currentStage,
  candidateName,
  trigger,
  subFlyoutSide = "left",
  onTransitionDone,
  onMoveRequested,
}: CandidateMoveDropdownProps) {
  const { companyId } = useCurrentCompany()
  const [open, setOpen] = useState(false)
  const [pipeline, setPipeline] = useState<StageOption[]>([])
  const [hoveredStageIdx, setHoveredStageIdx] = useState<number | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const flyoutRef = useRef<HTMLDivElement>(null)

  const canonicalStage = currentStage || ""
  const canTransition = !!vacancyCandidateId && !!jobId

  const fetchPipeline = useCallback(async () => {
    if (!jobId) return
    try {
      const res = await fetch(`/api/backend-proxy/jobs/${jobId}/pipeline`)
      if (res.ok) {
        const data = await res.json()
        if (data.pipeline) {
          setPipeline(data.pipeline.filter((s: StageOption) => !s.is_hired))
        }
      }
    } catch { /* silent */ }
  }, [jobId])

  // Busca pipeline ao abrir pela primeira vez
  useEffect(() => {
    if (open && pipeline.length === 0) fetchPipeline()
  }, [open, pipeline.length, fetchPipeline])

  // Fecha ao clicar fora
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (flyoutRef.current && !flyoutRef.current.contains(e.target as Node)) {
        setOpen(false)
        setHoveredStageIdx(null)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const handleTransition = useCallback(async (toStage: string, subStatus?: string) => {
    setOpen(false)
    setHoveredStageIdx(null)
    if (onMoveRequested) {
      onMoveRequested(toStage, subStatus)
      return
    }
    if (!canTransition) {
      toast.error("Candidato sem vínculo com vaga", {
        description: "Não é possível mover este candidato.",
      })
      return
    }
    setIsProcessing(true)
    try {
      const body: Record<string, unknown> = {
        vacancy_candidate_id: vacancyCandidateId,
        from_stage: canonicalStage,
        to_stage: toStage,
        vacancy_id: jobId,
        action: "manual",
      }
      if (subStatus) body.sub_status = subStatus

      const res = await fetch("/api/backend-proxy/transition/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
      if (res.ok) {
        const data = await res.json()
        if (data.requires_approval) {
          toast.info("Aguardando aprovação", {
            description: `A transição de ${candidateName || "candidato"} requer aprovação.`,
          })
        } else if (data.success) {
          const targetStage = pipeline.find(s => s.name === toStage)
          const targetSubLabel = subStatus
            ? (targetStage?.sub_statuses?.find(s => s.name === subStatus)?.display_name || subStatus)
            : null
          toast.success("Candidato movido", {
            description: targetSubLabel
              ? `${candidateName || "Candidato"} → ${targetStage?.display_name || toStage} · ${targetSubLabel}`
              : `${candidateName || "Candidato"} → ${targetStage?.display_name || toStage}`,
          })
          onTransitionDone?.()
        } else {
          toast.error("Erro ao mover", { description: data.message || "Não foi possível mover." })
        }
      } else {
        toast.error("Erro ao mover", { description: "Falha ao executar transição." })
      }
    } catch {
      toast.error("Erro de conexão", { description: "Não foi possível conectar ao servidor." })
    } finally {
      setIsProcessing(false)
    }
  }, [canTransition, vacancyCandidateId, canonicalStage, jobId, candidateName, pipeline, onTransitionDone, onMoveRequested])

  const stagesFiltered = pipeline.filter(s => {
    const sName = s.name.toLowerCase()
    const cName = canonicalStage.toLowerCase()
    return sName !== cName && s.display_name?.toLowerCase() !== cName
  })

  return (
    <div className="relative inline-flex" ref={flyoutRef}>
      {/* Trigger customizável */}
      <div
        onClick={(e) => {
          e.stopPropagation()
          if (!isProcessing) setOpen(v => !v)
        }}
        className="cursor-pointer"
      >
        {isProcessing
          ? <span className="flex items-center gap-1 text-micro text-lia-text-secondary"><Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />Movendo...</span>
          : trigger}
      </div>

      {/* Flyout principal */}
      {open && (
        <div className="absolute top-full right-0 mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl shadow-lg z-[60] min-w-[210px] py-1 max-h-80 overflow-y-auto">
          {stagesFiltered.length === 0 && (
            <p className="px-3 py-2 text-micro text-lia-text-tertiary">Carregando etapas…</p>
          )}
          {stagesFiltered.map((stage, idx) => (
            <div
              key={stage.name}
              className="relative"
              onMouseEnter={() => setHoveredStageIdx(idx)}
              onMouseLeave={() => setHoveredStageIdx(null)}
            >
              <button
                onClick={() => {
                  if (!stage.sub_statuses?.length) handleTransition(stage.name)
                }}
                disabled={!canTransition}
                className={[
                  "w-full text-left px-3 py-1.5 text-micro text-lia-text-secondary",
                  "hover:bg-lia-interactive-hover transition-colors flex items-center gap-2",
                  !canTransition ? "opacity-40 cursor-not-allowed" : "",
                ].join(" ")}
              >
                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: stage.color }} />
                <span className="flex-1">{stage.display_name}</span>
                {!!stage.sub_statuses?.length && (
                  <ChevronRight className="w-3 h-3 text-lia-text-tertiary" />
                )}
              </button>

              {/* Sub-status nested flyout */}
              {hoveredStageIdx === idx && !!stage.sub_statuses?.length && (
                <div
                  className={[
                    "absolute top-0 bg-lia-bg-primary border border-lia-border-subtle rounded-xl shadow-lg z-[70] min-w-[230px] py-1 max-h-64 overflow-y-auto",
                    subFlyoutSide === "left" ? "right-full mr-0.5" : "left-full ml-0.5",
                  ].join(" ")}
                >
                  <button
                    onClick={() => handleTransition(stage.name)}
                    className="w-full text-left px-3 py-1.5 text-micro text-lia-text-tertiary hover:bg-lia-interactive-hover italic transition-colors"
                  >
                    Mover sem sub-status
                  </button>
                  <div className="border-t border-lia-border-subtle my-0.5" />
                  {stage.sub_statuses.map(sub => (
                    <button
                      key={sub.name}
                      onClick={() => handleTransition(stage.name, sub.name)}
                      className="w-full text-left px-3 py-1.5 text-micro text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors"
                    >
                      {sub.display_name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
          {!canTransition && stagesFiltered.length > 0 && (
            <p className="px-3 py-2 text-micro text-lia-text-tertiary border-t border-lia-border-subtle mt-0.5">
              Candidato não vinculado a esta vaga
            </p>
          )}
        </div>
      )}
    </div>
  )
}
