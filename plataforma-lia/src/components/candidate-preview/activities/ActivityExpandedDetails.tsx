"use client"
import React from "react"
import { textStyles, cardStyles, badgeStyles, formatScorePercent } from '@/lib/design-tokens'
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Brain, ChevronDown,
  Calendar, ExternalLink, CheckCircle, Mail, Download, Linkedin,
  Mic, Play, ClipboardCheck, FileText, Code, Gift, UserCheck,
  Shield, Users, Building, Clock, AlertCircle,
  Eye, Video, Target, Briefcase, ThumbsUp, ThumbsDown
} from "lucide-react"
import { ScreeningQuestion, TranscriptionSegment } from "@/components/modals/screening-media-modal"
import { Activity as ActivityData } from "@/data/demo-activities"

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
  onSetSelectedFile,
  onSetPreviewType,
  onSetShowPreview,
}: ActivityExpandedDetailsProps) {
  return (
    const ActivityIcon = activity.icon
    const isExpanded = expandedActivity === activity.id

    if (isTimeline) {
      return (
        <div key={activity.id} className="relative flex items-start ml-12">
          <div
            className="absolute -left-6 w-3 h-3 rounded-full border-2 border-white z-10"
            style={{backgroundColor: activity.iconColor, marginTop: '14px'}}
          ></div>
          <div className="flex-1 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md transition-colors motion-reduce:transition-none">
            <div
              className="p-3 cursor-pointer hover:bg-lia-bg-primary dark:hover:bg-gray-800 transition-colors motion-reduce:transition-none"
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
                            className="text-xs text-lia-text-secondary dark:text-lia-text-secondary hover:text-lia-text-primary hover:underline flex items-center gap-0.5"
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
                        <Badge className={`text-xs px-1.5 py-0 h-4 ${activity.score >= 80 ? 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary border-lia-border-default dark:border-lia-border-default font-semibold' : activity.score >= 60 ? 'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary border-lia-border-subtle dark:border-lia-border-subtle font-medium' : 'bg-status-error/10 text-status-error border-status-error/30 font-medium'}`}>
                          {formatScorePercent(activity.score)}
                        </Badge>
                      )}
                      {activity.statusLabel && (
                        <Badge className={`text-xs px-1.5 py-0 h-4 ${activity.status === 'approved' || activity.status === 'completed' ? 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary border-lia-border-default dark:border-lia-border-default font-semibold' : activity.status === 'in-progress' ? 'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary border-lia-border-subtle dark:border-lia-border-subtle font-medium' : activity.status === 'rejected' ? 'bg-status-error/10 text-status-error border-status-error/30 font-medium' : 'bg-white text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-subtle'}`}>
                          {activity.statusLabel}
                        </Badge>
                      )}
                      <ChevronDown className={`w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary transition-transform motion-reduce:transition-none ${isExpanded ? 'rotate-180' : ''}`} />
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
      <div key={activity.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md transition-colors motion-reduce:transition-none">
        <div
          className="p-2.5 cursor-pointer hover:bg-lia-bg-primary dark:hover:bg-gray-800 transition-colors motion-reduce:transition-none"
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
                        className="text-xs text-lia-text-secondary dark:text-lia-text-secondary hover:text-lia-text-primary hover:underline flex items-center gap-0.5"
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
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${activity.score >= 80 ? 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary border-lia-border-default dark:border-lia-border-default font-semibold' : activity.score >= 60 ? 'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary border-lia-border-subtle dark:border-lia-border-subtle font-medium' : 'bg-status-error/10 text-status-error border-status-error/30 font-medium'}`}>
                      {formatScorePercent(activity.score)}
                    </Badge>
                  )}
                  {activity.statusLabel && (
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${activity.status === 'approved' || activity.status === 'completed' ? 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary border-lia-border-default dark:border-lia-border-default font-semibold' : activity.status === 'in-progress' ? 'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary border-lia-border-subtle dark:border-lia-border-subtle font-medium' : activity.status === 'rejected' ? 'bg-status-error/10 text-status-error border-status-error/30 font-medium' : 'bg-white text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-subtle'}`}>
                      {activity.statusLabel}
                    </Badge>
                  )}
                  <ChevronDown className={`w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary transition-transform motion-reduce:transition-none ${isExpanded ? 'rotate-180' : ''}`} />
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
    <div className="flex flex-col h-full">
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
  )
}
