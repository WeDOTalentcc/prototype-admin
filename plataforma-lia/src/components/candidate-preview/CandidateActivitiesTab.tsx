"use client"
import React, { useState } from"react"
import { textStyles, cardStyles, formatScorePercent } from '@/lib/design-tokens'
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  Brain, ChevronDown,
  Calendar, ExternalLink, CheckCircle, Mail, Download, Linkedin,
  Mic, Play, ClipboardCheck, FileText, Code, Gift, UserCheck,
  Shield, Users, Building, Clock, AlertCircle,
  Eye, Video, Target, Briefcase, ThumbsUp, ThumbsDown
} from"lucide-react"
import { ScreeningQuestion, TranscriptionSegment } from"@/components/modals/screening-media-modal"
import { getDemoActivities, Activity as ActivityData } from"@/data/demo-activities"
import { ActivityFilters, type ActivityFilterType, type ActivityViewType, type PeriodFilterType } from"./activities/ActivityFilters"
import { ActivityTimeline } from"./activities/ActivityTimeline"
import { ActivityExpandedDetails } from"./activities/ActivityExpandedDetails"

interface CandidateActivitiesTabProps {
  candidate: Record<string, unknown>
  jobId?: string
  onShowLiaModal: () => void
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

const colorToBg: Record<string, string> = {
  'var(--lia-text-secondary)': 'var(--lia-bg-tertiary)',
  'var(--lia-text-tertiary)': 'var(--lia-bg-tertiary)',
  'var(--status-success)': 'var(--status-success-bg)',
  'var(--status-error)': 'var(--status-error-bg)',
  'var(--status-warning)': 'var(--status-warning-bg)',
  'var(--wedo-purple)': 'var(--wedo-purple-bg-10)',
  'var(--wedo-orange)': 'var(--wedo-orange-bg-15)',
  'var(--wedo-cyan)': 'var(--wedo-cyan-bg-10)',
}
const getBgColor = (color: string) => colorToBg[color] || 'var(--lia-bg-tertiary)'

export function CandidateActivitiesTab({
  candidate,
  jobId,
  onShowLiaModal,
  onOpenTriagemDetails,
  onSetScreeningModalData,
  onSetScreeningModalOpen,
  onSetDiscModalData,
  onSetDiscModalOpen,
  onSetBigFiveModalCandidate,
  onSetBigFiveModalOpen,
  onSetSelectedFile,
  onSetPreviewType,
  onSetShowPreview,
}: CandidateActivitiesTabProps) {
  const [expandedActivity, setExpandedActivity] = useState<string | null>(null)
  const [activityFilter, setActivityFilter] = useState<ActivityFilterType>('all')
  const [activityView, setActivityView] = useState<ActivityViewType>('timeline')
  const [periodFilter, setPeriodFilter] = useState<PeriodFilterType>('all')

  const useDemoData = process.env.NEXT_PUBLIC_USE_DEMO_DATA !== 'false'
  const activities: ActivityData[] = useDemoData ? getDemoActivities() : []

  const filterByPeriod = (activity: ActivityData) => {
    if (periodFilter === 'all') return true
    const now = new Date()
    const activityDate = new Date(activity.timestamp)
    const daysDiff = Math.floor((now.getTime() - activityDate.getTime()) / (1000 * 60 * 60 * 24))
    if (periodFilter === '7days') return daysDiff <= 7
    if (periodFilter === '30days') return daysDiff <= 30
    if (periodFilter === '3months') return daysDiff <= 90
    return true
  }

  const filteredActivities = activities.filter(activity => {
    const typeFilter = activityFilter === 'all' ||
      (activityFilter === 'emails' && activity.type.includes('email')) ||
      (activityFilter === 'interviews' && (activity.type.includes('interview') || activity.type === 'video-interview')) ||
      (activityFilter === 'lia' && (activity.type.includes('lia') || activity.type === 'assessment')) ||
      (activityFilter === 'applications' && activity.type === 'job-application') ||
      (activityFilter === 'tests' && activity.type.includes('test')) ||
      (activityFilter === 'offers' && (activity.type === 'offer-sent' || activity.type === 'onboarding')) ||
      (activityFilter === 'evaluations' && (activity.type === 'rubric_evaluation' || activity.type.includes('evaluation')))
    return typeFilter && filterByPeriod(activity)
  })


  const renderActivityCard = (activity: ActivityData, isTimeline: boolean) => {
    const ActivityIcon = activity.icon
    const isExpanded = expandedActivity === activity.id

    if (isTimeline) {
      return (
        <div key={activity.id} className="relative flex items-start ml-12">
          <div
            className="absolute -left-6 w-3 h-3 rounded-full border-2 border-white z-10"
            style={{backgroundColor: activity.iconColor, marginTop: '14px'}}
          ></div>
          <div className="flex-1 border border-lia-border-subtle rounded-xl transition-colors motion-reduce:transition-none">
            <div
              className="p-3 cursor-pointer hover:bg-lia-bg-primary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
              onClick={() => setExpandedActivity(isExpanded ? null : activity.id)}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{backgroundColor: getBgColor(activity.iconColor)}}
                >
                  <ActivityIcon className="w-4 h-4" style={{color: activity.iconColor}} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h5 className={textStyles.label}>{activity.title}</h5>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        {activity.jobId && (
                          <a
                            href={`#vaga-${activity.jobId}`}
                            className="text-xs text-lia-text-secondary hover:text-lia-text-primary hover:underline flex items-center gap-0.5"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Briefcase className="w-2.5 h-2.5" />
                            {activity.jobTitle}
                          </a>
                        )}
                        <span className={textStyles.bodySmall}>{activity.author} • {activity.date}</span>
                      </div>
                      <p className={`${textStyles.bodySmall} mt-1`}>{activity.summary}</p>
                    </div>
                    <div className="flex items-center gap-1.5">
                      {activity.score && (
                        <Chip variant={activity.score < 60 ? 'danger' : 'neutral'} muted className={`text-micro px-1.5 py-0 h-4 ${activity.score >= 80 ? 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-default' : activity.score >= 60 ? 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle' : ''}`}>
                          {formatScorePercent(activity.score)}
                        </Chip>
                      )}
                      {activity.statusLabel && (
                        <Chip variant={activity.status === 'rejected' ? 'danger' : 'neutral'} muted className={`text-micro px-1.5 py-0 h-4 ${activity.status === 'approved' || activity.status === 'completed' ? 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-default' : activity.status === 'in-progress' ? 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle' : activity.status === 'rejected' ? '' : 'bg-lia-bg-primary text-lia-text-secondary border-lia-border-subtle'}`}>
                          {activity.statusLabel}
                        </Chip>
                      )}
                      <ChevronDown className={`w-3.5 h-3.5 text-lia-text-secondary transition-transform motion-reduce:transition-none ${isExpanded ? 'rotate-180' : ''}`} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            {isExpanded && activity.details && (
              <ActivityExpandedDetails
                activity={activity as ActivityData & { details: NonNullable<ActivityData['details']> }}
                candidate={candidate}
                onOpenTriagemDetails={onOpenTriagemDetails}
                onSetScreeningModalData={onSetScreeningModalData}
                onSetScreeningModalOpen={onSetScreeningModalOpen}
                onSetDiscModalData={onSetDiscModalData}
                onSetDiscModalOpen={onSetDiscModalOpen}
                onSetBigFiveModalCandidate={onSetBigFiveModalCandidate}
                onSetBigFiveModalOpen={onSetBigFiveModalOpen}
                onSetSelectedFile={onSetSelectedFile}
                onSetPreviewType={onSetPreviewType}
                onSetShowPreview={onSetShowPreview}
              />
            )}
          </div>
        </div>
      )
    }

    return (
      <div key={activity.id} className="border border-lia-border-subtle rounded-xl transition-colors motion-reduce:transition-none">
        <div
          className="p-2.5 cursor-pointer hover:bg-lia-bg-primary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
          onClick={() => setExpandedActivity(isExpanded ? null : activity.id)}
        >
          <div className="flex items-start gap-2">
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
              style={{backgroundColor: getBgColor(activity.iconColor)}}
            >
              <ActivityIcon className="w-3.5 h-3.5" style={{color: activity.iconColor}} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h5 className={`${textStyles.bodySmall} font-medium`}>{activity.title}</h5>
                  <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                    {activity.jobId && (
                      <a
                        href={`#vaga-${activity.jobId}`}
                        className="text-xs text-lia-text-secondary hover:text-lia-text-primary hover:underline flex items-center gap-0.5"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Briefcase className="w-2.5 h-2.5" />
                        {activity.jobId} - {activity.jobTitle}
                      </a>
                    )}
                    <span className={textStyles.bodySmall}>{activity.author} • {activity.authorRole}</span>
                    <span className={textStyles.bodySmall}>{activity.date}</span>
                  </div>
                  <p className={`${textStyles.bodySmall} mt-1`}>{activity.summary}</p>
                </div>
                <div className="flex items-center gap-1.5">
                  {activity.score && (
                    <Chip variant={activity.score < 60 ? 'danger' : 'neutral'} muted className={`text-micro px-1.5 py-0 h-4 ${activity.score >= 80 ? 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-default' : activity.score >= 60 ? 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle' : ''}`}>
                      {formatScorePercent(activity.score)}
                    </Chip>
                  )}
                  {activity.statusLabel && (
                    <Chip variant={activity.status === 'rejected' ? 'danger' : 'neutral'} muted className={`text-micro px-1.5 py-0 h-4 ${activity.status === 'approved' || activity.status === 'completed' ? 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-default' : activity.status === 'in-progress' ? 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle' : activity.status === 'rejected' ? '' : 'bg-lia-bg-primary text-lia-text-secondary border-lia-border-subtle'}`}>
                      {activity.statusLabel}
                    </Chip>
                  )}
                  <ChevronDown className={`w-3.5 h-3.5 text-lia-text-secondary transition-transform motion-reduce:transition-none ${isExpanded ? 'rotate-180' : ''}`} />
                </div>
              </div>
            </div>
          </div>
        </div>
        {isExpanded && activity.details && (
              <ActivityExpandedDetails
                activity={activity as ActivityData & { details: NonNullable<ActivityData['details']> }}
                candidate={candidate}
                onOpenTriagemDetails={onOpenTriagemDetails}
                onSetScreeningModalData={onSetScreeningModalData}
                onSetScreeningModalOpen={onSetScreeningModalOpen}
                onSetDiscModalData={onSetDiscModalData}
                onSetDiscModalOpen={onSetDiscModalOpen}
                onSetBigFiveModalCandidate={onSetBigFiveModalCandidate}
                onSetBigFiveModalOpen={onSetBigFiveModalOpen}
                onSetSelectedFile={onSetSelectedFile}
                onSetPreviewType={onSetPreviewType}
                onSetShowPreview={onSetShowPreview}
              />
            )}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full" data-testid="candidate-activities-tab">
      {/* Filters bar - extracted to ActivityFilters */}
      <ActivityFilters
        totalCount={filteredActivities.length}
        activityFilter={activityFilter}
        activityView={activityView}
        periodFilter={periodFilter}
        onActivityFilterChange={setActivityFilter}
        onActivityViewChange={setActivityView}
        onPeriodFilterChange={setPeriodFilter}
        onShowLiaModal={onShowLiaModal}
      />

      {/* Timeline/List content - extracted to ActivityTimeline */}
      <div className="flex-1 overflow-y-auto p-3">
        <ActivityTimeline
          filteredActivities={filteredActivities}
          activityView={activityView}
          candidateName={String(candidate.name ?? '')}
          renderActivityCard={renderActivityCard}
        />
      </div>
    </div>
  )
}
