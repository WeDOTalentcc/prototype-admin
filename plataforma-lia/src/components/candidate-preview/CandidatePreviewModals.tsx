"use client"

import { textStyles } from '@/lib/design-tokens'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { InsufficientDataModal, type DataRequirement } from "@/components/modals/insufficient-data-modal"
import { LiaChatModal } from "@/components/candidate-preview/LiaChatModal"
import dynamic from "next/dynamic"
import type { CandidateData } from "./ProfileTabTypes"
import type { ScreeningQuestion, TranscriptionSegment } from "@/components/modals/screening-media-modal"

const ScreeningMediaModal = dynamic(() => import("@/components/modals/screening-media-modal").then(m => ({ default: m.ScreeningMediaModal })), { ssr: false })
const DISCAssessmentModal = dynamic(() => import("@/components/disc-assessment-modal").then(m => ({ default: m.DISCAssessmentModal })), { ssr: false })
const BigFiveModal = dynamic(() => import("@/components/big-five-modal").then(m => ({ default: m.BigFiveModal })), { ssr: false })

interface LiaAction {
  id: string
  title: string
  icon: string
  buttonText: string
}

interface ScreeningModalDataType {
  type: 'audio' | 'video'
  title: string
  duration: string
  mediaUrl?: string
  questions: ScreeningQuestion[]
  transcription?: TranscriptionSegment[]
  highlights?: string[]
}

interface DISCModalDataType {
  discScores?: { dominance: number; influence: number; steadiness: number; conscientiousness: number }
  dominance?: number
  influence?: number
  steadiness?: number
  conscientiousness?: number
  profile?: string
  profileDescription?: string
  culturalFitScore?: number
  culturalFit?: number
}

interface CandidatePreviewModalsProps {
  c: CandidateData
  candidate: Record<string, unknown>
  showLiaModal: boolean
  setShowLiaModal: (v: boolean) => void
  liaActions: LiaAction[]
  liaChatMessages: Array<{ role: 'user' | 'lia'; content: string }>
  isLiaChatLoading: boolean
  liaConversation: string
  setLiaConversation: (v: string) => void
  sendLiaMessage: (msg: string) => void
  onContact?: (candidate: Record<string, unknown>, channel?: 'email' | 'whatsapp') => void
  onSendEmail?: (candidate: Record<string, unknown>) => void
  onSchedule?: (candidate: Record<string, unknown>) => void
  onScheduleInterview?: (candidate: Record<string, unknown>) => void
  onSendAgendamento?: (candidate: Record<string, unknown>) => void
  onAddToList?: (candidate: Record<string, unknown>) => void
  onAddToVacancy?: (candidate: Record<string, unknown>) => void
  showUpdateOpinionAlert: boolean
  setShowUpdateOpinionAlert: (v: boolean) => void
  lastOpinionDate: Date | null
  generateNewOpinion: () => void
  showInsufficientDataModal: boolean
  setShowInsufficientDataModal: (v: boolean) => void
  dataRequirements: DataRequirement[]
  handleProceedWithLimitedData: () => void
  screeningModalOpen: boolean
  setScreeningModalOpen: (v: boolean) => void
  screeningModalData: ScreeningModalDataType | null
  setScreeningModalData: (v: ScreeningModalDataType | null) => void
  onOpenTriagemDetails?: (candidate: Record<string, unknown>) => void
  discModalOpen: boolean
  setDiscModalOpen: (v: boolean) => void
  discModalData: Record<string, unknown> | null
  setDiscModalData: (v: Record<string, unknown> | null) => void
  bigFiveModalOpen: boolean
  setBigFiveModalOpen: (v: boolean) => void
  bigFiveModalCandidate: Record<string, unknown> | null
  setBigFiveModalCandidate: (v: Record<string, unknown> | null) => void
}

export function CandidatePreviewModals({
  c,
  candidate,
  showLiaModal,
  setShowLiaModal,
  liaActions,
  liaChatMessages,
  isLiaChatLoading,
  liaConversation,
  setLiaConversation,
  sendLiaMessage,
  onContact,
  onSendEmail,
  onSchedule,
  onScheduleInterview,
  onSendAgendamento,
  onAddToList,
  onAddToVacancy,
  showUpdateOpinionAlert,
  setShowUpdateOpinionAlert,
  lastOpinionDate,
  generateNewOpinion,
  showInsufficientDataModal,
  setShowInsufficientDataModal,
  dataRequirements,
  handleProceedWithLimitedData,
  screeningModalOpen,
  setScreeningModalOpen,
  screeningModalData,
  setScreeningModalData,
  onOpenTriagemDetails,
  discModalOpen,
  setDiscModalOpen,
  discModalData,
  setDiscModalData,
  bigFiveModalOpen,
  setBigFiveModalOpen,
  bigFiveModalCandidate,
  setBigFiveModalCandidate,
}: CandidatePreviewModalsProps) {
  useLiaModalTracking('candidate-lia-chat', showLiaModal)
  useLiaModalTracking('candidate-update-opinion-alert', showUpdateOpinionAlert)
  useLiaModalTracking('candidate-insufficient-data', showInsufficientDataModal)
  useLiaModalTracking('candidate-screening-media', screeningModalOpen)
  useLiaModalTracking('candidate-disc-assessment', discModalOpen)
  useLiaModalTracking('candidate-big-five', bigFiveModalOpen)
  return (
    <>
      <LiaChatModal
        isOpen={showLiaModal}
        onClose={() => setShowLiaModal(false)}
        candidate={c}
        liaActions={liaActions}
        chatMessages={liaChatMessages}
        isLiaChatLoading={isLiaChatLoading}
        liaConversation={liaConversation}
        onConversationChange={setLiaConversation}
        onSendMessage={sendLiaMessage}
        onContact={onContact as unknown as never}
        onSendEmail={onSendEmail as unknown as never}
        onSchedule={onSchedule as unknown as never}
        onScheduleInterview={onScheduleInterview as unknown as never}
        onSendAgendamento={onSendAgendamento as unknown as never}
        onAddToList={onAddToList as unknown as never}
        onAddToVacancy={onAddToVacancy as unknown as never}
      />

      <AlertDialog open={showUpdateOpinionAlert} onOpenChange={setShowUpdateOpinionAlert}>
        <AlertDialogContent className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
          <AlertDialogHeader>
            <AlertDialogTitle className={textStyles.title}>
              Parecer Existente
            </AlertDialogTitle>
            <AlertDialogDescription className={textStyles.bodySmall}>
              Já existe um parecer gerado há {lastOpinionDate ? Math.floor((Date.now() - lastOpinionDate.getTime()) / (1000 * 60 * 60 * 24)) : 0} dias. 
              Deseja gerar um novo parecer? O anterior será arquivado.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="text-xs">Cancelar</AlertDialogCancel>
            <AlertDialogAction 
              onClick={generateNewOpinion}
              className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-xs text-white"
            >
              Gerar Novo Parecer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      <InsufficientDataModal
        isOpen={showInsufficientDataModal}
        onClose={() => setShowInsufficientDataModal(false)}
        onProceedAnyway={dataRequirements.filter(r => r.required && !r.hasData).length === 0 ? handleProceedWithLimitedData : undefined}
        requirements={dataRequirements}
        candidateName={c?.name as string | undefined}
      />

      {screeningModalData && (
        <ScreeningMediaModal
          isOpen={screeningModalOpen}
          onClose={() => {
            setScreeningModalOpen(false)
            setScreeningModalData(null)
          }}
          type={screeningModalData.type}
          title={screeningModalData.title}
          duration={screeningModalData.duration}
          mediaUrl={screeningModalData.mediaUrl}
          jobTitle={(c?.job_title as string | undefined) || (c?.jobTitle as string | undefined)}
          candidateName={c?.name as string | undefined}
          questions={screeningModalData.questions}
          transcription={screeningModalData.transcription}
          highlights={screeningModalData.highlights}
          onOpenFullEvaluation={onOpenTriagemDetails ? () => {
            setScreeningModalOpen(false)
            setScreeningModalData(null)
            onOpenTriagemDetails(candidate)
          } : undefined}
        />
      )}
      
      {discModalData && (
        <DISCAssessmentModal
          isOpen={discModalOpen}
          onClose={() => {
            setDiscModalOpen(false)
            setDiscModalData(null)
          }}
          candidate={c as Record<string, unknown>}
          assessmentData={{
            discScores: (discModalData as DISCModalDataType).discScores || {
              dominance: (discModalData as DISCModalDataType).dominance || 75,
              influence: (discModalData as DISCModalDataType).influence || 85,
              steadiness: (discModalData as DISCModalDataType).steadiness || 45,
              conscientiousness: (discModalData as DISCModalDataType).conscientiousness || 60
            },
            profile: (discModalData as DISCModalDataType).profile || 'DI',
            profileDescription: (discModalData as DISCModalDataType).profileDescription || '',
            culturalFitNota: (discModalData as DISCModalDataType).culturalFitScore || (discModalData as DISCModalDataType).culturalFit || 82,
          } as never}
        />
      )}
      
      {bigFiveModalCandidate && (
        <BigFiveModal
          isOpen={bigFiveModalOpen}
          onClose={() => {
            setBigFiveModalOpen(false)
            setBigFiveModalCandidate(null)
          }}
          candidate={bigFiveModalCandidate}
        />
      )}
    </>
  )
}
