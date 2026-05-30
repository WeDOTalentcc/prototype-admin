"use client"
import React from "react"
import { ScreeningQuestion, TranscriptionSegment } from "@/components/modals/screening-media-modal"
import type { TimelineActivity as ActivityData } from "./ActivityTimeline"
import { ActivityCommunicationDetails } from "./ActivityCommunicationDetails"
import { ActivityEvaluationDetails } from "./ActivityEvaluationDetails"
import { ActivityMiscDetails } from "./ActivityMiscDetails"

interface ActivityExpandedDetailsProps {
  activity: ActivityData & { details: NonNullable<ActivityData['details']> }
  candidate: Record<string, unknown>
  onOpenTriagemDetails?: (candidate: Record<string, unknown>) => void
  onSetScreeningModalData: (data: {
    type: 'audio' | 'video'
    title: string
    duration: string
    mediaUrl?: string
    questions: ScreeningQuestion[]
    transcription?: TranscriptionSegment[]
    highlights?: string[]
  } | null) => void
  onSetScreeningModalOpen: (open: boolean) => void
  onSetDiscModalData: (data: Record<string, unknown>) => void
  onSetDiscModalOpen: (open: boolean) => void
  onSetBigFiveModalCandidate: (candidate: Record<string, unknown>) => void
  onSetBigFiveModalOpen: (open: boolean) => void
  onSetSelectedFile: (file: Record<string, unknown>) => void
  onSetPreviewType: (type: 'pdf' | 'image' | 'video' | 'audio' | null) => void
  onSetShowPreview: (show: boolean) => void
}

const COMMUNICATION_TYPES = new Set([
  'email-sent', 'email-received', 'interview-scheduled', 'lia-screening'
])

const EVALUATION_TYPES = new Set([
  'lia-evaluation', 'voice-screening', 'rubric_evaluation', 'assessment', 'video-interview'
])

const MISC_TYPES = new Set([
  'job-application', 'test-completed', 'offer-sent', 'technical-test',
  'english-test', 'data-collection', 'onboarding', 'interview-note'
])

export function ActivityExpandedDetails({
  activity,
  candidate,
  onOpenTriagemDetails,
  onSetScreeningModalData,
  onSetScreeningModalOpen,
  onSetDiscModalData,
  onSetDiscModalOpen,
  onSetBigFiveModalCandidate,
  onSetBigFiveModalOpen,
}: ActivityExpandedDetailsProps) {
  return (
    <div className="px-3 pb-3 border-t border-lia-border-subtle bg-lia-bg-primary/50/50">
      {COMMUNICATION_TYPES.has(activity.type) && (
        <ActivityCommunicationDetails activity={activity} />
      )}

      {EVALUATION_TYPES.has(activity.type) && (
        <ActivityEvaluationDetails
          activity={activity}
          candidate={candidate}
          onOpenTriagemDetails={onOpenTriagemDetails}
          onSetScreeningModalData={onSetScreeningModalData}
          onSetScreeningModalOpen={onSetScreeningModalOpen}
          onSetDiscModalData={onSetDiscModalData}
          onSetDiscModalOpen={onSetDiscModalOpen}
          onSetBigFiveModalCandidate={onSetBigFiveModalCandidate}
          onSetBigFiveModalOpen={onSetBigFiveModalOpen}
        />
      )}

      {MISC_TYPES.has(activity.type) && (
        <ActivityMiscDetails activity={activity} />
      )}
    </div>
  )
}
