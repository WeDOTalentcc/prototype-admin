"use client"

import { useEffect, useRef } from "react"
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
import { TalentPoolInsightsModal } from "@/components/talent-pool-insights/TalentPoolInsightsModal"
import { SendEmailModal } from "@/components/email-templates"
import { ConfirmStageDeleteModal } from "@/components/modals/confirm-stage-delete-modal"

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
 *
 * 2026-06-17: talent_pool_insights — Juicybox 2-column insights for a job's talent pool.
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

  // 2026-06-17: Talent Pool Insights modal (Juicybox pattern)
  const talentPoolInsights = useModalOpenListener<{
    job_id?: string
    job_title?: string
  }>("talent_pool_insights")

  // 2026-06-18: send_email_offer — backend prepare_offer_manual_send emits
  // open_modal + modal_id="send_email_offer". OfferReviewModal also normalised to
  // this path (was lia:open_send_email_modal orphan — H-6 class bug).
  const sendEmailOffer = useModalOpenListener<{
    template_id?: string
    subject_pre_filled?: string
    body_pre_filled?: string
    offer_id?: string
  }>("send_email_offer")

  // 2026-06-18: confirm_stage_delete — pipeline_tools emits when stage has
  // candidates; informs recruiter to reply in chat with destination stage.
  const confirmStageDelete = useModalOpenListener<{
    candidate_count?: number
  }>("confirm_stage_delete")

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

  // GAP-04-004: ref-stable map so the effect closure never goes stale
  // (useModalOpenListener returns non-memoized close fns — ref pattern avoids
  //  re-registering the event listener on every render)
  const _closeModalFns = useRef<Record<string, () => void>>({})
  _closeModalFns.current = {
    add_candidate: addCandidate.close,
    interview_scheduling: interviewScheduling.close,
    candidate_compare: candidateCompare.close,
    stage_transition: stageTransition.close,
    create_job: createJob.close,
    hiring_policy_config: hiringPolicyConfig.close,
    offer_review: offerReview.close,
    talent_pool_insights: talentPoolInsights.close,
    send_email_offer: sendEmailOffer.close,
    confirm_stage_delete: confirmStageDelete.close,
  }

  // GAP-04-004: selective close — modal_id targets one modal, omission closes all
  useEffect(() => {
    function handleCloseModal(e: Event) {
      const detail = (e as CustomEvent<{ modal_id?: string }>).detail ?? {}
      if (detail.modal_id) {
        _closeModalFns.current[detail.modal_id]?.()
      } else {
        Object.values(_closeModalFns.current).forEach((fn) => fn())
      }
    }
    window.addEventListener("lia:close_modal", handleCloseModal)
    return () => window.removeEventListener("lia:close_modal", handleCloseModal)
  }, [])

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

      {/* 2026-06-17: Talent Pool Insights — Juicybox 2-column modal.
          Opened via open_ui(modal_id="talent_pool_insights", data={job_id, job_title}).
          Falls back gracefully when job_id is missing (modal stays closed). */}
      {talentPoolInsights.isOpen && talentPoolInsights.data.job_id && (
        <TalentPoolInsightsModal
          isOpen={talentPoolInsights.isOpen}
          onClose={talentPoolInsights.close}
          jobId={talentPoolInsights.data.job_id}
          jobTitle={talentPoolInsights.data.job_title}
        />
      )}

      {/* 2026-06-18: send_email_offer — canonical global path for offer email send.
          Data carries pre-filled subject/body from backend preparation when available. */}
      <SendEmailModal
        isOpen={sendEmailOffer.isOpen}
        onClose={sendEmailOffer.close}
      />

      {/* 2026-06-18: confirm_stage_delete — informa recrutador que a etapa tem
          candidatos e pede que responda no chat para qual etapa movê-los. */}
      <ConfirmStageDeleteModal
        isOpen={confirmStageDelete.isOpen}
        onClose={confirmStageDelete.close}
        candidateCount={confirmStageDelete.data.candidate_count}
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
