"use client"
import React, { useState, useMemo } from "react"
import { textStyles, formatScorePercent } from '@/lib/design-tokens'
import { Chip } from "@/components/ui/chip"
import {
  Brain, ChevronDown,
  Calendar, Mail, Mic, Video, Code, Gift, ClipboardCheck,
  FileText, UserCheck, Shield, Clock, AlertCircle, Target,
  Briefcase, ThumbsUp, ThumbsDown, Activity
} from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { ScreeningQuestion, TranscriptionSegment } from "@/components/modals/screening-media-modal"
import { ActivityFilters, type ActivityFilterType, type ActivityViewType, type PeriodFilterType } from "./activities/ActivityFilters"
import { ActivityTimeline } from "./activities/ActivityTimeline"
import { useCandidateActivities, type CandidateActivity } from "@/hooks/candidates/use-candidate-activities"

// ── Icon + color map derived from activity type ──────────────────────────────
type IconMeta = { icon: LucideIcon; color: string }

function getActivityIconMeta(type: string): IconMeta {
  const t = (type ?? "").toLowerCase()
  if (t.includes("email")) return { icon: Mail, color: "var(--wedo-cyan)" }
  if (t.includes("voice") || t.includes("wsi") || t.includes("screening"))
    return { icon: Mic, color: "var(--wedo-purple)" }
  if (t.includes("video") || t.includes("interview"))
    return { icon: Video, color: "var(--wedo-orange)" }
  if (t.includes("lia") || t.includes("brain") || t.includes("ai") || t.includes("analysis"))
    return { icon: Brain, color: "var(--wedo-coral)" }
  if (t.includes("calendar") || t.includes("schedule") || t.includes("agendamento"))
    return { icon: Calendar, color: "var(--wedo-orange)" }
  if (t.includes("offer") || t.includes("onboarding"))
    return { icon: Gift, color: "var(--status-success)" }
  if (t.includes("test") || t.includes("code") || t.includes("technical"))
    return { icon: Code, color: "var(--wedo-purple)" }
  if (t.includes("eval") || t.includes("rubric") || t.includes("feedback"))
    return { icon: ClipboardCheck, color: "var(--wedo-orange)" }
  if (t.includes("document") || t.includes("file"))
    return { icon: FileText, color: "var(--lia-text-secondary)" }
  if (t.includes("approved") || t.includes("hired"))
    return { icon: ThumbsUp, color: "var(--status-success)" }
  if (t.includes("rejected") || t.includes("declined"))
    return { icon: ThumbsDown, color: "var(--status-error)" }
  if (t.includes("stage") || t.includes("pipeline"))
    return { icon: Target, color: "var(--wedo-cyan)" }
  if (t.includes("apply") || t.includes("application"))
    return { icon: UserCheck, color: "var(--wedo-cyan)" }
  if (t.includes("urgent") || t.includes("alert"))
    return { icon: AlertCircle, color: "var(--status-error)" }
  if (t.includes("shield") || t.includes("compliance"))
    return { icon: Shield, color: "var(--wedo-purple)" }
  return { icon: Activity, color: "var(--lia-text-secondary)" }
}

const colorToBg: Record<string, string> = {
  "var(--lia-text-secondary)": "var(--lia-bg-tertiary)",
  "var(--lia-text-tertiary)": "var(--lia-bg-tertiary)",
  "var(--status-success)": "var(--status-success-bg)",
  "var(--status-error)": "var(--status-error-bg)",
  "var(--status-warning)": "var(--status-warning-bg)",
  "var(--wedo-purple)": "var(--wedo-purple-bg-10)",
  "var(--wedo-orange)": "var(--wedo-orange-bg-15)",
  "var(--wedo-cyan)": "var(--wedo-cyan-bg-10)",
  "var(--wedo-coral)": "var(--wedo-orange-bg-15)",
}
const getBgColor = (color: string) => colorToBg[color] ?? "var(--lia-bg-tertiary)"

// ── Activity normalization ────────────────────────────────────────────────────
interface NormalizedActivity {
  id: string
  type: string
  icon: LucideIcon
  iconColor: string
  title: string
  author: string
  authorRole?: string
  date: string
  timestamp: Date
  summary: string
  jobId?: string
  jobTitle?: string
  score?: number
  statusLabel?: string
  status?: "approved" | "completed" | "in-progress" | "rejected" | "pending"
  platform?: string
  details?: Record<string, any>
}

function normalizeActivity(a: CandidateActivity): NormalizedActivity {
  const { icon, color } = getActivityIconMeta(a.type)
  const rawDate = a.timestamp ?? a.date ?? ""
  const dateObj = rawDate ? new Date(rawDate) : new Date()
  const formattedDate = rawDate
    ? dateObj.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })
    : "—"

  const rawStatus = (a.status as string | undefined) ?? ""
  const mappedStatus: NormalizedActivity["status"] =
    rawStatus === "approved" ? "approved"
    : rawStatus === "completed" ? "completed"
    : rawStatus === "in_progress" || rawStatus === "in-progress" ? "in-progress"
    : rawStatus === "rejected" || rawStatus === "declined" ? "rejected"
    : rawStatus === "pending" ? "pending"
    : undefined

  const statusLabel =
    mappedStatus === "approved" ? "Aprovado"
    : mappedStatus === "completed" ? "Concluído"
    : mappedStatus === "in-progress" ? "Em andamento"
    : mappedStatus === "rejected" ? "Reprovado"
    : mappedStatus === "pending" ? "Pendente"
    : undefined

  return {
    id: a.id,
    type: a.type,
    icon,
    iconColor: color,
    title: a.title ?? a.type,
    author: (a.author as string | undefined) ?? "IA",
    authorRole: a.author_role as string | undefined,
    date: formattedDate,
    timestamp: dateObj,
    summary: (a.summary as string | undefined) ?? "",
    jobId: a.job_id as string | undefined,
    jobTitle: a.job_title as string | undefined,
    score: typeof a.score === "number" ? a.score : undefined,
    statusLabel,
    status: mappedStatus,
    platform: a.platform as string | undefined,
    details: a.details,
  }
}

// ── Component ─────────────────────────────────────────────────────────────────
interface CandidateActivitiesTabProps {
  candidate: Record<string, unknown>
  jobId?: string
  onShowLiaModal: () => void
  onOpenTriagemDetails?: (candidate: Record<string, unknown>) => void
  onSetScreeningModalData: (data: {
    type: "audio" | "video"
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
  onSetPreviewType: (type: "pdf" | "image" | "video" | "audio" | null) => void
  onSetShowPreview: (show: boolean) => void
}

export function CandidateActivitiesTab({
  candidate,
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
  const [activityFilter, setActivityFilter] = useState<ActivityFilterType>("all")
  const [activityView, setActivityView] = useState<ActivityViewType>("timeline")
  const [periodFilter, setPeriodFilter] = useState<PeriodFilterType>("all")

  const { activities: rawActivities, isLoading, error } = useCandidateActivities(candidate)

  const activities: NormalizedActivity[] = useMemo(
    () => rawActivities.map(normalizeActivity),
    [rawActivities],
  )

  const filterByPeriod = (a: NormalizedActivity) => {
    if (periodFilter === "all") return true
    const now = new Date()
    const daysDiff = Math.floor((now.getTime() - a.timestamp.getTime()) / (1000 * 60 * 60 * 24))
    if (periodFilter === "7days") return daysDiff <= 7
    if (periodFilter === "30days") return daysDiff <= 30
    if (periodFilter === "3months") return daysDiff <= 90
    return true
  }

  const filteredActivities = activities.filter((a) => {
    const typeOk =
      activityFilter === "all" ||
      (activityFilter === "emails" && a.type.includes("email")) ||
      (activityFilter === "interviews" &&
        (a.type.includes("interview") || a.type === "video-interview")) ||
      (activityFilter === "lia" &&
        (a.type.includes("lia") || a.type === "assessment" || a.type.includes("ai"))) ||
      (activityFilter === "applications" && a.type === "job-application") ||
      (activityFilter === "tests" && a.type.includes("test")) ||
      (activityFilter === "offers" &&
        (a.type === "offer-sent" || a.type === "onboarding")) ||
      (activityFilter === "evaluations" &&
        (a.type === "rubric_evaluation" || a.type.includes("evaluation")))
    return typeOk && filterByPeriod(a)
  })

  const renderActivityCard = (activity: NormalizedActivity, isTimeline: boolean) => {
    const ActivityIcon = activity.icon
    const isExpanded = expandedActivity === activity.id

    if (isTimeline) {
      return (
        <div key={activity.id} className="relative flex items-start ml-12">
          <div
            className="absolute -left-6 w-3 h-3 rounded-full border-2 border-white z-10"
            style={{ backgroundColor: activity.iconColor, marginTop: "14px" }}
          />
          <div className="flex-1 border border-lia-border-subtle rounded-xl transition-colors motion-reduce:transition-none">
            <div
              className="p-3 cursor-pointer hover:bg-lia-bg-primary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
              onClick={() => setExpandedActivity(isExpanded ? null : activity.id)}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: getBgColor(activity.iconColor) }}
                >
                  <ActivityIcon className="w-4 h-4" style={{ color: activity.iconColor }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h5 className={textStyles.label}>{activity.title}</h5>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        {activity.jobId && (
                          <span className="text-xs text-lia-text-secondary flex items-center gap-0.5">
                            <Briefcase className="w-2.5 h-2.5" />
                            {activity.jobTitle ?? activity.jobId}
                          </span>
                        )}
                        <span className={textStyles.bodySmall}>
                          {activity.author}
                          {activity.date ? ` • ${activity.date}` : ""}
                        </span>
                      </div>
                      {activity.summary && (
                        <p className={`${textStyles.bodySmall} mt-1`}>{activity.summary}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5">
                      {activity.score != null && (
                        <Chip
                          variant={activity.score < 60 ? "danger" : "neutral"}
                          muted
                          className="text-micro px-1.5 py-0 h-4 flex items-center"
                        >
                          {formatScorePercent(activity.score)}
                        </Chip>
                      )}
                      {activity.statusLabel && (
                        <Chip
                          variant={activity.status === "rejected" ? "danger" : "neutral"}
                          muted
                          className="text-micro px-1.5 py-0 h-4 flex items-center"
                        >
                          {activity.statusLabel}
                        </Chip>
                      )}
                      <ChevronDown
                        className={`w-3.5 h-3.5 text-lia-text-secondary transition-transform motion-reduce:transition-none ${
                          isExpanded ? "rotate-180" : ""
                        }`}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            {isExpanded && activity.details && (
              <div className="px-3 pb-3 text-xs text-lia-text-secondary border-t border-lia-border-subtle pt-2">
                <pre className="whitespace-pre-wrap break-all">{JSON.stringify(activity.details, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      )
    }

    return (
      <div
        key={activity.id}
        className="border border-lia-border-subtle rounded-xl transition-colors motion-reduce:transition-none"
      >
        <div
          className="p-2.5 cursor-pointer hover:bg-lia-bg-primary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
          onClick={() => setExpandedActivity(isExpanded ? null : activity.id)}
        >
          <div className="flex items-start gap-2">
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: getBgColor(activity.iconColor) }}
            >
              <ActivityIcon className="w-3.5 h-3.5" style={{ color: activity.iconColor }} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h5 className={`${textStyles.bodySmall} font-medium`}>{activity.title}</h5>
                  <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                    {activity.jobId && (
                      <span className="text-xs text-lia-text-secondary flex items-center gap-0.5">
                        <Briefcase className="w-2.5 h-2.5" />
                        {activity.jobTitle ?? activity.jobId}
                      </span>
                    )}
                    <span className={textStyles.bodySmall}>
                      {activity.author}
                      {activity.authorRole ? ` · ${activity.authorRole}` : ""}
                    </span>
                    {activity.date && (
                      <span className={textStyles.bodySmall}>{activity.date}</span>
                    )}
                  </div>
                  {activity.summary && (
                    <p className={`${textStyles.bodySmall} mt-1`}>{activity.summary}</p>
                  )}
                </div>
                <div className="flex items-center gap-1.5">
                  {activity.score != null && (
                    <Chip
                      variant={activity.score < 60 ? "danger" : "neutral"}
                      muted
                      className="text-micro px-1.5 py-0 h-4 flex items-center"
                    >
                      {formatScorePercent(activity.score)}
                    </Chip>
                  )}
                  {activity.statusLabel && (
                    <Chip
                      variant={activity.status === "rejected" ? "danger" : "neutral"}
                      muted
                      className="text-micro px-1.5 py-0 h-4 flex items-center"
                    >
                      {activity.statusLabel}
                    </Chip>
                  )}
                  <ChevronDown
                    className={`w-3.5 h-3.5 text-lia-text-secondary transition-transform motion-reduce:transition-none ${
                      isExpanded ? "rotate-180" : ""
                    }`}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        {isExpanded && activity.details && (
          <div className="px-2.5 pb-2.5 text-xs text-lia-text-secondary border-t border-lia-border-subtle pt-2">
            <pre className="whitespace-pre-wrap break-all">{JSON.stringify(activity.details, null, 2)}</pre>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full" data-testid="candidate-activities-tab">
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

      <div className="flex-1 overflow-y-auto p-3">
        {isLoading && (
          <div className="flex items-center justify-center py-8" role="status" aria-live="polite">
            <div className="animate-spin motion-reduce:animate-none rounded-full h-5 w-5 border-2 border-lia-border-medium border-t-transparent mr-2" />
            <span className="text-xs text-lia-text-secondary">Carregando atividades...</span>
          </div>
        )}

        {error && !isLoading && (
          <div
            className="flex items-center gap-2 p-3 rounded-lg bg-status-error/10 border border-status-error/20"
            role="alert"
          >
            <span className="text-xs text-status-error">{error}</span>
          </div>
        )}

        {!isLoading && !error && (
          <ActivityTimeline
            filteredActivities={filteredActivities as Parameters<typeof ActivityTimeline>[0]["filteredActivities"]}
            activityView={activityView}
            candidateName={String(candidate.name ?? "")}
            renderActivityCard={renderActivityCard as Parameters<typeof ActivityTimeline>[0]["renderActivityCard"]}
          />
        )}
      </div>
    </div>
  )
}
