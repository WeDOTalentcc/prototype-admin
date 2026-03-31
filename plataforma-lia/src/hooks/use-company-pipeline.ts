// @ts-nocheck
/**
 * useCompanyPipeline
 *
 * Carrega o pipeline configurado da empresa via GET /api/backend-proxy/company-pipeline.
 * Retorna as etapas no formato interno do JobEditTab.
 *
 * Vue 3: useState → ref, useEffect([]) → onMounted
 */
import { useState, useEffect } from "react"
import { LIA_ASSISTED_STAGES, LIA_ASSISTED_STAGE_NAMES } from "@/lib/recruitment-stages"

export interface CompanyPipelineStageLocal {
  stageName: string
  order: number
  type: string
  stageCategory?: string
  name?: string
  isEditable?: boolean
  isRemovable?: boolean
  isReorderable?: boolean
  slaDays?: number
  defaultSlaDays?: number
  liaAssisted?: boolean
}

interface UseCompanyPipelineResult {
  pipeline: CompanyPipelineStageLocal[] | null
  loading: boolean
}

export function useCompanyPipeline(): UseCompanyPipelineResult {
  const [pipeline, setPipeline] = useState<CompanyPipelineStageLocal[] | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchPipeline() {
      try {
        const res = await fetch("/api/backend-proxy/company-pipeline")
        if (res.ok) {
          const data = await res.json()
          if (data.pipeline && Array.isArray(data.pipeline)) {
            setPipeline(
              data.pipeline
                .filter((s: Record<string, unknown>) => s.is_active !== false)
                .map((s: Record<string, unknown>, i: number) => ({
                  stageName: s.display_name || s.name,
                  order: i + 1,
                  type: "interview" as const,
                  name: s.name,
                  stageCategory: s.stage_category === "catalog" ? "default" : s.stage_category,
                  isEditable: s.stage_category !== "system",
                  isRemovable: s.stage_category === "custom",
                  isReorderable: s.stage_category !== "system",
                  slaDays: s.sla_hours ? Math.round(s.sla_hours / 24) : 3,
                  defaultSlaDays: s.sla_hours ? Math.round(s.sla_hours / 24) : 3,
                  liaAssisted:
                    LIA_ASSISTED_STAGES.includes(s.name) ||
                    LIA_ASSISTED_STAGE_NAMES.includes(s.display_name || ""),
                }))
            )
          }
        }
      } catch {
        // Fallback silencioso — componente usa constante local
      } finally {
        setLoading(false)
      }
    }
    fetchPipeline()
  }, [])

  return { pipeline, loading }
}
