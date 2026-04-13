
/**
 * GET /api/backend-proxy/pipeline-overview
 *
 * Proxy to the backend /api/v1/pipeline-overview endpoint which does efficient
 * single-query aggregation of candidate counts by stage across all active vacancies.
 *
 * Then enriches the response by merging with company pipeline stage metadata
 * (order, colour, icon) so the frontend can render a sorted stepper without
 * knowing internal stage keys.
 */
export const dynamic = "force-dynamic"

import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

interface PipelineStage {
  id: string
  name: string
  display_name: string
  stage_order: number
  color: string
  icon: string
  is_active: boolean
  is_final: boolean
  is_rejection: boolean
  stage_category: string
  action_behavior?: string
}

interface BackendStageItem {
  stage: string
  count: number
  candidates: Array<{
    vc_id: string
    vacancy_id: string
    candidate_id?: string
    name: string
    vacancy_title?: string | null
    sub_status?: string | null
    stage_entered_at?: string | null
    lia_score?: number | null
    match_percentage?: number | null
    wsi_score?: number | null
    lia_opinion_score?: number | null
    score_breakdown?: Record<string, unknown> | null
    technical_test_score?: number | null
    english_test_score?: number | null
    big_five_data?: Record<string, number> | null
  }>
}

export async function GET(request: NextRequest) {
  try {
    const authHeaders = getAuthHeaders(request)

    // Fetch both pipeline metadata and overview data in parallel
    const [pipelineRes, overviewRes] = await Promise.all([
      fetch(`${BACKEND_URL}/api/v1/recruitment-stages/company-pipeline`, {
        headers: authHeaders,
      }),
      fetch(`${BACKEND_URL}/api/v1/pipeline-overview?candidates_per_stage=100`, {
        headers: authHeaders,
      }),
    ])

    if (!pipelineRes.ok) {
      return NextResponse.json(
        { error: "Failed to fetch company pipeline", status: pipelineRes.status },
        { status: pipelineRes.status }
      )
    }
    if (!overviewRes.ok) {
      return NextResponse.json(
        { error: "Failed to fetch pipeline overview", status: overviewRes.status },
        { status: overviewRes.status }
      )
    }

    const pipelineRaw = await pipelineRes.json()
    const overviewRaw = await overviewRes.json()

    // Unwrap FastAPI envelope: {ok: true, data: {...}, meta: {}}
    const pipelineData = (pipelineRaw && 'ok' in pipelineRaw && pipelineRaw.data) ? pipelineRaw.data : pipelineRaw
    const overviewData = (overviewRaw && 'ok' in overviewRaw && overviewRaw.data) ? overviewRaw.data : overviewRaw

    const pipeline: PipelineStage[] = (pipelineData.pipeline || []).filter(
      (s: PipelineStage) => s.is_active !== false
    )

    const backendStages: BackendStageItem[] = overviewData.stages || []

    // Build a map from backend stage name → stage data
    const backendMap: Record<string, BackendStageItem> = {}
    for (const s of backendStages) {
      backendMap[s.stage.toLowerCase()] = s
    }

    // Merge pipeline metadata with backend counts; exclude only rejection stages —
    // final stages (e.g. Contratação/Hired) must remain visible in the panoramic flow.
    const knownStageNames = new Set<string>()

    const pipelineWithCounts = pipeline
      .filter((s: PipelineStage) => !s.is_rejection)
      .sort((a: PipelineStage, b: PipelineStage) => a.stage_order - b.stage_order)
      .map((s: PipelineStage) => {
        const key = s.name.toLowerCase()
        const displayKey = s.display_name.toLowerCase()
        const data = backendMap[key] || backendMap[displayKey]
        knownStageNames.add(key)
        knownStageNames.add(displayKey)
        return {
          ...s,
          count: data?.count ?? 0,
          candidates: data?.candidates ?? [],
        }
      })

    const INTERNAL_STAGE_NAMES = new Set([
      "initial",
      "pending_gate1",
      "pending_gate2",
      "new",
      "novo",
      "triagem",
      "entrevista rh",
      "entrevista técnica",
      "entrevista final",
      "proposta",
    ])

    let otherCandidates: typeof backendStages[0]["candidates"] = []
    let otherCount = 0

    for (const s of backendStages) {
      const key = s.stage.toLowerCase()
      if (!knownStageNames.has(key) && s.count > 0) {
        if (INTERNAL_STAGE_NAMES.has(key)) {
          console.log(
            `[pipeline-overview] Unmapped internal stage "${s.stage}" with ${s.count} candidates grouped under "Outros"`
          )
          otherCandidates = otherCandidates.concat(s.candidates)
          otherCount += s.count
        } else {
          console.log(
            `[pipeline-overview] Unmapped custom stage "${s.stage}" with ${s.count} candidates appended`
          )
          const customColorPalette = [
            "#5DA47A", "#60BED1", "#D19960", "#D17060",
            "#9860D1", "#6078D1", "#D1A960", "#8B5CF6",
            "#4DA6A0", "#C96B8A", "#7B8FD1", "#D18B60",
          ]
          let colorHash = 0
          for (let ci = 0; ci < key.length; ci++) {
            colorHash = ((colorHash << 5) - colorHash) + key.charCodeAt(ci)
            colorHash = colorHash & colorHash
          }
          const customColor = customColorPalette[Math.abs(colorHash) % customColorPalette.length]

          pipelineWithCounts.push({
            id: s.stage,
            name: s.stage,
            display_name: s.stage,
            stage_order: 9999,
            color: customColor,
            icon: "📋",
            is_active: true,
            is_final: false,
            is_rejection: false,
            stage_category: "custom",
            count: s.count,
            candidates: s.candidates,
          })
        }
      }
    }

    if (otherCount > 0) {
      pipelineWithCounts.push({
        id: "outros",
        name: "outros",
        display_name: "Outros",
        stage_order: 9998,
        color: "#8A8F98",
        icon: "📋",
        is_active: true,
        is_final: false,
        is_rejection: false,
        stage_category: "other",
        count: otherCount,
        candidates: otherCandidates,
      })
    }

    const totalCandidates = overviewData.total_candidates ?? 0

    return NextResponse.json({
      pipeline: pipelineWithCounts,
      total_candidates: totalCandidates,
    })
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error", details: String(error) },
      { status: 500 }
    )
  }
}
