"use client"

import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { CheckCircle2, XCircle, CircleDashed, AlertCircle, Target } from "lucide-react"
import { CANDIDATE_AI_QUERY_KEYS } from "@/hooks/candidates/candidate-ai-query-keys"

// Matriz de qualificação estilo LinkedIn: avaliação por critério com proveniência.
// 2 modos: 'grouped' (vaga -> Obrigatórios/Desejáveis) e 'flat' (busca -> lista única
// que explica o Match score).

export type CriterionStatus = "met" | "partial" | "not_met" | "unknown"
export type CriterionGroup = "must_have" | "preferred" | "criteria"
export type CriterionProvenance =
  | "resume" | "profile" | "screening" | "wsi" | "eligibility" | "none"

export interface MatrixCriterion {
  id: string
  label: string
  group: CriterionGroup
  status: CriterionStatus
  explanation?: string
  provenance?: CriterionProvenance
  is_inference?: boolean
}

export interface QualificationMatrixData {
  mode: "grouped" | "flat"
  criteria: MatrixCriterion[]
  met_count: number
  total_count: number
  must_have_met?: number
  must_have_total?: number
  overall_label?: string
  degraded?: boolean
  degraded_reason?: string | null
}

interface QualificationMatrixCardProps {
  candidateId: string
  companyId: string
  /** Matriz já disponível (modo vaga, vinda do parecer salvo). */
  matrix?: QualificationMatrixData | null
  /** Critérios da busca — quando presente (e sem matrix), busca on-the-fly. */
  searchCriteria?: Record<string, unknown> | null
  /** ID da vaga — quando presente (e sem matrix e sem searchCriteria), deriva on-the-fly. */
  jobId?: string | null
}

const PROVENANCE_LABEL: Record<CriterionProvenance, string> = {
  resume: "com base no currículo",
  profile: "com base no perfil",
  screening: "com base na triagem",
  eligibility: "com base na triagem",
  wsi: "com base no WSI",
  none: "",
}

function StatusIcon({ status }: { status: CriterionStatus }) {
  if (status === "met") return <CheckCircle2 className="h-4 w-4 text-status-success flex-shrink-0" />
  if (status === "partial") return <AlertCircle className="h-4 w-4 text-status-warning flex-shrink-0" />
  if (status === "not_met") return <XCircle className="h-4 w-4 text-status-error flex-shrink-0" />
  return <CircleDashed className="h-4 w-4 text-lia-text-secondary flex-shrink-0" />
}

function CriterionRow({ c }: { c: MatrixCriterion }) {
  const provenance = c.provenance ? PROVENANCE_LABEL[c.provenance] : ""
  return (
    <div className="flex items-start gap-2 py-1.5">
      <StatusIcon status={c.status} />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-lia-text-primary">{c.label}</p>
        {c.explanation ? (
          <p className="text-micro text-lia-text-secondary leading-relaxed">{c.explanation}</p>
        ) : null}
        {provenance ? (
          <p className="text-micro text-lia-text-muted italic mt-0.5">{provenance}</p>
        ) : null}
      </div>
    </div>
  )
}

function Section({ title, items }: { title: string; items: MatrixCriterion[] }) {
  if (items.length === 0) return null
  return (
    <div className="space-y-0.5">
      <p className="text-micro font-semibold uppercase tracking-wide text-lia-text-secondary mb-1">
        {title}
      </p>
      {items.map((c) => (
        <CriterionRow key={c.id} c={c} />
      ))}
    </div>
  )
}

function MatrixBody({ matrix }: { matrix: QualificationMatrixData }) {
  const label = matrix.overall_label || `Atende ${matrix.met_count}/${matrix.total_count} critérios`
  const mustHave = matrix.criteria.filter((c) => c.group === "must_have")
  const preferred = matrix.criteria.filter((c) => c.group === "preferred")
  const flat = matrix.criteria.filter((c) => c.group === "criteria")

  return (
    <Card className="bg-lia-bg-primary border border-lia-border-subtle">
      <CardHeader className="py-2 px-3">
        <div className="flex items-center gap-1.5">
          <div className="p-0.5 rounded-xl bg-lia-bg-tertiary">
            <Target className="w-3.5 h-3.5 text-wedo-cyan" />
          </div>
          <CardTitle className="text-xs font-semibold text-lia-text-primary">{label}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="px-3 pb-3 space-y-3">
        {matrix.mode === "grouped" ? (
          <>
            <Section title="Obrigatórios" items={mustHave} />
            <Section title="Desejáveis" items={preferred} />
          </>
        ) : (
          <Section title="Critérios da busca" items={flat.length ? flat : matrix.criteria} />
        )}
        {matrix.degraded ? (
          <p className="text-micro text-status-warning">
            Avaliação parcial — alguns critérios não puderam ser verificados.
          </p>
        ) : null}
      </CardContent>
    </Card>
  )
}

export function QualificationMatrixCard({
  candidateId,
  companyId,
  matrix,
  searchCriteria,
  jobId,
}: QualificationMatrixCardProps) {
  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
  const candidateIsLocal = UUID_RE.test(candidateId)
  const shouldFetchSearch = !matrix && !!searchCriteria && candidateIsLocal && !!companyId
  // Deriva on-the-fly da vaga quando não há parecer salvo (ou parecer antigo sem matrix).
  const shouldFetchJob = !matrix && !searchCriteria && !!jobId && candidateIsLocal && !!companyId
  const shouldFetch = shouldFetchSearch || shouldFetchJob

  const queryKey = shouldFetchJob
    ? CANDIDATE_AI_QUERY_KEYS.qualificationMatrix(candidateId, jobId!, companyId)
    : CANDIDATE_AI_QUERY_KEYS.criteriaMatch(candidateId, JSON.stringify(searchCriteria ?? {}), companyId)

  const requestBody = shouldFetchJob
    ? { job_id: jobId }
    : { search_criteria: searchCriteria ?? {} }

  const { data, isLoading, isError, refetch } = useQuery<QualificationMatrixData>({
    queryKey,
    queryFn: async () => {
      const res = await fetch(
        `/api/backend-proxy/opinions/candidate/${candidateId}/criteria-match?company_id=${encodeURIComponent(companyId)}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
        }
      )
      if (!res.ok) throw new Error("Falha ao avaliar critérios da vaga")
      const json = await res.json()
      // Unwrap FastAPI ResponseEnvelopeMiddleware: {ok, data, meta} -> data
      return (json && typeof json === "object" && "ok" in json && "data" in json) ? json.data : json
    },
    enabled: shouldFetch,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  if (matrix) {
    if (!matrix.criteria || matrix.criteria.length === 0) return null
    return <MatrixBody matrix={matrix} />
  }

  if (!shouldFetch) return null

  if (isLoading) {
    return (
      <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl p-3 animate-pulse motion-reduce:animate-none">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-4 h-4 bg-lia-interactive-active rounded-md" />
          <div className="w-32 h-4 bg-lia-interactive-active rounded-md" />
        </div>
        <div className="space-y-1.5">
          <div className="w-full h-3 bg-lia-interactive-active rounded-md" />
          <div className="w-3/4 h-3 bg-lia-interactive-active rounded-md" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <Card className="bg-lia-bg-primary border border-lia-border-subtle">
        <CardContent className="flex items-center gap-3 p-3 text-lia-text-secondary">
          <AlertCircle className="h-4 w-4 flex-shrink-0 text-status-warning" />
          <span className="text-xs flex-1">Não foi possível avaliar os critérios da busca</span>
          <button onClick={() => refetch()} className="text-xs text-lia-text-muted hover:underline">
            Tentar novamente
          </button>
        </CardContent>
      </Card>
    )
  }

  if (!data || !data.criteria || data.criteria.length === 0) return null
  return <MatrixBody matrix={data} />
}
