"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { AddCandidateModal } from "@/components/modals/add-candidate-modal"
import { CreateJobModal } from "@/components/modals/create-job-modal"
import { InterviewSchedulingModal } from "@/components/ui/interview-scheduling-modal"
import { CandidateCompareModal } from "@/components/modals/candidate-compare-modal"
import { useModalOpenListener } from "@/hooks/chat/useModalOpenListener"
import { useOfferReviewFlow } from "@/hooks/offers/useOfferReviewFlow"
import { LiaEntityModalHost } from "@/components/lia-global-modals/LiaEntityModalHost"
import { LiaTableStateBridge } from "@/components/lia-global-modals/LiaTableStateBridge"
import { HiringPolicyConfigModal } from "@/components/modals/hiring-policy-config-modal"

/**
 * LIAGlobalModals — listens for `lia:open_modal` events (dispatched by useUIAction)
 * and renders the correct modal regardless of which page the user is on.
 *
 * PR-J dual-path: Rail A cards that are not chat_executable open these modals
 * directly instead of running a chat loop.
 *
 * PR-B: also listens to `lia:open_offer_review` (Trigger A — Rail A Card 5.1
 * from any surface) and delegates to useOfferReviewFlow.
 *
 * Add new modal_id cases here as new capabilities are added to capability_map.yaml.
 *
 * Fase B3b (2026-06-09): adiciona hiring_policy_config (LiaPersonalizacaoHub em Dialog).
 * job_insights + job_compare tratados no LiaEntityModalHost (precisam de entidade).
 */
export function LIAGlobalModals() {
  const router = useRouter()

  const addCandidate = useModalOpenListener("add_candidate")
  const interviewScheduling = useModalOpenListener<{
    candidateName?: string
    candidateEmail?: string
    candidateId?: string
    jobTitle?: string
    jobVacancyId?: string
    userName?: string
    userEmail?: string
  }>("interview_scheduling")
  const candidateCompare = useModalOpenListener<{
    candidates?: { id: string; name: string }[]
    jobId?: string
    companyId?: string
  }>("candidate_compare")

  const stageTransition = useModalOpenListener<{ page?: string }>("stage_transition")

  // W1-3: Cards 1.1 (create-job) + 1.2 (job-template) open CreateJobModal.
  const createJob = useModalOpenListener("create_job")

  // B3b: Configurações LIA em modal (hiring_policy_config / configurar_policy capability)
  const hiringPolicyConfig = useModalOpenListener("hiring_policy_config")

  // GAP-04-001 fix: canonical path — chat LIA open_ui(send_offer) emits
  // lia:open_modal {modal_id:"offer_review"} via useUIAction case "open_modal".
  const offerReview = useModalOpenListener<{
    candidate_id?: string
    job_id?: string
    draft_id?: string
  }>("offer_review")

  // PR-B Trigger A: Rail A Card 5.1 sends ui_action="open_offer_review".
  // useUIAction dispatches `lia:open_offer_review` CustomEvent — handled here
  // so the modal works from any page (chat home, lateral, floating).
  const { openOfferReview } = useOfferReviewFlow()
  useEffect(() => {
    function handleOfferReview(e: Event) {
      const detail = (e as CustomEvent<{ candidate_id?: string; job_id?: string; draft_id?: string }>).detail
      if (detail?.candidate_id && detail?.job_id) {
        openOfferReview({
          candidateId: detail.candidate_id,
          jobId: detail.job_id,
          draftId: detail.draft_id,
        })
      }
    }
    window.addEventListener("lia:open_offer_review", handleOfferReview)
    return () => window.removeEventListener("lia:open_offer_review", handleOfferReview)
  }, [openOfferReview])

  // GAP-04-001: bridge canonical lia:open_modal path → openOfferReview
  useEffect(() => {
    if (offerReview.isOpen && offerReview.data.candidate_id && offerReview.data.job_id) {
      openOfferReview({
        candidateId: offerReview.data.candidate_id,
        jobId: offerReview.data.job_id,
        draftId: offerReview.data.draft_id,
      })
      offerReview.close()
    }
  }, [offerReview, openOfferReview])

  return (
    <>
      <AddCandidateModal
        isOpen={addCandidate.isOpen}
        onClose={addCandidate.close}
        onAdd={() => addCandidate.close()}
      />

      <InterviewSchedulingModal
        open={interviewScheduling.isOpen}
        onOpenChange={(open) => !open && interviewScheduling.close()}
        candidateName={interviewScheduling.data.candidateName ?? ""}
        candidateEmail={interviewScheduling.data.candidateEmail ?? ""}
        candidateId={interviewScheduling.data.candidateId}
        jobTitle={interviewScheduling.data.jobTitle ?? ""}
        jobVacancyId={interviewScheduling.data.jobVacancyId}
        userName={interviewScheduling.data.userName ?? ""}
        userEmail={interviewScheduling.data.userEmail ?? ""}
      />

      {candidateCompare.isOpen && (
        <CandidateCompareModal
          open={candidateCompare.isOpen}
          onClose={candidateCompare.close}
          candidates={candidateCompare.data.candidates ?? []}
          jobId={candidateCompare.data.jobId}
          companyId={candidateCompare.data.companyId}
        />
      )}

      {/* stage_transition: navigate to kanban instead of opening complex modal */}
      {stageTransition.isOpen && (() => {
        const page = stageTransition.data.page ?? "/visao-do-funil"
        stageTransition.close()
        router.push(page)
        return null
      })()}
      {/* Card 1.1 (Criar vaga) → CreateJobModal. "Criar em conversa" inicia o
          fluxo conversacional canônico via `lia:prefill-message` (mesmo
          mecanismo do DonePanel "Criar outra vaga" + lia-float-context). O
          orchestrator roteia "Criar nova vaga" → job_management/create_job. */}
      <CreateJobModal
        isOpen={createJob.isOpen}
        onClose={createJob.close}
        onCreateWithWizard={() => {
          createJob.close()
          window.dispatchEvent(
            new CustomEvent("lia:prefill-message", {
              detail: { message: "Criar nova vaga" },
            }),
          )
        }}
      />

      {/* B3b: Configurações LIA (hiring_policy_config / configurar_policy) */}
      <HiringPolicyConfigModal
        isOpen={hiringPolicyConfig.isOpen}
        onClose={hiringPolicyConfig.close}
      />

      {/* Fase B3: modais que precisam do objeto completo (candidato/vaga)
          abertos pela LIA via open_ui — resolve id→objeto e monta. */}
      <LiaEntityModalHost />

      {/* Fase 2: ponte in-page — aplica filtro/busca/ordenação do chat à
          tabela aberta (lia:apply_table_state). Não navega, não muta. */}
      <LiaTableStateBridge />
    </>
  )
}
