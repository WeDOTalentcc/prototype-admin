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
 * Modais id/objeto-leve continuam no LIAGlobalModals. job_insights/job_compare
 * (exigem shape específico de métricas, não o objeto cru) ficam p/ B3b.
 */
import { useEffect, useState } from "react"
import { toast } from "sonner"
import { useLiaCandidate, useLiaJob } from "@/hooks/lia/use-lia-entity"
import { ENTITY_MODAL_REGISTRY } from "@/components/lia-global-modals/lia-entity-modal-registry"
import { GeneralScoreModal } from "@/components/modals/general-score-modal"
import { BigFiveModal } from "@/components/big-five-modal"
import { JobReportModal } from "@/components/job-report-modal"

interface ActiveModal {
  modalId: string
  candidateId?: string
  jobId?: string
}

export function LiaEntityModalHost() {
  const [active, setActive] = useState<ActiveModal | null>(null)

  useEffect(() => {
    function handle(e: Event) {
      const detail = (e as CustomEvent<{
        modal_id: string
        data?: { candidate_id?: string; job_id?: string }
      }>).detail
      if (!detail || !(detail.modal_id in ENTITY_MODAL_REGISTRY)) return
      setActive({
        modalId: detail.modal_id,
        candidateId: detail.data?.candidate_id,
        jobId: detail.data?.job_id,
      })
    }
    window.addEventListener("lia:open_modal", handle)
    return () => window.removeEventListener("lia:open_modal", handle)
  }, [])

  const kind = active ? ENTITY_MODAL_REGISTRY[active.modalId] : undefined
  const candidateQuery = useLiaCandidate(
    kind === "candidate" ? active?.candidateId : undefined,
  )
  const jobQuery = useLiaJob(kind === "job" ? active?.jobId : undefined)

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
  }, [active, kind, candidateQuery.isError, jobQuery.isError])

  if (!active) return null

  // Não abre o modal até os dados chegarem (evita modal vazio/flicker).
  const loading =
    kind === "candidate" ? candidateQuery.isLoading : jobQuery.isLoading
  if (loading) return null

  const candidate = candidateQuery.data as Record<string, unknown> | undefined
  const job = jobQuery.data as Record<string, unknown> | undefined

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
    default:
      return null
  }
}
