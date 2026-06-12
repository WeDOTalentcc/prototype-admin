"use client"

/**
 * Fase B3 (2026-06-06): host de modais GLOBAIS que precisam do OBJETO completo
 * (candidato/vaga), abertos pela LIA via open_ui (que só carrega ids).
 *
 * Fluxo: open_ui (backend) emite `lia:open_modal` {modal_id, data:{candidate_id|
 * job_id, company_id}} → este host resolve id→objeto (useLiaCandidate/useLiaJob,
 * company-scoped) → monta o modal com o objeto. Loading: não abre até os dados
 * chegarem (evita modal vazio). Erro: toast honesto, não abre.
 *
 * Isolado do LIAGlobalModals (que trata modais id/objeto-leve) para reduzir
 * conflito no arquivo HOT. Adicionar um modal entidade-acoplável = 1 entrada no
 * ENTITY_MODAL_REGISTRY + 1 case no switch.
 *
 * Fase B3b (2026-06-09): 
 * - kind "jobs" (plural): job_compare — data.job_ids[] → useLiaJobs → JobCompareModal
 * - job_insights: kind "job" — mapeia job object → JobInsightData → JobInsightsModal
 */
import { useEffect, useState } from "react"
import { toast } from "sonner"
import { useLiaCandidate, useLiaJob, useLiaJobs } from "@/hooks/lia/use-lia-entity"
import { ENTITY_MODAL_REGISTRY } from "@/components/lia-global-modals/lia-entity-modal-registry"
import { GeneralScoreModal } from "@/components/modals/general-score-modal"
import { BigFiveModal } from "@/components/big-five-modal"
import { JobReportModal } from "@/components/job-report-modal"
import { JobCompareModal } from "@/components/modals/job-compare-modal"
import { JobInsightsModal, type JobInsightData } from "@/components/modals/job-insights-modal"

interface ActiveModal {
  modalId: string
  candidateId?: string
  jobId?: string
  jobIds?: string[]  // B3b: multi-vaga (job_compare)
}

export function LiaEntityModalHost() {
  const [active, setActive] = useState<ActiveModal | null>(null)

  useEffect(() => {
    function handle(e: Event) {
      const detail = (e as CustomEvent<{
        modal_id: string
        data?: {
          candidate_id?: string
          job_id?: string
          job_ids?: string[]  // B3b
        }
      }>).detail
      if (!detail || !(detail.modal_id in ENTITY_MODAL_REGISTRY)) return
      setActive({
        modalId: detail.modal_id,
        candidateId: detail.data?.candidate_id,
        jobId: detail.data?.job_id,
        jobIds: detail.data?.job_ids,  // B3b
      })
    }
    window.addEventListener("lia:open_modal", handle)
    return () => window.removeEventListener("lia:open_modal", handle)
  }, [])

  useEffect(() => {
    function handleClose() {
      setActive(null)
    }
    window.addEventListener("lia:close_modal", handleClose)
    return () => window.removeEventListener("lia:close_modal", handleClose)
  }, [])

  const kind = active ? ENTITY_MODAL_REGISTRY[active.modalId] : undefined
  const candidateQuery = useLiaCandidate(
    kind === "candidate" ? active?.candidateId : undefined,
  )
  const jobQuery = useLiaJob(kind === "job" ? active?.jobId : undefined)
  // B3b: hook sempre chamado (rules of hooks); ids=[] → enabled:false → sem fetch
  const jobsQueries = useLiaJobs(kind === "jobs" ? (active?.jobIds ?? []) : [])

  const close = () => setActive(null)

  useEffect(() => {
    if (!active) return
    if (kind === "candidate" && candidateQuery.isError) {
      toast.error("Não consegui carregar o candidato.")
      setActive(null)
    }
    if (kind === "job" && jobQuery.isError) {
      toast.error("Não consegui carregar a vaga.")
      setActive(null)
    }
    // B3b: qualquer query com erro fecha o modal
    if (kind === "jobs" && jobsQueries.some((q) => q.isError)) {
      toast.error("Não consegui carregar uma ou mais vagas.")
      setActive(null)
    }
  }, [active, kind, candidateQuery.isError, jobQuery.isError, jobsQueries])

  if (!active) return null

  // Não abre o modal até os dados chegarem (evita modal vazio/flicker).
  let loading = false
  if (kind === "candidate") loading = candidateQuery.isLoading
  else if (kind === "job") loading = jobQuery.isLoading
  else if (kind === "jobs") loading = jobsQueries.some((q) => q.isLoading)
  if (loading) return null

  const candidate = candidateQuery.data as Record<string, unknown> | undefined
  const job = jobQuery.data as Record<string, unknown> | undefined
  // B3b: filtra só os dados que carregaram com sucesso (defensivo)
  const jobs = jobsQueries
    .map((q) => q.data as Record<string, unknown> | undefined)
    .filter(Boolean) as Record<string, unknown>[]

  switch (active.modalId) {
    case "general_score":
      if (!candidate) return null
      return <GeneralScoreModal isOpen onClose={close} candidate={candidate} />
    case "big_five":
      if (!candidate) return null
      return <BigFiveModal isOpen onClose={close} candidate={candidate} />
    case "job_report":
      if (!job) return null
      return (
        <JobReportModal
          isOpen
          onClose={close}
          job={{ jobId: active.jobId ?? "", title: (job.title as string) ?? "" }}
        />
      )
    case "job_compare":
      if (jobs.length < 2) return null  // exige ao menos 2 vagas carregadas
      return (
        <JobCompareModal
          isOpen
          onClose={close}
          jobs={jobs as Parameters<typeof JobCompareModal>[0]["jobs"]}
        />
      )
    case "job_insights": {
      if (!job) return null
      // Mapeamento job object → JobInsightData. Campos analíticos (lia_metrics,
      // candidate_demographics) são opcionais — modal renderiza sem eles.
      const salaryRange = job.salary_range as { min?: number; max?: number } | undefined
      const insightData: JobInsightData = {
        id: (job.id as string) ?? active.jobId ?? "",
        code: job.code as string | undefined,
        title: (job.title as string) ?? "",
        status: (job.status as string) ?? "",
        priority: job.priority as string | undefined,
        deadline: job.deadline as string | undefined,
        candidates_count: job.candidates_count as number | undefined,
        approved_count: job.approved_count as number | undefined,
        screening_count: job.screening_count as number | undefined,
        rejected_count: job.rejected_count as number | undefined,
        performance_score: job.performance_score as number | undefined,
        avg_time_per_stage: job.avg_time_per_stage as number | undefined,
        salary_min: salaryRange?.min,
        salary_max: salaryRange?.max,
        work_model: job.work_model as string | undefined,
        location: job.location as string | undefined,
        behavioral_competencies: job.behavioral_competencies as JobInsightData["behavioral_competencies"],
        benefits: job.benefits as string[] | undefined,
        days_open: job.days_open as number | undefined,
        lia_metrics: job.lia_metrics as JobInsightData["lia_metrics"],
        candidate_demographics: job.candidate_demographics as JobInsightData["candidate_demographics"],
      }
      return (
        <JobInsightsModal
          isOpen
          onClose={close}
          jobs={[insightData]}
        />
      )
    }
    default:
      return null
  }
}
