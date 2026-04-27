"use client"

import { useRouter } from "next/navigation"
import { AddCandidateModal } from "@/components/modals/add-candidate-modal"
import { InterviewSchedulingModal } from "@/components/ui/interview-scheduling-modal"
import { CandidateCompareModal } from "@/components/modals/candidate-compare-modal"
import { useModalOpenListener } from "@/hooks/chat/useModalOpenListener"

/**
 * LIAGlobalModals — listens for `lia:open_modal` events (dispatched by useUIAction)
 * and renders the correct modal regardless of which page the user is on.
 *
 * PR-J dual-path: Rail A cards that are not chat_executable open these modals
 * directly instead of running a chat loop.
 *
 * Add new modal_id cases here as new capabilities are added to capability_map.yaml.
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
    </>
  )
}
