"use client"

import React, { useMemo } from "react"
import { useTranslations, useLocale } from "next-intl"
import { KanbanColumn } from "@/components/pages/job-kanban/KanbanColumn"
import { JOB_KANBAN_COLUMNS, groupJobsByKanbanColumn, jobToKanbanItem } from "@/lib/transforms/jobs-to-kanban"
import type { Job } from "@/components/jobs"

interface JobsKanbanViewProps {
  jobs: Job[]
  onJobClick: (job: Job) => void
}

export function JobsKanbanView({ jobs, onJobClick }: JobsKanbanViewProps) {
  const t = useTranslations("jobsView")
  const locale = useLocale()

  const grouped = useMemo(() => groupJobsByKanbanColumn(jobs), [jobs])

  const labels = useMemo(() => ({
    deadlineSoon: (days: number) => t("deadlineSoon", { days }),
    deadlinePast: (days: number) => t("deadlinePast", { days }),
    candidatesCount: (count: number) => t("candidatesCount", { count }),
    ageDays: (days: number) => t("ageDays", { days }),
    ribbon: {
      label: () => t("ribbon.label"),
      deadlineOverdue: (days: number) => t("ribbon.deadlineOverdue", { days }),
      deadlineSoon: (days: number) => t("ribbon.deadlineSoon", { days }),
      urgent: () => t("ribbon.urgent"),
      pendingApproval: () => t("ribbon.pendingApproval"),
      noCandidates: () => t("ribbon.noCandidates"),
    },
  }), [t])

  // Task #562 — Labels separados (mini funil + info chips) repassados às
  // colunas para evitar que o KanbanCard precise importar next-intl.
  const funnelLabels = useMemo(() => ({
    screening: t("funnel.screening"),
    interview: t("funnel.interview"),
    final: t("funnel.final"),
    hired: t("funnel.hired"),
  }), [t])

  const infoLabels = useMemo(() => ({
    ageDays: (days: number) => t("ageDays", { days }),
    ownerLabel: t("ownerLabel"),
  }), [t])

  const jobById = useMemo(() => {
    const m = new Map<string, Job>()
    jobs.forEach(j => m.set(String(j.id), j))
    return m
  }, [jobs])

  return (
    <div className="flex-1 min-h-0 overflow-x-auto overflow-y-hidden">
      <div className="flex gap-3 pb-2 h-full min-w-max">
        {JOB_KANBAN_COLUMNS.map((col) => {
          const colJobs = grouped[col.id] ?? []
          const items = colJobs.map((job) => jobToKanbanItem(job, { locale, labels }))
          return (
            <KanbanColumn
              key={col.id}
              stage={{ id: col.id, name: t(`columns.${col.id}`), accentClass: col.accentClass }}
              items={items}
              onItemClick={(item) => {
                const job = jobById.get(item.id)
                if (job) onJobClick(job)
              }}
              isDragDisabled
              emptyMessage={t("emptyColumn")}
              funnelLabels={funnelLabels}
              infoLabels={infoLabels}
            />
          )
        })}
      </div>
    </div>
  )
}
